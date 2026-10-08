"""Crash and restart recovery of the persistent production ledger (CP3 Phase 2 P0; R1-R7).

Real PostgreSQL (opt-in like the migration tests: JOBFIT_MIGRATION_TESTS=1 and JOBFIT_MIGRATION_ADMIN_URL,
a disposable server; every test uses its own scratch database). No provider call: the API process is the
subprocess tests/live_restart_worker.py with a fake SDK. It is killed with SIGKILL at an exact, flushed
barrier; a FRESH LiveRuntime over the same storage root then recovers.

This proves application-level restart behaviour on one host filesystem. It does not prove Docker volume
persistence (the CI named-volume smoke) nor deployed-host persistence (Phase 8).
"""
import json
import os
import queue
import signal
import subprocess
import sys
import threading
import time
from datetime import timedelta
from decimal import Decimal

import psycopg
import pytest

import scripts.db_baseline as baseline
from jobfit.config import REPO_ROOT, REPO_USAGE_LEDGER, ConfigurationError, get_production_settings
from jobfit.live import budget_store as store
from jobfit.live.common import usd_up
from jobfit.live.evidence import BreachMarker, breach_path
from jobfit.live.operation import LiveRefused
from jobfit.live.storage import MARKER_NAME, LiveStorage
from jobfit.llm.phase_bounds import compute_phase_bounds
from tests.test_live_runtime_db import (ADMIN, CloseSpy, alembic_config, command, gate_free, intents_in, key,
                                        parse_work, provision, rows, runtime, swap_root)

pytestmark = pytest.mark.skipif(os.environ.get('JOBFIT_MIGRATION_TESTS') != '1' or not ADMIN,
                                reason='requires JOBFIT_MIGRATION_TESTS=1 and a disposable pgvector server')
WORKER = REPO_ROOT / 'tests' / 'live_restart_worker.py'
COST = Decimal('0.01')


@pytest.fixture
def db():
    with baseline.scratch_database(ADMIN) as url:
        command.upgrade(alembic_config(url), 'head')
        yield url


@pytest.fixture
def root(tmp_path):
    r = tmp_path / 'ledger_root'
    provision(r)
    return r


# --- the worker process ------------------------------------------------------------------------------------

class Worker:
    def __init__(self, db, root, op, scenario, cost=COST):
        env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(REPO_ROOT / 'src'), str(REPO_ROOT)]))
        self.proc = subprocess.Popen([sys.executable, '-u', str(WORKER), '--db', db, '--root', str(root),
                                      '--op', op, '--scenario', scenario, '--cost', str(cost)],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
                                     cwd=str(REPO_ROOT))
        self.lines = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            self.lines.put(line.rstrip('\n'))
        self.lines.put(None)

    def expect(self, prefix, timeout=60):
        """The exact next barrier line; any other line, EOF or a timeout fails the test."""
        try:
            line = self.lines.get(timeout=timeout)
        except queue.Empty:
            self.kill()
            pytest.fail(f'worker gave no {prefix!r} within {timeout}s')
        if line is None or not line.startswith(prefix + ' '):
            self.kill()
            pytest.fail(f'expected {prefix!r}, got {line!r}; stderr: {self.proc.stderr.read()[-2000:]}')
        return line.split(' ')[1:]

    def kill(self):
        if self.proc.poll() is None:
            self.proc.send_signal(signal.SIGKILL)
        return self.proc.wait(30)

    def wait(self):
        return self.proc.wait(60)


def wait_gate(db, timeout=30):
    deadline = time.monotonic() + timeout
    while not gate_free(db):
        assert time.monotonic() < deadline, 'the dead worker still holds the gate'
        time.sleep(0.1)


def completed(db, root, cost=COST):
    """R1 baseline: one operation completed by a worker process that then exited."""
    op = key()
    w = Worker(db, root, op, 'complete', cost)
    _, outcome, _ = w.expect('DONE')
    assert outcome == 'settled' and w.wait() == 0
    return op


def killed_in_call(db, root):
    """A worker killed while its provider call is in flight: the intent is durable, no ledger line."""
    op = key()
    w = Worker(db, root, op, 'stop_in_call')
    (attempt,) = w.expect('IN_CALL')
    before = intents_in(root, op)
    assert [i['attempt_id'] for i in before] == [attempt] and ledger_lines(root, op) == []
    assert w.kill() == -signal.SIGKILL
    assert intents_in(root, op) == before and ledger_lines(root, op) == []
    wait_gate(db)
    return op, before[0]


def ledger_lines(root, op=None):
    path = root / 'ledger.jsonl'
    if not path.exists():
        return []
    out = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return [r for r in out if op is None or r.get('operation_key') == op]


def active_until(db, op):
    with psycopg.connect(db) as conn:
        return conn.execute('SELECT active_until FROM budget_reservations WHERE operation_key = %s',
                            (op,)).fetchone()[0]


def after_expiry(db, op):
    return active_until(db, op) + timedelta(seconds=1)


def row(db, op):
    return [r for r in rows(db) if r[0] == op]


def drop_operation_evidence(root, op):
    """Remove one operation's intents ('done' hints included) and ledger lines; the marker stays."""
    for name in ('ledger.jsonl', 'ledger.jsonl.intents.jsonl'):
        path = root / name
        if path.exists():
            keep = [line for line in path.read_text().splitlines()
                    if line.strip() and json.loads(line).get('operation_key') != op]
            path.write_text(''.join(line + '\n' for line in keep))


# --- R1: the ledger survives, its spend counts, a restart never re-runs a call ------------------------------

def test_r1_completed_evidence_survives_and_drives_later_admission(db, root, tmp_path):
    marker = (root / MARKER_NAME).read_text()
    op = completed(db, root)
    assert (root / MARKER_NAME).read_text() == marker
    assert len(intents_in(root, op)) == 1 and len(ledger_lines(root, op)) == 1
    assert row(db, op) == [(op, 'parse', 'settled', COST)]
    fresh = runtime(db, root)                                     # a new process over the same storage
    assert fresh.recorded_spend() == COST
    with pytest.raises(LiveRefused, match='duplicate_operation'):  # same key after the restart
        fresh.run('parse', op, parse_work)
    assert fresh.sdk.calls == []
    parse_bound = compute_phase_bounds().parse_max
    hard_stop = float(COST + parse_bound - Decimal('1e-10'))
    tight = runtime(db, root, hard_stop=hard_stop)
    with pytest.raises(LiveRefused, match='lifetime'):              # the earlier spend is counted
        tight.run('parse', key(), parse_work)
    assert tight.sdk.calls == []
    with baseline.scratch_database(ADMIN) as other:               # control: no earlier evidence
        command.upgrade(alembic_config(other), 'head')
        control = runtime(other, tmp_path / 'control_root', hard_stop=hard_stop)
        result, _ = control.run('parse', key(), parse_work)
        assert result == 'ok' and len(control.sdk.calls) == 1


# --- R2: an intent without a ledger line survives and is charged at its upper bound -------------------------

def test_r2_a_call_killed_in_flight_is_settled_at_its_upper_bound_after_restart(db, root, monkeypatch):
    op, intent = killed_in_call(db, root)
    fresh = runtime(db, root)
    with pytest.raises(LiveRefused, match='busy'):                 # the open row blocks until reconciled
        fresh.run('parse', key(), parse_work)
    assert fresh.sdk.calls == []
    reports = fresh.reconcile(at=after_expiry(db, op))
    upper = usd_up(intent['upper_cost'])
    assert [(r.operation_key, r.outcome) for r in reports] == [(op, 'settled')]
    assert row(db, op) == [(op, 'parse', 'settled', upper)] and fresh.recorded_spend() == upper
    assert fresh.sdk.calls == []                                   # recovery made no provider call
    result, _ = fresh.run('parse', key(), parse_work)
    assert result == 'ok' and len(fresh.sdk.calls) == 1


# --- R2b: no evidence for an expired reservation: deferred, never released ---------------------------------

def test_r2b_killed_after_admission_before_any_intent_stays_reserved(db, root):
    op = key()
    w = Worker(db, root, op, 'stop_after_admit')
    assert w.expect('ADMITTED') == [op]
    assert intents_in(root, op) == []
    assert w.kill() == -signal.SIGKILL
    assert intents_in(root, op) == [] and row(db, op) == [(op, 'parse', 'reserved', None)]
    wait_gate(db)
    fresh = runtime(db, root)
    for _ in range(2):
        reports = fresh.reconcile(at=after_expiry(db, op))
        assert [(r.operation_key, r.outcome) for r in reports] == [(op, 'deferred')]
        assert row(db, op) == [(op, 'parse', 'reserved', None)]
    with pytest.raises(LiveRefused, match='busy'):
        fresh.run('parse', key(), parse_work)
    assert fresh.sdk.calls == []


def test_r2b_evidence_lost_while_the_marker_survives_stays_reserved(db, root):
    op, _ = killed_in_call(db, root)
    drop_operation_evidence(root, op)
    assert intents_in(root, op) == [] and (root / MARKER_NAME).exists()
    fresh = runtime(db, root)
    reports = fresh.reconcile(at=after_expiry(db, op))
    assert [(r.operation_key, r.outcome) for r in reports] == [(op, 'deferred')]
    assert row(db, op) == [(op, 'parse', 'reserved', None)]
    with pytest.raises(LiveRefused, match='busy'):
        fresh.run('parse', key(), parse_work)
    assert fresh.sdk.calls == []


# --- R3: a breach marker survives and blocks; reconciliation closes nothing ---------------------------------

def test_r3_a_breach_marker_blocks_admission_and_reconciliation_after_restart(db, root, monkeypatch):
    op, _ = killed_in_call(db, root)
    BreachMarker(breach_path(root / 'ledger.jsonl')).write('call_wall_exceeded', op, 'a1')
    fresh, spy = runtime(db, root), CloseSpy(monkeypatch)
    with pytest.raises(LiveRefused, match='evidence_fail_closed'):
        fresh.run('parse', key(), parse_work)
    assert fresh.reconcile(at=after_expiry(db, op)) == []
    assert spy.calls == [] and row(db, op) == [(op, 'parse', 'reserved', None)] and fresh.sdk.calls == []


# --- R4: torn, corrupt or unattributed evidence stays fail closed ------------------------------------------

@pytest.mark.parametrize('damage', ['torn_ledger_tail', 'corrupt_intent_line', 'unattributed_ledger_line'])
def test_r4_damaged_evidence_fails_closed_after_restart(db, root, monkeypatch, damage):
    completed(db, root)
    op, _ = killed_in_call(db, root)
    if damage == 'torn_ledger_tail':
        with (root / 'ledger.jsonl').open('a') as f:
            f.write('{"model": "x", "cost_usd": 0.')
    elif damage == 'corrupt_intent_line':
        with (root / 'ledger.jsonl.intents.jsonl').open('a') as f:
            f.write('not json\n')
    else:
        with (root / 'ledger.jsonl').open('a') as f:
            f.write(json.dumps({'model': 'x', 'task': 'cv_parsing', 'cost_usd': 0.001}) + '\n')
    fresh, spy = runtime(db, root), CloseSpy(monkeypatch)
    with pytest.raises(LiveRefused, match='evidence_fail_closed'):
        fresh.run('parse', key(), parse_work)
    assert fresh.reconcile(at=after_expiry(db, op)) == []
    assert spy.calls == [] and row(db, op) == [(op, 'parse', 'reserved', None)] and fresh.sdk.calls == []


# --- R5: storage reset ----------------------------------------------------------------------------------------

def test_r5a1_a_lost_ledger_line_is_charged_at_the_surviving_intents_upper_bound(db, root):
    op = completed(db, root)
    (intent,) = intents_in(root, op)
    upper = usd_up(intent['upper_cost'])
    assert upper > COST
    (root / 'ledger.jsonl').write_text('')                         # ledger-only loss; journal and marker kept
    fresh = runtime(db, root)
    assert fresh.recorded_spend() == upper >= row(db, op)[0][3]   # never a downward reset
    parse_bound = compute_phase_bounds().parse_max
    tight = runtime(db, root, hard_stop=float(COST + parse_bound))  # c + bound would just fit; U + bound not
    with pytest.raises(LiveRefused, match='lifetime'):
        tight.run('parse', key(), parse_work)
    result, _ = fresh.run('parse', key(), parse_work)             # C7(b) does not fire on U >= c
    assert result == 'ok' and len(fresh.sdk.calls) == 1


def test_r5a2_lost_settled_history_fails_closed_from_the_database_witness(db, root, monkeypatch):
    op = completed(db, root)
    drop_operation_evidence(root, op)                              # ledger line AND intent gone, marker kept
    assert intents_in(root, op) == [] and ledger_lines(root, op) == []
    fresh = runtime(db, root)
    assert fresh.recorded_spend() == 0 < row(db, op)[0][3]
    with pytest.raises(LiveRefused, match='evidence_fail_closed'):
        fresh.run('parse', key(), parse_work)
    assert fresh.sdk.calls == [] and len(rows(db)) == 1


def test_r5b_a_reinitialized_root_reports_storage_mismatch_before_busy(db, root, monkeypatch):
    op, _ = killed_in_call(db, root)
    swap_root(root)                                                # a new valid storage B
    fresh, spy = runtime(db, root), CloseSpy(monkeypatch)
    with pytest.raises(LiveRefused, match='ledger_storage_mismatch'):
        fresh.run('parse', key(), parse_work)
    reports = fresh.reconcile(at=after_expiry(db, op))
    assert [(r.operation_key, r.outcome) for r in reports] == [(op, 'deferred')]
    assert spy.calls == [] and row(db, op) == [(op, 'parse', 'reserved', None)] and fresh.sdk.calls == []


@pytest.mark.parametrize('process_id', ['1234', '0123456789abcdef0123456789abcdef:0', 'old'])
def test_r5b_a_bare_or_malformed_process_id_row_refuses(db, root, process_id):
    with psycopg.connect(db, autocommit=True) as conn:
        conn.execute("INSERT INTO budget_reservations (operation_key, phase, reserved_usd, process_id, active_until) "
                     "VALUES ('legacy', 'parse', 0.1, %s, clock_timestamp() + interval '1 hour')", (process_id,))
        store.close(conn, 'legacy', None)
    fresh = runtime(db, root)
    with pytest.raises(LiveRefused, match='ledger_storage_mismatch'):
        fresh.run('parse', key(), parse_work)
    assert fresh.sdk.calls == []


# --- R6: unprovisioned or unwritable root at restart ----------------------------------------------------------

@pytest.mark.parametrize('how', ['marker_deleted', 'root_removed', 'unwritable'])
def test_r6_an_unprovisioned_or_unwritable_root_refuses_and_reconciles_nothing(db, root, monkeypatch, how):
    import shutil
    op, _ = killed_in_call(db, root)
    fresh, spy = runtime(db, root), CloseSpy(monkeypatch)
    if how == 'marker_deleted':
        (root / MARKER_NAME).unlink()
    elif how == 'root_removed':
        shutil.rmtree(root)
    else:
        fresh.storage = LiveStorage(root / 'ledger.jsonl',
                                    probe=lambda r: (_ for _ in ()).throw(PermissionError('read-only volume')))
    with pytest.raises(LiveRefused, match='ledger_storage_unavailable'):
        fresh.run('parse', key(), parse_work)
    assert fresh.reconcile(at=after_expiry(db, op)) == [] and not fresh.storage_ready()
    assert spy.calls == [] and row(db, op) == [(op, 'parse', 'reserved', None)] and fresh.sdk.calls == []
    if how == 'root_removed':
        assert not root.exists()                                   # never recreated


# --- R7: a misconfigured production ledger path never gets a runtime -----------------------------------------

@pytest.mark.parametrize('ledger', [str(REPO_USAGE_LEDGER), 'usage_ledger.jsonl', '/tmp/usage_ledger.jsonl',
                                    str(REPO_ROOT / 'reports/usage/prod.jsonl')])
def test_r7_a_misconfigured_ledger_path_is_rejected_before_any_runtime_exists(ledger):
    env = {'JOBFIT_ENV': 'prod', 'DATABASE_URL': 'postgresql://u:p@db/prod', 'JOBFIT_INTERNAL_TOKEN': 'i' * 32,
           'JOBFIT_LIVE_ENABLED': '1', 'OPENROUTER_API_KEY': 'sk-test', 'JOBFIT_OWNER_TOKEN': 'o' * 32,
           'JOBFIT_USAGE_LEDGER': ledger, 'JOBFIT_DAILY_BUDGET_USD': '2', 'API_BUDGET_USD': '5',
           'API_HARD_STOP_USD': '4.5'}
    with pytest.raises(ConfigurationError, match='JOBFIT_USAGE_LEDGER'):
        get_production_settings(env)
