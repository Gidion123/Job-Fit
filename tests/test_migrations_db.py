"""Alembic 0001/0002 on real PostgreSQL + pgvector (CP3, D-098). Opt-in; no API calls.

Needs JOBFIT_MIGRATION_TESTS=1 and JOBFIT_MIGRATION_ADMIN_URL, a role that may create databases on
a disposable pgvector server (the CI service). Every test works in its own scratch database, which
is dropped afterwards. Nothing here touches the local CP2 evaluation database.
"""
import json
import os

import psycopg
import pytest
from alembic import command

import scripts.db_baseline as baseline
from jobfit.config import REPO_ROOT
from jobfit.db import catalog
from jobfit.db.migrate import alembic_config
from jobfit.db.models import SCHEMA_SQL

ADMIN = os.environ.get('JOBFIT_MIGRATION_ADMIN_URL')
pytestmark = pytest.mark.skipif(os.environ.get('JOBFIT_MIGRATION_TESTS') != '1' or not ADMIN,
                                reason='requires JOBFIT_MIGRATION_TESTS=1 and a disposable pgvector server')
PIN = {r: json.loads((REPO_ROOT / f'migrations/catalog/{r}.json').read_text()) for r in ('0001',)}


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
    assert content(db) == before


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
