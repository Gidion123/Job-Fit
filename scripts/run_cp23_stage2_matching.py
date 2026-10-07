"""Four fixed development pairs x four models. Default: zero-call preflight.

Execution requires an exact plan-bound human approval, existing ledger and a
durable aggregate cap. Complete stages resume; an interrupted request does not.
"""
from pathlib import Path
import sys
sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1]/'src')]
import argparse
from datetime import date
import fcntl
import hashlib
import json
import time
from jobfit.config import REPO_ROOT, get_settings
from jobfit.cv.parser import ParsedCV
from jobfit.cv.text_extract import extract_text
from jobfit.schemas.cv import CVProfile
from jobfit.eval.fixed_requirements import fixed_reviewed_requirements
from jobfit.eval.stage2_route_repair import RouteClient
from jobfit.eval.stage2_matching import MatchingClient, MatchingSession, require_approval, sha
from jobfit.matching.evidence_matcher import match_evidence
from scripts.prepare_cp23_stage2_matching import prepare
from scripts.run_batch_extraction import development_sources, atomic_report

RUN = 'cp23_stage2_fixed_matching_20261003_v1'
PLAN = REPO_ROOT/'evals/results'/f'{RUN}_plan.json'
STATE = REPO_ROOT/'reports/quality_probe'/f'{RUN}.json'
APPROVAL = REPO_ROOT/'evals/results'/f'{RUN}_approval.json'
BUNDLE = REPO_ROOT/'evals/gold/development_v13_reviewed_20261003_stage1_r3'


def plan():
    result = prepare()
    for s in result['stages']:
        s['stage_id'] = '/'.join([s['model'], s['cv_id'], s['job_id']])
    protected = ['config/models_v1.yaml', 'config/pipeline_v1.yaml', 'evals/annotation_guideline_v1_3.md',
        'prompts/evidence_matching_v1_1.md', 'src/jobfit/matching/evidence_matcher.py',
        'src/jobfit/llm/client.py', 'src/jobfit/llm/probe.py', 'src/jobfit/llm/structured.py',
        'src/jobfit/eval/stage2_route_repair.py', 'src/jobfit/eval/stage2_matching.py',
        'src/jobfit/eval/fixed_requirements.py', 'scripts/prepare_cp23_stage2_matching.py',
        'scripts/run_cp23_stage2_matching.py', 'evals/splits/dev_job_ids.txt',
        'data/processed/jobs_features.jsonl', 'evals/results/cp23_stage1_case_candidates_20261003_v4.json']
    result.update(run_id=RUN, source_hashes={p:sha(REPO_ROOT/p) for p in protected},
        ceiling_usd='1.85', request_adaptation='GPT only: omit unsupported temperature; allow published dated response ID',
        process_failure_policy='retain settled invalid outputs and continue; no repeat of failed stages',
        stop_conditions=['input/code/config/plan hash mismatch','uncertain cost or unresolved request',
                         'aggregate ceiling or project hard stop','unexpected stage identity'],
        semantic_review='all final positive evidence claims require source review before safety/quality selection')
    return result


def inputs(stage):
    job = stage['job_id']
    text = development_sources([job])[0]['text']
    extraction = fixed_reviewed_requirements(BUNDLE, job, text)
    if stage['cv_id'] == 'CV1':
        cv = ParsedCV.model_validate(json.loads((REPO_ROOT/'evals/results/cp22_extraction_repair_v13_20261003_02.json').read_text())['parsed_cv'])
    else:
        path = REPO_ROOT/'data/synthetic_cvs/cv_02_career_switcher_ai_engineer_en.md'
        cv = ParsedCV(profile=CVProfile(cv_id='CV2', is_synthetic=True, raw_text=extract_text(path.read_bytes(),path.name).text), analysis_date=date(2026,9,30))
    digest = hashlib.sha256(json.dumps(extraction.model_dump(mode='json'),sort_keys=True).encode()).hexdigest()
    if digest != stage['fixed_requirements_sha256']:
        raise ValueError('Fixed input changed')
    return cv, extraction


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--stages', type=int, default=1, help='Maximum consecutive original stages this invocation')
    args = parser.parse_args()
    if not 1 <= args.stages <= 16:
        raise ValueError('Invalid stage count')
    rebuilt = plan()
    if PLAN.exists():
        if json.loads(PLAN.read_text()) != rebuilt:
            raise ValueError('Frozen matcher plan changed; do not reset it')
    else:
        with PLAN.open('x') as f: json.dump(rebuilt,f,indent=2)
    print(json.dumps({'status':'preflight','stages':16,'maximum_calls':32,'bound_usd':rebuilt['conservative_upper_usd'],'ceiling_usd':'1.85'}),flush=True)
    if not args.execute: return
    require_approval(PLAN, APPROVAL)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with STATE.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        client = RouteClient(get_settings(), run_id=RUN)
        session = MatchingSession(STATE, run_id=RUN, fingerprint=sha(PLAN),
            jobs=[s['stage_id'] for s in rebuilt['stages']], ledger=client.ledger, ceiling='1.85')
        if session.data['status'] not in {'ready','complete'} or session.data.get('transport_uncertain'):
            raise ValueError('Interrupted or uncertain matcher state; never redispatch')
        if session.data['status']=='complete': return
        remaining = sum(s['conservative_upper_usd'] for s in rebuilt['stages'][len(session.data['results']):])
        client.guard.check(remaining)
        session.check_budget(remaining)
        if not client.verify_inference_key()['inference_key']:
            raise ValueError('Inference key is not ordinary')
        for _ in range(args.stages):
            if session.data['status']!='ready': break
            s = rebuilt['stages'][len(session.data['results'])]
            # Detect mutations before each new dispatch, not only at program entry.
            if plan()!=rebuilt: raise ValueError('Plan inputs changed')
            cv, ex = inputs(s)
            session.begin(s['stage_id'])
            start = time.perf_counter()
            out = match_evidence(cv,ex,client=MatchingClient(client,session,s),model=s['model'],
                duration_years=s['duration_input'],cache=None)
            records = [r for r in client.ledger.records() if r.run_id==RUN]
            result = dict(stage_id=s['stage_id'],model=s['model'],cv_id=s['cv_id'],job_id=s['job_id'],
                status=out.status,attempts=out.attempts,error_code=out.error_code,
                assessments=[a.model_dump(mode='json') for a in out.assessments],
                stage_wall_ms=round((time.perf_counter()-start)*1000),
                fixed_requirements_sha256=s['fixed_requirements_sha256'],
                semantic_review='pending',metrics=None)
            target = REPO_ROOT/'evals/results'/f'{RUN}_{len(session.data["results"])+1:02d}.json'
            if target.exists(): raise ValueError('Existing stage result must not be overwritten')
            with target.open('x') as f: json.dump(result,f,indent=2,ensure_ascii=False)
            result.update(result_file=str(target.relative_to(REPO_ROOT)), result_sha256=sha(target))
            session.finish_matching(result)
            print(json.dumps({k:result[k] for k in ['stage_id','status','attempts','error_code']},ensure_ascii=False),flush=True)
            if session.data['status']=='stopped_uncertain_cost': break
        print(json.dumps({'session_status':session.data['status'],'completed':len(session.data['results']),
                          'spent_usd':str(session.spent())}),flush=True)


if __name__=='__main__':main()
