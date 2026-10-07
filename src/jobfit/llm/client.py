"""OpenRouter client for structured LLM calls and embeddings (DECISIONS D-030).

Every call: budget check first, then the request, then one ledger line.
Structured output uses response_format json_schema with strict: true, and provider routing
uses require_parameters: true and data_collection: "deny". Pydantic validation runs on the output.
"""
from __future__ import annotations

import json
import math
import time
from typing import Any, TypeVar

from pydantic import BaseModel

from jobfit.config import Settings
from jobfit.llm.budget import BudgetGuard
from jobfit.llm.ledger import UsageLedger, UsageRecord
from jobfit.llm.pricing import ModelPrice, estimate_cost, load_prices, rough_token_count

T = TypeVar("T", bound=BaseModel)

PROVIDER_PREFS = {"require_parameters": True, "data_collection": "deny"}


class IncompleteStructuredResponse(ValueError):
    """A provider response stopped before a complete structured result."""


class TruncatedStructuredResponse(IncompleteStructuredResponse):
    """The provider explicitly reported finish_reason=length."""


class UnexpectedResponseModel(ValueError):
    """The response model does not match the explicit registry allowlist."""


def strict_schema(schema: dict) -> dict:
    """Close objects and require declared properties for strict structured output."""
    schema = json.loads(json.dumps(schema))
    def walk(node):
        if isinstance(node, dict):
            node.pop('default', None)
            if node.get('type') == 'object':
                if isinstance(node.get('additionalProperties'), dict):
                    raise ValueError('Strict model output must use named fields, not arbitrary dictionaries')
                node['additionalProperties'] = False
                node['required'] = list(node.get('properties', {}))
            for value in node.values(): walk(value)
        elif isinstance(node, list):
            for value in node: walk(value)
    walk(schema)
    return schema


def _reported_cost(usage: Any) -> float | None:
    if usage is None:
        return None
    cost = getattr(usage, "cost", None)
    if cost is None:
        extra = getattr(usage, "model_extra", None) or {}
        cost = extra.get("cost")
    return float(cost) if cost is not None else None


class OpenRouterClient:
    def __init__(self, settings: Settings, sdk_client: Any | None = None, run_id: str = "adhoc",
                 chat_timeout_seconds: float = 90.0):
        if not math.isfinite(chat_timeout_seconds) or chat_timeout_seconds <= 0:
            raise ValueError('chat timeout must be positive and finite')
        self.settings = settings
        self.run_id = run_id
        self.chat_timeout_seconds = chat_timeout_seconds
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

    def verify_inference_key(self) -> dict[str, bool]:
        """Read-only key-type check. A successful /key GET alone is not enough.

        Management keys authenticate administrative calls but cannot run inference.
        Return only status booleans, never the key or the account response body.
        This check does not establish model availability or sufficient credits.
        """
        sdk = self.sdk.with_options(max_retries=0, timeout=20.0)
        response = sdk.get('/key', cast_to=dict)
        data = response.get('data', {})
        management = data.get('is_management_key')
        return {'authenticated': True, 'key_type_known': isinstance(management, bool),
                'is_management_key': management is True,
                'inference_key': management is False}

    def chat_structured(self, model: str, messages: list[dict], output_model: type[T], task: str,
                        max_tokens: int = 2000, temperature: float = 0.0) -> T:
        with self.ledger.exclusive():
            return self._chat_attempt(model, messages, output_model, task, max_tokens, temperature)

    def _chat_attempt(self, model, messages, output_model, task, max_tokens, temperature):
        price = self._price(model)
        schema = strict_schema(output_model.model_json_schema())
        if max_tokens < 1: raise ValueError('max_tokens must be positive')
        # Include schema and message framing in a conservative byte-token bound.
        est_in = len(json.dumps(messages, ensure_ascii=False).encode()) + len(json.dumps(schema).encode()) + 512
        upper_cost = estimate_cost(price, est_in, max_tokens)
        self.guard.check(upper_cost)
        sdk = self.sdk
        if hasattr(sdk, 'with_options'):
            sdk = sdk.with_options(max_retries=0, timeout=self.chat_timeout_seconds)
        start = time.perf_counter()
        record = UsageRecord(run_id=self.run_id, task=task, model=price.model_id,
                             cost_usd=upper_cost, cost_source='uncertain_upper_bound',
                             max_tokens=max_tokens)
        try:
            resp = sdk.chat.completions.create(
                model=price.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": output_model.__name__, "strict": True, "schema": schema},
                },
                extra_body={"provider": {**PROVIDER_PREFS, 'max_price': {
                    'prompt': price.input_per_m, 'completion': price.output_per_m, 'request': 0}}, "usage": {"include": True},
                    **({'reasoning':price.reasoning} if price.reasoning else {})},
            )
            usage = getattr(resp, "usage", None)
            record.input_tokens = getattr(usage, "prompt_tokens", 0) or 0
            record.output_tokens = getattr(usage, "completion_tokens", 0) or 0
            reported = _reported_cost(usage)
            if reported is not None:
                if not math.isfinite(reported) or reported < 0:
                    raise ValueError('invalid reported cost')
                record.cost_usd, record.cost_source = reported, "reported"
            elif record.input_tokens or record.output_tokens:
                record.cost_usd = estimate_cost(price, record.input_tokens, record.output_tokens)
                record.cost_source = 'estimated_from_reported_tokens'
            record.request_id = getattr(resp, 'id', None)
            record.finish_reason = getattr(resp.choices[0], 'finish_reason', 'stop')
            if getattr(resp, 'model', price.model_id) not in (price.model_id, *price.response_model_aliases):
                raise UnexpectedResponseModel('chat response model differs from requested model')
            if record.finish_reason == 'length':
                raise TruncatedStructuredResponse('structured response truncated')
            if record.finish_reason != 'stop':
                raise IncompleteStructuredResponse('incomplete or refused structured response')
            content = resp.choices[0].message.content
            return output_model.model_validate(json.loads(content))
        except BaseException as exc:
            record.ok = False
            record.error_type = type(exc).__name__
            if getattr(exc, 'status_code', None) in (400, 401, 402, 403, 404, 422, 429):
                record.cost_usd, record.cost_source = 0.0, 'rejected_request'
            raise
        finally:
            record.latency_ms = int((time.perf_counter() - start) * 1000)
            self.ledger.append(record)

    def embed(self, texts: list[str], model: str = "text-embedding-3-small", task: str = "embedding",
              *, dimensions: int) -> list[list[float]]:
        """Embedding interface: provider policy only, no chat response-format options.

        No invisible SDK retries. An uncertain failed request reserves an upper-bound
        cost in the ledger; reconcile it with provider billing before releasing it.
        """
        if not texts or any(not isinstance(t, str) or not t.strip() for t in texts):
            raise ValueError("embedding inputs must be non-empty strings")
        if dimensions < 1:
            raise ValueError("dimensions must be positive")
        with self.ledger.exclusive():
            return self._embed_attempt(texts, model, task, dimensions)

    def _embed_attempt(self, texts, model, task, dimensions):
        price = self._price(model)
        # UTF-8 bytes conservatively bound byte-BPE tokens; allowance for wrapping.
        upper_tokens = sum(len(t.encode("utf-8")) + 100 for t in texts)
        upper_cost = estimate_cost(price, upper_tokens)
        self.guard.check(upper_cost)
        sdk = self.sdk
        if hasattr(sdk, "with_options"):
            sdk = sdk.with_options(max_retries=0, timeout=60.0)
        start = time.perf_counter()
        record = UsageRecord(run_id=self.run_id, task=task, model=price.model_id,
                             dimensions=dimensions, batch_size=len(texts),
                             cost_usd=upper_cost, cost_source="uncertain_upper_bound")
        try:
            resp = sdk.embeddings.create(
                model=price.model_id, input=texts, encoding_format="float",
                extra_body={"provider": {**PROVIDER_PREFS,
                    "max_price": {"prompt": price.input_per_m, "request": 0}}},
            )
            # Native dimensions are deliberately used; validate rather than ask
            # the router to support an optional dimensions reduction parameter.
            record.request_id = getattr(resp, "id", None)
            usage = getattr(resp, "usage", None)
            record.input_tokens = getattr(usage, "prompt_tokens", 0) or 0
            reported = _reported_cost(usage)
            if reported is not None:
                if not math.isfinite(reported) or reported < 0:
                    raise ValueError("invalid reported cost")
                record.cost_usd, record.cost_source = reported, "reported"
            elif record.input_tokens:
                record.cost_usd = estimate_cost(price, record.input_tokens)
                record.cost_source = "estimated_from_reported_tokens"
            if getattr(resp, "model", price.model_id) not in (price.model_id, *price.response_model_aliases):
                raise ValueError("embedding response model differs from requested model")
            if sorted(d.index for d in resp.data) != list(range(len(texts))):
                raise ValueError("missing, duplicate, or invalid embedding indices")
            vectors = [d.embedding for d in sorted(resp.data, key=lambda d: d.index)]
            for vector in vectors:
                if len(vector) != dimensions or not all(math.isfinite(x) for x in vector):
                    raise ValueError("embedding dimension or finite-value check failed")
                if not any(vector):
                    raise ValueError("zero vector cannot support cosine search")
            return vectors
        except Exception as exc:
            record.ok = False
            record.error_type = type(exc).__name__
            # A rejected request has no generation; transport/5xx failures remain uncertain.
            if getattr(exc, "status_code", None) in (400, 401, 402, 403, 404, 422, 429):
                record.cost_usd, record.cost_source = 0.0, "rejected_request"
            raise
        finally:
            record.latency_ms = int((time.perf_counter() - start) * 1000)
            self.ledger.append(record)
