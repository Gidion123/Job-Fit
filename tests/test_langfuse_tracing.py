"""Synthetic, offline tests of the optional metadata-only tracing boundary."""
import json
from types import SimpleNamespace

import pytest

from jobfit.observability.langfuse import (LangfuseTracer, ScopeScrubbingExporter, build_tracer, mask_data,
                                          safe_export_span)
from jobfit.observability.metrics import Telemetry, observed

CANARY = 'PRIVATE_CV@example.com Date of Birth 01 January 1990'


class FakeSpan:
    def __init__(self, name, sink, **kwargs):
        self.name, self.sink, self.kwargs = name, sink, kwargs
        self.children = []
        sink.append(self)

    def start_observation(self, *, name, **kwargs):
        child = FakeSpan(name, self.sink, **kwargs)
        self.children.append(child)
        return child

    def update(self, **kwargs):
        self.kwargs.update(kwargs)
        return self

    def end(self):
        return self


class FakeClient:
    def __init__(self):
        self.spans = []

    def start_observation(self, *, name, **kwargs):
        return FakeSpan(name, self.spans, **kwargs)


def test_disabled_by_default_and_missing_credentials(monkeypatch):
    monkeypatch.delenv('JOBFIT_LANGFUSE_ENABLED', raising=False)
    assert build_tracer({'LANGFUSE_PUBLIC_KEY': 'synthetic', 'LANGFUSE_SECRET_KEY': 'synthetic'}) is None
    assert build_tracer({'JOBFIT_LANGFUSE_ENABLED': '1'}) is None


def test_one_trace_per_execution_and_real_stage_outcome():
    client = FakeClient()
    telemetry = Telemetry(LangfuseTracer(client))
    result = object()
    assert telemetry.trace_analysis(lambda: observed(telemetry, 'overall_analysis',
                                                      lambda: observed(telemetry, 'matching', lambda: result)),
                                    lambda: 'completed') is result
    assert [s.name for s in client.spans] == ['jobfit.analysis', 'overall_analysis', 'matching']
    assert client.spans[0].kwargs['metadata'] == {'outcome': 'completed'}
    assert client.spans[-1].kwargs['metadata'] == {'outcome': 'success'}
    assert all('input' not in s.kwargs and 'output' not in s.kwargs for s in client.spans)
    assert telemetry.registry.get_sample_value('jobfit_stage_executions_total',
                                                {'stage': 'matching', 'outcome': 'success'}) == 1


def test_exception_category_only_and_provider_outage_isolated():
    client = FakeClient()
    tracer = LangfuseTracer(client)
    error = ValueError(CANARY)

    def fail():
        raise error

    with pytest.raises(ValueError) as caught:
        tracer.analysis(fail, lambda: 'completed')
    assert caught.value is error
    assert client.spans[0].kwargs['metadata'] == {'outcome': 'failed'}
    assert CANARY not in str(client.spans[0].kwargs)

    class BrokenClient:
        def start_observation(self, **_):
            raise RuntimeError(CANARY)

    assert LangfuseTracer(BrokenClient()).analysis(lambda: 42, lambda: 'completed') == 42
    telemetry = Telemetry(LangfuseTracer(client))
    client.start_observation = BrokenClient().start_observation
    assert telemetry.trace_analysis(lambda: observed(telemetry, 'matching', lambda: 43),
                                    lambda: 'completed') == 43


def test_ledgered_attempt_has_only_known_tokens_cost_and_bounded_labels():
    client = FakeClient()
    telemetry = Telemetry(LangfuseTracer(client))
    record = SimpleNamespace(model='gpt-6-sol', ok=True, latency_ms=19,
                             cost_source='estimated_from_reported_tokens', cost_usd=.012,
                             input_tokens=123, output_tokens=45)
    ctx = SimpleNamespace(chain='matching', attempt_kind='validation_repair', upper_cost=.5)
    telemetry.trace_analysis(lambda: telemetry.attempt(record, ctx), lambda: 'completed')
    generation = client.spans[1]
    assert generation.name == 'llm_attempt'
    assert generation.kwargs['model'] == 'gpt-6-sol'
    assert generation.kwargs['usage_details'] == {'input': 123, 'output': 45}
    assert generation.kwargs['cost_details'] == {'total': .012}
    assert generation.kwargs['metadata']['cost_source'] == 'estimated_from_reported_tokens'
    assert client.spans[0].kwargs['metadata'] == {'outcome': 'completed'}
    record.cost_source, record.model = 'uncertain_upper_bound', CANARY
    telemetry.trace_analysis(lambda: telemetry.attempt(record, ctx), lambda: 'completed')
    uncertain = client.spans[-1]
    assert uncertain.kwargs['model'] == 'other'
    assert 'usage_details' not in uncertain.kwargs and 'cost_details' not in uncertain.kwargs
    assert CANARY not in str([s.kwargs for s in client.spans])
    record.ok, record.error_type = False, CANARY
    telemetry.trace_analysis(lambda: telemetry.attempt(record, ctx), lambda: 'failed')
    assert client.spans[-1].kwargs['metadata']['error_code'] == 'other'
    assert CANARY not in str(client.spans[-1].kwargs)


def test_mask_and_otel_export_reject_content_and_unknown_attributes():
    assert mask_data(data=CANARY) is None
    assert mask_data(data={'stage': 'matching', 'outcome': 'success'}) == {'stage': 'matching', 'outcome': 'success'}
    assert mask_data(data={'stage': CANARY}) is None
    assert mask_data(data={'stage': {'private': CANARY}}) is None
    assert mask_data(data={'prompt': CANARY}) is None
    attrs = {'langfuse.observation.type': 'span',
             'langfuse.observation.metadata.stage': 'matching'}
    span = SimpleNamespace(name='matching', instrumentation_scope=SimpleNamespace(name='langfuse-sdk', attributes={}, version=None, schema_url=''),
                           events=[], links=[], status=SimpleNamespace(description=None),
                           resource=SimpleNamespace(attributes={'service.name': 'jobfit-api'}), attributes=attrs)
    assert safe_export_span(span)
    span.attributes = {**attrs, 'langfuse.observation.input': CANARY}
    assert not safe_export_span(span)
    span.attributes = {**attrs, 'langfuse.observation.metadata.stage': CANARY}
    assert not safe_export_span(span)
    span.attributes = attrs
    span.events = [CANARY]
    assert not safe_export_span(span)
    span.events = []
    span.resource.attributes['owner.email'] = CANARY
    assert not safe_export_span(span)
    span.resource.attributes = {'service.name': CANARY}
    assert not safe_export_span(span)
    span.resource.attributes = {'service.name': 'jobfit-api'}
    span.instrumentation_scope.attributes = {'private': CANARY}
    assert not safe_export_span(span)


def test_real_sdk_export_payload_is_metadata_only():
    langfuse = pytest.importorskip('langfuse')
    exporter_module = pytest.importorskip('opentelemetry.sdk.trace.export.in_memory_span_exporter')
    exporter = exporter_module.InMemorySpanExporter()
    client = langfuse.Langfuse(public_key='pk-lf-synthetic', secret_key='sk-lf-synthetic',
                               base_url='https://jp.cloud.langfuse.com',
                               span_exporter=ScopeScrubbingExporter(exporter, 'pk-lf-synthetic'),
                               mask=mask_data, should_export_span=safe_export_span)
    tracer = LangfuseTracer(client)
    telemetry = Telemetry(tracer)
    record = SimpleNamespace(model='gpt-6-sol', ok=True, latency_ms=20,
                             cost_source='reported', cost_usd=.01, input_tokens=10, output_tokens=3)
    ctx = SimpleNamespace(chain='matching', attempt_kind='initial', upper_cost=.5)
    tracer.analysis(lambda: observed(telemetry, 'matching', lambda: telemetry.attempt(record, ctx)),
                    lambda: 'completed')
    # The SDK mask strips accidental input/output. The export filter also rejects
    # a raw OpenTelemetry attribute injected after that mask has run.
    masked = client.start_observation(name='matching', input=CANARY, output=CANARY)
    masked._otel_span.set_attribute('langfuse.observation.input', CANARY)
    masked.end()
    with pytest.raises(ValueError):
        tracer.analysis(lambda: (_ for _ in ()).throw(ValueError(CANARY)), lambda: 'completed')
    client.flush()
    spans = exporter.get_finished_spans()
    assert [s.name for s in spans] == ['llm_attempt', 'matching', 'jobfit.analysis', 'jobfit.analysis']
    encoded = json.dumps([dict(s.attributes) for s in spans])
    assert CANARY not in encoded and 'observation.input' not in encoded and 'observation.output' not in encoded
    assert all(not span.instrumentation_scope.attributes for span in spans)
    attrs = dict(spans[0].attributes)
    assert json.loads(attrs['langfuse.observation.usage_details']) == {'input': 10, 'output': 3}
    assert json.loads(attrs['langfuse.observation.cost_details']) == {'total': .01}


def test_api_duplicate_is_one_actual_trace_and_keeps_analysis_result():
    import uuid
    from tests.test_public_beta_api import make, owner, session, wait, scored

    client = FakeClient()
    telemetry = Telemetry(LangfuseTracer(client))
    api, _ = make(analyze=lambda cv, **kw: scored('A'), telemetry=telemetry)
    headers = session(api)
    key = str(uuid.uuid4())
    first = api.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(headers, key))
    assert first.status_code == 200
    result = wait(api, headers, first.json()['run_id'])
    second = api.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(headers, key))
    assert result['status'] == 'done'
    assert second.json()['duplicate'] is True
    assert [span.name for span in client.spans].count('jobfit.analysis') == 1
    assert client.spans[0].kwargs['metadata'] == {'outcome': 'success'}
    assert all('input' not in span.kwargs and 'output' not in span.kwargs for span in client.spans)


def test_parse_and_search_trace_only_executed_stages():
    client = FakeClient()
    telemetry = Telemetry(LangfuseTracer(client))
    assert telemetry.trace_operation('parse', lambda: observed(telemetry, 'cv_parse', lambda: 'parsed')) == 'parsed'
    assert telemetry.trace_operation('search', lambda: observed(telemetry, 'query_embedding',
                                                               lambda: observed(telemetry, 'retrieval',
                                                                                lambda: ['synthetic-job']))) == ['synthetic-job']
    assert [s.name for s in client.spans] == [
        'jobfit.parse', 'cv_parse', 'jobfit.search', 'query_embedding', 'retrieval']
    assert [s.name for s in client.spans].count('jobfit.analysis') == 0


def test_span_update_and_end_failures_do_not_change_analysis():
    class BrokenSpan:
        def start_observation(self, **_):
            return self

        def update(self, **_):
            raise RuntimeError(CANARY)

        def end(self):
            raise RuntimeError(CANARY)

    class BrokenClient:
        def start_observation(self, **_):
            return BrokenSpan()

    telemetry = Telemetry(LangfuseTracer(BrokenClient()))
    assert telemetry.trace_analysis(lambda: observed(telemetry, 'matching', lambda: 'same-result'),
                                    lambda: 'completed') == 'same-result'


def test_enabled_configuration_uses_japan_endpoint_and_exact_scope_key(monkeypatch):
    langfuse = pytest.importorskip('langfuse')
    captured = {}

    def fake_client(**kwargs):
        captured.update(kwargs)
        return FakeClient()

    monkeypatch.setattr(langfuse, 'Langfuse', fake_client)
    tracer = build_tracer({'JOBFIT_LANGFUSE_ENABLED': '1',
                           'LANGFUSE_PUBLIC_KEY': 'pk-lf-synthetic',
                           'LANGFUSE_SECRET_KEY': 'sk-lf-synthetic'})
    assert isinstance(tracer, LangfuseTracer)
    assert captured['base_url'] == 'https://jp.cloud.langfuse.com'
    assert isinstance(captured['span_exporter'], ScopeScrubbingExporter)
    scope = SimpleNamespace(name='langfuse-sdk', attributes={'public_key': 'pk-lf-other'},
                            version='4.17.0', schema_url='')
    span = SimpleNamespace(name='matching', instrumentation_scope=scope, events=[], links=[],
                           status=SimpleNamespace(description=None),
                           resource=SimpleNamespace(attributes={'service.name': 'jobfit-api'}), attributes={})
    assert not captured['should_export_span'](span)
    scope.attributes = {'public_key': 'pk-lf-synthetic'}
    assert captured['should_export_span'](span)


def test_privacy_self_check_blocks_enabling(monkeypatch):
    from jobfit.observability import langfuse as module

    monkeypatch.setattr(module, 'safe_export_span', lambda span: True)
    with pytest.raises(RuntimeError, match='privacy validation failed'):
        module.build_tracer({'JOBFIT_LANGFUSE_ENABLED': '1',
                             'LANGFUSE_PUBLIC_KEY': 'pk-lf-synthetic',
                             'LANGFUSE_SECRET_KEY': 'sk-lf-synthetic'})


def test_real_enabled_builder_uses_fake_transport_and_scrubs_scope(monkeypatch):
    pytest.importorskip('langfuse')
    otlp = pytest.importorskip('opentelemetry.exporter.otlp.proto.http.trace_exporter')
    exporter_module = pytest.importorskip('opentelemetry.sdk.trace.export.in_memory_span_exporter')
    memory = exporter_module.InMemorySpanExporter()
    config = {}

    def fake_transport(**kwargs):
        config.update(kwargs)
        return memory

    monkeypatch.setattr(otlp, 'OTLPSpanExporter', fake_transport)
    tracer = build_tracer({'JOBFIT_LANGFUSE_ENABLED': '1',
                           'LANGFUSE_PUBLIC_KEY': 'pk-lf-synthetic-builder',
                           'LANGFUSE_SECRET_KEY': 'sk-lf-synthetic-builder'})
    assert config['endpoint'] == 'https://jp.cloud.langfuse.com/api/public/otel/v1/traces'
    assert tracer.analysis(lambda: 7, lambda: 'completed') == 7
    tracer.client.flush()
    spans = memory.get_finished_spans()
    assert len(spans) == 1 and spans[0].name == 'jobfit.analysis'
    assert not spans[0].instrumentation_scope.attributes
    assert 'synthetic-builder' not in json.dumps(dict(spans[0].attributes))


def test_sdk_initialization_failure_keeps_default_api_startup_dark(monkeypatch, capsys):
    from fastapi.testclient import TestClient
    from jobfit.api.wiring import create_default_app

    langfuse = pytest.importorskip('langfuse')
    monkeypatch.setenv('JOBFIT_ENV', 'dev')
    monkeypatch.setenv('JOBFIT_LIVE_ENABLED', '0')
    monkeypatch.setenv('JOBFIT_PUBLIC_LIVE', '0')
    monkeypatch.setenv('JOBFIT_REAL_CV_ENABLED', '0')
    monkeypatch.setenv('JOBFIT_LANGFUSE_ENABLED', '1')
    monkeypatch.setenv('LANGFUSE_PUBLIC_KEY', 'pk-lf-synthetic-startup')
    monkeypatch.setenv('LANGFUSE_SECRET_KEY', 'sk-lf-synthetic-startup')

    def broken_sdk(**_):
        raise RuntimeError(CANARY)

    monkeypatch.setattr(langfuse, 'Langfuse', broken_sdk)
    api = TestClient(create_default_app())
    assert api.get('/health').status_code == 200
    assert api.app.state is not None
    captured = capsys.readouterr()
    assert CANARY not in captured.out + captured.err
    assert 'sk-lf-synthetic-startup' not in captured.out + captured.err


def test_sdk_import_and_otlp_initialization_fail_open(monkeypatch):
    import builtins
    otlp = pytest.importorskip('opentelemetry.exporter.otlp.proto.http.trace_exporter')
    env = {'JOBFIT_LANGFUSE_ENABLED': '1', 'LANGFUSE_PUBLIC_KEY': 'pk-lf-synthetic-import',
           'LANGFUSE_SECRET_KEY': 'sk-lf-synthetic-import'}
    original_import = builtins.__import__

    def broken_import(name, *args, **kwargs):
        if name == 'langfuse':
            raise ImportError(CANARY)
        return original_import(name, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(builtins, '__import__', broken_import)
        assert build_tracer(env) is None

    def broken_exporter(**_):
        raise OSError(CANARY)

    monkeypatch.setattr(otlp, 'OTLPSpanExporter', broken_exporter)
    assert build_tracer(env) is None


def test_exporter_failures_are_isolated_and_sensitive_batch_is_never_forwarded(capsys, caplog):
    langfuse = pytest.importorskip('langfuse')
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import ReadableSpan
    from opentelemetry.sdk.trace.export import SpanExportResult
    from opentelemetry.sdk.util.instrumentation import InstrumentationScope

    class Delegate:
        def __init__(self):
            self.batches = []
            self.fail = False

        def export(self, spans):
            if self.fail:
                raise RuntimeError(CANARY)
            self.batches.append(spans)
            return SpanExportResult.SUCCESS

        def shutdown(self):
            raise RuntimeError(CANARY)

        def force_flush(self, timeout_millis=30000):
            raise RuntimeError(CANARY)

    delegate = Delegate()
    exporter = ScopeScrubbingExporter(delegate, 'pk-lf-synthetic-failure')
    scope = InstrumentationScope('langfuse-sdk', '4.17.0', attributes={'public_key': 'pk-lf-synthetic-failure'})
    resource = Resource({'service.name': 'jobfit-api'})
    safe = ReadableSpan(name='matching', resource=resource, instrumentation_scope=scope,
                        attributes={'langfuse.observation.type': 'span'})
    sensitive = ReadableSpan(name='matching', resource=resource, instrumentation_scope=scope,
                             attributes={'langfuse.observation.input': CANARY})
    assert exporter.export([safe, sensitive]) == SpanExportResult.SUCCESS
    assert delegate.batches == []
    assert exporter.export([safe]) == SpanExportResult.SUCCESS
    outbound = delegate.batches[0][0]
    assert not outbound.instrumentation_scope.attributes
    assert CANARY not in json.dumps(dict(outbound.attributes))
    assert 'pk-lf-synthetic-failure' not in json.dumps(dict(outbound.attributes))
    delegate.fail = True
    assert exporter.export([safe]) == SpanExportResult.FAILURE
    assert exporter.force_flush() is False
    assert exporter.shutdown() is None

    client = langfuse.Langfuse(public_key='pk-lf-synthetic-exporter-failure',
                               secret_key='sk-lf-synthetic-exporter-failure',
                               base_url='https://jp.cloud.langfuse.com',
                               span_exporter=ScopeScrubbingExporter(delegate, 'pk-lf-synthetic-exporter-failure'),
                               mask=mask_data, should_export_span=safe_export_span)
    telemetry = Telemetry(LangfuseTracer(client))
    assert telemetry.trace_analysis(lambda: observed(telemetry, 'matching', lambda: 'same-result'),
                                    lambda: 'completed') == 'same-result'
    client.flush()
    output = capsys.readouterr()
    assert CANARY not in output.out + output.err + caplog.text
    assert 'sk-lf-synthetic-exporter-failure' not in output.out + output.err + caplog.text
