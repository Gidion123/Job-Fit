"""Per-requirement results, constraints, and the score (System Design v1.3, sections 7 to 9)."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class EvidenceLabel(str, Enum):
    MATCH = "MATCH"
    PARTIAL = "PARTIAL"
    NO_MATCH = "NO_MATCH"


class CheckStatus(str, Enum):
    DONE = "done"
    NEEDS_CLARIFICATION = "needs_clarification"
    FAILED = "failed"  # system failure, never turned into NO_MATCH


class ConstraintKind(str, Enum):
    EXPERIENCE = "experience"
    LOCATION = "location"
    WORK_AUTHORIZATION = "work_authorization"


class ConstraintState(str, Enum):
    COMPATIBLE = "compatible"
    UNKNOWN = "unknown"
    EXPLICIT_CONFLICT = "explicit_conflict"


class ScoreStatus(str, Enum):
    FINAL = "final"
    PROVISIONAL = "provisional"
    ON_HOLD = "on_hold"
    NO_SCORE = "no_score"


class BranchAssessment(BaseModel):
    branch_id: str
    label: EvidenceLabel | None = None
    check_status: CheckStatus = CheckStatus.DONE
    cv_quotes: list[str] = Field(default_factory=list)


class UnitAssessment(BaseModel):
    unit_id: str
    label: EvidenceLabel | None = None
    check_status: CheckStatus = CheckStatus.DONE
    cv_quotes: list[str] = Field(default_factory=list)  # word for word from the CV
    branches: list[BranchAssessment] = Field(default_factory=list)
    ai_suggested: bool = False

    @model_validator(mode="after")
    def _quote_rule(self) -> "UnitAssessment":
        # Guideline B2: a label without a quote can only be NO_MATCH.
        if self.label in (EvidenceLabel.MATCH, EvidenceLabel.PARTIAL) and not self.cv_quotes and not self.branches:
            raise ValueError("MATCH or PARTIAL needs at least one CV quote")
        if self.check_status == CheckStatus.FAILED and self.label is not None:
            raise ValueError("a failed check cannot carry an evidence label")
        return self


class ConstraintResult(BaseModel):
    kind: ConstraintKind
    state: ConstraintState
    message: str = ""


class ScoreResult(BaseModel):
    score_pct: float | None = None
    status: ScoreStatus
    matched: int = 0
    partial: int = 0
    required_total: int = 0  # the denominator
    preferred_met: int = 0
    preferred_total: int = 0
    unknown_importance_total: int = 0
    reasons: list[str] = Field(default_factory=list)

    @property
    def weighted_points(self) -> float:
        return self.matched + 0.5 * self.partial

    @property
    def met_display(self) -> str:
        """The "x of y" text shown next to every score (5 MATCH + 2 PARTIAL of 10 -> "6 of 10")."""
        return f"{self.weighted_points:g} of {self.required_total} required requirements"


class JobAnalysis(BaseModel):
    job_id: str
    stage1_rank: int = Field(ge=1)  # internal order from search, used only as a tie-break
    score: ScoreResult
    constraints: list[ConstraintResult] = Field(default_factory=list)

    @property
    def overall_constraint_state(self) -> ConstraintState:
        states = {c.state for c in self.constraints}
        if ConstraintState.EXPLICIT_CONFLICT in states:
            return ConstraintState.EXPLICIT_CONFLICT
        if not states or ConstraintState.UNKNOWN in states:
            return ConstraintState.UNKNOWN  # "no known conflict" is not "compatible"
        return ConstraintState.COMPATIBLE
