"""OpenRouter client for structured LLM calls and embeddings (DECISIONS D-030).

Every call: budget check first, then the request, then one ledger line.
Structured output uses response_format json_schema with strict: true, and provider routing
uses require_parameters: true and data_collection: "deny". Pydantic validation runs on the output.
"""
from __future__ import annotations

import json
import time
from typing import Any, TypeVar

from pydantic import BaseModel

from jobfit.config import Settings
from jobfit.llm.budget import BudgetGuard
from jobfit.llm.ledger import UsageLedger, UsageRecord
from jobfit.llm.pricing import ModelPrice, estimate_cost, load_prices, rough_token_count

T = TypeVar("T", bound=BaseModel)

PROVIDER_PREFS = {"require_parameters": True, "data_collection": "deny"}


def _reported_cost(usage: Any) -> float | None:
    if usage is None:
        return None
    cost = getattr(usage, "cost", None)
    if cost is None:
        extra = getattr(usage, "model_extra", None) or {}
        cost = extra.get("cost")
    return float(cost) if cost is not None else None


class OpenRouterClient:
    def __init__(self, settings: Settings, sdk_client: Any | None = None, run_id: str = "adhoc"):
        self.settings = settings
        self.run_id = run_id
        self.prices = load_prices(settings.models_file)
        self.ledger = UsageLedger(settings.usage_ledger)
        self.guard = BudgetGuard(self.ledger, settings.api_budget_usd, settings.api_hard_stop_usd)
        self._sdk = sdk_client

    @property
    def sdk(self) -> Any:
        if self._sdk is None:
            if not self.settings.has_openrouter_key:
                raise RuntimeError("OPENROUTER_API_KEY is not set. Fill it in .env (never in chat or code).")
            from openai import OpenAI

            self._sdk = OpenAI(base_url=self.settings.openrouter_base_url, api_key=self.settings.openrouter_api_key)
        return self._sdk

    def _price(self, model: str) -> ModelPrice:
        if model not in self.prices:
            raise KeyError(f"{model} is not in {self.settings.models_file.name}; add it there and in docs/experiments.md first")
        return self.prices[model]

    def chat_structured(self, model: str, messages: list[dict], output_model: type[T], task: str,
                        max_tokens: int = 2000, temperature: float = 0.0) -> T:
        price = self._price(model)
        est_in = sum(rough_token_count(m.get("content", "")) for m in messages)
        self.guard.check(estimate_cost(price, est_in, max_tokens))

        schema = output_model.model_json_schema()
        start = time.perf_counter()
        record = UsageRecord(run_id=self.run_id, task=task, model=price.model_id)
        try:
            resp = self.sdk.chat.completions.create(
                model=price.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": output_model.__name__, "strict": True, "schema": schema},
                },
                extra_body={"provider": PROVIDER_PREFS, "usage": {"include": True}},
            )
            usage = getattr(resp, "usage", None)
            record.input_tokens = getattr(usage, "prompt_tokens", 0) or 0
            record.output_tokens = getattr(usage, "completion_tokens", 0) or 0
            reported = _reported_cost(usage)
            if reported is not None:
                record.cost_usd, record.cost_source = reported, "reported"
            else:
                record.cost_usd = estimate_cost(price, record.input_tokens, record.output_tokens)
            content = resp.choices[0].message.content
            return output_model.model_validate(json.loads(content))
        except Exception as exc:
            record.ok = False
            record.error_type = type(exc).__name__
            raise
        finally:
            record.latency_ms = int((time.perf_counter() - start) * 1000)
            self.ledger.append(record)

    def embed(self, texts: list[str], model: str = "text-embedding-3-small", task: str = "embedding") -> list[list[float]]:
        price = self._price(model)
        est_in = sum(rough_token_count(t) for t in texts)
        self.guard.check(estimate_cost(price, est_in))
        start = time.perf_counter()
        record = UsageRecord(run_id=self.run_id, task=task, model=price.model_id)
        try:
            resp = self.sdk.embeddings.create(model=price.model_id, input=texts)
            usage = getattr(resp, "usage", None)
            record.input_tokens = getattr(usage, "prompt_tokens", 0) or 0
            reported = _reported_cost(usage)
            if reported is not None:
                record.cost_usd, record.cost_source = reported, "reported"
            else:
                record.cost_usd = estimate_cost(price, record.input_tokens)
            return [d.embedding for d in resp.data]
        except Exception as exc:
            record.ok = False
            record.error_type = type(exc).__name__
            raise
        finally:
            record.latency_ms = int((time.perf_counter() - start) * 1000)
            self.ledger.append(record)
