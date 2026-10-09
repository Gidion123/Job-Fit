"""Small HTTP client for the JobFit API. The UI holds no business logic.

Production contract (CP3 Phase 2B, D-101): every request carries the internal service token
(JOBFIT_INTERNAL_TOKEN in the UI container) and the normalized client IP taken from the header
Caddy sets; a live run carries one idempotency key per user action, reused by any retry of that
action. The Caddy header and how Streamlit reads it are a deployment detail, validated there.

Owner-local validation (D-105): when JOBFIT_OWNER_TOKEN is set in the UI process environment, the
Streamlit server forwards it to the internal API as X-JobFit-Owner-Token. It never reaches the
browser, and the public UI deployment never sets it (non-owners stay behind the closed public beta).
"""
from __future__ import annotations

import os
import uuid

import httpx

API_URL = os.environ.get('JOBFIT_API_URL', 'http://127.0.0.1:8000')


class ApiClient:
    def __init__(self, base_url: str = API_URL, http: httpx.Client | None = None):
        self.base_url = base_url
        self.http = http or httpx.Client(base_url=base_url, timeout=30.0)
        self.headers: dict[str, str] = {}
        self.internal_token = os.environ.get('JOBFIT_INTERNAL_TOKEN') or None
        self.owner_token = os.environ.get('JOBFIT_OWNER_TOKEN') or None     # owner-local validation only
        self.client_ip: str | None = None

    def _ingress(self) -> dict[str, str]:
        out = {}
        if self.internal_token:
            out['X-JobFit-Internal-Token'] = self.internal_token
        if self.owner_token:
            out['X-JobFit-Owner-Token'] = self.owner_token
        if self.client_ip:
            out['X-JobFit-Client-IP'] = self.client_ip
        return out

    def start_session(self) -> None:
        s = self.http.post('/session', headers=self._ingress()).json()
        self.headers = {'X-Session-Id': s['session_id'], 'X-Session-Token': s['token']}

    def _call(self, method: str, path: str, extra_headers: dict | None = None, **kw):
        headers = {**self._ingress(), **self.headers, **(extra_headers or {})}
        r = self.http.request(method, path, headers=headers, **kw)
        if r.status_code >= 400:
            body = r.json() if r.headers.get('content-type', '').startswith('application/json') else {}
            detail = body.get('detail') if body else r.text
            raise ApiError(r.status_code, str(detail), body.get('code') if body else None)
        return r.json()

    def health(self):
        return self.http.get('/health').json()

    def demo_cvs(self):
        return self._call('GET', '/demo/cvs')

    def upload(self, name: str, data: bytes):
        return self._call('POST', '/cv/upload', files={'file': (name, data)})

    def consent(self, digest: str):
        return self._call('POST', '/cv/consent', json={'digest': digest, 'affirmative': True})

    def start_run(self, cv_id: str, seniority_rule: bool, filters: dict | None = None, mode: str = 'saved',
                  action_key: str | None = None):
        """``action_key``: one UUIDv4 per user action; pass the same key again to retry that action."""
        body = {'demo_cv_id': cv_id, 'seniority_rule': seniority_rule, 'mode': mode, **(filters or {})}
        extra = {'Idempotency-Key': action_key or str(uuid.uuid4())} if mode == 'live' else None
        return self._call('POST', '/recommendations', extra_headers=extra, json=body)['run_id']

    def poll(self, run_id: str):
        return self._call('GET', f'/recommendations/{run_id}')

    def demo_summary(self, cv_id: str):
        return self._call('GET', f'/demo/cvs/{cv_id}/summary')

    def edit_preview(self, text: str):
        return self._call('POST', '/cv/preview', json={'text': text})

    def tailor(self, run_id: str):
        return self._call('POST', '/tailor', json={'run_id': run_id})

    def coach_questions(self, run_id: str, job_id: str):
        return self._call('POST', '/tailor', json={'run_id': run_id, 'job_id': job_id})

    def coach_answer(self, run_id: str, job_id: str, gap_index: int, done: bool, answers: dict):
        return self._call('POST', '/tailor/answer', json={'run_id': run_id, 'job_id': job_id, 'gap_index': gap_index,
                                                          'done': done, 'answers': answers})

    def job(self, job_id: str):
        return self._call('GET', f'/jobs/{job_id}')

    def paste(self, jd_text: str):
        return self._call('POST', '/jobs/paste', json={'jd_text': jd_text})['paste_id']

    def analyze(self, paste_id: str, cv_id: str):
        return self._call('POST', '/analyze', json={'paste_id': paste_id, 'demo_cv_id': cv_id})['run_id']

    # --- uploaded CV (D-103/D-105): each billable action carries its own Idempotency-Key ---------------
    def parse_cv(self, action_key: str) -> str:
        return self._call('POST', '/cv/parse', extra_headers={'Idempotency-Key': action_key})['run_id']

    def search_jobs(self, filters: dict, action_key: str) -> dict:
        """Relevant Jobs (search stage, no score); synchronous."""
        return self._call('POST', '/jobs/search', extra_headers={'Idempotency-Key': action_key},
                          json={'cv_source': 'upload', **filters})

    def analyze_job(self, job_id: str, history_confirmed: bool, action_key: str) -> str:
        return self._call('POST', f'/jobs/{job_id}/analyze', extra_headers={'Idempotency-Key': action_key},
                          json={'cv_source': 'upload', 'history_confirmed': bool(history_confirmed)})['run_id']

    def analyze_pasted(self, paste_id: str, history_confirmed: bool, action_key: str) -> str:
        return self._call('POST', '/analyze', extra_headers={'Idempotency-Key': action_key},
                          json={'paste_id': paste_id, 'cv_source': 'upload',
                                'history_confirmed': bool(history_confirmed)})['run_id']

    def coach(self, run_id: str, job_id: str) -> dict:
        """Improve My CV for This Job: A/B/C/not-verified for one Analyze Fit result (deterministic)."""
        return self._call('POST', '/tailor', json={'run_id': run_id, 'job_id': job_id})

    def market(self, role_family: str | None = None, top: int = 15):
        params = {'top': top, **({'role_family': role_family} if role_family else {})}
        return self._call('GET', '/market/skills', params=params)

    def feedback(self, run_id: str, job_id: str | None, rating: str, reason: str = 'other'):
        return self._call('POST', '/feedback', json={'run_id': run_id, 'job_id': job_id, 'rating': rating, 'reason': reason})

    def heartbeat(self):
        return self._call('POST', '/session/heartbeat')

    def delete_session(self):
        out = self._call('DELETE', '/session')
        self.headers = {}
        return out


class ApiError(RuntimeError):
    def __init__(self, status: int, detail: str, code: str | None = None):
        super().__init__(f'{status}: {detail}')
        self.status, self.detail, self.code = status, detail, code
