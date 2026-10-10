"""D-105 product flow in the Streamlit UI (AppTest) and the UI API client. Fakes only, no paid call.

Home -> Upload CV -> exact preview -> consent -> Continue (consent + parse) -> CV ready -> Find Jobs
(optional pre-search filters) -> Relevant Jobs -> zero-call local refinement -> Analyze Fit -> Improve My
CV, and Check a Job, one screen at a time (visual design v3; Indonesian copy by default). A CV change
clears everything derived from the earlier CV and resets the work-history confirmation; a rerun or a retry
never posts a billable action twice. Content blocks are st.html, so the tests read their HTML.
"""
import hashlib
import re
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
        return {'analyzed_k': 10, 'live_storage_ready': None}

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


def htmls(at) -> list[str]:
    """The page's HTML content blocks (the stylesheet and the scroll script are not content)."""
    return [str(h.value) for h in at.get('html') if not str(h.value).startswith(('<style>', '<script>'))]


def page_text(at) -> str:
    return '\n'.join(htmls(at))


def digest_of(at) -> str:
    return at.session_state['preview']['digest']


def upload_and_parse(at, content=b'Data Analyst, PT Contoh 2024\nPython and SQL reporting for sales.', name='cv.txt'):
    if at.session_state['page'] == 'landing':
        at.button(key='cta_upload').click().run()
    at.file_uploader[0].upload(name, content, 'text/plain').run()
    assert not at.exception
    assert at.session_state['page'] == 'privacy'
    at.checkbox(key=f'consent_{digest_of(at)}').check().run()
    at.button(key='parse_go').click().run()
    assert not at.exception
    assert at.session_state['page'] == 'ready' and at.session_state['cv_ready']
    assert 'CV kamu siap' in page_text(at)


def find_jobs(at):
    at.button(key='choose_find').click().run()
    at.button(key='search_submit').click().run()
    assert not at.exception
    assert at.session_state['page'] == 'results'


def shown(at) -> tuple[int, int]:
    """(shown, total) from the Relevant Jobs counter."""
    m = re.search(r'data-count="(\d+)" data-total="(\d+)"', page_text(at))
    return int(m.group(1)), int(m.group(2))


def ranks(at) -> list[str]:
    return re.findall(r'data-job="[^"]+" data-rank="(\d+)"', page_text(at))


def history_box(at, where, digest):
    return at.checkbox(key=f'history_{where}_{digest}')


def has_history_box(at, where, digest) -> bool:
    return any(c.key == f'history_{where}_{digest}' for c in at.checkbox)


def group(text: str, name: str) -> str:
    """The HTML of one overview group (data-group="...") up to the next group or the end of its block."""
    start = text.index(f'data-group="{name}"')
    end = text.find('data-group=', start + 10)
    return text[start:end if end > 0 else len(text)]


# ---- the full flow -------------------------------------------------------------------------------------------

def test_upload_preview_consent_parse_find_jobs_analyze_fit_and_coach(app):
    at = app
    assert at.button(key='jf_brand').label == 'JobFit'
    assert 'Cari lowongan.' in page_text(at)                                     # the design's home screen
    upload_and_parse(at)
    assert [c[0] for c in Recorder.calls[:4]] == ['start_session', 'upload', 'consent', 'parse_cv']
    find_jobs(at)
    assert len(names('search_jobs')) == 1
    assert shown(at) == (4, 4)
    assert not any('%' in h for h in htmls(at) if 'data-job=' in h)            # search stage: no score
    at.button(key='analyze_J1').click().run()                                   # the first card: J1
    assert not at.exception
    assert at.session_state['page'] == 'analysis'
    run_id = at.session_state['analyses']['J1']['run_id']
    assert run_id in at.session_state['run_started']                            # the honest wait screen polled it
    text = page_text(at)
    assert 'jf-coverage-value' in text and 'Cakupan Bukti CV' in text
    assert 'Bukan peluang diterima kerja' in text                               # never a hiring probability
    assert names('analyze_job')[0][1][0] == 'J1'
    assert not at.get('progress')                                               # no invented numeric progress
    assert names('job') == []                                                   # no production job-detail lookup
    assert names('coach') == []                                                 # the coach is its own screen
    at.button(key='open_coach').click().run()
    assert not at.exception and at.session_state['page'] == 'coach'
    text = page_text(at)
    a_items = [h for h in htmls(at) if 'data-category="A"' in h]
    assert a_items and 'AWS' in a_items[0] and 'Deployed services to cloud infrastructure.' in a_items[0]
    assert any('data-category="B"' in h and 'Docker' in h for h in htmls(at))   # B, asked first
    assert any(b.key.startswith('yes_') for b in at.button) and any(b.key.startswith('no_') for b in at.button)
    assert len(names('coach')) == 1


def test_the_coach_drafts_only_from_the_answers_and_not_done_gives_no_draft(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    at.button(key='analyze_J1').click().run()
    at.button(key='open_coach').click().run()
    no = next(b for b in at.button if b.key.startswith('no_'))
    no.click().run()
    assert not at.exception
    assert names('coach_answer')                                                # "not done": learning ideas only
    assert 'Jangan tambahkan klaim ini ke CV' in page_text(at)
    assert not any(k.startswith('draft_') and (at.session_state[k] or {}).get('bullet')
                   for k in at.session_state)


def test_local_refinement_makes_no_call_and_keeps_the_order(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    before = list(Recorder.calls)
    at.selectbox(key='refine_mode').set_value('remote').run()
    assert shown(at) == (2, 4)
    at.checkbox(key='refine_unknown').uncheck().run()
    assert shown(at) == (1, 4)
    at.selectbox(key='refine_mode').set_value('').run()
    at.selectbox(key='refine_role').set_value('data_science').run()
    at.checkbox(key='refine_unknown').check().run()
    assert shown(at) == (2, 4)
    assert ranks(at) == ['2', '4']                                              # retrieval order kept
    at.button(key='refine_reset').click().run()
    assert shown(at) == (4, 4)
    assert Recorder.calls == before                                             # zero API calls, zero keys


def test_a_refinement_with_no_match_shows_the_empty_state_without_a_call(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    before = list(Recorder.calls)
    at.selectbox(key='refine_country').set_value('SG').run()
    at.selectbox(key='refine_mode').set_value('remote').run()
    assert shown(at) == (1, 4)                                                  # J3: unknown values stay shown
    at.checkbox(key='refine_unknown').uncheck().run()
    assert shown(at) == (0, 4)
    assert 'Tidak ada lowongan dengan filter ini' in page_text(at)
    assert Recorder.calls == before


def test_no_work_history_question_until_an_analyze_fit_is_near(app):
    at = app
    upload_and_parse(at)
    digest = digest_of(at)
    assert not has_history_box(at, 'find', digest) and not has_history_box(at, 'check', digest)   # CV ready
    find_jobs(at)
    assert history_box(at, 'find', digest).value is False                      # contextual, default False


def test_unconfirmed_first_analyze_fit_sends_false_and_the_answer_is_then_fixed(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    digest = digest_of(at)
    at.button(key='analyze_J1').click().run()
    assert names('analyze_job')[-1][1][1] is False
    assert at.session_state['history_locked'][digest] is False
    at.button(key='analysis_back').click().run()
    assert not has_history_box(at, 'find', digest)                              # cannot change under the result
    assert 'Riwayat kerja: belum dikonfirmasi lengkap' in page_text(at)


def test_check_a_job_reuses_the_history_answer_and_a_new_cv_resets_everything(app):
    at = app
    upload_and_parse(at)
    digest_a = digest_of(at)
    find_jobs(at)
    history_box(at, 'find', digest_a).check().run()                            # chosen before the first Analyze Fit
    at.button(key='analyze_J1').click().run()
    assert names('analyze_job')[-1][1][1] is True
    at.button(key='nav_check').click().run()
    assert at.session_state['page'] == 'check'
    assert not has_history_box(at, 'check', digest_a)                           # the same fixed answer
    assert 'Riwayat kerja: dikonfirmasi lengkap' in page_text(at)
    at.text_area(key='check_jd').input('Machine learning engineer. ' * 20).run()
    at.button(key='check_submit').click().run()
    assert not at.exception
    assert names('analyze_job')[-1][1][1] is True and names('analyze_pasted')[-1][1][1] is True
    assert at.session_state['page'] == 'analysis' and at.session_state['return_to'] == 'check'
    assert 'Sisa 1 dari 3 cek kecocokan' in page_text(at)
    # CV B: nothing from CV A stays visible and the confirmation resets to False
    at.button(key='nav_cv').click().run()
    at.button(key='ready_replace').click().run()
    at.button(key='replace_confirm').click().run()
    assert at.session_state['page'] == 'upload'
    at.file_uploader[0].upload('cv_b.txt', b'Analyst 2023\nExcel reporting.', 'text/plain').run()
    assert not at.exception
    assert at.session_state['page'] == 'privacy'
    assert 'jf-coverage' not in page_text(at)
    for key in ('analyses', 'search', 'coach', 'pasted', 'paste_ids', 'cv_ready', 'parse_run', 'return_to',
                'history_choice', 'history_locked'):
        assert key not in at.session_state
    at.checkbox(key=f'consent_{digest_of(at)}').check().run()
    at.button(key='parse_go').click().run()
    digest_b = names('consent')[-1][1][0]
    assert digest_b != digest_a
    find_jobs(at)
    box = history_box(at, 'find', digest_b)
    assert box.value is False and not box.disabled
    at.button(key='analyze_J1').click().run()
    assert names('analyze_job')[-1][1][1] is False                               # never carried across CVs


def test_a_lost_first_response_keeps_the_history_locked_and_the_retry_identical(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    digest = digest_of(at)
    history_box(at, 'find', digest).check().run()
    Recorder.lose_next_analyze = True
    at.button(key='analyze_J1').click().run()
    assert 'Koneksi bermasalah' in page_text(at)
    assert not at.session_state['analyses']                                     # no entry: response lost
    assert at.session_state['history_locked'][digest] is True                   # still locked to the chosen answer
    assert not has_history_box(at, 'find', digest)
    at.button(key='analyze_J1').click().run()
    first, second = names('analyze_job')
    assert first[1][1] is True and second[1][1] is True                         # same history value
    assert first[1][2] == second[1][2]                                          # same Idempotency-Key


def test_analyze_fit_separates_gaps_not_verified_and_strengths(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    at.button(key='analyze_J1').click().run()
    text = page_text(at)
    assert 'Python' in group(text, 'strengths')
    gaps = group(text, 'gaps')
    assert re.findall(r'<li>([^<]+)</li>', gaps)[:2] == ['AWS', 'Docker']       # editable PARTIAL and NO_MATCH
    assert '3 years of ML engineering' not in gaps                              # never listed as a gap
    assert '3 years of ML engineering' in group(text, 'not_verified')
    statuses = dict(re.findall(r'data-status="(\w+)"><div class="jf-requirement-head"><div><div class="jf-h3" '
                               r'role="heading" aria-level="3">([^<]+)<', text))
    assert {v: k for k, v in statuses.items()} == {'Python': 'MATCH', 'AWS': 'PARTIAL', 'Docker': 'NO_MATCH',
                                                   '3 years of ML engineering': 'UNVERIFIED'}


def test_the_country_selector_covers_the_seeded_snapshot(app):
    at = app
    upload_and_parse(at)
    at.button(key='choose_find').click().run()
    assert at.selectbox(key='search_country').options == ['Semua', 'Indonesia', 'Singapura', 'Malaysia', 'Filipina',
                                                          'Amerika Serikat']
    at.selectbox(key='search_country').set_value('PH')
    at.button(key='search_submit').click().run()                               # a form submits its values together
    assert names('search_jobs')[-1][1][0]['country_code'] == 'PH'


def test_a_successful_edit_is_a_new_cv_too(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    digest = digest_of(at)
    at.button(key='nav_cv').click().run()
    at.button(key='ready_edit').click().run()
    assert at.session_state['page'] == 'edit'
    at.text_area(key=f'text_{digest}').input('Experience\nData Analyst 2024, Python reporting.').run()
    at.button(key='edit_save').click().run()
    assert not at.exception and names('edit_preview')
    assert 'search' not in at.session_state and 'cv_ready' not in at.session_state
    assert at.session_state['page'] == 'privacy'
    assert 'data-count=' not in page_text(at)


def test_a_retry_after_a_lost_response_reuses_the_key_and_a_rerun_never_posts_again(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    Recorder.lose_next_analyze = True
    at.button(key='analyze_J1').click().run()
    assert 'Koneksi bermasalah' in page_text(at)
    at.button(key='analyze_J1').click().run()                   # the retry of the same action
    first, second = names('analyze_job')
    assert first[1][2] == second[1][2]                          # same Idempotency-Key, one execution server-side
    calls = len(Recorder.calls)
    at.run()                                                    # plain reruns: polling only, never a new POST
    at.run()
    assert len(names('analyze_job')) == 2 and len(names('parse_cv')) == 1 and len(names('search_jobs')) == 1
    assert len(Recorder.calls) == calls


def test_a_short_pasted_job_is_refused_before_any_call(app):
    at = app
    upload_and_parse(at)
    at.button(key='choose_check').click().run()
    at.text_area(key='check_jd').input('Too short.').run()
    at.button(key='check_submit').click().run()
    assert 'minimal 200 karakter' in page_text(at)
    assert names('paste', 'analyze_pasted') == []


def test_delete_session(app):
    at = app
    upload_and_parse(at)
    at.button(key='open_delete').click().run()
    assert 'Hentikan &amp; hapus sesi?' in page_text(at)                        # confirmation first
    assert names('delete_session') == []
    at.button(key='delete_confirm').click().run()
    assert names('delete_session') and at.session_state['page'] == 'deleted'
    assert 'Sesi sudah dihapus' in page_text(at)
    assert 'preview' not in at.session_state and 'api' not in at.session_state


def test_the_language_switch_changes_the_copy_and_keeps_the_session(app):
    at = app
    upload_and_parse(at)
    digest = digest_of(at)
    at.button(key='lang_en').click().run()
    assert not at.exception
    assert 'Your CV is ready' in page_text(at) and at.session_state['cv_ready']
    assert digest_of(at) == digest and len(names('upload')) == 1                 # nothing was sent again
    at.button(key='lang_id').click().run()
    assert 'CV kamu siap' in page_text(at)


def test_help_explains_coverage_honestly(app):
    at = app
    at.button(key='open_help').click().run()
    text = page_text(at)
    assert 'bukan peluang diterima kerja dan bukan skor ATS' in text
    at.button(key='help_ok').click().run()
    assert 'Cara membaca hasil JobFit' not in page_text(at)


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


# ---- untrusted CV/JD text renders as inert text, never as markup ------------------------------------------------

EVIL = '<img src=x onerror=alert(1)><a href="https://evil.example">x</a> [x](https://evil.example) ![i](https://evil.example/p.png)'


def render_untrusted():
    """Run inside AppTest: product views fed with markup-looking CV/JD-derived strings."""
    import sys
    sys.path.insert(0, 'ui')
    from components import analysis_view, coach_view, job_card
    evil = ('<img src=x onerror=alert(1)><a href="https://evil.example">x</a> [x](https://evil.example) '
            '![i](https://evil.example/p.png)')
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


def test_untrusted_text_is_escaped_before_it_reaches_the_page():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_function(render_untrusted, default_timeout=30).run()
    assert not at.exception
    bodies = htmls(at) + [m.value for m in at.markdown] + [c.value for c in at.caption]
    untrusted = [b for b in bodies if 'evil.example' in b]
    assert len(untrusted) >= 8                     # title, company, conflicts, gaps, quotes, A, B, C, not verified
    for body in untrusted:
        assert '<img' not in body and '<a ' not in body and 'onerror=alert' not in body.replace('onerror=alert(1)&gt;', ''), body
        assert '&lt;img src=x onerror=alert(1)&gt;&lt;a href=&quot;https://evil.example&quot;&gt;' in body, body
    assert not at.markdown                         # nothing goes through Markdown rendering


# ---- Analyze Fit results open on their own screen; switching between them never posts ----------------------

def coverage_title(at) -> str:
    return re.search(r'<div class="jf-h1" role="heading" aria-level="1">([^<]+)</div>', page_text(at)).group(1)


def test_a_finished_analyze_fit_opens_its_result_screen_once(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    at.button(key='analyze_J1').click().run()                   # J1
    assert not at.exception
    assert at.session_state['page'] == 'analysis' and coverage_title(at) == 'Role J1'
    assert page_text(at).count('jf-coverage-value') == 1
    at.button(key='analysis_back').click().run()
    assert at.session_state['page'] == 'results'
    assert any(b.key == 'show_J1' for b in at.button) and not any(b.key == 'analyze_J1' for b in at.button)
    assert 'Sudah dicek' in page_text(at)


def test_show_analyze_fit_result_switches_at_once_without_a_post(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    at.button(key='analyze_J1').click().run()                   # J1
    at.button(key='analysis_back').click().run()
    at.button(key='analyze_J2').click().run()                   # J2 (J1 already analyzed)
    assert coverage_title(at) == 'Role J2'
    keys = [c[1][2] for c in names('analyze_job')]
    at.button(key='analysis_back').click().run()
    at.button(key='show_J1').click().run()                      # one interaction: the result screen shows J1
    assert coverage_title(at) == 'Role J1'
    assert page_text(at).count('jf-coverage-value') == 1        # never duplicated
    at.run()
    at.run()                                                    # plain reruns
    assert coverage_title(at) == 'Role J1'
    assert len(names('analyze_job')) == 2 and [c[1][2] for c in names('analyze_job')] == keys


def test_the_quota_disables_analyze_fit_after_three(app):
    at = app
    upload_and_parse(at)
    find_jobs(at)
    for job in ('J1', 'J2', 'J3'):
        at.button(key=f'analyze_{job}').click().run()
        at.button(key='analysis_back').click().run()
    assert at.button(key='analyze_J4').disabled
    assert 'Jatah cek kecocokan habis' in page_text(at)
    assert len(names('analyze_job')) == 3


# ---- an outdated API (before D-104) is named, never a bare "Not Found" ------------------------------------------

def test_an_outdated_api_is_flagged_and_its_not_found_is_explained(monkeypatch):
    from streamlit.testing.v1 import AppTest
    Recorder.calls, Recorder.lose_next_analyze, Recorder.poll_running_once = [], False, set()

    class Old(Fake):
        def health(self):                               # the Oct 4 API: no live_storage_ready
            return {'ok': True, 'real_cv_enabled': False, 'live_enabled': False, 'saved_demo': True}

        def edit_preview(self, text):
            raise ApiError(404, 'Not Found')
    fake_module = types.ModuleType('api_client')
    fake_module.ApiClient, fake_module.ApiError = Old, ApiError
    monkeypatch.setitem(sys.modules, 'api_client', fake_module)
    at = AppTest.from_file(str(ROOT / 'ui/streamlit_app.py'), default_timeout=60).run()
    assert 'versi lama' in page_text(at)
    at.button(key='cta_upload').click().run()
    at.file_uploader[0].upload('cv.txt', b'Data Analyst 2024\nPython reporting.', 'text/plain').run()
    at.button(key='privacy_edit').click().run()
    at.text_area(key=f'text_{digest_of(at)}').input('Experience\nAnalyst 2024.').run()
    at.button(key='edit_save').click().run()
    assert not at.exception
    assert 'tidak dikenal oleh API' in page_text(at)


def test_the_current_api_shows_no_outdated_warning(app):
    assert 'versi lama' not in page_text(app)


def test_a_held_result_explains_why_with_the_requirement_text():
    import sys as _sys
    _sys.path.insert(0, str(ROOT / 'ui'))
    from components import reason_texts
    card = {'reasons': ['An experience, level or education requirement needs checking: U04.'],
            'requirements': [{'unit_id': 'U04', 'requirement': 'Intermediate statistics skills'}]}
    assert reason_texts(card) == ['Syarat pengalaman, level, atau pendidikan ini perlu dicek dulu: '
                                  'Intermediate statistics skills']


def test_hold_and_provisional_reasons_are_explained_once():
    import sys as _sys
    _sys.path.insert(0, str(ROOT / 'ui'))
    from components import coverage_html, reason_texts
    held = {'scored': False, 'reasons': ['Evidence matching did not finish: timeout'],
            'hold_reason': 'Evidence matching did not finish: timeout', 'requirements': []}
    text = coverage_html(held)
    assert 'Pencocokan bukti dengan CV belum selesai (timeout)' in text
    assert text.count('Evidence matching did not finish') == 0              # translated and shown once
    provisional = {'scored': True, 'status': 'provisional', 'score_pct': 60.0, 'matched': 2, 'partial': 1,
                   'required_total': 4, 'requirements': [],
                   'reasons': ['Some requirements need checking; excluded unresolved units are listed separately.',
                               '2 requirement(s) not clearly required or preferred'],
                   'excluded_units': [{'unit_id': 'U05', 'text': 'Structured data experience'}]}
    assert reason_texts(provisional) == ['Beberapa syarat perlu dicek dan tidak dihitung di skor: '
                                         'Structured data experience',
                                         '2 syarat belum jelas wajib atau nilai tambah.']
    assert 'Kenapa skornya sementara' in coverage_html(provisional)


def test_the_requirement_behind_a_hold_is_marked_in_its_row():
    import sys as _sys
    _sys.path.insert(0, str(ROOT / 'ui'))
    from components import requirement_html
    row = {'unit_id': 'U04', 'requirement': 'Intermediate statistics', 'importance': 'required', 'cv_quotes': []}
    assert 'jf-flagged' in requirement_html(row, 'NO_MATCH', True)
    assert 'jf-flagged' not in requirement_html(row, 'NO_MATCH')


def test_the_ui_follows_the_api_session_analysis_limit(monkeypatch):
    from streamlit.testing.v1 import AppTest
    Recorder.calls, Recorder.lose_next_analyze, Recorder.poll_running_once = [], False, set()

    class Ten(Fake):
        def health(self):
            return {'analyzed_k': 10, 'live_storage_ready': True, 'analysis_limit': 10}
    fake_module = types.ModuleType('api_client')
    fake_module.ApiClient, fake_module.ApiError = Ten, ApiError
    monkeypatch.setitem(sys.modules, 'api_client', fake_module)
    at = AppTest.from_file(str(ROOT / 'ui/streamlit_app.py'), default_timeout=60).run()
    assert '10 cek kecocokan per sesi' in page_text(at)
    upload_and_parse(at)
    find_jobs(at)
    for job in ('J1', 'J2', 'J3'):
        at.button(key=f'analyze_{job}').click().run()
        at.button(key='analysis_back').click().run()
    assert not at.button(key='analyze_J4').disabled                             # past the default of 3
    assert 'Sisa 7 dari 10 cek kecocokan' in page_text(at)


def test_disabled_real_cv_processing_explains_the_disabled_consent_truthfully(monkeypatch):
    from streamlit.testing.v1 import AppTest
    Recorder.calls, Recorder.lose_next_analyze, Recorder.poll_running_once = [], False, set()

    class Off(Fake):                                   # production: JOBFIT_REAL_CV_ENABLED=0
        def upload(self, name, data):
            return {**super().upload(name, data), 'provider_processing': 'disabled',
                    'message': 'Live analysis of uploaded CVs is not enabled yet.'}
    fake_module = types.ModuleType('api_client')
    fake_module.ApiClient, fake_module.ApiError = Off, ApiError
    monkeypatch.setitem(sys.modules, 'api_client', fake_module)
    at = AppTest.from_file(str(ROOT / 'ui/streamlit_app.py'), default_timeout=60).run()
    at.button(key='cta_upload').click().run()
    at.file_uploader[0].upload('cv.txt', b'Data Analyst 2024\nPython reporting.', 'text/plain').run()
    digest = digest_of(at)
    assert at.checkbox(key=f'consent_{digest}').disabled and at.button(key='parse_go').disabled
    assert 'Analisis CV asli belum diaktifkan di demo ini' in page_text(at)
    assert 'Live analysis of uploaded CVs' not in page_text(at)
    at.button(key='privacy_demo').click().run()
    assert at.session_state['page'] == 'demo'
    assert names('consent', 'parse_cv') == []
