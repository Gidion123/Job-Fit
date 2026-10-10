"""FastAPI app for JobFit v1 (CP3.1).

Privacy follows D-051 and D-021:
- every request needs the session id and token from POST /session; data is owner-scoped;
- the heartbeat keeps the liveness lease only and never resets the idle age;
- an uploaded CV goes through the bounded, memory-only upload boundary (``jobfit.cv.upload_guard``:
  raw body and file size limits, container checks, a bounded extraction worker, fixed error codes),
  then it is read and masked locally; the user can edit the masked text, and
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
- the owner token bypasses only the per-IP ticket and the session allowance; non-owner live needs
  public live and a ticket. The owner never bypasses the budgets, the one-operation gate,
  idempotency, the evidence and storage checks, the per-call bounds or the input envelopes.

D-103 public-beta contract (API semantics only; the Streamlit UI follows in Phase 3b):
- POST /jobs/search returns relevant jobs in retrieval order, labelled as the search stage
  (stage 'retrieval', analyzed false, match_score null); it is never a JobFit match ranking and
  no CP2.4 final-order claim applies to it;
- POST /jobs/{job_id}/analyze and the pasted-JD POST /analyze run one ``job_analysis`` operation
  (stage 'analyzed'); inputs above the D-103 envelopes are refused (413) before any reservation;
- in production the public (non-owner) beta flow runs only with the session's consented, uploaded
  CV (``cv_source=upload``); the real-CV adapter is connected, but activation stays blocked
  (``public_beta_open`` False) until the remaining privacy, artifact and release gates pass,
  whatever JOBFIT_PUBLIC_LIVE says. Demo CVs are synthetic and never stand in for that flow.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import functools
import json
import logging
import os
import secrets
import threading
import time

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from jobfit.api.presenter import SEARCH_STAGE_LABEL, analyzed_job, job_card, recommendation, retrieval_card
from jobfit.cv import upload_guard
from jobfit.cv.parser import ParsedCV
from jobfit.privacy.masking import VERSION_V2, sanitize_upload
from jobfit.privacy.structure import SanitizeRefused
from jobfit.schemas.api import (AnalyzeRequest, CoachAnswer, ConsentRequest, FeedbackRequest, JobAnalyzeRequest,
                                MarketQuery, PasteRequest, PreviewEdit, RunRequest, SearchRequest, TailorRequest)
from jobfit.search.filters import JobFilters
from jobfit.session.store import SessionDenied, SessionHandle, SessionStore
from jobfit.support.cv_coach import (bullet, gaps_for_job, not_verified, representation_items, requirement_groups,
                                     true_gaps)
from jobfit.support.cv_suggestions import suggestions
from jobfit.support.market_insight import skill_counts

log = logging.getLogger('jobfit.api')
REAL_CV_MESSAGE = ('Live analysis of uploaded CVs is not enabled yet: the remaining release and activation checks '
                   'are still pending. Masking, preview and consent work, and nothing is sent to an AI provider. '
                   'Use a demo CV for now.')
# D-104 fail-closed preview refusals: fixed codes and messages, never exception or CV text.
SANITIZE_REFUSALS = {
    'professional_boundary_not_found': ('No recognised CV section (for example Experience, Skills, Projects or '
                                        'Education) was found, so nothing can be prepared for analysis. Nothing '
                                        'was sent anywhere.'),
    'masking_failed': 'The text could not be prepared safely. Nothing was sent anywhere.',
}
LIVE_OFF_MESSAGE = 'Live analysis is switched off in this deployment. Use the saved demo.'
PUBLIC_LIVE_OFF_MESSAGE = 'Public live analysis is not enabled yet. Use the saved demo.'
ANALYZE_CLOSED_MESSAGE = 'Pasted job descriptions cannot be analyzed live in this deployment yet.'
PUBLIC_BETA_CLOSED_MESSAGE = ('The public beta is not open yet. The uploaded-CV flow is connected, but activation '
                              'waits for the remaining privacy, artifact and release checks. Use the saved demo.')
INTERNAL_TOKEN_HEADER, CLIENT_IP_HEADER, OWNER_TOKEN_HEADER = ('x-jobfit-internal-token', 'x-jobfit-client-ip',
                                                             'x-jobfit-owner-token')
MAX_RUNS_PER_SESSION = 3
MAX_ANALYSES_PER_SESSION = 3        # default; JOBFIT_SESSION_ANALYSIS_LIMIT overrides it (owner-local demo only)
SESSION_ANALYSIS_LIMIT_ENV = 'JOBFIT_SESSION_ANALYSIS_LIMIT'


def session_analysis_limit() -> int:
    """Analyze Fit runs (and pasted JDs) per session: 3 unless the deployment sets 1..50 explicitly.

    The owner-local compose file raises it for demos. Non-owner public-beta sessions stay bounded by the
    D-103 session allowance (3 job_analysis) in jobfit.live.quota whatever this says; budgets are untouched.
    """
    raw = os.environ.get(SESSION_ANALYSIS_LIMIT_ENV, '').strip()
    if not raw:
        return MAX_ANALYSES_PER_SESSION
    if not raw.isdigit() or not 1 <= int(raw) <= 50:
        raise ValueError(f'{SESSION_ANALYSIS_LIMIT_ENV} must be an integer from 1 to 50')
    return int(raw)
MAX_PREVIEWS_PER_SESSION = 5         # CV uploads plus preview edits per session (upload abuse control)
REAL_ERROR_STATUS = {'input_too_large': 413, 'parse_required': 409, 'search_required': 409,
                     'consent_required': 409, 'production_retrieval_unavailable': 503}
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
    # Prod live only: () -> bool, the persistent ledger storage root is provisioned and writable.
    live_storage_ready: Callable | None = None
    # D-103 public-beta contract. search(cv, filters) -> job ids in retrieval order (no provider call
    # for a demo CV); analyze_one(cv, *, job_id, jd_text, live) -> JobResult of one job_analysis
    # operation; job_analysis_refusal(cv, *, job_id, jd_text) -> 'input_too_large' or None, checked
    # before any reservation.
    search: Callable | None = None
    analyze_one: Callable | None = None
    job_analysis_refusal: Callable | None = None
    search_limit: int = 10
    # Real-CV public-beta adapter (CP3). Off in every shipped configuration: real_cv_enabled stays False
    # until the D-051 gates (FAIL-37 masking, provider ZDR compatibility) pass; public_beta_open is True
    # only with public live, real_cv_enabled and the D-103 per-phase eligibility. Hooks:
    # real_parse(store, handle, lease, *, live) -> ParsedCV (reserved parse);
    # real_search(store, handle, lease, filters, *, live) -> retrieval rows (reserved search);
    # consume_ticket(ip_pseudonym) -> 'consumed' | 'refused' | 'unavailable' | 'unknown'.
    real_parse: Callable | None = None
    real_search: Callable | None = None
    consume_ticket: Callable | None = None
    public_beta_open: bool = False
    telemetry: object | None = None


@dataclass
class _Run:
    owner: str
    kind: str = 'recommendations'
    status: str = 'running'
    done: list = field(default_factory=list)
    result: dict | None = None
    error: str | None = None
    real: bool = False          # derived from the uploaded CV: dropped when the preview changes
    analysis_outcome: str = 'unknown'  # classified from JobResult, never from presentation JSON
    request_id: str | None = None


def create_app(deps: AppDeps) -> FastAPI:
    from jobfit.observability.metrics import Telemetry
    from jobfit.observability.http import HTTPMetrics
    telemetry = deps.telemetry or Telemetry()
    runs: dict[str, _Run] = {}
    pastes: dict[str, tuple[str, str]] = {}      # paste_id -> (owner, text); session-only
    feedback: list[dict] = []
    lock = threading.Lock()
    analysis_limit = session_analysis_limit()
    stop = threading.Event()
    upload_slot = threading.BoundedSemaphore(1)    # one /cv/upload in flight per API process (one API process)
    previews: dict[str, int] = {}                  # session -> CV uploads plus preview edits

    def drop_owner(owner: str) -> None:
        if allowances is not None:
            allowances.drop(owner)
        if beta is not None:
            beta.drop(owner)
        previews.pop(owner, None)
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
                owners = {r.owner for r in runs.values()} | {o for o, _ in pastes.values()} | set(previews)
                owners |= beta.sessions() if beta is not None else set()
                for owner in owners | (allowances.sessions() if allowances is not None else set()):
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
    app.add_middleware(upload_guard.UploadBodyLimit)    # raw body limit of POST /cv/upload only
    idempotency = allowances = beta = None
    if deps.ingress is not None:
        from jobfit.live.operation import IdempotencyRegistry
        from jobfit.live.quota import BetaAllowances, SessionAllowances
        idempotency = IdempotencyRegistry()
        allowances = app.state.allowances = SessionAllowances()   # legacy 10-job recommendation (never admitted)
        beta = app.state.beta_allowances = BetaAllowances()       # D-103: 1 parse, 1 search, 3 job analyses

        @app.middleware('http')
        async def internal_only(request: Request, call_next):
            if request.url.path != '/health' and not deps.ingress.internal_ok(request.headers.get(INTERNAL_TOKEN_HEADER)):
                return JSONResponse({'detail': 'Unauthorized'}, status_code=401)
            return await call_next(request)

    app.state.telemetry = telemetry
    app.add_middleware(HTTPMetrics, telemetry=telemetry, routes=app.routes)

    @app.get('/metrics', include_in_schema=False)
    def metrics(request: Request):
        # Explicit even in development: no ingress is not permission to expose metrics.
        from starlette.responses import Response
        from prometheus_client import CONTENT_TYPE_LATEST
        if deps.ingress is None or not deps.ingress.internal_ok(request.headers.get(INTERNAL_TOKEN_HEADER)):
            raise HTTPException(401, 'Unauthorized')
        try:
            return Response(telemetry.render(), headers={'Content-Type': CONTENT_TYPE_LATEST,
                                                        'Cache-Control': 'no-store'})
        except Exception:
            return JSONResponse({'detail': 'Metrics unavailable'}, status_code=503)

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

    def mark_analysis_result(state: _Run, result) -> None:
        from jobfit.recommend.service import JobResult
        from jobfit.schemas.analysis import ScoreStatus
        if isinstance(result, JobResult):
            if result.hold_reason or result.score.status == ScoreStatus.ON_HOLD:
                state.analysis_outcome = 'held'
            elif result.score.status == ScoreStatus.FINAL:
                state.analysis_outcome = 'success'
            # Provisional and no-score results remain unknown, never completed.

    def start_job(h: SessionHandle, kind: str, limit: int, work: Callable[[_Run], dict],
                  run_id: str | None = None, real: bool = False, request_id: str | None = None) -> str:
        with lock:
            mine = [r for r in runs.values() if r.owner == h.session_id and r.kind == kind]
            if any(r.status == 'running' for r in mine) or len(mine) >= limit:
                raise HTTPException(429, 'Run limit for this session reached')
            run_id = run_id or secrets.token_urlsafe(12)
            runs[run_id] = state = _Run(owner=h.session_id, kind=kind, real=real, request_id=request_id)

        def target():
            try:
                from jobfit.observability.metrics import observed
                out = (observed(telemetry, 'overall_analysis', work, state,
                                classify_result=lambda _: state.analysis_outcome)
                       if kind == 'analysis' else work(state))
                if kind == 'analysis':
                    from jobfit.observability.metrics import safely
                    label = {'success': 'completed', 'held': 'held', 'refused': 'refused',
                             'failure': 'failed'}.get(state.analysis_outcome, 'unknown')
                    safely(telemetry.analysis_finished, label, state.request_id)
                with lock:
                    if runs.get(run_id) is state:      # a deleted session never gets late data
                        state.result, state.status = out, 'done'
            except Exception as exc:  # shown as a run error, never as a score; no payload in the message
                if kind == 'analysis':
                    from jobfit.observability.metrics import safely
                    label = ('refused' if type(exc).__name__ in
                             {'LiveRefused', 'RealCVRefused', 'LiveSafetyRefusal', 'SessionDenied'} else 'failed')
                    safely(telemetry.analysis_finished, label, state.request_id)
                with lock:
                    if runs.get(run_id) is state:   # a safe refusal code (busy, budget ...) or the class name
                        state.status, state.error = 'failed', getattr(exc, 'code', None) or type(exc).__name__
        try:
            threading.Thread(target=target, daemon=True).start()
        except Exception:
            with lock:                          # never leave a "running" run that no worker owns
                if runs.get(run_id) is state:
                    runs.pop(run_id)
            raise
        return run_id

    # ---------- health and session ----------
    @app.get('/health')
    def health():
        storage = None
        if deps.live_storage_ready is not None:
            try:
                storage = bool(deps.live_storage_ready())
            except Exception:
                storage = False
        return {'ok': True, 'real_cv_enabled': deps.real_cv_enabled, 'live_enabled': deps.live_enabled,
                'saved_demo': deps.saved_demo is not None, 'analyzed_k': deps.analyzed_k,
                'live_storage_ready': storage, 'analysis_limit': analysis_limit}

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

    def count_preview(request: Request, h: SessionHandle) -> str | None:
        """Upload abuse control for preview mutations (uploads and preview edits), before any upload body is
        read: at most MAX_PREVIEWS_PER_SESSION per session, then the per-IP-pseudonym hourly limit."""
        with lock:
            if previews.get(h.session_id, 0) >= MAX_PREVIEWS_PER_SESSION:
                return 'upload_rate_limited'
            if deps.ingress is not None and not deps.ingress.allow_upload(
                    deps.ingress.ip_pseudonym(request.headers.get(CLIENT_IP_HEADER))):
                return 'upload_rate_limited'
            previews[h.session_id] = previews.get(h.session_id, 0) + 1
        return None

    @app.post('/cv/upload')
    async def upload(request: Request, h: SessionHandle = Depends(handle)):
        if not upload_slot.acquire(blocking=False):       # global: before the body is consumed
            return upload_guard.rejection_response('upload_busy')
        data = None
        try:
            code = count_preview(request, h)
            if code is not None:
                return upload_guard.rejection_response(code)
            try:
                ext, data = await upload_guard.read_upload(request)
                upload_guard.check_container(data, ext)
                text = await run_in_threadpool(upload_guard.bounded_extract, data, ext)
            except upload_guard.UploadRejected as exc:   # fixed message and code; nothing kept or sent anywhere
                return upload_guard.rejection_response(exc.code)
            finally:
                del data   # original bytes are not kept (D-051 section 2.7)
            return _set_preview(h, text.text, list(text.warnings), text.layout, upload=True)
        finally:
            upload_slot.release()

    def _drop_real_runs(h: SessionHandle) -> None:
        with lock:                                   # results derived from the earlier CV are dropped
            for key in [k for k, r in runs.items() if r.owner == h.session_id and r.real]:
                runs.pop(key)

    def _set_preview(h: SessionHandle, raw: str, warnings: list, layout: str | None, *, upload: bool):
        """D-104: every upload and every edit goes through the full structural sanitizer (v2).

        An upload starts with fresh owner marks; an edit re-sanitizes with the stored marks, so a name or
        handle the user types back in is masked again. A refusal fails closed: the preview, consent and all
        derived state are invalidated, a failed fresh upload also clears the previous upload's owner marks,
        and a fixed code is returned. Owner marks never leave the session store.
        """
        try:
            marks = None if upload else deps.store.owner_marks(h)
            try:
                preview = sanitize_upload(raw, marks=marks, edited=not upload)
            except SanitizeRefused as exc:
                deps.store.invalidate_preview(h, clear_owner_marks=upload)
                _drop_real_runs(h)
                code = exc.code if exc.code in SANITIZE_REFUSALS else 'masking_failed'
                return JSONResponse({'detail': SANITIZE_REFUSALS[code], 'code': code}, status_code=422)
            deps.store.set_preview(h, preview)       # clears consent and derived data; replaces the owner marks
        except SessionDenied:
            raise HTTPException(401, 'Session unavailable') from None
        _drop_real_runs(h)
        return {'masked_text': preview.text, 'digest': preview.digest, 'masked_counts': preview.counts,
                'removed': dict(preview.removed), 'owner_repeat_guard': preview.owner_repeat_guard,
                'warnings': warnings + list(preview.warnings), 'layout': layout,
                'provider_processing': 'enabled' if deps.real_cv_enabled else 'disabled',
                'message': None if deps.real_cv_enabled else REAL_CV_MESSAGE}

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError):
        """An invalid preview edit never echoes the submitted text (FastAPI's default 422 does).

        Text that is not valid Unicode cannot reach the sanitizer, so it fails closed like a masking failure:
        the current preview, consent and derived state are invalidated (a failed edit keeps the owner marks).
        Every other route, and every non-body error here (missing session headers), keeps the default handler; body
        errors are never handed to it, so their `input` (the CV text) never reaches a response.
        """
        if request.method != 'POST' or request.url.path != '/cv/preview':
            return await request_validation_exception_handler(request, exc)
        body_errors = [e for e in exc.errors() if tuple(e.get('loc', ()))[:1] == ('body',)]
        other_errors = [e for e in exc.errors() if tuple(e.get('loc', ()))[:1] != ('body',)]
        if not body_errors:
            return await request_validation_exception_handler(request, exc)
        if other_errors:
            return await request_validation_exception_handler(request, RequestValidationError(other_errors, body=None))
        if any(error.get('type') == 'string_unicode' for error in body_errors):
            try:
                h = _auth(request.headers.get('x-session-id', ''), request.headers.get('x-session-token', ''), True)
                deps.store.invalidate_preview(h, clear_owner_marks=False)
                _drop_real_runs(h)
            except (HTTPException, SessionDenied):
                return JSONResponse({'detail': 'Session unavailable'}, status_code=401)
            return JSONResponse({'detail': SANITIZE_REFUSALS['masking_failed'], 'code': 'masking_failed'},
                                status_code=422)
        return JSONResponse({'detail': 'The edited text must be 1 to 100,000 characters of text.',
                             'code': 'preview_invalid'}, status_code=422)

    @app.post('/cv/preview')
    def edit_preview(body: PreviewEdit, request: Request, h: SessionHandle = Depends(handle)):
        """The user corrects the masked text; masking runs again and earlier consent is cleared."""
        code = count_preview(request, h)
        if code is not None:
            return upload_guard.rejection_response(code)
        return _set_preview(h, body.text, ['Edited by the user; earlier consent no longer applies.'], 'edited',
                            upload=False)

    @app.post('/cv/consent')
    def consent(body: ConsentRequest, h: SessionHandle = Depends(handle)):
        try:
            deps.store.consent(h, exact_digest=body.digest, affirmative=body.affirmative)
        except SessionDenied as exc:
            raise HTTPException(409, str(exc))
        return {'consented': True, 'provider_processing': 'enabled' if deps.real_cv_enabled else 'disabled',
                'message': None if deps.real_cv_enabled else REAL_CV_MESSAGE}

    # ---------- real-CV public beta (consented upload -> reserved parse -> search -> Analyze Fit) ----------
    def real_cv_gate() -> None:
        if not deps.real_cv_enabled:
            raise HTTPException(403, REAL_CV_MESSAGE)

    def consented_lease(h: SessionHandle):
        """Only a consented D-104 (v2) sanitized preview can reach a real-CV provider operation."""
        try:
            return deps.store.consented_lease(h, masking_version=VERSION_V2)
        except SessionDenied:
            raise HTTPException(409, 'consent_required')

    def parsed_state(h: SessionHandle):
        from jobfit.recommend.real_cv_flow import RealCVRefused, consented_parsed_cv
        lease = consented_lease(h)
        try:
            return lease, consented_parsed_cv(deps.store, h, lease)
        except RealCVRefused as exc:
            raise HTTPException(409, exc.code)
        except SessionDenied:
            raise HTTPException(409, 'consent_required')

    def real_http_error(exc: Exception) -> HTTPException:
        """A safe status and code for a real-CV refusal; never a payload or exception text."""
        code = getattr(exc, 'code', None)
        if isinstance(exc, SessionDenied):
            return HTTPException(409, 'consent_required')
        if code in REAL_ERROR_STATUS:
            return HTTPException(REAL_ERROR_STATUS[code], code)
        if code is not None and hasattr(exc, 'status'):
            return HTTPException(exc.status, code)
        return HTTPException(503, 'unavailable')

    def real_live_request(request: Request, h: SessionHandle, phase: str, action: tuple[str, dict]):
        """Admission for a real-CV operation: idempotency bound to the action; owner (no ticket, no
        allowance) or, only when the public beta is open, the durable ticket and the session allowance."""
        from jobfit.live.keys import action_fingerprint, operation_key
        from jobfit.live.operation import LiveRefused
        from jobfit.live.quota import LiveRequest
        if deps.ingress is None:
            raise HTTPException(503, LIVE_OFF_MESSAGE)         # the real-CV path runs only on the prod runtime
        try:
            op = operation_key(request.headers.get('idempotency-key') or '')
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        owner = deps.ingress.is_owner(request.headers.get(OWNER_TOKEN_HEADER))
        if not owner and not deps.public_beta_open:
            raise HTTPException(503, PUBLIC_BETA_CLOSED_MESSAGE)
        kind, identity = action
        try:
            entry, new = idempotency.claim(op, h.session_id, phase, action_fingerprint(kind, **identity))
        except LiveRefused as exc:
            raise HTTPException(exc.status, exc.code)
        if not new:
            if phase == 'job_analysis':
                request.scope['jobfit_analysis_duplicate'] = True
            return {'run_id': entry.run_id, 'duplicate': True}
        pseudonym = deps.ingress.ip_pseudonym(request.headers.get(CLIENT_IP_HEADER))
        quota = finalize = None
        if not owner:
            if pseudonym is None or deps.consume_ticket is None:
                idempotency.release(op)
                raise HTTPException(403, 'ticket_required')
            claim = beta.claim(h.session_id, phase, op, functools.partial(deps.consume_ticket, pseudonym))
            if isinstance(claim, str):
                idempotency.release(op)
                raise HTTPException(403 if claim == 'phase_not_admitted' else 429, claim)
            quota, finalize = claim.quota, claim.on_first_intent
        return LiveRequest(operation_key=op, owner=owner, ip_pseudonym=pseudonym, session_id=h.session_id,
                           run_id=entry.run_id, on_first_billable=finalize, quota=quota)

    def settle_live(h: SessionHandle, live, exc: Exception | None) -> None:
        if live is None:
            return
        if beta is not None:
            beta.release_if_pending(h.session_id, live.operation_key)   # no-op once counted
        if exc is None:
            idempotency.update(live.operation_key, state='done')
        else:
            unknown = getattr(exc, 'code', None) == 'admission_outcome_unknown'
            idempotency.update(live.operation_key, state='admission_unknown' if unknown else 'failed')

    def start_real_job(h: SessionHandle, kind: str, limit: int, live, call, present,
                       request_id: str | None = None) -> dict:
        def work(state: _Run) -> dict:
            try:
                out = call()
            except Exception as exc:
                settle_live(h, live, exc)
                raise
            settle_live(h, live, None)
            if kind == 'analysis':
                mark_analysis_result(state, out)
            return present(out)
        try:
            run_id = start_job(h, kind, limit, work, run_id=live.run_id if live else None, real=True,
                               request_id=request_id)
        except Exception:
            if live is not None:
                if beta is not None:
                    beta.release_if_pending(h.session_id, live.operation_key)
                idempotency.release(live.operation_key)
            raise
        return {'run_id': run_id}

    @app.post('/cv/parse')
    def parse(request: Request, h: SessionHandle = Depends(handle)):
        """Reserved parse of the exact consented masked CV (D-103 parse phase); polled as a run."""
        real_cv_gate()
        if deps.real_parse is None:
            raise HTTPException(503, LIVE_OFF_MESSAGE)
        lease = consented_lease(h)
        live = real_live_request(request, h, 'parse', ('real_parse', {'cv': lease.text_digest}))
        if isinstance(live, dict):
            return live

        def call():
            return deps.real_parse(deps.store, h, lease, live=live)

        def present(parsed) -> dict:
            return {'stage': 'parsed', 'source': 'live', 'summary': parsed.summary()}
        return start_real_job(h, 'parse', MAX_RUNS_PER_SESSION, live, call, present)

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
                finally:   # no-op once finalized at the first durable intent; otherwise no billable call ran
                    allowances.release_if_pending(h.session_id, live.operation_key)
                idempotency.update(live.operation_key, state='done')
            return {**recommendation(rec, deps.job_meta), 'source': 'live', 'label': 'Live analysis'}
        if live is None:
            return {'run_id': start_job(h, 'recommendations', MAX_RUNS_PER_SESSION, work)}
        try:
            run_id = start_job(h, 'recommendations', MAX_RUNS_PER_SESSION, work, run_id=live.run_id)
        except Exception:                                   # any failure before a worker owns the job
            allowances.release_if_pending(h.session_id, live.operation_key)
            idempotency.release(live.operation_key)          # nothing started: the key is free again
            raise
        return {'run_id': run_id}

    def live_request(request: Request, h: SessionHandle, phase: str, action: str | None = None):
        """Production live admission at the API: idempotency, owner, public live and the ticket.

        ``action`` (keys.action_fingerprint) binds the key to the intended action, not only to the
        session and phase; the same key for another action is refused (409).
        """
        from jobfit.live.keys import operation_key
        from jobfit.live.operation import LiveRefused
        from jobfit.live.quota import LiveRequest
        try:
            op = operation_key(request.headers.get('idempotency-key') or '')
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        owner = deps.ingress.is_owner(request.headers.get(OWNER_TOKEN_HEADER))
        if not owner and not deps.public_live:
            raise HTTPException(503, PUBLIC_LIVE_OFF_MESSAGE)
        try:
            entry, new = idempotency.claim(op, h.session_id, phase, action)
        except LiveRefused as exc:
            raise HTTPException(exc.status, exc.code)
        if not new:                         # the same action again: its run, no allowance touched
            if phase == 'job_analysis':
                request.scope['jobfit_analysis_duplicate'] = True
            return {'run_id': entry.run_id, 'duplicate': True}
        finalize = None
        if not owner:
            # D-096: one ticket covers one recommendation run. The parse (Phase 3 consent adapter)
            # marks ticket_held; until then no session holds a ticket, so this refuses.
            if not allowances.claim(h.session_id, op):
                idempotency.release(op)
                raise HTTPException(403, 'ticket_required')
            finalize = functools.partial(allowances.finalize, h.session_id, op)
        return LiveRequest(operation_key=op, owner=owner, session_id=h.session_id, run_id=entry.run_id,
                           ip_pseudonym=deps.ingress.ip_pseudonym(request.headers.get(CLIENT_IP_HEADER)),
                           on_first_billable=finalize)

    @app.get('/recommendations/{run_id}')
    def poll(run_id: str, h: SessionHandle = Depends(handle)):
        with lock:
            state = owned_run(run_id, h)
            return {'status': state.status, 'kind': state.kind, 'progress': len(state.done),
                    'partial': list(state.done), 'result': state.result, 'error': state.error}

    def run_cards(run_id: str, h: SessionHandle) -> list[dict]:
        """The analyzed cards of a finished run: a demo recommendation run, or one Analyze Fit result (D-105)."""
        state = owned_run(run_id, h)
        if state.status == 'done' and state.kind == 'analysis':
            return [state.result['card']]
        if state.status != 'done' or state.kind != 'recommendations':
            raise HTTPException(409, 'Suggestions need a finished recommendation run or Analyze Fit result')
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
        return {'job_id': body.job_id, 'gaps': gaps_for_job(card), 'representation': representation_items(card),
                'true_gaps': true_gaps(card), 'not_verified': not_verified(card),
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
            if sum(o == h.session_id for o, _ in pastes.values()) >= analysis_limit:
                raise HTTPException(429, 'Paste limit for this session reached')
            pastes[paste_id] = (h.session_id, body.jd_text)
        return {'paste_id': paste_id, 'characters': len(body.jd_text),
                'note': 'The pasted text is kept only in this session and is treated as data, never as instructions.'}

    @app.post('/analyze')
    def analyze(body: AnalyzeRequest, request: Request, h: SessionHandle = Depends(handle)):
        with lock:
            owner, text = pastes.get(body.paste_id, (None, None))
        if owner != h.session_id:
            raise HTTPException(404, 'Pasted JD not found')
        if body.cv_source == 'upload':                  # Check a Job with the consented, parsed CV
            real_cv_gate()
            if not deps.live_enabled or deps.analyze_one is None:
                raise HTTPException(503, LIVE_OFF_MESSAGE)
            lease, parsed = parsed_state(h)
            history = '1' if body.history_confirmed else '0'
            return start_job_analysis(request, h, parsed, job_id='pasted', jd_text=text,
                                      meta={'title': 'Pasted job description'},
                                      note='Pasted JDs are analyzed for this session only.',
                                      action=('pasted_jd', {'cv': lease.text_digest, 'paste': body.paste_id,
                                                            'history': history}),
                                      real=True, history_confirmed=body.history_confirmed)
        cv = deps.demo_cvs.get(body.demo_cv_id)
        if cv is None:
            raise HTTPException(404, 'Unknown demo CV')
        if not deps.live_enabled:
            raise HTTPException(503, LIVE_OFF_MESSAGE)
        if deps.ingress is not None:        # production: one job_analysis operation (D-103)
            if deps.analyze_one is None:
                raise HTTPException(503, ANALYZE_CLOSED_MESSAGE)
            return start_job_analysis(request, h, cv, job_id='pasted', jd_text=text,
                                      meta={'title': 'Pasted job description'},
                                      note='Pasted JDs are analyzed for this session only.',
                                      action=('pasted_jd', {'cv': body.demo_cv_id, 'paste': body.paste_id}))
        if deps.analyze_pasted is None:
            raise HTTPException(503, LIVE_OFF_MESSAGE)

        def work(state: _Run) -> dict:
            r = deps.analyze_pasted(cv, text)
            mark_analysis_result(state, r)
            card = job_card(r, {'title': 'Pasted job description'})
            return {'card': card, 'requirement_groups': requirement_groups(card), 'source': 'live',
                    'note': 'Pasted JDs are analyzed for this session only.'}
        return {'run_id': start_job(h, 'analysis', analysis_limit, work,
                                    request_id=request.scope.get('jobfit_request_id'))}

    # ---------- D-103 public-beta contract: search stage, then one job_analysis per chosen job ----------
    def beta_owner_only(request: Request) -> None:
        """Production, demo CV: owner only. The public flow uses the consented uploaded CV, and only once open."""
        if deps.ingress is not None and not deps.ingress.is_owner(request.headers.get(OWNER_TOKEN_HEADER)):
            raise HTTPException(503, PUBLIC_BETA_CLOSED_MESSAGE)

    @app.post('/jobs/search')
    def search_jobs(body: SearchRequest, request: Request, h: SessionHandle = Depends(handle)):
        try:
            filters = JobFilters(role_family=body.role_family, country_code=body.country_code, city=body.city,
                                 experience_bucket=body.experience_bucket, work_mode=body.work_mode,
                                 posted_within_days=body.posted_within_days, include_unknown=body.include_unknown)
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        if body.cv_source == 'upload':
            return real_search_jobs(request, h, filters)
        cv = deps.demo_cvs.get(body.demo_cv_id)
        if cv is None:
            raise HTTPException(404, 'Unknown demo CV')
        if not deps.live_enabled or deps.search is None:
            raise HTTPException(503, LIVE_OFF_MESSAGE)
        beta_owner_only(request)
        try:
            ids = list(deps.search(cv, filters))[:deps.search_limit]
        except Exception as exc:          # a safe code or the class name; never a payload
            raise HTTPException(503, getattr(exc, 'code', None) or type(exc).__name__)
        return {'stage': 'retrieval', 'final_order': False, 'label': SEARCH_STAGE_LABEL,
                'analysis_limit': analysis_limit, 'cv_source': 'demo',
                'jobs': [retrieval_card(j, i + 1, {**deps.jobs.get(j, {}), **deps.job_meta.get(j, {})})
                         for i, j in enumerate(ids)]}

    def search_identity(filters: JobFilters) -> str:
        """Canonical form of every search filter and preference (role family included), for the action.

        The same normalization the filters apply (search.filters.filter_status): country uppercased,
        city stripped and casefolded; everything else unchanged. Sorted keys, compact separators.
        """
        canonical = {
            'role_family': filters.role_family,
            'country_code': filters.country_code.upper() if filters.country_code is not None else None,
            'city': filters.city.strip().casefold() if filters.city is not None else None,
            'experience_bucket': filters.experience_bucket,
            'work_mode': filters.work_mode,
            'posted_within_days': filters.posted_within_days,
            'include_unknown': bool(filters.include_unknown),
        }
        return json.dumps(canonical, sort_keys=True, separators=(',', ':'))

    def real_search_jobs(request: Request, h: SessionHandle, filters: JobFilters) -> dict:
        """Reserved query embedding (D-103 search phase), then production retrieval; synchronous."""
        from jobfit.live.keys import operation_key
        from jobfit.recommend.real_cv_flow import search_result_key
        real_cv_gate()
        if not deps.live_enabled or deps.real_search is None:
            raise HTTPException(503, LIVE_OFF_MESSAGE)
        lease, parsed = parsed_state(h)
        # the action: the consented CV plus every normalized filter and preference (no CV or JD text)
        live = real_live_request(request, h, 'search',
                                 ('real_search', {'cv': lease.text_digest, 'filters': search_identity(filters)}))
        if isinstance(live, dict):                      # an exact retry: that operation's own results
            try:
                op = operation_key(request.headers.get('idempotency-key') or '')
                rows = deps.store.read(h, lease, search_result_key(op))
            except (KeyError, ValueError, SessionDenied):
                raise HTTPException(409, 'search_not_available')
        else:
            try:
                rows = deps.real_search(deps.store, h, lease, filters, live=live)
            except Exception as exc:
                settle_live(h, live, exc)
                raise real_http_error(exc) from None
            settle_live(h, live, None)
        # analysis_date: the date the filters used (posted window), for zero-call local refinement in the UI
        return {'stage': 'retrieval', 'final_order': False, 'label': SEARCH_STAGE_LABEL,
                'analysis_limit': analysis_limit, 'cv_source': 'upload',
                'analysis_date': parsed.analysis_date.isoformat(),
                'jobs': [retrieval_card(r['job_id'], r['retrieval_rank'], r) for r in rows[:deps.search_limit]]}

    @app.post('/jobs/{job_id}/analyze')
    def analyze_corpus_job(job_id: str, body: JobAnalyzeRequest, request: Request,
                           h: SessionHandle = Depends(handle)):
        if body.cv_source == 'upload':                  # Analyze Fit on a job from this session's Relevant Jobs
            from jobfit.recommend.real_cv_flow import SEARCH_KEY
            real_cv_gate()
            if not deps.live_enabled or deps.analyze_one is None:
                raise HTTPException(503, LIVE_OFF_MESSAGE)
            lease, parsed = parsed_state(h)
            try:
                rows = deps.store.read(h, lease, SEARCH_KEY)
            except (KeyError, SessionDenied):
                raise HTTPException(409, 'search_required')
            row = next((r for r in rows if r['job_id'] == job_id), None)
            if row is None:
                raise HTTPException(404, 'Analyze Fit needs a job from your Relevant Jobs')
            history = '1' if body.history_confirmed else '0'
            return start_job_analysis(request, h, parsed, job_id=job_id, jd_text=None, meta=row, note=None,
                                      action=('corpus_job', {'cv': lease.text_digest, 'job': job_id,
                                                             'history': history}),
                                      real=True, history_confirmed=body.history_confirmed)
        if job_id not in deps.jobs:
            raise HTTPException(404, 'Job not in the searchable corpus')
        cv = deps.demo_cvs.get(body.demo_cv_id)
        if cv is None:
            raise HTTPException(404, 'Unknown demo CV')
        if not deps.live_enabled or deps.analyze_one is None:
            raise HTTPException(503, LIVE_OFF_MESSAGE)
        return start_job_analysis(request, h, cv, job_id=job_id, jd_text=None,
                                  meta=deps.job_meta.get(job_id) or deps.jobs[job_id], note=None,
                                  action=('corpus_job', {'cv': body.demo_cv_id, 'job': job_id}))

    def start_job_analysis(request: Request, h: SessionHandle, cv, *, job_id: str, jd_text: str | None,
                           meta, note: str | None, action: tuple[str, dict], real: bool = False,
                           history_confirmed: bool = False) -> dict:
        """One job_analysis operation: owner-only in production, envelope check before any reservation.

        ``action`` names the intended action by non-sensitive ids only (the CV id and the corpus job
        id or the opaque paste id); the idempotency key is bound to its fingerprint. The real-CV
        adapter binds the consented-CV digest the same way. ``real``: the session's consented, parsed
        CV, admitted for the owner or (public beta open) through the ticket and the session allowance.
        ``history_confirmed`` (real CVs only, D-105): the user's confirmation for the current CV digest that
        it lists the whole work history; bound into the action, so another answer is another action.
        """
        if not real:
            beta_owner_only(request)
        if deps.job_analysis_refusal is not None:
            try:
                refusal = deps.job_analysis_refusal(cv, job_id=job_id, jd_text=jd_text)
            except Exception as exc:            # e.g. the job is not an eligible production job
                raise real_http_error(exc) from None
            if refusal is not None:
                raise HTTPException(413, refusal)
        if real:
            live = real_live_request(request, h, 'job_analysis', action)
            if isinstance(live, dict):
                return live
            return start_real_job(h, 'analysis', analysis_limit, live,
                                  lambda: deps.analyze_one(cv, job_id=job_id, jd_text=jd_text, live=live,
                                                           history_confirmed=history_confirmed),
                                  lambda r: {**analyzed_job(r, meta), 'source': 'live', 'cv_source': 'upload',
                                             **({'session_note': note} if note else {})},
                                  request_id=request.scope.get('jobfit_request_id'))
        live = None
        if deps.ingress is not None:
            from jobfit.live.keys import action_fingerprint
            kind, identity = action
            live = live_request(request, h, 'job_analysis', action_fingerprint(kind, **identity))
            if isinstance(live, dict):          # the same action again: its run, never a second execution
                return live

        def work(state: _Run) -> dict:
            if live is None:
                r = deps.analyze_one(cv, job_id=job_id, jd_text=jd_text, live=None)
            else:
                try:
                    r = deps.analyze_one(cv, job_id=job_id, jd_text=jd_text, live=live)
                except Exception as exc:
                    unknown = getattr(exc, 'code', None) == 'admission_outcome_unknown'
                    idempotency.update(live.operation_key, state='admission_unknown' if unknown else 'failed')
                    raise
                idempotency.update(live.operation_key, state='done')
            mark_analysis_result(state, r)
            return {**analyzed_job(r, meta), 'source': 'live', **({'session_note': note} if note else {})}
        try:
            run_id = start_job(h, 'analysis', analysis_limit, work, run_id=live.run_id if live else None,
                               request_id=request.scope.get('jobfit_request_id'))
        except Exception:
            if live is not None:
                idempotency.release(live.operation_key)      # nothing started: the key is free again
            raise
        return {'run_id': run_id}

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
