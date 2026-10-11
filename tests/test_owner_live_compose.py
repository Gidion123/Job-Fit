"""Owner-only live demo override for the production VPS Compose (parsed, not run).

The override turns live and uploaded-CV processing on for the owner only, adds a localhost-only owner UI
and mounts the pinned query tokenizer. It never touches the public UI, public live, budgets or ports.
"""
from pathlib import Path

import pytest
import yaml

from jobfit.config import get_production_settings

ROOT = Path(__file__).resolve().parents[1]
OVERRIDE = yaml.safe_load((ROOT / 'deploy/owner-live/docker-compose.owner-live.yml').read_text())
SERVICES = OVERRIDE['services']


def test_only_the_api_and_a_private_owner_ui_are_changed():
    assert set(SERVICES) == {'api', 'ui-owner'}                      # db and the public ui are untouched
    assert set(OVERRIDE) == {'services'}                              # no networks, volumes or Caddy changes


def test_the_api_goes_live_for_the_owner_only_with_unchanged_budgets():
    api = {k: str(v) for k, v in SERVICES['api']['environment'].items()}
    assert api['JOBFIT_LIVE_ENABLED'] == '1' and api['JOBFIT_REAL_CV_ENABLED'] == '1'
    assert api['JOBFIT_PUBLIC_LIVE'] == '0'
    assert not {'JOBFIT_DAILY_BUDGET_USD', 'API_HARD_STOP_USD', 'API_BUDGET_USD', 'JOBFIT_SESSION_ANALYSIS_LIMIT',
                'JOBFIT_LANGFUSE_ENABLED', 'JOBFIT_USAGE_LEDGER', 'DATABASE_URL'} & set(api)
    for name in ('OPENROUTER_API_KEY', 'JOBFIT_OWNER_TOKEN'):
        assert api[name].startswith('${' + name + ':?')                 # from .env.prod, no default, no value
    assert 'ports' not in SERVICES['api']
    assert SERVICES['api']['volumes'] == ['./reports/tokenizers:/app/reports/tokenizers:ro']


def test_the_owner_ui_is_localhost_only_and_carries_the_owner_token_server_side():
    owner = SERVICES['ui-owner']
    assert owner['ports'] == ['127.0.0.1:8511:8501']
    env = {k: str(v) for k, v in owner['environment'].items()}
    assert env['JOBFIT_OWNER_TOKEN'].startswith('${JOBFIT_OWNER_TOKEN:?')
    assert env['JOBFIT_API_URL'] == 'http://api:8000' and env['JOBFIT_INTERNAL_TOKEN'].startswith('${')
    assert 'OPENROUTER_API_KEY' not in env
    assert owner['networks'] == ['application_net'] and owner['build']['dockerfile'] == 'Dockerfile.ui'


@pytest.mark.skipif(Path('/var').resolve() != Path('/var'), reason='/var is a symlink here (macOS); CI runs it')
def test_the_merged_api_environment_passes_the_production_invariants():
    env = {'JOBFIT_ENV': 'prod', 'DATABASE_URL': 'postgresql://jobfit:x@db:5432/jobfit',
           'JOBFIT_INTERNAL_TOKEN': 'i' * 40, 'JOBFIT_USAGE_LEDGER': '/var/lib/jobfit/ledger/usage_ledger.jsonl',
           'JOBFIT_DAILY_BUDGET_USD': '5', 'API_HARD_STOP_USD': '25', 'API_BUDGET_USD': '25',
           'OPENROUTER_API_KEY': 'k' * 40, 'JOBFIT_OWNER_TOKEN': 'o' * 40,
           **{k: str(v) for k, v in SERVICES['api']['environment'].items() if not str(v).startswith('${')}}
    s = get_production_settings(env)
    assert s.live_enabled and s.real_cv_enabled and not s.public_live
