"""Authorized, versioned development export. Original decisions never rewritten.

Row gold and logical mapping are separate. No metric or blanket completeness claim.
Human approval provenance comes from stored review receipts, not export timestamps.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict,Counter
from copy import deepcopy
import hashlib,io,json,os,re
import openpyxl
from jobfit.eval.review_export import identity,dependency_token,digest,SHEETS

ACTIVE_HOLDS={
 ('F00103','D1-U27'):'Enterprise REST API integration is a practice; skill_tool category needs D-049 compatibility review',
 ('F00074','D2-U20'):'CI/CD is a practice, not a named tool; D-049 category compatibility review needed',
 ('F00012','D3-U12'):'MLOps CI/CD is a practice, not a named tool; D-049 category compatibility review needed',
 ('F00022','J1-U04'):'D-049 and/or composite conflicts with historical independent AND split',
 ('F00022','J1-U20'):'D-049 and/or composite conflicts with historical independent AND split',
 ('F00022','J1-U21'):'D-049 and/or composite conflicts with historical independent AND split',
 ('F00022','J1-U05'):'Historical and/or dataset group needs explicit cardinality compatibility',
 ('F00022','J1-U06'):'Historical knowledge and/or experience qualifier needs explicit compatibility',
 ('F00022','J1-U07'):'Historical knowledge and/or experience qualifier needs explicit compatibility',
 ('F00022','J1-U08'):'Historical knowledge and/or experience qualifier needs explicit compatibility',
 ('F00034','J3-U11'):'REST API practice classified skill_tool in historical gold; D-049 category review needed',
 ('F00016','J4-U06'):'Generic LLM experience is not a named technology under D-049',
 ('F00016','J4-U12'):'REST API practice historical tool category needs D-049 review',
 ('F00016','J4-U20'):'CI/CD practice historical tool category needs D-049 review',
 ('F00114','J5-U03'):'Reviewer explicitly retains unresolved and/or composite and requires B/C hold',
}
MULTI_OR={('F00103','D1-G2'),('F00029','P07-G1'),('F00029','P07-G11')}
CATEGORIES={'skill_tool','knowledge_area','experience_duration','education','language','certification','soft_skill','location','work_authorization','other'}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read_workbook(path):
    raw=Path(path).read_bytes();before=hashlib.sha256(raw).hexdigest()
    book=openpyxl.load_workbook(io.BytesIO(raw),read_only=True,data_only=True)
    out={}
    try:
        for name in ('JDs','CVs',*SHEETS):
            rows=iter(book[name].values);columns=next(rows)
            out[name]=[dict(zip(columns,r)) for r in rows if any(v is not None for v in r)]
    finally:book.close()
    if sha(path)!=before:raise ValueError('Workbook changed during read; retry a new snapshot, never overwrite')
    return out,before


def plan(snapshot,*,development_ids,canonical_jds,canonical_cvs,approval_receipt):
    s=deepcopy(snapshot);candidates={n:[] for n in SHEETS};held=[];excluded=[];logical=[];coverage=[]
    jobs={r['job_id']:r['jd_text'] for r in s['JDs']};cvs={r['cv_id']:r['cv_text'] for r in s['CVs']}
    if len(jobs)!=len(s['JDs']) or len(cvs)!=len(s['CVs']):raise ValueError('Duplicate source identities')
    if not set(jobs)<=development_ids or not set(cvs)<={'CV1','CV2'}:raise ValueError('Development scope only')
    if cvs!=canonical_cvs:raise ValueError('CV sources differ')
    if not approval_receipt.get('user_confirmed_BC_after_final_A') or not approval_receipt.get('source_sha256'):
        raise ValueError('Explicit user dependency-review receipt required')
    maps={}
    for sheet in SHEETS:
        maps[sheet]={identity(sheet,r):r for r in s[sheet]}
        if len(maps[sheet])!=len(s[sheet]):raise ValueError('Duplicate decision identity')
    groups=defaultdict(list)
    for r in s['A_Extraction']:
        if r.get('review_action')!='rejected':groups[(r['job_id'],r.get('group_id') or r['unit_no'])].append(r)
    unsafe=set()
    for (job,gid),rs in groups.items():
        if len(rs)>1 and ((job,gid) not in MULTI_OR or len({x['importance'] for x in rs})!=1 or len({x['source_quote'] for x in rs})!=1):
            unsafe.update((job,x['unit_no']) for x in rs)
    candidate_a={};candidate_b={}
    for sheet in SHEETS:
        for r in s[sheet]:
            key=identity(sheet,r);job=r['job_id'];reasons=[]
            if r.get('review_action')=='rejected':
                excluded.append({'sheet':sheet,'identity':key,'reason':'rejected','review_note':r.get('review_note')})
                if not r.get('review_note'):held.append({'sheet':sheet,'identity':key,'reasons':['Rejected decision lacks explanatory note; retained audit only']})
                continue
            if r.get('review_status')!='approved':reasons.append('not_approved')
            if r.get('review_action') not in {'accepted','edited','added'}:reasons.append('invalid_review_action')
            if r.get('review_action') in {'edited','added'} and not r.get('review_note'):reasons.append('changed_decision_missing_note')
            if not r.get('guideline_version') or r.get('label_source') not in {'model_draft','annotator'}:reasons.append('missing_provenance')
            if job not in jobs or job not in development_ids:reasons.append('unknown_or_non_development_job')
            if jobs.get(job)!=canonical_jds.get(job) or job=='F00369':reasons.append('source_provenance_hold_whole_job')
            if sheet=='A_Extraction':
                if (job,r['unit_no']) in ACTIVE_HOLDS:reasons.append(ACTIVE_HOLDS[(job,r['unit_no'])])
                if (job,r['unit_no']) in unsafe:reasons.append('unsafe_multirow_group_mapping')
                if not r.get('source_quote') or r['source_quote'] not in canonical_jds.get(job,''):reasons.append('invalid_original_JD_quote')
                if r.get('importance') not in {'required','preferred','unknown'} or r.get('category') not in CATEGORIES:reasons.append('invalid_requirement_fields')
                if not r.get('unit_text'):reasons.append('empty_unit')
                if r.get('min_years') is not None:
                    import math
                    if isinstance(r['min_years'],bool) or not isinstance(r['min_years'],(int,float)) or not math.isfinite(r['min_years']) or r['min_years']<0:reasons.append('invalid_duration')
                # Identical retained text with different identities must be reviewed, not counted twice.
                if sum(x['review_action']!='rejected' and x['job_id']==job and x['unit_text'].strip().casefold()==r['unit_text'].strip().casefold() for x in s[sheet])>1:reasons.append('duplicate_retained_requirement')
            elif sheet=='B_Evidence':
                a=candidate_a.get(job+'/'+r['unit_no'])
                if not a:reasons.append('A_not_exportable')
                elif a['unit_text']!=r.get('unit_text'):reasons.append('stale_B_unit_text')
                if r.get('cv_id') not in cvs:reasons.append('unknown_CV')
                if r.get('label') not in {'MATCH','PARTIAL','NO_MATCH'} or r.get('check_status') not in {'done','needs_clarification'}:reasons.append('invalid_evidence_or_process_failure')
                if r.get('label')=='NO_MATCH':
                    if r.get('cv_quote'):reasons.append('negative_label_has_quote')
                elif not r.get('cv_quote') or r['cv_quote'] not in cvs.get(r.get('cv_id'),''):reasons.append('invalid_CV_quote')
                if r.get('label')!='NO_MATCH' and r.get('cv_section') not in {'Experience','Projects','Education','Skills','Certifications','Summary','Other'}:reasons.append('invalid_CV_section')
            else:
                if r.get('cv_id') not in cvs:reasons.append('unknown_CV')
                if type(r.get('relevance_0_3')) is not int or r['relevance_0_3'] not in range(4) or not r.get('main_reason'):reasons.append('invalid_ordinal_relevance')
                if job=='F00114':reasons.append('Reviewer_requested_BC_hold_for_unresolved_composite')
                # J1 reason explicitly depends on incompatible mathematical/statistical AND interpretation.
                if job=='F00022':reasons.append('C_reason_depends_on_unresolved_D049_J1_units')
            if reasons:
                held.append({'sheet':sheet,'identity':key,'reasons':sorted(set(reasons)),'record':r});continue
            rec=deepcopy(r)
            rec.update(split='development',approval_provenance={'source':r.get('_origin','reviewed_workbook'),
                'review_kind':'user_review_with_delegated_followup_QA' if not r.get('_origin') else 'historical_approved_pilot',
                'reviewer':r.get('reviewed_by'),'reviewed_at':r.get('reviewed_at'),
                'receipt_sha256':approval_receipt['source_sha256'],
                'global_dependency_confirmation':approval_receipt['user_confirmed_BC_after_final_A'],
                'row_specific_recheck_timestamp_available':False},
                compatibility={'active_guideline':'v1.3','checked_by':'delegated_execution_role','original_version_preserved':True,
                    'basis':'Source/quote/category/group checks; explicit approved case precedents retained; no global equivalence inferred'},
                jd_source_sha256=hashlib.sha256(canonical_jds[job].encode()).hexdigest())
            if sheet=='A_Extraction':
                rec['logical_unit_id']=job+'/'+(r.get('group_id') or r['unit_no']);candidate_a[key]=rec
            elif sheet=='B_Evidence':
                rec['logical_unit_id']=candidate_a[job+'/'+r['unit_no']]['logical_unit_id']
                rec['dependency_fingerprint']=dependency_token(s,sheet,r);candidate_b[key]=rec
            else:rec['dependency_fingerprint']=dependency_token(s,sheet,r)
            candidates[sheet].append(rec)
    for (job,gid),rs in groups.items():
        retained=[candidate_a.get(job+'/'+r['unit_no']) for r in rs]
        logical.append({'logical_unit_id':job+'/'+gid,'job_id':job,'row_ids':[r['unit_no'] for r in rs],
            'kind':'OR' if len(rs)>1 else ('reviewed_single_row_composite' if rs[0].get('group_id') or '|' in rs[0]['unit_text'] else 'atomic_or_qualified'),
            'count_as':1,'status':'ready' if all(retained) else 'held',
            'guideline_versions':sorted({r['guideline_version'] for r in rs}),
            'mapping_basis':'Exact shared quote and explicit reviewed OR meaning' if len(rs)>1 else 'Reviewed row retained without branch invention',
            'source_quotes':list(dict.fromkeys(r['source_quote'] for r in rs)),
            'scorer_adapter':'Do not flatten OR children; use best supported branch under existing scoring rule. No group label invented by export.'})
    # An OR is atomic for export eligibility: no partial group can leak into scoring.
    blocked_groups={g['logical_unit_id'] for g in logical if g['status']=='held'}
    for sheet in ('A_Extraction','B_Evidence'):
        keep=[]
        for r in candidates[sheet]:
            if r['logical_unit_id'] in blocked_groups:held.append({'sheet':sheet,'identity':identity(sheet,r),'reasons':['logical_group_partly_held'],'record':r})
            else:keep.append(r)
        candidates[sheet]=keep
    for job in sorted(jobs):
        kept=[r for r in s['A_Extraction'] if r['job_id']==job and r['review_action']!='rejected']
        ready=[r for r in candidates['A_Extraction'] if r['job_id']==job]
        coverage.append({'job_id':job,'reviewed_retained_A':len(kept),'promoted_A_rows':len(ready),
            'all_retained_rows_exportable':len(kept)==len(ready),
            'semantic_completeness':'not_inferred_from_row_approval',
            'whole_JD_metric_eligible':False,'reason':'Requires explicit complete source-to-logical-unit alignment receipt before extraction F1'})
    pairs=[]
    for cv,job in sorted({(r['cv_id'],r['job_id']) for r in s['B_Evidence']}):
        expected={r['unit_no'] for r in s['A_Extraction'] if r['job_id']==job and r['review_action']!='rejected'}
        actual={r['unit_no'] for r in candidates['B_Evidence'] if r['cv_id']==cv and r['job_id']==job}
        pairs.append({'cv_id':cv,'job_id':job,'expected_retained_units':len(expected),'ready_evidence_rows':len(actual),
                      'missing_or_held_units':sorted(expected-actual),'complete_existing_reviewed_units':actual==expected,
                      'whole_pair_metric_eligible':False,'reason':'Source completeness/alignment is a separate metric gate'})
    counts={sheet:{'read':len(s[sheet]),'approved':sum(r.get('review_status')=='approved' for r in s[sheet]),
        'rejected':sum(r.get('review_action')=='rejected' for r in s[sheet]),
        'approved_retained':sum(r.get('review_status')=='approved' and r.get('review_action')!='rejected' for r in s[sheet]),
        'staged':len(candidates[sheet]),'held_retained':sum(x['sheet']==sheet and x.get('record',{}).get('review_action')!='rejected' for x in held)} for sheet in SHEETS}
    return {'schema_version':'development-reviewed-records-v1','candidates':candidates,'held':held,'excluded':excluded,
            'logical_units':logical,'coverage':coverage,'pairs':pairs,'counts':counts,'approval_receipt':approval_receipt,
            'status':'validated_partition','gold_written':False,'snapshot_digest':digest(s),
            'limits':['Record-level gold is not whole-JD completeness or verified model alignment.',
                      'Original guideline/review metadata retained. Export time is not a review time.',
                      'Never concatenate pilot and this authoritative current bundle without identity overlay.']}


def validate_saved(directory):
    directory=Path(directory);m=json.loads((directory/'manifest.json').read_text())
    for name,expected in m['files'].items():
        if sha(directory/name)!=expected:raise ValueError('Export hash mismatch')
    for sheet,name in [('A_Extraction','extraction_gold.jsonl'),('B_Evidence','evidence_gold.jsonl'),('C_Relevance','relevance_gold.jsonl')]:
        rows=[json.loads(x) for x in (directory/name).read_text().splitlines()]
        if len(rows)!=m['counts'][sheet]['promoted'] or len({identity(sheet,r) for r in rows})!=len(rows):raise ValueError('Count/identity mismatch')
        if any(r['review_status']!='approved' or r['review_action']=='rejected' or r['split']!='development' for r in rows):raise ValueError('Invalid promotion')
    return m


def promote(plan,directory,*,workbook,workbook_sha256,source_hashes):
    # Promotion metadata must not mutate the validated staging plan in memory.
    plan=deepcopy(plan)
    directory=Path(directory)
    if directory.exists():raise ValueError('Versioned output exists')
    if sha(workbook)!=workbook_sha256:raise ValueError('Workbook changed before promotion; rebuild snapshot')
    for p,h in source_hashes.items():
        if sha(p)!=h:raise ValueError('Protected source changed before promotion')
    tmp=directory.with_name(directory.name+'.pending');tmp.mkdir(parents=True,exist_ok=False)
    files={}
    for sheet,name in [('A_Extraction','extraction_gold.jsonl'),('B_Evidence','evidence_gold.jsonl'),('C_Relevance','relevance_gold.jsonl')]:
        with (tmp/name).open('x') as f:
            for r in plan['candidates'][sheet]:f.write(json.dumps(r,ensure_ascii=False)+'\n')
            f.flush();os.fsync(f.fileno())
        files[name]=sha(tmp/name)
    for key,name in [('logical_units','logical_units.json'),('held','held_records.json'),('excluded','excluded_records.json'),('coverage','JD_coverage.json'),('pairs','pair_coverage.json')]:
        with (tmp/name).open('x') as f:json.dump(plan[key],f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        files[name]=sha(tmp/name)
    m={k:v for k,v in plan.items() if k not in {'candidates','held','excluded','logical_units','coverage','pairs'}}
    m.update(status='promoted_record_gold',gold_written=True,exported_at=datetime.now(timezone.utc).isoformat(),
             workbook_sha256=workbook_sha256,files=files,source_hashes=source_hashes,
             selection_rule='Authoritative workbook decisions by JD/pair; non-overlapping pilot records retained once. Original root pilot files immutable.')
    for c in m['counts'].values():c['promoted']=c['staged']
    with (tmp/'manifest.json').open('x') as f:json.dump(m,f,indent=2);f.flush();os.fsync(f.fileno())
    validate_saved(tmp)
    if sha(workbook)!=workbook_sha256:raise ValueError('Workbook changed during staging; no promotion')
    for p,h in source_hashes.items():
        if sha(p)!=h:raise ValueError('Protected source changed during staging; no promotion')
    os.rename(tmp,directory)  # whole new bundle atomically visible; historical files untouched
    validate_saved(directory)
    return m
