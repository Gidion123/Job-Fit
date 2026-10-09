"""Reserved, concurrency-safe client around the frozen RuntimeClient (D-097 adapter 1, FAIL-36, D-101).

Nothing frozen is edited or patched globally. One frozen RuntimeClient is built per operation and
only that instance's ``guard`` and ``ledger`` attributes are replaced:

- ``ReservedClient.chat_structured/embed`` check the sticky fatal state, classify the call against
  the accepted Phase 2A model, check the operation horizon, set a call-scoped AttemptContext and
  call the frozen ``_chat_attempt``/``_embed_attempt`` directly, without the frozen whole-call
  ``ledger.exclusive()`` lock (so matching calls run concurrently);
- the frozen attempt calls ``guard.check(upper)`` immediately before the SDK. ``ReservationGuard``
  runs the frozen lifetime guard (normalized: no ValueError ever reaches validated_call), reserves
  the upper cost inside the admitted reservation, resolves the ticket at the first billable call,
  writes the durable intent, finalizes the allowance at the first intent, checks that the current
  ledger storage is still the admitted one (every attempt), and only then marks the attempt in flight;
- the frozen attempt appends its record in ``finally``; ``CorrelatedLedger`` writes it with the
  attempt id and closes the attempt exactly once.

Every Phase 2B refusal is a LiveSafetyRefusal (RuntimeError) and sets the operation's sticky
``fatal_refusal`` first: the frozen validated_call turns it into StageFailure with no repair, and
any later call of the operation (a frozen Luna fallback included) is refused before the SDK.
"""
from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import yaml

from jobfit.live.common import CURRENT_ATTEMPT, AttemptContext, LiveSafetyRefusal, usd_up
from jobfit.live.deadlines import PhaseWindow
from jobfit.live.evidence import CorrelatedLedger, IntentJournal, journal_path
from jobfit.llm.budget import BudgetExceeded, BudgetGuard
from jobfit.llm.phase_bounds import DEFAULT_CONFIG, EMBED_OVERHEAD_BYTES, MODELS_FILE, guard_input_bytes

CHAIN_PHASE = {'parse': 'parse', 'extraction': 'recommendation', 'matching': 'recommendation',
               'fallback': 'recommendation', 'embed': 'recommendation'}
# D-103 controlled public beta: the same accepted chains, admitted under the beta phases only (the
# legacy 10-job 'recommendation' phase is never admitted by a beta runtime).
BETA_CHAIN_PHASE = {'parse': 'parse', 'extraction': 'job_analysis', 'matching': 'job_analysis',
                    'fallback': 'job_analysis', 'embed': 'search'}
TASK_SUFFIXES = (('_validation_repair', 'validation_repair'), ('_length_continuation', 'length_continuation'))
QUOTA_FATAL = {'refused': 'quota_refused', 'unavailable': 'quota_unavailable', 'unknown': 'quota_outcome_unknown'}
STORAGE_FATAL = ('ledger_storage_mismatch', 'ledger_storage_unavailable')


class OperationState:
    """Admitted state of one billable phase operation, shared by its worker threads (no DB access)."""

    def __init__(self, operation_key: str, phase: str, reserved_usd: Decimal, window: PhaseWindow, *,
                 anchor_mono: float, quota: Callable[[], str] | None = None,
                 on_first_intent: Callable[[], bool] | None = None,
                 storage_check: Callable[[], str | None] | None = None, clock=time.monotonic):
        self.operation_key, self.phase, self.reserved_usd, self.window = operation_key, phase, reserved_usd, window
        self.anchor_mono, self.clock = anchor_mono, clock
        self.lock = threading.Lock()
        self.drained = threading.Condition(self.lock)
        self.quota_lock = threading.Lock()
        self.quota, self.quota_done = quota, quota is None
        self.fatal_refusal: str | None = None
        self.committed_upper = Decimal(0)
        self.inflight: dict[str, tuple[float, float]] = {}
        self.admitted, self.closing = True, False
        self.embed_calls = 0
        # Safety-critical, exactly once: finalizes the session allowance at the first durable intent.
        self.on_first_intent = on_first_intent
        self.first_intent_lock = threading.Lock()
        self.first_intent_callback_attempted = False
        # Storage continuity (persistent ledger C11): checked after every durable intent, before the SDK.
        # The flag is independent of the first-fatal slot; once set, this operation is never settled
        # or released in this process.
        self.storage_check = storage_check
        self.storage_continuity_failed = False

    # --- fatal state ---------------------------------------------------------------------------
    def set_fatal(self, reason: str) -> None:
        with self.lock:
            if self.fatal_refusal is None:
                self.fatal_refusal = reason

    def fatal(self, reason: str):
        self.set_fatal(reason)
        raise LiveSafetyRefusal(self.fatal_refusal)

    def fail_storage(self, reason: str) -> None:
        """Record a storage-continuity failure: one acquisition of ``lock``, inline first-fatal-wins.

        Never calls set_fatal() (the lock is not reentrant), takes no other lock, calls nothing.
        """
        with self.lock:
            self.storage_continuity_failed = True
            if self.fatal_refusal is None:
                self.fatal_refusal = reason

    def check_fatal(self) -> None:
        if self.fatal_refusal is not None:
            raise LiveSafetyRefusal(self.fatal_refusal)

    # --- admission-time limits --------------------------------------------------------------------
    def check_horizon(self, wall: float) -> None:
        """A call may start only if it fits before the horizon: elapsed + W(call) <= T_op."""
        if self.clock() - self.anchor_mono + wall > self.window.horizon:
            self.fatal('deadline_exceeded')

    def reserve(self, upper: Decimal) -> None:
        with self.lock:
            if self.fatal_refusal is not None:
                reason = self.fatal_refusal
            elif not self.admitted or self.closing:
                reason = self.fatal_refusal = 'reservation_inactive'
            elif self.committed_upper + upper > self.reserved_usd:
                reason = self.fatal_refusal = 'reservation_exhausted'
            else:
                self.committed_upper += upper     # never given back: a later failure is fatal anyway
                return
        raise LiveSafetyRefusal(reason)

    def resolve_quota(self) -> None:
        """The ticket at the first billable call: consumed once, never repeated in this operation."""
        with self.quota_lock:
            if not self.quota_done:
                try:
                    outcome = self.quota()
                except Exception:
                    outcome = 'unknown'
                self.quota_done = True
                if outcome != 'consumed':
                    self.fatal(QUOTA_FATAL.get(outcome, 'quota_outcome_unknown'))
        self.check_fatal()

    # --- in-flight accounting -------------------------------------------------------------------
    def open_attempt(self, ctx: AttemptContext) -> None:
        with self.lock:
            self.inflight[ctx.attempt_id] = (self.clock(), ctx.wall_seconds)
            ctx.inflight_open = True

    def close_attempt(self, ctx: AttemptContext) -> None:
        with self.lock:
            if ctx.inflight_open:
                ctx.inflight_open = False
                self.inflight.pop(ctx.attempt_id, None)
                self.drained.notify_all()

    def wait_drained(self, timeout: float) -> bool:
        with self.lock:
            return self.drained.wait_for(lambda: not self.inflight, timeout=timeout)

    def overdue(self) -> list[str]:
        now = self.clock()
        with self.lock:
            return [a for a, (start, wall) in self.inflight.items() if now - start > wall]


def _kind_fits(kind: str, a) -> bool:
    if kind == 'initial':
        return a.continuations == 0 and a.repairs == 0
    if kind == 'validation_repair':
        return a.repairs >= 1
    if kind == 'length_continuation':
        return a.continuations >= 1
    return False


class CallModel:
    """Classifies a call against the accepted Phase 2A chains and checks it fits a modelled attempt."""

    def __init__(self, bounds, pipeline_config: Path, *, phase_config: Path = DEFAULT_CONFIG,
                 models_file: Path = MODELS_FILE, chain_phase: dict[str, str] = CHAIN_PHASE):
        cfg = yaml.safe_load(Path(pipeline_config).read_text())
        pcfg = yaml.safe_load(Path(phase_config).read_text())
        registry = yaml.safe_load(Path(models_file).read_text())
        ch = self.chains = bounds.chains
        self.models = {'parse': {pcfg['parse_model'], ch['parse'].price.model_id},
                       'extraction': {cfg['extraction_model'], ch['extraction'].price.model_id},
                       'matching': {cfg['matching_model'], ch['matching'].price.model_id},
                       'fallback': {cfg['matching_fallback_model'], ch['fallback'].price.model_id}}
        emb = cfg['embedding_model']
        self.embed_models = {emb, registry['embeddings'][emb]['id']}
        if 'embed_max_bytes' in bounds.details:          # D-103: the exact canonical-byte envelope
            self.embed_max_tokens = int(bounds.details['embed_max_bytes'])
        else:
            self.embed_max_tokens = 4 * int(bounds.details['cv_max_chars']) + EMBED_OVERHEAD_BYTES
        self.chain_phase = dict(chain_phase)

    def classify(self, model: str, task: str) -> tuple[str, str] | None:
        base, kind = task, 'initial'
        for suffix, name in TASK_SUFFIXES:
            if task.endswith(suffix):
                base, kind = task[:-len(suffix)], name
        if base == 'cv_parsing' and model in self.models['parse']:
            return 'parse', kind
        if base == 'jd_extraction' and model in self.models['extraction']:
            return 'extraction', kind
        if base == 'evidence_matching':
            if model in self.models['matching']:
                return 'matching', kind
            if model in self.models['fallback']:
                return 'fallback', kind
        return None

    def chat_fits(self, chain: str, kind: str, messages, output_model, max_tokens) -> bool:
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens < 1:
            return False
        try:
            size = guard_input_bytes(messages, output_model)
        except Exception:
            return False
        return any(_kind_fits(kind, a) and max_tokens <= a.max_tokens and size <= region.attempt_input_bytes(a)
                   for region in self.chains[chain].regions.values()
                   for seq in region.sequences.values() for a in seq)

    def embed_fits(self, model: str, texts: list[str]) -> bool:
        return model in self.embed_models and sum(len(t.encode('utf-8')) + 100 for t in texts) <= self.embed_max_tokens


class ReservationGuard:
    """Replaces one frozen client's guard; runs right before the SDK call inside the frozen attempt."""

    def __init__(self, lifetime: BudgetGuard, op: OperationState, journal: IntentJournal):
        self.lifetime, self.op, self.journal = lifetime, op, journal

    def check(self, estimated_cost_usd) -> None:
        op = self.op
        op.check_fatal()
        ctx = CURRENT_ATTEMPT.get()
        if ctx is None or ctx.owner is not op:
            op.fatal('no_attempt_context')
        try:
            self.lifetime.check(estimated_cost_usd)
        except BudgetExceeded:
            op.fatal('lifetime_refused')
        except Exception:      # ValueError (invalid values, corrupt ledger), EvidenceError, OSError
            op.fatal('evidence_fail_closed')
        try:
            upper = usd_up(estimated_cost_usd)
        except Exception:
            op.fatal('evidence_fail_closed')
        op.reserve(upper)
        op.resolve_quota()
        ctx.upper_cost = upper
        try:
            self.journal.append_intent(ctx)
        except Exception:
            op.fatal('intent_write_failed')
        with op.first_intent_lock:
            if op.on_first_intent is not None and not op.first_intent_callback_attempted:
                op.first_intent_callback_attempted = True      # set before the callback: exactly once
                try:
                    ok = op.on_first_intent() is True
                except Exception:
                    ok = False
                if not ok:
                    op.set_fatal('allowance_finalize_failed')    # sticky; seen by every waiter below
        if op.storage_check is not None:      # every attempt: the CURRENT storage is still the admitted one
            try:
                reason = op.storage_check()
            except Exception:
                reason = 'ledger_storage_unavailable'
            if reason is not None:
                if reason not in STORAGE_FATAL:
                    reason = 'ledger_storage_unavailable'
                op.fail_storage(reason)
        op.check_fatal()
        op.open_attempt(ctx)       # in flight only once the intent is durable (and the allowance final)


class ReservedClient:
    """The client handed to the frozen pipeline (``client=``); exposes only chat_structured and embed."""

    def __init__(self, inner, op: OperationState, call_model: CallModel):
        self._inner, self._op, self._model = inner, op, call_model

    def _attempt(self, model, task, kind, chain, wall) -> AttemptContext:
        return AttemptContext(self._op.operation_key, uuid.uuid4().hex, self._op.phase, task, model, kind, chain,
                              wall, owner=self._op)

    def _run(self, ctx: AttemptContext, call):
        token = CURRENT_ATTEMPT.set(ctx)
        try:
            return call()
        finally:
            self._op.close_attempt(ctx)       # covers a frozen raise between guard.check and its try
            CURRENT_ATTEMPT.reset(token)

    def chat_structured(self, model: str, messages: list[dict], output_model, task: str,
                        max_tokens: int = 2000, temperature: float = 0.0):
        op = self._op
        op.check_fatal()
        found = self._model.classify(model, task)
        if found is None:
            op.fatal('call_outside_model')
        chain, kind = found
        if self._model.chain_phase[chain] != op.phase:
            op.fatal('phase_mismatch')
        if not self._model.chat_fits(chain, kind, messages, output_model, max_tokens):
            op.fatal('call_outside_model')
        wall = op.window.wall('chat')
        op.check_horizon(wall)
        ctx = self._attempt(model, task, kind, chain, wall)
        return self._run(ctx, lambda: self._inner._chat_attempt(model, messages, output_model, task,
                                                                 max_tokens, temperature))

    def embed(self, texts: list[str], model: str = 'text-embedding-3-small', task: str = 'embedding', *,
              dimensions: int) -> list[list[float]]:
        op = self._op
        op.check_fatal()
        if not texts or any(not isinstance(t, str) or not t.strip() for t in texts):
            raise ValueError('embedding inputs must be non-empty strings')      # same as the frozen embed()
        if dimensions < 1:
            raise ValueError('dimensions must be positive')
        if self._model.chain_phase['embed'] != op.phase:
            op.fatal('phase_mismatch')
        with op.lock:
            op.embed_calls += 1
            extra = op.embed_calls > 1
        if extra or not self._model.embed_fits(model, texts):
            op.fatal('call_outside_model')
        wall = op.window.wall('embed')
        op.check_horizon(wall)
        ctx = self._attempt(model, task, 'embedding', 'embed', wall)
        return self._run(ctx, lambda: self._inner._embed_attempt(texts, model, task, dimensions))


def bind_reserved_client(inner, op: OperationState, call_model: CallModel, ledger_path: Path) -> ReservedClient:
    """Rebind ONE frozen client instance: the synchronized correlated ledger and the reservation guard.

    The frozen lifetime BudgetGuard is rebuilt over the correlated ledger, so its total_spent()
    reads through the same synchronized I/O as the appends.
    """
    journal = IntentJournal(journal_path(ledger_path))
    ledger = CorrelatedLedger(Path(ledger_path), journal)
    inner.ledger = ledger
    inner.guard = ReservationGuard(BudgetGuard(ledger, inner.settings.api_budget_usd,
                                               inner.settings.api_hard_stop_usd), op, journal)
    return ReservedClient(inner, op, call_model)
