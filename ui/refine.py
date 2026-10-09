"""Refine these results: pure, local filtering of Relevant Jobs already returned by Find Jobs (D-105).

No API call, no provider call, no search: it only chooses which cached cards to display, in their
original retrieval order. It can only narrow the returned set, never widen it; broadening means
changing the pre-search filters and pressing Find Jobs again.

The semantics mirror the frozen D-010 filter (jobfit.search.filters.filter_status), applied to the
filter-effective card metadata the API returns:
- a value that is missing ('', 'unknown', 'not stated', None; 'remote_mentioned' for work mode; a
  posting date after the analysis date) is UNKNOWN and is shown only when ``include_unknown``;
- a known, different value is a conflict and is hidden;
- city is compared stripped and casefolded; country uppercased.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

FIELDS = ('role_family', 'country_code', 'city', 'experience_bucket', 'work_mode')
UNKNOWN_WORDS = {'', 'unknown', 'not_stated', 'not stated'}


def _unknown(value) -> bool:
    return value is None or str(value).strip().lower() in UNKNOWN_WORDS


def _posted(raw) -> date | None:
    if _unknown(raw):
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def _value(card: dict, field: str):
    value = card.get(field)
    if field == 'work_mode' and value == 'remote_mentioned':
        return None
    if _unknown(value):
        return None
    if field == 'city':
        return str(value).strip().casefold()
    if field == 'country_code':
        return str(value).upper()
    return value


def _wanted(field: str, value):
    if field == 'city':
        return value.strip().casefold()
    if field == 'country_code':
        return value.upper()
    return value


def state(card: dict, criteria: dict, *, analysis_date: date | None) -> str:
    """'matches', 'unknown' or 'conflicts' for the active criteria (None or '' = not active)."""
    checks = []
    for field in FIELDS:
        wanted = criteria.get(field)
        if wanted in (None, ''):
            continue
        value = _value(card, field)
        checks.append('unknown' if value is None else 'matches' if value == _wanted(field, wanted) else 'conflicts')
    days = criteria.get('posted_within_days')
    if days:
        posted = _posted(card.get('posted_at'))
        if posted is None or analysis_date is None or posted > analysis_date:
            checks.append('unknown')
        else:
            checks.append('matches' if posted >= analysis_date - timedelta(days=int(days)) else 'conflicts')
    if 'conflicts' in checks:
        return 'conflicts'
    return 'unknown' if 'unknown' in checks else 'matches'


def refine(cards: list[dict], criteria: dict, *, analysis_date: date | None, include_unknown: bool = True) -> list[dict]:
    """The displayed subset, in the original retrieval order; never more than ``cards``."""
    keep = {'matches', 'unknown'} if include_unknown else {'matches'}
    return [c for c in cards if state(c, criteria, analysis_date=analysis_date) in keep]


def options(cards: list[dict], field: str) -> list[str]:
    """The known values present in the returned cards (for the refine dropdowns)."""
    values = {str(card.get(field)).strip() for card in cards if _value(card, field) is not None}
    return sorted(values, key=str.casefold)
