"""Phase 2B operation runner on real PostgreSQL with a fake SDK (D-096, D-101). Opt-in; no API calls.

Covers the phase-scoped gate, the persisted backstop after a lost coordinator, the watchdog, the
ticket at the first call, restart idempotency and ambiguous commits. Each test has its own scratch
database (upgraded to head) and its own temporary production ledger.
"""
import json
import os
import threading
import time
import uuid
from decimal import Decimal
from types import SimpleNamespace

import psycopg
import pytest
from alembic import command

import scripts.db_baseline as baseline
from jobfit.config import REPO_ROOT, Settings
from jobfit.db.migrate import alembic_config
from jobfit.live import budget_store as store
from jobfit.live.deadlines import PhaseWindow
from jobfit.live.evidence import BreachMarker
from jobfit.live.operation import LiveRefused, LiveRuntime
from jobfit.live.storage import MARKER_NAME, LiveStorage, init_storage
from jobfit.llm.phase_bounds import compute_phase_bounds
from jobfit.llm.runtime import build_runtime_client
from tests.test_live_unit import MSGS, Answer, FakeSDK, response

ADMIN = os.environ.get('JOBFIT_MIGRATION_ADMIN_URL')
pytestmark = pytest.mark.skipif(os.environ.get('JOBFIT_MIGRATION_TESTS') != '1' or not ADMIN,
                                reason='requires JOBFIT_MIGRATION_TESTS=1 and a disposable pgvector server')
CONFIG = REPO_ROOT / 'config/versions/pipeline_cp23_freeze_candidate_v4_20261006.yaml'
BOUNDS = None


def bounds():
    global BOUNDS
    if BOUNDS is None:
        BOUNDS = compute_phase_bounds()
    return BOUNDS


@pytest.fixture
def db():
    with baseline.scratch_database(ADMIN) as url:
        command.upgrade(alembic_config(url), 'head')
        yield url


def key():
    return 'idem:' + str(uuid.uuid4())


class Conn:
    """A real autocommit connection that can fail its COMMIT on demand (outcome unknown)."""

    def __init__(self, url, plan):
        self.conn, self.plan = psycopg.connect(url, autocommit=True), plan
        self.thread = threading.get_ident()       # S is used only by the thread that opened it
        self.pid = self.conn.info.backend_pid
        plan.setdefault('pids', []).append(self.pid)

    def execute(self, sql, *a, **kw):
        assert threading.get_ident() == self.thread, 'a worker thread touched a coordinator connection'
        if sql == 'COMMIT' and self.plan.get('fail_commits'):
            self.plan['fail_commits'] -= 1
            self.conn.execute(sql)
            raise psycopg.OperationalError('connection lost during COMMIT')
        return self.conn.execute(sql, *a, **kw)

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def provision(root):
    """A provisioned ledger storage root (the operator's init step); idempotent for one root."""
    root.mkdir(parents=True, exist_ok=True)            # the live evidence code never creates directories
    if not (root / MARKER_NAME).exists():
        init_storage(root / 'ledger.jsonl')
    return LiveStorage(root / 'ledger.jsonl').validate()


def runtime(db, tmp_path, sdk=None, cap=2.0, hard_stop=4.5, window=None, plan=None, **kw):
    provision(tmp_path)
    sdk = sdk if sdk is not None else FakeSDK()
    s = SimpleNamespace(usage_ledger=tmp_path / 'ledger.jsonl', database_url=db, daily_budget_usd=cap,
                        api_hard_stop_usd=hard_stop)
    client_settings = Settings(openrouter_api_key='k' * 40, usage_ledger=tmp_path / 'ledger.jsonl',
                               api_budget_usd=5.0, api_hard_stop_usd=hard_stop)
    plan = plan if plan is not None else {}
    rt = LiveRuntime(s, bounds(), pipeline_config=CONFIG, connect=lambda: Conn(db, plan),
                     client_factory=lambda op: build_runtime_client(client_settings, CONFIG, run_id=op, sdk_client=sdk),
                     watchdog_interval=0.05, drain_grace=1.0, **kw)
    if window is not None:
        rt.windows['parse'] = window
    rt.sdk, rt.plan = sdk, plan
    return rt


def parse_work(client):
    return client.chat_structured('deepseek-flash', MSGS, Answer, 'cv_parsing', max_tokens=16000).answer


def rows(db):
    with psycopg.connect(db) as conn:
        return conn.execute('SELECT operation_key, phase, status, settled_usd FROM budget_reservations '
                            'ORDER BY created_at').fetchall()


def gate_free(db):
    with psycopg.connect(db, autocommit=True) as conn:
        ok = store.try_gate(conn)
        if ok:
            store.release_gate(conn)
        return ok


# --- normal operations ------------------------------------------------------------------------------------

def test_parse_operation_consumes_the_ticket_at_the_first_call_and_settles_from_the_ledger(db, tmp_path):
    rt, op, ticket = runtime(db, tmp_path), key(), []
    result, report = rt.run('parse', op, parse_work, quota=lambda: ticket.append(1) or 'consumed')
    assert result == 'ok' and ticket == [1] and len(rt.sdk.calls) == 1
    assert report.outcome == 'settled' and report.spend == Decimal('0.001')
    assert rows(db) == [(op, 'parse', 'settled', Decimal('0.0010000000'))]
    assert gate_free(db)


def test_recommendation_is_refused_by_the_real_bound_at_the_us2_cap(db, tmp_path):
    rt = runtime(db, tmp_path)
    with pytest.raises(LiveRefused) as exc:
        rt.run('recommendation', key(), lambda client: pytest.fail('no pipeline may run'))
    assert exc.value.code == 'budget' and exc.value.status == 429
    assert rt.sdk.calls == [] and rows(db) == [] and gate_free(db)


def test_a_held_gate_refuses_busy_before_any_reservation_or_ticket(db, tmp_path):
    rt, ticket = runtime(db, tmp_path), []
    with psycopg.connect(db, autocommit=True) as other:
        assert store.try_gate(other)
        with pytest.raises(LiveRefused, match='busy'):
            rt.run('parse', key(), parse_work, quota=lambda: ticket.append(1) or 'consumed')
    assert ticket == [] and rows(db) == [] and rt.sdk.calls == []


def test_quota_refusal_releases_the_reservation_without_any_provider_call(db, tmp_path):
    rt, op = runtime(db, tmp_path), key()
    with pytest.raises(LiveRefused) as exc:
        rt.run('parse', op, parse_work, quota=lambda: 'refused')
    assert exc.value.code == 'quota_refused' and exc.value.status == 429
    assert rt.sdk.calls == [] and rows(db) == [(op, 'parse', 'released', Decimal('0E-10'))]


def test_the_gate_is_phase_scoped_and_never_held_between_operations(db, tmp_path):
    rt = runtime(db, tmp_path)
    rt.run('parse', key(), parse_work)
    assert gate_free(db)                         # think-time: nothing is held
    rt.run('parse', key(), parse_work)           # another session's operation is admitted
    assert [r[2] for r in rows(db)] == ['settled', 'settled']


def test_a_fatal_refusal_discards_the_result_and_settles_from_evidence(db, tmp_path, monkeypatch):
    from jobfit.live.evidence import IntentJournal
    rt, op = runtime(db, tmp_path), key()
    monkeypatch.setattr(IntentJournal, 'append_intent', lambda self, ctx: (_ for _ in ()).throw(OSError('fsync')))

    def work(client):
        try:
            parse_work(client)
        except Exception:
            pass
        return 'pipeline result that must be discarded'
    with pytest.raises(LiveRefused, match='intent_write_failed'):
        rt.run('parse', op, work)
    assert rt.sdk.calls == [] and rows(db) == [(op, 'parse', 'released', Decimal('0E-10'))]


# --- restart idempotency and ambiguous commits ------------------------------------------------------------------

def test_after_a_restart_the_same_key_never_runs_again_whatever_the_phase(db, tmp_path):
    op = key()
    runtime(db, tmp_path).run('parse', op, parse_work)
    fresh = runtime(db, tmp_path)                        # new process: no in-memory registry
    for phase in ('parse', 'recommendation'):
        with pytest.raises(LiveRefused, match='duplicate_operation'):
            fresh.run(phase, op, parse_work)
    assert fresh.sdk.calls == [] and len(rows(db)) == 1


def test_an_unknown_admission_commit_never_enters_the_pipeline(db, tmp_path):
    plan = {}
    rt, op = runtime(db, tmp_path, plan=plan), key()
    plan['fail_commits'] = 1
    with pytest.raises(LiveRefused, match='admission_outcome_unknown'):
        rt.run('parse', op, lambda client: pytest.fail('the pipeline must not run'))
    assert rt.sdk.calls == [] and rows(db) == [(op, 'parse', 'reserved', None)]
    with pytest.raises(LiveRefused, match='duplicate_operation'):        # a retry is resolved by the key
        rt.run('parse', op, parse_work)
    with pytest.raises(LiveRefused, match='busy'):                       # the orphan row blocks others
        rt.run('parse', key(), parse_work)


def test_an_unknown_settlement_commit_is_re_read_not_retried(db, tmp_path):
    plan = {}
    rt, op = runtime(db, tmp_path, plan=plan), key()

    def work(client):
        out = parse_work(client)
        plan['fail_commits'] = 1                     # the next COMMIT is the settlement's
        return out
    result, report = rt.run('parse', op, work)
    assert result == 'ok' and report.outcome == 'settled'
    assert rows(db) == [(op, 'parse', 'settled', Decimal('0.0010000000'))]


# --- lost coordinator: the persisted backstop -------------------------------------------------------------------

def test_a_lost_coordinator_never_lets_a_second_operation_overlap(db, tmp_path):
    release, in_call = threading.Event(), threading.Event()

    def blocking(kw):
        in_call.set()
        assert release.wait(30)
        return response(kw['model'])
    window = PhaseWindow('parse', chat_wall=6.0, embed_wall=6.0, calls_wall=6.0, horizon=8.0, window=9.0)
    rt_a = runtime(db, tmp_path, sdk=FakeSDK(blocking), window=window)
    op_a, outcome = key(), {}

    def run_a():
        try:
            outcome['a'] = rt_a.run('parse', op_a, parse_work)
        except LiveRefused as exc:
            outcome['a'] = exc.code
    a = threading.Thread(target=run_a)
    a.start()
    assert in_call.wait(30)
    with psycopg.connect(ADMIN, autocommit=True) as admin:          # drop A's coordinator connection S
        admin.execute('SELECT pg_terminate_backend(%s)', (rt_a.plan['pids'][0],))
    rt_b = runtime(db, tmp_path, window=window)                     # same storage root as A
    with pytest.raises(LiveRefused, match='busy'):                    # B gets the advisory gate, not admission
        rt_b.run('parse', key(), parse_work)
    release.set()
    a.join(30)
    assert outcome['a'] == 'coordinator_lost'                        # A's call returned; S could not settle
    assert [r[2] for r in rows(db)] == ['reserved']
    time.sleep(9.5)                                                  # past A's active_until
    journal = tmp_path / 'ledger.jsonl.intents.jsonl'
    good = journal.read_text()
    journal.write_text(good + '{"type": "intent"')                   # A's evidence made unreconcilable
    rt_b2 = runtime(db, tmp_path, window=window)
    with pytest.raises(LiveRefused, match='evidence_fail_closed'):
        rt_b2.run('parse', key(), parse_work)
    assert [r[2] for r in rows(db)] == ['reserved']
    journal.write_text(good)
    result, _ = rt_b2.run('parse', key(), parse_work)               # A reconciled first, then B admitted
    assert result == 'ok'
    assert [r[2] for r in rows(db)] == ['settled', 'settled']
    assert rt_b.sdk.calls == [] and len(rt_b2.sdk.calls) == 1


# --- watchdog -----------------------------------------------------------------------------------------------------

def test_the_watchdog_flags_a_call_past_its_wall_without_cancelling_it(db, tmp_path):
    window = PhaseWindow('parse', chat_wall=0.3, embed_wall=0.3, calls_wall=0.3, horizon=30.0, window=40.0)
    rt, op = runtime(db, tmp_path, sdk=FakeSDK(delay=1.0), window=window), key()
    with pytest.raises(LiveRefused, match='call_wall_exceeded'):
        rt.run('parse', op, parse_work)
    assert len(rt.sdk.calls) == 1 and len(rt.ledger.raw_lines()) == 1     # the call returned and was ledgered
    assert rows(db) == [(op, 'parse', 'settled', Decimal('0.0010000000'))]
    assert BreachMarker(tmp_path / 'ledger.jsonl.breach.jsonl').present()
    with pytest.raises(LiveRefused, match='evidence_fail_closed'):       # admission blocked until review
        rt.run('parse', key(), parse_work)


def test_an_unwritable_breach_marker_keeps_the_row_open_and_disables_admission(db, tmp_path, monkeypatch):
    window = PhaseWindow('parse', chat_wall=0.3, embed_wall=0.3, calls_wall=0.3, horizon=30.0, window=40.0)
    rt, op = runtime(db, tmp_path, sdk=FakeSDK(delay=1.0), window=window), key()
    monkeypatch.setattr(BreachMarker, 'write', lambda self, *a, **kw: (_ for _ in ()).throw(OSError('ro')))
    with pytest.raises(LiveRefused) as exc:
        rt.run('parse', op, parse_work)
    assert exc.value.code in ('call_wall_exceeded', 'breach_marker_write_failed')
    assert rt.admission_disabled == 'breach_marker_write_failed'
    assert rows(db) == [(op, 'parse', 'reserved', None)]
    with pytest.raises(LiveRefused, match='admission_disabled'):
        rt.run('parse', key(), parse_work)
    other = runtime(db, tmp_path)                            # another process: the open row blocks it
    with pytest.raises(LiveRefused, match='busy'):
        other.run('parse', key(), parse_work)
    foreign = runtime(db, tmp_path / 'o')                    # another storage root: refused before 'busy'
    with pytest.raises(LiveRefused, match='ledger_storage_mismatch'):
        foreign.run('parse', key(), parse_work)


def test_the_real_cap_refuses_a_recommendation_without_finalizing_the_allowance(db, tmp_path):
    from jobfit.live.quota import SessionAllowances
    allowances, op = SessionAllowances(), key()
    allowances.mark_ticket_held('s1')
    assert allowances.claim('s1', op)
    finalized = []
    rt = runtime(db, tmp_path)
    with pytest.raises(LiveRefused, match='budget'):
        rt.run('recommendation', op, lambda client: pytest.fail('no pipeline may run'),
               on_first_intent=lambda: finalized.append(1) or allowances.finalize('s1', op))
    assert finalized == [] and rt.sdk.calls == [] and rows(db) == []
    allowances.release_if_pending('s1', op)                  # what the API worker does afterwards
    assert allowances.state('s1') == (SessionAllowances.TICKET_HELD, None)


# --- persistent ledger storage: preflight, admission, continuity and settlement (C3, C6, C11) -----------------

def swap_root(root):
    """Replace the root's contents with a freshly provisioned storage B (a new storage_id)."""
    for p in root.iterdir():
        p.unlink()
    return init_storage(root / 'ledger.jsonl')


def snapshot(root):
    return {p.name: p.read_bytes() for p in root.iterdir()}


def restore(root, snap):
    for p in root.iterdir():
        p.unlink()
    for name, data in snap.items():
        (root / name).write_bytes(data)


def intents_in(root, op=None):
    path = root / 'ledger.jsonl.intents.jsonl'
    if not path.exists():
        return []
    rows_ = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return [r for r in rows_ if r.get('type') == 'intent' and (op is None or r['operation_key'] == op)]


class CloseSpy:
    def __init__(self, monkeypatch):
        self.calls, real = [], store.close

        def spy(conn, op, amount):
            self.calls.append(op)
            return real(conn, op, amount)
        monkeypatch.setattr(store, 'close', spy)


def counting_factory(rt):
    calls, real = [], rt.client_factory

    def factory(op):
        calls.append(op)
        return real(op)
    rt.client_factory = factory
    return calls


@pytest.mark.parametrize('how', ['marker_missing', 'root_missing', 'unwritable'])
def test_an_unprovisioned_or_unwritable_root_refuses_before_any_reservation(db, tmp_path, how):
    rt = runtime(db, tmp_path)
    if how == 'marker_missing':
        (tmp_path / MARKER_NAME).unlink()
    elif how == 'root_missing':
        rt.ledger_path = tmp_path / 'gone' / 'ledger.jsonl'
        rt.storage = LiveStorage(rt.ledger_path)
    else:
        rt.storage = LiveStorage(rt.ledger_path, probe=lambda root: (_ for _ in ()).throw(PermissionError('ro')))
    factory = counting_factory(rt)
    with pytest.raises(LiveRefused, match='ledger_storage_unavailable') as exc:
        rt.run('parse', key(), parse_work, quota=lambda: pytest.fail('ticket consumed'))
    assert exc.value.status == 503 and factory == [] and rt.sdk.calls == [] and rows(db) == []
    assert not (tmp_path / 'gone').exists()


@pytest.mark.parametrize('how', ['swap', 'marker_lost'])
def test_storage_replaced_between_preflight_and_admission_is_refused_before_inserting(db, tmp_path, monkeypatch, how):
    rt, op = runtime(db, tmp_path), key()
    real = store.take_owner

    def take_owner_then_swap(conn, operation_key):
        real(conn, operation_key)
        if how == 'swap':
            swap_root(tmp_path)
        else:
            (tmp_path / MARKER_NAME).unlink()
    monkeypatch.setattr(store, 'take_owner', take_owner_then_swap)
    code = 'ledger_storage_mismatch' if how == 'swap' else 'ledger_storage_unavailable'
    with pytest.raises(LiveRefused, match=code):
        rt.run('parse', op, parse_work, quota=lambda: pytest.fail('ticket consumed'))
    assert rows(db) == [] and rt.sdk.calls == [] and intents_in(tmp_path) == []


def test_storage_swapped_before_the_first_attempt_stops_it_after_the_durable_intent(db, tmp_path, monkeypatch):
    from tests.test_live_unit import Counting
    rt, op, spy = runtime(db, tmp_path), key(), CloseSpy(monkeypatch)
    hook = Counting(lambda: True)

    def work(client):
        swap_root(tmp_path)
        return parse_work(client)
    with pytest.raises(LiveRefused, match='ledger_storage_mismatch'):
        rt.run('parse', op, work, on_first_intent=hook)
    assert hook.count == 1                                       # the first durable intent finalized it
    assert len(intents_in(tmp_path, op)) == 1 and rt.sdk.calls == []
    assert rows(db) == [(op, 'parse', 'reserved', None)] and spy.calls == []
    assert op in rt.settlement_blocked


def test_storage_swapped_between_attempts_stops_every_later_attempt(db, tmp_path, monkeypatch):
    from jobfit.llm.structured import StageFailure, validated_call
    rt, op, spy = runtime(db, tmp_path), key(), CloseSpy(monkeypatch)
    seen = {}

    def work(client):
        assert parse_work(client) == 'ok'                        # first attempt on A
        seen['a'] = snapshot(tmp_path)
        swap_root(tmp_path)
        for _ in range(2):
            with pytest.raises(Exception):
                parse_work(client)
        with pytest.raises(StageFailure):                        # the frozen repair path is refused too
            validated_call(client, model='deepseek-flash', prompt='p', payload={}, output_model=Answer,
                           task='cv_parsing', validate=lambda o: None, max_tokens=16000)
        return 'done'
    with pytest.raises(LiveRefused, match='ledger_storage_mismatch'):
        rt.run('parse', op, work)
    assert len(rt.sdk.calls) == 1 and spy.calls == []
    assert rows(db) == [(op, 'parse', 'reserved', None)]
    assert len(intents_in(tmp_path, op)) == 1                    # the second attempt's intent, in B


# A lost root fails the frozen lifetime check's ledger read first (evidence_fail_closed), before any intent.
@pytest.mark.parametrize('how, code', [('marker', 'ledger_storage_unavailable'), ('root', 'evidence_fail_closed')])
def test_marker_lost_before_an_attempt_is_storage_unavailable_and_a_lost_root_fails_the_intent(db, tmp_path,
                                                                                            monkeypatch, how, code):
    import shutil
    rt, op, spy = runtime(db, tmp_path), key(), CloseSpy(monkeypatch)

    def work(client):
        if how == 'marker':
            (tmp_path / MARKER_NAME).unlink()
        else:
            shutil.rmtree(tmp_path)
        return parse_work(client)
    with pytest.raises(LiveRefused, match=code):
        rt.run('parse', op, work)
    assert rt.sdk.calls == [] and spy.calls == []
    assert rows(db) == [(op, 'parse', 'reserved', None)]
    if how == 'root':
        assert not tmp_path.exists()                             # never recreated, no intent anywhere
    else:
        assert len(intents_in(tmp_path, op)) == 1                # the intent was durable before the check


def test_a_stable_storage_is_checked_once_per_attempt_and_changes_nothing(db, tmp_path, monkeypatch):
    rt, op = runtime(db, tmp_path), key()
    real, checks = rt._continuity_check, []

    def counting(admitted):
        inner = real(admitted)

        def check():
            checks.append(1)
            return inner()
        return check
    monkeypatch.setattr(rt, '_continuity_check', counting)

    def work(client):
        return [parse_work(client) for _ in range(3)]
    result, report = rt.run('parse', op, work)
    assert result == ['ok'] * 3 and len(checks) == len(rt.sdk.calls) == 3
    assert report.outcome == 'settled' and rows(db)[0][2] == 'settled'
    assert not rt.settlement_blocked


# --- C11-D: a continuity failure blocks settlement for the rest of the process ------------------------------

def test_restored_storage_never_settles_an_operation_whose_first_attempt_hit_another_storage(db, tmp_path,
                                                                                            monkeypatch):
    rt, op, spy = runtime(db, tmp_path), key(), CloseSpy(monkeypatch)
    settles, owner_released_with = [], []
    real_settle, real_release = rt.settle, store.release_owner
    monkeypatch.setattr(rt, 'settle', lambda *a, **kw: settles.append(a) or real_settle(*a, **kw))

    def release(conn, operation_key):
        owner_released_with.append(operation_key in rt.settlement_blocked)
        return real_release(conn, operation_key)
    monkeypatch.setattr(store, 'release_owner', release)
    a = snapshot(tmp_path)

    def work(client):
        swap_root(tmp_path)
        with pytest.raises(Exception):
            parse_work(client)                                   # durable intent on B, mismatch, SDK 0
        restore(tmp_path, a)                                     # A is back before settlement
        return 'done'
    with pytest.raises(LiveRefused, match='ledger_storage_mismatch'):
        rt.run('parse', op, work)
    assert rt.storage.validate() == LiveStorage(tmp_path / 'ledger.jsonl').validate()     # A valid again
    assert settles == [] and spy.calls == [] and rt.sdk.calls == []
    assert rows(db) == [(op, 'parse', 'reserved', None)]
    assert op in rt.settlement_blocked and owner_released_with == [True]


def test_restored_storage_with_partial_evidence_never_closes_the_operation(db, tmp_path, monkeypatch):
    window = PhaseWindow('parse', chat_wall=6.0, embed_wall=6.0, calls_wall=6.0, horizon=8.0, window=9.0)
    rt, op, spy = runtime(db, tmp_path, window=window), key(), CloseSpy(monkeypatch)
    snap = {}

    def work(client):
        assert parse_work(client) == 'ok'                        # first call on A: one intent, one line
        snap['a'] = snapshot(tmp_path)
        swap_root(tmp_path)
        with pytest.raises(Exception):
            parse_work(client)                                   # second intent on B, SDK 0
        restore(tmp_path, snap['a'])
        return 'done'
    with pytest.raises(LiveRefused, match='ledger_storage_mismatch'):
        rt.run('parse', op, work)
    assert len(rt.sdk.calls) == 1 and spy.calls == []
    assert rows(db) == [(op, 'parse', 'reserved', None)]
    assert len(intents_in(tmp_path, op)) == 1                    # A's evidence alone would settle it
    from datetime import datetime, timedelta, timezone
    reports = rt.reconcile(at=datetime.now(timezone.utc) + timedelta(seconds=30))     # same process, expired
    assert [(r.operation_key, r.outcome) for r in reports] == [(op, 'deferred')]
    assert spy.calls == [] and rows(db) == [(op, 'parse', 'reserved', None)]


def test_a_continuity_failure_blocks_settlement_even_when_another_fatal_won_the_slot(db, tmp_path, monkeypatch):
    from tests.test_live_unit import Counting
    rt, op, spy = runtime(db, tmp_path), key(), CloseSpy(monkeypatch)
    hook = Counting(lambda: False)                               # allowance_finalize_failed wins the slot
    a = snapshot(tmp_path)

    def work(client):
        swap_root(tmp_path)
        with pytest.raises(Exception):
            parse_work(client)
        restore(tmp_path, a)
        return 'done'
    with pytest.raises(LiveRefused, match='allowance_finalize_failed'):
        rt.run('parse', op, work, on_first_intent=hook)
    assert hook.count == 1 and rt.sdk.calls == [] and spy.calls == []
    assert rows(db) == [(op, 'parse', 'reserved', None)] and op in rt.settlement_blocked


# --- C6: settlement revalidates the current storage (swap after preflight, no continuity failure) -----------

@pytest.mark.parametrize('variant', ['zero_attempts', 'one_call', 'marker_deleted', 'between_read_and_bracket'])
def test_settlement_after_a_storage_swap_is_deferred_never_released(db, tmp_path, monkeypatch, variant):
    import jobfit.live.operation as operation_module
    rt, op, spy = runtime(db, tmp_path), key(), CloseSpy(monkeypatch)
    if variant == 'between_read_and_bracket':
        real_ev = operation_module.operation_evidence

        def read_then_swap(*a, **kw):
            ev = real_ev(*a, **kw)
            swap_root(tmp_path)
            return ev
        monkeypatch.setattr(operation_module, 'operation_evidence', read_then_swap)

    def work(client):
        if variant in ('one_call', 'between_read_and_bracket'):
            assert parse_work(client) == 'ok'
        if variant in ('zero_attempts', 'one_call'):
            swap_root(tmp_path)
        if variant == 'marker_deleted':
            (tmp_path / MARKER_NAME).unlink()
        return 'done'
    result, report = rt.run('parse', op, work)
    assert result == 'done' and report.outcome == 'deferred' and spy.calls == []
    assert rows(db) == [(op, 'parse', 'reserved', None)] and not rt.settlement_blocked
    nxt = 'ledger_storage_unavailable' if variant == 'marker_deleted' else 'ledger_storage_mismatch'
    with pytest.raises(LiveRefused, match=nxt):
        rt.run('parse', key(), parse_work)
