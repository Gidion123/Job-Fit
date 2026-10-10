"""API tests with a fake recommendation run. No provider, DB or network."""
from datetime import date
import threading
import time

from fastapi.testclient import TestClient

from jobfit.api.main import AppDeps, REAL_CV_MESSAGE, create_app
from jobfit.cv.parser import ParsedCV
from jobfit.eval.product_order import held_score
from jobfit.recommend.service import JobResult, Recommendation
from jobfit.schemas.analysis import ScoreResult, ScoreStatus, UnitAssessment
from jobfit.schemas.cv import CVProfile
from jobfit.schemas.requirements import JDExtraction
from jobfit.session.store import SessionStore

CV = ParsedCV(profile=CVProfile(cv_id='CV1', raw_text='Python and SQL.'), analysis_date=date(2026, 9, 30))
EXT = JDExtraction.model_validate({'job_id': 'A', 'units': [
    {'unit_id': 'u1', 'text': 'Python', 'importance': 'required', 'field': 'skill_tool', 'source_quotes': ['Python']}]})


def fake_rec(cv, seniority, on_result, filters=None):
    a = JobResult('A', 1, ScoreResult(score_pct=100.0, status=ScoreStatus.FINAL, matched=1, required_total=1),
                  assessments=[UnitAssessment(unit_id='u1', label='MATCH', cv_quotes=['Python and SQL.'])],
                  matcher_model='gpt-6-sol', extraction=EXT)
    b = JobResult('B', 2, held_score('JD extraction not available: not_extracted'),
                  hold_reason='JD extraction not available: not_extracted')
    for r in (b, a):
        on_result(r)
    return Recommendation('CV1', ['A', 'B'], {'A': a, 'B': b}, ['A', 'B'], ['A', 'B'], [],
                          {'seniority_rule': 'seniority-demote-3y-v1' if seniority else None})


def make(run=fake_rec, saved_demo=None):
    deps = AppDeps(store=SessionStore(), demo_cvs={'CV1': CV}, run=run, live_enabled=True,
                   job_meta={'A': {'title': 'Junior DS', 'company': 'X'}}, sweep_seconds=None,
                   saved_demo=saved_demo)
    client = TestClient(create_app(deps))
    s = client.post('/session').json()
    return client, {'X-Session-Id': s['session_id'], 'X-Session-Token': s['token']}


def wait(client, headers, run_id):
    for _ in range(200):
        body = client.get(f'/recommendations/{run_id}', headers=headers).json()
        if body['status'] != 'running':
            return body
        time.sleep(0.01)
    raise AssertionError('run did not finish')


def test_requests_without_valid_session_are_refused():
    client, headers = make()
    assert client.get('/demo/cvs').status_code == 422
    assert client.get('/demo/cvs', headers={**headers, 'X-Session-Token': 'wrong'}).status_code == 401


def test_demo_run_returns_groups_and_progress():
    client, headers = make()
    run_id = client.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'live'}, headers=headers).json()['run_id']
    body = wait(client, headers, run_id)
    assert body['status'] == 'done' and body['progress'] == 2
    assert body['result']['blocks'][0]['title'] == 'Target-role jobs'
    groups = body['result']['blocks'][0]['groups']
    assert [c['job_id'] for c in groups['matches']] == ['A'] and groups['matches'][0]['title'] == 'Junior DS'
    assert groups['matches'][0]['requirements'][0]['requirement'] == 'Python'
    assert [c['job_id'] for c in groups['not_fully_analyzed']] == ['B']
    assert groups['not_fully_analyzed'][0]['score_pct'] is None
    assert 'not a hiring probability' in body['result']['note']


def test_other_session_cannot_read_a_run():
    client, headers = make()
    run_id = client.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'live'}, headers=headers).json()['run_id']
    other = client.post('/session').json()
    h2 = {'X-Session-Id': other['session_id'], 'X-Session-Token': other['token']}
    assert client.get(f'/recommendations/{run_id}', headers=h2).status_code == 404


def test_upload_is_masked_locally_and_real_cv_processing_stays_off():
    client, headers = make()
    text = b'Rina Putri\nrina@example.com +62 812-3456-7890\nExperience\nPython analyst 2025'
    up = client.post('/cv/upload', files={'file': ('cv.txt', text, 'text/plain')}, headers=headers).json()
    assert 'rina@example.com' not in up['masked_text'] and 'Rina Putri' not in up['masked_text']  # header removed
    assert up['masked_text'].startswith('Experience') and up['removed']['header_lines'] == 2
    assert up['provider_processing'] == 'disabled' and up['message'] == REAL_CV_MESSAGE
    ok = client.post('/cv/consent', json={'digest': up['digest'], 'affirmative': True}, headers=headers).json()
    assert ok['provider_processing'] == 'disabled'
    bad = client.post('/cv/consent', json={'digest': '0' * 64, 'affirmative': True}, headers=headers)
    assert bad.status_code == 409


def test_unreadable_upload_fails_before_anything_else():
    client, headers = make()
    r = client.post('/cv/upload', files={'file': ('cv.exe', b'xx', 'application/octet-stream')}, headers=headers)
    assert r.status_code == 415 and r.json()['code'] == 'unsupported_type'    # upload hardening (CP3)


def test_delete_session_drops_late_results():
    gate = threading.Event()

    def slow(cv, seniority, on_result, filters=None):
        gate.wait(5)
        return fake_rec(cv, seniority, on_result)
    client, headers = make(slow)
    run_id = client.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'live'}, headers=headers).json()['run_id']
    assert client.delete('/session', headers=headers).json() == {'deleted': True}
    gate.set()
    time.sleep(0.05)
    assert client.get(f'/recommendations/{run_id}', headers=headers).status_code == 401


def test_one_running_run_per_session():
    gate = threading.Event()

    def slow(cv, seniority, on_result, filters=None):
        gate.wait(5)
        return fake_rec(cv, seniority, on_result)
    client, headers = make(slow)
    assert client.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'live'}, headers=headers).status_code == 200
    assert client.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'live'}, headers=headers).status_code == 429
    gate.set()


def test_failed_run_shows_error_not_a_score():
    def boom(cv, seniority, on_result, filters=None):
        raise RuntimeError('provider down')
    client, headers = make(boom)
    run_id = client.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'live'}, headers=headers).json()['run_id']
    body = wait(client, headers, run_id)
    assert body['status'] == 'failed' and body['error'] == 'RuntimeError' and body['result'] is None


def test_filters_reach_the_run_and_bad_values_are_refused():
    seen = {}

    def capture(cv, seniority, on_result, filters=None):
        seen['filters'] = filters
        return fake_rec(cv, seniority, on_result)
    client, headers = make(capture)
    r = client.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'live', 'country_code': 'ID', 'work_mode': 'remote',
                                               'include_unknown': False}, headers=headers)
    wait(client, headers, r.json()['run_id'])
    f = seen['filters']
    assert (f.country_code, f.work_mode, f.include_unknown) == ('ID', 'remote', False)
    bad = client.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'live', 'posted_within_days': 3}, headers=headers)
    assert bad.status_code == 422


def test_saved_demo_is_default_labeled_and_costs_no_run():
    called = []

    def never(*a, **k):
        called.append(1)
        raise AssertionError('live run must not start')
    saved = {'cv_id': 'CV1', 'blocks': [{'title': 'Target-role jobs', 'groups': {'matches': [], 'conflicts': [],
                                          'not_fully_analyzed': []}}]}
    client, headers = make(never, saved_demo=lambda cv, sen: saved if (cv, sen) == ('CV1', True) else None)
    run_id = client.post('/recommendations', json={'demo_cv_id': 'CV1'}, headers=headers).json()['run_id']
    body = client.get(f'/recommendations/{run_id}', headers=headers).json()
    assert body['status'] == 'done' and body['result']['source'] == 'saved_demo'
    assert body['result']['label'] == 'Demo with saved results' and not called
    off = client.post('/recommendations', json={'demo_cv_id': 'CV1', 'seniority_rule': False}, headers=headers)
    assert off.status_code == 409
    filt = client.post('/recommendations', json={'demo_cv_id': 'CV1', 'country_code': 'ID'}, headers=headers)
    assert filt.status_code == 422


def test_live_result_is_labeled_live():
    client, headers = make()
    run_id = client.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'live'}, headers=headers).json()['run_id']
    assert wait(client, headers, run_id)['result']['source'] == 'live'


def test_live_switched_off_is_refused_before_any_run():
    deps_called = []
    deps = AppDeps(store=SessionStore(), demo_cvs={'CV1': CV}, run=lambda *a, **k: deps_called.append(1),
                   sweep_seconds=None, live_enabled=False)
    c = TestClient(create_app(deps))
    s = c.post('/session').json()
    h = {'X-Session-Id': s['session_id'], 'X-Session-Token': s['token']}
    assert c.get('/health').json()['live_enabled'] is False
    assert c.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'live'}, headers=h).status_code == 503
    assert not deps_called


def test_the_session_analysis_limit_defaults_to_10_and_is_configurable(monkeypatch):
    import pytest as _pytest
    from jobfit.api.main import SESSION_ANALYSIS_LIMIT_ENV
    monkeypatch.delenv(SESSION_ANALYSIS_LIMIT_ENV, raising=False)
    client, _ = make()
    assert client.get('/health').json()['analysis_limit'] == 10
    monkeypatch.setenv(SESSION_ANALYSIS_LIMIT_ENV, '7')
    client, _ = make()
    assert client.get('/health').json()['analysis_limit'] == 7
    monkeypatch.setenv(SESSION_ANALYSIS_LIMIT_ENV, '0')
    with _pytest.raises(ValueError):
        make()
