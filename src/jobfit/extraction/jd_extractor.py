"""Source-validated JD extraction. Failed outputs never become empty successful jobs."""
from dataclasses import dataclass, field
import re
from jobfit.config import REPO_ROOT, GUIDELINE_VERSION, SCHEMA_VERSION, GUIDELINE_FILE, JD_PROMPT_FILE, JD_PROMPT_VERSION
from jobfit.extraction.cache import ExtractionCache, cache_key, content_hash
from jobfit.jobs.cleaning import CLEANING_VERSION
from jobfit.llm.structured import StageFailure, validated_call, STRUCTURED_MAX_TOKENS
from jobfit.llm.output_policy import POLICY_VERSION, MODEL_OUTPUT_LIMIT, output_allowance, estimate_input_tokens
from jobfit.matching.quote_check import require_quotes
from jobfit.schemas.requirements import JDExtraction, JDQuality, LabelSource
from jobfit.extraction.coverage import qualification_coverage
from jobfit.extraction.audited import ExtractionSpec, AuditedExtraction, qualification_inventory, validate_inventory

@dataclass
class ExtractionResult:
    extraction: JDExtraction | None
    status: str
    cache_hit: bool=False
    attempts: int=0
    error_code: str | None=None
    key: str | None=None
    guideline_version: str=GUIDELINE_VERSION
    coverage: dict=field(default_factory=dict)

def extract_jd(text: str, *, job_id: str, client, model: str,
               cache: ExtractionCache | None=None, scope: str='session_jd', spec: ExtractionSpec | None=None,
               dynamic_output: bool=False) -> ExtractionResult:
    if scope not in ['session_jd','corpus_jd']: raise ValueError('invalid JD scope')
    if not text.strip() or len(text)>100_000: return ExtractionResult(None,'failed',error_code='empty_or_oversize_JD')
    if spec is None and JD_PROMPT_VERSION == 'jd-prompt-v1.4-experimental':
        # The selected prompt requires source-inventory fields on its wire
        # schema. Never send it with the plain JDExtraction schema.
        spec=ExtractionSpec(JD_PROMPT_FILE, JD_PROMPT_VERSION)
    prompt=(spec.prompt_file if spec else JD_PROMPT_FILE).read_text()+'\n\n'+GUIDELINE_FILE.read_text()
    wire=AuditedExtraction if spec else JDExtraction
    inventory=qualification_inventory(text) if spec else []
    payload={'job_id':job_id,'jd_text':text,
             **({'qualification_inventory':inventory} if spec else {})}
    max_tokens=(output_allowance('jd_extraction',estimate_input_tokens(prompt,payload,wire.model_json_schema()),
                                 max(len(inventory),1)) if dynamic_output else STRUCTURED_MAX_TOKENS)
    key=cache_key(text=text,model=model,schema=SCHEMA_VERSION+content_hash(str(wire.model_json_schema())),prompt=prompt,
        preprocessing=CLEANING_VERSION,guideline=GUIDELINE_VERSION,scope=scope,
        context={'job_id':job_id,'max_tokens':max_tokens,
                 'registry':content_hash((REPO_ROOT/'config/models_v1.yaml').read_text()),
                 **({'output_policy':POLICY_VERSION} if dynamic_output else {}),
                 **({'coverage_contract':spec.coverage_contract} if spec else {})})
    def validate(out):
        if out.job_id!=job_id: raise ValueError('job_identity_mismatch')
        if spec: validate_inventory(out,inventory)
        headings=list(re.finditer(r'(?im)^[ \t]*(?:qualifications(?:[ \t]+and[ \t]+requirements)?|preferred[ \t]+competencies[ \t]+and[ \t]+qualifications|requirements?|kualifikasi|persyaratan|character)[ \t]*:?[ \t]*$',text))
        # Some scraped public JDs flatten the heading and its first requirement
        # into one paragraph. An empty model answer is still unsafe there.
        headings+=list(re.finditer(r'(?i)\b(?:qualifications?[ \t]+and[ \t]+experience|qualifications?[ \t]+and[ \t]+requirements|minimum[ \t]+requirements?)\s*:',text))
        if not out.units and any(len(text[h.end():].strip())>20 for h in headings):
            # A populated requirement section is an observable conflict with an
            # empty answer, not proof that any nonempty answer is complete.
            raise ValueError('empty_extraction_despite_requirement_section')
        for u in out.units:
            require_quotes(u.source_quotes,text)
            if u.label_source!=LabelSource.MODEL_DRAFT: raise ValueError('model_cannot_claim_annotator_provenance')
            if len({b.branch_id for b in u.branches})!=len(u.branches): raise ValueError('duplicate_branch_ids')
    def checked_result(out, *, attempts=0, cache_hit=False):
        coverage=qualification_coverage(text,out.units)
        if spec:
            coverage['inventory_contract']=spec.coverage_contract
            coverage['inventory_count']=len(inventory)
            coverage['inventory_mappings']=[x.model_dump() for x in out.qualification_coverage]
            coverage['extraction_prompt_version']=spec.prompt_version
            out=JDExtraction.model_validate(out.model_dump(exclude={'qualification_coverage'}))
        if coverage['status']=='review_required':
            # Runtime safety overlay: leave raw cached/historical model output
            # intact; recheck cached responses too. This is not a new prompt.
            out=out.model_copy(update={'jd_quality':JDQuality.LOOKS_INCOMPLETE})
        return ExtractionResult(out,'done',attempts=attempts,cache_hit=cache_hit,key=key,coverage=coverage)
    if cache:
        saved=cache.get(key,scope=scope)
        if saved:
            try:
                out=wire.model_validate(saved);validate(out)
                return checked_result(out,cache_hit=True)
            except ValueError: pass  # corrupt/stale entry is a miss; do not use it
    try:
        out,attempts=validated_call(client,model=model,prompt=prompt,payload=payload,
            output_model=wire,task='jd_extraction',validate=validate,max_tokens=max_tokens,
            model_output_limit=MODEL_OUTPUT_LIMIT if dynamic_output else None)
    except StageFailure as exc:
        return ExtractionResult(None,'failed',attempts=exc.attempts,error_code=exc.code,key=key)
    out.extractor_version=(spec.prompt_version if spec else JD_PROMPT_VERSION)+'/'+model
    if cache: cache.put(key,out.model_dump(mode='json'),scope=scope)
    return checked_result(out,attempts=attempts)
