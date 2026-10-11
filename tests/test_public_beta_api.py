"""D-103 public-beta API contract (semantics only; no Streamlit UI). Fakes only: no provider, DB or network.

- the search stage is labelled as retrieval-stage relevant jobs, never a JobFit match ranking, and
  carries no match score; only an analyzed job has one;
- job_analysis (a corpus job or a pasted JD) is one operation with the D-103 envelope checked
  before any reservation, for the owner too;
- in production the public (non-owner) beta flow stays closed until the real-CV consent adapter
  connects the session's uploaded CV, whatever JOBFIT_PUBLIC_LIVE says;
- the owner bypasses only the ticket and the session allowance: budget, gate, idempotency and
  envelope refusals still apply.
"""
import threading
import time
import uuid

from fastapi.testclient import TestClient

from jobfit.api.main import PUBLIC_BETA_CLOSED_MESSAGE, AppDeps, create_app
from jobfit.eval.product_order import held_score
from jobfit.live.operation import LiveRefused
from jobfit.live.quota import Ingress
from jobfit.llm.public_beta_bounds import compute_public_beta_bounds
from jobfit.recommend.beta_analysis import HOLD_REASON, job_analysis_refusal
from jobfit.recommend.service import JobResult
from jobfit.schemas.analysis import ScoreResult, ScoreStatus, UnitAssessment
from jobfit.session.store import SessionStore
from tests.test_api import CV, EXT, fake_rec
from tests.test_live_api import OWNER, TOKEN, HMAC_KEY

JOBS = {j: {'job_id': j, 'title': f'Role {j}', 'company': 'Acme', 'location': 'Jakarta', 'url': None}
        for j in ('A', 'B', 'C')}
JD = 'Requirements:\n- Python and SQL for data pipelines.\n' + 'We build analytics products. ' * 10
ENV = compute_public_beta_bounds().envelopes


def scored(job_id):
    return JobResult(job_id, 1, ScoreResult(score_pct=100.0, status=ScoreStatus.FINAL, matched=1, required_total=1),
                     assessments=[UnitAssessment(unit_id='u1', label='MATCH', cv_quotes=['Python and SQL.'])],
                     matcher_model='gpt-6-sol', extraction=EXT)


def refusal(cv, *, job_id, jd_text):
    """The real D-103 check; a corpus job here has the small saved extraction EXT."""
    if jd_text is not None:
        return job_analysis_refusal(ENV, cv, job_id, jd_text=jd_text)
    return job_analysis_refusal(ENV, cv, job_id, cached=(EXT, None))


def make(prod=True, public_live=True, analyze=None, search=None, live_enabled=True, **kw):
    calls = {'analyze': [], 'search': []}

    def default_analyze(cv, *, job_id, jd_text, live):
        calls['analyze'].append((job_id, jd_text, live))
        return scored(job_id)

    def default_search(cv, filters):
        calls['search'].append(filters)
        return ['C', 'A', 'B']
    deps = AppDeps(store=SessionStore(), demo_cvs={'CV1': CV}, run=fake_rec, sweep_seconds=None, live_enabled=live_enabled,
                   jobs=JOBS, job_meta=JOBS, analyze_pasted=lambda cv, text: scored('pasted'),
                   ingress=Ingress(TOKEN, OWNER, HMAC_KEY) if prod else None, public_live=public_live,
                   search=search or default_search, analyze_one=analyze or default_analyze,
                   job_analysis_refusal=refusal, **kw)
    return TestClient(create_app(deps)), calls


def session(client, prod=True):
    headers = {'x-jobfit-internal-token': TOKEN, 'x-jobfit-client-ip': '203.0.113.7'} if prod else {}
    s = client.post('/session', headers=headers).json()
    return {'X-Session-Id': s['session_id'], 'X-Session-Token': s['token'], **headers}


def owner(headers, key=None):
    return {**headers, 'x-jobfit-owner-token': OWNER, 'Idempotency-Key': key or str(uuid.uuid4())}


def wait(client, headers, run_id):
    for _ in range(300):
        body = client.get(f'/recommendations/{run_id}', headers=headers).json()
        if body['status'] != 'running':
            return body
        time.sleep(0.01)
    raise AssertionError('run did not finish')


def paste(client, headers, text=JD):
    return client.post('/jobs/paste', json={'jd_text': text}, headers=headers).json()['paste_id']


# --- search stage --------------------------------------------------------------------------------------

def test_the_search_stage_is_labelled_and_has_no_match_score():
    client, calls = make(prod=False)
    h = session(client, prod=False)
    body = client.post('/jobs/search', json={'demo_cv_id': 'CV1'}, headers=h).json()
    assert body['stage'] == 'retrieval' and body['final_order'] is False
    assert 'not JobFit match rankings' in body['label'].replace('Not', 'not') and body['analysis_limit'] == 10
    assert [(j['job_id'], j['retrieval_rank']) for j in body['jobs']] == [('C', 1), ('A', 2), ('B', 3)]
    for j in body['jobs']:
        assert j['stage'] == 'retrieval' and j['analyzed'] is False and j['match_score'] is None
        assert not {'score_pct', 'scored', 'requirements', 'status'} & set(j)
    assert len(calls['search']) == 1


def test_the_search_stage_is_cut_to_its_limit_and_needs_live():
    client, _ = make(prod=False, search=lambda cv, f: [f'J{i}' for i in range(30)], search_limit=10)
    h = session(client, prod=False)
    assert len(client.post('/jobs/search', json={'demo_cv_id': 'CV1'}, headers=h).json()['jobs']) == 10
    assert client.post('/jobs/search', json={'demo_cv_id': 'nope'}, headers=h).status_code == 404
    off, _ = make(prod=False, live_enabled=False)
    assert off.post('/jobs/search', json={'demo_cv_id': 'CV1'}, headers=session(off, prod=False)).status_code == 503


# --- the public flow stays closed until the real-CV consent adapter -------------------------------------

def test_the_public_beta_routes_are_closed_to_non_owners_even_with_public_live_on():
    client, calls = make(public_live=True)
    h = session(client)
    pid = paste(client, h)
    for path, body in (('/jobs/search', {'demo_cv_id': 'CV1'}), ('/jobs/A/analyze', {'demo_cv_id': 'CV1'}),
                       ('/analyze', {'paste_id': pid, 'demo_cv_id': 'CV1'})):
        r = client.post(path, json=body, headers={**h, 'Idempotency-Key': str(uuid.uuid4())})
        assert r.status_code == 503 and r.json()['detail'] == PUBLIC_BETA_CLOSED_MESSAGE, path
    assert calls == {'analyze': [], 'search': []}


# --- job_analysis ------------------------------------------------------------------------------------------

def test_an_analyzed_corpus_job_has_its_match_score_and_the_owner_skips_only_the_ticket():
    client, calls = make()
    h = session(client)
    r = client.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h))
    body = wait(client, h, r.json()['run_id'])
    assert body['status'] == 'done' and body['kind'] == 'analysis'
    res = body['result']
    assert res['stage'] == 'analyzed' and res['analyzed'] is True and res['match_score'] == 100.0
    assert res['card']['job_id'] == 'A' and res['card']['title'] == 'Role A'
    ((job_id, jd_text, live),) = calls['analyze']
    assert (job_id, jd_text) == ('A', None)
    assert live.owner is True and live.on_first_billable is None       # no ticket, no allowance
    assert live.operation_key.startswith('idem:')


def test_a_held_analysis_has_no_match_score():
    held = JobResult('A', 1, held_score(HOLD_REASON), hold_reason=HOLD_REASON, extraction=EXT)
    client, _ = make(analyze=lambda cv, **kw: held)
    h = session(client)
    res = wait(client, h, client.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h)).json()['run_id'])
    assert res['result']['analyzed'] is True and res['result']['match_score'] is None
    assert 'beta_envelope_exceeded' in res['result']['card']['hold_reason']


def test_the_owner_pasted_jd_is_one_job_analysis_of_the_session_text():
    client, calls = make()
    h = session(client)
    pid = paste(client, h)
    r = client.post('/analyze', json={'paste_id': pid, 'demo_cv_id': 'CV1'}, headers=owner(h))
    res = wait(client, h, r.json()['run_id'])['result']
    assert res['stage'] == 'analyzed' and res['card']['title'] == 'Pasted job description'
    assert calls['analyze'][0][:2] == ('pasted', JD)


def test_an_oversized_pasted_jd_is_refused_before_any_operation_for_the_owner_too():
    client, calls = make()
    h = session(client)
    big = 'Requirements:\n- Python\n' + 'x' * ENV.jd_document_max_bytes       # under the paste limit, over D-103
    r = client.post('/analyze', json={'paste_id': paste(client, h, big), 'demo_cv_id': 'CV1'}, headers=owner(h))
    assert r.status_code == 413 and r.json()['detail'] == 'input_too_large'
    assert calls['analyze'] == []
    dev, dev_calls = make(prod=False)
    dh = session(dev, prod=False)
    r = dev.post('/analyze', json={'paste_id': paste(dev, dh, big), 'demo_cv_id': 'CV1'}, headers=dh)
    assert r.status_code == 200          # the development path (no D-103 runtime) is unchanged


def test_owner_job_analysis_needs_a_canonical_idempotency_key_and_never_runs_twice():
    client, calls = make()
    h = session(client)
    no_key = {**h, 'x-jobfit-owner-token': OWNER}
    assert client.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=no_key).status_code == 422
    key = str(uuid.uuid4())
    first = client.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h, key)).json()
    wait(client, h, first['run_id'])
    again = client.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h, key)).json()
    assert again == {'run_id': first['run_id'], 'duplicate': True} and len(calls['analyze']) == 1


# --- the idempotency key is bound to the intended action (session, phase and action) ----------------------

def mismatch(r):
    return r.status_code == 409 and r.json()['detail'] == 'idempotency_key_mismatch'


def test_the_same_key_for_the_same_corpus_job_returns_the_original_run():
    client, calls = make()
    h, key = session(client), str(uuid.uuid4())
    first = client.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h, key)).json()
    wait(client, h, first['run_id'])
    for _ in range(2):
        again = client.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h, key))
        assert again.status_code == 200 and again.json() == {'run_id': first['run_id'], 'duplicate': True}
    assert [c[0] for c in calls['analyze']] == ['A']


def test_the_same_key_for_another_corpus_job_is_refused():
    client, calls = make()
    h, key = session(client), str(uuid.uuid4())
    first = client.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h, key)).json()
    wait(client, h, first['run_id'])
    assert mismatch(client.post('/jobs/B/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h, key)))
    assert [c[0] for c in calls['analyze']] == ['A']
    # the original action is still answered with its run
    assert client.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h, key)).json()['run_id'] == \
        first['run_id']


def test_the_same_key_for_another_pasted_jd_is_refused():
    client, calls = make()
    h, key = session(client), str(uuid.uuid4())
    one, two = paste(client, h), paste(client, h, JD + ' Docker and Kubernetes.')
    first = client.post('/analyze', json={'paste_id': one, 'demo_cv_id': 'CV1'}, headers=owner(h, key)).json()
    wait(client, h, first['run_id'])
    assert mismatch(client.post('/analyze', json={'paste_id': two, 'demo_cv_id': 'CV1'}, headers=owner(h, key)))
    again = client.post('/analyze', json={'paste_id': one, 'demo_cv_id': 'CV1'}, headers=owner(h, key))
    assert again.json() == {'run_id': first['run_id'], 'duplicate': True}
    # a pasted JD and a corpus job are different actions too
    assert mismatch(client.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h, key)))
    assert [c[1] for c in calls['analyze']] == [JD]


def test_another_session_or_phase_with_the_same_key_is_still_refused():
    client, calls = make()
    h, key = session(client), str(uuid.uuid4())
    first = client.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h, key)).json()
    wait(client, h, first['run_id'])
    other = session(client)
    assert mismatch(client.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(other, key)))
    r = client.post('/recommendations', json={'demo_cv_id': 'CV1', 'mode': 'live'}, headers=owner(h, key))
    assert mismatch(r)
    assert len(calls['analyze']) == 1


def test_the_action_fingerprint_holds_no_raw_identifier():
    from jobfit.live.keys import action_fingerprint
    a = action_fingerprint('corpus_job', cv='CV1', job='A')
    assert a == action_fingerprint('corpus_job', job='A', cv='CV1') != action_fingerprint('corpus_job', cv='CV1', job='B')
    assert a != action_fingerprint('pasted_jd', cv='CV1', paste='A') and len(a) == 64 and 'CV1' not in a


def test_the_owner_never_bypasses_budget_or_the_gate():
    for code in ('budget', 'lifetime', 'busy', 'phase_not_admitted'):
        def refused(cv, **kw):
            raise LiveRefused(code)
        client, _ = make(analyze=refused)
        h = session(client)
        r = client.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h))
        assert wait(client, h, r.json()['run_id'])['error'] == code


def test_unknown_jobs_and_cvs_are_refused():
    client, calls = make()
    h = session(client)
    assert client.post('/jobs/ZZ/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h)).status_code == 404
    assert client.post('/jobs/A/analyze', json={'demo_cv_id': 'nope'}, headers=owner(h)).status_code == 404
    assert calls['analyze'] == []


def test_job_analysis_routes_stay_closed_without_their_hooks():
    deps_less = TestClient(create_app(AppDeps(store=SessionStore(), demo_cvs={'CV1': CV}, run=fake_rec,
                                              sweep_seconds=None, live_enabled=True, jobs=JOBS,
                                              ingress=Ingress(TOKEN, OWNER, HMAC_KEY))))
    h = session(deps_less)
    assert deps_less.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h)).status_code == 503
    assert deps_less.post('/jobs/search', json={'demo_cv_id': 'CV1'}, headers=owner(h)).status_code == 503
    pid = paste(deps_less, h)
    assert deps_less.post('/analyze', json={'paste_id': pid, 'demo_cv_id': 'CV1'}, headers=owner(h)).status_code == 503


def test_a_session_runs_at_most_three_analyses_at_a_time_limit():
    gate = threading.Event()

    def slow(cv, **kw):
        gate.wait(5)
        return scored(kw['job_id'])
    client, _ = make(analyze=slow)
    h = session(client)
    first = client.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h))
    assert first.status_code == 200
    busy = client.post('/jobs/B/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h))
    assert busy.status_code == 429                 # one running analysis per session; the key is freed
    gate.set()
    wait(client, h, first.json()['run_id'])


def test_the_production_runtime_is_built_with_the_public_beta_bounds(monkeypatch):
    import jobfit.live.operation as operation
    from jobfit.api import wiring
    from jobfit.llm.public_beta_bounds import PublicBetaBounds
    seen = []

    class FakeRuntime:
        def __init__(self, settings, bounds, **kw):
            seen.append(bounds)
            self.storage = type('S', (), {'validate': lambda self: 'id'})()

        def reconcile(self):
            return []
    monkeypatch.setattr(operation, 'LiveRuntime', FakeRuntime)
    wiring.build_runtime(object())
    assert isinstance(seen[0], PublicBetaBounds) and seen[0].phase_bounds() == compute_public_beta_bounds().phase_bounds()
