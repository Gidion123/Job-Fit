from decimal import Decimal
from types import SimpleNamespace
import pytest
from jobfit.eval.stage2_route_repair import GPT_ID, RUN_ID, V5_ID, TemperatureAdapter, RouteSession
from jobfit.llm.ledger import UsageLedger, UsageRecord
from jobfit.llm.budget import BudgetExceeded


def test_gpt_omits_only_unsupported_temperature():
    calls = []
    sdk = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: calls.append(kw))))
    adapter = TemperatureAdapter(sdk)
    policy = {'require_parameters': True, 'data_collection': 'deny'}
    adapter.create(model=GPT_ID, temperature=0, max_tokens=6000, extra_body={'provider': policy})
    adapter.create(model='google/gemini-3.5-flash-lite', temperature=0, extra_body={'provider': policy})
    assert 'temperature' not in calls[0] and calls[0]['max_tokens'] == 6000
    assert calls[1]['temperature'] == 0
    assert all(call['extra_body']['provider'] == policy for call in calls)


def test_prior_spend_cannot_be_reset_by_successor_id(tmp_path):
    ledger = UsageLedger(tmp_path / 'ledger.jsonl')
    ledger.append(UsageRecord(run_id=V5_ID, task='jd_extraction', model=GPT_ID,
                              cost_usd=0.4, cost_source='reported'))
    session = RouteSession(tmp_path / 'state.json', run_id=RUN_ID, fingerprint='fixed',
                           jobs=['gpt/J'], ledger=ledger, ceiling='3.16')
    assert session.spent() == Decimal('0.4')
    with pytest.raises(BudgetExceeded, match='Aggregate'):
        session.check_budget(2.8)
    session.check_budget(2.7)
