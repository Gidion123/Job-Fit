"""CP2.4 report contract: CV3-CV5 headline, CV1-CV2 diagnostic, never pooled. Synthetic data only."""
import pytest

from jobfit.eval.heldout_report import (PRIMARY, SUPPLEMENTARY, build_report, check_contract, headline_text)

ELIGIBLE = [f'J{i}' for i in range(40)]


def run_file():
    return {'run_id': 'synthetic', 'cvs': {cv: {'stage1_ids': ELIGIBLE[:10], 'final_order': ELIGIBLE[:10][::-1]}
                                           for cv in PRIMARY + SUPPLEMENTARY}}


def labels(primary_rel: int, familiar_rel: int):
    out = {}
    for cv in PRIMARY + SUPPLEMENTARY:
        rel = primary_rel if cv in PRIMARY else familiar_rel
        out[cv] = {j: rel for j in ELIGIBLE[:10]}
    return out


def test_headline_uses_only_cv3_to_cv5():
    rep = build_report(run_file(), labels(primary_rel=3, familiar_rel=0), eligible=ELIGIBLE)
    assert rep['headline'] == 'primary_heldout'
    assert rep['primary_heldout']['p_at_5']['final_macro'] == 1.0          # CV3-CV5 all relevant
    assert rep['supplementary_familiar']['p_at_5']['final_macro'] == 0.0   # CV1-CV2 none relevant
    # a pooled mean would be 0.6; it must not exist anywhere in the report
    assert 0.6 not in [m['final_macro'] for g in ('primary_heldout', 'supplementary_familiar')
                       for m in (rep[g]['p_at_5'],)]
    text = headline_text(rep)
    assert text.startswith('Held-out test (CV3-CV5') and 'P@5 1.000' in text and 'familiar-profile diagnostic' in text


def test_pooled_keys_are_rejected():
    rep = build_report(run_file(), labels(3, 0), eligible=ELIGIBLE)
    for bad in ('pooled', 'overall', 'all_cvs', 'cv1_cv5', 'combined'):
        broken = dict(rep, **{bad: {'p_at_5': 0.6}})
        with pytest.raises(ValueError):
            check_contract(broken)
    moved = dict(rep, primary_heldout=dict(rep['primary_heldout'], cvs=['CV1', 'CV3', 'CV4']))
    with pytest.raises(ValueError):
        check_contract(moved)


def test_run_must_cover_exactly_cv1_to_cv5():
    r = run_file()
    del r['cvs']['CV5']
    with pytest.raises(ValueError):
        build_report(r, {}, eligible=ELIGIBLE)


def test_missing_labels_are_not_zero_and_cv_is_omitted_with_reason():
    lab = labels(3, 3)
    del lab['CV4'][ELIGIBLE[0]]                      # one top position unjudged for CV4
    rep = build_report(run_file(), lab, eligible=ELIGIBLE)
    g = rep['primary_heldout']['ndcg_at_10']
    assert g['cv_count'] == 2 and 'CV4' in g['omitted'] and g['final_macro'] == 1.0


def test_evaluator_refuses_without_approved_freeze(tmp_path):
    import json
    from scripts import evaluate_cp24_test as ev
    run = tmp_path / 'run.json'
    run.write_text(json.dumps({'run_id': 'x', 'freeze_folder': str(tmp_path), 'cvs': {}}))
    labels = tmp_path / 'labels.jsonl'
    labels.write_text('')
    with pytest.raises(SystemExit):
        ev.main([str(run), str(labels)])
