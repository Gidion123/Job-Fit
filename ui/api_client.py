"""Small HTTP client for the JobFit API. The UI holds no business logic."""
from __future__ import annotations

import os

import httpx

API_URL = os.environ.get('JOBFIT_API_URL', 'http://127.0.0.1:8000')


class ApiClient:
    def __init__(self, base_url: str = API_URL, http: httpx.Client | None = None):
        self.base_url = base_url
        self.http = http or httpx.Client(base_url=base_url, timeout=30.0)
        self.headers: dict[str, str] = {}

    def start_session(self) -> None:
        s = self.http.post('/session').json()
        self.headers = {'X-Session-Id': s['session_id'], 'X-Session-Token': s['token']}

    def _call(self, method: str, path: str, **kw):
        r = self.http.request(method, path, headers=self.headers, **kw)
        if r.status_code >= 400:
            detail = r.json().get('detail') if r.headers.get('content-type', '').startswith('application/json') else r.text
            raise ApiError(r.status_code, str(detail))
        return r.json()

    def health(self):
        return self.http.get('/health').json()

    def demo_cvs(self):
        return self._call('GET', '/demo/cvs')

    def upload(self, name: str, data: bytes):
        return self._call('POST', '/cv/upload', files={'file': (name, data)})

    def consent(self, digest: str):
        return self._call('POST', '/cv/consent', json={'digest': digest, 'affirmative': True})

    def start_run(self, cv_id: str, seniority_rule: bool, filters: dict | None = None, mode: str = 'saved'):
        body = {'demo_cv_id': cv_id, 'seniority_rule': seniority_rule, 'mode': mode, **(filters or {})}
        return self._call('POST', '/recommendations', json=body)['run_id']

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
    def __init__(self, status: int, detail: str):
        super().__init__(f'{status}: {detail}')
        self.status, self.detail = status, detail
