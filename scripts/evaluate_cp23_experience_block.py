"""Offline check of the experience conflict block (experience-upper-bound-v1). No model call.

Sol matching (saved), H2v2, PARTIAL weight 0.5, product order (D-073), with and
without the conflict block, seniority rule off/on, K 10/20. Development CV1/CV2 only.
The synthetic CVs have complete dated histories by design (T07), so history is
treated as confirmed here. In the app the user confirms it in the parsing preview.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.cv.parser import ParsedCV
from jobfit.eval.product_order import held_score, product_order_metrics
from jobfit.matching.experience_rule import RULE_VERSION, experience_conflicts
from jobfit.schemas.analysis import ConstraintState
from jobfit.scoring.hold_policy_v11 import score_with_hold_policy
from jobfit.search.seniority import demote_senior
from scripts.evaluate_cp23_freeze_grid import FEATURES, SOL_OUT, luna_inputs
from scripts.evaluate_cp23_product_order import GOLD, NEW, OLD, OUT_DIR, SPLIT, read
from scripts.run_cp23_luna_matching import matchable


def judged(gold: Path) -> dict[str, dict[str, int]]:
    out = {'CV1': {}, 'CV2': {}}
    for line in gold.read_text().splitlines():
        row = json.loads(line)
        if row['cv_id'] in out and row.get('review_status') == 'approved':
            out[row['cv_id']][row['job_id']] = int(row['relevance_0_3'])
    return out


def build(gold: Path = GOLD) -> dict:
    redo = set(read(NEW / 'plan_v1.json')['redo_jds'])
    rankings = read(OLD / 'plan.json')['rankings']
    eligible = SPLIT.read_text().splitlines()
    labels = judged(gold)
    buckets = {json.loads(l)['final_cluster_id']: json.loads(l).get('experience_bucket')
               for l in FEATURES.read_text().splitlines()}
    sol = luna_inputs(redo, SOL_OUT, 'gpt-6-sol')
    cvs = {cv: ParsedCV.model_validate(read(OLD / f'{cv}_parse.json')['parsed']) for cv in rankings}
    conflicts, flagged = {}, []
    for cv, ranking in rankings.items():
        for job in ranking:
            ext = matchable(job, redo)
            found = experience_conflicts(ext, cvs[cv], history_confirmed=True) if ext else []
            conflicts[(cv, job)] = found
            if any(c.state == ConstraintState.EXPLICIT_CONFLICT for c in found):
                flagged.append({'cv_id': cv, 'job_id': job, 'relevance': labels[cv].get(job),
                                'bucket': buckets.get(job),
                                'scored': sol[(cv, job)][0] is not None,
                                'messages': [c.message for c in found if c.state == ConstraintState.EXPLICIT_CONFLICT]})
    cells = []
    for rule in (False, True):
        for k in (10, 20):
            for block in (False, True):
                for cv, ranking in rankings.items():
                    top = (demote_senior(ranking, buckets) if rule else list(ranking))[:k]
                    scores = {j: held_score(sol[(cv, j)][1]) if sol[(cv, j)][0] is None else
                              score_with_hold_policy(*sol[(cv, j)][0], policy='H2v2', partial_weight=0.5)[0]
                              for j in top}
                    cons = {j: conflicts[(cv, j)] for j in top} if block else None
                    m = product_order_metrics(top, scores, labels[cv], eligible_ids=eligible, constraints=cons)
                    cells.append({'seniority_rule': rule, 'k': k, 'conflict_block': block, 'cv_id': cv,
                                  'p_at_5': m['p_at_5'], 'ndcg_at_10': m['ndcg_at_10'],
                                  'final_top5': m['order'][:5], 'unjudged_final_top10': m['unjudged_final_top10']})
    return {'schema_version': 'cp23-dev-experience-block-v1', 'rule': RULE_VERSION, 'split': 'development',
            'api_calls': 0, 'matcher': 'gpt-6-sol', 'hold_policy': 'H2v2', 'partial_weight': 0.5,
            'cv_total_years': {cv: None for cv in cvs},
            'flagged_pairs': flagged, 'cells': cells,
            'limits': ['Two CVs. CV2 has about 5.4 years of total (mostly marketing) history, so the upper-bound rule cannot flag it; only CV1 can change.',
                       'Guideline Part D rates an explicit experience conflict as 1, so the block and the labels share the same idea (circularity, as with the seniority rule).',
                       'Missing labels are never zero; cells with unjudged top-10 jobs are provisional until gold r4.'],
            'input_sha256': {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
                             for p in (gold, SPLIT, FEATURES, OLD / 'plan.json', SOL_OUT / 'summary_v1.json')}}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--gold', type=Path, default=GOLD)
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--name', default='experience_block_v1.json')
    args = ap.parse_args()
    res = build(args.gold)
    print('flagged:', [(f['cv_id'], f['job_id'], f['relevance'], f['bucket'], f['scored']) for f in res['flagged_pairs']])
    fmt = lambda v: '  -  ' if v is None else f'{v:.3f}'
    for rule in (False, True):
        for k in (10, 20):
            for block in (False, True):
                rows = [c for c in res['cells'] if (c['seniority_rule'], c['k'], c['conflict_block']) == (rule, k, block)]
                print(f"rule={int(rule)} K={k} block={int(block)} " + ' '.join(
                    f"{r['cv_id']} P5 {fmt(r['p_at_5'])} N10 {fmt(r['ndcg_at_10'])} miss={len(r['unjudged_final_top10'])}" for r in rows))
    if args.write:
        with (OUT_DIR / args.name).open('x') as f:
            json.dump(res, f, indent=2)
