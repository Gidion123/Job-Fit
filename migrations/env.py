"""Alembic environment for the CP3 production schema (D-098).

Raw-SQL revisions only: there are no SQLAlchemy models and no autogenerate. The database URL
comes from ``config.attributes['database_url']`` (programmatic use) or an explicit
``DATABASE_URL``; there is no fallback to the local development database, and the URL is never
printed. All revisions of one command run in a single transaction, so a failed upgrade leaves
no partial schema and no version row behind.
"""
from __future__ import annotations

import os

from alembic import context
from sqlalchemy import create_engine, pool

from jobfit.db.migrate import ALEMBIC_VERSION_TABLE, sqlalchemy_url

config = context.config


def database_url() -> str:
    url = config.attributes.get('database_url') or os.environ.get('DATABASE_URL')
    if not url:
        raise RuntimeError('DATABASE_URL must be set explicitly for migrations')
    return sqlalchemy_url(url)


def run_migrations_online() -> None:
    engine = create_engine(database_url(), poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=None,
                              version_table=ALEMBIC_VERSION_TABLE, transaction_per_migration=False)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    raise RuntimeError('offline SQL generation is not supported; run against a database')
run_migrations_online()
