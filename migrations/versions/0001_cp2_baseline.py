"""CP2 baseline: the exact SCHEMA_SQL of src/jobfit/db/models.py at the start of CP3 (D-098).

SCHEMA_SQL below is an immutable literal copy. It is never imported from jobfit at migration time,
so later edits to models.py cannot change this revision (tests/test_migrations_offline.py pins
the hash). The guard refuses any database that already holds application objects in public
(tables, views, sequences, functions, types; extension-owned objects excepted): an existing CP2
database is verified and stamped with scripts/db_baseline.py instead, never upgraded through 0001.

Revision ID: 0001
Revises: (none)
"""
import os

from alembic import op
from sqlalchemy import text

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

SCHEMA_SQL_SHA256 = '38abfee02611336eb1355090843a7231c9e46f93a256ea660d310f63070250b3'
SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS jobs (
    job_id              text PRIMARY KEY,          -- final_cluster_id from the CP1 snapshot
    job_uid             text,
    content_hash        text NOT NULL,
    snapshot_id         text NOT NULL,
    title               text NOT NULL,
    normalized_title    text,
    company             text,
    role_family         text,
    role_group          text,                      -- target / adjacent / non_target
    country_code        text,
    city_normalized     text,
    analysis_geo        text,
    work_mode           text,
    experience_bucket   text,
    years_min           integer,
    years_max           integer,
    jd_language         text,
    jd_quality          text,
    posted_at           text,
    apply_url           text,
    google_url          text,
    skills_v0           text[] NOT NULL DEFAULT '{}',
    description_clean   text NOT NULL,
    loaded_at           timestamptz NOT NULL DEFAULT now(),
    search              tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('simple', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(description_clean, '')), 'B')
    ) STORED
);

CREATE INDEX IF NOT EXISTS jobs_search_idx ON jobs USING gin (search);
CREATE INDEX IF NOT EXISTS jobs_role_group_idx ON jobs (role_group);

-- Filled in CP2.2 (D-020: text-embedding-3-small, 1536 dimensions).
CREATE TABLE IF NOT EXISTS job_embeddings (
    job_id          text NOT NULL REFERENCES jobs (job_id) ON DELETE CASCADE,
    model           text NOT NULL,
    content_hash    text NOT NULL,
    embedding       vector(1536) NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (job_id, model)
);

-- Versioned CP2.2 storage. Preserve the original table and any legacy vectors.
-- Unconstrained vector supports 1536 and 4096 dimensions without an ANN index.
CREATE TABLE IF NOT EXISTS job_embedding_versions (
    job_id text NOT NULL REFERENCES jobs(job_id),
    profile_id text NOT NULL,
    model text NOT NULL,
    dimensions integer NOT NULL CHECK (dimensions > 0),
    preprocessing_version text NOT NULL,
    profile_spec jsonb NOT NULL,
    content_hash text NOT NULL,
    input_hash text NOT NULL,
    input_tokens integer NOT NULL,
    original_tokens integer NOT NULL,
    truncated boolean NOT NULL,
    embedding vector NOT NULL,
    run_id text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (vector_dims(embedding) = dimensions),
    PRIMARY KEY(job_id, profile_id, content_hash, input_hash)
);
CREATE INDEX IF NOT EXISTS job_embedding_versions_profile_idx
    ON job_embedding_versions(profile_id);
"""
# Application-owned objects already in public (anything not owned by an extension). Alembic's own
# version table is created in this same transaction before the revision runs, so it is allowed.
UNEXPECTED_OBJECTS = """
SELECT 'relation ' || c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p', 'v', 'm', 'f', 'S', 'c')
  AND c.relname <> 'alembic_version'
  AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid = 'pg_class'::regclass
                  AND d.objid = c.oid AND d.deptype = 'e')
UNION ALL
SELECT 'function ' || p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid = 'pg_proc'::regclass
                  AND d.objid = p.oid AND d.deptype = 'e')
UNION ALL
SELECT 'type ' || t.typname FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace
WHERE n.nspname = 'public' AND t.typtype IN ('d', 'e', 'r', 'm')
  AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid = 'pg_type'::regclass
                  AND d.objid = t.oid AND d.deptype = 'e')
ORDER BY 1
"""


def upgrade() -> None:
    bind = op.get_bind()
    found = [row[0] for row in bind.execute(text(UNEXPECTED_OBJECTS))]
    if found:
        raise RuntimeError('database is not empty (' + ', '.join(found[:10]) + '); for an existing CP2 '
                           'database, verify and stamp with scripts/db_baseline.py, never upgrade through 0001')
    bind.exec_driver_sql(SCHEMA_SQL)


def require_destructive_downgrade() -> None:
    if os.environ.get('JOBFIT_ALLOW_DESTRUCTIVE_DOWNGRADE') != '1' or os.environ.get('JOBFIT_ENV') == 'prod':
        raise RuntimeError('destructive downgrade is allowed only on CI/ephemeral databases '
                           '(JOBFIT_ALLOW_DESTRUCTIVE_DOWNGRADE=1 and JOBFIT_ENV != prod); '
                           'production recovery is the previous image plus a database restore')


def downgrade() -> None:
    require_destructive_downgrade()
    op.get_bind().exec_driver_sql('DROP TABLE job_embedding_versions, job_embeddings, jobs')
