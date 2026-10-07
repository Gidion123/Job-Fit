"""Stage-3 development comparison from saved rankings and reviewed C records.

No inference, database access, label mutation, winner selection or test query.
Hash verification binds the comparison to the original ranking and review receipts.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

from jobfit.eval.contract import comparison_gates_ready, validate_metric_contract
from jobfit.eval.run_eval import CV_FILES, METHODS, compare_rankings

RANKINGS = 'evals/results/cp22_retrieval_top30_20261002_03.json'
READINESS = 'evals/results/cp23_stage1_readiness_20261003_v4.json'
CONTRACT = 'evals/results/cp23_metric_contract_D052_D054_20261003_v1.json'


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def checked_path(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('Missing or external comparison input')
    return path


def verify_hash(root, relative, expected, verified):
    actual = file_hash(checked_path(root, relative))
    if actual != expected:
        raise ValueError(f'Stale comparison input: {relative}')
    verified[relative] = actual


def aggregate(rows):
    """Macro means across the two CVs, never across ranked job positions."""
    out = []
    methods = sorted({r['method'] for r in rows})
    for method in methods:
        selected = [r for r in rows if r['method'] == method]
        if {r['cv_id'] for r in selected} != {'CV1', 'CV2'} or len(selected) != 2:
            raise ValueError('Exactly two development queries per method required')
        by_k = {r['cv_id']: {m['k']: m for m in r['metrics']} for r in selected}
        values = lambda k, key: [by_k[cv][k][key] for cv in ('CV1', 'CV2')]
        p5 = [v['value'] for v in values(5, 'precision_at_k')]
        n10 = values(10, 'ndcg_at_k')
        mean = lambda vs: sum(vs) / len(vs) if all(v is not None for v in vs) else None
        out.append({'method': method, 'query_count': 2,
                    'p_at_5_macro': mean(p5), 'ndcg_at_10_macro': mean(n10),
                    'recall_labeled_pool': {str(k): mean([v['value'] for v in values(k, 'recall_at_k')])
                                            for k in (10, 20, 30)},
                    'judged_original_top_k': {str(k): sum(by_k[cv][k]['coverage']['judged_at_metric_cutoff']
                                                        for cv in ('CV1', 'CV2')) for k in (10, 20, 30)},
                    'original_top_k_positions': {str(k): 2 * k for k in (10, 20, 30)},
                    'local_invocation_ms': {r['cv_id']: r['latency_ms'] for r in selected}})
    return out


def evaluate(root):
    root = Path(root).resolve()
    read = lambda p: json.loads(checked_path(root, p).read_text())
    readiness, contract, saved = read(READINESS), read(CONTRACT), read(RANKINGS)
    verified = {p: file_hash(checked_path(root, p)) for p in (READINESS, CONTRACT, RANKINGS)}
    for p in ('src/jobfit/eval/retrieval_evaluation.py', 'src/jobfit/eval/run_eval.py',
              'src/jobfit/eval/metrics.py', 'src/jobfit/eval/contract.py',
              'scripts/evaluate_cp23_retrieval.py'):
        verified[p] = file_hash(checked_path(root, p))
    validate_metric_contract(contract, root=root)
    if not comparison_gates_ready(readiness):
        raise ValueError('Stage-1 readiness remains blocked')
    for key, relative in readiness['receipt_paths'].items():
        if key == 'gold_bundle':
            continue
        verify_hash(root, relative, readiness['receipts'][key + '_sha256'], verified)
    bundle = readiness['receipt_paths']['gold_bundle']
    verify_hash(root, bundle + '/manifest.json', readiness['receipts']['gold_manifest_sha256'], verified)
    manifest = read(bundle + '/manifest.json')
    for relative, expected in manifest['files'].items():
        verify_hash(root, bundle + '/' + relative, expected, verified)
    dev_file = 'evals/splits/dev_job_ids.txt'
    split = read('evals/splits/split_manifest.json')
    verify_hash(root, dev_file, split['output_hashes']['dev_job_ids.txt'], verified)
    dev = checked_path(root, dev_file).read_text().splitlines()
    if len(dev) != len(set(dev)) or len(dev) != 214:
        raise ValueError('Frozen 214-job development universe required')
    c_path = bundle + '/relevance_gold.jsonl'
    rows = [json.loads(line) for line in checked_path(root, c_path).read_text().splitlines()]
    judgments = {'CV1': {}, 'CV2': {}}
    for row in rows:
        cv, job, grade = row['cv_id'], row['job_id'], row['relevance_0_3']
        if (cv not in judgments or job not in dev or row['split'] != 'development'
                or row['review_status'] != 'approved' or row['review_action'] not in {'accepted', 'edited', 'added'}
                or type(grade) is not int or grade not in range(4)):
            raise ValueError('Unapproved, held-out or invalid C reference')
        if job in judgments[cv]:
            raise ValueError('Duplicate C identity')
        judgments[cv][job] = grade
    if saved['status'] != 'success' or len(saved['runs']) != 12:
        raise ValueError('Twelve successful saved retrieval runs required')
    if {(r['cv_id'], r['method']) for r in saved['runs']} != {(cv, method) for cv in CV_FILES for method in METHODS}:
        raise ValueError('Incomplete six-method/two-query comparison')
    runs = []
    query_caches = {file_hash(p): str(p.relative_to(root))
                    for p in (root / 'reports/embedding_queries').glob('*.json')}
    for original in saved['runs']:
        r = dict(original)
        if (r['status'] != 'success' or r['api_calls'] != 0 or r['cost_usd'] != 0
                or r['split'] != 'development' or r['execution_kind'] != 'saved_retrieval'
                or r['snapshot_id'] != 'CP1_20260926' or r['eligible_count'] != 214
                or sorted(r['eligible_ids']) != sorted(dev) or r['filter_status'] != 'no_optional_filters'
                or r['filters'] != {'role_group': ['target'], 'optional': {}}):
            raise ValueError('Unexpected saved retrieval scope')
        for relative, expected in r['provenance'].items():
            verify_hash(root, relative, expected, verified)
        verify_hash(root, dev_file, r['split_sha256'], verified)
        verify_hash(root, 'data/processed/jobs_features.jsonl', r['corpus_sha256'], verified)
        verify_hash(root, 'data/synthetic_cvs/' + CV_FILES[r['cv_id']], r['cv_sha256'], verified)
        if r.get('query_cache_sha256'):
            relative = query_caches.get(r['query_cache_sha256'])
            if relative is None:
                raise ValueError('Saved query cache is missing or changed; no inference fallback')
            verify_hash(root, relative, r['query_cache_sha256'], verified)
        if r['eligible_ids_sha256'] != digest(sorted(dev)) or r['config_sha256'] != digest(r['retrieval_config']):
            raise ValueError('Eligible/configuration digest mismatch')
        if (r['requested_k'] != 30 or r['branch_depth'] != 30 or r['rrf_k'] != 60
                or r['returned_count'] != len(r['ranking']) or r['ranking'] != [v['job_id'] for v in r['results']]):
            raise ValueError('Saved depth, configuration or result identity mismatch')
        r['development_ids'] = dev
        r['judgments_sha256'] = verified[c_path]
        runs.append(r)
    result = compare_rankings(runs, judgments, readiness=readiness, contract=contract)
    if result['status'] != 'diagnostic_only' or result['primary_publication_blocked_by_unjudged']:
        raise ValueError('Primary original-position comparison remains blocked')
    # No optional filters were applied: do not misrepresent identity-pool recall as filter quality.
    for row in result['metrics']:
        for metric in row['metrics']:
            metric['filter_recall'] = {'value': None, 'status': 'not_measured',
                                       'reason': 'No optional filter implementation/condition in this run'}
    result.update(schema_version='cp23-stage3-retrieval-comparison-v1',
                  run_id='cp23_stage3_retrieval_evaluation_20261003_v2',
                  status='development_retrieval_comparison_complete',
                  aggregate=aggregate(result['metrics']),
                  input_hashes=verified,
                  judgment_inventory={cv: {'judged': len(j), 'relevant_2_3': sum(v >= 2 for v in j.values()),
                                           'grade_counts': dict(Counter(j.values()))} for cv, j in judgments.items()},
                  filter_comparison={'status': 'deferred', 'filter_recall': None},
                  source_limited_cases=readiness['original_top10_union']['source_limited'],
                  interpretation_limits=[
                      'Two familiar development CVs only; no statistical superiority or held-out claim.',
                      'Recall is relative to the declared reviewed eligible pool, not all 214 development jobs.',
                      'Top20/top30 include unjudged positions; these are not automatically irrelevant.',
                      'Only stage-1 retrieval is measured, not final evidence-based recommendation quality.',
                      'Single fixed-order local invocation latency excludes embedding, LLM, connection and preparation.',
                      'Hybrid used branch depth30/RRF60 for this run; active default depth20 is unchanged.',
                      'F00369 C is approved on a truncated source; its A/B remain held.',
                      'Model, embedding, method and K selection require the later configuration decision.'],
                  api_calls=0, cost_usd=0, gold_written=False, workbook_read=False,
                  test_access=False, winner=None, configuration_selected=False)
    return result
