"""Prepare a pending alignment proposal from saved development run 06, without inference.

No workbook input, no gold writes, no quality metrics. Existing artifacts are
preserved; pass a fresh --output path for a later review record.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
from collections import Counter
import hashlib
import json
from jobfit.config import REPO_ROOT
from jobfit.eval.alignment import alignment_review
from scripts.run_batch_extraction import development_sources


def prepare():
    extraction_path = REPO_ROOT / 'evals/gold/extraction_gold.jsonl'
    evidence_path = REPO_ROOT / 'evals/gold/evidence_gold.jsonl'
    run_path = REPO_ROOT / 'evals/results/cp22_live_cv1_j1_20261002_06.json'
    extraction = [json.loads(x) for x in extraction_path.read_text().splitlines()]
    evidence = [json.loads(x) for x in evidence_path.read_text().splitlines()]
    run = json.loads(run_path.read_text())
    source = development_sources(['F00022'])[0]['text']
    source_hash = hashlib.sha256(source.encode()).hexdigest()
    if source_hash != run['jd_sha256']:
        raise ValueError('Saved run and frozen development JD source differ')
    gold = [r for r in extraction if r['job_id'] == 'F00022']
    b = [r for r in evidence if r['job_id'] == 'F00022' and r['cv_id'] == 'CV1']
    if any(r['review_status'] != 'approved' or r['split'] != 'development' for r in b):
        raise ValueError('Evidence reference must be approved development only')
    # Explicit semantic proposals after reading source, unit text and qualifiers.
    # Numbers identify records only; neither numbering nor counts generate mappings.
    entries = [
        ([1], [1], 'Same scoped DS employment duration; fresh-graduate exception remains unknown importance.'),
        ([2], [2], 'Python requirement; compare qualification wording, not only the shared clause.'),
        ([3], [3], 'SQL requirement; shared Python/SQL clause is not an automatic merge.'),
        ([4], [4], 'Math: model drops Intermediate depth wording; inspect qualifier preservation without inventing a new depth label rule.'),
        ([20], [5], 'Statistics: model drops Intermediate depth wording; same qualifier review as math.'),
        ([21], [6], 'Machine learning: model drops Intermediate depth wording; same qualifier review as math.'),
        ([5], [7], 'Gold required structured/unstructured alternative G2; model unknown simple unresolved. Gold MATCH versus model failed/null is not NO_MATCH. Main denominator changes.'),
        ([6, 7], [8], 'Model combines architecture AND engineering, unresolved. Gold has two preferred units with NO_MATCH and PARTIAL. Not one comparable label.'),
        ([8], [9], 'GCP preferred requirement.'),
        ([9], [10], 'Visualization tools required; preserve tool-versus-example distinction.'),
        ([10], [11], 'Google Data Studio preferred example.'),
        ([11], [12], 'Problem solving: model NO_MATCH versus approved MATCH; review meaning of source evidence.'),
        ([12], [13], 'Structured thinking: both NO_MATCH; agreement is not a new annotation approval.'),
        ([13], [14], 'Scientific approach: model NO_MATCH versus approved PARTIAL.'),
        ([14], [15], 'Minimal supervision: both NO_MATCH.'),
        ([15], [16], 'Keeping supervisor informed: model NO_MATCH versus approved MATCH.'),
        ([16], [17], 'Teamwork: both NO_MATCH.'),
        ([17], [18], 'Communication: model MATCH versus approved PARTIAL. Preserve pilot v0.1 precedent; any clarification remains a human decision.'),
        ([18], [19, 20], 'Model splits willingness to learn and independent learning; gold keeps one scoped unit. Do not count one gold label twice.'),
        ([19], [21], 'Initiative: both NO_MATCH.'),
    ]
    proposals = [{'gold_ids': [f'J1-U{x:02d}' for x in gi],
                  'model_ids': [f'U{x:02d}' for x in mi], 'note': note}
                 for gi, mi, note in entries]
    result = alignment_review(gold, run['report']['extraction']['units'], proposals)
    bm = {r['unit_no']: r for r in b}
    mm = {r['unit_id']: r for r in run['report']['assessments']}
    for row in result['rows']:
        row['gold_evidence'] = [bm[k] for k in row['gold_ids']]
        row['model_evidence'] = [mm[k] for k in row['model_ids']]
    dev = set((REPO_ROOT / 'evals/splits/dev_job_ids.txt').read_text().splitlines())
    result.update(
        job_id='F00022', cv_id='CV1', split='development',
        analysis_date=run['report']['analysis_date'], source_sha256=source_hash,
        sources={str(p.relative_to(REPO_ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in [extraction_path, evidence_path, run_path]},
        coverage={'gold_A': len(gold), 'model_A': len(run['report']['extraction']['units']),
                  'gold_B': len(b), 'model_B': len(mm), 'proposed_groups': len(result['rows']),
                  'relations': dict(Counter(x['relation'] for x in result['rows']))},
        saved_model_score=run['report']['score'],
        approved_pilot_score_reference={'score_pct': 92.86, 'required_total': 7,
            'note': 'Existing pilot v1 result, not recalculated or changed here.'},
        J4_eligibility={'job_id': 'F00016', 'in_frozen_development': 'F00016' in dev,
            'approved_development_A': sum(r['job_id'] == 'F00016' and r['review_status'] == 'approved' and r['split'] == 'development' for r in extraction),
            'approved_B_rows': sum(r['job_id'] == 'F00016' and r['review_status'] == 'approved' for r in evidence),
            'measurement_limit': 'Eligible for extraction review only. No J4 evidence accuracy claim; no new model run.'},
        api_calls=0, cost_usd=0, workbook_read=False, gold_written=False,
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = prepare()
    with args.output.open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({'status': result['status'], 'coverage': result['coverage'], 'cost_usd': 0}))


if __name__ == '__main__':
    main()
