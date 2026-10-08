"""Alembic revisions and the catalog helper, without a database (CP3, D-098)."""
import ast
import hashlib
import importlib.util

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from jobfit.config import REPO_ROOT
from jobfit.db.migrate import ALEMBIC_INI, alembic_config, sqlalchemy_url
from jobfit.db.models import SCHEMA_SQL

VERSIONS = REPO_ROOT / 'migrations/versions'
SCHEMA_SQL_SHA256 = '38abfee02611336eb1355090843a7231c9e46f93a256ea660d310f63070250b3'   # CP2 SCHEMA_SQL, 7 Oct 2026


def revision_module(name):
    spec = importlib.util.spec_from_file_location(name, VERSIONS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_revisions_form_one_linear_chain():
    script = ScriptDirectory.from_config(alembic_config('postgresql://unused/unused'))
    assert script.get_heads() == ['0001']
    assert script.get_revision('0001').down_revision is None
    assert sorted(p.name for p in VERSIONS.glob('*.py')) == ['0001_cp2_baseline.py']


def test_0001_is_an_immutable_literal_copy_of_the_cp2_schema_sql():
    m = revision_module('0001_cp2_baseline')
    assert m.SCHEMA_SQL == SCHEMA_SQL                                          # same bytes as models.py today
    assert hashlib.sha256(m.SCHEMA_SQL.encode()).hexdigest() == m.SCHEMA_SQL_SHA256 == SCHEMA_SQL_SHA256


@pytest.mark.parametrize('name', ['0001_cp2_baseline'])
def test_revisions_never_import_application_code(name):
    tree = ast.parse((VERSIONS / f'{name}.py').read_text())
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    imported |= {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert imported <= {'os', 'alembic', 'sqlalchemy'}, imported


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


@pytest.mark.parametrize('name', ['0001_cp2_baseline'])
def test_destructive_downgrade_is_guarded(monkeypatch, name):
    guard = revision_module(name).require_destructive_downgrade
    for env in ({}, {'JOBFIT_ALLOW_DESTRUCTIVE_DOWNGRADE': '1', 'JOBFIT_ENV': 'prod'},
                {'JOBFIT_ALLOW_DESTRUCTIVE_DOWNGRADE': 'true'}):
        monkeypatch.delenv('JOBFIT_ALLOW_DESTRUCTIVE_DOWNGRADE', raising=False)
        monkeypatch.delenv('JOBFIT_ENV', raising=False)
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        with pytest.raises(RuntimeError, match='destructive downgrade'):
            guard()
    monkeypatch.setenv('JOBFIT_ALLOW_DESTRUCTIVE_DOWNGRADE', '1')
    monkeypatch.setenv('JOBFIT_ENV', 'dev')
    guard()
