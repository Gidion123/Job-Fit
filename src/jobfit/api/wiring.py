"""Real dependencies for the API (local demo on Dion's Mac). Not used by tests.

Before the D-053 freeze the app searches the 214 development jobs only, with
their saved extractions, so no test job is processed by a model. Demo CVs are the
synthetic CV1 and CV2 with the parse that the CP2.3 runs used, and their cached
query embeddings (no embedding call). Matching calls Sol through the runtime
client, so each demo run costs money (about US$0.55 for K=20) and is counted by
the project budget guard.

Production (JOBFIT_ENV=prod, CP3 Phase 2B, D-101, D-103): every live operation goes through the
Phase 2B runtime (reservation, correlated ledger, phase-scoped gate) with the production settings'
client_settings(); there is no fallback to the development wiring. The runtime uses the D-103
public-beta bounds: it admits parse, search and job_analysis only, and refuses the legacy 10-job
recommendation (phase_not_admitted). Search and job analysis are owner-only until the real-CV
consent adapter exists, and public live stays off: the deployment is dark.
"""
from __future__ import annotations

from datetime import date
import json
import threading

import yaml

from jobfit.api.main import AppDeps
from jobfit.config import REPO_ROOT, get_production_settings, get_settings
from jobfit.cv.parser import ParsedCV
from jobfit.extraction.saved_records import load_record
from jobfit.llm.runtime import build_runtime_client
from jobfit.recommend.service import RecommendConfig, extraction_from_record, hybrid_retriever, recommend
from jobfit.search.filters import JobFilters, filter_jobs
from jobfit.session.store import SessionStore

CONFIG = REPO_ROOT / 'config/versions/pipeline_cp23_freeze_candidate_v4_20261006.yaml'
# Demo CVs are synthetic with complete dated work histories by design (T07), so the
# D-086 experience block treats their history as confirmed. Uploaded CVs need the user's confirmation.
DEMO_HISTORY_CONFIRMED = True
PARSES = REPO_ROOT / 'evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1'
CV_FILES = {'CV1': 'cv_01_fresh_graduate_data_science_id.md', 'CV2': 'cv_02_career_switcher_ai_engineer_en.md'}


def _features() -> dict[str, dict]:
    rows = {}
    for line in (REPO_ROOT / 'data/processed/jobs_features.jsonl').read_text().splitlines():
        row = json.loads(line)
        rows[row['final_cluster_id']] = row
    return rows


def _extraction_record(job: str) -> dict | None:
    return load_record(job)


def load_saved_demo():
    """Latest saved demo bundle; answers only when its key matches the current files."""
    from hashlib import sha256
    from jobfit.llm.runtime import RULES_FILE
    from jobfit.recommend.saved_demo import demo_key
    folders = sorted((REPO_ROOT / 'evals/demo').glob('saved_demo_v*'), key=lambda p: int(p.name.rsplit('_v', 1)[1]))
    if not folders:
        return None
    entries = json.loads((folders[-1] / 'bundle.json').read_text())['entries']
    def digest(path):
        return sha256(path.read_bytes()).hexdigest()

    def lookup(cv_id: str, seniority: bool):
        if cv_id not in CV_FILES:
            return None
        key = demo_key(cv_id=cv_id, cv_sha256=digest(REPO_ROOT / 'data/synthetic_cvs' / CV_FILES[cv_id]),
                       config_sha256=digest(CONFIG), rules_sha256=digest(RULES_FILE), seniority=seniority)
        entry = entries.get(key)
        return entry['result'] if entry else None
    return lookup


class LiveUnavailable(RuntimeError):
    """Live analysis is switched off or its local inputs are missing in this deployment."""


def live_enabled() -> bool:
    # Fail closed (FAIL-38, D-096): off unless JOBFIT_LIVE_ENABLED=1 and the production settings
    # are complete. Invalid or contradictory settings raise ConfigurationError instead of guessing.
    return get_production_settings().live_enabled


def build_runtime(settings, telemetry=None):
    """The Phase 2B runtime for prod live; startup reconciliation of expired, unowned reservations.

    Reconciliation runs only on a provisioned, writable ledger storage root with trustworthy
    evidence (it checks both itself). A missing or invalid root never stops the app: the saved demo
    keeps working and every live operation is refused (ledger_storage_unavailable).
    """
    import logging
    from jobfit.live.operation import LiveRuntime
    from jobfit.live.storage import StorageUnavailable
    from jobfit.live.runtime_client import build_public_beta_client
    from jobfit.llm.public_beta_bounds import compute_public_beta_bounds
    # Every live provider request (chat and embeddings) is sent with data_collection=deny and zdr=true.
    runtime = LiveRuntime(settings, compute_public_beta_bounds(), pipeline_config=CONFIG, telemetry=telemetry,
                          client_factory=lambda op: build_public_beta_client(settings.client_settings(), CONFIG,
                                                                             run_id=op))
    try:
        runtime.storage.validate()
    except StorageUnavailable as exc:
        logging.getLogger('jobfit.live').warning('ledger storage not ready at startup: %s', exc.reason)
    try:
        runtime.reconcile()
    except Exception:
        pass        # admission still decides from persisted state (any open reservation refuses)
    return runtime


def build_deps() -> AppDeps:
    settings = get_production_settings()
    prod = settings.environment == 'prod'
    from jobfit.observability.metrics import Telemetry
    from jobfit.observability.cost import CostCollector, DatabaseCollector, production_snapshot
    telemetry = Telemetry()
    telemetry.registry.register(CostCollector(production_snapshot(settings)))
    if prod:
        import psycopg
        telemetry.registry.register(DatabaseCollector(
            lambda: psycopg.connect(settings.database_url, autocommit=True, connect_timeout=2)))
    runtime = build_runtime(settings, telemetry=telemetry) if prod and settings.live_enabled else None
    config = RecommendConfig.from_yaml(CONFIG)
    features = _features()
    dev = set((REPO_ROOT / 'evals/splits/dev_job_ids.txt').read_text().split())
    buckets = {j: r.get('experience_bucket') for j, r in features.items()}
    meta = {j: {'title': r['title'], 'company': r['company'], 'location': r.get('location_raw'),
                'url': r.get('apply_url')} for j, r in features.items() if j in dev}
    demo = {cv: ParsedCV.model_validate(json.loads((PARSES / f'{cv}_parse.json').read_text())['parsed'])
            for cv in CV_FILES}
    target = [features[j] for j in sorted(dev) if features[j].get('role_group') == 'target']
    analysis_date = date.fromisoformat(str(yaml.safe_load(CONFIG.read_text())['analysis_date']))
    live_state: dict = {}
    lock = threading.Lock()

    def live_inputs():
        """Built on the first live run only: DB, tokenizer, query cache and (dev only) model client."""
        if not live_enabled():
            raise LiveUnavailable('Live analysis is switched off in this deployment')
        with lock:
            if live_state:
                return live_state
            from jobfit.search import dense, keyword
            from jobfit.search.embeddings import ModelTokenizer, cv_body, load_specs, prepare
            from jobfit.search.query_cache import SyntheticQueryCache
            try:
                spec = next(s for s in load_specs() if 'qwen' in s.model)
                cache = SyntheticQueryCache(REPO_ROOT / 'reports/embedding_queries')
                queries = {}
                for cv, name in CV_FILES.items():
                    text = cv_body(REPO_ROOT / 'data/synthetic_cvs' / name)
                    doc = prepare(cv, text, spec, ModelTokenizer(spec))
                    queries[cv] = (keyword.cv_skills(text), dense.QueryEmbedding(spec.profile_id, cache.get(spec, doc)))
            except (OSError, ValueError, KeyError) as exc:
                raise LiveUnavailable(f'Local retrieval inputs are missing: {type(exc).__name__}') from exc
            live_state.update(spec=spec, queries=queries)
            if not prod:      # development only; prod builds one reserved client per operation
                live_state['client'] = build_runtime_client(get_settings(), CONFIG, run_id='app_demo')
            return live_state

    def run(cv: ParsedCV, seniority_enabled: bool, on_result, filters: JobFilters | None = None, live=None):
        from jobfit.db.session import connect
        if prod and (runtime is None or live is None):
            raise LiveUnavailable('production live runs only through the Phase 2B runtime')
        state = live_inputs()
        filtered = filter_jobs(target, filters or JobFilters(), analysis_date=analysis_date)
        eligible = list(filtered.eligible_ids)

        def pipeline(client):
            stage1 = []
            if eligible:
                skills, query = state['queries'][cv.profile.cv_id]
                with connect(settings.database_url if prod else None) as conn:
                    retrieve = hybrid_retriever(conn, skills, query, state['spec'], job_ids=eligible)
                    stage1 = retrieve(min(config.stage1_candidate_depth, len(eligible)))
            return recommend(cv, retrieve=lambda depth: stage1[:depth], buckets=buckets,
                             extraction_for=lambda j: extraction_from_record(_extraction_record(j)),
                             client=client, config=config, seniority_enabled=seniority_enabled,
                             on_result=on_result, filtered=filtered, history_confirmed=DEMO_HISTORY_CONFIRMED)
        if prod:
            result, _ = runtime.run('recommendation', live.operation_key, pipeline,
                                    on_first_intent=live.on_first_billable)
            return result
        return pipeline(state['client'])

    client_state: dict = {}

    def model_client():
        if not live_enabled():
            raise LiveUnavailable('Live analysis is switched off in this deployment')
        with lock:
            if 'client' not in client_state:
                client_state['client'] = build_runtime_client(get_settings(), CONFIG, run_id='app_paste')
            return client_state['client']

    raw_cfg = yaml.safe_load(CONFIG.read_text())

    def analyze_pasted(cv: ParsedCV, jd_text: str):
        """Pasted JD: extraction with no cache (session data never reaches a disk cache), then the
        same matching, score and experience rule as a corpus job."""
        from jobfit.extraction.audited import ExtractionSpec
        from jobfit.extraction.jd_extractor import extract_jd
        from jobfit.matching.experience_rule import constraint_lookup
        from jobfit.recommend.service import analyze_job
        client = model_client()
        spec = ExtractionSpec(REPO_ROOT / raw_cfg['jd_prompt_file'], raw_cfg['jd_prompt_version'])
        ext = extract_jd(jd_text, job_id='pasted', client=client, model=raw_cfg['extraction_model'], cache=None,
                         scope='session_jd', spec=spec, dynamic_output=True)
        extraction, reason = (ext.extraction, None) if ext.status == 'done' else (None, ext.error_code or ext.status)
        if extraction is not None and extraction.jd_quality.value != 'ok':
            extraction, reason = None, 'jd_quality_' + extraction.jd_quality.value
        constraints = (constraint_lookup(cv, history_confirmed=DEMO_HISTORY_CONFIRMED)
                       if config.experience_conflict_rule else None)
        return analyze_job(cv, 'pasted', 1, extraction, reason, client=client, fallback_client=None,
                           config=config, constraints=constraints)

    def search(cv: ParsedCV, filters: JobFilters | None = None) -> list[str]:
        """D-103 search stage for a demo CV: hybrid retrieval with its cached query embedding (no
        provider call), in retrieval order. A real CV's query embedding (the 'search' phase) comes
        with the real-CV consent adapter."""
        from jobfit.db.session import connect
        state = live_inputs()
        filtered = filter_jobs(target, filters or JobFilters(), analysis_date=analysis_date)
        eligible = list(filtered.eligible_ids)
        if not eligible:
            return []
        skills, query = state['queries'][cv.profile.cv_id]
        with connect(settings.database_url if prod else None) as conn:
            retrieve = hybrid_retriever(conn, skills, query, state['spec'], job_ids=eligible)
            # D-105: the browse list uses the frozen stage-1 candidate depth (30), not the analyzed K
            return list(retrieve(min(config.stage1_candidate_depth, len(eligible))))

    def beta_envelopes():
        from jobfit.llm.public_beta_bounds import compute_public_beta_bounds
        return runtime.bounds.envelopes if runtime is not None else compute_public_beta_bounds().envelopes

    def job_source(job_id: str, jd_text: str | None) -> dict:
        """Pasted text, a matchable saved extraction, or (production) the eligible production JD text
        for a live extraction inside the same job_analysis operation. No development fallback."""
        if jd_text is not None:
            return {'jd_text': jd_text}
        cached = extraction_from_record(_extraction_record(job_id))
        if cached[0] is not None or not prod:
            return {'cached': cached}
        import psycopg
        from jobfit.search.production import eligible_job_text
        with psycopg.connect(settings.database_url, autocommit=True) as conn:
            return {'jd_text': eligible_job_text(conn, job_id)}

    def job_analysis_refusal(cv: ParsedCV, *, job_id: str, jd_text: str | None):
        from jobfit.recommend.beta_analysis import job_analysis_refusal as refusal
        return refusal(beta_envelopes(), cv, job_id, **job_source(job_id, jd_text))

    def analyze_one(cv: ParsedCV, *, job_id: str, jd_text: str | None, live=None,
                    history_confirmed: bool = DEMO_HISTORY_CONFIRMED):
        """D-103 job_analysis: one JD through the frozen steps (no disk cache for a pasted JD).

        ``history_confirmed``: synthetic demo CVs are complete by design; an uploaded CV passes the user's
        own confirmation for its current digest (D-105), so its history is never assumed complete.
        """
        from jobfit.extraction.audited import ExtractionSpec
        from jobfit.matching.experience_rule import constraint_lookup
        from jobfit.recommend.beta_analysis import analyze_one_job
        if prod and (runtime is None or live is None):
            raise LiveUnavailable('production live runs only through the Phase 2B runtime')
        spec = ExtractionSpec(REPO_ROOT / raw_cfg['jd_prompt_file'], raw_cfg['jd_prompt_version'])
        constraints = (constraint_lookup(cv, history_confirmed=history_confirmed)
                       if config.experience_conflict_rule else None)

        def work(client):
            return analyze_one_job(cv, job_id, envelopes=beta_envelopes(), client=client, config=config,
                                   spec=spec, extraction_model=raw_cfg['extraction_model'], scope='session_jd',
                                   constraints=constraints, telemetry=telemetry, **job_source(job_id, jd_text))
        if prod:
            result, _ = runtime.run('job_analysis', live.operation_key, work, quota=getattr(live, 'quota', None),
                                    on_first_intent=live.on_first_billable)
            return result
        return work(model_client())

    # --- real-CV public beta (CP3): every hook runs only on the production runtime -------------------
    def real_parse(store, handle, lease, *, live):
        from jobfit.recommend.real_cv_flow import reserved_parse
        if runtime is None or live is None:
            raise LiveUnavailable('production live runs only through the Phase 2B runtime')
        parse_model = yaml.safe_load((REPO_ROOT / 'config/cp3/public_beta_bounds_v1.yaml').read_text())['parse_model']
        return reserved_parse(runtime, store, handle, lease, operation_key=live.operation_key, model=parse_model,
                              envelopes=runtime.bounds.envelopes, quota=live.quota,
                              on_first_intent=live.on_first_billable, telemetry=telemetry)

    def real_search(store, handle, lease, filters, *, live):
        import psycopg
        from jobfit.recommend.real_cv_flow import reserved_search
        from jobfit.search.embeddings import load_specs
        if runtime is None or live is None:
            raise LiveUnavailable('production live runs only through the Phase 2B runtime')
        models = yaml.safe_load((REPO_ROOT / 'config/models_v1.yaml').read_text())['embeddings']
        model_id = models[raw_cfg['embedding_model']]['id']
        spec = next(s for s in load_specs() if s.model == model_id)
        return reserved_search(runtime, store, handle, lease, operation_key=live.operation_key, spec=spec,
                               connect=lambda: psycopg.connect(settings.database_url, autocommit=True),
                               filters=filters, depth=config.stage1_candidate_depth, envelopes=runtime.bounds.envelopes,
                               quota=live.quota, on_first_intent=live.on_first_billable, telemetry=telemetry)

    def consume_ticket(pseudonym: str) -> str:
        import psycopg
        from jobfit.live.quota import consume_ticket as consume
        return consume(lambda: psycopg.connect(settings.database_url, autocommit=True), pseudonym)

    jobs = {j: {'job_id': j, 'title': r['title'], 'company': r['company'], 'location': r.get('location_raw'),
                'work_mode': r.get('work_mode'), 'posted_at': r.get('posted_at'),
                'experience_bucket': r.get('experience_bucket'), 'role_family': r.get('role_family'),
                'role_group': r.get('role_group'), 'skills': r.get('skills') or [], 'url': r.get('apply_url'),
                'description': r.get('description_clean')} for j, r in features.items() if j in dev}
    summaries = {cv: {**p.summary(), 'cv_id': cv, 'synthetic': True,
                      'history_confirmed': DEMO_HISTORY_CONFIRMED,
                      'note': 'Synthetic demo CV; work history is complete by design, so it counts as confirmed.'}
                 for cv, p in demo.items()}
    ingress = maintenance = None
    if prod:
        import psycopg
        from jobfit.live.quota import Ingress, purge_expired
        ingress = Ingress(settings.internal_token, settings.owner_token, settings.ip_hmac_key)

        def maintenance():
            """D-096: quota rows are deleted after 48 h (startup and hourly; consume purges too)."""
            purge_expired(lambda: psycopg.connect(settings.database_url, autocommit=True))
        try:
            maintenance()
        except Exception:
            pass        # retried hourly by the sweeper; a consume purges before it runs anyway
    return AppDeps(telemetry=telemetry, store=SessionStore(), demo_cvs=demo, run=run, job_meta=meta, saved_demo=load_saved_demo(),
                   live_enabled=settings.live_enabled, analyze_pasted=None if prod else analyze_pasted, jobs=jobs,
                   demo_summaries=summaries, analyzed_k=config.stage1_k, ingress=ingress,
                   public_live=settings.public_live, maintenance=maintenance,
                   live_storage_ready=runtime.storage_ready if runtime is not None else None,
                   search=search, analyze_one=analyze_one, job_analysis_refusal=job_analysis_refusal,
                   search_limit=config.stage1_candidate_depth,
                   # D-105: uploaded CVs only with the explicit JOBFIT_REAL_CV_ENABLED switch on the production
                   # runtime; the public beta stays closed (non-owners get 503), whatever JOBFIT_PUBLIC_LIVE says.
                   real_cv_enabled=settings.real_cv_enabled and runtime is not None, public_beta_open=False,
                   real_parse=real_parse if prod else None, real_search=real_search if prod else None,
                   consume_ticket=consume_ticket if prod else None)


def create_default_app():
    from jobfit.observability.http import configure_logging
    configure_logging()
    from jobfit.api.main import create_app
    return create_app(build_deps())
