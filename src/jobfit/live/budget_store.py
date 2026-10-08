"""Persisted budget reservations (D-096, D-101): admission, settlement and the reconciler queries.

All statements run on a connection in autocommit mode with explicit BEGIN/COMMIT, so the one
moment whose outcome can be unknown (COMMIT) is visible. Admission and settlement are serialized
by the BUDGET_KEY transaction lock. Times come from the database wall clock (clock_timestamp()
read after the lock); they are not assumed monotonic. Amounts are numeric/Decimal only.

Admission, under the lock, refuses in this order:
- duplicate_operation: the operation key exists (one idempotency key conflicts globally);
- ledger_storage_mismatch: any row (whatever its status) has a malformed process_id or one bound
  to another ledger storage root (persistent ledger contract C7: every reservation must be
  settleable from the current storage's evidence);
- busy: ANY reservation is still 'reserved' (the persisted backstop of the live gate: an
  unresolved row is evidence that an earlier billable operation was not safely closed);
- evidence_fail_closed: the ledger, intent journal or breach marker cannot be trusted, or the
  settled history in the database exceeds the recorded spend (evidence was lost or reset);
- budget: the day's liability (with the conservative carry-over) plus the new bound exceeds the cap;
- lifetime: recorded spend plus open liability plus the new bound exceeds API_HARD_STOP_USD.
``recorded_spend()`` is read exactly once per admission transaction; the evidence check and the
lifetime check use that one snapshot.

process_id grammar: ``<storage_id>:<pid>``, 32 lowercase hex characters, a colon, a decimal pid
without sign or leading zero. Closed rows are the database witness of the settled history and are
never purged by this code (D-101 retention invariant).
"""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from jobfit.live.common import EvidenceError
from jobfit.live.keys import BUDGET_KEY, GATE_KEY, owner_key

NOW_SQL = ("SELECT ts, (ts AT TIME ZONE 'Asia/Jakarta')::date, "
           "(((ts AT TIME ZONE 'Asia/Jakarta')::date)::timestamp AT TIME ZONE 'Asia/Jakarta') "
           'FROM (SELECT {source} AS ts) t')
# Conservative carry-over (D-101): an earlier-day reservation whose possible activity window crossed
# today's start counts for the WHOLE day at its reserved (open) or settled amount.
DAY_LIABILITY_SQL = ("SELECT coalesce(sum(CASE status WHEN 'reserved' THEN reserved_usd "
                     "WHEN 'settled' THEN settled_usd ELSE 0 END), 0) FROM budget_reservations "
                     'WHERE production_day = %(today)s OR (production_day < %(today)s AND active_until > %(day_start)s)')
OPEN_LIABILITY_SQL = "SELECT coalesce(sum(reserved_usd), 0) FROM budget_reservations WHERE status = 'reserved'"
INSERT_SQL = ('INSERT INTO budget_reservations (operation_key, phase, reserved_usd, process_id, created_at, '
              'production_day, active_until) VALUES (%(op)s, %(phase)s, %(bound)s, %(pid)s, %(ts)s, %(today)s, '
              '%(ts)s + make_interval(secs => %(window)s)) ON CONFLICT (operation_key) DO NOTHING '
              'RETURNING reservation_id, created_at, active_until, production_day')


PROCESS_ID_RE = re.compile(r'([0-9a-f]{32}):([1-9][0-9]*)')
PROCESS_ID_SQL = '^[0-9a-f]{32}:[1-9][0-9]*$'        # the same grammar, as a PostgreSQL regular expression
FOREIGN_STORAGE_SQL = ("SELECT 1 FROM budget_reservations WHERE process_id !~ %(grammar)s "
                       'OR substr(process_id, 1, 32) <> %(sid)s LIMIT 1')
SETTLED_TOTAL_SQL = "SELECT coalesce(sum(settled_usd), 0) FROM budget_reservations WHERE status = 'settled'"


def parse_process_id(value) -> tuple[str, int]:
    """(storage_id, pid) of a well-formed process_id; ValueError for anything else."""
    m = PROCESS_ID_RE.fullmatch(value) if isinstance(value, str) else None
    if m is None:
        raise ValueError('malformed reservation process_id')
    return m.group(1), int(m.group(2))


def process_id_for(storage_id: str, pid: int) -> str:
    value = f'{storage_id}:{pid}'
    parse_process_id(value)
    return value


class AdmissionRefused(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class AdmissionUnavailable(RuntimeError):
    """A clean failure before COMMIT was sent: nothing was reserved."""


class AdmissionOutcomeUnknown(RuntimeError):
    """COMMIT was sent but its outcome is not proven: never enter the pipeline, never retry here."""


class SettlementOutcomeUnknown(RuntimeError):
    """COMMIT of a settlement was sent but its outcome is not proven: re-read, never retry blindly."""


@dataclass(frozen=True)
class Admission:
    reservation_id: object
    operation_key: str
    phase: str
    reserved_usd: Decimal
    created_at: datetime
    active_until: datetime
    production_day: date


def _rollback(conn) -> None:
    try:
        conn.execute('ROLLBACK')
    except Exception:
        pass        # a broken connection has rolled back on the server already


def _now(conn, at=None):
    if at is None:
        return conn.execute(NOW_SQL.format(source='clock_timestamp()')).fetchone()
    return conn.execute(NOW_SQL.format(source='%s::timestamptz'), (at,)).fetchone()   # tests only


def admit(conn, *, operation_key: str, phase: str, bound: Decimal, daily_cap: Decimal, hard_stop: Decimal,
          window_seconds: float, process_id: str, storage_id: str, recorded_spend: Callable[[], Decimal],
          at=None) -> Admission:
    """One admission transaction. ``recorded_spend()`` reads the ledger and journal after the lock, once."""
    if not (isinstance(bound, Decimal) and bound.is_finite() and bound > 0):
        raise AdmissionRefused('budget')
    try:
        if parse_process_id(process_id)[0] != storage_id:
            raise ValueError('process_id is not bound to the admitted storage')
    except ValueError:
        raise AdmissionRefused('ledger_storage_mismatch') from None
    try:
        conn.execute('BEGIN')
        conn.execute('SELECT pg_advisory_xact_lock(%s)', (BUDGET_KEY,))
        ts, today, day_start = _now(conn, at)
        refusal = None
        if conn.execute('SELECT 1 FROM budget_reservations WHERE operation_key = %s', (operation_key,)).fetchone():
            refusal = 'duplicate_operation'
        elif conn.execute(FOREIGN_STORAGE_SQL, {'grammar': PROCESS_ID_SQL, 'sid': storage_id}).fetchone():
            refusal = 'ledger_storage_mismatch'
        elif conn.execute("SELECT 1 FROM budget_reservations WHERE status = 'reserved' LIMIT 1").fetchone():
            refusal = 'busy'
        else:
            spend = recorded_spend()                     # the one evidence snapshot of this admission
            settled_total = conn.execute(SETTLED_TOTAL_SQL).fetchone()[0]
            if settled_total > spend:
                raise EvidenceError('the settled history exceeds the recorded spend: evidence was lost')
            day = conn.execute(DAY_LIABILITY_SQL, {'today': today, 'day_start': day_start}).fetchone()[0]
            open_liability = conn.execute(OPEN_LIABILITY_SQL).fetchone()[0]
            if day + bound > daily_cap:
                refusal = 'budget'
            elif spend + open_liability + bound > hard_stop:
                refusal = 'lifetime'
        row = None
        if refusal is None:
            row = conn.execute(INSERT_SQL, {'op': operation_key, 'phase': phase, 'bound': bound, 'pid': process_id,
                                            'ts': ts, 'today': today, 'window': window_seconds}).fetchone()
            if row is None:
                refusal = 'duplicate_operation'
        if refusal is not None:
            _rollback(conn)
            raise AdmissionRefused(refusal)
    except AdmissionRefused:
        raise
    except EvidenceError:
        _rollback(conn)
        raise AdmissionRefused('evidence_fail_closed') from None
    except Exception:
        _rollback(conn)
        raise AdmissionUnavailable('admission failed before commit; nothing was reserved') from None
    try:
        conn.execute('COMMIT')
    except Exception:
        raise AdmissionOutcomeUnknown('admission commit outcome is unknown') from None
    reservation_id, created_at, active_until, production_day = row
    return Admission(reservation_id, operation_key, phase, bound, created_at, active_until, production_day)


def close(conn, operation_key: str, settled_usd: Decimal | None) -> str:
    """Settle (``settled_usd``) or release (None) one open reservation. Returns the outcome.

    A closed row is never touched ('already_closed'); the guard trigger keeps it immutable anyway.
    """
    status = 'released' if settled_usd is None else 'settled'
    amount = Decimal(0) if settled_usd is None else settled_usd
    try:
        conn.execute('BEGIN')
        conn.execute('SELECT pg_advisory_xact_lock(%s)', (BUDGET_KEY,))
        row = conn.execute('SELECT status FROM budget_reservations WHERE operation_key = %s FOR UPDATE',
                           (operation_key,)).fetchone()
        if row is None:
            _rollback(conn)
            raise EvidenceError('settlement of an unknown reservation')
        if row[0] != 'reserved':
            _rollback(conn)
            return 'already_closed'
        conn.execute("UPDATE budget_reservations SET status = %s, settled_usd = %s, "
                     'closed_at = greatest(clock_timestamp(), created_at) '
                     "WHERE operation_key = %s AND status = 'reserved'", (status, amount, operation_key))
    except EvidenceError:
        raise
    except Exception:
        _rollback(conn)
        raise
    try:
        conn.execute('COMMIT')
    except Exception:
        raise SettlementOutcomeUnknown('settlement commit outcome is unknown') from None
    return status


def status_of(conn, operation_key: str) -> str | None:
    row = conn.execute('SELECT status FROM budget_reservations WHERE operation_key = %s', (operation_key,)).fetchone()
    return row[0] if row else None


def process_of(conn, operation_key: str) -> str | None:
    row = conn.execute('SELECT process_id FROM budget_reservations WHERE operation_key = %s',
                       (operation_key,)).fetchone()
    return row[0] if row else None


def expired_open(conn, *, at=None) -> list[str]:
    """Open reservations whose possible activity window has ended (reconciliation candidates).

    ``at`` is a test seam only: None (production) compares with the database clock_timestamp().
    """
    return [r[0] for r in conn.execute(
        "SELECT operation_key FROM budget_reservations WHERE status = 'reserved' "
        'AND active_until < coalesce(%s::timestamptz, clock_timestamp()) ORDER BY created_at', (at,)).fetchall()]


def try_gate(conn) -> bool:
    return bool(conn.execute('SELECT pg_try_advisory_lock(%s)', (GATE_KEY,)).fetchone()[0])


def release_gate(conn) -> None:
    conn.execute('SELECT pg_advisory_unlock(%s)', (GATE_KEY,))


def take_owner(conn, operation_key: str) -> None:
    conn.execute('SELECT pg_advisory_lock(%s)', (owner_key(operation_key),))


def try_owner(conn, operation_key: str) -> bool:
    return bool(conn.execute('SELECT pg_try_advisory_lock(%s)', (owner_key(operation_key),)).fetchone()[0])


def release_owner(conn, operation_key: str) -> None:
    conn.execute('SELECT pg_advisory_unlock(%s)', (owner_key(operation_key),))
