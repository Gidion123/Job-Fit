"""Database schema for the job snapshot (System Design v1.3, section 13).

Plain SQL for CP2. Alembic migrations replace this in CP3.2.
The full-text column uses the `simple` configuration (no stemming), because the corpus mixes
English and Indonesian job descriptions.
"""
from __future__ import annotations

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
"""
