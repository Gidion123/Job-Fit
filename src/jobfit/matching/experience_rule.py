"""Experience conflict block for the product order (development candidate, not frozen).

Rule `experience-upper-bound-v1`, the same idea as the CP2.2 vertical slice:
- only a REQUIRED unit with its own `min_years` counts (alternatives stay unknown);
- the CV total is the whole dated work history, without double-counting overlaps;
- the total is used only when the user confirmed the work history is complete;
- if the total is below the minimum, even all of it cannot reach the minimum, so the
  job gets an explicit conflict;
- the total never proves the requirement is met, because the JD usually asks for
  years in a specific role. So above the minimum the state stays unknown.

A conflict does not change the score. It only moves the job to the conflict block
(D-013), between the scored jobs and the held jobs.
"""
from __future__ import annotations

from datetime import date

from jobfit.cv.parser import ParsedCV
from jobfit.matching.constraints import experience_years
from jobfit.schemas.analysis import ConstraintKind, ConstraintResult, ConstraintState
from jobfit.schemas.requirements import Importance, JDExtraction, UnitKind

RULE_VERSION = 'experience-upper-bound-v1'


def experience_conflicts(extraction: JDExtraction, cv: ParsedCV, *, history_confirmed: bool,
                         analysis_date: date | None = None) -> list[ConstraintResult]:
    when = analysis_date or cv.analysis_date
    total = experience_years(cv.profile.experience, when) if history_confirmed else None
    out = []
    for u in extraction.units:
        if u.importance != Importance.REQUIRED or u.min_years is None or u.kind == UnitKind.ALTERNATIVE_GROUP:
            continue
        quote = ' | '.join(u.source_quotes)
        if total is not None and total < u.min_years:
            out.append(ConstraintResult(kind=ConstraintKind.EXPERIENCE, state=ConstraintState.EXPLICIT_CONFLICT,
                message=f'{u.unit_id}: the JD asks for at least {u.min_years:g} years; the whole CV work history '
                        f'is about {total:g} years. JD: {quote}'))
        else:
            reason = ('work history not confirmed as complete' if not history_confirmed
                      else 'dates incomplete' if total is None
                      else 'total history covers it, but years in the asked role are not verified')
            out.append(ConstraintResult(kind=ConstraintKind.EXPERIENCE, state=ConstraintState.UNKNOWN,
                message=f'{u.unit_id}: {reason}. JD: {quote}'))
    return out


def constraint_lookup(cv: ParsedCV, *, history_confirmed: bool):
    """Adapter for recommend(..., constraints=...)."""
    return lambda job_id, extraction: experience_conflicts(extraction, cv, history_confirmed=history_confirmed)
