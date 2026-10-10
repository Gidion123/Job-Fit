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
    bodies = []

    def keep(r):
        assert r.status_code == 200, r.text
        bodies.append(r.text)
        return r.json()
    with caplog.at_level(logging.DEBUG):
        up = keep(client.post('/cv/upload', files={'file': ('cv.txt', CANARY_CV.encode())}, headers=h))
        assert up['provider_processing'] == 'enabled'                    # the open beta offers consent
        keep(client.post('/cv/consent', json={'digest': up['digest'], 'affirmative': True}, headers=h))
        run = keep(client.post('/cv/parse', headers=key_headers(h, owner=False)))
        bodies.append(json.dumps(wait(client, h, run['run_id'])))
        keep(search(client, h, owner=False))
        run = keep(analyze(client, h, 'P2', owner=False))
        bodies.append(json.dumps(wait(client, h, run['run_id'])))
        pid = keep(client.post('/jobs/paste', json={'jd_text': JD}, headers=h))['paste_id']
        run = keep(client.post('/analyze', json={'paste_id': pid, 'cv_source': 'upload'},
                               headers=key_headers(h, owner=False)))
        bodies.append(json.dumps(wait(client, h, run['run_id'])))
        metrics = client.get('/metrics', headers=h).text
    tracer.client.flush()
    spans = memory.get_finished_spans()
    exported = json.dumps([{'name': s.name, 'attrs': dict(s.attributes)} for s in spans])
    assert {'jobfit.parse', 'jobfit.search', 'jobfit.analysis'} <= {s.name for s in spans}
    assert len(f.tickets) == 1 and all(not live.owner for live in f.lives)   # one per-IP ticket, never the owner
    for kw in f.sdk.calls:                                                   # every provider call is ZDR
        assert kw['extra_body']['provider']['zdr'] is True
        assert kw['extra_body']['provider']['data_collection'] == 'deny'
    state = deps.store._states[h['X-Session-Id']]
    sinks = {'responses': '\n'.join(bodies), 'logs': caplog.text, 'metrics': metrics, 'langfuse': exported,
             'providers': '\n'.join(payload_texts(f.sdk)), 'state': repr(state) + json.dumps(state.text)}
    for sink, text in sinks.items():
        leaked = [k for k, v in RAW.items() if v in text]
        assert not leaked, (sink, leaked)
    assert 'observation.input' not in exported and 'observation.output' not in exported
    client.delete('/session', headers=h)
    assert h['X-Session-Id'] not in deps.store._states
