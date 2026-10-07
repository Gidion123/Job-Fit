"""D-079 matching model sweep, stage 1: every candidate on the same 4 gold pairs.

Approved by Dion on 4 October 2026: test all matching candidates at once under
the same current settings. Development CV1/CV2 only. Extraction is not part of
this sweep (DeepSeek stays; a new extraction comparison needs manual mapping).

Same for every model: the four fixed development pairs and their reviewed
requirement units (D-062 inputs), evidence prompt v1.1, quote validator v1.1,
dynamic output policy v1.1, 240 s timeout, at most one validation repair and one
length continuation, no cache. Guardrails G1/G2 and the D-067 reference are
applied in the offline evaluation, exactly as for the earlier comparison.

Request handling per model comes from public endpoint metadata only: drop
`temperature` when no endpoint supports it, clamp max_tokens to the smallest
published output limit, accept published dated model aliases. Prices must be at
or below the declared ceilings (D-029 price screen). Calls run one at a time, so
the reservation never exceeds one call. A route error on a model's first pair
skips that model; budget or key errors stop the run.

Default is a zero-call preflight. --execute only on Dion's machine.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import statistics
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.config import get_settings
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.pricing import ModelPrice
from jobfit.matching.evidence_matcher import match_evidence
from scripts.run_cp23_luna_matching import CappedClient, RunCapReached, write_once
from scripts.run_cp23_stage2_matching import inputs

RUN_ID = 'cp23_model_sweep_stage1_20261004_v1'
OUT = ROOT / 'evals/results/cp23/model_sweep_v1'
CAP = 3.00
PLAN_FILE = ROOT / 'evals/results/cp23_stage2_fixed_matching_20261003_v1_plan.json'
# key: (preferred OpenRouter id, input ceiling per M, output ceiling per M, role)
CANDIDATES = {
    'gpt-6-luna': ('openai/gpt-6-luna', 0.10, 0.50, 'selected D-077'),
    'deepseek-flash': ('deepseek/deepseek-v4.1-flash', 0.30, 1.20, 'baseline'),
    'gemini-3.5-flash-lite': ('google/gemini-3.5-flash-lite', 0.30, 2.50, 'round one'),
    'deepseek-v4-pro': ('deepseek/deepseek-v4-pro', 0.66, 3.96, 'round two'),
    'gemini-3.8-flash': ('google/gemini-3.8-flash', 0.75, 3.75, 'new'),
    'claude-haiku-4.5': ('anthropic/claude-haiku-4.5', 1.00, 5.00, 'round one'),
    'gpt-6-sol': ('openai/gpt-6-sol', 2.00, 10.00, 'quality reference'),
    'claude-sonnet-5.5': ('anthropic/claude-sonnet-5.5', 2.00, 10.00, 'new'),
    'gemini-3.1-pro': ('google/gemini-3.1-pro-preview', 2.00, 12.00, 'new, preview'),
    'claude-opus-5.5': ('anthropic/claude-opus-5.5', 4.00, 20.00, 'new, upper reference'),
}
ROUTE_ERRORS = {'NotFoundError', 'BadRequestError', 'UnprocessableEntityError', 'UnexpectedResponseModel'}
# 403 stops the whole run. On 4 October the 403s for Gemini 3.1 Pro and Opus were an
# OpenRouter workspace lifetime budget (US$5), not model access (D-079 correction, D-081).
STOP_ERRORS = {'RunCapReached', 'BudgetExceeded', 'AuthenticationError', 'PermissionDeniedError'}
CONTINUATION_RUN_ID = RUN_ID + '_cont1'
CONTINUATION2_RUN_ID = RUN_ID + '_cont2'
CONT2_DIR = OUT / 'continuation_2'
# Pairs blocked by the workspace budget, not by the model (infrastructure failures).
CONT2_TASKS = [('claude-opus-5.5', 'CV1', 'F00332'), ('claude-opus-5.5', 'CV1', 'F00036'),
               ('claude-opus-5.5', 'CV2', 'F00815'), ('claude-opus-5.5', 'CV2', 'F00018'),
               ('gemini-3.1-pro', 'CV2', 'F00018')]
# Estimate only: observed median matching cost per call from the ledger when the model
# has history; otherwise 11k input and 6k output tokens at the ceiling price. x1.5 for repairs.
EST_INPUT, EST_OUTPUT, EST_REPAIR_FACTOR = 11_000, 6_000, 1.5


def per_call_estimate(client, item) -> float:
    values = sorted(r.cost_usd for r in client.ledger.records() if r.model == item['model_id'] and r.ok
                    and r.task.startswith('evidence_matching') and r.cost_source == 'reported')
    if values:
        return values[len(values) // 2]
    return (EST_INPUT * item['ceiling_in'] + EST_OUTPUT * item['ceiling_out']) / 1e6


def stages():
    plan = json.loads(PLAN_FILE.read_text())['stages']
    seen, out = set(), []
    for s in plan:
        key = (s['cv_id'], s['job_id'])
        if key not in seen:
            seen.add(key)
            out.append({k: s[k] for k in ('cv_id', 'job_id', 'fixed_requirements_sha256', 'duration_input')})
    if len(out) != 4:
        raise ValueError('Expected the four fixed development pairs')
    return out


def fetch_metadata(model_id: str) -> dict:
    import httpx
    r = httpx.get(f'https://openrouter.ai/api/v1/models/{model_id}/endpoints', timeout=20)
    if r.status_code == 404:
        return {'found': False}
    r.raise_for_status()
    data = r.json()['data']
    eps = data.get('endpoints') or []
    structured = [e for e in eps if 'structured_outputs' in (e.get('supported_parameters') or [])
                  and 'response_format' in (e.get('supported_parameters') or [])]
    limits = [e.get('max_completion_tokens') for e in structured if isinstance(e.get('max_completion_tokens'), int)]
    aliases = sorted({e['name'].split(' | ', 1)[1] for e in eps if ' | ' in (e.get('name') or '')} |
                     ({data['canonical_slug']} if data.get('canonical_slug') else set()))
    prices = [(float(e['pricing']['prompt']) * 1e6, float(e['pricing']['completion']) * 1e6) for e in structured]
    return {'found': True, 'endpoints': len(eps), 'structured_endpoints': len(structured),
            'min_output_limit': min(limits) if limits else None,
            'temperature_supported': any('temperature' in (e.get('supported_parameters') or []) for e in structured),
            'response_aliases': aliases, 'cheapest_structured_price_per_m': min(prices) if prices else None}


def search_ids(fragment: str) -> list[str]:
    import httpx
    r = httpx.get('https://openrouter.ai/api/v1/models', timeout=20)
    r.raise_for_status()
    return sorted(m['id'] for m in r.json()['data'] if fragment in m['id'])


class SweepAdapter:
    """Per-model request adaptation from public metadata. No relaxed provider policy, no retries."""

    def __init__(self, sdk, rules):
        self.sdk, self.rules = sdk, rules
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def with_options(self, **kwargs):
        return SweepAdapter(self.sdk.with_options(**kwargs), self.rules)

    def get(self, *args, **kwargs):
        return self.sdk.get(*args, **kwargs)

    def create(self, **kwargs):
        rule = self.rules.get(kwargs.get('model'))
        if rule:
            if not rule['temperature_supported']:
                kwargs.pop('temperature', None)
            if rule['min_output_limit']:
                kwargs['max_tokens'] = min(kwargs['max_tokens'], rule['min_output_limit'])
        return self.sdk.chat.completions.create(**kwargs)


class SweepClient(OpenRouterClient):
    def configure(self, resolved: dict):
        self.rules = {}
        for key, item in resolved.items():
            base = self.prices.get(key)
            price = ModelPrice(key, item['model_id'], item['ceiling_in'], item['ceiling_out'],
                               tuple(item['metadata']['response_aliases']), base.reasoning if base else None)
            self.prices[key] = self.prices[item['model_id']] = price
            self.rules[item['model_id']] = item['metadata']

    @property
    def sdk(self):
        return SweepAdapter(super().sdk, getattr(self, 'rules', {}))


def preflight(check_network: bool = True):
    settings = get_settings()
    client = SweepClient(settings, run_id=RUN_ID, chat_timeout_seconds=240.0)
    resolved, problems = {}, []
    for key, (model_id, cin, cout, role) in CANDIDATES.items():
        meta = fetch_metadata(model_id) if check_network else {
            'found': True, 'min_output_limit': None, 'temperature_supported': True, 'response_aliases': [],
            'structured_endpoints': None, 'cheapest_structured_price_per_m': None}
        item = {'model_id': model_id, 'ceiling_in': cin, 'ceiling_out': cout, 'role': role, 'metadata': meta}
        if not meta['found']:
            problems.append(f'{key}: id {model_id} not found; candidates: {search_ids(model_id.split("/")[0] + "/" + model_id.split("/")[1].split("-")[0])}')
        elif check_network and not meta['structured_endpoints']:
            problems.append(f'{key}: no endpoint supports structured outputs')
        elif check_network and (meta['cheapest_structured_price_per_m'][0] > cin + 1e-9
                                or meta['cheapest_structured_price_per_m'][1] > cout + 1e-9):
            problems.append(f'{key}: cheapest structured price {meta["cheapest_structured_price_per_m"]} above ceiling')
        resolved[key] = item
    pairs = stages()
    per_model = {k: round(len(pairs) * EST_REPAIR_FACTOR * per_call_estimate(client, i), 4) for k, i in resolved.items()}
    estimate = sum(per_model.values())
    receipt = {'run_id': RUN_ID, 'decision': 'D-079 stage 1', 'split': 'development', 'cap_usd': CAP,
               'pairs': pairs, 'models': resolved, 'estimate_usd': round(estimate, 4), 'estimate_by_model_usd': per_model,
               'project_budget_usd': settings.api_budget_usd, 'project_hard_stop_usd': settings.api_hard_stop_usd,
               'ledger_before_usd': client.ledger.total_spent(), 'problems': problems,
               'settings': {'prompt': 'evidence v1.1', 'validator': 'quote-check-v1.1', 'guardrails_in_run': [],
                            'guardrails_in_evaluation': ['G1', 'G2'], 'reference': 'D-067',
                            'dynamic_output': True, 'timeout_s': 240, 'workers': 1, 'cache': 'none'},
               'input_sha256': {str(PLAN_FILE.relative_to(ROOT)): sha256(PLAN_FILE.read_bytes()).hexdigest()}}
    if estimate > CAP:
        problems.append('estimate above cap')
    if client.ledger.total_spent() + CAP > settings.api_hard_stop_usd:
        problems.append('project hard stop has insufficient headroom')
    return receipt, client


def continue_run(models: list[str]):
    """Run only models that have no saved pair yet, under the same plan and the same cumulative cap."""
    plan = json.loads((OUT / 'plan_v1.json').read_text())
    unknown = [m for m in models if m not in plan['models']]
    if unknown:
        raise SystemExit(f'Not in the frozen plan: {unknown}')
    done = [m for m in models if any(OUT.glob(f'{m}__*.json'))]
    if done:
        raise SystemExit(f'These models already have saved pairs; make a new version instead: {done}')
    if (OUT / 'continuation_v1.json').exists():
        raise SystemExit('Continuation already used')
    settings = get_settings()
    client = SweepClient(settings, run_id=CONTINUATION_RUN_ID, chat_timeout_seconds=240.0)
    fresh = {m: fetch_metadata(plan['models'][m]['model_id']) for m in models}
    for m, meta in fresh.items():
        if not meta['found'] or not meta['structured_endpoints']:
            raise SystemExit(f'{m}: endpoint metadata changed; stop')
        plan['models'][m]['metadata'] = meta
    write_once(OUT / 'continuation_v1.json', {'run_id': CONTINUATION_RUN_ID, 'models': models,
                                               'reason': 'v1 stopped on a model-level PermissionDeniedError before these models ran',
                                               'cumulative_cap_usd': CAP, 'ledger_before_usd': client.ledger.total_spent()})
    if not client.verify_inference_key()['inference_key']:
        raise ValueError('Key is not an inference key')
    client.configure(plan['models'])
    # Cumulative cap: everything spent since the original stage-1 plan counts.
    capped = CappedClient(client, plan['ledger_before_usd'], cap=CAP)
    with client.ledger.exclusive():
        for key in models:
            for s in plan['pairs']:
                cv, extraction = inputs(s)
                start = time.perf_counter()
                result = match_evidence(cv, extraction, client=capped, model=key, duration_years=s['duration_input'],
                                        cache=None, validator_version='quote-check-v1.1', guardrail_ids=(),
                                        dynamic_output=True)
                row = {'model': key, 'model_id': plan['models'][key]['model_id'], 'cv_id': s['cv_id'],
                       'job_id': s['job_id'], 'status': result.status, 'error_code': result.error_code,
                       'attempts': result.attempts, 'wall_ms': round((time.perf_counter() - start) * 1000),
                       'assessments': [a.model_dump(mode='json') for a in result.assessments],
                       'run_id': CONTINUATION_RUN_ID}
                write_once(OUT / f"{key}__{s['cv_id']}_{s['job_id']}.json", row)
                print(json.dumps({k: row[k] for k in ('model', 'cv_id', 'job_id', 'status', 'error_code', 'wall_ms')}), flush=True)
                if row['error_code'] in STOP_ERRORS or row['error_code'] in ROUTE_ERRORS:
                    print(json.dumps({'stopped_model': key, 'reason': row['error_code']}))
                    break
    cost = sum(r.cost_usd for r in client.ledger.records() if r.run_id == CONTINUATION_RUN_ID)
    print(json.dumps({'continuation_cost_usd': round(cost, 4), 'ledger_total_usd': round(client.ledger.total_spent(), 4)}))


def continue_run_2(execute: bool):
    """Redo only the pairs blocked by the OpenRouter workspace budget. Old failure files stay as provenance."""
    plan = json.loads((OUT / 'plan_v1.json').read_text())
    by_pair = {(s['cv_id'], s['job_id']): s for s in plan['pairs']}
    for model, cv, job in CONT2_TASKS:
        old = json.loads((OUT / f'{model}__{cv}_{job}.json').read_text()) if (OUT / f'{model}__{cv}_{job}.json').exists() else None
        if old is not None and old['error_code'] != 'PermissionDeniedError':
            raise SystemExit(f'{model} {cv}/{job} was not a 403 infrastructure failure; refusing to redo it')
    settings = get_settings()
    client = SweepClient(settings, run_id=CONTINUATION2_RUN_ID, chat_timeout_seconds=240.0)
    spent_since_plan = client.ledger.total_spent() - plan['ledger_before_usd']
    est = {m: per_call_estimate(client, plan['models'][m]) * EST_REPAIR_FACTOR for m in {t[0] for t in CONT2_TASKS}}
    estimate = sum(est[m] for m, _, _ in CONT2_TASKS)
    info = {'run_id': CONTINUATION2_RUN_ID, 'tasks': CONT2_TASKS, 'estimate_usd': round(estimate, 4),
            'cumulative_cap_usd': CAP, 'spent_since_stage1_plan_usd': round(spent_since_plan, 4),
            'remaining_cap_usd': round(CAP - spent_since_plan, 4), 'ledger_usd': round(client.ledger.total_spent(), 4),
            'jobfit_guard': [settings.api_budget_usd, settings.api_hard_stop_usd]}
    print(json.dumps(info, indent=1))
    if estimate > CAP - spent_since_plan:
        raise SystemExit('Estimate above the remaining stage-1 cap; ask Dion before changing the cap')
    if not execute:
        return
    if (CONT2_DIR / 'continuation_v2.json').exists():
        raise SystemExit('Continuation 2 already used')
    from scripts.probe_openrouter_access import require_access
    require_access(sorted({t[0] for t in CONT2_TASKS}))  # tiny paid probe; stops before any benchmark call
    for m in {t[0] for t in CONT2_TASKS}:
        meta = fetch_metadata(plan['models'][m]['model_id'])
        if not meta['found'] or not meta['structured_endpoints']:
            raise SystemExit(f'{m}: endpoint metadata changed; stop')
        plan['models'][m]['metadata'] = meta
    write_once(CONT2_DIR / 'continuation_v2.json', {**info, 'reason': 'D-081: the 4 October 403s were an OpenRouter workspace lifetime budget of US$5, raised by Dion; v1 failure files kept as provenance'})
    client.configure(plan['models'])
    capped = CappedClient(client, plan['ledger_before_usd'], cap=CAP)
    with client.ledger.exclusive():
        for model, cv_id, job in CONT2_TASKS:
            s = by_pair[(cv_id, job)]
            cv, extraction = inputs(s)
            start = time.perf_counter()
            result = match_evidence(cv, extraction, client=capped, model=model, duration_years=s['duration_input'],
                                    cache=None, validator_version='quote-check-v1.1', guardrail_ids=(),
                                    dynamic_output=True)
            row = {'model': model, 'model_id': plan['models'][model]['model_id'], 'cv_id': cv_id, 'job_id': job,
                   'status': result.status, 'error_code': result.error_code, 'attempts': result.attempts,
                   'wall_ms': round((time.perf_counter() - start) * 1000),
                   'assessments': [a.model_dump(mode='json') for a in result.assessments],
                   'run_id': CONTINUATION2_RUN_ID, 'supersedes': f'{model}__{cv_id}_{job}.json (403 workspace budget)'}
            write_once(CONT2_DIR / f'{model}__{cv_id}_{job}.json', row)
            print(json.dumps({k: row[k] for k in ('model', 'cv_id', 'job_id', 'status', 'error_code', 'wall_ms')}), flush=True)
            if row['error_code'] in STOP_ERRORS:
                raise SystemExit('Stopped: ' + row['error_code'] + ' (run the access probe to see why)')
    cost = sum(r.cost_usd for r in client.ledger.records() if r.run_id == CONTINUATION2_RUN_ID)
    print(json.dumps({'continuation2_cost_usd': round(cost, 4), 'ledger_total_usd': round(client.ledger.total_spent(), 4)}))


def main(execute: bool, check_network: bool):
    receipt, client = preflight(check_network)
    print(json.dumps({k: receipt[k] for k in ('run_id', 'estimate_usd', 'estimate_by_model_usd', 'cap_usd', 'ledger_before_usd',
                                               'project_hard_stop_usd', 'problems')}, indent=1))
    for key, item in receipt['models'].items():
        m = item['metadata']
        print(f"  {key:22s} {item['model_id']:34s} temp={m.get('temperature_supported')} out_limit={m.get('min_output_limit')} "
              f"price={m.get('cheapest_structured_price_per_m')}")
    if not execute:
        return
    if receipt['problems']:
        raise SystemExit('Preflight problems must be resolved first: ' + '; '.join(receipt['problems']))
    if (OUT / 'plan_v1.json').exists():
        raise SystemExit('This versioned sweep already exists; make a new version')
    write_once(OUT / 'plan_v1.json', receipt)
    if not client.verify_inference_key()['inference_key']:
        raise ValueError('Key is not an inference key')
    client.configure(receipt['models'])
    capped = CappedClient(client, client.ledger.total_spent(), cap=CAP)
    summary = []
    with client.ledger.exclusive():
        for key in receipt['models']:
            skipped = None
            for n, s in enumerate(receipt['pairs']):
                if skipped:
                    break
                cv, extraction = inputs(s)
                start = time.perf_counter()
                result = match_evidence(cv, extraction, client=capped, model=key, duration_years=s['duration_input'],
                                        cache=None, validator_version='quote-check-v1.1', guardrail_ids=(),
                                        dynamic_output=True)
                row = {'model': key, 'model_id': receipt['models'][key]['model_id'], 'cv_id': s['cv_id'],
                       'job_id': s['job_id'], 'status': result.status, 'error_code': result.error_code,
                       'attempts': result.attempts, 'wall_ms': round((time.perf_counter() - start) * 1000),
                       'assessments': [a.model_dump(mode='json') for a in result.assessments]}
                write_once(OUT / f"{key}__{s['cv_id']}_{s['job_id']}.json", row)
                print(json.dumps({k: row[k] for k in ('model', 'cv_id', 'job_id', 'status', 'error_code', 'wall_ms')}), flush=True)
                if row['error_code'] in STOP_ERRORS:
                    write_once(OUT / 'summary_v1.json', {'run_id': RUN_ID, 'stopped': row['error_code'], 'models': summary})
                    raise SystemExit('Stopped: ' + row['error_code'])
                if row['error_code'] in ROUTE_ERRORS:
                    skipped = row['error_code']
            summary.append({'model': key, 'skipped_after_first_pair': skipped})
    cost = {k: sum(r.cost_usd for r in client.ledger.records()
                   if r.run_id == RUN_ID and r.model == receipt['models'][k]['model_id']) for k in receipt['models']}
    write_once(OUT / 'summary_v1.json', {'run_id': RUN_ID, 'stopped': None, 'models': summary, 'cost_usd': cost,
                                         'run_cost_usd': sum(cost.values()), 'ledger_total_usd': client.ledger.total_spent()})
    print(json.dumps({'run_cost_usd': round(sum(cost.values()), 4), 'cost_by_model': {k: round(v, 4) for k, v in cost.items()}}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--skip-network-check', action='store_true', help='offline preflight only')
    parser.add_argument('--continue-models', nargs='+', help='run only these unrun models (D-079 continuation)')
    parser.add_argument('--budget-recovery', action='store_true',
                        help='D-081: redo only the pairs blocked by the OpenRouter workspace budget (preflight unless --execute)')
    args = parser.parse_args()
    if args.budget_recovery:
        continue_run_2(args.execute)
        raise SystemExit(0)
    if args.continue_models:
        continue_run(args.continue_models)
        raise SystemExit(0)
    if args.execute and args.skip_network_check:
        raise SystemExit('The metadata check is required before paid calls')
    main(args.execute, not args.skip_network_check)
