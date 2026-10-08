"""API privacy acceptance tests mapped to privacy-threat-model.md PR-01..PR-09 (synthetic only).

Scope: the FastAPI layer with a fake run. PR-08 (provider endpoint policy) and PR-10
(paired quality before/after masking) need provider calls and are not covered here.
A pass covers this measured scope only, not a deployed host.
"""
from datetime import date
import logging
import os
import tempfile
import threading
import time
from pathlib import Path

from fastapi.testclient import TestClient

from jobfit.api.main import AppDeps, create_app
from jobfit.cv.parser import ParsedCV
from jobfit.schemas.cv import CVProfile
from jobfit.session.store import SessionStore
from tests.test_api import fake_rec, wait

ROOT = Path(__file__).resolve().parents[1]
CV = ParsedCV(profile=CVProfile(cv_id='CV1', raw_text='Python and SQL.'), analysis_date=date(2026, 9, 30))
CANARY = 'CANARY-7Q4Z'
UPLOAD = (f'Sari Contoh {CANARY}\nsari.contoh@example.com | +62 812-3456-7890 | linkedin.com/in/sari-contoh\n'
          'Pengalaman\nData Analyst, PT Contoh, 2025 - sekarang\nPython, SQL').encode()


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def app(run=fake_rec, store=None, **kw):
    calls = []

    def spy(*a, **k):
        calls.append(1)
        return run(*a, **k)
    kw.setdefault('live_enabled', True)
    deps = AppDeps(store=store or SessionStore(), demo_cvs={'CV1': CV}, run=spy, sweep_seconds=None, **kw)
    return TestClient(create_app(deps)), deps, calls


def session(client):
    s = client.post('/session').json()
    return {'X-Session-Id': s['session_id'], 'X-Session-Token': s['token']}


def test_pr01_direct_identifiers_masked_and_name_limit_disclosed():
    client, _, _ = app()
    up = client.post('/cv/upload', files={'file': ('cv.txt', UPLOAD)}, headers=session(client)).json()
    text = up['masked_text']
    for raw in ('sari.contoh@example.com', '812-3456-7890', 'linkedin.com/in/sari-contoh'):
        assert raw not in text
    assert {'email', 'phone', 'profile'} <= set(up['masked_counts'])
    assert 'Python, SQL' in text and '2025 - sekarang' in text          # professional evidence kept
    assert any('may miss identifiers' in w for w in up['warnings'])       # names need reviewed hints


def test_pr02_upload_and_consent_never_start_a_provider_run():
    client, _, calls = app()
    h = session(client)
    up = client.post('/cv/upload', files={'file': ('cv.txt', UPLOAD)}, headers=h).json()
    client.post('/cv/consent', json={'digest': up['digest'], 'affirmative': True}, headers=h)
    client.post('/cv/consent', json={'digest': up['digest'], 'affirmative': False}, headers=h)
    assert calls == [] and up['provider_processing'] == 'disabled'


def test_pr03_sessions_are_isolated():
    client, _, _ = app()
    a, b = session(client), session(client)
    run_id = client.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'live'}, headers=a).json()['run_id']
    wait(client, a, run_id)
    assert client.get(f'/recommendations/{run_id}', headers=b).status_code == 404
    swapped = {'X-Session-Id': a['X-Session-Id'], 'X-Session-Token': b['X-Session-Token']}
    assert client.get(f'/recommendations/{run_id}', headers=swapped).status_code == 401
    assert client.delete('/session', headers=swapped).status_code == 401
    assert client.get(f'/recommendations/{run_id}', headers=a).status_code == 200   # a still intact


def test_pr04_delete_during_work_invalidates_and_drops_late_results():
    gate = threading.Event()

    def slow(cv, sen, on_result, filters=None):
        gate.wait(5)
        return fake_rec(cv, sen, on_result)
    client, deps, _ = app(slow)
    h = session(client)
    run_id = client.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'live'}, headers=h).json()['run_id']
    client.delete('/session', headers=h)
    assert not deps.store.exists(h['X-Session-Id'])
    gate.set()
    time.sleep(0.05)
    assert client.get(f'/recommendations/{run_id}', headers=h).status_code == 401
    assert not deps.store.exists(h['X-Session-Id'])                        # no recreation


def test_pr05_disconnect_expiry_with_fake_clock_and_sweeper():
    clock = Clock()
    store = SessionStore(clock=clock, disconnect_seconds=120, idle_seconds=1800, absolute_seconds=7200)
    client, deps, _ = app(store=store)
    deps.sweep_seconds = 0.02
    with TestClient(create_app(deps)) as live:
        h = session(live)
        live.post('/session/heartbeat', headers=h)
        clock.now += 119
        assert live.get('/demo/cvs', headers=h).status_code == 200      # heartbeat via request
        clock.now += 121
        time.sleep(0.1)                                                  # sweeper runs
        assert not store.exists(h['X-Session-Id'])
        assert live.get('/demo/cvs', headers=h).status_code == 401


def test_pr06_oversized_and_malformed_uploads_rejected_without_temp_residue():
    client, _, calls = app()
    h = session(client)
    tmp = Path(tempfile.gettempdir())
    before = set(os.listdir(tmp))
    big = client.post('/cv/upload', files={'file': ('cv.txt', b'a' * (10 * 1024 * 1024 + 1))}, headers=h)
    bad_pdf = client.post('/cv/upload', files={'file': ('cv.pdf', b'%PDF-1.4 broken')}, headers=h)
    exe = client.post('/cv/upload', files={'file': ('cv.exe', b'MZ')}, headers=h)
    # upload hardening (CP3): stable codes; 413 above the raw request cap, 415 for an unsupported type
    assert (big.status_code, big.json()['code']) == (413, 'upload_too_large')
    assert (bad_pdf.status_code, bad_pdf.json()['code']) == (422, 'document_unreadable')
    assert (exe.status_code, exe.json()['code']) == (415, 'unsupported_type')
    assert set(os.listdir(tmp)) - before == set() and calls == []


def test_pr07_no_cv_text_in_logs_or_error_bodies(caplog):
    client, _, _ = app()
    h = session(client)
    with caplog.at_level(logging.DEBUG):
        up = client.post('/cv/upload', files={'file': ('cv.txt', UPLOAD)}, headers=h)
        client.post('/cv/consent', json={'digest': '0' * 64, 'affirmative': True}, headers=h)
        err = client.post('/cv/upload', files={'file': ('cv.exe', UPLOAD)}, headers=h)
    assert CANARY not in caplog.text and 'sari.contoh' not in caplog.text
    assert CANARY not in err.text
    assert up.status_code == 200


def test_pr09_ui_never_renders_raw_html():
    for path in (ROOT / 'ui').glob('*.py'):
        assert 'unsafe_allow_html' not in path.read_text(), path.name
