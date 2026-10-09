"""CP3 evidence-matching cost/quality/latency comparison: GPT-6 Sol vs GPT-6 Luna vs Claude Haiku 5.5.

PREPARED, NOT EXECUTED. Default is a zero-call preflight (dry run). Paid calls need --execute,
run on the owner's machine after the runtime network preflight passes.

Same as the D-079 sweep for every candidate: the four fixed development pairs (73 reviewed
units, D-062/D-063 inputs), evidence prompt v1.1, quote validator v1.1, dynamic output
policy, 240 s timeout, at most one validation repair and one length continuation, one
worker, no cache, no guardrail in the run (G1/G2 and the D-067 reference are applied in
the offline evaluation). No model-specific reasoning or effort setting. Only the model changes.

Leakage protection is identity-based: CV1/CV2 only, exactly the four approved pairs, every
job in dev_job_ids and not in test_job_ids, and exact hashes of every fixed input.

Every provider attempt (main, validation repair, length continuation) is recorded with its
latency and reported usage (input, output and reasoning tokens, provider cost) in
requests.jsonl. The project ledger stays the cost authority; nothing frozen is changed.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.config import get_settings
from jobfit.eval.qa_phase_a import FORBIDDEN_CVS, LeakageError, check_pairs, dev_path
from jobfit.llm.client import OpenRouterClient, strict_schema
from jobfit.llm.ledger import UsageLedger
from jobfit.llm.output_policy import MODEL_OUTPUT_LIMIT
from jobfit.llm.pricing import ModelPrice
from jobfit.llm.structured import REPAIR_CONTEXT_MAX_BYTES
from jobfit.matching.evidence_matcher import match_evidence
from scripts.run_cp23_luna_matching import CappedClient, write_once
from scripts.run_cp23_model_sweep import (
    EST_REPAIR_FACTOR,
    ROUTE_ERRORS,
    STOP_ERRORS,
    SweepAdapter,
    SweepClient,
    fetch_metadata,
    per_call_estimate,
    search_ids,
    stages,
)
from scripts.run_cp23_stage2_matching import inputs

CONFIG = ROOT / 'config/cp3/llm_cost_quality_comparison_v1.yaml'
APPROVED_PAIRS = (('CV1', 'F00332'), ('CV1', 'F00036'), ('CV2', 'F00815'), ('CV2', 'F00018'))
EXPECTED_UNITS = 73
KINDS = {'evidence_matching': 'main', 'evidence_matching_validation_repair': 'validation_repair',
         'evidence_matching_length_continuation': 'length_continuation'}
# Worst-case extra request bytes: the continuation note, and the repair turn (the prior output
# is kept only up to REPAIR_CONTEXT_MAX_BYTES; JSON escaping can at most double it) plus its note.
CONTINUATION_EXTRA_BYTES = 1_000
REPAIR_EXTRA_BYTES = 2 * REPAIR_CONTEXT_MAX_BYTES + 4_000
MAX_ATTEMPTS_PER_PAIR = 3


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def load_config(path: Path = CONFIG) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


# ---- development-only guard ---------------------------------------------------------------------------------

def check_dev_only(config: dict) -> list[tuple[str, str]]:
    """Primary gate is identity: CV1/CV2, the four approved pairs, dev jobs only. Raises LeakageError."""
    pairs = [tuple(p) for p in config['benchmark']['pairs']]
    if tuple(pairs) != APPROVED_PAIRS:
        raise LeakageError(f'Only the four approved D-079 development pairs are allowed, got {pairs}')
    if any(cv in FORBIDDEN_CVS for cv, _ in pairs):
        raise LeakageError('Held-out CVs are not allowed')
    check_pairs(pairs)                                  # CV1/CV2 only; job in dev ids and not in test ids
    for rel in config['protected_sha256']:               # defence in depth: no locked CP2.4 test material
        dev_path(rel)
    return pairs


def verify_protected(config: dict) -> None:
    changed = [rel for rel, h in config['protected_sha256'].items()
               if not (ROOT / rel).is_file() or digest(ROOT / rel) != h]
    if changed:
        raise ValueError(f'Protected input changed: {changed}')


def benchmark(config: dict) -> tuple[list[dict], dict]:
    """The fixed pairs and their inputs, loaded once and shared by every model."""
    pairs = check_dev_only(config)
    verify_protected(config)
    plan = stages()
    if [(s['cv_id'], s['job_id']) for s in plan] != list(pairs):
        raise ValueError('The fixed plan does not hold exactly the approved pairs')
    loaded = {(s['cv_id'], s['job_id']): inputs(s) for s in plan}    # inputs() re-checks the requirement digest
    units = sum(len(ex.units) for _, ex in loaded.values())
    if units != config['benchmark']['units'] or units != EXPECTED_UNITS:
        raise ValueError(f'Expected {EXPECTED_UNITS} units, found {units}')
    return plan, loaded


def input_digest(stage: dict, cv, extraction) -> str:
    body = {'cv_id': stage['cv_id'], 'job_id': stage['job_id'], 'cv_text': cv.profile.raw_text,
            'analysis_date': cv.analysis_date.isoformat(), 'extraction': extraction.model_dump(mode='json'),
            'duration_input': stage['duration_input']}
    return sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


# ---- request shape and conservative cost (no provider call) ---------------------------------------------------

class _ShapeProbe:
    """Captures the exact first request match_evidence would send, then stops it. No provider call."""

    def chat_structured(self, model, messages, output_model, task, max_tokens=2000, temperature=0.0):
        self.messages, self.max_tokens = messages, max_tokens
        self.schema = strict_schema(output_model.model_json_schema())
        raise RuntimeError('shape probe')


def request_shapes(plan: list[dict], loaded: dict) -> dict:
    shapes = {}
    for s in plan:
        cv, extraction = loaded[(s['cv_id'], s['job_id'])]
        probe = _ShapeProbe()
        match_evidence(cv, extraction, client=probe, model='shape-probe', duration_years=s['duration_input'],
                       cache=None, validator_version='quote-check-v1.1', guardrail_ids=(), dynamic_output=True)
        # Same byte bound CappedClient and OpenRouterClient reserve (bytes >= tokens).
        input_bound = (len(json.dumps(probe.messages, ensure_ascii=False).encode())
                       + len(json.dumps(probe.schema).encode()) + 512)
        shapes[f"{s['cv_id']}/{s['job_id']}"] = {
            'units': len(extraction.units), 'input_bytes_bound': input_bound, 'max_tokens': probe.max_tokens,
            'prompt_sha256': sha256(probe.messages[0]['content'].encode()).hexdigest(),
            'input_sha256': input_digest(s, cv, extraction)}
    return shapes


def pair_upper_tokens(shape: dict) -> tuple[int, int]:
    """Worst case: main, length continuation and validation repair, each at its largest allowance."""
    base, limit = shape['input_bytes_bound'], shape['max_tokens']
    doubled = min(MODEL_OUTPUT_LIMIT, 2 * limit)
    tokens_in = base + (base + CONTINUATION_EXTRA_BYTES) + (base + CONTINUATION_EXTRA_BYTES + REPAIR_EXTRA_BYTES)
    return tokens_in, limit + doubled + doubled


def conservative_cost(shapes: dict, candidates: dict) -> dict:
    by_model = {}
    for key, c in candidates.items():
        total = 0.0
        for shape in shapes.values():
            tin, tout = pair_upper_tokens(shape)
            total += (tin * c['ceiling_in_per_m'] + tout * c['ceiling_out_per_m']) / 1e6
        by_model[key] = round(total, 4)
    return {'by_model_usd': by_model, 'total_usd': round(sum(by_model.values()), 4),
            'basis': 'per pair: main + length continuation (2x output) + validation repair (2x output), '
                     'input as UTF-8 bytes (>= tokens), every attempt at the price ceiling'}


# ---- recording (experiment-only wrappers; the frozen client is unchanged) -------------------------------------

def _usage_value(usage, *names):
    node = usage
    for name in names:
        if node is None:
            return None
        value = getattr(node, name, None)
        if value is None:
            extra = getattr(node, 'model_extra', None) or (node if isinstance(node, dict) else {})
            value = extra.get(name) if isinstance(extra, dict) else None
        node = value
    return node


class Recorder:
    """One row per provider attempt. Metadata only: no CV text, no prompt, no output."""

    def __init__(self, path: Path | None = None):
        self.path, self.rows, self.context, self.current = path, [], {}, None
        self.attempt = 0

    def start_pair(self, **context):
        self.context, self.attempt = dict(context), 0

    def begin(self, task: str, max_tokens: int, messages: list[dict]):
        self.attempt += 1
        self.current = {**self.context, 'attempt': self.attempt, 'task': task, 'kind': KINDS.get(task, task),
                        'max_tokens_requested': max_tokens,
                        'prompt_sha256': sha256(messages[0]['content'].encode()).hexdigest(),
                        'sent': False, 'latency_ms': None, 'outcome': None}

    def request(self, kwargs: dict, rule: dict | None):
        limit = (rule or {}).get('min_output_limit')
        self.current.update(sent=True, model_id_requested=kwargs.get('model'),
                            max_tokens_sent=min(kwargs['max_tokens'], limit) if limit else kwargs.get('max_tokens'),
                            temperature_sent=None if rule and not rule.get('temperature_supported', True)
                            else kwargs.get('temperature'),
                            reasoning_param_sent='reasoning' in (kwargs.get('extra_body') or {}))

    def response(self, resp, latency_ms: int):
        usage = getattr(resp, 'usage', None)
        cost = _usage_value(usage, 'cost')
        self.current.update(
            latency_ms=latency_ms, request_id=getattr(resp, 'id', None),
            response_model=getattr(resp, 'model', None),
            provider=getattr(resp, 'provider', None) or (getattr(resp, 'model_extra', None) or {}).get('provider'),
            finish_reason=getattr(resp.choices[0], 'finish_reason', None) if getattr(resp, 'choices', None) else None,
            input_tokens=_usage_value(usage, 'prompt_tokens'), output_tokens=_usage_value(usage, 'completion_tokens'),
            reasoning_tokens=_usage_value(usage, 'completion_tokens_details', 'reasoning_tokens'),
            cached_input_tokens=_usage_value(usage, 'prompt_tokens_details', 'cached_tokens'),
            total_tokens=_usage_value(usage, 'total_tokens'),
            cost_usd_reported=float(cost) if cost is not None else None)

    def transport_error(self, exc: BaseException, latency_ms: int):
        self.current.update(latency_ms=latency_ms, transport_error=type(exc).__name__,
                            status_code=getattr(exc, 'status_code', None))

    def finish(self, outcome: str):
        row, self.current = self.current, None
        if row is None:
            return
        row['outcome'] = outcome
        self.rows.append(row)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(row, sort_keys=True) + '\n')


class RecordingAdapter(SweepAdapter):
    """SweepAdapter plus per-attempt recording. with_options keeps the adapter type and the same recorder."""

    def __init__(self, sdk, rules, recorder: Recorder):
        super().__init__(sdk, rules)
        self.recorder = recorder

    def with_options(self, **kwargs):
        return RecordingAdapter(self.sdk.with_options(**kwargs), self.rules, self.recorder)

    def create(self, **kwargs):
        if self.recorder.current is not None:
            self.recorder.request(kwargs, self.rules.get(kwargs.get('model')))
        start = time.perf_counter()
        try:
            resp = super().create(**kwargs)
        except BaseException as exc:
            if self.recorder.current is not None:
                self.recorder.transport_error(exc, round((time.perf_counter() - start) * 1000))
            raise
        if self.recorder.current is not None:
            self.recorder.response(resp, round((time.perf_counter() - start) * 1000))
        return resp


class RecordingClient(SweepClient):
    def __init__(self, *args, recorder: Recorder, **kwargs):
        super().__init__(*args, **kwargs)
        self.recorder = recorder

    def configure(self, resolved: dict):
        """Endpoint rules and price ceilings as in D-079; no reasoning/effort for any candidate."""
        self.rules = {}
        for key, item in resolved.items():
            price = ModelPrice(key, item['model_id'], item['ceiling_in'], item['ceiling_out'],
                               tuple(item['metadata']['response_aliases']), None)
            self.prices[key] = self.prices[item['model_id']] = price
            self.rules[item['model_id']] = item['metadata']

    @property
    def sdk(self):
        return RecordingAdapter(OpenRouterClient.sdk.fget(self), getattr(self, 'rules', {}), self.recorder)

    def _chat_attempt(self, model, messages, output_model, task, max_tokens, temperature):
        self.recorder.begin(task, max_tokens, messages)
        try:
            out = super()._chat_attempt(model, messages, output_model, task, max_tokens, temperature)
        except BaseException as exc:
            self.recorder.finish(type(exc).__name__)
            raise
        self.recorder.finish('returned')
        return out


# ---- preflight ------------------------------------------------------------------------------------------------

OFFLINE_METADATA = {'found': None, 'endpoints': None, 'structured_endpoints': None, 'min_output_limit': None,
                    'temperature_supported': True, 'response_aliases': [], 'cheapest_structured_price_per_m': None}


def resolve_models(config: dict, check_network: bool, fetch=None, search=None):
    fetch, search = fetch or fetch_metadata, search or search_ids
    resolved, problems = {}, []
    for key, c in config['candidates'].items():
        model_id = c.get('model_id')
        item = {'model_id': model_id, 'ceiling_in': c['ceiling_in_per_m'], 'ceiling_out': c['ceiling_out_per_m'],
                'role': c['role'], 'verified': False, 'metadata': dict(OFFLINE_METADATA)}
        resolved[key] = item
        if not model_id:
            problems.append(f'{key}: no OpenRouter id configured')
            continue
        if not check_network:
            continue
        meta = fetch(model_id)
        item['metadata'] = {**OFFLINE_METADATA, **meta}
        if not meta['found']:
            try:
                nearby = search(model_id.split('/')[-1].split('-')[0])
            except Exception as exc:  # noqa: BLE001 - the listing is informative only; the run stops either way
                nearby = [f'lookup failed: {type(exc).__name__}']
            problems.append(f'{key}: id {model_id} not found (not substituted; nearby ids for the owner: {nearby})')
        elif not meta['structured_endpoints']:
            problems.append(f'{key}: no endpoint supports structured outputs')
        elif (meta['cheapest_structured_price_per_m'][0] > item['ceiling_in'] + 1e-9
              or meta['cheapest_structured_price_per_m'][1] > item['ceiling_out'] + 1e-9):
            problems.append(f'{key}: cheapest structured price {meta["cheapest_structured_price_per_m"]} '
                            f'above the ceiling {[item["ceiling_in"], item["ceiling_out"]]}')
        else:
            item['verified'] = True
    return resolved, problems


def preflight(config: dict, check_network: bool, settings=None, fetch=None, search=None):
    settings = settings or get_settings()
    plan, loaded = benchmark(config)
    shapes = request_shapes(plan, loaded)
    resolved, problems = resolve_models(config, check_network, fetch, search)
    cost = conservative_cost(shapes, config['candidates'])
    ledger_total = UsageLedger(settings.usage_ledger).total_spent()
    if not check_network:
        problems.append('runtime network preflight not run (--skip-network-check); --execute is refused')
    if ledger_total + cost['total_usd'] > settings.api_hard_stop_usd + 1e-9:
        problems.append(f'project hard stop has insufficient headroom: ledger {ledger_total:.4f} + cap '
                        f'{cost["total_usd"]:.4f} > API_HARD_STOP_USD {settings.api_hard_stop_usd}')
    if len({s['prompt_sha256'] for s in shapes.values()}) != 1:
        problems.append('prompt hash differs between pairs')
    n_models, n_pairs = len(config['candidates']), len(plan)
    history = SimpleNamespace(ledger=UsageLedger(settings.usage_ledger))
    estimate = {k: round(n_pairs * EST_REPAIR_FACTOR * per_call_estimate(history, i), 4)
                for k, i in resolved.items()}
    receipt = {
        'run_id': config['run_id'], 'status': 'preflight', 'split': 'development', 'baseline': config['baseline'],
        'models': resolved, 'pairs': [{k: s[k] for k in ('cv_id', 'job_id', 'fixed_requirements_sha256',
                                                         'duration_input')} for s in plan],
        'units': sum(s['units'] for s in shapes.values()), 'request_shapes': shapes,
        'requests': {'expected_main': n_models * n_pairs,
                     'worst_case_with_repair_and_continuation': n_models * n_pairs * MAX_ATTEMPTS_PER_PAIR},
        'conservative_max_cost': cost, 'run_cap_usd': cost['total_usd'],
        'estimated_cost': {'by_model_usd': estimate, 'total_usd': round(sum(estimate.values()), 4),
                           'basis': 'informational, not the cap: 4 pairs x 1.5 x median reported evidence_matching '
                                    'cost per call in the ledger, else 11k/6k tokens at the ceiling (D-079 method)'},
        'system_prompt_sha256': sorted({s['prompt_sha256'] for s in shapes.values()}),
        'protected_sha256': config['protected_sha256'], 'method': config['method'],
        'ledger_before_usd': round(ledger_total, 6), 'project_hard_stop_usd': settings.api_hard_stop_usd,
        'project_budget_usd': settings.api_budget_usd,
        'output_dir': str(Path(config['output_dir']) / config['run_id']),
        'execute_ready': not problems, 'problems': problems}
    return receipt, plan, loaded


# ---- execution ------------------------------------------------------------------------------------------------

def run_benchmark(capped, recorder: Recorder, receipt: dict, plan: list[dict], loaded: dict, out: Path) -> list[dict]:
    """Every model, the same pairs in the same order, the same input objects. Failures are written, not dropped."""
    summary = []
    for key, item in receipt['models'].items():
        skipped = None
        for s in plan:
            cv, extraction = loaded[(s['cv_id'], s['job_id'])]
            base = {'model': key, 'model_id': item['model_id'], 'cv_id': s['cv_id'], 'job_id': s['job_id'],
                    'input_sha256': input_digest(s, cv, extraction)}
            if skipped:
                write_once(out / 'pairs' / f"{key}__{s['cv_id']}_{s['job_id']}.json",
                           {**base, 'status': 'not_run', 'error_code': f'model_stopped:{skipped}', 'attempts': 0,
                            'wall_ms': None, 'assessments': []})
                continue
            recorder.start_pair(model=key, model_id=item['model_id'], cv_id=s['cv_id'], job_id=s['job_id'])
            start = time.perf_counter()
            result = match_evidence(cv, extraction, client=capped, model=key, duration_years=s['duration_input'],
                                    cache=None, validator_version='quote-check-v1.1', guardrail_ids=(),
                                    dynamic_output=True)
            row = {**base, 'status': result.status, 'error_code': result.error_code, 'attempts': result.attempts,
                   'wall_ms': round((time.perf_counter() - start) * 1000),
                   'assessments': [a.model_dump(mode='json') for a in result.assessments]}
            write_once(out / 'pairs' / f"{key}__{s['cv_id']}_{s['job_id']}.json", row)
            print(json.dumps({k: row[k] for k in ('model', 'cv_id', 'job_id', 'status', 'error_code', 'wall_ms')}),
                  flush=True)
            if row['error_code'] in STOP_ERRORS:
                summary.append({'model': key, 'stopped_run': row['error_code']})
                return summary
            if row['error_code'] in ROUTE_ERRORS:
                skipped = row['error_code']
        summary.append({'model': key, 'stopped_model_after': skipped})
    return summary


def execute(receipt: dict, plan: list[dict], loaded: dict, settings=None) -> dict:
    settings = settings or get_settings()
    out = ROOT / receipt['output_dir']
    if out.exists():
        raise SystemExit(f'{out.relative_to(ROOT)} already exists; make a new run_id version instead')
    write_once(out / 'plan.json', receipt)
    recorder = Recorder(out / 'requests.jsonl')
    client = RecordingClient(settings, run_id=receipt['run_id'], chat_timeout_seconds=240.0, recorder=recorder)
    if not client.verify_inference_key()['inference_key']:
        raise SystemExit('Key is not an inference key')
    client.configure(receipt['models'])
    capped = CappedClient(client, client.ledger.total_spent(), cap=receipt['run_cap_usd'])
    run_start = time.perf_counter()
    with client.ledger.exclusive():                     # one call at a time; CappedClient avoids re-locking
        summary = run_benchmark(capped, recorder, receipt, plan, loaded, out)
    records = [r for r in client.ledger.records() if r.run_id == receipt['run_id']]
    result = {'run_id': receipt['run_id'], 'models': summary,
              'total_wall_ms': round((time.perf_counter() - run_start) * 1000),
              'ledger_cost_usd_by_model': {k: round(sum(r.cost_usd for r in records if r.model == m['model_id']), 6)
                                           for k, m in receipt['models'].items()},
              'ledger_total_after_usd': round(client.ledger.total_spent(), 6)}
    write_once(out / 'summary.json', result)
    return result


def show(receipt: dict) -> None:
    print(json.dumps({k: receipt[k] for k in ('run_id', 'split', 'baseline', 'units', 'requests',
                                               'conservative_max_cost', 'run_cap_usd', 'estimated_cost',
                                               'system_prompt_sha256',
                                               'ledger_before_usd', 'project_hard_stop_usd', 'output_dir',
                                               'execute_ready', 'problems')}, indent=1))
    print('pairs:', ', '.join(f"{p['cv_id']}x{p['job_id']}" for p in receipt['pairs']))
    for key, item in receipt['models'].items():
        m = item['metadata']
        print(f"  {key:18s} {item['model_id'] or 'UNRESOLVED':30s} verified={item['verified']} "
              f"ceiling={item['ceiling_in']}/{item['ceiling_out']} structured={m.get('structured_endpoints')} "
              f"price={m.get('cheapest_structured_price_per_m')} out_limit={m.get('min_output_limit')}")
    print('protected inputs:')
    for rel, h in receipt['protected_sha256'].items():
        print(f'  {h}  {rel}')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--execute', action='store_true', help='make the paid calls (owner machine only)')
    parser.add_argument('--skip-network-check', action='store_true', help='offline preflight; never with --execute')
    parser.add_argument('--config', type=Path, default=CONFIG)
    args = parser.parse_args(argv)
    if args.execute and args.skip_network_check:
        raise SystemExit('The runtime metadata check is required before paid calls')
    config = load_config(args.config)
    receipt, plan, loaded = preflight(config, check_network=not args.skip_network_check)
    show(receipt)
    if not args.execute:
        print('DRY RUN: no provider request was made. Add --execute (after a clean preflight) for the paid run.')
        return 0
    if receipt['problems']:
        raise SystemExit('Preflight problems must be resolved first: ' + '; '.join(receipt['problems']))
    print(json.dumps(execute(receipt, plan, loaded), indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
