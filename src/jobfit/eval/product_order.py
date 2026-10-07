"""Development order metrics on the real product order (D-073).

The product shows scored jobs first, by match percentage, ties in stage-1 order;
jobs with an explicit conflict next; and jobs that could not be fully analyzed
last, in stage-1 order (System Design v1.3 section 9, D-013, scoring/ranking.py).
This module builds exactly that list and scores it with the D-052 original-position
metrics. A held or failed job is never skipped, never given a zero relevance and
never replaced by a lower-ranked job: it simply sits in the last block, where the
user would see it.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from jobfit.eval.metrics import ranking_metrics
from jobfit.schemas.analysis import ConstraintResult, JobAnalysis, ScoreResult, ScoreStatus
from jobfit.scoring.ranking import SCORED, order_group


def product_order_ids(stage1_ids: Sequence[str], scores: Mapping[str, ScoreResult],
                      constraints: Mapping[str, list[ConstraintResult]] | None = None) -> list[str]:
    """Return the product order for the analyzed candidates (stage-1 top K)."""
    ids = list(stage1_ids)
    if len(ids) != len(set(ids)):
        raise ValueError('Candidate identities must be unique')
    if set(scores) != set(ids):
        raise ValueError('Every candidate needs a score object, including an explicit hold')
    constraints = constraints or {}
    analyses = [JobAnalysis(job_id=job, stage1_rank=rank, score=scores[job],
                            constraints=constraints.get(job, []))
                for rank, job in enumerate(ids, 1)]
    group = order_group(analyses)
    return [a.job_id for a in group.no_conflict + group.has_conflict + group.not_fully_analyzed]


def held_score(reason: str) -> ScoreResult:
    """Explicit hold for a candidate whose extraction or matching did not finish."""
    return ScoreResult(status=ScoreStatus.ON_HOLD, reasons=[reason])


def product_order_metrics(stage1_ids: Sequence[str], scores: Mapping[str, ScoreResult],
                          judgments: Mapping[str, int], *, eligible_ids: Sequence[str],
                          constraints: Mapping[str, list[ConstraintResult]] | None = None) -> dict:
    order = product_order_ids(stage1_ids, scores, constraints)
    unscored = [j for j in stage1_ids if scores[j].status not in SCORED]
    p5 = ranking_metrics(order, dict(judgments), eligible_ids=list(eligible_ids), k=5)
    n10 = ranking_metrics(order, dict(judgments), eligible_ids=list(eligible_ids), k=10)
    return {
        'protocol': 'D-073_product_order_holds_last',
        'order': order,
        'candidate_count': len(order),
        'unscored_count': len(unscored),
        'unscored_ids': unscored,
        'unscored_in_final_top10': [j for j in order[:10] if j in unscored],
        'strict_D052_complete': not unscored,
        'p_at_5': p5['precision_at_k']['value'],
        'ndcg_at_10': n10['ndcg_at_k'],
        'p5_reason': p5['precision_at_k'].get('reason'),
        'ndcg_reason': n10['ndcg_reason'],
        'unjudged_final_top10': n10['coverage']['unjudged_original_top_k_ids'],
    }
