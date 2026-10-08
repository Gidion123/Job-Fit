"""Verify an existing CP2 database against Alembic 0001, and stamp it only if it matches (D-098).

    python scripts/db_baseline.py verify     # read-only comparison, exit 0 only on an exact match
    python scripts/db_baseline.py stamp      # verify, then a guarded, locked `alembic stamp 0001`
    python scripts/db_baseline.py reference --revision 0002   # print a reference fingerprint

The target is the database in DATABASE_URL (required; never printed). The reference is built
fresh on the same server: a scratch database is created, upgraded through the Alembic revisions
and fingerprinted, then dropped (CREATEDB privilege needed). The target itself is only read,
except by `stamp`, which writes the Alembic version row after a successful verification.

A database that already has an Alembic version table is refused: a stamp is only ever the
first stamp. Any difference fails closed; it is reported structurally, without row data.
Never run a bare `alembic stamp` on an existing database.

`stamp` runs on one dedicated connection that holds the JobFit schema advisory lock (session
level) from before its final validation until after its post-commit check, so no cooperating
JobFit migration can interleave. Inside one transaction it locks the three CP2 tables (no DDL or
writes on them until commit), re-validates the exact baseline, writes the version row through
Alembic on the same connection, and validates again before committing. After the commit it checks
once more; on drift it removes the stamp only if that stamp is provably its own (same table,
revision 0001), and otherwise changes nothing and reports a blocker. Assumption: during the
maintenance window, schema changes are made only through JobFit tooling. PostgreSQL cannot stop
an unrelated session from creating new objects in public; such drift is detected, and the only
case it could survive is a crash of this process between its commit and its post-commit check.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from contextlib import contextmanager

import psycopg
from alembic import command
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url

from jobfit.db import catalog
from jobfit.db.migrate import SCHEMA_LOCK_KEY, alembic_config, sqlalchemy_url

BASELINE = '0001'
CP2_TABLES = 'public.jobs, public.job_embeddings, public.job_embedding_versions'
LOCK_TIMEOUT = '30s'


class StampAborted(RuntimeError):
    """The stamp found drift and was not kept (rolled back, or its own stamp removed)."""


class StampBlocker(RuntimeError):
    """The revision state is not provably this operation's stamp; nothing was changed."""


def _with_database(url: str, name: str) -> str:
    return make_url(url).set(database=name).render_as_string(hide_password=False)


@contextmanager
def scratch_database(server_url: str):
    """A temporary database on the same server as ``server_url``; always dropped afterwards."""
    name = 'jobfit_ref_' + secrets.token_hex(6)
    with psycopg.connect(server_url, autocommit=True) as admin:
        admin.execute(f'CREATE DATABASE {name}')
    try:
        yield _with_database(server_url, name)
    finally:
        with psycopg.connect(server_url, autocommit=True) as admin:
            admin.execute(f'DROP DATABASE IF EXISTS {name} WITH (FORCE)')


def reference_fingerprint(server_url: str, revision: str = BASELINE) -> dict:
    with scratch_database(server_url) as url:
        command.upgrade(alembic_config(url), revision)
        with psycopg.connect(url) as conn:
            return catalog.fingerprint(conn)


def read_target(url: str) -> tuple[str, dict]:
    with psycopg.connect(url) as conn:
        conn.read_only = True
        return catalog.revision_state(conn), catalog.fingerprint(conn)


def _verify_with_reference(target_url: str, *, allowed_vector_versions: tuple[str, ...] = ()) -> tuple[dict, dict]:
    state, actual = read_target(target_url)
    expected = reference_fingerprint(target_url, BASELINE)
    differences = catalog.compare(expected, actual)
    if state != 'absent':
        differences.insert(0, f'alembic version table: expected absent, found {state}')
    want = expected['environment']['extension_versions'].get('vector')
    have = actual['environment']['extension_versions'].get('vector')
    if have != want and have not in allowed_vector_versions:
        differences.append(f'environment/vector version: expected {want!r}, found {have!r}')
    report = {'ok': not differences, 'revision_state': state, 'differences': differences,
              'environment': {'target': actual['environment'], 'reference': expected['environment']}}
    return report, expected


def verify(target_url: str, *, allowed_vector_versions: tuple[str, ...] = ()) -> dict:
    return _verify_with_reference(target_url, allowed_vector_versions=allowed_vector_versions)[0]


def _check(pg, expected: dict, revision: str) -> list[str]:
    state = catalog.revision_state(pg)
    differences = catalog.compare(expected, catalog.fingerprint(pg))
    if state != revision:
        differences.insert(0, f'alembic version table: expected {revision}, found {state}')
    return differences


def _version_table_oid(pg):
    return pg.execute(f"SELECT to_regclass('public.{catalog.ALEMBIC_VERSION_TABLE}')::oid").fetchone()[0]


def _post_commit_check(pg, expected: dict) -> list[str]:
    return _check(pg, expected, BASELINE)


def stamp(target_url: str, *, allowed_vector_versions: tuple[str, ...] = ()) -> dict:
    report, expected = _verify_with_reference(target_url, allowed_vector_versions=allowed_vector_versions)
    if not report['ok']:
        report['stamped'] = False
        return report
    engine = create_engine(sqlalchemy_url(target_url), poolclass=pool.NullPool)
    try:
        with engine.connect() as conn:
            pg = conn.connection.driver_connection     # same session and transaction as ``conn``
            # Every statement on this connection runs inside an explicit conn.begin() block, so
            # SQLAlchemy's autobegin never opens a transaction behind our back.
            with conn.begin():                            # short transaction: session settings + lock
                pg.execute(f"SET lock_timeout = '{LOCK_TIMEOUT}'")
                pg.execute('SELECT pg_advisory_lock(%s)', (SCHEMA_LOCK_KEY,))   # session level: survives commits
            try:
                return _stamp_locked(conn, pg, target_url, expected, report)
            finally:
                try:
                    with conn.begin():
                        pg.execute('SELECT pg_advisory_unlock(%s)', (SCHEMA_LOCK_KEY,))
                except Exception:
                    pass        # a broken connection has already released its session locks
    finally:
        engine.dispose()


def _stamp_locked(conn, pg, target_url, expected, report) -> dict:
    with conn.begin():                                    # stamp transaction T
        pg.execute(f'LOCK TABLE {CP2_TABLES} IN EXCLUSIVE MODE')
        differences = _check(pg, expected, 'absent')
        if differences:
            raise StampAborted('baseline changed before the stamp: ' + '; '.join(differences[:5]))
        config = alembic_config(target_url)
        config.attributes['connection'] = conn
        command.stamp(config, BASELINE)
        created_oid = _version_table_oid(pg)
        differences = _check(pg, expected, BASELINE)
        if differences:
            raise StampAborted('schema changed during the stamp; rolled back: ' + '; '.join(differences[:5]))
    with conn.begin():                                    # still under the session advisory lock
        differences = _post_commit_check(pg, expected)
    if differences:
        _compensate(conn, pg, expected, created_oid, differences)
    report.update(stamped=True, revision_state=BASELINE)
    return report


def _compensate(conn, pg, expected, created_oid, seen: list[str]) -> None:
    """Remove the stamp only if it is provably this operation's; otherwise change nothing."""
    with conn.begin():
        oid = _version_table_oid(pg)
        if oid is None:
            raise StampBlocker('post-commit check failed and the version table is gone; nothing changed: '
                               + '; '.join(seen[:5]))
        pg.execute(f'LOCK TABLE public.{catalog.ALEMBIC_VERSION_TABLE} IN ACCESS EXCLUSIVE MODE')
        state = catalog.revision_state(pg)
        drift = catalog.compare(expected, catalog.fingerprint(pg))
        if state != BASELINE or _version_table_oid(pg) != created_oid:
            raise StampBlocker(f'revision state {state} is not this operation\'s stamp; nothing changed: '
                               + '; '.join(seen[:5]))
        if not drift:
            raise StampBlocker('post-commit check saw differences that are gone on recheck: schema activity '
                               'outside JobFit tooling; stamp left in place for manual review: '
                               + '; '.join(seen[:5]))
        pg.execute(f'DROP TABLE public.{catalog.ALEMBIC_VERSION_TABLE}')
    raise StampAborted('schema drift after the stamp; this operation\'s stamp was removed: ' + '; '.join(drift[:5]))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('action', choices=['verify', 'stamp', 'reference'])
    parser.add_argument('--revision', default=BASELINE, help='reference only: revision to build')
    parser.add_argument('--allow-vector-version', action='append', default=[],
                        help='accept this pgvector version on the target (explicit, reviewed choice)')
    args = parser.parse_args(argv)
    url = os.environ.get('DATABASE_URL')
    if not url:
        print(json.dumps({'ok': False, 'error': 'DATABASE_URL must be set explicitly'}))
        return 2
    if args.action == 'reference':
        print(json.dumps({'revision': args.revision, **reference_fingerprint(url, args.revision)},
                         indent=1, sort_keys=True))
        return 0
    allowed = tuple(args.allow_vector_version)
    try:
        report = verify(url, allowed_vector_versions=allowed) if args.action == 'verify' else stamp(
            url, allowed_vector_versions=allowed)
    except StampAborted as exc:
        print(json.dumps({'ok': False, 'stamped': False, 'error': 'stamp_aborted', 'detail': str(exc)}, indent=1))
        return 2
    except StampBlocker as exc:
        print(json.dumps({'ok': False, 'stamped': False, 'error': 'stamp_blocker', 'detail': str(exc)}, indent=1))
        return 3
    print(json.dumps(report, indent=1, sort_keys=True))
    return 0 if report['ok'] else 2


if __name__ == '__main__':
    sys.exit(main())
