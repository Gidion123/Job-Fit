"""CP2.4 held-out test run (D-053) in phases. Dry run unless --execute. Needs an APPROVED freeze.

Phases (each resumable; every saved record is write-once):
  parse       CV3-CV5 parsed with the same call as development (local masking with the
              first-name hint, DeepSeek Flash). CV1/CV2 reuse their development parse.
  queries     Qwen query vectors for CV1-CV5 into a separate held-out cache. CV1/CV2 vectors
              are copied from the development cache (same text, same model, no call).
  stage1      Hybrid Qwen top 30 over the 214 test jobs per CV (local database, no call).
  extraction  DeepSeek Flash extraction (prompt v1.4, corpus_jd, dynamic output) for the
              jobs each CV will analyze: top K after the seniority rule.
  matching    recommend() per CV with the frozen config (Sol, Luna fallback, H2v2, experience
              block with history confirmed: synthetic test CVs have complete dated histories, T07).
  pool        Writes the run file for scripts/build_cp23_test_workbook.py.
Caps: extraction US$1.00, matching US$2.50, parse and queries US$0.20 (all against the ledger,
on top of the project guard). Test outcomes are never used to change anything (D-046, D-053).
"""
from __future__ import annotations

import argparse
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

OUT = ROOT / 'evals/results/cp24/test_run_v1'
QUERY_CACHE = ROOT / 'reports/embedding_queries_test'
DEV_PARSES = ROOT / 'evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1'
CVS = {'CV1': 'data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md',
       'CV2': 'data/synthetic_cvs/cv_02_career_switcher_ai_engineer_en.md',
       'CV3': 'data/synthetic_cvs/cv_03_junior_ml_engineer_1yr_en.md',
       'CV4': 'data/synthetic_cvs/cv_04_data_analyst_to_ds_id.md',
       'CV5': 'data/synthetic_cvs/cv_05_ml_engineer_3yr_en.md'}
DEV_CV = {'CV1', 'CV2'}
CAPS = {'parse': 0.20, 'queries': 0.20, 'extraction': 1.00, 'matching': 2.50}
PARSE_MODEL = 'deepseek-flash'
ANALYSIS_DATE = date(2026, 9, 30)
PHASES = ('parse', 'queries', 'stage1', 'extraction', 'matching', 'pool')


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write_once(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=1, default=str)


def read(path: Path):
    return json.loads(path.read_text())


def test_ids() -> list[str]:
    return sorted((ROOT / 'evals/splits/test_job_ids.txt').read_text().split())


def first_name(path: Path) -> str:
    for line in path.read_text().splitlines():
        if line.startswith('# '):
            return line[2:].split()[0]
    raise ValueError(f'no name heading in {path.name}')


def config_path(freeze: Path) -> Path:
    return ROOT / read(freeze / 'freeze_receipt_APPROVED.json')['config_file']


def require_approved(freeze: Path | None) -> Path:
    from scripts.run_corpus_extraction import require_freeze
    require_freeze(freeze)
    return freeze


# ---------- pure helpers (unit tested) ----------

def analyzed_jobs(stage1: dict[str, list[str]], buckets: dict, k: int, rule: bool = True) -> dict[str, list[str]]:
    from jobfit.search.seniority import demote_senior
    return {cv: demote_senior(ids, buckets, enabled=rule)[:k] for cv, ids in stage1.items()}


def run_file(stage1: dict, finals: dict, freeze: Path, run_id: str) -> dict:
    if set(stage1) != set(finals):
        raise ValueError('every CV needs both orders')
    return {'run_id': run_id, 'freeze_folder': str(freeze.relative_to(ROOT)) if freeze.is_absolute() else str(freeze),
            'cvs': {cv: {'stage1_ids': stage1[cv][:10], 'final_order': finals[cv][:10]} for cv in sorted(stage1)}}


# ---------- phases ----------

def base_client(run_id: str, cfg_file: Path | None = None):
    from jobfit.config import get_settings
    from jobfit.llm.client import OpenRouterClient
    from jobfit.llm.runtime import build_runtime_client
    settings = get_settings()
    if settings.api_budget_usd != 19 or settings.api_hard_stop_usd != 18.5:
        raise SystemExit('Project guard values changed; ask Dion')
    if cfg_file:
        return build_runtime_client(settings, cfg_file, run_id=run_id)
    return OpenRouterClient(settings, run_id=run_id, chat_timeout_seconds=240.0)


def phase_parse(execute: bool) -> dict:
    from jobfit.cv.parser import parse_cv
    from jobfit.cv.text_extract import TextResult, extract_text
    from jobfit.privacy.masking import mask_local
    plan = {'reuse_dev': sorted(DEV_CV), 'parse': [c for c in CVS if c not in DEV_CV and not (OUT / f'{c}_parse.json').exists()]}
    if not execute:
        return plan
    for cv in sorted(DEV_CV):
        dest = OUT / f'{cv}_parse.json'
        if not dest.exists():
            src = DEV_PARSES / f'{cv}_parse.json'
            write_once(dest, {**read(src), 'reused_from': str(src.relative_to(ROOT)), 'reused_sha256': digest(src)})
    if plan['parse']:
        from scripts.run_cp23_luna_matching import CappedClient
        from scripts.probe_openrouter_access import require_access
        require_access([PARSE_MODEL])
        base = base_client('cp24_test_parse_v1')
        client = CappedClient(base, base.ledger.total_spent(), cap=CAPS['parse'])
        with base.ledger.exclusive():
            for cv in plan['parse']:
                path = ROOT / CVS[cv]
                raw = extract_text(path.read_bytes(), path.name)
                name = first_name(path)
                preview = mask_local(raw.text, reviewed_identifiers={'name': (name,)})
                if name.casefold() in preview.text.casefold():
                    raise SystemExit(f'{cv}: identifier remained after masking')
                parsed = parse_cv(TextResult(text=preview.text), cv_id=cv, analysis_date=ANALYSIS_DATE,
                                  client=client, model=PARSE_MODEL, is_synthetic=True)
                write_once(OUT / f'{cv}_parse.json', {'cv_id': cv, 'status': parsed.profile.parse_status.value,
                           'masking_counts': preview.counts, 'masked_digest': preview.digest,
                           'parsed': parsed.model_dump(mode='json'), 'attempts': parsed.attempts})
                if parsed.profile.parse_status.value != 'ok':
                    raise SystemExit(f'{cv} parsing failed; stop before matching (record kept)')
    return plan


class HeldOutQueryCache:
    """Same file format as the development cache, its own folder, CV1-CV5 allowed."""

    def __init__(self, directory: Path):
        from jobfit.search.query_cache import SyntheticQueryCache
        self.inner = SyntheticQueryCache(directory)
        self.directory = directory

    def path(self, spec, doc):
        from jobfit.search.embeddings import sha256 as h
        if doc.document_id not in CVS:
            raise ValueError('held-out query cache permits CV1-CV5 only')
        return self.directory / (h('|'.join((doc.document_id, spec.profile_id, doc.source_hash, doc.input_hash))) + '.json')

    def get(self, spec, doc):
        from jobfit.search.embeddings import validate_vector
        row = read(self.path(spec, doc))
        if row['profile_id'] != spec.profile_id or row['input_hash'] != doc.input_hash or row['source_hash'] != doc.source_hash:
            raise ValueError('query cache provenance mismatch')
        validate_vector(row['vector'], spec.dimensions)
        return row['vector']

    def put(self, spec, doc, vector):
        from dataclasses import asdict
        from jobfit.search.embeddings import validate_vector
        validate_vector(vector, spec.dimensions)
        path = self.path(spec, doc)
        if path.exists():
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        write_once(path, dict(profile_id=spec.profile_id, profile_spec=asdict(spec), source_hash=doc.source_hash,
                              input_hash=doc.input_hash, vector=vector))


def query_docs():
    from jobfit.search.embeddings import ModelTokenizer, cv_body, load_specs, prepare
    spec = next(s for s in load_specs() if 'qwen' in s.model)
    tok = ModelTokenizer(spec)
    return spec, {cv: prepare(cv, cv_body(ROOT / p), spec, tok) for cv, p in CVS.items()}


def phase_queries(execute: bool) -> dict:
    from jobfit.search.query_cache import SyntheticQueryCache
    spec, docs = query_docs()
    cache = HeldOutQueryCache(QUERY_CACHE)
    missing = [cv for cv, d in docs.items() if not cache.path(spec, d).exists()]
    plan = {'model': spec.model, 'copy_from_dev': [c for c in missing if c in DEV_CV],
            'embed': [c for c in missing if c not in DEV_CV]}
    if not execute:
        return plan
    dev = SyntheticQueryCache(ROOT / 'reports/embedding_queries')
    for cv in plan['copy_from_dev']:
        cache.put(spec, docs[cv], dev.get(spec, docs[cv]))
    if plan['embed']:
        base = base_client('cp24_test_queries_v1')
        if base.ledger.total_spent() + CAPS['queries'] > 18.5:
            raise SystemExit('No room under the project hard stop')
        vectors = base.embed([docs[c].text for c in plan['embed']], model=spec.model, task='test_query_embedding',
                             dimensions=spec.dimensions)
        for cv, vec in zip(plan['embed'], vectors):
            cache.put(spec, docs[cv], vec)
    return plan


def phase_stage1(execute: bool, cfg) -> dict:
    dest = OUT / 'stage1.json'
    plan = {'cvs': list(CVS), 'eligible': 'test split, 214 jobs', 'depth': cfg.stage1_candidate_depth, 'exists': dest.exists()}
    if not execute or dest.exists():
        return plan
    from jobfit.db.session import connect
    from jobfit.recommend.service import hybrid_retriever
    from jobfit.search import keyword
    spec, docs = query_docs()
    cache = HeldOutQueryCache(QUERY_CACHE)
    from jobfit.search.dense import QueryEmbedding
    ids = test_ids()
    out = {}
    with connect() as conn:
        for cv, doc in docs.items():
            retrieve = hybrid_retriever(conn, keyword.cv_skills(doc.text), QueryEmbedding(spec.profile_id, cache.get(spec, doc)),
                                        spec, job_ids=ids)
            out[cv] = retrieve(cfg.stage1_candidate_depth)
            if not set(out[cv]) <= set(ids) or len(out[cv]) != cfg.stage1_candidate_depth:
                raise SystemExit(f'{cv}: stage-1 result outside the test split or short')
    write_once(dest, {'rankings': out, 'test_ids_sha256': digest(ROOT / 'evals/splits/test_job_ids.txt'),
                      'profile_id': spec.profile_id, 'created': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
    return plan


def features():
    return {json.loads(l)['final_cluster_id']: json.loads(l)
            for l in (ROOT / 'data/processed/jobs_features.jsonl').read_text().splitlines()}


def phase_extraction(execute: bool, cfg, cfg_raw: dict) -> dict:
    stage1 = read(OUT / 'stage1.json')['rankings']
    feats = features()
    jobs = sorted(set().union(*analyzed_jobs(stage1, {j: f.get('experience_bucket') for j, f in feats.items()},
                                             cfg.stage1_k).values()))
    todo = [j for j in jobs if not (OUT / f'jd_{j}.json').exists()]
    base = base_client('cp24_test_extraction_v1')
    price = base._price(cfg_raw['extraction_model'])
    costs = [r.cost_usd for r in base.ledger.records()
             if r.model == price.model_id and r.task == 'jd_extraction' and r.ok and r.cost_source == 'reported']
    estimate = round(1.5 * statistics.median(costs) * len(todo), 4)
    plan = {'jobs': len(jobs), 'to_call': len(todo), 'estimate_usd': estimate, 'cap_usd': CAPS['extraction']}
    if estimate > CAPS['extraction']:
        raise SystemExit('Estimate above the extraction cap')
    if not execute or not todo:
        return plan
    from jobfit.extraction.audited import ExtractionSpec
    from jobfit.extraction.cache import ExtractionCache
    from jobfit.extraction.jd_extractor import extract_jd
    from scripts.probe_openrouter_access import require_access
    from scripts.run_cp23_luna_matching import CappedClient
    require_access([cfg_raw['extraction_model']])
    spec = ExtractionSpec(ROOT / cfg_raw['jd_prompt_file'], cfg_raw['jd_prompt_version'])
    cache = ExtractionCache(ROOT / 'reports/extraction_cache')
    client = CappedClient(base, base.ledger.total_spent(), cap=CAPS['extraction'])
    with base.ledger.exclusive():
        for job in todo:
            try:
                r = extract_jd(feats[job]['description_clean'], job_id=job, client=client, model=cfg_raw['extraction_model'],
                               cache=cache, scope='corpus_jd', spec=spec, dynamic_output=True)
                row = {'job_id': job, 'status': r.status, 'attempts': r.attempts, 'error_code': r.error_code,
                       'coverage': r.coverage, 'extraction': r.extraction.model_dump(mode='json') if r.extraction else None}
            except Exception as exc:  # kept, never retried here
                row = {'job_id': job, 'status': 'failed', 'error_code': type(exc).__name__, 'extraction': None}
            write_once(OUT / f'jd_{job}.json', row)
            print(json.dumps({'job_id': job, 'status': row['status'], 'error': row.get('error_code')}), flush=True)
            if row.get('error_code') in {'RunCapReached', 'AuthenticationError', 'PermissionDeniedError', 'BudgetExceeded'}:
                raise SystemExit('Stopped on a budget or authorization error')
    return plan


def phase_matching(execute: bool, cfg, cfg_file: Path) -> dict:
    from jobfit.cv.parser import ParsedCV
    from jobfit.recommend.service import extraction_from_record, recommend
    from jobfit.api.presenter import recommendation
    stage1 = read(OUT / 'stage1.json')['rankings']
    feats = features()
    buckets = {j: f.get('experience_bucket') for j, f in feats.items()}
    todo = [cv for cv in CVS if not (OUT / f'final_{cv}.json').exists()]
    estimate = round(1.2 * 0.027 * cfg.stage1_k * len(todo), 4)
    plan = {'cvs': todo, 'k': cfg.stage1_k, 'estimate_usd': estimate, 'cap_usd': CAPS['matching']}
    if estimate > CAPS['matching']:
        raise SystemExit('Estimate above the matching cap')
    if not execute or not todo:
        return plan
    from scripts.probe_openrouter_access import require_access
    from scripts.run_cp23_luna_matching import CappedClient
    require_access([cfg.matching_model])
    base = base_client('cp24_test_matching_v1', cfg_file)
    client = CappedClient(base, base.ledger.total_spent(), cap=CAPS['matching'])
    meta = {j: {'title': f['title'], 'company': f['company']} for j, f in feats.items()}

    def lookup(job):
        p = OUT / f'jd_{job}.json'
        return extraction_from_record(read(p) if p.exists() else None)
    with base.ledger.exclusive():
        for cv in todo:
            parsed = ParsedCV.model_validate(read(OUT / f'{cv}_parse.json')['parsed'])
            start = time.perf_counter()
            rec = recommend(parsed, retrieve=lambda d, r=stage1[cv]: r[:d], buckets=buckets, extraction_for=lookup,
                            client=client, config=cfg, history_confirmed=True)
            write_once(OUT / f'final_{cv}.json', {
                'cv_id': cv, 'order': rec.order, 'analyzed_ids': rec.analyzed_ids, 'stage1_ids': rec.stage1_ids,
                'held_ids': rec.held_ids, 'fallback_ids': rec.fallback_ids, 'versions': rec.versions,
                'wall_s': round(time.perf_counter() - start, 1),
                'jobs': {j: {'score': r.score.model_dump(mode='json'),
                             'assessments': [a.model_dump(mode='json') for a in r.assessments],
                             'constraints': [c.model_dump(mode='json') for c in r.constraints],
                             'hold_reason': r.hold_reason, 'matcher_model': r.matcher_model, 'attempts': r.attempts}
                         for j, r in rec.jobs.items()},
                'presented': recommendation(rec, meta)})
            print(json.dumps({'cv': cv, 'held': rec.held_ids, 'fallback': rec.fallback_ids}), flush=True)
    return plan


def phase_pool(freeze: Path) -> dict:
    stage1 = read(OUT / 'stage1.json')['rankings']
    finals = {cv: read(OUT / f'final_{cv}.json')['order'] for cv in CVS}
    run = run_file(stage1, finals, freeze, 'cp24_test_v1')
    path = OUT / 'test_run.json'
    if not path.exists():
        write_once(path, run)
    return {'run_file': str(path.relative_to(ROOT)), 'next': f'python scripts/build_cp23_test_workbook.py {path.relative_to(ROOT)}'}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('phase', choices=PHASES)
    ap.add_argument('--freeze', type=Path, required=True, help='approved freeze folder under evals/freeze/')
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args(argv)
    freeze = require_approved(args.freeze if args.freeze.is_absolute() else ROOT / args.freeze)
    import yaml
    from jobfit.recommend.service import RecommendConfig
    cfg_file = config_path(freeze)
    cfg, cfg_raw = RecommendConfig.from_yaml(cfg_file), yaml.safe_load(cfg_file.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    if args.phase == 'parse':
        plan = phase_parse(args.execute)
    elif args.phase == 'queries':
        plan = phase_queries(args.execute)
    elif args.phase == 'stage1':
        plan = phase_stage1(args.execute, cfg)
    elif args.phase == 'extraction':
        plan = phase_extraction(args.execute, cfg, cfg_raw)
    elif args.phase == 'matching':
        plan = phase_matching(args.execute, cfg, cfg_file)
    else:
        plan = phase_pool(freeze)
    print(json.dumps({'phase': args.phase, 'executed': args.execute, **plan}, indent=1, default=str))
    if not args.execute and args.phase != 'pool':
        print('Dry run. Nothing was called or written.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
