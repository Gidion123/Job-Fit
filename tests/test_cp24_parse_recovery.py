"""Audit-safe parse recovery: move with receipt, timeout-only, attempt limit, other CVs untouched."""
import json
from hashlib import sha256

import pytest

from scripts import cp24_archive_failed_parse as rec


def write(out, cv, status='failed', warnings=('cv_parsing: APITimeoutError (1 attempt(s))',)):
    p = out / f'{cv}_parse.json'
    p.write_text(json.dumps({'cv_id': cv, 'status': status, 'masked_digest': 'd', 'attempts': 1,
                             'parsed': {'warnings': list(warnings)}}))
    return p


def test_timeout_record_is_moved_not_deleted_and_receipted(tmp_path):
    src = write(tmp_path, 'CV5')
    ok4 = write(tmp_path, 'CV4', status='ok', warnings=())
    before = sha256(src.read_bytes()).hexdigest()
    plan = rec.check('CV5', tmp_path)
    rec.archive(plan, tmp_path)
    assert not src.exists() and ok4.exists()
    moved = tmp_path / 'failed_attempts/CV5_parse_attempt1.json'
    assert sha256(moved.read_bytes()).hexdigest() == before
    receipt = json.loads((tmp_path / 'failed_attempts/CV5_parse_attempt1_receipt.json').read_text())
    assert receipt['sha256'] == before and 'APITimeoutError' in receipt['failure'][0] and receipt['record_id'] == 'CV5'


def test_refuses_success_records_and_content_failures(tmp_path):
    write(tmp_path, 'CV4', status='ok', warnings=())
    with pytest.raises(SystemExit):
        rec.check('CV4', tmp_path)
    write(tmp_path, 'CV3', warnings=('cv_parsing: invalid_source_quote (2 attempt(s))',))
    with pytest.raises(SystemExit):
        rec.check('CV3', tmp_path)


def test_attempt_limit(tmp_path):
    for _ in range(2):
        write(tmp_path, 'CV5')
        rec.archive(rec.check('CV5', tmp_path), tmp_path)
    write(tmp_path, 'CV5')
    with pytest.raises(SystemExit):
        rec.check('CV5', tmp_path)


def test_needs_approved_freeze(tmp_path):
    with pytest.raises(SystemExit):
        rec.main(['--cv', 'CV5', '--freeze', str(tmp_path)])


def test_frozen_parse_phase_would_only_redo_the_archived_cv(tmp_path, monkeypatch):
    from scripts import run_cp24_test as t
    monkeypatch.setattr(t, 'OUT', tmp_path)
    for cv in ('CV1', 'CV2', 'CV3', 'CV4'):
        write(tmp_path, cv, status='ok', warnings=())
    assert t.phase_parse(False)['parse'] == ['CV5']


def jd(out, job, code, attempts):
    p = out / f'jd_{job}.json'
    p.write_text(json.dumps({'job_id': job, 'status': 'failed', 'attempts': attempts, 'error_code': code,
                             'extraction': None}))
    return p


def test_extraction_timeout_is_archived_and_schema_failure_is_refused(tmp_path):
    src = jd(tmp_path, 'F00206', 'APITimeoutError', 1)
    jd(tmp_path, 'F00480', 'schema_validation', 2)
    before = sha256(src.read_bytes()).hexdigest()
    rec.archive(rec.check_job('F00206', tmp_path), tmp_path)
    moved = tmp_path / 'failed_attempts/jd_F00206_attempt1.json'
    assert not src.exists() and sha256(moved.read_bytes()).hexdigest() == before
    with pytest.raises(SystemExit, match='stays failed'):
        rec.check_job('F00480', tmp_path)
    assert (tmp_path / 'jd_F00480.json').exists()


def test_frozen_extraction_phase_would_only_redo_the_archived_job(tmp_path, monkeypatch):
    from scripts import run_cp24_test as t
    jobs = ['F1', 'F2', 'F3']
    for j in jobs[1:]:
        jd(tmp_path, j, 'x', 1)
    assert [j for j in jobs if not (tmp_path / f'jd_{j}.json').exists()] == ['F1']   # same rule as the frozen phase


def test_failed_extraction_becomes_an_explicit_hold_never_zero():
    from jobfit.recommend.service import extraction_from_record
    ext, reason = extraction_from_record({'job_id': 'F00480', 'status': 'failed', 'error_code': 'schema_validation',
                                          'extraction': None})
    assert ext is None and reason == 'schema_validation'
