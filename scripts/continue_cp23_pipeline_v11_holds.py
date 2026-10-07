"""One bounded follow-up for structural holds and an empty inline-heading JD.

This is a new versioned plan within the same US$3.00 v1.1 aggregate ceiling.
The original 60-pair result and every old call remain immutable.
"""
from __future__ import annotations
from datetime import date
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from scripts.run_cp23_pipeline_v11 import OLD,OUT,RUN_ID,MODEL,preflight,protected,write_once,RunClient
from jobfit.cv.parser import ParsedCV
from jobfit.extraction.audited import ExtractionSpec
from jobfit.extraction.cache import ExtractionCache
from jobfit.extraction.jd_extractor import extract_jd
from jobfit.matching.evidence_matcher import match_evidence
from jobfit.schemas.requirements import JDExtraction
from jobfit.scoring.hold_policy_v11 import score_with_hold_policy

CASES=[('CV1','F00022'),('CV2','F00126'),('CV1','F00310'),('CV2','F00310')]
JOBS=['F00022','F00126','F00310']


def main(execute=False):
    first,sources,base=preflight()
    if not (OUT/'summary_v1.json').exists():
        raise ValueError('Primary v1.1 plan is not complete')
    for cv,job in CASES:
        row=json.loads((OUT/f'pair_{cv}_{job}_v11.json').read_text())
        expected='no_score' if job=='F00310' else 'on_hold'
        if row['status']!='done' or (row.get('score_H2') or {}).get('status')!=expected:
            raise ValueError('Case is no longer held under the documented reason')
        prior_path=(OUT/f'jd_{job}_v11.json') if job=='F00310' else (OLD/f'jd_{job}.json')
        old=json.loads(prior_path.read_text())['extraction']
        if job=='F00310':
            if old['units'] or 'Qualifications and Experience:' not in sources[job]:
                raise ValueError('The known flattened-heading omission is absent')
        elif not any(u['needs_review'] for u in old['units']):
            raise ValueError('No structural hold to investigate')
    plan={'run_id':RUN_ID,'plan_version':'v2_remaining_holds_and_heading_guards',
        'cases':[{'cv_id':c,'job_id':j} for c,j in CASES],
        'jobs':JOBS,
        'reason':'Two jobs exceed H2. F00310 returned no units despite an explicit qualification heading. F00309 is excluded because its nine extracted requirements are all preferred.',
        'same_model_prompt_schema':True,'aggregate_cap_usd':3.00,
        'estimate_median_x_1_5_usd':round(1.5*(len(JOBS)*first['medians_usd']['jd_extraction']+
                                               len(CASES)*first['medians_usd']['evidence_matching']),9),
        'primary_plan_sha256':__import__('hashlib').sha256((OUT/'plan_v1.json').read_bytes()).hexdigest(),
        'protected_sha256':first['protected_sha256']}
    path=OUT/'hold_continuation_plan_v2.json'
    if path.exists():
        if json.loads(path.read_text())!=plan:raise ValueError('Frozen hold continuation plan changed')
    else:write_once(path,plan)
    run_spent=sum(r.cost_usd for r in base.ledger.records() if r.run_id==RUN_ID)
    if run_spent+plan['estimate_median_x_1_5_usd']>3.00:
        raise ValueError('Continuation estimate exceeds remaining v1.1 cap')
    print(json.dumps({'plan_version':plan['plan_version'],'cases':plan['cases'],
        'aggregate_cap_usd':3.00,'already_accounted_usd':run_spent,
        'remaining_cap_usd':3.00-run_spent,
        'estimate_median_x_1_5_usd':plan['estimate_median_x_1_5_usd']}),flush=True)
    if not execute:return
    if protected()!=plan['protected_sha256']:raise ValueError('Protected input changed')
    if not base.verify_inference_key()['inference_key']:raise ValueError('Inference key unavailable')
    start_total=base.ledger.total_spent()-run_spent
    client=RunClient(base,start_total)
    spec=ExtractionSpec(ROOT/'prompts/jd_extraction_v1_4_experimental.md','jd-prompt-v1.4-experimental')
    cache=ExtractionCache(ROOT/'reports/extraction_cache')
    with base.ledger.exclusive():
        for job in JOBS:
            if protected()!=plan['protected_sha256']:raise ValueError('Protected input changed')
            jd_path=OUT/f'jd_hold_{job}_v11_v2.json'
            if jd_path.exists():jd=json.loads(jd_path.read_text())
            else:
                start=time.perf_counter()
                result=extract_jd(sources[job],job_id=job,client=client,model=MODEL,
                    cache=cache,scope='corpus_jd',spec=spec,dynamic_output=True)
                jd={'job_id':job,'status':result.status,'attempts':result.attempts,
                    'error_code':result.error_code,'wall_ms':round((time.perf_counter()-start)*1000),
                    'coverage':result.coverage,
                    'extraction':result.extraction.model_dump(mode='json') if result.extraction else None}
                write_once(jd_path,jd)
                print(json.dumps({'stage':'held_jd','job_id':job,'status':jd['status'],
                    'error_code':jd['error_code']}),flush=True)
            if jd.get('error_code') in {'RunCapReached','AuthenticationError','PermissionDeniedError',
                                         'APIConnectionError','APIStatusError'}:
                raise RuntimeError('Stop after budget, authorization, or transport failure')
        for cv,job in CASES:
            jd=json.loads((OUT/f'jd_hold_{job}_v11_v2.json').read_text())
            pair_path=OUT/f'pair_hold_{cv}_{job}_v11_v2.json'
            if pair_path.exists():continue
            raw=jd.get('extraction')
            if jd['status']!='done' or not raw or raw['jd_quality']!='ok':
                row={'cv_id':cv,'job_id':job,'status':'held_extraction',
                    'reason':jd.get('error_code') or (raw or {}).get('jd_quality'),
                    'score_H1':None,'score_H2':None,'wall_ms':0}
            else:
                parsed=ParsedCV.model_validate(json.loads((OLD/f'{cv}_parse.json').read_text())['parsed'])
                extraction=JDExtraction.model_validate(raw)
                start=time.perf_counter()
                result=match_evidence(parsed,extraction,client=client,model=MODEL,
                    validator_version='quote-check-v1.1',guardrail_ids=('G1','G2'),dynamic_output=True)
                h1,_=score_with_hold_policy(extraction,result.assessments,policy='H1')
                h2,excluded=score_with_hold_policy(extraction,result.assessments,policy='H2')
                row={'cv_id':cv,'job_id':job,'status':result.status,'error_code':result.error_code,
                    'source':'v11_matching_hold_continuation','jd_source':'v11_hold_continuation',
                    'score_H1':h1.model_dump(mode='json'),'score_H2':h2.model_dump(mode='json'),
                    'excluded_needs_review':excluded,'wall_ms':round((time.perf_counter()-start)*1000),
                    'assessments':[a.model_dump(mode='json') for a in result.assessments]}
            write_once(pair_path,row)
            print(json.dumps({'stage':'held_pair','cv_id':cv,'job_id':job,'status':row['status'],
                'score_status':(row.get('score_H2') or {}).get('status')}),flush=True)
            if row.get('error_code') in {'RunCapReached','AuthenticationError','PermissionDeniedError',
                                         'APIConnectionError','APIStatusError'}:
                raise RuntimeError('Stop after budget, authorization, or transport failure')
    if protected()!=plan['protected_sha256']:raise ValueError('Protected input changed after continuation')
    write_once(OUT/'hold_continuation_summary_v2.json',{'run_id':RUN_ID,
        'cases':[{'cv_id':cv,'job_id':job,
                  'status':json.loads((OUT/f'pair_hold_{cv}_{job}_v11_v2.json').read_text())['status'],
                  'H2_status':(json.loads((OUT/f'pair_hold_{cv}_{job}_v11_v2.json').read_text()).get('score_H2') or {}).get('status')}
                 for cv,job in CASES],
        'aggregate_accounted_usd':sum(r.cost_usd for r in base.ledger.records() if r.run_id==RUN_ID)})


if __name__=='__main__':
    main('--execute' in sys.argv)
