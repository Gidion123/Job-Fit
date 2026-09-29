"""Runs the 8 development fixtures in evals/fixtures against the deterministic rules."""
import json
from datetime import date
from pathlib import Path

import pytest

from jobfit.matching.constraints import experience_constraint, experience_years
from jobfit.schemas.analysis import BranchAssessment, CheckStatus, EvidenceLabel, UnitAssessment
from jobfit.schemas.cv import ExperienceEntry, ParseStatus
from jobfit.schemas.requirements import JDExtraction
from jobfit.scoring.score import compute_score, merge_duplicate_units, resolve_alternative_group

FIXTURES = sorted((Path(__file__).resolve().parents[1] / "evals" / "fixtures").glob("dev_*.json"))


def load(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    extraction = JDExtraction.model_validate(d["extraction"])
    assessments = [UnitAssessment.model_validate(a) for a in d["assessments"]]
    return d, extraction, assessments


def test_eight_fixtures_exist():
    assert len(FIXTURES) == 8


@pytest.mark.parametrize("path", FIXTURES, ids=[p.stem for p in FIXTURES])
def test_fixture_score(path):
    d, extraction, assessments = load(path)
    exp = d["expected"]
    result = compute_score(extraction, assessments, ParseStatus(d["cv_parse_status"]))
    assert result.status.value == exp["status"]
    assert result.required_total == exp["required_total"]
    if exp["score_pct"] is None:
        assert result.score_pct is None
    else:
        assert result.score_pct == pytest.approx(exp["score_pct"], abs=0.01)
    for key in ("matched", "partial", "unknown_importance_total", "preferred_total", "preferred_met", "met_display"):
        if key in exp:
            assert getattr(result, key) == exp[key], key


@pytest.mark.parametrize("path", FIXTURES, ids=[p.stem for p in FIXTURES])
def test_fixture_experience_constraint(path):
    d, _, _ = load(path)
    exp = d["experience"]
    entries = [ExperienceEntry.model_validate(e) for e in exp["cv_entries"]]
    years = experience_years(entries, date.fromisoformat(d["analysis_date"]))
    assert experience_constraint(exp["min_years"], years).state.value == d["expected"]["constraint_state"]


def test_repeated_requirement_keeps_all_quotes():
    d, extraction, _ = load(next(p for p in FIXTURES if "repeated" in p.stem))
    units, merged = merge_duplicate_units(extraction.units)
    sql = next(u for u in units if u.unit_id == "u1")
    assert len(sql.source_quotes) == d["expected"]["merged_quotes_for_u1"]
    assert merged == {"u3": "u1"}


def test_cv_parse_failure_puts_score_on_hold():
    _, extraction, assessments = load(FIXTURES[0])
    assert compute_score(extraction, assessments, ParseStatus.FAILED).status.value == "on_hold"


def test_incomplete_jd_puts_score_on_hold():
    _, extraction, assessments = load(FIXTURES[0])
    extraction.jd_quality = "looks_incomplete"
    assert compute_score(extraction, assessments).status.value == "on_hold"


def test_missing_assessment_is_not_no_match():
    _, extraction, assessments = load(FIXTURES[0])
    result = compute_score(extraction, assessments[:-1])
    assert result.status.value == "on_hold" and result.score_pct is None


def B(label, status=CheckStatus.DONE, quote="q"):
    return BranchAssessment(branch_id="b", label=label, check_status=status, cv_quotes=[quote] if label else [])


@pytest.mark.parametrize(
    "branches, expected",
    [
        ([B(EvidenceLabel.MATCH), B(None, CheckStatus.FAILED)], EvidenceLabel.MATCH),
        ([B(EvidenceLabel.PARTIAL), B(EvidenceLabel.NO_MATCH)], EvidenceLabel.PARTIAL),
        ([B(EvidenceLabel.NO_MATCH), B(EvidenceLabel.NO_MATCH)], EvidenceLabel.NO_MATCH),
        ([B(EvidenceLabel.NO_MATCH), B(None, CheckStatus.FAILED)], None),  # cannot be determined yet
        ([B(EvidenceLabel.PARTIAL), B(None, CheckStatus.FAILED)], None),  # not final
    ],
)
def test_alternative_group_table(branches, expected):
    label, _ = resolve_alternative_group(branches)
    assert label == expected


def test_overlapping_experience_not_counted_twice():
    entries = [
        ExperienceEntry(title="A", start=date(2025, 1, 1), end=date(2025, 12, 31)),
        ExperienceEntry(title="B", start=date(2025, 7, 1), end=date(2026, 6, 30)),
    ]
    assert experience_years(entries, date(2026, 9, 29)) == 1.5
