"""One-CV recommendation flow for the D-083 development configuration.

This joins the parts that were evaluated separately in CP2.3, in the same order:

1. stage 1 returns the top `stage1_candidate_depth` jobs (Hybrid Qwen, caller-owned);
2. the D-074 seniority rule moves 3y+ jobs down inside that list (user can switch it off);
3. the top K jobs are analyzed;
4. each job uses its cached JD extraction (offline corpus, never re-extracted here);
5. evidence matching runs with the main model; on a processing failure only, the
   fallback model is tried once and the job records which model gave the result;
6. H2v2 turns assessments into a score (D-072);
7. the product order puts scored jobs first, conflicts next, held jobs last (D-013, D-073).

Retrieval, extraction lookup and model clients are passed in, so tests run with
fakes and cost nothing. A job that cannot be analyzed gets an explicit hold with
its reason. It is never dropped, never scored as zero and never replaced.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from jobfit.cv.parser import ParsedCV
from jobfit.eval.product_order import held_score, product_order_ids
from jobfit.matching.evidence_matcher import MatchingResult, match_evidence
from jobfit.schemas.analysis import ConstraintResult, ScoreResult, UnitAssessment
from jobfit.schemas.requirements import JDExtraction
from jobfit.scoring.hold_policy_v11 import score_with_hold_policy
from jobfit.search.filters import FilterResult, FilterState
from jobfit.search.seniority import RULE_VERSION, demote_senior

SERVICE_VERSION = 'recommend-service-v1'


@dataclass(frozen=True)
class RecommendConfig:
    pipeline_version: str
    stage1_candidate_depth: int
    stage1_k: int
    seniority_rule: str | None
    matching_model: str
    matching_fallback_model: str | None
    evidence_validator: str
    evidence_guardrails: tuple[str, ...]
    hold_policy: str
    partial_weight: float
    concurrency: int
    experience_conflict_rule: str | None = None   # D-086

    def __post_init__(self):
        if not 1 <= self.stage1_k <= self.stage1_candidate_depth:
            raise ValueError('stage1_k must be between 1 and the candidate depth')
        if self.seniority_rule not in (None, RULE_VERSION):
            raise ValueError('unknown seniority rule version')
        if not 0 <= self.partial_weight <= 1:
            raise ValueError('partial_weight must be between 0 and 1')
        if self.concurrency < 1:
            raise ValueError('concurrency must be positive')
        from jobfit.matching.experience_rule import RULE_VERSION as EXP_RULE
        if self.experience_conflict_rule not in (None, EXP_RULE):
            raise ValueError('unknown experience conflict rule version')

    @classmethod
    def from_yaml(cls, path: str | Path) -> 'RecommendConfig':
        raw = yaml.safe_load(Path(path).read_text())
        return cls(pipeline_version=raw['pipeline_version'],
                   stage1_candidate_depth=int(raw['stage1_candidate_depth']),
                   stage1_k=int(raw['stage1_k']),
                   seniority_rule=raw.get('stage1_seniority_rule'),
                   matching_model=raw['matching_model'],
                   matching_fallback_model=raw.get('matching_fallback_model'),
                   evidence_validator=raw['evidence_validator'],
                   evidence_guardrails=tuple(raw['evidence_guardrails']),
                   hold_policy=raw['hold_policy'],
                   partial_weight=float(raw['partial_weight']),
                   concurrency=int(raw['matching_concurrency_limit']),
                   experience_conflict_rule=raw.get('experience_conflict_rule'))


@dataclass
class JobResult:
    job_id: str
    stage1_rank: int          # position after the seniority rule, used only as a tie-break
    score: ScoreResult
    assessments: list[UnitAssessment] = field(default_factory=list)
    excluded_units: list[dict] = field(default_factory=list)
    constraints: list[ConstraintResult] = field(default_factory=list)
    matcher_model: str | None = None
    used_fallback: bool = False
    hold_reason: str | None = None
    attempts: list[dict] = field(default_factory=list)
    extraction: JDExtraction | None = None   # for display (requirement text and JD quotes)


@dataclass
class Recommendation:
    cv_id: str
    order: list[str]
    jobs: dict[str, JobResult]
    stage1_ids: list[str]
    analyzed_ids: list[str]
    demoted_ids: list[str]
    versions: dict
    # D-010 optional filters: job id -> 'matches' or 'unknown' (None when no filter object was given)
    filter_states: dict[str, str] | None = None
    active_filters: tuple[str, ...] = ()
    empty_message: str | None = None

    @property
    def held_ids(self) -> list[str]:
        return [j for j in self.analyzed_ids if self.jobs[j].hold_reason]

    @property
    def fallback_ids(self) -> list[str]:
        return [j for j in self.analyzed_ids if self.jobs[j].used_fallback]


Retrieve = Callable[[int], Sequence[str]]
ExtractionLookup = Callable[[str], tuple[JDExtraction | None, str | None]]
ConstraintLookup = Callable[[str, JDExtraction], list[ConstraintResult]]


def _match_once(cv, extraction, client, model, config, matcher=None) -> tuple[MatchingResult | None, dict]:
    try:
        result = (matcher or match_evidence)(cv, extraction, client=client, model=model,
                                validator_version=config.evidence_validator,
                                guardrail_ids=config.evidence_guardrails, dynamic_output=True)
    except Exception as exc:  # recorded, the fallback decides what happens next
        return None, {'model': model, 'status': 'error', 'error': type(exc).__name__}
    return result, {'model': model, 'status': result.status, 'error': result.error_code}


def analyze_job(cv: ParsedCV, job_id: str, rank: int, extraction: JDExtraction | None,
                missing_reason: str | None, *, client, fallback_client, config: RecommendConfig,
                constraints: ConstraintLookup | None = None, matcher=None) -> JobResult:
    if extraction is None:
        reason = 'JD extraction not available: ' + (missing_reason or 'unknown')
        return JobResult(job_id, rank, held_score(reason), hold_reason=reason)
    attempts = []
    result, info = _match_once(cv, extraction, client, config.matching_model, config, matcher)
    attempts.append(info)
    used_fallback = False
    if (result is None or result.status != 'done') and config.matching_fallback_model:
        result, info = _match_once(cv, extraction, fallback_client or client,
                                   config.matching_fallback_model, config, matcher)
        attempts.append(info)
        used_fallback = True
    if result is None or result.status != 'done':
        reason = 'Evidence matching did not finish: ' + (attempts[-1]['error'] or attempts[-1]['status'])
        return JobResult(job_id, rank, held_score(reason), hold_reason=reason, attempts=attempts,
                         used_fallback=used_fallback, extraction=extraction)
    score, excluded = score_with_hold_policy(extraction, result.assessments, policy=config.hold_policy,
                                             partial_weight=config.partial_weight)
    return JobResult(job_id, rank, score, assessments=result.assessments, excluded_units=excluded,
                     constraints=constraints(job_id, extraction) if constraints else [],
                     matcher_model=attempts[-1]['model'], used_fallback=used_fallback, attempts=attempts,
                     extraction=extraction)


def recommend(cv: ParsedCV, *, retrieve: Retrieve, buckets: Mapping[str, str | None],
              extraction_for: ExtractionLookup, client, config: RecommendConfig,
              fallback_client=None, seniority_enabled: bool = True,
              constraints: ConstraintLookup | None = None,
              on_result: Callable[[JobResult], None] | None = None,
              filtered: FilterResult | None = None, matcher=None,
              history_confirmed: bool = False) -> Recommendation:
    """Return the ordered recommendations for one parsed CV.

    `on_result` is called once per analyzed job as soon as it finishes (for a UI
    that shows progress). It never changes the final order.

    `retrieve(depth)` must return stage-1 job ids, best first, already limited to
    the eligible jobs for this user and split. `buckets` maps job id to the CP1
    experience bucket. `seniority_enabled=False` is the user switch.
    """
    status = cv.profile.parse_status
    if getattr(status, 'value', status) != 'ok':
        raise ValueError('CV must be parsed and confirmed before recommendations')
    if filtered is not None and not filtered.eligible_ids:
        return Recommendation(cv_id=cv.profile.cv_id, order=[], jobs={}, stage1_ids=[], analyzed_ids=[],
                              demoted_ids=[], versions={'service': SERVICE_VERSION, 'pipeline': config.pipeline_version},
                              filter_states={}, active_filters=filtered.active_filters,
                              empty_message=filtered.empty_message)
    stage1 = list(retrieve(config.stage1_candidate_depth))[:config.stage1_candidate_depth]
    if len(stage1) != len(set(stage1)):
        raise ValueError('Stage-1 ids must be unique')
    if filtered is not None and not set(stage1) <= set(filtered.eligible_ids):
        raise ValueError('Stage-1 returned a job outside the filtered eligible set')
    if constraints is None and config.experience_conflict_rule:
        from jobfit.matching.experience_rule import constraint_lookup
        constraints = constraint_lookup(cv, history_confirmed=history_confirmed)
    rule_on = bool(config.seniority_rule) and seniority_enabled
    reordered = demote_senior(stage1, buckets, enabled=rule_on)
    analyzed = reordered[:config.stage1_k]
    lookups = {job: extraction_for(job) for job in analyzed}
    with ThreadPoolExecutor(max_workers=min(config.concurrency, max(len(analyzed), 1))) as pool:
        futures = {job: pool.submit(analyze_job, cv, job, rank, *lookups[job], client=client,
                                    fallback_client=fallback_client, config=config, constraints=constraints,
                                    matcher=matcher)
                   for rank, job in enumerate(analyzed, 1)}
        owner = {f: job for job, f in futures.items()}
        jobs = {}
        for f in as_completed(owner):
            jobs[owner[f]] = f.result()
            if on_result:
                on_result(jobs[owner[f]])
    order = product_order_ids(analyzed, {j: r.score for j, r in jobs.items()},
                              {j: r.constraints for j, r in jobs.items()})
    states = None
    if filtered is not None:
        states = {x.job_id: x.status.value for x in filtered.matches + filtered.unknown}
        # Stable split keeps the product order inside each block (same result as
        # recommend/pipeline.assemble_recommendations, checked in the tests).
        order = ([j for j in order if states[j] == FilterState.MATCHES.value] +
                 [j for j in order if states[j] == FilterState.UNKNOWN.value])
    demoted = [j for j in analyzed if rule_on and reordered.index(j) != stage1.index(j)
               and buckets.get(j) in ('3-4y', '5y+')]
    return Recommendation(cv_id=cv.profile.cv_id, order=order, jobs=jobs, stage1_ids=stage1,
                          analyzed_ids=analyzed, demoted_ids=demoted,
                          versions={'service': SERVICE_VERSION, 'pipeline': config.pipeline_version,
                                    'seniority_rule': config.seniority_rule if rule_on else None,
                                    'matching_model': config.matching_model,
                                    'matching_fallback_model': config.matching_fallback_model,
                                    'hold_policy': config.hold_policy,
                                    'partial_weight': config.partial_weight, 'k': config.stage1_k,
                                    'experience_conflict_rule': config.experience_conflict_rule,
                                    'history_confirmed': history_confirmed},
                          filter_states=states and {j: states[j] for j in analyzed},
                          active_filters=filtered.active_filters if filtered else ())


def hybrid_retriever(conn, cv_skills, query, spec, *, job_ids, rrf_k: int = 60,
                     min_branch_depth: int = 20) -> Retrieve:
    """Stage-1 callable with the same branch rule as the saved development runs.

    eval/retrieval_run.py uses branch_depth = max(K, 20), so a top-30 list fuses
    the FTS top 30 and the dense top 30. Using 20 here would change the list.
    """
    from jobfit.search import hybrid

    def retrieve(depth: int) -> list[str]:
        rows = hybrid.rank(conn, cv_skills, query, spec, job_ids=job_ids, top_k=depth,
                           branch_depth=max(depth, min_branch_depth), k=rrf_k)
        return [r['job_id'] for r in rows]
    return retrieve


def extraction_from_record(row: Mapping | None) -> tuple[JDExtraction | None, str | None]:
    """Same matchable rule as the evaluated runs (run_cp23_luna_matching.matchable)."""
    if row is None:
        return None, 'not_extracted'
    raw = row.get('extraction')
    if row.get('status') != 'done' or not raw:
        return None, row.get('error_code') or row.get('status') or 'extraction_failed'
    if raw.get('jd_quality') != 'ok':
        return None, 'jd_quality_' + str(raw.get('jd_quality'))
    return JDExtraction.model_validate(raw), None
