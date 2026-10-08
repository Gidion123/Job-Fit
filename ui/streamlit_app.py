"""JobFit Streamlit UI. Calls the API only (no business logic here).

Run: uvicorn jobfit.api.wiring:create_default_app --factory --app-dir src   (API)
     streamlit run ui/streamlit_app.py                                      (UI)
Privacy UX (D-051): pre-upload notice, editable masked preview, consent for the exact text,
"Hentikan & hapus sesi", a liveness heartbeat while the page is open, and honest expiry messages.
"""
from __future__ import annotations

import time

import streamlit as st

from api_client import ApiClient, ApiError
from components import job_card, safe, suggestions

st.set_page_config(page_title='JobFit', layout='wide')


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


@st.fragment(run_every=30)
def liveness():
    """Browser liveness: runs only while this page is open and connected. It keeps the
    2-minute lease alive but does not count as activity, so the 30-minute idle limit still applies."""
    try:
        api.heartbeat()
    except Exception:
        pass


liveness()

st.title('JobFit')
st.caption('Find AI and data jobs that fit your CV, and see which requirements your CV supports. '
           'The match % is CV evidence coverage, not a hiring probability.')

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
    seniority = st.toggle('Move jobs asking 3+ years down', value=True,
                          help='Early-career rule. Jobs are moved down, never removed.')
    live_mode = st.toggle('Live analysis (paid model calls)', value=False,
                          help='Off: demo with saved results, instant and free, unfiltered list only. '
                               'On: runs the real pipeline now.')
    st.subheader('Optional filters (live analysis only)')
    country = st.selectbox('Country', ['Any', 'ID', 'SG', 'MY'], help='From the job posting metadata')
    mode = st.selectbox('Work mode', ['Any', 'onsite', 'hybrid', 'remote'])
    posted = st.selectbox('Posted within', ['Any time', '7 days', '30 days'])
    include_unknown = st.checkbox('Also show jobs where this information is missing', value=True,
                                  help='Missing is not the same as a match. These jobs are shown in their own block.')
    filters = {'country_code': None if country == 'Any' else country,
               'work_mode': None if mode == 'Any' else mode,
               'posted_within_days': {'7 days': 7, '30 days': 30}.get(posted),
               'include_unknown': include_unknown}

demo_tab, paste_tab, market_tab, upload_tab = st.tabs(['Demo CVs', 'Paste a job', 'Market', 'Upload your CV'])

with demo_tab:
    cvs = call(api.demo_cvs)
    names = {c['cv_id']: f"{c['cv_id']} (synthetic): {', '.join(c['experience']) or 'no work history'}" for c in cvs}
    chosen = st.selectbox('Choose a synthetic demo CV', list(names), format_func=names.get)
    st.session_state.chosen_cv = chosen
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
        import uuid
        action_key = str(uuid.uuid4())       # one key per click; a retry of this action reuses it
        try:
            run_id = call(api.start_run, chosen, seniority, filters if live_mode else None,
                          mode='live' if live_mode else 'saved', action_key=action_key)
        except ApiError as exc:
            st.error(exc.detail)
            st.stop()
        bar = st.progress(0.0, text='Analyzing jobs...')
        progress_box = st.empty()
        body = call(api.poll, run_id)
        k = (call(api.health) or {}).get('analyzed_k') or 10
        while body['status'] == 'running':
            done = body['progress']
            bar.progress(min(done / k, 1.0), text=f'Analyzed {done} of {k} jobs...')
            with progress_box.container():
                for card in body['partial'][-3:]:
                    st.caption(f"Done: {card.get('title') or card['job_id']}")
            time.sleep(1.5)
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
                st.header(block['title'])
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
            with st.expander('CV coach for one job (your answers only, never invented)'):
                pick = st.selectbox('Job', [c['job_id'] for c in scored],
                                    format_func=lambda j: next(c.get('title') or j for c in scored if c['job_id'] == j))
                coach = call(api.coach_questions, st.session_state.run_id, pick)
                st.caption(coach['rules'])
                if not coach['gaps']:
                    st.write('No gap to coach for this job.')
                for gap in coach['gaps']:
                    st.markdown(f"**{safe(gap['requirement'])}**")
                    done = st.radio(gap['question_first'], ['Yes', 'No'], index=None, horizontal=True,
                                    key=f"done_{pick}_{gap['gap_index']}")
                    answers = {}
                    if done == 'Yes':
                        for qk, qtext in gap['questions'].items():
                            answers[qk] = st.text_input(qtext, key=f"{qk}_{pick}_{gap['gap_index']}", max_chars=300)
                    if done and st.button('Draft', key=f"draft_{pick}_{gap['gap_index']}"):
                        try:
                            out = call(api.coach_answer, st.session_state.run_id, pick, gap['gap_index'],
                                       done == 'Yes', answers)
                            if out['bullet']:
                                st.text_area('Edit if needed, then copy it into your CV', out['bullet'],
                                             key=f"bullet_{pick}_{gap['gap_index']}")
                                st.caption(out['note'])
                            else:
                                for idea in out['ideas']:
                                    st.write('- ' + idea)
                        except ApiError as exc:
                            st.error(exc.detail)
        st.caption(f"Versions: {versions}")

with paste_tab:
    st.write('Paste a job description to compare it with the chosen demo CV. The text stays in this session only, '
             'is treated as data (never as instructions) and is analyzed live (paid model calls).')
    jd = st.text_area('Job description', height=250, max_chars=20000)
    if st.button('Compare with the demo CV'):
        if len(jd.strip()) < 200:
            st.error('Please paste the full job description (at least 200 characters).')
        else:
            try:
                pid = call(api.paste, jd)
                run_id = call(api.analyze, pid, st.session_state.get('chosen_cv', 'CV1'))
                with st.spinner('Extracting requirements and checking evidence...'):
                    body = call(api.poll, run_id)
                    while body['status'] == 'running':
                        time.sleep(1.5)
                        body = call(api.poll, run_id)
                if body['status'] == 'failed':
                    st.error(f"The analysis stopped ({body['error']}). No score was made up.")
                else:
                    st.session_state.paste_result = body['result']
            except ApiError as exc:
                st.error(exc.detail)
    if st.session_state.get('paste_result'):
        job_card(st.session_state.paste_result['card'], 1)
        st.caption(st.session_state.paste_result['note'])

with market_tab:
    family = st.selectbox('Role family', ['All', 'ai_ml_engineering', 'data_science', 'genai_llm', 'software_ai'])
    out = call(api.market, None if family == 'All' else family, 15)
    st.write(out['explanation'])
    st.bar_chart({r['skill']: r['jobs'] for r in out['skills']}, horizontal=True)
    st.caption('Source: ' + out['source'])

with upload_tab:
    st.markdown('**Before you upload:** the JobFit server temporarily receives your file to read it. '
                'Names, emails, phone numbers, profile links and ID numbers are then masked locally, '
                'and you see the exact text that would be used. Masking can miss things, so please check it. '
                'Nothing is sent to an AI provider without your consent.')
    file = st.file_uploader('PDF, DOCX or text', type=['pdf', 'docx', 'txt', 'md'])
    if file is not None and st.session_state.get('upload_id') != file.file_id:
        try:
            st.session_state.preview = call(api.upload, file.name, file.getvalue())
            st.session_state.upload_id = file.file_id
            st.session_state.consented = False
        except ApiError as exc:
            st.error(exc.detail)
    preview = st.session_state.get('preview')
    if preview:
        edited = st.text_area('Masked text (you can correct it, for example to mask a name the detector missed)',
                              preview['masked_text'], height=300)
        if edited != preview['masked_text'] and st.button('Use my corrected text'):
            st.session_state.preview = call(api.edit_preview, edited)
            st.session_state.consented = False
            st.rerun()
        for w in preview['warnings']:
            st.caption(w)
        if preview['message']:
            st.info(preview['message'])
        if st.checkbox('I checked the masked text and agree to send exactly this text for analysis',
                       key=f"consent_{preview['digest']}") and not st.session_state.get('consented'):
            out = call(api.consent, preview['digest'])
            st.session_state.consented = True
            if out['message']:
                st.info(out['message'])
