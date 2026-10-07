from datetime import date
from pathlib import Path
import json
import pytest
from jobfit.cv.parser import ParsedCV
from jobfit.schemas.cv import CVProfile
from jobfit.schemas.requirements import JDExtraction
from jobfit.extraction.cache import ExtractionCache,content_hash
from jobfit.extraction.jd_extractor import extract_jd
from jobfit.eval.fixture_client import FixtureClient
from jobfit.matching.evidence_matcher import match_evidence
from jobfit.llm.budget import BudgetGuard
from jobfit.llm.ledger import UsageLedger

@pytest.mark.parametrize('heading',['Requirements','Qualifications and Requirements','Kualifikasi','Persyaratan','Character'])
def test_populated_heading_without_colon_cannot_be_empty_success(heading):
    c=FixtureClient([{'job_id':'DEV','units':[]}]*2)
    r=extract_jd(heading+'\nPython and SQL experience is mandatory.',job_id='DEV',client=c,model='deepseek-flash')
    assert r.status=='failed' and r.error_code=='empty_extraction_despite_requirement_section' and len(c.calls)==2

@pytest.mark.parametrize('bad',[[],None,{'key':'x'},42,{'scope':'corpus_jd','value':[]}])
def test_malformed_cache_envelope_is_a_miss_not_an_unhandled_crash(tmp_path,bad):
    key=content_hash('key');(tmp_path/f'{key}.json').write_text(json.dumps(bad))
    assert ExtractionCache(tmp_path).get(key,scope='corpus_jd') is None

def test_memory_scope_cannot_return_CV_evidence_as_public_JD(tmp_path):
    key=content_hash('reused explicit key');cache=ExtractionCache(tmp_path)
    cache.put(key,{'private':'CV evidence'},scope='session_evidence')
    assert cache.get(key,scope='corpus_jd') is None
    assert cache.get(key,scope='session_jd') is None
    assert not list(tmp_path.iterdir())
    assert cache.get(key,scope='session_evidence')=={'private':'CV evidence'}
    with pytest.raises(ValueError):cache.put(key,{},scope='unrecognized')

def test_disk_cache_payload_tampering_is_not_reused(tmp_path):
    key=content_hash('public');cache=ExtractionCache(tmp_path);cache.put(key,{'a':'original'},scope='corpus_jd')
    p=tmp_path/f'{key}.json';data=json.loads(p.read_text());data['value']={'a':'changed'};p.write_text(json.dumps(data))
    assert ExtractionCache(tmp_path).get(key,scope='corpus_jd') is None

@pytest.mark.parametrize('v',[float('nan'),float('inf'),-.01,True,'2'])
def test_invalid_duration_bound_never_bypasses_qualified_MATCH(v):
    cv=ParsedCV(profile=CVProfile(cv_id='DEV',raw_text='Python'),analysis_date=date(2026,9,30))
    ex=JDExtraction(job_id='DEV',units=[{'unit_id':'q','text':'Python for 3 years','kind':'qualified','min_years':3,'importance':'required','source_quotes':['Python']}])
    c=FixtureClient([])
    with pytest.raises(ValueError):match_evidence(cv,ex,client=c,model='deepseek-flash',duration_years={'q':v})
    assert not c.calls

@pytest.mark.parametrize('v',[float('nan'),float('inf'),-.01])
def test_invalid_budget_estimate_is_rejected_before_spend(tmp_path,v):
    guard=BudgetGuard(UsageLedger(tmp_path/'unused.jsonl'),cap_usd=9,hard_stop_usd=8.5)
    with pytest.raises(ValueError):guard.check(v)
    assert not (tmp_path/'unused.jsonl').exists()

def test_invalid_ledger_total_cannot_disable_hard_stop(tmp_path,monkeypatch):
    ledger=UsageLedger(tmp_path/'unused.jsonl')
    monkeypatch.setattr(ledger,'total_spent',lambda:float('nan'))
    with pytest.raises(ValueError,match='Ledger total'):
        BudgetGuard(ledger,cap_usd=9,hard_stop_usd=8.5).check(.1)

@pytest.mark.parametrize('ceiling',['nan','inf','-1'])
def test_invalid_batch_approval_cannot_bypass_authorization(monkeypatch,ceiling):
    import scripts.run_batch_extraction as batch
    import sys
    monkeypatch.setattr(sys,'argv',['run_batch_extraction','--run-id','fixture','--execute','--approved-budget-usd',ceiling])
    def must_not_construct(*args,**kwargs):
        pytest.fail('Invalid approval must stop before client construction or file access')
    monkeypatch.setattr(batch,'OpenRouterClient',must_not_construct)
    with pytest.raises(ValueError,match='approval ceiling'):
        batch.main()
