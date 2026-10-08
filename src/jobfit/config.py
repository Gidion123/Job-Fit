"""Settings from environment variables and the git-ignored .env file (DECISIONS D-028).

Keys are never printed, logged, or written anywhere else. repr() hides them.
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

# Versions written into every stored output, so results can be traced (System Design v1.3 section 12).
SNAPSHOT_ID = "CP1_20260926"
SCHEMA_VERSION = "v1"
SCORE_VERSION = "v1"  # PARTIAL weight 0.5; soft skills and constraints outside the % (D-032, D-033)
_PIPELINE = yaml.safe_load((REPO_ROOT / 'config/pipeline_v1.yaml').read_text())
GUIDELINE_VERSION = _PIPELINE['guideline_version']
GUIDELINE_FILE = REPO_ROOT / _PIPELINE['guideline_file']
JD_PROMPT_FILE = REPO_ROOT / _PIPELINE['jd_prompt_file']
JD_PROMPT_VERSION = _PIPELINE['jd_prompt_version']
EVIDENCE_PROMPT_FILE = REPO_ROOT / _PIPELINE['evidence_prompt_file']
EVIDENCE_PROMPT_VERSION = _PIPELINE['evidence_prompt_version']
EVIDENCE_VALIDATOR = _PIPELINE.get('evidence_validator', 'quote-check-v1.0')
EVIDENCE_GUARDRAILS = tuple(_PIPELINE.get('evidence_guardrails', []))
PROMPT_VERSION = JD_PROMPT_VERSION  # compatibility alias; metadata names each stage explicitly

def runtime_versions() -> dict:
    """Actual runtime provenance; never use this to relabel historical artifacts."""
    files={'guideline':GUIDELINE_FILE,'jd_prompt':JD_PROMPT_FILE,'evidence_prompt':EVIDENCE_PROMPT_FILE}
    return {'guideline_version':GUIDELINE_VERSION,'jd_prompt_version':JD_PROMPT_VERSION,
            'evidence_prompt_version':EVIDENCE_PROMPT_VERSION,'schema_version':SCHEMA_VERSION,'score_version':SCORE_VERSION,
            **{k+'_file':str(p.relative_to(REPO_ROOT)) for k,p in files.items()},
            **{k+'_sha256':hashlib.sha256(p.read_bytes()).hexdigest() for k,p in files.items()}}


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:  # python-dotenv is in requirements.txt; tests do not need it
        return
    load_dotenv(REPO_ROOT / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str | None = field(default=None, repr=False)
    database_url: str = "postgresql://jobfit:jobfit@localhost:5434/jobfit"
    # Budget values come from .env (D-019, D-031). These defaults match .env.example.
    api_budget_usd: float = 5.0
    api_hard_stop_usd: float = 4.5
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    models_file: Path = REPO_ROOT / "config" / "models_v1.yaml"
    usage_ledger: Path = REPO_ROOT / "reports" / "usage" / "usage_ledger.jsonl"

    @property
    def has_openrouter_key(self) -> bool:
        return bool(self.openrouter_api_key)


def get_settings() -> Settings:
    _load_dotenv()
    return Settings(
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY") or None,
        database_url=os.getenv("DATABASE_URL", Settings.database_url),
        api_budget_usd=float(os.getenv("API_BUDGET_USD", str(Settings.api_budget_usd))),
        api_hard_stop_usd=float(os.getenv("API_HARD_STOP_USD", str(Settings.api_hard_stop_usd))),
    )


# --- CP3 production settings (D-095, D-096; FAIL-38) -------------------------------------------
# Used only by the API/wiring path. Scripts and CP2 runners keep Settings/get_settings above.
# Live analysis is off unless it is switched on explicitly and completely configured.

class ConfigurationError(ValueError):
    """Production settings are missing, invalid or contradictory. Messages never contain values."""


MIN_SECRET_LENGTH = 32
REPO_USAGE_LEDGER = Settings.usage_ledger


def _flag(env, name: str) -> bool:
    raw = env.get(name, '0').strip()
    if raw not in ('0', '1'):
        raise ConfigurationError(f'{name} must be 0 or 1')
    return raw == '1'


def _money(env, name: str) -> float:
    raw = (env.get(name) or '').strip()
    if not raw:
        raise ConfigurationError(f'{name} must be set explicitly')
    try:
        value = float(raw)
    except ValueError:
        raise ConfigurationError(f'{name} must be a number') from None
    return _check_money(value, name)


def _check_money(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigurationError(f'{name} must be a number')
    if not (value > 0 and math.isfinite(value)):
        raise ConfigurationError(f'{name} must be finite and greater than 0')
    return value


def _check_secret(value, name: str) -> None:
    if not isinstance(value, str) or len(value) < MIN_SECRET_LENGTH:
        raise ConfigurationError(f'{name} must be set (at least {MIN_SECRET_LENGTH} characters)')


def check_production_invariants(s: 'ProductionSettings') -> None:
    """The one set of production rules. Runs on every construction and again before eligibility."""
    if s.environment not in ('dev', 'prod'):
        raise ConfigurationError('JOBFIT_ENV must be dev or prod')
    for name, flag in (('JOBFIT_LIVE_ENABLED', s.live_enabled), ('JOBFIT_PUBLIC_LIVE', s.public_live)):
        if not isinstance(flag, bool):
            raise ConfigurationError(f'{name} must be 0 or 1')
    prod = s.environment == 'prod'
    if s.public_live and not s.live_enabled:
        raise ConfigurationError('JOBFIT_PUBLIC_LIVE=1 requires JOBFIT_LIVE_ENABLED=1')
    if s.public_live and not prod:
        raise ConfigurationError('JOBFIT_PUBLIC_LIVE=1 requires JOBFIT_ENV=prod')
    if prod:
        if not isinstance(s.database_url, str) or not s.database_url:
            raise ConfigurationError('DATABASE_URL must be set explicitly in prod')
        if s.database_url == Settings.database_url:
            raise ConfigurationError('DATABASE_URL must not be the local development default in prod')
        _check_secret(s.internal_token, 'JOBFIT_INTERNAL_TOKEN')
    if s.live_enabled and not s.openrouter_api_key:
        raise ConfigurationError('OPENROUTER_API_KEY must be set when live analysis is enabled')
    if s.live_enabled and prod:
        _check_secret(s.owner_token, 'JOBFIT_OWNER_TOKEN')
        if Path(s.usage_ledger).resolve() == REPO_USAGE_LEDGER.resolve():
            raise ConfigurationError('JOBFIT_USAGE_LEDGER must not be the repository development ledger')
        daily = _check_money(s.daily_budget_usd, 'JOBFIT_DAILY_BUDGET_USD')
        budget = _check_money(s.api_budget_usd, 'API_BUDGET_USD')
        hard_stop = _check_money(s.api_hard_stop_usd, 'API_HARD_STOP_USD')
        if hard_stop > budget:
            raise ConfigurationError('API_HARD_STOP_USD must not be above API_BUDGET_USD')
        if daily > hard_stop:
            raise ConfigurationError('JOBFIT_DAILY_BUDGET_USD must not be above API_HARD_STOP_USD')
    if s.public_live:
        _check_secret(s.ip_hmac_key, 'JOBFIT_IP_HMAC_KEY')


@dataclass(frozen=True)
class ProductionSettings:
    environment: str = 'dev'
    live_enabled: bool = False
    public_live: bool = False
    database_url: str = field(default=Settings.database_url, repr=False)
    openrouter_api_key: str | None = field(default=None, repr=False)
    internal_token: str | None = field(default=None, repr=False)
    owner_token: str | None = field(default=None, repr=False)
    ip_hmac_key: str | None = field(default=None, repr=False)
    usage_ledger: Path = REPO_USAGE_LEDGER
    # D-096 calendar-day admission cap, enforced by the Phase 2B adapter (not by BudgetGuard).
    daily_budget_usd: float | None = None
    # Lifetime ceiling of the usage ledger, consumed by the frozen BudgetGuard (D-031).
    api_budget_usd: float = Settings.api_budget_usd
    api_hard_stop_usd: float = Settings.api_hard_stop_usd

    def __post_init__(self):
        # Direct construction and dataclasses.replace() are validated too, not only get_production_settings().
        check_production_invariants(self)

    def client_settings(self) -> Settings:
        """Settings for the frozen OpenRouter client: lifetime guard over this ledger.

        Not yet used by the live client: the API wiring still builds it from get_settings();
        switching it to these settings is Phase 2B work.
        """
        return Settings(openrouter_api_key=self.openrouter_api_key, database_url=self.database_url,
                        api_budget_usd=self.api_budget_usd, api_hard_stop_usd=self.api_hard_stop_usd,
                        usage_ledger=self.usage_ledger)


def get_production_settings(env=None) -> ProductionSettings:
    """Parse the production settings from the environment; the dataclass enforces the rules."""
    if env is None:
        _load_dotenv()
        env = os.environ
    environment = (env.get('JOBFIT_ENV') or 'dev').strip()
    if environment not in ('dev', 'prod'):
        raise ConfigurationError('JOBFIT_ENV must be dev or prod')
    prod = environment == 'prod'
    live = _flag(env, 'JOBFIT_LIVE_ENABLED')
    public = _flag(env, 'JOBFIT_PUBLIC_LIVE')

    values: dict = {'environment': environment, 'live_enabled': live, 'public_live': public}
    database_url = env.get('DATABASE_URL') or ''
    if database_url:
        values['database_url'] = database_url
    elif prod:
        raise ConfigurationError('DATABASE_URL must be set explicitly in prod')
    if prod:
        values['internal_token'] = env.get('JOBFIT_INTERNAL_TOKEN') or None
    if live:
        values['openrouter_api_key'] = env.get('OPENROUTER_API_KEY') or None
    if live and prod:
        values['owner_token'] = env.get('JOBFIT_OWNER_TOKEN') or None
        ledger = (env.get('JOBFIT_USAGE_LEDGER') or '').strip()
        if not ledger:
            raise ConfigurationError('JOBFIT_USAGE_LEDGER must be set when live analysis is enabled in prod')
        values['usage_ledger'] = Path(ledger).resolve()
        values.update(daily_budget_usd=_money(env, 'JOBFIT_DAILY_BUDGET_USD'),
                      api_budget_usd=_money(env, 'API_BUDGET_USD'),
                      api_hard_stop_usd=_money(env, 'API_HARD_STOP_USD'))
    if public:
        values['ip_hmac_key'] = env.get('JOBFIT_IP_HMAC_KEY') or None
    return ProductionSettings(**values)
