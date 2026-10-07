from collections import Counter
import pytest
from scripts.run_cp23_stage2_matching import plan,inputs,BUNDLE
from jobfit.eval.matching_evaluation import reference_inventory,reference_rows,evaluate

def test_reference_coverage_and_class_support_without_inference():
    r=reference_inventory(BUNDLE,plan()['stages'],inputs)
    assert r['units']==73 and r['classes']=={'MATCH':35,'PARTIAL':22,'NO_MATCH':16}
    assert len(r['pairs'])==4 and r['fixed_input_alignment_verified'] is False
    assert r['metrics'] is None and r['model_calls']==0

def test_failed_case_counts_all_gold_as_fn_not_negative_or_excluded():
    stage=plan()['stages'][0];cv,ex=inputs(stage);gold=reference_rows(BUNDLE,stage,cv,ex)
    failed=dict(status='failed',assessments=[])
    with pytest.raises(ValueError):evaluate(failed,gold,ex)
    metrics=evaluate(failed,gold,ex,fixed_input_alignment_verified=True)
    assert metrics['macro_f1']==0 and metrics['coverage']['numerator']==0
    for label,count in Counter(gold.values()).items():
        assert metrics['per_class'][label]['fn']==count
        assert metrics['confusion'][label]['not_assessed']==count

def test_null_or_clarification_is_not_forced_no_match():
    stage=plan()['stages'][0];cv,ex=inputs(stage);gold=reference_rows(BUNDLE,stage,cv,ex)
    rows=[]
    for unit in ex.units:
        # Failed checks deliberately have no branches or label. This is one
        # accepted process result that contains unassessed requirements.
        rows.append(dict(unit_id=unit.unit_id,label=None,check_status='failed'))
    m=evaluate(dict(status='done',assessments=rows),gold,ex,fixed_input_alignment_verified=True)
    assert m['macro_f1']==0 and all(m['confusion'][lab]['NO_MATCH']==0 for lab in gold.values())

def test_identity_omission_not_silently_ignored():
    stage=plan()['stages'][0];cv,ex=inputs(stage);gold=reference_rows(BUNDLE,stage,cv,ex)
    with pytest.raises(ValueError,match='identities'):
        evaluate(dict(status='done',assessments=[]),gold,ex,fixed_input_alignment_verified=True)
