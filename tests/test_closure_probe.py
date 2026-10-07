from pathlib import Path
from types import SimpleNamespace as NS
from decimal import Decimal
import pytest
from test_pilot_probe import setup, VALID
from jobfit.llm.closure_probe import ClosureProbeSession,ClosureProbeClient
from jobfit.llm.budget import BudgetExceeded
from jobfit.llm.ledger import UsageRecord
from jobfit.schemas.requirements import JDExtraction

def session(tmp_path):
 c,_,calls=setup(tmp_path,[VALID,VALID,VALID])
 s=ClosureProbeSession(tmp_path/'closure.json',run_id=c.run_id,fingerprint='new',jobs=['A','B'],ledger=c.ledger,ceiling='.40')
 return c,s,calls

def test_cap_resume_and_eight_calls(tmp_path):
 c,s,calls=session(tmp_path)
 c.ledger.append(UsageRecord(run_id=c.run_id,task='previous',model='m',cost_usd=.395,cost_source='uncertain_upper_bound'))
 again=ClosureProbeSession(s.path,run_id=c.run_id,fingerprint='new',jobs=['A','B'],ledger=c.ledger,ceiling='.40')
 with pytest.raises(BudgetExceeded):again.check_budget(.006)
 assert again.spent()==Decimal('.395')
 with pytest.raises(ValueError):ClosureProbeSession(s.path,run_id=c.run_id,fingerprint='new',jobs=['A','B'],ledger=c.ledger,ceiling='.41')

def test_attempt_limit_includes_repairs_across_resume(tmp_path):
 c,s,calls=session(tmp_path);s.begin('A');w=ClosureProbeClient(c,s)
 for _ in range(2):w.chat_structured('deepseek-flash',[],JDExtraction,'jd_extraction',max_tokens=16000)
 with pytest.raises(BudgetExceeded):w.chat_structured('deepseek-flash',[],JDExtraction,'jd_extraction')
 assert len(calls)==2
 assert calls[0]['extra_body']['provider']['data_collection']=='deny'
 assert calls[0]['extra_body']['provider']['require_parameters'] is True
 assert not s.data['reservations']

def test_input_limit_and_total_limit_make_zero_dispatch(tmp_path):
 c,s,calls=session(tmp_path);s.begin('A');w=ClosureProbeClient(c,s)
 with pytest.raises(BudgetExceeded):w.chat_structured('deepseek-flash',[{'role':'user','content':'x'*100001}],JDExtraction,'jd_extraction')
 s.data['stage_attempts']={'previous':8}
 with pytest.raises(BudgetExceeded):w.chat_structured('deepseek-flash',[],JDExtraction,'jd_extraction')
 assert not calls

def test_crash_reservation_cannot_be_retried(tmp_path,monkeypatch):
 c,s,_=session(tmp_path);s.begin('A')
 def crash(*a,**k):raise KeyboardInterrupt()
 monkeypatch.setattr(c,'chat_structured',crash)
 with pytest.raises(KeyboardInterrupt):ClosureProbeClient(c,s).chat_structured('deepseek-flash',[],JDExtraction,'jd_extraction')
 assert s.data['reservations']
 with pytest.raises(BudgetExceeded):s.check_budget(0)
