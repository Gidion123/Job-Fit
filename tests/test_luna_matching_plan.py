from types import SimpleNamespace

import pytest

from scripts.run_cp23_luna_matching import CappedClient, RunCapReached, phases


def test_phase_plan_is_fixed_and_development_scoped():
    rankings = {'CV1': [f'A{i}' for i in range(30)], 'CV2': [f'B{i}' for i in range(30)]}
    p = phases(rankings)
    assert [x['name'] for x in p] == ['P0_luna_canary', 'A_luna_cv1_top20', 'C_luna_remaining39']
    assert [x['workers'] for x in p] == [1, 20, 8]
    assert all(x['model'] == 'gpt-6-luna' for x in p)
    assert p[1]['pairs'] == [['CV1', f'A{i}'] for i in range(20)]
    luna = [tuple(x) for phase in p for x in phase['pairs']]
    assert len(luna) == 60 and len(set(luna)) == 60


def test_v2_uses_the_approved_luna_route_adaptation():
    from jobfit.eval.stage2_route_repair import RouteClient, TemperatureAdapter
    from scripts.run_cp23_luna_matching import CLIENT_CLASS, STOP_ERRORS
    assert CLIENT_CLASS is RouteClient and 'NotFoundError' in STOP_ERRORS
    sent = {}

    class Fake:
        chat = type('C', (), {'completions': type('D', (), {'create': staticmethod(lambda **kw: sent.update(kw))})})()

    TemperatureAdapter(Fake()).create(model='openai/gpt-6-luna', temperature=0.0, messages=[])
    assert 'temperature' not in sent


class FakeLedger:
    def __init__(self):
        self.spent = 0.0

    def total_spent(self):
        return self.spent


class FakeBase:
    def __init__(self):
        self.ledger = FakeLedger()
        self.guard = SimpleNamespace(check=lambda amount: None)
        self.calls = 0

    def _price(self, model):
        from jobfit.llm.pricing import ModelPrice
        return ModelPrice('fake', 'fake', 1_000_000.0, 1_000_000.0)

    def _chat_attempt(self, *args):
        self.calls += 1
        return {'ok': True}


def test_cap_blocks_dispatch_before_any_paid_call():
    from pydantic import BaseModel

    class Out(BaseModel):
        ok: bool

    base = FakeBase()
    client = CappedClient(base, starting_total=0.0, cap=0.01)
    with pytest.raises(RunCapReached):
        client.chat_structured('m', [{'role': 'user', 'content': 'x'}], Out, 'evidence_matching', max_tokens=10_000)
    assert base.calls == 0 and client.inflight == 0
