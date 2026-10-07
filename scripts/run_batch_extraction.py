"""Development-only JD extraction, preflight default, versioned resumable cache.

Held-out JD extraction is deferred until configuration freeze. A batch above $1
requires an explicit user-approved ceiling, supplied by --approved-budget-usd.
This script never reads pending workbook labels or modifies source/gold data.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import argparse
import hashlib
import json
import re
import os
import math
import yaml
from jobfit.config import REPO_ROOT, get_settings, GUIDELINE_FILE, runtime_versions
from jobfit.extraction.cache import ExtractionCache
from jobfit.extraction.jd_extractor import extract_jd, JD_PROMPT_FILE
from jobfit.llm.client import OpenRouterClient, strict_schema
from jobfit.llm.structured import STRUCTURED_MAX_TOKENS, REPAIR_CONTEXT_MAX_BYTES
from jobfit.schemas.requirements import JDExtraction


def development_sources(ids=None):
    split=REPO_ROOT/'evals/splits'
    manifest=json.loads((split/'split_manifest.json').read_text())
    for filename,digest in manifest['output_hashes'].items():
        if hashlib.sha256((split/filename).read_bytes()).hexdigest()!=digest:
            raise ValueError('Frozen split hash mismatch')
    dev=set((split/'dev_job_ids.txt').read_text().splitlines())
    chosen=set(ids) if ids else dev
    if not chosen or not chosen<=dev: raise ValueError('Only frozen development IDs are permitted')
    rows=[]
    with (REPO_ROOT/'data/processed/jobs_features.jsonl').open() as f:
        for line in f:
            row=json.loads(line)
            if row['final_cluster_id'] in chosen:
                rows.append({'job_id':row['final_cluster_id'],'text':row['description_clean']})
    if {r['job_id'] for r in rows}!=chosen: raise ValueError('Missing development source')
    return sorted(rows,key=lambda r:r['job_id'])


def atomic_report(path,data):
    tmp=path.with_suffix('.tmp')
    with tmp.open('w') as f:
        json.dump(data,f,indent=2,ensure_ascii=False);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id',required=True)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--job-id',action='append')
    p.add_argument('--approved-budget-usd',type=float,default=1.0,
        help='Only increase after explicit user approval for this batch')
    a=p.parse_args()
    if not math.isfinite(a.approved_budget_usd) or a.approved_budget_usd < 0:
        raise ValueError('Batch approval ceiling must be finite and nonnegative')
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',a.run_id): raise ValueError('Invalid run id')
    path=REPO_ROOT/'evals/results'/f'{a.run_id}.json'
    if path.exists():raise ValueError('Preserve old run records; use a new run id. Cached successes will be reused.')
    cfg=yaml.safe_load((REPO_ROOT/'config/pipeline_v1.yaml').read_text())
    client=OpenRouterClient(get_settings(),run_id=a.run_id)
    cache=ExtractionCache(REPO_ROOT/'reports/extraction_cache')
    rows=development_sources(a.job_id)
    prompt=JD_PROMPT_FILE.read_text()+'\n\n'+GUIDELINE_FILE.read_text()
    schema=json.dumps(strict_schema(JDExtraction.model_json_schema()))
    price=client.prices[cfg['model']]
    class NoInference:
        def chat_structured(self,*args,**kwargs): raise RuntimeError('PreflightNoInference')
    estimates=[]
    for row in rows:
        cached=extract_jd(row['text'],job_id=row['job_id'],client=NoInference(),model=cfg['model'],cache=cache,scope='corpus_jd')
        payload={'untrusted_document_data':{'job_id':row['job_id'],'jd_text':row['text']}}
        messages=[{'role':'system','content':prompt},{'role':'user','content':json.dumps(payload,ensure_ascii=False)}]
        # Covers both calls, schema bytes and the repair system message.
        tokens=len(json.dumps(messages,ensure_ascii=False).encode())+len(schema.encode())+2048+REPAIR_CONTEXT_MAX_BYTES
        upper=0 if cached.cache_hit else 2*(tokens*price.input_per_m+STRUCTURED_MAX_TOKENS*price.output_per_m)/1_000_000
        estimates.append({'job_id':row['job_id'],'cached':cached.cache_hit,'upper_usd':upper})
    bound=sum(e['upper_usd'] for e in estimates)
    report={'run_id':a.run_id,'mode':'live' if a.execute else 'preflight','model':price.model_id,
        'scope':'frozen development only','max_output_tokens':STRUCTURED_MAX_TOKENS,'development_jobs':len(rows),'held_out_deferred':214,
        'pending':sum(not e['cached'] for e in estimates),'cache_hits':sum(e['cached'] for e in estimates),
        'conservative_upper_usd':bound,'approval_ceiling_usd':a.approved_budget_usd,
        'budget_approval_needed':bound>a.approved_budget_usd,'estimates':estimates,'results':[],
        'versions':runtime_versions(),
        'guideline_sha256':hashlib.sha256(GUIDELINE_FILE.read_bytes()).hexdigest(),
        'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'status':'preflight'}
    atomic_report(path,report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['estimates','results']},indent=2),flush=True)
    if not a.execute:return
    if bound>a.approved_budget_usd:raise ValueError('Batch ceiling requires user approval before inference')
    client.guard.check(bound)
    if not client.verify_inference_key()['inference_key']:raise ValueError('Inference key check failed')
    failures=0
    report['status']='running'
    for row in rows:
        result=extract_jd(row['text'],job_id=row['job_id'],client=client,model=cfg['model'],cache=cache,scope='corpus_jd')
        item={'job_id':row['job_id'],'status':result.status,'cache_hit':result.cache_hit,'attempts':result.attempts,
            'error_code':result.error_code,'cache_key':result.key,'units':len(result.extraction.units) if result.extraction else None}
        report['results'].append(item)
        failures=failures+1 if result.status=='failed' else 0
        atomic_report(path,report);print(json.dumps(item),flush=True)
        if failures>=3 or result.error_code in ['AuthenticationError','PermissionDeniedError','BudgetExceeded','APIConnectionError','APITimeoutError']:
            report['status']='stopped_on_failure';break
    else:report['status']='completed'
    usage=[r for r in client.ledger.records() if r.run_id==a.run_id]
    report.update(calls=len(usage),cost_usd=sum(r.cost_usd for r in usage if not r.cached),
        done=sum(r['status']=='done' for r in report['results']),failed=sum(r['status']=='failed' for r in report['results']),
        not_attempted=len(rows)-len(report['results']))
    atomic_report(path,report)
    print(json.dumps({k:report[k] for k in ['status','done','failed','not_attempted','calls','cost_usd']}))


if __name__=='__main__':main()
