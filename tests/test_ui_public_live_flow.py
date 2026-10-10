"""The mentor flow without Langfuse: Streamlit UI over the real API app (public beta open, recording fake
providers, no paid call): upload -> masking -> consent -> parse -> Find Jobs with the same extracted CV ->
Analyze Fit -> result."""
import sys
import time
import types
from pathlib import Path

from jobfit.observability.metrics import Telemetry
from jobfit.recommend.real_cv_flow import PARSED_KEY
from tests.test_fail37_api_privacy import CANARY_CV, RAW, SpyFakes
from tests.test_live_api import TOKEN
from tests.test_real_cv_api import make
from tests.test_ui_product_flow import page_text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ui'))
from api_client import ApiClient, ApiError  # noqa: E402


def a_state(at):
    import re
    keys = {k: at.session_state[k] for k in ('parse_run', 'consented_digest', 'cv_ready', 'hold_poll')
            if k in at.session_state}
    errors = re.findall(r'jf-notice[^>]*>(.{0,300})', page_text(at))
    return at.session_state['page'], keys, [e.value for e in at.exception], errors


def settle(at, done, tries=100):
    for _ in range(tries):
        if done(at):
            return
        time.sleep(0.02)
        at.run()
    raise AssertionError(('the UI did not reach the expected state', a_state(at)))


def test_a_mentor_runs_the_live_flow_without_langfuse_and_find_jobs_keeps_the_parsed_cv(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    f = SpyFakes(tmp_path)
    client, _, deps = make(tmp_path / 'app', public=True, telemetry=Telemetry())   # no tracer at all
    deps.real_parse, deps.real_search, deps.analyze_one = f.real_parse, f.real_search, f.analyze_one
    deps.consume_ticket = f.consume_ticket
    monkeypatch.setenv('JOBFIT_INTERNAL_TOKEN', TOKEN)
    monkeypatch.delenv('JOBFIT_OWNER_TOKEN', raising=False)                         # the public UI has none
    import client_ip                                     # the browser IP as Caddy forwards it via the trusted proxy
    monkeypatch.setattr(client_ip, 'client_ip_from', lambda peer, forwarded, trusted: ('203.0.113.9', 'forwarded'))

    class Real(ApiClient):
        def __init__(self):
            super().__init__(http=client)
    fake_module = types.ModuleType('api_client')
    fake_module.ApiClient, fake_module.ApiError = Real, ApiError
    monkeypatch.setitem(sys.modules, 'api_client', fake_module)

    at = AppTest.from_file(str(ROOT / 'ui/streamlit_app.py'), default_timeout=60).run()
    assert not at.exception
    at.button(key='cta_upload').click().run()
    at.file_uploader[0].upload('cv.txt', CANARY_CV.encode(), 'text/plain').run()
    assert not at.exception and at.session_state['page'] == 'privacy'
    assert at.session_state['preview']['provider_processing'] == 'enabled'
    assert 'belum diaktifkan' not in page_text(at)                     # no "real-CV analysis is off" notice
    digest = at.session_state['preview']['digest']
    consent = at.checkbox(key=f'consent_{digest}')
    assert not consent.disabled
    consent.check().run()
    at.button(key='parse_go').click().run()
    settle(at, lambda a: a.session_state['page'] == 'ready' and a.session_state.get('cv_ready'))
    assert not at.exception and len(f.tickets) == 1
    state = deps.store._states[at.session_state['api'].headers['X-Session-Id']]
    parsed = state.data[PARSED_KEY]                                       # the extracted CV stays in the session
    assert parsed.profile.is_synthetic is False

    at.button(key='choose_find').click().run()
    at.button(key='search_submit').click().run()
    settle(at, lambda a: a.session_state['page'] == 'results')
    assert not at.exception
    job = next(b.key.removeprefix('analyze_') for b in at.button if b.key and b.key.startswith('analyze_'))
    at.button(key=f'analyze_{job}').click().run()
    settle(at, lambda a: a.session_state['page'] == 'analysis')
    assert not at.exception
    assert f.analyzed_cvs == [parsed] and state.data[PARSED_KEY] is parsed  # Find Jobs/Analyze use that CV
    text = page_text(at)
    assert not [k for k, v in RAW.items() if v in text]                # no raw canary on any screen
    assert all(not live.owner for live in f.lives) and len(f.tickets) == 1
