"""Alembic revisions and the catalog helper, without a database (CP3, D-098)."""
import ast
import hashlib
import importlib.util
import inspect
import json
import re
import textwrap

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from jobfit.config import REPO_ROOT
from jobfit.db import catalog
from jobfit.db.migrate import ALEMBIC_INI, alembic_config, sqlalchemy_url
from jobfit.db.models import SCHEMA_SQL

VERSIONS = REPO_ROOT / 'migrations/versions'
SCHEMA_SQL_SHA256 = '38abfee02611336eb1355090843a7231c9e46f93a256ea660d310f63070250b3'   # CP2 SCHEMA_SQL, 7 Oct 2026
ERROR_CODE = r'[A-Za-z_][A-Za-z0-9_]{0,63}'   # jd_extraction_cache_state_check, failed rows


def revision_module(name):
    spec = importlib.util.spec_from_file_location(name, VERSIONS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_revisions_form_one_linear_chain():
    script = ScriptDirectory.from_config(alembic_config('postgresql://unused/unused'))
    assert script.get_heads() == ['0002']
    assert script.get_revision('0002').down_revision == '0001'
    assert script.get_revision('0001').down_revision is None
    assert sorted(p.name for p in VERSIONS.glob('*.py')) == ['0001_cp2_baseline.py', '0002_cp3_production.py']


def test_0001_is_an_immutable_literal_copy_of_the_cp2_schema_sql():
    m = revision_module('0001_cp2_baseline')
    assert m.SCHEMA_SQL == SCHEMA_SQL                                          # same bytes as models.py today
    assert hashlib.sha256(m.SCHEMA_SQL.encode()).hexdigest() == m.SCHEMA_SQL_SHA256 == SCHEMA_SQL_SHA256


@pytest.mark.parametrize('name', ['0001_cp2_baseline', '0002_cp3_production'])
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


@pytest.mark.parametrize('name', ['0001_cp2_baseline', '0002_cp3_production'])
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


def stage_failure_codes() -> set[str]:
    """Every value StageFailure.code (and the extraction result) can take, as far as it is enumerable."""
    import builtins
    import httpx
    import openai
    import jobfit.llm.client as client
    import jobfit.llm.budget as budget
    from jobfit.llm.structured import validated_call
    tree = ast.parse(textwrap.dedent(inspect.getsource(validated_call)))
    literal = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
               and re.fullmatch(r'[A-Za-z_]+', n.value)}
    # validated_call falls back to type(exc).__name__ for unexpected exceptions.
    names = {v.__name__ for mod in (openai, httpx, builtins, client, budget) for v in list(vars(mod).values())
             if isinstance(v, type) and issubclass(v, BaseException)}
    return literal | names | {'empty_or_oversize_JD'}


def test_every_stage_failure_code_fits_the_negative_cache_constraint():
    source = (VERSIONS / '0002_cp3_production.py').read_text()
    assert f"error_code ~ '^{ERROR_CODE}$'" in source
    codes = stage_failure_codes()
    assert {'schema_validation', 'truncated', 'APITimeoutError', 'BudgetExceeded', 'qualified_MATCH_needs_bounded_duration',
            'invalid_structured_output_or_source'} <= codes
    assert all(re.fullmatch(ERROR_CODE, c) for c in codes), sorted(c for c in codes if not re.fullmatch(ERROR_CODE, c))


@pytest.mark.parametrize('revision', ['0001', '0002'])
def test_pinned_fingerprints_describe_only_application_objects(revision):
    pin = json.loads((REPO_ROOT / f'migrations/catalog/{revision}.json').read_text())
    assert pin['revision'] == revision and set(pin) == {'revision', 'objects'}
    assert 'alembic_version' not in pin['objects']['tables']
    assert {'jobs', 'job_embeddings', 'job_embedding_versions'} <= set(pin['objects']['tables'])
    assert ['vector', 'public'] in pin['objects']['extensions']


def test_0002_pin_adds_to_0001_without_changing_its_objects():
    old, new = (json.loads((REPO_ROOT / f'migrations/catalog/{r}.json').read_text())['objects'] for r in ('0001', '0002'))
    for table, entry in old['tables'].items():
        added = new['tables'][table]
        for key in ('constraints', 'indexes'):
            assert [x for x in entry[key]] == [x for x in added[key] if x in entry[key]]
            assert all(x in added[key] for x in entry[key])
        assert added['columns'][:len(entry['columns'])] == entry['columns']   # 0001 columns unchanged, in order


def test_compare_reports_structure_without_row_data():
    base = {'objects': {'tables': {'jobs': {'kind': 'r', 'columns': [['job_id', 'text', True, None, '', '', None]]}},
                        'extensions': [['vector', 'public']]}}
    same = json.loads(json.dumps(base))
    assert catalog.compare(base, same) == []
    other = json.loads(json.dumps(base))
    other['objects']['tables']['jobs']['columns'][0][1] = 'integer'
    other['objects']['tables']['extra'] = {'kind': 'r'}
    del other['objects']['extensions']
    diffs = catalog.compare(base, other)
    assert any(d.startswith('/tables/jobs/columns') for d in diffs)
    assert '/tables/extra: unexpected' in diffs and '/extensions: missing' in diffs
