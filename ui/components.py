"""Job rows, the Analyze Fit view, the coach and the demo cards. Rendering only, no business logic.

Text from job postings, CVs and the API is untrusted: it reaches the page only through ``theme.esc``
inside ``st.html`` blocks (never Markdown), or as widget labels and table cells, which show it as
plain text. It cannot add links, images (remote loading) or formatting.
"""
from __future__ import annotations

import re
from datetime import date

import streamlit as st

from texts import api_text, t
from theme import badge, blockquote, esc, html, icon, notice, section_head, tag

ROLES = ('ai_ml_engineering', 'data_science', 'genai_llm', 'software_ai')
EXPERIENCE = ('entry', '1-2y', '3-4y', '5y+')
WORK_MODES = ('onsite', 'hybrid', 'remote')
COUNTRIES = ('ID', 'SG', 'MY', 'PH', 'US')
STATUS = ('final', 'provisional', 'on_hold', 'no_score')
REASONS = ('relevant', 'not_relevant_role', 'too_senior', 'wrong_evidence', 'missing_requirement', 'other')


def _label(prefix: str, value, known) -> str | None:
    return t(f'{prefix}.{value}') if value in known else None


def role_label(value) -> str:
    return _label('role', value, ROLES) or t('job.role.none')


def experience_label(value) -> str:
    return _label('experience', value, EXPERIENCE) or str(value)


def mode_label(value) -> str:
    return _label('mode', value, WORK_MODES) or t('job.mode.none')


def country_label(value) -> str:
    return _label('country', value, COUNTRIES) or str(value)


def option_label(field: str):
    """format_func for a filter select box ('' / None / 'Any' = no filter)."""
    labels = {'role_family': role_label, 'country_code': country_label, 'experience_bucket': experience_label,
              'work_mode': mode_label}.get(field, str)
    return lambda v: t('filter.any') if v in ('', None, 'Any') else labels(v)


def posted_text(raw, analysis_date: date | None) -> str:
    if not raw or str(raw).strip().lower() in ('unknown', 'not stated', 'none'):
        return t('job.date.none')
    try:
        posted = date.fromisoformat(str(raw)[:10])
    except ValueError:
        return t('job.date.none')
    if analysis_date is None or posted > analysis_date:
        return t('job.date.on', date=posted.isoformat())
    days = (analysis_date - posted).days
    return t('job.date.today') if days == 0 else t('job.date', n=days)


def metadata_html(card: dict, analysis_date: date | None = None) -> str:
    """Search-stage metadata of one job; every missing value is shown as missing, never guessed."""
    experience = card.get('experience_bucket')
    first = [icon('location') + esc(card.get('location') or t('job.location.none')),
             esc(mode_label(card.get('work_mode'))),
             esc(t('job.experience', x=experience_label(experience)) if experience in EXPERIENCE
                 else t('job.experience.none'))]
    second = [esc(role_label(card.get('role_family'))), esc(posted_text(card.get('posted_at'), analysis_date))]
    if card.get('filter_status') == 'unknown':
        second.append(esc(t('job.missing')))
    row = lambda items: '<div class="jf-metadata">' + ''.join(f'<span>{x}</span>' for x in items) + '</div>'  # noqa: E731
    return row(first) + row(second)


def relevant_job_html(card: dict, position: int, analysis_date: date | None = None) -> str:
    """One search-stage job: metadata only. No score (retrieval rank is search relevance, not fit)."""
    title = esc(card.get('title') or card['job_id'])
    return (f'<div class="jf" data-job="{esc(card["job_id"])}" data-rank="{esc(card.get("retrieval_rank"))}">'
            f'<div class="jf-job-title"><div><div class="jf-h3" role="heading" aria-level="3">{title}</div>'
            f'<p class="jf-company">{esc(card.get("company") or "")}</p></div>'
            f'<span class="jf-job-number">{position:02d}</span></div>{metadata_html(card, analysis_date)}</div>')


# ------------------------------------------------------------------------------- Analyze Fit view ------------
def _groups(result: dict, card: dict) -> dict:
    groups = result.get('requirement_groups')
    if groups is None:                   # an older result without the grouping: the previous two sections
        required = [r for r in card['requirements'] if r.get('importance') == 'required']
        groups = {'strengths': [r['unit_id'] for r in required if r['label'] == 'MATCH'],
                  'gaps': [r['unit_id'] for r in required if r['label'] in ('PARTIAL', 'NO_MATCH')],
                  'not_verified': [], 'conflict': []}
    return groups


def _status(row: dict, groups: dict) -> str:
    unit = row.get('unit_id')
    if unit in groups.get('conflict', []):
        return 'CONFLICT'
    if unit in groups.get('not_verified', []):
        return 'UNVERIFIED'
    return row.get('label') if row.get('label') in ('MATCH', 'PARTIAL', 'NO_MATCH') else 'UNCHECKED'


REASON_KEY = {'MATCH': 'reason.match', 'PARTIAL': 'reason.partial', 'NO_MATCH': 'reason.none',
              'UNVERIFIED': 'reason.unverified', 'CONFLICT': 'reason.conflict', 'UNCHECKED': 'reason.unchecked'}


def requirement_html(row: dict, status: str, flagged: bool = False) -> str:
    kind = {'required': 'req.required', 'preferred': 'req.preferred'}.get(row.get('importance'), 'req.other')
    quotes = ''.join(blockquote(q) for q in row.get('cv_quotes') or [])
    quote_block = f'<span class="jf-quote-label">{esc(t("req.quoteLabel"))}</span>{quotes}' if quotes else ''
    return (f'<article class="jf-requirement" data-status="{status}"><div class="jf-requirement-head"><div>'
            f'<div class="jf-h3" role="heading" aria-level="3">{esc(row["requirement"])}</div>'
            f'<span class="jf-small jf-muted">{esc(t(kind))}</span></div>'
            f'{badge(None if status == "UNCHECKED" else status)}</div>{quote_block}'
            f'<p>{esc(t(REASON_KEY[status]))}</p>'
            + (f'<p class="jf-flagged"><strong>{esc(t("req.flagged"))}</strong></p>' if flagged else '')
            + '</article>')


def reason_texts(card: dict) -> list[str]:
    """The API's score reasons in the interface language; unit ids become their requirement text."""
    names = {r.get('unit_id'): r['requirement'] for r in card.get('requirements', []) if r.get('unit_id')}

    def items(text):
        ids = re.findall(r'\b[A-Z]\d{2,}\b', text)
        return '; '.join(names.get(u, u) for u in ids)
    out = []
    for reason in card.get('reasons') or []:
        if reason.startswith('An experience, level or education requirement needs checking'):
            out.append(t('reason.protected', items=items(reason)))
        elif reason.startswith('More than 20 percent'):
            out.append(t('reason.over20'))
        elif reason.startswith('Required units not judged yet'):
            out.append(t('reason.notjudged', items=items(reason)))
        elif reason.startswith('JD looks incomplete'):
            out.append(t('reason.incomplete'))
        elif reason.startswith('Not enough information'):
            out.append(t('reason.norequired'))
        elif reason.startswith('Evidence matching did not finish'):
            out.append(t('reason.matching', code=reason.split(':', 1)[-1].strip()))
        elif reason.startswith('JD extraction not available'):
            out.append(t('reason.extraction', code=reason.split(':', 1)[-1].strip()))
        elif reason.startswith('Held: the job requirements are larger than'):
            out.append(t('reason.envelope'))
        elif reason.startswith('Some requirements need checking'):
            excluded = '; '.join(str(u.get('text') or u.get('unit_id')) if isinstance(u, dict) else str(u)
                                 for u in card.get('excluded_units') or [])
            out.append(t('reason.excluded', items=excluded) if excluded else reason)
        elif m := re.match(r'(\d+) requirement\(s\) not clearly required or preferred', reason):
            out.append(t('reason.unknownimportance', n=m.group(1)))
        else:
            out.append(reason)
    return out


def coverage_html(card: dict) -> str:
    if not card['scored']:
        why = reason_texts(card)
        hold = (f'<p class="jf-small jf-mt4"><strong>{esc(t("hold.why"))}</strong></p><ul>'
                + ''.join(f'<li>{esc(w)}</li>' for w in why) + '</ul>') if why else ''
        if card.get('hold_reason') and card['hold_reason'] not in (card.get('reasons') or []):
            hold += f'<p class="jf-small">{esc(card["hold_reason"])}</p>'     # shown once, never twice
        hold += f'<p class="jf-small jf-mt4">{esc(t("hold.note"))}</p>'
        return notice(f'<strong>{esc(t("hold.h"))}</strong><p>{esc(t("hold.p"))}</p>{hold}', 'warn')
    total = card['required_total']
    missing = max(total - card['matched'] - card['partial'], 0)
    provisional = ''
    if card.get('status') == 'provisional':
        why = reason_texts(card)
        provisional = (f'<p class="jf-small jf-muted">{esc(t("coverage.provisional"))}</p>'
                       + (f'<p class="jf-small jf-muted"><strong>{esc(t("provisional.why"))}</strong></p><ul '
                          f'class="jf-small jf-muted">' + ''.join(f'<li>{esc(w)}</li>' for w in why) + '</ul>'
                          if why else ''))
    return (f'<section class="jf jf-coverage" aria-label="{esc(t("coverage.label"))}"><div>'
            f'<strong class="jf-coverage-value">{card["score_pct"]:.0f}<span>%</span></strong>'
            f'<span class="jf-small jf-muted">{esc(t("coverage.label"))}</span></div><div>'
            f'<div class="jf-h2" role="heading" aria-level="2">{esc(t("coverage.h2"))}</div>'
            f'<p class="jf-disclaimer">{esc(t("coverage.disclaimer"))}</p>'
            f'<p class="jf-small jf-muted">{esc(t("coverage.counts", a=card["matched"], b=card["partial"], c=missing))}'
            f'</p><p class="jf-small jf-muted">{esc(t("coverage.basis", n=total))}</p>{provisional}</div></section>')


def overview_html(strengths: list[dict], gaps: list[dict]) -> str:
    def items(rows, empty):
        if not rows:
            return f'<p class="jf-small jf-muted">{esc(empty)}</p>'
        return '<ul>' + ''.join(f'<li>{esc(r["requirement"])}</li>' for r in rows) + '</ul>'
    return (f'<div class="jf jf-overview"><div class="jf-group" data-group="strengths">'
            f'<div class="jf-h4" role="heading" aria-level="3">{esc(t("side.strong.h3"))}</div>'
            f'{items(strengths, t("side.strong.empty"))}</div><div class="jf-group" data-group="gaps">'
            f'<div class="jf-h4" role="heading" aria-level="3">{esc(t("side.gaps.h3"))}</div>'
            f'{items(gaps, t("side.gaps.empty"))}<p class="jf-small jf-muted jf-mt4">{esc(t("side.gaps.note"))}</p>'
            f'</div></div>')


def analysis_view(result: dict, *, aside=None) -> None:
    """One Analyze Fit result: evidence coverage, evidence per requirement, strengths, gaps and honest holds.

    ``aside()`` renders extra widgets (next step, quota) below the overview in the side column.
    """
    card = result['card']
    groups = _groups(result, card)
    by_unit = {r['unit_id']: r for r in card['requirements'] if r.get('unit_id')}
    strengths = [by_unit[u] for u in groups['strengths'] if u in by_unit]
    gaps = [by_unit[u] for u in groups['gaps'] if u in by_unit]
    unverified = [by_unit[u] for u in groups['not_verified'] if u in by_unit]
    html(coverage_html(card))
    left, right = st.columns([2.7, 1], gap='large')
    with left:
        rows = sorted(card['requirements'], key=lambda r: r.get('importance') != 'required')   # stable: JD order
        flagged = set() if card['scored'] else {u for reason in card.get('reasons') or []
                                                 for u in re.findall(r'\b[A-Z]\d{2,}\b', reason)}
        body = ''.join(requirement_html(r, _status(r, groups), r.get('unit_id') in flagged) for r in rows)
        html(f'<div class="jf">{section_head(esc(t("req.h2")), esc(t("req.meta")))}'
             f'<div class="jf-requirements jf-mt4">{body}</div></div>')
        if card['explicit_conflicts']:
            items = ''.join(f'<li>{esc(m)}</li>' for m in card['explicit_conflicts'])
            html(f'<section class="jf jf-fact conflict" data-group="conflict">{badge("CONFLICT")}'
                 f'<div class="jf-h3" role="heading" aria-level="3">{esc(t("exp.h3"))}</div><ul>{items}</ul>'
                 f'<p class="jf-small jf-mt4">{esc(t("exp.conflict"))}</p></section>')
        if unverified:
            items = ''.join(f'<li>{esc(r["requirement"])}</li>' for r in unverified)
            html(f'<section class="jf jf-fact" data-group="not_verified">{badge("UNVERIFIED")}'
                 f'<div class="jf-h3" role="heading" aria-level="3">{esc(t("unverified.h3"))}</div>'
                 f'<p>{esc(t("unverified.p"))}</p><ul>{items}</ul></section>')
        notes = []
        if card.get('excluded_units'):
            notes.append(t('excluded', n=len(card['excluded_units'])))
        soft = card.get('soft_skills') or {}
        if soft.get('total'):
            notes.append(t('soft', a=soft['matched'], b=soft['partial'], n=soft['total']))
        if notes:
            html('<div class="jf">' + ''.join(f'<p class="jf-small jf-muted">{esc(n)}</p>' for n in notes) + '</div>')
        if card['scored']:
            with st.expander(t('calc.summary')):
                html(f'<div class="jf"><p>{esc(t("calc.body", n=card["required_total"]))}</p>'
                     f'<p class="jf-small jf-muted jf-mt4">{esc(t("calc.note"))}</p></div>')
    with right:
        html(overview_html(strengths, gaps))
        if aside is not None:
            aside()


# ----------------------------------------------------------------------------- Improve My CV (coach) ----------
QUESTION_KEYS = ('what_when', 'own_part', 'tools', 'result')
REQUIRED_ANSWERS = ('what_when', 'own_part')        # what jobfit.support.cv_coach.bullet requires


def _question(key: str, api_text_value: str) -> tuple[str, str]:
    if key in QUESTION_KEYS:
        return t(f'coach.q.{key}'), t(f'coach.q.{key}.hint')
    return api_text_value, ''


def coach_view(coach: dict, *, on_answer, scope: str | None = None) -> None:
    """Improve My CV for This Job: four exclusive categories; B builds a bullet only from the user's answers."""
    scope = scope or str(coach['job_id'])
    if coach['representation']:
        html(f'<div class="jf">{section_head(esc(t("coach.partial.h2")), tag(esc(t("badge.PARTIAL")), "partial"))}'
             '</div>')
        for item in coach['representation']:
            quotes = ''.join(blockquote(q) for q in item['current'])
            current = f'<span class="jf-quote-label">{esc(t("coach.item.current"))}</span>{quotes}' if quotes else ''
            html(f'<article class="jf jf-coach-item" data-category="A">'
                 f'<p class="jf-small jf-muted">{esc(t("coach.item.asks"))}</p>'
                 f'<div class="jf-h3" role="heading" aria-level="3">{esc(item["requirement"])}</div>{current}'
                 f'<p class="jf-description">{esc(api_text(item["guidance"]))}</p></article>')
    if coach['gaps']:
        html(f'<div class="jf jf-mt6">{section_head(esc(t("coach.missing.h2")))}'
             f'<p class="jf-muted jf-mt4">{esc(t("coach.missing.p"))}</p></div>')
        for gap in coach['gaps']:
            _gap(gap, f"{scope}_{gap['gap_index']}", on_answer)
    if coach['true_gaps']:
        items = ''.join(f'<li>{esc(g["conflict"])}<br><span class="jf-small">{esc(api_text(g["note"]))}</span></li>'
                        for g in coach['true_gaps'])
        html(f'<section class="jf jf-fact conflict" data-category="C">{badge("CONFLICT")}'
             f'<div class="jf-h3" role="heading" aria-level="3">{esc(t("coach.true.h2"))}</div><ul>{items}</ul>'
             f'<p class="jf-small jf-mt4"><strong>{esc(t("coach.true.note"))}</strong></p></section>')
    if coach['not_verified']:
        items = ''.join(f'<li>{esc(i["requirement"])}: {esc(api_text(i["note"]))}</li>' for i in coach['not_verified'])
        html(f'<section class="jf jf-fact" data-category="not_verified">{badge("UNVERIFIED")}'
             f'<div class="jf-h3" role="heading" aria-level="3">{esc(t("coach.unverified.h2"))}</div>'
             f'<p>{esc(t("unverified.p"))}</p><ul>{items}</ul></section>')
    if not any(coach[k] for k in ('representation', 'gaps', 'true_gaps', 'not_verified')):
        html(f'<p class="jf jf-muted">{esc(t("coach.nothing"))}</p>')


def _gap(gap: dict, key: str, on_answer) -> None:
    """B: "have you done this?" first; "no" gives learning ideas, "yes" asks the fixed questions, then a draft."""
    html(f'<article class="jf jf-coach-item" data-category="B">{badge("NO_MATCH")}'
         f'<div class="jf-h3" role="heading" aria-level="3">{esc(gap["requirement"])}</div>'
         f'<p class="jf-description">{esc(t("coach.missing.q"))}</p></article>')
    done = st.session_state.get(f'done_{key}')
    if done is None:
        with st.container(horizontal=True, gap='small'):
            if st.button(t('coach.yes'), key=f'yes_{key}'):
                st.session_state[f'done_{key}'] = 'yes'
                st.rerun()
            if st.button(t('coach.no'), key=f'no_{key}', type='tertiary'):
                st.session_state[f'done_{key}'] = 'no'
                st.session_state[f'draft_{key}'] = {'ideas': (on_answer(gap['gap_index'], False, {}) or {}).get('ideas', [])}
                st.rerun()
        return
    if done == 'no':
        ideas = (st.session_state.get(f'draft_{key}') or {}).get('ideas') or []
        listed = ('<p class="jf-mt4"><strong>' + esc(t('coach.ideas')) + '</strong></p><ul>'
                  + ''.join(f'<li>{esc(api_text(i))}</li>' for i in ideas) + '</ul>') if ideas else ''
        html(notice(f'<p>{esc(t("coach.no.notice"))}</p>{listed}'))
        _reset_button(key)
        return
    draft = st.session_state.get(f'draft_{key}') or {}
    if draft.get('bullet') and draft.get('status') != 'rejected':
        _draft(draft, key)
        return
    with st.container(key=f'jfcoachform_{key}'):
        with st.form(f'form_{key}', border=False):
            html(f'<p class="jf jf-small jf-muted">{esc(t("coach.form.intro"))}</p>')
            answers = {}
            c1, c2 = st.columns(2)
            for i, (qk, qtext) in enumerate(gap['questions'].items()):
                label, hint = _question(qk, qtext)
                answers[qk] = (c1 if i % 2 == 0 else c2).text_input(label, key=f'{qk}_{key}', max_chars=300,
                                                                      help=hint or None)
            submitted = st.form_submit_button(t('coach.submit'), type='primary')
        if submitted:
            missing = [k for k in REQUIRED_ANSWERS if k in answers and not (answers[k] or '').strip()]
            if missing:
                names = ', '.join(_question(k, '')[0].rstrip(' *') for k in missing)
                html(notice(esc(t('coach.form.error', list=names)), 'error'))
            else:
                out = on_answer(gap['gap_index'], True, answers)
                if out and out.get('bullet'):
                    st.session_state[f'draft_{key}'] = {'bullet': out['bullet'], 'note': out.get('note'),
                                                        'status': 'review', 'answers': dict(answers)}
                    st.rerun()
                elif out:
                    for idea in out.get('ideas', []):
                        html(f'<p class="jf jf-small">{esc(api_text(idea))}</p>')
    if draft.get('status') == 'rejected':
        html(f'<p class="jf jf-small jf-muted">{esc(t("toast.rejected"))}</p>')
    _reset_button(key)


def _reset_button(key: str) -> None:
    if st.button(t('coach.changeAnswer'), key=f'reset_{key}', type='tertiary'):
        st.session_state.pop(f'done_{key}', None)
        st.session_state.pop(f'draft_{key}', None)
        st.rerun()


def _draft(draft: dict, key: str) -> None:
    status = draft.get('status', 'review')
    cls = {'accepted': 'supported', 'edited': 'info'}.get(status, '')
    html(f'<div class="jf jf-mt4"><div class="jf-section-head"><div class="jf-h4" role="heading" aria-level="4">'
         f'{esc(t("draft.h4"))}</div>{tag(esc(t("draft.status." + status)), cls)}</div>'
         f'<p class="jf-small jf-muted jf-mt4">{esc(t("draft.note"))}</p></div>')
    if draft.get('editing'):
        edited = st.text_area(t('draft.editLabel'), draft['bullet'], key=f'bullet_{key}', max_chars=1200)
        if st.button(t('draft.save'), key=f'save_{key}'):
            if edited.strip():
                draft.update(bullet=edited.strip(), editing=False, status='edited')
            st.rerun()
        return
    st.code(draft['bullet'], language=None, wrap_lines=True)
    html(f'<p class="jf jf-small jf-muted">{esc(t("draft.copy"))}</p>')
    if draft.get('confirm'):
        with st.container(key=f'jfmodal_wrap_accept_{key}'):
            with st.container(key=f'jfmodal_card_accept_{key}'):
                html(f'<div class="jf"><div class="jf-h2" role="heading" aria-level="2">'
                     f'{esc(t("dialog.accept.title"))}</div><p class="jf-mt4">{esc(t("dialog.accept.body"))}</p></div>')
                with st.container(horizontal=True, gap='small'):
                    if st.button(t('dialog.accept.yes'), key=f'acceptyes_{key}', type='primary'):
                        draft.update(status='accepted', confirm=False)
                        st.toast(t('toast.accepted'))
                        st.rerun()
                    if st.button(t('dialog.accept.no'), key=f'acceptno_{key}', type='tertiary'):
                        draft['confirm'] = False
                        st.rerun()
    with st.container(horizontal=True, gap='small'):
        if st.button(t('draft.accept'), key=f'accept_{key}'):
            draft['confirm'] = True
            st.rerun()
        if st.button(t('draft.edit'), key=f'edit_{key}', type='tertiary'):
            draft['editing'] = True
            st.rerun()
        if st.button(t('draft.reject'), key=f'reject_{key}', type='tertiary'):
            draft.update(status='rejected', bullet=None)
            st.toast(t('toast.rejected'))
            st.rerun()
    answers = draft.get('answers') or {}
    with st.expander(t('draft.facts')):
        html('<div class="jf">' + ''.join(
            f'<p class="jf-small"><strong>{esc(_question(k, k)[0].rstrip(" *"))}</strong> {esc(v)}</p>'
            for k, v in answers.items() if v) + '</div>')
    _reset_button(key)


# ----------------------------------------------------------------------- saved synthetic demo (secondary) ------
def _evidence_table(card: dict) -> None:
    labels = {'MATCH': t('badge.MATCH'), 'PARTIAL': t('badge.PARTIAL'), 'NO_MATCH': t('badge.NO_MATCH')}
    rows = [{t('col.requirement'): r['requirement'], t('col.type'): r['importance'],
             t('col.result'): labels.get(r['label'], t('badge.UNVERIFIED')),
             t('col.quote'): ' | '.join(r['cv_quotes'])} for r in card['requirements']]
    st.dataframe(rows, hide_index=True, width='stretch')


def job_card(card: dict, rank: int, *, api=None, run_id: str | None = None) -> None:
    """One analyzed demo job (saved or live demo run), with evidence, posting text and feedback."""
    title = esc(card.get('title') or card['job_id'])
    with st.container(key=f"jfrow_demo_{run_id}_{card['job_id']}_{rank}"):
        if card['scored']:
            side = (f'<div style="text-align:right"><strong class="jf-h2">{card["score_pct"]:.0f}%</strong>'
                    f'<div class="jf-small jf-muted">{esc(t("card.status." + card["status"]))}</div></div>')
            counts = (f'<p class="jf-small jf-muted jf-mt4">'
                      f'{esc(t("card.of", a=card["matched"], b=card["partial"], n=card["required_total"]))}</p>')
        else:
            side = tag(esc(t('card.status.' + card['status'])), 'partial' if card['status'] == 'on_hold' else '')
            counts = ''
        html(f'<div class="jf"><div class="jf-job-title"><div><div class="jf-h3" role="heading" aria-level="3">'
             f'{rank}. {title}</div><p class="jf-company">{esc(card.get("company") or "")} · '
             f'{esc(card.get("location") or t("job.location.none"))}</p></div>{side}</div>{counts}</div>')
        for msg in card['explicit_conflicts']:
            html(notice(esc(t('card.conflict', msg=msg)), 'warn'))
        if card.get('hold_reason'):
            html(notice(esc(card['hold_reason'])))
        notes = []
        if card.get('excluded_units'):
            notes.append(t('excluded', n=len(card['excluded_units'])))
        soft = card['soft_skills']
        if soft['total']:
            notes.append(t('soft', a=soft['matched'], b=soft['partial'], n=soft['total']))
        if notes:
            html('<div class="jf">' + ''.join(f'<p class="jf-small jf-muted">{esc(n)}</p>' for n in notes) + '</div>')
        if card['requirements']:
            with st.expander(t('card.evidence')):
                _evidence_table(card)
        if api is not None and card['job_id'] != 'pasted':
            with st.expander(t('card.posting')):
                key = f"job_{card['job_id']}"
                if st.button(t('card.posting.load'), key=f'load_{run_id}_{key}'):
                    try:
                        st.session_state[key] = api.job(card['job_id'])
                    except Exception as exc:
                        st.session_state[key] = {'description': t('card.posting.error', err=type(exc).__name__)}
                if key in st.session_state:
                    st.text(st.session_state[key].get('description') or '')
        if card.get('url'):
            st.link_button(t('job.apply'), card['url'], type='tertiary')
        if api is not None and run_id:
            with st.container(horizontal=True, gap='small', vertical_alignment='center'):
                up = st.button(t('feedback.useful'), key=f"up_{run_id}_{card['job_id']}")
                reason = st.selectbox(t('feedback.reason'), REASONS, format_func=lambda r: t('reason.' + r),
                                      key=f"reason_{run_id}_{card['job_id']}", label_visibility='collapsed',
                                      width=240)
                down = st.button(t('feedback.not'), key=f"down_{run_id}_{card['job_id']}")
            if up or down:
                api.feedback(run_id, card['job_id'], 'useful' if up else 'not_useful', reason)
                st.toast(t('feedback.thanks'))


def suggestions(out: dict) -> None:
    st.caption(out['guard'])
    if not out['items']:
        html(f'<p class="jf jf-muted">{esc(t("demo.suggest.none"))}</p>')
    for i, item in enumerate(out['items']):
        quotes = ''.join(f'<p class="jf-small jf-muted">{esc(t("demo.suggest.quote", q=q))}</p>'
                         for q in item['cv_quotes'])
        with st.container(key=f'jfrow_suggestion_{i}'):
            html(f'<div class="jf"><div class="jf-h4" role="heading" aria-level="3">{esc(item["requirement"])}'
                 f' <span class="jf-small jf-muted">· {esc(t("demo.suggest.asked", n=item["jobs_asking"]))}</span>'
                 f'</div><p class="jf-mt4">{esc(item["advice"])}</p>{quotes}</div>')
