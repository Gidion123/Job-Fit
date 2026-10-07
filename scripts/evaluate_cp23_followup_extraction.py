"""Accepted D-064 mappings, with separate seven-JD and common-four-JD tables."""
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'src')]
import argparse,hashlib,json
from copy import deepcopy
from collections import defaultdict
from jobfit.config import REPO_ROOT
from jobfit.eval.metrics import extraction_metrics
from scripts.evaluate_cp23_stage2_round1 import accepted_packet, summarize as recompute_round1

PACKET=REPO_ROOT/'evals/results/cp23_stage2_followup_alignment_review_20261003_v1.json'
APPROVAL=REPO_ROOT/'evals/results/cp23_stage2_followup_alignment_acceptance_20261003_v1.json'
ROUND1=REPO_ROOT/'evals/results/cp23_stage2_round1_quality_evaluation_20261003_v1.json'
COMMON={'F00332','F00036','F00815','F00018'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def aggregate(rows,expected_gold):
    tp=sum(r['tp'] for r in rows);fp=sum(r['fp'] for r in rows);fn=sum(r['fn'] for r in rows)
    if tp+fn!=expected_gold:raise ValueError('Reference denominator changed')
    return dict(tp=tp,fp=fp,fn=fn,gold_units=expected_gold,cases=len(rows),
        precision=tp/(tp+fp) if tp+fp else 0,recall=tp/(tp+fn),f1=2*tp/(2*tp+fp+fn))

def evaluate():
    accepted_packet()  # Previous candidate/reference acceptance remains valid.
    receipt=json.loads(APPROVAL.read_text())
    if receipt.get('approved_by')!='Dion' or receipt.get('accepted_recommendations') is not True or receipt.get('packet_sha256')!=sha(PACKET):
        raise ValueError('Exact new candidate alignment acceptance required')
    packet=json.loads(PACKET.read_text())
    for path,digest in packet['source_hashes'].items():
        if sha(REPO_ROOT/path)!=digest:raise ValueError('Reviewed alignment input changed: '+path)
    models=defaultdict(list);attrs=defaultdict(lambda:dict(one_to_one=0,category_correct=0,importance_correct=0))
    for original in packet['cases']:
        case=deepcopy(original)
        if case['status']=='retained_process_failure':counts=dict(tp=0,fp=0,fn=case['gold_units'])
        else:
            case['human_verified']=True
            case['verification_method']=receipt['verification_method']
            for row in case['rows']:
                row.update(status='verified',semantic_equivalent=row['recommended_semantic_equivalent'])
                if row['relation']=='one_to_one':
                    a=attrs[case['model']];a['one_to_one']+=1;a['category_correct']+=row['same_category'];a['importance_correct']+=row['same_importance']
            metrics=extraction_metrics(case,reference_complete=True);counts={k:metrics[k] for k in ['tp','fp','fn']}
        models[case['model']].append(dict(stage_id=case['stage_id'],job_id=case['job_id'],status=case['status'],**counts))
    if {m:len(r) for m,r in models.items()}!={'gpt-6-sol':4,'deepseek-v4-pro':7}:raise ValueError('Original candidate scope changed')
    prior=json.loads(ROUND1.read_text())
    if prior['extraction']!=recompute_round1()['extraction']:
        raise ValueError('Round-one extraction table differs from its accepted underlying outputs')
    full7={m:aggregate(r['case_rows'],120) for m,r in prior['extraction'].items()}
    full7['deepseek-v4-pro']=aggregate(models['deepseek-v4-pro'],120)
    common4={m:aggregate([c for c in r['case_rows'] if c['stage_id'].split('/')[-1] in COMMON],73) for m,r in prior['extraction'].items()}
    common4.update({m:aggregate([c for c in r if c['job_id'] in COMMON],73) for m,r in models.items()})
    for m,a in attrs.items():a['category_accuracy_one_to_one']=a['category_correct']/a['one_to_one'];a['importance_accuracy_one_to_one']=a['importance_correct']/a['one_to_one']
    return dict(schema_version='cp23-followup-extraction-v1',full_seven_JD=full7,common_four_JD=common4,
        new_case_results=dict(models),new_attribute_accuracy=dict(attrs),acceptance_receipt=str(APPROVAL.relative_to(REPO_ROOT)),
        verification_method=receipt['verification_method'],winner=None,
        hashes={str(p.relative_to(REPO_ROOT)):sha(p) for p in [PACKET,APPROVAL,ROUND1]},
        limits=['Common-four contains the original Gemini failure; no survivor filtering.',
            'D-064 uses a new repair format; results compare tested model/protocol combinations, not isolated model capability.',
            'Attribute accuracy is conditional on one-to-one mappings; category effects on scoring remain important.',
            'Source-supported opening statements outside fixed gold still count as FP; FP does not imply fabrication.',
            'Candidate alignment is accepted assisted QA, not independent human annotation.',
            'Safety and matching gates remain separate from extraction F1.'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);a=p.parse_args()
    out=evaluate()
    with Path(a.output).open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(dict(full7=out['full_seven_JD'],common4=out['common_four_JD'])))
