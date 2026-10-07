from dataclasses import replace
from types import SimpleNamespace
import pytest
from jobfit.config import Settings
from jobfit.extraction.jd_extractor import extract_jd
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.ledger import UsageRecord
from jobfit.llm.probe import ProbeClient, ProbeSession
from jobfit.llm.budget import BudgetExceeded

def setup(tmp_path, responses, cost=.005, hard_stop=8.5):
    calls=[]
    def create(**kw):
        calls.append(kw)
        content=responses.pop(0)
        return SimpleNamespace(model='deepseek/deepseek-v4.1-flash',id='fake',
            usage=SimpleNamespace(prompt_tokens=100,completion_tokens=100,cost=cost),
            choices=[SimpleNamespace(finish_reason='stop',message=SimpleNamespace(content=content))])
    sdk=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    c=OpenRouterClient(replace(Settings(),usage_ledger=tmp_path/'ledger.jsonl',api_budget_usd=9,api_hard_stop_usd=hard_stop),sdk_client=sdk,run_id='fixed_probe')
    s=ProbeSession(tmp_path/'state.json',run_id=c.run_id,fingerprint='fixed',jobs=['A','B','C'],ledger=c.ledger)
    return c,s,calls

VALID='{"job_id":"A","units":[{"unit_id":"u","text":"Python","importance":"required","source_quotes":["Python"]}]}'

def test_one_repair_counts_and_next_job_requires_semantic_check(tmp_path):
    c,s,calls=setup(tmp_path,['{"job_id":"wrong","units":[]}',VALID])
    s.check_budget(.19);s.begin('A')
    r=extract_jd('Python',job_id='A',client=ProbeClient(c,s),model='deepseek-flash')
    assert r.status=='done' and r.attempts==2 and len(calls)==2
    assert str(s.spent())=='0.010' and not s.data['reservations']
    s.finish({'job_id':'A','status':'done','result_sha256':'hash'})
    resumed=ProbeSession(s.path,run_id=c.run_id,fingerprint='fixed',jobs=['A','B','C'],ledger=c.ledger)
    with pytest.raises(ValueError):resumed.begin('B')
    resumed.record_check({'job_id':'A','result_sha256':'hash','checked_by':'execution-role','notes':'Merged required concepts.',
        'checks':{'quotes':'pass','coverage':'pass','grouping':'fail','qualifiers':'pass','importance':'pass'}})
    assert resumed.data['status']=='stopped_semantic_issue'
    assert resumed.data['results'][0]['operational_check']['human_annotation_approval'] is False
    with pytest.raises(ValueError):resumed.begin('B')

def test_ceiling_persists_across_resume_and_project_guard_also_applies(tmp_path):
    c,s,calls=setup(tmp_path,[VALID]);c.ledger.append(UsageRecord(run_id=c.run_id,task='prior',model='m',cost_usd=.195))
    resumed=ProbeSession(s.path,run_id=c.run_id,fingerprint='fixed',jobs=['A','B','C'],ledger=c.ledger)
    with pytest.raises(BudgetExceeded):resumed.check_budget(.006)
    resumed.begin('A')
    r=extract_jd('Python',job_id='A',client=ProbeClient(c,resumed),model='deepseek-flash')
    assert r.status=='failed' and r.error_code=='BudgetExceeded' and not calls
    resumed.finish({'job_id':'A','status':'failed','result_sha256':'hash'})
    with pytest.raises(ValueError):resumed.begin('B')

def test_project_hard_stop_cannot_be_replaced_by_probe_cap(tmp_path):
    c,s,calls=setup(tmp_path,[VALID],hard_stop=0)
    s.begin('A');r=extract_jd('Python',job_id='A',client=ProbeClient(c,s),model='deepseek-flash')
    assert r.error_code=='BudgetExceeded' and not calls

def test_config_changes_and_orphan_receipts_cannot_reset_budget(tmp_path):
    c,s,_=setup(tmp_path,[])
    with pytest.raises(ValueError,match='identity'):
        ProbeSession(s.path,run_id=c.run_id,fingerprint='changed',jobs=['A','B','C'],ledger=c.ledger)
    c.ledger.append(UsageRecord(run_id=c.run_id,task='prior',model='m',cost_usd=.01))
    with pytest.raises(ValueError,match='without state'):
        ProbeSession(tmp_path/'different.json',run_id=c.run_id,fingerprint='fixed',jobs=['A','B','C'],ledger=c.ledger)

def test_uncertain_attempt_reservation_survives_restart(tmp_path,monkeypatch):
    c,s,calls=setup(tmp_path,[VALID]);s.begin('A')
    def interrupted(*a,**kw):raise RuntimeError('no durable receipt')
    monkeypatch.setattr(c,'chat_structured',interrupted)
    r=extract_jd('Python',job_id='A',client=ProbeClient(c,s),model='deepseek-flash')
    assert r.status=='failed' and s.data['reservations']
    resumed=ProbeSession(s.path,run_id=c.run_id,fingerprint='fixed',jobs=['A','B','C'],ledger=c.ledger)
    with pytest.raises(BudgetExceeded,match='Unsettled'):resumed.check_budget(0)

def test_order_and_exact_result_check_are_required(tmp_path):
    c,s,_=setup(tmp_path,[])
    with pytest.raises(ValueError):s.begin('B')
    s.begin('A');s.finish({'job_id':'A','status':'done','result_sha256':'real'})
    with pytest.raises(ValueError,match='exact result'):s.record_check({'job_id':'A','result_sha256':'stale'})

@pytest.mark.parametrize('cap',['.21','NaN','-1'])
def test_probe_cannot_increase_approved_cap(tmp_path,cap):
    c,s,_=setup(tmp_path,[])
    with pytest.raises(ValueError):ProbeSession(s.path,run_id=c.run_id,fingerprint='fixed',jobs=['A','B','C'],ledger=c.ledger,ceiling=cap)
