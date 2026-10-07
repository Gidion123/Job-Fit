import json
from pathlib import Path
import pytest
from jobfit.extraction.audited import ExtractionSpec,qualification_inventory
from jobfit.extraction.jd_extractor import extract_jd
from jobfit.extraction.cache import ExtractionCache
from jobfit.eval.fixture_client import FixtureClient
ROOT=Path(__file__).resolve().parents[1]
SPEC=ExtractionSpec(ROOT/'prompts/jd_extraction_v1_3.md','jd-prompt-v1.3')
TEXT='Qualifications\n- Python\n- SQL'

def response(p):
 return {'job_id':p['job_id'],'units':[{'unit_id':'u'+str(i),'text':word,'importance':'required','field':'skill_tool','source_quotes':[word]} for i,word in enumerate(['Python','SQL'])],
         'qualification_coverage':[{'source_id':'Q01','unit_ids':['u0']},{'source_id':'Q02','unit_ids':['u1']}]}


def test_coverage_contract_preserves_units_and_cache_isolated(tmp_path):
 c=FixtureClient([response]);cache=ExtractionCache(tmp_path)
 r=extract_jd(TEXT,job_id='X',client=c,model='deepseek-flash',spec=SPEC,cache=cache,scope='corpus_jd')
 assert r.status=='done' and r.coverage['inventory_count']==2 and len(r.extraction.units)==2
 assert r.extraction.extractor_version=='jd-prompt-v1.3/deepseek-flash'
 assert 'qualification_coverage' not in r.extraction.model_dump()
 again=extract_jd(TEXT,job_id='X',client=FixtureClient([]),model='deepseek-flash',spec=SPEC,cache=cache,scope='corpus_jd')
 assert again.cache_hit and again.coverage==r.coverage
 legacy=extract_jd(TEXT,job_id='X',client=FixtureClient([response]),model='deepseek-flash',cache=cache,scope='corpus_jd')
 assert not legacy.cache_hit and legacy.key!=r.key

@pytest.mark.parametrize('mode',['missing','unsupported','invented_id'])
def test_invalid_inventory_gets_one_repair_then_failure(mode):
 def bad(p):
  r=response(p)
  if mode=='missing':r['qualification_coverage']=r['qualification_coverage'][:1]
  elif mode=='unsupported':r['qualification_coverage'][1]['unit_ids']=['u0']
  else:r['qualification_coverage'][1]['unit_ids']=['invented']
  return r
 c=FixtureClient([bad,bad]);r=extract_jd(TEXT,job_id='X',client=c,model='deepseek-flash',spec=SPEC)
 assert r.status=='failed' and r.attempts==2 and len(c.calls)==2
 assert r.error_code.startswith('qualification_inventory_')


def test_development_source_inventories_and_responsibilities_excluded():
 rows=[json.loads(l) for l in (ROOT/'data/processed/jobs_features.jsonl').read_text().splitlines()]
 for job,n in [('F00034',9),('F00332',8)]:
  t=next(r['description_clean'] for r in rows if r['final_cluster_id']==job)
  inv=qualification_inventory(t)
  assert len(inv)==n and all(q['source_quote'] in t for q in inv)
 assert qualification_inventory('Responsibilities\n- Python')==[]
