"""Presenter blocks for D-010 filters. Offline."""
from jobfit.api.presenter import recommendation
from jobfit.eval.product_order import held_score
from jobfit.recommend.service import JobResult, Recommendation
from jobfit.schemas.analysis import ScoreResult, ScoreStatus


def job(j, pct=None):
    score = ScoreResult(score_pct=pct, status=ScoreStatus.FINAL, required_total=1) if pct is not None else held_score('x')
    return JobResult(j, 1, score, hold_reason=None if pct is not None else 'x')


def test_blocks_follow_filter_state_and_keep_order():
    jobs = {'A': job('A', 80.0), 'B': job('B', 60.0), 'C': job('C')}
    rec = Recommendation('CV1', ['A', 'C', 'B'], jobs, list('ACB'), list('ACB'), [], {},
                         filter_states={'A': 'matches', 'C': 'matches', 'B': 'unknown'},
                         active_filters=('country_code',))
    out = recommendation(rec, {})
    first, second = out['blocks']
    assert first['title'] == 'Matches your filters' and [c['job_id'] for c in first['groups']['matches']] == ['A']
    assert [c['job_id'] for c in first['groups']['not_fully_analyzed']] == ['C']
    assert [c['job_id'] for c in second['groups']['matches']] == ['B'] and second['filter_state'] == 'unknown'
    assert out['active_filters'] == ['country_code']


def test_empty_result_carries_message():
    rec = Recommendation('CV1', [], {}, [], [], [], {}, filter_states={}, active_filters=('city',),
                         empty_message='No jobs meet the active filters. Change them; the system did not widen the search.')
    out = recommendation(rec, {})
    assert 'did not widen' in out['empty_message'] and out['blocks'][0]['groups']['matches'] == []
