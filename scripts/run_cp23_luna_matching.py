"""D-076 development check: GPT-6 Luna versus DeepSeek Flash for evidence matching.

Version 2 (4 October 2026). Version 1 stopped: every Luna call was rejected
(NotFoundError, US$0) because the request sent `temperature`, which no Luna
endpoint supports, and the US$0.40 cap could not hold the conservative
reservations of 20 parallel DeepSeek calls. Version 1 records stay in
`evals/results/cp23/luna_matching_v1/`. Version 2 uses the approved D-058 Luna
request adaptation (`RouteClient`: temperature omitted, dated alias accepted),
runs Luna only (Dion's choice), starts with one canary call, and uses a
US$0.50 reservation cap.

Approved by Dion on 4 October 2026 (audit decision 1). Development CV1/CV2 only.
Same 60 Part B pairs, same saved DeepSeek JD extractions (pipeline v1.1),
same prompt v1.1, validator v1.1, G1/G2 and dynamic output policy. Only the
matching model changes. Aggregate cap US$0.40 on top of the project guard.

Phases (each pair is one matching call, no cache, one validation repair at most):
  0. Canary: one Luna pair (CV2 rank 1). Any failure stops the run.
  A. Luna, CV1 Hybrid Qwen top 20, 20 workers  -> one-CV K=20 wall time
  C. Luna, the other 39 pairs, 8 workers       -> full 60-pair Luna coverage
DeepSeek latency comes from saved runs (pipeline v1.1 and the 8 v1 calls).

Default is a zero-call preflight. Run with --execute only on Dion's machine,
where the git-ignored .env holds the key. The key is never printed or written.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
import json
from pathlib import Path
import statistics
import sys
from threading import Lock
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.config import get_settings
from jobfit.cv.parser import ParsedCV
from jobfit.eval.stage2_route_repair import RouteClient
from jobfit.llm.client import OpenRouterClient, strict_schema
from jobfit.llm.output_policy import MODEL_OUTPUT_LIMIT
from jobfit.llm.pricing import estimate_cost
from jobfit.matching.evidence_matcher import match_evidence
from jobfit.schemas.requirements import JDExtraction
from jobfit.scoring.hold_policy_v11 import score_with_hold_policy

OLD = ROOT / 'evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1'
V11 = ROOT / 'evals/results/cp23/pipeline_v11'
OUT = ROOT / 'evals/results/cp23/luna_matching_v2'
V1_OUT = ROOT / 'evals/results/cp23/luna_matching_v1'
RUN_ID = 'cp23_luna_matching_20261004_v2'
CAP = 0.50
CLIENT_CLASS = RouteClient
LUNA, DEEPSEEK = 'gpt-6-luna', 'deepseek-flash'
CONTINUATION_JDS = {'F00022', 'F00126', 'F00310'}
STOP_ERRORS = {'RunCapReached', 'AuthenticationError', 'PermissionDeniedError', 'APIConnectionError',
               'APIStatusError', 'BudgetExceeded', 'NotFoundError', 'BadRequestError'}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write_once(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def protected() -> dict[str, str]:
    paths = [ROOT / 'evals/labeling/JobFit_Development_Labeling_v1.3.xlsx',
             ROOT / 'evals/splits/dev_job_ids.txt', ROOT / 'evals/splits/test_job_ids.txt',
             ROOT / 'prompts/evidence_matching_v1_1.md', ROOT / 'evals/annotation_guideline_v1_3.md',
             ROOT / 'data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md',
             ROOT / 'data/synthetic_cvs/cv_02_career_switcher_ai_engineer_en.md',
             OLD / 'plan.json', V11 / 'plan_v1.json', V11 / 'coverage_summary_v2.json']
    paths += sorted((ROOT / 'evals/gold/development_v13_reviewed_20261003_stage1_r3').glob('*'))
    return {str(p.relative_to(ROOT)): digest(p) for p in paths if p.is_file()}


def jd_path(job: str, redo: set[str]) -> Path:
    if job in CONTINUATION_JDS:
        return V11 / f'jd_hold_{job}_v11_v2.json'
    return V11 / f'jd_{job}_v11.json' if job in redo else OLD / f'jd_{job}.json'


def matchable(job: str, redo: set[str]) -> JDExtraction | None:
    path = jd_path(job, redo)
    if not path.exists():
        return None
    row = json.loads(path.read_text())
    raw = row.get('extraction')
    if row.get('status') != 'done' or not raw or raw.get('jd_quality') != 'ok':
        return None
    return JDExtraction.model_validate(raw)


def phases(rankings: dict[str, list[str]]) -> list[dict]:
    """Fixed phase plan. Pure function, unit tested."""
    cv1, cv2 = rankings['CV1'], rankings['CV2']
    return [
        {'name': 'P0_luna_canary', 'model': LUNA, 'workers': 1, 'pairs': [['CV2', cv2[0]]]},
        {'name': 'A_luna_cv1_top20', 'model': LUNA, 'workers': 20, 'pairs': [['CV1', j] for j in cv1[:20]]},
        {'name': 'C_luna_remaining39', 'model': LUNA, 'workers': 8,
         'pairs': [['CV1', j] for j in cv1[20:30]] + [['CV2', j] for j in cv2[1:30]]},
    ]


class RunCapReached(RuntimeError):
    pass


class CappedClient:
    """Reserve the conservative upper cost of in-flight requests before dispatch."""

    def __init__(self, base: OpenRouterClient, starting_total: float, cap: float = CAP):
        self.base, self.starting_total, self.cap = base, starting_total, cap
        self.lock, self.inflight = Lock(), 0.0

    def chat_structured(self, model, messages, output_model, task, max_tokens=2000, temperature=0.0):
        price = self.base._price(model)
        schema = strict_schema(output_model.model_json_schema())
        est_in = len(json.dumps(messages, ensure_ascii=False).encode()) + len(json.dumps(schema).encode()) + 512
        upper = estimate_cost(price, est_in, max_tokens)
        with self.lock:
            spent = self.base.ledger.total_spent() - self.starting_total
            if spent + self.inflight + upper > self.cap + 1e-9:
                raise RunCapReached('Luna check aggregate cap would be exceeded')
            self.base.guard.check(upper + self.inflight)
            self.inflight += upper
        try:
            return self.base._chat_attempt(model, messages, output_model, task, max_tokens, temperature)
        finally:
            with self.lock:
                self.inflight -= upper


def endpoint_metadata(model_id: str) -> dict:
    """Smallest published output limit and temperature support (public metadata, no key)."""
    import httpx
    response = httpx.get(f'https://openrouter.ai/api/v1/models/{model_id}/endpoints', timeout=20)
    response.raise_for_status()
    endpoints = response.json()['data']['endpoints']
    limits = [e.get('max_completion_tokens') for e in endpoints]
    limits = [x for x in limits if isinstance(x, int) and x > 0]
    return {'endpoints': len(endpoints), 'min_output_limit': min(limits) if limits else None,
            'any_endpoint_supports_temperature': any('temperature' in (e.get('supported_parameters') or [])
                                                     for e in endpoints)}


def reservation_upper(model: str, prices, rankings, redo) -> list[float]:
    """Conservative per-call upper costs, computed exactly like the client reservation."""
    from jobfit.llm.output_policy import estimate_input_tokens, output_allowance
    from jobfit.matching import evidence_matcher as em
    prompt = em.EVIDENCE_PROMPT_FILE.read_text() + '\n\n' + em.GUIDELINE_FILE.read_text()
    schema = em.EvidenceResponse.model_json_schema()
    cvs = {cv: ParsedCV.model_validate(json.loads((OLD / f'{cv}_parse.json').read_text())['parsed'])
           for cv in rankings}
    out = []
    for cv, ranking in rankings.items():
        for job in ranking:
            extraction = matchable(job, redo)
            if extraction is None:
                continue
            p = cvs[cv]
            payload = {'extraction': extraction.model_dump(mode='json'), 'cv_id': p.profile.cv_id,
                       'analysis_date': p.analysis_date.isoformat(), 'verified_duration_years': {},
                       'cv_text': p.profile.raw_text}
            max_tokens = output_allowance('evidence_matching', estimate_input_tokens(prompt, payload, schema),
                                          len(extraction.units))
            messages = [{'role': 'system', 'content': prompt},
                        {'role': 'user', 'content': json.dumps({'untrusted_document_data': payload}, ensure_ascii=False)}]
            est_in = (len(json.dumps(messages, ensure_ascii=False).encode()) +
                      len(json.dumps(strict_schema(schema)).encode()) + 512)
            out.append(estimate_cost(prices[model], est_in, max_tokens))
    return sorted(out)


def preflight(check_endpoints: bool = True):
    rankings = json.loads((OLD / 'plan.json').read_text())['rankings']
    redo = set(json.loads((V11 / 'plan_v1.json').read_text())['redo_jds'])
    dev = set((ROOT / 'evals/splits/dev_job_ids.txt').read_text().splitlines())
    plan_phases = phases(rankings)
    if any(job not in dev for p in plan_phases for _, job in p['pairs']):
        raise ValueError('Non-development job in plan')
    settings = get_settings()
    base = CLIENT_CLASS(settings, run_id=RUN_ID, chat_timeout_seconds=240.0)
    records = base.ledger.records()
    medians = {}
    for model in (LUNA,):
        model_id = base._price(model).model_id
        values = [r.cost_usd for r in records if r.model == model_id and r.task == 'evidence_matching'
                  and r.ok and r.cost_source == 'reported']
        if not values:
            raise ValueError(f'No observed matching cost for {model}')
        medians[model] = statistics.median(values)
    calls = {LUNA: sum(1 for p in plan_phases for _, job in p['pairs'] if matchable(job, redo))}
    estimate = 1.5 * calls[LUNA] * medians[LUNA]
    uppers = reservation_upper(LUNA, base.prices, rankings, redo)
    peak_reservation = sum(uppers[-max(p['workers'] for p in plan_phases):])
    metadata = endpoint_metadata(base._price(LUNA).model_id) if check_endpoints else None
    limits = {LUNA: metadata['min_output_limit'] if metadata else None}
    receipt = {'run_id': RUN_ID, 'scope': 'development_CV1_CV2', 'decision': 'audit decision 1, 4 Oct 2026',
               'cap_usd': CAP, 'phases': plan_phases, 'matching_calls': calls,
               'peak_inflight_reservation_usd': round(peak_reservation, 6),
               'luna_endpoint_metadata': metadata,
               'request_adaptation': 'D-058 RouteClient: temperature omitted for openai/gpt-6-luna; dated alias accepted',
               'predecessor': 'cp23_luna_matching_20261004_v1 (stopped: Luna NotFoundError x18 at US$0; RunCapReached in DeepSeek phase)',
               'median_matching_cost_usd': medians, 'estimate_median_x_1_5_usd': round(estimate, 6),
               'endpoint_min_output_limit': limits, 'policy_output_limit': MODEL_OUTPUT_LIMIT,
               'project_budget_usd': settings.api_budget_usd, 'project_hard_stop_usd': settings.api_hard_stop_usd,
               'ledger_before_usd': base.ledger.total_spent(), 'protected_sha256': protected(),
               'extraction_source': 'saved DeepSeek pipeline v1.1 extractions, no new extraction call',
               'settings': {'prompt': 'evidence v1.1', 'validator': 'quote-check-v1.1', 'guardrails': ['G1', 'G2'],
                            'dynamic_output': True, 'timeout_s': 240, 'cache': 'none'}}
    if estimate > CAP:
        raise ValueError('Estimate exceeds the approved cap')
    if peak_reservation > CAP:
        raise ValueError('Peak in-flight reservation exceeds the cap; lower the workers or ask Dion')
    if base.ledger.total_spent() + CAP > settings.api_hard_stop_usd:
        raise ValueError('Project hard stop has insufficient headroom')
    for model, limit in limits.items():
        # A length continuation may double an allowance of roughly 20k to 30k tokens.
        if check_endpoints and (limit is None or limit < 65_536):
            raise ValueError(f'{model} endpoint output limit is unknown or below 65,536; stop and review')
    return receipt, rankings, redo, base


def run_phase(phase, client, cvs, redo, out_dir: Path):
    def one(cv, job):
        start = time.perf_counter()
        extraction = matchable(job, redo)
        if extraction is None:
            return {'cv_id': cv, 'job_id': job, 'model': phase['model'], 'status': 'held_extraction',
                    'error_code': None, 'wall_ms': 0, 'assessments': [], 'scores': {}}
        try:
            result = match_evidence(cvs[cv], extraction, client=client, model=phase['model'],
                                    validator_version='quote-check-v1.1', guardrail_ids=('G1', 'G2'),
                                    dynamic_output=True)
            status, error, assessments = result.status, result.error_code, result.assessments
        except Exception as exc:  # recorded, never retried here
            status, error, assessments = 'failed', type(exc).__name__, []
        scores = {}
        for policy in ('H1', 'H2', 'H2v2'):
            score, excluded = score_with_hold_policy(extraction, assessments, policy=policy)
            scores[policy] = {'score': score.model_dump(mode='json'), 'excluded': excluded}
        return {'cv_id': cv, 'job_id': job, 'model': phase['model'], 'status': status, 'error_code': error,
                'wall_ms': round((time.perf_counter() - start) * 1000),
                'assessments': [a.model_dump(mode='json') for a in assessments], 'scores': scores}

    started = time.perf_counter()
    rows, stop = [], None
    with ThreadPoolExecutor(max_workers=phase['workers']) as pool:
        futures = {pool.submit(one, cv, job): (cv, job) for cv, job in phase['pairs']}
        for future in as_completed(futures):
            row = future.result()
            write_once(out_dir / f"{phase['name']}__{row['cv_id']}_{row['job_id']}.json", row)
            rows.append(row)
            print(json.dumps({'phase': phase['name'], 'cv': row['cv_id'], 'job': row['job_id'],
                              'status': row['status'], 'error': row['error_code']}), flush=True)
            if row['error_code'] in STOP_ERRORS:
                stop = row['error_code']
    wall = round((time.perf_counter() - started) * 1000)
    called = [r for r in rows if r['status'] != 'held_extraction']
    return {'phase': phase['name'], 'model': phase['model'], 'workers': phase['workers'],
            'pairs': len(rows), 'called': len(called), 'phase_wall_ms': wall,
            'pair_wall_ms_p50': statistics.median([r['wall_ms'] for r in called]) if called else None,
            'pair_wall_ms_max': max([r['wall_ms'] for r in called], default=None),
            'done': sum(r['status'] == 'done' for r in called), 'stop': stop}


def main(execute: bool, check_endpoints: bool):
    receipt, rankings, redo, base = preflight(check_endpoints)
    print(json.dumps({k: receipt[k] for k in ('run_id', 'matching_calls', 'estimate_median_x_1_5_usd', 'cap_usd',
                                               'peak_inflight_reservation_usd', 'project_budget_usd',
                                               'project_hard_stop_usd', 'ledger_before_usd',
                                               'endpoint_min_output_limit', 'luna_endpoint_metadata')}), flush=True)
    if not execute:
        return
    plan_path = OUT / 'plan_v1.json'
    if plan_path.exists():
        raise SystemExit('This versioned run already exists; make a new version instead of resuming')
    write_once(plan_path, receipt)
    if not base.verify_inference_key()['inference_key']:
        raise ValueError('Key is not an inference key')
    cvs = {cv: ParsedCV.model_validate(json.loads((OLD / f'{cv}_parse.json').read_text())['parsed'])
           for cv in ('CV1', 'CV2')}
    starting = base.ledger.total_spent()
    client = CappedClient(base, starting)
    summaries = []
    with base.ledger.exclusive():
        for phase in receipt['phases']:
            if protected() != receipt['protected_sha256']:
                raise ValueError('Protected input changed')
            summary = run_phase(phase, client, cvs, redo, OUT)
            summaries.append(summary)
            print(json.dumps(summary), flush=True)
            # The canary exists to catch route, key or budget errors (STOP_ERRORS) before
            # parallel dispatch; a model answer that fails validation is a normal result.
            if summary['stop']:
                break
    run_cost = sum(r.cost_usd for r in base.ledger.records() if r.run_id == RUN_ID)
    write_once(OUT / 'summary_v1.json', {'run_id': RUN_ID, 'phases': summaries, 'run_cost_usd': run_cost,
                                         'ledger_total_usd': base.ledger.total_spent(),
                                         'completed': len(summaries) == len(receipt['phases']) and not summaries[-1]['stop']})
    print(json.dumps({'run_cost_usd': run_cost, 'completed': len(summaries) == len(receipt['phases'])
                      and not summaries[-1]['stop']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--skip-endpoint-check', action='store_true', help='offline preflight only')
    args = parser.parse_args()
    if args.execute and args.skip_endpoint_check:
        raise SystemExit('The endpoint output-limit check is required before paid calls')
    main(args.execute, not args.skip_endpoint_check)
