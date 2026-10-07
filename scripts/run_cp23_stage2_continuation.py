"""Preflight the 27 unrun v1.4 extraction cases; paid mode needs new approval.

The prior DeepSeek/F00332 result is a separately frozen semantic failure. Each
new case needs a source check before the next dispatch. Semantic failures count
as failures and remain in the comparison; process/transport failures stop.
"""
from pathlib import Path
import sys
sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1]/'src')]

import argparse
from decimal import Decimal
import fcntl
import hashlib
import json
import time

from jobfit.config import REPO_ROOT, get_settings
from jobfit.eval.stage2_continuation import (V5_RUN, Stage2ComparisonClient,
                                             Stage2ComparisonSession, build_continuation_plan)
from jobfit.extraction.audited import ExtractionSpec
from jobfit.extraction.jd_extractor import extract_jd
from jobfit.llm.client import OpenRouterClient
from scripts.run_batch_extraction import development_sources

RUN_ID = V5_RUN
PLAN = REPO_ROOT/'evals/results'/f'{RUN_ID}_preflight.json'
STATE = REPO_ROOT/'reports/quality_probe'/f'{RUN_ID}.json'
SPEC = ExtractionSpec(REPO_ROOT/'prompts/jd_extraction_v1_4_experimental.md', 'jd-prompt-v1.4-experimental')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def approved_receipt(path: Path, plan: dict, plan_sha256: str) -> Decimal:
    receipt = json.loads(path.read_text())
    required = {'decision': 'approved', 'approved_by': 'Dion', 'scope': RUN_ID,
                'plan_sha256': plan_sha256}
    if any(receipt.get(k) != v for k,v in required.items()):
        raise ValueError('Distinct continuation approval does not match the frozen plan')
    cap = Decimal(str(receipt['aggregate_cap_usd']))
    if not cap.is_finite() or cap < Decimal(plan['conservative_upper_usd']) or cap > Decimal('3.16'):
        raise ValueError('Continuation cap cannot cover all remaining cases')
    return cap


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--execute', action='store_true')
    mode.add_argument('--record-check', type=Path)
    parser.add_argument('--approval-receipt', type=Path)
    args = parser.parse_args()

    cases = json.loads((REPO_ROOT/'evals/results/cp23_stage1_case_candidates_20261003_v4.json').read_text())
    ids = [x['job_id'] for x in cases['cases']]
    sources = {r['job_id']:r['text'] for r in development_sources(ids)}
    plan = build_continuation_plan(REPO_ROOT, sources)
    if not PLAN.exists():
        with PLAN.open('x') as file:
            json.dump(plan,file,indent=2,ensure_ascii=False)
            file.write('\n')
    elif json.loads(PLAN.read_text()) != plan:
        raise ValueError('Frozen continuation plan changed; use a new version')
    plan_sha = sha(PLAN.read_bytes())
    settings = get_settings()
    client = OpenRouterClient(settings, run_id=RUN_ID)
    summary = {'status':'preflight_only','run_id':RUN_ID,'remaining_stages':plan['stage_count'],
               'maximum_calls_including_repairs':plan['maximum_calls_including_repairs'],
               'conservative_upper_usd':plan['conservative_upper_usd'],
               'ledger_total_usd':client.ledger.total_spent(),
               'project_guard_headroom_usd':settings.api_hard_stop_usd-client.ledger.total_spent(),
               'paid_approval_required':True,'plan_sha256':plan_sha}
    if not args.execute and not args.record_check:
        print(json.dumps(summary,indent=2));return
    if not args.approval_receipt:
        raise ValueError('Paid continuation requires its own explicit approval receipt')
    cap = approved_receipt(args.approval_receipt,plan,plan_sha)
    if Decimal(str(settings.api_hard_stop_usd-client.ledger.total_spent())) < Decimal(plan['conservative_upper_usd']):
        raise ValueError('Project hard stop cannot cover remaining conservative bound')

    STATE.parent.mkdir(parents=True,exist_ok=True)
    with STATE.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        stages = [s['stage_id'] for s in plan['stages']]
        session = Stage2ComparisonSession(STATE,run_id=RUN_ID,fingerprint=plan_sha,
                                          jobs=stages,ledger=client.ledger,ceiling=str(cap))
        if args.record_check:
            session.record_check(json.loads(args.record_check.read_text()))
            print(json.dumps({'status':session.data['status'],'completed':len(session.data['results']),
                              'semantic_failures':session.data.get('semantic_failures',[])}));return
        if session.data.get('transport_uncertain'):
            raise ValueError('Uncertain transport charge requires reconciliation')
        if session.data['status']=='complete':
            print(json.dumps({'status':'complete','completed':len(stages)}));return
        if session.data['status']!='ready':
            raise ValueError('Previous stage awaits source check or process failure has stopped the run')
        stage=plan['stages'][len(session.data['results'])]
        remaining=sum((Decimal(str(s['conservative_upper_usd'])) for s in plan['stages'][len(session.data['results']):]),Decimal('0'))
        session.check_budget(remaining)
        client.guard.check(float(remaining))
        if not client.verify_inference_key()['inference_key']:
            raise ValueError('Inference key type is invalid')
        session.begin(stage['stage_id'])
        started=time.perf_counter()
        result={'job_id':stage['stage_id'],'source_job_id':stage['job_id'],
                'model':stage['model'],'model_id':stage['model_id'],
                'plan_sha256':plan_sha,'source_sha256':stage['source_sha256'],
                'prompt_version':SPEC.prompt_version}
        try:
            out=extract_jd(sources[stage['job_id']],job_id=stage['job_id'],
                           client=Stage2ComparisonClient(client,session,stage),model=stage['model'],
                           cache=None,scope='corpus_jd',spec=SPEC)
            result.update(status=out.status,attempts=out.attempts,error_code=out.error_code,
                          extraction=out.extraction.model_dump(mode='json') if out.extraction else None,
                          coverage=out.coverage,cache_hit=False)
        except BaseException as exc:
            result.update(status='failed',error_code=type(exc).__name__,
                          attempts=session.data.get('stage_attempts',{}).get(stage['stage_id'],0))
        result['latency_ms']=int((time.perf_counter()-started)*1000)
        result['result_sha256']=sha(json.dumps(result,sort_keys=True).encode())
        session.finish(result)
        output=REPO_ROOT/'evals/results'/f'{RUN_ID}_{len(session.data["results"]):02d}.json'
        with output.open('x') as file: json.dump(result,file,indent=2,ensure_ascii=False)
        print(json.dumps({'status':session.data['status'],'stage':stage['stage_id'],
                          'attempts':result['attempts'],'result':str(output.relative_to(REPO_ROOT)),
                          'ledger_total_usd':client.ledger.total_spent()}))


if __name__=='__main__':
    main()
