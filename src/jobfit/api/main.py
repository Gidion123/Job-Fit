"""FastAPI app for JobFit v1 (CP3.1).

Privacy follows D-051 and D-021:
- every request needs the session id and token from POST /session; data is owner-scoped;
- the heartbeat keeps the liveness lease only and never resets the idle age;
- an uploaded CV is read and masked locally; the user can edit the masked text, and
  consent is bound to that exact text; provider processing of uploaded (real) CVs stays
  disabled until the D-051 release gates pass, so analysis runs on the synthetic demo CVs;
- a pasted JD lives only in the session; it never enters the corpus or a disk cache;
- DELETE /session clears everything at once; late results are dropped; the sweeper
  enforces server expiry even if the user never sends another request;
- feedback has categories only, no free text.
All dependencies are injected (`AppDeps`), so tests run with fakes and no cost.

Production ingress (CP3 Phase 2B, D-096/D-101; ``AppDeps.ingress`` set by the prod wiring):
- every route except /health needs the internal service token (constant-time check);
- the client IP is accepted only with that token and becomes an HMAC pseudonym, never stored raw;
- POST /session is rate-limited per IP pseudonym;
- a live recommendation needs a canonical UUIDv4 Idempotency-Key: a retry of the same action gets
  the same run, never a second execution; another session or phase with that key gets 409;
- the owner token bypasses only the per-IP ticket; non-owner live needs public live and a ticket;
- pasted-JD /analyze stays closed in production live (no reservation phase is defined for it).
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import logging
import secrets
import threading
import time

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from jobfit.api.presenter import job_card, recommendation
from jobfit.cv.parser import ParsedCV
from jobfit.cv.text_extract import extract_text
from jobfit.privacy.masking import mask_local
from jobfit.schemas.api import (AnalyzeRequest, CoachAnswer, ConsentRequest, FeedbackRequest, MarketQuery, PasteRequest,
                                PreviewEdit, RunRequest, TailorRequest)
from jobfit.search.filters import JobFilters
from jobfit.session.store import SessionDenied, SessionHandle, SessionStore
from jobfit.support.cv_coach import bullet, gaps_for_job
from jobfit.support.cv_suggestions import suggestions
from jobfit.support.market_insight import skill_counts

log = logging.getLogger('jobfit.api')
REAL_CV_MESSAGE = ('Analysis of uploaded CVs is not enabled yet. Masking, preview and consent work, but the '
                   'provider privacy checks (D-051) are still open. Use a demo CV for now.')
LIVE_OFF_MESSAGE = 'Live analysis is switched off in this deployment. Use the saved demo.'
PUBLIC_LIVE_OFF_MESSAGE = 'Public live analysis is not enabled yet. Use the saved demo.'
ANALYZE_CLOSED_MESSAGE = 'Pasted job descriptions cannot be analyzed live in this deployment yet.'
INTERNAL_TOKEN_HEADER, CLIENT_IP_HEADER, OWNER_TOKEN_HEADER = ('x-jobfit-internal-token', 'x-jobfit-client-ip',
                                                             'x-jobfit-owner-token')
MAX_RUNS_PER_SESSION = 3
MAX_ANALYSES_PER_SESSION = 3
MAX_FEEDBACK = 5000


@dataclass
class AppDeps:
    store: SessionStore
    demo_cvs: Mapping[str, ParsedCV]
    # run(cv, seniority_enabled, on_result, filters) -> Recommendation
    run: Callable
    job_meta: Mapping[str, Mapping] = field(default_factory=dict)
    real_cv_enabled: bool = False
    # D-022: saved_demo(cv_id, seniority) -> presented result, or None when the saved
    # bundle does not match the current CV, configuration and rules.
    saved_demo: Callable | None = None
    live_enabled: bool = False            # fail closed (FAIL-38); the wiring passes the real value
    sweep_seconds: float | None = 30.0   # D-051 server expiry; None turns the sweeper off (tests)
    # analyze_pasted(cv, jd_text) -> JobResult (live; extraction with no disk cache)
    analyze_pasted: Callable | None = None
    # public job records of the searchable corpus (title, company, description, skills ...)
    jobs: Mapping[str, Mapping] = field(default_factory=dict)
    # demo parse summaries (ParsedCV.summary() plus the location suggestion)
    demo_summaries: Mapping[str, dict] = field(default_factory=dict)
    analyzed_k: int | None = None
    # Production ingress (Phase 2B): jobfit.live.quota.Ingress; None in dev and in tests.
    ingress: object | None = None
    public_live: bool = False
    # Periodic upkeep from the sweeper thread (prod: the 48 h quota-row purge); failures are logged
    # and retried at the next interval, and never stop the session sweeper.
    maintenance: Callable | None = None
    maintenance_seconds: float = 3600.0


@dataclass
class _Run:
    owner: str
    kind: str = 'recommendations'
    status: str = 'running'
    done: list = field(default_factory=list)
    result: dict | None = None
    error: str | None = None


def create_app(deps: AppDeps) -> FastAPI:
    runs: dict[str, _Run] = {}
    pastes: dict[str, tuple[str, str]] = {}      # paste_id -> (owner, text); session-only
    feedback: list[dict] = []
    lock = threading.Lock()
    stop = threading.Event()

    def drop_owner(owner: str) -> None:
        for key in [k for k, r in runs.items() if r.owner == owner]:
            runs.pop(key)
        for key in [k for k, (o, _) in pastes.items() if o == owner]:
            pastes.pop(key)

    def sweeper():
        last_maintenance = None
        while not stop.wait(deps.sweep_seconds):
            deps.store.sweep()
            now = time.monotonic()
            if deps.maintenance and (last_maintenance is None or now - last_maintenance >= deps.maintenance_seconds):
                last_maintenance = now
                try:
                    deps.maintenance()
                except Exception:
                    log.warning('maintenance failed; retried at the next interval')
            with lock:   # results and pasted JDs of an expired session are dropped with it
                for owner in {r.owner for r in runs.values()} | {o for o, _ in pastes.values()}:
                    if not deps.store.exists(owner):
                        drop_owner(owner)

    @asynccontextmanager
    async def lifespan(_app):
        if deps.sweep_seconds:
            threading.Thread(target=sweeper, daemon=True).start()
        yield
        stop.set()

    app = FastAPI(title='JobFit API', version='1.0', lifespan=lifespan,
                  description='Evidence-grounded job matching for early-career AI/data job seekers. '
                              'Match % is CV evidence coverage, not a hiring probability.')
    idempotency = None
    if deps.ingress is not None:
        from jobfit.live.operation import IdempotencyRegistry
        idempotency = IdempotencyRegistry()

        @app.middleware('http')
        async def internal_only(request: Request, call_next):
            if request.url.path != '/health' and not deps.ingress.internal_ok(request.headers.get(INTERNAL_TOKEN_HEADER)):
                return JSONResponse({'detail': 'Unauthorized'}, status_code=401)
            return await call_next(request)

    def _auth(x_session_id: str, x_session_token: str, activity: bool) -> SessionHandle:
        h = SessionHandle(x_session_id, x_session_token)
        try:
            deps.store.heartbeat(h, user_activity=activity)
        except SessionDenied:
            raise HTTPException(401, 'Session unavailable')
        return h

    def handle(x_session_id: str = Header(...), x_session_token: str = Header(...)) -> SessionHandle:
        return _auth(x_session_id, x_session_token, True)

    def liveness(x_session_id: str = Header(...), x_session_token: str = Header(...)) -> SessionHandle:
        return _auth(x_session_id, x_session_token, False)

    def owned_run(run_id: str, h: SessionHandle) -> _Run:
        state = runs.get(run_id)
        if state is None or state.owner != h.session_id:
            raise HTTPException(404, 'Run not found')
        return state

    def start_job(h: SessionHandle, kind: str, limit: int, work: Callable[[_Run], dict],
                  run_id: str | None = None) -> str:
        with lock:
            mine = [r for r in runs.values() if r.owner == h.session_id and r.kind == kind]
            if any(r.status == 'running' for r in mine) or len(mine) >= limit:
                raise HTTPException(429, 'Run limit for this session reached')
            run_id = run_id or secrets.token_urlsafe(12)
            runs[run_id] = state = _Run(owner=h.session_id, kind=kind)

        def target():
            try:
                out = work(state)
                with lock:
                    if runs.get(run_id) is state:      # a deleted session never gets late data
                        state.result, state.status = out, 'done'
            except Exception as exc:  # shown as a run error, never as a score; no payload in the message
                with lock:
                    if runs.get(run_id) is state:   # a safe refusal code (busy, budget ...) or the class name
                        state.status, state.error = 'failed', getattr(exc, 'code', None) or type(exc).__name__
        threading.Thread(target=target, daemon=True).start()
        return run_id

    # ---------- health and session ----------
    @app.get('/health')
    def health():
        return {'ok': True, 'real_cv_enabled': deps.real_cv_enabled, 'live_enabled': deps.live_enabled,
                'saved_demo': deps.saved_demo is not None, 'analyzed_k': deps.analyzed_k}

    @app.post('/session')
    def new_session(request: Request):
        if deps.ingress is not None:
            pseudonym = deps.ingress.ip_pseudonym(request.headers.get(CLIENT_IP_HEADER))
            if not deps.ingress.allow_session(pseudonym):
                raise HTTPException(429, 'Too many new sessions; try again later')
        h = deps.store.create()
        return {'session_id': h.session_id, 'token': h.credential}

    @app.post('/session/heartbeat')
    def heartbeat(h: SessionHandle = Depends(liveness)):
        return {'ok': True}

    @app.delete('/session')
    def delete_session(h: SessionHandle = Depends(handle)):
        deps.store.delete(h)
        with lock:
            drop_owner(h.session_id)
        return {'deleted': True}

    # ---------- CVs ----------
    @app.get('/demo/cvs')
    def demo_cvs(h: SessionHandle = Depends(handle)):
        return [{'cv_id': cv_id, 'text': cv.profile.raw_text, 'synthetic': True,
                 'experience': [e.title for e in cv.profile.experience]} for cv_id, cv in deps.demo_cvs.items()]

    @app.get('/demo/cvs/{cv_id}/summary')
    def demo_summary(cv_id: str, h: SessionHandle = Depends(handle)):
        if cv_id not in deps.demo_summaries:
            raise HTTPException(404, 'Unknown demo CV')
        return deps.demo_summaries[cv_id]

    @app.post('/cv/upload')
    async def upload(file: UploadFile = File(...), h: SessionHandle = Depends(handle)):
        data = await file.read()
        text = extract_text(data, file.filename or 'upload.txt')
        del data   # original bytes are not kept (D-051 section 2.7)
        if text.status != 'ok':
            raise HTTPException(422, text.warnings[0] if text.warnings else 'The document could not be read')
        return _set_preview(h, text.text, list(text.warnings), text.layout)

    def _set_preview(h: SessionHandle, raw: str, warnings: list, layout: str | None) -> dict:
        try:
            preview = mask_local(raw)
        except ValueError:
            raise HTTPException(422, 'No usable text after masking; nothing was sent anywhere')
        try:
            deps.store.set_preview(h, preview)
        except SessionDenied:
            raise HTTPException(401, 'Session unavailable')
        return {'masked_text': preview.text, 'digest': preview.digest, 'masked_counts': preview.counts,
                'warnings': warnings + list(preview.warnings), 'layout': layout,
                'provider_processing': 'enabled' if deps.real_cv_enabled else 'disabled',
                'message': None if deps.real_cv_enabled else REAL_CV_MESSAGE}

    @app.post('/cv/preview')
    def edit_preview(body: PreviewEdit, h: SessionHandle = Depends(handle)):
        """The user corrects the masked text; masking runs again and earlier consent is cleared."""
        return _set_preview(h, body.text, ['Edited by the user; earlier consent no longer applies.'], 'edited')

    @app.post('/cv/consent')
    def consent(body: ConsentRequest, h: SessionHandle = Depends(handle)):
        try:
            deps.store.consent(h, exact_digest=body.digest, affirmative=body.affirmative)
        except SessionDenied as exc:
            raise HTTPException(409, str(exc))
        return {'consented': True, 'provider_processing': 'enabled' if deps.real_cv_enabled else 'disabled',
                'message': None if deps.real_cv_enabled else REAL_CV_MESSAGE}

    @app.post('/cv/parse')
    def parse(h: SessionHandle = Depends(handle)):
        if not deps.real_cv_enabled:
            raise HTTPException(403, REAL_CV_MESSAGE)
        raise HTTPException(501, 'Real-CV parsing is not wired in v1')

    # ---------- recommendations ----------
    @app.post('/recommendations')
    def start(body: RunRequest, request: Request, h: SessionHandle = Depends(handle)):
        cv = deps.demo_cvs.get(body.demo_cv_id)
        if cv is None:
            raise HTTPException(404, 'Unknown demo CV')
        try:
            filters = JobFilters(role_family=body.role_family, country_code=body.country_code, city=body.city,
                                 work_mode=body.work_mode, posted_within_days=body.posted_within_days,
                                 include_unknown=body.include_unknown)
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        if body.mode == 'saved':
            if filters.active:
                raise HTTPException(422, 'Filters need a live run; the saved demo covers the unfiltered list only.')
            saved = deps.saved_demo(body.demo_cv_id, body.seniority_rule) if deps.saved_demo else None
            if saved is None:
                raise HTTPException(409, 'No saved demo matches the current configuration. Use a live run.')
            run_id = secrets.token_urlsafe(12)
            with lock:
                runs[run_id] = _Run(owner=h.session_id, status='done',
                                    result={**saved, 'source': 'saved_demo', 'label': 'Demo with saved results'})
            return {'run_id': run_id}
        if not deps.live_enabled:
            raise HTTPException(503, LIVE_OFF_MESSAGE)
        live = None
        if deps.ingress is not None:
            live = live_request(request, h, 'recommendation')
            if isinstance(live, dict):          # the same action again: its run, never a second execution
                return live

        def work(state: _Run) -> dict:
            def on_result(r):
                with lock:
                    if any(v is state for v in runs.values()):   # not after deletion
                        state.done.append(job_card(r, deps.job_meta.get(r.job_id)))
            if live is None:
                rec = deps.run(cv, body.seniority_rule, on_result, filters)
            else:
                try:
                    rec = deps.run(cv, body.seniority_rule, on_result, filters, live=live)
                except Exception as exc:
                    unknown = getattr(exc, 'code', None) == 'admission_outcome_unknown'
                    idempotency.update(live.operation_key, state='admission_unknown' if unknown else 'failed')
                    raise
                idempotency.update(live.operation_key, state='done')
            return {**recommendation(rec, deps.job_meta), 'source': 'live', 'label': 'Live analysis'}
        if live is None:
            return {'run_id': start_job(h, 'recommendations', MAX_RUNS_PER_SESSION, work)}
        try:
            run_id = start_job(h, 'recommendations', MAX_RUNS_PER_SESSION, work, run_id=live.run_id)
        except HTTPException:
            idempotency.release(live.operation_key)          # nothing started: the key is free again
            raise
        return {'run_id': run_id}

    def live_request(request: Request, h: SessionHandle, phase: str):
        """Production live admission at the API: idempotency, owner, public live and the ticket."""
        from jobfit.live.keys import operation_key
        from jobfit.live.operation import LiveRefused
        from jobfit.live.quota import LiveRequest
        try:
            op = operation_key(request.headers.get('idempotency-key') or '')
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        owner = deps.ingress.is_owner(request.headers.get(OWNER_TOKEN_HEADER))
        if not owner:
            if not deps.public_live:
                raise HTTPException(503, PUBLIC_LIVE_OFF_MESSAGE)
            # D-096: the ticket is consumed by the parse; a recommendation needs the session's ticket.
            # The public parse is not wired before the Phase 3 consent adapter, so none exists yet.
            raise HTTPException(403, 'ticket_required')
        try:
            entry, new = idempotency.claim(op, h.session_id, phase)
        except LiveRefused as exc:
            raise HTTPException(exc.status, exc.code)
        if not new:
            return {'run_id': entry.run_id, 'duplicate': True}
        return LiveRequest(operation_key=op, owner=owner, session_id=h.session_id, run_id=entry.run_id,
                           ip_pseudonym=deps.ingress.ip_pseudonym(request.headers.get(CLIENT_IP_HEADER)))

    @app.get('/recommendations/{run_id}')
    def poll(run_id: str, h: SessionHandle = Depends(handle)):
        with lock:
            state = owned_run(run_id, h)
            return {'status': state.status, 'kind': state.kind, 'progress': len(state.done),
                    'partial': list(state.done), 'result': state.result, 'error': state.error}

    def run_cards(run_id: str, h: SessionHandle) -> list[dict]:
        state = owned_run(run_id, h)
        if state.status != 'done' or state.kind != 'recommendations':
            raise HTTPException(409, 'Suggestions need a finished recommendation run')
        return [c for b in state.result['blocks'] for g in b['groups'].values() for c in g]

    @app.post('/tailor')
    def tailor(body: TailorRequest, h: SessionHandle = Depends(handle)):
        with lock:
            cards = run_cards(body.run_id, h)
        if body.job_id is None:
            return suggestions(cards)
        card = next((c for c in cards if c['job_id'] == body.job_id), None)
        if card is None or not card.get('scored'):
            raise HTTPException(404, 'Pick a scored job from this run')
        return {'job_id': body.job_id, 'gaps': gaps_for_job(card),
                'rules': 'Bullets use only your answers; "not done" gives learning ideas, never a bullet; '
                         'answers stay in this session and never change the score.'}

    @app.post('/tailor/answer')
    def tailor_answer(body: CoachAnswer, h: SessionHandle = Depends(handle)):
        with lock:
            cards = run_cards(body.run_id, h)
        card = next((c for c in cards if c['job_id'] == body.job_id and c.get('scored')), None)
        gaps = gaps_for_job(card) if card else []
        if body.gap_index >= len(gaps):
            raise HTTPException(404, 'Gap not found for this job')
        try:
            return bullet(gaps[body.gap_index]['requirement'], body.done, body.answers)
        except ValueError as exc:
            raise HTTPException(422, str(exc))

    # ---------- jobs ----------
    @app.get('/jobs/{job_id}')
    def job_detail(job_id: str, h: SessionHandle = Depends(handle)):
        job = deps.jobs.get(job_id)
        if job is None:
            raise HTTPException(404, 'Job not in the searchable corpus')
        return {k: job.get(k) for k in ('job_id', 'title', 'company', 'location', 'work_mode', 'posted_at',
                                         'experience_bucket', 'role_family', 'url', 'description')}

    @app.post('/jobs/paste')
    def paste(body: PasteRequest, h: SessionHandle = Depends(handle)):
        paste_id = secrets.token_urlsafe(12)
        with lock:
            if sum(o == h.session_id for o, _ in pastes.values()) >= MAX_ANALYSES_PER_SESSION:
                raise HTTPException(429, 'Paste limit for this session reached')
            pastes[paste_id] = (h.session_id, body.jd_text)
        return {'paste_id': paste_id, 'characters': len(body.jd_text),
                'note': 'The pasted text is kept only in this session and is treated as data, never as instructions.'}

    @app.post('/analyze')
    def analyze(body: AnalyzeRequest, h: SessionHandle = Depends(handle)):
        with lock:
            owner, text = pastes.get(body.paste_id, (None, None))
        if owner != h.session_id:
            raise HTTPException(404, 'Pasted JD not found')
        cv = deps.demo_cvs.get(body.demo_cv_id)
        if cv is None:
            raise HTTPException(404, 'Unknown demo CV')
        if not deps.live_enabled or deps.analyze_pasted is None:
            raise HTTPException(503, LIVE_OFF_MESSAGE)
        if deps.ingress is not None:
            raise HTTPException(503, ANALYZE_CLOSED_MESSAGE)

        def work(state: _Run) -> dict:
            r = deps.analyze_pasted(cv, text)
            card = job_card(r, {'title': 'Pasted job description'})
            return {'card': card, 'source': 'live', 'note': 'Pasted JDs are analyzed for this session only.'}
        return {'run_id': start_job(h, 'analysis', MAX_ANALYSES_PER_SESSION, work)}

    # ---------- market and feedback ----------
    @app.get('/market/skills')
    def market(role_family: str | None = None, top: int = 15, h: SessionHandle = Depends(handle)):
        return market_query(MarketQuery(role_family=role_family, top=top), h)

    @app.post('/market/query')
    def market_query(body: MarketQuery, h: SessionHandle = Depends(handle)):
        try:
            return skill_counts(deps.jobs, role_family=body.role_family, top=body.top)
        except ValueError as exc:
            raise HTTPException(422, str(exc))

    @app.post('/feedback')
    def give_feedback(body: FeedbackRequest, h: SessionHandle = Depends(handle)):
        with lock:
            owned_run(body.run_id, h)
            if len(feedback) >= MAX_FEEDBACK:
                feedback.pop(0)
            feedback.append({'job_id': body.job_id, 'rating': body.rating, 'reason': body.reason})
        return {'recorded': True, 'stored': 'rating and category only, no text'}

    @app.get('/feedback/summary')
    def feedback_summary(h: SessionHandle = Depends(handle)):
        from collections import Counter
        with lock:
            return {'count': len(feedback), 'ratings': dict(Counter(f['rating'] for f in feedback)),
                    'reasons': dict(Counter(f['reason'] for f in feedback))}

    return app
