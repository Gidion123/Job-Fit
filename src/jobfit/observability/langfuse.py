"""Metadata-only Langfuse adapter. No application content crosses this boundary."""
from __future__ import annotations

from contextvars import ContextVar
import base64
from functools import partial
import json
import math
import os
import re
import uuid
from types import SimpleNamespace

from jobfit.observability.metrics import CHAINS, ERROR_CODES, KINDS, MODELS, STAGES, bounded

_PARENT = ContextVar('jobfit_langfuse_parent', default=None)
_OUTCOMES = frozenset({'success', 'failure', 'refused', 'held', 'unknown', 'completed', 'failed'})
_SOURCES = frozenset({'reported', 'estimated_from_reported_tokens', 'uncertain_upper_bound', 'rejected_request', 'other'})
_NAMES = frozenset({'jobfit.analysis', 'jobfit.parse', 'jobfit.search', 'llm_attempt'}) | STAGES
_PREFIX = 'langfuse.observation.'


def _number(value, *, integer=False):
    return (type(value) is int if integer else type(value) in (int, float)) and 0 <= value <= 1_000_000_000 and math.isfinite(value)


def _safe_metadata(data):
    if not isinstance(data, dict):
        return False
    rules = {'stage': lambda v: type(v) is str and v in STAGES,
             'outcome': lambda v: type(v) is str and v in _OUTCOMES,
             'error_code': lambda v: type(v) is str and (v in ERROR_CODES or v == 'other'),
             'chain': lambda v: type(v) is str and (v in CHAINS or v == 'other'),
             'kind': lambda v: type(v) is str and (v in KINDS or v == 'other'),
             'cost_source': lambda v: type(v) is str and v in _SOURCES,
             'latency_ms': lambda v: _number(v)}
    return all(key in rules and rules[key](value) for key, value in data.items())


def mask_data(*, data, **_):
    """SDK mask backup: retain only explicitly valid metadata, never input/output."""
    return data if _safe_metadata(data) else None


# The SDK adds a release from deploy variables (GITHUB_SHA, GIT_COMMIT, ...): a short token only.
_DEPLOY_KEYS = ('langfuse.release', 'langfuse.environment')


def _deploy_token(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9._-]{1,64}', value) is not None


def safe_export_span(span, *, public_key=None):
    """Reject any unexpected OpenTelemetry data before Langfuse's exporter sees it."""
    try:
        if (span.name not in _NAMES or span.instrumentation_scope.name != 'langfuse-sdk'
                or span.events or span.links or span.status.description):
            return False
        scope = span.instrumentation_scope
        scope_attrs = dict(scope.attributes or {})
        if set(scope_attrs) - {'public_key'}:
            return False
        if public_key is not None and scope_attrs != {'public_key': public_key}:
            return False
        if public_key is None and scope_attrs and (not isinstance(scope_attrs['public_key'], str)
                                                   or not re.fullmatch(r'pk-lf-[A-Za-z0-9_-]{1,200}',
                                                                       scope_attrs['public_key'])):
            return False
        if scope.schema_url or (scope.version and not re.fullmatch(r'[0-9.]+', scope.version)):
            return False
        allowed_resource = {'telemetry.sdk.language', 'telemetry.sdk.name', 'telemetry.sdk.version',
                            'service.instance.id', 'service.name', *_DEPLOY_KEYS}
        resource = dict(span.resource.attributes)
        if set(resource) - allowed_resource:
            return False
        if not all(_deploy_token(resource[k]) for k in _DEPLOY_KEYS if k in resource):
            return False
        if resource.get('service.name') not in (None, 'jobfit-api', 'unknown_service:python',
                                                'unknown_service:uvicorn'):
            return False
        instance = resource.get('service.instance.id')
        if instance is not None and (not isinstance(instance, str) or
                                     str(uuid.UUID(instance)) != instance):
            return False
        for key in ('telemetry.sdk.language', 'telemetry.sdk.name', 'telemetry.sdk.version'):
            value = resource.get(key)
            if value is not None and (not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9.]+', value)):
                return False
        attrs = dict(span.attributes or {})
        for key, value in attrs.items():
            if key in _DEPLOY_KEYS:
                if not _deploy_token(value):
                    return False
            elif key == 'langfuse.internal.is_app_root':
                if value is not True:
                    return False
            elif key == _PREFIX + 'type':
                if value not in ('span', 'generation'):
                    return False
            elif key == _PREFIX + 'level':
                if value not in ('DEFAULT', 'ERROR'):
                    return False
            elif key == _PREFIX + 'model.name':
                if value not in MODELS and value != 'other':
                    return False
            elif key in (_PREFIX + 'usage_details', _PREFIX + 'cost_details'):
                values = json.loads(value)
                expected = {'input', 'output'} if key.endswith('usage_details') else {'total'}
                if set(values) != expected or not all(_number(v, integer=key.endswith('usage_details'))
                                                       for v in values.values()):
                    return False
            elif key.startswith(_PREFIX + 'metadata.'):
                if not _safe_metadata({key.removeprefix(_PREFIX + 'metadata.'): value}):
                    return False
            else:
                return False
        return True
    except (AttributeError, TypeError, ValueError, KeyError):
        return False


class ScopeScrubbingExporter:
    """Remove the SDK's project key from OTLP scope after local routing."""
    def __init__(self, delegate, public_key):
        self.delegate = delegate
        self.public_key = public_key

    def export(self, spans):
        from opentelemetry.sdk.trace import ReadableSpan
        from opentelemetry.sdk.trace.export import SpanExportResult
        from opentelemetry.sdk.util.instrumentation import InstrumentationScope

        try:
            cleaned = []
            for span in spans:
                if not safe_export_span(span, public_key=self.public_key):
                    return SpanExportResult.SUCCESS  # privacy refusal drops the whole batch
                scope = span.instrumentation_scope
                cleaned.append(ReadableSpan(
                    name=span.name, context=span.context, parent=span.parent, resource=span.resource,
                    attributes=span.attributes, events=span.events, links=span.links, kind=span.kind,
                    status=span.status, start_time=span.start_time, end_time=span.end_time,
                    instrumentation_scope=InstrumentationScope(scope.name, scope.version, scope.schema_url)))
            return self.delegate.export(cleaned)
        except Exception:
            return SpanExportResult.FAILURE

    def shutdown(self):
        try:
            self.delegate.shutdown()
        except Exception:
            pass

    def force_flush(self, timeout_millis=30000):
        try:
            return self.delegate.force_flush(timeout_millis=timeout_millis)
        except Exception:
            return False


class LangfuseTracer:
    def __init__(self, client):
        self.client = client

    def analysis(self, fn, outcome):
        """Start exactly once in the worker, after admission."""
        return self.operation('analysis', fn, outcome)

    def operation(self, phase, fn, outcome):
        """Run one actual AI operation without passing its inputs or result to the SDK."""
        if phase not in {'analysis', 'parse', 'search'}:
            return fn()
        try:
            root = self.client.start_observation(name='jobfit.' + phase, as_type='span')
        except Exception:
            return fn()
        token = _PARENT.set(root)
        status = 'failed'
        try:
            result = fn()
            status = bounded(outcome(), _OUTCOMES)
            return result
        except Exception as exc:
            status = ('refused' if type(exc).__name__ in
                      {'LiveRefused', 'RealCVRefused', 'LiveSafetyRefusal', 'SessionDenied'} else 'failed')
            raise
        finally:
            _PARENT.reset(token)
            try:
                root.update(metadata={'outcome': status}, level='ERROR' if status == 'failed' else 'DEFAULT')
            except Exception:
                pass
            try:
                root.end()
            except Exception:
                pass

    def start_stage(self, stage):
        parent = _PARENT.get()
        if parent is None:
            return None
        child = parent.start_observation(name=bounded(stage, STAGES), as_type='span',
                                         metadata={'stage': bounded(stage, STAGES)})
        return child, _PARENT.set(child)

    def finish_stage(self, handle, status, error_code):
        if handle is None:
            return
        child, token = handle
        _PARENT.reset(token)
        metadata = {'outcome': bounded(status, _OUTCOMES)}
        if error_code is not None:
            metadata['error_code'] = bounded(error_code, ERROR_CODES)
        try:
            child.update(metadata=metadata, level='ERROR' if status == 'failure' else 'DEFAULT')
        finally:
            child.end()

    def attempt(self, record, ctx):
        parent = _PARENT.get()
        if parent is None:
            return
        source = bounded(record.cost_source, _SOURCES)
        metadata = {'chain': bounded(ctx.chain, CHAINS), 'kind': bounded(ctx.attempt_kind, KINDS),
                    'outcome': 'success' if record.ok else 'failure', 'cost_source': source}
        if not record.ok:
            metadata['error_code'] = bounded(getattr(record, 'error_type', None), ERROR_CODES)
        if _number(record.latency_ms):
            metadata['latency_ms'] = record.latency_ms
        kw = {'name': 'llm_attempt', 'as_type': 'generation', 'model': bounded(record.model, MODELS),
              'metadata': metadata, 'level': 'DEFAULT' if record.ok else 'ERROR'}
        if source in {'reported', 'estimated_from_reported_tokens'}:
            if _number(record.input_tokens, integer=True) and _number(record.output_tokens, integer=True):
                kw['usage_details'] = {'input': record.input_tokens, 'output': record.output_tokens}
            if _number(record.cost_usd):
                kw['cost_details'] = {'total': record.cost_usd}
        parent.start_observation(**kw).end()


def build_tracer(environ=None):
    env = os.environ if environ is None else environ
    if env.get('JOBFIT_LANGFUSE_ENABLED') != '1':
        return None
    public, secret = env.get('LANGFUSE_PUBLIC_KEY'), env.get('LANGFUSE_SECRET_KEY')
    if not public or not secret:
        return None
    # A failed privacy self-check blocks enabling tracing, even if the app could run.
    canary = 'PRIVATE_CANARY@example.com'
    probe = SimpleNamespace(name='matching', instrumentation_scope=SimpleNamespace(
        name='langfuse-sdk', attributes={}, version=None, schema_url=''),
                            events=[], links=[], status=SimpleNamespace(description=None),
                            resource=SimpleNamespace(attributes={'service.name': 'jobfit-api'}),
                            attributes={'langfuse.observation.input': canary})
    if (_safe_metadata({'stage': canary}) or mask_data(data=canary) is not None
            or safe_export_span(probe)):
        raise RuntimeError('Langfuse privacy validation failed')
    try:
        from langfuse import Langfuse
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        auth = base64.b64encode(f'{public}:{secret}'.encode('utf-8')).decode('ascii')
        exporter = ScopeScrubbingExporter(OTLPSpanExporter(
            endpoint='https://jp.cloud.langfuse.com/api/public/otel/v1/traces',
            headers={'Authorization': 'Basic ' + auth, 'x-langfuse-public-key': public}), public)
        return LangfuseTracer(Langfuse(public_key=public, secret_key=secret,
                                       base_url='https://jp.cloud.langfuse.com', span_exporter=exporter,
                                       mask=mask_data, should_export_span=partial(safe_export_span, public_key=public)))
    except Exception:
        return None  # operational SDK failure disables tracing, without exposing its exception
