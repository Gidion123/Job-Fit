"""D-051 owner-scoped volatile state and consent/lifecycle primitives.

No persistence or background heartbeat. CP3 must wire browser liveness and a
periodic cleanup scheduler; these unit controls are not deployed guarantees.
"""
from dataclasses import dataclass, field
from copy import deepcopy
import hashlib
import hmac
import math
import secrets
import threading
import time

class SessionDenied(PermissionError):
    pass

@dataclass(frozen=True)
class SessionHandle:
    session_id: str
    credential: str = field(repr=False)

@dataclass(frozen=True)
class Lease:
    session_id: str
    generation: int
    text_digest: str

@dataclass
class _State:
    owner_digest: bytes = field(repr=False)
    created: float
    heartbeat: float
    activity: float
    generation: int = 0
    text: str | None = field(default=None, repr=False)
    text_digest: str | None = None
    consent_digest: str | None = None
    masking_version: str | None = None
    data: dict = field(default_factory=dict, repr=False)

class SessionStore:
    def __init__(self, *, clock=time.monotonic, disconnect_seconds=120, idle_seconds=1800, absolute_seconds=7200):
        limits = (disconnect_seconds, idle_seconds, absolute_seconds)
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in limits):
            raise ValueError('Session timeouts must be positive finite numbers')
        self.clock = clock
        self.disconnect, self.idle, self.absolute = limits
        self._states = {}; self._lock = threading.RLock()

    def create(self):
        with self._lock:
            now = self.clock(); token = secrets.token_urlsafe(32); identity = secrets.token_urlsafe(24)
            self._states[identity] = _State(hashlib.sha256(token.encode()).digest(), now, now, now)
            return SessionHandle(identity, token)

    def _expired(self, state, now):
        return now >= min(state.heartbeat + self.disconnect, state.activity + self.idle, state.created + self.absolute)

    def _drop(self, identity):
        state = self._states.pop(identity, None)
        if state:
            state.text = None; state.text_digest = None; state.consent_digest = None
            state.data.clear(); state.generation += 1

    def _get(self, handle):
        state = self._states.get(handle.session_id)
        if state is None or not hmac.compare_digest(state.owner_digest, hashlib.sha256(handle.credential.encode()).digest()):
            raise SessionDenied('Session unavailable')
        if self._expired(state, self.clock()):
            self._drop(handle.session_id)
            raise SessionDenied('Session unavailable')
        return state

    def heartbeat(self, handle, *, user_activity=False):
        with self._lock:
            state = self._get(handle); now = self.clock(); state.heartbeat = now
            if user_activity:
                state.activity = now

    def set_preview(self, handle, preview):
        from jobfit.privacy.masking import MaskedPreview
        if not isinstance(preview, MaskedPreview) or hashlib.sha256(preview.text.encode()).hexdigest() != preview.digest:
            raise ValueError('Validated local masked preview required')
        with self._lock:
            state = self._get(handle)
            state.generation += 1; state.data.clear(); state.consent_digest = None
            state.text = preview.text; state.text_digest = preview.digest; state.masking_version = preview.version
            state.activity = self.clock()
            return Lease(handle.session_id, state.generation, preview.digest)

    def preview(self, handle):
        with self._lock:
            state = self._get(handle)
            return state.text, state.text_digest

    def consent(self, handle, *, exact_digest, affirmative):
        with self._lock:
            state = self._get(handle)
            if affirmative is not True or not state.text or exact_digest != state.text_digest:
                raise SessionDenied('Affirmative consent for exact preview required')
            state.consent_digest = exact_digest; state.activity = self.clock()
            return Lease(handle.session_id, state.generation, exact_digest)

    def _authorized(self, handle, lease):
        state = self._get(handle)
        if (lease.session_id != handle.session_id or lease.generation != state.generation
                or lease.text_digest != state.text_digest or state.consent_digest != lease.text_digest):
            raise SessionDenied('Preview changed or consent unavailable')
        return state

    def dispatch(self, handle, lease, operation):
        """Pass only exact consented text; do not hold the lock during a provider call.

        Recheck after completion: late data never gets stored or returned. A
        request already in flight cannot be recalled from a provider.
        """
        with self._lock:
            text = self._authorized(handle, lease).text
        result = operation(text)
        with self._lock:
            self._authorized(handle, lease)
        return result

    def put(self, handle, lease, key, value):
        with self._lock:
            self._authorized(handle, lease).data[key] = deepcopy(value)

    def read(self, handle, lease, key):
        with self._lock:
            return deepcopy(self._authorized(handle, lease).data[key])

    def delete(self, handle):
        with self._lock:
            self._get(handle); self._drop(handle.session_id)

    def exists(self, session_id: str) -> bool:
        """True while the session is stored (used to drop API results of expired sessions)."""
        with self._lock:
            return session_id in self._states

    def sweep(self):
        """CP3 periodic scheduler must call this without depending on user requests."""
        with self._lock:
            expired = [key for key, state in self._states.items() if self._expired(state, self.clock())]
            for key in expired:
                self._drop(key)
            return len(expired)
