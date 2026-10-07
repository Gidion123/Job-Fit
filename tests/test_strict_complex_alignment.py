from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts.prepare_cp23_extraction_alignment import prepare
from jobfit.eval.strict_complex_alignment import apply_approved_complex_policy
from jobfit.eval.metrics import extraction_metrics

def case_and_receipt():
    c=next(c for c in prepare()['cases'] if c['stage_id']=='claude-haiku-4.5/F00036')
    r=json.loads(Path('evals/results/cp23_stage2_complex_alignment_approval_20261003_v1.json').read_text())
    return c,r

def test_exact_case_accounting_preserves_pending_review_and_original():
    c,r=case_and_receipt();original=deepcopy(c)
    out=apply_approved_complex_policy(c,r)
    assert c==original and out['human_verified'] is False
    expanded=[row for row in out['rows'] if row.get('accounting_only')]
    assert len(expanded)==5
    assert sum(len(row['gold_ids']) for row in expanded)==2
    assert sum(len(row['model_ids']) for row in expanded)==3
    assert out['original_complex_relation']['relation']=='complex_pending'
    with pytest.raises(ValueError):extraction_metrics(out,reference_complete=True)

def test_not_a_blanket_many_to_many_approval():
    c,r=case_and_receipt();c['stage_id']='other/F00036'
    with pytest.raises(ValueError):apply_approved_complex_policy(c,r)
    c,r=case_and_receipt();r['approved_by']='model'
    with pytest.raises(ValueError):apply_approved_complex_policy(c,r)

def test_counts_under_synthetic_verified_fixture_only():
    c,r=case_and_receipt();out=apply_approved_complex_policy(c,r)
    # This is a test-owned artificial verified fixture, never a saved acceptance.
    out['human_verified']=True
    for row in out['rows']:
        row['status']='verified';row['semantic_equivalent']=False
    m=extraction_metrics(out,reference_complete=True)
    assert m['tp']==0 and m['fn']==len(c['gold_unit_ids']) and m['fp']==len(c['model_unit_ids'])
