import math

import pytest

from jobfit.eval.product_order import held_score, product_order_ids, product_order_metrics
from jobfit.schemas.analysis import ConstraintKind, ConstraintResult, ConstraintState, ScoreResult, ScoreStatus


def s(pct, status=ScoreStatus.FINAL):
    return ScoreResult(score_pct=pct, status=status, required_total=4)


def test_holds_go_last_in_stage1_order_and_ties_keep_stage1():
    ids = ['A', 'B', 'C', 'D', 'E']
    scores = {'A': held_score('failed'), 'B': s(50.0), 'C': s(80.0, ScoreStatus.PROVISIONAL),
              'D': ScoreResult(status=ScoreStatus.NO_SCORE), 'E': s(50.0)}
    assert product_order_ids(ids, scores) == ['C', 'B', 'E', 'A', 'D']


def test_conflict_block_sits_between_scored_and_held():
    ids = ['A', 'B', 'C']
    conflict = [ConstraintResult(kind=ConstraintKind.EXPERIENCE, state=ConstraintState.EXPLICIT_CONFLICT)]
    scores = {'A': s(90.0), 'B': s(60.0), 'C': held_score('failed')}
    assert product_order_ids(ids, scores, {'A': conflict}) == ['B', 'A', 'C']


def test_every_candidate_needs_an_explicit_score_object():
    with pytest.raises(ValueError):
        product_order_ids(['A', 'B'], {'A': s(10.0)})


def test_metrics_hand_computed():
    # Final order: C(rel 3), B(rel 0), A(held, rel 2). Pool: A=2, B=0, C=3.
    ids = ['A', 'B', 'C']
    scores = {'A': held_score('failed'), 'B': s(40.0), 'C': s(70.0)}
    judgments = {'A': 2, 'B': 0, 'C': 3}
    out = product_order_metrics(ids, scores, judgments, eligible_ids=ids)
    assert out['order'] == ['C', 'B', 'A'] and out['unscored_ids'] == ['A']
    assert out['strict_D052_complete'] is False
    dcg = 7 / math.log2(2) + 0 + 3 / math.log2(4)
    ideal = 7 / math.log2(2) + 3 / math.log2(3)
    # only three returned positions exist, so P@5 and NDCG@10 are unavailable (short list)
    assert out['p_at_5'] is None and out['ndcg_at_10'] is None
    ten = ids + [f'X{i}' for i in range(7)]
    scores.update({f'X{i}': s(10.0 - i) for i in range(7)})
    judgments.update({f'X{i}': 0 for i in range(7)})
    out = product_order_metrics(ten, scores, judgments, eligible_ids=ten)
    assert out['order'][:3] == ['C', 'B', 'X0'] and out['order'][-1] == 'A'
    assert out['p_at_5'] == pytest.approx(1 / 5)
    dcg = 7 / math.log2(2) + 3 / math.log2(11)
    assert out['ndcg_at_10'] == pytest.approx(dcg / ideal)


def test_unjudged_job_in_final_top10_makes_metric_unavailable():
    ids = [f'J{i}' for i in range(10)]
    scores = {j: s(100.0 - i) for i, j in enumerate(ids)}
    judgments = {j: 1 for j in ids[1:]}
    out = product_order_metrics(ids, scores, judgments, eligible_ids=ids)
    assert out['ndcg_at_10'] is None and out['unjudged_final_top10'] == ['J0']
