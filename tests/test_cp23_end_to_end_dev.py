"""No-network checks for the capped, development-only CP2.3 runner."""
import json

from datetime import datetime, timezone, timedelta
import pytest
from scripts.run_cp23_end_to_end_dev import CAP, RUN, OUT, plan, hold_unresolved_structure, check_deadline, PartBDeadlineReached
from scripts.evaluate_cp23_end_to_end_dev import assessment_gate, final_order_metrics
from jobfit.config import REPO_ROOT
from jobfit.schemas.analysis import ScoreResult, ScoreStatus
from types import SimpleNamespace


def test_part_b_plan_uses_only_locked_development_and_approved_cap():
    item=plan()
    dev=set((REPO_ROOT/'evals/splits/dev_job_ids.txt').read_text().splitlines())
    test=set((REPO_ROOT/'evals/splits/test_job_ids.txt').read_text().splitlines())
    jobs=set().union(*map(set,item['rankings'].values()))
    assert item['run_id']==RUN
    assert item['approved_cap_usd']==CAP==2.5
    assert item['estimate_medians_x_1_5_usd']<=CAP
    assert jobs<=dev and jobs.isdisjoint(test)
    assert set(item['rankings'])=={'CV1','CV2'}
    assert item['cv_job_pairs']==60
    assert item['model']=='deepseek-flash'
    assert item['validator']=='quote-check-v1.1'
    assert item['guardrails']==['G1','G2']
    assert item['masking']=='local-pattern-masking-v1'


def test_part_b_saved_plan_preserves_source_hashes():
    path=REPO_ROOT/'evals/results/cp23/end_to_end_dev'/RUN/'plan.json'
    if path.exists():
        saved=json.loads(path.read_text())
        current=plan()
        assert saved['protected_sha256']==current['protected_sha256']
        assert saved['rankings']==current['rankings']


def test_resume_has_only_unsaved_pairs_and_keeps_timeout_records():
    saved=json.loads((OUT/'plan.json').read_text())
    remaining={(cv,job) for cv,jobs in saved['rankings'].items() for job in jobs
               if not (OUT/f'match_{cv}_{job}.json').exists()}
    assert len(remaining)<=31
    assert ('CV1','F00129') in remaining or (OUT/'match_CV1_F00129.json').exists()
    assert ('CV1','F00601') not in remaining
    assert ('CV1','F00650') not in remaining
    receipt=json.loads((OUT/'cap_and_deadline_amendment_v2.json').read_text())
    assert receipt['approved_total_cap_usd']==CAP
    assert receipt['remaining_policy']=='only_unsaved_pairs_no_timeout_replay'
    assert receipt['cutoff_utc']=='2026-10-04T04:00:00Z'


def test_presentation_cutoff_stops_before_six_minute_stage_window():
    now=datetime.now(timezone.utc)
    with pytest.raises(PartBDeadlineReached): check_deadline(now+timedelta(minutes=5))
    check_deadline(now+timedelta(minutes=8))


def test_evaluation_holds_unresolved_structure_and_failed_matching():
    jd={'status':'done','extraction':{'jd_quality':'ok','units':[{'needs_review':True}]}}
    assert assessment_gate({'status':'done'},jd)=='held_structure_review'
    jd['extraction']['units'][0]['needs_review']=False
    assert assessment_gate({'status':'failed'},jd)=='held_matching'
    assert assessment_gate({'status':'done'},jd) is None
    jd['extraction']['jd_quality']='looks_incomplete'
    assert assessment_gate({'status':'done'},jd)=='held_incomplete_jd'


def test_part_b_never_publishes_percentage_for_unresolved_composite():
    score=ScoreResult(status=ScoreStatus.FINAL,score_pct=80,required_total=5)
    unresolved=SimpleNamespace(units=[SimpleNamespace(needs_review=True)])
    held=hold_unresolved_structure(unresolved,score)
    assert held.status is ScoreStatus.ON_HOLD and held.score_pct is None
    assert held.required_total==5 and score.score_pct==80
    resolved=SimpleNamespace(units=[SimpleNamespace(needs_review=False)])
    assert hold_unresolved_structure(resolved,score) is score


def test_incomplete_matching_never_promotes_a_deeper_result_into_primary_top_five():
    ids=[f'F{i:05d}' for i in range(10)]
    judgments={job:(2 if n in (0,2,4) else 0) for n,job in enumerate(ids)}
    scores={job:100-n for n,job in enumerate(ids) if n!=1}
    order,primary,diagnostic=final_order_metrics(ids,scores,judgments,ids)
    assert len(order)==9 and order[1]==ids[2]
    assert primary['p_at_5'] is None and primary['ndcg_at_10'] is None
    assert primary['p5_reason']=='incomplete_top_k_analysis'
    assert diagnostic['not_a_primary_H4_metric']
    scores[ids[1]]=99
    _,primary,_=final_order_metrics(ids,scores,judgments,ids)
    assert primary['p_at_5']['value']==0.6
