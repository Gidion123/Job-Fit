"""Ingress controls and the per-IP ticket (D-096, D-101).

Trust chain (deployment detail, not yet validated end to end): only Caddy is public; it overwrites
the forwarded client-IP header; Streamlit forwards the normalized IP with the internal service
token; FastAPI accepts the IP only after a constant-time token check. Raw IPs are never stored:
only HMAC-SHA256(JOBFIT_IP_HMAC_KEY, ip), with IPv6 reduced to its /64.

The ticket is consumed by one conditional upsert, in its own short transaction on its own
connection, at the first billable call of an ordinary public parse. A proven commit consumes it
for good (no refund); an unproven commit is 'unknown' and is never repeated in the operation.
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


def consume_ticket(connect: Callable, ip_hmac: str) -> str:
    """'consumed' | 'refused' | 'unavailable' (failed before COMMIT) | 'unknown' (COMMIT not proven)."""
    try:
        conn = connect()
    except Exception:
        return 'unavailable'
    try:
        try:
            conn.execute('BEGIN')
            conn.execute(RETENTION_SQL)
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
    """What the API passes to a live operation: never a raw IP."""
    operation_key: str
    owner: bool
    ip_pseudonym: str | None
    session_id: str
    run_id: str


class Ingress:
    def __init__(self, internal_token: str | None, owner_token: str | None = None, ip_hmac_key: str | None = None,
                 *, session_limit: int = SESSION_LIMIT, session_window: float = SESSION_WINDOW_SECONDS,
                 clock=time.monotonic):
        if not internal_token:
            raise ValueError('the internal service token is required')
        self._internal, self._owner, self._ip_key = internal_token, owner_token, ip_hmac_key
        self.session_limit, self.session_window, self.clock = session_limit, session_window, clock
        self._sessions: dict[str, deque] = {}
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
        key = pseudonym or 'unknown'
        now = self.clock()
        with self._lock:
            q = self._sessions.setdefault(key, deque())
            while q and now - q[0] > self.session_window:
                q.popleft()
            if len(q) >= self.session_limit:
                return False
            q.append(now)
            return True
