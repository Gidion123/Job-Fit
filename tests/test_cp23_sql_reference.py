"""Check that the D-067 example interpretation does not become an AND rule."""
from jobfit.matching.guardrails import apply_guardrails


def test_postgresql_example_is_not_a_second_required_tool():
    cv = "## Pengalaman\nWrote SQL queries in BigQuery to build weekly reports."
    assessment = {"unit_id": "P52-U10", "label": "MATCH",
                  "cv_quotes": ["Wrote SQL queries in BigQuery to build weekly reports."],
                  "branches": []}
    old, old_flags = apply_guardrails(
        {"text": "SQL/PostgreSQL", "branches": []}, assessment, cv)
    new, new_flags = apply_guardrails(
        {"text": "SQL (PostgreSQL example)", "branches": []}, assessment, cv)
    assert old["label"] == "PARTIAL"
    assert old_flags[0]["flags"] == ["partial_item_coverage"]
    assert new["label"] == "MATCH"
    assert new_flags == []
