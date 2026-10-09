"""Correlated production ledger, durable call intents, breach marker and per-attempt settlement.

Evidence rules (D-101):
- no provider call without a durable intent (written by the reservation guard before the SDK call);
- every production ledger line carries ``operation_key`` and ``attempt_id`` (extra keys the frozen
  UsageRecord ignores), so a line correlates to exactly one intent;
- a ledger line wins over its intent (no double counting); an intent with no line is charged at
  its upper bound and is uncertain; a duplicate line, a line without an intent, an unattributed
  line, a torn or corrupt line fail closed (no settlement, no admission) for manual review;
- a reported cost above the intent's upper bound is never clamped: it is kept, settled at full
  value, and a durable breach marker blocks admission until manual review.
The ledger is never edited automatically.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from jobfit.live.common import (CURRENT_ATTEMPT, AttemptContext, EvidenceError, FileLock, LiveSafetyRefusal,
                                append_durable, usd_up)
from jobfit.llm.ledger import UsageLedger, UsageRecord

INTENT_KEYS = ('operation_key', 'attempt_id', 'phase', 'task', 'model', 'attempt_kind', 'chain', 'upper_cost')


def journal_path(ledger_path: Path) -> Path:
    return Path(ledger_path).with_name(Path(ledger_path).name + '.intents.jsonl')


def breach_path(ledger_path: Path) -> Path:
    return Path(ledger_path).with_name(Path(ledger_path).name + '.breach.jsonl')


def _lock_for(path: Path) -> FileLock:
    return FileLock.for_path(Path(path).with_name(Path(path).name + '.lock'))


def _read_lines(path: Path) -> list[dict]:
    """Strict JSONL read: a torn final line or any unparsable line is corrupt evidence."""
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        raise EvidenceError(f'{path.name} is unreadable') from None
    if text and not text.endswith('\n'):
        raise EvidenceError(f'{path.name} ends with a torn line')
    out = []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            raise EvidenceError(f'{path.name} has a corrupt line') from None
        if not isinstance(row, dict):
            raise EvidenceError(f'{path.name} has a non-object line')
        out.append(row)
    return out


class IntentJournal:
    """Durable call intents and 'done' hints; own thread lock plus flock, fsync per line."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.lock = _lock_for(self.path)

    def _append(self, row: dict) -> None:
        with self.lock.hold(exclusive=True):
            append_durable(self.path, json.dumps(row, ensure_ascii=False))

    def append_intent(self, ctx: AttemptContext) -> None:
        self._append({'type': 'intent', 'operation_key': ctx.operation_key, 'attempt_id': ctx.attempt_id,
                      'phase': ctx.phase, 'task': ctx.task, 'model': ctx.model, 'attempt_kind': ctx.attempt_kind,
                      'chain': ctx.chain, 'upper_cost': str(ctx.upper_cost)})

    def append_done(self, ctx: AttemptContext) -> None:
        self._append({'type': 'done', 'operation_key': ctx.operation_key, 'attempt_id': ctx.attempt_id})

    def read(self) -> list[dict]:
        with self.lock.hold(exclusive=False):
            return _read_lines(self.path)


class CorrelatedLedger(UsageLedger):
    """The frozen ledger format plus operation_key/attempt_id, with short synchronized file I/O.

    append: thread lock + exclusive flock around the write only, then fsync, then the 'done' hint;
    the attempt is always closed in ``finally`` (exactly once, via the owner's idempotent close).
    records/total_spent: thread lock + shared flock, strict parsing (a partial line never parses).
    """

    def __init__(self, path: Path, journal: IntentJournal):
        super().__init__(path)
        self.io = FileLock.for_path(self.path.with_name(self.path.name + '.io.lock'))
        self.journal = journal

    def append(self, record: UsageRecord) -> None:
        ctx = CURRENT_ATTEMPT.get()
        try:
            if ctx is None or ctx.owner is None:
                raise LiveSafetyRefusal('no_attempt_context')
            try:
                row = json.loads(record.model_dump_json())
                row.update(operation_key=ctx.operation_key, attempt_id=ctx.attempt_id)
                with self.io.hold(exclusive=True):
                    append_durable(self.path, json.dumps(row, ensure_ascii=False))
            except Exception:
                ctx.owner.set_fatal('ledger_write_failed')
                raise LiveSafetyRefusal('ledger_write_failed') from None
            try:
                self.journal.append_done(ctx)       # only after the ledger line is durable
            except Exception:
                pass    # 'done' is an in-flight hint only; the durable ledger line is authoritative
        finally:
            if ctx is not None and ctx.owner is not None:
                ctx.owner.close_attempt(ctx)

    def raw_lines(self) -> list[dict]:
        with self.io.hold(exclusive=False):
            return _read_lines(self.path)

    def records(self) -> list[UsageRecord]:
        return [UsageRecord.model_validate(row) for row in self.raw_lines()]


class BreachMarker:
    """Durable manual-review marker on the ledger volume. Present (or unreadable) blocks admission."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.lock = _lock_for(self.path)

    def write(self, reason: str, operation_key: str | None = None, attempt_id: str | None = None,
              detail: str | None = None) -> None:
        row = {'ts': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'reason': reason,
               'operation_key': operation_key, 'attempt_id': attempt_id, 'detail': detail}
        with self.lock.hold(exclusive=True):
            append_durable(self.path, json.dumps(row))

    def present(self) -> bool:
        try:
            return self.path.exists() and self.path.stat().st_size > 0
        except OSError:
            return True


@dataclass
class OperationEvidence:
    operation_key: str
    spend: Decimal = Decimal(0)
    uncertain: bool = False
    complete: bool = True            # every intent has its correlated ledger line
    attempts: int = 0
    breaches: list = field(default_factory=list)    # (attempt_id, reported, upper)

    def settlement(self) -> Decimal | None:
        """None = release (proven zero spend, nothing uncertain, every intent ledgered); else settle."""
        if self.spend == 0 and not self.uncertain and self.complete:
            return None
        return self.spend


def _index(intent_rows: list[dict], ledger_rows: list[dict]):
    intents: dict[str, dict] = {}
    for row in intent_rows:
        if row.get('type') == 'done':
            continue
        if row.get('type') != 'intent' or any(not isinstance(row.get(k), str) for k in INTENT_KEYS):
            raise EvidenceError('malformed intent')
        if row['attempt_id'] in intents:
            raise EvidenceError('duplicate intent')
        usd_up(row['upper_cost'])
        intents[row['attempt_id']] = row
    lines: dict[str, dict] = {}
    for row in ledger_rows:
        op, attempt = row.get('operation_key'), row.get('attempt_id')
        if not isinstance(op, str) or not isinstance(attempt, str):
            raise EvidenceError('unattributed production ledger line')
        if attempt in lines:
            raise EvidenceError('duplicate ledger line for one attempt')
        intent = intents.get(attempt)
        if intent is None or intent['operation_key'] != op:
            raise EvidenceError('ledger line without a matching intent')
        lines[attempt] = row
    return intents, lines


def _snapshot(journal: IntentJournal, ledger: CorrelatedLedger):
    """Ledger first, then the journal: every line's intent was durable before its SDK call, so it is
    in the later journal read; an intent newer than the ledger read only counts as unledgered (more)."""
    ledger_rows = ledger.raw_lines()
    return _index(journal.read(), ledger_rows)


def _line_cost(row: dict) -> Decimal:
    return usd_up(row.get('cost_usd', 0))


def operation_evidence(operation_key: str, journal: IntentJournal, ledger: CorrelatedLedger) -> OperationEvidence:
    """Per-attempt evidence of one operation (raises EvidenceError when it cannot be trusted)."""
    intents, lines = _snapshot(journal, ledger)
    ev = OperationEvidence(operation_key)
    for attempt, intent in intents.items():
        if intent['operation_key'] != operation_key:
            continue
        ev.attempts += 1
        upper = usd_up(intent['upper_cost'])
        line = lines.get(attempt)
        if line is None:
            ev.spend += upper
            ev.uncertain = True
            ev.complete = False
            continue
        cost = _line_cost(line)
        ev.spend += cost
        if line.get('cost_source') == 'uncertain_upper_bound':
            ev.uncertain = True
        if cost > upper:
            ev.breaches.append((attempt, cost, upper))
    return ev


def recorded_spend(journal: IntentJournal, ledger: CorrelatedLedger, breach: BreachMarker) -> Decimal:
    """Lifetime recorded spend: every ledger line, plus every intent with no ledger line at its upper bound.

    Open reservations are added separately by the admission (their full reserved amount).
    """
    if breach.present():
        raise EvidenceError('breach marker present: manual review required')
    intents, lines = _snapshot(journal, ledger)
    total = sum((_line_cost(row) for row in lines.values()), Decimal(0))
    total += sum((usd_up(i['upper_cost']) for a, i in intents.items() if a not in lines), Decimal(0))
    return total
