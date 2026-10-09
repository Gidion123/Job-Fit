"""Real-CV public-beta API contract (CP3). Fakes only: no provider, runtime or database.

Upload -> exact consent -> reserved parse -> reserved search (Relevant Jobs, no score) -> Analyze Fit
on a job from those results, and Check a Job with a pasted JD. Real CVs and the public beta stay off
unless enabled; the owner skips only the ticket and the allowance; the public path uses the durable
ticket and BetaAllowances; edits, deletion and limits behave as specified.
"""
import json
import threading
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from jobfit.api.main import PUBLIC_BETA_CLOSED_MESSAGE, REAL_CV_MESSAGE, AppDeps, create_app
from jobfit.cv import upload_guard
from jobfit.live.operation import LiveRefused
from jobfit.live.quota import Ingress
from jobfit.llm.runtime import build_runtime_client
from jobfit.privacy import real_cv
from jobfit.recommend.real_cv_flow import PARSED_KEY, SEARCH_KEY, search_result_key, store_search_results
from jobfit.session.store import SessionStore
from tests.test_api import CV as DEMO_CV, fake_rec
from tests.test_live_api import HMAC_KEY, OWNER, TOKEN
from tests.test_live_unit import CONFIG, FakeSDK, response, settings
from tests.test_public_beta_api import JD, scored
from tests.test_real_cv_adapter import CV_TEXT, WIRE

CANARY = 'Data Analyst, PT Contoh'
ROWS = [{'job_id': f'P{i}', 'retrieval_rank': i, 'filter_status': 'matches', 'title': f'Role P{i}',
         'company': 'Acme', 'role_family': 'data_science', 'country_code': 'ID', 'city': 'Jakarta',
         'location': 'Jakarta, ID', 'work_mode': 'remote', 'posted_at': '2026-10-01', 'url': None}
        for i in (1, 2, 3)]
QUOTA_FATAL = {'refused': 'quota_refused', 'unavailable': 'quota_unavailable', 'unknown': 'quota_outcome_unknown'}


class Fakes:
    """Simulates the runtime's admission order: the ticket at the first billable call, then the intent."""

    def __init__(self, tmp_path, ticket='consumed'):
        self.tmp_path, self.ticket = tmp_path, ticket
        self.provider_calls, self.lives, self.tickets = [], [], []

    def billable(self, live):
        self.lives.append(live)
        if live.quota is not None:
            outcome = live.quota()
            if outcome != 'consumed':
                raise LiveRefused(QUOTA_FATAL[outcome])
        if live.on_first_billable is not None:
            assert live.on_first_billable() is True
        self.provider_calls.append(live.operation_key)

    def real_parse(self, store, handle, lease, *, live):
        self.billable(live)
        sdk = FakeSDK(lambda kw: response(kw['model'], json.dumps(WIRE)))
        client = build_runtime_client(settings(self.tmp_path / uuid.uuid4().hex), CONFIG, sdk_client=sdk)
        parsed = real_cv.parse_consented_cv(store, handle, lease, client=client, model='deepseek-flash',
                                            analysis_date=real_cv.jakarta_date(), cv_id=real_cv.new_cv_id())
        store.put(handle, lease, PARSED_KEY, parsed)
        return parsed

    def real_search(self, store, handle, lease, filters, *, live):
        self.billable(live)
        self.searches = getattr(self, 'searches', 0) + 1
        rows = ROWS if self.searches == 1 else [dict(r, retrieval_rank=4 - r['retrieval_rank']) for r in ROWS[::-1]]
        store_search_results(store, handle, lease, live.operation_key, rows)
        return rows

    def analyze_one(self, cv, *, job_id, jd_text, live, history_confirmed=False):
        assert cv.profile.is_synthetic is False or live.owner
        self.billable(live)
        self.history = getattr(self, 'history', []) + [history_confirmed]
        return scored(job_id)

    def consume_ticket(self, pseudonym):
        self.tickets.append(pseudonym)
        return self.ticket


def make(tmp_path, *, real=True, public=False, ticket='consumed', **kw):
    f = Fakes(tmp_path, ticket)
    deps = AppDeps(store=SessionStore(), demo_cvs={'CV1': DEMO_CV}, run=fake_rec, sweep_seconds=None,
                   live_enabled=True, ingress=Ingress(TOKEN, OWNER, HMAC_KEY), public_live=public,
                   real_cv_enabled=real, public_beta_open=public, real_parse=f.real_parse,
                   real_search=f.real_search, analyze_one=f.analyze_one, consume_ticket=f.consume_ticket,
                   job_analysis_refusal=lambda cv, **kw: None, **kw)
    return TestClient(create_app(deps)), f, deps


def session(client, ip='203.0.113.7'):
    headers = {'x-jobfit-internal-token': TOKEN, 'x-jobfit-client-ip': ip}
    s = client.post('/session', headers=headers).json()
    return {'X-Session-Id': s['session_id'], 'X-Session-Token': s['token'], **headers}


def key_headers(h, owner=True, key=None):
    out = {**h, 'Idempotency-Key': key or str(uuid.uuid4())}
    if owner:
        out['x-jobfit-owner-token'] = OWNER
    return out


def wait(client, h, run_id):
    for _ in range(500):
        body = client.get(f'/recommendations/{run_id}', headers=h).json()
        if body['status'] != 'running':
            return body
        time.sleep(0.01)
    raise AssertionError('run did not finish')


def upload_and_consent(client, h, text=CV_TEXT):
    up = client.post('/cv/upload', files={'file': ('cv.txt', text.encode())}, headers=h)
    assert up.status_code == 200, up.text
    assert client.post('/cv/consent', json={'digest': up.json()['digest'], 'affirmative': True},
                       headers=h).status_code == 200
    return up.json()


def parse(client, h, owner=True, key=None):
    r = client.post('/cv/parse', headers=key_headers(h, owner, key))
    assert r.status_code == 200, r.text
    return wait(client, h, r.json()['run_id'])


def search(client, h, owner=True, key=None, **filters):
    return client.post('/jobs/search', json={'cv_source': 'upload', **filters}, headers=key_headers(h, owner, key))


def analyze(client, h, job_id='P1', owner=True, key=None):
    return client.post(f'/jobs/{job_id}/analyze', json={'cv_source': 'upload'}, headers=key_headers(h, owner, key))


# --- gates ---------------------------------------------------------------------------------------------

def test_real_cvs_stay_off_unless_enabled_even_for_the_owner(tmp_path):
    client, f, _ = make(tmp_path, real=False)
    h = session(client)
    upload_and_consent(client, h)
    r = client.post('/cv/parse', headers=key_headers(h))
    assert r.status_code == 403 and r.json()['detail'] == REAL_CV_MESSAGE
    assert search(client, h).status_code == 403 and analyze(client, h).status_code == 403
    assert f.provider_calls == []


def test_the_public_beta_stays_closed_to_non_owners_until_open(tmp_path):
    client, f, _ = make(tmp_path, public=False)
    h = session(client)
    upload_and_consent(client, h)
    r = client.post('/cv/parse', headers=key_headers(h, owner=False))
    assert r.status_code == 503 and r.json()['detail'] == PUBLIC_BETA_CLOSED_MESSAGE
    assert f.provider_calls == [] and f.tickets == []


# --- the owner flow ---------------------------------------------------------------------------------------

def test_the_owner_flow_upload_consent_parse_search_analyze(tmp_path):
    client, f, _ = make(tmp_path)
    h = session(client)
    upload_and_consent(client, h)
    body = parse(client, h)
    assert body['status'] == 'done' and body['kind'] == 'parse' and body['result']['stage'] == 'parsed'
    assert body['result']['summary']['parse_status'] == 'ok'
    s = search(client, h)
    assert s.status_code == 200, s.text
    out = s.json()
    assert out['stage'] == 'retrieval' and out['final_order'] is False and out['cv_source'] == 'upload'
    for card, row in zip(out['jobs'], ROWS):
        assert card['match_score'] is None and card['analyzed'] is False
        assert {k: card[k] for k in ('role_family', 'country_code', 'city', 'work_mode', 'posted_at')} == {
            k: row[k] for k in ('role_family', 'country_code', 'city', 'work_mode', 'posted_at')}
    a = analyze(client, h, 'P2')
    res = wait(client, h, a.json()['run_id'])['result']
    assert res['stage'] == 'analyzed' and res['match_score'] == 100.0 and res['cv_source'] == 'upload'
    assert res['card']['title'] == 'Role P2'
    assert all(live.owner and live.quota is None and live.on_first_billable is None for live in f.lives)
    assert f.tickets == []


def test_check_a_job_uses_the_consented_parsed_cv_and_the_session_paste(tmp_path):
    client, f, _ = make(tmp_path)
    h = session(client)
    upload_and_consent(client, h)
    parse(client, h)
    pid = client.post('/jobs/paste', json={'jd_text': JD}, headers=h).json()['paste_id']
    r = client.post('/analyze', json={'paste_id': pid, 'cv_source': 'upload'}, headers=key_headers(h))
    res = wait(client, h, r.json()['run_id'])['result']
    assert res['stage'] == 'analyzed' and res['card']['title'] == 'Pasted job description'


# --- order, consent and invalidation ----------------------------------------------------------------------

def test_nothing_runs_before_consent_parse_or_search(tmp_path):
    client, f, _ = make(tmp_path)
    h = session(client)
    client.post('/cv/upload', files={'file': ('cv.txt', CV_TEXT.encode())}, headers=h)
    r = client.post('/cv/parse', headers=key_headers(h))
    assert (r.status_code, r.json()['detail']) == (409, 'consent_required')
    up = client.post('/cv/upload', files={'file': ('cv.txt', CV_TEXT.encode())}, headers=h).json()
    client.post('/cv/consent', json={'digest': '0' * 64, 'affirmative': True}, headers=h)     # wrong digest
    assert client.post('/cv/parse', headers=key_headers(h)).status_code == 409
    client.post('/cv/consent', json={'digest': up['digest'], 'affirmative': True}, headers=h)
    assert (search(client, h).status_code, search(client, h).json()['detail']) == (409, 'parse_required')
    assert analyze(client, h).status_code == 409
    parse(client, h)
    assert (analyze(client, h).status_code, analyze(client, h).json()['detail']) == (409, 'search_required')
    search(client, h)
    assert analyze(client, h, 'NOT_IN_RESULTS').status_code == 404
    assert len(f.provider_calls) == 2                             # the parse and the search only


def test_an_edit_invalidates_consent_parse_search_and_upload_runs(tmp_path):
    client, f, deps = make(tmp_path)
    h = session(client)
    upload_and_consent(client, h)
    run_id = client.post('/cv/parse', headers=key_headers(h)).json()['run_id']
    assert wait(client, h, run_id)['status'] == 'done'
    search(client, h)
    analysis = analyze(client, h, 'P1').json()['run_id']
    wait(client, h, analysis)
    client.post('/cv/preview', json={'text': CV_TEXT + '\nAirflow'}, headers=h)
    assert client.post('/cv/parse', headers=key_headers(h)).json()['detail'] == 'consent_required'
    assert search(client, h).status_code == 409
    # runs derived from the earlier CV are dropped with it
    assert client.get(f'/recommendations/{run_id}', headers=h).status_code == 404
    assert client.get(f'/recommendations/{analysis}', headers=h).status_code == 404


def test_delete_clears_every_cv_derived_state(tmp_path):
    client, f, deps = make(tmp_path)
    h = session(client)
    upload_and_consent(client, h)
    run_id = client.post('/cv/parse', headers=key_headers(h)).json()['run_id']
    wait(client, h, run_id)
    client.delete('/session', headers=h)
    assert client.get(f'/recommendations/{run_id}', headers=h).status_code == 401
    assert not deps.store.exists(h['X-Session-Id'])


# --- public path: the durable ticket opens the session allowance -------------------------------------------

def test_the_public_flow_counts_one_parse_one_search_and_three_analyses(tmp_path):
    client, f, _ = make(tmp_path, public=True)
    h = session(client)
    upload_and_consent(client, h)
    assert parse(client, h, owner=False)['status'] == 'done'
    assert len(f.tickets) == 1
    assert client.post('/cv/parse', headers=key_headers(h, owner=False)).json()['detail'] == 'allowance_exhausted'
    assert search(client, h, owner=False).status_code == 200
    assert search(client, h, owner=False).json()['detail'] == 'allowance_exhausted'
    for job in ('P1', 'P2', 'P3'):
        assert wait(client, h, analyze(client, h, job, owner=False).json()['run_id'])['status'] == 'done'
    fourth = analyze(client, h, 'P1', owner=False)
    assert (fourth.status_code, fourth.json()['detail']) == (429, 'allowance_exhausted')
    assert len(f.tickets) == 1 and len(f.provider_calls) == 5


@pytest.mark.parametrize('outcome', ['refused', 'unavailable', 'unknown'])
def test_an_unproven_ticket_makes_no_provider_call_and_no_allowance(tmp_path, outcome):
    client, f, _ = make(tmp_path, public=True, ticket=outcome)
    h = session(client)
    upload_and_consent(client, h)
    body = parse(client, h, owner=False)
    assert body['status'] == 'failed' and body['error'] == QUOTA_FATAL[outcome]
    assert f.provider_calls == [] and client.app.state.beta_allowances.remaining(h['X-Session-Id']) is None


def test_the_same_key_for_the_same_parse_returns_its_run_and_another_action_is_refused(tmp_path):
    client, f, _ = make(tmp_path)
    h = session(client)
    upload_and_consent(client, h)
    key = str(uuid.uuid4())
    first = client.post('/cv/parse', headers=key_headers(h, key=key)).json()
    wait(client, h, first['run_id'])
    assert client.post('/cv/parse', headers=key_headers(h, key=key)).json() == {**first, 'duplicate': True}
    assert search(client, h, key=key).status_code == 409                    # another phase and action
    assert len(f.provider_calls) == 1


# --- upload abuse limits (before any body is read) ---------------------------------------------------------

def test_one_upload_in_flight_per_process(tmp_path, monkeypatch):
    client, f, _ = make(tmp_path)
    gate, started = threading.Event(), threading.Event()
    real = upload_guard.bounded_extract

    def slow(data, ext, **kw):
        started.set()
        gate.wait(10)
        return real(data, ext, **kw)
    monkeypatch.setattr(upload_guard, 'bounded_extract', slow)
    h1, h2 = session(client), session(client, ip='203.0.113.8')
    out = {}
    t = threading.Thread(target=lambda: out.setdefault('a', client.post(
        '/cv/upload', files={'file': ('cv.txt', CV_TEXT.encode())}, headers=h1)))
    t.start()
    assert started.wait(10)
    second = client.post('/cv/upload', files={'file': ('cv.txt', CV_TEXT.encode())}, headers=h2)
    assert second.status_code == 503 and second.json()['code'] == 'upload_busy'
    gate.set()
    t.join(10)
    assert out['a'].status_code == 200
    assert client.post('/cv/upload', files={'file': ('cv.txt', CV_TEXT.encode())}, headers=h2).status_code == 200


def test_previews_per_session_and_uploads_per_ip_are_limited(tmp_path):
    client, f, _ = make(tmp_path)
    h = session(client)
    for _ in range(5):
        assert client.post('/cv/upload', files={'file': ('cv.txt', CV_TEXT.encode())}, headers=h).status_code == 200
    sixth = client.post('/cv/upload', files={'file': ('cv.txt', CV_TEXT.encode())}, headers=h)
    assert sixth.status_code == 429 and sixth.json()['code'] == 'upload_rate_limited'
    edit = client.post('/cv/preview', json={'text': CV_TEXT}, headers=h)
    assert edit.status_code == 429 and edit.json()['code'] == 'upload_rate_limited'
    ok = 0
    for i in range(3):                                    # the same IP in fresh sessions: 10 per hour in total
        s = session(client)
        for _ in range(4):
            r = client.post('/cv/upload', files={'file': ('cv.txt', CV_TEXT.encode())}, headers=s)
            ok += r.status_code == 200
    assert ok == 5                                        # 5 earlier uploads + 5 here = 10 for this IP


# --- privacy -----------------------------------------------------------------------------------------------

def test_no_cv_text_in_logs_or_error_bodies(tmp_path, caplog):
    import logging
    client, f, _ = make(tmp_path)
    h = session(client)
    with caplog.at_level(logging.DEBUG):
        upload_and_consent(client, h)
        parse(client, h)
        r = search(client, h, work_mode='remote')
        bad = analyze(client, h, 'NOT_IN_RESULTS')
    assert CANARY not in caplog.text and CANARY not in bad.text and CANARY not in json.dumps(r.json())


# --- search idempotency: the action is the CV plus every normalized filter; retries replay their own result --

BASE = {'role_family': 'data_science', 'country_code': 'ID', 'city': 'Medan', 'work_mode': 'remote',
        'posted_within_days': 30, 'include_unknown': True}


def handle_of(h):
    from jobfit.session.store import SessionHandle
    return SessionHandle(h['X-Session-Id'], h['X-Session-Token'])


def parsed_session(client, owner=True):
    h = session(client)
    upload_and_consent(client, h)
    assert parse(client, h, owner=owner)['status'] == 'done'
    return h


def test_the_same_key_and_filters_replay_the_original_results_without_a_call(tmp_path):
    client, f, _ = make(tmp_path)
    h, key = parsed_session(client), str(uuid.uuid4())
    first = search(client, h, key=key, **BASE)
    calls = len(f.provider_calls)
    again = search(client, h, key=key, **BASE)
    assert first.status_code == again.status_code == 200 and again.json() == first.json()
    assert len(f.provider_calls) == calls


@pytest.mark.parametrize('field,value', [('role_family', 'genai_llm'), ('country_code', 'SG'), ('city', 'Jakarta'),
                                         ('work_mode', 'hybrid'), ('posted_within_days', 7),
                                         ('include_unknown', False)])
def test_the_same_key_with_any_changed_filter_is_refused_without_a_call_ticket_or_allowance(tmp_path, field, value):
    client, f, _ = make(tmp_path, public=True)
    h, key = parsed_session(client, owner=False), str(uuid.uuid4())
    assert search(client, h, owner=False, key=key, **BASE).status_code == 200
    calls, tickets = len(f.provider_calls), len(f.tickets)
    remaining = client.app.state.beta_allowances.remaining(h['X-Session-Id'])
    r = search(client, h, owner=False, key=key, **{**BASE, field: value})
    assert (r.status_code, r.json()['detail']) == (409, 'idempotency_key_mismatch')
    assert len(f.provider_calls) == calls and len(f.tickets) == tickets
    assert client.app.state.beta_allowances.remaining(h['X-Session-Id']) == remaining


@pytest.mark.parametrize('first,retry', [({'country_code': 'id'}, {'country_code': 'ID'}),
                                         ({'city': ' Medan '}, {'city': 'medan'})])
def test_equivalent_filters_after_normalization_replay_the_original_result(tmp_path, first, retry):
    client, f, _ = make(tmp_path, public=True)
    h, key = parsed_session(client, owner=False), str(uuid.uuid4())
    original = search(client, h, owner=False, key=key, **{**BASE, **first})
    assert original.status_code == 200
    calls, tickets = len(f.provider_calls), len(f.tickets)
    remaining = client.app.state.beta_allowances.remaining(h['X-Session-Id'])
    again = search(client, h, owner=False, key=key, **{**BASE, **retry})
    assert again.status_code == 200 and again.json() == original.json()
    assert len(f.provider_calls) == calls and len(f.tickets) == tickets
    assert client.app.state.beta_allowances.remaining(h['X-Session-Id']) == remaining


def test_a_retry_returns_its_own_search_not_the_latest_one(tmp_path):
    client, f, deps = make(tmp_path)
    h = parsed_session(client)
    k1, k2 = str(uuid.uuid4()), str(uuid.uuid4())
    a = search(client, h, key=k1).json()['jobs']
    b = search(client, h, key=k2, work_mode='remote').json()['jobs']
    assert [j['job_id'] for j in a] != [j['job_id'] for j in b]
    calls = len(f.provider_calls)
    assert search(client, h, key=k1).json()['jobs'] == a                  # K1 replays A, not the later B
    assert len(f.provider_calls) == calls
    handle = handle_of(h)
    lease = deps.store.consented_lease(handle)
    assert [r['job_id'] for r in deps.store.read(handle, lease, SEARCH_KEY)] == [j['job_id'] for j in b]


def test_an_edit_clears_the_current_and_the_per_operation_search_results(tmp_path):
    client, f, deps = make(tmp_path)
    h, key = parsed_session(client), str(uuid.uuid4())
    search(client, h, key=key)
    client.post('/cv/preview', json={'text': CV_TEXT + '\nAirflow'}, headers=h)
    assert search(client, h, key=key).json()['detail'] == 'consent_required'
    handle = handle_of(h)
    text, digest = deps.store.preview(handle)
    client.post('/cv/consent', json={'digest': digest, 'affirmative': True}, headers=h)
    lease = deps.store.consented_lease(handle)
    from jobfit.live.keys import operation_key
    for k in (SEARCH_KEY, search_result_key(operation_key(key))):
        with pytest.raises(KeyError):
            deps.store.read(handle, lease, k)
    assert search(client, h, key=key).status_code == 409                  # parse required again, no replay
