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
