from dataclasses import replace
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from jobfit.config import Settings
from jobfit.llm.budget import BudgetExceeded, BudgetGuard
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.ledger import UsageLedger, UsageRecord
from jobfit.llm.pricing import estimate_cost, load_prices


def test_guard_blocks_past_hard_stop(tmp_path):
    ledger = UsageLedger(tmp_path / "ledger.jsonl")
    ledger.append(UsageRecord(run_id="r", task="extraction", model="m", cost_usd=13.95))
    guard = BudgetGuard(ledger, cap_usd=15, hard_stop_usd=14)
    guard.check(0.04)  # 13.99, allowed
    with pytest.raises(BudgetExceeded):
        guard.check(0.10)
    assert guard.should_warn()


def test_cached_calls_do_not_count(tmp_path):
    ledger = UsageLedger(tmp_path / "ledger.jsonl")
    ledger.append(UsageRecord(run_id="r", task="t", model="m", cost_usd=1.0))
    ledger.append(UsageRecord(run_id="r", task="t", model="m", cost_usd=1.0, cached=True))
    assert ledger.total_spent() == 1.0


def test_prices_file_has_shortlist(tmp_path):
    prices = load_prices(Settings().models_file)
    for key in ("deepseek-flash", "gpt-6-luna", "gemini-3.5-flash-lite", "claude-haiku-4.5", "text-embedding-3-small"):
        assert key in prices
    luna = prices["gpt-6-luna"]
    assert estimate_cost(luna, 1_000_000, 1_000_000) == pytest.approx(0.60)


class Out(BaseModel):
    answer: str


class FakeSDK:
    def __init__(self, cost=0.0012):
        self.calls = 0
        usage = SimpleNamespace(prompt_tokens=100, completion_tokens=20, cost=cost)
        msg = SimpleNamespace(content='{"answer": "ok"}')
        resp = SimpleNamespace(usage=usage, choices=[SimpleNamespace(message=msg)])

        def create(**kwargs):
            self.calls += 1
            self.last_kwargs = kwargs
            return resp

        self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))


def make_settings(tmp_path, hard_stop=None):
    s = replace(Settings(), usage_ledger=tmp_path / "ledger.jsonl")
    return s if hard_stop is None else replace(s, api_hard_stop_usd=hard_stop)


def test_default_budget_matches_env_example():
    s = Settings()
    assert (s.api_budget_usd, s.api_hard_stop_usd) == (5.0, 4.5)


def test_client_logs_reported_cost_without_prompt(tmp_path):
    sdk = FakeSDK()
    client = OpenRouterClient(make_settings(tmp_path), sdk_client=sdk, run_id="test")
    out = client.chat_structured("gpt-6-luna", [{"role": "user", "content": "SECRET CV TEXT"}], Out, task="extraction")
    assert out.answer == "ok"
    kw = sdk.last_kwargs
    assert kw["response_format"]["json_schema"]["strict"] is True
    assert kw["extra_body"]["provider"]["require_parameters"] is True
    line = (tmp_path / "ledger.jsonl").read_text()
    assert "SECRET CV TEXT" not in line
    rec = client.ledger.records()[0]
    assert rec.cost_source == "reported" and rec.cost_usd == pytest.approx(0.0012)


def test_client_refuses_before_calling_when_over_budget(tmp_path):
    sdk = FakeSDK()
    client = OpenRouterClient(make_settings(tmp_path, hard_stop=0.0), sdk_client=sdk)
    with pytest.raises(BudgetExceeded):
        client.chat_structured("claude-haiku-4.5", [{"role": "user", "content": "x"}], Out, task="extraction")
    assert sdk.calls == 0


def test_unknown_model_must_be_registered_first(tmp_path):
    client = OpenRouterClient(make_settings(tmp_path), sdk_client=FakeSDK())
    with pytest.raises(KeyError):
        client.chat_structured("some/new-model", [{"role": "user", "content": "x"}], Out, task="extraction")


def test_settings_repr_hides_keys():
    s = Settings(openrouter_api_key="sk-or-fake-for-test")
    assert "sk-or-fake-for-test" not in repr(s)
