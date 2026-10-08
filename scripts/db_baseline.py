"""Verify an existing CP2 database against Alembic 0001, and stamp it only if it matches (D-098).

    python scripts/db_baseline.py verify     # read-only comparison, exit 0 only on an exact match
    python scripts/db_baseline.py stamp      # verify again, then `alembic stamp 0001`
    python scripts/db_baseline.py reference --revision 0002   # print a reference fingerprint

The target is the database in DATABASE_URL (required; never printed). The reference is built
fresh on the same server: a scratch database is created, upgraded through the Alembic revisions
and fingerprinted, then dropped (CREATEDB privilege needed). The target itself is only read,
except by `stamp`, which writes the Alembic version row after a successful verification.

A database that already has an Alembic version table is refused: a stamp is only ever the
first stamp. Any difference fails closed; it is reported structurally, without row data.
Never run a bare `alembic stamp` on an existing database.
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
from sqlalchemy.engine import make_url

from jobfit.db import catalog
from jobfit.db.migrate import alembic_config

BASELINE = '0001'


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


def verify(target_url: str, *, allowed_vector_versions: tuple[str, ...] = ()) -> dict:
    state, actual = read_target(target_url)
    expected = reference_fingerprint(target_url, BASELINE)
    differences = catalog.compare(expected, actual)
    if state != 'absent':
        differences.insert(0, f'alembic version table: expected absent, found {state}')
    want = expected['environment']['extension_versions'].get('vector')
    have = actual['environment']['extension_versions'].get('vector')
    if have != want and have not in allowed_vector_versions:
        differences.append(f'environment/vector version: expected {want!r}, found {have!r}')
    return {'ok': not differences, 'revision_state': state, 'differences': differences,
            'environment': {'target': actual['environment'], 'reference': expected['environment']}}


def stamp(target_url: str, *, allowed_vector_versions: tuple[str, ...] = ()) -> dict:
    report = verify(target_url, allowed_vector_versions=allowed_vector_versions)
    if not report['ok']:
        report['stamped'] = False
        return report
    _, before = read_target(target_url)
    command.stamp(alembic_config(target_url), BASELINE)
    state, after = read_target(target_url)
    if state != BASELINE or catalog.compare(before, after):
        raise RuntimeError('stamp did not leave exactly revision 0001 with an unchanged schema')
    report.update(stamped=True, revision_state=state)
    return report


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
    report = verify(url, allowed_vector_versions=allowed) if args.action == 'verify' else stamp(
        url, allowed_vector_versions=allowed)
    print(json.dumps(report, indent=1, sort_keys=True))
    return 0 if report['ok'] else 2


if __name__ == '__main__':
    sys.exit(main())
