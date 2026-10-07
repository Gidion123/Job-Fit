"""Preflight by default; --execute builds resumably and checks CV1/CV2 search.

No labels, test CVs, development pools, or model selection. Review the printed
estimate before --execute. Batches above USD 1 need separate human approval.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import os
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import yaml
from jobfit.config import REPO_ROOT, SNAPSHOT_ID, get_settings
from jobfit.db.models import SCHEMA_SQL
from jobfit.db.session import connect
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.pricing import estimate_cost
from jobfit.search.embeddings import ModelTokenizer, build, cv_body, job_text, load_specs, prepare
from jobfit.search.embedding_store import JobEmbeddingStore
from jobfit.search.query_cache import SyntheticQueryCache
from jobfit.search.response_cache import ResponseCache
from jobfit.search import dense, hybrid, keyword

DEV_CVS = {
    'CV1': 'cv_01_fresh_graduate_data_science_id.md',
    'CV2': 'cv_02_career_switcher_ai_engineer_en.md',
}


def job_inventory(conn):
    rows = conn.execute('SELECT job_id,content_hash,snapshot_id FROM jobs ORDER BY job_id').fetchall()
    return dict(jobs=len(rows), inventory_sha256=hashlib.sha256(json.dumps(rows).encode()).hexdigest(),
                legacy_embeddings=conn.execute('SELECT count(*) FROM job_embeddings').fetchone()[0])


def development_ids():
    directory = REPO_ROOT / 'evals/splits'
    manifest = json.loads((directory / 'split_manifest.json').read_text())
    # Frozen files are verified before any search; never recreate assignments.
    for name in ('dev_job_ids.txt', 'test_job_ids.txt'):
        digest = hashlib.sha256((directory / name).read_bytes()).hexdigest()
        if digest != manifest['output_hashes'][name]:
            raise ValueError('frozen split hash mismatch')
    dev = set((directory / 'dev_job_ids.txt').read_text().splitlines())
    test = set((directory / 'test_job_ids.txt').read_text().splitlines())
    if len(dev) != 214 or len(test) != 214 or dev & test:
        raise ValueError('invalid frozen split')
    return dev


def cost_plan(documents, client, spec, store, exists=True):
    missing = [d for d in documents if not exists or not store.contains(spec, d)]
    price = client._price(spec.model)
    tokens = sum(d.input_tokens for d in missing)
    upper = sum(len(d.text.encode('utf-8')) + 100 for d in missing)
    return dict(documents=len(documents), cached=len(documents)-len(missing), pending=len(missing),
                tokenizer_tokens=tokens, conservative_token_bound=upper,
                estimated_usd=estimate_cost(price, tokens), conservative_usd=estimate_cost(price, upper),
                truncated=sum(d.truncated for d in documents))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--run-id', default='embeddings-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    args = parser.parse_args()
    settings = get_settings()
    client = OpenRouterClient(settings, run_id=args.run_id)
    cfg = yaml.safe_load((REPO_ROOT / 'config/retrieval_v1.yaml').read_text())
    specs = load_specs(settings.models_file)
    ids = development_ids()
    report = dict(run_id=args.run_id, timestamp=datetime.now(timezone.utc).isoformat(),
                  executed=args.execute, snapshot_id=SNAPSHOT_ID,
                  corpus='all 632 loaded auditable jobs; search smoke restricted to development 214',
                  query_cvs=list(DEV_CVS), config=cfg, profiles=[], results=[], search_smoke=[],
                  ledger_before_usd=client.ledger.total_spent(), hard_stop_usd=settings.api_hard_stop_usd)
    destination = REPO_ROOT / 'evals/results' / (args.run_id + '.json')
    if destination.exists():
        raise ValueError('run report exists; choose a new run-id (cache still resumes)')

    def save():
        report['ledger_after_usd'] = client.ledger.total_spent()
        report['session_ledger_delta_usd'] = round(report['ledger_after_usd'] - report['ledger_before_usd'], 9)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', dir=destination.parent,
                                             prefix='.' + destination.name, delete=False) as output:
                temporary = output.name
                output.write(json.dumps(report, indent=2) + '\n')
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, destination)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

    with connect() as conn:
        conn.autocommit = True
        report['database_before'] = job_inventory(conn)
        if report['database_before']['jobs'] != 632:
            raise ValueError('unexpected loaded corpus size; inspect before proceeding')
        rows = conn.execute('SELECT job_id,content_hash,title,normalized_title,description_clean '
                            'FROM jobs WHERE snapshot_id=%s ORDER BY job_id', (SNAPSHOT_ID,)).fetchall()
        jobs = [dict(zip(('job_id','content_hash','title','normalized_title','description_clean'), r)) for r in rows]
        if len(jobs) != 632 or not ids <= {j['job_id'] for j in jobs}:
            raise ValueError('snapshot/split coverage mismatch')
        exists = conn.execute("SELECT to_regclass('job_embedding_versions')").fetchone()[0] is not None
        store = JobEmbeddingStore(conn, args.run_id)
        queries = SyntheticQueryCache(REPO_ROOT / 'reports/embedding_queries')
        all_inputs = []
        for spec in specs:
            tokenizer = ModelTokenizer(spec)
            documents = [prepare(j['job_id'], job_text(j), spec, tokenizer, j['content_hash']) for j in jobs]
            cvs = [prepare(cid, cv_body(REPO_ROOT / 'data/synthetic_cvs' / filename), spec, tokenizer)
                   for cid, filename in DEV_CVS.items()]
            plan = dict(profile=asdict(spec), profile_id=spec.profile_id,
                        jobs=cost_plan(documents, client, spec, store, exists),
                        queries=cost_plan(cvs, client, spec, queries))
            report['profiles'].append(plan)
            all_inputs.append((spec, documents, cvs))
        report['estimated_total_usd'] = sum(p[k]['estimated_usd'] for p in report['profiles'] for k in ('jobs','queries'))
        report['conservative_total_usd'] = sum(p[k]['conservative_usd'] for p in report['profiles'] for k in ('jobs','queries'))
        report['remaining_guard_usd'] = settings.api_hard_stop_usd - report['ledger_before_usd']
        client.guard.check(report['conservative_total_usd'])
        save()
        print(json.dumps({k: report[k] for k in ('run_id','profiles','estimated_total_usd','conservative_total_usd','remaining_guard_usd')}, indent=2), flush=True)
        if not args.execute:
            return 0
        if report['conservative_total_usd'] > 1.0:
            raise ValueError('batch exceeds USD 1; separate approval is required before execution')
        try:
            report['authentication'] = client.verify_inference_key()
        except Exception as exc:
            report['blocked_reason'] = 'key_verification_failed'
            report['authentication_error_type'] = type(exc).__name__
            save()
            print(json.dumps({'blocked_reason': report['blocked_reason'],
                              'error_type': type(exc).__name__}), flush=True)
            return 1
        if not report['authentication']['inference_key']:
            report['blocked_reason'] = ('management_key' if report['authentication']['is_management_key']
                                        else 'key_type_unknown')
            save()
            print(json.dumps({'blocked_reason': report['blocked_reason'],
                              'action': 'Use a regular API key from OpenRouter settings/keys.'}), flush=True)
            return 1
        save()
        conn.execute(SCHEMA_SQL)
        receipts = ResponseCache(REPO_ROOT / 'reports/embedding_receipts/responses.sqlite3')
        for spec, documents, cvs in all_inputs:
            for label, inputs, cache in [('jobs', documents, store), ('queries', cvs, queries)]:
                def progress(counts):
                    print(json.dumps(dict(model=spec.model, kind=label, **counts)), flush=True)
                result = build(inputs, spec, client, cache, cfg['batch_size'], cfg['max_batch_tokens'], progress,
                               response_cache=receipts)
                report['results'].append(dict(model=spec.model, kind=label, **result))
                save()
                if result['error_type']:
                    report['database_after'] = job_inventory(conn)
                    save()
                    receipts.close()
                    return 1
            for doc in cvs:
                query = dense.QueryEmbedding(spec.profile_id, queries.get(spec, doc))
                drows = dense.rank(conn, query, spec, job_ids=ids, top_k=20)
                hrows = hybrid.rank(conn, keyword.cv_skills(doc.text), query, spec,
                                    job_ids=ids, top_k=20, branch_depth=cfg['branch_depth'], k=cfg['rrf_k'])
                again = hybrid.rank(conn, keyword.cv_skills(doc.text), query, spec,
                                    job_ids=ids, top_k=20, branch_depth=cfg['branch_depth'], k=cfg['rrf_k'])
                valid = (len(drows) == len(hrows) == 20 and hrows == again
                         and {r['job_id'] for r in drows+hrows} <= ids)
                report['search_smoke'].append(dict(model=spec.model, cv_id=doc.document_id,
                    dense_count=len(drows), hybrid_count=len(hrows), valid=valid,
                    ranking_sha256=hashlib.sha256(json.dumps([drows,hrows],sort_keys=True).encode()).hexdigest()))
                if not valid:
                    raise ValueError('development retrieval smoke check failed')
        report['database_after'] = job_inventory(conn)
        receipts.close()
        report['database_unchanged'] = report['database_before'] == report['database_after']
        report['stored_embeddings'] = conn.execute('SELECT model,dimensions,count(*) FROM job_embedding_versions GROUP BY model,dimensions ORDER BY model').fetchall()
        save()
        if not report['database_unchanged']:
            raise ValueError('job inventory changed during embedding build')
    print(json.dumps(dict(report=str(destination.relative_to(REPO_ROOT)), results=report['results'],
                         search_smoke=report['search_smoke'], cost_usd=report['session_ledger_delta_usd'])), flush=True)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        # SDK error bodies can contain inputs. Never print exception messages here.
        print('Build stopped: ' + type(exc).__name__ + '. Inspect saved metadata and ledger.', file=sys.stderr)
        raise SystemExit(1)
