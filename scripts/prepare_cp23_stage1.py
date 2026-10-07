"""Read-only CP2.3 Stage-1 source/gold and saved-ranking inventory.

Writes new manifests exclusively. No workbook loader, DB connection or model client.
Selected IDs are preregistered for source variation; this is not a quality run.
"""
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from jobfit.eval.contract import validate_metric_contract

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT/'evals/gold/development_v13_reviewed_20261003_stage1_r3'
RANKING = ROOT/'evals/results/cp22_retrieval_top30_20261002_03.json'
RECEIPT = ROOT/'evals/results/cp23_metric_contract_D052_D054_20261003_v1.json'
CV_FILES = {'CV1':'cv_01_fresh_graduate_data_science_id.md',
            'CV2':'cv_02_career_switcher_ai_engineer_en.md'}
CASE_IDS = ('F00332','F00036','F00309','F00354','F00815','F00010','F00018')
PAIRS = (('CV1','F00332'),('CV1','F00036'),('CV2','F00815'),('CV2','F00018'))
VARIATION = {
 'F00332':'English entry-level DS; eight qualification bullets, explicit AND and preferred credit-scoring exposure; known assisted model alignment questions.',
 'F00036':'Indonesian 2-3-year DS; tool alternatives, ML components and preferred big-data clause.',
 'F00309':'English short DS; entire qualifications section preferred, including 1-3-year qualifier; zero-required-score case.',
 'F00354':'English entry ML/AI internship; ten qualification bullets, AND/OR, broad technology interest as soft-skill scope.',
 'F00815':'English AI engineer; nine requirement bullets, named framework/cloud alternatives and API experience.',
 'F00010':'English senior computer-vision title, 8-year qualified AI/ML/DS duration; cloud deployment and Indonesian citizenship.',
 'F00018':'Mixed Indonesian wrapper/English senior ML source; fifteen required/plus bullets and nested cloud/AWS preference approved in review.'}
BULLETS={'F00332':8,'F00036':10,'F00309':3,'F00354':10,'F00815':9,'F00010':7,'F00018':15}
NOTES={
 'F00332':['Source AND Python/SQL/Excel is three units, not an OR. Dion approved two B corrections to PARTIAL and rechecked C=3; historical assisted output remains separate.'],
 'F00036':['2-3 years stays scoped to professional Data Scientist or similar work; projects alone do not satisfy duration.'],
 'F00309':['Preferred heading governs all three clauses; an empty required score denominator is legitimate.'],
 'F00354':['Duplicate company description is not a requirement; qualification interest in LLM/RAG/etc is not proven technical competence.'],
 'F00815':['API build/deploy and technical framework alternatives stay distinct; category/qualifier requires reviewer confirmation before formal alignment.'],
 'F00010':['English communication and remote cross-functional communication retain different qualifiers; 8 years is role-scoped.'],
 'F00018':['General cloud and AWS stack are both preferred under Will be a plus (approved correction). Bedrock is a separately named preference; check no unsupported double counting in formal comparison.']}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rows(name):return [json.loads(line) for line in (BUNDLE/name).read_text().splitlines()]
def row_hash(row):return hashlib.sha256(json.dumps(row,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def selected_sources(wanted):
    found={}
    dev=set((ROOT/'evals/splits/dev_job_ids.txt').read_text().splitlines())
    test=set((ROOT/'evals/splits/test_job_ids.txt').read_text().splitlines())
    if dev&test or not set(wanted)<=dev or set(wanted)&test:
        raise ValueError('Candidate must be frozen development only and split-disjoint')
    for line in (ROOT/'data/processed/jobs_features.jsonl').open():
        match=re.search(r'"final_cluster_id"\s*:\s*"([^"]+)"',line)
        if match and match.group(1) in wanted:
            row=json.loads(line)
            if row['final_cluster_id'] in found:raise ValueError('Duplicate source JD')
            found[row['final_cluster_id']]=row
    if set(found)!=set(wanted):raise ValueError('Missing source JD')
    return found


def main():
    validate_metric_contract(json.loads(RECEIPT.read_text()), ROOT)
    m=json.loads((BUNDLE/'manifest.json').read_text())
    for name,digest in m['files'].items():
        if sha(BUNDLE/name)!=digest:raise ValueError('Reviewed bundle file changed: '+name)
    for name in ('data/processed/jobs_features.jsonl','evals/splits/split_manifest.json',
                 'evals/pools/dev_pool.csv'):
        if sha(ROOT/name)!=m['source_hashes'][name]:raise ValueError('Protected source changed: '+name)
    aa=rows('extraction_gold.jsonl');bb=rows('evidence_gold.jsonl');cc=rows('relevance_gold.jsonl')
    held=json.loads((BUNDLE/'held_records.json').read_text())
    logical=json.loads((BUNDLE/'logical_units.json').read_text())
    source=selected_sources(set(CASE_IDS)|{'F00034'})
    cvs={cv:(ROOT/'data/synthetic_cvs'/filename).read_text() for cv,filename in CV_FILES.items()}
    cases=[]
    for job in CASE_IDS:
        jd=source[job]['description_clean'];arows=[x for x in aa if x['job_id']==job]
        if not arows:raise ValueError('No A gold for '+job)
        if any(x['review_status']!='approved' or x['review_action']=='rejected' or
               x['source_quote'] not in jd or x['jd_source_sha256']!=hashlib.sha256(jd.encode()).hexdigest()
               for x in arows):raise ValueError('Invalid A source/approval: '+job)
        hs=[x for x in held if x['record'].get('job_id')==job and x['sheet']=='A_Extraction']
        if hs:raise ValueError('Candidate has held A rows: '+job)
        units=[x for x in logical if x['job_id']==job and x['status']=='ready']
        unit_ids={x['unit_no'] for x in arows}
        if {rid for x in units for rid in x['row_ids']}!=unit_ids:raise ValueError('Logical-unit coverage mismatch: '+job)
        cases.append({'job_id':job,'title':source[job]['title'],'role_family':source[job]['role_family'],
            'experience_bucket':source[job]['experience_bucket'],'source_language':'mixed_id_en' if job=='F00018' else
            'id' if job=='F00036' else 'en','source_characters':len(jd),
            'source_sha256':hashlib.sha256(jd.encode()).hexdigest(),
            'gold_A_file_sha256':m['files']['extraction_gold.jsonl'],
            'gold_A_rows':len(arows),'logical_unit_count':len(units),
            'logical_unit_ids':[x['logical_unit_id'] for x in units],
            'A_identities':[{'unit_no':x['unit_no'],'logical_unit_id':x['logical_unit_id'],
                'row_sha256':row_hash(x),'guideline_version':x['guideline_version'],
                'category':x['category'],'importance':x['importance'],'group_id':x.get('group_id'),
                'min_years':x.get('min_years'),'source_quote_exact':True} for x in arows],
            'qualification_bullets_delegated_source_review':BULLETS[job],
            'exact_quote_valid_count':len(arows),'held_A_count':0,
            'complete_reference_status':'delegated_source_QA_candidate_not_independent_human_certification',
            'source_review_notes':NOTES[job], 'variation_reason':VARIATION[job],
            'formal_model_alignment_approved':False})
    pairs=[]
    for cv,job in PAIRS:
        a={x['unit_no']:x for x in aa if x['job_id']==job}
        b=[x for x in bb if (x['cv_id'],x['job_id'])==(cv,job)]
        if {x['unit_no'] for x in b}!=set(a) or len(b)!=len(a):raise ValueError('Incomplete B pair: '+cv+'/'+job)
        if any(x['review_status']!='approved' or x['review_action']=='rejected' or
               x['check_status']!='done' or (x.get('cv_quote') and x['cv_quote'] not in cvs[cv]) or
               (x['label'] in ('MATCH','PARTIAL') and not x.get('cv_quote')) or
               x['jd_source_sha256']!=a[x['unit_no']]['jd_source_sha256'] for x in b):
            raise ValueError('B quote/status/source invalid: '+cv+'/'+job)
        if any(x['sheet']=='B_Evidence' and (x['record']['cv_id'],x['record']['job_id'])==(cv,job) for x in held):
            raise ValueError('Held B pair: '+cv+'/'+job)
        counts={label:sum(x['label']==label for x in b) for label in ('MATCH','PARTIAL','NO_MATCH')}
        pairs.append({'cv_id':cv,'job_id':job,'CV_sha256':sha(ROOT/'data/synthetic_cvs'/CV_FILES[cv]),
            'gold_B_file_sha256':m['files']['evidence_gold.jsonl'],
            'B_rows':len(b),'A_to_B_identity_complete':True,'positive_CV_quotes_exact':True,
            'all_check_status_done':True,'class_support':counts,
            'B_identities':[{'unit_no':x['unit_no'],'row_sha256':row_hash(x),
                             'guideline_version':x['guideline_version'],'label':x['label']} for x in b],
            'fixed_requirement_input':'reviewed A logical units for '+job,
            'formal_model_to_gold_alignment_approved':False,
            'special_note':'F00332 assisted 16-unit mapping and two PARTIAL B edits are approved in D-054; future candidate outputs still need separate alignment.' if job=='F00332' else None})
    regression_held=[x for x in held if x['record'].get('job_id')=='F00034']
    candidate={'schema_version':'cp23-stage1-case-candidates-v4','status':'reviewed_reference_subset_ready_future_model_mappings_separate',
        'selection_basis':'Source variation selected before any CP2.3 candidate-quality comparison',
        'api_calls':0,'gold_bundle':str(BUNDLE.relative_to(ROOT)),'gold_manifest_sha256':sha(BUNDLE/'manifest.json'),
        'metric_contract_receipt_sha256':sha(RECEIPT),'source_corpus_sha256':sha(ROOT/'data/processed/jobs_features.jsonl'),
        'development_split_sha256':sha(ROOT/'evals/splits/dev_job_ids.txt'),
        'case_count':len(cases),'pair_count':len(pairs),'cases':cases,'pairs':pairs,
        'known_regression_separate':{'job_id':'F00034','source_sha256':hashlib.sha256(source['F00034']['description_clean'].encode()).hexdigest(),
            'previously_exposed_to_experimental_prompt':True,'A_held_count':sum(x['sheet']=='A_Extraction' for x in regression_held),
            'held_reasons':sorted({reason for x in regression_held for reason in x['reasons']}),
            'status':'hold_from_seven_until_historical_v0_1_structure_compatible',
            'use':'regression_diagnostic_only_not_unseen_quality'},
        'review_scope':'delegated source/technical QA; Dion verified only the saved assisted F00332 mapping, not future candidate outputs',
        'existing_assisted_F00332_alignment_receipt_sha256':sha(ROOT/'evals/results/cp23_F00332_alignment_approval_20261003_v1.json'),
        'exclusions_considered':[{'job_id':'F00066','reason':'PKWT willingness qualification is absent from exported A; do not call it whole-JD complete'},
                                 {'job_id':'F00208','reason':'US residence appears in two scored location units; overlap needs reconciliation before inclusion'}],
        'formal_metrics':None,'winner':None}
    ranking=json.loads(RANKING.read_text())
    dev=set((ROOT/'evals/splits/dev_job_ids.txt').read_text().splitlines())
    methods={'B0','B1','dense_openai','dense_qwen','hybrid_openai','hybrid_qwen'}
    if len(ranking['runs'])!=12 or {(x['cv_id'],x['method']) for x in ranking['runs']}!={(cv,method) for cv in CV_FILES for method in methods}:
        raise ValueError('Expected twelve saved methods/CVs')
    seen={};coverage=[]
    judged={(x['cv_id'],x['job_id']):x for x in cc}
    hold_c={(x['record']['cv_id'],x['record']['job_id']):x for x in held if x['sheet']=='C_Relevance'}
    split_sha=sha(ROOT/'evals/splits/dev_job_ids.txt')
    corpus_sha=sha(ROOT/'data/processed/jobs_features.jsonl')
    shared_filters=None
    for run in ranking['runs']:
        if run['status']!='success' or run['split']!='development' or set(run['eligible_ids'])!=dev or len(run['ranking'])<30:
            raise ValueError('Noncomparable saved retrieval')
        cv=run['cv_id'];method=run['method'];ids=run['ranking']
        if (run['split_sha256']!=split_sha or run['corpus_sha256']!=corpus_sha or
            run['cv_sha256']!=sha(ROOT/'data/synthetic_cvs'/CV_FILES[cv]) or
            run['eligible_count']!=len(dev) or run['requested_k']!=30 or
            run['filter_status']!='no_optional_filters'):
            raise ValueError('Stale or altered retrieval provenance')
        filters=json.dumps(run['filters'],sort_keys=True)
        if shared_filters is not None and filters!=shared_filters:
            raise ValueError('Saved retrieval filters differ across methods')
        shared_filters=filters
        if len(ids)!=len(set(ids)) or not set(ids)<=dev:raise ValueError('Duplicate/out-of-scope ranking')
        for rank,job in enumerate(ids[:10],1):seen.setdefault((cv,job),[]).append({'method':method,'rank':rank})
        coverage.append({'cv_id':cv,'method':method,'cutoffs':{
            str(k):{'judged':sum((cv,j) in judged for j in ids[:k]),
                    'held':sum((cv,j) in hold_c for j in ids[:k]),
                    'unjudged':sum((cv,j) not in judged and (cv,j) not in hold_c for j in ids[:k])}
            for k in (5,10,20,30)}})
    with (ROOT/'evals/gold/relevance_gold.csv').open() as f:pilot={(x['cv_id'],x['job_id']):x for x in csv.DictReader(f)}
    gaps=[]
    for (cv,job),methods_ranks in sorted(seen.items()):
        if (cv,job) in judged:continue
        hold=hold_c.get((cv,job));old=pilot.get((cv,job))
        gaps.append({'cv_id':cv,'job_id':job,'status':'held' if hold else 'unjudged',
            'reasons':hold['reasons'] if hold else ['no_eligible_current_C_judgment'],
            'approved_compatible_judgment_elsewhere':False,
            'elsewhere_check':'No separately verified compatible judgment; historical pilot row, if present, needs source and D-049 receipt',
            'contributing_methods_ranks':sorted(methods_ranks,key=lambda x:(x['method'],x['rank'])),
            'historical_pilot':{'exists':bool(old),'guideline_version':old.get('guideline_version') if old else None,
                'review_action':old.get('review_action') if old else None,
                'record_sha256':row_hash(old) if old else None,
                'reuse':'requires_source_and_D049_compatibility_receipt_not_auto_promoted' if old else None},
            'review_path':'source_provenance_blocker' if job=='F00369' else
                'resolve_existing_hold' if hold else 'optional_new_relevance_review'})
    coverage_summary={'schema_version':'cp23-stage1-top10-gap-v4','status':'judgment_coverage_ready_not_quality_comparison',
        'retrieval_artifact':str(RANKING.relative_to(ROOT)),'retrieval_sha256':sha(RANKING),
        'common_filters':ranking['runs'][0]['filters'],'development_split_sha256':split_sha,
        'source_corpus_sha256':corpus_sha,
        'gold_manifest_sha256':sha(BUNDLE/'manifest.json'),'union_top10_cv_job_pairs':len(seen),
        'judged_union':sum(key in judged for key in seen),'held_union':sum(key in hold_c for key in seen),
        'unjudged_union':sum(key not in judged and key not in hold_c for key in seen),
        'cutoff_coverage':coverage,'gaps':gaps,
        'new_review_items':sum(x['status']=='unjudged' for x in gaps),
        'existing_held_rechecks':sum(x['status']=='held' and x['job_id']!='F00369' for x in gaps),
        'source_provenance_blockers':sum(x['job_id']=='F00369' for x in gaps),
        'historical_pilot_reuse_autoapproved':False,
        'source_limited_judgments':[{'cv_id':'CV1','job_id':'F00369','source':'archived_truncated_original',
            'C_reviewed_directly':True,'A_B_still_held':True}],
        'time_estimate_minutes_new_only':sum(x['status']=='unjudged' for x in gaps)*2.4,
        'time_basis':'D-045 measured pilot relevance review 2.4 min per label; excludes held-case/source resolution and QA',
        'quality_metrics':None,'winner':None,'api_calls':0}
    out_cases=ROOT/'evals/results/cp23_stage1_case_candidates_20261003_v4.json'
    out_gaps=ROOT/'evals/results/cp23_stage1_top10_gaps_20261003_v4.json'
    out_csv=ROOT/'evals/results/cp23_stage1_top10_gaps_20261003_v4.csv'
    for path,object_ in ((out_cases,candidate),(out_gaps,coverage_summary)):
        with path.open('x') as f:json.dump(object_,f,indent=2,ensure_ascii=False)
    with out_csv.open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['cv_id','job_id','status','methods_ranks','reasons','historical_pilot_version','review_path'])
        writer.writeheader()
        for x in gaps:writer.writerow({'cv_id':x['cv_id'],'job_id':x['job_id'],'status':x['status'],
            'methods_ranks':'; '.join(y['method']+':'+str(y['rank']) for y in x['contributing_methods_ranks']),
            'reasons':'; '.join(x['reasons']),'historical_pilot_version':x['historical_pilot']['guideline_version'],
            'review_path':x['review_path']})
    print(json.dumps({'cases':len(cases),'pairs':len(pairs),'union':len(seen),'judged':coverage_summary['judged_union'],
        'held':coverage_summary['held_union'],'new':coverage_summary['unjudged_union'],'outputs':[str(p.relative_to(ROOT)) for p in (out_cases,out_gaps,out_csv)]}))


if __name__=='__main__':main()
