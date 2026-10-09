"""D-105 product flow in the Streamlit UI (AppTest) and the UI API client. Fakes only, no paid call.

Upload -> exact preview -> consent -> Continue (consent + parse) -> CV ready -> Find Jobs (optional
pre-search filters) -> Relevant Jobs -> zero-call local refinement -> Analyze Fit -> Improve My CV,
and Check a Job. A CV change clears everything derived from the earlier CV and resets the
work-history confirmation; a rerun or a retry never posts a billable action twice.
"""
import hashlib
import sys
import time
import types
from datetime import date
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ui'))

from api_client import ApiClient, ApiError  # noqa: E402
from refine import options, refine, state  # noqa: E402

DAY = '2026-10-09'
CARDS = [
    {'job_id': 'J1', 'retrieval_rank': 1, 'title': 'ML Engineer', 'company': 'Acme', 'role_family': 'ai_ml_engineering',
     'country_code': 'ID', 'city': 'Jakarta', 'location': 'Jakarta, ID', 'experience_bucket': 'entry',
     'work_mode': 'remote', 'posted_at': '2026-10-05', 'url': 'https://jobs.example/J1', 'filter_status': 'matches'},
    {'job_id': 'J2', 'retrieval_rank': 2, 'title': 'Data Scientist', 'company': 'Beta', 'role_family': 'data_science',
     'country_code': 'SG', 'city': None, 'location': 'SG', 'experience_bucket': '3-4y', 'work_mode': 'onsite',
     'posted_at': '2026-09-01', 'url': None, 'filter_status': 'matches'},
    {'job_id': 'J3', 'retrieval_rank': 3, 'title': 'LLM Engineer', 'company': 'Gamma', 'role_family': 'genai_llm',
     'country_code': None, 'city': None, 'location': None, 'experience_bucket': None, 'work_mode': 'remote_mentioned',
     'posted_at': None, 'url': None, 'filter_status': 'matches'},
    {'job_id': 'J4', 'retrieval_rank': 4, 'title': 'Analytics Engineer', 'company': 'Delta',
     'role_family': 'data_science', 'country_code': 'ID', 'city': 'Bandung', 'location': 'Bandung, ID',
     'experience_bucket': '1-2y', 'work_mode': 'hybrid', 'posted_at': '2026-10-08', 'url': None,
     'filter_status': 'matches'},
]


# ---- pure local refinement -----------------------------------------------------------------------------------

def test_refine_only_narrows_and_keeps_retrieval_order():
    d = date.fromisoformat(DAY)
    assert refine(CARDS, {}, analysis_date=d) == CARDS
    out = refine(CARDS, {'role_family': 'data_science'}, analysis_date=d)
    assert [c['job_id'] for c in out] == ['J2', 'J4']
    out = refine(CARDS, {'work_mode': 'remote'}, analysis_date=d)
    assert [c['job_id'] for c in out] == ['J1', 'J3']                     # remote_mentioned is unknown, kept
    assert [c['job_id'] for c in refine(CARDS, {'work_mode': 'remote'}, analysis_date=d,
                                        include_unknown=False)] == ['J1']
    assert [c['job_id'] for c in refine(CARDS, {'city': ' JAKARTA '}, analysis_date=d,
                                        include_unknown=False)] == ['J1']
    assert [c['job_id'] for c in refine(CARDS, {'posted_within_days': 7}, analysis_date=d)] == ['J1', 'J3', 'J4']
    for crit in ({'country_code': 'id'}, {'experience_bucket': '3-4y'}, {'posted_within_days': 30}):
        shown = refine(CARDS, crit, analysis_date=d)
        assert set(c['job_id'] for c in shown) <= set(c['job_id'] for c in CARDS)
        assert [c['retrieval_rank'] for c in shown] == sorted(c['retrieval_rank'] for c in shown)
    assert options(CARDS, 'work_mode') == ['hybrid', 'onsite', 'remote']


@pytest.mark.parametrize('crit', [{'role_family': 'data_science'}, {'country_code': 'SG'}, {'city': 'jakarta'},
                                  {'experience_bucket': 'entry'}, {'work_mode': 'remote'}, {'posted_within_days': 7},
                                  {'posted_within_days': 30, 'work_mode': 'hybrid', 'country_code': 'ID'}])
def test_refine_states_equal_the_frozen_filter_on_the_same_rows(crit):
    """The UI refinement agrees with jobfit.search.filters.filter_status on the server's metadata."""
    from jobfit.search.filters import JobFilters, filter_status
    d = date.fromisoformat(DAY)
    for card in CARDS:
        row = {'job_id': card['job_id'], 'role_group': 'target', 'role_family': card['role_family'],
               'analysis_geo': ('indonesia' if card['country_code'] == 'ID' else
                                'foreign' if card['country_code'] else 'unknown'),
               'country_code': card['country_code'], 'city_normalized': card['city'],
               'experience_bucket': card['experience_bucket'], 'work_mode': card['work_mode'],
               'posted_at': card['posted_at']}
        server = filter_status(row, JobFilters(**crit), analysis_date=d).status.value
        assert state(card, crit, analysis_date=d) == server, (card['job_id'], crit)


# ---- a recording fake client for AppTest ----------------------------------------------------------------------

class Recorder:
    calls: list = []
    lose_next_analyze = False
    poll_running_once: set = set()


def analyzed(job_id, title):
    card = {'job_id': job_id, 'title': title, 'company': 'Acme', 'location': 'Jakarta, ID', 'url': None,
            'score_pct': 50.0, 'status': 'final', 'scored': True, 'matched': 1, 'partial': 1, 'required_total': 3,
            'soft_skills': {'total': 0, 'matched': 0, 'partial': 0}, 'reasons': [], 'hold_reason': None,
            'explicit_conflicts': [], 'excluded_units': [],
            'requirements': [
                {'unit_id': 'u1', 'requirement': 'Python', 'importance': 'required', 'field': 'skill_tool',
                 'label': 'MATCH', 'check_status': 'ok', 'cv_quotes': ['Python and SQL reporting for sales.']},
                {'unit_id': 'u2', 'requirement': 'AWS', 'importance': 'required', 'field': 'skill_tool',
                 'label': 'PARTIAL', 'check_status': 'ok', 'cv_quotes': ['Deployed services to cloud infrastructure.']},
                {'unit_id': 'u3', 'requirement': 'Docker', 'importance': 'required', 'field': 'skill_tool',
                 'label': 'NO_MATCH', 'check_status': 'ok', 'cv_quotes': []},
                {'unit_id': 'u4', 'requirement': '3 years of ML engineering', 'importance': 'required',
                 'field': 'experience_duration', 'label': 'NO_MATCH', 'check_status': 'ok', 'cv_quotes': []}],
            'matcher_model': 'fake', 'used_fallback': False}
    from jobfit.support.cv_coach import requirement_groups     # the API's grouping, as the presenter adds it
    return {'stage': 'analyzed', 'analyzed': True, 'match_score': 50.0, 'card': card,
            'requirement_groups': requirement_groups(card), 'note': 'note', 'source': 'live', 'cv_source': 'upload'}


class Fake(ApiClient):
    """Every method records (name, args); nothing leaves the process."""

    def __init__(self):
        self.base_url, self.headers, self.runs = 'fake', {}, {}

    def _rec(self, name, *args):
        Recorder.calls.append((name, args))

    def start_session(self):
        self._rec('start_session')

    def heartbeat(self):
        return {}

    def health(self):
        return {'analyzed_k': 10}

    def upload(self, name, data):
        self._rec('upload', name)
        text = 'Experience\n' + data.decode()
        return {'masked_text': text, 'digest': hashlib.sha256(text.encode()).hexdigest(), 'masked_counts': {},
                'removed': {'header_lines': 2}, 'owner_repeat_guard': True, 'warnings': ['can miss things'],
                'layout': 'text', 'provider_processing': 'enabled', 'message': None}

    def edit_preview(self, text):
        self._rec('edit_preview')
        return {'masked_text': text, 'digest': hashlib.sha256(text.encode()).hexdigest(), 'masked_counts': {},
                'removed': {}, 'owner_repeat_guard': True, 'warnings': [], 'layout': 'edited',
                'provider_processing': 'enabled', 'message': None}

    def consent(self, digest):
        self._rec('consent', digest)
        return {'consented': True, 'provider_processing': 'enabled', 'message': None}

    def _run(self, run_id, result):
        self.runs[run_id] = result
        Recorder.poll_running_once.add(run_id)
        return run_id

    def parse_cv(self, action_key):
        self._rec('parse_cv', action_key)
        return self._run(f'parse-{len(Recorder.calls)}', {'stage': 'parsed', 'source': 'live', 'summary': {}})

    def poll(self, run_id):
        if run_id in Recorder.poll_running_once:                 # one real "still running" poll each
            Recorder.poll_running_once.discard(run_id)
            return {'status': 'running', 'kind': 'x', 'progress': 0, 'partial': [], 'result': None, 'error': None}
        return {'status': 'done', 'kind': 'x', 'progress': 0, 'partial': [], 'result': self.runs[run_id], 'error': None}

    def search_jobs(self, filters, action_key):
        self._rec('search_jobs', dict(filters), action_key)
        return {'stage': 'retrieval', 'final_order': False, 'label': 'Relevant jobs (search stage).',
                'analysis_limit': 3, 'cv_source': 'upload', 'analysis_date': DAY, 'jobs': [dict(c) for c in CARDS]}

    def analyze_job(self, job_id, history_confirmed, action_key):
        self._rec('analyze_job', job_id, history_confirmed, action_key)
        if Recorder.lose_next_analyze:
            Recorder.lose_next_analyze = False
            raise httpx.ReadError('response lost after the server accepted the request')
        return self._run(f'an-{job_id}-{action_key}', analyzed(job_id, f'Role {job_id}'))

    def paste(self, jd_text):
        self._rec('paste')
        return 'paste-1'

    def analyze_pasted(self, paste_id, history_confirmed, action_key):
        self._rec('analyze_pasted', paste_id, history_confirmed, action_key)
        return self._run(f'pa-{action_key}', analyzed('pasted', 'Pasted job description'))

    def coach(self, run_id, job_id):
        self._rec('coach', run_id, job_id)
        return {'job_id': job_id, 'rules': 'answers only',
                'representation': [{'requirement': 'AWS', 'asked': 'This job asks for: AWS',
                                    'current': ['Deployed services to cloud infrastructure.'],
                                    'guidance': 'If accurate, make this line more specific.',
                                    'evidence': ['Deployed services to cloud infrastructure.']}],
                'gaps': [{'gap_index': 0, 'requirement': 'Docker', 'label': 'NO_MATCH',
                          'question_first': 'Have you worked on: Docker?',
                          'questions': {'what_when': 'When?', 'own_part': 'What?', 'tools': 'Tools?', 'result': 'Result?'}}],
                'true_gaps': [], 'not_verified': []}

    def coach_answer(self, run_id, job_id, gap_index, done, answers):
        self._rec('coach_answer', run_id, job_id)
        return {'bullet': None, 'parts': [], 'ideas': ['Learn the basics of: Docker.']}

    def job(self, job_id):
        self._rec('job', job_id)
        return {}

    def demo_cvs(self):
        return [{'cv_id': 'CV1', 'experience': [], 'text': 'demo'}]

    def demo_summary(self, cv_id):
        return {'sections_found': [], 'employment': []}

    def market(self, role_family=None, top=15):
        return {'explanation': 'x', 'skills': [], 'source': 'fake'}

    def delete_session(self):
        self._rec('delete_session')
        return {}


@pytest.fixture
def app(monkeypatch):
    from streamlit.testing.v1 import AppTest
    Recorder.calls, Recorder.lose_next_analyze, Recorder.poll_running_once = [], False, set()
    fake_module = types.ModuleType('api_client')
    fake_module.ApiClient, fake_module.ApiError = Fake, ApiError
    monkeypatch.setitem(sys.modules, 'api_client', fake_module)
    return AppTest.from_file(str(ROOT / 'ui/streamlit_app.py'), default_timeout=60).run()


def names(*kinds):
    return [c for c in Recorder.calls if c[0] in kinds]


def button(at, label):
    return next(b for b in at.button if b.label == label)


def upload_and_parse(at, content=b'Data Analyst, PT Contoh 2024\nPython and SQL reporting for sales.'):
    at.file_uploader[0].upload('cv.txt', content, 'text/plain').run()
    assert not at.exception
    next(c for c in at.checkbox if c.label.startswith('I checked this text')).check().run()
    button(at, 'Continue: analyze my CV').click().run()
    assert not at.exception
    assert any(s.value == 'CV ready.' for s in at.success)


def find_jobs(at):
    at.button(key='choose_find').click().run()
    at.button(key='search_submit').click().run()
    assert not at.exception


def shown_caption(at):
    return next(c.value for c in at.caption if c.value.startswith('Showing '))


# ---- the full flow -------------------------------------------------------------------------------------------

def test_upload_preview_consent_parse_find_jobs_analyze_fit_and_coach(app):
    at = app
    assert at.title[0].value == 'JobFit'
    upload_and_parse(at)
    assert [c[0] for c in Recorder.calls[:4]] == ['start_session', 'upload', 'consent', 'parse_cv']
    find_jobs(at)
    assert len(names('search_jobs')) == 1
    assert shown_caption(at).startswith('Showing 4 of 4 relevant jobs')
    assert not any('%' in m.value for m in at.markdown if 'Relevant Jobs' in m.value)
    button(at, 'Analyze Fit').click().run()                     # the first card: J1
    assert not at.exception
    assert at.get('status')                                     # the Analyze Fit wait renders an honest status
    assert any(m.label == 'Evidence coverage' for m in at.metric)
    assert any('not a hiring probability' in c.value for c in at.caption)
    assert names('analyze_job')[0][1][0] == 'J1'
    assert any('This job asks for: AWS' in m.value for m in at.markdown)          # A, evidence-only
    assert any(r.label == 'Have you worked on: Docker?' for r in at.radio)          # B, questions
    assert len(names('coach')) == 1
    assert not at.get('progress')                                # no invented numeric progress
    assert names('job') == []                                    # no production job-detail lookup


def test_local_refinement_makes_no_call_and_keeps_the_order(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    before = list(Recorder.calls)
    at.selectbox(key='refine_mode').set_value('remote').run()
    assert shown_caption(at).startswith('Showing 2 of 4')
    at.checkbox(key='refine_unknown').uncheck().run()
    assert shown_caption(at).startswith('Showing 1 of 4')
    at.selectbox(key='refine_mode').set_value('').run()
    at.selectbox(key='refine_role').set_value('data_science').run()
    at.checkbox(key='refine_unknown').check().run()
    assert shown_caption(at).startswith('Showing 2 of 4')
    titles = [m.value for m in at.markdown if m.value.startswith('**#')]
    assert titles[0].startswith('**#2 ') and titles[1].startswith('**#4 ')        # retrieval order kept
    assert Recorder.calls == before                                              # zero API calls, zero keys


def history_box(at, where, digest):
    return at.checkbox(key=f'history_{where}_{digest}')


def test_no_work_history_question_until_an_analyze_fit_is_near(app):
    at = app
    upload_and_parse(at)
    assert not any(c.label.startswith('My CV lists my complete work history') for c in at.checkbox)   # CV Ready
    find_jobs(at)
    digest = names('consent')[0][1][0]
    assert history_box(at, 'find', digest).value is False                       # contextual, default False


def test_unconfirmed_first_analyze_fit_sends_false_and_the_answer_is_then_fixed(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    digest = names('consent')[0][1][0]
    button(at, 'Analyze Fit').click().run()
    assert names('analyze_job')[-1][1][1] is False
    fixed = at.checkbox(key=f'history_fixed_find_{digest}')
    assert fixed.disabled and fixed.value is False                              # cannot change under the result


def test_check_a_job_reuses_the_history_answer_and_a_new_cv_resets_everything(app):
    at = app
    upload_and_parse(at)
    digest_a = names('consent')[0][1][0]
    find_jobs(at)
    history_box(at, 'find', digest_a).check().run()                            # chosen before the first Analyze Fit
    button(at, 'Analyze Fit').click().run()
    assert names('analyze_job')[-1][1][1] is True
    at.button(key='choose_check').click().run()
    fixed = at.checkbox(key=f'history_fixed_check_{digest_a}')
    assert fixed.disabled and fixed.value is True                               # the same fixed answer
    at.text_area(key='check_jd').input('Machine learning engineer. ' * 20).run()
    button(at, 'Analyze Fit for this job').click().run()
    assert not at.exception
    assert names('analyze_job')[-1][1][1] is True and names('analyze_pasted')[-1][1][1] is True
    assert any('of 3 job analyses used' in c.value for c in at.caption if c.value.startswith('2 '))
    # CV B: nothing from CV A stays visible and the confirmation resets to False
    at.file_uploader[0].upload('cv_b.txt', b'Analyst 2023\nExcel reporting.', 'text/plain').run()
    assert not at.exception
    assert not any(s.value == 'CV ready.' for s in at.success)
    assert not any(c.value.startswith('Showing ') for c in at.caption)
    assert not any(m.label == 'Evidence coverage' for m in at.metric)
    assert not any('This job asks for' in m.value for m in at.markdown)
    for key in ('analyses', 'search', 'coach', 'pasted', 'paste_ids', 'cv_ready', 'parse_run', 'flow',
                'history_choice', 'history_locked'):
        assert key not in at.session_state
    next(c for c in at.checkbox if c.label.startswith('I checked this text')).check().run()
    button(at, 'Continue: analyze my CV').click().run()
    digest_b = names('consent')[-1][1][0]
    assert digest_b != digest_a
    find_jobs(at)
    box = history_box(at, 'find', digest_b)
    assert box.value is False and not box.disabled
    button(at, 'Analyze Fit').click().run()
    assert names('analyze_job')[-1][1][1] is False                               # never carried across CVs


def test_a_lost_first_response_keeps_the_history_locked_and_the_retry_identical(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    digest = names('consent')[0][1][0]
    history_box(at, 'find', digest).check().run()
    Recorder.lose_next_analyze = True
    button(at, 'Analyze Fit').click().run()
    assert any('Connection problem' in e.value for e in at.error)
    assert 'analyses' not in at.session_state or not at.session_state['analyses']   # no entry: response lost
    fixed = at.checkbox(key=f'history_fixed_find_{digest}')
    assert fixed.disabled and fixed.value is True                               # still locked to the chosen answer
    button(at, 'Analyze Fit').click().run()
    first, second = names('analyze_job')
    assert first[1][1] is True and second[1][1] is True                         # same history value
    assert first[1][2] == second[1][2]                                          # same Idempotency-Key


def test_analyze_fit_separates_gaps_not_verified_and_strengths(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    button(at, 'Analyze Fit').click().run()
    md = [m.value for m in at.markdown]
    heads = {h: md.index(h) for h in ('**Strengths (supported by your CV)**',
                                      '**Evidence gaps (partly supported or not found)**',
                                      '**Not verified from this CV**')}
    after = lambda h: md[heads[h] + 1:]                                          # noqa: E731
    gaps = [m for m in after('**Evidence gaps (partly supported or not found)**')
            if m.startswith('- ')][:2]
    assert [g.split(':')[0] for g in gaps] == ['- AWS', '- Docker']             # editable PARTIAL and NO_MATCH
    assert next(m for m in after('**Not verified from this CV**') if m.startswith('- ')) == \
        '- 3 years of ML engineering'
    assert not any(m.startswith('- 3 years of ML engineering:') for m in md)     # never listed as a gap


def test_the_country_selector_covers_the_seeded_snapshot(app):
    at = app
    upload_and_parse(at)
    at.button(key='choose_find').click().run()
    assert at.selectbox(key='search_country').options == ['Any', 'Indonesia', 'Singapore', 'Malaysia', 'Philippines',
                                                          'United States']
    at.selectbox(key='search_country').set_value('PH')
    at.button(key='search_submit').click().run()                               # a form submits its values together
    assert names('search_jobs')[-1][1][0]['country_code'] == 'PH'


def test_a_successful_edit_is_a_new_cv_too(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    digest = names('consent')[0][1][0]
    at.text_area(key=f'text_{digest}').input('Experience\nData Analyst 2024, Python reporting.').run()
    button(at, 'Use my corrected text').click().run()
    assert not at.exception and names('edit_preview')
    assert 'search' not in at.session_state and 'cv_ready' not in at.session_state
    assert not any(c.value.startswith('Showing ') for c in at.caption)


def test_a_retry_after_a_lost_response_reuses_the_key_and_a_rerun_never_posts_again(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    Recorder.lose_next_analyze = True
    button(at, 'Analyze Fit').click().run()
    assert any('Connection problem' in e.value for e in at.error)
    button(at, 'Analyze Fit').click().run()                     # the retry of the same action
    first, second = names('analyze_job')
    assert first[1][2] == second[1][2]                          # same Idempotency-Key, one execution server-side
    calls = len(Recorder.calls)
    at.run()                                                    # plain reruns: polling only, never a new POST
    at.run()
    assert len(names('analyze_job')) == 2 and len(names('parse_cv')) == 1 and len(names('search_jobs')) == 1
    assert len(Recorder.calls) == calls


def test_delete_session(app):
    at = app
    upload_and_parse(at)
    button(at, 'Hentikan & hapus sesi').click().run()
    assert names('delete_session') and any('Session deleted' in s.value for s in at.success)


# ---- the client: owner header and the real API (fakes, owner-only real-CV mode) -----------------------------

def test_the_owner_header_is_sent_only_when_configured(monkeypatch):
    monkeypatch.delenv('JOBFIT_OWNER_TOKEN', raising=False)
    assert 'X-JobFit-Owner-Token' not in ApiClient(http=object())._ingress()
    monkeypatch.setenv('JOBFIT_OWNER_TOKEN', 'o' * 40)
    assert ApiClient(http=object())._ingress()['X-JobFit-Owner-Token'] == 'o' * 40


def test_the_client_runs_the_owner_flow_against_the_real_api(tmp_path, monkeypatch):
    from tests.test_live_api import OWNER, TOKEN
    from tests.test_public_beta_api import JD
    from tests.test_real_cv_adapter import CV_TEXT
    from tests.test_real_cv_api import make
    client, fakes, _deps = make(tmp_path)
    monkeypatch.setenv('JOBFIT_INTERNAL_TOKEN', TOKEN)
    monkeypatch.setenv('JOBFIT_OWNER_TOKEN', OWNER)
    api = ApiClient(http=client)
    api.client_ip = '203.0.113.5'
    api.start_session()
    preview = api.upload('cv.txt', CV_TEXT.encode())
    api.consent(preview['digest'])

    def done(run_id):
        for _ in range(500):
            body = api.poll(run_id)
            if body['status'] != 'running':
                return body
            time.sleep(0.01)
    assert done(api.parse_cv('3f0b6a52-3c4e-4c43-9d1e-6a1f3cc0a101'))['status'] == 'done'
    found = api.search_jobs({'experience_bucket': 'entry'}, '3f0b6a52-3c4e-4c43-9d1e-6a1f3cc0a102')
    assert found['jobs'] and all(j['match_score'] is None for j in found['jobs'])
    run_id = api.analyze_job('P1', True, '3f0b6a52-3c4e-4c43-9d1e-6a1f3cc0a103')
    assert done(run_id)['result']['card']['scored'] and fakes.history == [True]
    assert set(api.coach(run_id, 'P1')) >= {'representation', 'gaps', 'true_gaps', 'not_verified'}
    pasted = api.analyze_pasted(api.paste(JD), False, '3f0b6a52-3c4e-4c43-9d1e-6a1f3cc0a104')
    assert done(pasted)['status'] == 'done' and fakes.history == [True, False]
    assert fakes.tickets == []                                  # the owner never uses a public ticket
    with pytest.raises(ApiError) as exc:
        api.search_jobs({'experience_bucket': 'senior'}, '3f0b6a52-3c4e-4c43-9d1e-6a1f3cc0a105')
    assert exc.value.status == 422
    api.delete_session()


# ---- untrusted CV/JD text renders as text, never as user-controlled Markdown ------------------------------------

EVIL = '[x](https://evil.example) ![i](https://evil.example/p.png)'


def render_untrusted():
    """Run inside AppTest: product views fed with Markdown-looking CV/JD-derived strings."""
    import sys
    sys.path.insert(0, 'ui')
    from components import analysis_view, coach_view, job_card
    evil = '[x](https://evil.example) ![i](https://evil.example/p.png)'
    card = {'job_id': 'J', 'title': evil, 'company': evil, 'location': evil, 'url': None, 'score_pct': 50.0,
            'status': 'final', 'scored': True, 'matched': 1, 'partial': 0, 'required_total': 2,
            'soft_skills': {'total': 0, 'matched': 0, 'partial': 0}, 'reasons': [], 'hold_reason': None,
            'explicit_conflicts': [f'u1: {evil}'], 'excluded_units': [],
            'requirements': [{'unit_id': 'u1', 'requirement': evil, 'importance': 'required',
                              'field': 'experience_duration', 'label': 'NO_MATCH', 'check_status': 'ok',
                              'cv_quotes': []},
                             {'unit_id': 'u2', 'requirement': evil, 'importance': 'required', 'field': 'skill_tool',
                              'label': 'PARTIAL', 'check_status': 'ok', 'cv_quotes': [evil]}],
            'matcher_model': 'fake', 'used_fallback': False}
    analysis_view({'card': card, 'requirement_groups': {'conflict': ['u1'], 'not_verified': [], 'strengths': [],
                                                        'gaps': ['u2']}})
    coach_view({'job_id': 'J', 'rules': 'rules',
                'representation': [{'requirement': evil, 'asked': f'This job asks for: {evil}', 'current': [evil],
                                    'guidance': 'fixed', 'evidence': [evil]}],
                'gaps': [{'gap_index': 0, 'requirement': evil, 'label': 'NO_MATCH',
                          'question_first': f'Have you worked on: {evil}?', 'questions': {}}],
                'true_gaps': [{'conflict': f'u1: {evil}', 'note': 'fact'}],
                'not_verified': [{'requirement': evil, 'unit_ids': ['u9'], 'note': 'Not verified from this CV.'}]},
               on_answer=lambda *a: None)
    job_card(card, 1)


def test_untrusted_text_is_escaped_before_markdown_rendering():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_function(render_untrusted, default_timeout=30).run()
    assert not at.exception
    bodies = ([m.value for m in at.markdown] + [c.value for c in at.caption] + [w.value for w in at.warning]
              + [r.label for r in at.radio])
    untrusted = [b for b in bodies if 'evil' in b]
    assert len(untrusted) >= 8                     # title, company, conflicts, gaps, quotes, questions, C, not verified
    for body in untrusted:
        assert '[x](' not in body and '![i](' not in body, body                 # never live Markdown
        assert r'\[x\]\(https' in body and r'\!\[i\]\(https' in body, body       # escaped, shown as text


# ---- the Analyze Fit result panel sits above the Relevant Jobs list, shown once -----------------------------

def panel_titles(at):
    return [m.value for m in at.markdown if m.value.startswith('#### ')]


def first_card_index(md):
    return next(i for i, m in enumerate(md) if m.startswith('**#'))


def test_a_finished_analyze_fit_appears_in_the_panel_above_the_job_list(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    button(at, 'Analyze Fit').click().run()                     # J1
    assert not at.exception
    assert [s.value for s in at.subheader].count('Analyze Fit result') == 1
    md = [m.value for m in at.markdown]
    assert md.index('#### Role J1') < first_card_index(md)      # in view: before every job card
    assert panel_titles(at) == ['#### Role J1'] and [m.label for m in at.metric].count('Evidence coverage') == 1
    assert any(c.value == 'Analyze Fit result shown above.' for c in at.caption)


def test_show_analyze_fit_result_switches_the_panel_at_once_without_a_post(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    button(at, 'Analyze Fit').click().run()                     # J1
    button(at, 'Analyze Fit').click().run()                     # J2 (J1 already analyzed)
    assert panel_titles(at) == ['#### Role J2']
    keys = [c[1][2] for c in names('analyze_job')]
    at.button(key='show_J1').click().run()                      # one interaction: the panel shows J1 at once
    assert panel_titles(at) == ['#### Role J1']
    assert [s.value for s in at.subheader].count('Analyze Fit result') == 1       # never duplicated
    assert [m.label for m in at.metric].count('Evidence coverage') == 1
    at.run()
    at.run()                                                    # plain reruns
    assert panel_titles(at) == ['#### Role J1']
    assert len(names('analyze_job')) == 2 and [c[1][2] for c in names('analyze_job')] == keys
