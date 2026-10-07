from decimal import Decimal
import pytest
from jobfit.eval.stage2_remaining_cases import RemainingSession, RUN_ID, V5_ID, V6_ID
from jobfit.llm.ledger import UsageLedger, UsageRecord


def setup_failure(tmp_path, uncertain=False):
    ledger = UsageLedger(tmp_path/'ledger.jsonl')
    session = RemainingSession(tmp_path/'state.json',run_id=RUN_ID,fingerprint='fixed',
        jobs=['model/J1','model/J2'],ledger=ledger,ceiling='3.16')
    session.begin('model/J1')
    ledger.append(UsageRecord(run_id=RUN_ID, task='jd_extraction', model='model',
        cost_usd=.02, cost_source='uncertain_upper_bound' if uncertain else 'reported'))
    session.data['stage_attempts']={'model/J1':1}
    session.finish({'job_id':'model/J1','result_sha256':'exact','status':'failed','error_code':'BadRequestError'})
    check=dict(job_id='model/J1',result_sha256='exact',error_code='BadRequestError',
        disposition='retain_failed_case_no_retry',notes='Rejected repair; retain the failed outcome.',checked_by='QA check')
    return session,ledger,check


def test_settled_failure_requires_receipt_then_next_case_only(tmp_path):
    session,_,check=setup_failure(tmp_path)
    assert session.data['status']=='stopped_process_failure'
    with pytest.raises(ValueError):session.begin('model/J2')
    session.record_check(check)
    assert session.data['status']=='ready'
    assert session.data['results'][0]['status']=='failed'
    assert session.data['results'][0]['operational_check']['human_annotation_approval'] is False
    with pytest.raises(ValueError):session.begin('model/J1')
    session.begin('model/J2')


@pytest.mark.parametrize('change',[{'result_sha256':'wrong'},{'error_code':'wrong'},{'disposition':'retry'}])
def test_wrong_failure_receipt_cannot_release_gate(tmp_path,change):
    session,_,check=setup_failure(tmp_path);check.update(change)
    with pytest.raises(ValueError):session.record_check(check)
    assert session.data['status']=='stopped_process_failure'


@pytest.mark.parametrize('uncertain,reserved',[(True,False),(False,True)])
def test_uncertain_or_reserved_failure_still_stops(tmp_path,uncertain,reserved):
    session,_,check=setup_failure(tmp_path,uncertain)
    if reserved:session.data['reservations']=[{'upper_usd':.02}]
    with pytest.raises(ValueError):session.record_check(check)
    assert session.data['status']=='stopped_process_failure'


def test_all_three_versions_count_toward_same_cap(tmp_path):
    session,ledger,_=setup_failure(tmp_path)
    for run in (V5_ID,V6_ID):
        ledger.append(UsageRecord(run_id=run,task='jd_extraction',model='model',cost_usd=.4,cost_source='reported'))
    assert session.spent()==Decimal('.82')
    from jobfit.llm.budget import BudgetExceeded
    with pytest.raises(BudgetExceeded):session.check_budget(2.35)
