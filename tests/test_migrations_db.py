"""Alembic 0001/0002 on real PostgreSQL + pgvector (CP3, D-098). Opt-in; no API calls.

Needs JOBFIT_MIGRATION_TESTS=1 and JOBFIT_MIGRATION_ADMIN_URL, a role that may create databases on
a disposable pgvector server (the CI service). Every test works in its own scratch database, which
is dropped afterwards. Nothing here touches the local CP2 evaluation database.
"""
import json
import os
import threading
import time
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import psycopg
import pytest
from alembic import command

import scripts.db_baseline as baseline
from jobfit.config import REPO_ROOT
from jobfit.db import catalog, lifecycle
from jobfit.db.migrate import alembic_config
from jobfit.db.models import SCHEMA_SQL

ADMIN = os.environ.get('JOBFIT_MIGRATION_ADMIN_URL')
pytestmark = pytest.mark.skipif(os.environ.get('JOBFIT_MIGRATION_TESTS') != '1' or not ADMIN,
                                reason='requires JOBFIT_MIGRATION_TESTS=1 and a disposable pgvector server')
PIN = {r: json.loads((REPO_ROOT / f'migrations/catalog/{r}.json').read_text()) for r in ('0001', '0002')}
T0 = datetime(2026, 10, 8, 3, 0, tzinfo=timezone.utc)
HMAC = 'a' * 64


@pytest.fixture
def db():
    with baseline.scratch_database(ADMIN) as url:
        yield url


def state_and_fingerprint(url):
    return baseline.read_target(url)


def upgrade(url, revision='head'):
    command.upgrade(alembic_config(url), revision)


def cp2(url, *, rows=True):
    """A CP2-shaped database: the unchanged CP2 SCHEMA_SQL, as load_snapshot applies it."""
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(SCHEMA_SQL)
        if rows:
            fill(conn)


def fill(conn):
    for job, text in (('DEV_A', 'python sql'), ('DEV_B', 'python'), ('TEST_C', 'sql')):
        conn.execute('INSERT INTO jobs (job_id, content_hash, snapshot_id, title, description_clean, role_group) '
                     "VALUES (%s, 'current', 'fixture', %s, %s, 'target')", (job, text, text))
    conn.execute("INSERT INTO job_embeddings (job_id, model, content_hash, embedding) "
                 "VALUES ('DEV_A', 'legacy', 'current', %s::vector)", ('[' + ','.join(['0.5'] * 1536) + ']',))


def content(url):
    with psycopg.connect(url) as conn:
        return (conn.execute('SELECT job_id, content_hash, title, description_clean, search::text FROM jobs '
                             'ORDER BY job_id').fetchall(),
                conn.execute('SELECT job_id, model, md5(embedding::text) FROM job_embeddings ORDER BY 1').fetchall(),
                conn.execute('SELECT job_id, md5(embedding::text) FROM job_embedding_versions ORDER BY 1').fetchall())


# --- F1, F2: exact baseline ----------------------------------------------------------------------------

def test_empty_database_upgrades_to_the_pinned_schemas(db):
    upgrade(db, '0001')
    state, fp = state_and_fingerprint(db)
    assert state == '0001' and catalog.compare(PIN['0001'], fp) == []
    upgrade(db, 'head')
    state, fp = state_and_fingerprint(db)
    assert state == '0002' and catalog.compare(PIN['0002'], fp) == []


def test_raw_cp2_schema_sql_equals_alembic_0001_without_the_version_table(db):
    cp2(db, rows=False)
    state, raw = state_and_fingerprint(db)
    assert state == 'absent'
    reference = baseline.reference_fingerprint(ADMIN, '0001')     # has alembic_version, excluded
    assert catalog.compare(reference, raw) == [] and catalog.compare(PIN['0001'], raw) == []


# --- F3, F4: verify and stamp ----------------------------------------------------------------------------

def test_cp2_database_verifies_stamps_and_upgrades_without_touching_rows(db):
    cp2(db)
    before = content(db)
    report = baseline.verify(db)
    assert report['ok'] and report['differences'] == [] and report['revision_state'] == 'absent'
    report = baseline.stamp(db)
    assert report['stamped'] and report['revision_state'] == '0001'
    state, fp = state_and_fingerprint(db)
    assert state == '0001' and catalog.compare(PIN['0001'], fp) == []
    upgrade(db, 'head')
    state, fp = state_and_fingerprint(db)
    assert state == '0002' and catalog.compare(PIN['0002'], fp) == []
    assert content(db) == before
    with psycopg.connect(db) as conn:
        assert conn.execute('SELECT DISTINCT is_active, dedupe_status, covered_miss_count, inactive_since, '
                            'first_seen_at FROM jobs').fetchall() == [(False, 'canonical', 0, None, None)]


VERSION_TABLE = ('CREATE TABLE alembic_version (version_num varchar(32) NOT NULL, '
                 'CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))')
MISMATCHES = {
    'missing_index': 'DROP INDEX jobs_role_group_idx',
    'extra_index': 'CREATE INDEX extra_idx ON jobs (company)',
    'extra_column': 'ALTER TABLE jobs ADD COLUMN extra text',
    'nullability': 'ALTER TABLE jobs ALTER COLUMN title DROP NOT NULL',
    'vector_type': 'ALTER TABLE job_embeddings ALTER COLUMN embedding TYPE vector',
    'dropped_check': 'ALTER TABLE job_embedding_versions DROP CONSTRAINT job_embedding_versions_dimensions_check',
    'changed_default': 'ALTER TABLE jobs ALTER COLUMN loaded_at SET DEFAULT clock_timestamp()',
    'search_not_generated': 'ALTER TABLE jobs DROP COLUMN search; ALTER TABLE jobs ADD COLUMN search tsvector; '
                            'CREATE INDEX jobs_search_idx ON jobs USING gin (search)',
    'fk_action': 'ALTER TABLE job_embeddings DROP CONSTRAINT job_embeddings_job_id_fkey, ADD CONSTRAINT '
                 'job_embeddings_job_id_fkey FOREIGN KEY (job_id) REFERENCES jobs (job_id)',
    'extra_table': 'CREATE TABLE jobs_old (id int)',
    'lookalike_version_table': 'CREATE TABLE alembic_versions (version_num varchar(32))',
    'extra_function': "CREATE FUNCTION extra() RETURNS int LANGUAGE sql AS 'SELECT 1'",
    'empty_version_table': VERSION_TABLE,
    'stamped_version_table': VERSION_TABLE + "; INSERT INTO alembic_version VALUES ('0001')",
    'malformed_version_table': 'CREATE TABLE alembic_version (version_num text)',
}


@pytest.mark.parametrize('name', sorted(MISMATCHES))
def test_any_mismatch_fails_closed_and_is_never_stamped(db, name):
    cp2(db)
    with psycopg.connect(db, autocommit=True) as conn:
        conn.execute(MISMATCHES[name])
    before = state_and_fingerprint(db)
    report = baseline.verify(db)
    assert not report['ok'] and report['differences']
    report = baseline.stamp(db)
    assert report['stamped'] is False
    assert state_and_fingerprint(db) == before                     # nothing written
    if 'version_table' in name and name != 'lookalike_version_table':
        assert report['revision_state'] in {'empty', '0001', 'malformed'}


def test_a_database_without_the_schema_or_the_extension_fails(db):
    report = baseline.verify(db)
    assert not report['ok']
    assert any('/tables/jobs: missing' in d for d in report['differences'])
    assert any(d.startswith('/extensions') for d in report['differences'])


def test_0001_refuses_an_existing_cp2_database(db):
    cp2(db)
    before = state_and_fingerprint(db)
    with pytest.raises(RuntimeError, match='verify and stamp'):
        upgrade(db, '0001')
    assert state_and_fingerprint(db) == before and before[0] == 'absent'   # no version table left behind


# --- F6: the frozen CP2 code works unchanged on 0002 ------------------------------------------------------

class Tokenizer:
    def encode(self, text):
        return list(text)


def retrieval_results(url):
    from jobfit.search import dense, fts, hybrid
    from jobfit.search.embedding_store import JobEmbeddingStore
    from jobfit.search.embeddings import EmbeddingSpec, prepare
    spec = EmbeddingSpec('fixture/model', 2, 'fixture-v1', 100, 'fixture', '1')
    with psycopg.connect(url, autocommit=True) as conn:
        store = JobEmbeddingStore(conn, 'fixture')
        store.save_batch(spec, [(prepare(j, 'python sql ' + j, spec, Tokenizer(), 'current'), v)
                                for j, v in (('DEV_A', [1., 0.]), ('DEV_B', [0., 1.]), ('TEST_C', [1., 1.]))])
        query = dense.QueryEmbedding(spec.profile_id, [1., 0.])
        ids = {'DEV_A', 'DEV_B', 'TEST_C'}
        return (dense.rank(conn, query, spec, job_ids=ids), fts.rank(conn, {'python', 'sql'}, job_ids=ids),
                hybrid.rank(conn, {'python', 'sql'}, query, spec, job_ids=ids, top_k=3))


def test_frozen_retrieval_and_cp2_loader_work_unchanged_on_0002(db):
    from jobfit.db.load_snapshot import COLUMNS, load
    with baseline.scratch_database(ADMIN) as plain:
        cp2(plain)
        expected = retrieval_results(plain)
    cp2(db)
    baseline.stamp(db)
    upgrade(db, 'head')
    assert retrieval_results(db) == expected
    row = {c: None for c in COLUMNS}
    row.update(job_id='NEW_1', content_hash='h', snapshot_id='fixture', title='t', description_clean='d', skills_v0=[])
    with psycopg.connect(db) as conn:
        load(conn, [row])                                   # re-runs SCHEMA_SQL first: must be a no-op
        assert conn.execute("SELECT is_active, dedupe_status FROM jobs WHERE job_id = 'NEW_1'").fetchone() == (
            False, 'canonical')
    state, fp = state_and_fingerprint(db)
    assert state == '0002' and catalog.compare(PIN['0002'], fp) == []


# --- F7: 0002 constraints ---------------------------------------------------------------------------------

@pytest.fixture
def prod(db):
    upgrade(db, 'head')
    with psycopg.connect(db, autocommit=True) as conn:
        fill(conn)
        yield conn


def rejects(conn, sql, params=None):
    with pytest.raises(psycopg.Error):
        with conn.transaction():
            conn.execute(sql, params)


def test_jobs_lifecycle_and_dedupe_constraints(prod):
    rejects(prod, "UPDATE jobs SET is_active = true WHERE job_id = 'DEV_A'")              # never seen
    prod.execute("UPDATE jobs SET first_seen_at = %s, last_seen_at = %s, is_active = true WHERE job_id = 'DEV_A'",
                 (T0, T0))
    rejects(prod, "UPDATE jobs SET dedupe_status = 'review_required' WHERE job_id = 'DEV_A'")   # active suspect
    rejects(prod, "UPDATE jobs SET inactive_since = %s WHERE job_id = 'DEV_A'", (T0,))
    rejects(prod, "UPDATE jobs SET last_seen_at = %s WHERE job_id = 'DEV_A'", (T0 - timedelta(days=1),))
    rejects(prod, "UPDATE jobs SET covered_miss_count = -1 WHERE job_id = 'DEV_A'")
    rejects(prod, "UPDATE jobs SET dedupe_status = 'duplicate' WHERE job_id = 'DEV_B'")
    rejects(prod, "UPDATE jobs SET dedupe_suspect_of = 'DEV_A' WHERE job_id = 'DEV_B'")    # still canonical
    rejects(prod, "UPDATE jobs SET dedupe_status = 'review_required', dedupe_suspect_of = 'DEV_B' WHERE job_id = 'DEV_B'")
    prod.execute("UPDATE jobs SET dedupe_status = 'review_required', dedupe_suspect_of = 'DEV_A' WHERE job_id = 'DEV_B'")


def test_sources_hits_and_sync_run_constraints(prod):
    prod.execute("INSERT INTO job_sources VALUES ('jsearch', 'x1', 'DEV_A', %s, %s)", (T0, T0))
    rejects(prod, "INSERT INTO job_sources VALUES ('jsearch', 'x1', 'DEV_B', %s, %s)", (T0, T0))  # identity is unique
    rejects(prod, "INSERT INTO job_sources VALUES ('', 'x2', 'DEV_B', %s, %s)", (T0, T0))
    rejects(prod, "INSERT INTO job_sources VALUES ('jsearch', 'x3', 'DEV_B', %s, %s)", (T0, T0 - timedelta(1)))
    run = prod.execute("INSERT INTO sync_runs (status, manifest_sha256, code_version) VALUES ('running', %s, 'v') "
                       'RETURNING sync_run_id', ('b' * 64,)).fetchone()[0]
    rejects(prod, "INSERT INTO sync_runs (status, manifest_sha256, code_version) VALUES ('running', %s, 'v')", ('c' * 64,))
    rejects(prod, "INSERT INTO sync_runs (status, manifest_sha256, code_version) VALUES ('succeeded', %s, 'v')", ('c' * 64,))
    rejects(prod, "INSERT INTO sync_runs (status, manifest_sha256, code_version, finished_at) "
                  "VALUES ('failed', 'nothex', 'v', now())")
    rejects(prod, "INSERT INTO sync_runs (status, manifest_sha256, code_version, finished_at, counts) "
                  "VALUES ('failed', %s, 'v', now(), '[]')", ('c' * 64,))
    prod.execute("UPDATE sync_runs SET status = 'succeeded', finished_at = now() WHERE sync_run_id = %s", (run,))
    prod.execute("INSERT INTO job_query_hits VALUES ('DEV_A', 'q1', %s, %s, %s)", (T0, T0, run))
    rejects(prod, "INSERT INTO job_query_hits VALUES ('DEV_A', 'q1', %s, %s, NULL)", (T0, T0))
    rejects(prod, "INSERT INTO live_quota VALUES ('not-a-hmac', now())")


def cache_row(**changes):
    row = dict(cache_key='d' * 64, job_id='DEV_A', content_hash='current', scope='corpus_jd', status='ok',
               value=json.dumps({'job_id': 'DEV_A'}), value_hash='e' * 64, error_code=None, expires_at=None,
               model='deepseek-flash', prompt_version='jd-prompt-v1.4-experimental', created_at=T0)
    row.update(changes)
    return row


def insert_cache(conn, row):
    conn.execute('INSERT INTO jd_extraction_cache (cache_key, job_id, content_hash, scope, status, value, value_hash, '
                 'error_code, expires_at, model, prompt_version, created_at) VALUES (%(cache_key)s, %(job_id)s, '
                 '%(content_hash)s, %(scope)s, %(status)s, %(value)s::jsonb, %(value_hash)s, %(error_code)s, '
                 '%(expires_at)s, %(model)s, %(prompt_version)s, %(created_at)s)', row)


FAILED = dict(status='failed', value=None, value_hash=None, error_code='schema_validation',
              expires_at=T0 + timedelta(days=7))
INVALID_CACHE_ROWS = {
    'ok_value_null': dict(value=None),
    'ok_value_array': dict(value='[]'),
    'ok_value_scalar': dict(value='1'),
    'ok_hash_null': dict(value_hash=None),
    'ok_hash_not_hex': dict(value_hash='E' * 64),
    'ok_hash_short': dict(value_hash='e' * 63),
    'ok_error_code_set': dict(error_code='truncated'),
    'ok_expires_set': dict(expires_at=T0 + timedelta(days=7)),
    'failed_value_set': dict(FAILED, value='{}'),
    'failed_hash_set': dict(FAILED, value_hash='e' * 64),
    'failed_value_and_hash_set': dict(FAILED, value='{}', value_hash='e' * 64),
    'failed_error_code_null': dict(FAILED, error_code=None),
    'failed_error_code_spaces': dict(FAILED, error_code='bad code'),
    'failed_error_code_punctuation': dict(FAILED, error_code='bad-code'),
    'failed_error_code_too_long': dict(FAILED, error_code='a' * 65),
    'failed_error_code_leading_digit': dict(FAILED, error_code='9code'),
    'failed_expires_null': dict(FAILED, expires_at=None),
    'failed_expires_equal': dict(FAILED, expires_at=T0),
    'failed_expires_before': dict(FAILED, expires_at=T0 - timedelta(seconds=1)),
    'other_status': dict(status='pending'),
    'session_scope': dict(scope='session_jd'),
    'key_not_hex': dict(cache_key='D' * 64),
    'key_short': dict(cache_key='d' * 63),
}


@pytest.mark.parametrize('name', sorted(INVALID_CACHE_ROWS))
def test_every_partial_cache_state_is_rejected(prod, name):
    with pytest.raises(psycopg.Error):
        with prod.transaction():
            insert_cache(prod, cache_row(**INVALID_CACHE_ROWS[name]))


def test_complete_cache_states_are_accepted_and_every_stage_failure_code_fits(prod):
    from tests.test_migrations_offline import stage_failure_codes
    insert_cache(prod, cache_row())
    for i, code in enumerate(sorted(stage_failure_codes())):
        insert_cache(prod, cache_row(cache_key=f'{i:064x}', **dict(FAILED, error_code=code)))
    # Negative-cache TTL is testable with a frozen clock: the provider decides freshness from expires_at.
    fresh = 'SELECT count(*) FROM jd_extraction_cache WHERE status = %s AND expires_at > %s'
    assert prod.execute(fresh, ('failed', T0 + timedelta(days=6))).fetchone()[0] == len(stage_failure_codes())
    assert prod.execute(fresh, ('failed', T0 + timedelta(days=8))).fetchone()[0] == 0


RESERVE = ('INSERT INTO budget_reservations (operation_key, phase, reserved_usd, process_id, active_until) '
           "VALUES (%s, %s, %s::numeric, 'p1', now() + interval '1 hour') RETURNING reservation_id")


def reserve(conn, key, usd='0.4716399', phase='parse'):
    return conn.execute(RESERVE, (key, phase, usd)).fetchone()[0]


def test_reservation_amounts_and_states(prod):
    for bad in ('0', '-1', 'NaN', 'Infinity'):
        rejects(prod, RESERVE, ('k', 'parse', bad))
    rejects(prod, RESERVE, ('k', 'embedding', '1'))
    rid = reserve(prod, 'op-1')
    rejects(prod, RESERVE, ('op-1', 'parse', '1'))                                    # idempotency key
    row = prod.execute("SELECT status, settled_usd, closed_at, production_day = (now() AT TIME ZONE 'Asia/Jakarta')::date "
                       'FROM budget_reservations WHERE reservation_id = %s', (rid,)).fetchone()
    assert row == ('reserved', None, None, True)
    rejects(prod, "UPDATE budget_reservations SET status = 'settled' WHERE reservation_id = %s", (rid,))
    rejects(prod, "UPDATE budget_reservations SET status = 'released', settled_usd = 0.01, closed_at = now() "
                  'WHERE reservation_id = %s', (rid,))           # a release must record exactly zero
    rejects(prod, 'UPDATE budget_reservations SET reserved_usd = 0.1 WHERE reservation_id = %s', (rid,))
    rejects(prod, "UPDATE budget_reservations SET settled_usd = 'NaN', status = 'settled', closed_at = now() "
                  'WHERE reservation_id = %s', (rid,))
    rejects(prod, 'DELETE FROM budget_reservations WHERE reservation_id = %s', (rid,))  # open: keeps counting
    prod.execute("UPDATE budget_reservations SET status = 'settled', settled_usd = 0.0123456789, closed_at = now() "
                 'WHERE reservation_id = %s', (rid,))
    assert prod.execute('SELECT settled_usd FROM budget_reservations WHERE reservation_id = %s',
                        (rid,)).fetchone()[0] == Decimal('0.0123456789')
    for change in ("status = 'released', settled_usd = 0", 'settled_usd = 0', 'settled_usd = 1', "status = 'reserved', "
                   'settled_usd = NULL, closed_at = NULL', 'closed_at = now()'):
        rejects(prod, f'UPDATE budget_reservations SET {change} WHERE reservation_id = %s', (rid,))
    zero = reserve(prod, 'op-2', phase='recommendation', usd='84.7704449')
    prod.execute("UPDATE budget_reservations SET status = 'released', settled_usd = 0, closed_at = now() "
                 'WHERE reservation_id = %s', (zero,))
    rejects(prod, "UPDATE budget_reservations SET status = 'settled', settled_usd = 0.5 WHERE reservation_id = %s", (zero,))
    prod.execute('DELETE FROM budget_reservations WHERE reservation_id = %s', (rid,))    # closed rows may be purged
    # The database cannot see the ledger: whether a release is allowed (zero ledger spend and no
    # uncertain upper-bound record) is decided by the Phase 2B runtime before it closes the row.


INSERT_AT = ('INSERT INTO budget_reservations (operation_key, phase, reserved_usd, process_id, created_at, '
             "production_day, active_until) VALUES (%s, 'parse', 1, 'p1', %s, %s, %s) RETURNING reservation_id")


def test_reservation_lifetime_is_required_valid_and_immutable(prod):
    rejects(prod, "INSERT INTO budget_reservations (operation_key, phase, reserved_usd, process_id) "
                  "VALUES ('no-deadline', 'parse', 1, 'p1')")                       # no default: required
    created = datetime(2026, 10, 8, 3, 0, tzinfo=timezone.utc)
    day = date(2026, 10, 8)
    for bad in (created, created - timedelta(seconds=1)):
        rejects(prod, INSERT_AT, ('bad-deadline', created, day, bad))
    rid = prod.execute(INSERT_AT, ('ok', created, day, created + timedelta(minutes=10))).fetchone()[0]
    assert prod.execute('SELECT active_until FROM budget_reservations WHERE reservation_id = %s',
                        (rid,)).fetchone()[0] == created + timedelta(minutes=10)
    for value in (created + timedelta(minutes=20), created + timedelta(minutes=5)):
        rejects(prod, 'UPDATE budget_reservations SET active_until = %s WHERE reservation_id = %s', (value, rid))
    prod.execute("UPDATE budget_reservations SET status = 'settled', settled_usd = 0.2, closed_at = %s "
                 'WHERE reservation_id = %s', (created + timedelta(minutes=1), rid))
    rejects(prod, 'UPDATE budget_reservations SET active_until = %s WHERE reservation_id = %s',
            (created + timedelta(hours=1), rid))


def test_production_day_is_the_jakarta_date_of_created_at(prod):
    rid = reserve(prod, 'default-day')                                      # defaults stay consistent
    assert prod.execute("SELECT production_day = (created_at AT TIME ZONE 'Asia/Jakarta')::date "
                        'FROM budget_reservations WHERE reservation_id = %s', (rid,)).fetchone()[0] is True
    before = datetime(2026, 10, 8, 16, 59, 59, 999999, tzinfo=timezone.utc)   # 23:59:59.999999 WIB, 8 Oct
    after = datetime(2026, 10, 8, 17, 0, 0, tzinfo=timezone.utc)              # 00:00:00 WIB, 9 Oct
    for key, created, good, wrong in (('before', before, date(2026, 10, 8), date(2026, 10, 9)),
                                      ('after', after, date(2026, 10, 9), date(2026, 10, 8))):
        rejects(prod, INSERT_AT, (key + '-wrong', created, wrong, created + timedelta(hours=1)))
        rid = prod.execute(INSERT_AT, (key, created, good, created + timedelta(hours=1))).fetchone()[0]
        assert prod.execute('SELECT production_day FROM budget_reservations WHERE reservation_id = %s',
                            (rid,)).fetchone()[0] == good
        rejects(prod, 'UPDATE budget_reservations SET production_day = %s WHERE reservation_id = %s', (wrong, rid))
    # An explicit past created_at with the default (today's) production_day is inconsistent: rejected.
    old = datetime(2020, 1, 1, tzinfo=timezone.utc)
    rejects(prod, "INSERT INTO budget_reservations (operation_key, phase, reserved_usd, process_id, created_at, "
                  "active_until) VALUES ('stale-default', 'parse', 1, 'p1', %s, %s)", (old, old + timedelta(hours=1)))


def test_job_delete_cascades_except_versioned_vectors(prod):
    prod.execute("INSERT INTO job_sources VALUES ('jsearch', 'c1', 'TEST_C', %s, %s)", (T0, T0))
    prod.execute("INSERT INTO job_query_hits VALUES ('TEST_C', 'q1', %s, %s, NULL)", (T0, T0))
    insert_cache(prod, cache_row(job_id='TEST_C'))
    prod.execute("INSERT INTO job_embedding_versions (job_id, profile_id, model, dimensions, preprocessing_version, "
                 "profile_spec, content_hash, input_hash, input_tokens, original_tokens, truncated, embedding, run_id) "
                 "VALUES ('TEST_C', 'p', 'm', 2, 'v', '{}', 'current', 'i', 1, 1, false, '[1,0]', 'r')")
    rejects(prod, "DELETE FROM jobs WHERE job_id = 'TEST_C'")             # 0001 FK has no cascade
    prod.execute("DELETE FROM job_embedding_versions WHERE job_id = 'TEST_C'")
    prod.execute("DELETE FROM jobs WHERE job_id = 'TEST_C'")
    for table in ('job_sources', 'job_query_hits', 'jd_extraction_cache'):
        assert prod.execute(f"SELECT count(*) FROM {table} WHERE job_id = 'TEST_C'").fetchone()[0] == 0


def test_lifecycle_cleanup_keeps_retained_non_target_rows(prod):
    old = T0 - timedelta(days=365)
    prod.execute('DELETE FROM job_embeddings')
    prod.execute('DELETE FROM jobs')
    for job, group, active, inactive_since in (
            ('NT_1', 'non_target', False, None), ('NT_2', 'adjacent', False, None),          # retained CP1 rows
            ('GONE', 'target', False, T0 - timedelta(days=61)), ('RECENT', 'target', False, T0 - timedelta(days=59)),
            ('LIVE', 'target', True, None)):
        prod.execute('INSERT INTO jobs (job_id, content_hash, snapshot_id, title, description_clean, role_group, '
                     'is_active, first_seen_at, last_seen_at, inactive_since, loaded_at) '
                     "VALUES (%s, 'h', 'fixture', 't', 'd', %s, %s, %s, %s, %s, %s)",
                     (job, group, active, old, old, inactive_since, old))
    prod.execute("INSERT INTO job_sources VALUES ('jsearch', 'g1', 'GONE', %s, %s)", (old, old))
    prod.execute("INSERT INTO job_query_hits VALUES ('GONE', 'q1', %s, %s, NULL)", (old, old))
    insert_cache(prod, cache_row(job_id='GONE'))
    prod.execute("INSERT INTO job_embedding_versions (job_id, profile_id, model, dimensions, preprocessing_version, "
                 "profile_spec, content_hash, input_hash, input_tokens, original_tokens, truncated, embedding, run_id) "
                 "VALUES ('GONE', 'p', 'm', 2, 'v', '{}', 'h', 'i', 1, 1, false, '[1,0]', 'r')")
    with prod.transaction():
        assert lifecycle.hard_delete_expired(prod, T0) == ['GONE']
    remaining = [r[0] for r in prod.execute('SELECT job_id FROM jobs ORDER BY job_id').fetchall()]
    assert remaining == ['LIVE', 'NT_1', 'NT_2', 'RECENT']
    for table in ('job_sources', 'job_query_hits', 'jd_extraction_cache', 'job_embedding_versions'):
        assert prod.execute(f"SELECT count(*) FROM {table} WHERE job_id = 'GONE'").fetchone()[0] == 0
    retrieved = prod.execute(f'SELECT job_id FROM jobs WHERE {lifecycle.PRODUCTION_RETRIEVAL_FILTER} ORDER BY job_id')
    assert [r[0] for r in retrieved.fetchall()] == ['LIVE']                      # retained rows never retrieved


# --- F8: one ticket per IP even under concurrency --------------------------------------------------------

# The planned Phase 2B statement: consume a ticket only if none was consumed in the last 24 hours.
CONSUME = ('INSERT INTO live_quota (ip_hmac, consumed_at) VALUES (%s, now()) ON CONFLICT (ip_hmac) DO UPDATE '
           "SET consumed_at = now() WHERE live_quota.consumed_at <= now() - interval '24 hours' RETURNING 1")


@pytest.mark.parametrize('previous', [None, timedelta(hours=25)])
def test_concurrent_ticket_consumption_succeeds_exactly_once(db, previous):
    upgrade(db, 'head')
    if previous:
        with psycopg.connect(db, autocommit=True) as conn:
            conn.execute('INSERT INTO live_quota VALUES (%s, now() - %s)', (HMAC, previous))
    barrier, results = threading.Barrier(2), []

    def consume():
        with psycopg.connect(db) as conn:
            barrier.wait()
            row = conn.execute(CONSUME, (HMAC,)).fetchone()
            time.sleep(0.3)                     # hold the row lock while the other request waits
            conn.commit()
            results.append(row is not None)
    threads = [threading.Thread(target=consume) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert sorted(results) == [False, True]
    with psycopg.connect(db) as conn:
        assert conn.execute(CONSUME, (HMAC,)).fetchone() is None              # still within 24 hours


# --- F9: guarded downgrade ---------------------------------------------------------------------------------

def test_downgrade_is_refused_unless_explicitly_allowed_outside_prod(db, monkeypatch):
    upgrade(db, 'head')
    monkeypatch.delenv('JOBFIT_ALLOW_DESTRUCTIVE_DOWNGRADE', raising=False)
    with pytest.raises(RuntimeError, match='destructive downgrade'):
        command.downgrade(alembic_config(db), '0001')
    monkeypatch.setenv('JOBFIT_ALLOW_DESTRUCTIVE_DOWNGRADE', '1')
    monkeypatch.setenv('JOBFIT_ENV', 'prod')
    with pytest.raises(RuntimeError, match='destructive downgrade'):
        command.downgrade(alembic_config(db), '0001')
    state, fp = state_and_fingerprint(db)
    assert state == '0002' and catalog.compare(PIN['0002'], fp) == []
    monkeypatch.setenv('JOBFIT_ENV', 'dev')
    command.downgrade(alembic_config(db), '0001')
    state, fp = state_and_fingerprint(db)
    assert state == '0001' and catalog.compare(PIN['0001'], fp) == []
    command.downgrade(alembic_config(db), 'base')
    assert state_and_fingerprint(db)[1]['objects']['tables'] == {}
    upgrade(db, 'head')
    state, fp = state_and_fingerprint(db)
    assert state == '0002' and catalog.compare(PIN['0002'], fp) == []
