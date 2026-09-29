"""Ordering inside one result group (System Design v1.3, section 9; D-013).

1. Scored jobs without an explicit conflict, by match %, highest first.
2. Scored jobs with an explicit conflict, by match %, in a separate block.
3. Ties keep the stage-1 search order. "More requirements met first" is not used (H8).
Jobs on hold or with no score go to "Could not be fully analyzed", in stage-1 order.
"""
from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel, Field

from jobfit.schemas.analysis import ConstraintState, JobAnalysis, ScoreStatus

SCORED = {ScoreStatus.FINAL, ScoreStatus.PROVISIONAL}


class OrderedGroup(BaseModel):
    no_conflict: list[JobAnalysis] = Field(default_factory=list)
    has_conflict: list[JobAnalysis] = Field(default_factory=list)
    not_fully_analyzed: list[JobAnalysis] = Field(default_factory=list)

    def job_ids(self) -> dict[str, list[str]]:
        return {
            "no_conflict": [a.job_id for a in self.no_conflict],
            "has_conflict": [a.job_id for a in self.has_conflict],
            "not_fully_analyzed": [a.job_id for a in self.not_fully_analyzed],
        }


def _score_key(a: JobAnalysis) -> tuple[float, int]:
    return (-(a.score.score_pct or 0.0), a.stage1_rank)


def order_group(analyses: Iterable[JobAnalysis]) -> OrderedGroup:
    items = list(analyses)
    scored = [a for a in items if a.score.status in SCORED]
    rest = sorted((a for a in items if a.score.status not in SCORED), key=lambda a: a.stage1_rank)
    conflict = [a for a in scored if a.overall_constraint_state == ConstraintState.EXPLICIT_CONFLICT]
    clean = [a for a in scored if a.overall_constraint_state != ConstraintState.EXPLICIT_CONFLICT]
    return OrderedGroup(
        no_conflict=sorted(clean, key=_score_key),
        has_conflict=sorted(conflict, key=_score_key),
        not_fully_analyzed=rest,
    )
