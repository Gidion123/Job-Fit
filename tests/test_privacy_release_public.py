"""Pre-deploy privacy release evidence for the controlled public beta (synthetic canary CV, no paid call).

A non-owner visitor (no owner token, a per-IP ticket) runs the whole live flow through the API with the
real request builders over a recording ZDR client and metadata-only Langfuse tracing exported in memory.
No raw canary may reach a response, a log, /metrics, a provider payload, the session state or the
Langfuse export. The deployed gate (CP3.4) repeats this on the VPS; see docs/checkpoint_3.
"""
import json
import logging

import pytest

from jobfit.observability.metrics import Telemetry
from tests.test_fail37_api_privacy import CANARY_CV, JD, RAW, SpyFakes, payload_texts
from tests.test_real_cv_api import analyze, key_headers, make, search, session, wait


def test_a_public_visitor_runs_the_live_flow_without_any_canary_in_any_sink(tmp_path, caplog):
    langfuse = pytest.importorskip('langfuse')
    memory_module = pytest.importorskip('opentelemetry.sdk.trace.export.in_memory_span_exporter')
    from jobfit.observability.langfuse import LangfuseTracer, ScopeScrubbingExporter, mask_data, safe_export_span
    memory = memory_module.InMemorySpanExporter()
    key = 'pk-lf-synthetic-public-release'              # unique: the SDK caches one client per public key
    tracer = LangfuseTracer(langfuse.Langfuse(
        public_key=key, secret_key='sk-lf-synthetic', base_url='https://jp.cloud.langfuse.com',
        span_exporter=ScopeScrubbingExporter(memory, key), mask=mask_data,
        should_export_span=safe_export_span))
    f = SpyFakes(tmp_path)
    client, _, deps = make(tmp_path / 'app', public=True, telemetry=Telemetry(tracer))
    deps.real_parse, deps.real_search, deps.analyze_one = f.real_parse, f.real_search, f.analyze_one
    deps.consume_ticket = f.consume_ticket
    h = session(client)                                       # a visitor: no owner token anywhere
    with caplog.at_level(logging.DEBUG):
        bodies, metrics = public_flow(client, h)
    tracer.client.flush()
    spans = memory.get_finished_spans()
    exported = json.dumps([{'name': s.name, 'attrs': dict(s.attributes)} for s in spans])
    assert {'jobfit.parse', 'jobfit.search', 'jobfit.analysis'} <= {s.name for s in spans}
    assert_no_canary(f, deps, h, bodies, caplog.text, metrics, langfuse=exported)
    assert 'observation.input' not in exported and 'observation.output' not in exported
    client.delete('/session', headers=h)
    assert h['X-Session-Id'] not in deps.store._states


def public_flow(client, h):
    """Upload -> masking preview -> consent -> parse -> Find Jobs -> Analyze Fit (corpus and pasted JD)."""
    bodies = []

    def keep(r):
        assert r.status_code == 200, r.text
        bodies.append(r.text)
        return r.json()
    up = keep(client.post('/cv/upload', files={'file': ('cv.txt', CANARY_CV.encode())}, headers=h))
    assert up['provider_processing'] == 'enabled'                        # the open beta offers consent
    keep(client.post('/cv/consent', json={'digest': up['digest'], 'affirmative': True}, headers=h))
    run = keep(client.post('/cv/parse', headers=key_headers(h, owner=False)))
    parsed = wait(client, h, run['run_id'])
    assert parsed['status'] == 'done', parsed
    bodies.append(json.dumps(parsed))
    found = keep(search(client, h, owner=False))                        # Find Jobs uses the parsed CV
    assert found['jobs'] and found['cv_source'] == 'upload'
    run = keep(analyze(client, h, 'P2', owner=False))
    done = wait(client, h, run['run_id'])
    assert done['status'] == 'done', done
    bodies.append(json.dumps(done))
    pid = keep(client.post('/jobs/paste', json={'jd_text': JD}, headers=h))['paste_id']
    run = keep(client.post('/analyze', json={'paste_id': pid, 'cv_source': 'upload'},
                           headers=key_headers(h, owner=False)))
    bodies.append(json.dumps(wait(client, h, run['run_id'])))
    return bodies, client.get('/metrics', headers=h).text


def assert_no_canary(f, deps, h, bodies, logs, metrics, **extra):
    assert len(f.tickets) == 1 and all(not live.owner for live in f.lives)   # one per-IP ticket, never the owner
    for kw in f.sdk.calls:                                                   # every provider call is ZDR
        assert kw['extra_body']['provider']['zdr'] is True
        assert kw['extra_body']['provider']['data_collection'] == 'deny'
    state = deps.store._states[h['X-Session-Id']]
    sinks = {'responses': '\n'.join(bodies), 'logs': logs, 'metrics': metrics, **extra,
             'providers': '\n'.join(payload_texts(f.sdk)), 'state': repr(state) + json.dumps(state.text)}
    for sink, text in sinks.items():
        leaked = [k for k, v in RAW.items() if v in text]
        assert not leaked, (sink, leaked)


def test_without_langfuse_a_public_visitor_runs_the_live_flow_with_the_parsed_cv_and_no_canary(tmp_path, caplog):
    """Owner decision for the Basic Auth demo: JOBFIT_LANGFUSE_ENABLED=0, no tracer at all."""
    f = SpyFakes(tmp_path)
    client, _, deps = make(tmp_path / 'app', public=True, telemetry=Telemetry())
    deps.real_parse, deps.real_search, deps.analyze_one = f.real_parse, f.real_search, f.analyze_one
    deps.consume_ticket = f.consume_ticket
    assert client.get('/health').json()['public_beta_open'] is True
    h = session(client)
    with caplog.at_level(logging.DEBUG):
        bodies, metrics = public_flow(client, h)
    assert len(f.analyzed_cvs) == 2 and f.analyzed_cvs[0] == f.analyzed_cvs[1]   # the same extracted CV
    assert f.analyzed_cvs[0].profile.is_synthetic is False
    assert_no_canary(f, deps, h, bodies, caplog.text, metrics)
    client.delete('/session', headers=h)
    assert h['X-Session-Id'] not in deps.store._states


def test_a_closed_beta_offers_no_consent_and_makes_no_provider_call(tmp_path):
    f = SpyFakes(tmp_path)
    client, _, deps = make(tmp_path / 'app', public=False, telemetry=Telemetry())
    deps.real_parse, deps.real_search, deps.analyze_one = f.real_parse, f.real_search, f.analyze_one
    deps.consume_ticket = f.consume_ticket
    assert client.get('/health').json()['public_beta_open'] is False
    h = session(client)
    up = client.post('/cv/upload', files={'file': ('cv.txt', CANARY_CV.encode())}, headers=h).json()
    assert up['provider_processing'] == 'disabled'                       # the UI's "not enabled" notice
    client.post('/cv/consent', json={'digest': up['digest'], 'affirmative': True}, headers=h)
    assert client.post('/cv/parse', headers=key_headers(h, owner=False)).status_code != 200
    assert f.sdk.calls == [] and f.tickets == []
