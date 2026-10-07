"""D-063 accepted mappings, fixed-input evidence, and original-case accounting.

Offline only. Writes fresh artifacts; never edits gold, predictions or paid states.
The legacy human_verified field denotes accepted assisted QA, not independence.
"""
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'src')]
import argparse, hashlib, json
from collections import Counter, defaultdict
from copy import deepcopy
from decimal import Decimal
from jobfit.config import REPO_ROOT
from jobfit.eval.metrics import extraction_metrics, evidence_metrics, operational_summary
from jobfit.eval.matching_evaluation import reference_rows
from jobfit.eval.strict_complex_alignment import apply_approved_complex_policy
from jobfit.schemas.analysis import UnitAssessment
from jobfit.scoring.score import effective_label
from scripts.run_cp23_stage2_matching import PLAN,STATE,BUNDLE,inputs,RUN

APPROVAL='evals/results/cp23_stage2_alignment_and_fixed_adapter_approval_20261003_v1.json'
INVENTORY='evals/results/cp23_stage2_v14_observation_inventory_20261003_v3.json'

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def accepted_packet(root=REPO_ROOT):
    receipt=read(root/APPROVAL)
    if (receipt.get('decision_id'),receipt.get('approved_by'),receipt.get('accepted_recommendations'),receipt.get('fixed_input_adapter_accepted'))!=('D-063','Dion',True,True):
        raise ValueError('Exact alignment and fixed-input acceptance required')
    for path,digest in receipt['hashes'].items():
        if sha(root/path)!=digest:raise ValueError('Accepted reference/input changed: '+path)
    return read(root/receipt['packet']),receipt

def summarize():
    packet,receipt=accepted_packet()
    by_model=defaultdict(lambda:dict(tp=0,fp=0,fn=0,cases=0,process_valid=0,
                                    one_to_one=0,category_correct=0,importance_correct=0,case_rows=[]))
    complex_receipt=read(REPO_ROOT/'evals/results/cp23_stage2_complex_alignment_approval_20261003_v1.json')
    for case in packet['cases']:
        model=case.get('model',case['stage_id'].split('/')[0]);m=by_model[model];m['cases']+=1
        if case['status']=='retained_process_failure':
            counts=dict(tp=0,fp=0,fn=case['gold_units']);f1=0.0
        else:
            if sha(REPO_ROOT/case['result_file'])!=read(REPO_ROOT/INVENTORY)['input_hashes'][case['result_file']]:
                raise ValueError('Historical extraction output changed')
            aligned=deepcopy(case)
            aligned['human_verified']=True
            aligned['verification_method']=receipt['verification_method']
            for row in aligned['rows']:
                row['status']='verified';row['semantic_equivalent']=row['recommended_semantic_equivalent']
                if row['relation']=='one_to_one':
                    m['one_to_one']+=1;m['category_correct']+=int(row['same_category']);m['importance_correct']+=int(row['same_importance'])
            if aligned['stage_id']=='claude-haiku-4.5/F00036':
                aligned=apply_approved_complex_policy(aligned,complex_receipt)
            metric=extraction_metrics(aligned,reference_complete=True)
            counts={k:metric[k] for k in ('tp','fp','fn')};f1=metric['f1']['value'];m['process_valid']+=1
        for k,v in counts.items():m[k]+=v
        m['case_rows'].append(dict(stage_id=case['stage_id'],status=case['status'],**counts,f1=f1))
    for model,m in by_model.items():
        m.update(precision=m['tp']/(m['tp']+m['fp']),recall=m['tp']/(m['tp']+m['fn']),
                 f1=2*m['tp']/(2*m['tp']+m['fp']+m['fn']),
                 category_accuracy_one_to_one=m['category_correct']/m['one_to_one'],
                 importance_accuracy_one_to_one=m['importance_correct']/m['one_to_one'],
                 attribute_denominator='all accepted one-to-one relations; not extraction recall')
        if m['tp']+m['fn']!=120 or m['cases']!=7:raise ValueError('Original seven-JD scope changed')
    plan=read(PLAN);state=read(STATE)
    if state['status']!='complete' or len(state['results'])!=16:raise ValueError('Matching collection incomplete')
    mapping={s['stage_id']:s for s in plan['stages']};truth={};pred=defaultdict(dict);matching=defaultdict(list)
    for result in state['results']:
        if sha(REPO_ROOT/result['result_file'])!=result['result_sha256']:raise ValueError('Matching result changed')
        stage=mapping[result['stage_id']];cv,ex=inputs(stage);gold=reference_rows(BUNDLE,stage,cv,ex)
        for unit,label in gold.items():truth['/'.join([stage['cv_id'],stage['job_id'],unit])]=label
        if result['status']=='done':
            by_id={a.unit_id:a for a in map(UnitAssessment.model_validate,result['assessments'])}
            if len(result['assessments'])!=len(ex.units) or set(by_id)!={u.unit_id for u in ex.units}:
                raise ValueError('Assessment coverage changed')
            for unit in ex.units:
                label,status=effective_label(unit,by_id[unit.unit_id])
                key='/'.join([stage['cv_id'],stage['job_id'],unit.unit_id])
                pred[stage['model']][key]=dict(label=label.value if status.value=='done' and label is not None else None,status=status.value)
        matching[stage['model']].append(dict(stage_id=stage['stage_id'],status=result['status'],attempts=result['attempts'],
            error_code=result['error_code'],units=len(gold),stage_wall_ms=result['stage_wall_ms']))
    evidence={model:dict(metrics=evidence_metrics(truth,pred[model],alignment_verified=True),cases=cases,
                process_valid=sum(c['status']=='done' for c in cases),original_cases=len(cases)) for model,cases in matching.items()}
    if len(truth)!=73 or len(evidence)!=4 or any(m['original_cases']!=4 for m in evidence.values()):
        raise ValueError('Common original matching scope changed')
    ledger=[read_line for line in (REPO_ROOT/'reports/usage/usage_ledger.jsonl').read_text().splitlines() if line.strip() for read_line in [json.loads(line)]]
    live=[r for r in ledger if r['run_id']==RUN]
    if sum(c['attempts'] for cases in matching.values() for c in cases)!=len(live):raise ValueError('Ledger-attempt mismatch')
    costs=defaultdict(list)
    registry=read(PLAN)['stages'];aliases={s['model_id']:s['model'] for s in registry}
    for record in live:costs[aliases[record['model']]].append(record)
    return dict(schema_version='cp23-stage2-round1-quality-v1',scope='development only; fixed four pairs, seven whole JDs',
        acceptance_receipt=APPROVAL,verification_method=receipt['verification_method'],extraction=dict(by_model),evidence=evidence,
        evidence_support=dict(Counter(truth.values())),matching_operations={m:operational_summary(r) for m,r in costs.items()},
        matching_cost_usd=str(sum((Decimal(str(r['cost_usd'])) for r in live),Decimal(0))),matching_api_calls=len(live),
        ledger_accounted_usd=str(sum((Decimal(str(r['cost_usd'])) for r in ledger if not r.get('cached')),Decimal(0))),
        project_hard_stop_usd='8.50',matching_ceiling_usd='1.85',winner=None,
        limits=['Evidence uses fixed reviewed requirements, not an end-to-end extraction comparison',
                'Failed matching is not_assessed: gold-class FN, never NO_MATCH or excluded',
                'Gemini/F00815 extraction failure contributes 16 FN on the common original scope',
                'Category accuracy conditional on one-to-one relations; omissions/splits remain in primary F1',
                'Cost/latency include attempts and rejected repairs; one small run is not production timing',
                'Safety/source entailment review and D-029 quality reference remain separate selection gates'],
        hashes={str(PLAN.relative_to(REPO_ROOT)):sha(PLAN),str(STATE.relative_to(REPO_ROOT)):sha(STATE),APPROVAL:sha(REPO_ROOT/APPROVAL)})

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--repair-rerun',action='store_true');args=p.parse_args()
    out=summarize()
    if args.repair_rerun:
        from scripts.analyze_cp23_repair_views import build
        out=build(out)
    with Path(args.output).open('x') as file:json.dump(out,file,indent=2)
    if args.repair_rerun:
        print('Repair comparison saved; API calls in analysis: 0')
        sys.exit(0)
    for model,m in out['extraction'].items():print(model,'extraction F1',round(m['f1'],6),'evidence Macro-F1',round(out['evidence'][model]['metrics']['macro_f1'],6))
    print('matching cost',out['matching_cost_usd'],'calls',out['matching_api_calls'],'ledger',out['ledger_accounted_usd'])
