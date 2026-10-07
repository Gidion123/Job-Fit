"""Technical source and score-receipt audit of saved v1.1 development stages."""
from __future__ import annotations
from collections import Counter
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from scripts.run_batch_extraction import development_sources

OLD=ROOT/'evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1'
NEW=ROOT/'evals/results/cp23/pipeline_v11'
OUTPUT=NEW/'technical_qa_v1.json'
CONTINUATION={('CV1','F00022'),('CV2','F00126'),('CV1','F00310'),('CV2','F00310')}


def read(path):return json.loads(path.read_text())


def audit(*, include_continuation=False):
    if include_continuation and not (NEW/'hold_continuation_summary_v2.json').exists():
        raise ValueError('Continuation is incomplete')
    plan=read(NEW/'plan_v1.json')
    ranks=read(OLD/'plan.json')['rankings']
    source={r['job_id']:r['text'] for r in development_sources(sorted(set(sum(ranks.values(),[]))))}
    cvs={cv:read(OLD/f'{cv}_parse.json')['parsed']['profile']['raw_text'] for cv in ranks}
    counts=Counter();faults=[];status=Counter()
    for cv,rank in ranks.items():
        for job in rank:
            continued=include_continuation and (cv,job) in CONTINUATION
            pair=read(NEW/f'pair_hold_{cv}_{job}_v11_v2.json' if continued else
                      NEW/f'pair_{cv}_{job}_v11.json')
            counts['pairs']+=1
            status[(pair.get('score_H2') or {}).get('status') or pair['status']]+=1
            if (pair['cv_id'],pair['job_id'])!=(cv,job):faults.append([cv,job,'pair_identity'])
            jdpath=(NEW/f'jd_hold_{job}_v11_v2.json' if continued else
                    NEW/f'jd_{job}_v11.json' if job in plan['redo_jds'] else OLD/f'jd_{job}.json')
            if not jdpath.exists():continue
            jd=read(jdpath);raw=jd.get('extraction')
            if not raw:continue
            if raw['job_id']!=job:faults.append([cv,job,'jd_identity'])
            units=raw['units'];unitids={u['unit_id'] for u in units}
            for unit in units:
                counts['unit_occurrences']+=1
                for quote in unit['source_quotes']:
                    counts['jd_quote_occurrences']+=1
                    if quote not in source[job]:faults.append([cv,job,'jd_quote'])
            if pair['status']!='done':continue
            assessments=(read(OLD/f'match_{cv}_{job}.json')['assessments']
                         if pair['source']=='reused_v1_matching' else pair['assessments'])
            if unitids!={x['unit_id'] for x in assessments}:faults.append([cv,job,'unit_identity'])
            for assessment in assessments:
                for item in [assessment,*assessment.get('branches',[])]:
                    for quote in item['cv_quotes']:
                        counts['cv_quote_occurrences']+=1
                        if quote not in cvs[cv]:faults.append([cv,job,'cv_quote'])
            excluded=pair['excluded_needs_review']
            if excluded:
                if any(x['unit_id'] not in unitids or not next(u for u in units if u['unit_id']==x['unit_id'])['needs_review']
                       for x in excluded):faults.append([cv,job,'invalid_exclusion'])
                if pair['score_H2']['score_pct'] is not None and pair['score_H2']['status']!='provisional':
                    faults.append([cv,job,'excluded_score_not_provisional'])
                counts['excluded_unit_occurrences']+=len(excluded)
    return {'scope':'development_CV1_CV2','run_id':plan['run_id'],
        'continuation_included':include_continuation,'counts':dict(counts),
        'H2_status_counts':{str(k):v for k,v in status.items()},
        'faults':[{'cv_id':c,'job_id':j,'kind':kind} for c,j,kind in faults],
        'semantic_approval':False,
        'limit':'Exact source occurrence and identity are technical checks, not evidence entailment or complete JD interpretation.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--include-continuation',action='store_true')
    args=parser.parse_args()
    if args.include_continuation:OUTPUT=NEW/'technical_qa_v2.json'
    result=audit(include_continuation=args.include_continuation)
    if OUTPUT.exists():raise SystemExit('Versioned audit exists')
    with OUTPUT.open('x') as stream:json.dump(result,stream,indent=2)
    print(json.dumps({'counts':result['counts'],'faults':len(result['faults'])}))
    if result['faults']:raise SystemExit(1)
