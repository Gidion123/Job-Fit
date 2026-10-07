"""No workbook write or inference: explicit D-054 gold amendment safeguards."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from jobfit.eval.development_gold import validate_saved
from jobfit.eval.stage1_amendment import promote_amendment, stage_approved_changes


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'evals/gold/development_v13_reviewed_20261002_r2'
PACKET = ROOT/'evals/labeling/drafts/cp23_stage1_relevance_review_20261003_v1.json'
HELD_PACKET = ROOT/'evals/labeling/drafts/cp23_stage1_held_C_review_20261003_v1.json'
APPROVAL = ROOT/'evals/results/cp23_stage1_user_review_receipt_20261003_v2.json'
C_RECHECK = ROOT/'evals/results/cp23_F00332_C_recheck_20261003_v1.json'


def staged(**overrides):
    args=dict(root=ROOT,base=BASE,review_packet=PACKET,held_c_packet=HELD_PACKET,
              approval_receipt=APPROVAL,dependent_c_receipt=C_RECHECK)
    args.update(overrides)
    return stage_approved_changes(**args)


def test_approved_overlay_changes_exactly_two_B_and_nine_C():
    rows,changes,base,held,resolved=staged()
    assert [len(rows[k]) for k in ('A_Extraction','B_Evidence','C_Relevance')]==[1058,1364,78]
    assert len(changes)==11 and len(resolved)==3
    assert len([h for h in held if h['sheet']=='C_Relevance'])==2
    assert len([h for h in held if h['sheet']=='A_Extraction'])==45
    assert len([h for h in held if h['sheet']=='B_Evidence'])==39
    b=[r for r in rows['B_Evidence'] if r['cv_id']=='CV1' and r['job_id']=='F00332'
       and r['unit_no'] in {'P30-U08','P30-U15'}]
    assert len(b)==2 and all(r['label']=='PARTIAL' and r['review_action']=='edited' for r in b)
    assert all(r['approval_provenance']['reviewer']=='Dion' for r in b)
    c={(r['cv_id'],r['job_id']):r for r in rows['C_Relevance']}
    assert c['CV1','F00332']['relevance_0_3']==3 and c['CV1','F00332']['dependency_recheck']
    assert c['CV1','F00369']['source_limitation']
    assert c['CV2','F00559']['dependency_scope'].startswith('direct_ordinal')
    assert base['counts']['C_Relevance']['promoted']==69  # original manifest untouched


def test_draft_or_approval_mutation_blocks_promotion(tmp_path):
    packet=json.loads(PACKET.read_text())
    packet['rows'][0]['exact_jd_excerpt']='invented requirement'
    bad=tmp_path/'bad_packet.json';bad.write_text(json.dumps(packet))
    with pytest.raises(ValueError):staged(review_packet=bad)
    approval=json.loads(APPROVAL.read_text())
    approval['approved']['six_C'][0][2]=3
    bad=tmp_path/'bad_approval.json';bad.write_text(json.dumps(approval))
    with pytest.raises(ValueError):staged(approval_receipt=bad)
    c=json.loads(C_RECHECK.read_text());c['relevance_0_3']=2
    bad=tmp_path/'bad_C_recheck.json';bad.write_text(json.dumps(c))
    with pytest.raises(ValueError):staged(dependent_c_receipt=bad)


def test_versioned_promotion_preserves_base_and_rejects_overwrite(tmp_path):
    before=(BASE/'manifest.json').read_bytes()
    output=tmp_path/'versioned_amendment'
    result=promote_amendment(ROOT,BASE,output,PACKET,HELD_PACKET,APPROVAL,C_RECHECK)
    assert result['counts']['C_Relevance']['promoted']==78
    assert result['counts']['C_Relevance']['held_retained']==2
    assert validate_saved(output)['files']['resolved_held_C_records.json']
    assert (BASE/'manifest.json').read_bytes()==before
    with pytest.raises(ValueError,match='already exists'):
        promote_amendment(ROOT,BASE,output,PACKET,HELD_PACKET,APPROVAL,C_RECHECK)
