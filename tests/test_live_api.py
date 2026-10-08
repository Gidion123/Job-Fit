"""Phase 2B production ingress of the API (D-096, D-101). Fakes only: no provider, DB or network."""
import threading
import time
import uuid

from fastapi.testclient import TestClient

from jobfit.api.main import AppDeps, create_app
from jobfit.live.operation import LiveRefused
from jobfit.live.quota import Ingress, normalize_ip
from jobfit.session.store import SessionStore
from tests.test_api import CV, fake_rec

TOKEN, OWNER, HMAC_KEY = 't' * 40, 'o' * 40, 'h' * 40


def make(run=None, public_live=False, session_limit=10, saved_demo=None, **kw):
    calls = []

    def default_run(cv, seniority, on_result, filters=None, live=None):
        calls.append(live)
        return fake_rec(cv, seniority, on_result, filters)
    ingress = Ingress(TOKEN, OWNER, HMAC_KEY, session_limit=session_limit)
    deps = AppDeps(store=SessionStore(), demo_cvs={'CV1': CV}, run=run or default_run, sweep_seconds=None,
                   live_enabled=True, ingress=ingress, public_live=public_live, saved_demo=saved_demo,
                   analyze_pasted=lambda cv, text: None, **kw)
    return TestClient(create_app(deps)), calls


def session(client, ip='203.0.113.7'):
    r = client.post('/session', headers={'x-jobfit-internal-token': TOKEN, 'x-jobfit-client-ip': ip})
    assert r.status_code == 200, r.text
    s = r.json()
    return {'X-Session-Id': s['session_id'], 'X-Session-Token': s['token'], 'x-jobfit-internal-token': TOKEN,
            'x-jobfit-client-ip': ip}


def live(client, headers, key=None, owner=True):
    h = dict(headers)
    if owner:
        h['x-jobfit-owner-token'] = OWNER
    if key is not False:
        h['Idempotency-Key'] = key or str(uuid.uuid4())
    return client.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'live'}, headers=h)


def wait(client, headers, run_id):
    for _ in range(300):
        body = client.get(f'/recommendations/{run_id}', headers=headers).json()
        if body['status'] != 'running':
            return body
        time.sleep(0.01)
    raise AssertionError('run did not finish')


def test_every_route_but_health_needs_the_internal_token():
    client, _ = make()
    assert client.get('/health').status_code == 200
    assert client.post('/session').status_code == 401
    assert client.post('/session', headers={'x-jobfit-internal-token': 'wrong'}).status_code == 401
    headers = session(client)
    no_token = {k: v for k, v in headers.items() if k != 'x-jobfit-internal-token'}
    assert client.get('/demo/cvs', headers=no_token).status_code == 401
    assert client.get('/demo/cvs', headers=headers).status_code == 200


def test_live_defaults_to_off_in_app_deps():
    assert AppDeps(store=SessionStore(), demo_cvs={}, run=lambda *a: None).live_enabled is False


def test_session_creation_is_rate_limited_per_ip_pseudonym():
    client, _ = make(session_limit=2)
    session(client, '198.51.100.1')
    session(client, '198.51.100.1')
    r = client.post('/session', headers={'x-jobfit-internal-token': TOKEN, 'x-jobfit-client-ip': '198.51.100.1'})
    assert r.status_code == 429
    session(client, '198.51.100.2')                    # another IP is unaffected


def test_ip_pseudonyms_are_hmacs_with_ipv6_reduced_to_its_64():
    ingress = Ingress(TOKEN, OWNER, HMAC_KEY)
    a = ingress.ip_pseudonym('2001:db8:1:2:aaaa::1')
    assert a == ingress.ip_pseudonym('2001:db8:1:2:ffff::9') != ingress.ip_pseudonym('2001:db8:1:3::1')
    assert len(a) == 64 and '2001' not in a
    assert normalize_ip('::ffff:192.0.2.1') == '192.0.2.1' and normalize_ip('not an ip') is None
    assert Ingress(TOKEN).ip_pseudonym('192.0.2.1') is None          # no HMAC key, no pseudonym


def test_owner_and_internal_tokens_are_compared_safely():
    ingress = Ingress(TOKEN, None, HMAC_KEY)
    assert not ingress.is_owner(None) and not ingress.is_owner('') and not ingress.is_owner(OWNER)
    assert Ingress(TOKEN, OWNER).is_owner(OWNER) and not Ingress(TOKEN, OWNER).is_owner(OWNER[:-1])


def test_non_owner_live_is_refused_while_public_live_is_off():
    client, calls = make()
    headers = session(client)
    assert live(client, headers, owner=False).status_code == 503
    assert calls == []


def test_public_non_owner_recommendation_needs_the_parse_ticket():
    client, calls = make(public_live=True)
    r = live(client, session(client), owner=False)
    assert r.status_code == 403 and r.json()['detail'] == 'ticket_required' and calls == []


def test_owner_live_needs_a_canonical_idempotency_key():
    client, calls = make()
    headers = session(client)
    assert live(client, headers, key=False).status_code == 422
    assert live(client, headers, key='not-a-uuid').status_code == 422
    assert live(client, headers, key=str(uuid.uuid4()).upper()).status_code == 422
    assert calls == []


def test_a_retried_action_gets_the_same_run_and_never_runs_twice():
    gate = threading.Event()
    seen = []

    def slow_run(cv, seniority, on_result, filters=None, live=None):
        seen.append(live)
        assert gate.wait(10)
        return fake_rec(cv, seniority, on_result, filters)
    client, _ = make(run=slow_run)
    headers = session(client)
    key = str(uuid.uuid4())
    first = live(client, headers, key).json()['run_id']
    again = live(client, headers, key).json()                      # while running
    assert again == {'run_id': first, 'duplicate': True}
    gate.set()
    assert wait(client, headers, first)['status'] == 'done'
    assert live(client, headers, key).json()['run_id'] == first     # after completion / lost response
    assert len(seen) == 1
    req = seen[0]
    assert req.operation_key == 'idem:' + key and req.owner and req.run_id == first
    assert req.ip_pseudonym and '203.0.113.7' not in req.ip_pseudonym


def test_the_same_key_from_another_session_is_refused():
    client, calls = make()
    key = str(uuid.uuid4())
    a, b = session(client), session(client, '192.0.2.9')
    run_id = live(client, a, key).json()['run_id']
    r = live(client, b, key)
    assert r.status_code == 409 and r.json()['detail'] == 'idempotency_key_mismatch'
    wait(client, a, run_id)
    assert len(calls) == 1


def test_a_refused_operation_shows_its_safe_code():
    def refused(cv, seniority, on_result, filters=None, live=None):
        raise LiveRefused('budget')
    client, _ = make(run=refused)
    headers = session(client)
    body = wait(client, headers, live(client, headers).json()['run_id'])
    assert body['status'] == 'failed' and body['error'] == 'budget' and body['result'] is None


def test_an_unknown_admission_lets_the_same_key_retry_through_the_database_key():
    attempts = []

    def flaky(cv, seniority, on_result, filters=None, live=None):
        attempts.append(live.operation_key)
        if len(attempts) == 1:
            raise LiveRefused('admission_outcome_unknown')
        raise LiveRefused('duplicate_operation')           # the runner found the committed row
    client, _ = make(run=flaky)
    headers = session(client)
    key = str(uuid.uuid4())
    first = live(client, headers, key).json()['run_id']
    assert wait(client, headers, first)['error'] == 'admission_outcome_unknown'
    second = live(client, headers, key).json()['run_id']
    assert second != first and wait(client, headers, second)['error'] == 'duplicate_operation'
    assert attempts == ['idem:' + key] * 2


def test_pasted_jd_analysis_stays_closed_in_production():
    client, _ = make()
    headers = session(client)
    paste_id = client.post('/jobs/paste', json={'jd_text': 'Python developer with SQL and cloud data pipelines. ' * 5}, headers=headers).json()['paste_id']
    r = client.post('/analyze', json={'paste_id': paste_id, 'demo_cv_id': 'CV1'}, headers=headers)
    assert r.status_code == 503


def test_the_saved_demo_still_works_without_any_live_operation():
    client, calls = make(saved_demo=lambda cv, seniority: {'blocks': [], 'note': 'saved'})
    headers = session(client)
    r = client.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'saved'}, headers=headers)
    assert r.status_code == 200 and calls == []


# --- production wiring: every live operation goes through the Phase 2B runtime ---------------------------

def prod_env(tmp_path, monkeypatch, live='1'):
    env = {'JOBFIT_ENV': 'prod', 'JOBFIT_LIVE_ENABLED': live, 'JOBFIT_PUBLIC_LIVE': '0',
           'DATABASE_URL': 'postgresql://nobody@127.0.0.1:1/none', 'JOBFIT_INTERNAL_TOKEN': TOKEN,
           'OPENROUTER_API_KEY': 'k' * 40, 'JOBFIT_OWNER_TOKEN': OWNER,
           'JOBFIT_USAGE_LEDGER': str(tmp_path / 'prod_ledger.jsonl'), 'JOBFIT_DAILY_BUDGET_USD': '2',
           'API_BUDGET_USD': '5', 'API_HARD_STOP_USD': '4.5'}
    for k, v in env.items():
        monkeypatch.setenv(k, v)


def test_prod_wiring_is_dark_and_has_no_development_fallback(tmp_path, monkeypatch):
    import pytest
    from jobfit.api import wiring
    prod_env(tmp_path, monkeypatch)
    deps = wiring.build_deps()
    assert deps.live_enabled and deps.ingress is not None and not deps.public_live
    assert deps.analyze_pasted is None                              # /analyze closed in production
    with pytest.raises(wiring.LiveUnavailable):                      # never the development client
        deps.run(deps.demo_cvs['CV1'], True, lambda r: None, None)


def test_prod_runtime_uses_the_production_client_settings(tmp_path, monkeypatch):
    from jobfit.api import wiring
    from jobfit.config import get_production_settings
    prod_env(tmp_path, monkeypatch)
    settings = get_production_settings()
    runtime = wiring.build_runtime(settings)          # startup reconciliation fails closed without a database
    client = runtime.client_factory('idem:x')
    assert client.settings.usage_ledger == settings.usage_ledger and client.run_id == 'idem:x'
    assert client.settings.api_hard_stop_usd == 4.5 and runtime.windows['parse'].window == 720.0
    assert runtime.bound['recommendation'] > settings.daily_budget_usd > runtime.bound['parse']
