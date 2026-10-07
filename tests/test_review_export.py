from copy import deepcopy
import json
import pytest
from jobfit.eval.review_export import plan_export,dependency_token,digest,write_staging

REVIEWER='fixture-annotator'
WHEN='2026-10-02T10:00:00+07:00'

def fixture():
    meta={'review_status':'approved','review_action':'accepted','review_note':None,'guideline_version':'v1.2','label_source':'model_draft'}
    return {'JDs':[{'job_id':'DEV','jd_text':'Python and SQL required.'}],'CVs':[{'cv_id':'CV1','cv_text':'Used Python at work.'}],
        'A_Extraction':[dict(meta,job_id='DEV',unit_no='u1',unit_text='Python',source_quote='Python',importance='required',category='skill_tool',group_id=None,min_years=None)],
        'B_Evidence':[dict(meta,cv_id='CV1',job_id='DEV',unit_no='u1',unit_text='Python',label='MATCH',check_status='done',cv_quote='Used Python at work.',cv_section='Experience')],
        'C_Relevance':[dict(meta,cv_id='CV1',job_id='DEV',relevance_0_3=3,main_reason='Contextual Python use.',constraint_note=None)]}

def plan(current,base,acks=None):
    hashes={'JD/DEV':digest(base['JDs'][0]['jd_text']),'CV/CV1':digest(base['CVs'][0]['cv_text'])}
    return plan_export(current,base,development_ids={'DEV'},source_hashes=hashes,reviewed_by=REVIEWER,reviewed_at=WHEN,acknowledgments=acks)

def test_approved_candidate_is_staged_without_gold_or_source_mutation(tmp_path):
    s=fixture();before=deepcopy(s);p=plan(s,before)
    assert not p['errors'] and not p['gold_written']
    write_staging(p,tmp_path/'new')
    assert s==before and (tmp_path/'new/export_candidate.json').exists()
    with pytest.raises(FileExistsError):write_staging(p,tmp_path/'new')
    assert p['candidates']['A_Extraction'][0]['guideline_version']=='v1.2'

@pytest.mark.parametrize('status,action',[('pending',None),('approved','rejected')])
def test_pending_and_rejected_never_become_gold_and_do_not_block_independent_C(status,action):
    base=fixture();s=deepcopy(base)
    s['A_Extraction'][0].update(review_status=status,review_action=action)
    s['B_Evidence'][0].update(review_status=status,review_action=action)
    # Treat this as the already reviewed baseline: no upstream revision to the independent C.
    p=plan(s,deepcopy(s))
    assert p['candidates']['A_Extraction']==[] and p['candidates']['B_Evidence']==[]
    assert len(p['candidates']['C_Relevance'])==1 and len(p['excluded'])==2

def test_A_semantic_change_requires_exact_B_and_C_recheck_not_just_approved_status(tmp_path):
    base=fixture();s=deepcopy(base)
    s['A_Extraction'][0].update(importance='preferred',review_action='edited',review_note='Fixture review.')
    p=plan(s,base)
    assert sum(x['code']=='dependency_recheck_required' for x in p['errors'])==2
    with pytest.raises(ValueError):write_staging(p,tmp_path/'must_not_exist')
    assert not (tmp_path/'must_not_exist').exists()
    acks={}
    for sheet in ['B_Evidence','C_Relevance']:
        row=s[sheet][0];key=sheet+'/CV1/DEV'+('/u1' if sheet=='B_Evidence' else '')
        acks[key]={'token':dependency_token(s,sheet,row),'reviewed_by':REVIEWER,'reviewed_at':WHEN}
    assert not plan(s,base,acks)['errors']
    s['B_Evidence'][0].update(label='PARTIAL')
    assert any(e['code']=='dependency_recheck_required' for e in plan(s,base,acks)['errors'])

def test_source_and_duplicate_id_guards():
    base=fixture();s=deepcopy(base);s['CVs'][0]['cv_text']='changed'
    with pytest.raises(ValueError):plan(s,base)
    s=deepcopy(base);s['A_Extraction']*=2
    with pytest.raises(ValueError):plan(s,base)

@pytest.mark.parametrize('change,code',[({'cv_quote':'invented'},'invalid_CV_quote'),({'unit_text':'SQL'},'stale_B_unit_text'),({'check_status':'failed'},'failed_or_invalid_check_not_gold_evidence')])
def test_invalid_approved_evidence_is_blocked(change,code):
    base=fixture();s=deepcopy(base);s['B_Evidence'][0].update(change)
    p=plan(s,base)
    assert any(e['code']==code for e in p['errors']) and not p['candidates']['B_Evidence']

def test_approved_B_cannot_reference_pending_A():
    s=fixture();s['A_Extraction'][0]['review_status']='pending'
    p=plan(s,deepcopy(s));assert any(e['code']=='A_not_exportable_approved' for e in p['errors'])

def test_row_order_and_review_note_do_not_invalidate_unchanged_semantics():
    base=fixture();s=deepcopy(base);s['A_Extraction'][0]['review_note']='Checked.'
    assert not plan(s,base)['errors']

def test_legacy_exporter_cannot_rewrite_frozen_split(tmp_path,monkeypatch):
    import scripts.export_pilot_gold as legacy
    split=tmp_path/'splits';split.mkdir();(split/'split_manifest.json').write_text('{}')
    marker=split/'dev_job_ids.txt';marker.write_text('214 frozen IDs marker')
    monkeypatch.setattr(legacy,'SPLITS',split)
    monkeypatch.setattr(legacy,'WORKBOOK',tmp_path/'must_not_open.xlsx')
    monkeypatch.setattr(legacy,'GOLD',tmp_path/'must_not_write')
    assert legacy.main()==1 and marker.read_text()=='214 frozen IDs marker'
    assert not (tmp_path/'must_not_write').exists()

@pytest.mark.parametrize('years',[float('nan'),float('inf'),-1,True,'2'])
def test_approved_duration_must_be_valid_before_export(years):
    s=fixture();s['A_Extraction'][0]['min_years']=years
    p=plan(s,deepcopy(s))
    assert any(e['code']=='invalid_min_years' for e in p['errors'])
    assert not p['candidates']['A_Extraction']

def test_OR_member_change_invalidates_evidence_for_other_member():
    base=fixture();a=base['A_Extraction'][0];a['group_id']='G1'
    base['A_Extraction'].append(dict(a,unit_no='u2',unit_text='SQL',source_quote='SQL'))
    s=deepcopy(base);s['A_Extraction'][1]['review_action']='rejected'
    p=plan(s,base)
    assert any(e['sheet']=='B_Evidence' and e['identity']=='CV1/DEV/u1' and e['code']=='dependency_recheck_required' for e in p['errors'])

def test_staging_refuses_actual_gold_even_with_valid_candidate():
    from jobfit.config import REPO_ROOT
    s=fixture()
    with pytest.raises(ValueError,match='Actual gold'):
        write_staging(plan(s,deepcopy(s)),REPO_ROOT/'evals/gold/not_allowed')

def test_source_duplicate_and_review_provenance_are_not_lost():
    s=fixture();s['A_Extraction'][0].update(reviewed_by='original-reviewer',reviewed_at='2026-09-30T09:00:00+07:00')
    r=plan(s,deepcopy(s))['candidates']['A_Extraction'][0]
    assert r['reviewed_by']=='original-reviewer' and r['reviewed_at']=='2026-09-30T09:00:00+07:00'
    s['JDs']*=2
    with pytest.raises(ValueError,match='Duplicate source'):
        plan(s,deepcopy(s))
