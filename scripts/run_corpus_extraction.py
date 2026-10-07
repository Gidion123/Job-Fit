"""Resumable DeepSeek Flash JD extraction for one split of the 428 target jobs.

Same extraction call as the evaluated pipeline: prompt v1.4, scope corpus_jd,
dynamic output, shared extraction cache. Preflight (dry run) unless --execute.

- development: allowed now. JDs already extracted in the evaluated runs are reused
  as they are (same records the CP2.3 results used), so only missing JDs are called.
- test: refused until an APPROVED freeze receipt exists with no file drift (D-053),
  because test JDs are held-out model processing.

Every JD gets one write-once record. A rerun with the same version folder only
does the JDs without a record. A failure is kept as a record, never retried here.
Order: one canary JD, then the rest with 4 workers under a hard run cap.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

MODEL = 'deepseek-flash'
PROMPT = 'prompts/jd_extraction_v1_4_experimental.md'
PROMPT_VERSION = 'jd-prompt-v1.4-experimental'
WORKERS = 4
OUT_ROOT = ROOT / 'evals/results/cp23'
STOP_ERRORS = {'RunCapReached', 'AuthenticationError', 'PermissionDeniedError', 'APIConnectionError',
               'APIStatusError', 'BudgetExceeded', 'NotFoundError', 'BadRequestError'}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write_once(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def split_sources(split: str) -> dict[str, str]:
    folder = ROOT / 'evals/splits'
    manifest = json.loads((folder / 'split_manifest.json').read_text())
    for name, value in manifest['output_hashes'].items():
        if digest(folder / name) != value:
            raise ValueError('Frozen split hash mismatch')
    ids = set((folder / ('dev_job_ids.txt' if split == 'development' else 'test_job_ids.txt')).read_text().split())
    out = {}
    with (ROOT / 'data/processed/jobs_features.jsonl').open() as f:
        for line in f:
            row = json.loads(line)
            if row['final_cluster_id'] in ids:
                out[row['final_cluster_id']] = row['description_clean']
    if set(out) != ids or len(ids) != 214:
        raise ValueError('Split sources incomplete')
    return dict(sorted(out.items()))


def reusable(job: str) -> Path | None:
    """Evaluated record for this job if it is matchable. The newest record counts,
    so an older success never replaces a newer failure (saved_records rule)."""
    from jobfit.extraction.saved_records import record_path
    path = record_path(job, include_corpus=False)
    if path:
        row = json.loads(path.read_text())
        if row.get('status') == 'done' and (row.get('extraction') or {}).get('jd_quality') == 'ok':
            return path
    return None


def require_freeze(folder: Path | None) -> str:
    from scripts.prepare_cp23_freeze import verify
    if folder is None or not (folder / 'freeze_receipt_APPROVED.json').exists():
        raise SystemExit('Test extraction needs --freeze pointing to an APPROVED freeze receipt (D-053)')
    drift = verify(folder)
    if drift:
        raise SystemExit(f'Files changed since the freeze: {drift}')
    return digest(folder / 'freeze_receipt_APPROVED.json')


def out_dir(split: str, version: int) -> Path:
    return OUT_ROOT / f'corpus_extraction_{split}_v{version}'


def quality(records: list[dict]) -> dict:
    """Plain counts for review. No model judgement, no threshold that changes data."""
    status = Counter(r['status'] for r in records)
    ok = [r for r in records if r['status'] == 'done' and (r.get('extraction') or {}).get('jd_quality') == 'ok']
    units = [len(r['extraction']['units']) for r in ok]
    return {'records': len(records), 'status': dict(status),
            'matchable': len(ok), 'not_matchable': len(records) - len(ok),
            'errors': dict(Counter(r.get('error_code') for r in records if r.get('error_code'))),
            'jd_quality': dict(Counter((r.get('extraction') or {}).get('jd_quality') for r in records if r.get('extraction'))),
            'coverage_review': sum(1 for r in records if (r.get('coverage') or {}).get('status') == 'review_required'),
            'reused': sum(1 for r in records if r.get('reused_from')),
            'units_median': statistics.median(units) if units else None,
            'units_min': min(units) if units else None, 'units_max': max(units) if units else None,
            'zero_required': sum(1 for r in ok if not any(u['importance'] == 'required'
                                                          for u in r['extraction']['units']))}


def preflight(split: str, version: int, cap: float, freeze: Path | None):
    from jobfit.config import get_settings
    from jobfit.llm.client import OpenRouterClient
    receipt_hash = require_freeze(freeze) if split == 'test' else None
    sources = split_sources(split)
    folder = out_dir(split, version)
    done = {p.stem.removeprefix('jd_') for p in folder.glob('jd_*.json')}
    reuse = {job: reusable(job) for job in sources if split == 'development' and job not in done}
    reuse = {j: p for j, p in reuse.items() if p}
    todo = [j for j in sources if j not in done and j not in reuse]
    settings = get_settings()
    client = OpenRouterClient(settings, run_id=f'corpus_extraction_{split}_v{version}', chat_timeout_seconds=240.0)
    price = client._price(MODEL)
    costs = [r.cost_usd for r in client.ledger.records()
             if r.model == price.model_id and r.task == 'jd_extraction' and r.ok and r.cost_source == 'reported']
    if not costs:
        raise ValueError('No observed extraction cost')
    median = statistics.median(costs)
    estimate = round(1.5 * median * len(todo), 6)
    plan = {'run_id': f'corpus_extraction_{split}_v{version}', 'split': split, 'model': MODEL,
            'prompt': PROMPT, 'prompt_version': PROMPT_VERSION, 'prompt_sha256': digest(ROOT / PROMPT),
            'guideline_sha256': digest(ROOT / 'evals/annotation_guideline_v1_3.md'),
            'scope': 'corpus_jd', 'dynamic_output': True, 'workers': WORKERS,
            'jobs': len(sources), 'already_recorded': len(done), 'reuse': len(reuse), 'to_call': len(todo),
            'median_call_usd': median, 'estimate_median_x_1_5_usd': estimate, 'cap_usd': cap,
            'ledger_before_usd': client.ledger.total_spent(),
            'project_budget_usd': settings.api_budget_usd, 'project_hard_stop_usd': settings.api_hard_stop_usd,
            'freeze_receipt_sha256': receipt_hash}
    if estimate > cap:
        raise SystemExit(f'Estimate {estimate} is above the cap {cap}')
    if settings.api_budget_usd != 19 or settings.api_hard_stop_usd != 18.5:
        raise SystemExit('Project guard values changed; ask Dion')
    if client.ledger.total_spent() + cap > settings.api_hard_stop_usd:
        raise SystemExit('Project hard stop has no room for this cap')
    return plan, sources, reuse, todo, client


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--split', choices=['development', 'test'], required=True)
    ap.add_argument('--version', type=int, default=1)
    ap.add_argument('--cap', type=float, default=3.0, help='hard run cap in USD')
    ap.add_argument('--freeze', type=Path, help='approved freeze folder (test only)')
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args(argv)
    plan, sources, reuse, todo, base = preflight(args.split, args.version, args.cap, args.freeze)
    print(json.dumps(plan, indent=1), flush=True)
    if not args.execute:
        print('Dry run. Nothing was called or written.')
        return 0
    from jobfit.extraction.audited import ExtractionSpec
    from jobfit.extraction.cache import ExtractionCache
    from jobfit.extraction.jd_extractor import extract_jd
    from scripts.probe_openrouter_access import require_access
    from scripts.run_cp23_luna_matching import CappedClient
    folder = out_dir(args.split, args.version)
    folder.mkdir(parents=True, exist_ok=True)
    plan_path = folder / f'plan_{time.strftime("%Y%m%dT%H%M%S")}.json'
    write_once(plan_path, plan)
    for job, path in reuse.items():
        row = json.loads(path.read_text())
        write_once(folder / f'jd_{job}.json', {**row, 'reused_from': str(path.relative_to(ROOT)),
                                                'reused_sha256': digest(path)})
    if todo:
        require_access([MODEL])
        if not base.verify_inference_key()['inference_key']:
            raise SystemExit('Key is not an inference key')
    spec = ExtractionSpec(ROOT / PROMPT, PROMPT_VERSION)
    cache = ExtractionCache(ROOT / 'reports/extraction_cache')
    client = CappedClient(base, base.ledger.total_spent(), cap=args.cap)

    def one(job: str) -> dict:
        start = time.perf_counter()
        try:
            r = extract_jd(sources[job], job_id=job, client=client, model=MODEL, cache=cache,
                           scope='corpus_jd', spec=spec, dynamic_output=True)
            row = {'job_id': job, 'status': r.status, 'attempts': r.attempts, 'error_code': r.error_code,
                   'cache_hit': r.cache_hit, 'key': r.key, 'coverage': r.coverage,
                   'extraction': r.extraction.model_dump(mode='json') if r.extraction else None}
        except Exception as exc:  # kept as a record, never retried here
            row = {'job_id': job, 'status': 'failed', 'error_code': type(exc).__name__, 'extraction': None}
        row['wall_ms'] = round((time.perf_counter() - start) * 1000)
        write_once(folder / f'jd_{job}.json', row)
        return row

    stop = None
    with base.ledger.exclusive():
        if todo:
            canary = one(todo[0])
            print(json.dumps({'canary': todo[0], 'status': canary['status'], 'error': canary.get('error_code')}), flush=True)
            if canary.get('error_code') in STOP_ERRORS:
                stop = canary['error_code']
        rest = todo[1:] if not stop else []
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            for row in pool.map(one, rest):
                print(json.dumps({'job_id': row['job_id'], 'status': row['status'], 'error': row.get('error_code')}), flush=True)
                if row.get('error_code') in STOP_ERRORS and not stop:
                    stop = row['error_code']
                    pool.shutdown(wait=True, cancel_futures=True)
                    break
    records = [json.loads(p.read_text()) for p in sorted(folder.glob('jd_*.json'))]
    run_cost = sum(r.cost_usd for r in base.ledger.records() if r.run_id == plan['run_id'])
    summary = {'run_id': plan['run_id'], 'stop_reason': stop, 'run_cost_usd': run_cost,
               'ledger_total_usd': base.ledger.total_spent(), 'complete': len(records) == len(sources),
               'quality': quality(records)}
    write_once(folder / f'summary_{time.strftime("%Y%m%dT%H%M%S")}.json', summary)
    print(json.dumps(summary, indent=1))
    return 0 if not stop else 2


if __name__ == '__main__':
    raise SystemExit(main())
