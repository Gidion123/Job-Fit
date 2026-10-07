"""Offline P7 report (development CV1/CV2 only, no model call).

1. H7 language view: per CV (CV1 Indonesian, CV2 English) and per retrieval method,
   P@5, NDCG@10 and labeled-pool recall@10/20/30; plus recall split by JD language.
2. Per-CV intervals for precision (Wilson 95%, k trials). One CV is one query,
   so this shows how wide a single-query precision is, not a population estimate.
3. Hard negatives: judged 0/1 jobs inside the stage-1 top 10 (Hybrid Qwen) and the
   final top 10 (Sol, H2v2, w 0.5, seniority rule on), with simple CP1 attributes.
Missing labels are never zero; a value with an unjudged position is None.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.eval.metrics import ranking_metrics
from jobfit.eval.product_order import held_score, product_order_ids
from jobfit.scoring.hold_policy_v11 import score_with_hold_policy
from jobfit.search.seniority import demote_senior
from scripts.evaluate_cp23_experience_block import judged
from scripts.evaluate_cp23_freeze_grid import FEATURES, SOL_OUT, luna_inputs
from scripts.evaluate_cp23_product_order import GOLD, NEW, OLD, OUT_DIR, SPLIT, read

RETRIEVAL = ROOT / 'evals/results/cp22_retrieval_top30_20261002_03.json'
CV_LANGUAGE = {'CV1': 'id', 'CV2': 'en'}


def wilson(hits: int, n: int, z: float = 1.96) -> list[float] | None:
    if n == 0:
        return None
    p = hits / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3)]


def precision_block(ranking, labels, k):
    top = ranking[:k]
    if any(j not in labels for j in top):
        return {'k': k, 'value': None, 'wilson_95': None, 'unjudged': [j for j in top if j not in labels]}
    hits = sum(labels[j] >= 2 for j in top)
    return {'k': k, 'value': hits / k, 'hits': hits, 'wilson_95': wilson(hits, k), 'unjudged': []}


def build(gold: Path = GOLD) -> dict:
    labels = judged(gold)
    eligible = SPLIT.read_text().splitlines()
    feats = {json.loads(l)['final_cluster_id']: json.loads(l) for l in FEATURES.read_text().splitlines()}
    runs = read(RETRIEVAL)['runs']
    language = []
    for r in runs:
        cv, ranking = r['cv_id'], r['ranking']
        m5 = ranking_metrics(ranking, labels[cv], eligible_ids=eligible, k=5)
        m10 = ranking_metrics(ranking, labels[cv], eligible_ids=eligible, k=10)
        rec = {k: ranking_metrics(ranking, labels[cv], eligible_ids=eligible, k=k)['recall_at_k'] for k in (10, 20, 30)}
        by_lang = {}
        relevant = [j for j, v in labels[cv].items() if v >= 2]
        for lang in ('id', 'en'):
            rel = [j for j in relevant if feats[j]['jd_language'] == lang]
            by_lang[lang] = {'relevant': len(rel), 'found_top20': sum(j in ranking[:20] for j in rel)}
        language.append({'cv_id': cv, 'cv_language': CV_LANGUAGE[cv], 'method': r['method'],
                         'p_at_5': m5['precision_at_k']['value'], 'ndcg_at_10': m10['ndcg_at_k'],
                         'recall': {k: {'value': v['value'], 'numerator': v.get('numerator'),
                                        'denominator': v.get('denominator')} for k, v in rec.items()},
                         'relevant_found_by_jd_language_top20': by_lang,
                         'precision_intervals': [precision_block(ranking, labels[cv], 5),
                                                 precision_block(ranking, labels[cv], 10)]})
    # Final order (Sol) for hard negatives
    redo = set(read(NEW / 'plan_v1.json')['redo_jds'])
    rankings = read(OLD / 'plan.json')['rankings']
    buckets = {j: f.get('experience_bucket') for j, f in feats.items()}
    sol = luna_inputs(redo, SOL_OUT, 'gpt-6-sol')
    hard, finals = [], {}
    for cv, ranking in rankings.items():
        top = demote_senior(ranking, buckets)[:10]
        scores = {j: held_score(sol[(cv, j)][1]) if sol[(cv, j)][0] is None else
                  score_with_hold_policy(*sol[(cv, j)][0], policy='H2v2', partial_weight=0.5)[0] for j in top}
        final = product_order_ids(top, scores)
        finals[cv] = final
        for where, ids in (('stage1_top10', ranking[:10]), ('final_top10', final)):
            for pos, j in enumerate(ids, 1):
                if labels[cv].get(j) in (0, 1):
                    f = feats[j]
                    hard.append({'cv_id': cv, 'list': where, 'position': pos, 'job_id': j,
                                 'relevance': labels[cv][j], 'title': f['title'],
                                 'role_family': f['role_family'], 'experience_bucket': f['experience_bucket'],
                                 'jd_language': f['jd_language'], 'country': f.get('country_code'),
                                 'score_pct': scores[j].score_pct if j in scores else None,
                                 'score_status': scores[j].status.value if j in scores else None})
    summary = {f'{cv}/{w}': dict(Counter(h['experience_bucket'] for h in hard if h['cv_id'] == cv and h['list'] == w))
               for cv in rankings for w in ('stage1_top10', 'final_top10')}
    return {'schema_version': 'cp23-dev-p7-v1', 'split': 'development', 'api_calls': 0,
            'gold': str(gold.relative_to(ROOT)), 'language_view': language,
            'hard_negatives': hard, 'hard_negative_buckets': summary, 'final_top10': finals,
            'limits': ['Two CVs: one Indonesian, one English, and they also differ in profile, so a gap cannot be blamed on language alone.',
                       'Wilson intervals treat the k positions as independent trials; with one query this only shows how wide the number is.',
                       'Labels come from a pool built from these methods (pool bias, D-075).'],
            'input_sha256': {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
                             for p in (gold, SPLIT, FEATURES, RETRIEVAL, SOL_OUT / 'summary_v1.json')}}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--gold', type=Path, default=GOLD)
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--name', default='p7_report_r3_v1.json')
    args = ap.parse_args()
    res = build(args.gold)
    f = lambda v: '  -  ' if v is None else f'{v:.2f}'
    for r in res['language_view']:
        rec = r['recall']
        print(f"{r['cv_id']}({r['cv_language']}) {r['method']:14s} P5 {f(r['p_at_5'])} N10 {f(r['ndcg_at_10'])} "
              f"R10 {f(rec[10]['value'])} R20 {f(rec[20]['value'])} R30 {f(rec[30]['value'])} "
              f"P5 CI {r['precision_intervals'][0]['wilson_95']} lang {r['relevant_found_by_jd_language_top20']}")
    print('hard negative buckets:', res['hard_negative_buckets'])
    for h in res['hard_negatives']:
        if h['list'] == 'final_top10':
            print('final', h['cv_id'], h['position'], h['job_id'], h['relevance'], h['experience_bucket'], h['role_family'], h['title'][:50], h['score_pct'])
    if args.write:
        with (OUT_DIR / args.name).open('x') as fh:
            json.dump(res, fh, indent=2)
