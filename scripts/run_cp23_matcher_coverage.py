"""D-079 stage 2: 60-pair development coverage check for a matching model that passed stage 1.

Same design as the D-076 Luna check (same 60 pairs, same saved DeepSeek
extractions, prompt v1.1, validator v1.1, G1/G2, dynamic output, 240 s timeout,
one canary call, H1/H2/H2v2 scores saved per pair). Request handling comes from
public endpoint metadata (D-079 SweepClient). Phase A worker count is the
largest value up to 20 whose conservative in-flight reservation stays within
80 percent of the cap, so the one-CV wall time is measured with that many workers.
Aggregate cap US$5.00 for all stage-2 runs together. Default is a zero-call preflight.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.config import get_settings
from jobfit.cv.parser import ParsedCV
from scripts.run_cp23_luna_matching import (OLD, V11, CappedClient, matchable, protected, reservation_upper,
                                            run_phase, write_once)
from scripts.run_cp23_model_sweep import OUT as SWEEP_OUT, SweepClient, fetch_metadata

STAGE2_CAP = 5.00
STAGE2_PREFIX = 'cp23_matcher_coverage_'


def latest_sweep_result() -> Path:
    folder = ROOT / 'evals/results/cp23/dev_eval_v2_20261004'
    files = sorted(folder.glob('model_sweep_stage1_v*.json'), key=lambda p: int(p.stem.rsplit('_v', 1)[1]))
    return files[-1]


def out_dir(model: str) -> Path:
    return ROOT / f'evals/results/cp23/matcher_coverage_{model}_v1'


def run_id(model: str) -> str:
    return f'{STAGE2_PREFIX}{model}_20261004_v1'


def phases(rankings, workers_a: int, model: str):
    cv1, cv2 = rankings['CV1'], rankings['CV2']
    return [
        {'name': 'P0_canary', 'model': model, 'workers': 1, 'pairs': [['CV2', cv2[0]]]},
        {'name': 'A_cv1_top20', 'model': model, 'workers': workers_a, 'pairs': [['CV1', j] for j in cv1[:20]]},
        {'name': 'C_remaining39', 'model': model, 'workers': 8,
         'pairs': [['CV1', j] for j in cv1[20:30]] + [['CV2', j] for j in cv2[1:30]]},
    ]


def stage2_spent(client) -> float:
    return sum(r.cost_usd for r in client.ledger.records() if r.run_id.startswith(STAGE2_PREFIX))


def preflight(model: str, check_network: bool = True):
    sweep = json.loads((SWEEP_OUT / 'plan_v1.json').read_text())
    gate = json.loads(latest_sweep_result().read_text())
    if not gate['stage2_gate_valid_4_of_4_and_macro_f1_at_least_luna'].get(model):
        raise SystemExit(f'{model} did not pass the D-079 stage-1 gate')
    item = dict(sweep['models'][model])
    if check_network:
        item['metadata'] = fetch_metadata(item['model_id'])
    settings = get_settings()
    client = SweepClient(settings, run_id=run_id(model), chat_timeout_seconds=240.0)
    client.configure({model: item})
    rankings = json.loads((OLD / 'plan.json').read_text())['rankings']
    redo = set(json.loads((V11 / 'plan_v1.json').read_text())['redo_jds'])
    uppers = reservation_upper(model, client.prices, rankings, redo)
    already = stage2_spent(client)
    remaining = STAGE2_CAP - already
    workers_a = max(w for w in range(1, 21) if sum(uppers[-w:]) <= 0.8 * remaining) if uppers[-1] <= 0.8 * remaining else 0
    plan_phases = phases(rankings, workers_a, model)
    calls = sum(1 for p in plan_phases for _, job in p['pairs'] if matchable(job, redo))
    observed = gate
    per_pair = observed['models'][model]['cost_per_valid_pair_usd']
    estimate = round(1.2 * calls * per_pair, 4)
    receipt = {'run_id': run_id(model), 'model': model, 'model_id': item['model_id'], 'decision': 'D-079 stage 2',
               'split': 'development', 'stage2_cap_usd': STAGE2_CAP, 'stage2_spent_before_usd': round(already, 6),
               'phases': plan_phases, 'matching_calls': calls, 'estimate_usd': estimate,
               'phase_a_workers': workers_a, 'peak_reservation_usd': round(sum(uppers[-max(workers_a, 8):]), 4),
               'metadata': item['metadata'], 'ledger_before_usd': client.ledger.total_spent(),
               'project_hard_stop_usd': settings.api_hard_stop_usd, 'protected_sha256': protected()}
    problems = []
    if workers_a < 4:
        problems.append('too little cap left for a parallel phase A')
    if estimate > remaining:
        problems.append('estimate above the remaining stage-2 cap')
    if client.ledger.total_spent() + remaining > settings.api_hard_stop_usd:
        problems.append('project hard stop has insufficient headroom')
    receipt['problems'] = problems
    return receipt, client, redo


def main(model: str, execute: bool, check_network: bool):
    receipt, client, redo = preflight(model, check_network)
    print(json.dumps({k: receipt[k] for k in ('run_id', 'matching_calls', 'estimate_usd', 'stage2_cap_usd',
                                               'stage2_spent_before_usd', 'phase_a_workers', 'peak_reservation_usd',
                                               'ledger_before_usd', 'problems')}, indent=1))
    if not execute:
        return
    if receipt['problems']:
        raise SystemExit('Resolve preflight problems first')
    out = out_dir(model)
    if (out / 'plan_v1.json').exists():
        raise SystemExit('This versioned run already exists')
    from scripts.probe_openrouter_access import require_access
    require_access([model])  # D-081: tiny paid probe; stops before any benchmark call
    write_once(out / 'plan_v1.json', receipt)
    if not client.verify_inference_key()['inference_key']:
        raise ValueError('Key is not an inference key')
    cvs = {cv: ParsedCV.model_validate(json.loads((OLD / f'{cv}_parse.json').read_text())['parsed'])
           for cv in ('CV1', 'CV2')}
    # Cap counts every stage-2 run together.
    capped = CappedClient(client, client.ledger.total_spent() - stage2_spent(client), cap=STAGE2_CAP)
    summaries = []
    with client.ledger.exclusive():
        for phase in receipt['phases']:
            summary = run_phase(phase, capped, cvs, redo, out)
            summaries.append(summary)
            print(json.dumps(summary), flush=True)
            if summary['stop']:
                break
    cost = sum(r.cost_usd for r in client.ledger.records() if r.run_id == receipt['run_id'])
    write_once(out / 'summary_v1.json', {'run_id': receipt['run_id'], 'phases': summaries, 'run_cost_usd': cost,
                                         'ledger_total_usd': client.ledger.total_spent(),
                                         'completed': len(summaries) == 3 and not summaries[-1]['stop']})
    print(json.dumps({'run_cost_usd': round(cost, 4), 'completed': len(summaries) == 3 and not summaries[-1]['stop']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--skip-network-check', action='store_true')
    args = parser.parse_args()
    if args.execute and args.skip_network_check:
        raise SystemExit('The metadata check is required before paid calls')
    main(args.model, args.execute, not args.skip_network_check)
