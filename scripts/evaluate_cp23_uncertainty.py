"""D-075 uncertainty and pool-bias report for the CP2.3 development comparisons.

No model call. Fulfils the D-045 promise of bootstrap intervals.
1. Matching: paired bootstrap (units, and whole CV/JD pairs) of the Macro-F1
   difference between candidates, on the exact predictions used by the D-067
   comparison, for the old/new reference and with/without G1/G2.
2. Matching error profile: MATCH overclaims and underclaims per model.
3. Retrieval: per-CV counts, unjudged jobs in each saved top-30 (pool bias),
   and the Indonesian (CV1) versus English (CV2) gap (H7).
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

import scripts.evaluate_cp23_sql_reference_v2 as reference_eval

GOLD = ROOT / 'evals/gold/development_v13_reviewed_20261003_stage1_r3/relevance_gold.jsonl'
RETRIEVAL = ROOT / 'evals/results/cp22_retrieval_top30_20261002_03.json'
OUT_DIR = ROOT / 'evals/results/cp23/dev_eval_v2_20261004'
CLASSES = ('MATCH', 'PARTIAL', 'NO_MATCH')
SEED, DRAWS = 20261004, 5000


def macro_f1(keys, truth, pred):
    tp = dict.fromkeys(CLASSES, 0); fp = dict.fromkeys(CLASSES, 0); fn = dict.fromkeys(CLASSES, 0)
    for k in keys:
        g, p = truth[k], (pred.get(k) or {}).get('label')
        if p == g:
            tp[g] += 1
        else:
            fn[g] += 1
            if p in CLASSES:
                fp[p] += 1
    return sum((2 * tp[c] / d) if (d := 2 * tp[c] + fp[c] + fn[c]) else 0.0 for c in CLASSES) / 3


def capture_predictions():
    """Re-run the D-067 evaluation offline and capture its exact inputs."""
    calls = []
    original = reference_eval.evidence_metrics

    def spy(labels, predictions, **kwargs):
        calls.append((dict(labels), {k: dict(v) for k, v in predictions.items()}))
        return original(labels, predictions, **kwargs)

    reference_eval.evidence_metrics = spy
    try:
        report = reference_eval.build()
    finally:
        reference_eval.evidence_metrics = original
    store, index = {}, 0
    for scope, models in report['results'].items():
        for model in models:  # same iteration order as build()
            for ref in ('old', 'new'):
                for view in ('all_cases', 'answered_cases_only', 'all_cases_guarded', 'answered_cases_only_guarded'):
                    if models[model][ref][view] is None:
                        continue
                    store[(scope, model, ref, view)] = calls[index]
                    index += 1
    if index != len(calls):
        raise ValueError('Captured prediction count does not match the evaluation')
    for (scope, model, ref, view), (truth, pred) in store.items():
        expected = report['results'][scope][model][ref][view]['macro_f1']
        if view.startswith('all') and abs(macro_f1(sorted(truth), truth, pred) - expected) > 1e-9:
            raise ValueError(f'Macro-F1 replication failed for {scope}/{model}/{ref}/{view}')
    return store


def paired_bootstrap(truth, pa, pb, rng):
    keys = sorted(truth)
    pairs = sorted({k.rsplit('/', 1)[0] for k in keys})
    by_pair = {p: [k for k in keys if k.startswith(p + '/')] for p in pairs}
    observed = macro_f1(keys, truth, pa) - macro_f1(keys, truth, pb)
    unit, cluster = [], []
    for _ in range(DRAWS):
        sample = [rng.choice(keys) for _ in keys]
        unit.append(macro_f1(sample, truth, pa) - macro_f1(sample, truth, pb))
        sample = [k for p in (rng.choice(pairs) for _ in pairs) for k in by_pair[p]]
        cluster.append(macro_f1(sample, truth, pa) - macro_f1(sample, truth, pb))
    unit.sort(); cluster.sort()
    lo, hi = int(0.025 * DRAWS), int(0.975 * DRAWS) - 1
    return {'units': len(keys), 'pairs': len(pairs), 'observed_difference': observed,
            'unit_bootstrap_95': [unit[lo], unit[hi]],
            'pair_bootstrap_95': [cluster[lo], cluster[hi]],
            'share_of_unit_draws_below_0_03': sum(d < 0.03 for d in unit) / DRAWS}


def error_profile(truth, pred):
    labels = {k: (pred.get(k) or {}).get('label') for k in truth}
    predicted_match = sum(v == 'MATCH' for v in labels.values())
    over = sum(labels[k] == 'MATCH' and truth[k] != 'MATCH' for k in truth)
    over_any = sum(labels[k] in ('MATCH', 'PARTIAL') and truth[k] == 'NO_MATCH' for k in truth)
    under = sum(truth[k] == 'MATCH' and labels[k] in ('PARTIAL', 'NO_MATCH') for k in truth)
    rank = {'NO_MATCH': 0, 'PARTIAL': 1, 'MATCH': 2}
    stronger = sum(labels[k] in rank and rank[labels[k]] > rank[truth[k]] for k in truth)
    weaker = sum(labels[k] in rank and rank[labels[k]] < rank[truth[k]] for k in truth)
    return {'claims_stronger_than_gold': stronger, 'claims_weaker_than_gold': weaker,
            'predicted_match': predicted_match, 'match_overclaim': over,
            'positive_claim_on_gold_no_match': over_any, 'match_underclaim': under,
            'match_precision': (predicted_match - over) / predicted_match if predicted_match else None,
            'not_assessed': sum(v is None for v in labels.values())}


def retrieval_report():
    judged = {}
    for line in GOLD.read_text().splitlines():
        row = json.loads(line)
        if row['review_status'] == 'approved':
            judged[(row['cv_id'], row['job_id'])] = int(row['relevance_0_3'])
    relevant = {cv: {j for (c, j), v in judged.items() if c == cv and v >= 2} for cv in ('CV1', 'CV2')}
    rows = []
    for run in json.loads(RETRIEVAL.read_text())['runs']:
        cv, ranking = run['cv_id'], run['ranking']
        found = {k: len(relevant[cv] & set(ranking[:k])) for k in (10, 20, 30)}
        rows.append({'cv_id': cv, 'method': run['method'], 'relevant_in_pool': len(relevant[cv]),
                     'found_at_k': found,
                     'unjudged_in_top': {k: sum((cv, j) not in judged for j in ranking[:k]) for k in (10, 20, 30)},
                     'relevant_ranks': [i + 1 for i, j in enumerate(ranking) if j in relevant[cv]]})
    h7 = {}
    for method in sorted({r['method'] for r in rows}):
        a = next(r for r in rows if r['method'] == method and r['cv_id'] == 'CV1')
        b = next(r for r in rows if r['method'] == method and r['cv_id'] == 'CV2')
        h7[method] = {'CV1_indonesian_recall20': a['found_at_k'][20] / a['relevant_in_pool'],
                      'CV2_english_recall20': b['found_at_k'][20] / b['relevant_in_pool']}
    return rows, h7


def build():
    rng = random.Random(SEED)
    store = capture_predictions()
    comparisons = []
    for ref in ('old', 'new'):
        for view in ('all_cases', 'all_cases_guarded'):
            truth, ds = store[('round_one_B', 'deepseek-flash', ref, view)]
            _, luna = store[('round_one_B', 'gpt-6-luna', ref, view)]
            comparisons.append({'a': 'deepseek-flash', 'b': 'gpt-6-luna', 'reference': ref, 'view': view,
                                **paired_bootstrap(truth, ds, luna, rng)})
    truth, sol = store[('reference_round_two', 'gpt-6-sol', 'new', 'all_cases_guarded')]
    _, ds = store[('round_one_B', 'deepseek-flash', 'new', 'all_cases_guarded')]
    if set(truth) == set(store[('round_one_B', 'deepseek-flash', 'new', 'all_cases_guarded')][0]):
        comparisons.append({'a': 'gpt-6-sol', 'b': 'deepseek-flash', 'reference': 'new', 'view': 'all_cases_guarded',
                            **paired_bootstrap(truth, sol, ds, rng)})
    profiles = {f'{scope}/{model}': error_profile(*store[(scope, model, 'new', 'all_cases_guarded')])
                for (scope, model, ref, view) in store if ref == 'new' and view == 'all_cases_guarded'}
    rows, h7 = retrieval_report()
    return {'schema_version': 'cp23-dev-uncertainty-v1', 'date': '2026-10-04', 'split': 'development',
            'api_calls': 0, 'seed': SEED, 'draws': DRAWS, 'test_used': False, 'gold_written': False,
            'matching_bootstrap': comparisons, 'matching_error_profile_new_reference_guarded': profiles,
            'retrieval_per_cv': rows, 'h7_indonesian_vs_english_recall20': h7,
            'interpretation_limits': ['73 units in 4 CV/JD pairs; two retrieval CV queries.',
                                      'A pair bootstrap with four pairs is coarse; both intervals are reported.',
                                      'Unjudged jobs count as not found in labeled-pool recall, which favours methods '
                                      'whose deeper ranks overlap the pooled top-10 lists.'],
            'input_sha256': {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
                             for p in (GOLD, RETRIEVAL, reference_eval.VALIDATED, reference_eval.REFERENCE)}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = build()
    for c in result['matching_bootstrap']:
        print(c['a'], 'vs', c['b'], c['reference'], c['view'], round(c['observed_difference'], 3),
              [round(x, 3) for x in c['unit_bootstrap_95']], [round(x, 3) for x in c['pair_bootstrap_95']],
              round(c['share_of_unit_draws_below_0_03'], 2))
    for k, v in result['matching_error_profile_new_reference_guarded'].items():
        print(k, v)
    for k, v in result['h7_indonesian_vs_english_recall20'].items():
        print('H7', k, {a: round(b, 3) for a, b in v.items()})
    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with (OUT_DIR / 'uncertainty_v1.json').open('x') as stream:
            json.dump(result, stream, indent=2)
