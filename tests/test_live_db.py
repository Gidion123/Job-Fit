"""Phase 2B budget store on real PostgreSQL (D-096, D-101). Opt-in like the migration tests; no API calls.

Needs JOBFIT_MIGRATION_TESTS=1 and JOBFIT_MIGRATION_ADMIN_URL (a disposable pgvector server). Every
test uses its own scratch database upgraded to head, dropped afterwards.
"""
import os
import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import psycopg
import pytest
from alembic import command

import scripts.db_baseline as baseline
from jobfit.db.migrate import alembic_config
from jobfit.live import budget_store as store
from jobfit.live import quota
from jobfit.live.keys import GATE_KEY
from jobfit.llm.phase_bounds import compute_phase_bounds

ADMIN = os.environ.get('JOBFIT_MIGRATION_ADMIN_URL')
pytestmark = pytest.mark.skipif(os.environ.get('JOBFIT_MIGRATION_TESTS') != '1' or not ADMIN,
                                reason='requires JOBFIT_MIGRATION_TESTS=1 and a disposable pgvector server')
CAP, HARD_STOP = Decimal('2'), Decimal('4.5')
UTC = timezone.utc


@pytest.fixture
def db():
    with baseline.scratch_database(ADMIN) as url:
        command.upgrade(alembic_config(url), 'head')
        yield url


def conn_for(url):
    return psycopg.connect(url, autocommit=True)


def admit(url, op, phase='parse', bound='0.4716399', spend='0', at=None, cap=CAP, hard_stop=HARD_STOP,
          window=720.0):
    with conn_for(url) as conn:
        return store.admit(conn, operation_key=op, phase=phase, bound=Decimal(bound), daily_cap=cap,
                           hard_stop=hard_stop, window_seconds=window, process_id='test',
                           recorded_spend=lambda: Decimal(spend), at=at)


def refused(url, *args, **kw):
    with pytest.raises(store.AdmissionRefused) as exc:
        admit(url, *args, **kw)
    return exc.value.code


def close(url, op, amount):
    with conn_for(url) as conn:
        return store.close(conn, op, None if amount is None else Decimal(amount))


def insert_row(url, op, created, active_until, status='reserved', reserved='0.5', settled=None, phase='parse'):
    """A historical row with explicit times (production_day must be the Jakarta date of created_at)."""
    with conn_for(url) as conn:
        conn.execute('INSERT INTO budget_reservations (operation_key, phase, reserved_usd, process_id, created_at, '
                     "production_day, active_until) VALUES (%s, %s, %s, 'old', %s, "
                     "(%s::timestamptz AT TIME ZONE 'Asia/Jakarta')::date, %s)",
                     (op, phase, Decimal(reserved), created, created, active_until))
        if status != 'reserved':
            conn.execute("UPDATE budget_reservations SET status = %s, settled_usd = %s, closed_at = %s "
                         'WHERE operation_key = %s', (status, Decimal(settled or '0'), active_until, op))


def rows(url):
    with conn_for(url) as conn:
        return conn.execute('SELECT operation_key, phase, status, reserved_usd, settled_usd, production_day, '
                            'active_until - created_at FROM budget_reservations ORDER BY created_at').fetchall()


# --- admission under the real configuration ----------------------------------------------------------

def test_real_bounds_admit_parse_and_refuse_recommendation_at_the_us2_cap(db):
    bounds = compute_phase_bounds()
    assert bounds.recommendation_upper_bound > CAP > bounds.parse_max
    assert refused(db, 'idem:rec', phase='recommendation', bound=str(bounds.recommendation_upper_bound)) == 'budget'
    a = admit(db, 'idem:parse', bound=str(bounds.parse_max))
    assert a.reserved_usd == bounds.parse_max and a.phase == 'parse'
    (op, phase, status, reserved, settled, day, window), = rows(db)
    assert (op, phase, status, reserved, settled) == ('idem:parse', 'parse', 'reserved', bounds.parse_max, None)
    assert window == timedelta(seconds=720)


def test_cap_boundary_is_inclusive(db):
    insert_row(db, 'old', datetime.now(UTC) - timedelta(minutes=5), datetime.now(UTC) - timedelta(minutes=1),
               status='settled', settled='1.5')
    assert refused(db, 'idem:over', bound='0.5000000001') == 'budget'
    admit(db, 'idem:equal', bound='0.5')


# --- the persisted backstop, duplicates and idempotency ------------------------------------------------

def test_any_open_reservation_refuses_admission_even_after_active_until(db):
    now = datetime.now(UTC)
    insert_row(db, 'stale', now - timedelta(hours=3), now - timedelta(hours=2))     # expired but unresolved
    assert refused(db, 'idem:next') == 'busy'
    assert close(db, 'stale', '0.1') == 'settled'
    admit(db, 'idem:next')


def test_one_operation_key_conflicts_globally_whatever_the_phase(db):
    admit(db, 'idem:k')
    close(db, 'idem:k', None)
    assert refused(db, 'idem:k') == 'duplicate_operation'
    assert refused(db, 'idem:k', phase='recommendation', bound='1') == 'duplicate_operation'
    assert len(rows(db)) == 1


def test_untrusted_evidence_refuses_admission(db):
    from jobfit.live.common import EvidenceError

    def broken():
        raise EvidenceError('corrupt')
    with conn_for(db) as conn, pytest.raises(store.AdmissionRefused) as exc:
        store.admit(conn, operation_key='idem:e', phase='parse', bound=Decimal('0.1'), daily_cap=CAP,
                    hard_stop=HARD_STOP, window_seconds=720.0, process_id='t', recorded_spend=broken)
    assert exc.value.code == 'evidence_fail_closed' and rows(db) == []


# --- lifetime hard stop: no under-count ------------------------------------------------------------------

def test_lifetime_counts_recorded_spend_plus_new_bound(db):
    assert refused(db, 'idem:l', bound='0.6', spend='4.0') == 'lifetime'        # 4.0 + 0.6 > 4.5
    admit(db, 'idem:l2', bound='0.5', spend='4.0')                                # 4.5 = 4.5


def test_lifetime_liability_adds_open_reservations_to_recorded_spend_not_max(db):
    insert_row(db, 'open', datetime.now(UTC), datetime.now(UTC) + timedelta(minutes=10), reserved='0.5')
    with conn_for(db) as conn:
        open_liability = conn.execute(store.OPEN_LIABILITY_SQL).fetchone()[0]
    recorded = Decimal('1.0')                       # e.g. a settled operation's ledger lines
    assert recorded + open_liability == Decimal('1.5') != max(recorded, open_liability)
    # the admission formula is spend + open + new; with an open row the backstop refuses first anyway
    assert refused(db, 'idem:x', bound='0.6', spend='1.0', hard_stop=Decimal('2.0')) == 'busy'


# --- cross-midnight carry-over (D-101) -------------------------------------------------------------------

def jakarta(y, m, d, hh, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=timezone(timedelta(hours=7)))


def test_earlier_day_row_active_past_midnight_counts_for_the_whole_next_day(db):
    # settled yesterday at 23:50 WIB with a window ending 00:05 WIB today: it counts all day today
    insert_row(db, 'carry', jakarta(2026, 10, 8, 23, 50), jakarta(2026, 10, 9, 0, 5), status='settled',
               settled='1.8')
    noon = jakarta(2026, 10, 9, 12)                 # long after its active_until
    assert refused(db, 'idem:a', bound='0.3', at=noon) == 'budget'        # 1.8 + 0.3 > 2
    admit(db, 'idem:b', bound='0.2', at=noon)                              # 1.8 + 0.2 = 2


def test_earlier_day_row_that_ended_before_midnight_does_not_count(db):
    insert_row(db, 'done', jakarta(2026, 10, 8, 22), jakarta(2026, 10, 8, 23, 59), status='settled', settled='1.9')
    admit(db, 'idem:c', bound='1.9', at=jakarta(2026, 10, 9, 0, 1))
    (_, _, _, _, _, day, _), = [r for r in rows(db) if r[0] == 'idem:c']
    assert str(day) == '2026-10-09'


def test_admission_time_is_taken_after_the_budget_lock(db):
    """An admission that waits on the lock across midnight is labelled with the later time."""
    holder = conn_for(db)
    holder.execute('BEGIN')
    holder.execute('SELECT pg_advisory_xact_lock(%s)', (store.BUDGET_KEY,))
    result = {}

    def late():
        result['a'] = admit(db, 'idem:late')
    t = threading.Thread(target=late)
    t.start()
    t.join(0.5)
    assert t.is_alive()                              # waiting on BUDGET_KEY
    with conn_for(db) as conn:
        before_release = conn.execute('SELECT clock_timestamp()').fetchone()[0]
    holder.execute('COMMIT')
    holder.close()
    t.join(30)
    assert result['a'].created_at >= before_release


# --- settlement ---------------------------------------------------------------------------------------------

def test_settle_release_and_closed_rows_are_final(db):
    admit(db, 'idem:s')
    assert close(db, 'idem:s', '0.0123') == 'settled'
    assert close(db, 'idem:s', None) == 'already_closed'
    admit(db, 'idem:r')
    assert close(db, 'idem:r', None) == 'released'
    assert {(r[0], r[2], r[4]) for r in rows(db)} == {('idem:s', 'settled', Decimal('0.0123000000')),
                                                       ('idem:r', 'released', Decimal('0E-10'))}


def test_two_concurrent_settlers_produce_one_final_state(db):
    admit(db, 'idem:t')
    barrier, out = threading.Barrier(2), []

    def settle(amount):
        barrier.wait()
        out.append(close(db, 'idem:t', amount))
    threads = [threading.Thread(target=settle, args=(a,)) for a in ('0.2', None)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    assert sorted(out, key=str) in (['already_closed', 'settled'], ['already_closed', 'released'])


def test_settling_an_unknown_reservation_fails_closed(db):
    from jobfit.live.common import EvidenceError
    with pytest.raises(EvidenceError):
        close(db, 'idem:none', None)


# --- concurrency -----------------------------------------------------------------------------------------------

def test_parallel_admissions_admit_exactly_one(db):
    barrier, out = threading.Barrier(8), []

    def one(i):
        barrier.wait()
        try:
            admit(db, f'idem:p{i}', bound='0.3')
            out.append('admitted')
        except store.AdmissionRefused as exc:
            out.append(exc.code)
    threads = [threading.Thread(target=one, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    assert out.count('admitted') == 1 and set(out) == {'admitted', 'busy'}


def test_near_cap_sequential_admissions_never_exceed_the_cap(db):
    admitted = Decimal(0)
    for i in range(10):
        try:
            admit(db, f'idem:n{i}', bound='0.45')
            admitted += Decimal('0.45')
            close(db, f'idem:n{i}', '0.45')
        except store.AdmissionRefused as exc:
            assert exc.code == 'budget'
    assert admitted == Decimal('1.80')


def test_the_gate_is_a_session_lock_released_with_the_connection(db):
    a, b = conn_for(db), conn_for(db)
    assert store.try_gate(a) and not store.try_gate(b)
    a.close()
    assert store.try_gate(b)
    b.close()
    assert GATE_KEY != store.BUDGET_KEY


# --- ticket (live_quota) --------------------------------------------------------------------------------------

HMAC = 'b' * 64


def test_ticket_consumed_once_then_refused_and_old_rows_are_deleted(db):
    connect = lambda: conn_for(db)
    assert quota.consume_ticket(connect, HMAC) == 'consumed'
    assert quota.consume_ticket(connect, HMAC) == 'refused'
    with conn_for(db) as conn:
        conn.execute("UPDATE live_quota SET consumed_at = now() - interval '49 hours'")
        conn.execute("INSERT INTO live_quota VALUES (%s, now() - interval '50 hours')", ('c' * 64,))
    assert quota.consume_ticket(connect, HMAC) == 'consumed'
    with conn_for(db) as conn:
        assert conn.execute('SELECT ip_hmac FROM live_quota').fetchall() == [(HMAC,)]


def test_two_concurrent_consumptions_for_one_ip_consume_exactly_one(db):
    barrier, out = threading.Barrier(2), []

    def one():
        barrier.wait()
        out.append(quota.consume_ticket(lambda: conn_for(db), HMAC))
    threads = [threading.Thread(target=one) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    assert sorted(out) == ['consumed', 'refused']


class _CommitFails:
    """Delegates to a real connection; COMMIT really commits, then raises (outcome unknown)."""

    def __init__(self, conn, after=True):
        self.conn, self.after = conn, after

    def execute(self, sql, *a, **kw):
        if sql == 'COMMIT':
            if self.after:
                self.conn.execute(sql)
            raise psycopg.OperationalError('connection lost during COMMIT')
        return self.conn.execute(sql, *a, **kw)

    def close(self):
        self.conn.close()


def test_ticket_commit_outcome_unknown_is_reported_and_the_ticket_may_be_consumed(db):
    assert quota.consume_ticket(lambda: _CommitFails(conn_for(db)), HMAC) == 'unknown'
    assert quota.consume_ticket(lambda: conn_for(db), HMAC) == 'refused'      # it had committed


def test_ticket_failure_before_commit_is_unavailable_and_consumes_nothing(db):
    class Broken(_CommitFails):
        def execute(self, sql, *a, **kw):
            if 'INSERT INTO live_quota' in sql:
                raise psycopg.OperationalError('connection lost')
            return self.conn.execute(sql, *a, **kw)
    assert quota.consume_ticket(lambda: Broken(conn_for(db)), HMAC) == 'unavailable'
    assert quota.consume_ticket(lambda: conn_for(db), HMAC) == 'consumed'


def test_admission_commit_outcome_unknown_never_guesses(db):
    with pytest.raises(store.AdmissionOutcomeUnknown):
        store.admit(_CommitFails(conn_for(db)), operation_key='idem:u', phase='parse', bound=Decimal('0.1'),
                    daily_cap=CAP, hard_stop=HARD_STOP, window_seconds=720.0, process_id='t',
                    recorded_spend=lambda: Decimal(0))
    assert refused(db, 'idem:u') == 'duplicate_operation'        # it had committed: a retry never re-runs
    close(db, 'idem:u', None)
    with pytest.raises(store.AdmissionOutcomeUnknown):
        store.admit(_CommitFails(conn_for(db), after=False), operation_key='idem:v', phase='parse',
                    bound=Decimal('0.1'), daily_cap=CAP, hard_stop=HARD_STOP, window_seconds=720.0,
                    process_id='t', recorded_spend=lambda: Decimal(0))
    admit(db, 'idem:v')                                           # it had not committed: a retry admits


def test_settlement_commit_outcome_unknown_is_reported(db):
    admit(db, 'idem:w')
    with pytest.raises(store.SettlementOutcomeUnknown):
        store.close(_CommitFails(conn_for(db)), 'idem:w', Decimal('0.1'))
    with conn_for(db) as conn:
        assert store.status_of(conn, 'idem:w') == 'settled'
