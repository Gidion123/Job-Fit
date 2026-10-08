"""CP3 production schema: lifecycle, dedupe, sources, sync runs, extraction cache, quota, reservations.

Additive only (D-098): no 0001 column, constraint or index changes, so the frozen CP2 readers
(search/dense.py, search/fts.py, search/hybrid.py) and the CP2 loader keep working. New jobs
columns have defaults that keep rows out of production retrieval until the seed or the sync
sets them.

Budget reservations (D-096). What this schema enforces by itself:
- a released reservation has settled_usd = 0; a closed reservation (settled or released) can
  never change, so a settled reservation can never be rewritten as released;
- an open reservation cannot be deleted, because it keeps counting against the daily cap;
- production_day is the Asia/Jakarta date of created_at;
- active_until, the persisted end of the reservation's possible activity, is supplied by the
  reservation creator, lies after created_at and never changes. Whether an earlier-day
  reservation is still outstanding is therefore decided from stored state, never from the
  current deployment's configuration.
What it cannot prove: the database has no access to the authoritative production ledger, so it
cannot show that a reservation had zero ledger spend and no uncertain upper-bound record. That
check, before any release, belongs to the Phase 2B runtime.

Revision ID: 0002
Revises: 0001
"""
import os

from alembic import op

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

UPGRADE_SQL = r"""
ALTER TABLE jobs
    ADD COLUMN is_active boolean NOT NULL DEFAULT false,
    ADD COLUMN dedupe_status text NOT NULL DEFAULT 'canonical',
    ADD COLUMN dedupe_suspect_of text REFERENCES jobs (job_id) ON DELETE SET NULL,
    ADD COLUMN first_seen_at timestamptz,
    ADD COLUMN last_seen_at timestamptz,
    ADD COLUMN covered_miss_count integer NOT NULL DEFAULT 0,
    ADD COLUMN inactive_since timestamptz,
    ADD CONSTRAINT jobs_dedupe_status_check CHECK (dedupe_status IN ('canonical', 'review_required')),
    ADD CONSTRAINT jobs_active_canonical_check CHECK (dedupe_status = 'canonical' OR NOT is_active),
    ADD CONSTRAINT jobs_dedupe_suspect_check
        CHECK (dedupe_suspect_of IS NULL OR (dedupe_status = 'review_required' AND dedupe_suspect_of <> job_id)),
    ADD CONSTRAINT jobs_active_seen_check
        CHECK (NOT is_active OR (first_seen_at IS NOT NULL AND last_seen_at IS NOT NULL)),
    ADD CONSTRAINT jobs_seen_order_check CHECK (last_seen_at >= first_seen_at),
    ADD CONSTRAINT jobs_active_inactive_since_check CHECK (NOT is_active OR inactive_since IS NULL),
    ADD CONSTRAINT jobs_covered_miss_count_check CHECK (covered_miss_count >= 0);

CREATE TABLE sync_runs (
    sync_run_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    status text NOT NULL,
    manifest_sha256 text NOT NULL,
    code_version text NOT NULL,
    query_status jsonb NOT NULL DEFAULT '{}'::jsonb,
    counts jsonb NOT NULL DEFAULT '{}'::jsonb,
    error_code text,
    CONSTRAINT sync_runs_status_check CHECK (status IN ('running', 'succeeded', 'failed', 'aborted')),
    CONSTRAINT sync_runs_finished_check CHECK ((status = 'running') = (finished_at IS NULL)),
    CONSTRAINT sync_runs_finished_order_check CHECK (finished_at >= started_at),
    CONSTRAINT sync_runs_manifest_check CHECK (manifest_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT sync_runs_query_status_check CHECK (jsonb_typeof(query_status) = 'object'),
    CONSTRAINT sync_runs_counts_check CHECK (jsonb_typeof(counts) = 'object')
);
CREATE UNIQUE INDEX sync_runs_one_running_idx ON sync_runs ((true)) WHERE status = 'running';

CREATE TABLE job_sources (
    source text NOT NULL,
    source_job_id text NOT NULL,
    job_id text NOT NULL REFERENCES jobs (job_id) ON DELETE CASCADE,
    first_seen_at timestamptz NOT NULL,
    last_seen_at timestamptz NOT NULL,
    PRIMARY KEY (source, source_job_id),
    CONSTRAINT job_sources_identity_check CHECK (source <> '' AND source_job_id <> ''),
    CONSTRAINT job_sources_seen_order_check CHECK (last_seen_at >= first_seen_at)
);
CREATE INDEX job_sources_job_id_idx ON job_sources (job_id);

CREATE TABLE job_query_hits (
    job_id text NOT NULL REFERENCES jobs (job_id) ON DELETE CASCADE,
    query_id text NOT NULL,
    first_hit_at timestamptz NOT NULL,
    last_hit_at timestamptz NOT NULL,
    last_sync_run_id bigint REFERENCES sync_runs (sync_run_id),
    PRIMARY KEY (job_id, query_id),
    CONSTRAINT job_query_hits_order_check CHECK (last_hit_at >= first_hit_at)
);
CREATE INDEX job_query_hits_query_id_idx ON job_query_hits (query_id);

CREATE TABLE jd_extraction_cache (
    cache_key text PRIMARY KEY,
    job_id text NOT NULL REFERENCES jobs (job_id) ON DELETE CASCADE,
    content_hash text NOT NULL,
    scope text NOT NULL,
    status text NOT NULL,
    value jsonb,
    value_hash text,
    error_code text,
    expires_at timestamptz,
    model text NOT NULL,
    prompt_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT jd_extraction_cache_key_check CHECK (cache_key ~ '^[0-9a-f]{64}$'),
    CONSTRAINT jd_extraction_cache_scope_check CHECK (scope = 'corpus_jd'),
    CONSTRAINT jd_extraction_cache_status_check CHECK (status IN ('ok', 'failed')),
    CONSTRAINT jd_extraction_cache_state_check CHECK (
        (status = 'ok'
            AND value IS NOT NULL AND jsonb_typeof(value) = 'object'
            AND value_hash IS NOT NULL AND value_hash ~ '^[0-9a-f]{64}$'
            AND error_code IS NULL AND expires_at IS NULL)
        OR
        (status = 'failed'
            AND value IS NULL AND value_hash IS NULL
            AND error_code IS NOT NULL AND error_code ~ '^[A-Za-z_][A-Za-z0-9_]{0,63}$'
            AND expires_at IS NOT NULL AND expires_at > created_at))
);
CREATE INDEX jd_extraction_cache_job_id_idx ON jd_extraction_cache (job_id);

CREATE TABLE budget_reservations (
    reservation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_key text NOT NULL UNIQUE,
    phase text NOT NULL,
    production_day date NOT NULL DEFAULT ((now() AT TIME ZONE 'Asia/Jakarta')::date),
    reserved_usd numeric(20, 10) NOT NULL,
    settled_usd numeric(20, 10),
    status text NOT NULL DEFAULT 'reserved',
    process_id text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    active_until timestamptz NOT NULL,
    closed_at timestamptz,
    CONSTRAINT budget_reservations_phase_check CHECK (phase IN ('parse', 'recommendation')),
    CONSTRAINT budget_reservations_reserved_check CHECK (reserved_usd > 0 AND reserved_usd <> 'NaN'),
    CONSTRAINT budget_reservations_settled_check CHECK (settled_usd >= 0 AND settled_usd <> 'NaN'),
    CONSTRAINT budget_reservations_state_check CHECK (
        (status = 'reserved' AND settled_usd IS NULL AND closed_at IS NULL)
        OR (status = 'settled' AND settled_usd IS NOT NULL AND closed_at IS NOT NULL)
        OR (status = 'released' AND settled_usd = 0 AND closed_at IS NOT NULL)),
    CONSTRAINT budget_reservations_closed_order_check CHECK (closed_at >= created_at),
    CONSTRAINT budget_reservations_active_until_check CHECK (active_until > created_at),
    CONSTRAINT budget_reservations_production_day_check
        CHECK (production_day = (created_at AT TIME ZONE 'Asia/Jakarta')::date)
);
CREATE INDEX budget_reservations_day_status_idx ON budget_reservations (production_day, status);

CREATE FUNCTION budget_reservations_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        IF OLD.status = 'reserved' THEN
            RAISE EXCEPTION 'an open budget reservation cannot be deleted';
        END IF;
        RETURN OLD;
    END IF;
    IF OLD.status <> 'reserved' THEN
        RAISE EXCEPTION 'a closed budget reservation is immutable';
    END IF;
    IF NEW.reservation_id <> OLD.reservation_id OR NEW.operation_key <> OLD.operation_key
            OR NEW.phase <> OLD.phase OR NEW.production_day <> OLD.production_day
            OR NEW.reserved_usd <> OLD.reserved_usd OR NEW.process_id <> OLD.process_id
            OR NEW.created_at <> OLD.created_at OR NEW.active_until <> OLD.active_until THEN
        RAISE EXCEPTION 'budget reservation identity, amount, day and lifetime are immutable';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER budget_reservations_guard BEFORE UPDATE OR DELETE ON budget_reservations
    FOR EACH ROW EXECUTE FUNCTION budget_reservations_guard();

CREATE TABLE live_quota (
    ip_hmac text PRIMARY KEY,
    consumed_at timestamptz NOT NULL,
    CONSTRAINT live_quota_ip_hmac_check CHECK (ip_hmac ~ '^[0-9a-f]{64}$')
);
CREATE INDEX live_quota_consumed_at_idx ON live_quota (consumed_at);
"""

DOWNGRADE_SQL = """
DROP TABLE live_quota;
DROP TABLE budget_reservations;
DROP FUNCTION budget_reservations_guard();
DROP TABLE jd_extraction_cache;
DROP TABLE job_query_hits;
DROP TABLE job_sources;
DROP TABLE sync_runs;
ALTER TABLE jobs
    DROP CONSTRAINT jobs_dedupe_status_check,
    DROP CONSTRAINT jobs_active_canonical_check,
    DROP CONSTRAINT jobs_dedupe_suspect_check,
    DROP CONSTRAINT jobs_active_seen_check,
    DROP CONSTRAINT jobs_seen_order_check,
    DROP CONSTRAINT jobs_active_inactive_since_check,
    DROP CONSTRAINT jobs_covered_miss_count_check,
    DROP COLUMN is_active,
    DROP COLUMN dedupe_status,
    DROP COLUMN dedupe_suspect_of,
    DROP COLUMN first_seen_at,
    DROP COLUMN last_seen_at,
    DROP COLUMN covered_miss_count,
    DROP COLUMN inactive_since;
"""


def upgrade() -> None:
    op.get_bind().exec_driver_sql(UPGRADE_SQL)


def require_destructive_downgrade() -> None:
    if os.environ.get('JOBFIT_ALLOW_DESTRUCTIVE_DOWNGRADE') != '1' or os.environ.get('JOBFIT_ENV') == 'prod':
        raise RuntimeError('destructive downgrade is allowed only on CI/ephemeral databases '
                           '(JOBFIT_ALLOW_DESTRUCTIVE_DOWNGRADE=1 and JOBFIT_ENV != prod); '
                           'production recovery is the previous image plus a database restore')


def downgrade() -> None:
    require_destructive_downgrade()
    op.get_bind().exec_driver_sql(DOWNGRADE_SQL)
