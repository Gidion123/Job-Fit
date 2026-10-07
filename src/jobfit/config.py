"""Settings from environment variables and the git-ignored .env file (DECISIONS D-028).

Keys are never printed, logged, or written anywhere else. repr() hides them.
"""
from __future__ import annotations

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
