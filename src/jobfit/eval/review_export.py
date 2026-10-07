"""Pure review/export planning. No workbook reader and no writes to actual gold.

Use only after review is finished and export is separately authorized. During
implementation this module is exercised exclusively with temporary fixtures.
Dependency acknowledgments attest the exact current A/B/C state, not row numbers.
"""
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import hashlib, json, math
from jobfit.config import REPO_ROOT, SNAPSHOT_ID

SHEETS=('A_Extraction','B_Evidence','C_Relevance')
A_FIELDS=('job_id','unit_no','unit_text','source_quote','importance','category','group_id','min_years')
B_FIELDS=('cv_id','job_id','unit_no','unit_text','label','check_status','cv_quote','cv_section')
C_FIELDS=('cv_id','job_id','relevance_0_3','main_reason','constraint_note')

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def identity(sheet,row):
    fields={'A_Extraction':('job_id','unit_no'),'B_Evidence':('cv_id','job_id','unit_no'),'C_Relevance':('cv_id','job_id')}[sheet]
    return '/'.join(str(row[k]) for k in fields)

def content(row,fields):
    return {k:row.get(k) for k in fields}|{'retained':row.get('review_action')!='rejected'}

def a_basis(snapshot,job,unit=None):
    rows=[r for r in snapshot['A_Extraction'] if r['job_id']==job]
    if unit is not None:
        selected=next((r for r in rows if r['unit_no']==unit),None)
        if selected is None:return digest(None)
        rows=[r for r in rows if r['unit_no']==unit or (selected.get('group_id') and r.get('group_id')==selected['group_id'])]
    return digest(sorted((content(r,A_FIELDS) for r in rows),key=lambda r:r['unit_no']))

def dependency_token(snapshot,sheet,row):
    """Token a human recheck must reference; unrelated row reordering has no effect."""
    job=row['job_id']
    if sheet=='B_Evidence':
        return digest({'A':a_basis(snapshot,job,row['unit_no']),'B':content(row,B_FIELDS)})
    if sheet=='C_Relevance':
        b=[content(r,B_FIELDS) for r in snapshot['B_Evidence'] if (r['job_id'],r['cv_id'])==(job,row['cv_id'])]
        return digest({'A':a_basis(snapshot,job),'B':sorted(b,key=lambda r:r['unit_no']),'C':content(row,C_FIELDS)})
    raise ValueError('Only B/C have upstream dependencies')

def plan_export(snapshot: dict,baseline: dict,*,development_ids: set[str],
                source_hashes: dict,acknowledgments: dict | None=None,
                reviewed_by: str,reviewed_at: str) -> dict:
    """Validate every candidate before returning a staged proposal; pending is excluded.

    C is an independent whole-CV/JD judgment: it does not require every A/B row
    approved. It does require an explicit recheck when its upstream draft changes.
    """
    if not reviewed_by.strip() or datetime.fromisoformat(reviewed_at).tzinfo is None:
        raise ValueError('Supply actual reviewer attribution and timezone-aware review time')
    acknowledgments=acknowledgments or {}
    errors=[];excluded=[];candidates={s:[] for s in SHEETS};deps=[]
    maps={}
    for s in SHEETS:
        maps[s]={identity(s,r):r for r in snapshot[s]}
        if len(maps[s])!=len(snapshot[s]):raise ValueError('Duplicate identity in '+s)
    jobs={r['job_id']:r['jd_text'] for r in snapshot['JDs']}
    cvs={r['cv_id']:r['cv_text'] for r in snapshot['CVs']}
    if len(jobs)!=len(snapshot['JDs']) or len(cvs)!=len(snapshot['CVs']):
        raise ValueError('Duplicate source identity')
    actual={**{'JD/'+k:digest(v) for k,v in jobs.items()},**{'CV/'+k:digest(v) for k,v in cvs.items()}}
    if actual!=source_hashes:raise ValueError('Source text or identity changed from verified baseline')
    if not set(jobs)<=development_ids or not set(cvs)<={'CV1','CV2'}:raise ValueError('Development-only source scope violated')
    def issue(s,r,code): errors.append({'sheet':s,'identity':identity(s,r),'code':code})
    for s in SHEETS:
        for r in snapshot[s]:
            key=identity(s,r)
            if r.get('review_status')!='approved' or r.get('review_action')=='rejected':
                excluded.append({'sheet':s,'identity':key,'reason':'rejected' if r.get('review_action')=='rejected' else 'not_approved'})
                continue
            initial=len(errors)
            if r.get('review_action') not in {'accepted','edited','added'}:issue(s,r,'missing_valid_review_action')
            if not r.get('guideline_version') or r.get('label_source') not in {'model_draft','annotator'}:issue(s,r,'missing_provenance')
            if r.get('review_action')=='edited' and not (r.get('review_note') or '').strip():issue(s,r,'edited_needs_review_note')
            if r['job_id'] not in jobs:issue(s,r,'missing_JD_source')
            if s!='A_Extraction' and r['cv_id'] not in cvs:issue(s,r,'missing_CV_source')
            if s=='A_Extraction':
                if not r.get('source_quote') or r['source_quote'] not in jobs.get(r['job_id'],''):issue(s,r,'invalid_JD_quote')
                if r.get('importance') not in {'required','preferred','unknown'}:issue(s,r,'invalid_importance')
                if r.get('category') not in {'skill_tool','knowledge_area','experience_duration','education','language','certification','soft_skill','location','work_authorization','other'}:issue(s,r,'invalid_category')
                if not (r.get('unit_text') or '').strip():issue(s,r,'missing_unit_text')
                years=r.get('min_years')
                if years is not None and (isinstance(years,bool) or not isinstance(years,(int,float)) or not math.isfinite(years) or years<0):
                    issue(s,r,'invalid_min_years')
            elif s=='B_Evidence':
                a=maps['A_Extraction'].get(r['job_id']+'/'+r['unit_no'])
                if not a or not any(identity('A_Extraction',x)==r['job_id']+'/'+r['unit_no'] for x in candidates['A_Extraction']):
                    issue(s,r,'A_not_exportable_approved')
                elif r.get('unit_text')!=a['unit_text']:issue(s,r,'stale_B_unit_text')
                if r.get('label') not in {'MATCH','PARTIAL','NO_MATCH'}:issue(s,r,'invalid_label')
                if r.get('check_status') not in {'done','needs_clarification'}:issue(s,r,'failed_or_invalid_check_not_gold_evidence')
                q=r.get('cv_quote')
                if r.get('label')=='NO_MATCH':
                    if q:issue(s,r,'NO_MATCH_with_unrelated_quote')
                elif not q or q not in cvs.get(r['cv_id'],''):issue(s,r,'invalid_CV_quote')
                if r.get('label')!='NO_MATCH' and r.get('cv_section') not in {'Experience','Projects','Education','Skills','Certifications','Summary','Other'}:issue(s,r,'invalid_CV_section')
            else:
                if type(r.get('relevance_0_3')) is not int or r['relevance_0_3'] not in range(4):issue(s,r,'invalid_relevance')
                if not (r.get('main_reason') or '').strip():issue(s,r,'missing_relevance_reason')
            if s in ['B_Evidence','C_Relevance']:
                old=next((x for x in baseline[s] if identity(s,x)==key),None)
                upstream_changed=(a_basis(snapshot,r['job_id'],r['unit_no'] if s=='B_Evidence' else None)!=a_basis(baseline,r['job_id'],r['unit_no'] if s=='B_Evidence' else None))
                if s=='C_Relevance':
                    select=lambda snap:sorted((content(x,B_FIELDS) for x in snap['B_Evidence'] if (x['cv_id'],x['job_id'])==(r['cv_id'],r['job_id'])),key=lambda x:x['unit_no'])
                    upstream_changed|=select(snapshot)!=select(baseline)
                token=dependency_token(snapshot,s,r)
                ack=acknowledgments.get(s+'/'+key,{})
                try:
                    ack_time_valid=datetime.fromisoformat(ack.get('reviewed_at','')).tzinfo is not None
                except (ValueError,TypeError):ack_time_valid=False
                ack_ok=(ack.get('token')==token and ack.get('reviewed_by')==reviewed_by and ack_time_valid)
                # A newly added B/C judgment needs its dependencies explicitly acknowledged.
                if (upstream_changed or old is None) and not ack_ok:issue(s,r,'dependency_recheck_required')
                deps.append({'sheet':s,'identity':key,'upstream_changed':upstream_changed,'current_token':token,'acknowledged':ack_ok})
            if len(errors)==initial:
                rec=deepcopy(r)
                rec.update(split='development',snapshot_id=SNAPSHOT_ID)
                # Existing review provenance survives; supplied attribution fills
                # missing export metadata, never overwrites an earlier reviewer.
                rec['reviewed_by']=r.get('reviewed_by') or reviewed_by
                rec['reviewed_at']=r.get('reviewed_at') or reviewed_at
                candidates[s].append(rec)
    coverage=[]
    for job in sorted(jobs):
        a=[r for r in snapshot['A_Extraction'] if r['job_id']==job]
        coverage.append({'job_id':job,'A_rows':len(a),'A_not_yet_reviewed':sum(r.get('review_status')!='approved' for r in a),
                         'A_candidate_rows':sum(r['job_id']==job for r in candidates['A_Extraction']),
                         'all_existing_A_rows_reviewed':all(r.get('review_status')=='approved' for r in a),
                         'semantic_completeness_not_inferred':True})
    return {'status':'blocked' if errors else 'candidate_ready_for_human_export_check','gold_written':False,
            'candidates':candidates,'errors':errors,'excluded':excluded,'dependency_checks':deps,'coverage':coverage,
            'snapshot_digest':digest(snapshot),'baseline_digest':digest(baseline),'source_hashes':source_hashes}

def write_staging(plan: dict,directory: Path):
    """Exclusive candidate artifact only, outside actual gold. No promotion operation."""
    directory=directory.resolve()
    protected=(REPO_ROOT/'evals/gold').resolve()
    if directory==protected or protected in directory.parents:raise ValueError('Actual gold output is not supported by this staging helper')
    if plan['errors'] or plan['status']!='candidate_ready_for_human_export_check':raise ValueError('Resolve export validation errors first')
    directory.mkdir(parents=True,exist_ok=False)
    with (directory/'export_candidate.json').open('x') as f:json.dump(plan,f,indent=2,ensure_ascii=False)
