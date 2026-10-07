"""Read-only identity and exact-quote audit of saved Part B development outputs."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from scripts.run_batch_extraction import development_sources

RUN=ROOT/'evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1'
OUTPUT=ROOT/'evals/results/cp23/end_to_end_dev/cp23_partb_saved_quote_audit_20261004_v1.json'


def audit():
    plan=json.loads((RUN/'plan.json').read_text())
    dev=set((ROOT/'evals/splits/dev_job_ids.txt').read_text().splitlines())
    jobs=set().union(*(set(v) for v in plan['rankings'].values()))
    if not jobs<=dev or set(plan['rankings'])!={'CV1','CV2'}:
        raise ValueError('Development-only identity changed')
    source={r['job_id']:r['text'] for r in development_sources(sorted(jobs))}
    cv={c:json.loads((RUN/f'{c}_parse.json').read_text())['parsed']['profile']['raw_text']
        for c in ('CV1','CV2')}
    counts=Counter();faults=[]
    for path in sorted(RUN.glob('match_*.json')):
        row=json.loads(path.read_text());c,j=row['cv_id'],row['job_id']
        if c not in cv or j not in jobs: faults.append((c,j,'identity'));continue
        if row['status']!='done': continue
        counts['matching_done']+=1
        jd=json.loads((RUN/f'jd_{j}.json').read_text())['extraction']
        units=jd['units'];assessments=row['assessments']
        if {u['unit_id'] for u in units}!={a['unit_id'] for a in assessments}:
            faults.append((c,j,'unit_identity'))
        for u in units:
            counts['units']+=1
            for quote in u['source_quotes']:
                counts['jd_quotes']+=1
                if quote not in source[j]: faults.append((c,j,'jd_quote'))
        for a in assessments:
            counts['assessments']+=1
            for item in [a,*a['branches']]:
                for quote in item['cv_quotes']:
                    counts['cv_quotes']+=1
                    if quote not in cv[c]: faults.append((c,j,'cv_quote'))
    return {'scope':'development_only','run_id':plan['run_id'],
            'plan_sha256':sha256((RUN/'plan.json').read_bytes()).hexdigest(),
            'counts':dict(counts),'faults':[{'cv_id':c,'job_id':j,'kind':k} for c,j,k in faults],
            'semantic_entailment_approved':False,
            'limit':'Exact occurrence and identity only; a quote may still fail to support a model label.'}


if __name__=='__main__':
    result=audit()
    if OUTPUT.exists(): raise SystemExit('Versioned audit exists; do not overwrite')
    with OUTPUT.open('x') as f: json.dump(result,f,indent=2)
    print(json.dumps({'counts':result['counts'],'faults':len(result['faults'])}))
    if result['faults']: raise SystemExit(1)
