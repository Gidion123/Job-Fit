"""Controlled public live override for the production VPS Compose (parsed, not run)."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OVERRIDE = yaml.safe_load((ROOT / 'deploy/public-live/docker-compose.public-live.yml').read_text())
SERVICES = OVERRIDE['services']


def env(service):
    return {k: str(v) for k, v in SERVICES[service]['environment'].items()}


def test_only_api_and_ui_environment_change():
    assert set(OVERRIDE) == {'services'} and set(SERVICES) == {'api', 'ui'}
    assert set(SERVICES['ui']) == {'environment'}                       # no ports, build or network changes
    assert set(SERVICES['api']) == {'environment', 'volumes'}
    assert SERVICES['api']['volumes'] == ['./reports/tokenizers:/app/reports/tokenizers:ro']


def test_public_live_stays_off_until_the_owner_switches_it_after_the_gate():
    api = env('api')
    assert api['JOBFIT_PUBLIC_LIVE'] == '${JOBFIT_PUBLIC_LIVE:-0}'
    assert api['JOBFIT_LIVE_ENABLED'] == '1' and api['JOBFIT_REAL_CV_ENABLED'] == '1'
    assert api['JOBFIT_LANGFUSE_ENABLED'] == '${JOBFIT_LANGFUSE_ENABLED:-0}'   # owner decision: optional, off


def test_secrets_come_from_the_env_file_and_budgets_are_unchanged():
    api = env('api')
    for name in ('OPENROUTER_API_KEY', 'JOBFIT_OWNER_TOKEN', 'JOBFIT_IP_HMAC_KEY'):
        assert api[name].startswith('${' + name + ':?')
    for name in ('LANGFUSE_PUBLIC_KEY', 'LANGFUSE_SECRET_KEY'):                # optional: no Langfuse keys needed
        assert api[name] == '${' + name + ':-}'
    assert not {'JOBFIT_DAILY_BUDGET_USD', 'API_HARD_STOP_USD', 'API_BUDGET_USD', 'JOBFIT_SESSION_ANALYSIS_LIMIT',
                'JOBFIT_USAGE_LEDGER', 'DATABASE_URL'} & set(api)


def test_the_public_ui_never_gets_the_owner_token_and_trusts_only_the_configured_proxy():
    ui = env('ui')
    assert set(ui) == {'JOBFIT_TRUSTED_PROXIES'}
    assert ui['JOBFIT_TRUSTED_PROXIES'].startswith('${JOBFIT_TRUSTED_PROXIES:?')
