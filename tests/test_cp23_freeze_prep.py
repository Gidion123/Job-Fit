"""Freeze receipt, D-053 pool and blind workbook preparation. Offline, no test data read."""
import json

import pytest

from jobfit.eval.test_pool import blind_items, build_pool
from scripts import build_cp23_test_workbook as wbk
from scripts import prepare_cp23_freeze as frz


def test_pool_is_deduplicated_union_with_ranks_and_counts():
    s1 = {'CV1': ['A', 'B', 'C'], 'CV3': list('PQRSTUVWXYZ')}
    fin = {'CV1': ['C', 'D'], 'CV3': list('ZYXWVUTSRQ')}
    pool = build_pool(s1, fin, eligible=set('ABCDPQRSTUVWXYZ'))
    cv1 = [r for r in pool['rows'] if r['cv_id'] == 'CV1']
    assert [r['job_id'] for r in cv1] == ['A', 'B', 'C', 'D']
    assert cv1[2] == {'cv_id': 'CV1', 'job_id': 'C', 'stage1_rank': 3, 'final_rank': 1}
    assert pool['per_cv']['CV1'] == {'stage1_returned': 3, 'final_returned': 2, 'overlap': 1,
                                     'pairs': 4, 'short_list': True}
    # CV3: stage-1 top 10 is P..Y, final top 10 is Z..Q, union 11 pairs
    assert pool['per_cv']['CV3']['pairs'] == 11 and pool['pairs'] == 15
    assert pool['effort']['estimated_minutes'] == 36


def test_pool_refuses_non_test_jobs_and_duplicates():
    with pytest.raises(ValueError):
        build_pool({'CV1': ['A']}, {'CV1': ['X']}, eligible={'A'})
    with pytest.raises(ValueError):
        build_pool({'CV1': ['A', 'A']}, {'CV1': ['A']}, eligible={'A'})


def test_blind_items_hide_ranks_and_are_reproducible():
    rows = [{'cv_id': 'CV1', 'job_id': j, 'stage1_rank': i, 'final_rank': None} for i, j in enumerate('ABCDE', 1)]
    a, b = blind_items(rows, seed=7), blind_items(rows, seed=7)
    assert a == b and set(a[0]) == {'item_id', 'cv_id', 'job_id'}
    assert [x['item_id'] for x in a] == ['T01', 'T02', 'T03', 'T04', 'T05']
    assert sorted(x['job_id'] for x in a) == list('ABCDE')


V3 = 'config/versions/pipeline_cp23_provisional_v3_20261004.yaml'


def test_freeze_draft_lists_blockers_and_hashes():
    old = frz.build(V3)
    assert any('stage1_k' in b for b in old['blockers'])      # provisional config is blocked
    receipt = frz.build()
    assert receipt['status'] == 'DRAFT_NOT_APPROVED' and receipt['approval'] is None
    assert receipt['blockers'] == [] and receipt['config']['stage1_k'] == 10
    assert receipt['experience_block']['rule'] == 'experience-upper-bound-v1'
    rc = receipt['report_contract']
    assert rc['primary_cvs'] == ['CV3', 'CV4', 'CV5'] and rc['supplementary_cvs'] == ['CV1', 'CV2']
    assert 'src/jobfit/eval/heldout_report.py' in receipt['files_sha256']
    assert 'evals/gold/development_v13_reviewed_20261004_gap_r4/relevance_gold.jsonl' in receipt['files_sha256']
    assert receipt['stage1_call']['branch_depth'].endswith('30')
    assert 'docs/evaluation.md' in receipt['files_sha256']
    assert receipt['matching_call']['model'] == 'gpt-6-sol'


def test_verify_detects_drift(tmp_path):
    receipt = frz.build()
    receipt['files_sha256']['docs/evaluation.md'] = '0' * 64
    (tmp_path / 'freeze_receipt.json').write_text(json.dumps(receipt))
    assert frz.verify(tmp_path) == ['docs/evaluation.md']


def test_approve_refuses_blockers_or_unknown_decision(tmp_path):
    (tmp_path / 'freeze_receipt.json').write_text(json.dumps(frz.build(V3)))
    with pytest.raises(SystemExit):
        frz.approve(tmp_path, None)
    with pytest.raises(SystemExit):
        frz.approve(tmp_path, 'D-999')
    with pytest.raises(SystemExit):   # D-053 exists, but the draft still has blockers
        frz.approve(tmp_path, 'D-053')
    assert not (tmp_path / 'freeze_receipt_APPROVED.json').exists()


def test_workbook_needs_approved_freeze(tmp_path):
    run = tmp_path / 'run.json'
    run.write_text(json.dumps({'run_id': 'x', 'freeze_folder': str(tmp_path), 'cvs': {}}))
    with pytest.raises(SystemExit):
        wbk.load_run(run)


def test_blind_workbook_has_no_rank_or_method_columns(tmp_path):
    from openpyxl import load_workbook
    items = [{'item_id': 'T01', 'cv_id': 'CV3', 'job_id': 'J1'}]
    jobs = {'J1': {'title': 't', 'company': 'c', 'description_clean': 'd'}}
    path = tmp_path / 'w.xlsx'
    wbk.write_workbook(path, items, jobs, ['CV3'])
    wb = load_workbook(path)
    header = [c.value for c in wb['Items'][1]]
    assert header == wbk.COLUMNS
    assert not any(w in ' '.join(header) for w in ('rank', 'score', 'method', 'bucket', 'model'))
    assert wb['CVs']['A2'].value == 'CV3' and wb['CVs']['B2'].value.startswith('<!--')
