"""Production retrieval contract on real PostgreSQL (scratch database, fixture rows). No API calls.

Only active, canonical, target-role production jobs with a current embedding of the frozen profile
are retrievable; every optional pre-search filter narrows the eligible pool before retrieval (D-105,
role family included) and keeps UNKNOWN jobs unless asked; results carry the filter-effective metadata
local refinement needs; a missing seed, schema or index fails closed and
nothing falls back to development data.
"""
import os
from dataclasses import replace
from datetime import date

import psycopg
import pytest

from jobfit.search import production
from jobfit.search.dense import QueryEmbedding
from jobfit.search.embedding_store import JobEmbeddingStore
from jobfit.search.embeddings import EmbeddingSpec, prepare
from jobfit.search.filters import JobFilters
from tests.test_live_runtime_db import ADMIN, alembic_config, baseline, command

pytestmark = pytest.mark.skipif(os.environ.get('JOBFIT_MIGRATION_TESTS') != '1' or not ADMIN,
                                reason='requires JOBFIT_MIGRATION_TESTS=1 and a disposable pgvector server')
SPEC = EmbeddingSpec('fixture/model', 2, 'fixture-v1', 1000, 'fixture', '1')
DAY = date(2026, 10, 9)
JOBS = [  # job_id, active, role_group, role_family, country, work_mode, posted_at, vector
    ('P1', True, 'target', 'ai_ml_engineering', 'ID', 'remote', '2026-10-05', [1.0, 0.0]),
    ('P2', True, 'target', 'data_science', 'SG', 'onsite', '2026-10-01', [0.8, 0.6]),
    ('P3', True, 'target', 'genai_llm', None, None, None, [0.6, 0.8]),
    ('N1', False, 'target', 'data_science', 'ID', 'remote', '2026-10-05', [1.0, 0.0]),     # not active
    ('N2', True, 'non_target', None, 'ID', 'remote', '2026-10-05', [1.0, 0.0]),            # not a target role
]


BUCKET = {'P1': 'entry', 'P2': '3-4y'}         # P3 states no experience requirement (unknown)


class Tok:
    def encode(self, text):
        return list(text)


def insert(conn, rows=JOBS, spec=SPEC):
    for job_id, active, group, family, country, mode, posted, _ in rows:
        conn.execute(
            "INSERT INTO jobs (job_id, content_hash, snapshot_id, title, company, description_clean, role_group, "
            "role_family, country_code, city_normalized, analysis_geo, experience_bucket, work_mode, posted_at, "
            "apply_url, is_active, first_seen_at, last_seen_at) VALUES (%s, 'current', 'fixture', %s, 'Acme', "
            "'python sql machine learning pipelines', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now())",
            (job_id, f'Engineer {job_id}', group, family, country, 'Jakarta' if country == 'ID' else None,
             'indonesia' if country == 'ID' else 'foreign' if country else 'unknown', BUCKET.get(job_id), mode,
             posted, f'https://jobs.example/{job_id}', active))
    store = JobEmbeddingStore(conn, 'fixture')
    store.save_batch(spec, [(prepare(r[0], 'python sql ' + r[0], spec, Tok(), 'current'), r[7]) for r in rows])


@pytest.fixture
def conn():
    with baseline.scratch_database(ADMIN) as url:
        command.upgrade(alembic_config(url), 'head')
        with psycopg.connect(url, autocommit=True) as c:
            yield c


QUERY = QueryEmbedding(SPEC.profile_id, [1.0, 0.0])


def search(conn, filters=None, depth=10):
    return production.production_search(conn, {'python', 'sql'}, QUERY, SPEC, filters, analysis_date=DAY,
                                        depth=depth)


def test_only_eligible_production_jobs_are_retrieved_with_their_metadata(conn):
    insert(conn)
    out = search(conn)
    assert {r['job_id'] for r in out} == {'P1', 'P2', 'P3'}
    assert [r['retrieval_rank'] for r in out] == [1, 2, 3]
    p1 = next(r for r in out if r['job_id'] == 'P1')
    assert {k: p1[k] for k in ('role_family', 'country_code', 'city', 'experience_bucket', 'work_mode', 'posted_at',
                               'url')} == {
        'role_family': 'ai_ml_engineering', 'country_code': 'ID', 'city': 'Jakarta', 'experience_bucket': 'entry',
        'work_mode': 'remote', 'posted_at': '2026-10-05', 'url': 'https://jobs.example/P1'}
    assert all(r['filter_status'] == 'matches' for r in out)       # blank filters: no narrowing, no unknown


def test_optional_filters_keep_unknown_jobs_and_role_family_narrows_before_retrieval(conn):
    insert(conn)
    remote = search(conn, JobFilters(work_mode='remote'))
    assert {r['job_id']: r['filter_status'] for r in remote} == {'P1': 'matches', 'P3': 'unknown'}
    strict = search(conn, JobFilters(work_mode='remote', include_unknown=False))
    assert [r['job_id'] for r in strict] == ['P1']
    role = search(conn, JobFilters(role_family='data_science'))
    assert {r['job_id'] for r in role} == {'P2'}                   # D-105: a pre-search filter, never widened


@pytest.mark.parametrize('filters,expected', [
    (JobFilters(country_code='sg'), {'P2': 'matches', 'P3': 'unknown'}),
    (JobFilters(city=' jakarta '), {'P1': 'matches', 'P2': 'unknown', 'P3': 'unknown'}),
    (JobFilters(city=' jakarta ', include_unknown=False), {'P1': 'matches'}),
    (JobFilters(experience_bucket='3-4y'), {'P2': 'matches', 'P3': 'unknown'}),
    (JobFilters(posted_within_days=7), {'P1': 'matches', 'P3': 'unknown'}),
    (JobFilters(posted_within_days=7, include_unknown=False), {'P1': 'matches'}),
    (JobFilters(role_family='genai_llm', experience_bucket='entry'), {'P3': 'unknown'}),
    (JobFilters(role_family='genai_llm', experience_bucket='entry', include_unknown=False), {}),
])
def test_each_pre_search_filter_narrows_the_pool_before_retrieval(conn, filters, expected):
    insert(conn)
    out = search(conn, filters)
    assert {r['job_id']: r['filter_status'] for r in out} == expected
    assert [r['retrieval_rank'] for r in out] == list(range(1, len(out) + 1))


def test_no_seed_fails_closed_and_never_falls_back_to_development_rows(conn):
    insert(conn, [replace_active(r) for r in JOBS])                 # CP1-style rows, nothing active yet
    with pytest.raises(production.ProductionRetrievalUnavailable) as exc:
        search(conn)
    assert exc.value.code == 'production_retrieval_unavailable'


def replace_active(row):
    return (row[0], False, *row[2:])


def test_an_incomplete_or_incompatible_index_fails_closed(conn):
    insert(conn)
    conn.execute("DELETE FROM job_embedding_versions WHERE job_id = 'P2'")
    with pytest.raises(production.ProductionRetrievalUnavailable):
        search(conn)
    with pytest.raises(production.ProductionRetrievalUnavailable):
        production.production_search(conn, {'python'}, QueryEmbedding(SPEC.profile_id, [1.0, 0.0]),
                                      replace(SPEC, preprocessing_version='other'), None, analysis_date=DAY, depth=5)


def test_a_stale_job_text_is_not_indexed(conn):
    insert(conn)
    conn.execute("UPDATE jobs SET content_hash = 'changed' WHERE job_id = 'P3'")
    with pytest.raises(production.ProductionRetrievalUnavailable):
        search(conn)


def test_the_production_schema_is_required():
    with baseline.scratch_database(ADMIN) as url:
        command.upgrade(alembic_config(url), '0001')                 # no lifecycle columns
        with psycopg.connect(url, autocommit=True) as c:
            with pytest.raises(production.ProductionRetrievalUnavailable):
                search(c)


def test_a_retrieved_id_outside_the_eligible_set_fails_closed(conn, monkeypatch):
    insert(conn)
    import jobfit.recommend.service as service
    monkeypatch.setattr(service, 'hybrid_retriever', lambda *a, **kw: (lambda depth: ['P1', 'N1']))
    with pytest.raises(production.ProductionRetrievalUnavailable):
        search(conn)
