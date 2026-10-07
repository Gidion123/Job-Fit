"""D-071 and D-072 development hold policies. The score formula itself remains score v1.

H1: historic whole-job hold. H2: D-071, kept unchanged for historical receipts.
H2v2: D-072. Like H2, but an unresolved requirement about work experience,
seniority level or education is never removed from the denominator, and a
flag on a unit outside the percentage (preferred, unknown importance, soft
skill, constraint) does not make a score provisional.
"""
from __future__ import annotations

import re

from jobfit.schemas.analysis import ScoreStatus
from jobfit.schemas.requirements import (CONSTRAINT_FIELDS, SEPARATE_FIELDS, Importance, JDExtraction,
                                         RequirementField, RequirementUnit)
from jobfit.scoring.score import compute_score, merge_duplicate_units

HOLD_POLICIES = frozenset({'H1', 'H2', 'H2v2'})
PROTECTED_FIELDS = frozenset({RequirementField.EXPERIENCE_DURATION, RequirementField.EDUCATION})
# Seniority words and year counts. A literal, documented heuristic, not a classifier.
_SENIORITY = re.compile(
    r"\b(senior|sr(?=\.)|principal|tech lead|team lead|leader|manager|head of|director|intermediate|mid[- ]level|"
    r"junior|entry[- ]level|fresh ?graduate|recent graduate|final[- ]year|"
    r"\d+\s*\+?\s*(?:-|to|sampai)?\s*\d*\s*(?:years?|yrs?|tahun))\b", re.I)


def is_protected_unit(unit: RequirementUnit) -> bool:
    """True when the unit states work experience, seniority level or education (D-072)."""
    if unit.field in PROTECTED_FIELDS or unit.min_years is not None:
        return True
    if any(b.field in PROTECTED_FIELDS or b.min_years is not None for b in unit.branches):
        return True
    texts = [unit.text, *(b.text for b in unit.branches)]
    return any(_SENIORITY.search(t or '') for t in texts)


def _scored_required(units):
    return [u for u in units if u.importance == Importance.REQUIRED and
            u.field not in CONSTRAINT_FIELDS and u.field not in SEPARATE_FIELDS]


def _receipt(units):
    return [{'unit_id':u.unit_id,'text':u.text,'reason':'model marked the requirement structure needs_review',
             'importance':u.importance.value,'source_quotes':u.source_quotes} for u in units]


def score_with_hold_policy(extraction: JDExtraction, assessments, *, policy: str = 'H2',
                           partial_weight: float = 0.5):
    """Return (score, excluded-unit receipt) without changing source requirements.

    H1 is the historic whole-job hold. H2 excludes unresolved logical units
    only when at most 20 percent of scored required units are unresolved.
    All H2 scores with exclusions remain provisional. No processing failure is
    converted into NO_MATCH.
    """
    if policy not in HOLD_POLICIES:
        raise ValueError('unknown hold policy')
    assessments=list(assessments)
    if policy=='H2v2':
        return _score_h2v2(extraction,assessments,partial_weight)
    base=compute_score(extraction,assessments,partial_weight=partial_weight)
    merged,duplicates=merge_duplicate_units(extraction.units)
    flagged=[u for u in merged if u.needs_review]
    receipt=[{'unit_id':u.unit_id,'text':u.text,'reason':'model marked the requirement structure needs_review',
              'importance':u.importance.value,'source_quotes':u.source_quotes} for u in flagged]
    if not flagged:
        return base, []
    if policy=='H1':
        return base.model_copy(update={'status':ScoreStatus.ON_HOLD,'score_pct':None,
            'reasons':base.reasons+['Requirement structure needs review; identified denominator is not validated.']}), []
    required=[u for u in merged if u.importance==Importance.REQUIRED and
              u.field not in CONSTRAINT_FIELDS and u.field not in SEPARATE_FIELDS]
    unresolved=[u for u in required if u.needs_review]
    if not required or len(unresolved)/len(required)>.2:
        return base.model_copy(update={'status':ScoreStatus.ON_HOLD,'score_pct':None,
            'reasons':base.reasons+['More than 20 percent of scored required units need checking.']}), []
    flagged_ids={u.unit_id for u in flagged}
    dropped=flagged_ids|{old for old,kept in duplicates.items() if kept in flagged_ids}
    filtered=extraction.model_copy(update={'units':[u for u in extraction.units if u.unit_id not in dropped]})
    scored=compute_score(filtered,assessments,partial_weight=partial_weight)
    if scored.score_pct is None:
        # Other process failures or missing evidence still hold the score.
        return scored, receipt
    return scored.model_copy(update={'status':ScoreStatus.PROVISIONAL,
        'reasons':scored.reasons+['Some requirements need checking; excluded unresolved units are listed separately.']}), receipt


def _score_h2v2(extraction: JDExtraction, assessments, partial_weight: float):
    base=compute_score(extraction,assessments,partial_weight=partial_weight)
    merged,duplicates=merge_duplicate_units(extraction.units)
    required=_scored_required(merged)
    unresolved=[u for u in required if u.needs_review]
    if not unresolved:
        # Flags outside the percentage are shown elsewhere; they do not change status.
        return base, []
    protected=[u for u in unresolved if is_protected_unit(u)]
    if protected:
        ids=', '.join(u.unit_id for u in protected)
        return base.model_copy(update={'status':ScoreStatus.ON_HOLD,'score_pct':None,
            'reasons':base.reasons+[f'An experience, level or education requirement needs checking: {ids}.']}), []
    if len(unresolved)/len(required)>.2:
        return base.model_copy(update={'status':ScoreStatus.ON_HOLD,'score_pct':None,
            'reasons':base.reasons+['More than 20 percent of scored required units need checking.']}), []
    unresolved_ids={u.unit_id for u in unresolved}
    dropped=unresolved_ids|{old for old,kept in duplicates.items() if kept in unresolved_ids}
    filtered=extraction.model_copy(update={'units':[u for u in extraction.units if u.unit_id not in dropped]})
    scored=compute_score(filtered,assessments,partial_weight=partial_weight)
    receipt=_receipt(unresolved)
    if scored.score_pct is None:
        return scored, receipt
    return scored.model_copy(update={'status':ScoreStatus.PROVISIONAL,
        'reasons':scored.reasons+['Some requirements need checking; excluded unresolved units are listed separately.']}), receipt
