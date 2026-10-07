"""D-078 offline grid for the freeze proposal. No model call. Development CV1/CV2 only.

Grid: matcher (Sol, Luna v2, DeepSeek v1.1) x seniority rule (off/on) x K (10/20/30)
x PARTIAL weight (0.25/0.5/0.75), hold policy H2v2, product order (D-073).
Every cell keeps its availability reason; unjudged jobs are never set to zero.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.eval.metrics import ranking_metrics
from jobfit.eval.product_order import held_score, product_order_metrics
from jobfit.schemas.analysis import UnitAssessment
from jobfit.scoring.hold_policy_v11 import score_with_hold_policy
from jobfit.search.seniority import RULE_VERSION, demote_senior
from scripts.evaluate_cp23_product_order import GOLD, NEW, OLD, OUT_DIR, SPLIT, judgments, load_pair, read
from scripts.run_cp23_luna_matching import OUT as LUNA_OUT, matchable

FEATURES = ROOT / 'data/processed/jobs_features.jsonl'
WEIGHTS, DEPTHS = (0.25, 0.5, 0.75), (10, 20, 30)


SOL_OUT = ROOT / 'evals/results/cp23/matcher_coverage_gpt-6-sol_v1'


def luna_inputs(redo, folder=LUNA_OUT, model='gpt-6-luna'):
    rows = {}
    for path in folder.glob('*__*.json'):
        row = read(path)
        if row.get('model') == model:
            rows[(row['cv_id'], row['job_id'])] = row
    if len(rows) != 60:
        raise ValueError(f'Expected 60 {model} records, found {len(rows)}')
    out = {}
    for key, row in rows.items():
        extraction = matchable(key[1], redo)
        if row['status'] != 'done' or extraction is None:
            out[key] = (None, row.get('error_code') or row['status'])
        else:
            out[key] = ((extraction, [UnitAssessment.model_validate(a) for a in row['assessments']]), None)
    return out


def build(gold: Path = GOLD):
    redo = set(read(NEW / 'plan_v1.json')['redo_jds'])
    rankings = read(OLD / 'plan.json')['rankings']
    eligible = SPLIT.read_text().splitlines()
    judged = judgments(gold)
    buckets = {json.loads(l)['final_cluster_id']: json.loads(l).get('experience_bucket')
               for l in FEATURES.read_text().splitlines()}
    sources = {'sol': luna_inputs(redo, SOL_OUT, 'gpt-6-sol'), 'luna': luna_inputs(redo),
               'deepseek': {(cv, j): load_pair(cv, j, redo)[:2] for cv, r in rankings.items() for j in r}}
    cells = []
    for matcher, inputs in sources.items():
        for rule in (False, True):
            for cv, ranking in rankings.items():
                order = demote_senior(ranking, buckets) if rule else list(ranking)
                stage1 = ranking_metrics(order, judged[cv], eligible_ids=eligible, k=10)
                stage1_p5 = ranking_metrics(order, judged[cv], eligible_ids=eligible, k=5)['precision_at_k']['value']
                kept = sum(buckets.get(j) not in ('3-4y', '5y+') for j in ranking)
                for k in DEPTHS:
                    top = order[:k]
                    for w in WEIGHTS:
                        scores = {}
                        for job in top:
                            data, reason = inputs[(cv, job)]
                            scores[job] = (held_score(reason) if data is None else
                                           score_with_hold_policy(*data, policy='H2v2', partial_weight=w)[0])
                        m = product_order_metrics(top, scores, judged[cv], eligible_ids=eligible)
                        cells.append({'matcher': matcher, 'seniority_rule': rule, 'cv_id': cv, 'k': k,
                                      'partial_weight': w, 'rule_depth': 30, 'full_ranking_equivalent': (not rule) or kept >= k,
                                      'stage1_p_at_5': stage1_p5, 'stage1_ndcg_at_10': stage1['ndcg_at_k'],
                                      'p_at_5': m['p_at_5'], 'ndcg_at_10': m['ndcg_at_10'],
                                      'unscored_in_top_k': m['unscored_count'],
                                      'unjudged_final_top10': m['unjudged_final_top10']})
    summary = []
    keys = sorted({(c['matcher'], c['seniority_rule'], c['k'], c['partial_weight']) for c in cells})
    for key in keys:
        rows = [c for c in cells if (c['matcher'], c['seniority_rule'], c['k'], c['partial_weight']) == key]
        def macro(field):
            vals = [r[field] for r in rows]
            return None if any(v is None for v in vals) else sum(vals) / len(vals)
        summary.append({'matcher': key[0], 'seniority_rule': key[1], 'k': key[2], 'partial_weight': key[3],
                        'macro_p_at_5': macro('p_at_5'), 'macro_ndcg_at_10': macro('ndcg_at_10'),
                        'macro_stage1_p_at_5': macro('stage1_p_at_5'),
                        'macro_stage1_ndcg_at_10': macro('stage1_ndcg_at_10'),
                        'full_ranking_equivalent': all(r['full_ranking_equivalent'] for r in rows),
                        'unscored_in_top_k': {r['cv_id']: r['unscored_in_top_k'] for r in rows},
                        'missing_labels': sorted({f"{r['cv_id']}/{j}" for r in rows for j in r['unjudged_final_top10']})})
    return {'schema_version': 'cp23-dev-freeze-grid-v1', 'split': 'development', 'api_calls': 0,
            'hold_policy': 'H2v2', 'order': 'D-073 product order', 'seniority_rule_version': RULE_VERSION,
            'limits': ['Two development CVs; indicative only.',
                       'D-078 defines the seniority rule on the stage-1 top 30, so every cell is exact for that definition; full_ranking_equivalent marks cells that would also match a rule over the whole ranking.',
                       'Explicit-conflict block is empty: saved stages carry no confirmed constraint context.'],
            'summary': summary, 'cells': cells,
            'input_sha256': {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
                             for p in (gold, SPLIT, FEATURES, OLD / 'plan.json', NEW / 'plan_v1.json',
                                       LUNA_OUT / 'summary_v1.json', SOL_OUT / 'summary_v1.json')}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--name', default='freeze_grid_v1.json')
    args = parser.parse_args()
    result = build()
    fmt = lambda v: '  -  ' if v is None else f'{v:.3f}'
    for r in result['summary']:
        print(f"{r['matcher']:8s} rule={int(r['seniority_rule'])} K={r['k']:2d} w={r['partial_weight']:.2f} "
              f"stage1 P5 {fmt(r['macro_stage1_p_at_5'])} N10 {fmt(r['macro_stage1_ndcg_at_10'])} | final P5 {fmt(r['macro_p_at_5'])} "
              f"N10 {fmt(r['macro_ndcg_at_10'])}  held={r['unscored_in_top_k']} missing={r['missing_labels']}")
    if args.write:
        with (OUT_DIR / args.name).open('x') as stream:
            json.dump(result, stream, indent=2)
