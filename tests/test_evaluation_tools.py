from copy import deepcopy
import json
import math
from pathlib import Path
import pytest
from jobfit.eval.metrics import ranking_metrics, evidence_metrics, extraction_metrics, operational_summary
from jobfit.eval.run_eval import validate_comparable, compare_rankings, compare_llm_artifacts
from jobfit.eval.contract import validate_metric_contract

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = json.loads((ROOT/'evals/results/cp23_metric_contract_D052_D054_20261003_v1.json').read_text())


def ready():
    return {'status':'ready','gates':{k:True for k in ('contract','references','alignment','coverage','implementation')},
            'receipts':{k:'a'*64 for k in ('reference_sha256','alignment_sha256','coverage_sha256')},
            'held_reference_ids':[]}


def test_missing_original_rank2_cannot_be_filled_by_rank6():
    r = ranking_metrics(['a','missing','b','c','d','late'],
        {'a':2,'b':0,'c':0,'d':0,'late':3},eligible_ids={'a','missing','b','c','d','late'},k=5)
    assert r['precision_at_k']['value'] is None
    assert r['precision_at_k']['numerator']==1 and r['precision_at_k']['denominator']==5
    assert r['coverage']['unjudged_original_top_k_ids']==['missing']
    assert r['recall_at_k']['value']==.5
    assert r['ndcg_at_k'] is None


def test_p_at_5_original_denominator_and_short_ranking_hold():
    ranking=list('abcde')
    r=ranking_metrics(ranking,{'a':3,'b':2,'c':0,'d':2,'e':1},eligible_ids=ranking,k=5)
    assert r['precision_at_k']=={'numerator':3,'denominator':5,'value':.6}
    short=ranking_metrics(ranking[:4],{'a':3,'b':2,'c':0,'d':2,'e':1},eligible_ids=ranking,k=5)
    assert short['precision_at_k']['value'] is None
    assert short['precision_at_k']['reason']=='short_ranking_convention_pending'
    assert short['recall_at_k']['value'] is None


def test_exponential_ndcg_uses_original_positions_and_declared_eligible_pool():
    ranking=['b','a']
    judgments={'a':3,'b':2}
    r=ranking_metrics(ranking,judgments,eligible_ids={'a','b'},k=2)
    expected=(3+7/math.log2(3))/(7+3/math.log2(3))
    assert r['ndcg_at_k']==pytest.approx(expected)
    assert r['ndcg_ideal_scope']=='all_eligible_judged_pool'
    missing=ranking_metrics(['a','b']+['x'+str(i) for i in range(8)],judgments,
        eligible_ids={'a','b'}|{'x'+str(i) for i in range(8)},k=10)
    assert missing['ndcg_at_k'] is None and missing['ndcg_reason']=='missing_original_position_judgment'
    zeros=ranking_metrics(['a','b'],{'a':0,'b':0},eligible_ids={'a','b'},k=2)
    assert zeros['ndcg_at_k'] is None and zeros['ndcg_reason']=='zero_ideal_dcg'


def test_labeled_pool_recall_and_filter_coverage_are_explicit():
    r=ranking_metrics(['a','unjudged','c'],{'a':3,'b':2,'c':0,'d':3},
        eligible_ids={'a','b','c','unjudged'},k=2)
    assert r['recall_at_k']=={'numerator':1,'denominator':2,'value':.5}
    assert r['filter_recall']['value']==pytest.approx(2/3)
    assert r['coverage']['unjudged_original_top_k']==1
    no_relevant=ranking_metrics(['c'],{'c':0},eligible_ids={'c'},k=1)
    assert no_relevant['recall_at_k']['value'] is None
    assert no_relevant['recall_at_k']['reason']=='zero_judged_relevant_denominator'


def test_original_top_k_labeled_pool_recall_two_of_three():
    ranking=['a','unjudged','b','c']
    r=ranking_metrics(ranking,{'a':2,'b':3,'c':0,'d':2},
                      eligible_ids={'a','b','c','d','unjudged'},k=3)
    assert r['recall_at_k']=={'numerator':2,'denominator':3,'value':pytest.approx(2/3)}
    assert r['coverage']['unjudged_original_top_k_ids']==['unjudged']
    assert r['precision_at_k']['value'] is None


@pytest.mark.parametrize('ranking,judgments,eligible',[
    (['a','a'],{'a':3},['a']),(['outside'],{'a':3},['a']),
    (['a'],{'a':None},['a']),(['a'],{'a':True},['a']),
    (['a'],{'a':3},['a','a'])])
def test_invalid_ranking_and_missing_label_do_not_become_zero(ranking,judgments,eligible):
    with pytest.raises(ValueError):ranking_metrics(ranking,judgments,eligible_ids=eligible,k=1)


def test_evidence_failure_counts_gold_class_false_negative():
    g={'a':'MATCH','b':'PARTIAL','c':'NO_MATCH','d':'MATCH'}
    p={'a':'MATCH','b':'MATCH','c':'NO_MATCH','d':{'status':'failed','label':None}}
    r=evidence_metrics(g,p,alignment_verified=True)
    assert r['per_class']['MATCH']['f1']==.5
    assert r['macro_f1']==.5 and r['coverage']['value']==.75
    assert r['confusion']['MATCH']['not_assessed']==1
    assert r['confusion']['MATCH']['NO_MATCH']==0
    with pytest.raises(ValueError,match='alignment'):evidence_metrics(g,p,alignment_verified=False)
    with pytest.raises(ValueError,match='Contradictory'):
        evidence_metrics(g,{'a':{'status':'failed','label':'MATCH'}},alignment_verified=True)


def test_all_failed_three_class_support_gives_zero_macro_not_perfect():
    g={'a':'MATCH','b':'PARTIAL','c':'NO_MATCH'}
    r=evidence_metrics(g,{},alignment_verified=True)
    assert r['macro_f1']==0 and r['coverage']['value']==0
    assert [r['per_class'][x]['fn'] for x in ('MATCH','PARTIAL','NO_MATCH')]==[1,1,1]
    assert all(r['per_class'][x]['precision'] is None and r['per_class'][x]['f1']==0 for x in g.values())


def test_aggregate_support_is_required_not_each_pair():
    p1=evidence_metrics({'p1a':'MATCH','p1b':'PARTIAL'},{'p1a':'MATCH'},alignment_verified=True)
    assert p1['macro_f1'] is None and not p1['class_support_complete']
    aggregate=evidence_metrics({'p1a':'MATCH','p1b':'PARTIAL','p2a':'NO_MATCH'},
        {'p1a':'MATCH','p2a':'NO_MATCH'},alignment_verified=True)
    assert aggregate['class_support_complete'] and aggregate['macro_f1']==pytest.approx((1+0+1)/3)


def aligned():
    return {'human_verified':True,'gold_unit_ids':['g1','g2'],'model_unit_ids':['m1','m2'],'rows':[
        {'gold_ids':['g1'],'model_ids':['m2'],'status':'verified','semantic_equivalent':True},
        {'gold_ids':['g2'],'model_ids':[],'status':'verified','semantic_equivalent':False},
        {'gold_ids':[],'model_ids':['m1'],'status':'verified','semantic_equivalent':False}]}


def test_extraction_f1_requires_completeness_and_verified_alignment():
    a=aligned();r=extraction_metrics(a,reference_complete=True)
    assert (r['tp'],r['fp'],r['fn'])==(1,1,1) and r['f1']['value']==.5
    with pytest.raises(ValueError):extraction_metrics(a,reference_complete=False)
    a['human_verified']=False
    with pytest.raises(ValueError):extraction_metrics(a,reference_complete=True)
    a=aligned();a['rows'][0]['gold_ids'].append('g3')
    with pytest.raises(ValueError,match='omits or invents'):extraction_metrics(a,reference_complete=True)
    a=aligned();a['rows'].append(a['rows'][0])
    with pytest.raises(ValueError,match='Duplicate'):extraction_metrics(a,reference_complete=True)
    a=aligned();a['gold_unit_ids'].append('g3')
    with pytest.raises(ValueError,match='omits'):extraction_metrics(a,reference_complete=True)


def test_strict_split_and_merge_count_independently_assessable_units():
    # One model unit merged two gold obligations; one gold obligation was
    # split into two model units. Neither relation is multiple true positives.
    a={'human_verified':True,'gold_unit_ids':['g1','g2','g3','g4'],
       'model_unit_ids':['m1','m2','m3','m4'],'rows':[
           {'gold_ids':['g1','g2'],'model_ids':['m1'],'status':'verified','semantic_equivalent':True},
           {'gold_ids':['g3'],'model_ids':['m2','m3'],'status':'verified','semantic_equivalent':True},
           {'gold_ids':['g4'],'model_ids':['m4'],'status':'verified','semantic_equivalent':True}]}
    result=extraction_metrics(a,reference_complete=True)
    assert (result['tp'],result['fp'],result['fn'],result['split_merge_relations'])==(1,3,3,2)
    assert result['f1']['value']==.25
    a['human_verified']=False
    with pytest.raises(ValueError,match='verified semantic alignment'):
        extraction_metrics(a,reference_complete=True)


def test_complex_many_to_many_alignment_remains_unavailable():
    a={'human_verified':True,'gold_unit_ids':['g1','g2'],
       'model_unit_ids':['m1','m2'],'rows':[
           {'gold_ids':['g1','g2'],'model_ids':['m1','m2'],
            'status':'verified','semantic_equivalent':True}]}
    with pytest.raises(ValueError,match='many-to-many'):
        extraction_metrics(a,reference_complete=True)


def test_cost_and_latency_keep_failed_and_cached_runs_separate():
    rows=[dict(cost_usd=.01,latency_ms=x,ok=(x!=300),cached=False) for x in [100,200,300]]
    rows += [dict(cost_usd=0,latency_ms=4,cached=True),dict(cost_usd=.01,latency_ms=None,cached=False)]
    r=operational_summary(rows)
    assert r['live']['cost_usd']==.04 and r['live']['p95_ms']==300
    assert r['live']['latency_missing']==1 and r['live']['failures']==1
    assert r['cached']['p50_ms']==4


def runs():
    ids=['a'+str(i) for i in range(30)]
    base=dict(cv_id='CV1',split='development',execution_kind='fake_client',ranking=ids,
              eligible_ids=ids,development_ids=ids,filters={'role':None},split_sha256='s',
              cv_sha256='cv',corpus_sha256='jobs',judgments_sha256='labels',ranking_exhaustive=False)
    return [dict(base,method='B0'),dict(base,method='dense')]


@pytest.mark.parametrize('field,value',[('filters',{'role':'DS'}),('cv_sha256','changed'),
    ('judgments_sha256','other'),('eligible_ids',['a0']),('execution_kind','live_model'),('cv_id','CV3')])
def test_unfair_or_heldout_comparisons_are_blocked(field,value):
    r=deepcopy(runs());r[1][field]=value
    with pytest.raises(ValueError):validate_comparable(r)


def test_contract_approval_alone_does_not_unlock_reference_readiness():
    r=compare_rankings(runs(),{'CV1':{'a0':3}},readiness={'status':'ready'},contract=RECEIPT)
    assert r['status']=='blocked' and r['metrics'] is None and r['winner'] is None
    stale=deepcopy(RECEIPT);stale['source_sha256']='changed'
    with pytest.raises(ValueError,match='stale'):validate_metric_contract(stale)
    old={'review_status':'approved','ndcg_gain':'linear','short_precision':'observed'}
    with pytest.raises(ValueError,match='D-052'):compare_rankings(runs(),{'CV1':{}},readiness=ready(),contract=old)
    held=ready();held['held_reference_ids']=['CV1/F00022']
    assert compare_rankings(runs(),{'CV1':{}},readiness=held,contract=RECEIPT)['status']=='blocked'
    no_receipt=ready();no_receipt['receipts'].pop('alignment_sha256')
    assert compare_rankings(runs(),{'CV1':{}},readiness=no_receipt,contract=RECEIPT)['status']=='blocked'
    with pytest.raises(ValueError,match='K=10/20/30'):
        compare_rankings(runs(),{'CV1':{}},readiness=ready(),contract=RECEIPT,ks=())


def test_fake_runner_reports_original_rank_diagnostics_not_winner():
    r=compare_rankings(runs(),{'CV1':{'a0':3,'a1':0}},readiness=ready(),contract=RECEIPT)
    assert r['execution_kind']=='fake_client' and len(r['metrics'])==2 and r['winner'] is None
    assert r['primary_publication_blocked_by_unjudged']
    assert r['metrics'][0]['metrics'][0]['precision_at_k']['value'] is None


def test_saved_top20_cannot_be_claimed_as_top30():
    rows=runs()
    for r in rows:r['ranking']=r['ranking'][:20]
    r=compare_rankings(rows,{'CV1':{}},readiness=ready(),contract=RECEIPT)
    assert r['status']=='blocked' and r['metrics'] is None


def llm_runs():
    base=dict(split='development',cv_ids=['CV1'],case_ids=['CV1/A'],execution_kind='fake_client',
              prompt_hashes={'extraction':'prompt'},input_hashes={'CV1':'cv','A':'jd'},
              gold_sha256='gold',guideline_sha256='guide',requirement_hashes={'A':'fixed'},
              attempt_kind='first_attempt',reviewer_assisted=False,alignment_receipt_sha256='receipt',
              alignment_verified=True,complete_reference=True,guideline_compatibility_verified=True,
              evidence_gold={'a':'MATCH','b':'PARTIAL','c':'NO_MATCH'},
              evidence_predictions={'a':'MATCH','b':'PARTIAL','c':'NO_MATCH'},
              extraction_alignments=[aligned()],
              usage_records=[dict(cost_usd=0,latency_ms=10,cached=False,ok=True)])
    return [dict(base,model='baseline'),dict(base,model='candidate')]


def test_llm_comparison_is_offline_and_safety_does_not_follow_from_schema():
    r=compare_llm_artifacts(llm_runs(),readiness=ready(),registered_models={'baseline','candidate'},contract=RECEIPT)
    assert r['metrics'][0]['evidence']['macro_f1']==1
    assert r['metrics'][0]['safety_gate'] is None and r['winner'] is None
    assert r['selection_eligible'] and r['execution_kind']=='fake_client'


@pytest.mark.parametrize('field,value',[('input_hashes',{'CV1':'changed'}),('execution_kind','live_model'),
    ('prompt_hashes',{'extraction':'changed'}),('requirement_hashes',{'A':'other'}),
    ('attempt_kind','automatic_repair')])
def test_llm_comparison_blocks_incomparable_inputs(field,value):
    r=deepcopy(llm_runs());r[1][field]=value
    with pytest.raises(ValueError):compare_llm_artifacts(r,readiness=ready(),contract=RECEIPT,registered_models={'baseline','candidate'})


def test_pending_alignment_and_reference_case_cap_block_metrics():
    r=llm_runs();r[0]['alignment_verified']=False
    result=compare_llm_artifacts(r,readiness=ready(),contract=RECEIPT,registered_models={'baseline','candidate'})
    assert result['metrics'] is None
    r=llm_runs();r[0].update(role='reference',case_ids=list(map(str,range(11))))
    with pytest.raises(ValueError,match='10 cases'):
        compare_llm_artifacts(r,readiness=ready(),contract=RECEIPT,registered_models={'baseline','candidate'})


def test_reviewer_assistance_or_missing_receipt_cannot_be_primary_comparison():
    r=llm_runs();r[0]['reviewer_assisted']=True
    with pytest.raises(ValueError,match='Reviewer assistance'):
        compare_llm_artifacts(r,readiness=ready(),contract=RECEIPT,registered_models={'baseline','candidate'})
    r=llm_runs();r[0]['alignment_receipt_sha256']=None
    result=compare_llm_artifacts(r,readiness=ready(),contract=RECEIPT,registered_models={'baseline','candidate'})
    assert result['status']=='blocked' and result['metrics'] is None
