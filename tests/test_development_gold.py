from copy import deepcopy
import json
import pytest
from jobfit.eval.development_gold import plan,promote,sha,validate_saved


def fixture():
 a=dict(job_id='F00029',unit_no='P07-U26a',unit_text='Kubernetes',source_quote='Kubernetes or MLOps experience is a plus.',importance='preferred',category='skill_tool',group_id='P07-G11',min_years=None,label_source='model_draft',review_status='approved',review_action='accepted',guideline_version='v1.3')
 b=dict(cv_id='CV1',job_id='F00029',unit_no='P07-U26a',unit_text='Kubernetes',label='MATCH',check_status='done',cv_quote='Used Kubernetes',cv_section='Experience',label_source='model_draft',review_status='approved',review_action='accepted',guideline_version='v1.3')
 return {'JDs':[{'job_id':'F00029','jd_text':a['source_quote']}],'CVs':[{'cv_id':'CV1','cv_text':'Used Kubernetes'}],
  'A_Extraction':[a,dict(a,unit_no='P07-U26b',unit_text='MLOps',category='knowledge_area',guideline_version='v1.2')],
  'B_Evidence':[b,dict(b,unit_no='P07-U26b',unit_text='MLOps',label='NO_MATCH',cv_quote=None)],
  'C_Relevance':[dict(cv_id='CV1',job_id='F00029',relevance_0_3=2,main_reason='Evidence with gaps',label_source='model_draft',review_status='approved',review_action='accepted',guideline_version='v1.3')]}

def check(s):return plan(s,development_ids={'F00029'},canonical_jds={'F00029':'Kubernetes or MLOps experience is a plus.'},canonical_cvs={'CV1':'Used Kubernetes'},approval_receipt={'source_sha256':'receipt','user_confirmed_BC_after_final_A':True})

def test_or_is_one_unit_versions_and_unknown_review_dates_preserved():
 s=fixture();r=check(s)
 assert len(r['logical_units'])==1 and r['logical_units'][0]['count_as']==1
 assert r['logical_units'][0]['kind']=='OR'
 assert r['logical_units'][0]['guideline_versions']==['v1.2','v1.3']
 assert r['candidates']['A_Extraction'][0]['approval_provenance']['reviewed_at'] is None
 assert not r['coverage'][0]['whole_JD_metric_eligible']
 assert s==fixture()

def test_pending_or_rejected_does_not_promote_and_dependencies_hold():
 s=fixture();s['A_Extraction'][0]['review_status']='pending'
 r=check(s);assert not r['candidates']['A_Extraction'] and not r['candidates']['B_Evidence']
 assert r['candidates']['C_Relevance'] # independent ordinal judgment
 s=fixture();s['A_Extraction'][0].update(review_action='rejected',review_note='duplicate')
 r=check(s);assert len(r['excluded'])==1
 assert all(a['unit_no']!='P07-U26a' for a in r['candidates']['A_Extraction'])

def test_source_and_cv_and_duplicate_checks():
 s=fixture();s['JDs'][0]['jd_text']+=' supplemented source'
 r=check(s);assert not any(r['candidates'].values())
 s=fixture();s['CVs'][0]['cv_text']='different'
 with pytest.raises(ValueError):check(s)
 s=fixture();s['A_Extraction'].append(deepcopy(s['A_Extraction'][0]))
 with pytest.raises(ValueError):check(s)

def test_atomic_versioned_bundle_reread_and_no_overwrite(tmp_path):
 workbook=tmp_path/'workbook';workbook.write_bytes(b'unchanged')
 r=check(fixture());dst=tmp_path/'gold/version'
 m=promote(r,dst,workbook=workbook,workbook_sha256=sha(workbook),source_hashes={})
 assert validate_saved(dst)==m and m['counts']['A_Extraction']['promoted']==2
 assert workbook.read_bytes()==b'unchanged'
 with pytest.raises(ValueError):promote(r,dst,workbook=workbook,workbook_sha256=sha(workbook),source_hashes={})
 (dst/'evidence_gold.jsonl').write_text('tampered')
 with pytest.raises(ValueError):validate_saved(dst)

def test_external_workbook_edit_blocks_promotion(tmp_path):
 p=tmp_path/'book';p.write_bytes(b'before');h=sha(p);p.write_bytes(b'after')
 with pytest.raises(ValueError,match='Workbook changed'):promote(check(fixture()),tmp_path/'gold',workbook=p,workbook_sha256=h,source_hashes={})
 assert not (tmp_path/'gold').exists()


def test_promotion_does_not_mutate_review_plan(tmp_path):
 p=tmp_path/'book';p.write_bytes(b'original')
 r=check(fixture());before=deepcopy(r)
 promote(r,tmp_path/'bundle',workbook=p,workbook_sha256=sha(p),source_hashes={})
 assert r==before


def test_changed_protected_source_blocks_export(tmp_path):
 p=tmp_path/'book';p.write_bytes(b'original');source=tmp_path/'source';source.write_bytes(b'before');h=sha(source)
 source.write_bytes(b'after')
 with pytest.raises(ValueError):promote(check(fixture()),tmp_path/'bundle',workbook=p,workbook_sha256=sha(p),source_hashes={str(source):h})
 assert not (tmp_path/'bundle').exists()
