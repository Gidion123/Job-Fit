"""Offline comparison for the D-076 Luna matching check. Run after run_cp23_luna_matching.py.

No model call. Compares GPT-6 Luna with the saved DeepSeek Flash pipeline v1.1
matching on the same 60 development pairs and the same JD extractions:
coverage, label agreement and direction, product-order metrics (H2v2, weight 0.5)
and one-CV K=20 wall time from phases A (Luna) and B (DeepSeek).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.eval.product_order import held_score, product_order_metrics
from jobfit.schemas.analysis import ScoreResult, UnitAssessment
from jobfit.schemas.requirements import JDExtraction
from jobfit.scoring.hold_policy_v11 import score_with_hold_policy
from jobfit.scoring.score import effective_label
from scripts.evaluate_cp23_product_order import OLD, NEW, SPLIT, judgments, load_pair, read
from scripts.run_cp23_luna_matching import OUT, V1_OUT, matchable
import statistics

RANK = {'NO_MATCH': 0, 'PARTIAL': 1, 'MATCH': 2}


def labels(extraction: JDExtraction, assessments) -> dict[str, str | None]:
    units = {u.unit_id: u for u in extraction.units}
    out = {}
    for a in assessments:
        a = UnitAssessment.model_validate(a)
        if a.unit_id in units:
            value, _ = effective_label(units[a.unit_id], a)
            out[a.unit_id] = value.value if value else None
    return out


def build(out_dir: Path, model: str = 'gpt-6-luna') -> dict:
    rankings = read(OLD / 'plan.json')['rankings']
    redo = set(read(NEW / 'plan_v1.json')['redo_jds'])
    eligible = SPLIT.read_text().splitlines()
    judged = judgments()
    summary = read(out_dir / 'summary_v1.json')
    luna_rows = {}
    for path in out_dir.glob('*__*.json'):
        row = read(path)
        if row['model'] == model:
            luna_rows[(row['cv_id'], row['job_id'])] = row
    if len(luna_rows) != 60:
        raise ValueError(f'Expected 60 {model} pair records, found {len(luna_rows)}')

    agree = total = stronger = weaker = 0
    usable = {'deepseek': 0, model: 0}
    luna_scores, ds_scores = {}, {}
    for (cv, job), row in luna_rows.items():
        inputs, reason, _ = load_pair(cv, job, redo)
        extraction = matchable(job, redo)
        if inputs is None:
            ds_scores[(cv, job)] = held_score(reason)
        else:
            ds_scores[(cv, job)] = score_with_hold_policy(*inputs, policy='H2v2')[0]
        if row['status'] == 'held_extraction' or extraction is None:
            luna_scores[(cv, job)] = held_score('held_extraction')
        else:
            luna_scores[(cv, job)] = ScoreResult.model_validate(row['scores']['H2v2']['score'])
            if inputs is not None and row['status'] == 'done':
                a, b = labels(extraction, inputs[1]), labels(extraction, row['assessments'])
                for unit, ds_label in a.items():
                    lu = b.get(unit)
                    if ds_label is None or lu is None:
                        continue
                    total += 1
                    agree += ds_label == lu
                    stronger += RANK[lu] > RANK[ds_label]
                    weaker += RANK[lu] < RANK[ds_label]
        for name, sc in (('deepseek', ds_scores), (model, luna_scores)):
            usable[name] += sc[(cv, job)].status.value in ('final', 'provisional')
    order = []
    for cv, ranking in rankings.items():
        for k in (10, 20):
            top = ranking[:k]
            for name, sc in (('deepseek', ds_scores), (model, luna_scores)):
                m = product_order_metrics(top, {j: sc[(cv, j)] for j in top}, judged[cv], eligible_ids=eligible)
                order.append({'cv_id': cv, 'k': k, 'matcher': name, 'p_at_5': m['p_at_5'],
                              'ndcg_at_10': m['ndcg_at_10'], 'unscored_in_top_k': m['unscored_count'],
                              'unjudged_final_top10': m['unjudged_final_top10']})
    def stats(values):
        values = sorted(values)
        if not values:
            return None
        return {'n': len(values), 'p50_ms': statistics.median(values),
                'p95_ms': values[min(len(values) - 1, int(round(0.95 * (len(values) - 1))))], 'max_ms': values[-1]}
    v1_parallel = [read(x)['wall_ms'] for x in V1_OUT.glob('B_deepseek_cv1_top20__*.json')
                   if read(x)['status'] == 'done']
    v11_pairs = [read(x).get('wall_ms') for x in NEW.glob('pair_CV*_v11.json')
                 if read(x).get('source') == 'v11_matching' and read(x).get('status') == 'done']
    luna_phase_a = [r['wall_ms'] for (cv, job), r in luna_rows.items()
                    if r['status'] == 'done' and cv == 'CV1' and job in rankings['CV1'][:20]]
    latency = {f'{model}_cv1_top20_pair_wall': stats(luna_phase_a),
               'deepseek_v1_8_parallel_calls_pair_wall': stats(v1_parallel),
               'deepseek_v11_4_worker_pair_wall': stats([x for x in v11_pairs if x]),
               'note': 'Phase wall times are in latency_and_cost.phases. DeepSeek one-CV wall time is not '
                       'measured with 20 workers; with full parallelism it is bounded by its slowest pair.'}
    return {'schema_version': 'cp23-dev-luna-comparison-v1', 'model': model, 'latency_reference': latency, 'split': 'development', 'api_calls': 0,
            'hold_policy': 'H2v2', 'partial_weight': 0.5,
            'usable_pairs_of_60': usable,
            'unit_label_agreement': {'units_compared': total, 'same_label': agree,
                                     'candidate_stronger_than_deepseek': stronger, 'candidate_weaker_than_deepseek': weaker},
            'product_order': order, 'latency_and_cost': summary,
            'limits': ['Label agreement compares two models, not a model with gold; it shows direction only.',
                       'Two development CVs; indicative.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-dir', default=str(OUT))
    parser.add_argument('--model', default='gpt-6-luna')
    parser.add_argument('--name', default='luna_comparison_v1.json')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = build(Path(args.out_dir), args.model)
    print(json.dumps({k: result[k] for k in ('usable_pairs_of_60', 'unit_label_agreement')}, indent=1))
    for row in result['product_order']:
        print(row)
    if args.write:
        target = ROOT / 'evals/results/cp23/dev_eval_v2_20261004' / args.name
        with target.open('x') as stream:
            json.dump(result, stream, indent=2)
