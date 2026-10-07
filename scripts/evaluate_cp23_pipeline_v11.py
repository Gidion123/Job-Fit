"""D-052 original-position H1/H2 comparison for saved pipeline v1.1 output."""
from __future__ import annotations
import json
from pathlib import Path
import argparse
from hashlib import sha256
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from jobfit.eval.metrics import ranking_metrics
from jobfit.scoring.hold_policy_v11 import score_with_hold_policy
from jobfit.schemas.requirements import JDExtraction
from jobfit.schemas.analysis import UnitAssessment

OLD=ROOT/'evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1'
NEW=ROOT/'evals/results/cp23/pipeline_v11'
GOLD=ROOT/'evals/gold/development_v13_reviewed_20261003_stage1_r3/relevance_gold.jsonl'
OUTPUT=NEW/'evaluation_v1.json'
CONTINUATION_CASES={('CV1','F00022'),('CV2','F00126'),('CV1','F00310'),('CV2','F00310')}


def read(path):return json.loads(path.read_text())


def evaluate(*, include_continuation: bool = False):
    plan=read(NEW/'plan_v1.json')
    if not (NEW/'summary_v1.json').exists():
        raise ValueError('v1.1 run is incomplete; do not publish order metrics')
    ranks=read(OLD/'plan.json')['rankings']
    eligible=(ROOT/'evals/splits/dev_job_ids.txt').read_text().splitlines()
    judged={cv:{} for cv in ranks}
    for line in GOLD.read_text().splitlines():
        row=json.loads(line)
        if row['cv_id'] in judged and row['review_status']=='approved':
            judged[row['cv_id']][row['job_id']]=int(row['relevance_0_3'])
    results=[]
    continuation_sources=[]
    if include_continuation:
        if not (NEW/'hold_continuation_summary_v2.json').exists():
            raise ValueError('The continuation is incomplete')
        for cv,job in CONTINUATION_CASES:
            if not (NEW/f'pair_hold_{cv}_{job}_v11_v2.json').exists():
                raise ValueError(f'Missing continuation pair {cv}/{job}')
    for cv,ranking in ranks.items():
        for depth in [10,20,30]:
            selected=ranking[:depth]
            for policy in ['H1','H2']:
                for weight in [.25,.5,.75]:
                    scores={};missing={};status={}
                    for job in selected:
                        continuation=include_continuation and (cv,job) in CONTINUATION_CASES
                        pair_path=(NEW/f'pair_hold_{cv}_{job}_v11_v2.json' if continuation
                                   else NEW/f'pair_{cv}_{job}_v11.json')
                        pair=read(pair_path)
                        jd_path=(NEW/f'jd_hold_{job}_v11_v2.json' if continuation else
                                 NEW/f'jd_{job}_v11.json' if job in plan['redo_jds'] else OLD/f'jd_{job}.json')
                        if continuation and (cv,job) not in continuation_sources:
                            continuation_sources.append((cv,job))
                        if pair['status']!='done' or not jd_path.exists():
                            missing[job]=pair.get('reason') or pair.get('error_code') or pair['status']
                            continue
                        jd=read(jd_path)
                        if jd['status']!='done' or jd['extraction']['jd_quality']!='ok':
                            missing[job]='held_extraction';continue
                        if pair['source']=='reused_v1_matching':
                            assessments=read(OLD/f'match_{cv}_{job}.json')['assessments']
                        else:assessments=pair['assessments']
                        extraction=JDExtraction.model_validate(jd['extraction'])
                        result,_=score_with_hold_policy(extraction,
                            [UnitAssessment.model_validate(x) for x in assessments],
                            policy=policy,partial_weight=weight)
                        status[job]=result.status.value
                        if result.score_pct is None or result.status.value not in ['final','provisional']:
                            missing[job]=result.status.value
                        else:scores[job]=result.score_pct
                    original5=ranking_metrics(selected,judged[cv],eligible_ids=eligible,k=5)
                    original10=ranking_metrics(selected,judged[cv],eligible_ids=eligible,k=10)
                    if missing:
                        final_order=None;final5=None;final10=None
                        reason='incomplete_original_top_k_scores'
                    else:
                        final_order=sorted(selected,key=lambda j:(-scores[j],selected.index(j)))
                        final5=ranking_metrics(final_order,judged[cv],eligible_ids=eligible,k=5)
                        final10=ranking_metrics(final_order,judged[cv],eligible_ids=eligible,k=10)
                        reason=None
                    results.append({'cv_id':cv,'k':depth,'hold_policy':policy,'partial_weight':weight,
                        'scored':len(scores),'candidate_count':len(selected),'missing_score_ids':missing,
                        'status_by_job':status,'original_ranked_ids':selected,
                        'score_ranked_ids':final_order,'complete_score_order':not bool(missing),
                        'stage1':{'p_at_5':original5['precision_at_k'],'ndcg_at_10':original10['ndcg_at_k'],
                                  'ndcg_reason':original10['ndcg_reason']},
                        'score_order':{'p_at_5':final5['precision_at_k'] if final5 else None,
                                       'ndcg_at_10':final10['ndcg_at_k'] if final10 else None,
                                       'p5_coverage':final5['coverage'] if final5 else None,
                                       'ndcg10_coverage':final10['coverage'] if final10 else None,
                                       'reason':reason or (final10['ndcg_reason'] if final10 else None)}})
    return {'run_id':'cp23_pipeline_v11_evaluation_20261004_v2' if include_continuation else
            'cp23_pipeline_v11_evaluation_20261004_v1','scope':'development_CV1_CV2',
        'protocol':'D-052_original_positions','judged_pool_counts':{k:len(v) for k,v in judged.items()},
        'no_missing_as_zero':True,'product_order_valid':False,
        'continuation_used':[{'cv_id':cv,'job_id':job} for cv,job in sorted(continuation_sources)],
        'source_hashes':{'plan_v1':sha256((NEW/'plan_v1.json').read_bytes()).hexdigest(),
                         'continuation_summary_v2':sha256((NEW/'hold_continuation_summary_v2.json').read_bytes()).hexdigest()
                         if include_continuation else None},
        'product_order_limit':'D-013 constraints and filters are not reconstructed from these stage files',
        'results':results}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--include-continuation',action='store_true')
    args=parser.parse_args()
    if args.include_continuation:
        OUTPUT=NEW/'evaluation_v2.json'
    result=evaluate(include_continuation=args.include_continuation)
    if OUTPUT.exists():raise SystemExit('Versioned evaluation exists')
    with OUTPUT.open('x') as stream:json.dump(result,stream,indent=2)
    print(json.dumps({'cells':len(result['results']),
        'complete':sum(x['complete_score_order'] for x in result['results']),
        'measurable_ndcg':sum(x['score_order']['ndcg_at_10'] is not None for x in result['results'])}))
