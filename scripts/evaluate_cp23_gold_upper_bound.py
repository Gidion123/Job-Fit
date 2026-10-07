"""Gold-input score-order diagnostic. Incomplete top K has no invented score order."""
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'src')]
import json,hashlib
from collections import defaultdict
from jobfit.config import REPO_ROOT as ROOT
from jobfit.schemas.requirements import JDExtraction,RequirementUnit
from jobfit.schemas.analysis import UnitAssessment
from jobfit.scoring.score import compute_score
from jobfit.eval.metrics import ranking_metrics
B=ROOT/'evals/gold/development_v13_reviewed_20261003_stage1_r3'
R=ROOT/'evals/results/cp22_retrieval_top30_20261002_03.json'
def load(p):return json.loads(p.read_text())
def lines(p):return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def score_order(top,values):
    if len(top)!=len(set(top)):raise ValueError('Duplicate job identity')
    if not set(values)<=set(top):raise ValueError('Score outside candidate set')
    if set(values)!=set(top):return None
    return sorted(top,key=lambda j:(-values[j],top.index(j)))

def build():
    A=lines(B/'extraction_gold.jsonl');E=lines(B/'evidence_gold.jsonl');C=lines(B/'relevance_gold.jsonl')
    logical=load(B/'logical_units.json');jd={r['job_id']:r for r in load(B/'JD_coverage.json')}
    pair={(r['cv_id'],r['job_id']):r for r in load(B/'pair_coverage.json')}
    def score(cv,job):
        if job not in jd or not jd[job]['all_retained_rows_exportable']:return None,'A absent or retained source/compatibility hold'
        if (cv,job) not in pair or not pair[cv,job]['complete_existing_reviewed_units']:return None,'B absent or incomplete reviewed units'
        aa={r['unit_no']:r for r in A if r['job_id']==job};bb={r['unit_no']:r for r in E if r['cv_id']==cv and r['job_id']==job}
        if set(aa)!=set(bb):return None,'A/B identity coverage differs'
        units=[];assess=[];seen=set();rank={'NO_MATCH':0,'PARTIAL':1,'MATCH':2}
        for g in [g for g in logical if g['job_id']==job]:
            ids=g['row_ids']
            if g['status']!='ready' or g['count_as']!=1 or seen.intersection(ids) or not set(ids)<=set(aa):return None,'Logical mapping unavailable'
            seen.update(ids);rows=[aa[i] for i in ids]
            if len({(r['importance'],r['category'],r['min_years']) for r in rows})!=1:return None,'Logical attributes conflict'
            if any(bb[i]['check_status'] not in ['done','needs_clarification'] or bb[i]['label'] not in rank for i in ids):return None,'Gold not assessed'
            row=rows[0];uid=g['logical_unit_id']
            # Gold already stores the reviewed logical label; multirow OR uses best branch.
            lab=max((bb[i]['label'] for i in ids),key=rank.get)
            units.append(RequirementUnit(unit_id=uid,text=' | '.join(r['unit_text'] for r in rows),field=row['category'],importance=row['importance'],
                min_years=row['min_years'],source_quotes=g['source_quotes']))
            assess.append(UnitAssessment(unit_id=uid,label=lab,check_status='done',cv_quotes=[bb[i]['cv_quote'] for i in ids if bb[i]['label']==lab and bb[i].get('cv_quote')] if lab!='NO_MATCH' else []))
        if seen!=set(aa):return None,'Logical map omits rows'
        result=compute_score(JDExtraction(job_id=job,units=units),assess).model_dump(mode='json')
        return (result,None) if result['score_pct'] is not None else (None,'Score '+result['status'])
    rows=[]
    for run in load(R)['runs']:
        cv=run['cv_id'];judgments={r['job_id']:r['relevance_0_3'] for r in C if r['cv_id']==cv}
        for k in [10,20,30]:
            top=run['ranking'][:k];scores={};missing=[]
            for j in top:
                value,reason=score(cv,j)
                if value:scores[j]=value
                else:missing.append({'job_id':j,'original_rank':top.index(j)+1,'status':'not_analyzed','reason':reason})
            for w in [.25,.5,.75]:
                values={j:round((s['matched']+w*s['partial'])/s['required_total']*100,2) for j,s in scores.items()}
                ordered=score_order(top,values)
                metrics=lambda order:{'P@5':ranking_metrics(order,judgments,eligible_ids=run['eligible_ids'],k=5),
                    'NDCG@10':ranking_metrics(order,judgments,eligible_ids=run['eligible_ids'],k=10)}
                rows.append({'cv_id':cv,'method':run['method'],'k':k,'partial_weight':w,'original_order':top,
                    'gold_score_order':ordered,'original_metrics':metrics(top),'score_order_metrics':metrics(ordered) if ordered else None,
                    'scores':values,'score_components':scores,'not_analyzed':missing,
                    'status':'measured' if ordered else 'unavailable_incomplete_gold_top_k',
                    'reason':None if ordered else 'No authorized order for unscored jobs. Keep original IDs visible; no dropping or implicit zero.'})
    return {'run_id':'cp23_gold_input_upper_bound_20261004_v1','scope':'CV1/CV2 development, six methods, original K=10/20/30',
        'api_calls':0,'winner':None,'rows':rows,'complete_ordering_cells':sum(r['status']=='measured' for r in rows),'cells':len(rows),
        'limits':['Upper bound conditional on reviewed inventory, not perfect coverage of every source and not a system result.',
            'Record-level gold is not universal whole-JD completeness.',
            'No score assigned to held/missing A/B; entire score ordering unavailable if one candidate cannot be scored.',
            'Runtime PARTIAL remains 0.5; other weights are offline arithmetic sensitivity from identical scorer counts.',
            'No optional filter or constraint-based ordering was added.'],
        'hashes':{str(p.relative_to(ROOT)):sha(p) for p in [R,*[B/n for n in ['extraction_gold.jsonl','evidence_gold.jsonl','relevance_gold.jsonl','logical_units.json','JD_coverage.json','pair_coverage.json']]]}}
if __name__=='__main__':
    r=build()
    with (ROOT/'evals/results/cp23_gold_input_upper_bound_20261004_v1.json').open('x') as f:json.dump(r,f,indent=2)
    print('Complete ordering cells',r['complete_ordering_cells'],'/',r['cells'])
