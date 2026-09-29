from jobfit.schemas.analysis import ConstraintKind, ConstraintResult, ConstraintState, JobAnalysis, ScoreResult, ScoreStatus
from jobfit.scoring.ranking import order_group


def job(jid, rank, pct, status=ScoreStatus.FINAL, conflict=False):
    state = ConstraintState.EXPLICIT_CONFLICT if conflict else ConstraintState.COMPATIBLE
    return JobAnalysis(
        job_id=jid, stage1_rank=rank,
        score=ScoreResult(score_pct=pct, status=status, required_total=4),
        constraints=[ConstraintResult(kind=ConstraintKind.EXPERIENCE, state=state)],
    )


def test_order_by_score_then_conflict_block_then_unscored():
    jobs = [
        job("A", 1, 60.0),
        job("B", 2, 90.0, conflict=True),
        job("C", 3, 75.0, status=ScoreStatus.PROVISIONAL),
        job("D", 4, None, status=ScoreStatus.ON_HOLD),
        job("E", 5, 80.0),
        job("F", 6, None, status=ScoreStatus.NO_SCORE),
    ]
    assert order_group(jobs).job_ids() == {
        "no_conflict": ["E", "C", "A"],
        "has_conflict": ["B"],
        "not_fully_analyzed": ["D", "F"],
    }


def test_tie_keeps_stage1_order_not_more_requirements():
    a = job("A", 2, 75.0)
    b = job("B", 1, 75.0)
    a.score.required_total = 12  # more requirements met must not win the tie (H8)
    assert order_group([a, b]).job_ids()["no_conflict"] == ["B", "A"]
