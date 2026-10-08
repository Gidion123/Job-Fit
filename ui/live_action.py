"""Pending live-action key for the UI (D-101; Phase 2B audit correction B).

One explicit user action gets one UUIDv4 Idempotency-Key. Until the server acknowledges the action
with a run id, a retry of the same action (same fingerprint) reuses that key, so a lost response can
never start a second billable run. The fingerprint is an opaque SHA-256 digest of the action's
identity (demo CV id, or later the consent digest of an uploaded CV; seniority switch; canonical
filters): never CV text, file bytes or object reprs. It lives only in the Streamlit session.
"""
from __future__ import annotations

import hashlib
import json
import uuid

FILTER_FIELDS = ('role_family', 'country_code', 'city', 'work_mode', 'posted_within_days', 'include_unknown')


def _canonical(field: str, value):
    if isinstance(value, str):
        value = value.strip() or None
    if field == 'include_unknown':
        return True if value is None else bool(value)       # RunRequest default
    return value


def action_fingerprint(cv_identity: str, seniority: bool, filters: dict | None) -> str:
    """64-hex digest of the action identity; equal for semantically identical actions."""
    filters = filters or {}
    canon = {'cv': str(cv_identity), 'seniority': bool(seniority),
             'filters': {f: _canonical(f, filters.get(f)) for f in FILTER_FIELDS}}
    return hashlib.sha256(json.dumps(canon, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class LiveActions:
    """Kept in st.session_state. Polling never touches it."""

    def __init__(self):
        self._pending: tuple[str, str] | None = None     # (fingerprint, key) not yet acknowledged
        self.last_run_id: str | None = None

    def key_for(self, fingerprint: str) -> str:
        if self._pending is not None and self._pending[0] == fingerprint:
            return self._pending[1]                      # a retry of the same action
        self._pending = (fingerprint, str(uuid.uuid4()))  # a new explicit action
        return self._pending[1]

    def acknowledged(self, run_id: str) -> None:
        """The server returned a run id: the next click is a new action with a new key."""
        self._pending = None
        self.last_run_id = run_id

    @property
    def pending_key(self) -> str | None:
        return self._pending[1] if self._pending else None
