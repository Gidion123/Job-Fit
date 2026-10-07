"""Preflight a fixed Stage-2 extraction comparison; live work needs a review receipt.

One JD/model stage per invocation. Its source-based semantic check must be
recorded before the next stage. The output is an experiment draft, never gold.
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
from jobfit.eval.stage2_extraction import build_plan, Stage2ExtractionSession, Stage2ExtractionClient
from jobfit.extraction.audited import ExtractionSpec
from jobfit.extraction.jd_extractor import extract_jd
from jobfit.llm.client import OpenRouterClient
from scripts.run_batch_extraction import development_sources

RUN_ID = 'cp23_stage2_round1_extraction_20261003_v4'
PLAN = REPO_ROOT/'evals/results'/f'{RUN_ID}_preflight.json'
STATE = REPO_ROOT/'reports/quality_probe'/f'{RUN_ID}.json'
SPEC = ExtractionSpec(REPO_ROOT/'prompts/jd_extraction_v1_4_experimental.md', 'jd-prompt-v1.4-experimental')


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def approved_receipt(path: Path, plan: dict, *, plan_sha256: str) -> Decimal:
    receipt = json.loads(path.read_text())
    required = {'decision': 'approved', 'approved_by': 'Dion', 'scope': RUN_ID,
                'plan_sha256': plan_sha256}
    if any(receipt.get(key) != value for key, value in required.items()):
        raise ValueError('Explicit approval receipt does not match frozen comparison')
    cap = Decimal(str(receipt['aggregate_cap_usd']))
    if not cap.is_finite() or cap < Decimal(plan['conservative_upper_usd']) or cap > Decimal('8.50'):
        raise ValueError('Approval cap does not cover the conservative batch or exceeds project hard stop')
    return cap


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--execute', action='store_true')
    group.add_argument('--record-check', type=Path)
    parser.add_argument('--approval-receipt', type=Path)
    args = parser.parse_args()
    selected = json.loads((REPO_ROOT/'evals/results/cp23_stage1_case_candidates_20261003_v4.json').read_text())
    sources = {row['job_id']: row['text'] for row in development_sources([x['job_id'] for x in selected['cases']])}
    plan = build_plan(REPO_ROOT, sources, run_id=RUN_ID,
                      prompt_file='prompts/jd_extraction_v1_4_experimental.md')
    if not PLAN.exists():
        PLAN.write_text(json.dumps(plan, indent=2, ensure_ascii=False)+'\n')
    elif json.loads(PLAN.read_text()) != plan:
        raise ValueError('Frozen Stage-2 plan changed; preserve old artifact and create a new run ID')
    plan_sha = digest_bytes(PLAN.read_bytes())
    settings = get_settings()
    client = OpenRouterClient(settings, run_id=RUN_ID)
    summary = {'status': 'preflight_only', 'run_id': RUN_ID, 'stages': plan['stage_count'],
               'maximum_calls': plan['maximum_calls_including_repairs'],
               'conservative_upper_usd': plan['conservative_upper_usd'],
               'ledger_total_usd': client.ledger.total_spent(),
               'project_guard_headroom_usd': settings.api_hard_stop_usd-client.ledger.total_spent(),
               'paid_approval_required': True, 'plan_sha256': plan_sha}
    if not args.execute and not args.record_check:
        print(json.dumps(summary, indent=2)); return
    if not args.approval_receipt:
        raise ValueError('Paid execution requires a versioned explicit approval receipt')
    cap = approved_receipt(args.approval_receipt, plan, plan_sha256=plan_sha)
    if Decimal(str(settings.api_hard_stop_usd-client.ledger.total_spent())) < Decimal(plan['conservative_upper_usd']):
        raise ValueError('Project guard cannot cover the frozen conservative batch')
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with STATE.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX|fcntl.LOCK_NB)
        stages = [x['stage_id'] for x in plan['stages']]
        session = Stage2ExtractionSession(STATE, run_id=RUN_ID, fingerprint=plan_sha,
                                          jobs=stages, ledger=client.ledger, ceiling=str(cap))
        if args.record_check:
            session.record_check(json.loads(args.record_check.read_text()))
            print(json.dumps({'status': session.data['status'], 'completed': len(session.data['results'])})); return
        if session.data.get('transport_uncertain'):
            raise ValueError('Uncertain transport charge requires reconciliation before continuation')
        if session.data['status'] == 'complete':
            print(json.dumps({'status': 'complete', 'completed': len(stages)})); return
        if session.data['status'] != 'ready':
            raise ValueError('Previous result awaits source inspection or the run has stopped')
        stage = plan['stages'][len(session.data['results'])]
        remaining = sum(Decimal(str(x['conservative_upper_usd'])) for x in plan['stages'][len(session.data['results']):])
        session.check_budget(remaining)
        client.guard.check(float(remaining))
        if not client.verify_inference_key()['inference_key']:
            raise ValueError('Inference key type is invalid')
        session.begin(stage['stage_id'])
        started = time.perf_counter()
        result = {'job_id': stage['stage_id'], 'source_job_id': stage['job_id'],
                  'model': stage['model'], 'model_id': stage['model_id'],
                  'plan_sha256': plan_sha, 'source_sha256': stage['source_sha256'],
                  'prompt_version': SPEC.prompt_version}
        try:
            r = extract_jd(sources[stage['job_id']], job_id=stage['job_id'],
                           client=Stage2ExtractionClient(client, session, stage), model=stage['model'],
                           cache=None, scope='corpus_jd', spec=SPEC)
            result.update(status=r.status, attempts=r.attempts, error_code=r.error_code,
                          extraction=r.extraction.model_dump(mode='json') if r.extraction else None,
                          coverage=r.coverage, cache_hit=False)
        except BaseException as exc:
            result.update(status='failed', error_code=type(exc).__name__, attempts=session.data.get('stage_attempts', {}).get(stage['stage_id'], 0))
        result['latency_ms'] = int((time.perf_counter()-started)*1000)
        result['result_sha256'] = digest_bytes(json.dumps(result, sort_keys=True).encode())
        session.finish(result)
        output = REPO_ROOT/'evals/results'/f'{RUN_ID}_{len(session.data["results"]):02d}.json'
        with output.open('x') as file:
            json.dump(result, file, indent=2, ensure_ascii=False)
        print(json.dumps({'status': session.data['status'], 'stage': stage['stage_id'],
                          'attempts': result['attempts'], 'result': str(output.relative_to(REPO_ROOT)),
                          'ledger_total_usd': client.ledger.total_spent()}))


if __name__ == '__main__':
    main()
