"""One-time production corpus seed for a restored copy of the CP1 database (D-098 section 2, D-105).

After ``alembic upgrade head`` the 0002 lifecycle columns are empty: every job is inactive, so the
production retriever finds nothing. This command initializes that lifecycle once, on a restored
COPY (never the CP2 evaluation database), with no migration and no new table:

- source: ``data/processed/jobs_features.jsonl``, only ``is_auditable == true`` rows (the 632 rows
  ``load_snapshot.read_candidates()`` loads), keyed by ``final_cluster_id``; the database job ids must
  equal that set exactly;
- seen timestamps: the feature ``first_seen_at``/``last_seen_at`` when both are valid and ordered;
  otherwise BOTH are the single seed-transaction timestamp ("entered the production lifecycle at seed
  time"), never an invented historical date. Reported as ``legacy_seen_timestamp_fallback``;
- all rows canonical; the 428 target rows active, the 204 non-target rows inactive with
  ``inactive_since`` NULL (never hard-deleted by the 60-day rule);
- one ``job_sources`` row per canonical job with the SAME effective timestamps as the job. Limitation
  (D-105): CP1 jobs that stood for several source slots keep only their canonical source identity;
  member-level alias provenance is deferred to the corpus/sync work and not claimed complete here.

Fail closed: anything but a pristine post-0002 lifecycle (any active row, any seen or inactive
timestamp, a suspect link, a miss count, a non-canonical row, any source, hit or sync row) is refused,
never repaired. ``--dry-run`` reports and rolls back; ``--verify`` checks the seeded state read-only,
including a complete current embedding index of the frozen profile for every eligible job.

Usage: python -m jobfit.db.seed_production [--dry-run | --verify] [--database-url URL] [--features PATH]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg
import yaml

from jobfit.config import REPO_ROOT

FEATURES = REPO_ROOT / 'data/processed/jobs_features.jsonl'
EXPECTED = {'jobs': 632, 'active_target': 428, 'inactive_non_target': 204}
REVISION = '0002'
PIPELINE = REPO_ROOT / 'config/versions/pipeline_cp23_freeze_candidate_v4_20261006.yaml'


class SeedRefused(Exception):
    def __init__(self, problems: list[str]):
        super().__init__('; '.join(problems))
        self.problems = problems


def _timestamp(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None      # a naive time has no defined instant


def read_features(path: Path = FEATURES) -> dict[str, dict]:
    """The auditable feature rows by job id (``final_cluster_id``)."""
    rows = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            if not r.get('is_auditable'):
                continue
            job_id = r['final_cluster_id']
            if job_id in rows:
                raise SeedRefused([f'duplicate auditable job id {job_id}'])
            rows[job_id] = {'job_id': job_id, 'role_group': r.get('role_group'),
                            'first': _timestamp(r.get('first_seen_at')), 'last': _timestamp(r.get('last_seen_at')),
                            'source': r.get('source_provider'), 'source_job_id': r.get('source_job_id')}
    return rows


def effective_seen(row: dict, seed_time: datetime) -> tuple[datetime, datetime, bool]:
    """(first, last, fallback): the feature times when both are valid and ordered, else the seed time twice."""
    first, last = row['first'], row['last']
    if first is not None and last is not None and last >= first:
        return first, last, False
    return seed_time, seed_time, True


def frozen_embedding_spec():
    from jobfit.search.embeddings import load_specs
    raw = yaml.safe_load(PIPELINE.read_text())
    models = yaml.safe_load((REPO_ROOT / 'config/models_v1.yaml').read_text())['embeddings']
    model_id = models[raw['embedding_model']]['id']
    return next(s for s in load_specs() if s.model == model_id)


def _one(conn, sql, params=None):
    return conn.execute(sql, params).fetchone()[0]


def pristine_problems(conn, features: dict[str, dict], expected: dict = EXPECTED) -> list[str]:
    """Why this database is not a pristine post-0002 restored snapshot (empty list = pristine)."""
    problems = []
    try:
        version = _one(conn, 'SELECT version_num FROM alembic_version')
    except Exception:
        return ['alembic_version missing: run the guarded stamp and alembic upgrade head first']
    if version != REVISION:
        return [f'schema revision is {version}, expected {REVISION}']
    if len(features) != expected['jobs']:
        problems.append(f"{len(features)} auditable feature rows, expected {expected['jobs']}")
    db = dict(conn.execute('SELECT job_id, role_group FROM jobs').fetchall())
    if set(db) != set(features):
        problems.append(f'job ids differ from the auditable features: {len(set(db) - set(features))} extra, '
                        f'{len(set(features) - set(db))} missing')
    elif any(db[j] != features[j]['role_group'] for j in db):
        problems.append('role_group differs between the database and the features')
    if sum(r['role_group'] == 'target' for r in features.values()) != expected['active_target']:
        problems.append(f"target feature rows are not {expected['active_target']}")
    checks = {
        'active rows': 'SELECT count(*) FROM jobs WHERE is_active',
        'rows with first_seen_at': 'SELECT count(*) FROM jobs WHERE first_seen_at IS NOT NULL',
        'rows with last_seen_at': 'SELECT count(*) FROM jobs WHERE last_seen_at IS NOT NULL',
        'rows with inactive_since': 'SELECT count(*) FROM jobs WHERE inactive_since IS NOT NULL',
        'rows with dedupe_suspect_of': 'SELECT count(*) FROM jobs WHERE dedupe_suspect_of IS NOT NULL',
        'rows with covered_miss_count': 'SELECT count(*) FROM jobs WHERE covered_miss_count <> 0',
        'non-canonical rows': "SELECT count(*) FROM jobs WHERE dedupe_status <> 'canonical'",
        'job_sources rows': 'SELECT count(*) FROM job_sources',
        'job_query_hits rows': 'SELECT count(*) FROM job_query_hits',
        'sync_runs rows': 'SELECT count(*) FROM sync_runs',
    }
    for label, sql in checks.items():
        n = _one(conn, sql)
        if n:
            problems.append(f'not pristine: {n} {label} (already or partly seeded; refused, never repaired)')
    bad_sources = [j for j, r in features.items() if not r['source'] or not r['source_job_id']]
    if bad_sources:
        problems.append(f'{len(bad_sources)} auditable rows without a canonical source identity')
    return problems


def verify_problems(conn, features: dict[str, dict], spec=None, expected: dict = EXPECTED) -> tuple[list[str], dict]:
    """Read-only checks of the seeded lifecycle; ``spec=None`` skips the embedding-index check."""
    from jobfit.search import production
    problems = []
    db_ids = {r[0] for r in conn.execute('SELECT job_id FROM jobs').fetchall()}
    if db_ids != set(features) or len(features) != expected['jobs']:
        problems.append(f"job ids are not exactly the {expected['jobs']} auditable feature ids")
    counts = {
        'active_target': _one(conn, "SELECT count(*) FROM jobs WHERE is_active AND role_group = 'target'"),
        'inactive_non_target': _one(conn, "SELECT count(*) FROM jobs WHERE NOT is_active AND role_group <> 'target'"),
        'active_non_target': _one(conn, "SELECT count(*) FROM jobs WHERE is_active AND role_group <> 'target'"),
        'inactive_target': _one(conn, "SELECT count(*) FROM jobs WHERE NOT is_active AND role_group = 'target'"),
        'non_canonical': _one(conn, "SELECT count(*) FROM jobs WHERE dedupe_status <> 'canonical'"),
        'active_bad_seen': _one(conn, 'SELECT count(*) FROM jobs WHERE is_active AND (first_seen_at IS NULL '
                                      'OR last_seen_at IS NULL OR last_seen_at < first_seen_at)'),
        'inactive_with_inactive_since': _one(conn, 'SELECT count(*) FROM jobs WHERE NOT is_active '
                                                   'AND inactive_since IS NOT NULL'),
        'job_sources': _one(conn, 'SELECT count(*) FROM job_sources'),
        'job_sources_bad_seen': _one(conn, 'SELECT count(*) FROM job_sources s JOIN jobs j USING (job_id) '
                                           'WHERE s.first_seen_at IS DISTINCT FROM j.first_seen_at '
                                           'OR s.last_seen_at IS DISTINCT FROM j.last_seen_at '
                                           'OR s.last_seen_at < s.first_seen_at'),
    }
    if counts['active_target'] != expected['active_target'] or counts['inactive_target']:
        problems.append(f"active target rows {counts['active_target']}, expected {expected['active_target']}")
    if counts['inactive_non_target'] != expected['inactive_non_target'] or counts['active_non_target']:
        problems.append(f"inactive non-target rows {counts['inactive_non_target']}, "
                        f"expected {expected['inactive_non_target']}")
    for key, label in (('non_canonical', 'non-canonical rows'),
                       ('active_bad_seen', 'active rows without valid ordered seen timestamps'),
                       ('inactive_with_inactive_since', 'initially inactive rows with inactive_since set'),
                       ('job_sources_bad_seen', 'job_sources rows whose timestamps differ from the job')):
        if counts[key]:
            problems.append(f'{counts[key]} {label}')
    sources = set(conn.execute('SELECT source, source_job_id, job_id FROM job_sources').fetchall())
    identities = {(r['source'], r['source_job_id'], j) for j, r in features.items()}
    if counts['job_sources'] != expected['jobs'] or sources != identities:
        problems.append(f"job_sources are not exactly the {expected['jobs']} canonical feature identities")
    if spec is not None:
        try:
            eligible = production.eligible_jobs(conn)
            production.check_index(conn, spec, [r['job_id'] for r in eligible])
            counts['eligible_indexed'] = len(eligible)
        except production.ProductionRetrievalUnavailable as exc:
            problems.append(f'embedding index: {exc.reason}')
    return problems, counts


def seed(conn, features: dict[str, dict], *, dry_run: bool = False, expected: dict = EXPECTED) -> dict:
    """Seed in one transaction; refuse anything but a pristine lifecycle. ``conn`` must not be autocommit."""
    report: dict = {}
    with conn.transaction():
        problems = pristine_problems(conn, features, expected)
        if problems:
            raise SeedRefused(problems)
        seed_time = _one(conn, 'SELECT now()')                 # one transaction timestamp for every fallback
        fallback = {'total': 0, 'target': 0, 'non_target': 0}
        for job_id, row in sorted(features.items()):
            first, last, used = effective_seen(row, seed_time)
            if used:
                fallback['total'] += 1
                fallback['target' if row['role_group'] == 'target' else 'non_target'] += 1
            conn.execute("UPDATE jobs SET first_seen_at = %s, last_seen_at = %s, dedupe_status = 'canonical', "
                         "is_active = (role_group = 'target'), inactive_since = NULL WHERE job_id = %s",
                         (first, last, job_id))
            conn.execute('INSERT INTO job_sources (source, source_job_id, job_id, first_seen_at, last_seen_at) '
                         'VALUES (%s, %s, %s, %s, %s)', (row['source'], row['source_job_id'], job_id, first, last))
        problems, counts = verify_problems(conn, features, expected=expected)
        if problems:
            raise SeedRefused(problems)                         # rolls the whole transaction back
        report = {'seed_time': seed_time.isoformat(), 'counts': counts, 'legacy_seen_timestamp_fallback': fallback,
                  'dry_run': dry_run,
                  'note': 'Fallback rows entered the production lifecycle at seed time; no historical date '
                          'was invented. job_sources hold the canonical source identity only (member-level '
                          'alias provenance deferred).'}
        if dry_run:
            raise psycopg.Rollback()
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='One-time production corpus seed (restored copy only).')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true', help='report the counts and roll back')
    mode.add_argument('--verify', action='store_true', help='read-only check of the seeded state')
    parser.add_argument('--database-url', default=os.environ.get('DATABASE_URL'))
    parser.add_argument('--features', type=Path, default=FEATURES)
    args = parser.parse_args(argv)
    if not args.database_url:
        print('refused: DATABASE_URL is not set', file=sys.stderr)
        return 2
    try:
        features = read_features(args.features)
        with psycopg.connect(args.database_url) as conn:
            if args.verify:
                problems, counts = verify_problems(conn, features, frozen_embedding_spec())
                print(json.dumps({'ok': not problems, 'problems': problems, 'counts': counts}, indent=2))
                return 0 if not problems else 2
            report = seed(conn, features, dry_run=args.dry_run)
    except SeedRefused as exc:
        print(json.dumps({'ok': False, 'refused': exc.problems}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps({'ok': True, **report}, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
