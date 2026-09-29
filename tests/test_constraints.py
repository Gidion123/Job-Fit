"""Constraint states (System Design v1.3, sections 7 and 9)."""
from datetime import date

from jobfit.matching.constraints import (
    experience_constraint,
    experience_years,
    location_constraint,
    work_authorization_constraint,
)
from jobfit.schemas.analysis import ConstraintState
from jobfit.schemas.cv import ExperienceEntry

TODAY = date(2026, 9, 29)


def test_present_uses_analysis_date():
    e = [ExperienceEntry(title="Junior ML Engineer", start=date(2025, 8, 1), is_present=True)]
    assert experience_years(e, TODAY) == round(14 / 12, 2)


def test_missing_dates_give_unknown_not_zero():
    e = [ExperienceEntry(title="Project with no dates")]
    assert experience_years(e, TODAY) is None
    assert experience_constraint(2, None).state == ConstraintState.UNKNOWN


def test_too_short_is_explicit_conflict():
    assert experience_constraint(3, 1.2).state == ConstraintState.EXPLICIT_CONFLICT
    assert experience_constraint(1, 1.2).state == ConstraintState.COMPATIBLE


def test_location_needs_confirmed_location():
    assert location_constraint("Indonesia", False, None).state == ConstraintState.UNKNOWN
    assert location_constraint("Indonesia", False, "indonesia").state == ConstraintState.COMPATIBLE
    assert location_constraint("Singapore", False, "Indonesia").state == ConstraintState.EXPLICIT_CONFLICT
    assert location_constraint("Singapore", True, "Indonesia").state == ConstraintState.UNKNOWN
    assert location_constraint(None, None, "Indonesia").state == ConstraintState.UNKNOWN


def test_work_authorization_is_always_unknown_when_mentioned():
    assert work_authorization_constraint(False) is None
    assert work_authorization_constraint(True).state == ConstraintState.UNKNOWN
