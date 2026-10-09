"""Phase 2B budget store on real PostgreSQL (D-096, D-101). Opt-in like the migration tests; no API calls.

Needs JOBFIT_MIGRATION_TESTS=1 and JOBFIT_MIGRATION_ADMIN_URL (a disposable pgvector server). Every
test uses its own scratch database upgraded to head, dropped afterwards.
"""
import os
import threading
import uuid
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
SID = uuid.uuid4().hex                       # the ledger storage every reservation here belongs to
PID = store.process_id_for(SID, 4242)


@pytest.fixture
def db():
    with baseline.scratch_database(ADMIN) as url:
        command.upgrade(alembic_config(url), 'head')
        yield url


def conn_for(url):
    return psycopg.connect(url, autocommit=True)


def settled_total(url):
    with conn_for(url) as conn:
        return conn.execute(store.SETTLED_TOTAL_SQL).fetchone()[0]


def admit(url, op, phase='parse', bound='0.4716399', spend=None, at=None, cap=CAP, hard_stop=HARD_STOP,
          window=720.0):
    """spend=None: evidence consistent with the database (the recorded spend equals the settled history)."""
    recorded = (lambda: settled_total(url)) if spend is None else (lambda: Decimal(spend))
    with conn_for(url) as conn:
        return store.admit(conn, operation_key=op, phase=phase, bound=Decimal(bound), daily_cap=cap,
                           hard_stop=hard_stop, window_seconds=window, process_id=PID, storage_id=SID,
                           recorded_spend=recorded, at=at)


def refused(url, *args, **kw):
    with pytest.raises(store.AdmissionRefused) as exc:
        admit(url, *args, **kw)
    return exc.value.code


def close(url, op, amount):
    with conn_for(url) as conn:
        return store.close(conn, op, None if amount is None else Decimal(amount))


def insert_row(url, op, created, active_until, status='reserved', reserved='0.5', settled=None, phase='parse',
               process_id=PID):
    """A historical row with explicit times (production_day must be the Jakarta date of created_at)."""
    with conn_for(url) as conn:
        conn.execute('INSERT INTO budget_reservations (operation_key, phase, reserved_usd, process_id, created_at, '
                     "production_day, active_until) VALUES (%s, %s, %s, %s, %s, "
                     "(%s::timestamptz AT TIME ZONE 'Asia/Jakarta')::date, %s)",
                     (op, phase, Decimal(reserved), process_id, created, created, active_until))
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
                    hard_stop=HARD_STOP, window_seconds=720.0, process_id=PID, storage_id=SID,
                    recorded_spend=broken)
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


def old_row(db, ip_hmac, hours):
    with conn_for(db) as conn:
        conn.execute("INSERT INTO live_quota VALUES (%s, now() - make_interval(secs => %s))", (ip_hmac, hours * 3600.0))


def quota_rows(db):
    with conn_for(db) as conn:
        return sorted(r[0] for r in conn.execute('SELECT ip_hmac FROM live_quota').fetchall())


def test_a_clean_refusal_never_undoes_the_48_hour_retention(db):
    old_row(db, HMAC, 1)                                  # this IP is within its 24 hours
    old_row(db, 'c' * 64, 50)                             # unrelated rows past 48 hours
    old_row(db, 'd' * 64, 49)
    assert quota.consume_ticket(lambda: conn_for(db), HMAC) == 'refused'
    assert quota_rows(db) == [HMAC]


def test_retention_purge_runs_without_any_ticket_consumption(db):
    old_row(db, 'c' * 64, 50)
    old_row(db, 'd' * 64, 48.5)
    old_row(db, 'e' * 64, 30)                             # between 24 and 48 hours: kept
    old_row(db, HMAC, 0)
    assert quota.purge_expired(lambda: conn_for(db)) == 2
    assert quota_rows(db) == sorted([HMAC, 'e' * 64])
    assert quota.purge_expired(lambda: conn_for(db)) == 0


def test_a_failed_purge_fails_the_ticket_closed_and_consumes_nothing(db):
    class PurgeFails(_CommitFails):
        def execute(self, sql, *a, **kw):
            if sql.startswith('DELETE FROM live_quota'):
                raise psycopg.OperationalError('connection lost')
            return self.conn.execute(sql, *a, **kw)
    assert quota.consume_ticket(lambda: PurgeFails(conn_for(db)), HMAC) == 'unavailable'
    assert quota_rows(db) == []
    with pytest.raises(psycopg.OperationalError):
        quota.purge_expired(lambda: PurgeFails(conn_for(db)))


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
    """Delegates to a real connection; COMMIT really commits, then raises (outcome unknown).

    With ``only_after``, only the COMMIT of a transaction that ran a statement containing that
    text fails (e.g. the ticket consume, not the separately committed retention purge).
    """

    def __init__(self, conn, after=True, only_after=None):
        self.conn, self.after, self.only_after, self.armed = conn, after, only_after, only_after is None

    def execute(self, sql, *a, **kw):
        if self.only_after and self.only_after in sql:
            self.armed = True
        if sql == 'COMMIT' and self.armed:
            if self.after:
                self.conn.execute(sql)
            raise psycopg.OperationalError('connection lost during COMMIT')
        return self.conn.execute(sql, *a, **kw)

    def close(self):
        self.conn.close()


def test_ticket_commit_outcome_unknown_is_reported_and_the_ticket_may_be_consumed(db):
    consume_commit_fails = lambda: _CommitFails(conn_for(db), only_after='INSERT INTO live_quota')
    assert quota.consume_ticket(consume_commit_fails, HMAC) == 'unknown'
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
                    daily_cap=CAP, hard_stop=HARD_STOP, window_seconds=720.0, process_id=PID,
                    storage_id=SID, recorded_spend=lambda: Decimal(0))
    assert refused(db, 'idem:u') == 'duplicate_operation'        # it had committed: a retry never re-runs
    close(db, 'idem:u', None)
    with pytest.raises(store.AdmissionOutcomeUnknown):
        store.admit(_CommitFails(conn_for(db), after=False), operation_key='idem:v', phase='parse',
                    bound=Decimal('0.1'), daily_cap=CAP, hard_stop=HARD_STOP, window_seconds=720.0,
                    process_id=PID, storage_id=SID, recorded_spend=lambda: Decimal(0))
    admit(db, 'idem:v')                                           # it had not committed: a retry admits


def test_settlement_commit_outcome_unknown_is_reported(db):
    admit(db, 'idem:w')
    with pytest.raises(store.SettlementOutcomeUnknown):
        store.close(_CommitFails(conn_for(db)), 'idem:w', Decimal('0.1'))
    with conn_for(db) as conn:
        assert store.status_of(conn, 'idem:w') == 'settled'


# --- persistent ledger storage: process_id grammar, admission order, one spend snapshot (C7) -----------------

GRAMMAR_CASES = [
    (PID, True),
    (f'{SID}:1', True),
    ('1234', False),                          # a bare pid (the pre-storage format)
    (f'{SID}:', False),
    (SID, False),
    (f'{SID}:0', False),
    (f'{SID}:01', False),
    (f'{SID}:-1', False),
    (f'{SID.upper()}:12', False),
    (f'{SID[:31]}:12', False),
    (f'{SID}a:12', False),
    (f'{SID}:12\n', False),
    (f'{SID}:12 ', False),
    (f'{SID}:1:2', False),
]


@pytest.mark.parametrize('value, ok', GRAMMAR_CASES)
def test_process_id_grammar_is_strict_in_python_and_in_sql(db, value, ok):
    try:
        store.parse_process_id(value)
        py_ok = True
    except ValueError:
        py_ok = False
    with conn_for(db) as conn:
        sql_ok = conn.execute('SELECT %s ~ %s', (value, store.PROCESS_ID_SQL)).fetchone()[0]
    assert py_ok is ok and sql_ok is ok


@pytest.mark.parametrize('bad', ['1234', 'old', f'{SID}:0', f'{uuid.uuid4().hex}:77'])
def test_a_foreign_or_malformed_storage_witness_refuses_before_busy(db, bad):
    now = datetime.now(UTC)
    insert_row(db, 'foreign', now - timedelta(minutes=2), now + timedelta(minutes=10), process_id=bad)  # reserved
    assert refused(db, 'idem:f') == 'ledger_storage_mismatch'          # not 'busy': the order is explicit


@pytest.mark.parametrize('status', ['settled', 'released'])
def test_a_closed_row_from_another_storage_also_refuses(db, status):
    now = datetime.now(UTC)
    insert_row(db, 'closed', now - timedelta(hours=2), now - timedelta(hours=1), status=status,
               settled='0.1' if status == 'settled' else '0',
               process_id=f'{uuid.uuid4().hex}:9')
    assert refused(db, 'idem:g', spend='5') == 'ledger_storage_mismatch'


def test_duplicate_comes_before_the_storage_witness(db):
    now = datetime.now(UTC)
    insert_row(db, 'idem:dup', now - timedelta(minutes=2), now + timedelta(minutes=10), process_id='1234')
    assert refused(db, 'idem:dup') == 'duplicate_operation'


def test_admit_refuses_a_process_id_not_bound_to_its_storage(db):
    other = uuid.uuid4().hex
    with conn_for(db) as conn:
        for pid, sid in ((PID, other), ('4242', SID), (f'{SID}:0', SID)):
            with pytest.raises(store.AdmissionRefused, match='ledger_storage_mismatch'):
                store.admit(conn, operation_key='idem:b', phase='parse', bound=Decimal('0.1'), daily_cap=CAP,
                            hard_stop=HARD_STOP, window_seconds=720.0, process_id=pid, storage_id=sid,
                            recorded_spend=lambda: Decimal(0))
    assert rows(db) == []


def test_settled_history_above_the_recorded_spend_fails_closed_before_budget_and_lifetime(db):
    now = datetime.now(UTC)
    insert_row(db, 'hist', now - timedelta(hours=30), now - timedelta(hours=29), status='settled', settled='0.3')
    assert refused(db, 'idem:h', spend='0.2999999999') == 'evidence_fail_closed'   # evidence lost
    admit(db, 'idem:h2', spend='0.3')                                              # consistent: admitted


class CountingSpend:
    def __init__(self, *values):
        self.values, self.calls = list(values), 0

    def __call__(self):
        self.calls += 1
        return Decimal(self.values[min(self.calls, len(self.values)) - 1])


def admit_with(url, op, spend, bound='0.1', hard_stop=HARD_STOP, cap=CAP):
    with conn_for(url) as conn:
        return store.admit(conn, operation_key=op, phase='parse', bound=Decimal(bound), daily_cap=cap,
                           hard_stop=hard_stop, window_seconds=720.0, process_id=PID, storage_id=SID,
                           recorded_spend=spend)


def test_recorded_spend_is_read_exactly_once_per_admission(db):
    ok = CountingSpend('0')
    admit_with(db, 'idem:once', ok)
    assert ok.calls == 1
    close(db, 'idem:once', '0.05')
    for spend, kw, code in ((CountingSpend('0'), {}, 'evidence_fail_closed'),            # 0.05 settled > 0
                            (CountingSpend('0.05'), {'bound': '3'}, 'budget'),
                            (CountingSpend('4.45'), {'bound': '0.1'}, 'lifetime')):
        with pytest.raises(store.AdmissionRefused, match=code):
            admit_with(db, 'idem:x', spend, **kw)
        assert spend.calls == 1
    for code, setup in (('duplicate_operation', None), ('busy', 'open'), ('ledger_storage_mismatch', 'foreign')):
        spend = CountingSpend('0.05')
        op = 'idem:once' if code == 'duplicate_operation' else f'idem:{code}'
        now = datetime.now(UTC)
        if setup == 'open':
            insert_row(db, 'open', now, now + timedelta(minutes=10))
        if setup == 'foreign':
            close(db, 'open', '0')
            insert_row(db, 'foreign', now - timedelta(hours=2), now - timedelta(hours=1), status='released',
                       process_id='99')
        with pytest.raises(store.AdmissionRefused, match=code):
            admit_with(db, op, spend)
        assert spend.calls == 0                         # refused before the evidence snapshot


def test_lifetime_uses_the_same_snapshot_as_the_evidence_check(db):
    spend = CountingSpend('0', '4.45')        # a second read would trip lifetime (4.45 + 0.1 > 4.5)
    admit_with(db, 'idem:snap', spend)
    assert spend.calls == 1 and rows(db)[0][2] == 'reserved'


def test_expired_open_uses_the_database_clock_unless_a_test_time_is_given(db):
    now = datetime.now(UTC)
    insert_row(db, 'soon', now - timedelta(minutes=1), now + timedelta(minutes=10))
    with conn_for(db) as conn:
        assert store.expired_open(conn) == []
        assert store.expired_open(conn, at=now + timedelta(minutes=11)) == ['soon']
        assert store.process_of(conn, 'soon') == PID and store.process_of(conn, 'none') is None
