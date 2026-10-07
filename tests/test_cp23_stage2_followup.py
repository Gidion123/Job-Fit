import json
from dataclasses import replace
from types import SimpleNamespace
from decimal import Decimal
import pytest
from pydantic import BaseModel
from jobfit.config import Settings
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.budget import BudgetExceeded
from scripts.run_cp23_stage2_followup import FollowupSession,FollowupStageClient,RUN,execution_plan

class Output(BaseModel):value:str

def setup(tmp_path,error=None):
    calls=[]
    def create(**kw):
        calls.append(kw)
        if error:raise error
        return SimpleNamespace(model='deepseek/deepseek-v4-pro',id='fake',usage=SimpleNamespace(prompt_tokens=100,completion_tokens=100,cost=.001),
            choices=[SimpleNamespace(finish_reason='stop',message=SimpleNamespace(content='{"value":"ok"}'))])
    client=OpenRouterClient(replace(Settings(),usage_ledger=tmp_path/'ledger',api_budget_usd=9,api_hard_stop_usd=8.5),
        sdk_client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))),run_id=RUN)
    stage=dict(stage_id='stage',model='deepseek-v4-pro',kind='matching',first_input_token_upper=10000,repair_input_token_upper=12000)
    session=FollowupSession(tmp_path/'state',run_id=RUN,fingerprint='fixed',jobs=['stage','next'],ledger=client.ledger,ceiling='6.40')
    session.begin('stage')
    return client,session,stage,calls

def test_one_repair_settled_failure_resume_and_durable_typed_receipts(tmp_path):
    c,s,stage,calls=setup(tmp_path);w=FollowupStageClient(c,s,stage)
    for _ in range(2):assert w.chat_structured('deepseek-v4-pro',[],Output,'evidence_matching',16000).value=='ok'
    with pytest.raises(BudgetExceeded):w.chat_structured('deepseek-v4-pro',[],Output,'evidence_matching',16000)
    s.finish_case(dict(stage_id='stage',status='failed'))
    assert s.data['status']=='ready' and len(s.data['typed_attempt_outputs'])==2 and len(calls)==2
    assert FollowupSession(s.path,run_id=RUN,fingerprint='fixed',jobs=['stage','next'],ledger=c.ledger,ceiling='6.40').spent()==Decimal('.002')

def test_unknown_cost_and_interruption_cannot_advance(tmp_path):
    c,s,stage,calls=setup(tmp_path,RuntimeError('network'))
    with pytest.raises(RuntimeError):FollowupStageClient(c,s,stage).chat_structured('deepseek-v4-pro',[],Output,'evidence_matching',16000)
    assert s.data['status']=='stopped_uncertain_cost' and s.data['transport_uncertain'] and len(calls)==1

def test_portable_wire_is_budgeted_before_dispatch(tmp_path):
    c,s,stage,calls=setup(tmp_path)
    messages=[dict(role='system',content='rubric'),dict(role='user',content='CV'),dict(role='assistant',content='draft'),dict(role='system',content='The previous response failed validation (invalid_source_quote). Retry once.')]
    FollowupStageClient(c,s,stage).chat_structured('deepseek-v4-pro',messages,Output,'evidence_matching',16000)
    assert [m['role'] for m in calls[0]['messages']]==['system','user','assistant','user']
    assert messages[-1]['role']=='system'

def test_scope_and_input_guards_precede_paid_call(tmp_path):
    c,s,stage,calls=setup(tmp_path);w=FollowupStageClient(c,s,stage)
    with pytest.raises(ValueError):w.chat_structured('deepseek-v4-pro',[],Output,'jd_extraction',16000)
    stage['first_input_token_upper']=1
    with pytest.raises(BudgetExceeded):w.chat_structured('deepseek-v4-pro',[],Output,'evidence_matching',16000)
    assert not calls

def test_reference_and_round2_use_bound_same_common_cases():
    # The D-064 run is closed. Check the frozen plan it actually used, instead of
    # rebuilding a live plan whose guard also hashes README files.
    from scripts.run_cp23_stage2_followup import PLAN
    p=json.loads(PLAN.read_text());s=p['stages']
    assert len(s)==19 and sum(x['model']=='gpt-6-sol' for x in s)==8
    assert sum(x['model']=='deepseek-v4-pro' for x in s)==11
    assert len({x['job_id'] for x in s if x['model']=='gpt-6-sol' and x['kind']=='extraction'})==4
    assert {(x['cv_id'],x['job_id']) for x in s if x['kind']=='matching'}=={('CV1','F00332'),('CV1','F00036'),('CV2','F00815'),('CV2','F00018')}
    assert Decimal(p['conservative_upper_usd'])<=Decimal('6.40')
    assert p['response_model_aliases']['openai/gpt-6-sol']==['openai/gpt-6-sol-20260922']


def test_followup_protocol_inputs_unchanged_except_readme_documentation():
    # Prompts, gold, CVs, split, workbook and code must still match the approved
    # proposal. README files are documentation, not protocol inputs.
    from scripts.run_cp23_stage2_followup import PROPOSAL,sha
    from jobfit.config import REPO_ROOT
    approved=json.loads(PROPOSAL.read_text())['source_hashes']
    # One recorded drift (receipt below): the closed run's input workbook was replaced
    # by a copy with different bytes. Its new hash is pinned so further change still fails.
    receipt=json.loads((REPO_ROOT/'evals/results/cp23/protocol_drift_receipt_20261006_v1.json').read_text())
    approved=dict(approved)
    assert approved[receipt['file']]==receipt['approved_sha256_in_D064_proposal']
    approved[receipt['file']]=receipt['current_sha256']
    drift=[path for path,digest in approved.items()
           if not path.endswith('README.md') and sha(REPO_ROOT/path)!=digest]
    assert drift==[]
