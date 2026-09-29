"""Constraint states: compatible / unknown / explicit conflict (System Design v1.3, sections 7 and 9).

"No known conflict" is not "compatible". Missing information gives UNKNOWN.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from jobfit.schemas.analysis import ConstraintKind, ConstraintResult, ConstraintState
from jobfit.schemas.cv import ExperienceEntry


def _month_index(d: date) -> int:
    return d.year * 12 + (d.month - 1)


def experience_years(entries: Iterable[ExperienceEntry], analysis_date: date) -> float | None:
    """Total years across the given entries, without counting overlapping months twice.

    "Present/sekarang" uses analysis_date. If any entry has no start date, or no end date and is not
    marked present, the total is unknown (None): incomplete dates are not turned into false precision.
    Month granularity: an entry from Aug 2025 to Jul 2026 counts as 12 months.
    """
    months: set[int] = set()
    items = list(entries)
    if not items:
        return None
    for e in items:
        if e.start is None:
            return None
        end = analysis_date if e.is_present else e.end
        if end is None:
            return None
        months.update(range(_month_index(e.start), _month_index(end) + 1))
    return round(len(months) / 12, 2)


def experience_constraint(min_years: float | None, cv_years: float | None) -> ConstraintResult:
    kind = ConstraintKind.EXPERIENCE
    if min_years is None:
        return ConstraintResult(kind=kind, state=ConstraintState.UNKNOWN, message="The JD states no experience minimum")
    if cv_years is None:
        return ConstraintResult(
            kind=kind, state=ConstraintState.UNKNOWN, message="The CV has no complete dates for the relevant work"
        )
    if cv_years >= min_years:
        return ConstraintResult(
            kind=kind,
            state=ConstraintState.COMPATIBLE,
            message=f"The JD asks for at least {min_years:g} years; the CV shows about {cv_years:g}",
        )
    return ConstraintResult(
        kind=kind,
        state=ConstraintState.EXPLICIT_CONFLICT,
        message=f"The JD asks for at least {min_years:g} years; the CV shows about {cv_years:g}",
    )


def location_constraint(
    job_country: str | None, is_remote: bool | None, confirmed_location: str | None
) -> ConstraintResult:
    """Checked only against a location the user confirmed (never the CV suggestion by itself)."""
    kind = ConstraintKind.LOCATION
    if not confirmed_location:
        return ConstraintResult(kind=kind, state=ConstraintState.UNKNOWN, message="No confirmed user location")
    if is_remote is None or job_country is None:
        return ConstraintResult(kind=kind, state=ConstraintState.UNKNOWN, message="Job location or work mode missing")
    if job_country.strip().lower() == confirmed_location.strip().lower():
        return ConstraintResult(kind=kind, state=ConstraintState.COMPATIBLE, message=f"Job is in {job_country}")
    if is_remote:
        return ConstraintResult(
            kind=kind, state=ConstraintState.UNKNOWN, message="Remote, but the allowed region is not verified"
        )
    return ConstraintResult(
        kind=kind,
        state=ConstraintState.EXPLICIT_CONFLICT,
        message=f"Onsite job in {job_country}, outside {confirmed_location}",
    )


def work_authorization_constraint(jd_mentions_authorization: bool) -> ConstraintResult | None:
    """v1 does not collect the user's work authorization, so a JD statement is always UNKNOWN."""
    if not jd_mentions_authorization:
        return None
    return ConstraintResult(
        kind=ConstraintKind.WORK_AUTHORIZATION,
        state=ConstraintState.UNKNOWN,
        message="The JD mentions work authorization; your status is not collected",
    )
