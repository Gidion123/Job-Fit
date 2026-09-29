import pytest
from pydantic import ValidationError

from jobfit.schemas.analysis import CheckStatus, ConstraintKind, ConstraintResult, ConstraintState, JobAnalysis, ScoreResult, ScoreStatus, UnitAssessment
from jobfit.schemas.cv import ExperienceEntry
from jobfit.schemas.requirements import JDExtraction, RequirementUnit


def test_alternative_group_needs_two_branches():
    with pytest.raises(ValidationError):
        RequirementUnit(unit_id="g", text="Python or Java", kind="alternative_group", importance="required",
                        branches=[{"branch_id": "a", "text": "Python"}])


def test_qualified_unit_needs_min_years():
    with pytest.raises(ValidationError):
        RequirementUnit(unit_id="q", text="3 years of Python", kind="qualified", importance="required")


def test_unit_ids_unique_within_job():
    unit = {"unit_id": "u1", "text": "SQL", "importance": "required"}
    with pytest.raises(ValidationError):
        JDExtraction(job_id="J", units=[unit, unit])


def test_match_without_quote_is_rejected():
    with pytest.raises(ValidationError):
        UnitAssessment(unit_id="u1", label="MATCH")


def test_failed_check_cannot_have_label():
    with pytest.raises(ValidationError):
        UnitAssessment(unit_id="u1", label="NO_MATCH", check_status=CheckStatus.FAILED)


def test_experience_dates_validated():
    with pytest.raises(ValidationError):
        ExperienceEntry(title="x", start="2026-05-01", end="2026-01-01")


def test_no_constraints_means_unknown_not_compatible():
    a = JobAnalysis(job_id="J", stage1_rank=1, score=ScoreResult(status=ScoreStatus.NO_SCORE))
    assert a.overall_constraint_state == ConstraintState.UNKNOWN
    a.constraints = [ConstraintResult(kind=ConstraintKind.EXPERIENCE, state=ConstraintState.COMPATIBLE),
                     ConstraintResult(kind=ConstraintKind.LOCATION, state=ConstraintState.UNKNOWN)]
    assert a.overall_constraint_state == ConstraintState.UNKNOWN
