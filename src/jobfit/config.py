"""Settings from environment variables and the git-ignored .env file (DECISIONS D-028).

Keys are never printed, logged, or written anywhere else. repr() hides them.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Versions written into every stored output, so results can be traced (System Design v1.3 section 12).
SNAPSHOT_ID = "CP1_20260926"
SCHEMA_VERSION = "v1"
SCORE_VERSION = "v0"  # PARTIAL weight 0.5
GUIDELINE_VERSION = "v0.1"
PROMPT_VERSION = "v1"


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:  # python-dotenv is in requirements.txt; tests do not need it
        return
    load_dotenv(REPO_ROOT / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str | None = field(default=None, repr=False)
    database_url: str = "postgresql://jobfit:jobfit@localhost:5432/jobfit"
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
