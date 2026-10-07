"""CP2.4 supplementary descriptive metrics from the saved test run (no model call, no tuning).

Covers master-plan CP2.4 steps 4-6 that the frozen headline report does not: labeled-pool recall,
safety (hard negatives and low-relevance jobs in the top positions, quote validity), process status
(holds, fallbacks, failures) and cost/latency. The headline contract (cp24-report-contract-v1) and the
CP2.4 files are only read. CP2.4 stays locked from optimization (D-089): nothing here chooses anything.
Output: evals/results/cp24/supplementary_v2/ (written once).
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.eval.heldout_report import PRIMARY, SUPPLEMENTARY  # noqa: E402
from jobfit.eval.metrics import ranking_metrics  # noqa: E402
from jobfit.matching.quote_check import require_quotes  # noqa: E402

RUN = ROOT / 'evals/results/cp24/test_run_v1'
GOLD = ROOT / 'evals/gold/test_v13_cp24_r1'
OUT = ROOT / 'evals/results/cp24/supplementary_v2'  # v1 counted held jobs without a matching call as fallback


def digest(p: Path) -> str:
    return sha256(p.read_bytes()).hexdigest()


def main() -> int:
    if OUT.exists():
        raise SystemExit(f'{OUT.relative_to(ROOT)} exists; written once')
    labels = {}
    for line in (GOLD / 'relevance_gold.jsonl').read_text().splitlines():
        r = json.loads(line)
        labels.setdefault(r['cv_id'], {})[r['job_id']] = int(r['relevance_0_3'])
    eligible = sorted((ROOT / 'evals/splits/test_job_ids.txt').read_text().split())
    run = json.loads((RUN / 'test_run.json').read_text())
    per_cv, cases = {}, []
    for cv in PRIMARY + SUPPLEMENTARY:
        f = json.loads((RUN / f'final_{cv}.json').read_text())
        text = json.loads((RUN / f'{cv}_parse.json').read_text())['parsed']['profile']['raw_text']
        lab = labels.get(cv, {})
        order, stage1 = run['cvs'][cv]['final_order'], run['cvs'][cv]['stage1_ids']
        status = Counter(f['jobs'][j]['score']['status'] for j in f['order'])
        positives = invalid = 0
        for j in f['order']:
            for a in f['jobs'][j]['assessments']:
                for item in (a.get('branches') or [a]):
                    if item.get('label') in ('MATCH', 'PARTIAL'):
                        positives += 1
                        try:
                            require_quotes(item['cv_quotes'], text)
                        except Exception:
                            invalid += 1
        rec = {}
        for name, o in (('stage1', stage1), ('final', order)):
            m = ranking_metrics(o, lab, eligible_ids=eligible, k=10)
            rec[name] = {'value': m['recall_at_k']['value'], 'numerator': m['recall_at_k']['numerator'],
                         'denominator': m['recall_at_k']['denominator'], 'reason': m['recall_at_k'].get('reason')}
        hard_neg = [(pos, j) for pos, j in enumerate(order, 1) if lab.get(j) == 0]
        low_top5 = [(pos, j, lab.get(j)) for pos, j in enumerate(order[:5], 1) if lab.get(j) is not None and lab[j] <= 1]
        held_rel = [(j, lab.get(j), f['jobs'][j]['score']['status']) for j in f['order']
                    if f['jobs'][j]['score']['status'] not in ('final', 'provisional') and (lab.get(j) or 0) >= 2]
        def path(j):
            att = f['jobs'][j]['attempts']
            if not att:
                return 'no_matching_call (held before matching)'
            return ' -> '.join(f"{a['model']}:{a['status'] if a['status'] == 'done' else a.get('error')}" for a in att)
        paths = Counter(path(j) for j in f['order'])
        fallback = [j for j in f['order'] if len(f['jobs'][j]['attempts']) > 1]
        sol_errors = Counter(a.get('error') or a.get('status') for j in f['order'] for a in f['jobs'][j]['attempts']
                             if a.get('model') == 'gpt-6-sol' and a.get('status') != 'done')
        per_cv[cv] = {'group': 'primary_heldout' if cv in PRIMARY else 'supplementary_familiar',
                      'wall_s': f['wall_s'], 'analyzed': len(f['order']), 'score_status': dict(status),
                      'held_or_unscored': sum(v for k, v in status.items() if k not in ('final', 'provisional')),
                      'luna_fallback': len(fallback), 'matching_paths': dict(paths), 'sol_attempt_errors': dict(sol_errors),
                      'quote_validity': {'positive_items': positives, 'invalid': invalid,
                                         'rate': (positives - invalid) / positives if positives else None},
                      'labeled_pool_recall_at_10': rec,
                      'hard_negatives_rel0_in_final_top10': [{'position': p, 'job_id': j} for p, j in hard_neg],
                      'relevance_0_1_in_final_top5': [{'position': p, 'job_id': j, 'relevance': r} for p, j, r in low_top5],
                      'relevant_jobs_held_or_unscored': [{'job_id': j, 'relevance': r, 'status': s} for j, r, s in held_rel]}
        for p, j in hard_neg:
            cases.append({'cv_id': cv, 'job_id': j, 'kind': 'hard negative (relevance 0) in final top 10', 'position': p,
                          'score_status': f['jobs'][j]['score']['status'], 'score_pct': f['jobs'][j]['score']['score_pct']})
        for j, r, s in held_rel:
            cases.append({'cv_id': cv, 'job_id': j, 'kind': 'relevant job held or unscored', 'relevance': r, 'score_status': s,
                          'reasons': f['jobs'][j]['score'].get('reasons')})
    from jobfit.config import get_settings
    from jobfit.llm.ledger import UsageLedger
    recs = [r for r in UsageLedger(get_settings().usage_ledger).records() if r.run_id.startswith('cp24_test')]
    cost = {}
    for r in recs:
        c = cost.setdefault(r.run_id, {'calls': 0, 'usd': 0.0, 'latency_ms': []})
        c['calls'] += 1
        c['usd'] += r.cost_usd
        if r.ok and r.latency_ms:
            c['latency_ms'].append(r.latency_ms)
    cost = {k: {'calls': v['calls'], 'usd': round(v['usd'], 6),
                'latency_p50_s': round(statistics.median(v['latency_ms']) / 1000, 1) if v['latency_ms'] else None,
                'latency_p95_s': round(sorted(v['latency_ms'])[max(0, round(.95 * len(v['latency_ms'])) - 1)] / 1000, 1) if v['latency_ms'] else None}
            for k, v in sorted(cost.items())}
    walls = [v['wall_s'] for v in per_cv.values()]
    out = {'created_at': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'api_calls': 0,
           'scope': 'descriptive supplement to cp24-report-contract-v1; headline unchanged; no choice is made from these numbers',
           'per_cv': per_cv, 'cases': cases,
           'totals': {'quote_validity_all_cvs': sum(v['quote_validity']['positive_items'] - v['quote_validity']['invalid'] for v in per_cv.values()) /
                      sum(v['quote_validity']['positive_items'] for v in per_cv.values()),
                      'positive_items': sum(v['quote_validity']['positive_items'] for v in per_cv.values()),
                      'luna_fallback_jobs': sum(v['luna_fallback'] for v in per_cv.values()),
                      'analyzed_jobs': sum(v['analyzed'] for v in per_cv.values()),
                      'one_cv_wall_s': {'min': min(walls), 'median': statistics.median(walls), 'max': max(walls)}},
           'cost_by_phase': cost, 'cost_total_usd': round(sum(v['usd'] for v in cost.values()), 6),
           'not_measured': {'evidence_macro_f1_on_test': 'test A/B sheets were AI-assisted drafts that were not imported (D-088 imports C only) and pipeline units differ from gold units; development values stand (CP2.3)',
                            'extraction_f1_on_test': 'same reason; extraction schema validity is in process status (FAIL-33)',
                            'unsupported_claims_on_test': 'needs unit-level gold evidence on test; not available',
                            'filter_recall': 'no optional filter used in the test run'}}
    OUT.mkdir(parents=True)
    (OUT / 'summary.json').write_text(json.dumps(out, indent=1) + '\n')
    (OUT / 'receipt.json').write_text(json.dumps({
        'summary_sha256': digest(OUT / 'summary.json'), 'script_sha256': digest(Path(__file__)),
        'inputs_sha256': {str(p.relative_to(ROOT)): digest(p) for p in
                          [RUN / 'test_run.json', GOLD / 'relevance_gold.jsonl'] + sorted(RUN.glob('final_CV*.json'))}}, indent=1) + '\n')
    print(json.dumps({'totals': out['totals'], 'cost_total_usd': out['cost_total_usd'], 'cases': len(cases)}, indent=1))
    for cv, v in per_cv.items():
        print(cv, v['wall_s'], v['score_status'], 'fallback', v['luna_fallback'], v['sol_attempt_errors'], 'recall', v['labeled_pool_recall_at_10']['stage1']['value'], v['labeled_pool_recall_at_10']['final']['value'], 'hardneg', v['hard_negatives_rel0_in_final_top10'], 'low5', v['relevance_0_1_in_final_top5'], 'heldrel', v['relevant_jobs_held_or_unscored'])
    print(json.dumps(cost))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
