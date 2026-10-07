"""D-066 quote normalization and conservative OR-group repair."""
import pytest

from jobfit.matching.quote_check_v11 import (
    QuoteResolutionError, normalize_assessments_v11, resolve_quote,
)


def test_separator_and_markdown_difference_returns_original_span():
    source = "**S1 Statistika**, Jakarta · Agustus 2022 — Agustus 2026"
    result = resolve_quote("S1 Statistika, Jakarta \x14 Agustus 2022 - Agustus 2026", source)
    assert result["cv_span"] == "S1 Statistika**, Jakarta · Agustus 2022 — Agustus 2026"
    assert "normalized_separators" in result["flags"]
    assert source[result["start"]:result["end"]] == result["cv_span"]


@pytest.mark.parametrize("quote", ["S1 Matematika, Jakarta", "S1 Statistika part Jakarta", "Invented skill"])
def test_changed_or_invented_word_never_matches(quote):
    with pytest.raises(QuoteResolutionError, match="changed_or_invented_word"):
        resolve_quote(quote, "S1 Statistika, Jakarta")


def test_repeated_normalized_source_is_ambiguous():
    with pytest.raises(QuoteResolutionError, match="ambiguous_source_span"):
        resolve_quote("Python — SQL", "Python - SQL in project. Python · SQL in work.")


def test_exact_quote_stays_exact():
    result = resolve_quote("Python (pandas)", "Built with Python (pandas) and SQL.")
    assert result["cv_span"] == result["model_quote"]
    assert result["flags"] == []


def test_c_plus_plus_does_not_match_bare_c():
    with pytest.raises(QuoteResolutionError):
        resolve_quote("C", "C++")


def _unit(*names):
    return {"unit_id": "U1", "branches": [
        {"branch_id": f"B{i}", "text": text} for i, text in enumerate(names, 1)
    ]}


def _group(label="MATCH", quote="Used Python"):
    return {"unit_id": "U1", "label": label, "cv_quotes": [quote],
            "branches": [{"branch_id": "B1", "label": None, "cv_quotes": []},
                         {"branch_id": "B2", "label": None, "cv_quotes": []}]}


def test_parent_moves_only_to_unique_supported_branch():
    rows, flags = normalize_assessments_v11([_group()], [_unit("Python", "SQL")], "Used Python")
    assert rows[0]["label"] is None
    assert rows[0]["branches"][0]["label"] == "MATCH"
    assert rows[0]["branches"][1]["check_status"] == "failed"
    assert any(f["kind"] == "parent_moved_unique_branch" for f in flags)


def test_multiple_or_no_supported_branches_stay_unassessed():
    for quote in ("Used Python and SQL", "Used Looker Studio"):
        with pytest.raises(ValueError, match="ambiguous_parent_group_label"):
            normalize_assessments_v11([_group(quote=quote)], [_unit("Python", "SQL")], quote)


def test_existing_branch_labels_win_over_parent():
    row = _group()
    row["branches"][0] = {"branch_id": "B1", "label": "MATCH", "cv_quotes": ["Used Python"]}
    row["branches"][1] = {"branch_id": "B2", "label": "NO_MATCH", "cv_quotes": []}
    rows, flags = normalize_assessments_v11([row], [_unit("Python", "SQL")], "Used Python")
    assert rows[0]["label"] is None and rows[0]["cv_quotes"] == []
    assert [b["label"] for b in rows[0]["branches"]] == ["MATCH", "NO_MATCH"]
    assert any(f["kind"] == "parent_ignored_branch_labels_present" for f in flags)
