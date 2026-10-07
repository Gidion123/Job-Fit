import pytest
from test_closure_probe import session
from jobfit.llm.semantic_repair import SemanticRepairSession
from jobfit.llm.closure_probe import ClosureProbeClient
from jobfit.schemas.requirements import JDExtraction


def ready(tmp_path):
 c,s,calls=session(tmp_path);s.begin('A');ClosureProbeClient(c,s).chat_structured('deepseek-flash',[],JDExtraction,'extract')
 s.finish({'job_id':'A','status':'done','result_sha256':'first'})
 r=SemanticRepairSession(s.path,run_id=c.run_id,fingerprint='new',jobs=['A','B'],ledger=c.ledger,ceiling='.40')
 return c,r,calls


def test_semantic_repair_preserves_first_output_counts_and_budget(tmp_path):
 c,s,calls=ready(tmp_path);before=s.spent()
 s.begin_repair({'job_id':'A','result_sha256':'first','corrections':['source-grounded fix']},'extensionhash')
 ClosureProbeClient(c,s).chat_structured('deepseek-flash',[],JDExtraction,'repair')
 s.finish_repair({'job_id':'A','status':'done','result_sha256':'second'})
 assert s.data['prior_stage_results'][0]['result_sha256']=='first'
 assert len(s.data['results'])==1 and s.data['results'][0]['result_sha256']=='second'
 assert len(calls)==2 and s.data['stage_attempts']['A']==2 and s.spent()>before
 with pytest.raises(ValueError):s.begin_repair({'job_id':'A','result_sha256':'second','corrections':['more']},'hash')


def test_terminal_semantic_failure_cannot_be_reopened(tmp_path):
 c,s,calls=ready(tmp_path)
 s.record_check({'job_id':'A','result_sha256':'first','checked_by':'review','notes':'failure','checks':{k:'fail' for k in ['quotes','coverage','grouping','qualifiers','importance']}})
 with pytest.raises(ValueError):s.begin_repair({'job_id':'A','result_sha256':'first','corrections':['fix']},'hash')
 assert len(calls)==1
