"""Bounded, resumable development coverage run. Preflight unless --execute.

No historical artifact is overwritten. A process-wide ledger lock prevents
another cooperating worker from spending during concurrent matching. A local
in-flight upper-bound sum closes the race between four matching requests.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import statistics
import sys
from threading import Lock
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]

from jobfit.config import get_settings
from jobfit.cv.parser import ParsedCV
from jobfit.extraction.audited import ExtractionSpec
from jobfit.extraction.cache import ExtractionCache
from jobfit.extraction.jd_extractor import extract_jd
from jobfit.llm.client import OpenRouterClient, strict_schema
from jobfit.llm.pricing import estimate_cost
from jobfit.matching.evidence_matcher import match_evidence
from jobfit.schemas.requirements import JDExtraction
from jobfit.schemas.analysis import UnitAssessment
from jobfit.scoring.hold_policy_v11 import score_with_hold_policy
from scripts.run_batch_extraction import development_sources

OLD=ROOT/'evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1'
OUT=ROOT/'evals/results/cp23/pipeline_v11'
CONFIG=ROOT/'config/versions/pipeline_cp23_v11_20261004.yaml'
RUN_ID='cp23_pipeline_v11_20261004_v1'
MODEL='deepseek-flash'
CAP=3.00


def digest(path):return sha256(Path(path).read_bytes()).hexdigest()


def write_once(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2)


def protected():
    paths=[ROOT/'evals/labeling/JobFit_Development_Labeling_v1.3.xlsx',
        ROOT/'evals/splits/dev_job_ids.txt',ROOT/'evals/splits/test_job_ids.txt',
        ROOT/'data/processed/jobs_features.jsonl',ROOT/'evals/pools/dev_pool.csv',
        ROOT/'evals/results/cp22_retrieval_top30_20261002_03.json',
        ROOT/'evals/annotation_guideline_v1_3.md',
        ROOT/'prompts/jd_extraction_v1_4_experimental.md',
        ROOT/'prompts/evidence_matching_v1_1.md',
        ROOT/'data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md',
        ROOT/'data/synthetic_cvs/cv_02_career_switcher_ai_engineer_en.md']
    paths+=sorted((ROOT/'evals/gold/development_v13_reviewed_20261002_r2').glob('*'))
    return {str(p.relative_to(ROOT)):digest(p) for p in paths if p.is_file()}


class RunCapReached(RuntimeError):pass


class RunClient:
    def __init__(self,base,starting_total):
        self.base=base;self.starting_total=starting_total
        self.lock=Lock();self.inflight=0.0

    def chat_structured(self,model,messages,output_model,task,max_tokens=2000,temperature=0.0):
        price=self.base._price(model)
        schema=strict_schema(output_model.model_json_schema())
        est_in=len(json.dumps(messages,ensure_ascii=False).encode())+len(json.dumps(schema).encode())+512
        upper=estimate_cost(price,est_in,max_tokens)
        with self.lock:
            spent=self.base.ledger.total_spent()-self.starting_total
            if spent+self.inflight+upper>CAP+1e-9:
                raise RunCapReached('v1.1 aggregate cap would be exceeded')
            # Both the project guard and run cap include outstanding requests.
            self.base.guard.check(upper+self.inflight)
            self.inflight+=upper
        try:
            # The enclosing executor owns ledger.exclusive for the entire run.
            # _chat_attempt still checks the project guard and writes one ledger
            # record for this actual OpenRouter call.
            return self.base._chat_attempt(model,messages,output_model,task,max_tokens,temperature)
        finally:
            with self.lock:self.inflight-=upper


def preflight():
    import yaml
    cfg=yaml.safe_load(CONFIG.read_text())
    if (cfg['pipeline_version'],cfg['model'],cfg['hold_policy'],cfg['matching_concurrency_limit']) != (
        'pipeline-v1.1-development',MODEL,'H2',4):raise ValueError('v1.1 configuration changed')
    prior=json.loads((OLD/'plan.json').read_text())
    ranks=prior['rankings']
    if len(ranks)!=2 or sum(map(len,ranks.values()))!=60 or len(set(sum(ranks.values(),[])))!=52:
        raise ValueError('Part B scope changed')
    ids=set((ROOT/'evals/splits/dev_job_ids.txt').read_text().splitlines())
    if not set(sum(ranks.values(),[]))<=ids:raise ValueError('Non-development ID in plan')
    sources={r['job_id']:r['text'] for r in development_sources(sorted(set(sum(ranks.values(),[]))))}
    if len(sources)!=52:raise ValueError('Development sources missing')
    redo_jds=[];redo_pairs=[];reuse_pairs=[]
    for job in sorted(sources):
        p=OLD/f'jd_{job}.json'
        if job!='F00369' and (not p.exists() or json.loads(p.read_text()).get('status')!='done'
             or (json.loads(p.read_text()).get('extraction') or {}).get('jd_quality')!='ok'):
            redo_jds.append(job)
    for cv,ranking in ranks.items():
        for job in ranking:
            row=json.loads((OLD/f'match_{cv}_{job}.json').read_text())
            if job in redo_jds or row['status']!='done':redo_pairs.append([cv,job])
            else:reuse_pairs.append([cv,job])
    if len(redo_pairs)+len(reuse_pairs)!=60:raise ValueError('Pair inventory mismatch')
    settings=get_settings()
    client=OpenRouterClient(settings,run_id=RUN_ID,chat_timeout_seconds=240.0)
    price=client._price(MODEL)
    records=client.ledger.records()
    medians={}
    for task in ['jd_extraction','evidence_matching']:
        values=[r.cost_usd for r in records if r.model==price.model_id and r.task==task and r.ok and r.cost_source=='reported']
        if not values:raise ValueError('No observed successful call costs')
        medians[task]=statistics.median(values)
    estimate=1.5*(len(redo_jds)*medians['jd_extraction']+len(redo_pairs)*medians['evidence_matching'])
    receipt={'run_id':RUN_ID,'scope':'development_only_CV1_CV2','pipeline_version':cfg['pipeline_version'],
        'config_sha256':digest(CONFIG),'original_plan_sha256':digest(OLD/'plan.json'),
        'old_run':str(OLD.relative_to(ROOT)),'redo_jds':redo_jds,'redo_pairs':redo_pairs,
        'reuse_pairs':reuse_pairs,'total_pairs':60,'unique_jds':52,
        'medians_usd':medians,'estimate_median_x_1_5_usd':round(estimate,9),
        'approved_cap_usd':CAP,'project_budget_usd':settings.api_budget_usd,
        'project_hard_stop_usd':settings.api_hard_stop_usd,
        'ledger_before_usd':client.ledger.total_spent(),
        'protected_sha256':protected(),'matching_concurrency_limit':4,
        'source_hold':['F00369']}
    if estimate>CAP:raise ValueError('Median estimate exceeds approved v1.1 cap')
    if settings.api_budget_usd!=19 or settings.api_hard_stop_usd!=18.5:
        raise ValueError('Dion has not configured the approved numeric project guard')
    if client.ledger.total_spent()+CAP>settings.api_hard_stop_usd:
        raise ValueError('Project hard stop has insufficient headroom')
    return receipt,sources,client


def main(execute=False):
    plan,sources,base=preflight()
    OUT.mkdir(parents=True,exist_ok=True)
    p=OUT/'plan_v1.json'
    if p.exists():
        old=json.loads(p.read_text())
        for field in ['run_id','config_sha256','original_plan_sha256','redo_jds','redo_pairs',
                      'reuse_pairs','protected_sha256']:
            if old[field]!=plan[field]:raise ValueError('Frozen v1.1 plan changed')
        plan=old
    else:write_once(p,plan)
    print(json.dumps({k:plan[k] for k in ['run_id','redo_jds','redo_pairs','estimate_median_x_1_5_usd',
           'approved_cap_usd','project_budget_usd','project_hard_stop_usd','ledger_before_usd']}),flush=True)
    if not execute:return
    if protected()!=plan['protected_sha256']:raise ValueError('Protected input changed before dispatch')
    if not base.verify_inference_key()['inference_key']:raise ValueError('Inference key is not valid for inference')
    start_total=base.ledger.total_spent()-sum(r.cost_usd for r in base.ledger.records() if r.run_id==RUN_ID)
    client=RunClient(base,start_total)
    spec=ExtractionSpec(ROOT/'prompts/jd_extraction_v1_4_experimental.md','jd-prompt-v1.4-experimental')
    cache=ExtractionCache(ROOT/'reports/extraction_cache')
    run_start=time.perf_counter()
    with base.ledger.exclusive():
        for job in plan['redo_jds']:
            dest=OUT/f'jd_{job}_v11.json'
            if dest.exists():continue
            if protected()!=plan['protected_sha256']:raise ValueError('Protected input changed')
            start=time.perf_counter()
            result=extract_jd(sources[job],job_id=job,client=client,model=MODEL,
                cache=cache,scope='corpus_jd',spec=spec,dynamic_output=True)
            write_once(dest,{'job_id':job,'status':result.status,'attempts':result.attempts,
                'error_code':result.error_code,'cache_hit':result.cache_hit,
                'coverage':result.coverage,'wall_ms':round((time.perf_counter()-start)*1000),
                'extraction':result.extraction.model_dump(mode='json') if result.extraction else None})
            print(json.dumps({'stage':'jd','job_id':job,'status':result.status,
                'error_code':result.error_code}),flush=True)
            if result.error_code in {'RunCapReached','AuthenticationError','PermissionDeniedError'}:
                raise RuntimeError('Stopping after a budget or authorization failure')

        cvs={cv:ParsedCV.model_validate(json.loads((OLD/f'{cv}_parse.json').read_text())['parsed'])
             for cv in ['CV1','CV2']}
        def pair_result(cv,job):
            start=time.perf_counter()
            old_row=json.loads((OLD/f'match_{cv}_{job}.json').read_text())
            jdpath=OUT/f'jd_{job}_v11.json' if job in plan['redo_jds'] else OLD/f'jd_{job}.json'
            if not jdpath.exists():
                return {'cv_id':cv,'job_id':job,'status':'held_source','reason':'source_provenance_hold',
                    'score_H1':None,'score_H2':None,'wall_ms':0}
            jd=json.loads(jdpath.read_text())
            raw=jd.get('extraction')
            if jd['status']!='done' or not raw or raw['jd_quality']!='ok':
                return {'cv_id':cv,'job_id':job,'status':'held_extraction','reason':jd.get('error_code') or raw['jd_quality'],
                    'score_H1':None,'score_H2':None,'wall_ms':0}
            extraction=JDExtraction.model_validate(raw)
            if [cv,job] in plan['reuse_pairs']:
                assessments=[UnitAssessment.model_validate(a) for a in old_row['assessments']]
                source='reused_v1_matching'
                match_status=old_row['status'];error_code=old_row.get('error_code')
            else:
                result=match_evidence(cvs[cv],extraction,client=client,model=MODEL,
                    validator_version='quote-check-v1.1',guardrail_ids=('G1','G2'),dynamic_output=True)
                assessments=result.assessments;source='v11_matching'
                match_status=result.status;error_code=result.error_code
            h1,_=score_with_hold_policy(extraction,assessments,policy='H1')
            h2,excluded=score_with_hold_policy(extraction,assessments,policy='H2')
            return {'cv_id':cv,'job_id':job,'status':match_status,'error_code':error_code,
                'source':source,'jd_source':'v11' if job in plan['redo_jds'] else 'reused_v1',
                'score_H1':h1.model_dump(mode='json'),'score_H2':h2.model_dump(mode='json'),
                'excluded_needs_review':excluded,'wall_ms':round((time.perf_counter()-start)*1000),
                'assessments':[] if source=='reused_v1_matching' else [a.model_dump(mode='json') for a in assessments]}

        # Only unresolved pairs dispatch paid matching. Reused pairs are rescored
        # deterministically in the same pass. The four-worker limit is explicit.
        all_pairs=[(cv,job) for cv,rank in json.loads((OLD/'plan.json').read_text())['rankings'].items() for job in rank]
        pending=[(cv,job) for cv,job in all_pairs if not (OUT/f'pair_{cv}_{job}_v11.json').exists()]
        with ThreadPoolExecutor(max_workers=4) as pool:
            for offset in range(0,len(pending),4):
                group=pending[offset:offset+4]
                futures={pool.submit(pair_result,cv,job):(cv,job) for cv,job in group}
                stop_reason=None
                for future in as_completed(futures):
                    cv,job=futures[future]
                    row=future.result()
                    write_once(OUT/f'pair_{cv}_{job}_v11.json',row)
                    print(json.dumps({'stage':'pair','cv_id':cv,'job_id':job,'status':row['status'],
                        'score_status':(row.get('score_H2') or {}).get('status'),'error_code':row.get('error_code')}),flush=True)
                    if row.get('error_code') in {'RunCapReached','AuthenticationError','PermissionDeniedError',
                            'APIConnectionError','APIStatusError'}:
                        stop_reason='Stopping after budget, authorization, or unknown transport failure'
                if stop_reason:raise RuntimeError(stop_reason)

    if protected()!=plan['protected_sha256']:raise ValueError('Protected input changed after run')
    saved=[json.loads((OUT/f'pair_{cv}_{job}_v11.json').read_text()) for cv,job in all_pairs]
    usable=lambda policy:sum((r.get(f'score_{policy}') or {}).get('status') in {'final','provisional'} for r in saved)
    summary={'run_id':RUN_ID,'status':'completed','pairs':len(saved),'H1_usable':usable('H1'),
        'H2_usable':usable('H2'),'per_cv':{cv:{p:sum(r['cv_id']==cv and
             (r.get(f'score_{p}') or {}).get('status') in {'final','provisional'} for r in saved)
             for p in ['H1','H2']} for cv in ['CV1','CV2']},
        'ledger_run_cost_usd':sum(r.cost_usd for r in base.ledger.records() if r.run_id==RUN_ID),
        'ledger_total_usd':base.ledger.total_spent(),'wall_ms':round((time.perf_counter()-run_start)*1000),
        'protected_sha256':plan['protected_sha256']}
    dest=OUT/'summary_v1.json'
    if dest.exists():raise ValueError('Versioned summary already exists')
    write_once(dest,summary)
    print(json.dumps(summary),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    main(args.execute)
