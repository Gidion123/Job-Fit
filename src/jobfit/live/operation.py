"""Operation runner for one billable live phase operation (D-096 gate, D-101 semantics).

Order (connection S is owned by the runner thread only; worker threads never touch it):
 1. S opens; the advisory gate is tried (busy -> refused, nothing reserved, no ticket consumed);
 2. preflight: process admission not disabled, the ledger storage root provisioned and writable,
    breach marker absent, evidence readable, the frozen client and its SDK object built; then
    expired, unowned reservations are reconciled;
 3. the owner lock is taken, the storage is validated again (same storage id or refused before any
    reservation), ``anchor_mono`` is read, then the admission transaction runs with the process_id
    ``<storage_id>:<pid>``;
 4. the frozen pipeline runs with a ReservedClient; every attempt re-checks the storage after its
    durable intent; a watchdog flags any call past W(call);
 5. drain, then settle or release from per-attempt evidence (deferred when it cannot be trusted, and
    always deferred after a storage-continuity failure);
 6. a fatal refusal discards the pipeline result; finally the locks are released and S closed.

Settlement (run and reconciliation alike) validates the CURRENT storage, checks the reservation's
storage binding, reads the evidence, validates the storage again, and only then closes the row.
Reconciliation runs only on valid storage with globally trustworthy evidence, and never releases an
expired reservation that has no evidence at all (a crash before the first intent and lost evidence
are indistinguishable after a restart).

The gate is phase-scoped: it is held for one parse or one recommendation operation only, never
across user think-time. The persisted backstop (any 'reserved' row refuses admission) keeps
operations from overlapping even if S, and with it the advisory locks, is lost.
"""
from __future__ import annotations

import logging
import os
import secrets
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import psycopg

from jobfit.live import budget_store as store
from jobfit.live.common import EvidenceError
from jobfit.live.deadlines import PhaseWindow, chat_timeout_seconds, phase_window
from jobfit.live.evidence import (BreachMarker, CorrelatedLedger, IntentJournal, breach_path, journal_path,
                                  operation_evidence, recorded_spend)
from jobfit.live.reserved_client import CallModel, OperationState, ReservedClient, bind_reserved_client
from jobfit.live.storage import LiveStorage, StorageUnavailable

log = logging.getLogger('jobfit.live')
REFUSAL_STATUS = {'busy': 429, 'budget': 429, 'lifetime': 429, 'quota_refused': 429, 'ticket_required': 403,
                  'duplicate_operation': 409, 'idempotency_key_mismatch': 409}   # every other code: 503


class LiveRefused(RuntimeError):
    """A refusal or fatal safety stop of a live operation; ``code`` is safe to show."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code
        self.status = REFUSAL_STATUS.get(code, 503)


@dataclass
class OperationReport:
    operation_key: str
    phase: str
    outcome: str                  # settled | released | deferred | already_closed
    spend: Decimal | None = None
    fatal_refusal: str | None = None


class LiveRuntime:
    """Process-wide production runtime: settings, accepted bounds, evidence files, DB connections."""

    def __init__(self, settings, bounds, *, pipeline_config: Path, client_factory: Callable[[str], object],
                 connect: Callable[[], psycopg.Connection] | None = None, clock=time.monotonic,
                 watchdog_interval: float = 0.5, drain_grace: float = 5.0, storage: LiveStorage | None = None):
        self.settings, self.bounds = settings, bounds
        self.ledger_path = Path(settings.usage_ledger)
        self.journal = IntentJournal(journal_path(self.ledger_path))
        self.ledger = CorrelatedLedger(self.ledger_path, self.journal)
        self.breach = BreachMarker(breach_path(self.ledger_path))
        self.call_model = CallModel(bounds, pipeline_config)
        timeout = chat_timeout_seconds(pipeline_config)
        self.windows = {p: phase_window(p, bounds, timeout) for p in ('parse', 'recommendation')}
        self.bound = {'parse': bounds.parse_max, 'recommendation': bounds.recommendation_upper_bound}
        self.client_factory = client_factory
        self.connect = connect or (lambda: psycopg.connect(settings.database_url, autocommit=True))
        self.clock, self.watchdog_interval, self.drain_grace = clock, watchdog_interval, drain_grace
        self.admission_disabled: str | None = None
        self.storage = storage if storage is not None else LiveStorage(self.ledger_path)
        self.pid = os.getpid()
        # Operations whose storage continuity failed: never settled or released by this process.
        # Process-local defence in depth; never cleared by code. Its lock is never held with op.lock.
        self.settlement_blocked: set[str] = set()
        self.settlement_blocked_lock = threading.Lock()

    # --- evidence and settlement ---------------------------------------------------------------
    def recorded_spend(self) -> Decimal:
        return recorded_spend(self.journal, self.ledger, self.breach)

    def storage_ready(self) -> bool:
        try:
            self.storage.validate()
            return True
        except StorageUnavailable:
            return False

    def _current_storage(self) -> str:
        try:
            return self.storage.validate()
        except StorageUnavailable as exc:
            raise EvidenceError(f'ledger storage unavailable: {exc.reason}') from None

    def _continuity_check(self, admitted: str) -> Callable[[], str | None]:
        def check() -> str | None:
            try:
                current = self.storage.validate()
            except Exception:
                return 'ledger_storage_unavailable'
            return None if current == admitted else 'ledger_storage_mismatch'
        return check

    def settle(self, conn, operation_key: str, *, reconciling: bool = False) -> OperationReport:
        """Settle or release one reservation from its evidence. EvidenceError leaves it reserved.

        Order: blocked check, current storage, reservation binding, evidence, storage again, close.
        """
        with self.settlement_blocked_lock:
            blocked = operation_key in self.settlement_blocked
        if blocked:
            raise EvidenceError('storage continuity failed for this operation: manual review')
        current = self._current_storage()
        try:
            bound_to, _ = store.parse_process_id(store.process_of(conn, operation_key))
        except ValueError:
            raise EvidenceError('reservation process_id is malformed or missing') from None
        if bound_to != current:
            raise EvidenceError('ledger storage mismatch: the reservation belongs to another storage')
        try:
            ev = operation_evidence(operation_key, self.journal, self.ledger)
        except EvidenceError:
            raise
        except Exception:
            raise EvidenceError('evidence unreadable') from None
        if reconciling and ev.attempts == 0:
            raise EvidenceError('no evidence for an expired reservation: manual review')
        if self._current_storage() != current:
            raise EvidenceError('ledger storage changed during settlement')
        for attempt, reported, upper in ev.breaches:
            try:
                self.breach.write('reported_cost_above_upper_bound', operation_key, attempt,
                                  f'reported {reported} > upper {upper}')
            except Exception:
                self.admission_disabled = 'breach_marker_write_failed'
                raise EvidenceError('breach marker could not be written; reservation kept open') from None
        amount = ev.settlement()
        try:
            outcome = store.close(conn, operation_key, amount)
        except store.SettlementOutcomeUnknown:
            with self.connect() as fresh:                 # re-read once; never retry blindly
                status = store.status_of(fresh, operation_key)
            outcome = status if status in ('settled', 'released') else 'deferred'
        return OperationReport(operation_key, '', outcome, ev.spend)

    def reconcile(self, *, at=None) -> list[OperationReport]:
        """Expired reservations whose owner lock is free and whose evidence is readable.

        Gated: storage valid, then the global evidence (breach marker absent, ledger and journal
        strictly parsable); otherwise no row is touched. ``at`` is a test seam (None: DB clock).
        """
        try:
            self.storage.validate()
        except StorageUnavailable as exc:
            log.warning('reconciliation skipped: ledger storage unavailable (%s)', exc.reason)
            return []
        try:
            self.recorded_spend()
        except Exception:
            log.warning('reconciliation skipped: evidence cannot be trusted (manual review)')
            return []
        reports = []
        with self.connect() as conn:
            for op in store.expired_open(conn, at=at):
                if not store.try_owner(conn, op):
                    log.warning('reservation %s is owned past active_until: manual review', op)
                    continue
                try:
                    reports.append(self.settle(conn, op, reconciling=True))
                except EvidenceError as exc:
                    log.warning('reservation %s kept open for manual review: %s', op, exc)
                    reports.append(OperationReport(op, '', 'deferred'))
                finally:
                    try:
                        store.release_owner(conn, op)
                    except Exception:
                        pass
        return reports

    # --- one operation ---------------------------------------------------------------------------
    def run(self, phase: str, operation_key: str, work: Callable[[ReservedClient], object], *,
            quota: Callable[[], str] | None = None,
            on_first_intent: Callable[[], bool] | None = None) -> tuple[object, OperationReport]:
        if phase not in self.windows:
            raise ValueError('unknown phase')
        window: PhaseWindow = self.windows[phase]
        try:
            conn = self.connect()
        except Exception:
            raise LiveRefused('unavailable') from None
        gate = owned = False
        op: OperationState | None = None
        stop = threading.Event()
        try:
            gate = store.try_gate(conn)
            if not gate:
                raise LiveRefused('busy')
            if self.admission_disabled:
                raise LiveRefused('admission_disabled')
            try:
                preflight_storage = self.storage.validate()
            except StorageUnavailable:
                raise LiveRefused('ledger_storage_unavailable') from None
            try:
                self.recorded_spend()
            except (EvidenceError, OSError):
                raise LiveRefused('evidence_fail_closed') from None
            try:
                inner = self.client_factory(operation_key)
                inner.sdk                               # build the SDK object before admission
            except Exception:
                raise LiveRefused('unavailable') from None
            try:
                self.reconcile()
            except Exception:
                log.warning('reconciliation failed; admission decides from persisted state')
            store.take_owner(conn, operation_key)
            owned = True
            try:                                        # immediately before admission: same storage
                storage_id = self.storage.validate()
            except StorageUnavailable:
                raise LiveRefused('ledger_storage_unavailable') from None
            if storage_id != preflight_storage:
                raise LiveRefused('ledger_storage_mismatch')
            anchor = self.clock()                       # before the admission statement is sent
            try:
                store.admit(conn, operation_key=operation_key, phase=phase, bound=self.bound[phase],
                            daily_cap=Decimal(str(self.settings.daily_budget_usd)),
                            hard_stop=Decimal(str(self.settings.api_hard_stop_usd)),
                            window_seconds=window.window, process_id=store.process_id_for(storage_id, self.pid),
                            storage_id=storage_id, recorded_spend=self.recorded_spend)
            except store.AdmissionRefused as exc:
                raise LiveRefused(exc.code) from None
            except store.AdmissionOutcomeUnknown:
                raise LiveRefused('admission_outcome_unknown') from None
            except store.AdmissionUnavailable:
                raise LiveRefused('unavailable') from None
            op = OperationState(operation_key, phase, self.bound[phase], window, anchor_mono=anchor,
                                quota=quota, on_first_intent=on_first_intent,
                                storage_check=self._continuity_check(storage_id), clock=self.clock)
            client = bind_reserved_client(inner, op, self.call_model, self.ledger_path)
            watchdog = threading.Thread(target=self._watch, args=(op, stop), daemon=True)
            watchdog.start()
            result, error = None, None
            try:
                result = work(client)
            except Exception as exc:               # a pipeline failure; settled from evidence below
                error = exc
            remaining = max(0.0, anchor + window.horizon - self.clock()) + self.drain_grace
            drained = op.wait_drained(remaining)
            with op.lock:
                op.closing = True
                storage_failed = op.storage_continuity_failed       # snapshot; op.lock released below
            report = OperationReport(operation_key, phase, 'deferred', None, op.fatal_refusal)
            if storage_failed:
                # Never settled or released by this process, even if the original storage comes back.
                # Registered while this runner still holds the owner lock, so no reconciler can close it.
                with self.settlement_blocked_lock:
                    self.settlement_blocked.add(operation_key)
                log.warning('operation %s kept reserved: ledger storage continuity failed', operation_key)
            elif drained and not self.admission_disabled:   # an unwritten breach marker keeps the row open
                try:
                    report = self.settle(conn, operation_key)
                    report.phase, report.fatal_refusal = phase, op.fatal_refusal
                except EvidenceError as exc:
                    log.warning('operation %s deferred for review: %s', operation_key, exc)
                except Exception:
                    op.set_fatal('coordinator_lost')
                    report.fatal_refusal = op.fatal_refusal
            if op.fatal_refusal is not None:
                raise LiveRefused(op.fatal_refusal)
            if error is not None:
                raise error
            return result, report
        finally:
            stop.set()
            for held, release in ((owned, lambda: store.release_owner(conn, operation_key)),
                                  (gate, lambda: store.release_gate(conn))):
                if held:
                    try:
                        release()
                    except Exception:
                        pass        # a lost connection has released its session locks
            try:
                conn.close()
            except Exception:
                pass

    def _watch(self, op: OperationState, stop: threading.Event) -> None:
        """Detects a call past W(call): sticky fatal, durable breach marker. It never cancels the call."""
        flagged: set[str] = set()
        while not stop.wait(self.watchdog_interval):
            for attempt in op.overdue():
                if attempt in flagged:
                    continue
                flagged.add(attempt)
                op.set_fatal('call_wall_exceeded')
                try:
                    self.breach.write('call_wall_exceeded', op.operation_key, attempt)
                except Exception:
                    op.set_fatal('breach_marker_write_failed')
                    self.admission_disabled = 'breach_marker_write_failed'


@dataclass
class _Entry:
    session: str
    phase: str
    run_id: str | None = None
    state: str = 'starting'          # starting | running | done | failed | admission_unknown


@dataclass
class IdempotencyRegistry:
    """In-memory binding of one idempotency key to (session, phase, run). The DB key is the backstop."""
    entries: dict[str, _Entry] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def claim(self, operation_key: str, session: str, phase: str) -> tuple[_Entry, bool]:
        """(entry, True): a new claim with a pre-assigned run id, go ahead. (entry, False): the same
        action again, return its run and never re-run. Another session or phase: refused."""
        with self.lock:
            entry = self.entries.get(operation_key)
            if entry is not None and (entry.session != session or entry.phase != phase):
                raise LiveRefused('idempotency_key_mismatch')
            if entry is None or entry.state == 'admission_unknown':
                # a retry after an unknown admission resolves through the DB key: duplicate or new admission
                entry = self.entries[operation_key] = _Entry(session, phase, run_id=secrets.token_urlsafe(12))
                return entry, True
            return entry, False

    def release(self, operation_key: str) -> None:
        with self.lock:
            self.entries.pop(operation_key, None)

    def update(self, operation_key: str, **changes) -> None:
        with self.lock:
            entry = self.entries.get(operation_key)
            if entry is not None:
                for k, v in changes.items():
                    setattr(entry, k, v)
