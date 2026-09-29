"""Deterministic score v0 (System Design v1.3, section 8; DECISIONS D-006).

Required-requirement match = (MATCH + 0.5 x PARTIAL) / required units x 100

This is CV evidence coverage of the required units that were identified.
It is not a chance of being hired and not a measure of real ability.
No model is trained here: the score is a fixed rule.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

from jobfit.schemas.analysis import (
    BranchAssessment,
    CheckStatus,
    EvidenceLabel,
    ScoreResult,
    ScoreStatus,
    UnitAssessment,
)
from jobfit.schemas.cv import ParseStatus
from jobfit.schemas.requirements import Importance, JDExtraction, JDQuality, RequirementUnit, UnitKind

PARTIAL_WEIGHT = 0.5  # hypothesis H-weight, audited on the development set (section 21)

_IMPORTANCE_RANK = {Importance.REQUIRED: 2, Importance.PREFERRED: 1, Importance.UNKNOWN: 0}
_LABEL_RANK = {EvidenceLabel.MATCH: 2, EvidenceLabel.PARTIAL: 1, EvidenceLabel.NO_MATCH: 0}


def _merge_key(unit: RequirementUnit) -> tuple:
    name = unit.normalized_name or unit.text
    name = re.sub(r"\s+", " ", name.strip().lower())
    branches = tuple(sorted(b.text.strip().lower() for b in unit.branches))
    return (unit.kind, name, unit.min_years, branches)


def merge_duplicate_units(units: Iterable[RequirementUnit]) -> tuple[list[RequirementUnit], dict[str, str]]:
    """Count a repeated requirement once and keep all its JD quotes.

    Returns the merged units and a map {dropped unit_id: kept unit_id}.
    If the copies disagree on importance, the stronger one wins (required > preferred > unknown).
    """
    kept: dict[tuple, RequirementUnit] = {}
    merged_into: dict[str, str] = {}
    for unit in units:
        key = _merge_key(unit)
        if key not in kept:
            kept[key] = unit.model_copy(deep=True)
            continue
        base = kept[key]
        merged_into[unit.unit_id] = base.unit_id
        quotes = base.source_quotes + [q for q in unit.source_quotes if q not in base.source_quotes]
        importance = max(base.importance, unit.importance, key=lambda i: _IMPORTANCE_RANK[i])
        kept[key] = base.model_copy(
            update={
                "source_quotes": quotes,
                "importance": importance,
                "needs_review": base.needs_review or unit.needs_review,
            }
        )
    return list(kept.values()), merged_into


def resolve_alternative_group(branches: list[BranchAssessment]) -> tuple[EvidenceLabel | None, CheckStatus]:
    """Section 6 table. A processing failure is never treated as NO_MATCH.

    - any branch MATCH -> MATCH
    - otherwise, if any branch is not judged (failed, or no label) -> cannot be determined yet
    - otherwise the best of PARTIAL / NO_MATCH
    """
    labels = [b.label for b in branches if b.label is not None]
    if EvidenceLabel.MATCH in labels:
        return EvidenceLabel.MATCH, CheckStatus.DONE
    if any(b.label is None for b in branches):
        return None, CheckStatus.FAILED
    best = max(labels, key=lambda lab: _LABEL_RANK[lab])
    status = (
        CheckStatus.NEEDS_CLARIFICATION
        if any(b.check_status == CheckStatus.NEEDS_CLARIFICATION for b in branches)
        else CheckStatus.DONE
    )
    return best, status


def effective_label(unit: RequirementUnit, assessment: UnitAssessment | None) -> tuple[EvidenceLabel | None, CheckStatus]:
    """Final label of a unit. None means the unit could not be judged."""
    if assessment is None:
        return None, CheckStatus.FAILED
    if unit.kind == UnitKind.ALTERNATIVE_GROUP and assessment.branches:
        return resolve_alternative_group(assessment.branches)
    if assessment.check_status == CheckStatus.FAILED:
        return None, CheckStatus.FAILED
    return assessment.label, assessment.check_status


def compute_score(
    extraction: JDExtraction,
    assessments: Iterable[UnitAssessment],
    cv_parse_status: ParseStatus = ParseStatus.OK,
) -> ScoreResult:
    """Apply the section 8 status table, in this order:

    1. CV failed to parse            -> on hold
    2. JD looks incomplete           -> on hold (the user can paste the full JD)
    3. no required unit identified   -> no score
    4. a required unit not judged    -> on hold (it stays in the denominator, never NO_MATCH)
    5. some units importance unknown -> provisional
    6. otherwise                     -> final

    needs_clarification with a label still counts; the clarification question is shown to the user.
    """
    units, _ = merge_duplicate_units(extraction.units)
    by_id = {a.unit_id: a for a in assessments}

    required = [u for u in units if u.importance == Importance.REQUIRED]
    preferred = [u for u in units if u.importance == Importance.PREFERRED]
    unknown_total = sum(1 for u in units if u.importance == Importance.UNKNOWN)

    preferred_met = sum(
        1 for u in preferred if effective_label(u, by_id.get(u.unit_id))[0] == EvidenceLabel.MATCH
    )
    base = {
        "required_total": len(required),
        "preferred_met": preferred_met,
        "preferred_total": len(preferred),
        "unknown_importance_total": unknown_total,
    }

    if cv_parse_status == ParseStatus.FAILED:
        return ScoreResult(status=ScoreStatus.ON_HOLD, reasons=["CV could not be parsed (system failure)"], **base)
    if extraction.jd_quality == JDQuality.LOOKS_INCOMPLETE:
        return ScoreResult(status=ScoreStatus.ON_HOLD, reasons=["JD looks incomplete; paste the full JD"], **base)
    if not required:
        return ScoreResult(status=ScoreStatus.NO_SCORE, reasons=["Not enough information to compute"], **base)

    matched = partial = 0
    not_judged: list[str] = []
    for unit in required:
        label, _status = effective_label(unit, by_id.get(unit.unit_id))
        if label is None:
            not_judged.append(unit.unit_id)
        elif label == EvidenceLabel.MATCH:
            matched += 1
        elif label == EvidenceLabel.PARTIAL:
            partial += 1

    if not_judged:
        return ScoreResult(
            status=ScoreStatus.ON_HOLD,
            matched=matched,
            partial=partial,
            reasons=[f"Required units not judged yet: {', '.join(not_judged)}"],
            **base,
        )

    pct = round((matched + PARTIAL_WEIGHT * partial) / len(required) * 100, 2)
    if unknown_total:
        return ScoreResult(
            score_pct=pct,
            status=ScoreStatus.PROVISIONAL,
            matched=matched,
            partial=partial,
            reasons=[f"{unknown_total} requirement(s) not clearly required or preferred"],
            **base,
        )
    return ScoreResult(score_pct=pct, status=ScoreStatus.FINAL, matched=matched, partial=partial, **base)
