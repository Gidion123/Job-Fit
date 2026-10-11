"""Read-only persisted accounting snapshot, also usable while live is OFF.

Never calls storage.validate(), reconcile(), admission or settlement. Those can write.
File stat continuity brackets a read-only DB snapshot. A concurrent change omits balances.
"""
from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

from prometheus_client.core import GaugeMetricFamily

from jobfit.live import budget_store as bs
from jobfit.live.evidence import _read_lines, _index, _line_cost, journal_path, breach_path
from jobfit.live.storage import LiveStorage


def signature(paths):
    out = []
    for path in paths:
        try:
            st = path.stat()
            out.append((st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns))
        except FileNotFoundError:
            out.append(None)
    return out


class CostSnapshot:
    def __init__(self, ledger, connect, daily, hard_stop, total):
        self.ledger, self.connect = Path(ledger), connect
        self.daily, self.hard_stop, self.total = map(Decimal, map(str, (daily, hard_stop, total)))
        if not all(x.is_finite() and x >= 0 for x in (self.daily, self.hard_stop, self.total)):
            raise ValueError('invalid monitoring budget')
        if not self.daily <= self.hard_stop <= self.total:
            raise ValueError('invalid monitoring budget order')

    def __call__(self):
        storage = LiveStorage(self.ledger)
        paths = [storage.marker_path, self.ledger, journal_path(self.ledger), breach_path(self.ledger)]
        before = signature(paths)
        sid = storage.read_marker()
        rows = _read_lines(self.ledger)
        intents, lines = _index(_read_lines(journal_path(self.ledger)), rows)
        if _read_lines(breach_path(self.ledger)):
            raise ValueError('breach requires review')
        # Missing accounting is unknown, never silently cost=0.
        if any('cost_usd' not in r for r in lines.values()):
            raise ValueError('missing cost')
        costs = {k: Decimal(0) for k in ('reported', 'estimated_from_reported_tokens',
                                       'uncertain_upper_bound', 'rejected_request', 'other')}
        for row in lines.values():
            key = row.get('cost_source')
            costs[key if key in costs else 'other'] += _line_cost(row)
        unledgered = sum((Decimal(i['upper_cost']) for a, i in intents.items() if a not in lines), Decimal(0))
        recorded = sum(costs.values()) + unledgered
        with self.connect() as conn:
            conn.execute('BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            try:
                conn.execute("SET LOCAL statement_timeout = '1000ms'")
                _, today, day_start = conn.execute(bs.NOW_SQL.format(source='clock_timestamp()')).fetchone()
                if conn.execute(bs.FOREIGN_STORAGE_SQL, {'grammar': bs.PROCESS_ID_SQL, 'sid': sid}).fetchone():
                    raise ValueError('storage mismatch')
                settled = conn.execute(bs.SETTLED_TOTAL_SQL).fetchone()[0]
                if settled > recorded:
                    raise ValueError('lost evidence')
                day = conn.execute(bs.DAY_LIABILITY_SQL, {'today': today, 'day_start': day_start}).fetchone()[0]
                opened = conn.execute(bs.OPEN_LIABILITY_SQL).fetchone()[0]
                day_settled = conn.execute("SELECT coalesce(sum(settled_usd), 0) FROM budget_reservations "
                                           "WHERE status = 'settled' AND production_day = %s", (today,)).fetchone()[0]
            finally:
                conn.execute('ROLLBACK')  # read-only transaction, no changes to commit
        if before != signature(paths) or sid != storage.read_marker():
            raise ValueError('snapshot changed')
        return {'recorded_spend_usd': recorded, 'settled_usd': settled,
                'daily_settled_usd': day_settled, 'daily_liability_usd': day,
                'open_reserved_usd': opened, 'unledgered_upper_usd': unledgered,
                'uncertain_cost_usd': costs['uncertain_upper_bound'] + unledgered,
                'reported_cost_usd': costs['reported'],
                'token_estimated_cost_usd': costs['estimated_from_reported_tokens'],
                'daily_limit_usd': self.daily, 'hard_stop_usd': self.hard_stop, 'total_limit_usd': self.total,
                'daily_remaining_usd': max(Decimal(0), self.daily - day),
                'lifetime_remaining_usd': max(Decimal(0), self.hard_stop - recorded - opened),
                'ledger_bytes': sum(p.stat().st_size for p in paths[1:] if p.exists())}


def production_snapshot(settings, environ=None):
    """Dark settings deliberately omit live budget fields. Read only explicit env values in dark mode.

    No historical/development ledger fallback, no key access, no new settings for admission.
    """
    import psycopg
    from jobfit.config import PROD_LEDGER_ROOT
    env = os.environ if environ is None else environ
    if settings.environment != 'prod':
        return None
    try:
        path = Path(env['JOBFIT_USAGE_LEDGER'])
        if not path.is_absolute() or path.resolve().parent != PROD_LEDGER_ROOT:
            return None
        return CostSnapshot(path, lambda: psycopg.connect(settings.database_url, autocommit=True, connect_timeout=2),
                            env['JOBFIT_DAILY_BUDGET_USD'], env['API_HARD_STOP_USD'], env['API_BUDGET_USD'])
    except (KeyError, ValueError, ArithmeticError, OSError):
        return None


class CostCollector:
    def __init__(self, snapshot):
        self.snapshot = snapshot

    def describe(self):
        return []  # registration must not read files or contact DB

    def collect(self):
        readable = False
        if self.snapshot is not None and hasattr(self.snapshot, 'ledger'):
            try:
                LiveStorage(self.snapshot.ledger).read_marker()
                _read_lines(self.snapshot.ledger)
                _read_lines(journal_path(self.snapshot.ledger))
                readable = True
            except Exception:
                pass
        yield GaugeMetricFamily('jobfit_ledger_storage_readable',
                                'Marker and accounting files readable; not a write or persistence probe',
                                value=int(readable))
        values = None
        try:
            values = self.snapshot() if self.snapshot is not None else None
        except Exception:
            pass  # no exception payload or guessed zero balances
        yield GaugeMetricFamily('jobfit_accounting_snapshot_available',
                                '1 only for a consistent read-only ledger and DB snapshot', value=int(values is not None))
        if values is not None:
            for name, value in values.items():
                yield GaugeMetricFamily('jobfit_accounting_' + name, 'Read-only production accounting: ' + name,
                                        value=float(value))


class DatabaseCollector:
    """Independent PostgreSQL reachability; never opens a write transaction."""

    def __init__(self, connect):
        self.connect = connect

    def describe(self):
        return []

    def collect(self):
        available = False
        if self.connect is not None:
            try:
                with self.connect() as conn:
                    conn.execute('BEGIN READ ONLY')
                    try:
                        conn.execute("SET LOCAL statement_timeout = '1000ms'")
                        available = conn.execute('SELECT 1').fetchone() == (1,)
                    finally:
                        conn.execute('ROLLBACK')
            except Exception:
                pass
        yield GaugeMetricFamily('jobfit_postgres_available',
                                'Read-only SELECT 1 succeeded; no schema or persistence check', value=int(available))
