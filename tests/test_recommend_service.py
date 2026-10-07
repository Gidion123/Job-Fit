"""Offline tests for the one-CV recommendation flow. Fake matcher, no model call."""
from datetime import date
import threading

import pytest

from jobfit.cv.parser import ParsedCV
from jobfit.matching.evidence_matcher import MatchingResult
from jobfit.recommend import service
from jobfit.recommend.service import RecommendConfig, recommend
from jobfit.schemas.analysis import ScoreStatus, UnitAssessment
from jobfit.schemas.cv import CVProfile
from jobfit.schemas.requirements import JDExtraction
from jobfit.config import REPO_ROOT

V3 = REPO_ROOT / 'config/versions/pipeline_cp23_provisional_v3_20261004.yaml'
CV = ParsedCV(profile=CVProfile(cv_id='CVX', raw_text='Used Python and SQL in a project.'),
              analysis_date=date(2026, 9, 30))


def cfg(**kw):
    base = dict(pipeline_version='t', stage1_candidate_depth=6, stage1_k=4,
                seniority_rule='seniority-demote-3y-v1', matching_model='sol', matching_fallback_model='luna',
                evidence_validator='quote-check-v1.1', evidence_guardrails=('G1', 'G2'),
                hold_policy='H2v2', partial_weight=0.5, concurrency=3)
    base.update(kw)
    return RecommendConfig(**base)


def extraction(job):
    return JDExtraction.model_validate({'job_id': job, 'units': [
        {'unit_id': 'u1', 'text': 'Python', 'importance': 'required', 'field': 'skill_tool', 'source_quotes': ['Python']},
        {'unit_id': 'u2', 'text': 'SQL', 'importance': 'required', 'field': 'skill_tool', 'source_quotes': ['SQL']}]})


def done(labels):
    return MatchingResult([UnitAssessment(unit_id=u, label=l, cv_quotes=['Used Python and SQL in a project.'] if l != 'NO_MATCH' else [])
                           for u, l in labels.items()], 'done')


def failed():
    return MatchingResult([UnitAssessment(unit_id=u, check_status='failed') for u in ('u1', 'u2')], 'failed', error_code='timeout')


@pytest.fixture
def fake(monkeypatch):
    calls = []
    plan = {}

    def match(cv, ext, *, client, model, **kw):
        calls.append((ext.job_id, model, kw))
        out = plan.get((ext.job_id, model), done({'u1': 'MATCH', 'u2': 'MATCH'}))
        if isinstance(out, Exception):
            raise out
        return out
    monkeypatch.setattr(service, 'match_evidence', match)
    return calls, plan


def run(config, buckets=None, missing=(), **kw):
    ids = ['A', 'B', 'C', 'D', 'E', 'F']
    return recommend(CV, retrieve=lambda depth: ids[:depth], buckets=buckets or {},
                     extraction_for=lambda j: (None, 'not_extracted') if j in missing else (extraction(j), None),
                     client=object(), config=config, **kw)


def test_v3_config_loads_with_frozen_choices():
    c = RecommendConfig.from_yaml(V3)
    assert (c.matching_model, c.matching_fallback_model, c.hold_policy) == ('gpt-6-sol', 'gpt-6-luna', 'H2v2')
    assert (c.stage1_candidate_depth, c.stage1_k, c.partial_weight, c.concurrency) == (30, 20, 0.5, 20)
    assert c.evidence_guardrails == ('G1', 'G2') and c.seniority_rule == 'seniority-demote-3y-v1'


def test_seniority_rule_runs_on_depth_then_top_k_is_analyzed(fake):
    calls, plan = fake
    rec = run(cfg(), buckets={'A': '5y+', 'B': '3-4y', 'C': 'not_stated'})
    assert rec.stage1_ids == list('ABCDEF') and rec.analyzed_ids == list('CDEF')
    assert sorted(j for j, _, _ in calls) == list('CDEF')
    assert rec.demoted_ids == [] and rec.versions['seniority_rule'] == 'seniority-demote-3y-v1'


def test_user_switch_turns_rule_off(fake):
    rec = run(cfg(), buckets={'A': '5y+'}, seniority_enabled=False)
    assert rec.analyzed_ids == list('ABCD') and rec.versions['seniority_rule'] is None


def test_demoted_jobs_inside_k_are_reported(fake):
    rec = run(cfg(stage1_k=6), buckets={'A': '5y+'})
    assert rec.analyzed_ids == list('BCDEFA') and rec.demoted_ids == ['A']
    assert rec.jobs['A'].stage1_rank == 6


def test_matcher_gets_evaluated_settings(fake):
    calls, _ = fake
    run(cfg())
    assert {m for _, m, _ in calls} == {'sol'}
    assert all(kw == {'validator_version': 'quote-check-v1.1', 'guardrail_ids': ('G1', 'G2'),
                      'dynamic_output': True} for _, _, kw in calls)


def test_product_order_scored_first_then_holds_in_stage1_order(fake):
    calls, plan = fake
    plan[('A', 'sol')] = done({'u1': 'MATCH', 'u2': 'NO_MATCH'})      # 50
    plan[('C', 'sol')] = done({'u1': 'MATCH', 'u2': 'PARTIAL'})       # 75
    plan[('B', 'sol')] = plan[('B', 'luna')] = failed()
    rec = run(cfg(), missing=('D',))
    assert rec.order == ['C', 'A', 'B', 'D']
    assert rec.jobs['C'].score.score_pct == 75.0 and rec.jobs['A'].score.score_pct == 50.0
    assert rec.held_ids == ['B', 'D']
    assert rec.jobs['D'].score.status == ScoreStatus.ON_HOLD and 'not_extracted' in rec.jobs['D'].hold_reason
    assert rec.jobs['B'].score.score_pct is None and rec.jobs['B'].attempts[-1]['model'] == 'luna'


def test_fallback_only_on_processing_failure_and_is_recorded(fake):
    calls, plan = fake
    plan[('A', 'sol')] = failed()
    plan[('B', 'sol')] = RuntimeError('network')
    rec = run(cfg())
    assert rec.jobs['A'].matcher_model == 'luna' and rec.jobs['A'].used_fallback
    assert rec.jobs['B'].matcher_model == 'luna' and rec.jobs['B'].attempts[0]['error'] == 'RuntimeError'
    assert rec.jobs['C'].matcher_model == 'sol' and not rec.jobs['C'].used_fallback
    assert sorted(rec.fallback_ids) == ['A', 'B']
    assert sum(m == 'luna' for _, m, _ in calls) == 2


def test_no_fallback_configured_holds_instead(fake):
    _, plan = fake
    plan[('A', 'sol')] = failed()
    rec = run(cfg(matching_fallback_model=None))
    assert rec.jobs['A'].hold_reason and rec.order[-1] == 'A'


def test_matching_runs_concurrently_within_limit(monkeypatch):
    active, peak, lock = [0], [0], threading.Lock()
    gate = threading.Barrier(3, timeout=5)

    def match(cv, ext, *, client, model, **kw):
        with lock:
            active[0] += 1; peak[0] = max(peak[0], active[0])
        try:
            gate.wait()
        except threading.BrokenBarrierError:
            pass
        with lock:
            active[0] -= 1
        return done({'u1': 'MATCH', 'u2': 'MATCH'})
    monkeypatch.setattr(service, 'match_evidence', match)
    run(cfg(stage1_k=6, concurrency=3))
    assert peak[0] == 3


def test_rejects_unconfirmed_cv_and_bad_config(fake):
    with pytest.raises(ValueError):
        cfg(stage1_k=7)
    with pytest.raises(ValueError):
        cfg(seniority_rule='other')
    bad = CV.model_copy(deep=True)
    bad.profile.parse_status = 'failed'
    with pytest.raises(ValueError):
        recommend(bad, retrieve=lambda d: ['A'], buckets={}, extraction_for=lambda j: (None, 'x'),
                  client=object(), config=cfg())


def test_duplicate_stage1_ids_are_rejected(fake):
    with pytest.raises(ValueError):
        recommend(CV, retrieve=lambda d: ['A', 'A'], buckets={}, extraction_for=lambda j: (extraction(j), None),
                  client=object(), config=cfg(stage1_k=2))


def test_hybrid_retriever_uses_saved_branch_rule(monkeypatch):
    from jobfit.search import hybrid
    seen = {}

    def fake_rank(conn, skills, query, spec, *, job_ids, top_k, branch_depth, k):
        seen.update(top_k=top_k, branch_depth=branch_depth, k=k)
        return [{'job_id': 'A'}, {'job_id': 'B'}]
    monkeypatch.setattr(hybrid, 'rank', fake_rank)
    retrieve = service.hybrid_retriever(None, set(), None, None, job_ids=['A', 'B'])
    assert retrieve(30) == ['A', 'B'] and seen == {'top_k': 30, 'branch_depth': 30, 'k': 60}
    retrieve(10)
    assert seen['branch_depth'] == 20


def test_extraction_record_rule_matches_evaluated_runs():
    raw = extraction('A').model_dump(mode='json')
    assert service.extraction_from_record({'status': 'done', 'extraction': raw})[0].job_id == 'A'
    assert service.extraction_from_record(None) == (None, 'not_extracted')
    assert service.extraction_from_record({'status': 'failed', 'error_code': 'timeout'}) == (None, 'timeout')
    bad = dict(raw, jd_quality='too_short')
    out = service.extraction_from_record({'status': 'done', 'extraction': bad})
    assert out[0] is None and out[1].startswith('jd_quality_')


def test_on_result_reports_each_job_once_without_changing_order(fake):
    seen = []
    rec = run(cfg(), on_result=lambda r: seen.append(r.job_id))
    assert sorted(seen) == sorted(rec.analyzed_ids) and len(seen) == 4
    assert rec.order == run(cfg()).order


def _filtered(states, active=('experience_bucket',)):
    from jobfit.search.filters import FilteredJob, FilterResult, FilterState
    items = {s: tuple(FilteredJob(j, FilterState(s), {}) for j, v in states.items() if v == s)
             for s in ('matches', 'unknown', 'conflicts')}
    return FilterResult(items['matches'], items['unknown'], items['conflicts'], active, True)


def test_filters_split_matches_then_unknown_keeping_product_order(fake):
    _, plan = fake
    plan[('A', 'sol')] = done({'u1': 'MATCH', 'u2': 'NO_MATCH'})   # 50
    plan[('C', 'sol')] = done({'u1': 'MATCH', 'u2': 'PARTIAL'})    # 75
    flt = _filtered({'A': 'matches', 'B': 'unknown', 'C': 'unknown', 'D': 'matches',
                     'E': 'matches', 'F': 'matches'})
    rec = run(cfg(), filtered=flt)
    assert rec.order[:2] == ['D', 'A'] and rec.order[2:] == ['B', 'C']
    assert rec.filter_states == {'A': 'matches', 'B': 'unknown', 'C': 'unknown', 'D': 'matches'}


def test_filter_split_agrees_with_assemble_recommendations(fake):
    from jobfit.recommend.pipeline import assemble_recommendations
    from jobfit.schemas.analysis import JobAnalysis
    _, plan = fake
    plan[('B', 'sol')] = plan[('B', 'luna')] = failed()
    plan[('C', 'sol')] = done({'u1': 'MATCH', 'u2': 'PARTIAL'})
    flt = _filtered({'A': 'unknown', 'B': 'matches', 'C': 'unknown', 'D': 'matches'})
    rec = recommend(CV, retrieve=lambda d: ['A', 'B', 'C', 'D'], buckets={},
                    extraction_for=lambda j: (extraction(j), None), client=object(),
                    config=cfg(stage1_candidate_depth=4, stage1_k=4), filtered=flt)
    groups = assemble_recommendations(flt, rec.analyzed_ids, {
        j: JobAnalysis(job_id=j, stage1_rank=i, score=rec.jobs[j].score) for i, j in enumerate(rec.analyzed_ids, 1)})
    flat = lambda g: g.no_conflict + g.has_conflict + g.not_fully_analyzed
    expected = [a.job_id for a in flat(groups.matching_filters)] + [a.job_id for a in flat(groups.unknown_filters)]
    assert rec.order == expected == ['D', 'B', 'A', 'C']


def test_no_active_filter_keeps_the_same_order(fake):
    base = run(cfg())
    flt = _filtered({j: 'matches' for j in 'ABCDEF'}, active=())
    assert run(cfg(), filtered=flt).order == base.order


def test_empty_filter_result_returns_message_and_never_widens(fake):
    calls, _ = fake
    flt = _filtered({'A': 'conflicts'})
    rec = run(cfg(), filtered=flt)
    assert rec.order == [] and 'did not widen' in rec.empty_message and calls == []


def test_retrieval_outside_filter_is_refused(fake):
    flt = _filtered({'A': 'matches'})
    with pytest.raises(ValueError):
        run(cfg(), filtered=flt)


def test_v4_config_and_experience_block(fake):
    c = RecommendConfig.from_yaml(REPO_ROOT / 'config/versions/pipeline_cp23_freeze_candidate_v4_20261006.yaml')
    assert (c.stage1_k, c.partial_weight, c.experience_conflict_rule) == (10, 0.5, 'experience-upper-bound-v1')
    from jobfit.schemas.cv import ExperienceEntry, PartialDate
    junior = CV.model_copy(deep=True)
    junior.profile.experience = [ExperienceEntry(title='Intern', start_partial=PartialDate(year=2026, month=2),
                                                 end_partial=PartialDate(year=2026, month=5))]

    def ext3(job):
        e = extraction(job).model_dump(mode='json')
        if job == 'A':
            e['units'].append({'unit_id': 'u3', 'text': '3 years', 'importance': 'required', 'field': 'experience_duration',
                               'kind': 'qualified', 'min_years': 3, 'source_quotes': ['3 years']})
        return JDExtraction.model_validate(e), None
    cfg_block = cfg(experience_conflict_rule='experience-upper-bound-v1')
    args = dict(retrieve=lambda d: list('ABCD'), buckets={}, extraction_for=ext3, client=object(), config=cfg_block)
    on = recommend(junior, history_confirmed=True, **args)
    off = recommend(junior, history_confirmed=False, **args)
    assert on.jobs['A'].constraints[0].state.value == 'explicit_conflict'
    assert all(c.state.value != 'explicit_conflict' for c in off.jobs['A'].constraints)
    # same scores, so only the conflict block can move A: scored non-conflict jobs come first
    assert on.order.index('A') > max(on.order.index(j) for j in 'BCD' if on.jobs[j].score.status.value in ('final', 'provisional'))
    assert on.versions['history_confirmed'] is True
