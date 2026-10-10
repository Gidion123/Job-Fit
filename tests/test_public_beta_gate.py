"""The controlled public beta (D-103) opens only when every gate holds; anything missing keeps it closed."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from jobfit.api.wiring import public_beta_open
from jobfit.config import get_production_settings
from jobfit.llm.public_beta_bounds import compute_public_beta_bounds

TRACED = SimpleNamespace(tracer=object())
UNTRACED = SimpleNamespace(tracer=None)
RUNTIME = SimpleNamespace(bounds=compute_public_beta_bounds())


def settings(**overrides):
    env = {'JOBFIT_ENV': 'prod', 'DATABASE_URL': 'postgresql://jobfit:x@db:5432/jobfit',
           'JOBFIT_INTERNAL_TOKEN': 'i' * 40, 'JOBFIT_OWNER_TOKEN': 'o' * 40, 'JOBFIT_IP_HMAC_KEY': 'h' * 40,
           'OPENROUTER_API_KEY': 'k' * 40, 'JOBFIT_USAGE_LEDGER': '/var/lib/jobfit/ledger/usage_ledger.jsonl',
           'JOBFIT_DAILY_BUDGET_USD': '5', 'API_HARD_STOP_USD': '25', 'API_BUDGET_USD': '25',
           'JOBFIT_LIVE_ENABLED': '1', 'JOBFIT_PUBLIC_LIVE': '1', 'JOBFIT_REAL_CV_ENABLED': '1', **overrides}
    return get_production_settings(env)


def test_the_beta_stays_closed_without_the_runtime_or_langfuse():
    s = SimpleNamespace(live_enabled=True, public_live=True, real_cv_enabled=True)
    assert public_beta_open(s, None, TRACED) is False
    assert public_beta_open(s, RUNTIME, UNTRACED) is False                  # D-103: Langfuse is required
    assert public_beta_open(s, RUNTIME, None) is False


@pytest.mark.parametrize('switch', ['JOBFIT_PUBLIC_LIVE', 'JOBFIT_REAL_CV_ENABLED'])
def test_the_beta_stays_closed_when_a_switch_is_off(switch):
    s = SimpleNamespace(live_enabled=True, public_live=True, real_cv_enabled=True)
    setattr(s, {'JOBFIT_PUBLIC_LIVE': 'public_live', 'JOBFIT_REAL_CV_ENABLED': 'real_cv_enabled'}[switch], False)
    assert public_beta_open(s, RUNTIME, TRACED) is False


def test_incomplete_settings_fail_closed_in_the_phase_check():
    s = SimpleNamespace(live_enabled=True, public_live=True, real_cv_enabled=True)  # not ProductionSettings
    assert public_beta_open(s, RUNTIME, TRACED) is False


def test_the_beta_opens_only_with_every_gate_and_a_daily_cap_that_fits_every_phase(monkeypatch):
    import jobfit.config as config                  # /var is a symlink on macOS; compare resolved paths there
    monkeypatch.setattr(config, 'PROD_LEDGER_ROOT', Path('/var/lib/jobfit/ledger').resolve())
    assert public_beta_open(settings(), RUNTIME, TRACED) is True
    assert public_beta_open(settings(), RUNTIME, UNTRACED) is False
    small = settings(JOBFIT_DAILY_BUDGET_USD='1', API_HARD_STOP_USD='25', API_BUDGET_USD='25')
    assert public_beta_open(small, RUNTIME, TRACED) is False                 # a phase bound above the cap
