"""A failed model case remains visible; new paid scope cannot inherit old approval."""
from decimal import Decimal
import importlib.util
import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from jobfit.config import REPO_ROOT
from jobfit.eval import stage2_continuation as continuation
from jobfit.llm.budget import BudgetGuard
from jobfit.llm.ledger import UsageLedger, UsageRecord
from jobfit.llm.pricing import load_prices


spec=importlib.util.spec_from_file_location('continuation_cli',REPO_ROOT/'scripts/run_cp23_stage2_continuation.py')
cli=importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


def sources():
    from scripts.run_batch_extraction import development_sources
    cases=json.loads((REPO_ROOT/'evals/results/cp23_stage1_case_candidates_20261003_v4.json').read_text())
    return {r['job_id']:r['text'] for r in development_sources([x['job_id'] for x in cases['cases']])}


def test_continuation_excludes_paid_failed_case_and_keeps_same_protocol():
    plan=continuation.build_continuation_plan(REPO_ROOT,sources())
    assert plan['stage_count']==27 and plan['maximum_calls_including_repairs']==54
    assert plan['prior_case']['stage_id']=='deepseek-flash/F00332'
    assert plan['stages'][0]['stage_id']=='deepseek-flash/F00036'
    assert len({s['stage_id'] for s in plan['stages']})==27
    assert Decimal(plan['conservative_upper_usd'])==Decimal('3.1559888')
    assert plan['no_candidate_winner'] and plan['paid_approval_required']


def test_changed_source_or_prior_semantic_receipt_blocks_continuation(monkeypatch,tmp_path):
    source=sources();source['F00332']+=' altered'
    with pytest.raises(ValueError,match='source changed'):
        continuation.build_continuation_plan(REPO_ROOT,source)
    old=json.loads((REPO_ROOT/continuation.V4_CHECK).read_text())
    old['checks']['coverage']='pass'
    altered=tmp_path/'altered-check.json';altered.write_text(json.dumps(old))
    monkeypatch.setattr(continuation,'V4_CHECK',str(altered))
    with pytest.raises(ValueError,match='durable semantic check differs'):
        continuation.build_continuation_plan(REPO_ROOT,sources())


def test_approval_cannot_reuse_v4_scope_or_undercut_bound(tmp_path):
    plan=continuation.build_continuation_plan(REPO_ROOT,sources())
    receipt={'decision':'approved','approved_by':'Dion','scope':'cp23_stage2_round1_extraction_20261003_v4',
             'plan_sha256':'a'*64,'aggregate_cap_usd':'3.16'}
    p=tmp_path/'receipt.json';p.write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='Distinct continuation approval'):
        cli.approved_receipt(p,plan,'a'*64)
    receipt['scope']=cli.RUN_ID;receipt['aggregate_cap_usd']='3.15';p.write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='cannot cover'):
        cli.approved_receipt(p,plan,'a'*64)
    receipt['aggregate_cap_usd']='3.16';p.write_text(json.dumps(receipt))
    assert cli.approved_receipt(p,plan,'a'*64)==Decimal('3.16')
    receipt['aggregate_cap_usd']='3.17';p.write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='cannot cover'):
        cli.approved_receipt(p,plan,'a'*64)


def test_semantic_failure_is_recorded_and_next_stage_can_start(tmp_path):
    ledger=UsageLedger(tmp_path/'ledger.jsonl')
    session=continuation.Stage2ComparisonSession(tmp_path/'state.json',run_id='fake-continuation',
        fingerprint='fixed',jobs=['m/J1','m/J2'],ledger=ledger,ceiling='0.20')
    session.begin('m/J1')
    session.finish({'job_id':'m/J1','status':'done','result_sha256':'first'})
    session.record_check({'job_id':'m/J1','result_sha256':'first',
        'checks':{'quotes':'pass','coverage':'fail','grouping':'pass','qualifiers':'pass','importance':'pass'},
        'notes':'A real source obligation is missing.','checked_by':'delegated_source_QA'})
    assert session.data['status']=='ready'
    assert session.data['semantic_failures']==['m/J1']
    assert session.data['results'][0]['operational_check']['alignment_status']=='pending'
    session.begin('m/J2')
    session.finish({'job_id':'m/J2','status':'done','result_sha256':'second'})
    session.record_check({'job_id':'m/J2','result_sha256':'second',
        'checks':{'quotes':'pass','coverage':'pass','grouping':'pass','qualifiers':'pass','importance':'pass'},
        'notes':'Checked against the complete synthetic source.','checked_by':'delegated_source_QA'})
    assert session.data['status']=='complete'
    assert session.data['semantic_failures']==['m/J1']


class TinyOutput(BaseModel):
    value:int


class FakeClient:
    run_id='fake-continuation'
    def __init__(self,ledger):
        self.ledger=ledger
        self.prices=load_prices(REPO_ROOT/'config/models_v1.yaml')
        self.guard=BudgetGuard(ledger,cap_usd=1.0,hard_stop_usd=1.0)
    def chat_structured(self,model,messages,output_model,task,max_tokens=2000,temperature=0):
        self.ledger.append(UsageRecord(run_id=self.run_id,task=task,model=model,
                                       cost_usd=0.001,cost_source='reported'))
        return TinyOutput(value=7)


def test_typed_first_attempt_is_durable_before_downstream_validation(tmp_path):
    ledger=UsageLedger(tmp_path/'ledger.jsonl')
    stage={'stage_id':'deepseek-flash/J1','first_input_token_upper':2000,
           'repair_input_token_upper':2500}
    session=continuation.Stage2ComparisonSession(tmp_path/'state.json',run_id='fake-continuation',
        fingerprint='fixed',jobs=[stage['stage_id']],ledger=ledger,ceiling='0.20')
    session.begin(stage['stage_id'])
    client=continuation.Stage2ComparisonClient(FakeClient(ledger),session,stage)
    out=client.chat_structured('deepseek-flash',[{'role':'user','content':'fictional fixture'}],
                               TinyOutput,'jd_extraction')
    assert out.value==7
    persisted=json.loads((tmp_path/'state.json').read_text())
    assert persisted['typed_attempt_outputs'][0]['attempt']==1
    assert persisted['typed_attempt_outputs'][0]['output']=={'value':7}
    assert persisted['typed_attempt_outputs'][0]['status']=='typed_draft_not_source_approved'
    assert len(ledger.records())==1
