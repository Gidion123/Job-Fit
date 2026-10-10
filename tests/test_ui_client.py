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


def page_text(at) -> str:
    """The HTML content blocks of the page (st.html), without the stylesheet and the scroll script."""
    return '\n'.join(str(h.value) for h in at.get('html') if not str(h.value).startswith(('<style>', '<script>')))


def open_demo(at):
    at.button(key='cta_demo').click().run()
    assert not at.exception and at.session_state['page'] == 'demo'


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
    assert at.button(key='jf_brand').label == 'JobFit'
    open_demo(at)
    assert at.selectbox(key='demo_cv').value == 'CV1'
    at.button(key='demo_run').click().run()   # saved demo is the default; none is saved in this fake
    assert 'No saved demo' in page_text(at)
    at.toggle(key='demo_live').set_value(True).run()
    at.button(key='demo_run').click().run()
    assert not at.exception
    assert 'Cocok (1)' in page_text(at)


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
    assert 'belum bisa dihubungi' in page_text(at)                 # a clear message, never a traceback
    assert at.button(key='api_retry')


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
    open_demo(at)
    at.button(key='demo_run').click().run()
    assert not at.exception
    text = page_text(at)
    assert 'kandidat dari pencarian dianalisis' in text
    assert 'Cocok (' in text
    assert 'Demo dengan hasil tersimpan' in text
    at.button(key='demo_suggest').click().run()
    assert not at.exception
    assert any('Never add a skill' in c.value for c in at.caption)
    at.button(key='demo_market').click().run()
    assert not at.exception and at.session_state['page'] == 'market'
    assert 'lowongan yang bisa dicari' in page_text(at)
    at.button(key='lang_en').click().run()
    assert 'searchable postings' in page_text(at)


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


# --- correction B: a pending live-action key survives a lost response --------------------------------------

from live_action import LiveActions, action_fingerprint  # noqa: E402


class LoseFirstLivePost:
    """Forwards every request to the real app; the first live POST is processed, then its response is lost."""

    def __init__(self, client):
        self.client, self.lost = client, False

    def post(self, *a, **kw):
        return self.client.post(*a, **kw)

    def get(self, *a, **kw):
        return self.client.get(*a, **kw)

    def request(self, method, path, **kw):
        response = self.client.request(method, path, **kw)
        if method == 'POST' and path == '/recommendations' and not self.lost:
            self.lost = True
            import httpx
            raise httpx.ReadError('response lost after the server accepted the request')
        return response


def wait_done(api, run_id):
    for _ in range(300):
        if api.poll(run_id)['status'] != 'running':
            return
        time.sleep(0.01)


def test_a_retry_after_a_lost_response_reuses_the_key_and_runs_once(monkeypatch):
    import httpx
    from tests.test_live_api import OWNER, TOKEN, make as make_prod
    test_client, calls = make_prod()
    monkeypatch.setenv('JOBFIT_INTERNAL_TOKEN', TOKEN)
    api = ApiClient(http=LoseFirstLivePost(test_client))
    api.start_session()
    api.headers['X-JobFit-Owner-Token'] = OWNER
    actions = LiveActions()
    fp = action_fingerprint('CV1', True, {'country_code': 'ID'})
    first_key = actions.key_for(fp)
    with pytest.raises(httpx.ReadError):
        api.start_run('CV1', True, {'country_code': 'ID'}, mode='live', action_key=first_key)
    retry_key = actions.key_for(action_fingerprint('CV1', True, {'country_code': ' ID '}))   # same action
    assert retry_key == first_key
    run_id = api.start_run('CV1', True, {'country_code': 'ID'}, mode='live', action_key=retry_key)
    wait_done(api, run_id)
    actions.acknowledged(run_id)
    assert len(calls) == 1 and calls[0].operation_key == 'idem:' + first_key and calls[0].run_id == run_id
    new_key = actions.key_for(fp)                                   # a genuinely new action
    assert new_key != first_key
    wait_done(api, api.start_run('CV1', True, {'country_code': 'ID'}, mode='live', action_key=new_key))
    assert len(calls) == 2 and calls[1].operation_key == 'idem:' + new_key


def test_fingerprints_are_canonical_and_identity_changes_make_a_new_action():
    base = action_fingerprint('CV1', True, {'country_code': 'ID', 'work_mode': 'remote', 'include_unknown': True})
    assert base == action_fingerprint('CV1', 1, {'work_mode': ' remote ', 'country_code': 'ID'})
    assert action_fingerprint('CV1', True, None) == action_fingerprint('CV1', True, {'city': '', 'include_unknown': None})
    for other in (action_fingerprint('CV2', True, {'country_code': 'ID', 'work_mode': 'remote'}),
                  action_fingerprint('CV1', False, {'country_code': 'ID', 'work_mode': 'remote'}),
                  action_fingerprint('CV1', True, {'country_code': 'SG', 'work_mode': 'remote'})):
        assert other != base
    actions = LiveActions()
    pending = actions.key_for(base)
    assert actions.key_for(action_fingerprint('CV2', True, None)) != pending      # changed while pending


def test_the_action_state_never_holds_cv_content():
    from tests.test_api import CV
    actions = LiveActions()
    fp = action_fingerprint(CV.profile.cv_id, True, {'country_code': 'ID'})
    actions.key_for(fp)
    assert len(fp) == 64 and all(c in '0123456789abcdef' for c in fp)
    stored = repr(vars(actions)) + fp
    assert CV.profile.raw_text not in stored and 'Python and SQL' not in stored


def test_streamlit_reuses_the_pending_key_until_the_server_acknowledges(monkeypatch):
    import httpx
    from streamlit.testing.v1 import AppTest
    test_client, _ = make()
    keys = []

    class Flaky(ApiClient):
        def __init__(self):
            super().__init__(http=test_client)

        def start_run(self, cv_id, seniority_rule, filters=None, mode='saved', action_key=None):
            if mode == 'live':
                keys.append(action_key)
                if len(keys) == 1:
                    super().start_run(cv_id, seniority_rule, filters, mode, action_key)
                    raise httpx.ReadError('response lost')
            return super().start_run(cv_id, seniority_rule, filters, mode, action_key)
    fake_module = types.ModuleType('api_client')
    fake_module.ApiClient, fake_module.ApiError = Flaky, ApiError
    monkeypatch.setitem(sys.modules, 'api_client', fake_module)
    at = AppTest.from_file(str(ROOT / 'ui/streamlit_app.py'), default_timeout=20).run()
    open_demo(at)
    at.toggle(key='demo_live').set_value(True).run()
    find = lambda: at.button(key='demo_run')  # noqa: E731
    find().click().run()
    assert 'Koneksi bermasalah' in page_text(at)
    find().click().run()                     # the retry of the same action
    assert not at.exception and keys[1] == keys[0]
    find().click().run()                     # acknowledged: a new click is a new action
    assert len(keys) == 3 and keys[2] != keys[0]
