"""Read-only, cache-only development retrieval. No labels or inference clients."""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import yaml
from jobfit.config import REPO_ROOT, SNAPSHOT_ID
from jobfit.eval.run_eval import CV_FILES
from jobfit.jobs.skills import DEFAULT_ALIAS_FILE
from jobfit.search import keyword, fts, dense, hybrid
from jobfit.search.embeddings import ModelTokenizer, cv_body, job_text, load_specs, prepare
from jobfit.search.query_cache import SyntheticQueryCache


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked_ranking(rows, eligible, k):
    ids = [r['job_id'] for r in rows]
    if len(ids) != len(set(ids)) or not set(ids) <= set(eligible) or len(ids) > k:
        raise ValueError('Invalid ranking identities/scope/depth')
    import math
    if any(not math.isfinite(r['score']) for r in rows):
        raise ValueError('Non-finite retrieval score')
    return rows


def measure(method, action, *, eligible, k, context, clock=time.perf_counter):
    start = clock()
    try:
        rows = checked_ranking(action(), eligible, k)
        return dict(context, method=method, status='success', ranking=[r['job_id'] for r in rows],
                    results=rows, returned_count=len(rows), latency_ms=(clock()-start)*1000,
                    error_type=None)
    except Exception as exc:
        # Never persist DB connection strings or source/query text from exceptions.
        return dict(context, method=method, status='failed', ranking=[], results=[],
                    returned_count=0, latency_ms=(clock()-start)*1000,
                    error_type=type(exc).__name__)


def validate_jobs(source, database):
    if len(database) != len(source) or {r['job_id'] for r in database} != set(source):
        raise ValueError('Database development coverage differs from frozen source')
    for row in database:
        s = source[row['job_id']]
        expected = dict(job_id=row['job_id'], snapshot_id=SNAPSHOT_ID, content_hash=s['content_hash'],
                        title=s['title'], normalized_title=s.get('normalized_title'),
                        description_clean=s['description_clean'], role_group=s['role_group'],
                        skills_v0=list(s.get('skills') or []))
        if row != expected or row['role_group'] != 'target':
            raise ValueError('Database source/skill/snapshot mismatch')


def cached_queries(root, specs, tokenizers):
    cache = SyntheticQueryCache(root/'reports/embedding_queries')
    out = {}
    for cv, filename in CV_FILES.items():
        path = root/'data/synthetic_cvs'/filename
        text = cv_body(path)
        skills = keyword.cv_skills(text)
        out[cv] = dict(cv_sha256=file_hash(path), query_body_sha256=digest(text),
                       skills=skills, queries={})
        for spec in specs:
            doc = prepare(cv, text, spec, tokenizers[spec.profile_id])
            try:
                vector = cache.get(spec, doc)
            except (FileNotFoundError, ValueError, KeyError, json.JSONDecodeError) as exc:
                raise ValueError(f'Incompatible or missing cached query: {cv}/{spec.model}; no inference fallback') from exc
            out[cv]['queries'][spec.profile_id] = dict(
                query=dense.QueryEmbedding(spec.profile_id, vector), input_hash=doc.input_hash,
                source_hash=doc.source_hash, cache_sha256=file_hash(cache.path(spec, doc)))
    return out


def run(conn, *, root=REPO_ROOT, k=30):
    """Caller supplies a fresh connection; this transaction is read-only/repeatable."""
    if not isinstance(k, int) or isinstance(k, bool) or k < 30:
        raise ValueError('Technical comparison requires at least top30')
    root = Path(root)
    start = time.perf_counter()
    cfg = yaml.safe_load((root/'config/retrieval_v1.yaml').read_text())
    branch = max(k, cfg['branch_depth'])
    manifest = json.loads((root/'evals/splits/split_manifest.json').read_text())
    dev_path = root/'evals/splits/dev_job_ids.txt'
    if file_hash(dev_path) != manifest['output_hashes']['dev_job_ids.txt']:
        raise ValueError('Frozen development split changed')
    dev = set(dev_path.read_text().splitlines())
    if len(dev) != 214:
        raise ValueError('Unexpected development universe')
    source_path = root/'data/processed/jobs_features.jsonl'
    source = {}
    for line in source_path.read_text().splitlines():
        row = json.loads(line)
        if row['final_cluster_id'] in dev:
            if row['final_cluster_id'] in source: raise ValueError('Duplicate source ID')
            source[row['final_cluster_id']] = row
    if set(source) != dev: raise ValueError('Missing development source')
    specs = load_specs(root/'config/models_v1.yaml')
    # Fail before tokenizer initialization could try to download OpenAI's vocabulary.
    tiktoken_file = root/'reports/tokenizers/tiktoken/9b5ad71b2ce5302211f9c61530b329a4922fc6a4'
    if not tiktoken_file.exists(): raise ValueError('Local OpenAI tokenizer missing; no network fallback')
    # Pinned cl100k_base bytes checked before tiktoken can reload a corrupt cache online.
    if file_hash(tiktoken_file) != '223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7':
        raise ValueError('Local OpenAI tokenizer checksum mismatch; no network fallback')
    tokenizers = {s.profile_id:ModelTokenizer(s) for s in specs}
    queries = cached_queries(root, specs, tokenizers)
    conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    columns = ['job_id','snapshot_id','content_hash','title','normalized_title','description_clean','role_group','skills_v0']
    rows = conn.execute('SELECT '+','.join(columns)+' FROM jobs WHERE job_id=ANY(%s) ORDER BY job_id', (sorted(dev),)).fetchall()
    jobs = [dict(zip(columns, r)) for r in rows]
    validate_jobs(source, jobs)
    vector_receipts = {}
    for spec in specs:
        rows = conn.execute('SELECT job_id,content_hash,input_hash,model,dimensions,preprocessing_version,profile_spec,md5(embedding::text) FROM job_embedding_versions WHERE profile_id=%s AND job_id=ANY(%s) ORDER BY job_id,input_hash', (spec.profile_id,sorted(dev))).fetchall()
        # Ignore historical source versions but reject ambiguous current input versions.
        rows = [r for r in rows if r[1] == source[r[0]]['content_hash']]
        if len(rows)!=len(dev) or {r[0] for r in rows}!=dev:
            raise ValueError('Missing/ambiguous current corpus vectors')
        for r in rows:
            doc = prepare(r[0], job_text(source[r[0]]), spec, tokenizers[spec.profile_id], source_hash=r[1])
            if (r[2],r[3],r[4],r[5],r[6]) != (doc.input_hash,spec.model,spec.dimensions,spec.preprocessing_version,asdict(spec)):
                raise ValueError('Corpus embedding input/profile mismatch')
        vector_receipts[spec.profile_id] = dict(count=len(rows), records_sha256=digest(rows), spec=asdict(spec))
    effective = dict(cfg, branch_depth=branch, requested_top_k=k)
    provenance = {p:file_hash(root/p) for p in ['config/retrieval_v1.yaml','config/models_v1.yaml','config/tokenizers_v1.json','config/pipeline_v1.yaml','src/jobfit/eval/retrieval_run.py','src/jobfit/search/keyword.py','src/jobfit/search/fts.py','src/jobfit/search/dense.py','src/jobfit/search/hybrid.py','src/jobfit/search/embeddings.py','src/jobfit/db/models.py']}
    provenance[str(Path(DEFAULT_ALIAS_FILE).relative_to(REPO_ROOT))] = file_hash(DEFAULT_ALIAS_FILE)
    shared = dict(split='development',snapshot_id=SNAPSHOT_ID,split_sha256=file_hash(dev_path),
        corpus_sha256=file_hash(source_path),development_content_sha256=digest({j:source[j]['content_hash'] for j in sorted(dev)}),
        eligible_ids=sorted(dev),eligible_ids_sha256=digest(sorted(dev)),eligible_count=len(dev),
        filters={'role_group':['target'],'optional':{}},filter_status='no_optional_filters',
        retrieval_config=effective,config_sha256=digest(effective),requested_k=k,rrf_k=cfg['rrf_k'],
        branch_depth=branch,execution_kind='saved_retrieval',api_calls=0,cost_usd=0,
        timing_scope='rank invocation only: SQL/vector transfer + scoring/sorting; excludes connection, source/cache/tokenizer preparation and serialization',
        database_transaction='repeatable_read_read_only',provenance=provenance)
    runs = []
    for cv, q in queries.items():
        common = dict(shared,cv_id=cv,cv_sha256=q['cv_sha256'],query_body_sha256=q['query_body_sha256'],
                      skill_query_sha256=digest(sorted(q['skills'])),fts_query_sha256=digest(fts.query_phrases(q['skills'])))
        for method, action, tie in [
            ('B0',lambda:keyword.rank(q['skills'],jobs,top_k=k),'rounded_score DESC, matched_skill_count DESC, job_id ASC'),
            ('B1',lambda:fts.rank(conn,q['skills'],job_ids=dev,top_k=k),'raw_ts_rank_cd DESC, job_id ASC; emitted scores rounded4')]:
            runs.append(measure(method,action,eligible=dev,k=k,context=dict(common,model=None,tie_break=tie,
                query_input_sha256=common['skill_query_sha256'] if method=='B0' else common['fts_query_sha256'],
                preprocessing_version='cp1-skill-aliases-v0' if method=='B0' else 'cp1-skill-aliases-v0-fts-simple',
                preprocessing_sha256=digest({'aliases':file_hash(DEFAULT_ALIAS_FILE),'method':method,
                    'code':file_hash(root/('src/jobfit/search/keyword.py' if method=='B0' else 'src/jobfit/search/fts.py'))}))))
        for spec in specs:
            name = 'openai' if spec.model.startswith('openai/') else 'qwen'
            query = q['queries'][spec.profile_id]
            ctx = dict(common,model=spec.model,profile_id=spec.profile_id,dimensions=spec.dimensions,
                preprocessing_version=spec.preprocessing_version,preprocessing_sha256=digest(asdict(spec)),
                query_input_sha256=query['input_hash'],query_cache_sha256=query['cache_sha256'],
                corpus_vector_receipt=vector_receipts[spec.profile_id])
            runs.append(measure('dense_'+name,lambda:dense.rank(conn,query['query'],spec,job_ids=dev,top_k=k),
                eligible=dev,k=k,context=dict(ctx,tie_break='cosine_similarity DESC, job_id ASC')))
            runs.append(measure('hybrid_'+name,lambda:hybrid.rank(conn,q['skills'],query['query'],spec,job_ids=dev,top_k=k,branch_depth=branch,k=cfg['rrf_k']),
                eligible=dev,k=k,context=dict(ctx,tie_break='RRF_score DESC, job_id ASC; each branch uses its own documented tie rule')))
    return dict(status='success' if all(r['status']=='success' for r in runs) else 'partial_failure',
        purpose='technical_candidate_generation_only',created_at=datetime.now(timezone.utc).isoformat(),
        runs=runs,preparation_and_ranking_ms=(time.perf_counter()-start)*1000,
        optional_filter_comparison={'status':'deferred','reason':'filters.py is a placeholder; UNKNOWN/filter-status semantics not implemented'},
        depth_note='Run-local branch depth raised to requested top30 for sufficient candidate depth; saved default20 unchanged; no K selection',
        quality_metrics=None,winner=None,pool_modified=False,api_calls=0,cost_usd=0,
        limitation='Single fixed-order local run; warm-cache/order effects, not a production latency benchmark')
