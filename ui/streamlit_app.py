"""JobFit Streamlit UI (visual design v3). Calls the API only (no business logic here).

Run: uvicorn jobfit.api.wiring:create_default_app --factory --app-dir src   (API)
     streamlit run ui/streamlit_app.py                                      (UI)

Product flow (D-105), one screen at a time as in the design: Home -> Upload CV -> local structural
sanitizer -> Review the exact text (optional edit, sanitized again) -> explicit consent -> parse -> CV ready
-> Find Jobs (optional pre-search filters -> Relevant Jobs -> zero-call local refinement -> Analyze Fit on a
chosen job) or Check a Job (pasted JD -> Analyze Fit) -> Improve My CV for This Job. The saved synthetic
demo and the market skills stay secondary screens.
Privacy UX (D-051/D-104): pre-upload notice, exact sanitized preview, consent for that exact text,
"Hentikan & hapus sesi" in the header on every screen, a liveness heartbeat while the page is open, and
honest expiry messages. Every billable action carries one idempotency key per user action; a rerun or retry
never runs it twice. Interface copy is Indonesian by default, with an English switch (texts.py).
"""
from __future__ import annotations

import hashlib
import time
from datetime import date

import httpx
import streamlit as st

from api_client import ApiClient, ApiError
from components import (COUNTRIES, EXPERIENCE, ROLES, WORK_MODES, analysis_view, coach_view, job_card,
                        metadata_html, option_label, relevant_job_html, suggestions)
from live_action import LiveActions, action_fingerprint, fingerprint
from refine import options, refine
from texts import t
from theme import (empty_state, esc, feature, heading, html, icon, inject, notice, processing, quota_html,
                   section_head, steps, sublabel, tag)

st.set_page_config(page_title='JobFit — Bukti, bukan tebakan', page_icon=':material/layers:', layout='wide',
                   initial_sidebar_state='collapsed')
inject()
POLL_SECONDS = 1.5
MAX_ANALYSES = 3                        # default; the API's /health analysis_limit wins
MIN_JD_CHARS = 200                      # the API's MIN_PASTE_CHARS
# Everything derived from the current uploaded CV; cleared whenever the CV (its digest) changes.
CV_STATE = ('cv_ready', 'parse_run', 'parse_result', 'consented_digest', 'search', 'analyses', 'selected_job',
            'coach', 'pasted', 'paste_ids', 'return_to', 'hold_poll', 'analyze_error', 'edit_error', 'run_started')
CV_PREFIXES = ('refine_', 'history_', 'done_', 'what_when_', 'own_part_', 'tools_', 'result_', 'bullet_', 'draft_')
CV_PAGES = ('ready', 'find', 'results', 'check', 'analysis', 'coach')
SAMPLE_CV = """Raka Contoh — CV sintetis
Email: raka@example.com
Telepon: +62 812 0000 0000
PROFILE
AI enthusiast seeking new opportunities.
PROFESSIONAL EXPERIENCE
Junior ML Engineer | Studio Data Contoh | January 2025 – May 2026
Built FastAPI endpoints for ML prediction services.
Wrote SQL queries to clean and aggregate product event data.
Deployed ML prediction services with Docker and automated tests.
Collaborated through Git pull requests and code reviews.
PROJECTS
Semantic Search Prototype | Personal project | June 2026
Built a semantic retrieval prototype using embeddings.
Deployed services to cloud infrastructure.
EDUCATION
Bachelor of Computer Science | Universitas Contoh | 2024
SKILLS
Python, FastAPI, SQL, Docker, Git, embeddings
"""

ss = st.session_state
ss.setdefault('lang', 'id')
ss.setdefault('page', 'landing')


def new_client():
    client = ApiClient()
    client.start_session()
    return client


def go(page: str) -> None:
    """Navigation callback: the next run renders ``page``."""
    ss.page = page
    ss.modal = None


def set_lang(lang: str) -> None:
    ss.lang = lang


def open_modal(name: str) -> None:
    ss.modal = name


# ------------------------------------------------------------------------------------ header ---------------
def topbar() -> None:
    with st.container(key='jf_topbar', horizontal=True, vertical_alignment='center', gap='small'):
        st.button('JobFit', key='jf_brand', type='tertiary', icon=':material/layers:', on_click=go, args=('landing',))
        with st.container(key='jf_brandtag', width='content'):
            html(f'<span class="jf">{esc(t("brand.tag"))}</span>')
        st.space('stretch')
        for code in ('id', 'en'):
            with st.container(key=f'jflang_{"on_" if ss.lang == code else ""}{code}', width='content'):
                st.button(code.upper(), key=f'lang_{code}', type='tertiary', on_click=set_lang, args=(code,))
        st.button(t('header.help'), key='open_help', type='tertiary', icon=':material/info:', on_click=open_modal,
                  args=('help',))
        if 'api' in ss:
            st.button(t('header.delete'), key='open_delete', type='tertiary', icon=':material/logout:',
                      on_click=open_modal, args=('delete',))


def product_nav() -> None:
    """The product menu once the CV is ready (Find Jobs, Check a Job, CV ready)."""
    current = {'find': 'find', 'results': 'find', 'check': 'check', 'ready': 'cv'}.get(ss.page)
    with st.container(key='jf_nav', horizontal=True, vertical_alignment='center', gap='medium'):
        for name, target in (('find', 'results' if ss.get('search') is not None else 'find'), ('check', 'check'),
                             ('cv', 'ready')):
            if name == 'cv':
                st.space('stretch')
            with st.container(key=f'jfnav_{"on_" if current == name else ""}{name}', width='content'):
                st.button(t(f'nav.{name}'), key=f'nav_{name}', type='tertiary', on_click=go, args=(target,))


def footer() -> None:
    with st.container(key='jf_footer', horizontal=True, vertical_alignment='center', gap='small'):
        html(f'<span class="jf jf-small jf-muted">{esc(t("footer.left"))}</span>')
        st.space('stretch')
        html(f'<span class="jf jf-small jf-muted">{esc(t("footer.right", limit=MAX_ANALYSES))}</span>')
        st.button(t('footer.link'), key='footer_help', type='tertiary', on_click=open_modal, args=('help',))


def scroll_top_now() -> None:
    """Scroll the page to the top now. The script text is unique per call, so the frontend runs it again;
    it carries no user data."""
    ss.screen_changes = ss.get('screen_changes', 0) + 1
    st.html(f'<script>/* screen {ss.screen_changes} */(function(){{const top=()=>{{const m=document.querySelector('
            f'\'[data-testid="stMain"]\');if(m){{m.scrollTo(0,0)}}window.scrollTo(0,0)}};top();'
            f'setTimeout(top,60);setTimeout(top,250)}})()</script>', unsafe_allow_javascript=True, width='content')


def scroll_to_top() -> None:
    """A new screen starts at the top, as in the design (Streamlit keeps the scroll position on a rerun)."""
    if ss.get('shown_page') != ss.page:
        ss.shown_page = ss.page
        scroll_top_now()


def modal() -> None:
    name = ss.get('modal')
    if not name:
        return
    with st.container(key=f'jfmodal_wrap_{name}'), st.container(key=f'jfmodal_card_{name}'):
        if name == 'help':
            html(f'<div class="jf"><div class="jf-h2" role="heading" aria-level="2">{esc(t("dialog.help.title"))}'
                 f'</div><p class="jf-mt4">{t("dialog.help.p1")}</p><p class="jf-mt4">{t("dialog.help.p2")}</p>'
                 f'<p class="jf-mt4">{t("dialog.help.p3")}</p><p class="jf-small jf-muted jf-mt4">'
                 f'{esc(t("dialog.help.small", limit=MAX_ANALYSES))}</p></div>')
            st.button(t('dialog.ok'), key='help_ok', type='primary', on_click=open_modal, args=(None,))
        elif name == 'delete':
            html(f'<div class="jf"><div class="jf-h2" role="heading" aria-level="2">{esc(t("dialog.delete.title"))}'
                 f'</div><p class="jf-mt4">{esc(t("dialog.delete.body"))}</p><p class="jf-small jf-muted jf-mt4">'
                 f'{esc(t("dialog.delete.small"))}</p></div>')
            with st.container(horizontal=True, gap='small'):
                with st.container(key='jfdanger_delete', width='content'):
                    confirmed = st.button(t('dialog.delete.yes'), key='delete_confirm')
                st.button(t('cancel'), key='delete_cancel', type='tertiary', on_click=open_modal, args=(None,))
            if confirmed:
                delete_session()
        elif name == 'replace':
            html(f'<div class="jf"><div class="jf-h2" role="heading" aria-level="2">{esc(t("dialog.replace.title"))}'
                 f'</div><p class="jf-mt4">{esc(t("dialog.replace.body"))}</p></div>')
            with st.container(horizontal=True, gap='small'):
                replace = st.button(t('privacy.replace'), key='replace_confirm', type='primary')
                st.button(t('cancel'), key='replace_cancel', type='tertiary', on_click=open_modal, args=(None,))
            if replace:
                reset_cv_state()
                for key in ('preview', 'preview_valid', 'upload_id', 'upload_error', 'manual_cv'):
                    ss.pop(key, None)
                ss.uploader_gen = ss.get('uploader_gen', 0) + 1     # a fresh, empty file picker
                go('upload')
                st.rerun()


def delete_session() -> None:
    try:
        ss.api.delete_session()
    except ApiError:
        pass
    lang = ss.lang
    for key in list(ss):
        del ss[key]
    ss.lang, ss.page = lang, 'deleted'
    st.rerun()


# ------------------------------------------------------------------------------- API plumbing --------------
def call(fn, *args, **kwargs):
    """Run one API call. An expired session is replaced and the user is told honestly."""
    try:
        return fn(*args, **kwargs)
    except ApiError as exc:
        if exc.status == 401:
            lang = ss.lang
            for key in list(ss):
                del ss[key]
            ss.lang, ss.page = lang, 'expired'
            try:
                ss.api = new_client()
            except Exception:
                pass
            st.rerun()
        raise


def friendly(exc: ApiError) -> str:
    """A fixed refusal code in the interface language; any other API message unchanged."""
    code = exc.code or exc.detail
    if exc.status == 404 and exc.detail == 'Not Found':      # FastAPI's unknown-route answer: an outdated API
        return t('err.not_found', url=ss.api.base_url if 'api' in ss else '')
    if code in ('allowance_exhausted', 'busy', 'consent_required', 'search_required', 'parse_required',
                'input_too_large', 'ticket_required', 'unavailable', 'production_retrieval_unavailable'):
        return t('err.code.' + code)
    return exc.detail


def show_error(message: str) -> None:
    html(notice(esc(message), 'error'))


def reset_cv_state() -> None:
    """A new upload or a successful edit is a new CV: nothing derived from the earlier CV stays visible."""
    for key in list(ss):
        if key in CV_STATE or key.startswith(CV_PREFIXES):
            del ss[key]


def billable(kind: str, start, **ids):
    """Start one billable action with its idempotency key; a lost response keeps the key for the retry."""
    key = actions.key_for(fingerprint(kind, **ids))
    try:
        out = call(start, key)
    except ApiError as exc:
        ss.billable_error = friendly(exc)
        return None
    except httpx.HTTPError:
        ss.billable_error = t('err.connection')
        return None
    actions.acknowledged(out if isinstance(out, str) else key)
    return out


def cancel_wait(run_id: str, page: str) -> None:
    ss.hold_poll = run_id
    go(page)
    st.toast(t('toast.cancelled'))


def wait_run(run_id: str, title: str, stages: list[str], back_to: str) -> dict:
    """Honest waiting: the stages this operation goes through and the real elapsed time, no percentage.

    "Cancel & go back" only stops waiting on this screen; the run keeps its id, so it is polled again
    (never posted again) when the user returns to it.
    """
    started = ss.setdefault('run_started', {}).setdefault(run_id, time.time())
    box = st.empty()

    def draw() -> None:
        with box.container():
            html(processing(title, stages, int(time.time() - started)))
    draw()
    st.button(t('proc.back'), key=f'cancel_{run_id}', type='tertiary', on_click=cancel_wait, args=(run_id, back_to))
    scroll_top_now()                             # the wait screen is at the top: show it before polling
    body = call(api.poll, run_id)
    while body['status'] == 'running':
        time.sleep(POLL_SECONDS)
        body = call(api.poll, run_id)
        draw()
    return body


# ------------------------------------------------------------------------------- session setup -------------
api_down = None
if 'api' not in ss and ss.page != 'deleted':      # after "delete", a new session starts only from Home
    try:
        ss.api = new_client()
    except Exception as exc:  # API down or not reachable: a clear message, never a traceback
        api_down = exc
if 'api' in ss and 'api_outdated' not in ss:
    # Once per API client (also after an expiry replaced it). The D-104 API (sanitizer v2, /cv/preview,
    # /cv/parse) reports live_storage_ready in /health; an older API does not: warn instead of failing
    # later with "Not Found". analysis_limit is the API's per-session Analyze Fit limit.
    try:
        health = ss.api.health() or {}
        ss.api_outdated = 'live_storage_ready' not in health
        ss.analysis_limit = int(health.get('analysis_limit') or MAX_ANALYSES)
    except Exception:
        ss.api_outdated = False
topbar()
if ss.get('api_outdated'):
    html(notice(t('api.outdated', url=esc(ss.api.base_url)), 'error'))
if api_down is not None:
    with st.container(key='jfnarrow_down'):
        html(heading(esc(t('api.down.h1'))))
        html(notice(esc(t('api.down.p', url=ApiClient().base_url, err=type(api_down).__name__)), 'error'))
        st.button(t('api.retry'), key='api_retry', type='primary')
    st.stop()
api: ApiClient | None = ss.get('api')
MAX_ANALYSES = int(ss.get('analysis_limit') or MAX_ANALYSES)
if 'live_actions' not in ss:
    ss.live_actions = LiveActions()
actions: LiveActions = ss.live_actions


@st.fragment(run_every=30)
def liveness():
    """Browser liveness: runs only while this page is open and connected. It keeps the
    2-minute lease alive but does not count as activity, so the 30-minute idle limit still applies."""
    try:
        if 'api' in st.session_state:
            st.session_state.api.heartbeat()
    except Exception:
        pass


liveness()

preview = ss.get('preview')
if ss.page in CV_PAGES and not ss.get('cv_ready'):
    ss.page = 'privacy' if preview else 'upload'
if ss.page in ('privacy', 'edit') and not preview:
    ss.page = 'upload'
if ss.get('cv_ready'):
    product_nav()
analyses = ss.setdefault('analyses', {}) if ss.get('cv_ready') else {}
used = len(analyses)


def back(label: str, target: str, key: str) -> None:
    st.button(label, key=key, type='tertiary', on_click=go, args=(target,))


# ------------------------------------------------------------------------------------ screens --------------
def landing() -> None:
    hero, preview_col = st.columns([1.05, 1], gap='large', vertical_alignment='center')
    with hero:
        html(f'<div class="jf jf-hero-copy"><div class="jf-eyebrow">{esc(t("landing.eyebrow"))}</div>'
             f'<div class="jf-display" role="heading" aria-level="1">{t("landing.h1")}</div>'
             f'<p class="jf-lead">'
             f'{esc(t("landing.lead"))}</p></div>')
        with st.container(horizontal=True, gap='small'):
            st.button(t('landing.cta').rstrip(' →'), key='cta_upload', type='primary', on_click=go, args=('upload',),
                      icon=':material/arrow_forward:', icon_position='right')
            st.button(t('landing.demo'), key='cta_demo', on_click=go, args=('demo',))
        html(f'<div class="jf"><p class="jf-small jf-muted">{esc(t("landing.demo.note"))}</p>'
             f'<p class="jf-privacy-line jf-mt6">{icon("shield")}{esc(t("landing.privacy"))}</p></div>')
    with preview_col:
        html(f'<div class="jf jf-evidence-preview"><div class="jf-preview-top"><span class="jf-eyebrow">'
             f'{esc(t("landing.preview.eyebrow"))}</span>{icon("layers")}</div><div class="jf-preview-body">'
             f'<p class="jf-small jf-muted">{esc(t("landing.preview.note"))}</p>'
             f'<div class="jf-h3" role="heading" aria-level="3">Python backend development</div>'
             f'<span class="jf-tag supported">{icon("check")}{esc(t("badge.MATCH"))}</span>'
             f'<span class="jf-quote-label">{esc(t("landing.preview.quoteLabel"))}</span>'
             f'<blockquote class="jf-quote">“Built FastAPI endpoints for ML prediction services.”</blockquote></div>'
             f'<div class="jf-preview-foot">{icon("check")}{esc(t("landing.preview.foot"))}</div></div>')
    html('<section class="jf jf-how">' + ''.join(
        f'<div><span class="jf-number">0{i}</span><div class="jf-h3" role="heading" aria-level="3">'
        f'{esc(t(f"landing.how{i}.h"))}</div><p>{esc(t(f"landing.how{i}.p"))}</p></div>' for i in (1, 2, 3))
        + '</section>')


def accept_upload(name: str, data: bytes, upload_id: str) -> None:
    """A new file or pasted text is a new CV: sanitize it on the server and show the exact preview."""
    ss.upload_id = upload_id
    reset_cv_state()
    try:
        ss.preview = call(api.upload, name, data)
        ss.preview_valid = True
        ss.pop('upload_error', None)
        go('privacy')
        st.rerun()
    except ApiError as exc:
        ss.pop('preview', None)
        ss.upload_error = friendly(exc)
    except httpx.HTTPError:
        ss.upload_error = t('err.connection')


def upload() -> None:
    with st.container(key='jfnarrow_upload'):
        html(steps(0) + heading(esc(t('upload.h1')), esc(t('upload.desc'))))
        with st.container(key='jfupload_zone'):
            html(f'<div class="jf jf-upload-head">{icon("upload")}<div class="jf-h2" role="heading" aria-level="2">'
                 f'{esc(t("upload.zone.h"))}</div><p>{esc(t("upload.zone.formats"))}</p></div>')
            file = st.file_uploader(t('upload.file.label'), type=['pdf', 'docx', 'txt', 'md'],
                                    key=f'cv_file_{ss.get("uploader_gen", 0)}', label_visibility='collapsed')
            if ss.get('upload_error'):
                show_error(ss.upload_error)
        if file is not None and ss.get('upload_id') != file.file_id:
            accept_upload(file.name, file.getvalue(), file.file_id)
            if ss.get('upload_error'):
                st.rerun()
        html(f'{notice(t("upload.notice"))}<p class="jf jf-small jf-muted">{esc(t("upload.small"))}</p>')
        with st.container(horizontal=True, gap='small'):
            st.download_button(t('upload.download'), SAMPLE_CV, file_name='JobFit-CV-contoh.txt', mime='text/plain',
                               key='sample_download', on_click='ignore', icon=':material/download:')
            st.button(t('upload.demo'), key='upload_demo', type='tertiary', on_click=go, args=('demo',))
        with st.expander(t('upload.manual.summary')):
            text = st.text_area(t('upload.manual.label'), key='manual_cv', height=220, max_chars=100_000,
                                placeholder=t('upload.manual.placeholder'))
            html(f'<p class="jf jf-small jf-muted">{esc(t("upload.manual.hint"))}</p>')
            if st.button(t('upload.manual.submit'), key='manual_submit', type='primary'):
                if not (text or '').strip():
                    show_error(t('upload.manual.empty'))
                else:
                    raw = text.encode('utf-8')
                    accept_upload('cv-teks.txt', raw, 'manual:' + hashlib.sha256(raw).hexdigest())
                    st.rerun()


def privacy() -> None:
    digest = preview['digest']
    with st.container(key='jfnarrow_privacy'):
        back(t('back'), 'ready' if ss.get('cv_ready') else 'upload', 'privacy_back')
        if ss.get('parse_run') and not ss.get('cv_ready') and ss.get('hold_poll') != ss.parse_run:
            body = wait_run(ss.parse_run, t('proc.parse.title'),
                            [t('proc.parse.1'), t('proc.parse.2'), t('proc.parse.3')], 'privacy')
            if body['status'] == 'done':
                ss.parse_result, ss.cv_ready = body['result'], True
                go('ready')
            else:
                ss.pop('parse_run', None)
                ss.parse_error = t('err.stopped', error=body.get('error'))
            st.rerun()
        html(steps(1) + heading(esc(t('privacy.h1')), esc(t('privacy.desc'))))
        with st.container(horizontal=True, vertical_alignment='center'):
            html(f'<div class="jf">{tag(esc(t("privacy.tag")), "info", "shield")}</div>')
            st.space('stretch')
            st.button(t('privacy.edit'), key='privacy_edit', icon=':material/edit:', on_click=go, args=('edit',))
            st.button(t('privacy.replace'), key='privacy_replace', type='tertiary', on_click=open_modal,
                      args=('replace',))
        html(notice(esc(t('privacy.notice'))))
        with st.expander(t('privacy.what.summary')):
            html(f'<p class="jf jf-muted">{t("privacy.what.body")}</p>')
        removed = {k: v for k, v in (preview.get('removed') or {}).items() if v}
        if removed:
            items = ', '.join(f'{k.replace("_", " ")} ({v})' for k, v in removed.items())
            html(f'<p class="jf jf-small jf-muted">{esc(t("privacy.removed", items=items))}</p>')
        html(f'<div class="jf"><span class="jf-field-label">{esc(t("privacy.label"))}</span>'
             f'<pre class="jf-preview-text" tabindex="0" data-digest="{esc(digest)}">{esc(preview["masked_text"])}'
             f'</pre><p class="jf-small jf-muted jf-mt4">{esc(t("privacy.source"))}</p></div>')
        for warning in preview['warnings']:
            html(f'<p class="jf jf-small jf-muted">{esc(warning)}</p>')
        if preview.get('message'):
            html(notice(esc(preview['message']), 'warn'))
        if ss.get('parse_error'):
            show_error(ss.pop('parse_error'))
        if ss.get('consent_error'):
            show_error(ss.pop('consent_error'))
        if ss.get('billable_error'):
            show_error(ss.pop('billable_error'))
        ready_to_send = ss.get('preview_valid') and preview.get('provider_processing') == 'enabled'
        if ss.get('cv_ready'):
            return
        html('<div class="jf" style="border-top:1px solid var(--border);margin-top:8px"></div>')
        agreed = st.checkbox(t('privacy.consent.strong'), key=f'consent_{digest}', disabled=not ready_to_send)
        html(f'<p class="jf jf-small jf-muted">{esc(t("privacy.consent.small"))}</p>')
        with st.container(horizontal=True, horizontal_alignment='right'):
            go_on = st.button(t('privacy.continue').rstrip(' →'), key='parse_go', type='primary',
                              disabled=not (agreed and ready_to_send), icon=':material/arrow_forward:',
                              icon_position='right')
        if go_on:
            ss.pop('hold_poll', None)
            if ss.get('consented_digest') != digest:
                try:
                    call(api.consent, digest)
                    ss.consented_digest = digest
                except ApiError as exc:
                    ss.consent_error = friendly(exc)
            if ss.get('consented_digest') == digest and not ss.get('parse_run'):
                run_id = billable('parse', api.parse_cv, cv=digest)
                if run_id:
                    ss.parse_run = run_id
            st.rerun()


def edit() -> None:
    digest = preview['digest']
    with st.container(key='jfnarrow_edit'):
        html(steps(1) + heading(esc(t('edit.h1')), esc(t('edit.desc'))))
        edited = st.text_area(t('edit.label'), preview['masked_text'], height=420, key=f'text_{digest}')
        if ss.get('edit_error'):
            show_error(ss.pop('edit_error'))
        with st.container(horizontal=True, vertical_alignment='center'):
            back(t('edit.back'), 'privacy', 'edit_back')
            st.space('stretch')
            save = st.button(t('edit.submit'), key='edit_save', type='primary')
        if save:
            if edited == preview['masked_text']:
                html(notice(esc(t('edit.unchanged')), 'warn'))
                return
            try:
                out = call(api.edit_preview, edited)
                reset_cv_state()
                ss.preview, ss.preview_valid = out, True
                go('privacy')
            except ApiError as exc:
                reset_cv_state()                 # the server invalidated the old preview too
                ss.preview_valid = False
                ss.edit_error = friendly(exc)
            st.rerun()


def ready() -> None:
    summary = (ss.get('parse_result') or {}).get('summary') or {}
    lines = len([x for x in preview['masked_text'].split('\n') if x.strip()])
    with st.container(key='jfmedium_ready'):
        html(steps(2) + heading(esc(t('ready.h1')), esc(t('ready.desc')), esc(t('ready.eyebrow'))))
        html(f'<div class="jf jf-ready-summary"><div><strong class="jf-row">{icon("file")}'
             f'{esc(t("ready.summary.title"))}</strong><span class="jf-small jf-muted">'
             f'{esc(t("ready.summary.meta", n=lines))}</span></div></div>')
        with st.expander(t('ready.review')):
            html(f'<pre class="jf jf-preview-text">{esc(preview["masked_text"])}</pre>')
            with st.container(horizontal=True, gap='small'):
                st.button(t('privacy.edit'), key='ready_edit', icon=':material/edit:', on_click=go, args=('edit',))
                st.button(t('privacy.replace'), key='ready_replace', type='tertiary', on_click=open_modal,
                          args=('replace',))
        find_col, check_col = st.columns([1.15, 1], gap='medium')
        with find_col, st.container(key='jfchoice_main_find', height='stretch'):
            html(f'<div class="jf jf-choice-head"><div class="jf-eyebrow">{esc(t("ready.find.eyebrow"))}</div>'
                 f'<div class="jf-h2" role="heading" aria-level="2">{esc(t("nav.find"))}</div>{sublabel("Find Jobs")}'
                 f'<p>{esc(t("ready.find.p"))}</p></div>')
            st.button(t('find.submit'), key='choose_find', type='primary', on_click=go,
                      args=('results' if ss.get('search') is not None else 'find',),
                      icon=':material/arrow_forward:', icon_position='right')
        with check_col, st.container(key='jfchoice_check', height='stretch'):
            html(f'<div class="jf jf-choice-head"><div class="jf-eyebrow">{esc(t("ready.check.eyebrow"))}</div>'
                 f'<div class="jf-h2" role="heading" aria-level="2">{esc(t("nav.check"))}</div>{sublabel("Check a Job")}'
                 f'<p>{esc(t("ready.check.p"))}</p></div>')
            st.button(t('ready.check.btn'), key='choose_check', on_click=go, args=('check',))
        html(f'<p class="jf jf-small jf-muted">{esc(quota_text())}</p>')
        with st.expander(t('ready.skills.summary')):
            skills = summary.get('skills') or []
            body = (''.join(tag(esc(s)) for s in skills) if skills
                    else f'<span class="jf-muted">{esc(t("ready.skills.empty"))}</span>')
            html(f'<div class="jf"><p class="jf-small jf-muted jf-mb4">{esc(t("ready.skills.note"))}</p>'
                 f'<div class="jf-cluster">{body}</div></div>')
        st.button(t('ready.market'), key='ready_market', type='tertiary', on_click=open_market, args=('ready',))


def quota_text() -> str:
    return t('quota.empty') if used >= MAX_ANALYSES else t('quota', left=MAX_ANALYSES - used, limit=MAX_ANALYSES)


def open_market(origin: str) -> None:
    ss.market_back = origin
    go('market')


# ---- work history (D-086), asked only where an Analyze Fit is about to happen ----------------------------
def history_control(where: str, digest: str) -> None:
    """One answer per sanitized-CV digest, shared by Find Jobs and Check a Job. It is frozen at the first
    Analyze Fit click, before the request is sent, so a retry after a lost response keeps the same action
    (same answer, same idempotency key) and existing results never change underneath it. A new upload or
    edit is a new digest and starts unchecked again (reset_cv_state clears every history_ key).
    """
    frozen = ss.get('history_locked', {})
    if digest in frozen:
        html(notice(f'<strong>{esc(t("history.on" if frozen[digest] else "history.off"))}</strong>'
                    f'<p>{esc(t("history.locked"))}</p>'))
        return
    choice = ss.setdefault('history_choice', {})
    choice[digest] = st.checkbox(t('history.check.strong'), value=choice.get(digest, False),
                                 key=f'history_{where}_{digest}')
    html(f'<p class="jf jf-small jf-muted">{esc(t("history.check.small"))}</p>')


def frozen_history(digest: str) -> bool:
    """Freeze the answer for this digest at the first Analyze Fit attempt (before any request)."""
    frozen = ss.setdefault('history_locked', {})
    if digest not in frozen:
        frozen[digest] = bool(ss.get('history_choice', {}).get(digest, False))
    return frozen[digest]


def analyze(kind: str, job_id: str, start, return_to: str, **ids) -> None:
    """Start one Analyze Fit; its run id is kept, so a rerun resumes polling and never posts again.

    ``start(key, history)`` sends the request; the history answer is frozen before it, so every retry of
    this action carries the same answer and therefore the same idempotency key.
    """
    digest = preview['digest']
    if job_id not in analyses:
        history = frozen_history(digest)
        run_id = billable(kind, lambda key: start(key, history), cv=digest, history=history, **ids)
        if not run_id:                 # rerun so the answer shows as fixed; the error is shown after it
            ss.analyze_error = ss.pop('billable_error', None)
            st.rerun()
        analyses[job_id] = {'run_id': run_id, 'result': None}
    ss.selected_job, ss.return_to = job_id, return_to
    go('analysis')
    st.rerun()


def page_heading(title: str, desc: str, product: tuple[str, str]) -> None:
    html(heading(esc(title), esc(desc), feature(*product), quota_html(used, MAX_ANALYSES)))


def find() -> None:
    digest = preview['digest']
    with st.container(key='jfmedium_find'):
        page_heading(t('find.h1'), t('find.desc'), ('nav.find', 'Find Jobs'))
        if ss.get('search_error'):
            show_error(ss.pop('search_error'))
        holder = st.empty()
        with holder.container(key='jfpanel_find'):
            html(f'<div class="jf">{section_head(esc(t("find.panel.h2")), esc(t("optional")))}</div>')
            with st.form('find_jobs', border=False):
                f1, f2, f3 = st.columns(3)
                family = f1.selectbox(t('filter.role'), ['Any', *ROLES], format_func=option_label('role_family'),
                                      key='search_role')
                country = f2.selectbox(t('filter.country'), ['Any', *COUNTRIES],
                                       format_func=option_label('country_code'), key='search_country')
                city = f3.text_input(t('filter.city'), max_chars=60, placeholder=t('filter.city.placeholder'),
                                     key='search_city')
                f4, f5, f6 = st.columns(3)
                experience = f4.selectbox(t('filter.experience'), ['Any', *EXPERIENCE],
                                          format_func=option_label('experience_bucket'), key='search_experience')
                mode = f5.selectbox(t('filter.mode'), ['Any', *WORK_MODES], format_func=option_label('work_mode'),
                                    key='search_mode')
                posted = f6.selectbox(t('filter.posted'), [None, 7, 30], key='search_posted',
                                      format_func=lambda v: t(f'filter.{v}') if v else t('filter.anytime'))
                with st.expander(t('filter.more')):
                    include_unknown = st.checkbox(t('filter.unknown.label'), value=True, key='search_unknown')
                    html(f'<p class="jf jf-small jf-muted">{esc(t("filter.unknown.small"))}</p>')
                with st.container(horizontal=True, vertical_alignment='center'):
                    html(f'<p class="jf jf-small jf-muted">{esc(t("find.hint"))}</p>')
                    submitted = st.form_submit_button(t('find.submit'), type='primary', key='search_submit',
                                                      icon=':material/search:')
        html(f'<p class="jf jf-small jf-muted">{esc(t("find.corpusNote"))}</p>')
        if ss.get('search') is not None:
            back(t('find.backToResults'), 'results', 'find_to_results')
    if submitted:
        filters = {'role_family': None if family == 'Any' else family,
                   'country_code': None if country == 'Any' else country,
                   'city': (city or '').strip() or None,
                   'experience_bucket': None if experience == 'Any' else experience,
                   'work_mode': None if mode == 'Any' else mode,
                   'posted_within_days': posted,
                   'include_unknown': include_unknown}
        with holder.container():
            html(processing(t('proc.search.title'), [t('proc.search.1'), t('proc.search.2'), t('proc.search.3')],
                            None))
        scroll_top_now()
        out = billable('search', lambda key: api.search_jobs(filters, key), cv=digest, filters=filters)
        if out:
            for key in [k for k in ss if k.startswith('refine_')]:
                del ss[key]
            ss.search = out
            go('results')
        else:
            ss.search_error = ss.pop('billable_error', None)
        st.rerun()


def reset_refine() -> None:
    for key in [k for k in ss if k.startswith('refine_')]:
        del ss[key]


def results() -> None:
    result = ss.get('search')
    if result is None:
        go('find')
        st.rerun()
    digest = preview['digest']
    cards = result['jobs']
    day = result.get('analysis_date')
    analysis_date = date.fromisoformat(day) if day else None
    page_heading(t('results.h1'), t('results.desc'), ('page.results', 'Relevant Jobs'))
    with st.container(horizontal=True, vertical_alignment='center'):
        html(f'<div class="jf jf-row jf-small jf-muted">{icon("file")}<span>{esc(t("results.meta"))}</span></div>')
        st.space('stretch')
        back(t('results.changeSearch'), 'find', 'change_search')
    if ss.get('analyze_error'):          # a failed Analyze Fit attempt, shown after the rerun
        show_error(ss.pop('analyze_error'))
    if not cards:
        html(empty_state(t('results.emptySearch.h'), t('results.emptySearch.p')))
        with st.container(horizontal=True, horizontal_alignment='center'):
            st.button(t('results.changeSearch'), key='empty_change', type='primary', on_click=go, args=('find',))
        return
    side, main = st.columns([1, 3.4], gap='large')
    with side, st.container(key='jfrefine'):
        crit_keys = ('refine_role', 'refine_country', 'refine_city', 'refine_experience', 'refine_mode',
                     'refine_posted')
        active = sum(1 for k in crit_keys if ss.get(k)) + (0 if ss.get('refine_unknown', True) else 1)
        with st.expander(t('refine.summary', n=active), expanded=True):
            html(f'<p class="jf jf-small jf-muted">{esc(t("refine.p"))}</p>')
            crit = {'role_family': st.selectbox(t('filter.role'), ['', *options(cards, 'role_family')],
                                                format_func=option_label('role_family'), key='refine_role'),
                    'country_code': st.selectbox(t('filter.country'), ['', *options(cards, 'country_code')],
                                                 format_func=option_label('country_code'), key='refine_country'),
                    'city': st.selectbox(t('filter.city'), ['', *options(cards, 'city')],
                                         format_func=option_label('city'), key='refine_city'),
                    'experience_bucket': st.selectbox(t('filter.experience'),
                                                      ['', *options(cards, 'experience_bucket')],
                                                      format_func=option_label('experience_bucket'),
                                                      key='refine_experience'),
                    'work_mode': st.selectbox(t('filter.mode'), ['', *options(cards, 'work_mode')],
                                              format_func=option_label('work_mode'), key='refine_mode'),
                    'posted_within_days': st.selectbox(t('filter.posted'), [None, 7, 30], key='refine_posted',
                                                       format_func=lambda v: t(f'filter.{v}') if v
                                                       else t('filter.anytime'))}
            keep_unknown = st.checkbox(t('filter.unknown.label'), value=True, key='refine_unknown',
                                       help=t('filter.unknown.small'))
            st.button(t('refine.reset'), key='refine_reset', type='tertiary', on_click=reset_refine)
    shown = refine(cards, crit, analysis_date=analysis_date, include_unknown=keep_unknown)
    with main:
        html(f'<div class="jf jf-section-head"><div class="jf-h2" role="heading" aria-level="2">'
             f'{esc(t("results.h2"))}</div><p class="jf-small jf-muted" role="status" data-count="{len(shown)}" '
             f'data-total="{len(cards)}">{esc(t("results.count", x=len(shown), y=len(cards)))}</p></div>')
        if not shown:
            html(empty_state(t('results.emptyFiltered.h'), t('results.emptyFiltered.p')))
            with st.container(horizontal=True, horizontal_alignment='center'):
                st.button(t('refine.reset'), key='empty_reset', type='primary', on_click=reset_refine)
            return
        if used >= MAX_ANALYSES:
            html(notice(f'<strong>{esc(t("limit.title"))}</strong><p>{esc(t("limit.body", limit=MAX_ANALYSES))}</p>', 'warn'))
        history_control('find', digest)
        for card in shown:
            job_id = card['job_id']
            with st.container(key=f'jfrow_{job_id}'):
                html(relevant_job_html(card, card.get('retrieval_rank') or 0, analysis_date))
                with st.container(horizontal=True, vertical_alignment='center', gap='small'):
                    if job_id in analyses:
                        if st.button(t('job.viewResult').rstrip(' →'), key=f'show_{job_id}',
                                     icon=':material/arrow_forward:', icon_position='right'):
                            ss.selected_job, ss.return_to = job_id, 'results'
                            go('analysis')
                            st.rerun()
                        html(f'<div class="jf">{tag(esc(t("job.cachedNote")), "supported", "check")}</div>')
                    elif st.button(t('job.analyze').rstrip(' →'), key=f'analyze_{job_id}',
                                   disabled=used >= MAX_ANALYSES, icon=':material/arrow_forward:',
                                   icon_position='right'):
                        analyze('corpus_job', job_id, lambda key, hist, j=job_id: api.analyze_job(j, hist, key),
                                'results', job=job_id)
                    if card.get('url'):
                        st.link_button(t('job.apply'), card['url'], type='tertiary')
    html(f'<p class="jf jf-small jf-muted">{esc(t("results.foot"))}</p>')


def check() -> None:
    digest = preview['digest']
    with st.container(key='jfmedium_check'):
        page_heading(t('check.h1'), t('check.desc'), ('nav.check', 'Check a Job'))
        if ss.get('analyze_error'):
            show_error(ss.pop('analyze_error'))
        with st.container(key='jfpanel_check'):
            jd = st.text_area(t('check.label'), height=300, max_chars=20000, key='check_jd')
            html(f'<p class="jf jf-small jf-muted">{esc(t("check.hint"))}</p>')
            if used >= MAX_ANALYSES:
                html(notice(f'<strong>{esc(t("limit.title"))}</strong><p>{esc(t("limit.body", limit=MAX_ANALYSES))}</p>', 'warn'))
            history_control('check', digest)
            with st.container(horizontal=True, horizontal_alignment='right'):
                submit = st.button(t('job.analyze').rstrip(' →'), key='check_submit', type='primary',
                                   disabled=used >= MAX_ANALYSES, icon=':material/arrow_forward:',
                                   icon_position='right')
            if submit:
                if len((jd or '').strip()) < MIN_JD_CHARS:
                    show_error(t('check.error'))
                else:
                    paste_ids = ss.setdefault('paste_ids', {})
                    text_key = hashlib.sha256(jd.encode()).hexdigest()       # a re-click reuses the same paste
                    try:
                        paste_id = paste_ids.get(text_key) or call(api.paste, jd)
                        paste_ids[text_key] = paste_id
                        ss.pasted = f'pasted:{paste_id}'
                        analyze('pasted_jd', ss.pasted, lambda key, hist: api.analyze_pasted(paste_id, hist, key),
                                'check', paste=paste_id)
                    except ApiError as exc:
                        show_error(friendly(exc))
        html(f'<p class="jf jf-small jf-muted">{esc(t("check.foot"))}</p>')


def search_card(job_id: str) -> dict | None:
    return next((c for c in (ss.get('search') or {}).get('jobs', []) if c['job_id'] == job_id), None)


def analysis() -> None:
    selected = ss.get('selected_job')
    entry = analyses.get(selected) if selected else None
    return_to = ss.get('return_to', 'results')
    back(t('analysis.back.check' if return_to == 'check' else 'analysis.back.results'), return_to, 'analysis_back')
    if entry is None:
        html(empty_state(t('analysis.empty.h'), t('analysis.empty.p')))
        return
    if entry['result'] is None:                 # started (now or before a rerun): poll, never re-post
        body = wait_run(entry['run_id'], t('proc.analyze.title'),
                        [t('proc.analyze.1'), t('proc.analyze.2'), t('proc.analyze.3')], return_to)
        if body['status'] != 'done':
            analyses.pop(selected, None)
            ss.analyze_error = t('err.stopped', error=body.get('error'))
            go(return_to)
        else:
            entry['result'] = body['result']
        st.rerun()
    result = entry['result']
    card = result['card']
    pasted = selected.startswith('pasted:')
    title = card.get('title') or card['job_id']
    if pasted:
        title, sub = t('pasted.title'), t('pasted.company')
    else:
        sub = ' · '.join(x for x in (card.get('company'), card.get('location')) if x)
    html(heading(esc(title), esc(sub), feature('page.analysis', 'Analyze Fit')))
    meta = search_card(selected)
    if meta:
        day = (ss.get('search') or {}).get('analysis_date')
        html(f'<div class="jf">{metadata_html(meta, date.fromisoformat(day) if day else None)}</div>')
    if card.get('url'):
        st.link_button(t('job.apply'), card['url'], type='tertiary')

    def aside() -> None:
        if card['scored']:
            with st.container(key='jfpanel_next'):
                html(f'<div class="jf"><div class="jf-h4" role="heading" aria-level="3">{esc(t("side.next.h3"))}</div>'
                     f'<p class="jf-small jf-muted jf-mt4">{esc(t("side.next.p"))}</p></div>')
                st.button(t('side.next.btn'), key='open_coach', type='primary', width='stretch', on_click=go,
                          args=('coach',))
                if ss.lang == 'id':
                    html('<p class="jf jf-small jf-muted" lang="en">Improve My CV for This Job</p>')
        html(f'<div class="jf">{quota_html(used, MAX_ANALYSES)}</div>')
    analysis_view(result, aside=aside)


def coach() -> None:
    selected = ss.get('selected_job')
    entry = analyses.get(selected) if selected else None
    if not entry or not entry.get('result') or not entry['result']['card']['scored']:
        go('analysis')
        st.rerun()
    card = entry['result']['card']
    title = t('pasted.title') if selected.startswith('pasted:') else (card.get('title') or card['job_id'])
    with st.container(key='jfmedium_coach'):
        back(t('coach.back'), 'analysis', 'coach_back')
        html(heading(esc(t('coach.h1')), esc(t('coach.desc', job=title)),
                     feature('page.coach', 'Improve My CV for This Job')))
        card_id = card['job_id']
        coach_key = f"{entry['run_id']}:{card_id}"
        cache = ss.setdefault('coach', {})
        if coach_key not in cache:
            try:
                cache[coach_key] = call(api.coach, entry['run_id'], card_id)
            except ApiError as exc:
                show_error(friendly(exc))
                return

        def answer(gap_index, done, answers, run_id=entry['run_id'], job=card_id):
            try:
                return call(api.coach_answer, run_id, job, gap_index, done, answers)
            except ApiError as exc:
                show_error(friendly(exc))
                return None
        coach_view(cache[coach_key], on_answer=answer, scope=hashlib.sha256(coach_key.encode()).hexdigest()[:12])


def market() -> None:
    origin = ss.get('market_back') or ('ready' if ss.get('cv_ready') else 'demo')
    with st.container(key='jfmedium_market'):
        back(t('market.back'), origin, 'market_back_btn')
        html(heading(esc(t('market.h1')), esc(t('market.desc')), esc(t('market.eyebrow'))))
        family = st.selectbox(t('market.role'), ['All', *ROLES], key='market_role',
                              format_func=lambda v: t('market.all') if v == 'All' else option_label('role_family')(v))
        out = call(api.market, None if family == 'All' else family, 15)
        total = max(int(out.get('postings') or 0), 1)
        rows = ''.join(
            f'<div class="jf-metric-row"><span class="jf-small">{esc(r["skill"])}</span><div class="jf-bar-track" '
            f'aria-hidden="true"><div class="jf-bar" style="width:{min(r["jobs"] / total, 1) * 100:.1f}%"></div></div>'
            f'<strong class="jf-small" title="{esc(t("market.row", n=r["jobs"], total=out.get("postings")))}">'
            f'{r["jobs"]} / {esc(out.get("postings"))}</strong></div>' for r in out['skills'])
        with st.container(key='jfpanel_market'):
            lead = out['explanation']
            if ss.lang == 'id' and out['skills']:     # the same numbers as the API sentence, in Indonesian
                top = out['skills'][0]
                lead = t('market.lead', total=out.get('postings'), skill=top['skill'], n=top['jobs'],
                         pct=round(100 * float(top.get('share') or 0)))
            html(f'<div class="jf"><p class="jf-muted" data-explanation>{esc(lead)}</p>'
                 f'{rows or "<p>" + esc(t("market.empty")) + "</p>"}'
                 f'<p class="jf-small jf-muted jf-mt6">{esc(t("market.source", source=out["source"]))}</p></div>')


def demo() -> None:
    """The saved synthetic demo (no upload): secondary, instant and free by default."""
    with st.container(key='jfmedium_demo'):
        back(t('back'), 'landing', 'demo_back')
        html(heading(esc(t('demo.h1')), esc(t('demo.desc')), esc(t('demo.eyebrow'))))
        cvs = call(api.demo_cvs)
        names = {c['cv_id']: t('demo.cv.option', id=c['cv_id'], jobs=', '.join(c['experience']) or t('demo.cv.nojobs'))
                 for c in cvs}
        with st.container(key='jfpanel_demo'):
            chosen = st.selectbox(t('demo.cv'), list(names), format_func=names.get, key='demo_cv')
            ss.chosen_cv = chosen
            seniority = st.toggle(t('demo.seniority'), value=True, help=t('demo.seniority.help'), key='demo_seniority')
            live_mode = st.toggle(t('demo.live'), value=False, help=t('demo.live.help'), key='demo_live')
            with st.expander(t('demo.filters')):
                d1, d2, d3 = st.columns(3)
                country = d1.selectbox(t('filter.country'), ['Any', 'ID', 'SG', 'MY'], key='demo_country',
                                       format_func=option_label('country_code'))
                mode = d2.selectbox(t('filter.mode'), ['Any', *WORK_MODES], key='demo_mode',
                                    format_func=option_label('work_mode'))
                posted = d3.selectbox(t('filter.posted'), [None, 7, 30], key='demo_posted',
                                      format_func=lambda v: t(f'filter.{v}') if v else t('filter.anytime'))
                include_unknown = st.checkbox(t('demo.unknown'), value=True, help=t('demo.unknown.help'),
                                              key='demo_unknown')
            filters = {'country_code': None if country == 'Any' else country,
                       'work_mode': None if mode == 'Any' else mode,
                       'posted_within_days': posted,
                       'include_unknown': include_unknown}
            with st.expander(t('demo.summary')):
                try:
                    summary = call(api.demo_summary, chosen)
                    html(f'<div class="jf"><p>{esc(t("demo.summary.location", loc=summary.get("location_suggestion") or t("demo.summary.none")))}'
                         f'</p><p class="jf-mt4">{esc(t("demo.summary.sections", sections=", ".join(summary.get("sections_found", []))))}'
                         f'</p></div>')
                    rows = [{t('demo.col.title'): e.get('title'), t('demo.col.org'): e.get('organization'),
                             t('demo.col.start'): str(e.get('start') or e.get('start_partial') or ''),
                             t('demo.col.end'): t('demo.present') if e.get('is_present')
                             else str(e.get('end') or e.get('end_partial') or '')}
                            for e in summary.get('employment', [])]
                    st.dataframe(rows, hide_index=True, width='stretch')
                    if summary.get('note'):
                        st.caption(summary['note'])
                except ApiError as exc:
                    st.caption(t('demo.summary.unavailable', status=exc.status))
            with st.expander(t('demo.text')):
                st.text(next(c['text'] for c in cvs if c['cv_id'] == chosen))
            run = st.button(t('demo.run').rstrip(' →'), key='demo_run', type='primary',
                            icon=':material/arrow_forward:', icon_position='right')
        st.button(t('ready.market'), key='demo_market', type='tertiary', on_click=open_market, args=('demo',))
        if run:
            demo_run(chosen, seniority, filters, live_mode)
        demo_results()


def demo_run(chosen: str, seniority: bool, filters: dict, live_mode: bool) -> None:
    action_key = None
    if live_mode:   # one key per user action, kept until the server acknowledges it
        action_key = actions.key_for(action_fingerprint(chosen, seniority, filters))
    try:
        run_id = call(api.start_run, chosen, seniority, filters if live_mode else None,
                      mode='live' if live_mode else 'saved', action_key=action_key)
    except ApiError as exc:
        show_error(friendly(exc))
        return
    except httpx.HTTPError:
        show_error(t('err.connection'))
        return
    if live_mode:
        actions.acknowledged(run_id)
    bar = st.progress(0.0, text=t('proc.demo.title'))      # real progress: finished jobs of K
    progress_box = st.empty()
    body = call(api.poll, run_id)
    k = (call(api.health) or {}).get('analyzed_k') or 10
    while body['status'] == 'running':
        done = body['progress']
        bar.progress(min(done / k, 1.0), text=t('proc.demo.count', done=done, k=k))
        with progress_box.container():
            for card in body['partial'][-3:]:
                st.caption('✓ ' + str(card.get('title') or card['job_id']))
        time.sleep(POLL_SECONDS)
        body = call(api.poll, run_id)
    bar.empty()
    progress_box.empty()
    if body['status'] == 'failed':
        show_error(t('demo.failed', error=body['error']))
    else:
        ss.result = body['result']
        ss.run_id = run_id
        ss.pop('tailor', None)


def demo_results() -> None:
    result = ss.get('result')
    if not result:
        return
    if result.get('source') == 'saved_demo':
        html(notice(esc(t('demo.saved'))))
    versions = result.get('versions', {})
    rule = (t('demo.rule.on', n=len(result.get('demoted_by_seniority_rule', []))) if versions.get('seniority_rule')
            else t('demo.rule.off'))
    html(f'<p class="jf jf-muted" data-analyzed>{esc(t("demo.analyzed", k=result.get("analyzed", versions.get("k")), rule=rule))}</p>')
    if result.get('empty_message'):
        html(notice(esc(result['empty_message']), 'warn'))
    for block in result['blocks']:
        groups = block['groups']
        if len(result['blocks']) > 1:
            html(f'<div class="jf jf-h2" role="heading" aria-level="2">{esc(block["title"])}</div>')
        html(f'<div class="jf jf-h3" role="heading" aria-level="2" data-demo="matches">'
             f'{esc(t("demo.matches", n=len(groups["matches"])))}</div>')
        for i, card in enumerate(groups['matches'], 1):
            job_card(card, i, api=api, run_id=ss.get('run_id'))
        if groups['conflicts']:
            html(f'<div class="jf"><div class="jf-h3" role="heading" aria-level="2">'
                 f'{esc(t("demo.conflicts", n=len(groups["conflicts"])))}</div>'
                 f'<p class="jf-small jf-muted">{esc(t("demo.conflicts.p"))}</p></div>')
            for i, card in enumerate(groups['conflicts'], 1):
                job_card(card, i, api=api, run_id=ss.get('run_id'))
        if groups['not_fully_analyzed']:
            html(f'<div class="jf jf-h3" role="heading" aria-level="2">'
                 f'{esc(t("demo.unscored", n=len(groups["not_fully_analyzed"])))}</div>')
            for i, card in enumerate(groups['not_fully_analyzed'], 1):
                job_card(card, i, api=api, run_id=ss.get('run_id'))
    html(f'<div class="jf jf-h2" role="heading" aria-level="2">{esc(t("demo.suggest.h2"))}</div>')
    if st.button(t('demo.suggest.btn'), key='demo_suggest'):
        ss.tailor = call(api.tailor, ss.run_id)
    if ss.get('tailor'):
        suggestions(ss.tailor)
    scored = [c for b in result['blocks'] for g in b['groups'].values() for c in g if c['scored']]
    if scored:
        pick = st.selectbox(t('demo.coach.pick'), [c['job_id'] for c in scored], key='demo_pick',
                            format_func=lambda j: next(c.get('title') or j for c in scored if c['job_id'] == j))
        demo_coach = call(api.coach_questions, ss.run_id, pick)

        def demo_answer(gap_index, done, answers, run_id=ss.run_id, job=pick):
            try:
                return call(api.coach_answer, run_id, job, gap_index, done, answers)
            except ApiError as exc:
                show_error(friendly(exc))
                return None
        coach_view(demo_coach, on_answer=demo_answer, scope=f'demo_{pick}')
    st.caption(t('demo.versions', v=versions))


def terminal(expired: bool) -> None:
    with st.container(key='jfnarrow_terminal'):
        html(heading(esc(t('expired.h1' if expired else 'deleted.h1')),
                     esc(t('expired.desc' if expired else 'deleted.desc'))))
        with st.container(key='jfpanel_terminal'):
            html(f'<div class="jf"><div class="jf-h2" role="heading" aria-level="2">{esc(t("terminal.h2"))}</div>'
                 f'<p class="jf-muted jf-mt4">{esc(t("terminal.p.expired" if expired else "terminal.p.deleted"))}'
                 f'</p></div>')
            st.button(t('terminal.btn'), key='terminal_home', type='primary', on_click=go, args=('landing',))


SCREENS = {'landing': landing, 'upload': upload, 'privacy': privacy, 'edit': edit, 'ready': ready, 'find': find,
           'results': results, 'check': check, 'analysis': analysis, 'coach': coach, 'market': market, 'demo': demo,
           'deleted': lambda: terminal(False), 'expired': lambda: terminal(True)}
SCREENS.get(ss.page, landing)()
footer()
modal()
scroll_to_top()
