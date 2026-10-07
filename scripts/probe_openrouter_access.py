"""Tiny paid access probe before any benchmark (D-081).

Sends one minimal structured request per model ("Reply only with OK", at most
64 output tokens, no CV or JD text) through the normal JobFit client, budget
guard and ledger. Prints only: model, ok/failed, HTTP status, a redacted provider
message, and the key's numeric usage/limit fields. Never prints the key.

Why: on 4 October an OpenRouter *workspace* lifetime budget (US$5) blocked
every request with HTTP 403 while the JobFit guard (US$19 / 18.5) still had
room. A 403 alone cannot tell budget, access or moderation apart; the provider
message can, so this probe surfaces it before a benchmark starts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from pydantic import BaseModel

from jobfit.config import get_settings

PROBE_RUN_ID = 'openrouter_access_probe_20261004'
PROMPT = [{'role': 'system', 'content': 'Reply only with OK in the field reply.'},
          {'role': 'user', 'content': 'OK?'}]


class ProbeReply(BaseModel):
    reply: str


def redact(text: str) -> str:
    text = re.sub(r'sk-[A-Za-z0-9_\-]{8,}', '[redacted-key]', text)
    text = re.sub(r'Bearer\s+\S+', 'Bearer [redacted]', text)
    return text[:300]


def classify(message: str, status) -> str:
    m = message.lower()
    if 'budget' in m or 'limit' in m and ('exceed' in m or 'reached' in m):
        return 'account_or_workspace_budget'
    if 'credit' in m or status == 402:
        return 'credits'
    if 'moderation' in m or 'flagged' in m:
        return 'moderation'
    if status == 404:
        return 'route_or_model_not_found'
    if status in (401,):
        return 'authentication'
    if status == 403:
        return 'forbidden_other'
    return 'other'


def key_status(client) -> dict:
    """Numeric fields only from GET /key. No identifiers, no key text."""
    try:
        data = client.sdk.with_options(max_retries=0, timeout=20.0).get('/key', cast_to=dict).get('data', {})
    except Exception as exc:  # status only
        return {'error': type(exc).__name__}
    return {k: data.get(k) for k in ('usage', 'limit', 'limit_remaining', 'is_free_tier', 'is_management_key')
            if k in data}


def probe(client, model_key: str) -> dict:
    try:
        # run() already holds ledger.exclusive(); chat_structured would take the same
        # flock again on a new file handle and block forever, so call the attempt directly.
        out = client._chat_attempt(model_key, PROMPT, ProbeReply, 'access_probe', 64, 0.0)
        return {'model': model_key, 'ok': True, 'reply_ok': out.reply.strip().upper().startswith('OK')}
    except Exception as exc:
        if getattr(exc, 'status_code', None) is None and type(exc).__name__ in (
                'TruncatedStructuredResponse', 'IncompleteStructuredResponse', 'ValidationError', 'JSONDecodeError'):
            # The provider generated tokens, so the route is open; only the tiny answer was imperfect.
            return {'model': model_key, 'ok': True, 'reply_ok': False, 'note': type(exc).__name__}
        status = getattr(exc, 'status_code', None)
        body = getattr(exc, 'body', None)
        message = ''
        if isinstance(body, dict):
            message = str((body.get('error') or {}).get('message') or body.get('message') or '')
        message = redact(message or str(exc))
        return {'model': model_key, 'ok': False, 'error': type(exc).__name__, 'status': status,
                'message': message, 'cause': classify(message, status)}


def run(models: list[str]) -> list[dict]:
    from scripts.run_cp23_model_sweep import CANDIDATES, SweepClient, fetch_metadata
    settings = get_settings()
    client = SweepClient(settings, run_id=PROBE_RUN_ID, chat_timeout_seconds=60.0)
    resolved = {}
    for m in models:
        if m not in CANDIDATES:
            raise SystemExit(f'Unknown model key {m}')
        model_id, cin, cout, role = CANDIDATES[m]
        resolved[m] = {'model_id': model_id, 'ceiling_in': cin, 'ceiling_out': cout, 'role': role,
                       'metadata': fetch_metadata(model_id)}
    client.configure(resolved)
    print(json.dumps({'key_numeric_status': key_status(client),
                      'jobfit_guard': {'API_BUDGET_USD': settings.api_budget_usd,
                                       'API_HARD_STOP_USD': settings.api_hard_stop_usd},
                      'local_ledger_usd': round(client.ledger.total_spent(), 6)}))
    results = []
    with client.ledger.exclusive():
        for m in models:
            r = probe(client, m)
            results.append(r)
            print(json.dumps(r))
            if not r['ok'] and r.get('cause') in ('account_or_workspace_budget', 'credits', 'authentication'):
                print(json.dumps({'stop': 'account-level block; fix the OpenRouter dashboard first'}))
                break
    return results


def require_access(models: list[str]) -> None:
    """Gate for paid runs: every listed model must answer the probe."""
    results = run(models)
    bad = [r for r in results if not r['ok']]
    if bad or len(results) != len(models):
        raise SystemExit('Access probe failed; no benchmark call was made: ' + json.dumps(bad))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--models', nargs='+', required=True)
    args = parser.parse_args()
    run(args.models)
