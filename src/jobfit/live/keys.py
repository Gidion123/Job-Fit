"""64-bit PostgreSQL advisory-lock keys and durable operation identities (Phase 2B)."""
from __future__ import annotations

import hashlib
import uuid

from jobfit.db.migrate import SCHEMA_LOCK_KEY


def advisory_key(label: str) -> int:
    """First 8 bytes of SHA-256(label) as a signed bigint (single-bigint advisory key space)."""
    return int.from_bytes(hashlib.sha256(label.encode()).digest()[:8], 'big', signed=True)


GATE_KEY = advisory_key('jobfit:live-gate:v1')       # session level: one billable phase operation
BUDGET_KEY = advisory_key('jobfit:budget:v1')        # transaction level: admission and settlement
FIXED_KEYS = frozenset({SCHEMA_LOCK_KEY, GATE_KEY, BUDGET_KEY})


def owner_key(operation_key: str) -> int:
    """Liveness lock of one operation. A collision with a fixed key refuses the operation."""
    key = advisory_key('jobfit:owner:v1:' + operation_key)
    if key in FIXED_KEYS:
        raise ValueError('operation key collides with a fixed advisory key')
    return key


def operation_key(idempotency_key: str) -> str:
    """'idem:<canonical uuid4>'. The phase lives in its own column, so one key conflicts globally."""
    try:
        parsed = uuid.UUID(idempotency_key)
    except (TypeError, ValueError, AttributeError):
        raise ValueError('Idempotency-Key must be a UUID') from None
    if parsed.version != 4 or str(parsed) != idempotency_key:
        raise ValueError('Idempotency-Key must be a canonical UUIDv4')
    return 'idem:' + str(parsed)
