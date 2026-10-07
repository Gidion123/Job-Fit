"""CP2.2 backend vertical slice. Upload preview, explicit confirmation, pasted-JD report.

No UI, workbook, corpus, test-set, gold or tuning mutation. Session cache is caller-owned.
"""
from dataclasses import dataclass, field, asdict
from datetime import date
from pydantic import BaseModel, Field
from jobfit.cv.parser import ParsedCV
from jobfit.config import runtime_versions
from jobfit.extraction.cache import ExtractionCache
from jobfit.extraction.paste_jd import preview_pasted_jd
from jobfit.matching.constraints import experience_years, experience_constraint, location_constraint, work_authorization_constraint
from jobfit.matching.evidence_matcher import match_evidence
from jobfit.schemas.analysis import ConstraintResult, ConstraintState, ConstraintKind, ScoreResult, ScoreStatus, UnitAssessment
from jobfit.schemas.requirements import JDExtraction, Importance, RequirementField, UnitKind
from jobfit.scoring.score import compute_score

@dataclass(frozen=True)
class RelevantWork:
    """Caller-reviewed scope links, not a model assertion of full technology tenure.

    The quote must explicitly establish the relevant activity for the entry period.
    No inference from the title. Partial activity periods require a separate dated
    entry with its source, rather than assigning the whole job's months.
    """
    employment_indices: tuple[int,...]
    scope_quotes: tuple[str,...]
    confirmed: bool=False

@dataclass
class AnalysisContext:
    analysis_date: date
    parsing_confirmed: bool=False
    complete_work_history_confirmed: bool=False
    relevant_work: dict[str,RelevantWork]=field(default_factory=dict)
    confirmed_location: str | None=None
    job_location: str | None=None
    job_is_remote: bool | None=None

class ComparisonReport(BaseModel):
    job_id: str
    cv_id: str
    analysis_date: date
    status: str
    extraction: JDExtraction | None=None
    assessments: list[UnitAssessment]=Field(default_factory=list)
    constraints: list[ConstraintResult]=Field(default_factory=list)
    score: ScoreResult
    warnings: list[str]=Field(default_factory=list)
    operations: dict=Field(default_factory=dict)
    versions: dict=Field(default_factory=dict)
    denominator_status: str='identified_units'
    scope: str='session_only'
    interpretation: str='CV evidence coverage, not a hiring probability; retrieval scores are not match percentages.'

def _durations(cv,extraction,context):
    entries=cv.profile.experience
    upper=experience_years(entries,context.analysis_date) if context.complete_work_history_confirmed else None
    years={}
    for u in extraction.units:
        minima=[(u.unit_id+'/'+b.branch_id,b.min_years) for b in u.branches] if u.branches else [(u.unit_id,u.min_years)]
        for key,minimum in minima:
            if minimum is None: continue
            link=context.relevant_work.get(key)
            value=None
            if link and link.confirmed:
                if not link.employment_indices or len(link.employment_indices)!=len(link.scope_quotes): raise ValueError('duration_link_requires_scoped_quotes')
                selected=[]
                for i,q in zip(link.employment_indices,link.scope_quotes):
                    if i<0 or i>=len(entries) or not q.strip() or q not in entries[i].description: raise ValueError('duration_link_source_invalid')
                    selected.append(entries[i])
                value=experience_years(selected,context.analysis_date)
            # Upper bound may establish shortfall, never compatible relevant duration.
            if value is None and upper is not None and upper<minimum: value=upper
            years[key]=value
    return years

def _constraints(extraction,years,context):
    out=[]
    for u in extraction.units:
        if u.importance!=Importance.REQUIRED: continue
        if u.min_years is not None and u.kind!=UnitKind.ALTERNATIVE_GROUP:
            c=experience_constraint(u.min_years,years.get(u.unit_id))
            c.message=f'{u.unit_id}: {c.message}. JD: '+ ' | '.join(u.source_quotes)
            out.append(c)
        elif any(b.min_years is not None for b in u.branches):
            out.append(ConstraintResult(kind='experience',state='unknown',message=f'{u.unit_id}: experience is an alternative, not an independent mandatory minimum. Review the supported branch. JD: '+ ' | '.join(u.source_quotes)))
    if not any(c.kind==ConstraintKind.EXPERIENCE for c in out):
        out.append(ConstraintResult(kind='experience',state='unknown',
            message='No unambiguous required experience minimum was extracted. Preferred or unknown conditions are not hard constraints.'))
    locations=[q for u in extraction.units if u.field==RequirementField.LOCATION for q in u.source_quotes]
    loc=location_constraint(context.job_location,context.job_is_remote,context.confirmed_location)
    if locations:loc.message+='; JD: '+' | '.join(locations)
    out.append(loc)
    auth=work_authorization_constraint(any(u.field==RequirementField.WORK_AUTHORIZATION for u in extraction.units))
    if auth:
        auth.message+='; JD: '+' | '.join(q for u in extraction.units if u.field==RequirementField.WORK_AUTHORIZATION for q in u.source_quotes)
        out.append(auth)
    return out

def compare_pasted_jd(cv: ParsedCV, jd_text: str, *, context: AnalysisContext, client, model: str,
                      cache: ExtractionCache | None=None, extraction_spec=None,
                      matching_validator: str | None=None,
                      matching_guardrails: tuple[str,...] | None=None) -> ComparisonReport:
    versions=runtime_versions()
    if extraction_spec:
        from hashlib import sha256
        versions.update(jd_prompt_version=extraction_spec.prompt_version,
            jd_prompt_file=str(extraction_spec.prompt_file.relative_to(__import__('jobfit.config',fromlist=['REPO_ROOT']).REPO_ROOT)),
            jd_prompt_sha256=sha256(extraction_spec.prompt_file.read_bytes()).hexdigest(),
            extraction_coverage_contract=extraction_spec.coverage_contract)
    if not isinstance(context.analysis_date,date) or context.analysis_date!=cv.analysis_date:
        raise ValueError('Use one explicit configured analysis_date for parsing and analysis')
    if cv.profile.parse_status.value!='ok' or not context.parsing_confirmed:
        return ComparisonReport(job_id='unprocessed',cv_id=cv.profile.cv_id,analysis_date=context.analysis_date,
            status='parsing_review_required',score=ScoreResult(status='on_hold',reasons=['Parse and review the CV summary before analysis.']),warnings=cv.warnings,versions=versions)
    preview=preview_pasted_jd(jd_text,client=client,model=model,cache=cache,extraction_spec=extraction_spec)
    ex=preview.result
    if ex.status=='failed':
        return ComparisonReport(job_id=preview.job_id,cv_id=cv.profile.cv_id,analysis_date=context.analysis_date,status='extraction_failed',
            score=ScoreResult(status='on_hold',reasons=['JD extraction failed; no score is available.']),warnings=preview.warnings,
            operations={'extraction':{'attempts':ex.attempts,'error_code':ex.error_code}},versions=versions)
    extraction=ex.extraction
    if extraction.jd_quality=='looks_incomplete':
        return ComparisonReport(job_id=preview.job_id,cv_id=cv.profile.cv_id,analysis_date=context.analysis_date,
            status='extraction_review_required',extraction=extraction,
            score=ScoreResult(status='on_hold',reasons=['JD source coverage or completeness needs review before matching.']),
            denominator_status='pending_source_coverage_review',
            warnings=preview.warnings+['No final percentage: review the extraction against the source JD.'],
            operations={'extraction':{'attempts':ex.attempts,'cache_hit':ex.cache_hit,'coverage':ex.coverage},
                        'matching':{'attempts':0,'status':'not_attempted'}},versions=versions)
    years=_durations(cv,extraction,context)
    matched=match_evidence(cv,extraction,client=client,model=model,duration_years=years,cache=cache,
                           validator_version=matching_validator,guardrail_ids=matching_guardrails)
    score=compute_score(extraction,matched.assessments,cv.profile.parse_status)
    unresolved=any(u.needs_review for u in extraction.units)
    if unresolved:
        # D-049: an unsupported composite is not a certified single obligation.
        # Preserve all identified units/counts, but withhold the percentage. The
        # deterministic score formula and historical artifacts remain unchanged.
        score=score.model_copy(update={'status':ScoreStatus.ON_HOLD,'score_pct':None,
            'reasons':score.reasons+['Requirement structure needs review; identified denominator is not validated.']})
    return ComparisonReport(job_id=preview.job_id,cv_id=cv.profile.cv_id,analysis_date=context.analysis_date,
        status='matching_failed' if matched.status!='done' else ('structure_review_required' if unresolved else 'done'),extraction=extraction,
        versions=versions,denominator_status='pending_structure_review' if unresolved else 'identified_units',
        assessments=matched.assessments,score=score,constraints=_constraints(extraction,years,context),
        warnings=preview.warnings+(['Some units require interpretation review before a final decision.'] if any(u.needs_review for u in extraction.units) else []),
        operations={'extraction':{'attempts':ex.attempts,'cache_hit':ex.cache_hit,'key':ex.key,'coverage':ex.coverage},
                    'matching':{'attempts':matched.attempts,'cache_hit':matched.cache_hit,'error_code':matched.error_code,
                                'source_flags':matched.source_flags},
                    'configured_analysis_date':context.analysis_date.isoformat(),'duration_bounds':years,
                    'complete_work_history_confirmed':context.complete_work_history_confirmed,
                    'scoped_work_links':{k:asdict(v) for k,v in context.relevant_work.items()}})
