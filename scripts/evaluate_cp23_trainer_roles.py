"""Offline check of training/mentoring posts that CP1 classed as target roles. No model call.

Development details only; for the test split only a count is printed (no titles), so
nothing about held-out jobs is used for a choice. Guideline v1.3 Part D treats
mentoring/training roles as outside the four target families.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

PATTERN = re.compile(r'\b(trainer|mentor|instruktur|instructor|tutor|pengajar|dosen|lecturer|teacher|guru|'
                     r'fasilitator|facilitator|coach|bootcamp)\b', re.I)
GOLD = ROOT / 'evals/gold/development_v13_reviewed_20261003_stage1_r3/relevance_gold.jsonl'


def build(gold: Path = GOLD) -> dict:
    dev = set((ROOT / 'evals/splits/dev_job_ids.txt').read_text().split())
    test = set((ROOT / 'evals/splits/test_job_ids.txt').read_text().split())
    rows = {json.loads(l)['final_cluster_id']: json.loads(l)
            for l in (ROOT / 'data/processed/jobs_features.jsonl').read_text().splitlines()}
    hits = sorted(j for j in dev if PATTERN.search(rows[j]['title']))
    labels = [json.loads(l) for l in gold.read_text().splitlines()]
    rankings = json.loads((ROOT / 'evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1/plan.json').read_text())['rankings']
    bundle = json.loads((ROOT / 'evals/demo/saved_demo_v1/bundle.json').read_text())
    final = {}
    for e in bundle['entries'].values():
        if e['seniority_rule']:
            cards = e['result']['blocks'][0]['groups']['matches']
            final[e['cv_id']] = [{'position': i, 'job_id': c['job_id'], 'score_pct': c['score_pct']}
                                 for i, c in enumerate(cards, 1) if c['job_id'] in hits]
    return {'schema_version': 'cp23-dev-trainer-roles-v1', 'api_calls': 0, 'pattern': PATTERN.pattern,
            'development_jobs': [{'job_id': j, 'title': rows[j]['title'], 'role_family': rows[j]['role_family'],
                                  'experience_bucket': rows[j]['experience_bucket']} for j in hits],
            'test_split_count_only': sum(1 for j in test if PATTERN.search(rows[j]['title'])),
            'approved_labels': [{'cv_id': l['cv_id'], 'job_id': l['job_id'], 'relevance': l['relevance_0_3']}
                                for l in labels if l['job_id'] in hits and l.get('review_status') == 'approved'],
            'stage1_top30_positions': {cv: [(i, j) for i, j in enumerate(r, 1) if j in hits] for cv, r in rankings.items()},
            'saved_demo_final_positions_rule_on_k20': final,
            'limits': ['Three development jobs: too few to tune or evaluate a rule.',
                       'One of them is in the pending blind gap workbook, so its label is not read here.']}


if __name__ == '__main__':
    res = build()
    print(json.dumps(res, indent=1, ensure_ascii=False))
    if '--write' in sys.argv:
        out = ROOT / 'evals/results/cp23/dev_eval_v2_20261004/trainer_roles_v1.json'
        with out.open('x') as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
