"""Job card, constraint line, evidence table, honest labels. Rendering only, no business logic.

Text from job postings and CVs is untrusted: it is escaped before Markdown rendering, so it
cannot add links, images (remote loading) or formatting. Tables and st.text show it as data.
"""
from __future__ import annotations

import re

import streamlit as st

STATUS = {'final': 'Score', 'provisional': 'Provisional score', 'on_hold': 'Not fully analyzed',
          'no_score': 'No score'}
LABEL = {'MATCH': 'Supported', 'PARTIAL': 'Partly supported', 'NO_MATCH': 'Not found in CV', None: 'Not checked'}
REASONS = {'relevant': 'Relevant', 'not_relevant_role': 'Wrong role', 'too_senior': 'Too senior',
           'wrong_evidence': 'Evidence is wrong', 'missing_requirement': 'A requirement is missing', 'other': 'Other'}


def safe(text) -> str:
    """Escape Markdown so untrusted text renders as plain words."""
    return re.sub(r'([\\`*_{}\[\]()#+\-.!|<>~])', r'\\\1', str(text or ''))


def job_card(card: dict, rank: int, *, api=None, run_id: str | None = None) -> None:
    title = safe(card.get('title') or card['job_id'])
    company = safe(card.get('company') or '')
    with st.container(border=True):
        left, right = st.columns([4, 1])
        left.markdown(f"**{rank}. {title}**  \n{company} · {safe(card.get('location') or 'location not stated')}")
        if card['scored']:
            right.metric(STATUS[card['status']], f"{card['score_pct']:.0f}%")
            right.caption(f"{card['matched']} supported, {card['partial']} partly, of {card['required_total']} required")
        else:
            right.markdown(f"**{STATUS[card['status']]}**")
        for msg in card['explicit_conflicts']:
            st.warning('Possible conflict: ' + msg)
        if card.get('hold_reason'):
            st.info(card['hold_reason'])
        if card.get('excluded_units'):
            st.caption(f"{len(card['excluded_units'])} requirement(s) need checking and are listed but not scored.")
        soft = card['soft_skills']
        if soft['total']:
            st.caption(f"Soft skills (shown separately, not in the %): {soft['matched']} supported, "
                       f"{soft['partial']} partly, of {soft['total']}")
        if card['requirements']:
            with st.expander('Evidence per requirement'):
                rows = [{'Requirement': r['requirement'], 'Type': r['importance'],
                         'Result': LABEL.get(r['label'], r['label']),
                         'CV quote': ' | '.join(r['cv_quotes'])} for r in card['requirements']]
                st.dataframe(rows, hide_index=True, use_container_width=True)
        if api is not None and card['job_id'] != 'pasted':
            with st.expander('Job posting'):
                key = f"job_{card['job_id']}"
                if st.button('Load posting text', key=f'load_{run_id}_{key}'):
                    try:
                        st.session_state[key] = api.job(card['job_id'])
                    except Exception as exc:
                        st.session_state[key] = {'description': f'Could not load the posting ({type(exc).__name__}).'}
                if key in st.session_state:
                    st.text(st.session_state[key].get('description') or '')
        if card.get('url'):
            st.link_button('Open job posting', card['url'])
        if api is not None and run_id:
            c1, c2, c3 = st.columns([1, 2, 1])
            reason = c2.selectbox('Reason', list(REASONS), format_func=REASONS.get,
                                  key=f"reason_{run_id}_{card['job_id']}", label_visibility='collapsed')
            if c1.button('Useful', key=f"up_{run_id}_{card['job_id']}"):
                api.feedback(run_id, card['job_id'], 'useful', reason)
                st.toast('Thanks, feedback saved (rating and reason only).')
            if c3.button('Not useful', key=f"down_{run_id}_{card['job_id']}"):
                api.feedback(run_id, card['job_id'], 'not_useful', reason)
                st.toast('Thanks, feedback saved (rating and reason only).')


def suggestions(out: dict) -> None:
    st.caption(out['guard'])
    if not out['items']:
        st.write('No suggestions: no partly supported or missing required items in the scored jobs.')
    for item in out['items']:
        with st.container(border=True):
            st.markdown(f"**{safe(item['requirement'])}** · asked by {item['jobs_asking']} analyzed job(s)")
            st.write(item['advice'])
            for q in item['cv_quotes']:
                st.caption('From your CV: ' + q)


# --- D-105 product flow: Relevant Jobs (search stage) and Analyze Fit (evidence stage) ---------------------
ROLE_FAMILY = {'ai_ml_engineering': 'AI / ML Engineering', 'data_science': 'Data Science',
               'genai_llm': 'GenAI / LLM', 'software_ai': 'Software-AI'}
EXPERIENCE = {'entry': 'Entry', '1-2y': '1–2 years', '3-4y': '3–4 years', '5y+': '5+ years'}
WORK_MODE = {'onsite': 'Onsite', 'hybrid': 'Hybrid', 'remote': 'Remote'}


def relevant_job_card(card: dict) -> None:
    """One search-stage job: metadata only. No score (retrieval rank is search relevance, not fit)."""
    meta = [ROLE_FAMILY.get(card.get('role_family'), 'Role family not stated'),
            safe(card.get('location') or 'location not stated'),
            WORK_MODE.get(card.get('work_mode'), 'work mode not stated'),
            'Experience requirement: ' + EXPERIENCE.get(card.get('experience_bucket'), 'not stated'),
            'posted ' + str(card.get('posted_at') or 'date not stated')[:10]]
    st.markdown(f"**#{card['retrieval_rank']} {safe(card.get('title') or card['job_id'])}**  \n"
                f"{safe(card.get('company') or '')}")
    st.caption(' · '.join(meta) + ('  ·  some filter information is missing in this posting'
                                   if card.get('filter_status') == 'unknown' else ''))
    if card.get('url'):
        st.link_button('Open job posting', card['url'])


def analysis_view(result: dict) -> None:
    """One Analyze Fit result: evidence coverage, per-requirement evidence, strengths, gaps, honest holds."""
    card = result['card']
    st.markdown(f"#### {safe(card.get('title') or card['job_id'])}")
    if card.get('company') or card.get('location'):
        st.caption(' · '.join(safe(x) for x in (card.get('company'), card.get('location')) if x))
    if card['scored']:
        st.metric('Evidence coverage', f"{card['score_pct']:.0f}%")
        st.caption(f"{card['matched']} supported, {card['partial']} partly supported, of {card['required_total']} "
                   'required. This is how much of the job your CV evidence supports, not a hiring probability.')
    else:
        st.warning('This job could not be fully analyzed, so no score is shown (none was made up).')
        if card.get('hold_reason'):
            st.info(card['hold_reason'])
    for msg in card['explicit_conflicts']:
        st.warning('Experience conflict: ' + msg)
    required = [r for r in card['requirements'] if r.get('importance') == 'required']
    strengths = [r for r in required if r['label'] == 'MATCH']
    gaps = [r for r in required if r['label'] in ('PARTIAL', 'NO_MATCH')]
    if strengths:
        st.markdown('**Strengths (supported by your CV)**')
        for r in strengths:
            st.markdown(f"- {safe(r['requirement'])}")
    if gaps:
        st.markdown('**Gaps (partly supported or not found)**')
        for r in gaps:
            st.markdown(f"- {safe(r['requirement'])}: {LABEL.get(r['label'], r['label'])}")
    if card.get('excluded_units'):
        st.caption(f"{len(card['excluded_units'])} requirement(s) need checking and are listed but not scored.")
    if card['requirements']:                # exact CV quotes per requirement; no posting lookup, no extra request
        with st.expander('Evidence per requirement', expanded=True):
            rows = [{'Requirement': r['requirement'], 'Type': r['importance'],
                     'Result': LABEL.get(r['label'], r['label']), 'CV quote': ' | '.join(r['cv_quotes'])}
                    for r in card['requirements']]
            st.dataframe(rows, hide_index=True, use_container_width=True)
    if card.get('url'):
        st.link_button('Open job posting', card['url'])


def coach_view(coach: dict, *, on_answer) -> None:
    """Improve My CV for This Job: four exclusive categories; B builds a bullet only from the answers."""
    st.caption(coach['rules'])
    if coach['representation']:
        st.markdown('**A. Make existing evidence clearer**')
        for item in coach['representation']:
            with st.container(border=True):
                st.markdown(safe(item['asked']))
                for quote in item['current']:
                    st.caption('Your CV now: ' + quote)
                st.write(item['guidance'])
    if coach['gaps']:
        st.markdown('**B. Possibly missing from your CV**')
        for gap in coach['gaps']:
            with st.container(border=True):
                st.markdown(f"**{safe(gap['requirement'])}**")
                key = f"{coach['job_id']}_{gap['gap_index']}"
                done = st.radio(gap['question_first'], ['Yes', 'No'], index=None, horizontal=True, key=f'done_{key}')
                answers = {}
                if done == 'Yes':
                    for qk, qtext in gap['questions'].items():
                        answers[qk] = st.text_input(qtext, key=f'{qk}_{key}', max_chars=300)
                if done and st.button('Draft', key=f'draft_{key}'):
                    out = on_answer(gap['gap_index'], done == 'Yes', answers)
                    if out and out.get('bullet'):
                        st.text_area('Edit if needed, then copy it into your CV', out['bullet'], key=f'bullet_{key}')
                        st.caption(out['note'])
                    elif out:
                        for idea in out['ideas']:
                            st.write('- ' + idea)
    if coach['true_gaps']:
        st.markdown('**C. True gaps (facts, not wording)**')
        for gap in coach['true_gaps']:
            st.warning(f"{gap['conflict']}  \n{gap['note']}")
    if coach['not_verified']:
        st.markdown('**Not verified from this CV**')
        for item in coach['not_verified']:
            st.caption(f"{safe(item['requirement'])}: {item['note']}")
    if not any(coach[k] for k in ('representation', 'gaps', 'true_gaps', 'not_verified')):
        st.write('Nothing to improve for this job from the required items.')
