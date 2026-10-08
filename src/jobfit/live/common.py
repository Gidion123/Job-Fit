"""Shared Phase 2B primitives: safety refusals, the call-scoped attempt context, file locks."""
from __future__ import annotations

import contextvars
import fcntl
import os
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from decimal import ROUND_CEILING, Decimal
from pathlib import Path

USD_QUANTUM = Decimal('1e-10')        # numeric(20, 10) in budget_reservations


class LiveSafetyRefusal(RuntimeError):
    """A Phase 2B safety refusal. Never a ValueError, so the frozen validated_call never repairs it."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class EvidenceError(RuntimeError):
    """The ledger, the intent journal or the breach marker cannot be trusted: fail closed."""


def usd_up(value) -> Decimal:
    """Exact Decimal of a float/str/Decimal amount, rounded UP to the reservation precision."""
    d = Decimal(str(value)) if not isinstance(value, Decimal) else value
    if not d.is_finite() or d < 0:
        raise EvidenceError('invalid amount')
    return d.quantize(USD_QUANTUM, rounding=ROUND_CEILING)


@dataclass
class AttemptContext:
    """One actual provider attempt. Lives in a ContextVar on the worker thread making the call."""
    operation_key: str
    attempt_id: str
    phase: str
    task: str
    model: str
    attempt_kind: str            # initial | validation_repair | length_continuation | embedding
    chain: str                   # parse | extraction | matching | fallback | embed
    wall_seconds: float          # W(call): per-call wall allowance
    owner: object = field(repr=False, default=None)     # the OperationState that admitted it
    upper_cost: Decimal | None = None
    inflight_open: bool = False


CURRENT_ATTEMPT: contextvars.ContextVar[AttemptContext | None] = contextvars.ContextVar('jobfit_attempt', default=None)


def append_durable(path: Path, line: str) -> None:
    """Append one line and fsync it (and the directory when the file is new)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open('a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()
        os.fsync(f.fileno())
    if new:
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


class FileLock:
    """In-process lock plus a short flock on a side file. Never held across a network call."""
    _registry: dict[str, 'FileLock'] = {}
    _registry_lock = threading.Lock()

    def __init__(self, path: Path):
        self.path = Path(path)
        self.thread_lock = threading.Lock()

    @classmethod
    def for_path(cls, path: Path) -> 'FileLock':
        key = str(Path(path).resolve())
        with cls._registry_lock:
            if key not in cls._registry:
                cls._registry[key] = cls(Path(key))
            return cls._registry[key]

    @contextmanager
    def hold(self, exclusive: bool):
        with self.thread_lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open('a') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
                try:
                    yield
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
