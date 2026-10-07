"""One command after Dion imports the 46 gap labels (gold r4). No model call.

Order:
1. check gold r4 exists and its manifest hashes match (the import itself stays Dion's step);
2. freeze grid with Sol scores on r4, then the D-078 rule (src/jobfit/eval/d078.py);
3. stage-1 retriever comparison on complete top-20 judgments: six methods, each with
   and without the seniority rule, plus an offline Hybrid Qwen + B0 fusion (RRF k=60);
   the PROPOSED retriever rule below is evaluated but decides nothing until approved;
4. experience conflict block and P7 report on r4.
Prints one summary. `--write` saves it in a new versioned folder.
Any cell with a missing label is reported unavailable, never zero.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.eval.d078 import choose
from jobfit.eval.metrics import ranking_metrics
from jobfit.search.hybrid import rrf
from jobfit.search.seniority import demote_senior

R4 = ROOT / 'evals/gold/development_v13_reviewed_20261004_gap_r4'
RETRIEVAL = ROOT / 'evals/results/cp22_retrieval_top30_20261002_03.json'
OUT_ROOT = ROOT / 'evals/results/cp23'
CURRENT = 'hybrid_qwen'
# D-084 (approved 6 Oct 2026 before any r4 number existed).
PROPOSED_RETRIEVER_RULE = {
    'status': 'approved_D-084',
    'rule': ('Keep Hybrid Qwen unless a challenger has macro NDCG@10 at least 0.05 higher AND macro P@5 '
             'not lower, both with the seniority rule on and complete judgments on both CVs. A switch is a '
             'new development iteration: the new top 30 needs new Sol matching before the freeze.'),
    'margin_ndcg': 0.05,
}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def check_gold(gold: Path) -> dict:
    manifest = json.loads((gold / 'manifest.json').read_text())
    bad = [n for n, h in manifest.get('files', {}).items() if n != 'manifest.json' and digest(gold / n) != h]
    if bad:
        raise SystemExit(f'Gold bundle files changed since import: {bad}')
    return {'bundle': gold.name, 'relevance_rows': manifest.get('relevance_rows'), 'manifest_sha256': digest(gold / 'manifest.json')}


def judged(gold_file: Path) -> dict[str, dict[str, int]]:
    out = {'CV1': {}, 'CV2': {}}
    for line in gold_file.read_text().splitlines():
        row = json.loads(line)
        if row['cv_id'] in out and row.get('review_status') == 'approved':
            out[row['cv_id']][row['job_id']] = int(row['relevance_0_3'])
    return out


def retriever_comparison(labels, eligible, buckets) -> dict:
    runs = json.loads(RETRIEVAL.read_text())['runs']
    rankings = {(r['cv_id'], r['method']): list(r['ranking']) for r in runs}
    for cv in ('CV1', 'CV2'):
        fused = rrf([[{'job_id': j} for j in rankings[(cv, CURRENT)]], [{'job_id': j} for j in rankings[(cv, 'B0')]]],
                    k=60, top_k=30)
        rankings[(cv, 'fusion_hybrid_qwen_B0')] = [r['job_id'] for r in fused]
    methods = sorted({m for _, m in rankings})
    rows = []
    for method in methods:
        for rule in (False, True):
            per_cv = {}
            for cv in ('CV1', 'CV2'):
                order = rankings[(cv, method)]
                order = demote_senior(order, buckets) if rule else order
                m5 = ranking_metrics(order, labels[cv], eligible_ids=eligible, k=5)
                m10 = ranking_metrics(order, labels[cv], eligible_ids=eligible, k=10)
                m20 = ranking_metrics(order, labels[cv], eligible_ids=eligible, k=20)
                per_cv[cv] = {'p_at_5': m5['precision_at_k']['value'], 'ndcg_at_10': m10['ndcg_at_k'],
                              'recall_at_20': m20['recall_at_k']['value'] if not m20['coverage']['unjudged_original_top_k_ids'] else None,
                              'unjudged_top20': m20['coverage']['unjudged_original_top_k_ids']}
            macro = lambda f: (None if any(v[f] is None for v in per_cv.values())
                               else sum(v[f] for v in per_cv.values()) / 2)
            rows.append({'method': method, 'seniority_rule': rule, 'per_cv': per_cv,
                         'macro_p_at_5': macro('p_at_5'), 'macro_ndcg_at_10': macro('ndcg_at_10'),
                         'macro_recall_at_20': macro('recall_at_20')})
    base = next(r for r in rows if r['method'] == CURRENT and r['seniority_rule'])
    verdicts = []
    for r in rows:
        if not r['seniority_rule'] or r['method'] == CURRENT:
            continue
        if None in (r['macro_ndcg_at_10'], r['macro_p_at_5'], base['macro_ndcg_at_10'], base['macro_p_at_5']):
            verdicts.append({'challenger': r['method'], 'result': 'unavailable (missing labels)'})
            continue
        wins = (r['macro_ndcg_at_10'] >= base['macro_ndcg_at_10'] + PROPOSED_RETRIEVER_RULE['margin_ndcg'] - 1e-9
                and r['macro_p_at_5'] >= base['macro_p_at_5'] - 1e-9)
        verdicts.append({'challenger': r['method'], 'result': 'beats current' if wins else 'does not beat current',
                         'ndcg_diff': round(r['macro_ndcg_at_10'] - base['macro_ndcg_at_10'], 3),
                         'p5_diff': round(r['macro_p_at_5'] - base['macro_p_at_5'], 3)})
    return {'rows': rows, 'proposed_rule': PROPOSED_RETRIEVER_RULE, 'proposed_rule_verdicts': verdicts}


def build(gold: Path) -> dict:
    from scripts import evaluate_cp23_experience_block as exp
    from scripts import evaluate_cp23_freeze_grid as grid
    from scripts import evaluate_cp23_p7 as p7
    gold_file = gold / 'relevance_gold.jsonl'
    labels = judged(gold_file)
    eligible = (ROOT / 'evals/splits/dev_job_ids.txt').read_text().splitlines()
    feats = {json.loads(l)['final_cluster_id']: json.loads(l) for l in grid.FEATURES.read_text().splitlines()}
    buckets = {j: f.get('experience_bucket') for j, f in feats.items()}
    g = grid.build(gold_file)
    sol = [r for r in g['summary'] if r['matcher'] == 'sol']
    decision = choose(sol)
    block = exp.build(gold_file)
    k = decision.get('k', 20)
    rule = decision.get('seniority_rule', True)
    block_cells = [c for c in block['cells'] if c['k'] == k and c['seniority_rule'] == rule]
    return {'schema_version': 'cp23-post-labeling-v1', 'api_calls': 0, 'gold': check_gold(gold) if (gold / 'manifest.json').exists() else {'bundle': gold.name},
            'd078_decision': decision,
            'freeze_grid_sol': sol,
            'retriever_comparison': retriever_comparison(labels, eligible, buckets),
            'experience_block_at_choice': block_cells,
            'experience_block_flagged': block['flagged_pairs'],
            'p7': p7.build(gold_file),
            'next_steps': ['Dion decides: D-078 result, the proposed retriever rule, the experience block.',
                           'Write config v4 with the chosen K/weight (new file, v3 unchanged).',
                           'Rebuild the saved demo bundle for v4 (scripts/build_demo_bundle.py).',
                           'Draft the freeze receipt: scripts/prepare_cp23_freeze.py --config <v4> --write.']}


def show(res: dict) -> None:
    f = lambda v: '  -  ' if v is None else f'{v:.3f}'
    d = res['d078_decision']
    print('D-078:', json.dumps({k: v for k, v in d.items() if k != 'trace'}))
    for t in d['trace']:
        print('   ', t)
    print('\nRetriever (stage 1, top-20 judgments):')
    for r in res['retriever_comparison']['rows']:
        miss = sum(len(v['unjudged_top20']) for v in r['per_cv'].values())
        print(f"  {r['method']:22s} rule={int(r['seniority_rule'])} P5 {f(r['macro_p_at_5'])} "
              f"N10 {f(r['macro_ndcg_at_10'])} R20 {f(r['macro_recall_at_20'])} unjudged_top20={miss}")
    print('  D-084 rule verdicts:', res['retriever_comparison']['proposed_rule_verdicts'])
    print('\nExperience block at the chosen cell:')
    for c in res['experience_block_at_choice']:
        print(f"  {c['cv_id']} block={int(c['conflict_block'])} P5 {f(c['p_at_5'])} N10 {f(c['ndcg_at_10'])}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--gold', type=Path, default=R4, help='gold bundle folder (default: r4)')
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args(argv)
    args.gold = (ROOT / args.gold).resolve() if not args.gold.is_absolute() else args.gold
    if not (args.gold / 'relevance_gold.jsonl').exists():
        raise SystemExit(f'{args.gold.name} not found. Run the import first: scripts/import_dev_relevance_gap.py --write')
    res = build(args.gold)
    show(res)
    if args.write:
        n = 1
        while (OUT_ROOT / f'post_labeling_{args.gold.name}_v{n}').exists():
            n += 1
        folder = OUT_ROOT / f'post_labeling_{args.gold.name}_v{n}'
        folder.mkdir(parents=True)
        (folder / 'summary.json').write_text(json.dumps(res, indent=1, ensure_ascii=False) + '\n')
        print('wrote', folder.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
