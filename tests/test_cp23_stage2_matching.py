import json
from dataclasses import replace
from types import SimpleNamespace
import pytest
from pydantic import BaseModel
from jobfit.config import Settings
from jobfit.eval.stage2_matching import MatchingClient, MatchingSession, require_approval, sha
from jobfit.llm.budget import BudgetExceeded
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.ledger import UsageRecord

class Output(BaseModel):
    value: str

def setup(tmp_path, error=None):
    calls=[]
    def create(**kw):
        calls.append(kw)
        if error: raise error
        return SimpleNamespace(model='deepseek/deepseek-v4.1-flash',id='fake',
            usage=SimpleNamespace(prompt_tokens=100,completion_tokens=100,cost=.001),
            choices=[SimpleNamespace(finish_reason='stop',message=SimpleNamespace(content='{"value":"ok"}'))])
    c=OpenRouterClient(replace(Settings(),usage_ledger=tmp_path/'ledger',api_budget_usd=9,api_hard_stop_usd=8.5),
        sdk_client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))),run_id='matching')
    stage=dict(stage_id='deepseek-flash/CV1/A',model='deepseek-flash',first_input_token_upper=10000,
        repair_input_token_upper=12000,output_token_upper_per_attempt=16000)
    s=MatchingSession(tmp_path/'state',run_id='matching',fingerprint='fixed',jobs=[stage['stage_id'],'next'],ledger=c.ledger,ceiling='1.85')
    s.begin(stage['stage_id'])
    return c,s,stage,calls

def call(c,s,stage):
    return MatchingClient(c,s,stage).chat_structured('deepseek-flash',[],Output,'evidence_matching',16000)

def test_attempt_limit_typed_outputs_and_resume(tmp_path):
    c,s,stage,calls=setup(tmp_path)
    assert call(c,s,stage).value=='ok'
    assert call(c,s,stage).value=='ok'
    with pytest.raises(BudgetExceeded): call(c,s,stage)
    assert len(calls)==2 and len(s.data['typed_attempt_outputs'])==2
    s.finish_matching(dict(stage_id=stage['stage_id'],status='failed'))
    assert s.data['status']=='ready'  # failure retained, not repeated or NO_MATCH
    restored=MatchingSession(s.path,run_id='matching',fingerprint='fixed',jobs=s.data['jobs'],ledger=c.ledger,ceiling='1.85')
    assert len(restored.data['results'])==1 and restored.spent()==s.spent()

def test_unknown_cost_prevents_repair_and_advance(tmp_path):
    c,s,stage,calls=setup(tmp_path,RuntimeError('network'))
    with pytest.raises(RuntimeError):call(c,s,stage)
    assert s.data['transport_uncertain'] and s.data['status']=='stopped_uncertain_cost'
    with pytest.raises(BudgetExceeded):call(c,s,stage)
    assert len(calls)==1

def test_orphan_call_no_receipt_reservation_stops(tmp_path,monkeypatch):
    c,s,stage,_=setup(tmp_path)
    def crash(*a,**kw): raise RuntimeError('interrupted')
    monkeypatch.setattr(c,'chat_structured',crash)
    with pytest.raises(RuntimeError):call(c,s,stage)
    assert s.data['reservations'] and s.data['transport_uncertain']

@pytest.mark.parametrize('change',[{'model':'gpt-6-luna'},{'task':'jd_extraction'},{'max_tokens':10},{'temperature':1}])
def test_request_scope_cannot_change(tmp_path,change):
    c,s,stage,calls=setup(tmp_path)
    args=dict(model='deepseek-flash',messages=[],output_model=Output,task='evidence_matching',max_tokens=16000,temperature=0)
    args.update(change)
    with pytest.raises((ValueError,BudgetExceeded)):MatchingClient(c,s,stage).chat_structured(**args)
    assert not calls

def test_aggregate_cost_and_input_guard(tmp_path):
    c,s,stage,calls=setup(tmp_path)
    c.ledger.append(UsageRecord(run_id='matching',task='prior',model='m',cost_usd=1.84999))
    with pytest.raises(BudgetExceeded):call(c,s,stage)
    stage['first_input_token_upper']=1
    with pytest.raises(BudgetExceeded):call(c,s,stage)
    assert not calls

def test_exact_approval_not_generic_ceiling(tmp_path):
    p=tmp_path/'plan';p.write_text('original');r=tmp_path/'receipt'
    r.write_text(json.dumps(dict(approved_by='Dion',plan_sha256=sha(p),ceiling_usd='1.85')))
    require_approval(p,r)
    p.write_text('changed')
    with pytest.raises(ValueError):require_approval(p,r)

def test_offline_real_plan_is_fixed_and_answers_absent():
    from scripts.run_cp23_stage2_matching import plan, inputs
    p=plan()
    assert p['stage_count']==16 and p['maximum_calls_including_repairs']==32
    assert float(p['conservative_upper_usd'])<=1.85
    assert p['gold_CV_answers_in_payload'] is False
    for stage in p['stages']:
        cv,ex=inputs(stage)
        assert cv.profile.is_synthetic and cv.profile.cv_id in ['CV1','CV2']
        assert len(ex.units)==stage['logical_units']
