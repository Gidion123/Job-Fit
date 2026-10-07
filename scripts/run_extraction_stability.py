"""Run-to-run stability of JD extraction (audit P6). Dry run unless --execute.

Five preregistered development JDs with gold extraction (F00332, F00036, F00309,
F00354, F00815) are extracted again `--repeats` times with the frozen call
(DeepSeek Flash, prompt v1.4, dynamic output) and NO cache, so each run is a fresh
model answer. Each run is compared with the saved evaluated extraction and with
the gold unit count:
- number of units and of required units (the score denominator),
- units marked needs_review (H2v2 hold risk),
- overlap of normalized unit texts between runs (Jaccard).
No score, label or gold changes. Hard cap US$0.50.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import re
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from scripts.run_corpus_extraction import MODEL, PROMPT, PROMPT_VERSION, STOP_ERRORS, reusable, split_sources, write_once

JOBS = ('F00332', 'F00036', 'F00309', 'F00354', 'F00815')
CAP = 0.50
GOLD = ROOT / 'evals/gold/development_v13_reviewed_20261003_stage1_r3/extraction_gold.jsonl'
OUT = ROOT / 'evals/results/cp23/extraction_stability_v1'


def gold_counts() -> dict[str, dict]:
    out = {}
    for line in GOLD.read_text().splitlines():
        row = json.loads(line)
        if row['job_id'] in JOBS and row.get('review_status') == 'approved':
            c = out.setdefault(row['job_id'], Counter())
            c['units'] += 1
            c['required'] += row['importance'] == 'required'
    return {j: dict(c) for j, c in out.items()}


def norm(text: str) -> str:
    return ' '.join(re.findall(r'\w+', text.casefold()))


def profile(extraction: dict | None) -> dict | None:
    if not extraction:
        return None
    units = extraction['units']
    return {'units': len(units), 'required': sum(u['importance'] == 'required' for u in units),
            'needs_review': sum(bool(u.get('needs_review')) for u in units),
            'jd_quality': extraction.get('jd_quality'), 'texts': sorted({norm(u['text']) for u in units})}


def jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    return round(len(sa & sb) / len(sa | sb), 3) if sa | sb else 1.0


def compare(runs: dict[str, list[dict | None]]) -> dict:
    """runs[job] = [saved, run1, run2, ...] profiles (None for a failed run)."""
    gold = gold_counts()
    report = {}
    for job, items in runs.items():
        ok = [p for p in items if p]
        pairs = [jaccard(a['texts'], b['texts']) for a, b in combinations(ok, 2)]
        report[job] = {'gold': gold.get(job), 'runs': [None if p is None else {k: v for k, v in p.items() if k != 'texts'} for p in items],
                       'unit_count_range': [min(p['units'] for p in ok), max(p['units'] for p in ok)] if ok else None,
                       'required_count_range': [min(p['required'] for p in ok), max(p['required'] for p in ok)] if ok else None,
                       'text_jaccard_pairs': pairs,
                       'text_jaccard_median': statistics.median(pairs) if pairs else None,
                       'failed_runs': sum(p is None for p in items)}
    same_den = sum(1 for r in report.values() if r['required_count_range'] and r['required_count_range'][0] == r['required_count_range'][1])
    return {'jobs': report, 'denominator_stable_jobs': same_den, 'jobs_total': len(report)}


def saved_profile(job: str) -> dict | None:
    path = reusable(job)
    return profile(json.loads(path.read_text())['extraction']) if path else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repeats', type=int, default=2)
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args(argv)
    from jobfit.config import get_settings
    from jobfit.llm.client import OpenRouterClient
    sources = split_sources('development')
    settings = get_settings()
    base = OpenRouterClient(settings, run_id='extraction_stability_v1', chat_timeout_seconds=240.0)
    price = base._price(MODEL)
    costs = [r.cost_usd for r in base.ledger.records()
             if r.model == price.model_id and r.task == 'jd_extraction' and r.ok and r.cost_source == 'reported']
    calls = len(JOBS) * args.repeats
    estimate = round(1.5 * statistics.median(costs) * calls, 6)
    plan = {'run_id': 'extraction_stability_v1', 'jobs': JOBS, 'repeats': args.repeats, 'calls': calls,
            'cache': 'none', 'model': MODEL, 'prompt_sha256': sha256((ROOT / PROMPT).read_bytes()).hexdigest(),
            'estimate_usd': estimate, 'cap_usd': CAP, 'ledger_before_usd': base.ledger.total_spent(),
            'saved_profiles_found': sum(saved_profile(j) is not None for j in JOBS)}
    print(json.dumps(plan, indent=1))
    if estimate > CAP or base.ledger.total_spent() + CAP > settings.api_hard_stop_usd:
        raise SystemExit('Estimate above the cap or no room under the project hard stop')
    if not args.execute:
        print('Dry run. Nothing was called or written.')
        return 0
    if OUT.exists():
        raise SystemExit('This versioned run already exists; make a new version')
    from jobfit.extraction.audited import ExtractionSpec
    from jobfit.extraction.jd_extractor import extract_jd
    from scripts.probe_openrouter_access import require_access
    from scripts.run_cp23_luna_matching import CappedClient
    require_access([MODEL])
    write_once(OUT / 'plan.json', plan)
    spec = ExtractionSpec(ROOT / PROMPT, PROMPT_VERSION)
    client = CappedClient(base, base.ledger.total_spent(), cap=CAP)
    runs = {j: [saved_profile(j)] for j in JOBS}
    stop = None
    with base.ledger.exclusive():
        for rep in range(1, args.repeats + 1):
            for job in JOBS:
                if stop:
                    break
                start = time.perf_counter()
                r = extract_jd(sources[job], job_id=job, client=client, model=MODEL, cache=None,
                               scope='corpus_jd', spec=spec, dynamic_output=True)
                row = {'job_id': job, 'repeat': rep, 'status': r.status, 'error_code': r.error_code,
                       'attempts': r.attempts, 'wall_ms': round((time.perf_counter() - start) * 1000),
                       'extraction': r.extraction.model_dump(mode='json') if r.extraction else None}
                write_once(OUT / f'jd_{job}_r{rep}.json', row)
                runs[job].append(profile(row['extraction']) if r.status == 'done' else None)
                print(json.dumps({k: row[k] for k in ('job_id', 'repeat', 'status', 'error_code')}), flush=True)
                if r.error_code in STOP_ERRORS:
                    stop = r.error_code
    result = {'run_id': plan['run_id'], 'stop_reason': stop,
              'run_cost_usd': sum(x.cost_usd for x in base.ledger.records() if x.run_id == plan['run_id']),
              'note': 'runs[0] is the saved evaluated extraction; later runs are fresh, uncached calls.',
              **compare(runs)}
    write_once(OUT / 'summary.json', result)
    print(json.dumps({k: result[k] for k in ('run_cost_usd', 'denominator_stable_jobs', 'jobs_total', 'stop_reason')}, indent=1))
    return 0 if not stop else 2


if __name__ == '__main__':
    raise SystemExit(main())
