"""UI client against the real FastAPI app (fake run), plus a Streamlit smoke test."""
import sys
import time
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ui'))

from api_client import ApiClient, ApiError  # noqa: E402
from tests.test_api import make  # noqa: E402


def test_client_full_flow_against_app():
    test_client, _ = make()
    api = ApiClient(http=test_client)
    api.start_session()
    assert [c['cv_id'] for c in api.demo_cvs()] == ['CV1']
    run_id = api.start_run('CV1', True, mode='live')
    for _ in range(200):
        body = api.poll(run_id)
        if body['status'] != 'running':
            break
        time.sleep(0.01)
    assert body['result']['blocks'][0]['groups']['matches'][0]['job_id'] == 'A'
    api.delete_session()
    with pytest.raises(ApiError):
        api.demo_cvs()


def test_streamlit_app_renders_demo_tab(monkeypatch):
    from streamlit.testing.v1 import AppTest
    test_client, _ = make()

    class Fake(ApiClient):
        def __init__(self):
            super().__init__(http=test_client)
    fake_module = types.ModuleType('api_client')
    fake_module.ApiClient, fake_module.ApiError = Fake, ApiError
    monkeypatch.setitem(sys.modules, 'api_client', fake_module)
    at = AppTest.from_file(str(ROOT / 'ui/streamlit_app.py'), default_timeout=20).run()
    assert not at.exception
    assert at.title[0].value == 'JobFit'
    assert at.selectbox[0].value == 'CV1'
    find = lambda: next(b for b in at.button if b.label == "Find matching jobs")
    find().click().run()                      # saved demo is the default; none is saved in this fake
    assert any('No saved demo' in e.value for e in at.error)
    next(t for t in at.toggle if t.label.startswith('Live analysis')).set_value(True).run()
    find().click().run()
    assert not at.exception
    assert any('Matches (1)' in s.value for s in at.subheader)


def test_streamlit_shows_message_when_api_is_down(monkeypatch):
    import httpx
    from streamlit.testing.v1 import AppTest

    class Down(ApiClient):
        def __init__(self):
            super().__init__(http=httpx.Client(base_url='http://api.invalid:1', timeout=0.5))
    fake_module = types.ModuleType('api_client')
    fake_module.ApiClient, fake_module.ApiError = Down, ApiError
    monkeypatch.setitem(sys.modules, 'api_client', fake_module)
    at = AppTest.from_file(str(ROOT / 'ui/streamlit_app.py'), default_timeout=20).run()
    assert not at.exception
    assert any('Cannot reach the JobFit API' in e.value for e in at.error)


def test_streamlit_full_saved_demo_flow_against_real_wiring(monkeypatch):
    """Real API wiring with live analysis off: saved demo, suggestions, market, summary."""
    from fastapi.testclient import TestClient
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv('JOBFIT_LIVE_ENABLED', '0')
    from jobfit.api.wiring import create_default_app
    test_client = TestClient(create_default_app())

    class Real(ApiClient):
        def __init__(self):
            super().__init__(http=test_client)
    fake_module = types.ModuleType('api_client')
    fake_module.ApiClient, fake_module.ApiError = Real, ApiError
    monkeypatch.setitem(sys.modules, 'api_client', fake_module)
    at = AppTest.from_file(str(ROOT / 'ui/streamlit_app.py'), default_timeout=30).run()
    assert not at.exception
    next(b for b in at.button if b.label == 'Find matching jobs').click().run()
    assert not at.exception
    assert any('candidates from the search were analyzed' in m.value for m in at.markdown)
    assert any(s.value.startswith('Matches (') for s in at.subheader)
    assert any('Demo with saved results' in i.value for i in at.info)
    next(b for b in at.button if b.label == 'Show suggestions from these results').click().run()
    assert not at.exception
    assert any('Never add a skill' in c.value for c in at.caption)
    assert any('searchable postings' in m.value for m in at.markdown)


def test_client_sends_the_ingress_headers_and_one_key_per_live_action(monkeypatch):
    import uuid as _uuid
    from tests.test_live_api import OWNER, TOKEN, make as make_prod
    test_client, calls = make_prod()
    monkeypatch.setenv('JOBFIT_INTERNAL_TOKEN', TOKEN)
    api = ApiClient(http=test_client)
    api.client_ip = '203.0.113.5'
    api.start_session()
    api.headers['X-JobFit-Owner-Token'] = OWNER      # owner transport is a CP3.3 UI detail
    key = str(_uuid.uuid4())
    first = api.start_run('CV1', True, mode='live', action_key=key)
    assert api.start_run('CV1', True, mode='live', action_key=key) == first      # a retry: same run
    for _ in range(300):
        if api.poll(first)['status'] != 'running':
            break
        time.sleep(0.01)
    assert len(calls) == 1 and calls[0].operation_key == 'idem:' + key
    monkeypatch.delenv('JOBFIT_INTERNAL_TOKEN')
    with pytest.raises(KeyError):            # without the internal token the API answers 401
        ApiClient(http=test_client).start_session()
