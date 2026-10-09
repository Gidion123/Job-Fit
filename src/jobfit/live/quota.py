"""Ingress controls and the per-IP ticket (D-096, D-101).

Trust chain (deployment detail, not yet validated end to end): only Caddy is public; it overwrites
the forwarded client-IP header; Streamlit forwards the normalized IP with the internal service
token; FastAPI accepts the IP only after a constant-time token check. Raw IPs are never stored:
only HMAC-SHA256(JOBFIT_IP_HMAC_KEY, ip), with IPv6 reduced to its /64.

The ticket is consumed by one conditional upsert, in its own short transaction on its own
connection, at the first billable call of an ordinary public parse. A proven commit consumes it
for good (no refund); an unproven commit is 'unknown' and is never repeated in the operation.

Retention (D-096: IP-HMAC rows are deleted after 48 hours) has its own committed lifecycle:
``purge_expired`` runs at startup, hourly from the API sweeper, and as a separate committed
transaction before every consume, so a quota refusal (ROLLBACK) can never undo a deletion.
"""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

CONSUME_SQL = ('INSERT INTO live_quota (ip_hmac, consumed_at) VALUES (%s, now()) ON CONFLICT (ip_hmac) DO UPDATE '
               "SET consumed_at = now() WHERE live_quota.consumed_at <= now() - interval '24 hours' RETURNING 1")
RETENTION_SQL = "DELETE FROM live_quota WHERE consumed_at < now() - interval '48 hours'"
SESSION_LIMIT = 10                  # new sessions per IP pseudonym ...
SESSION_WINDOW_SECONDS = 3600.0     # ... per rolling hour (in memory; one API process)
UPLOAD_LIMIT = 10                   # CV preview mutations (uploads and preview edits) per IP pseudonym per
                                    # rolling hour (in memory; one API process)


def _purge(conn) -> int:
    try:
        conn.execute('BEGIN')
        deleted = conn.execute(RETENTION_SQL).rowcount
        conn.execute('COMMIT')
    except Exception:
        _rollback(conn)
        raise
    return deleted


def purge_expired(connect: Callable) -> int:
    """Delete quota rows older than 48 hours in their own committed transaction; raises on failure."""
    conn = connect()
    try:
        return _purge(conn)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def consume_ticket(connect: Callable, ip_hmac: str) -> str:
    """'consumed' | 'refused' | 'unavailable' (failed before COMMIT) | 'unknown' (COMMIT not proven)."""
    try:
        conn = connect()
    except Exception:
        return 'unavailable'
    try:
        try:
            _purge(conn)                    # committed on its own: a refusal below cannot undo it
        except Exception:
            return 'unavailable'            # fail closed: no consume, no provider call
        try:
            conn.execute('BEGIN')
            row = conn.execute(CONSUME_SQL, (ip_hmac,)).fetchone()
        except Exception:
            _rollback(conn)
            return 'unavailable'
        if row is None:
            _rollback(conn)
            return 'refused'
        try:
            conn.execute('COMMIT')
        except Exception:
            return 'unknown'
        return 'consumed'
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _rollback(conn) -> None:
    try:
        conn.execute('ROLLBACK')
    except Exception:
        pass


def normalize_ip(raw: str | None) -> str | None:
    if not raw or not isinstance(raw, str):
        return None
    try:
        ip = ipaddress.ip_address(raw.strip())
    except ValueError:
        return None
    if ip.version == 6:
        if ip.ipv4_mapped is not None:
            return str(ip.ipv4_mapped)
        return str(ipaddress.ip_network(f'{ip}/64', strict=False))
    return str(ip)


def _same(given: str | None, expected: str | None) -> bool:
    """Constant-time comparison over fixed-length digests (no early return on length or prefix)."""
    a = hashlib.sha256((given or '').encode()).digest()
    b = hashlib.sha256((expected or '').encode()).digest()
    return hmac.compare_digest(a, b) and bool(expected) and given is not None


@dataclass(frozen=True)
class LiveRequest:
    """What the API passes to a live operation: never a raw IP. Immutable once built."""
    operation_key: str
    owner: bool
    ip_pseudonym: str | None
    session_id: str
    run_id: str
    # Public flow: finalizes the session's recommendation allowance at the first durable intent;
    # returns True only on a proven pending(op) -> used(op) (or already used(op)). None for the owner.
    on_first_billable: Callable[[], bool] | None = None
    # Real-CV public beta: the durable ticket callable for the operation's first billable call
    # (BetaAllowances, only while the session holds no proven ticket). None otherwise.
    quota: Callable[[], str] | None = None


class SessionAllowances:
    """D-096: one ticket covers one recommendation run. In memory, like the sessions (one API process).

    no_ticket -> ticket_held -> pending(op) -> used(op); pending(op) -> ticket_held when the operation
    provably stopped before its first durable provider intent. used(op) never goes back.
    """
    TICKET_HELD, PENDING, USED = 'ticket_held', 'recommendation_pending', 'recommendation_used'

    def __init__(self):
        self._state: dict[str, tuple[str, str | None]] = {}
        self._lock = threading.Lock()

    def mark_ticket_held(self, session: str) -> None:
        """Phase 3 parse hook: called only after the parse ticket was consumed."""
        with self._lock:
            if session not in self._state:
                self._state[session] = (self.TICKET_HELD, None)

    def state(self, session: str) -> tuple[str, str | None]:
        with self._lock:
            return self._state.get(session, ('no_ticket', None))

    def claim(self, session: str, op: str) -> bool:
        with self._lock:
            state, owner_op = self._state.get(session, ('no_ticket', None))
            if state == self.TICKET_HELD:
                self._state[session] = (self.PENDING, op)
                return True
            return state in (self.PENDING, self.USED) and owner_op == op     # an idempotent retry

    def finalize(self, session: str, op: str) -> bool:
        with self._lock:
            state, owner_op = self._state.get(session, ('no_ticket', None))
            if owner_op != op or state not in (self.PENDING, self.USED):
                return False
            self._state[session] = (self.USED, op)
            return True

    def release_if_pending(self, session: str, op: str) -> None:
        with self._lock:
            if self._state.get(session) == (self.PENDING, op):
                self._state[session] = (self.TICKET_HELD, None)

    def drop(self, session: str) -> None:
        with self._lock:
            self._state.pop(session, None)

    def sessions(self) -> set[str]:
        with self._lock:
            return set(self._state)


BETA_LIMITS = {'parse': 1, 'search': 1, 'job_analysis': 3}


@dataclass(frozen=True)
class BetaClaim:
    """What one admitted public-beta operation gets from BetaAllowances.

    ``quota`` is the ticket callable for the operation's first billable call when the session holds no
    proven ticket yet (None once it does); ``on_first_intent`` counts the operation against the
    session allowance at its first durable provider intent.
    """
    quota: Callable[[], str] | None
    on_first_intent: Callable[[], bool]


class _BetaSession:
    def __init__(self):
        self.pending: dict[str, str] = {}     # operation -> phase, not yet at its first durable intent
        self.used: dict[str, str] = {}        # operation -> phase, counted for good


class BetaAllowances:
    """D-103 session allowance, in memory (no migration, no new persistent store).

    The durable per-IP ticket (``live_quota``, one per IP pseudonym per 24 hours) is unchanged and
    consumed at the first billable call of the session's first public operation. A session gets an
    allowance only when that consume returns a PROVEN 'consumed': 'refused', 'unavailable' and
    'unknown' create nothing, and the operation's own guard then stops it before any provider call.
    With the allowance, the same session may run 1 parse, 1 search and up to 3 job_analysis
    operations; an operation counts at its first durable provider intent and is never refunded after
    it. A restart loses the allowance; the IP gets no new durable ticket within 24 hours.
    """

    def __init__(self, limits: dict[str, int] | None = None):
        self.limits = dict(BETA_LIMITS if limits is None else limits)
        self._sessions: dict[str, _BetaSession] = {}      # only sessions with a proven ticket
        self._acquiring: dict[str, tuple[str, str]] = {}   # session -> (operation, phase) consuming the ticket
        self._lock = threading.Lock()

    def claim(self, session: str, phase: str, op: str, consume: Callable[[], str]) -> BetaClaim | str:
        """A BetaClaim, or a refusal code: phase_not_admitted, allowance_exhausted or busy."""
        if phase not in self.limits:
            return 'phase_not_admitted'
        on_first_intent = lambda: self.finalize(session, op)   # noqa: E731
        with self._lock:
            s = self._sessions.get(session)
            if s is None:
                acquiring = self._acquiring.get(session)
                if acquiring is not None and acquiring != (op, phase):
                    return 'busy'                # one ticket attempt per session at a time
                self._acquiring[session] = (op, phase)
                return BetaClaim(lambda: self._consume(session, phase, op, consume), on_first_intent)
            if s.pending.get(op) == phase or s.used.get(op) == phase:
                return BetaClaim(None, on_first_intent)          # the same operation again
            taken = sum(p == phase for p in s.pending.values()) + sum(p == phase for p in s.used.values())
            if taken >= self.limits[phase]:
                return 'allowance_exhausted'
            s.pending[op] = phase
            return BetaClaim(None, on_first_intent)

    def _consume(self, session: str, phase: str, op: str, consume: Callable[[], str]) -> str:
        try:
            outcome = consume()
        except Exception:
            outcome = 'unknown'
        with self._lock:
            if self._acquiring.get(session) == (op, phase):
                self._acquiring.pop(session)
            if outcome == 'consumed' and session not in self._sessions:
                s = self._sessions[session] = _BetaSession()
                s.pending[op] = phase
        return outcome

    def finalize(self, session: str, op: str) -> bool:
        """pending(op) -> used(op) at the first durable intent; True only when op is proven counted."""
        with self._lock:
            s = self._sessions.get(session)
            if s is None:
                return False
            if op in s.pending:
                s.used[op] = s.pending.pop(op)
                return True
            return op in s.used

    def release_if_pending(self, session: str, op: str) -> None:
        """The operation provably stopped before its first durable provider intent."""
        with self._lock:
            if self._acquiring.get(session, (None,))[0] == op:
                self._acquiring.pop(session)
            s = self._sessions.get(session)
            if s is not None:
                s.pending.pop(op, None)

    def remaining(self, session: str) -> dict[str, int] | None:
        """Per-phase operations left, or None while the session holds no proven ticket."""
        with self._lock:
            s = self._sessions.get(session)
            if s is None:
                return None
            return {p: n - sum(q == p for q in (*s.pending.values(), *s.used.values()))
                    for p, n in self.limits.items()}

    def drop(self, session: str) -> None:
        with self._lock:
            self._sessions.pop(session, None)
            self._acquiring.pop(session, None)

    def sessions(self) -> set[str]:
        with self._lock:
            return set(self._sessions) | set(self._acquiring)


class Ingress:
    def __init__(self, internal_token: str | None, owner_token: str | None = None, ip_hmac_key: str | None = None,
                 *, session_limit: int = SESSION_LIMIT, session_window: float = SESSION_WINDOW_SECONDS,
                 clock=time.monotonic):
        if not internal_token:
            raise ValueError('the internal service token is required')
        self._internal, self._owner, self._ip_key = internal_token, owner_token, ip_hmac_key
        self.session_limit, self.session_window, self.clock = session_limit, session_window, clock
        self._sessions: dict[str, deque] = {}
        self._uploads: dict[str, deque] = {}
        self._lock = threading.Lock()

    def internal_ok(self, token: str | None) -> bool:
        return _same(token, self._internal)

    def is_owner(self, token: str | None) -> bool:
        return _same(token, self._owner)

    def ip_pseudonym(self, raw_ip: str | None) -> str | None:
        ip = normalize_ip(raw_ip)
        if ip is None or not self._ip_key:
            return None
        return hmac.new(self._ip_key.encode(), ip.encode(), hashlib.sha256).hexdigest()

    def allow_session(self, pseudonym: str | None) -> bool:
        return self._allow(self._sessions, pseudonym, self.session_limit)

    def allow_upload(self, pseudonym: str | None) -> bool:
        """At most UPLOAD_LIMIT CV preview mutations (uploads and preview edits) per IP pseudonym per rolling
        hour; checked before an upload body is read."""
        return self._allow(self._uploads, pseudonym, UPLOAD_LIMIT)

    def _allow(self, buckets: dict, pseudonym: str | None, limit: int) -> bool:
        key = pseudonym or 'unknown'
        now = self.clock()
        with self._lock:
            q = buckets.setdefault(key, deque())
            while q and now - q[0] > self.session_window:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True
