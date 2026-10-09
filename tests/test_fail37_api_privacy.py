"""FAIL-37 / D-104 commit 3: the sanitizer on the API lifecycle and the provider and sink privacy gates.

Offline only: recording fake SDKs drive the real request builders (frozen parse, query embedding, JD
extraction and evidence matching) through the public-beta ZDR client. No network and no paid call.
Real-CV flags stay off in production; these tests enable them only inside an in-process test app.
"""
import json
import logging
import pickle
import uuid

import pytest
import yaml

from jobfit.api.main import REAL_CV_MESSAGE, SANITIZE_REFUSALS
from jobfit.config import REPO_ROOT
from jobfit.extraction.audited import ExtractionSpec
from jobfit.live.runtime_client import build_public_beta_client
from jobfit.llm.public_beta_bounds import compute_public_beta_bounds
from jobfit.privacy import masking, real_cv
from jobfit.privacy.masking import mask_local, sanitize_upload
from jobfit.recommend.beta_analysis import analyze_one_job
from jobfit.recommend.real_cv_flow import PARSED_KEY, SEARCH_KEY, store_search_results
from jobfit.recommend.service import RecommendConfig
from jobfit.search.embeddings import EmbeddingSpec
from jobfit.session.store import SessionDenied, SessionHandle
from tests import masking_calibration as mc
from tests.test_live_recommend_equivalence import extraction
from tests.test_live_unit import CONFIG, FakeSDK, response, settings
from tests.test_public_beta_api import JD
from tests.test_real_cv_adapter import CV_TEXT, WIRE
from tests.test_real_cv_api import ROWS, Fakes, analyze, key_headers, make, search, session, wait

CFG = yaml.safe_load(CONFIG.read_text())
ENV = compute_public_beta_bounds().envelopes
SPEC = EmbeddingSpec('qwen3-embedding-8b', 4, 'fixture-v1', 100_000, 'fixture', '1')
EVIDENCE_QUOTE = 'Python and SQL reporting for sales.'
RAW = {   # raw privacy canaries: none may reach a provider, a response, a log or the session state
    'name': 'Ratna Kumalasari', 'email': 'ratna.kumalasari@example.com', 'phone': '+62 800-0000-0777',
    'home': 'Jl. Kenari Raya No. 77', 'linkedin': 'linkedin.com/in/example-ratna', 'handle': 'example-ratna',
    'summary': 'SUMMARYCANARY strategic visionary', 'early': 'EARLYSKILLCANARY', 'referee': 'Budi Hartono',
    'referee_phone': '+62 800-0000-0778', 'emergency': 'Sri Wahyuni', 'interest': 'INTERESTCANARY',
    'organization': 'ORGCANARY', 'supervisor': 'Dewi Lestari', 'inline_address': 'Jl. Sudirman No. 1',
    'body_email': 'ratna.k@example.org',
}
CANARY_CV = (f"{RAW['name']}\n{RAW['email']} | {RAW['phone']}\n{RAW['home']}, Jakarta\n"
             f"https://{RAW['linkedin']} | https://github.com/{RAW['handle']}\n"
             f"## Skills\n{RAW['early']} Excel\n"
             f"## Summary\n{RAW['summary']} with a record of transformation.\n"
             f"{CV_TEXT}\n"
             f"## Projects\nDashboard maintained by {RAW['name']} for the sales team.\n"
             f"Supervisor: {RAW['supervisor']}\n"
             f"Worked from {RAW['inline_address']}, leading the reporting migration.\n"
             f"Questions: {RAW['body_email']}\n"
             f"Code: https://github.com/{RAW['handle']}/sales-dashboard\n"
             f"## References\n{RAW['referee']}, {RAW['referee_phone']}\n"
             f"## Emergency Contact\n{RAW['emergency']}\n"
             f"## Interests\n{RAW['interest']} chess\n"
             f"## Organizations\n{RAW['organization']} youth party\n")


def evidence_answer(kw):
    """Deterministic evidence-matching answer for this CV, quoting its sanitized evidence."""
    data = json.loads(kw['messages'][1]['content'])['untrusted_document_data']
    assert EVIDENCE_QUOTE in data['cv_text']
    rows = [{'unit_id': u['unit_id'], 'label': 'MATCH', 'cv_quotes': [EVIDENCE_QUOTE]}
            for u in data['extraction']['units']]
    return response(kw['model'], json.dumps({'assessments': rows}))


def extraction_answer(kw):
    """Deterministic one-unit JD extraction quoting the session JD (`Python`)."""
    job_id = json.loads(kw['messages'][1]['content'])['untrusted_document_data']['job_id']
    unit = {'unit_id': 'u1', 'text': 'Python', 'field': 'skill_tool', 'importance': 'required',
            'source_quotes': ['Python']}
    return response(kw['model'], json.dumps({'job_id': job_id, 'units': [unit], 'jd_quality': 'ok',
                                             'qualification_coverage': [{'source_id': 'Q01', 'unit_ids': ['u1']}]}))


def respond(kw):
    name = kw['response_format']['json_schema']['name']
    if name == 'CVWire':
        return response(kw['model'], json.dumps(WIRE))
    if 'Evidence' in name:
        return evidence_answer(kw)
    return extraction_answer(kw)


class Tok:
    def encode(self, text):
        return text.split()


class SpyFakes(Fakes):
    """The test app's provider seams, driving the real request builders over a recording ZDR client."""

    def __init__(self, tmp_path):
        super().__init__(tmp_path)
        self.sdk = FakeSDK(respond)
        self.client = build_public_beta_client(settings(tmp_path / 'zdr'), CONFIG, run_id='spy', sdk_client=self.sdk)
        self.analyzed_cvs = []

    def real_parse(self, store, handle, lease, *, live):
        self.billable(live)
        parsed = real_cv.parse_consented_cv(store, handle, lease, client=self.client, model='deepseek-flash',
                                            analysis_date=real_cv.jakarta_date(), cv_id=real_cv.new_cv_id())
        store.put(handle, lease, PARSED_KEY, parsed)
        return parsed

    def real_search(self, store, handle, lease, filters, *, live):
        self.billable(live)
        parsed = store.read(handle, lease, PARSED_KEY)
        real_cv.embed_consented_cv(store, handle, lease, parsed, client=self.client, spec=SPEC, tokenizer=Tok())
        store_search_results(store, handle, lease, live.operation_key, ROWS)
        return ROWS

    def analyze_one(self, cv, *, job_id, jd_text, live, history_confirmed=False):
        self.billable(live)
        self.analyzed_cvs.append(cv)
        config = RecommendConfig.from_yaml(CONFIG)
        if jd_text is None:                              # a corpus job with its saved extraction
            ext, _ = extraction('J02')
            return analyze_one_job(cv, job_id, envelopes=ENV, client=self.client, config=config,
                                   cached=(ext.model_copy(update={'job_id': job_id}), None))
        return analyze_one_job(cv, job_id, envelopes=ENV, client=self.client, config=config, jd_text=jd_text,
                               spec=ExtractionSpec(REPO_ROOT / CFG['jd_prompt_file'], CFG['jd_prompt_version']),
                               extraction_model=CFG['extraction_model'], scope='session_jd')


def spy_app(tmp_path):
    f = SpyFakes(tmp_path)
    client, _, deps = make(tmp_path)
    deps.real_parse, deps.real_search, deps.analyze_one = f.real_parse, f.real_search, f.analyze_one
    return client, f, deps


def handle_of(h):
    return SessionHandle(h['X-Session-Id'], h['X-Session-Token'])


def upload(client, h, text):
    return client.post('/cv/upload', files={'file': ('cv.txt', text.encode())}, headers=h)


def edit(client, h, text):
    return client.post('/cv/preview', json={'text': text}, headers=h)


def consent(client, h, digest):
    return client.post('/cv/consent', json={'digest': digest, 'affirmative': True}, headers=h)


def parse_run(client, h):
    """POST /cv/parse, wait for it, and return (run_id, final body)."""
    r = client.post('/cv/parse', headers=key_headers(h))
    assert r.status_code == 200, r.text
    return r.json()['run_id'], wait(client, h, r.json()['run_id'])


def real_routes(client, h):
    """Status codes of the four uploaded-CV real operations."""
    pid = client.post('/jobs/paste', json={'jd_text': JD}, headers=h).json()['paste_id']
    return [client.post('/cv/parse', headers=key_headers(h)).status_code,
            search(client, h).status_code,
            analyze(client, h, 'P1').status_code,
            client.post('/analyze', json={'paste_id': pid, 'cv_source': 'upload'}, headers=key_headers(h)).status_code]


ALICE = 'Alice Example\nalice.example@example.com\n## Experience\nAnalyst at Contoh\n'


# --- upload and edit go through the full D-104 sanitizer ---------------------------------------------------

def test_the_upload_preview_is_the_v2_sanitized_text_with_a_public_digest(tmp_path):
    client, _, _ = make(tmp_path)
    body = upload(client, session(client), CANARY_CV).json()
    assert body['masked_text'] == sanitize_upload(CANARY_CV).text
    assert set(body) == {'masked_text', 'digest', 'masked_counts', 'removed', 'owner_repeat_guard', 'warnings',
                         'layout', 'provider_processing', 'message'}
    import hashlib
    assert body['digest'] == hashlib.sha256(body['masked_text'].encode()).hexdigest()
    assert body['owner_repeat_guard'] == 'active' and body['removed']['summary_sections'] == 1
    assert {'references', 'emergency_contact', 'interests', 'organizations'} <= set(body['removed'])
    assert not any(v in body['masked_text'] for v in RAW.values())


def test_an_edit_is_fully_sanitized_again_and_invalidates_consent_and_all_derived_state(tmp_path):
    client, f, deps = spy_app(tmp_path)
    h = session(client)
    up = upload(client, h, CANARY_CV).json()
    assert consent(client, h, up['digest']).status_code == 200
    run_id, run = parse_run(client, h)
    assert run['status'] == 'done' and search(client, h).status_code == 200
    calls = len(f.sdk.calls)
    added = (f"{RAW['name']}\n{RAW['email']}\n## Summary\n{RAW['summary']}\n" + up['masked_text'] +
             f"\nLead: {RAW['name']}, {RAW['body_email']}, {RAW['phone']}\nAlamat: {RAW['home']}\n"
             f"[repo](https://github.com/{RAW['handle']}/etl)\n## References\n{RAW['referee']}\n"
             f"## Interests\n{RAW['interest']}\n")
    out = edit(client, h, added).json()
    assert out['digest'] != up['digest'] and not any(v in out['masked_text'] for v in RAW.values())
    assert 'Lead: [NAME], [EMAIL], [PHONE]' in out['masked_text'] and 'Alamat: [ADDRESS]' in out['masked_text']
    assert '[repo](https://github.com/[PROFILE]/etl)' in out['masked_text']
    assert client.post('/cv/parse', headers=key_headers(h)).status_code == 409
    state = deps.store._states[h['X-Session-Id']]
    assert state.data == {} and state.consent_digest is None
    assert client.get(f"/recommendations/{run_id}", headers=h).status_code == 404     # real runs dropped
    assert consent(client, h, up['digest']).status_code == 409                               # old digest is stale
    assert len(f.sdk.calls) == calls


# --- OwnerMarks lifecycle ----------------------------------------------------------------------------------

def test_a_failed_edit_keeps_the_owner_marks_of_the_current_upload(tmp_path):
    client, _, deps = make(tmp_path)
    h = session(client)
    assert upload(client, h, ALICE).status_code == 200
    assert edit(client, h, 'no recognised heading at all').status_code == 422
    assert deps.store.owner_marks(handle_of(h)) is not None
    assert edit(client, h, '## Experience\nLead: Alice Example\n').json()['masked_text'] == '## Experience\nLead: [NAME]\n'


def test_a_failed_fresh_upload_clears_the_previous_owner_marks(tmp_path):
    client, _, deps = make(tmp_path)
    h = session(client)
    assert upload(client, h, ALICE).status_code == 200
    assert upload(client, h, 'Bob Builder\nno recognised heading').status_code == 422
    assert deps.store.owner_marks(handle_of(h)) is None
    assert 'Alice Example' in edit(client, h, '## Experience\nLead: Alice Example\n').json()['masked_text']


def test_a_new_upload_replaces_the_owner_marks(tmp_path):
    client, _, _ = make(tmp_path)
    h = session(client)
    upload(client, h, ALICE)
    upload(client, h, 'Bob Builder\nbob.builder@example.com\n## Experience\nTester\n')
    text = edit(client, h, '## Experience\nAlice Example and Bob Builder\n').json()['masked_text']
    assert text == '## Experience\nAlice Example and [NAME]\n'


def test_a_preview_without_marks_replaces_the_marks_and_delete_drops_them(tmp_path):
    client, _, deps = make(tmp_path)
    h = session(client)
    upload(client, h, ALICE)
    handle = handle_of(h)
    assert deps.store.owner_marks(handle) is not None
    deps.store.set_preview(handle, mask_local('## Experience\nAnalyst\n'))
    assert deps.store.owner_marks(handle) is None
    upload(client, h, ALICE)
    client.delete('/session', headers=h)
    with pytest.raises(SessionDenied):
        deps.store.owner_marks(handle)


# --- fail closed: no start, masking failure, session races -------------------------------------------------

@pytest.mark.parametrize('route', ['upload', 'edit', 'summary_only'])
def test_no_evidence_start_fails_closed_and_invalidates_everything(tmp_path, route):
    client, f, deps = spy_app(tmp_path)
    h = session(client)
    up = upload(client, h, CANARY_CV).json()
    consent(client, h, up['digest'])
    run_id, run = parse_run(client, h)
    assert run['status'] == 'done'
    calls = len(f.sdk.calls)
    bad = {'upload': lambda: upload(client, h, 'Only prose, no recognised section.'),
           'edit': lambda: edit(client, h, 'Only prose, no recognised section.'),
           'summary_only': lambda: upload(client, h, f"{RAW['name']}\n## Summary\n{RAW['summary']}\n")}[route]()
    assert bad.status_code == 422
    assert bad.json() == {'detail': SANITIZE_REFUSALS['professional_boundary_not_found'],
                          'code': 'professional_boundary_not_found'}
    assert real_routes(client, h) == [409, 409, 409, 409]
    state = deps.store._states[h['X-Session-Id']]
    assert state.text is None and state.data == {} and state.consent_digest is None
    assert client.get(f"/recommendations/{run_id}", headers=h).status_code == 404
    assert len(f.sdk.calls) == calls


def test_an_internal_sanitizer_error_fails_closed_through_the_real_boundary(tmp_path, monkeypatch, caplog):
    client, f, _ = spy_app(tmp_path)
    h = session(client)

    def broken(text):
        raise RuntimeError(f"INTERNALCANARY {RAW['email']}")
    monkeypatch.setattr(masking, '_address_spans', broken)
    with caplog.at_level(logging.DEBUG):
        r = upload(client, h, CANARY_CV)
    assert r.status_code == 422 and r.json() == {'detail': SANITIZE_REFUSALS['masking_failed'], 'code': 'masking_failed'}
    assert 'INTERNALCANARY' not in r.text and 'INTERNALCANARY' not in caplog.text and RAW['email'] not in caplog.text
    assert real_routes(client, h) == [409, 409, 409, 409] and f.sdk.calls == []


def test_a_lone_surrogate_edit_fails_closed(tmp_path):
    client, f, deps = spy_app(tmp_path)
    h = session(client)
    up = upload(client, h, CANARY_CV).json()
    consent(client, h, up['digest'])
    r = client.post('/cv/preview', content=b'{"text": "## Experience\\nbad \\ud800 text"}',
                    headers={**h, 'content-type': 'application/json'})
    assert r.status_code == 422 and r.json() == {'detail': SANITIZE_REFUSALS['masking_failed'], 'code': 'masking_failed'}
    state = deps.store._states[h['X-Session-Id']]
    assert (state.text, state.text_digest, state.consent_digest, state.masking_version) == (None, None, None, None)
    assert not state.data and deps.store.owner_marks(handle_of(h)) is not None      # a failed EDIT keeps the marks
    assert real_routes(client, h) == [409, 409, 409, 409] and f.sdk.calls == []
    later = f"## Experience\nDashboard maintained by {RAW['name']} for sales.\n"
    assert RAW['name'] in sanitize_upload(later).text                                # only the kept marks mask it
    assert RAW['name'] not in edit(client, h, later).json()['masked_text']


def test_a_lone_surrogate_edit_with_the_session_lost_mid_handler_is_401(tmp_path, monkeypatch):
    client, _, deps = make(tmp_path)
    h = session(client)
    assert upload(client, h, CANARY_CV).status_code == 200

    def gone(*_args, **_kwargs):
        raise SessionDenied('SESSIONCANARY expired')
    monkeypatch.setattr(deps.store, 'invalidate_preview', gone)
    r = client.post('/cv/preview', content=b'{"text": "## Experience\\nbad \\ud800 text"}',
                    headers={**h, 'content-type': 'application/json'})
    assert r.status_code == 401 and r.json() == {'detail': 'Session unavailable'} and 'SESSIONCANARY' not in r.text


@pytest.mark.parametrize('method,action', [('set_preview', 'upload'), ('invalidate_preview', 'failed_upload'),
                                           ('owner_marks', 'edit')])
def test_a_session_lost_mid_request_is_401_without_exception_text(tmp_path, monkeypatch, method, action):
    client, _, deps = make(tmp_path)
    h = session(client)

    def gone(*a, **kw):
        raise SessionDenied('RACECANARY internal detail')
    monkeypatch.setattr(deps.store, method, gone)
    r = {'upload': lambda: upload(client, h, ALICE), 'failed_upload': lambda: upload(client, h, 'no heading'),
         'edit': lambda: edit(client, h, ALICE)}[action]()
    assert r.status_code == 401 and r.json() == {'detail': 'Session unavailable'} and 'RACECANARY' not in r.text


# --- consent binding and the masking-version guard ---------------------------------------------------------

def test_consent_is_bound_to_the_exact_v2_digest(tmp_path):
    client, _, _ = make(tmp_path)
    h = session(client)
    up = upload(client, h, CANARY_CV).json()
    assert consent(client, h, '0' * 64).status_code == 409
    assert client.post('/cv/consent', json={'digest': up['digest'], 'affirmative': False}, headers=h).status_code == 409
    assert consent(client, h, up['digest']).status_code == 200
    edited = edit(client, h, up['masked_text'] + '\nAirflow\n').json()
    assert consent(client, h, up['digest']).status_code == 409 and consent(client, h, edited['digest']).status_code == 200


def test_a_v1_or_hand_built_preview_is_refused_by_every_uploaded_cv_operation(tmp_path):
    client, f, deps = spy_app(tmp_path)
    h = session(client)
    v1 = mask_local(CV_TEXT)
    deps.store.set_preview(handle_of(h), v1)
    assert consent(client, h, v1.digest).status_code == 200            # consent itself is digest-only
    assert real_routes(client, h) == [409, 409, 409, 409]
    assert f.sdk.calls == [] and f.provider_calls == []


# --- the API-phase gates: provider payloads and every sink --------------------------------------------------

def run_full_flow(client, f, h, caplog):
    bodies = []

    def keep(r):
        bodies.append(r.text)
        return r
    with caplog.at_level(logging.DEBUG):
        up = keep(upload(client, h, CANARY_CV)).json()
        keep(consent(client, h, up['digest']))
        parsed = keep(client.post('/cv/parse', headers=key_headers(h))).json()
        bodies.append(json.dumps(wait(client, h, parsed['run_id'])))        # search needs the finished parse
        assert keep(search(client, h)).status_code == 200
        a = keep(analyze(client, h, 'P2')).json()
        bodies.append(json.dumps(wait(client, h, a['run_id'])))
        pid = keep(client.post('/jobs/paste', json={'jd_text': JD}, headers=h)).json()['paste_id']
        b = keep(client.post('/analyze', json={'paste_id': pid, 'cv_source': 'upload'}, headers=key_headers(h))).json()
        bodies.append(json.dumps(wait(client, h, b['run_id'])))
        keep(edit(client, h, 'only prose, no section'))
        keep(upload(client, h, f"{RAW['name']}\n## Summary\n{RAW['summary']}\n"))
        keep(client.get('/metrics', headers=h))
    return bodies


def payload_texts(sdk):
    return [json.dumps(kw, default=str) for kw in sdk.calls]


def test_no_summary_or_raw_canary_reaches_any_provider_payload(tmp_path, caplog):
    """API gate no_summary_in_provider_payload (also part of raw_canary_sinks_zero)."""
    client, f, _ = spy_app(tmp_path)
    run_full_flow(client, f, session(client), caplog)
    kinds = {}
    for kw in f.sdk.calls:
        name = kw['response_format']['json_schema']['name'] if 'response_format' in kw else 'embedding'
        kinds[name] = kinds.get(name, 0) + 1
        assert kw['extra_body']['provider']['zdr'] is True and kw['extra_body']['provider']['data_collection'] == 'deny'
    assert kinds.get('CVWire') == 1 and kinds.get('embedding') == 1
    assert sum(v for k, v in kinds.items() if 'Evidence' in k) == 2            # per-job and pasted-JD matching
    assert sum(v for k, v in kinds.items() if k not in ('CVWire', 'embedding') and 'Evidence' not in k) == 1
    for text in payload_texts(f.sdk):
        assert RAW['summary'] not in text and 'SUMMARYCANARY' not in text
        assert not any(v in text for v in RAW.values()), text[:200]
    for kw in f.sdk.calls:
        name = kw['response_format']['json_schema']['name'] if 'response_format' in kw else 'embedding'
        content = json.dumps(kw.get('messages') or kw.get('input'))
        if name not in ('CVWire', 'embedding') and 'Evidence' not in name:       # the pasted-JD extraction
            assert 'Python and SQL for data pipelines' in content and EVIDENCE_QUOTE not in content
        else:
            assert EVIDENCE_QUOTE in content                                      # only sanitized CV evidence
    sanitized = sanitize_upload(CANARY_CV).text
    assert all(cv.profile.raw_text == sanitized for cv in f.analyzed_cvs) and len(f.analyzed_cvs) == 2


def test_raw_canary_sinks_zero_across_the_full_flow(tmp_path, caplog):
    """API gate raw_canary_sinks_zero: responses, errors, logs, provider payloads and session state."""
    client, f, deps = spy_app(tmp_path)
    h = session(client)
    bodies = run_full_flow(client, f, h, caplog)
    assert client.get('/metrics', headers=h).status_code == 404     # no metrics sink exists yet; add it here if one does
    state = deps.store._states[h['X-Session-Id']]
    sinks = {'responses': '\n'.join(bodies), 'logs': caplog.text, 'providers': '\n'.join(payload_texts(f.sdk)),
             'state': repr(state) + json.dumps(state.text) + repr(state.data)}
    for sink, text in sinks.items():
        leaked = [k for k, v in RAW.items() if v in text]
        assert not leaked, (sink, leaked)
    client.delete('/session', headers=h)
    assert h['X-Session-Id'] not in deps.store._states


def test_owner_marks_internals_never_serialize(tmp_path, caplog):
    client, f, deps = spy_app(tmp_path)
    h = session(client)
    bodies = run_full_flow(client, f, h, caplog)
    upload(client, h, CANARY_CV)
    marks = deps.store.owner_marks(handle_of(h))
    assert marks and repr(marks).startswith('OwnerMarks(<')
    secrets_ = [marks._key.hex()] + [d.hex() for d in marks._digests]
    everything = '\n'.join(bodies) + caplog.text + '\n'.join(payload_texts(f.sdk))
    assert not any(s in everything for s in secrets_)
    assert 'OwnerMarks' not in '\n'.join(bodies) and '_digests' not in everything
    assert '"marks"' not in '\n'.join(bodies)
    for dump in (pickle.dumps, json.dumps):
        with pytest.raises(TypeError):
            dump(marks)
    assert 'marks' not in repr(deps.store._states[h['X-Session-Id']]) or 'owner_marks=' not in \
        repr(deps.store._states[h['X-Session-Id']])
    up = upload(client, h, CANARY_CV).json()
    assert len(up['digest']) == 64 and consent(client, h, up['digest']).status_code == 200    # public digest kept


def test_the_api_gate_evidence_tests_exist():
    import sys
    module = sys.modules[__name__]
    for gate, node in mc.API_GATE_TESTS.items():
        path, name = node.split('::')
        assert path == 'tests/test_fail37_api_privacy.py' and callable(getattr(module, name)), gate
    assert set(mc.API_GATE_TESTS) == {g for g, v in mc.HARD_GATES.items() if v[0] == 'api'}


def test_the_closed_message_no_longer_claims_open_privacy_checks():
    assert 'not enabled yet' in REAL_CV_MESSAGE and 'still open' not in REAL_CV_MESSAGE
    assert 'D-051' not in REAL_CV_MESSAGE


def test_an_invalid_preview_edit_never_echoes_the_submitted_text(tmp_path, caplog):
    client, _, _ = make(tmp_path)
    h = session(client)
    canary = f"## Experience\n{RAW['email']} "
    with caplog.at_level(logging.DEBUG):
        for r in (edit(client, h, ''), edit(client, h, canary + 'x' * 100_000),
                  client.post('/cv/preview', content=f'{{"text": "{canary}'.encode(),          # malformed JSON
                              headers={**h, 'content-type': 'application/json'})):
            assert r.status_code == 422 and r.json() == {
                'detail': 'The edited text must be 1 to 100,000 characters of text.', 'code': 'preview_invalid'}
            assert RAW['email'] not in r.text and 'xxxx' not in r.text
    assert RAW['email'] not in caplog.text and 'xxxx' not in caplog.text


def no_session(h):
    """The request headers without the session pair (the internal ingress token stays)."""
    return {k: v for k, v in h.items() if not k.lower().startswith('x-session-')}


def test_other_validation_failures_keep_the_fastapi_default(tmp_path):
    client, _, _ = make(tmp_path)
    h = session(client)
    other = client.post('/jobs/paste', json={'jd_text': ''}, headers=h)                # another route: unchanged
    assert other.status_code == 422 and 'code' not in other.json()
    assert [e['type'] for e in other.json()['detail']] == ['string_too_short']
    missing = client.post('/cv/preview', json={'text': '## Experience\nPython 2025'}, headers=no_session(h))
    assert missing.status_code == 422 and 'code' not in missing.json()
    assert {e['loc'][0] for e in missing.json()['detail']} == {'header'}


def test_missing_headers_with_an_invalid_body_report_only_the_header_errors(tmp_path):
    client, _, _ = make(tmp_path)
    h = session(client)
    r = client.post('/cv/preview', json={'text': f"## Experience\n{RAW['email']} " + 'x' * 100_000},
                    headers=no_session(h))
    assert r.status_code == 422 and 'code' not in r.json()
    assert {e['loc'][0] for e in r.json()['detail']} == {'header'}
    assert RAW['email'] not in r.text and 'xxxx' not in r.text
