"""Corpus extraction script: offline checks only, no client is created."""
import pytest

from scripts import run_corpus_extraction as rce


def test_development_sources_are_the_frozen_214():
    src = rce.split_sources('development')
    assert len(src) == 214 and all(t.strip() for t in src.values())


def test_reuse_only_takes_evaluated_matchable_records():
    src = rce.split_sources('development')
    found = {j: rce.reusable(j) for j in src}
    found = {j: p for j, p in found.items() if p}
    assert len(found) >= 40
    assert all(p.name.startswith('jd_') for p in found.values())


def test_test_split_needs_approved_freeze(tmp_path):
    with pytest.raises(SystemExit):
        rce.main(['--split', 'test'])
    with pytest.raises(SystemExit):
        rce.require_freeze(tmp_path)


def test_quality_counts():
    ok = {'job_id': 'A', 'status': 'done', 'coverage': {'status': 'ok'},
          'extraction': {'jd_quality': 'ok', 'units': [{'importance': 'required'}, {'importance': 'preferred'}]}}
    pref = {'job_id': 'B', 'status': 'done', 'coverage': {'status': 'review_required'}, 'reused_from': 'x',
            'extraction': {'jd_quality': 'ok', 'units': [{'importance': 'preferred'}]}}
    bad = {'job_id': 'C', 'status': 'failed', 'error_code': 'timeout', 'extraction': None}
    q = rce.quality([ok, pref, bad])
    assert q['matchable'] == 2 and q['not_matchable'] == 1 and q['errors'] == {'timeout': 1}
    assert q['coverage_review'] == 1 and q['reused'] == 1 and q['zero_required'] == 1
    assert (q['units_min'], q['units_max']) == (1, 2)
