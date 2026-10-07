"""D-078 rule on hand-made grids."""
import itertools

from jobfit.eval.d078 import choose


def grid(values, off=None):
    rows = []
    for rule, k, w in itertools.product((True, False), (10, 20, 30), (0.25, 0.5, 0.75)):
        src = values if rule else (off or values)
        n, p = src.get((k, w), src.get(k, (0.5, 0.4)))
        rows.append({'seniority_rule': rule, 'k': k, 'partial_weight': w, 'macro_ndcg_at_10': n, 'macro_p_at_5': p})
    return rows


def test_smallest_k_within_tolerance_wins():
    out = choose(grid({10: (0.60, 0.5), 20: (0.615, 0.5), 30: (0.62, 0.6)}))
    assert out['k'] == 10 and out['partial_weight'] == 0.5 and out['seniority_rule']


def test_p5_tolerance_blocks_small_k():
    out = choose(grid({10: (0.61, 0.4), 20: (0.62, 0.6), 30: (0.60, 0.6)}))
    assert out['k'] == 20


def test_weight_changes_only_beyond_002():
    v = {10: (0.60, 0.5), 20: (0.50, 0.4), 30: (0.50, 0.4), (10, 0.25): (0.615, 0.5), (10, 0.75): (0.63, 0.5)}
    out = choose(grid(v))
    assert out['k'] == 10 and out['partial_weight'] == 0.75


def test_rule_dropped_only_if_worse_on_both():
    on = {10: (0.60, 0.5), 20: (0.5, 0.4), 30: (0.5, 0.4)}
    assert choose(grid(on, off={10: (0.65, 0.5)}))['seniority_rule'] is True      # P@5 tie
    assert choose(grid(on, off={10: (0.65, 0.6)}))['seniority_rule'] is False


def test_missing_labels_make_it_unavailable_never_zero():
    out = choose(grid({10: (None, 0.5), 20: (0.6, 0.5), 30: (0.6, 0.5)}))
    assert out['status'] == 'unavailable' and 'K=[10]' in out['reason']
