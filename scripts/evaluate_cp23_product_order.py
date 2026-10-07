"""D-072/D-073 offline development evaluation on saved pipeline v1.1 outputs.

No model call. Rescores every saved CV1/CV2 top-30 pair with hold policies
H1, H2 and H2v2 and PARTIAL weights 0.25/0.5/0.75, then measures the product
order (held jobs last) against stage 1 for K = 10, 20, 30. The strict D-052
availability is reported next to every cell. Gold, sources and saved runs are
read only; the output is a new versioned file.
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
from jobfit.schemas.requirements import JDExtraction
from jobfit.scoring.hold_policy_v11 import score_with_hold_policy

OLD = ROOT / 'evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1'
NEW = ROOT / 'evals/results/cp23/pipeline_v11'
GOLD = ROOT / 'evals/gold/development_v13_reviewed_20261003_stage1_r3/relevance_gold.jsonl'
SPLIT = ROOT / 'evals/splits/dev_job_ids.txt'
OUT_DIR = ROOT / 'evals/results/cp23/dev_eval_v2_20261004'
CONTINUATION = {('CV1', 'F00022'), ('CV2', 'F00126'), ('CV1', 'F00310'), ('CV2', 'F00310')}
POLICIES = ('H1', 'H2', 'H2v2')
WEIGHTS = (0.25, 0.5, 0.75)
DEPTHS = (10, 20, 30)


def read(path: Path):
    return json.loads(path.read_text())


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def judgments(gold: Path = GOLD) -> dict[str, dict[str, int]]:
    out = {'CV1': {}, 'CV2': {}}
    for line in gold.read_text().splitlines():
        row = json.loads(line)
        if row['cv_id'] in out and row['review_status'] == 'approved':
            out[row['cv_id']][row['job_id']] = int(row['relevance_0_3'])
    return out


def load_pair(cv: str, job: str, redo: set[str]):
    """Return (extraction, assessments, saved_record) or (None, reason, saved_record)."""
    cont = (cv, job) in CONTINUATION
    pair = read(NEW / (f'pair_hold_{cv}_{job}_v11_v2.json' if cont else f'pair_{cv}_{job}_v11.json'))
    jd_path = (NEW / f'jd_hold_{job}_v11_v2.json' if cont else
               NEW / f'jd_{job}_v11.json' if job in redo else OLD / f'jd_{job}.json')
    if pair['status'] != 'done' or not jd_path.exists():
        return None, pair.get('reason') or pair.get('error_code') or pair['status'], pair
    jd = read(jd_path)
    if jd['status'] != 'done' or jd['extraction']['jd_quality'] != 'ok':
        return None, 'held_extraction', pair
    raw = (read(OLD / f'match_{cv}_{job}.json')['assessments']
           if pair['source'] == 'reused_v1_matching' else pair['assessments'])
    return ((JDExtraction.model_validate(jd['extraction']),
             [UnitAssessment.model_validate(x) for x in raw]), None, pair)


def build() -> dict:
    plan = read(NEW / 'plan_v1.json')
    redo = set(plan['redo_jds'])
    rankings = read(OLD / 'plan.json')['rankings']
    eligible = SPLIT.read_text().splitlines()
    judged = judgments()

    scores = {}      # (policy, weight, cv, job) -> ScoreResult
    receipts = {}    # (policy, cv, job) -> excluded units at weight 0.5
    loaded = {}
    for cv, ranking in rankings.items():
        if len(ranking) != 30:
            raise ValueError('Expected the saved original top-30 ranking')
        for job in ranking:
            loaded[(cv, job)] = load_pair(cv, job, redo)

    # Validity check: H1/H2 at weight 0.5 must reproduce the saved run exactly.
    mismatches = []
    for (cv, job), (inputs, reason, pair) in loaded.items():
        for policy in POLICIES:
            for weight in WEIGHTS:
                if inputs is None:
                    scores[(policy, weight, cv, job)] = held_score(reason)
                    continue
                extraction, assessments = inputs
                result, excluded = score_with_hold_policy(extraction, assessments,
                                                          policy=policy, partial_weight=weight)
                scores[(policy, weight, cv, job)] = result
                if weight == 0.5:
                    receipts[(policy, cv, job)] = excluded
        for policy in ('H1', 'H2'):
            saved = pair.get(f'score_{policy}')
            if inputs is not None and saved is not None:
                mine = scores[(policy, 0.5, cv, job)]
                if (mine.status.value, mine.score_pct) != (saved['status'], saved['score_pct']):
                    mismatches.append({'cv_id': cv, 'job_id': job, 'policy': policy,
                                       'saved': [saved['status'], saved['score_pct']],
                                       'recomputed': [mine.status.value, mine.score_pct]})
    usable = {p: sum(scores[(p, 0.5, cv, j)].status.value in ('final', 'provisional')
                     for cv, r in rankings.items() for j in r) for p in POLICIES}

    stage1 = {}
    for cv, ranking in rankings.items():
        m5 = ranking_metrics(ranking, judged[cv], eligible_ids=eligible, k=5)
        m10 = ranking_metrics(ranking, judged[cv], eligible_ids=eligible, k=10)
        stage1[cv] = {'p_at_5': m5['precision_at_k']['value'], 'ndcg_at_10': m10['ndcg_at_k']}

    cells = []
    for cv, ranking in rankings.items():
        for depth in DEPTHS:
            top = ranking[:depth]
            for policy in POLICIES:
                for weight in WEIGHTS:
                    sc = {j: scores[(policy, weight, cv, j)] for j in top}
                    m = product_order_metrics(top, sc, judged[cv], eligible_ids=eligible)
                    cells.append({'cv_id': cv, 'k': depth, 'hold_policy': policy, 'partial_weight': weight,
                                  'stage1': stage1[cv], **m})

    def macro(rows, key):
        vals = [r[key] for r in rows]
        return None if any(v is None for v in vals) or len(vals) != 2 else sum(vals) / 2

    summary = []
    for depth in DEPTHS:
        for policy in POLICIES:
            for weight in WEIGHTS:
                rows = [c for c in cells if (c['k'], c['hold_policy'], c['partial_weight']) == (depth, policy, weight)]
                summary.append({'k': depth, 'hold_policy': policy, 'partial_weight': weight,
                                'macro_p_at_5': macro(rows, 'p_at_5'),
                                'macro_ndcg_at_10': macro(rows, 'ndcg_at_10'),
                                'per_cv': {r['cv_id']: {'p_at_5': r['p_at_5'], 'ndcg_at_10': r['ndcg_at_10'],
                                                        'unscored_in_top_k': r['unscored_count']} for r in rows},
                                'strict_D052_complete_cvs': sum(r['strict_D052_complete'] for r in rows)})
    stage1_macro = {'p_at_5': sum(v['p_at_5'] for v in stage1.values()) / 2,
                    'ndcg_at_10': sum(v['ndcg_at_10'] for v in stage1.values()) / 2}

    h2v2_changes = []
    for cv, ranking in rankings.items():
        for job in ranking:
            a, b = scores[('H2', 0.5, cv, job)], scores[('H2v2', 0.5, cv, job)]
            if (a.status, a.score_pct) != (b.status, b.score_pct):
                h2v2_changes.append({'cv_id': cv, 'job_id': job, 'H2': [a.status.value, a.score_pct],
                                     'H2v2': [b.status.value, b.score_pct], 'H2v2_reason': b.reasons[-1] if b.reasons else None,
                                     'H2_excluded': [u['text'] for u in receipts.get(('H2', cv, job), [])]})
    return {
        'schema_version': 'cp23-dev-product-order-v1', 'date': '2026-10-04', 'split': 'development',
        'scope': 'CV1/CV2, saved Hybrid Qwen top-30 and saved pipeline v1.1 stage outputs',
        'api_calls': 0, 'test_used': False, 'gold_written': False,
        'protocol': 'D-073 product order (held jobs last) is primary for development final order; '
                    'strict D-052 completeness is reported per cell',
        'limits': ['Two development CV queries; results are indicative, not statistically significant.',
                   'The explicit-conflict block is empty because saved stages have no confirmed constraint context.',
                   'Relevance judgments are single-annotator, model-assisted development gold.'],
        'validity_check': {'recomputed_vs_saved_H1_H2_mismatches': mismatches,
                           'usable_pairs_weight_0_5': usable,
                           'expected_from_coverage_summary_v2': {'H1': 26, 'H2': 42}},
        'stage1': stage1, 'stage1_macro': stage1_macro,
        'summary': summary, 'h2v2_status_changes_vs_h2': h2v2_changes, 'cells': cells,
        'input_sha256': {str(p.relative_to(ROOT)): digest(p) for p in
                         (GOLD, SPLIT, NEW / 'plan_v1.json', OLD / 'plan.json', NEW / 'coverage_summary_v2.json')},
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true', help='write the versioned result file')
    args = parser.parse_args()
    result = build()
    print(json.dumps({'validity': result['validity_check'], 'stage1_macro': result['stage1_macro']}, indent=1))
    for row in result['summary']:
        print(row['k'], row['hold_policy'], row['partial_weight'], 'P@5', row['macro_p_at_5'],
              'NDCG@10', None if row['macro_ndcg_at_10'] is None else round(row['macro_ndcg_at_10'], 3),
              {cv: v['unscored_in_top_k'] for cv, v in row['per_cv'].items()})
    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with (OUT_DIR / 'product_order_v1.json').open('x') as stream:
            json.dump(result, stream, indent=2, ensure_ascii=False)
