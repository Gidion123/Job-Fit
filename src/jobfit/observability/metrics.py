"""One registry per application process. No candidate identifiers or payloads."""
from __future__ import annotations

import time
import logging
from prometheus_client import CollectorRegistry, Counter, Histogram, ProcessCollector, generate_latest

STAGES = frozenset({'cv_parse', 'query_embedding', 'retrieval', 'extraction', 'matching',
                    'parse', 'search', 'job_analysis', 'recommendation', 'overall_analysis'})
MODELS = frozenset({'deepseek-flash', 'gpt-6-sol', 'gpt-6-luna', 'qwen3-embedding-8b',
                    'deepseek/deepseek-v4.1-flash', 'openai/gpt-6-sol', 'openai/gpt-6-luna',
                    'qwen/qwen3-embedding-8b'})
KINDS = frozenset({'initial', 'validation_repair', 'length_continuation', 'embedding'})
CHAINS = frozenset({'parse', 'extraction', 'matching', 'fallback', 'embed'})
ERROR_CODES = frozenset({'budget', 'lifetime', 'ledger_storage_unavailable',
                         'ledger_storage_mismatch', 'evidence_fail_closed',
                         'busy', 'unavailable', 'admission_disabled',
                         'admission_outcome_unknown', 'phase_not_admitted',
                         'call_wall_exceeded', 'coordinator_lost'})
BUCKETS = (.005, .025, .1, .25, .5, 1, 2.5, 5, 10, 30, 60, 120, 240, 600, 1200)


def bounded(value, allowed):
    return value if isinstance(value, str) and value in allowed else 'other'


def safely(fn, *args, **kwargs):
    """Observational failure must never change the application result or exception."""
    try:
        return fn(*args, **kwargs)
    except Exception:
        return None


def outcome(result):
    if getattr(result, 'hold_reason', None):
        return 'held'
    status = getattr(result, 'status', None)
    if status is not None and status not in ('done', 'ok', 'success'):
        return 'failure'
    score = getattr(result, 'score', None)
    if getattr(getattr(score, 'status', None), 'value', None) == 'on_hold':
        return 'held'
    return 'success'


def observed(telemetry, stage, fn, *args, classify_result=None, **kwargs):
    """Time the existing boundary; no retries, inputs, or results changed."""
    started = time.monotonic()
    status, error_code = 'failure', None
    trace_handle = safely(telemetry.trace_stage_start, stage) if telemetry is not None else None
    try:
        result = fn(*args, **kwargs)
        classifier = classify_result or outcome
        status = safely(classifier, result[0] if isinstance(result, tuple) else result) or 'unknown'
        return result
    except Exception as exc:
        # The exception class is inspected, never rendered in logs or labels.
        if type(exc).__name__ in {'LiveRefused', 'RealCVRefused', 'LiveSafetyRefusal', 'SessionDenied'}:
            status = 'refused'
        code = getattr(exc, 'code', None)
        error_code = bounded(code, ERROR_CODES) if code is not None else None
        if telemetry is not None and isinstance(code, str) and code in {'budget', 'lifetime'}:
            safely(telemetry.budget_refusal, code)
        raise
    finally:
        if telemetry is not None:
            safely(telemetry.trace_stage_finish, trace_handle, status, error_code)
            safely(telemetry.stage, stage, status, time.monotonic() - started, error_code)


class Telemetry:
    def __init__(self, tracer=None):
        self.tracer = tracer
        self.registry = CollectorRegistry()
        ProcessCollector(registry=self.registry)  # native Linux process start, memory and CPU
        kw = {'registry': self.registry}
        self.http = Counter('jobfit_http_requests_total', 'Completed HTTP requests', ['method', 'route', 'status'], **kw)
        self.http_time = Histogram('jobfit_http_duration_seconds', 'HTTP wall time, including response send',
                                   ['method', 'route'], buckets=BUCKETS, **kw)
        self.stages = Counter('jobfit_stage_executions_total', 'Executed boundaries, not cache hits',
                              ['stage', 'outcome'], **kw)
        self.stage_time = Histogram('jobfit_stage_duration_seconds', 'Boundary wall time; nested, do not sum',
                                    ['stage', 'outcome'], buckets=BUCKETS, **kw)
        self.calls = Counter('jobfit_llm_attempts_total', 'Durably ledgered attempts, including failures',
                             ['model', 'chain', 'kind', 'outcome'], **kw)
        self.call_time = Histogram('jobfit_llm_duration_seconds', 'Ledger attempt latency when known',
                                   ['model', 'chain'], buckets=BUCKETS, **kw)
        self.tokens = Counter('jobfit_llm_tokens_total', 'Tokens with known usage only', ['model', 'direction'], **kw)
        self.usage = Counter('jobfit_llm_usage_observations_total', 'Attempts with known token usage', ['model'], **kw)
        self.cost = Counter('jobfit_llm_accounted_cost_usd_total', 'Process observations, NOT a budget balance',
                            ['model', 'source'], **kw)
        self.estimate = Counter('jobfit_llm_upper_bound_usd_total', 'Sum of per-attempt reservation estimates',
                                ['model'], **kw)
        self.fallback = Counter('jobfit_llm_fallbacks_total', 'Ledgered initial fallback attempts', ['model'], **kw)
        self.analysis_requests = Counter('jobfit_analysis_requests_total', 'HTTP analysis responses, not completion',
                                         ['outcome'], **kw)
        self.analysis_outcomes = Counter('jobfit_analysis_outcomes_total', 'Finished asynchronous analyses',
                                         ['outcome'], **kw)
        self.rejections = Counter('jobfit_budget_rejections_total', 'Runtime budget refusals', ['reason'], **kw)

    def request(self, method, route, status, duration, duplicate=False):
        self.http.labels(method, route, str(status)).inc()
        self.http_time.labels(method, route).observe(duration)
        if method == 'POST' and route in {'/analyze', '/jobs/{job_id}/analyze'}:
            self.analysis_requests.labels('duplicate' if status < 400 and duplicate else 'accepted' if status < 400 else
                                          'refused' if status < 500 or status == 503 else 'failure').inc()

    def analysis_finished(self, status, request_id=None):
        label = bounded(status, {'completed', 'held', 'failed', 'refused', 'unknown'})
        self.analysis_outcomes.labels(label).inc()
        fields = {'_jobfit_analysis': True, 'safe_outcome': label}
        if isinstance(request_id, str) and len(request_id) == 32 and all(c in '0123456789abcdef' for c in request_id):
            fields['safe_request_id'] = request_id
        safely(logging.getLogger('jobfit.analysis').info, 'analysis_finished', extra=fields)

    def render(self):
        return generate_latest(self.registry)

    def trace_analysis(self, fn, outcome):
        return self.tracer.analysis(fn, outcome) if self.tracer is not None else fn()

    def trace_operation(self, phase, fn):
        return self.tracer.operation(phase, fn, lambda: 'success') if self.tracer is not None else fn()

    def trace_stage_start(self, stage):
        return self.tracer.start_stage(stage) if self.tracer is not None else None

    def trace_stage_finish(self, handle, status, error_code):
        if self.tracer is not None:
            self.tracer.finish_stage(handle, status, error_code)

    def stage(self, stage, status, duration, error_code=None):
        labels = (bounded(stage, STAGES), bounded(status, {'success', 'failure', 'refused', 'held', 'discarded', 'unknown'}))
        self.stages.labels(*labels).inc()
        self.stage_time.labels(*labels).observe(max(0, duration))
        fields = {'_jobfit_stage': True, 'safe_stage': labels[0], 'safe_outcome': labels[1],
                  'safe_duration_ms': round(max(0, duration) * 1000, 3)}
        if error_code is not None:
            fields['safe_error_code'] = bounded(error_code, ERROR_CODES)
        safely(logging.getLogger('jobfit.stage').info, 'stage_completed', extra=fields)

    def budget_refusal(self, reason):
        self.rejections.labels(bounded(reason, {'budget', 'lifetime'})).inc()

    def attempt(self, record, ctx):
        if self.tracer is not None:
            safely(self.tracer.attempt, record, ctx)
        model = bounded(record.model, MODELS)
        chain, kind = bounded(ctx.chain, CHAINS), bounded(ctx.attempt_kind, KINDS)
        self.calls.labels(model, chain, kind, 'success' if record.ok else 'failure').inc()
        if record.latency_ms is not None:
            self.call_time.labels(model, chain).observe(max(0, record.latency_ms / 1000))
        if chain == 'fallback' and kind == 'initial':
            self.fallback.labels(model).inc()
        source = bounded(record.cost_source, {'reported', 'estimated_from_reported_tokens',
                                               'uncertain_upper_bound', 'rejected_request'})
        self.cost.labels(model, source).inc(record.cost_usd)
        self.estimate.labels(model).inc(float(ctx.upper_cost))
        if source in {'reported', 'estimated_from_reported_tokens'}:
            self.tokens.labels(model, 'input').inc(record.input_tokens)
            self.tokens.labels(model, 'output').inc(record.output_tokens)
            self.usage.labels(model).inc()
