"""Production job lifecycle rules on the 0002 schema (D-098), shared by the sync and the retriever.

Retained historical rows (for example the 204 non-target CP1 rows) are seeded inactive with
``inactive_since`` NULL. Only the sync sets ``inactive_since`` when it deactivates a
lifecycle-managed job, so the 60-day hard delete never touches retained rows.
"""
from __future__ import annotations

# Production retrieval: active, canonical, target-role jobs (plus a current embedding, checked by
# the retriever through the frozen dense search). The same vacancy never appears twice.
PRODUCTION_RETRIEVAL_FILTER = "is_active AND dedupe_status = 'canonical' AND role_group = 'target'"
HARD_DELETE_AFTER_DAYS = 60


def hard_delete_expired(conn, now) -> list[str]:
    """Delete lifecycle-managed jobs inactive for more than 60 days at ``now``; return their IDs.

    job_embedding_versions (0001) has no ON DELETE CASCADE, so its rows are deleted first.
    job_sources, job_query_hits and jd_extraction_cache rows cascade with the job.
    """
    ids = [r[0] for r in conn.execute(
        'SELECT job_id FROM jobs WHERE NOT is_active AND inactive_since IS NOT NULL '
        "AND inactive_since < %s - make_interval(days => %s) ORDER BY job_id",
        (now, HARD_DELETE_AFTER_DAYS)).fetchall()]
    if ids:
        conn.execute('DELETE FROM job_embedding_versions WHERE job_id = ANY(%s)', (ids,))
        conn.execute('DELETE FROM jobs WHERE job_id = ANY(%s)', (ids,))
    return ids
