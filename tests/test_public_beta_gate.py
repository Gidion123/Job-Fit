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


def test_the_beta_stays_closed_without_the_runtime_or_a_switched_on_langfuse():
    s = SimpleNamespace(live_enabled=True, public_live=True, real_cv_enabled=True)
    assert public_beta_open(s, None, TRACED) is False
    assert public_beta_open(s, None, UNTRACED, langfuse_required=False) is False
    assert public_beta_open(s, RUNTIME, UNTRACED) is False                  # switched on but did not start
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


def test_without_langfuse_the_demo_opens_but_every_other_gate_still_holds(monkeypatch):
    import jobfit.config as config
    monkeypatch.setattr(config, 'PROD_LEDGER_ROOT', Path('/var/lib/jobfit/ledger').resolve())
    off = {'langfuse_required': False}                                     # JOBFIT_LANGFUSE_ENABLED=0
    assert public_beta_open(settings(), RUNTIME, UNTRACED, **off) is True
    assert public_beta_open(settings(), None, UNTRACED, **off) is False
    assert public_beta_open(settings(JOBFIT_PUBLIC_LIVE='0'), RUNTIME, UNTRACED, **off) is False
    assert public_beta_open(settings(JOBFIT_REAL_CV_ENABLED='0'), RUNTIME, UNTRACED, **off) is False
    small = settings(JOBFIT_DAILY_BUDGET_USD='1', API_HARD_STOP_USD='25', API_BUDGET_USD='25')
    assert public_beta_open(small, RUNTIME, UNTRACED, **off) is False
    s = SimpleNamespace(live_enabled=True, public_live=True, real_cv_enabled=True)   # incomplete settings
    assert public_beta_open(s, RUNTIME, UNTRACED, **off) is False


@pytest.mark.parametrize('enabled, tracer, expected', [('0', None, True), ('', None, True), ('1', None, False)])
def test_the_api_wiring_requires_langfuse_only_when_it_is_switched_on(monkeypatch, enabled, tracer, expected):
    import jobfit.api.wiring as wiring
    seen = {}
    real = wiring.public_beta_open

    def spy(settings, runtime, telemetry, *, langfuse_required=True):
        seen['required'] = langfuse_required
        return real(SimpleNamespace(live_enabled=True, public_live=True, real_cv_enabled=True), RUNTIME,
                    SimpleNamespace(tracer=tracer), langfuse_required=langfuse_required)
    monkeypatch.setattr(wiring, 'public_beta_open', spy)
    monkeypatch.setattr('jobfit.llm.public_beta_bounds.public_beta_phase_eligible', lambda s, b: True)
    monkeypatch.setenv('JOBFIT_LANGFUSE_ENABLED', enabled)
    monkeypatch.setenv('JOBFIT_ENV', 'dev')
    monkeypatch.setenv('JOBFIT_LIVE_ENABLED', '0')
    monkeypatch.setenv('JOBFIT_PUBLIC_LIVE', '0')
    monkeypatch.setenv('JOBFIT_REAL_CV_ENABLED', '0')
    deps = wiring.build_deps()
    assert seen['required'] is (enabled == '1') and deps.public_beta_open is expected
