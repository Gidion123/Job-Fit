"""D-078 rule for K and PARTIAL weight, exactly as approved before the labels existed.

1. Primary: macro NDCG@10 of the final product order at weight 0.5; secondary macro P@5.
2. K in {10, 20, 30}: smallest K whose NDCG@10 is within 0.02 of the best K and whose
   P@5 is not lower than the best K's P@5 minus 0.1. Smaller K wins ties.
3. Weight at the chosen K: keep 0.5 unless another weight is better by more than 0.02 NDCG@10.
4. Seniority rule: if the rule is worse than no rule on both NDCG@10 and P@5 at the
   chosen K, freeze without it.
5. A cell with a missing label is unavailable; it never counts as zero.
Rows: dicts with seniority_rule, k, partial_weight, macro_ndcg_at_10, macro_p_at_5.
"""
from __future__ import annotations

from collections.abc import Sequence

KS = (10, 20, 30)
WEIGHTS = (0.25, 0.5, 0.75)
EPS = 1e-9


def _cell(rows, rule, k, w):
    hit = [r for r in rows if r['seniority_rule'] == rule and r['k'] == k and abs(r['partial_weight'] - w) < EPS]
    if len(hit) != 1:
        raise ValueError(f'expected one cell for rule={rule} k={k} w={w}, found {len(hit)}')
    return hit[0]


def _ok(cell):
    return cell['macro_ndcg_at_10'] is not None and cell['macro_p_at_5'] is not None


def choose(rows: Sequence[dict], *, seniority_rule: bool = True) -> dict:
    trace = []
    cells = {k: _cell(rows, seniority_rule, k, 0.5) for k in KS}
    missing = [k for k, c in cells.items() if not _ok(c)]
    if missing:
        return {'status': 'unavailable', 'reason': f'cells with missing labels at weight 0.5: K={missing}',
                'trace': trace}
    best_k = max(KS, key=lambda k: (cells[k]['macro_ndcg_at_10'], -k))
    best = cells[best_k]
    trace.append(f"best K by NDCG@10 at w=0.5: {best_k} ({best['macro_ndcg_at_10']:.3f}, P@5 {best['macro_p_at_5']:.3f})")
    chosen_k = next(k for k in KS
                    if cells[k]['macro_ndcg_at_10'] >= best['macro_ndcg_at_10'] - 0.02 - EPS
                    and cells[k]['macro_p_at_5'] >= best['macro_p_at_5'] - 0.1 - EPS)
    trace.append(f'smallest K within 0.02 NDCG and 0.1 P@5 of the best: {chosen_k}')
    base = _cell(rows, seniority_rule, chosen_k, 0.5)
    weight = 0.5
    others = {w: _cell(rows, seniority_rule, chosen_k, w) for w in WEIGHTS if w != 0.5}
    better = {w: c for w, c in others.items() if _ok(c) and c['macro_ndcg_at_10'] > base['macro_ndcg_at_10'] + 0.02 + EPS}
    if better:
        weight = max(better, key=lambda w: better[w]['macro_ndcg_at_10'])
        trace.append(f'weight {weight} beats 0.5 by more than 0.02 NDCG@10')
    else:
        trace.append('no weight beats 0.5 by more than 0.02 NDCG@10; keep 0.5')
    unavailable_weights = [w for w, c in others.items() if not _ok(c)]
    if unavailable_weights:
        trace.append(f'weights unavailable (missing labels): {unavailable_weights}')
    rule_on = seniority_rule
    if seniority_rule:
        off = _cell(rows, False, chosen_k, weight)
        on = _cell(rows, True, chosen_k, weight)
        if _ok(off) and off['macro_ndcg_at_10'] > on['macro_ndcg_at_10'] + EPS and off['macro_p_at_5'] > on['macro_p_at_5'] + EPS:
            rule_on = False
            trace.append('rule worse than no rule on both NDCG@10 and P@5: freeze without it')
        elif not _ok(off):
            trace.append('no-rule cell unavailable: rule kept (step 4 cannot drop it)')
        else:
            trace.append('rule not worse on both metrics: keep the rule')
    final = _cell(rows, rule_on, chosen_k, weight)
    return {'status': 'chosen', 'k': chosen_k, 'partial_weight': weight, 'seniority_rule': rule_on,
            'macro_ndcg_at_10': final['macro_ndcg_at_10'], 'macro_p_at_5': final['macro_p_at_5'], 'trace': trace}
