"""One matching stage with complete identities and exact quotes, including OR branches."""
from dataclasses import dataclass, field
import math
from pydantic import BaseModel, ConfigDict
from jobfit.config import REPO_ROOT, GUIDELINE_VERSION, GUIDELINE_FILE, EVIDENCE_PROMPT_FILE, EVIDENCE_VALIDATOR, EVIDENCE_GUARDRAILS
from jobfit.cv.parser import ParsedCV
from jobfit.extraction.cache import cache_key, content_hash
from jobfit.llm.structured import StageFailure, validated_call, STRUCTURED_MAX_TOKENS
from jobfit.llm.output_policy import POLICY_VERSION, MODEL_OUTPUT_LIMIT, output_allowance, estimate_input_tokens
from jobfit.matching.quote_check import require_quotes
from jobfit.matching.quote_check_v11 import normalize_assessments_v11
from jobfit.matching.guardrails import apply_guardrails
from jobfit.schemas.analysis import UnitAssessment, CheckStatus, EvidenceLabel
from jobfit.schemas.requirements import JDExtraction, UnitKind, LabelSource

class EvidenceResponse(BaseModel):
    model_config=ConfigDict(extra='forbid')
    assessments: list[UnitAssessment]

@dataclass
class MatchingResult:
    assessments: list[UnitAssessment]
    status: str
    attempts: int=0
    cache_hit: bool=False
    error_code: str | None=None
    guideline_version: str=GUIDELINE_VERSION
    source_flags: list[dict]=field(default_factory=list)

def match_evidence(cv: ParsedCV, extraction: JDExtraction, *, client, model: str,
                   duration_years: dict[str,float | None] | None=None, cache=None,
                   validator_version: str | None=None,
                   guardrail_ids: tuple[str,...] | None=None,
                   dynamic_output: bool=False) -> MatchingResult:
    units={u.unit_id:u for u in extraction.units};durations=duration_years or {}
    selected_validator=validator_version or EVIDENCE_VALIDATOR
    selected_guards=EVIDENCE_GUARDRAILS if guardrail_ids is None else tuple(guardrail_ids)
    if selected_validator not in {'quote-check-v1.0','quote-check-v1.1'} or selected_guards not in ((),('G1','G2')):
        raise ValueError('unapproved evidence validation configuration')
    if any(v is not None and (isinstance(v,bool) or not isinstance(v,(int,float))
               or not math.isfinite(v) or v<0) for v in durations.values()):
        raise ValueError('duration bounds must be finite nonnegative numbers or unknown')
    def failed(code,attempts=0):
        return MatchingResult([UnitAssessment(unit_id=u,check_status='failed') for u in units],'failed',attempts=attempts,error_code=code)
    if cv.profile.parse_status.value!='ok': return failed('CV_parse_failed')
    if not units: return MatchingResult([],'done')
    prompt=EVIDENCE_PROMPT_FILE.read_text()+'\n\n'+GUIDELINE_FILE.read_text()
    payload={'extraction':extraction.model_dump(mode='json'),'cv_id':cv.profile.cv_id,
             'analysis_date':cv.analysis_date.isoformat(),'verified_duration_years':durations,
             'cv_text':cv.profile.raw_text}
    max_tokens=(output_allowance('evidence_matching',
                   estimate_input_tokens(prompt,payload,EvidenceResponse.model_json_schema()),len(units))
                if dynamic_output else STRUCTURED_MAX_TOKENS)
    context={'extraction':extraction.model_dump(mode='json'),'cv_id':cv.profile.cv_id,
             'analysis_date':cv.analysis_date.isoformat(),'verified_duration_years':durations,'max_tokens':max_tokens,
             'registry':content_hash((REPO_ROOT/'config/models_v1.yaml').read_text()),
             **({'output_policy':POLICY_VERSION} if dynamic_output else {})}
    key=cache_key(text=cv.profile.raw_text,model=model,schema=content_hash(str(EvidenceResponse.model_json_schema())),prompt=prompt,
        preprocessing='evidence-'+selected_validator+'-'+','.join(selected_guards),guideline=GUIDELINE_VERSION,scope='session_evidence',context=context)
    audit_flags=[]
    def validate(out, *, normalize=True):
        if normalize and selected_validator=='quote-check-v1.1':
            revised, flags=normalize_assessments_v11(
                [a.model_dump(mode='json') for a in out.assessments],
                [u.model_dump(mode='json') for u in extraction.units],cv.profile.raw_text)
            out.assessments=[UnitAssessment.model_validate(a) for a in revised]
            audit_flags.clear();audit_flags.extend(flags)
        rows=out.assessments
        if len(rows)!=len(units) or {a.unit_id for a in rows}!=set(units): raise ValueError('assessment_coverage')
        for a in rows:
            u=units[a.unit_id]
            if u.needs_review and a.check_status!=CheckStatus.FAILED: raise ValueError('unresolved_unit_needs_review')
            if a.label_source!=LabelSource.MODEL_DRAFT: raise ValueError('model_cannot_claim_annotator')
            if u.kind==UnitKind.ALTERNATIVE_GROUP and a.check_status!=CheckStatus.FAILED:
                if len(a.branches)!=len(u.branches) or {b.branch_id for b in a.branches}!={b.branch_id for b in u.branches}: raise ValueError('branch_coverage')
                if a.label is not None or a.cv_quotes: raise ValueError('group_label_must_be_resolved_by_scorer')
                targets=[(b,next(br.min_years for br in u.branches if br.branch_id==b.branch_id)) for b in a.branches]
            else:
                if a.branches: raise ValueError('unexpected_branches')
                targets=[(a,u.min_years)]
            for item,minimum in targets:
                if item.check_status==CheckStatus.FAILED:
                    if item.label is not None or item.cv_quotes: raise ValueError('failed_is_not_evidence')
                    continue
                if item.label is None: raise ValueError('done_requires_label')
                if item.label==EvidenceLabel.NO_MATCH:
                    if item.cv_quotes: raise ValueError('negative_cannot_cite_unrelated_evidence')
                else: require_quotes(item.cv_quotes,cv.profile.raw_text)
                duration_key=u.unit_id if not a.branches else u.unit_id+'/'+item.branch_id
                years=durations.get(duration_key)
                if minimum is not None:
                    if item.label==EvidenceLabel.MATCH and (years is None or years<minimum): raise ValueError('qualified_MATCH_needs_bounded_duration')
                    if years is None and u.importance.value=='required' and item.check_status!=CheckStatus.NEEDS_CLARIFICATION:
                        raise ValueError('unbounded_required_duration_needs_clarification')
    def apply_selected_guards(out):
        if not selected_guards: return
        revised=[]
        for assessment in out.assessments:
            unit=units[assessment.unit_id]
            row, changes=apply_guardrails(unit.model_dump(mode='json'), assessment.model_dump(mode='json'), cv.profile.raw_text)
            revised.append(UnitAssessment.model_validate(row))
            audit_flags.extend({'kind':'G1_G2','change':c} for c in changes)
        out.assessments=revised
    if cache:
        saved=cache.get(key,scope='session_evidence')
        if saved:
            try:
                out=EvidenceResponse.model_validate(saved['response'])
                validate(out,normalize=False)
                return MatchingResult(out.assessments,'done',cache_hit=True,source_flags=saved['source_flags'])
            except (KeyError,TypeError,ValueError): pass
    try:
        request_context={k:v for k,v in context.items() if k!='output_policy'}
        out,attempts=validated_call(client,model=model,prompt=prompt,payload={**request_context,'cv_text':cv.profile.raw_text},
            output_model=EvidenceResponse,task='evidence_matching',validate=validate,max_tokens=max_tokens,
            model_output_limit=MODEL_OUTPUT_LIMIT if dynamic_output else None)
    except StageFailure as exc: return failed(exc.code,exc.attempts)
    apply_selected_guards(out)
    if cache: cache.put(key,{'response':out.model_dump(mode='json'),'source_flags':audit_flags},scope='session_evidence')
    return MatchingResult(out.assessments,'done',attempts=attempts,source_flags=audit_flags)
