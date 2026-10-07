"""Development evaluation preparation and gated comparison, without inference.

No workbook input, gold promotion, test evaluation, or automatic winner. Current
CLI only prepares a prerequisite report. Metric comparisons need explicit review
and contract receipts supplied by the caller after human authorization.
"""
import csv
import hashlib
import json
from pathlib import Path
import yaml
from jobfit.config import REPO_ROOT, GUIDELINE_FILE, GUIDELINE_VERSION, JD_PROMPT_FILE, EVIDENCE_PROMPT_FILE, runtime_versions
from jobfit.eval.metrics import ranking_metrics, evidence_metrics, extraction_metrics, operational_summary
from jobfit.eval.contract import validate_metric_contract, comparison_gates_ready
from jobfit.search.embeddings import load_specs, validate_vector, cv_body, sha256

CV_FILES={'CV1':'cv_01_fresh_graduate_data_science_id.md', 'CV2':'cv_02_career_switcher_ai_engineer_en.md'}
METHODS={'B0','B1','dense_openai','dense_qwen','hybrid_openai','hybrid_qwen'}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate_comparable(runs):
    """Reject mismatched query sets, filters, source versions, and label coverage."""
    if not runs: raise ValueError('No candidate runs')
    contexts={};seen=set();queries={};kinds=set()
    for run in runs:
        cv=run['cv_id'];method=run['method'];key=(method,cv)
        if run['split']!='development' or cv not in CV_FILES:
            raise ValueError('Development CV1/CV2 only')
        if key in seen: raise ValueError('Duplicate candidate/query')
        seen.add(key);queries.setdefault(method,set()).add(cv)
        if run['execution_kind'] not in {'fake_client','saved_retrieval','live_model'}:
            raise ValueError('Declare execution provenance')
        kinds.add(run['execution_kind'])
        required=('split_sha256','cv_sha256','corpus_sha256','judgments_sha256')
        if any(not run.get(k) for k in required): raise ValueError('Missing input provenance')
        eligible=set(run['eligible_ids']);ranking=run['ranking']
        if len(eligible)!=len(run['eligible_ids']) or len(ranking)!=len(set(ranking)) or not set(ranking)<=eligible:
            raise ValueError('Duplicate or out-of-scope retrieval result')
        context={k:run[k] for k in (*required,'filters')}
        context['eligible_ids']=sorted(eligible)
        if cv in contexts and contexts[cv]!=context:
            raise ValueError('Candidates differ in split, CV, filter, corpus, or judgment coverage')
        contexts[cv]=context
    if len(kinds)!=1: raise ValueError('Fake, saved-retrieval and live results must be reported separately')
    if any(q!=next(iter(queries.values())) for q in queries.values()):
        raise ValueError('Every candidate must cover the same CVs')
    return {'execution_kind':next(iter(kinds)),'queries':sorted(next(iter(queries.values())))}

def compare_rankings(runs, judgments, *, readiness, contract, ks=(10,20,30)):
    context=validate_comparable(runs)
    validate_metric_contract(contract)
    if not comparison_gates_ready(readiness):
        return {'status':'blocked','metrics':None,'reasons':['Contract approval does not establish reference, alignment, coverage, and implementation readiness'], 'winner':None}
    if not ks or any(type(k) is not int or k not in {10,20,30} for k in ks):
        raise ValueError('Only predeclared K=10/20/30 are comparable')
    if set(judgments)!=set(context['queries']):
        raise ValueError('Judgment queries must match comparison CVs')
    for run in runs:
        if not set(judgments[run['cv_id']])<=set(run['development_ids']):
            raise ValueError('Judgment outside frozen development')
        if set(run['eligible_ids'])-set(run['development_ids']):
            raise ValueError('Eligible jobs outside frozen development')
        if len(run['ranking'])<max(ks):
            return {'status':'blocked','metrics':None,'reasons':['Saved ranking depth does not support requested K'], 'winner':None}
    rows=[]
    for run in runs:
        rows.append({'method':run['method'],'cv_id':run['cv_id'],
            'metrics':[ranking_metrics(run['ranking'],judgments[run['cv_id']],eligible_ids=run['eligible_ids'],k=k)
                for k in sorted(set(ks)|{5})],
            'model':run.get('model'),'retrieval_config':run.get('retrieval_config'),
            'cost_usd':run.get('cost_usd'),'latency_ms':run.get('latency_ms'),
            'provenance':{k:v for k,v in run.items() if k.endswith('sha256')}})
    return {'status':'diagnostic_only','execution_kind':context['execution_kind'], 'metrics':rows,
            'winner':None,'scope':'labeled_pool_only','configuration_selected':False,
            'primary_publication_blocked_by_unjudged':any(
                x['k'] in {5,10} and (x['precision_at_k']['value'] is None if x['k']==5 else x['ndcg_at_k'] is None)
                for row in rows for x in row['metrics'])}

def compare_llm_artifacts(runs, *, readiness, contract, registered_models):
    """Compare saved aligned artifacts only. Never invoke a model or infer approval.

    Reference comparisons must supply the same explicit subset for every model;
    the reference model is limited to ten cases. Safety judgments are caller-
    reviewed inputs, never inferred from successful JSON/quote validation.
    """
    validate_metric_contract(contract)
    if not runs:raise ValueError('No LLM artifacts')
    base=None;seen=set()
    for r in runs:
        if r['split']!='development' or not set(r['cv_ids'])<={'CV1','CV2'}:
            raise ValueError('Development-only LLM comparison')
        if r['model'] not in registered_models or r['model'] in seen:raise ValueError('Unknown/duplicate candidate')
        seen.add(r['model'])
        if r.get('role')=='reference' and len(r['case_ids'])>10:raise ValueError('Reference capped at 10 cases')
        if len(r['case_ids'])!=len(set(r['case_ids'])):raise ValueError('Duplicate comparison case')
        identity={k:r[k] for k in ['execution_kind','split','prompt_hashes','input_hashes','gold_sha256','guideline_sha256','requirement_hashes','attempt_kind']}
        if r['attempt_kind'] not in {'first_attempt','automatic_repair'} or r.get('reviewer_assisted') is not False:
            raise ValueError('Reviewer assistance is separate; attempts must use one declared protocol')
        if r.get('guideline_compatibility_verified') is not True:
            raise ValueError('Human-reviewed guideline compatibility required; do not reinterpret historical gold')
        identity['case_ids']=sorted(r['case_ids'])
        identity['cv_ids']=sorted(r['cv_ids'])
        identity['evidence_gold']=r['evidence_gold']
        if r['execution_kind'] not in {'fake_client','live_model'}:raise ValueError('Declare model execution kind')
        if base is not None and identity!=base:raise ValueError('LLM cases, provenance or prompts differ')
        base=identity
    if not comparison_gates_ready(readiness):
        return {'status':'blocked','metrics':None,'winner':None,'reason':'Reference/alignment/coverage/implementation gate pending despite approved contract'}
    rows=[]
    for r in runs:
        if not r.get('alignment_verified') or not r.get('complete_reference'):
            return {'status':'blocked','metrics':None,'winner':None,'reason':'Verified alignment and complete extraction reference required'}
        if not r.get('alignment_receipt_sha256'):
            return {'status':'blocked','metrics':None,'winner':None,'reason':'Missing human alignment receipt'}
        ev=evidence_metrics(r['evidence_gold'],r['evidence_predictions'],alignment_verified=True)
        ex=[extraction_metrics(a,reference_complete=True) for a in r['extraction_alignments']]
        safety=r.get('reviewed_safety')
        gate=None
        if safety and safety.get('review_status')=='approved':
            gate=(safety['unsupported_claims']==0 and safety['quotes_checked']>0 and safety['valid_quotes']==safety['quotes_checked'])
        rows.append({'model':r['model'],'evidence':ev,'extraction_per_case':ex,
                     'operations':operational_summary(r['usage_records']),'safety_gate':gate,
                     'safety_review_pending':gate is None})
    return {'status':'diagnostic_only','execution_kind':base['execution_kind'],'metrics':rows,'winner':None,
            'selection_eligible':all(row['evidence']['class_support_complete'] for row in rows),
            'configuration_selected':False,'provenance':base}

def prepare_development(root=REPO_ROOT):
    root=Path(root)
    dev_path=root/'evals/splits/dev_job_ids.txt';dev=set(dev_path.read_text().splitlines())
    manifest=json.loads((root/'evals/splits/split_manifest.json').read_text())
    if sha(dev_path)!=manifest['output_hashes']['dev_job_ids.txt']:
        raise ValueError('Frozen development split changed')
    paths=['evals/gold/extraction_gold.jsonl','evals/gold/evidence_gold.jsonl','evals/gold/relevance_gold.csv',
           'config/models_v1.yaml','config/retrieval_v1.yaml','config/pipeline_v1.yaml',
           str(GUIDELINE_FILE.relative_to(REPO_ROOT)),'evals/pools/dev_pool.csv','evals/results/t03_dev_pool_20261001.json',
           str(JD_PROMPT_FILE.relative_to(REPO_ROOT)),str(EVIDENCE_PROMPT_FILE.relative_to(REPO_ROOT)),'data/processed/jobs_features.jsonl']
    hashes={p:sha(root/p) for p in paths}
    a=[json.loads(x) for x in (root/paths[0]).read_text().splitlines()]
    b=[json.loads(x) for x in (root/paths[1]).read_text().splitlines()]
    with (root/paths[2]).open() as f:c=list(csv.DictReader(f))
    if any(x['split']!='development' or x['job_id'] not in dev for x in a+b+c):
        raise ValueError('Held-out or unknown gold scope is not allowed')
    if any(x['cv_id'] not in CV_FILES for x in b+c):raise ValueError('Only development CVs')
    # Historical CSV lacks review_status. Trust only the exact previously audited
    # approved pilot export bytes, not arbitrary files in a directory called gold.
    audit=json.loads((root/'evals/results/cp22_pipeline_audit_20261002.json').read_text())
    pilot_digest=next(x['before_sha256'] for x in audit['checks']['protected'] if x['path']==paths[2])
    legacy_trusted=hashes[paths[2]]==pilot_digest
    approved=lambda rows:[x for x in rows if x.get('review_status')=='approved' and x.get('review_action') in {'accepted','edited','added'}]
    aa,bb=approved(a),approved(b)
    cc=[x for x in c if x.get('review_action') in {'accepted','edited','added'} and
        (x.get('review_status')=='approved' or (not x.get('review_status') and legacy_trusted))]
    for rows,fields in [(aa,('job_id','unit_no')),(bb,('cv_id','job_id','unit_no')),(cc,('cv_id','job_id'))]:
        if len({tuple(x[k] for k in fields) for x in rows})!=len(rows):raise ValueError('Duplicate gold identity')
    with (root/'evals/pools/dev_pool.csv').open() as f:pool=list(csv.DictReader(f))
    priority={(x['cv_id'],x['job_id']) for x in pool if x['gold_review']=='yes' or x['already_gold']=='yes'}
    actual={(x['cv_id'],x['job_id']) for x in cc}
    missing=sorted(priority-actual)
    candidates=yaml.safe_load((root/'config/models_v1.yaml').read_text())
    rankings=json.loads((root/'evals/results/t03_dev_pool_20261001.json').read_text())
    cfg=yaml.safe_load((root/'config/retrieval_v1.yaml').read_text())
    if rankings['split_hashes']!=manifest['output_hashes'] or rankings['config']!=cfg:
        raise ValueError('Saved retrieval provenance differs from current configuration/split')
    if set(rankings['cvs'])!=set(CV_FILES):raise ValueError('Unexpected retrieval CV set')
    rows=[]
    for cv,filename in CV_FILES.items():
        cv_hash=sha(root/'data/synthetic_cvs'/filename)
        if cv_hash!=rankings['cv_hashes'][cv]:raise ValueError('Saved ranking CV changed')
        if set(rankings['cvs'][cv]['rankings'])!=METHODS:raise ValueError('Missing retrieval method')
        for method,rank in rankings['cvs'][cv]['rankings'].items():
            rows.append({'method':method,'cv_id':cv,'split':'development','execution_kind':'saved_retrieval',
                'ranking':[x['job_id'] for x in rank],'eligible_ids':sorted(dev),'development_ids':sorted(dev),
                'filters':{'mode':'automatic','optional_filters':None},'split_sha256':sha(dev_path),'cv_sha256':cv_hash,
                'corpus_sha256':hashes['data/processed/jobs_features.jsonl'],'judgments_sha256':hashes[paths[2]],
                'retrieval_config':cfg,'cost_usd':0,'latency_ms':None,'latency_status':'not_recorded_in_saved_pool',
                'model':next((v['id'] for k,v in candidates['embeddings'].items() if ('openai' in method and k=='text-embedding-3-small') or ('qwen' in method and k=='qwen3-embedding-8b')),None),
                'preprocessing':cfg['preprocessing_version'],'source_run_sha256':hashes['evals/results/t03_dev_pool_20261001.json'],
                'corpus_hash_status':'current_hash_recorded; original_pool_has_no_corpus_hash; fresh retrieval needed before comparison'})
    validate_comparable(rows)
    caches=[];specs={s.profile_id:s for s in load_specs()}
    cv_sources={sha256(cv_body(root/'data/synthetic_cvs'/filename).replace('\r\n','\n').replace('\r','\n').strip()):cv for cv,filename in CV_FILES.items()}
    cache_keys=set()
    for p in sorted((root/'reports/embedding_queries').glob('*.json')):
        entry=json.loads(p.read_text());spec=specs.get(entry['profile_id'])
        if not spec:raise ValueError('Unexpected embedding profile')
        cv_id=cv_sources.get(entry['source_hash'])
        if cv_id is None:raise ValueError('Cached query does not match a current allowed CV')
        key=(cv_id,spec.profile_id)
        if key in cache_keys:raise ValueError('Ambiguous cached query for current CV/profile')
        cache_keys.add(key)
        validate_vector(entry['vector'],spec.dimensions)
        caches.append({'cv_id':cv_id,'file':str(p.relative_to(root)),'sha256':sha(p),'profile_id':spec.profile_id,
                       'model':spec.model,'dimensions':spec.dimensions,'source_hash':entry['source_hash'],'input_hash':entry['input_hash'],
                       'check_scope':'Current CV body hash, profile and vector shape; exact prepared input checked by query-cache loader before retrieval'})
    blockers=[]
    if cache_keys!={(cv,profile) for cv in CV_FILES for profile in specs}:blockers.append('Missing existing CV/model query cache')
    if len({x['job_id'] for x in aa})<7:blockers.append('Priority extraction gold: fewer than 7 JDs')
    if len({(x['cv_id'],x['job_id']) for x in bb})<4:blockers.append('Priority evidence gold: fewer than 4 pairs')
    if missing or len(cc)<50:blockers.append('Priority relevance gold incomplete')
    blockers += ['Explicit whole-JD completeness receipts required; row approval is insufficient',
                 'D-049 guideline compatibility/migration review required for affected historical gold; no automatic version bump',
                 'Human fixture acceptance and semantic alignment remain pending',
                 'Metric convention receipt required before publication',
                 'Saved rankings have depth 20, cannot support K30',
                 'Filtered-condition eligible IDs/configuration must be fixed before comparison',
                 'Original pool lacks corpus-content hash and latency; refresh retrieval from existing vectors before formal comparison']
    return {'status':'blocked','purpose':'offline_preparation_not_tuning','split':'development','metrics':None,'winner':None,
        'blockers':blockers,'gold_inventory':{'A_approved_rows':len(aa),'A_jobs':len({x['job_id'] for x in aa}),
            'B_approved_rows':len(bb),'B_pairs':len({(x['cv_id'],x['job_id']) for x in bb}),'C_approved_rows':len(cc),
            'C_legacy_approval_provenance':'exact previously audited pilot export hash' if legacy_trusted else None,
            'priority_C_missing':missing,'A_complete_JDs_inferred_from_row_count':False},
        'input_hashes':hashes,'versions':runtime_versions(),'historical_gold_guidelines':sorted({x.get('guideline_version','unknown') for x in a+b+c}),
        'retrieval_inputs':rows,'existing_query_caches':caches,
        'llm_plan':{'round1':{k:v for k,v in candidates['models'].items() if v['role'] in {'round1_baseline','round1'}},
            'reference':{k:v for k,v in candidates['models'].items() if v['role']=='reference'},'reference_case_cap':10,
            'same_cases_same_prompt_required':True,'api_calls':0,'prices_availability_require_preflight_before_live':True,
            'alignment_policy':'No automatic unit-ID/quote mapping; D-054 strict split/merge counting only after semantic verification'},
        'metric_contract':{'review_status':'pending','ndcg_gain':None,'short_precision':None,'absent_class_policy':None,
                           'failed_prediction_policy':'proposed: explicit not_assessed, coverage and all-reference false negatives; pending'},
        'api_calls':0,'new_embedding_calls':0,'workbook_read':False,'gold_written':False,
        'documentation_conflicts':['CP2.3 historical about-30-case plan is superseded by D-045 sizes',
                                   'Gold README historical rebuild command is blocked after frozen split; do not run it'],
        'git_sha':'commit by user after review; no git command'}
