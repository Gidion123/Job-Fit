"""Price lookup for the budget guard estimate (config/models_v1.yaml)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ModelPrice:
    key: str
    model_id: str
    input_per_m: float
    output_per_m: float = 0.0


def load_prices(path: Path) -> dict[str, ModelPrice]:
    """Returns prices keyed by both the short key and the OpenRouter id."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    prices: dict[str, ModelPrice] = {}
    for section in ("models", "embeddings"):
        for key, m in (data.get(section) or {}).items():
            p = ModelPrice(key, m["id"], float(m["input_per_m"]), float(m.get("output_per_m", 0.0)))
            prices[key] = p
            prices[m["id"]] = p
    return prices


def estimate_cost(price: ModelPrice, input_tokens: int, output_tokens: int = 0) -> float:
    return (input_tokens * price.input_per_m + output_tokens * price.output_per_m) / 1_000_000


def rough_token_count(text: str) -> int:
    """About 4 characters per token. Only for the pre-call estimate, never for reporting."""
    return max(1, len(text) // 4)
