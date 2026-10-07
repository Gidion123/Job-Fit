"""Fail-closed CP3 production settings (D-095, D-096; FAIL-38). No provider call is made."""
import pytest

from jobfit.config import (REPO_USAGE_LEDGER, ConfigurationError, ProductionSettings, Settings,
                           get_production_settings)

TOKEN = 'x' * 32
PROD_DB = 'postgresql://jobfit:secret@db:5432/jobfit_prod'


def prod_env(tmp_path, **extra):
    env = {'JOBFIT_ENV': 'prod', 'DATABASE_URL': PROD_DB, 'JOBFIT_INTERNAL_TOKEN': TOKEN}
    env.update(extra)
    return env


def live_prod_env(tmp_path, **extra):
    env = prod_env(tmp_path, JOBFIT_LIVE_ENABLED='1', OPENROUTER_API_KEY='sk-test',
                   JOBFIT_OWNER_TOKEN='o' * 32, JOBFIT_USAGE_LEDGER=str(tmp_path / 'ledger.jsonl'),
                   JOBFIT_DAILY_BUDGET_USD='2', API_BUDGET_USD='10', API_HARD_STOP_USD='9.5')
    env.update(extra)
    return env


def test_defaults_are_safe_dev_with_live_and_public_live_off():
    s = get_production_settings({})
    assert s == ProductionSettings()
    assert s.environment == 'dev' and not s.live_enabled and not s.public_live
    assert s.openrouter_api_key is None and s.daily_budget_usd is None


def test_dev_live_needs_only_an_explicit_flag_and_a_key():
    s = get_production_settings({'JOBFIT_LIVE_ENABLED': '1', 'OPENROUTER_API_KEY': 'sk-test'})
    assert s.live_enabled and not s.public_live
    with pytest.raises(ConfigurationError, match='OPENROUTER_API_KEY'):
        get_production_settings({'JOBFIT_LIVE_ENABLED': '1'})


@pytest.mark.parametrize('name', ['JOBFIT_LIVE_ENABLED', 'JOBFIT_PUBLIC_LIVE'])
@pytest.mark.parametrize('value', ['true', 'yes', '2', 'on', ''])
def test_flags_accept_only_zero_or_one(name, value):
    with pytest.raises(ConfigurationError, match=name):
        get_production_settings({name: value})


def test_unknown_environment_is_rejected():
    with pytest.raises(ConfigurationError, match='JOBFIT_ENV'):
        get_production_settings({'JOBFIT_ENV': 'production'})


def test_public_live_without_live_is_a_contradiction(tmp_path):
    env = live_prod_env(tmp_path, JOBFIT_PUBLIC_LIVE='1', JOBFIT_LIVE_ENABLED='0', JOBFIT_IP_HMAC_KEY=TOKEN)
    with pytest.raises(ConfigurationError, match='requires JOBFIT_LIVE_ENABLED=1'):
        get_production_settings(env)


def test_public_live_requires_prod():
    env = {'JOBFIT_LIVE_ENABLED': '1', 'JOBFIT_PUBLIC_LIVE': '1', 'OPENROUTER_API_KEY': 'sk-test',
           'JOBFIT_IP_HMAC_KEY': TOKEN}
    with pytest.raises(ConfigurationError, match='requires JOBFIT_ENV=prod'):
        get_production_settings(env)


def test_prod_requires_an_explicit_non_default_database_url(tmp_path):
    env = prod_env(tmp_path)
    del env['DATABASE_URL']
    with pytest.raises(ConfigurationError, match='DATABASE_URL must be set'):
        get_production_settings(env)
    with pytest.raises(ConfigurationError, match='development default'):
        get_production_settings(prod_env(tmp_path, DATABASE_URL=Settings.database_url))


def test_prod_requires_the_internal_token_even_when_dark(tmp_path):
    s = get_production_settings(prod_env(tmp_path))
    assert s.environment == 'prod' and not s.live_enabled and s.internal_token == TOKEN
    with pytest.raises(ConfigurationError, match='JOBFIT_INTERNAL_TOKEN'):
        get_production_settings(prod_env(tmp_path, JOBFIT_INTERNAL_TOKEN='short'))


def test_dark_deploy_owner_live_needs_owner_token_ledger_and_budgets(tmp_path):
    s = get_production_settings(live_prod_env(tmp_path))
    assert s.live_enabled and not s.public_live and s.owner_token
    assert s.daily_budget_usd == 2.0 and s.api_budget_usd == 10.0 and s.api_hard_stop_usd == 9.5
    for name in ('JOBFIT_OWNER_TOKEN', 'JOBFIT_USAGE_LEDGER', 'JOBFIT_DAILY_BUDGET_USD',
                 'API_BUDGET_USD', 'API_HARD_STOP_USD', 'OPENROUTER_API_KEY'):
        env = live_prod_env(tmp_path)
        del env[name]
        with pytest.raises(ConfigurationError, match=name):
            get_production_settings(env)


@pytest.mark.parametrize('value', ['0', '-1', 'nan', 'inf', 'abc'])
def test_budget_values_must_be_finite_and_positive(tmp_path, value):
    with pytest.raises(ConfigurationError, match='JOBFIT_DAILY_BUDGET_USD'):
        get_production_settings(live_prod_env(tmp_path, JOBFIT_DAILY_BUDGET_USD=value))


def test_budget_ordering_is_enforced(tmp_path):
    with pytest.raises(ConfigurationError, match='API_HARD_STOP_USD must not be above'):
        get_production_settings(live_prod_env(tmp_path, API_HARD_STOP_USD='11'))
    with pytest.raises(ConfigurationError, match='JOBFIT_DAILY_BUDGET_USD must not be above'):
        get_production_settings(live_prod_env(tmp_path, JOBFIT_DAILY_BUDGET_USD='9.6'))


def test_prod_rejects_the_repository_development_ledger(tmp_path):
    with pytest.raises(ConfigurationError, match='repository development ledger'):
        get_production_settings(live_prod_env(tmp_path, JOBFIT_USAGE_LEDGER=str(REPO_USAGE_LEDGER)))


def test_public_live_requires_the_ip_hmac_key(tmp_path):
    env = live_prod_env(tmp_path, JOBFIT_PUBLIC_LIVE='1')
    with pytest.raises(ConfigurationError, match='JOBFIT_IP_HMAC_KEY'):
        get_production_settings(env)
    s = get_production_settings(live_prod_env(tmp_path, JOBFIT_PUBLIC_LIVE='1', JOBFIT_IP_HMAC_KEY=TOKEN))
    assert s.public_live and s.live_enabled


def test_secrets_never_appear_in_repr_or_errors(tmp_path):
    s = get_production_settings(live_prod_env(tmp_path, JOBFIT_PUBLIC_LIVE='1', JOBFIT_IP_HMAC_KEY='h' * 32))
    text = repr(s)
    for secret in ('sk-test', TOKEN, 'o' * 32, 'h' * 32, PROD_DB):
        assert secret not in text
    with pytest.raises(ConfigurationError) as exc:
        get_production_settings(live_prod_env(tmp_path, JOBFIT_DAILY_BUDGET_USD='not-a-secret-number'))
    assert 'not-a-secret-number' not in str(exc.value)


def test_client_settings_keep_the_lifetime_guard_on_the_production_ledger(tmp_path):
    s = get_production_settings(live_prod_env(tmp_path))
    c = s.client_settings()
    assert c.usage_ledger == (tmp_path / 'ledger.jsonl').resolve()
    assert (c.api_budget_usd, c.api_hard_stop_usd) == (10.0, 9.5)


def test_wiring_live_is_off_by_default_and_follows_the_settings(monkeypatch):
    from jobfit.api import wiring
    import jobfit.config
    monkeypatch.setattr(jobfit.config, '_load_dotenv', lambda: None)  # independent of a local .env
    for name in ('JOBFIT_ENV', 'JOBFIT_LIVE_ENABLED', 'JOBFIT_PUBLIC_LIVE'):
        monkeypatch.delenv(name, raising=False)
    assert wiring.live_enabled() is False
    monkeypatch.setenv('JOBFIT_LIVE_ENABLED', '1')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-test')
    assert wiring.live_enabled() is True
    monkeypatch.setenv('JOBFIT_PUBLIC_LIVE', '1')
    with pytest.raises(ConfigurationError):
        wiring.live_enabled()
