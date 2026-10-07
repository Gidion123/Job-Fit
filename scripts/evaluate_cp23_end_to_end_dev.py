"""D-052 metrics for actual Part B outputs, without filling missing labels."""
from __future__ import annotations

import json
import argparse
from pathlib import Path
import sys

sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1]/'src')]

from jobfit.config import REPO_ROOT
from jobfit.eval.metrics import ranking_metrics
from jobfit.schemas.analysis import UnitAssessment
from jobfit.schemas.requirements import JDExtraction
from jobfit.scoring.score import compute_score
from scripts.run_cp23_end_to_end_dev import OUT, RUN

GOLD = REPO_ROOT/'evals/gold/development_v13_reviewed_20261003_stage1_r3/relevance_gold.jsonl'
DEV = REPO_ROOT/'evals/splits/dev_job_ids.txt'
OUTPUT = REPO_ROOT/'evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1_evaluation.json'


def load_json(path):
    return json.loads(path.read_text())


def assessment_gate(record, jd):
    """Do not publish a percentage when source structure or matching is unresolved."""
    if jd.get('status') != 'done' or not jd.get('extraction'):
        return 'held_extraction'
    extraction = jd['extraction']
    if extraction.get('jd_quality') != 'ok':
        return 'held_incomplete_jd'
    if any(unit.get('needs_review') for unit in extraction.get('units', [])):
        return 'held_structure_review'
    if record.get('status') != 'done':
        return 'held_matching'
    return None


def final_order_metrics(selected, scores, judgments, eligible):
    """Do not let incomplete matching shift a lower rank into a metric slot."""
    order=sorted(scores,key=lambda j:(-scores[j],selected.index(j)))
    subset5=ranking_metrics(order,judgments,eligible_ids=eligible,k=5)
    subset10=ranking_metrics(order,judgments,eligible_ids=eligible,k=10)
    diagnostic={'p_at_5':subset5['precision_at_k'],'ndcg_at_10':subset10['ndcg_at_k'],
                'scored_candidates':len(order),'not_a_primary_H4_metric':True}
    if len(order)!=len(selected):
        return order, {'p_at_5':None,'ndcg_at_10':None,
                       'p5_reason':'incomplete_top_k_analysis','ndcg_reason':'incomplete_top_k_analysis',
                       'p5_coverage':None,'ndcg10_coverage':None}, diagnostic
    return order, {'p_at_5':subset5['precision_at_k'],'ndcg_at_10':subset10['ndcg_at_k'],
                   'p5_reason':None,'ndcg_reason':subset10['ndcg_reason'],
                   'p5_coverage':subset5['coverage'],'ndcg10_coverage':subset10['coverage']}, diagnostic


def evaluate():
    p=load_json(OUT/'plan.json')
    summary_path=OUT/'summary.json'
    source_run_status=load_json(summary_path).get('status') if summary_path.exists() else 'partial_or_stopped'
    eligible=DEV.read_text().splitlines()
    judgments={cv:{} for cv in p['rankings']}
    for line in GOLD.read_text().splitlines():
        item=json.loads(line)
        if item['cv_id'] in judgments and item['review_status']=='approved':
            judgments[item['cv_id']][item['job_id']]=int(item['relevance_0_3'])
    results=[]
    for cv_id, original in p['rankings'].items():
        for depth in (10,20,30):
            selected=original[:depth]
            for weight in (.25,.5,.75):
                scores={}; statuses={}
                for job in selected:
                    path=OUT/f'match_{cv_id}_{job}.json'
                    jd_path=OUT/f'jd_{job}.json'
                    if not path.exists() or not jd_path.exists():
                        statuses[job]='not_attempted';continue
                    record,jd=load_json(path),load_json(jd_path)
                    hold=assessment_gate(record,jd)
                    if hold:
                        statuses[job]=hold;continue
                    extraction=JDExtraction.model_validate(jd['extraction'])
                    assessments=[UnitAssessment.model_validate(x) for x in record['assessments']]
                    score=compute_score(extraction,assessments,partial_weight=weight)
                    statuses[job]=score.status.value
                    if score.score_pct is not None and score.status.value in ('final','provisional'):
                        scores[job]=score.score_pct
                # Diagnostic score order only. The product's D-013 constraint
                # groups are not reconstructed from these saved stage outputs.
                # Failed/unassessed jobs are separate, never zero-score entries.
                final, final_metrics, subset_diagnostic = final_order_metrics(
                    selected,scores,judgments[cv_id],eligible)
                stage5=ranking_metrics(selected,judgments[cv_id],eligible_ids=eligible,k=5)
                stage10=ranking_metrics(selected,judgments[cv_id],eligible_ids=eligible,k=10)
                results.append({'cv_id':cv_id,'candidate_k':depth,'partial_weight':weight,
                    'candidate_ids':selected,'scored':len(final),'held_or_failed':len(selected)-len(final),
                    'held_ids':[j for j in selected if j not in scores],
                    'status_by_job':statuses,'final_ranked_ids':final,'scores_pct':scores,
                    'stage1':{'p_at_5':stage5['precision_at_k'],'ndcg_at_10':stage10['ndcg_at_k'],
                              'ndcg_reason':stage10['ndcg_reason']},
                    'final':final_metrics,'scored_subset_diagnostic':subset_diagnostic})
    return {'run_id':RUN,'protocol':'D-052_original_positions_same_judged_pool',
        'scope':'development_only','source_run_status':source_run_status,
        'model_or_k_winner_selected':False,'eligible_jobs':len(eligible),
        'judgments_by_cv':{c:len(v) for c,v in judgments.items()},
        'score_order_policy':'final metrics require every original top-K candidate scored; held jobs are never skipped or zero',
        'product_order_valid':False,
        'product_order_limit':'D-013 constraint groups and optional filters are not reconstructed from saved Part B stages',
        'results':results,'test_access':False,'gold_written':False,
        'interpretation_limit':'K/weight cannot be selected when metric coverage or processing is insufficient'}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=OUTPUT)
    args=parser.parse_args()
    output=args.output
    if not output.is_absolute(): output=REPO_ROOT/output
    if output.exists(): raise SystemExit('Versioned output already exists; do not overwrite')
    result=evaluate()
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as f: json.dump(result,f,indent=2,ensure_ascii=False)
    print(json.dumps({'cells':len(result['results']),'judgments':result['judgments_by_cv'],
                      'output':str(output.relative_to(REPO_ROOT))}))
