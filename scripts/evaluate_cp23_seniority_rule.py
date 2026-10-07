"""D-074 offline development check of the stage-1 seniority rule. No model call.

Uses the saved top-30 rankings (six methods x CV1/CV2), CP1 experience buckets,
development relevance gold and saved pipeline v1.1 outputs. The rule is applied
inside the saved top-30 depth; a cell is marked `exact` only when at least K
non-demoted jobs exist in that depth, so the top K equals the rule applied to the
full ranking.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.eval.metrics import ranking_metrics
from jobfit.eval.product_order import held_score, product_order_metrics
from jobfit.scoring.hold_policy_v11 import score_with_hold_policy
from jobfit.search.seniority import DEMOTED_BUCKETS, RULE_VERSION, demote_senior
from scripts.evaluate_cp23_product_order import GOLD, NEW, OLD, OUT_DIR, SPLIT, judgments, load_pair, read

RETRIEVAL = ROOT / 'evals/results/cp22_retrieval_top30_20261002_03.json'
FEATURES = ROOT / 'data/processed/jobs_features.jsonl'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def metrics(ranking, judged, eligible):
    out = {}
    for k in (5, 10, 20):
        m = ranking_metrics(ranking, judged, eligible_ids=eligible, k=k)
        out[k] = m
    return {'p_at_5': out[5]['precision_at_k']['value'], 'ndcg_at_10': out[10]['ndcg_at_k'],
            'recall_at_10': out[10]['recall_at_k']['value'], 'recall_at_20': out[20]['recall_at_k']['value'],
            'unjudged_top10': out[10]['coverage']['unjudged_original_top_k_ids']}


def build():
    buckets = {}
    for line in FEATURES.read_text().splitlines():
        row = json.loads(line)
        buckets[row['final_cluster_id']] = row.get('experience_bucket')
    eligible = SPLIT.read_text().splitlines()
    judged = judgments()
    runs = read(RETRIEVAL)['runs']

    evidence = {cv: {f'{b}|{r}': n for (b, r), n in sorted(Counter(
        (buckets.get(j) or 'missing', 'relevant' if v >= 2 else 'not_relevant')
        for j, v in judged[cv].items()).items())} for cv in judged}
    retrieval = []
    for run in runs:
        cv, ranking = run['cv_id'], run['ranking']
        demoted = demote_senior(ranking, buckets)
        kept = sum(buckets.get(j) not in DEMOTED_BUCKETS for j in ranking)
        retrieval.append({'cv_id': cv, 'method': run['method'], 'non_demoted_in_top30': kept,
                          'exact_for_k10': kept >= 10, 'exact_for_k20': kept >= 20,
                          'original': metrics(ranking, judged[cv], eligible),
                          'with_rule': metrics(demoted, judged[cv], eligible)})

    plan = read(NEW / 'plan_v1.json')
    redo = set(plan['redo_jds'])
    rankings = read(OLD / 'plan.json')['rankings']
    final = []
    for cv, ranking in rankings.items():
        demoted = demote_senior(ranking, buckets)
        kept = sum(buckets.get(j) not in DEMOTED_BUCKETS for j in ranking)
        for k in (10, 20):
            for use_rule in (False, True):
                top = (demoted if use_rule else ranking)[:k]
                stage1 = metrics(demoted if use_rule else ranking, judged[cv], eligible)
                for policy in ('H2', 'H2v2'):
                    sc = {}
                    for job in top:
                        inputs, reason, _ = load_pair(cv, job, redo)
                        if inputs is None:
                            sc[job] = held_score(reason)
                        else:
                            sc[job] = score_with_hold_policy(*inputs, policy=policy, partial_weight=0.5)[0]
                    m = product_order_metrics(top, sc, judged[cv], eligible_ids=eligible)
                    final.append({'cv_id': cv, 'k': k, 'seniority_rule': use_rule, 'hold_policy': policy,
                                  'partial_weight': 0.5, 'exact': (not use_rule) or kept >= k,
                                  'stage1_p_at_5': stage1['p_at_5'], 'stage1_ndcg_at_10': stage1['ndcg_at_10'],
                                  'final_p_at_5': m['p_at_5'], 'final_ndcg_at_10': m['ndcg_at_10'],
                                  'unscored_in_top_k': m['unscored_count'],
                                  'unjudged_final_top10': m['unjudged_final_top10'], 'order': m['order']})
    return {'schema_version': 'cp23-dev-seniority-rule-v1', 'date': '2026-10-04', 'split': 'development',
            'rule_version': RULE_VERSION, 'demoted_buckets': sorted(DEMOTED_BUCKETS),
            'api_calls': 0, 'test_used': False, 'gold_written': False,
            'limits': ['Two development CV queries; indicative only.',
                       'experience_bucket is the CP1 v0 regex feature; 414 of 910 clusters are not_stated.',
                       'Rule chosen after looking at development labels; it must be frozen before any test use.'],
            'bucket_by_relevance_in_judged_pool': evidence,
            'retrieval': retrieval, 'final_order': final,
            'input_sha256': {str(p.relative_to(ROOT)): digest(p) for p in (RETRIEVAL, FEATURES, GOLD, SPLIT)}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = build()
    print(json.dumps(result['bucket_by_relevance_in_judged_pool']))
    for r in result['retrieval']:
        o, w = r['original'], r['with_rule']
        print(f"{r['cv_id']} {r['method']:14s} P5 {o['p_at_5']}->{w['p_at_5']}  NDCG {o['ndcg_at_10'] and round(o['ndcg_at_10'],3)}->{w['ndcg_at_10'] and round(w['ndcg_at_10'],3)}  R20 {o['recall_at_20'] and round(o['recall_at_20'],3)}->{w['recall_at_20'] and round(w['recall_at_20'],3)} exactK20={r['exact_for_k20']} unj={w['unjudged_top10']}")
    for f in result['final_order']:
        print(f['cv_id'], 'K', f['k'], 'rule', f['seniority_rule'], f['hold_policy'], 'stage1', f['stage1_p_at_5'], f['stage1_ndcg_at_10'] and round(f['stage1_ndcg_at_10'],3),
              'final', f['final_p_at_5'], f['final_ndcg_at_10'] and round(f['final_ndcg_at_10'],3), 'exact', f['exact'], 'unj', f['unjudged_final_top10'])
    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with (OUT_DIR / 'seniority_rule_v1.json').open('x') as stream:
            json.dump(result, stream, indent=2, ensure_ascii=False)
