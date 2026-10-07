"""D-053 held-out ranking pool: union of original top 10 stage-1 and top 10 final.

Pure functions, no file or model access. The script that writes workbooks lives in
scripts/build_cp23_test_workbook.py. Shorter lists are reported, never padded, and
no subset is chosen from relevance outcomes.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import random

POOL_RULE = 'D-053-top10-union-v1'
DEPTH = 10
# D-045 phase 1: 40 relevance labels in about 96 minutes, so 2.4 minutes per label.
MINUTES_PER_LABEL = 2.4


def build_pool(stage1: Mapping[str, Sequence[str]], final: Mapping[str, Sequence[str]], *,
               eligible: set[str], depth: int = DEPTH) -> dict:
    """Return pool rows with provenance and per-CV counts.

    `stage1[cv]` is the original stage-1 order (before the seniority rule) and
    `final[cv]` is the product order after matching. Both must stay inside the
    eligible test jobs.
    """
    if set(stage1) != set(final):
        raise ValueError('stage-1 and final orders must cover the same CVs')
    rows, per_cv = [], {}
    for cv in sorted(stage1):
        s1, fin = list(stage1[cv])[:depth], list(final[cv])[:depth]
        for name, ids in (('stage1', s1), ('final', fin)):
            if len(ids) != len(set(ids)):
                raise ValueError(f'{cv} {name} order has duplicate ids')
            if not set(ids) <= eligible:
                raise ValueError(f'{cv} {name} order leaves the eligible test jobs')
        union = list(dict.fromkeys(s1 + fin))
        for job in union:
            rows.append({'cv_id': cv, 'job_id': job,
                         'stage1_rank': s1.index(job) + 1 if job in s1 else None,
                         'final_rank': fin.index(job) + 1 if job in fin else None})
        per_cv[cv] = {'stage1_returned': len(s1), 'final_returned': len(fin),
                      'overlap': len(set(s1) & set(fin)), 'pairs': len(union),
                      'short_list': len(s1) < depth or len(fin) < depth}
    total = len(rows)
    return {'rule': POOL_RULE, 'depth': depth, 'rows': rows, 'per_cv': per_cv, 'pairs': total,
            'effort': {'minutes_per_label': MINUTES_PER_LABEL,
                       'source': 'D-045 phase 1 measured pace (40 labels, about 96 minutes)',
                       'estimated_minutes': round(total * MINUTES_PER_LABEL),
                       'sessions_at_2h': -(-round(total * MINUTES_PER_LABEL) // 120)}}


def blind_items(rows: Sequence[Mapping], *, seed: int, prefix: str = 'T') -> list[dict]:
    """Shuffle and strip every rank. Item ids are assigned after the shuffle."""
    pairs = [(r['cv_id'], r['job_id']) for r in rows]
    if len(pairs) != len(set(pairs)):
        raise ValueError('pool pairs must be unique')
    rng = random.Random(seed)
    shuffled = sorted(pairs)
    rng.shuffle(shuffled)
    width = max(2, len(str(len(shuffled))))
    return [{'item_id': f'{prefix}{i:0{width}d}', 'cv_id': cv, 'job_id': job}
            for i, (cv, job) in enumerate(shuffled, 1)]
