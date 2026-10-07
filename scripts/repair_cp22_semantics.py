"""One authorized final semantic repair; same run ID, ledger and stage limits."""
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'src')]
import argparse,fcntl,json,time,hashlib
from scripts.run_cp22_repair_probe import RUN_ID,STATE,STAGES,SPEC
from scripts.run_batch_extraction import development_sources
from jobfit.config import REPO_ROOT,get_settings,GUIDELINE_FILE
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.closure_probe import ClosureProbeClient
from jobfit.llm.semantic_repair import SemanticRepairSession
from jobfit.extraction.audited import AuditedExtraction,qualification_inventory,validate_inventory
from jobfit.extraction.coverage import qualification_coverage
from jobfit.schemas.requirements import JDExtraction
from jobfit.matching.quote_check import require_quotes

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('receipt',type=Path);args=p.parse_args()
 with STATE.with_suffix('.lock').open('a') as lock:
  fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
  prior=json.loads(STATE.read_text());last=prior['results'][-1]
  # Existing exact code/source fingerprint is unchanged, checked again here.
  for name,h in last['provenance'].items():
   if (REPO_ROOT/name).is_file() and sha((REPO_ROOT/name).read_bytes())!=h:raise ValueError('Frozen implementation changed')
  stage=last['job_id']
  if stage not in {'F00034','F00332_paste'}:raise ValueError('Only the two authorized JD extraction stages')
  job=stage.removesuffix('_paste')
  text=development_sources([job])[0]['text'];assert sha(text.encode())==last['provenance'][job]
  if stage.endswith('_paste'):
   from jobfit.jobs.cleaning import clean_description
   text,_=clean_description(text)
   assert sha(text.encode())==last['cleaned_source_sha256']
  wire_job_id=last['extraction']['job_id']
  receipt=json.loads(args.receipt.read_text());c=OpenRouterClient(get_settings(),run_id=RUN_ID)
  s=SemanticRepairSession(STATE,run_id=RUN_ID,fingerprint=prior['fingerprint'],jobs=STAGES,ledger=c.ledger,ceiling='.40')
  s.check_budget(.0492);c.guard.check(.0492)
  if not c.verify_inference_key()['inference_key']:raise ValueError('Invalid inference key')
  paths=['src/jobfit/llm/semantic_repair.py','scripts/repair_cp22_semantics.py']
  extension={n:sha((REPO_ROOT/n).read_bytes()) for n in paths};extension_hash=sha(json.dumps(extension,sort_keys=True).encode())
  s.begin_repair(receipt,extension_hash);start=time.perf_counter()
  output={'job_id':stage,'run_id':RUN_ID,'provenance':last['provenance'],'versions':{**last['versions'],'semantic_repair_version':'source-review-repair-v1'},'replaces_result_sha256':last['result_sha256'],'repair_extension_hashes':extension,'semantic_repair_receipt_sha256':sha(args.receipt.read_bytes())}
  try:
   prompt=SPEC.prompt_file.read_text()+'\n\n'+GUIDELINE_FILE.read_text()+'\n\nFinal allowed repair: retain all source-backed requirements and correct the trusted reviewer findings below. No other rule changes.\n'+json.dumps(receipt['corrections'])
   messages=[{'role':'system','content':prompt},{'role':'user','content':json.dumps({'untrusted_document_data':{'job_id':wire_job_id,'jd_text':text,'qualification_inventory':qualification_inventory(text),'prior_output':last['extraction']}},ensure_ascii=False)}]
   out=ClosureProbeClient(c,s).chat_structured('deepseek-flash',messages,AuditedExtraction,'jd_extraction_semantic_repair',max_tokens=16000)
   out=AuditedExtraction.model_validate(out);assert out.job_id==wire_job_id;validate_inventory(out,qualification_inventory(text))
   for u in out.units:
    require_quotes(u.source_quotes,text)
    if u.label_source.value!='model_draft':raise ValueError('Invalid provenance')
   extraction=JDExtraction.model_validate(out.model_dump(exclude={'qualification_coverage'}));extraction.extractor_version='jd-prompt-v1.3/source-review-repair-v1/deepseek-flash'
   coverage=qualification_coverage(text,out.units)
   coverage.update(inventory_contract=SPEC.coverage_contract,inventory_count=len(qualification_inventory(text)),inventory_mappings=[x.model_dump() for x in out.qualification_coverage],extraction_prompt_version=SPEC.prompt_version)
   output.update(status='done',extraction=extraction.model_dump(mode='json'),coverage=coverage,attempts=2,cache_hit=False)
   for k in ['key','cleaned_source_sha256']:
    if k in last:output[k]=last[k]
  except BaseException as e:output.update(status='failed',error_code=type(e).__name__,attempts=s.data.get('stage_attempts',{}).get(stage))
  output['latency_ms']=int((time.perf_counter()-start)*1000);output['result_sha256']=sha(json.dumps(output,sort_keys=True).encode())
  s.finish_repair(output)
  path=REPO_ROOT/'evals/results'/f'{RUN_ID}_{len(s.data["results"]):02d}_semantic_repair.json'
  with path.open('x') as f:json.dump(output,f,indent=2)
  print(json.dumps({'status':s.data['status'],'spent':str(s.spent()),'result':str(path)}))
if __name__=='__main__':main()
