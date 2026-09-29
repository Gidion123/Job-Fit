"""Append-only usage ledger: reports/usage/usage_ledger.jsonl (DECISIONS D-019).

One line per API call. Prompts, CV text, and keys are never stored here.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field


class UsageRecord(BaseModel):
    ts: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    run_id: str
    task: str  # extraction / evidence_matching / embedding / other
    gateway: str = "openrouter"
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    cost_source: str = "estimated"  # "reported" when the gateway returned the cost
    cached: bool = False
    latency_ms: int | None = None
    ok: bool = True
    error_type: str | None = None


class UsageLedger:
    def __init__(self, path: Path):
        self.path = Path(path)

    def append(self, record: UsageRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")

    def records(self) -> list[UsageRecord]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(UsageRecord.model_validate(json.loads(line)))
        return out

    def total_spent(self) -> float:
        return round(sum(r.cost_usd for r in self.records() if not r.cached), 6)
