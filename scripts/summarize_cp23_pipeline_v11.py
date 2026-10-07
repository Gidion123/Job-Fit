"""Summarize the immutable v1 and v1.1 development receipts without inference."""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.config import get_settings
from jobfit.llm.ledger import UsageLedger

OLD = ROOT / 'evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1'
NEW = ROOT / 'evals/results/cp23/pipeline_v11'
OUTPUT = NEW / 'coverage_summary_v2.json'
CONTINUATION = {('CV1', 'F00022'), ('CV2', 'F00126'),
                ('CV1', 'F00310'), ('CV2', 'F00310')}


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def summarize() -> dict:
    old_plan = read(OLD / 'plan.json')
    new_plan = read(NEW / 'plan_v1.json')
    primary = read(NEW / 'summary_v1.json')
    follow = read(NEW / 'hold_continuation_summary_v2.json')
    if primary['status'] != 'completed' or primary['pairs'] != 60:
        raise ValueError('Primary 60-pair run is incomplete')
    if len(follow['cases']) != len(CONTINUATION):
        raise ValueError('Continuation is incomplete')
    if set(old_plan['rankings']) != {'CV1', 'CV2'}:
        raise ValueError('Unexpected CV scope')
    if any(path.is_file() and sha256(path.read_bytes()).hexdigest() != expected
           for rel, expected in new_plan['protected_sha256'].items()
           for path in [ROOT / rel]):
        raise ValueError('Protected input changed')
    if any(not (ROOT / rel).is_file() for rel in new_plan['protected_sha256']):
        raise ValueError('Protected input is missing')

    pair_rows = []
    for cv, ranking in old_plan['rankings'].items():
        if len(ranking) != 30:
            raise ValueError('Expected original top-30 ranking')
        for position, job in enumerate(ranking, 1):
            continued = (cv, job) in CONTINUATION
            path = (NEW / f'pair_hold_{cv}_{job}_v11_v2.json' if continued else
                    NEW / f'pair_{cv}_{job}_v11.json')
            if not path.is_file():
                raise ValueError(f'Missing pair record {cv}/{job}')
            row = read(path)
            if (row['cv_id'], row['job_id']) != (cv, job):
                raise ValueError('Pair identity mismatch')
            pair_rows.append({'cv_id': cv, 'job_id': job, 'original_rank': position,
                              'record': str(path.relative_to(ROOT)),
                              'status': row['status'],
                              'error_code': row.get('error_code') or row.get('reason'),
                              'H1_status': (row.get('score_H1') or {}).get('status'),
                              'H2_status': (row.get('score_H2') or {}).get('status'),
                              'H1_score_pct': (row.get('score_H1') or {}).get('score_pct'),
                              'H2_score_pct': (row.get('score_H2') or {}).get('score_pct'),
                              'excluded_needs_review': row.get('excluded_needs_review') or [],
                              'continuation': continued})
    status_counts = {policy: dict(Counter(r[f'{policy}_status'] or 'no_score_object'
                                         for r in pair_rows)) for policy in ('H1', 'H2')}
    usable = lambda r, policy: r[f'{policy}_status'] in {'final', 'provisional'}
    per_cv = {cv: {policy: sum(r['cv_id'] == cv and usable(r, policy) for r in pair_rows)
                   for policy in ('H1', 'H2')} for cv in ('CV1', 'CV2')}
    jd_ids = sorted(set().union(*(set(x) for x in old_plan['rankings'].values())))
    jd_rows = []
    for job in jd_ids:
        if job == 'F00369':
            jd_rows.append({'job_id': job, 'status': 'held_source', 'jd_quality': None,
                            'unit_count': None, 'source': None})
            continue
        path = (NEW / f'jd_hold_{job}_v11_v2.json' if job in {'F00022', 'F00126', 'F00310'}
                else NEW / f'jd_{job}_v11.json' if job in new_plan['redo_jds']
                else OLD / f'jd_{job}.json')
        if not path.is_file():
            raise ValueError(f'Missing JD record {job}')
        row = read(path)
        extraction = row.get('extraction') or {}
        jd_rows.append({'job_id': job, 'status': row['status'],
                        'jd_quality': extraction.get('jd_quality'),
                        'unit_count': len(extraction.get('units', [])) if extraction else None,
                        'needs_review_units': sum(bool(u.get('needs_review')) for u in
                                                  extraction.get('units', [])),
                        'error_code': row.get('error_code'),
                        'source': str(path.relative_to(ROOT))})
    ledger = UsageLedger(get_settings().usage_ledger)
    calls = [r for r in ledger.records() if r.run_id == new_plan['run_id']]
    accounted = sum(r.cost_usd for r in calls)
    return {'schema_version': 'cp23-pipeline-v11-coverage-v2',
            'scope': 'development CV1/CV2, original Hybrid Qwen top-30 per CV',
            'historical_v1_final_pairs': 20,
            'historical_v1_H2_offline_counterfactual_pairs': 30,
            'v11_primary_H1_pairs': primary['H1_usable'],
            'v11_primary_H2_pairs': primary['H2_usable'],
            'v11_with_continuation_H1_pairs': sum(usable(r, 'H1') for r in pair_rows),
            'v11_with_continuation_H2_pairs': sum(usable(r, 'H2') for r in pair_rows),
            'per_cv': per_cv, 'pair_status_counts': status_counts,
            'process_valid_JDs': sum(r['status'] == 'done' for r in jd_rows),
            'JD_quality_ok': sum(r['jd_quality'] == 'ok' for r in jd_rows),
            'JD_attempted': len(jd_rows)-1, 'source_held_JDs': ['F00369'],
            'zero_required_examples': ['F00309'],
            'pairs': pair_rows, 'jds': jd_rows,
            'run_calls': len(calls), 'run_accounted_usd': accounted,
            'run_uncertain_reservation_usd': sum(r.cost_usd for r in calls
                                                 if r.cost_source == 'uncertain_upper_bound'),
            'run_cap_usd': 3.00, 'project_ledger_total_usd': ledger.total_spent(),
            'one_cv_k20_end_to_end_wall_measured': False,
            'quality_limit': 'Process-valid and source-exact outputs are not human-approved semantic matches.',
            'source_receipts': {'primary': str((NEW/'summary_v1.json').relative_to(ROOT)),
                                'continuation': str((NEW/'hold_continuation_summary_v2.json').relative_to(ROOT))},
            'protected_input_sha256': new_plan['protected_sha256'],
            'test_used': False, 'gold_written': False}


if __name__ == '__main__':
    result = summarize()
    if OUTPUT.exists():
        raise SystemExit('Versioned summary already exists')
    with OUTPUT.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps({k: result[k] for k in ('v11_with_continuation_H1_pairs',
                                             'v11_with_continuation_H2_pairs',
                                             'process_valid_JDs', 'run_accounted_usd')}))
