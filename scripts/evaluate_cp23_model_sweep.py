"""Offline evaluation of the D-079 matching model sweep (stage 1). No model call.

Same accounting as the D-067 comparison: all 73 reference units, failed or
unassessed units count as false negatives, G1/G2 applied in evaluation with the
SQL example adapter, D-067 reference. Adds valid pairs, error direction, cost,
latency, a paired bootstrap against GPT-6 Luna (the current D-077 matcher), and
run-to-run agreement with each model's earlier saved round-one/round-two output.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.eval.matching_evaluation import reference_rows
from jobfit.eval.metrics import evidence_metrics
from jobfit.llm.ledger import UsageLedger
from jobfit.config import get_settings
from jobfit.matching.guardrails import apply_guardrails
from jobfit.schemas.analysis import CheckStatus, UnitAssessment
from jobfit.scoring.score import effective_label
from scripts.evaluate_cp23_uncertainty import error_profile, macro_f1, paired_bootstrap
from scripts.run_cp23_model_sweep import OUT, RUN_ID, stages
from scripts.run_cp23_stage2_matching import inputs

BUNDLE = ROOT / 'evals/gold/development_v13_reviewed_20261003_stage1_r3'
VALIDATED = ROOT / 'evals/results/cp23_stage2_validator_v11_20261004_v2.json'
SQL_KEY = 'CV2/F00815/P52-U10'


def predictions(stage, cv, extraction, raw_assessments):
    units = {u.unit_id: u for u in extraction.units}
    plain, guarded = {}, {}
    prefix = f"{stage['cv_id']}/{stage['job_id']}/"
    for raw in raw_assessments:
        unit = units.get(raw['unit_id'])
        if unit is None:
            continue
        value, status = effective_label(unit, UnitAssessment.model_validate(raw))
        plain[prefix + unit.unit_id] = {'label': value.value if value and status == CheckStatus.DONE else None,
                                        'status': status.value}
        guard_unit = unit.model_dump(mode='json')
        if stage['job_id'] == 'F00815' and unit.unit_id == 'P52-U10':
            guard_unit['text'] = 'SQL (PostgreSQL example)'
        adjusted, _ = apply_guardrails(guard_unit, raw, cv.profile.raw_text)
        value, status = effective_label(unit, UnitAssessment.model_validate(adjusted))
        guarded[prefix + unit.unit_id] = {'label': value.value if value and status == CheckStatus.DONE else None,
                                          'status': status.value}
    return plain, guarded


def pair_file(key, s):
    name = f"{key}__{s['cv_id']}_{s['job_id']}.json"
    redo = OUT / 'continuation_2' / name
    return redo if redo.exists() else OUT / name


def pair_status(key, s):
    path = pair_file(key, s)
    return json.loads(path.read_text())['status'] if path.exists() else None


def build():
    plan = json.loads((OUT / 'plan_v1.json').read_text())
    summary = json.loads((OUT / 'summary_v1.json').read_text())
    pairs = stages()
    truth, loaded = {}, {}
    for s in pairs:
        cv, extraction = inputs(s)
        loaded[(s['cv_id'], s['job_id'])] = (s, cv, extraction)
        for unit, label in reference_rows(BUNDLE, s, cv, extraction).items():
            truth[f"{s['cv_id']}/{s['job_id']}/{unit}"] = label
    truth[SQL_KEY] = 'MATCH'  # D-067 reference
    ledger = [r for r in UsageLedger(get_settings().usage_ledger).records() if r.run_id in (RUN_ID, RUN_ID + '_cont1', RUN_ID + '_cont2')]
    old = json.loads(VALIDATED.read_text())['stages']
    models, preds = {}, {}
    for key, item in plan['models'].items():
        plain, guarded, valid, walls, statuses = {}, {}, 0, [], []
        for s in pairs:
            path = OUT / f"{key}__{s['cv_id']}_{s['job_id']}.json"
            redo = OUT / 'continuation_2' / path.name
            if redo.exists():  # D-081: replaces a 403 workspace-budget failure; the old file stays
                path = redo
            if not path.exists():
                statuses.append('not_run')
                continue
            row = json.loads(path.read_text())
            statuses.append(row['status'] if row['status'] == 'done' else f"{row['status']}:{row['error_code']}")
            walls.append(row['wall_ms'])
            if row['status'] != 'done':
                continue
            valid += 1
            st, cv, ex = loaded[(s['cv_id'], s['job_id'])]
            p, g = predictions(st, cv, ex, row['assessments'])
            plain.update(p); guarded.update(g)
        preds[key] = guarded
        metrics = evidence_metrics(truth, guarded, alignment_verified=True)
        answered_keys = [k for k in truth if any(k.startswith(f"{s['cv_id']}/{s['job_id']}/") for s in pairs
                                                 if pair_status(key, s) == 'done')]
        calls = [r for r in ledger if r.model == item['model_id']]
        earlier = [x for x in old if x['model'] == key and x.get('source_grounded_assessments')]
        agree = total = 0
        for x in earlier:
            st, cv, ex = loaded[(x['cv_id'], x['job_id'])]
            before, _ = predictions(st, cv, ex, x['source_grounded_assessments'])
            for unit, value in before.items():
                if unit in plain and value['label'] and plain[unit]['label']:
                    total += 1
                    agree += value['label'] == plain[unit]['label']
        models[key] = {'model_id': item['model_id'], 'role': item['role'], 'pair_status': statuses,
                       'valid_pairs': valid, 'macro_f1_all_cases_guarded': metrics['macro_f1'],
                       'macro_f1_answered_only': macro_f1(answered_keys, truth, guarded) if answered_keys else None,
                       'per_class_f1': {c: v['f1'] for c, v in metrics['per_class'].items()},
                       'error_profile': error_profile(truth, guarded),
                       'cost_usd': round(sum(r.cost_usd for r in calls), 6), 'calls': len(calls),
                       'cost_per_valid_pair_usd': round(sum(r.cost_usd for r in calls) / valid, 6) if valid else None,
                       'pair_wall_ms_p50': statistics.median(walls) if walls else None,
                       'pair_wall_ms_max': max(walls) if walls else None,
                       'run_to_run_label_agreement': {'units': total, 'same': agree,
                                                      'rate': agree / total if total else None}}
    rng = random.Random(20261004)
    boot = {k: paired_bootstrap(truth, preds[k], preds['gpt-6-luna'], rng)
            for k in models if k != 'gpt-6-luna' and models[k]['valid_pairs'] == 4 and models['gpt-6-luna']['valid_pairs'] == 4}
    gate = {k: v['valid_pairs'] == 4 and v['macro_f1_all_cases_guarded'] >= models['gpt-6-luna']['macro_f1_all_cases_guarded']
            for k, v in models.items() if k != 'gpt-6-luna'}
    return {'schema_version': 'cp23-dev-model-sweep-stage1-v1', 'split': 'development', 'api_calls': 0,
            'reference': 'D-067, all 73 units, failures as false negatives, G1/G2 in evaluation',
            'models': models, 'bootstrap_vs_luna': boot,
            'stage2_gate_valid_4_of_4_and_macro_f1_at_least_luna': gate,
            'run_summary': summary,
            'limits': ['Four CV/JD pairs and 73 units: differences of a few points are noise.',
                       'Run-to-run agreement compares the same model across two runs; earlier runs used older settings.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    r = build()
    print(f"{'model':22s} valid  macroF1  answered  stronger weaker  MATCHprec  cost/pair   p50s  run2run")
    for k, v in sorted(r['models'].items(), key=lambda kv: -(kv[1]['macro_f1_all_cases_guarded'] or 0)):
        e = v['error_profile']; a = v['run_to_run_label_agreement']['rate']
        f = lambda x, d=3: '  -  ' if x is None else f'{x:.{d}f}'
        print(f"{k:22s} {v['valid_pairs']}/4   {f(v['macro_f1_all_cases_guarded'])}   {f(v['macro_f1_answered_only'])}    "
              f"{e['claims_stronger_than_gold']:3d}    {e['claims_weaker_than_gold']:3d}     {f(e['match_precision'],2)}     "
              f"{f(v['cost_per_valid_pair_usd'],4)}   {f((v['pair_wall_ms_p50'] or 0)/1000,0)}   {f(a,2)}")
    for k, b in r['bootstrap_vs_luna'].items():
        print('vs luna', k, round(b['observed_difference'], 3), [round(x, 3) for x in b['unit_bootstrap_95']],
              [round(x, 3) for x in b['pair_bootstrap_95']])
    print('stage 2 gate:', r['stage2_gate_valid_4_of_4_and_macro_f1_at_least_luna'])
    if args.write:
        folder = ROOT / 'evals/results/cp23/dev_eval_v2_20261004'
        n = 1
        while (folder / f'model_sweep_stage1_v{n}.json').exists():
            n += 1
        target = folder / f'model_sweep_stage1_v{n}.json'
        print('writing', target.name)
        with target.open('x') as stream:
            json.dump(r, stream, indent=2)
