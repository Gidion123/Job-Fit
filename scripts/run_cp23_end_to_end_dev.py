"""Resumable CP2.3 development check. Preflight is the default and makes no API calls.

The frozen retrieval list and split restrict every job. A run-local cost ceiling
is checked before each routed call as well as the project ledger hard stop.
Only synthetic CV1/CV2 are accepted. No workbook or gold file is written.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone, timedelta
from hashlib import sha256
import json
from pathlib import Path
import statistics
import sys
import time

sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1] / 'src')]

from jobfit.config import REPO_ROOT, get_settings
from jobfit.cv.parser import ParsedCV, parse_cv
from jobfit.cv.text_extract import TextResult, extract_text
from jobfit.extraction.audited import ExtractionSpec
from jobfit.extraction.cache import ExtractionCache
from jobfit.extraction.jd_extractor import extract_jd
from jobfit.llm.client import OpenRouterClient
from jobfit.privacy.masking import mask_local
from jobfit.matching.evidence_matcher import match_evidence
from jobfit.scoring.score import compute_score
from jobfit.schemas.analysis import ScoreStatus
from scripts.run_batch_extraction import development_sources, atomic_report

RUN = 'cp23_end_to_end_dev_20261004_v1'
OUT = REPO_ROOT / 'evals/results/cp23/end_to_end_dev' / RUN
RANKINGS = REPO_ROOT / 'evals/results/cp22_retrieval_top30_20261002_03.json'
FREEZE = REPO_ROOT / 'config/versions/pipeline_cp23_provisional_20261004.yaml'
MODEL = 'deepseek-flash'
CAP = 2.50
DEADLINE_MARGIN = timedelta(minutes=6)


class PartBRunCapReached(RuntimeError):
    """The separately approved Part B ceiling is exhausted."""


class PartBDeadlineReached(RuntimeError):
    """Stop dispatch before the presentation cutoff."""


def check_deadline(deadline: datetime) -> None:
    if datetime.now(timezone.utc) + DEADLINE_MARGIN >= deadline:
        raise PartBDeadlineReached('Presentation cutoff reached; no new request dispatched')


def hold_unresolved_structure(extraction, score):
    """Mirror the D-049 hold already used by the one-JD pipeline."""
    if any(unit.needs_review for unit in extraction.units):
        return score.model_copy(update={
            'status': ScoreStatus.ON_HOLD, 'score_pct': None,
            'reasons': score.reasons + ['Requirement structure needs review; identified denominator is not validated.'],
        })
    return score


CV_FILES = {
    'CV1': ('data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md', 'Rina'),
    'CV2': ('data/synthetic_cvs/cv_02_career_switcher_ai_engineer_en.md', 'Bima'),
}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def plan() -> dict:
    import yaml
    cfg = yaml.safe_load(FREEZE.read_text())
    if (cfg.get('matching_model'), cfg.get('extraction_model'), cfg.get('stage1_k')) != (MODEL, MODEL, 20):
        raise ValueError('The selected CP2.3 configuration changed')
    run_data = json.loads(RANKINGS.read_text())
    rankings = {r['cv_id']: r['ranking'] for r in run_data['runs'] if r['method'] == 'hybrid_qwen'}
    if set(rankings) != set(CV_FILES) or any(len(ids) != 30 or len(ids) != len(set(ids)) for ids in rankings.values()):
        raise ValueError('Frozen hybrid Qwen rankings are incomplete')
    jobs = sorted(set().union(*map(set, rankings.values())))
    sources = development_sources(jobs)
    if len(sources) != len(jobs):
        raise ValueError('Development source coverage failed')
    client = OpenRouterClient(get_settings(), run_id=RUN)
    prices = client.prices[MODEL]
    ledger = client.ledger.records()
    medians = {}
    for task in ('cv_parsing', 'jd_extraction', 'evidence_matching'):
        values = [r.cost_usd for r in ledger if r.model == prices.model_id and r.task == task and r.ok and r.cost_source == 'reported']
        if not values:
            raise ValueError(f'No settled observed cost for {task}')
        medians[task] = statistics.median(values)
    # Every stage is counted, including existing cache entries. This overstates
    # expected spend and leaves headroom for one repair per some stages.
    estimate = 1.5 * (2 * medians['cv_parsing'] + len(jobs) * medians['jd_extraction'] +
                      sum(map(len, rankings.values())) * medians['evidence_matching'])
    protected = [RANKINGS, FREEZE, REPO_ROOT/'evals/splits/dev_job_ids.txt',
                 REPO_ROOT/'data/processed/jobs_features.jsonl',
                 REPO_ROOT/'evals/annotation_guideline_v1_3.md',
                 REPO_ROOT/'prompts/jd_extraction_v1_4_experimental.md',
                 REPO_ROOT/'prompts/evidence_matching_v1_1.md',
                 *(REPO_ROOT/p for p,_ in CV_FILES.values())]
    return {'run_id':RUN, 'scope':'development_only', 'rankings':rankings,
            'unique_jds':len(jobs), 'cv_job_pairs':sum(map(len,rankings.values())),
            'model':MODEL, 'prompt':'jd-prompt-v1.4-experimental',
            'validator':'quote-check-v1.1', 'guardrails':['G1','G2'],
            'masking':'local-pattern-masking-v1', 'analysis_date':'2026-09-30',
            'medians_usd':medians, 'estimate_medians_x_1_5_usd':estimate,
            'approved_cap_usd':CAP, 'protected_sha256':{str(p.relative_to(REPO_ROOT)):digest(p) for p in protected},
            'held_source_ids':['F00369']}


class RunClient:
    def __init__(self, base: OpenRouterClient, starting_total: float, cap: float, deadline: datetime):
        self.base, self.starting_total, self.cap, self.deadline = base, starting_total, cap, deadline

    def chat_structured(self, model, messages, output_model, task, max_tokens=2000, temperature=0.0):
        # This conservative per-request bound includes the schema through the
        # same method used by the routed client. It also covers a repair call.
        from jobfit.llm.client import strict_schema
        import json as _json
        from jobfit.llm.pricing import estimate_cost
        price = self.base._price(model)
        schema = strict_schema(output_model.model_json_schema())
        est_in = len(_json.dumps(messages,ensure_ascii=False).encode()) + len(_json.dumps(schema).encode()) + 512
        upper = estimate_cost(price,est_in,max_tokens)
        current = self.base.ledger.total_spent() - self.starting_total
        if current + upper > self.cap:
            raise PartBRunCapReached('Part B cap reached')
        return self.base.chat_structured(model,messages,output_model,task,max_tokens=max_tokens,temperature=temperature)


def save_item(name: str, value: dict) -> None:
    OUT.mkdir(parents=True,exist_ok=True)
    path = OUT/name
    if path.exists():
        raise ValueError(f'Immutable stage output already exists: {name}')
    with path.open('x') as f:
        json.dump(value,f,ensure_ascii=False,indent=2)


def load_cv(cv_id: str, client: RunClient) -> ParsedCV:
    path_str, name = CV_FILES[cv_id]
    path = REPO_ROOT/path_str
    raw = extract_text(path.read_bytes(),path.name)
    if raw.status != 'ok':
        raise ValueError(f'{cv_id} text extraction failed')
    preview = mask_local(raw.text,reviewed_identifiers={'name':(name,)})
    if name.casefold() in preview.text.casefold():
        raise ValueError(f'{cv_id} identifier remained after masking')
    parsed = parse_cv(TextResult(text=preview.text), cv_id=cv_id, analysis_date=date(2026,9,30),
                      client=client, model=MODEL, is_synthetic=True)
    save_item(f'{cv_id}_parse.json',{'cv_id':cv_id,'status':parsed.profile.parse_status.value,
        'masking_counts':preview.counts,'masked_digest':preview.digest,
        'parsed':parsed.model_dump(mode='json'),'attempts':parsed.attempts})
    return parsed


def execute(a):
    p = plan()
    if p['estimate_medians_x_1_5_usd'] > CAP:
        raise ValueError('Part B estimate exceeds the approved cap')
    OUT.mkdir(parents=True,exist_ok=True)
    plan_path = OUT/'plan.json'
    if plan_path.exists():
        frozen = json.loads(plan_path.read_text())
        if any(frozen[k] != p[k] for k in ('rankings','unique_jds','cv_job_pairs','model',
                                           'prompt','validator','guardrails','masking',
                                           'analysis_date','protected_sha256','held_source_ids')):
            raise ValueError('Part B plan changed; stop instead of resuming')
        amendment = OUT/'cap_and_deadline_amendment_v2.json'
        if a.execute:
            if not amendment.exists(): raise ValueError('Approved resume amendment is missing')
            receipt = json.loads(amendment.read_text())
            if (receipt.get('original_plan_sha256') != digest(plan_path)
                    or receipt.get('approved_total_cap_usd') != CAP
                    or receipt.get('run_id') != RUN
                    or receipt.get('remaining_policy') != 'only_unsaved_pairs_no_timeout_replay'
                    or receipt.get('cutoff_utc') != a.deadline_utc):
                raise ValueError('Resume amendment does not match original plan and approval')
        p = frozen
    else:
        with plan_path.open('x') as f: json.dump(p,f,ensure_ascii=False,indent=2)
    base = OpenRouterClient(get_settings(),run_id=RUN)
    starting_total = base.ledger.total_spent() - sum(r.cost_usd for r in base.ledger.records() if r.run_id == RUN)
    deadline = datetime.fromisoformat(a.deadline_utc.replace('Z','+00:00')) if a.deadline_utc else None
    if a.execute and (deadline is None or deadline.tzinfo is None):
        raise ValueError('A timezone-aware presentation cutoff is required')
    client = RunClient(base,starting_total,CAP,deadline or datetime.max.replace(tzinfo=timezone.utc))
    run_spend = base.ledger.total_spent() - starting_total
    remaining = [(cv,j) for cv,ranking in p['rankings'].items() for j in ranking
                 if not (OUT/f'match_{cv}_{j}.json').exists()]
    print(json.dumps({'run_id':RUN,'estimate_usd':p['estimate_medians_x_1_5_usd'],
        'approved_total_cap_usd':CAP,'accounted_cost_usd':run_spend,
        'remaining_cap_usd':CAP-run_spend,'jobs':p['unique_jds'],'pairs':p['cv_job_pairs'],
        'remaining_pairs':remaining,'deadline_utc':a.deadline_utc}),flush=True)
    if not a.execute: return
    if run_spend >= CAP: raise PartBRunCapReached('Part B cap already reached')
    check_deadline(deadline)
    if not base.verify_inference_key()['inference_key']:
        raise ValueError('Inference key check failed')
    spec = ExtractionSpec(REPO_ROOT/'prompts/jd_extraction_v1_4_experimental.md','jd-prompt-v1.4-experimental')
    cache = ExtractionCache(REPO_ROOT/'reports/extraction_cache')
    cvs = {}
    for cv_id in p['rankings']:
        path = OUT/f'{cv_id}_parse.json'
        cvs[cv_id] = ParsedCV.model_validate(json.loads(path.read_text())['parsed']) if path.exists() else load_cv(cv_id,client)
        if cvs[cv_id].profile.parse_status.value != 'ok':
            raise RuntimeError(f'{cv_id} parsing failed; stop before matching')
    sources = {r['job_id']:r['text'] for r in development_sources(sorted(set().union(*map(set,p['rankings'].values()))))}
    for job_id in sorted(sources):
        if job_id in p['held_source_ids']:
            continue
        target = OUT/f'jd_{job_id}.json'
        if target.exists(): continue
        if plan()['protected_sha256']!=p['protected_sha256']: raise ValueError('Protected input changed')
        start=time.perf_counter()
        result=extract_jd(sources[job_id],job_id=job_id,client=client,model=MODEL,
                          cache=cache,scope='corpus_jd',spec=spec)
        save_item(target.name,{'job_id':job_id,'status':result.status,'attempts':result.attempts,
            'cache_hit':result.cache_hit,'error_code':result.error_code,'key':result.key,
            'wall_ms':round((time.perf_counter()-start)*1000),
            'coverage':result.coverage,
            'extraction':result.extraction.model_dump(mode='json') if result.extraction else None})
        print(json.dumps({'phase':'extraction','job_id':job_id,'status':result.status,'attempts':result.attempts}),flush=True)
        if result.error_code in ('PartBRunCapReached','APIConnectionError','APITimeoutError','AuthenticationError'):
            raise RuntimeError('Stopping on budget, transport, or authentication uncertainty')
    for cv_id, ranking in p['rankings'].items():
        cv=cvs[cv_id]
        for job_id in ranking:
            target=OUT/f'match_{cv_id}_{job_id}.json'
            if target.exists(): continue
            check_deadline(deadline)
            jd_path=OUT/f'jd_{job_id}.json'
            if not jd_path.exists():
                save_item(target.name,{'cv_id':cv_id,'job_id':job_id,'status':'held_source','score':None})
                continue
            jd=json.loads(jd_path.read_text())
            if jd['status']!='done' or jd['extraction']['jd_quality']!='ok':
                save_item(target.name,{'cv_id':cv_id,'job_id':job_id,
                    'status':'held_extraction' if jd['status']=='done' else 'failed_extraction','score':None})
                continue
            from jobfit.schemas.requirements import JDExtraction
            extraction=JDExtraction.model_validate(jd['extraction'])
            if plan()['protected_sha256']!=p['protected_sha256']: raise ValueError('Protected input changed')
            start=time.perf_counter()
            result=match_evidence(cv,extraction,client=client,model=MODEL,
                                  validator_version='quote-check-v1.1',guardrail_ids=('G1','G2'))
            if result.error_code == 'PartBDeadlineReached':
                raise PartBDeadlineReached('Cutoff reached before a matching request')
            score=hold_unresolved_structure(extraction,compute_score(extraction,result.assessments))
            save_item(target.name,{'cv_id':cv_id,'job_id':job_id,'status':result.status,
                'attempts':result.attempts,'error_code':result.error_code,
                'wall_ms':round((time.perf_counter()-start)*1000),
                'score':score.model_dump(mode='json'),
                'assessments':[x.model_dump(mode='json') for x in result.assessments],
                'source_flags':result.source_flags})
            print(json.dumps({'phase':'matching','cv_id':cv_id,'job_id':job_id,'status':result.status,
                              'score_status':score.status.value}),flush=True)
            if result.error_code in ('PartBRunCapReached','APIConnectionError','APITimeoutError','AuthenticationError'):
                raise RuntimeError('Stopping on budget, transport, or authentication uncertainty')
    summary={'run_id':RUN,'status':'completed','ledger_cost_usd':sum(r.cost_usd for r in base.ledger.records() if r.run_id==RUN),
             'finished_at':time.time(),'jobs':len(list(OUT.glob('jd_*.json'))),
             'matches':len(list(OUT.glob('match_*.json')))}
    save_item('summary.json',summary)
    print(json.dumps(summary),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--deadline-utc')
    execute(parser.parse_args())
