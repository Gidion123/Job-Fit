"""Production retrieval for the real-CV Find Jobs flow (CP3, D-097 adapter 4, D-103 search stage).

Only the production contract is used: active, canonical, target-role jobs from the production
database (0002 lifecycle columns), the current embedding of the frozen embedding profile for every
eligible job, and the frozen hybrid retriever (FTS + dense, RRF) restricted to those ids. There is
**no fallback to the CP1 development split**: a missing seed, an incomplete or incompatible index,
a missing tokenizer or an integrity mismatch fails closed as ``production_retrieval_unavailable``.

Optional preferences (D-010 ``JobFilters``) keep the UNKNOWN behaviour. Target role is a preference
for local refinement, not a strict pre-filter (Find Jobs clarification, 8 Oct): it is dropped
before retrieval and returned as card metadata. Each result carries the lightweight metadata that
local filtering needs, so no per-job request is required. Results are retrieval-stage relevant
jobs, never JobFit match rankings.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date

ELIGIBLE_SQL = ("SELECT job_id, title, company, role_family, role_group, country_code, city_normalized, "
                "analysis_geo, work_mode, experience_bucket, posted_at, apply_url FROM jobs "
                "WHERE is_active AND dedupe_status = 'canonical' AND role_group = 'target' ORDER BY job_id")
INDEXED_SQL = ('SELECT count(DISTINCT e.job_id) FROM job_embedding_versions e JOIN jobs j ON j.job_id = e.job_id '
               'WHERE e.profile_id = %s AND e.model = %s AND e.dimensions = %s AND e.preprocessing_version = %s '
               'AND e.content_hash = j.content_hash AND e.job_id = ANY(%s)')
COLUMNS = ('job_id', 'title', 'company', 'role_family', 'role_group', 'country_code', 'city_normalized',
           'analysis_geo', 'work_mode', 'experience_bucket', 'posted_at', 'apply_url')
UNAVAILABLE = 'production_retrieval_unavailable'


class ProductionRetrievalUnavailable(RuntimeError):
    """Fail closed; ``code`` is safe to show. Never falls back to development data."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.code = UNAVAILABLE
        self.reason = reason


def eligible_jobs(conn) -> list[dict]:
    try:
        rows = conn.execute(ELIGIBLE_SQL).fetchall()
    except Exception:
        raise ProductionRetrievalUnavailable('production schema unavailable') from None
    if not rows:
        raise ProductionRetrievalUnavailable('no eligible production jobs (seed missing)')
    return [dict(zip(COLUMNS, row)) for row in rows]


def check_index(conn, spec, job_ids) -> None:
    """Every eligible job needs a current embedding of exactly the frozen profile."""
    try:
        (count,) = conn.execute(INDEXED_SQL, (spec.profile_id, spec.model, spec.dimensions,
                                              spec.preprocessing_version, sorted(job_ids))).fetchone()
    except Exception:
        raise ProductionRetrievalUnavailable('embedding index unavailable') from None
    if count != len(set(job_ids)):
        raise ProductionRetrievalUnavailable('embedding index incomplete or incompatible')


def load_query_tokenizer(spec):
    from jobfit.search.embeddings import ModelTokenizer
    try:
        return ModelTokenizer(spec)
    except Exception:
        raise ProductionRetrievalUnavailable('query tokenizer artifact unavailable') from None


def card_metadata(row: dict) -> dict:
    return {'title': row.get('title'), 'company': row.get('company'), 'role_family': row.get('role_family'),
            'country_code': row.get('country_code'), 'city': row.get('city_normalized'),
            'location': ', '.join(x for x in (row.get('city_normalized'), row.get('country_code')) if x) or None,
            'work_mode': row.get('work_mode'), 'posted_at': row.get('posted_at'), 'url': row.get('apply_url')}


def production_search(conn, cv_skills, query, spec, filters, *, analysis_date: date, depth: int) -> list[dict]:
    """Retrieval-stage results: ``[{'job_id', 'retrieval_rank', 'filter_status', **metadata}]``."""
    from jobfit.recommend.service import hybrid_retriever
    from jobfit.search.filters import JobFilters, filter_jobs
    if not isinstance(analysis_date, date) or depth < 1:
        raise ValueError('analysis_date and a positive depth are required')
    rows = eligible_jobs(conn)
    by_id = {r['job_id']: r for r in rows}
    check_index(conn, spec, by_id)
    pre = replace(filters or JobFilters(), role_family=None)       # target role: preference, not a pre-filter
    filtered = filter_jobs(rows, pre, analysis_date=analysis_date)
    eligible = list(filtered.eligible_ids)
    if not eligible:
        return []
    status = {f.job_id: f.status.value for f in (*filtered.matches, *filtered.unknown)}
    ids = hybrid_retriever(conn, cv_skills, query, spec, job_ids=eligible)(min(depth, len(eligible)))
    if len(ids) != len(set(ids)) or not set(ids) <= set(eligible):
        raise ProductionRetrievalUnavailable('retrieval returned a job outside the eligible production set')
    return [{'job_id': job_id, 'retrieval_rank': rank, 'filter_status': status[job_id],
             **card_metadata(by_id[job_id])} for rank, job_id in enumerate(ids, 1)]
