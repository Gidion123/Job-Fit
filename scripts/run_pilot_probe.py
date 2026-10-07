"""One JD per invocation, fixed US$0.20 aggregate probe including repair/resume.

Default: offline preflight. --execute runs only the next permitted JD.
--record-check FILE records an execution-role inspection, never label approval.
No workbook, CV, gold mutation, model selection or full batch.
"""
from pathlib import Path
import sys
sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1]/'src')]
import argparse
from decimal import Decimal
import fcntl
import hashlib
import json
import time
import yaml
from jobfit.config import REPO_ROOT, get_settings, GUIDELINE_FILE, runtime_versions
from jobfit.extraction.cache import ExtractionCache
from jobfit.extraction.jd_extractor import extract_jd, JD_PROMPT_FILE
from jobfit.llm.client import OpenRouterClient, strict_schema
from jobfit.llm.structured import STRUCTURED_MAX_TOKENS, REPAIR_CONTEXT_MAX_BYTES
from jobfit.llm.probe import ProbeSession, ProbeClient
from jobfit.schemas.requirements import JDExtraction
from scripts.run_batch_extraction import development_sources

RUN_ID = 'cp22_pilot_quality_probe_20261002'
JOBS = ['F00016', 'F00034', 'F00073']
STATE = REPO_ROOT/'reports/quality_probe'/f'{RUN_ID}.json'

def sha(value):
    return hashlib.sha256(value).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    a = p.add_mutually_exclusive_group()
    a.add_argument('--execute', action='store_true')
    a.add_argument('--record-check', type=Path)
    args = p.parse_args()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with STATE.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        rows = {r['job_id']: r for r in development_sources(JOBS)}
        gold = [json.loads(x) for x in (REPO_ROOT/'evals/gold/extraction_gold.jsonl').read_text().splitlines()]
        if any(not any(g['job_id']==j and g['split']=='development' and g['review_status']=='approved' for g in gold) for j in JOBS):
            raise ValueError('Probe requires approved development extraction references')
        cfg = yaml.safe_load((REPO_ROOT/'config/pipeline_v1.yaml').read_text())
        c = OpenRouterClient(get_settings(), run_id=RUN_ID)
        paths = ['config/models_v1.yaml','config/pipeline_v1.yaml',str(GUIDELINE_FILE.relative_to(REPO_ROOT)),
                 'evals/gold/extraction_gold.jsonl','evals/splits/split_manifest.json',
                 'src/jobfit/extraction/jd_extractor.py','src/jobfit/llm/structured.py','src/jobfit/llm/client.py',
                 'src/jobfit/llm/probe.py','src/jobfit/schemas/requirements.py','scripts/run_pilot_probe.py']
        provenance = {name: sha((REPO_ROOT/name).read_bytes()) for name in paths}
        provenance[str(JD_PROMPT_FILE.relative_to(REPO_ROOT))] = sha(JD_PROMPT_FILE.read_bytes())
        provenance.update({j:sha(rows[j]['text'].encode()) for j in JOBS})
        fingerprint = sha(json.dumps(provenance, sort_keys=True).encode())
        s = ProbeSession(STATE, run_id=RUN_ID, fingerprint=fingerprint, jobs=JOBS, ledger=c.ledger)
        if args.record_check:
            s.record_check(json.loads(args.record_check.read_text()))
            print(json.dumps({'status':s.data['status'],'spent_usd':str(s.spent())})); return
        if s.data['status'] not in {'ready','complete'}:
            raise ValueError('Probe stopped, interrupted, or waiting for semantic inspection; no inference permitted')
        cache = ExtractionCache(REPO_ROOT/'reports/extraction_cache')
        class NoInference:
            def chat_structured(self,*a,**k): raise RuntimeError('PreflightNoInference')
        prompt = JD_PROMPT_FILE.read_text()+'\n\n'+GUIDELINE_FILE.read_text()
        schema = json.dumps(strict_schema(JDExtraction.model_json_schema()))
        price = c.prices[cfg['model']]
        estimates = []
        for j in JOBS[len(s.data['results']):]:
            row = rows[j]
            cached = extract_jd(row['text'],job_id=j,client=NoInference(),model=cfg['model'],cache=cache,scope='corpus_jd')
            messages = [{'role':'system','content':prompt},{'role':'user','content':json.dumps({'untrusted_document_data':{'job_id':j,'jd_text':row['text']}},ensure_ascii=False)}]
            tokens = len(json.dumps(messages,ensure_ascii=False).encode())+len(schema.encode())+2048+REPAIR_CONTEXT_MAX_BYTES
            upper = 0 if cached.cache_hit else 2*(tokens*price.input_per_m+STRUCTURED_MAX_TOKENS*price.output_per_m)/1e6
            estimates.append({'job_id':j,'cache_hit':cached.cache_hit,'input_token_upper_per_attempt':tokens,'max_output_tokens':STRUCTURED_MAX_TOKENS,'attempts_max':2,'upper_usd':upper})
        bound = sum(x['upper_usd'] for x in estimates)
        s.check_budget(bound); c.guard.check(bound)
        summary = {'model':price.model_id,'scope':JOBS,'estimates':estimates,'remaining_upper_usd':bound,
                   'probe_spent_usd':str(s.spent()),'probe_ceiling_usd':s.data['ceiling'],'project_hard_stop_usd':c.guard.hard_stop_usd,
                   'project_spent_usd':str(sum(Decimal(str(r.cost_usd)) for r in c.ledger.records() if not r.cached)),
                   'provenance':provenance,'versions':runtime_versions(),'status':s.data['status'],'mode':'preflight','new_api_calls':0}
        report = REPO_ROOT/'evals/results'/f'{RUN_ID}_preflight_{len(s.data["results"]):02d}.json'
        if not report.exists(): report.write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps({k:v for k,v in summary.items() if k!='provenance'}),flush=True)
        if not args.execute or not estimates: return
        if not c.verify_inference_key()['inference_key']: raise ValueError('Not an inference key')
        j = estimates[0]['job_id'];s.begin(j);start=time.perf_counter()
        result = extract_jd(rows[j]['text'],job_id=j,client=ProbeClient(c,s),model=cfg['model'],cache=cache,scope='corpus_jd')
        output = {'job_id':j,'status':result.status,'attempts':result.attempts,'error_code':result.error_code,
                  'cache_hit':result.cache_hit,'cache_key':result.key,'source_sha256':provenance[j],
                  'extraction':result.extraction.model_dump(mode='json') if result.extraction else None,
                  'latency_ms':int((time.perf_counter()-start)*1000),'provenance':provenance,'versions':runtime_versions(),'run_id':RUN_ID}
        output['result_sha256']=sha(json.dumps(output,sort_keys=True).encode())
        s.finish(output)
        print(json.dumps({'job_id':j,'status':s.data['status'],'attempts':result.attempts,'error_code':result.error_code,'units':len(result.extraction.units) if result.extraction else None,'probe_spent_usd':str(s.spent())}),flush=True)

if __name__ == '__main__':
    main()
