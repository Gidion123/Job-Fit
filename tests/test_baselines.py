"""B0 ranking and the B1 query builder (no database needed); DB load is tested only when a database is reachable."""
import os

import pytest

from jobfit.search import fts, keyword


def test_b0_scores_share_of_job_skills_and_breaks_ties_by_job_id():
    jobs = [
        {"job_id": "F2", "skills_v0": ["python", "sql"]},
        {"job_id": "F1", "skills_v0": ["python", "sql"]},
        {"job_id": "F3", "skills_v0": ["python", "docker", "kubernetes", "aws"]},
        {"job_id": "F4", "skills_v0": []},
    ]
    ranked = keyword.rank({"python", "sql", "docker"}, jobs)
    assert [r["job_id"] for r in ranked] == ["F1", "F2", "F3", "F4"]
    assert ranked[2]["score"] == 0.5 and ranked[3]["score"] == 0.0


def test_b1_query_uses_aliases_and_skips_regex_only_skills():
    phrases = fts.query_phrases({"python", "r", "machine_learning"})
    assert "python" in phrases and "machine learning" in phrases
    assert "r" not in phrases
    query, params = fts.build_query(phrases)
    assert params == phrases


def test_b1_needs_at_least_one_phrase():
    with pytest.raises(ValueError):
        fts.build_query([])


@pytest.mark.skipif(not os.getenv("JOBFIT_DB_TESTS"), reason="set JOBFIT_DB_TESTS=1 with a running database")
def test_snapshot_load_matches_cp1_numbers():
    from jobfit.db.load_snapshot import load, read_candidates
    from jobfit.db.session import connect

    with connect() as conn:
        result = load(conn, read_candidates())
    assert result["loaded"] == 632
    assert result["by_role_group"]["target"] == 428
