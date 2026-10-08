"""Alembic plumbing for the CP3 production schema (D-098). The URL is never printed."""
from __future__ import annotations

from alembic.config import Config

from jobfit.config import REPO_ROOT

ALEMBIC_INI = REPO_ROOT / 'alembic.ini'
ALEMBIC_VERSION_TABLE = 'alembic_version'
# Advisory-lock key that serializes every cooperating JobFit schema operation: migrations/env.py
# takes it per migration transaction, and the guarded baseline stamp holds it for its whole run.
SCHEMA_LOCK_KEY = 5363645930281649010


def sqlalchemy_url(url: str) -> str:
    """psycopg 3 URL for SQLAlchemy (the bare postgresql:// scheme would select psycopg2)."""
    for prefix in ('postgresql+psycopg://', 'postgresql://', 'postgres://'):
        if url.startswith(prefix):
            return 'postgresql+psycopg://' + url[len(prefix):]
    raise ValueError('DATABASE_URL must be a postgresql:// URL')


def alembic_config(database_url: str) -> Config:
    """Alembic config for one explicit database; migrations/env.py reads the URL from it."""
    if not database_url:
        raise ValueError('an explicit database URL is required')
    config = Config(str(ALEMBIC_INI))
    config.attributes['database_url'] = database_url
    return config
