import pytest
from scripts.evaluate_cp23_gold_upper_bound import score_order

def test_missing_score_never_drops_or_fills_original_rank():
    original=['A','B','C']
    assert score_order(original,{'A':20,'C':100}) is None
    assert original==['A','B','C']

def test_score_ties_keep_retrieval_order():
    assert score_order(['C','B','A'],{'C':30,'B':80,'A':80})==['B','A','C']

@pytest.mark.parametrize('top,scores',[(['A','A'],{'A':1}),(['A'],{'B':1})])
def test_invalid_order_identity_rejected(top,scores):
    with pytest.raises(ValueError):score_order(top,scores)
