"""Deterministic development pooling; never silently drop mandatory top-five rows."""
import random


def pool_rows(cv_id, rankings, titles, gold_ids, *, limit=20, seed=20261001):
    rows = {}
    for method, ranking in sorted(rankings.items()):
        ids = [r['job_id'] for r in ranking[:10]]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate ranking id')
        for position, job_id in enumerate(ids, 1):
            row = rows.setdefault(job_id, dict(cv_id=cv_id, job_id=job_id,
                title=titles[job_id], best_rank=position, methods_top10=[],
                in_top5_any='no', already_gold='yes' if job_id in gold_ids else 'no',
                gold_review='no'))
            row['best_rank'] = min(row['best_rank'], position)
            row['methods_top10'].append(method)
            if position <= 5:
                row['in_top5_any'] = 'yes'
    mandatory = sorted(j for j, r in rows.items()
                       if r['in_top5_any'] == 'yes' and r['already_gold'] == 'no')
    conflict = len(mandatory) > limit
    selected = set(mandatory)
    others = sorted(j for j, r in rows.items()
                    if j not in selected and r['already_gold'] == 'no')
    random.Random(f'{seed}:{cv_id}').shuffle(others)
    if not conflict:
        selected.update(others[:max(0, limit-len(selected))])
    for job_id, row in rows.items():
        row['methods_top10'] = '|'.join(row['methods_top10'])
        row['gold_review'] = ('pending_decision' if conflict and row['already_gold'] == 'no'
                              else 'yes' if job_id in selected else 'no')
    return sorted(rows.values(), key=lambda r: r['job_id']), dict(
        pool_size=len(rows), mandatory_new_top5=len(mandatory), review_limit=limit,
        selection_blocked=conflict,
        selected_new=0 if conflict else len(selected),
        already_gold_in_pool=sum(r['already_gold'] == 'yes' for r in rows.values()))
