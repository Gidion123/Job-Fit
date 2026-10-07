"""Inspect an explicit reviewed bundle and saved retrieval without computing metrics."""
import csv,json,hashlib,re
from pathlib import Path
from jobfit.eval.development_gold import validate_saved,sha
from jobfit.eval.run_eval import CV_FILES,METHODS


def check_source_hashes(root, source_hashes):
    """Only the export-time gold README is documentary; synthetic CV Markdown is data."""
    for name,expected in source_hashes.items():
        if name == 'evals/gold/README.md':
            continue
        if sha(Path(root)/name) != expected:
            raise ValueError('Bundle source changed: '+name)


def inspect_acceptance_probe(root, path):
    """An explicit source-checked experiment receipt is not a baseline promotion."""
    root, path = Path(root), Path(path)
    data = json.loads(path.read_text())
    if data.get('status') != 'complete' or data.get('reservations') or data.get('transport_uncertain'):
        raise ValueError('Acceptance probe is incomplete or has uncertain requests')
    results = data.get('results', [])
    if not results or [r['job_id'] for r in results] != data['jobs']:
        raise ValueError('Acceptance stages incomplete')
    dev = set((root/'evals/splits/dev_job_ids.txt').read_text().splitlines())
    for stage in data['jobs']:
        if not set(re.findall(r'F\d{5}', stage)) <= dev or any(cv not in CV_FILES for cv in re.findall(r'CV\d+', stage)):
            raise ValueError('Acceptance must use development only')
    for result in results:
        check = result.get('operational_check', {})
        raw = {k:v for k,v in result.items() if k not in {'result_sha256','operational_check'}}
        digest = hashlib.sha256(json.dumps(raw,sort_keys=True).encode()).hexdigest()
        if result['status'] != 'done' or result['result_sha256'] != digest or check.get('result_sha256') != digest:
            raise ValueError('Acceptance result identity mismatch')
        expected = {'quotes','coverage','grouping','qualifiers','importance'}
        if set(check.get('checks', {})) != expected or any(x != 'pass' for x in check['checks'].values()):
            raise ValueError('Acceptance semantic check is not passed')
        if check.get('human_annotation_approval') is not False:
            raise ValueError('Operational check must not imply human gold approval')
        for name, h in result['provenance'].items():
            if (root/name).is_file() and sha(root/name) != h:
                raise ValueError('Acceptance source/configuration has changed')
    last = results[-1]
    return {'run_id': data['run_id'], 'receipt_sha256': sha(path), 'status': 'operationally_checked',
            'stages': len(results), 'versions': last['versions'],
            'score': last['report']['score'], 'baseline_promoted': False,
            'human_alignment_status': 'pending', 'quality_metric': None}


def prepare_reviewed_bundle(root,bundle,retrieval,acceptance_probe=None):
    root=Path(root);bundle=Path(bundle);retrieval=Path(retrieval)
    manifest=validate_saved(bundle)
    if manifest['status']!='promoted_record_gold':raise ValueError('Bundle is not promoted')
    check_source_hashes(root,manifest['source_hashes'])
    devfile=root/'evals/splits/dev_job_ids.txt';dev=set(devfile.read_text().splitlines())
    split=json.loads((root/'evals/splits/split_manifest.json').read_text())
    if sha(devfile)!=split['output_hashes']['dev_job_ids.txt']:raise ValueError('Frozen development split changed')
    rows={k:[json.loads(l) for l in (bundle/n).read_text().splitlines()] for k,n in
          [('A','extraction_gold.jsonl'),('B','evidence_gold.jsonl'),('C','relevance_gold.jsonl')]}
    if any(r['job_id'] not in dev for group in rows.values() for r in group):raise ValueError('Gold outside development')
    if any(r['cv_id'] not in CV_FILES for k in ['B','C'] for r in rows[k]):raise ValueError('Only CV1/CV2')
    saved=json.loads(retrieval.read_text());seen=set();scope=None
    if saved['status']!='success':raise ValueError('Unsuccessful retrieval')
    corpus_hash=sha(root/'data/processed/jobs_features.jsonl')
    coverage=[]
    for run in saved['runs']:
        key=(run['cv_id'],run['method'])
        if key in seen:raise ValueError('Duplicate retrieval context')
        seen.add(key)
        if run['split']!='development' or run['status']!='success' or set(run['eligible_ids'])!=dev:raise ValueError('Retrieval scope mismatch')
        if run['split_sha256']!=sha(devfile) or run['corpus_sha256']!=corpus_hash:raise ValueError('Stale retrieval input')
        if run['cv_sha256']!=sha(root/'data/synthetic_cvs'/CV_FILES[run['cv_id']]):raise ValueError('Stale CV')
        if len(run['ranking'])!=len(set(run['ranking'])) or not set(run['ranking'])<=dev:raise ValueError('Invalid ranking')
        if len(run['ranking'])<min(30,len(dev)):raise ValueError('Top30 unavailable')
        current=json.dumps(run['filters'],sort_keys=True)
        if scope is not None and scope!=current:raise ValueError('Unequal filters')
        scope=current
        judged={r['job_id'] for r in rows['C'] if r['cv_id']==run['cv_id']}
        coverage.append({'cv_id':key[0],'method':key[1],'judged_top30':len(set(run['ranking'])&judged),
                         'unjudged_top30':sorted(set(run['ranking'])-judged)})
    if seen!={(cv,m) for cv in CV_FILES for m in METHODS}:raise ValueError('Missing retrieval methods/CVs')
    with (root/'evals/pools/dev_pool.csv').open() as f:pool=list(csv.DictReader(f))
    priority={(r['cv_id'],r['job_id']) for r in pool if r['gold_review']=='yes' or r['already_gold']=='yes'}
    missing=sorted(priority-{(r['cv_id'],r['job_id']) for r in rows['C']})
    acceptance = inspect_acceptance_probe(root, acceptance_probe) if acceptance_probe else None
    return {'status':'blocked','purpose':'reviewed_bundle_readiness_not_tuning','api_calls':0,'metrics':None,'winner':None,
        'scoped_live_acceptance':acceptance,
        'gold_bundle':str(bundle.relative_to(root)),'gold_manifest_sha256':sha(bundle/'manifest.json'),
        'gold_inventory':{k:len(v) for k,v in rows.items()},'priority_relevance_missing_or_held':missing,
        'retrieval_artifact':str(retrieval.relative_to(root)),'retrieval_sha256':sha(retrieval),'verified_top30_runs':len(seen),
        'judgment_coverage':coverage,'coverage_is_not_a_quality_metric':True,
        'carryover_notes':['Default experimental-prompt promotion is not a winner selection; broad extraction follows configuration evaluation under D-050'],
        'blockers':['Metric convention receipt is still pending',
                    'Complete reference and semantic model alignment are not certified by record-level approval',
                    'Held records and unjudged retrieval candidates must not silently become relevance zero'] +
                   ([] if acceptance else ['No current acceptance receipt supplied; historical fixed-baseline probe failed F00034 completeness']),
        'next_stage':'CP2.3 preparation may proceed; formal comparison and configuration selection are not authorized by this report',
        'limitations':['Only CV1/CV2 development; no test access','Optional filters remain deferred',
                       'Gold source versions and held records remain explicit; no blanket version migration']}
