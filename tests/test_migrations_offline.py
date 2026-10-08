"""Alembic revisions and the catalog helper, without a database (CP3, D-098)."""
import pytest
from alembic import command
from alembic.config import Config

from jobfit.db.migrate import ALEMBIC_INI, alembic_config, sqlalchemy_url


def test_migrations_require_an_explicit_database_url(monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    with pytest.raises(RuntimeError, match='DATABASE_URL must be set explicitly'):
        command.upgrade(Config(str(ALEMBIC_INI)), 'head')
    with pytest.raises(ValueError):
        alembic_config('')


def test_offline_sql_generation_is_refused():
    with pytest.raises(RuntimeError, match='offline SQL generation is not supported'):
        command.upgrade(alembic_config('postgresql://unused/unused'), 'head', sql=True)


def test_urls_select_psycopg3():
    assert sqlalchemy_url('postgresql://u:p@h:5432/d') == 'postgresql+psycopg://u:p@h:5432/d'
    assert sqlalchemy_url('postgres://h/d') == 'postgresql+psycopg://h/d'
    assert sqlalchemy_url('postgresql+psycopg://h/d') == 'postgresql+psycopg://h/d'
    with pytest.raises(ValueError):
        sqlalchemy_url('mysql://h/d')
