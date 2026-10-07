import pytest
from jobfit.eval.alignment import alignment_review

def gold(n):return {'unit_no':n,'split':'development','review_status':'approved','review_action':'accepted','source_quote':'A and B'}
def model(n):return {'unit_id':n,'source_quotes':['A and B']}

def test_split_merge_and_omission_preserve_distinct_identities_without_metrics():
    g=[gold(x) for x in ['same_id','g2','g3','g4']];m=[model(x) for x in ['same_id','m2','m3']]
    p=[{'gold_ids':['same_id','g2'],'model_ids':['m3'],'note':'Separate evidence-scoped concepts combined.'},
       {'gold_ids':['g3'],'model_ids':['same_id','m2'],'note':'One compound gold unit split.'},
       {'gold_ids':['g4'],'model_ids':[],'note':'No model unit found.'}]
    r=alignment_review(g,m,p)
    assert [x['relation'] for x in r['rows']]==['model_merge','model_split','model_omission']
    assert r['metrics'] is None and not r['human_verified'] and not r['unmapped_gold']
    assert r['rows'][0]['model_ids']==['m3']  # identical-looking IDs never auto-align

def test_unmapped_and_reused_rows_cannot_silently_inflate_evaluation():
    p=[{'gold_ids':['g'],'model_ids':['m'],'note':'proposal'}]
    assert alignment_review([gold('g'),gold('unmapped')],[model('m')],p)['unmapped_gold']==['unmapped']
    with pytest.raises(ValueError):alignment_review([gold('g')],[model('m')],p+p)
    g=gold('g');g['review_status']='pending'
    with pytest.raises(ValueError):alignment_review([g],[model('m')],p)
