"""Phase 2B offline tests: keys, deadlines, evidence and the reserved client (fake SDK; no network, no DB).

The frozen code paths are the real ones: OpenRouterClient._chat_attempt / _embed_attempt, the frozen
validated_call and the frozen analyze_job fallback. Only the SDK is fake.
"""
import inspect
import json
import threading
import time
import uuid
from decimal import Decimal
from functools import lru_cache
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from jobfit.config import REPO_ROOT, Settings
from jobfit.live import evidence as ev_mod
from jobfit.live.common import CURRENT_ATTEMPT, AttemptContext, EvidenceError, LiveSafetyRefusal
from jobfit.live.deadlines import EMBED_TIMEOUT_SECONDS, chat_timeout_seconds, max_attempts, phase_window
from jobfit.live.evidence import (BreachMarker, CorrelatedLedger, IntentJournal, breach_path, journal_path,
                                  operation_evidence, recorded_spend)
from jobfit.live.keys import BUDGET_KEY, FIXED_KEYS, GATE_KEY, operation_key, owner_key
from jobfit.live.reserved_client import CallModel, OperationState, bind_reserved_client
from jobfit.llm.budget import BudgetGuard
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.ledger import UsageRecord
from jobfit.llm.phase_bounds import compute_phase_bounds
from jobfit.llm.runtime import build_runtime_client
from jobfit.llm.structured import StageFailure, validated_call

CONFIG = REPO_ROOT / 'config/versions/pipeline_cp23_freeze_candidate_v4_20261006.yaml'
FLASH, SOL, LUNA = 'deepseek/deepseek-v4.1-flash', 'openai/gpt-6-sol', 'openai/gpt-6-luna'


class Answer(BaseModel):
    answer: str


@lru_cache(maxsize=1)
def bounds():
    return compute_phase_bounds()


@lru_cache(maxsize=1)
def call_model():
    return CallModel(bounds(), CONFIG)


def response(model, content='{"answer":"ok"}', cost=0.001, finish='stop'):
    return SimpleNamespace(id='req', model=model, usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5, cost=cost),
                           choices=[SimpleNamespace(finish_reason=finish, message=SimpleNamespace(content=content))])


class FakeSDK:
    def __init__(self, respond=None, delay=0.0):
        self.calls, self.lock = [], threading.Lock()
        self.respond = respond or (lambda kw: response(kw['model']))
        self.delay, self.active, self.max_active = delay, 0, 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.embeddings = SimpleNamespace(create=self.embed)

    def with_options(self, **kw):
        assert kw['max_retries'] == 0
        return self

    def create(self, **kw):
        with self.lock:
            self.calls.append(kw)
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            if callable(self.delay):
                time.sleep(self.delay(kw))
            elif self.delay:
                time.sleep(self.delay)
            return self.respond(kw)
        finally:
            with self.lock:
                self.active -= 1

    def embed(self, **kw):
        with self.lock:
            self.calls.append(kw)
        return SimpleNamespace(id='e', model=kw['model'], usage=SimpleNamespace(prompt_tokens=5, cost=0.00001),
                               data=[SimpleNamespace(index=i, embedding=[0.5] * 4) for i in range(len(kw['input']))])


def settings(tmp_path, **kw):
    values = dict(openrouter_api_key='k' * 40, usage_ledger=tmp_path / 'ledger.jsonl', api_budget_usd=5.0,
                  api_hard_stop_usd=4.5)
    values.update(kw)
    return Settings(**values)


class Live:
    """One admitted operation: the frozen runtime client rebound to a reservation (as the runner does)."""

    def __init__(self, tmp_path, phase='parse', sdk=None, reserved=None, quota=None, clock=None, plain=False,
                 op_key=None, on_first_intent=None, **settings_kw):
        tmp_path.mkdir(parents=True, exist_ok=True)       # the live evidence code never creates directories
        self.sdk = sdk if sdk is not None else FakeSDK()
        self.op_key = op_key or 'idem:' + str(uuid.uuid4())
        if plain:   # the frozen RuntimeClient adapter has no embeddings endpoint; embedding uses the base client
            self.inner = OpenRouterClient(settings(tmp_path, **settings_kw), sdk_client=self.sdk, run_id=self.op_key)
        else:
            self.inner = build_runtime_client(settings(tmp_path, **settings_kw), CONFIG, run_id=self.op_key,
                                              sdk_client=self.sdk)
        window = phase_window(phase, bounds(), 240.0)
        if reserved is None:
            reserved = bounds().parse_max if phase == 'parse' else bounds().recommendation_upper_bound
        clock = clock or time.monotonic
        self.op = OperationState(self.op_key, phase, Decimal(reserved), window, anchor_mono=clock(),
                                 quota=quota, on_first_intent=on_first_intent, clock=clock)
        self.ledger_path = tmp_path / 'ledger.jsonl'
        self.client = bind_reserved_client(self.inner, self.op, call_model(), self.ledger_path)
        self.journal = IntentJournal(journal_path(self.ledger_path))
        self.ledger = CorrelatedLedger(self.ledger_path, self.journal)

    def evidence(self):
        return operation_evidence(self.op_key, self.journal, self.ledger)

    def ledger_rows(self):
        return self.ledger.raw_lines()

    def intents(self):
        return [r for r in self.journal.read() if r['type'] == 'intent']


MSGS = [{'role': 'user', 'content': 'synthetic text'}]


def parse_call(live, **kw):
    return live.client.chat_structured('deepseek-flash', MSGS, Answer, 'cv_parsing', max_tokens=16000, **kw)


# --- keys and deadlines -----------------------------------------------------------------------------------

def test_lock_keys_are_distinct_64_bit_and_stable():
    assert len(FIXED_KEYS) == 3 and GATE_KEY != BUDGET_KEY
    assert all(-2 ** 63 <= k < 2 ** 63 for k in FIXED_KEYS)
    assert owner_key('idem:a') == owner_key('idem:a') != owner_key('idem:b')


def test_operation_key_needs_a_canonical_uuid4():
    key = str(uuid.uuid4())
    assert operation_key(key) == 'idem:' + key
    for bad in ('', 'x', str(uuid.uuid1()), key.upper(), '{' + key + '}', None):
        with pytest.raises(ValueError):
            operation_key(bad)


def test_windows_are_derived_from_the_reachable_call_model_and_frozen_timeouts():
    b = bounds()
    assert [max_attempts(b.chains[c]) for c in ('parse', 'extraction', 'matching', 'fallback')] == [2, 3, 3, 3]
    assert chat_timeout_seconds(CONFIG) == 240.0
    parse, rec = phase_window('parse', b, 240.0), phase_window('recommendation', b, 240.0)
    assert (parse.horizon, parse.window) == (660.0, 720.0)
    assert (rec.horizon, rec.window) == (24990.0, 25050.0)
    assert rec.window < 24 * 3600


def test_frozen_embed_timeout_literal_is_pinned():
    assert 'timeout=60.0' in inspect.getsource(OpenRouterClient._embed_attempt)
    assert EMBED_TIMEOUT_SECONDS == 60.0


# --- the happy path, correlation, settlement --------------------------------------------------------------

def test_a_reserved_call_is_journalled_ledgered_with_its_attempt_and_settled_at_the_reported_cost(tmp_path):
    live = Live(tmp_path)
    assert parse_call(live).answer == 'ok'
    (intent,), (line,) = live.intents(), live.ledger_rows()
    assert line['attempt_id'] == intent['attempt_id'] and line['operation_key'] == live.op_key
    assert line['run_id'] == live.op_key and line['cost_source'] == 'reported'
    assert {r['type'] for r in live.journal.read()} == {'intent', 'done'}
    ev = live.evidence()
    assert ev.spend == Decimal('0.001') and not ev.uncertain and ev.complete and ev.settlement() == Decimal('0.001')
    assert not live.op.inflight and live.op.fatal_refusal is None
    assert live.inner.guard.lifetime.ledger is live.inner.ledger


def test_other_frozen_client_instances_are_untouched(tmp_path):
    live = Live(tmp_path)
    other = OpenRouterClient(settings(tmp_path / 'o'))
    assert type(other.guard) is BudgetGuard and type(other.ledger).__name__ == 'UsageLedger'
    assert OpenRouterClient.chat_structured is not type(live.client).chat_structured


def test_request_kwargs_are_byte_identical_to_the_frozen_path(tmp_path):
    live = Live(tmp_path)
    parse_call(live)
    plain_sdk = FakeSDK()
    plain = build_runtime_client(settings(tmp_path / 'p'), CONFIG, sdk_client=plain_sdk)
    plain.chat_structured('deepseek-flash', MSGS, Answer, 'cv_parsing', max_tokens=16000)
    assert live.sdk.calls == plain_sdk.calls


def test_concurrent_calls_complete_out_of_order_and_each_intent_maps_to_its_own_line(tmp_path):
    seen = {}

    def respond(kw):
        i = json.loads(kw['messages'][0]['content'])['i']
        seen[CURRENT_ATTEMPT.get().attempt_id] = i
        return response(kw['model'], json.dumps({'answer': f'a{i}'}), cost=0.001 * (i + 1))
    sdk = FakeSDK(respond, delay=lambda kw: 0.05 * (8 - json.loads(kw['messages'][0]['content'])['i']))
    live = Live(tmp_path, phase='recommendation', sdk=sdk)
    out = [None] * 8

    def one(i):
        out[i] = live.client.chat_structured('gpt-6-sol', [{'role': 'user', 'content': json.dumps({'i': i})}],
                                             Answer, 'evidence_matching', max_tokens=1000).answer
    threads = [threading.Thread(target=one, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    assert out == [f'a{i}' for i in range(8)] and sdk.max_active > 1          # FAIL-36: real concurrency
    lines = {r['attempt_id']: r for r in live.ledger_rows()}
    assert len(lines) == 8 and len(live.intents()) == 8
    assert all(lines[a]['cost_usd'] == pytest.approx(0.001 * (i + 1)) for a, i in seen.items())
    assert live.evidence().spend == sum(Decimal(str(0.001 * (i + 1))) for i in range(8))


def test_serial_and_concurrent_outputs_are_identical(tmp_path):
    def respond(kw):
        i = json.loads(kw['messages'][0]['content'])['i']
        return response(kw['model'], json.dumps({'answer': f'r{i * i}'}))
    serial_client = build_runtime_client(settings(tmp_path / 's'), CONFIG, sdk_client=FakeSDK(respond))
    msgs = [[{'role': 'user', 'content': json.dumps({'i': i})}] for i in range(10)]
    serial = [serial_client.chat_structured('gpt-6-sol', m, Answer, 'evidence_matching', max_tokens=500).answer
              for m in msgs]
    live = Live(tmp_path, phase='recommendation', sdk=FakeSDK(respond, delay=0.02))
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(10) as pool:
        concurrent = list(pool.map(lambda m: live.client.chat_structured('gpt-6-sol', m, Answer, 'evidence_matching',
                                                                         max_tokens=500).answer, msgs))
    assert concurrent == serial and len(live.ledger_rows()) == 10


# --- fatal, sticky refusals ----------------------------------------------------------------------------------

def frozen_match(live, sdk_answers):
    """The frozen analyze_job (Sol, then Luna on failure) with a matcher built on the frozen validated_call."""
    from jobfit.recommend.service import RecommendConfig, analyze_job

    def matcher(cv, extraction, *, client, model, **kw):
        out, _ = validated_call(client, model=model, prompt='p', payload={'x': 1}, output_model=Answer,
                                task='evidence_matching', validate=lambda o: None, max_tokens=1000)
        return SimpleNamespace(status='failed', assessments=[], error_code='test_stop', out=out)
    config = RecommendConfig.from_yaml(CONFIG)
    return analyze_job(None, 'J1', 1, SimpleNamespace(), None, client=live.client, fallback_client=None,
                       config=config, matcher=matcher)


def test_sol_intent_failure_refuses_the_frozen_luna_fallback_with_zero_sdk_calls(tmp_path, monkeypatch):
    live = Live(tmp_path, phase='recommendation')
    monkeypatch.setattr(IntentJournal, 'append_intent', lambda self, ctx: (_ for _ in ()).throw(OSError('fsync')))
    result = frozen_match(live, None)
    assert result.used_fallback and result.hold_reason                 # the frozen code tried Luna
    assert [a['model'] for a in result.attempts] == ['gpt-6-sol', 'gpt-6-luna']
    assert live.sdk.calls == [] and live.op.fatal_refusal == 'intent_write_failed'
    assert live.ledger_rows() == [] and not live.op.inflight
    assert live.evidence().settlement() is None                         # nothing happened: release


def test_any_safety_refusal_is_sticky_for_every_later_call(tmp_path):
    live = Live(tmp_path)
    with pytest.raises(LiveSafetyRefusal, match='call_outside_model'):
        live.client.chat_structured('unknown-model', MSGS, Answer, 'cv_parsing', max_tokens=100)
    for call in (lambda: parse_call(live),
                 lambda: live.client.embed(['x'], model='qwen3-embedding-8b', dimensions=4)):
        with pytest.raises(LiveSafetyRefusal, match='call_outside_model'):
            call()
    assert live.sdk.calls == []


def test_genuine_provider_failures_keep_the_frozen_repair_and_fallback(tmp_path):
    def respond(kw):
        bad = kw['model'] == SOL
        return response(kw['model'], '{"answer": 1}' if bad else '{"answer":"luna"}')
    live = Live(tmp_path, phase='recommendation', sdk=FakeSDK(respond))
    result = frozen_match(live, None)
    assert [kw['model'] for kw in live.sdk.calls] == [SOL, SOL, LUNA]    # initial, frozen repair, fallback
    assert live.op.fatal_refusal is None and result.used_fallback
    assert [a['status'] for a in result.attempts] == ['error', 'failed']        # Sol StageFailure, Luna answered
    assert len(live.ledger_rows()) == 3 and live.evidence().spend == Decimal('0.003')


def test_corrupt_ledger_is_a_fatal_refusal_without_validation_repair(tmp_path):
    live = Live(tmp_path)
    live.ledger_path.write_text('{"broken": \n')
    with pytest.raises(StageFailure) as exc:
        validated_call(live.client, model='deepseek-flash', prompt='p', payload={}, output_model=Answer,
                       task='cv_parsing', validate=lambda o: None)
    assert exc.value.code == 'LiveSafetyRefusal' and exc.value.attempts == 1
    assert live.sdk.calls == [] and live.op.fatal_refusal == 'evidence_fail_closed'


def test_lifetime_hard_stop_is_a_fatal_refusal(tmp_path):
    live = Live(tmp_path, api_budget_usd=0.01, api_hard_stop_usd=0.0001)
    with pytest.raises(LiveSafetyRefusal, match='lifetime_refused'):
        parse_call(live)
    assert live.sdk.calls == []


@pytest.mark.parametrize('outcome,reason', [('refused', 'quota_refused'), ('unavailable', 'quota_unavailable'),
                                            ('unknown', 'quota_outcome_unknown')])
def test_quota_failure_at_the_first_call_refuses_without_any_provider_call(tmp_path, outcome, reason):
    calls = []
    live = Live(tmp_path, quota=lambda: calls.append(1) or outcome)
    for _ in range(2):
        with pytest.raises(LiveSafetyRefusal, match=reason):
            parse_call(live)
    assert calls == [1] and live.sdk.calls == [] and live.intents() == []     # never repeated
    assert live.evidence().settlement() is None


def test_proven_quota_commit_then_intent_failure_keeps_the_ticket_and_calls_nothing(tmp_path, monkeypatch):
    consumed = []
    live = Live(tmp_path, quota=lambda: consumed.append(1) or 'consumed')
    monkeypatch.setattr(IntentJournal, 'append_intent', lambda self, ctx: (_ for _ in ()).throw(OSError('fsync')))
    with pytest.raises(LiveSafetyRefusal, match='intent_write_failed'):
        parse_call(live)
    assert consumed == [1] and live.sdk.calls == [] and not live.op.inflight


def test_quota_consumed_once_for_the_whole_operation(tmp_path):
    calls = []
    live = Live(tmp_path, quota=lambda: calls.append(1) or 'consumed')
    parse_call(live)
    parse_call(live)
    assert calls == [1] and len(live.sdk.calls) == 2


def test_reservation_exhausted_refuses_before_the_sdk(tmp_path):
    live = Live(tmp_path, reserved='0.02')
    parse_call(live)                                             # ~0.0193 upper fits
    with pytest.raises(LiveSafetyRefusal, match='reservation_exhausted'):
        parse_call(live)
    assert len(live.sdk.calls) == 1


def test_a_call_that_would_cross_the_horizon_is_refused(tmp_path):
    now = [0.0]
    live = Live(tmp_path, clock=lambda: now[0])
    now[0] = 660.0 - 270.0 + 1                                   # elapsed + W(chat) > T_op
    with pytest.raises(LiveSafetyRefusal, match='deadline_exceeded'):
        parse_call(live)
    assert live.sdk.calls == []


def test_phase_mismatch_is_refused(tmp_path):
    live = Live(tmp_path)
    with pytest.raises(LiveSafetyRefusal, match='phase_mismatch'):
        live.client.chat_structured('gpt-6-sol', MSGS, Answer, 'evidence_matching', max_tokens=100)
    rec = Live(tmp_path / 'r', phase='recommendation')
    with pytest.raises(LiveSafetyRefusal, match='phase_mismatch'):
        rec.client.chat_structured('deepseek-flash', MSGS, Answer, 'cv_parsing', max_tokens=100)


def test_a_call_above_the_modelled_attempt_is_refused(tmp_path):
    live = Live(tmp_path)
    with pytest.raises(LiveSafetyRefusal, match='call_outside_model'):
        live.client.chat_structured('deepseek-flash', MSGS, Answer, 'cv_parsing', max_tokens=16001)
    huge = [{'role': 'user', 'content': '\x01' * 200_000}]
    live2 = Live(tmp_path / 'b')
    with pytest.raises(LiveSafetyRefusal, match='call_outside_model'):
        live2.client.chat_structured('deepseek-flash', huge, Answer, 'cv_parsing', max_tokens=100)
    assert live.sdk.calls == [] and live2.sdk.calls == []


def test_one_embedding_call_per_recommendation_and_never_under_parse(tmp_path):
    live = Live(tmp_path, phase='recommendation', plain=True)
    assert live.client.embed(['cv text'], model='qwen3-embedding-8b', dimensions=4)
    (line,) = live.ledger_rows()
    assert line['task'] == 'embedding' and line['attempt_id'] == live.intents()[0]['attempt_id']
    with pytest.raises(LiveSafetyRefusal, match='call_outside_model'):
        live.client.embed(['again'], model='qwen3-embedding-8b', dimensions=4)
    parse = Live(tmp_path / 'p', plain=True)
    with pytest.raises(LiveSafetyRefusal, match='phase_mismatch'):
        parse.client.embed(['cv text'], model='qwen3-embedding-8b', dimensions=4)


# --- in-flight accounting and ledger failures -------------------------------------------------------------

def test_ledger_write_failure_is_fatal_closes_the_attempt_and_settles_at_the_upper_bound(tmp_path, monkeypatch):
    live = Live(tmp_path)
    real = ev_mod.append_durable

    def fail_ledger(path, line):
        if path.name == 'ledger.jsonl':
            raise OSError('disk full')
        return real(path, line)
    monkeypatch.setattr(ev_mod, 'append_durable', fail_ledger)
    with pytest.raises(LiveSafetyRefusal, match='ledger_write_failed'):
        parse_call(live)
    assert len(live.sdk.calls) == 1 and live.op.fatal_refusal == 'ledger_write_failed'
    assert live.op.wait_drained(0.01)                                  # drain ends at once
    monkeypatch.setattr(ev_mod, 'append_durable', real)
    ev = live.evidence()
    assert ev.uncertain and not ev.complete and ev.settlement() == Decimal(live.intents()[0]['upper_cost'])


def test_done_failure_after_a_durable_line_charges_the_line_cost(tmp_path, monkeypatch):
    live = Live(tmp_path)
    monkeypatch.setattr(IntentJournal, 'append_done', lambda self, ctx: (_ for _ in ()).throw(OSError('x')))
    parse_call(live)
    assert not live.op.inflight and live.op.fatal_refusal is None
    assert live.evidence().settlement() == Decimal('0.001')


def test_a_frozen_raise_between_the_guard_and_its_try_closes_the_attempt_once(tmp_path):
    live = Live(tmp_path)
    live.inner._sdk = None
    live.inner.settings = settings(tmp_path, openrouter_api_key=None)   # the frozen sdk property now raises
    with pytest.raises(RuntimeError, match='OPENROUTER_API_KEY'):
        parse_call(live)
    assert not live.op.inflight and live.ledger_rows() == []
    ev = live.evidence()
    assert ev.uncertain and ev.settlement() == Decimal(live.intents()[0]['upper_cost'])


# --- evidence rules -------------------------------------------------------------------------------------------

def ctx(op='idem:o', attempt='a1', upper='0.5', owner=None):
    return AttemptContext(op, attempt, 'parse', 'cv_parsing', 'm', 'initial', 'parse', 270.0, owner=owner,
                          upper_cost=Decimal(upper))


class Owner:
    def __init__(self):
        self.closed, self.fatal = 0, None

    def set_fatal(self, reason):
        self.fatal = reason

    def close_attempt(self, c):
        if c.inflight_open:
            c.inflight_open = False
            self.closed += 1


def write_line(ledger, c, cost=0.1, source='reported'):
    token = CURRENT_ATTEMPT.set(c)
    try:
        ledger.append(UsageRecord(run_id=c.operation_key, task='cv_parsing', model='m', cost_usd=cost,
                                  cost_source=source))
    finally:
        CURRENT_ATTEMPT.reset(token)


def files(tmp_path):
    journal = IntentJournal(journal_path(tmp_path / 'l.jsonl'))
    return journal, CorrelatedLedger(tmp_path / 'l.jsonl', journal), BreachMarker(breach_path(tmp_path / 'l.jsonl'))


def test_a_ledger_line_overrides_its_intent_and_a_missing_line_counts_the_upper_bound(tmp_path):
    journal, ledger, breach = files(tmp_path)
    a, b = ctx(attempt='a', owner=Owner()), ctx(attempt='b', owner=Owner())
    journal.append_intent(a)
    journal.append_intent(b)
    write_line(ledger, a, cost=0.1)
    ev = operation_evidence('idem:o', journal, ledger)
    assert ev.spend == Decimal('0.6') and ev.uncertain and not ev.complete       # 0.1 + upper 0.5, no double count
    assert recorded_spend(journal, ledger, breach) == Decimal('0.6')


def test_rejected_only_operations_release(tmp_path):
    journal, ledger, _ = files(tmp_path)
    a = ctx(owner=Owner())
    journal.append_intent(a)
    write_line(ledger, a, cost=0.0, source='rejected_request')
    assert operation_evidence('idem:o', journal, ledger).settlement() is None


def test_uncertain_ledger_lines_settle_and_never_release(tmp_path):
    journal, ledger, _ = files(tmp_path)
    a = ctx(owner=Owner())
    journal.append_intent(a)
    write_line(ledger, a, cost=0.3, source='uncertain_upper_bound')
    ev = operation_evidence('idem:o', journal, ledger)
    assert ev.uncertain and ev.settlement() == Decimal('0.3')


@pytest.mark.parametrize('case', ['duplicate_line', 'orphan_line', 'unattributed_line', 'torn_line', 'duplicate_intent'])
def test_untrustworthy_evidence_fails_closed(tmp_path, case):
    journal, ledger, breach = files(tmp_path)
    a = ctx(owner=Owner())
    journal.append_intent(a)
    if case == 'duplicate_line':
        write_line(ledger, a)
        write_line(ledger, ctx(owner=Owner()))
    elif case == 'orphan_line':
        write_line(ledger, ctx(attempt='ghost', owner=Owner()))
    elif case == 'unattributed_line':
        ledger.path.write_text(json.dumps({'run_id': 'x', 'task': 't', 'model': 'm', 'cost_usd': 0.1}) + '\n')
    elif case == 'torn_line':
        ledger.path.write_text('{"run_id": "x"')
    else:
        journal.append_intent(a)
    with pytest.raises(EvidenceError):
        operation_evidence('idem:o', journal, ledger)
    with pytest.raises(EvidenceError):
        recorded_spend(journal, ledger, breach)


def test_a_reported_cost_above_the_upper_bound_is_kept_and_flagged(tmp_path):
    journal, ledger, breach = files(tmp_path)
    a = ctx(upper='0.01', owner=Owner())
    journal.append_intent(a)
    write_line(ledger, a, cost=0.05)
    ev = operation_evidence('idem:o', journal, ledger)
    assert ev.spend == Decimal('0.05') and ev.breaches == [('a1', Decimal('0.05'), Decimal('0.01'))]
    breach.write('reported_cost_above_upper_bound', 'idem:o', 'a1')
    with pytest.raises(EvidenceError, match='breach'):
        recorded_spend(journal, ledger, breach)


def test_concurrent_appends_and_lifetime_reads_never_see_a_partial_line(tmp_path):
    journal, ledger, _ = files(tmp_path)
    guard = BudgetGuard(ledger, 1e9, 1e9)
    stop, errors, snapshots = threading.Event(), [], []

    def reader():
        while not stop.is_set():
            try:
                snapshots.append(ledger.total_spent())
                guard.check(0.0)
            except Exception as exc:            # pragma: no cover - the assertion reports it
                errors.append(repr(exc))
    readers = [threading.Thread(target=reader) for _ in range(3)]
    for t in readers:
        t.start()
    for i in range(1500):
        c = ctx(attempt=f'a{i}', owner=Owner())
        journal.append_intent(c)
        write_line(ledger, c, cost=0.001)
    stop.set()
    for t in readers:
        t.join(30)
    assert errors == [] and snapshots == sorted(snapshots)
    assert len(ledger.raw_lines()) == 1500


def test_a_call_landing_during_an_evidence_read_never_looks_like_an_orphan_line(tmp_path, monkeypatch):
    journal, ledger, breach = files(tmp_path)
    real = CorrelatedLedger.raw_lines

    def read_then_a_call_lands(self):
        rows = real(self)
        c = ctx(attempt='late', owner=Owner())
        journal.append_intent(c)
        monkeypatch.setattr(CorrelatedLedger, 'raw_lines', real)
        write_line(self, c, cost=0.2)
        return rows
    monkeypatch.setattr(CorrelatedLedger, 'raw_lines', read_then_a_call_lands)
    assert recorded_spend(journal, ledger, breach) == Decimal('0.5')       # the late intent counts at its upper bound


# --- correction D: the recommendation allowance is finalized fail-closed at the first durable intent ---------

from jobfit.live.quota import LiveRequest, SessionAllowances  # noqa: E402

SOL_MSGS = [{'role': 'user', 'content': 'synthetic evidence request'}]


def sol_call(live, msgs=SOL_MSGS):
    return live.client.chat_structured('gpt-6-sol', msgs, Answer, 'evidence_matching', max_tokens=1000)


class Counting:
    def __init__(self, fn):
        self.fn, self.count, self.lock = fn, 0, threading.Lock()

    def __call__(self):
        with self.lock:
            self.count += 1
        return self.fn()


def allowance_live(tmp_path, claimed=True, finalize=None, sdk=None):
    allowances, op = SessionAllowances(), 'idem:' + str(uuid.uuid4())
    allowances.mark_ticket_held('s1')
    if claimed:
        assert allowances.claim('s1', op)
    hook = Counting(finalize or (lambda: allowances.finalize('s1', op)))
    live = Live(tmp_path, phase='recommendation', sdk=sdk, op_key=op, on_first_intent=hook)
    return live, allowances, hook


def test_finalize_success_lets_the_sdk_call_proceed_and_uses_the_allowance(tmp_path):
    live, allowances, hook = allowance_live(tmp_path)
    assert sol_call(live).answer == 'ok'
    sol_call(live)                                                   # later calls do not finalize again
    assert hook.count == 1 and len(live.sdk.calls) == 2
    assert allowances.state('s1') == (SessionAllowances.USED, live.op_key)


@pytest.mark.parametrize('failure', ['returns_false', 'raises'])
def test_a_failed_finalize_makes_no_sdk_call_and_is_sticky(tmp_path, failure):
    def raising():
        raise RuntimeError('allowance store unavailable')
    live, allowances, hook = allowance_live(tmp_path, finalize=(lambda: False) if failure == 'returns_false' else raising)
    with pytest.raises(LiveSafetyRefusal, match='allowance_finalize_failed'):
        sol_call(live)
    with pytest.raises(LiveSafetyRefusal, match='allowance_finalize_failed'):
        sol_call(live)                                               # sticky
    assert hook.count == 1 and live.sdk.calls == [] and not live.op.inflight
    (intent,) = live.intents()                                       # the intent is durable
    ev = live.evidence()
    assert ev.uncertain and ev.settlement() == Decimal(intent['upper_cost'])   # settled conservatively


def test_after_a_failed_finalize_the_frozen_fallback_and_repair_make_no_sdk_call(tmp_path):
    live, _, hook = allowance_live(tmp_path, finalize=lambda: False)
    result = frozen_match(live, None)
    assert [a['model'] for a in result.attempts] == ['gpt-6-sol', 'gpt-6-luna'] and result.hold_reason
    with pytest.raises(StageFailure):
        validated_call(live.client, model='gpt-6-sol', prompt='p', payload={}, output_model=Answer,
                       task='evidence_matching', validate=lambda o: None)
    assert hook.count == 1 and live.sdk.calls == [] and live.op.fatal_refusal == 'allowance_finalize_failed'


def test_a_session_dropped_before_the_first_intent_cannot_finalize(tmp_path):
    live, allowances, hook = allowance_live(tmp_path)
    allowances.drop('s1')                                            # deleted or expired after claim()
    with pytest.raises(LiveSafetyRefusal, match='allowance_finalize_failed'):
        sol_call(live)
    assert live.sdk.calls == [] and allowances.state('s1') == ('no_ticket', None)


def concurrent_first_calls(live, n=8):
    barrier, errors, done = threading.Barrier(n), [], []

    def one(i):
        barrier.wait()
        try:
            done.append(sol_call(live, [{'role': 'user', 'content': f'request {i}'}]).answer)
        except LiveSafetyRefusal as exc:
            errors.append(exc.reason)
    threads = [threading.Thread(target=one, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    return done, errors


def test_concurrent_first_intents_finalize_exactly_once(tmp_path):
    live, allowances, hook = allowance_live(tmp_path, sdk=FakeSDK(delay=0.02))
    done, errors = concurrent_first_calls(live)
    assert hook.count == 1 and errors == [] and len(done) == 8 and len(live.sdk.calls) == 8
    assert allowances.state('s1') == (SessionAllowances.USED, live.op_key)


@pytest.mark.parametrize('failure', ['returns_false', 'raises'])
def test_concurrent_first_intents_with_a_failed_finalize_make_no_sdk_call(tmp_path, failure):
    def raising():
        raise RuntimeError('boom')
    live, _, hook = allowance_live(tmp_path, finalize=(lambda: False) if failure == 'returns_false' else raising)
    done, errors = concurrent_first_calls(live)
    assert hook.count == 1 and done == [] and errors == ['allowance_finalize_failed'] * 8
    assert live.sdk.calls == [] and not live.op.inflight
    frozen_match(live, None)                                         # Luna and repair stay blocked
    assert live.sdk.calls == []


def test_finalize_is_never_attempted_without_a_durable_intent(tmp_path, monkeypatch):
    live, _, hook = allowance_live(tmp_path)
    with pytest.raises(LiveSafetyRefusal, match='call_outside_model'):           # refused before the guard
        live.client.chat_structured('unknown-model', SOL_MSGS, Answer, 'evidence_matching', max_tokens=10)
    assert hook.count == 0
    live2, _, hook2 = allowance_live(tmp_path / 'b')
    monkeypatch.setattr(IntentJournal, 'append_intent', lambda self, ctx: (_ for _ in ()).throw(OSError('fsync')))
    with pytest.raises(LiveSafetyRefusal, match='intent_write_failed'):
        sol_call(live2)
    assert hook2.count == 0 and live2.sdk.calls == []
    monkeypatch.undo()
    hook3 = Counting(lambda: True)
    live3 = Live(tmp_path / 'c', quota=lambda: 'refused', on_first_intent=hook3)
    with pytest.raises(LiveSafetyRefusal, match='quota_refused'):
        parse_call(live3)
    assert hook3.count == 0 and live3.sdk.calls == []


def test_allowance_state_machine_and_immutable_live_request():
    import dataclasses
    a = SessionAllowances()
    assert not a.claim('s', 'idem:1')                                # no ticket
    a.mark_ticket_held('s')
    assert a.claim('s', 'idem:1') and a.claim('s', 'idem:1')         # pending, idempotent
    assert not a.claim('s', 'idem:2') and not a.finalize('s', 'idem:2')
    a.release_if_pending('s', 'idem:1')
    assert a.state('s') == (SessionAllowances.TICKET_HELD, None) and not a.finalize('s', 'idem:1')
    assert a.claim('s', 'idem:3') and a.finalize('s', 'idem:3') and a.finalize('s', 'idem:3')
    a.release_if_pending('s', 'idem:3')                              # used never goes back
    assert a.state('s') == (SessionAllowances.USED, 'idem:3') and not a.claim('s', 'idem:4')
    req = LiveRequest('idem:3', False, None, 's', 'r', on_first_billable=lambda: True)
    with pytest.raises(dataclasses.FrozenInstanceError):
        req.on_first_billable = None
