"""D-105 pre-local product contract (API side). Fakes only: no provider, runtime or database call.

- the explicit owner-only real-CV switch (JOBFIT_REAL_CV_ENABLED) with the public beta closed;
- every optional pre-search filter, blank = no narrowing, invalid values refused;
- the browse list uses the frozen stage-1 candidate depth (30), not the analyzed K;
- the work-history confirmation is the user's, bound into the Analyze Fit action;
- "Improve My CV for This Job" works on an Analyze Fit result (corpus job and pasted JD).
"""
from types import SimpleNamespace

import pytest
import yaml

from jobfit.api.main import PUBLIC_BETA_CLOSED_MESSAGE
from jobfit.config import ConfigurationError, ProductionSettings, get_production_settings
from tests.test_live_api import OWNER, TOKEN, prod_env
from tests.test_public_beta_api import JD
from tests.test_real_cv_api import (analyze, key_headers, make, parse, search, session, upload_and_consent,
                                    wait)

FROZEN = 'config/versions/pipeline_cp23_freeze_candidate_v4_20261006.yaml'


def ready(tmp_path, **kw):
    client, f, deps = make(tmp_path, **kw)
    h = session(client)
    upload_and_consent(client, h)
    assert parse(client, h)['status'] == 'done'
    return client, f, deps, h


# ---- settings and wiring: the explicit, owner-only switch -------------------------------------------------

@pytest.mark.parametrize('env', [{'JOBFIT_REAL_CV_ENABLED': '1'},
                                 {'JOBFIT_REAL_CV_ENABLED': '1', 'JOBFIT_ENV': 'prod', 'DATABASE_URL': 'postgresql://x/y',
                                  'JOBFIT_INTERNAL_TOKEN': TOKEN}])
def test_the_real_cv_switch_requires_prod_and_live(env):
    with pytest.raises(ConfigurationError, match='JOBFIT_REAL_CV_ENABLED=1 requires'):
        get_production_settings(env)


def test_the_real_cv_switch_is_off_by_default_and_only_0_or_1():
    assert ProductionSettings().real_cv_enabled is False
    assert get_production_settings({}).real_cv_enabled is False
    with pytest.raises(ConfigurationError, match='JOBFIT_REAL_CV_ENABLED must be 0 or 1'):
        get_production_settings({'JOBFIT_REAL_CV_ENABLED': 'yes'})


def test_wiring_enables_real_cvs_only_with_the_switch_and_keeps_the_public_beta_closed(tmp_path, monkeypatch):
    from jobfit.api import wiring
    prod_env(tmp_path, monkeypatch)
    deps = wiring.build_deps()
    assert deps.real_cv_enabled is False and deps.public_beta_open is False      # prod + live alone: still off
    monkeypatch.setenv('JOBFIT_REAL_CV_ENABLED', '1')
    deps = wiring.build_deps()
    assert deps.real_cv_enabled is True and deps.public_beta_open is False and deps.public_live is False


def test_default_wiring_stays_dark(monkeypatch):
    from jobfit.api import wiring
    for name in ('JOBFIT_ENV', 'JOBFIT_LIVE_ENABLED', 'JOBFIT_PUBLIC_LIVE', 'JOBFIT_REAL_CV_ENABLED'):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr('jobfit.config._load_dotenv', lambda: None)
    deps = wiring.build_deps()
    assert deps.real_cv_enabled is False and deps.public_beta_open is False and deps.ingress is None


def test_owner_only_flow_works_and_a_non_owner_gets_503_without_a_ticket_or_call(tmp_path):
    client, f, _deps, h = ready(tmp_path)                     # real CVs on, public beta closed
    assert search(client, h).status_code == 200
    calls = len(f.provider_calls)
    other = session(client, ip='198.51.100.9')
    upload_and_consent(client, other)
    for r in (client.post('/cv/parse', headers=key_headers(other, owner=False)),
              search(client, other, owner=False), analyze(client, other, owner=False)):
        assert r.status_code in (409, 503)
    r = client.post('/cv/parse', headers=key_headers(other, owner=False))
    assert r.status_code == 503 and r.json()['detail'] == PUBLIC_BETA_CLOSED_MESSAGE
    assert f.tickets == [] and len(f.provider_calls) == calls
    assert client.get('/health').json()['real_cv_enabled'] is True


# ---- pre-search filters -------------------------------------------------------------------------------------

def test_every_pre_search_filter_reaches_the_production_search(tmp_path):
    client, _f, deps, h = ready(tmp_path)
    seen = []
    original = deps.real_search

    def spy(store, handle, lease, filters, *, live):
        seen.append(filters)
        return original(store, handle, lease, filters, live=live)
    deps.real_search = spy
    assert search(client, h).status_code == 200                                     # blank: nothing narrows
    assert seen[-1].active == ()
    chosen = {'role_family': 'data_science', 'country_code': 'id', 'city': ' Jakarta ', 'experience_bucket': '1-2y',
              'work_mode': 'hybrid', 'posted_within_days': 30, 'include_unknown': False}
    r = search(client, h, **chosen)
    assert r.status_code == 200, r.text
    f = seen[-1]
    assert (f.role_family, f.country_code, f.city, f.experience_bucket, f.work_mode, f.posted_within_days,
            f.include_unknown) == ('data_science', 'id', ' Jakarta ', '1-2y', 'hybrid', 30, False)
    assert set(f.active) == {'role_family', 'country_code', 'city', 'experience_bucket', 'work_mode',
                             'posted_within_days'}


@pytest.mark.parametrize('bad', [{'role_family': 'marketing'}, {'experience_bucket': 'senior'},
                                 {'work_mode': 'anywhere'}, {'posted_within_days': 14}, {'country_code': 'IDN'},
                                 {'city': '   '}])
def test_invalid_filter_values_fail_clearly_before_any_call(tmp_path, bad):
    client, f, _deps, h = ready(tmp_path)
    calls = len(f.provider_calls)
    r = search(client, h, **bad)
    assert r.status_code == 422 and len(f.provider_calls) == calls


def test_the_experience_filter_is_part_of_the_search_action(tmp_path):
    client, _f, _deps, h = ready(tmp_path)
    key = '3f0b6a52-3c4e-4c43-9d1e-6a1f3cc0a001'
    assert search(client, h, key=key, experience_bucket='entry').status_code == 200
    r = search(client, h, key=key, experience_bucket='5y+')
    assert r.status_code == 409 and r.json()['detail'] == 'idempotency_key_mismatch'


def test_the_real_search_response_carries_the_refinement_date_and_card_metadata(tmp_path):
    client, _f, _deps, h = ready(tmp_path)
    body = search(client, h).json()
    assert body['stage'] == 'retrieval' and body['final_order'] is False and body['analysis_limit'] == 10
    assert len(body['analysis_date']) == 10
    for card in body['jobs']:
        assert card['match_score'] is None and 'experience_bucket' in card and 'score_pct' not in card


# ---- browse depth: the frozen stage-1 candidate depth ------------------------------------------------------

def test_browse_depth_is_the_frozen_stage1_candidate_depth(tmp_path, monkeypatch):
    from jobfit.api import wiring
    from jobfit.recommend import real_cv_flow
    raw = yaml.safe_load(open(FROZEN))
    assert (raw.get('stage1_candidate_depth'), raw.get('stage1_k')) == (30, 10)    # frozen values, not edited
    prod_env(tmp_path, monkeypatch)
    monkeypatch.setenv('JOBFIT_REAL_CV_ENABLED', '1')
    deps = wiring.build_deps()
    assert deps.search_limit == 30
    captured = {}
    monkeypatch.setattr(real_cv_flow, 'reserved_search', lambda *a, **kw: captured.update(kw) or [])
    deps.real_search(None, None, None, None, live=SimpleNamespace(operation_key='idem:x', quota=None,
                                                                   on_first_billable=None))
    assert captured['depth'] == 30


def test_the_api_returns_up_to_the_browse_depth(tmp_path):
    rows = [{'job_id': f'J{i}', 'retrieval_rank': i, 'filter_status': 'matches'} for i in range(1, 41)]
    client, _f, deps, h = ready(tmp_path, search_limit=30)
    from jobfit.recommend.real_cv_flow import store_search_results

    def forty(store, handle, lease, filters, *, live):
        store_search_results(store, handle, lease, live.operation_key, rows)
        return rows
    deps.real_search = forty
    jobs = search(client, h).json()['jobs']
    assert [j['retrieval_rank'] for j in jobs] == list(range(1, 31))


# ---- work-history confirmation (D-086 input) bound to the action -------------------------------------------

def test_history_confirmation_defaults_false_and_is_bound_into_the_analyze_action(tmp_path):
    client, f, _deps, h = ready(tmp_path)
    assert search(client, h).status_code == 200
    r = analyze(client, h, 'P1')
    assert wait(client, h, r.json()['run_id'])['status'] == 'done'
    assert f.history == [False]                                                     # never assumed complete
    key = '3f0b6a52-3c4e-4c43-9d1e-6a1f3cc0a002'
    r = client.post('/jobs/P2/analyze', json={'cv_source': 'upload', 'history_confirmed': True},
                    headers=key_headers(h, key=key))
    assert wait(client, h, r.json()['run_id'])['status'] == 'done' and f.history[-1] is True
    other = client.post('/jobs/P2/analyze', json={'cv_source': 'upload', 'history_confirmed': False},
                        headers=key_headers(h, key=key))
    assert other.status_code == 409 and other.json()['detail'] == 'idempotency_key_mismatch'


def test_check_a_job_passes_the_confirmation_too(tmp_path):
    client, f, _deps, h = ready(tmp_path)
    pid = client.post('/jobs/paste', json={'jd_text': JD}, headers=h).json()['paste_id']
    r = client.post('/analyze', json={'paste_id': pid, 'cv_source': 'upload', 'history_confirmed': True},
                    headers=key_headers(h))
    assert wait(client, h, r.json()['run_id'])['status'] == 'done' and f.history == [True]


# ---- Improve My CV for This Job on an Analyze Fit result -----------------------------------------------------

def test_the_coach_works_on_a_selected_job_and_a_pasted_jd(tmp_path):
    client, f, _deps, h = ready(tmp_path)
    assert search(client, h).status_code == 200
    corpus = analyze(client, h, 'P1').json()['run_id']
    pid = client.post('/jobs/paste', json={'jd_text': JD}, headers=h).json()['paste_id']
    pasted = client.post('/analyze', json={'paste_id': pid, 'cv_source': 'upload'},
                         headers=key_headers(h)).json()['run_id']
    calls = len(f.provider_calls)
    for run_id, job_id in ((corpus, 'P1'), (pasted, 'pasted')):
        result = wait(client, h, run_id)['result']
        out = client.post('/tailor', json={'run_id': run_id, 'job_id': job_id}, headers=h)
        assert out.status_code == 200, out.text
        assert set(out.json()) == {'job_id', 'gaps', 'representation', 'true_gaps', 'not_verified', 'rules'}
        groups = result['requirement_groups']                                   # Analyze Fit grouping, from the API
        assert set(groups) == {'conflict', 'not_verified', 'strengths', 'gaps'}
        assert groups['strengths'] == ['u1'] and not groups['gaps'] and not groups['not_verified']
        assert client.post('/tailor', json={'run_id': run_id}, headers=h).status_code == 200
        assert wait(client, h, run_id)['result'] == result                       # coaching never changes a score
    assert len(f.provider_calls) == calls                                          # deterministic: no provider call


def test_the_coach_refuses_an_unfinished_or_foreign_run(tmp_path):
    client, _f, _deps, h = ready(tmp_path)
    assert client.post('/tailor', json={'run_id': 'nope', 'job_id': 'P1'}, headers=h).status_code == 404
    other = session(client, ip='198.51.100.10')
    assert search(client, h).status_code == 200
    run_id = analyze(client, h, 'P1').json()['run_id']
    wait(client, h, run_id)
    assert client.post('/tailor', json={'run_id': run_id, 'job_id': 'P1'}, headers=other).status_code == 404
    assert OWNER not in str(client.post('/tailor', json={'run_id': run_id, 'job_id': 'P1'}, headers=h).json())
