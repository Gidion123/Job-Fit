"""Synthetic-only paired masking check on the four fixed development evidence pairs.

Preflight makes no call. The masked run uses the same reviewed requirement inputs
as the saved unmasked DeepSeek comparison. No real CV or test set is allowed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'src')]

from jobfit.config import REPO_ROOT,get_settings
from jobfit.cv.parser import ParsedCV
from jobfit.eval.matching_evaluation import reference_rows
from jobfit.eval.metrics import evidence_metrics
from jobfit.llm.client import OpenRouterClient
from jobfit.matching.evidence_matcher import match_evidence
from jobfit.schemas.analysis import UnitAssessment
from jobfit.scoring.score import effective_label
from scripts.run_cp23_end_to_end_dev import OUT as PART_B_OUT, RUN as PART_B_RUN, CAP, RunClient
from scripts.run_cp23_stage2_matching import BUNDLE,inputs
from scripts.check_cp23_masking_quotes import check as check_masked_quotes, OUTPUT as QUOTE_RECEIPT

RUN='cp23_masking_paired_dev_20261004_v1'
OUT=REPO_ROOT/'evals/results/cp23/end_to_end_dev'/RUN
STAGE_PLAN=REPO_ROOT/'evals/results/cp23_stage2_fixed_matching_20261003_v1_plan.json'
PAIRS=(('CV1','F00332'),('CV1','F00036'),('CV2','F00815'),('CV2','F00018'))


def fixed_pair_quote_preflight():
    """The fixed reference quotes must survive masking unchanged for this scope."""
    if not QUOTE_RECEIPT.exists():
        raise ValueError('Synthetic masking quote receipt is missing')
    receipt=json.loads(QUOTE_RECEIPT.read_text())
    current=check_masked_quotes()
    if receipt!=current or not current['all_changed_quotes_mapped_exactly']:
        raise ValueError('Synthetic masking quote receipt is stale or incomplete')
    affected={(row['cv_id'],row['job_id']) for result in current['results'].values()
              for row in result['changed_rows']}
    if affected.intersection(PAIRS):
        raise ValueError('A fixed matching reference quote changed after masking; review transfer first')
    return receipt['schema_version']


def calculate(records, stages):
    truth={};pred={};cases=[]
    for stage in stages:
        cv,ex=inputs(stage)
        gold=reference_rows(BUNDLE,stage,cv,ex)
        key=(stage['cv_id'],stage['job_id'])
        record=records.get(key)
        for unit,label in gold.items():truth['/'.join((*key,unit))]=label
        if record and record['status']=='done':
            by={a.unit_id:a for a in map(UnitAssessment.model_validate,record['assessments'])}
            for unit in ex.units:
                label,status=effective_label(unit,by[unit.unit_id])
                pred['/'.join((*key,unit.unit_id))]={'status':status.value,
                    'label':label.value if status.value=='done' and label is not None else None}
        cases.append({'cv_id':key[0],'job_id':key[1],'units':len(gold),
                      'status':record['status'] if record else 'not_attempted'})
    return {'metrics':evidence_metrics(truth,pred,alignment_verified=True),'cases':cases}


def main():
    a=argparse.ArgumentParser();a.add_argument('--execute',action='store_true');opts=a.parse_args()
    all_stages=json.loads(STAGE_PLAN.read_text())['stages']
    stages=[s for s in all_stages if s['model']=='deepseek-flash' and (s['cv_id'],s['job_id']) in PAIRS]
    if len(stages)!=4:raise ValueError('Fixed development pair plan changed')
    quote_protocol=fixed_pair_quote_preflight()
    base=OpenRouterClient(get_settings(),run_id=RUN)
    prior=[r for r in base.ledger.records() if r.run_id in (RUN,PART_B_RUN)]
    previous=sum(r.cost_usd for r in prior)
    print(json.dumps({'pairs':len(stages),'prior_part_b_usd':previous,'shared_cap_usd':CAP,
                      'model':'deepseek-flash','scope':'synthetic_development'}),flush=True)
    if not opts.execute:return
    if previous>=CAP:raise ValueError('Approved Part B cap is exhausted')
    if not base.verify_inference_key()['inference_key']:raise ValueError('Inference key check failed')
    client=RunClient(base,base.ledger.total_spent()-previous,CAP)
    OUT.mkdir(parents=True,exist_ok=True)
    for stage in stages:
        cv_id,job_id=stage['cv_id'],stage['job_id']
        path=OUT/f'{cv_id}_{job_id}.json'
        if path.exists():continue
        masked_path=PART_B_OUT/f'{cv_id}_parse.json'
        if not masked_path.exists():raise ValueError('Masked CV parsing record missing')
        masked=ParsedCV.model_validate(json.loads(masked_path.read_text())['parsed'])
        _,ex=inputs(stage)
        result=match_evidence(masked,ex,client=client,model='deepseek-flash',
                              duration_years=stage['duration_input'],
                              validator_version='quote-check-v1.1',guardrail_ids=('G1','G2'))
        record={'cv_id':cv_id,'job_id':job_id,'status':result.status,'error_code':result.error_code,
                'attempts':result.attempts,'source_flags':result.source_flags,
                'assessments':[x.model_dump(mode='json') for x in result.assessments]}
        with path.open('x') as f:json.dump(record,f,indent=2,ensure_ascii=False)
        print(json.dumps({'cv_id':cv_id,'job_id':job_id,'status':result.status,'attempts':result.attempts}),flush=True)
        if result.error_code in ('PartBRunCapReached','APIConnectionError','APITimeoutError','AuthenticationError'):
            raise RuntimeError('Stop on budget or uncertain transport')
    records={(d['cv_id'],d['job_id']):d for path in OUT.glob('CV*.json') for d in [json.loads(path.read_text())]}
    measured=calculate(records,stages)
    output=OUT/'summary.json'
    if output.exists():raise ValueError('Preserve earlier summary')
    old=json.loads((REPO_ROOT/'evals/results/cp23_sql_reference_comparison_20261004_v2.json').read_text())
    unmasked=old['results']['round_one_B']['deepseek-flash']['new']['all_cases_guarded']['macro_f1']
    data={'run_id':RUN,'scope':'development synthetic only, four fixed pairs',
          'same_fixed_requirements_as_unmasked':True,'masked':measured,
          'quote_compatibility_protocol':quote_protocol,
          'reference_transfer_limit':'Fixed source quotes survive masking unchanged; semantic label equivalence is not independently approved.',
          'unmasked_reference_macro_f1':unmasked,
          'unmasked_reference_note':'Saved D-067 v1.1 G1/G2 DeepSeek result on the same 73 fixed requirements; this is a historical nonpaired model draw.',
          'cost_usd':sum(r.cost_usd for r in base.ledger.records() if r.run_id==RUN),
          'shared_part_b_cost_usd':sum(r.cost_usd for r in base.ledger.records() if r.run_id in (RUN,PART_B_RUN)),
          'gold_written':False,'test_access':False}
    with output.open('x') as f:json.dump(data,f,indent=2)
    print(json.dumps({'masked_macro_f1':measured['metrics']['macro_f1'],
                      'cost_usd':data['cost_usd'],'shared_part_b_cost_usd':data['shared_part_b_cost_usd']}),flush=True)


if __name__=='__main__':main()
