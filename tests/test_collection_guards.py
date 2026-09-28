"""Offline safety regressions. No provider calls or real credentials."""
import argparse
import io
import json
import pytest
from scripts import jsearch_collection as collector


def test_multipage_request_cannot_overrun_verified_free_units(monkeypatch, tmp_path):
    row = {k: '' for k in collector.FIELDS}
    row.update(query_id='TEST', query='test', country='id', language='id', num_pages=3)
    monkeypatch.setattr(collector, 'read_plan', lambda _: [row])
    monkeypatch.setattr(collector, 'get_usage', lambda _: ('Basic', True, 2))
    monkeypatch.setattr(collector, 'RAW', tmp_path)
    monkeypatch.setenv('JSEARCH_API_KEY', 'test-only-dummy')
    monkeypatch.setattr(collector.urllib.request, 'urlopen', lambda *a, **k: pytest.fail('Unexpected network call'))
    args = argparse.Namespace(plan=None, pilot=False, query_id=None, bucket=None,
                              max_requests=10, pages_per_query=1, execute=True, free_only=True)
    collector.collect(args)
    assert not list(tmp_path.iterdir())


def test_string_false_is_not_a_verified_free_plan(monkeypatch):
    payload = {'data': {'plan': {'is_free': 'false'}, 'quotas': []}}
    monkeypatch.setattr(collector.urllib.request, 'urlopen', lambda *a, **k: io.BytesIO(json.dumps(payload).encode()))
    assert collector.get_usage('test-only-dummy')[1] is False


def test_missing_request_quota_does_not_use_unrelated_quota(monkeypatch):
    payload = {'data': {'plan': {'is_free': True}, 'quotas': [{'name': 'Bandwidth', 'remaining': 1000}]}}
    monkeypatch.setattr(collector.urllib.request, 'urlopen', lambda *a, **k: io.BytesIO(json.dumps(payload).encode()))
    with pytest.raises(SystemExit, match='remaining quota is unavailable'):
        collector.get_usage('test-only-dummy')
