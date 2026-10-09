"""One-time production corpus seed on real PostgreSQL (disposable scratch databases only).

Auditable-only source with exact id-set equality; pristine-state refusal (never repair); the seed-time
timestamp fallback shared by the job and its canonical job_sources row; dry-run; read-only verify
including the embedding index; and retrieval of exactly the seeded active target rows.
"""
import json
import os
from datetime import datetime, timezone

import psycopg
import pytest

from jobfit.db import seed_production as sp
from jobfit.search import production
from jobfit.search.embedding_store import JobEmbeddingStore
from jobfit.search.embeddings import prepare
from tests.test_live_runtime_db import ADMIN, alembic_config, baseline, command
from tests.test_production_retrieval_db import DAY, QUERY, SPEC, Tok

pytestmark = pytest.mark.skipif(os.environ.get('JOBFIT_MIGRATION_TESTS') != '1' or not ADMIN,
                                reason='requires JOBFIT_MIGRATION_TESTS=1 and a disposable pgvector server')
EXPECTED = {'jobs': 5, 'active_target': 3, 'inactive_non_target': 2}
VALID = ('2026-09-26T03:43:06+00:00', '2026-09-26T04:43:17+00:00')
FEATURES = [  # job_id, role_group, first_seen_at, last_seen_at, auditable
    ('T1', 'target', *VALID, True),
    ('T2', 'target', None, None, True),                          # missing: seed-time fallback
    ('T3', 'target', 'not-a-date', VALID[1], True),             # invalid: seed-time fallback
    ('N1', 'non_target', *VALID, True),
    ('N2', 'non_target', VALID[0], None, True),                  # half missing: fallback
    ('X1', 'target', *VALID, False),                             # not auditable: never used
]


def write_features(path, rows=FEATURES):
    with open(path, 'w', encoding='utf-8') as f:
        for job_id, group, first, last, auditable in rows:
            f.write(json.dumps({'final_cluster_id': job_id, 'role_group': group, 'first_seen_at': first,
                                'last_seen_at': last, 'is_auditable': auditable, 'source_provider': 'jsearch',
                                'source_job_id': f'src-{job_id}'}) + '\n')
    return path


def insert_jobs(conn, ids):
    groups = {r[0]: r[1] for r in FEATURES}
    for job_id in ids:
        conn.execute("INSERT INTO jobs (job_id, content_hash, snapshot_id, title, company, description_clean, "
                     "role_group, role_family, country_code, analysis_geo) VALUES (%s, 'current', 'fixture', %s, "
                     "'Acme', 'python sql pipelines', %s, %s, 'ID', 'indonesia')",
                     (job_id, f'Engineer {job_id}', groups.get(job_id, 'target'),
                      'data_science' if groups.get(job_id, 'target') == 'target' else None))
    targets = [j for j in ids if groups.get(j, 'target') == 'target']
    JobEmbeddingStore(conn, 'fixture').save_batch(
        SPEC, [(prepare(j, 'python sql ' + j, SPEC, Tok(), 'current'), [1.0, 0.0]) for j in targets])


@pytest.fixture
def db(tmp_path):
    """A scratch database at 0002 with the five auditable fixture jobs (pristine lifecycle)."""
    with baseline.scratch_database(ADMIN) as url:
        command.upgrade(alembic_config(url), 'head')
        with psycopg.connect(url, autocommit=True) as c:
            insert_jobs(c, ['T1', 'T2', 'T3', 'N1', 'N2'])
        yield url, sp.read_features(write_features(tmp_path / 'features.jsonl'))


def run_seed(url, features, **kw):
    with psycopg.connect(url) as conn:
        return sp.seed(conn, features, expected=EXPECTED, **kw)


def lifecycle(url):
    with psycopg.connect(url) as c:
        jobs = {r[0]: r[1:] for r in c.execute('SELECT job_id, is_active, first_seen_at, last_seen_at, '
                                               'inactive_since, dedupe_status FROM jobs').fetchall()}
        sources = {r[2]: r for r in c.execute('SELECT source, source_job_id, job_id, first_seen_at, last_seen_at '
                                              'FROM job_sources').fetchall()}
    return jobs, sources


def test_only_auditable_rows_are_the_source():
    rows = sp.read_features(sp.FEATURES)
    assert len(rows) == 632 and sum(r['role_group'] == 'target' for r in rows.values()) == 428
    fallback = [j for j, r in rows.items() if sp.effective_seen(r, datetime.now(timezone.utc))[2]]
    assert len(fallback) == 6 and sum(rows[j]['role_group'] == 'target' for j in fallback) == 5


def test_the_seed_activates_targets_and_uses_one_seed_time_for_every_fallback(db):
    url, features = db
    report = run_seed(url, features)
    assert report['legacy_seen_timestamp_fallback'] == {'total': 3, 'target': 2, 'non_target': 1}
    assert report['counts']['active_target'] == 3 and report['counts']['inactive_non_target'] == 2
    jobs, sources = lifecycle(url)
    seed_time = datetime.fromisoformat(report['seed_time'])
    assert jobs['T1'][1:3] == (datetime.fromisoformat(VALID[0]), datetime.fromisoformat(VALID[1]))   # kept exactly
    for job_id in ('T2', 'T3', 'N2'):
        assert jobs[job_id][1] == jobs[job_id][2] == seed_time            # entered the lifecycle at seed time
    assert {j for j, r in jobs.items() if r[0]} == {'T1', 'T2', 'T3'}
    assert all(r[3] is None and r[4] == 'canonical' for r in jobs.values())
    assert set(sources) == set(jobs) and 'X1' not in sources
    for job_id, (source, source_job_id, _, first, last) in sources.items():
        assert (source, source_job_id) == ('jsearch', f'src-{job_id}')
        assert first is not None and last >= first and (first, last) == jobs[job_id][1:3]   # same effective times
    with psycopg.connect(url) as c:
        problems, counts = sp.verify_problems(c, features, SPEC, expected=EXPECTED)
    assert problems == [] and counts['eligible_indexed'] == 3


def test_dry_run_reports_and_changes_nothing(db):
    url, features = db
    before = lifecycle(url)
    report = run_seed(url, features, dry_run=True)
    assert report['dry_run'] is True and report['legacy_seen_timestamp_fallback']['total'] == 3
    assert lifecycle(url) == before


def test_refused_before_0002(tmp_path):
    with baseline.scratch_database(ADMIN) as url:
        command.upgrade(alembic_config(url), '0001')
        features = sp.read_features(write_features(tmp_path / 'f.jsonl'))
        with pytest.raises(sp.SeedRefused, match='expected 0002'):
            run_seed(url, features)


@pytest.mark.parametrize('rows', [FEATURES[:-2], FEATURES + [('T9', 'target', *VALID, True)]])
def test_refused_when_the_ids_differ_from_the_auditable_features(db, tmp_path, rows):
    url, _ = db
    features = sp.read_features(write_features(tmp_path / 'other.jsonl', rows))
    with pytest.raises(sp.SeedRefused, match='job ids differ|auditable feature rows'):
        with psycopg.connect(url) as conn:
            sp.seed(conn, features, expected={**EXPECTED, 'jobs': len(features)})


PARTIAL = [
    "UPDATE jobs SET is_active = true, first_seen_at = now(), last_seen_at = now() WHERE job_id = 'T1'",
    "UPDATE jobs SET first_seen_at = now() WHERE job_id = 'T1'",
    "UPDATE jobs SET last_seen_at = now(), first_seen_at = now() WHERE job_id = 'N1'",
    "UPDATE jobs SET inactive_since = now() WHERE job_id = 'N1'",
    "UPDATE jobs SET covered_miss_count = 1 WHERE job_id = 'T2'",
    "UPDATE jobs SET dedupe_status = 'review_required' WHERE job_id = 'N2'",
    "INSERT INTO job_sources VALUES ('jsearch', 'src-T1', 'T1', now(), now())",
    "INSERT INTO sync_runs (status, finished_at, manifest_sha256, code_version) "
    "VALUES ('failed', now(), repeat('a', 64), 'x')",
]


@pytest.mark.parametrize('mutation', PARTIAL)
def test_a_partial_lifecycle_is_refused_and_never_repaired(db, mutation):
    url, features = db
    with psycopg.connect(url, autocommit=True) as c:
        c.execute(mutation)
    before = lifecycle(url)
    with pytest.raises(sp.SeedRefused, match='not pristine'):
        run_seed(url, features)
    assert lifecycle(url) == before


def test_a_second_seed_is_refused(db):
    url, features = db
    run_seed(url, features)
    before = lifecycle(url)
    with pytest.raises(sp.SeedRefused, match='not pristine'):
        run_seed(url, features)
    assert lifecycle(url) == before


@pytest.mark.parametrize('breakage,reason', [
    ("UPDATE jobs SET is_active = false WHERE job_id = 'T1'", 'active target rows'),
    ("UPDATE job_sources SET last_seen_at = last_seen_at + interval '1 day' WHERE job_id = 'T2'",
     'job_sources rows whose timestamps differ'),
    ("UPDATE jobs SET inactive_since = now() WHERE job_id = 'N1'", 'inactive_since set'),
    ("DELETE FROM job_sources WHERE job_id = 'N2'", 'canonical feature identities'),
    ("DELETE FROM job_embedding_versions WHERE job_id = 'T3'", 'embedding index'),
])
def test_verify_reports_every_broken_invariant(db, breakage, reason):
    url, features = db
    run_seed(url, features)
    with psycopg.connect(url, autocommit=True) as c:
        c.execute(breakage)
        problems, _ = sp.verify_problems(c, features, SPEC, expected=EXPECTED)
    assert any(reason in p for p in problems), problems


def test_verify_fails_on_an_unseeded_database(db):
    url, features = db
    with psycopg.connect(url, autocommit=True) as c:
        problems, _ = sp.verify_problems(c, features, SPEC, expected=EXPECTED)
    assert any('active target rows 0' in p for p in problems)
    assert any('no eligible production jobs' in p for p in problems)


def test_production_search_returns_only_the_seeded_active_targets(db):
    url, features = db
    run_seed(url, features)
    with psycopg.connect(url, autocommit=True) as c:
        out = production.production_search(c, {'python', 'sql'}, QUERY, SPEC, None, analysis_date=DAY, depth=30)
    assert {r['job_id'] for r in out} == {'T1', 'T2', 'T3'}
