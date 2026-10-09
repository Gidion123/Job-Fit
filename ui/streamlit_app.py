"""JobFit Streamlit UI. Calls the API only (no business logic here).

Run: uvicorn jobfit.api.wiring:create_default_app --factory --app-dir src   (API)
     streamlit run ui/streamlit_app.py                                      (UI)

Product flow (D-105): Upload your CV -> local structural sanitizer -> exact preview -> optional edit
(sanitized again) -> explicit consent -> parse -> Find Jobs (optional pre-search filters -> Relevant
Jobs -> zero-call local refinement -> Analyze Fit on a chosen job) or Check a Job (pasted JD ->
Analyze Fit) -> Improve My CV for This Job. A saved synthetic demo and market skills stay secondary.
Privacy UX (D-051/D-104): pre-upload notice, exact sanitized preview, consent for that exact text,
"Hentikan & hapus sesi", a liveness heartbeat while the page is open, and honest expiry messages.
Every billable action carries one idempotency key per user action; a rerun or retry never runs it twice.
"""
from __future__ import annotations

import hashlib
import time
from datetime import date

import httpx
import streamlit as st

from api_client import ApiClient, ApiError
from components import (EXPERIENCE, ROLE_FAMILY, WORK_MODE, analysis_view, coach_view, job_card,
                        relevant_job_card, safe, suggestions)
from live_action import LiveActions, action_fingerprint, fingerprint
from refine import options, refine

st.set_page_config(page_title='JobFit', layout='wide')
POLL_SECONDS = 1.5
COUNTRY = {'ID': 'Indonesia', 'SG': 'Singapore', 'MY': 'Malaysia', 'PH': 'Philippines', 'US': 'United States'}
HISTORY_LABEL = 'My CV lists my complete work history (all jobs, with dates)'
HISTORY_HELP = ('Leave this unchecked if older or less relevant jobs may be missing from your CV: then a "needs N '
                'years" requirement is shown as not verified instead of being compared with your total experience. '
                'It never changes the evidence coverage.')
MAX_ANALYSES = 3
# Everything derived from the current uploaded CV; cleared whenever the CV (its digest) changes.
CV_STATE = ('cv_ready', 'parse_run', 'parse_result', 'consented_digest', 'flow', 'search', 'analyses',
            'selected_job', 'coach', 'pasted', 'paste_ids')
CV_PREFIXES = ('refine_', 'history_', 'done_', 'what_when_', 'own_part_', 'tools_', 'result_', 'bullet_', 'draft_')


def new_client():
    client = ApiClient()
    client.start_session()
    return client


if 'api' not in st.session_state:
    try:
        st.session_state.api = new_client()
    except Exception as exc:  # API down or not reachable: show a clear message, never a traceback
        st.title('JobFit')
        st.error(f'Cannot reach the JobFit API at {ApiClient().base_url}. It may still be starting. '
                 f'Wait a few seconds and press Retry. ({type(exc).__name__})')
        st.button('Retry')
        st.stop()
api: ApiClient = st.session_state.api
if 'live_actions' not in st.session_state:
    st.session_state.live_actions = LiveActions()
actions: LiveActions = st.session_state.live_actions


def call(fn, *args, **kwargs):
    """Run one API call. An expired session is replaced and the user is told honestly."""
    try:
        return fn(*args, **kwargs)
    except ApiError as exc:
        if exc.status == 401:
            for key in list(st.session_state):
                del st.session_state[key]
            try:
                st.session_state.api = new_client()
            except Exception:
                pass
            st.warning('Your session expired (no activity, or the page was away too long) and its data was '
                       'deleted on the server. A new empty session has started; please run the step again.')
            st.stop()
        raise


def reset_cv_state() -> None:
    """A new upload or a successful edit is a new CV: nothing derived from the earlier CV stays visible."""
    for key in list(st.session_state):
        if key in CV_STATE or key.startswith(CV_PREFIXES):
            del st.session_state[key]


def wait_run(run_id: str, label: str, steps: list[str]) -> dict:
    """Honest progress: the stages this operation goes through, no invented percentage."""
    with st.status(label, expanded=True) as status:
        for step in steps:
            st.write(step)
        st.caption('This can take a minute or two. You can keep this page open; nothing runs twice.')
        body = call(api.poll, run_id)
        while body['status'] == 'running':
            time.sleep(POLL_SECONDS)
            body = call(api.poll, run_id)
        if body['status'] == 'failed':
            status.update(label=f"Stopped ({body['error']}). No result was made up.", state='error')
        else:
            status.update(label='Done', state='complete', expanded=False)
    return body


def billable(kind: str, start, **ids):
    """Start one billable action with its idempotency key; a lost response keeps the key for the retry."""
    key = actions.key_for(fingerprint(kind, **ids))
    try:
        out = call(start, key)
    except ApiError as exc:
        st.session_state.billable_error = exc.detail
        st.error(exc.detail)
        return None
    except httpx.HTTPError:
        st.session_state.billable_error = ('Connection problem: press the button again to retry the same request '
                                           '(it will not run twice).')
        st.error(st.session_state.billable_error)
        return None
    actions.acknowledged(out if isinstance(out, str) else key)
    return out


@st.fragment(run_every=30)
def liveness():
    """Browser liveness: runs only while this page is open and connected. It keeps the
    2-minute lease alive but does not count as activity, so the 30-minute idle limit still applies."""
    try:
        api.heartbeat()
    except Exception:
        pass


liveness()

with st.sidebar:
    st.subheader('Session')
    st.caption('Your data lives only in this session. It is deleted when you press the button below, '
               'about 2 minutes after you close the page, after 30 minutes without activity, or after 2 hours.')
    if st.button('Hentikan & hapus sesi', type='primary'):
        try:
            api.delete_session()
        except ApiError:
            pass
        for key in list(st.session_state):
            del st.session_state[key]
        st.success('Session deleted. Your data was cleared on the server.')
        st.stop()

st.title('JobFit')
st.markdown('**Find relevant AI/data jobs and see exactly what your CV supports.**')
st.caption('Match % is CV evidence coverage for one analyzed job, not a hiring probability.')

# ---------------------------------------------------------------- 1. Upload your CV --------------------------
st.header('Upload your CV')
st.markdown('**How your CV is handled:** the server receives your file only to read its text. Identity and '
            'contact details, your Summary or profile section and privacy-only sections are removed or masked '
            'locally. Masking is careful but bounded and can miss something, so check the text below: it is '
            'exactly what would be analyzed. Nothing reaches an AI provider before you agree. Session data is '
            'temporary, and you can stop and delete it at any time (sidebar).')
file = st.file_uploader('PDF, DOCX or text', type=['pdf', 'docx', 'txt', 'md'])
if file is not None and st.session_state.get('upload_id') != file.file_id:
    st.session_state.upload_id = file.file_id
    reset_cv_state()
    try:
        st.session_state.preview = call(api.upload, file.name, file.getvalue())
        st.session_state.preview_valid = True
    except ApiError as exc:
        st.session_state.pop('preview', None)
        st.error(exc.detail)

preview = st.session_state.get('preview')
if preview:
    digest = preview['digest']
    removed = preview.get('removed') or {}
    if removed:
        st.caption('Removed locally before preview: ' + ', '.join(f'{k.replace("_", " ")} ({v})'
                                                                  for k, v in removed.items() if v))
    edited = st.text_area('Exact text that would be analyzed (you can correct it; it is checked again)',
                          preview['masked_text'], height=300, key=f'text_{digest}')
    if edited != preview['masked_text'] and st.button('Use my corrected text'):
        try:
            out = call(api.edit_preview, edited)
            reset_cv_state()
            st.session_state.preview, st.session_state.preview_valid = out, True
            st.rerun()
        except ApiError as exc:
            reset_cv_state()                 # the server invalidated the old preview too
            st.session_state.preview_valid = False
            st.error(exc.detail)
    for w in preview['warnings']:
        st.caption(w)
    if preview.get('message'):
        st.info(preview['message'])
    ready_to_send = st.session_state.get('preview_valid') and preview.get('provider_processing') == 'enabled'
    if not st.session_state.get('cv_ready'):
        agreed = st.checkbox('I checked this text and agree to send exactly this text for analysis',
                             key=f'consent_{digest}', disabled=not ready_to_send)
        if st.button('Continue: analyze my CV', type='primary', disabled=not (agreed and ready_to_send)):
            if st.session_state.get('consented_digest') != digest:
                try:
                    call(api.consent, digest)
                    st.session_state.consented_digest = digest
                except ApiError as exc:
                    st.error(exc.detail)
            if st.session_state.get('consented_digest') == digest and not st.session_state.get('parse_run'):
                run_id = billable('parse', api.parse_cv, cv=digest)
                if run_id:
                    st.session_state.parse_run = run_id
        if st.session_state.get('parse_run') and not st.session_state.get('cv_ready'):
            body = wait_run(st.session_state.parse_run, 'Preparing your sanitized CV…',
                            ['Parsing professional evidence from the approved text…'])
            if body['status'] == 'done':
                st.session_state.parse_result, st.session_state.cv_ready = body['result'], True
                st.rerun()
            else:
                st.session_state.pop('parse_run', None)

# ---------------------------------------------------------------- 2. Find Jobs / Check a Job -----------------
if preview and st.session_state.get('cv_ready'):
    digest = preview['digest']
    st.success('CV ready.')
    if st.session_state.get('analyze_error'):          # a failed Analyze Fit attempt, shown after the rerun
        st.error(st.session_state.pop('analyze_error'))
    analyses = st.session_state.setdefault('analyses', {})
    used = len(analyses)
    st.subheader('What do you want to do?')
    c1, c2 = st.columns(2)
    if c1.button('Find Jobs', type='primary', use_container_width=True, key='choose_find'):
        st.session_state.flow = 'find'
    if c2.button('Check a Job', use_container_width=True, key='choose_check'):
        st.session_state.flow = 'check'
    st.caption(f'{used} of {MAX_ANALYSES} job analyses used in this session.')

    def history_control(where: str) -> None:
        """The D-086 work-history answer, asked only where an Analyze Fit is about to happen (D-105).

        One answer per sanitized-CV digest, shared by Find Jobs and Check a Job. It is frozen at the first
        Analyze Fit click, before the request is sent, so a retry after a lost response keeps the same action
        (same answer, same idempotency key) and existing results never change underneath it. A new upload
        or edit is a new digest and starts unchecked again (reset_cv_state clears every history_ key).
        """
        frozen = st.session_state.get('history_locked', {})
        if digest in frozen:
            st.checkbox(HISTORY_LABEL, value=frozen[digest], disabled=True, key=f'history_fixed_{where}_{digest}')
            st.caption('Fixed for this CV version: every analysis of this CV uses the same answer. '
                       'Upload or edit your CV to change it.')
            return
        choice = st.session_state.setdefault('history_choice', {})
        choice[digest] = st.checkbox(HISTORY_LABEL, value=choice.get(digest, False), key=f'history_{where}_{digest}',
                                     help=HISTORY_HELP)

    def frozen_history() -> bool:
        """Freeze the answer for this digest at the first Analyze Fit attempt (before any request)."""
        frozen = st.session_state.setdefault('history_locked', {})
        if digest not in frozen:
            frozen[digest] = bool(st.session_state.get('history_choice', {}).get(digest, False))
        return frozen[digest]

    def analyze(kind: str, job_id: str, start, **ids):
        """Start one Analyze Fit; its run id is kept, so a rerun resumes polling and never posts again.

        ``start(key, history)`` sends the request; the history answer is frozen before it, so every retry of
        this action carries the same answer and therefore the same idempotency key.
        """
        if job_id not in analyses:
            history = frozen_history()
            run_id = billable(kind, lambda key: start(key, history), cv=digest, history=history, **ids)
            if not run_id:                 # rerun so the answer shows as fixed; the error is shown after it
                st.session_state.analyze_error = st.session_state.pop('billable_error', None)
                st.rerun()
            analyses[job_id] = {'run_id': run_id, 'result': None}
            st.session_state.selected_job = job_id
            st.rerun()                     # the counter updates; the result section below polls the run
        st.session_state.selected_job = job_id

    def corpus_job(job_id: str) -> bool:
        return not job_id.startswith('pasted:')

    def pasted_job(job_id: str) -> bool:
        return job_id.startswith('pasted:')

    def result_panel(owned) -> None:
        """The one place an Analyze Fit result is shown, for the selected job of this flow (``owned``).

        A pending run is only polled here (never posted again) and the finished result renders in this same
        panel, in view: Find Jobs shows it above the Relevant Jobs list, Check a Job below its button.
        """
        selected = st.session_state.get('selected_job')
        entry = analyses.get(selected) if selected and owned(selected) else None
        if entry is None:
            return
        if entry['result'] is None:                 # started (now or before a rerun): poll, never re-post
            body = wait_run(entry['run_id'], 'Analyzing this job against your CV…',
                            ['Extracting the job requirements…', 'Checking your CV evidence for each requirement…'])
            if body['status'] != 'done':
                analyses.pop(selected, None)
                return
            entry['result'] = body['result']        # the panel is already in view: render it right here
        with st.container(border=True):
            st.subheader('Analyze Fit result')
            title = safe(entry['result']['card'].get('title') or entry['result']['card']['job_id'])
            st.caption(f'Showing the analysis of {title}.' + (
                ' Other analyzed jobs: press "Show Analyze Fit result" on their card.' if owned is corpus_job else ''))
            analysis_view(entry['result'])
            if entry['result']['card']['scored']:
                with st.expander('Improve My CV for This Job'):
                    st.caption('Built only from your CV evidence and your own answers. Nothing is invented, and '
                               'answers never change the score; the score changes only after you update and '
                               're-upload your CV.')
                    card_id = entry['result']['card']['job_id']
                    coach_key = f"{entry['run_id']}:{card_id}"
                    coach = st.session_state.setdefault('coach', {})
                    if coach_key not in coach:
                        coach[coach_key] = call(api.coach, entry['run_id'], card_id)

                    def answer(gap_index, done, answers, run_id=entry['run_id'], job=card_id):
                        try:
                            return call(api.coach_answer, run_id, job, gap_index, done, answers)
                        except ApiError as exc:
                            st.error(exc.detail)
                            return None
                    coach_view(coach[coach_key], on_answer=answer)

    if st.session_state.get('flow') == 'find':
        st.subheader('Find Jobs')
        with st.form('find_jobs'):
            st.caption('All filters are optional. Leave them on Any to search every eligible job.')
            f1, f2, f3 = st.columns(3)
            family = f1.selectbox('Role family', ['Any', *ROLE_FAMILY], format_func=lambda v: ROLE_FAMILY.get(v, v))
            country = f2.selectbox('Country', ['Any', *COUNTRY], format_func=lambda v: COUNTRY.get(v, v),
                                   key='search_country')
            city = f3.text_input('City (blank = any)', max_chars=60)
            f4, f5, f6 = st.columns(3)
            experience = f4.selectbox('Experience requirement', ['Any', *EXPERIENCE],
                                      format_func=lambda v: EXPERIENCE.get(v, v))
            mode = f5.selectbox('Work mode', ['Any', *WORK_MODE], format_func=lambda v: WORK_MODE.get(v, v))
            posted = f6.selectbox('Posted within', ['Any time', '7 days', '30 days'])
            with st.expander('Advanced'):
                include_unknown = st.checkbox('Include jobs where this information is missing', value=True)
            submitted = st.form_submit_button('Find Jobs', type='primary', key='search_submit')
        if submitted:
            filters = {'role_family': None if family == 'Any' else family,
                       'country_code': None if country == 'Any' else country,
                       'city': city.strip() or None,
                       'experience_bucket': None if experience == 'Any' else experience,
                       'work_mode': None if mode == 'Any' else mode,
                       'posted_within_days': {'7 days': 7, '30 days': 30}.get(posted),
                       'include_unknown': include_unknown}
            with st.status('Searching relevant jobs…', expanded=False) as status:
                out = billable('search', lambda key: api.search_jobs(filters, key), cv=digest, filters=filters)
                status.update(label='Search finished' if out else 'Search stopped',
                              state='complete' if out else 'error')
            if out:
                for key in [k for k in st.session_state if k.startswith('refine_')]:
                    del st.session_state[key]
                st.session_state.search = out
        result = st.session_state.get('search')
        if result is not None:
            cards = result['jobs']
            st.markdown(f"**Relevant Jobs** (search stage): {safe(result['label'])}")
            result_panel(corpus_job)                # the selected job's result, above the list (in view)
            if not cards:
                st.warning('No jobs match these filters. Change the filters and search again; '
                           'nothing was widened automatically.')
            else:
                with st.expander('Refine these results (no new search)', expanded=False):
                    r1, r2, r3 = st.columns(3)
                    crit = {'role_family': r1.selectbox('Role family', ['', *options(cards, 'role_family')],
                                                        format_func=lambda v: ROLE_FAMILY.get(v, v) or 'Any',
                                                        key='refine_role'),
                            'country_code': r2.selectbox('Country', ['', *options(cards, 'country_code')],
                                                         format_func=lambda v: v or 'Any', key='refine_country'),
                            'city': r3.selectbox('City', ['', *options(cards, 'city')],
                                                 format_func=lambda v: v or 'Any', key='refine_city')}
                    r4, r5, r6 = st.columns(3)
                    crit['experience_bucket'] = r4.selectbox(
                        'Experience requirement', ['', *options(cards, 'experience_bucket')],
                        format_func=lambda v: EXPERIENCE.get(v, v) or 'Any', key='refine_experience')
                    crit['work_mode'] = r5.selectbox('Work mode', ['', *options(cards, 'work_mode')],
                                                     format_func=lambda v: WORK_MODE.get(v, v) or 'Any',
                                                     key='refine_mode')
                    crit['posted_within_days'] = r6.selectbox('Posted within', [None, 7, 30],
                                                              format_func=lambda v: f'{v} days' if v else 'Any time',
                                                              key='refine_posted')
                    keep_unknown = st.checkbox('Show jobs where this information is missing', value=True,
                                               key='refine_unknown')
                    st.caption('These controls only filter the jobs already shown. To broaden the search, change '
                               'the filters above and press Find Jobs again.')
                day = result.get('analysis_date')
                shown = refine(cards, crit, analysis_date=date.fromisoformat(day) if day else None,
                               include_unknown=keep_unknown)
                st.caption(f'Showing {len(shown)} of {len(cards)} relevant jobs, in search-relevance order. '
                           'Analyze a job to see how well your CV supports it.')
                history_control('find')
                for card in shown:
                    with st.container(border=True):
                        relevant_job_card(card)
                        job_id = card['job_id']
                        if job_id in analyses:
                            if st.session_state.get('selected_job') == job_id:
                                st.caption('Analyze Fit result shown above.')
                            elif st.button('Show Analyze Fit result', key=f'show_{job_id}'):
                                st.session_state.selected_job = job_id
                                st.rerun()          # the panel above already rendered: show the new choice
                        elif st.button('Analyze Fit', key=f'analyze_{job_id}', disabled=used >= MAX_ANALYSES):
                            analyze('corpus_job', job_id,
                                    lambda key, hist, j=job_id: api.analyze_job(j, hist, key), job=job_id)

    if st.session_state.get('flow') == 'check':
        st.subheader('Check a Job')
        st.caption('Paste a job description you found elsewhere. It stays in this session only, is treated as '
                   'data (never as instructions) and is never added to the job corpus.')
        jd = st.text_area('Job description', height=250, max_chars=20000, key='check_jd')
        history_control('check')
        if st.button('Analyze Fit for this job', type='primary', disabled=used >= MAX_ANALYSES):
            if len(jd.strip()) < 200:
                st.error('Please paste the full job description (at least 200 characters).')
            else:
                paste_ids = st.session_state.setdefault('paste_ids', {})
                text_key = hashlib.sha256(jd.encode()).hexdigest()       # a re-click reuses the same paste
                try:
                    paste_id = paste_ids.get(text_key) or call(api.paste, jd)
                    paste_ids[text_key] = paste_id
                    st.session_state.pasted = f'pasted:{paste_id}'
                    analyze('pasted_jd', st.session_state.pasted,
                            lambda key, hist: api.analyze_pasted(paste_id, hist, key), paste=paste_id)
                except ApiError as exc:
                    st.error(exc.detail)
        result_panel(pasted_job)                    # the pasted JD's result, directly below this flow

# ---------------------------------------------------------------- secondary: demo and market -----------------
st.divider()
with st.expander('Try with a demo CV (saved synthetic results; no upload)'):
    cvs = call(api.demo_cvs)
    names = {c['cv_id']: f"{c['cv_id']} (synthetic): {', '.join(c['experience']) or 'no work history'}" for c in cvs}
    chosen = st.selectbox('Choose a synthetic demo CV', list(names), format_func=names.get)
    st.session_state.chosen_cv = chosen
    seniority = st.toggle('Move jobs asking 3+ years down', value=True,
                          help='Early-career rule. Jobs are moved down, never removed.')
    live_mode = st.toggle('Live analysis (paid model calls)', value=False,
                          help='Off: demo with saved results, instant and free, unfiltered list only. '
                               'On: runs the real pipeline now (development only).')
    d1, d2, d3 = st.columns(3)
    country = d1.selectbox('Country (live demo only)', ['Any', 'ID', 'SG', 'MY'])
    mode = d2.selectbox('Work mode (live demo only)', ['Any', 'onsite', 'hybrid', 'remote'])
    posted = d3.selectbox('Posted within (live demo only)', ['Any time', '7 days', '30 days'])
    include_unknown = st.checkbox('Also show jobs where this information is missing', value=True,
                                  help='Missing is not the same as a match. These jobs are shown in their own block.')
    filters = {'country_code': None if country == 'Any' else country,
               'work_mode': None if mode == 'Any' else mode,
               'posted_within_days': {'7 days': 7, '30 days': 30}.get(posted),
               'include_unknown': include_unknown}
    with st.expander('Parsing summary (check before analysis)'):
        try:
            summary = call(api.demo_summary, chosen)
            st.write(f"Location suggestion: {summary.get('location_suggestion') or 'not found'} "
                     '(a suggestion only; it is never used as your confirmed location).')
            st.write('Sections found: ' + ', '.join(summary.get('sections_found', [])))
            rows = [{'Title': e.get('title'), 'Organization': e.get('organization'),
                     'Start': str(e.get('start') or e.get('start_partial') or ''),
                     'End': 'present' if e.get('is_present') else str(e.get('end') or e.get('end_partial') or '')}
                    for e in summary.get('employment', [])]
            st.dataframe(rows, hide_index=True, use_container_width=True)
            st.caption(summary.get('note', ''))
        except ApiError as exc:
            st.caption(f'Summary not available ({exc.status}).')
    with st.expander('Show CV text'):
        st.text(next(c['text'] for c in cvs if c['cv_id'] == chosen))
    if st.button('Find matching jobs'):
        action_key = None
        if live_mode:   # one key per user action, kept until the server acknowledges it
            action_key = actions.key_for(action_fingerprint(chosen, seniority, filters))
        try:
            run_id = call(api.start_run, chosen, seniority, filters if live_mode else None,
                          mode='live' if live_mode else 'saved', action_key=action_key)
        except ApiError as exc:
            st.error(exc.detail)
            st.stop()
        except httpx.HTTPError:
            st.error('Connection problem: press the button again to retry the same request '
                     '(it will not run twice).')
            st.stop()
        if live_mode:
            actions.acknowledged(run_id)
        bar = st.progress(0.0, text='Analyzing jobs...')      # real progress: finished jobs of K
        progress_box = st.empty()
        body = call(api.poll, run_id)
        k = (call(api.health) or {}).get('analyzed_k') or 10
        while body['status'] == 'running':
            done = body['progress']
            bar.progress(min(done / k, 1.0), text=f'Analyzed {done} of {k} jobs...')
            with progress_box.container():
                for card in body['partial'][-3:]:
                    st.caption(f"Done: {card.get('title') or card['job_id']}")
            time.sleep(POLL_SECONDS)
            body = call(api.poll, run_id)
        bar.empty()
        progress_box.empty()
        if body['status'] == 'failed':
            st.error(f"The analysis stopped ({body['error']}). No score was made up.")
        else:
            st.session_state.result = body['result']
            st.session_state.run_id = run_id
            st.session_state.pop('tailor', None)
    result = st.session_state.get('result')
    if result:
        if result.get('source') == 'saved_demo':
            st.info('Demo with saved results: computed earlier for this synthetic CV and this configuration.')
        versions = result.get('versions', {})
        st.write(f"{result.get('analyzed', versions.get('k'))} candidates from the search were analyzed "
                 f"(stage-1 search, then evidence matching). "
                 + (f"{len(result.get('demoted_by_seniority_rule', []))} job(s) moved down by the 3+ years rule."
                    if versions.get('seniority_rule') else 'The 3+ years rule is off.'))
        if result.get('empty_message'):
            st.warning(result['empty_message'])
        for block in result['blocks']:
            groups = block['groups']
            if len(result['blocks']) > 1:
                st.subheader(block['title'])
            st.subheader(f"Matches ({len(groups['matches'])})")
            for i, card in enumerate(groups['matches'], 1):
                job_card(card, i, api=api, run_id=st.session_state.get('run_id'))
            if groups['conflicts']:
                st.subheader(f"Possible conflict ({len(groups['conflicts'])})")
                st.caption('These jobs ask for more years than your whole confirmed work history. '
                           'The score is unchanged; they are listed after the other scored jobs.')
                for i, card in enumerate(groups['conflicts'], 1):
                    job_card(card, i, api=api, run_id=st.session_state.get('run_id'))
            if groups['not_fully_analyzed']:
                st.subheader(f"Could not be fully analyzed ({len(groups['not_fully_analyzed'])})")
                for i, card in enumerate(groups['not_fully_analyzed'], 1):
                    job_card(card, i, api=api, run_id=st.session_state.get('run_id'))
        st.subheader('CV suggestions')
        if st.button('Show suggestions from these results'):
            st.session_state.tailor = call(api.tailor, st.session_state.run_id)
        if st.session_state.get('tailor'):
            suggestions(st.session_state.tailor)
        scored = [c for b in result['blocks'] for g in b['groups'].values() for c in g if c['scored']]
        if scored:
            pick = st.selectbox('Improve the CV for one demo job', [c['job_id'] for c in scored],
                                format_func=lambda j: next(c.get('title') or j for c in scored if c['job_id'] == j))
            demo_coach = call(api.coach_questions, st.session_state.run_id, pick)

            def demo_answer(gap_index, done, answers, run_id=st.session_state.run_id, job=pick):
                try:
                    return call(api.coach_answer, run_id, job, gap_index, done, answers)
                except ApiError as exc:
                    st.error(exc.detail)
                    return None
            coach_view(demo_coach, on_answer=demo_answer)
        st.caption(f"Versions: {versions}")

with st.expander('Explore market skills'):
    family = st.selectbox('Role family (market)', ['All', 'ai_ml_engineering', 'data_science', 'genai_llm',
                                                   'software_ai'])
    out = call(api.market, None if family == 'All' else family, 15)
    st.write(out['explanation'])
    st.bar_chart({r['skill']: r['jobs'] for r in out['skills']}, horizontal=True)
    st.caption('Source: ' + out['source'])
