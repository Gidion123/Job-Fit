"""Owner-only Local Mac profile (D-105): a separate, production-like stack with no secrets in the repo.

The compose file is parsed, not run (no Docker here; the images are built by the CI docker-build job).
Its API environment, with placeholder secrets and budgets, must pass the real production settings
invariants, switch uploaded CVs on for the owner and keep public live off.
"""
import re
from pathlib import Path

import yaml

from jobfit.config import get_production_settings

ROOT = Path(__file__).resolve().parents[1]
OWNER = yaml.safe_load((ROOT / 'docker-compose.owner-local.yml').read_text())
BASE = yaml.safe_load((ROOT / 'docker-compose.yml').read_text())
REQUIRED = re.compile(r'^\$\{([A-Z_]+):\?[^}]+\}$')
SECRETS = ('OPENROUTER_API_KEY', 'JOBFIT_INTERNAL_TOKEN', 'JOBFIT_OWNER_TOKEN')
BUDGETS = ('JOBFIT_DAILY_BUDGET_USD', 'API_HARD_STOP_USD', 'API_BUDGET_USD')
PLACEHOLDER = {'OPENROUTER_API_KEY': 'k' * 40, 'JOBFIT_INTERNAL_TOKEN': 'i' * 40, 'JOBFIT_OWNER_TOKEN': 'o' * 40,
               'JOBFIT_DAILY_BUDGET_USD': '5', 'API_HARD_STOP_USD': '10', 'API_BUDGET_USD': '10'}


def env(service):
    return {k: str(v) for k, v in OWNER['services'][service]['environment'].items()}


def test_every_secret_and_budget_comes_from_the_owner_env_file_without_a_default():
    api, ui = env('api'), env('ui')
    for name in SECRETS + BUDGETS:
        assert REQUIRED.match(api[name]) and REQUIRED.match(api[name]).group(1) == name, name
    for name in ('JOBFIT_INTERNAL_TOKEN', 'JOBFIT_OWNER_TOKEN'):
        assert REQUIRED.match(ui[name]), name
    assert 'OPENROUTER_API_KEY' not in ui                                         # the UI never holds the key


def test_the_profile_is_owner_only_and_passes_the_production_invariants():
    api = env('api')
    assert (api['JOBFIT_ENV'], api['JOBFIT_LIVE_ENABLED'], api['JOBFIT_PUBLIC_LIVE'],
            api['JOBFIT_REAL_CV_ENABLED']) == ('prod', '1', '0', '1')
    resolved = {k: PLACEHOLDER.get(REQUIRED.match(v).group(1)) if REQUIRED.match(v) else v for k, v in api.items()}
    settings = get_production_settings(resolved)
    assert settings.real_cv_enabled and settings.live_enabled and not settings.public_live
    assert str(settings.usage_ledger) == '/var/lib/jobfit/ledger/usage_ledger.jsonl'


def test_storage_and_tokenizer_mounts():
    volumes = OWNER['services']['api']['volumes']
    assert 'jobfit_owner_ledger:/var/lib/jobfit/ledger' in volumes
    assert './reports/tokenizers:/app/reports/tokenizers:ro' in volumes
    assert set(OWNER['volumes']) == {'jobfit_owner_pgdata', 'jobfit_owner_ledger'}


def test_it_never_collides_with_or_reuses_the_cp2_stack():
    names = {s['container_name'] for s in OWNER['services'].values()}
    base_names = {s['container_name'] for s in BASE['services'].values()}
    ports = {p for s in OWNER['services'].values() for p in s.get('ports', [])}
    base_ports = {p for s in BASE['services'].values() for p in s.get('ports', [])}
    host = lambda ps: {p.rsplit(':', 1)[0] for p in ps}                         # noqa: E731
    assert not names & base_names and not host(ports) & host(base_ports)
    assert all(p.startswith('127.0.0.1:') for p in ports)
    assert 'jobfit_pgdata' not in OWNER['volumes']                               # never the CP2 database volume


def test_the_real_cv_switch_is_only_in_the_owner_profile():
    for service in BASE['services'].values():
        assert 'JOBFIT_REAL_CV_ENABLED' not in (service.get('environment') or {})
        assert 'JOBFIT_OWNER_TOKEN' not in (service.get('environment') or {})
    assert str(BASE['services']['api']['environment']['JOBFIT_LIVE_ENABLED']) == '0'
