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
    import jobfit.config
    monkeypatch.setattr(jobfit.config, 'PROD_LEDGER_ROOT', tmp_path.resolve())   # tmp_path stands in for the root
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
    assert deps.maintenance is not None                             # hourly 48 h quota purge
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
    from jobfit.live.runtime_client import PublicBetaRuntimeClient
    assert isinstance(client, PublicBetaRuntimeClient)           # every live request carries deny + ZDR
    assert client.settings.api_hard_stop_usd == 4.5 and runtime.windows['parse'].window == 720.0
    # D-103: the production runtime admits the public-beta phases only, never the legacy 10-job phase
    assert runtime.beta and set(runtime.bound) == {'parse', 'search', 'job_analysis'}
    assert runtime.bound['parse'] < settings.daily_budget_usd


# --- retention maintenance from the sweeper ----------------------------------------------------------------

def test_a_failing_maintenance_purge_never_stops_the_session_sweeper():
    class CountingStore(SessionStore):
        sweeps = 0

        def sweep(self):
            CountingStore.sweeps += 1
            return super().sweep()
    calls = []

    def maintenance():
        calls.append(time.monotonic())
        if len(calls) == 1:
            raise RuntimeError('database down')          # first purge fails
    deps = AppDeps(store=CountingStore(), demo_cvs={'CV1': CV}, run=fake_rec, sweep_seconds=0.02,
                   maintenance=maintenance, maintenance_seconds=0.05)
    with TestClient(create_app(deps)):
        deadline = time.monotonic() + 10
        while len(calls) < 3 and time.monotonic() < deadline:
            time.sleep(0.02)
        sweeps_after_retry = CountingStore.sweeps
        time.sleep(0.1)
        assert len(calls) >= 3                            # failed once, retried, succeeded again
        assert CountingStore.sweeps > sweeps_after_retry  # expiry sweeping still runs
    assert all(b - a >= 0.04 for a, b in zip(calls, calls[1:]))   # at most once per interval


# --- correction D: one recommendation per ticket, consumed only at the first durable intent ---------------

from jobfit.live.quota import SessionAllowances  # noqa: E402

USED, HELD = SessionAllowances.USED, SessionAllowances.TICKET_HELD


def public_app(run):
    client, _ = make(run=run, public_live=True)
    headers = session(client)
    allowances = client.app.state.allowances
    allowances.mark_ticket_held(headers['X-Session-Id'])     # as the Phase 3 parse will after its ticket
    return client, headers, allowances


def billable_run(seen, then=None):
    def run(cv, seniority, on_result, filters=None, live=None):
        seen.append(live)
        assert live.on_first_billable() is True              # the first durable provider intent
        if then:
            raise then
        return fake_rec(cv, seniority, on_result, filters)
    return run


def test_the_first_recommendation_uses_the_ticket_allowance_and_a_second_is_refused():
    seen = []
    client, headers, allowances = public_app(billable_run(seen))
    key = str(uuid.uuid4())
    run_id = live(client, headers, key, owner=False).json()['run_id']
    wait(client, headers, run_id)
    sid = headers['X-Session-Id']
    assert allowances.state(sid) == (USED, 'idem:' + key)
    assert live(client, headers, key, owner=False).json() == {'run_id': run_id, 'duplicate': True}   # same action
    second = live(client, headers, owner=False)
    assert second.status_code == 403 and second.json()['detail'] == 'ticket_required'
    assert len(seen) == 1 and allowances.state(sid) == (USED, 'idem:' + key)


def test_a_retry_while_running_reuses_the_run_without_a_second_allowance():
    gate, seen = threading.Event(), []

    def slow(cv, seniority, on_result, filters=None, live=None):
        seen.append(live)
        assert live.on_first_billable() is True
        assert gate.wait(10)
        return fake_rec(cv, seniority, on_result, filters)
    client, headers, allowances = public_app(slow)
    key = str(uuid.uuid4())
    first = live(client, headers, key, owner=False).json()['run_id']
    assert live(client, headers, key, owner=False).json()['run_id'] == first
    gate.set()
    wait(client, headers, first)
    assert len(seen) == 1 and allowances.state(headers['X-Session-Id']) == (USED, 'idem:' + key)


def test_a_new_session_without_a_ticket_is_refused():
    client, calls = make(public_live=True)
    r = live(client, session(client), owner=False)
    assert r.status_code == 403 and r.json()['detail'] == 'ticket_required' and calls == []


def test_run_limit_refusal_leaves_the_ticket_held_and_frees_the_key():
    client, headers, allowances = public_app(fake_rec_live)
    for _ in range(3):                                         # the session's run limit, filled by owner runs
        wait(client, headers, live(client, headers).json()['run_id'])
    key = str(uuid.uuid4())
    r = live(client, headers, key, owner=False)
    assert r.status_code == 429
    assert allowances.state(headers['X-Session-Id']) == (HELD, None)
    assert live(client, headers, key, owner=False).status_code == 429      # not answered as a duplicate


def fake_rec_live(cv, seniority, on_result, filters=None, live=None):
    return fake_rec(cv, seniority, on_result, filters)


def test_a_synchronous_start_failure_releases_the_allowance_and_the_key(monkeypatch):
    import types as _types
    import jobfit.api.main as api_main
    seen = []
    client, _ = make(run=billable_run(seen), public_live=True)
    client = TestClient(client.app, raise_server_exceptions=False)
    headers = session(client)
    allowances = client.app.state.allowances
    allowances.mark_ticket_held(headers['X-Session-Id'])

    class NoThread:
        def __init__(self, *a, **kw):
            pass

        def start(self):
            raise RuntimeError('cannot start a thread')
    real = api_main.threading
    monkeypatch.setattr(api_main, 'threading', _types.SimpleNamespace(Thread=NoThread, Lock=real.Lock,
                                                                      Event=real.Event))
    key = str(uuid.uuid4())
    assert live(client, headers, key, owner=False).status_code == 500
    assert allowances.state(headers['X-Session-Id']) == (HELD, None) and seen == []
    monkeypatch.setattr(api_main, 'threading', real)
    run_id = live(client, headers, key, owner=False).json()['run_id']        # the same key starts normally
    wait(client, headers, run_id)
    assert len(seen) == 1 and allowances.state(headers['X-Session-Id']) == (USED, 'idem:' + key)


def test_busy_and_budget_refusals_before_any_billable_call_keep_the_ticket():
    for code in ('busy', 'budget'):
        def refused(cv, seniority, on_result, filters=None, live=None, code=code):
            raise LiveRefused(code)                        # refused before the first durable intent
        client, headers, allowances = public_app(refused)
        body = wait(client, headers, live(client, headers, owner=False).json()['run_id'])
        assert body['error'] == code
        assert allowances.state(headers['X-Session-Id']) == (HELD, None)


def test_a_failure_after_the_first_durable_intent_keeps_the_allowance_used():
    seen = []
    client, headers, allowances = public_app(billable_run(seen, then=RuntimeError('provider failed')))
    key = str(uuid.uuid4())
    body = wait(client, headers, live(client, headers, key, owner=False).json()['run_id'])
    assert body['status'] == 'failed'
    assert allowances.state(headers['X-Session-Id']) == (USED, 'idem:' + key)


def test_session_delete_and_expiry_drop_the_allowance():
    client, headers, allowances = public_app(fake_rec_live)
    assert client.delete('/session', headers=headers).json() == {'deleted': True}
    assert allowances.state(headers['X-Session-Id']) == ('no_ticket', None)
    now = [0.0]
    store = SessionStore(clock=lambda: now[0])
    deps = AppDeps(store=store, demo_cvs={'CV1': CV}, run=fake_rec_live, sweep_seconds=0.02, live_enabled=True,
                   ingress=Ingress(TOKEN, OWNER, HMAC_KEY), public_live=True)
    with TestClient(create_app(deps)) as c:
        h = session(c)
        c.app.state.allowances.mark_ticket_held(h['X-Session-Id'])
        now[0] = 10_000.0                                  # past every session limit
        deadline = time.monotonic() + 5
        while c.app.state.allowances.state(h['X-Session-Id'])[0] != 'no_ticket' and time.monotonic() < deadline:
            time.sleep(0.02)
        assert c.app.state.allowances.state(h['X-Session-Id']) == ('no_ticket', None)


def test_the_owner_never_touches_the_public_allowance():
    seen = []

    def owner_run(cv, seniority, on_result, filters=None, live=None):
        seen.append(live)
        return fake_rec(cv, seniority, on_result, filters)
    client, headers, allowances = public_app(owner_run)
    wait(client, headers, live(client, headers).json()['run_id'])
    assert seen[0].owner and seen[0].on_first_billable is None
    assert allowances.state(headers['X-Session-Id']) == (HELD, None)


# --- persistent ledger storage readiness (C3) ---------------------------------------------------------------

def test_health_reports_ledger_storage_readiness_as_a_boolean_only():
    def broken():
        raise OSError('volume gone')
    for ready, expected in ((None, None), (lambda: True, True), (lambda: False, False), (broken, False)):
        client, _ = make(live_storage_ready=ready)
        assert client.get('/health').json()['live_storage_ready'] is expected


def test_prod_with_an_unprovisioned_root_keeps_the_saved_demo_and_reports_storage_not_ready(tmp_path, monkeypatch):
    from jobfit.api import wiring
    prod_env(tmp_path, monkeypatch)
    deps = wiring.build_deps()                          # startup never fails on an unprovisioned root
    client = TestClient(create_app(deps))
    assert client.get('/health').json()['live_storage_ready'] is False
    headers = session(client)
    r = client.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'saved'}, headers=headers)
    assert r.status_code == 200
    assert sorted(p.name for p in tmp_path.iterdir()) == []      # nothing was created in the root


def test_reconciliation_on_invalid_storage_touches_no_database(tmp_path, monkeypatch):
    from jobfit.api import wiring
    from jobfit.config import get_production_settings
    from jobfit.live.storage import init_storage
    prod_env(tmp_path, monkeypatch)
    runtime = wiring.build_runtime(get_production_settings())
    connects = []
    runtime.connect = lambda: connects.append(1) or (_ for _ in ()).throw(AssertionError('no DB call'))
    assert runtime.reconcile() == [] and connects == []           # no marker
    init_storage(runtime.ledger_path)
    runtime.breach.write('call_wall_exceeded', 'idem:x', 'a1')
    assert runtime.storage_ready() and runtime.reconcile() == [] and connects == []   # breach: global gate
