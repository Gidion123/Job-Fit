"""Provisioned production ledger storage root (CP3 Phase 2 persistent ledger; C2-C4). Offline, tmp_path only."""
import json
import uuid
from pathlib import Path

import pytest

from jobfit.live.common import FileLock, append_durable
from jobfit.live.evidence import breach_path, journal_path
from jobfit.live.storage import (MARKER_NAME, LiveStorage, StorageInitError, StorageUnavailable,
                                 evidence_and_lock_paths, init_storage, main, valid_storage_id)


@pytest.fixture
def root(tmp_path):
    r = tmp_path / 'ledger_root'
    r.mkdir()
    return r


def ledger(root):
    return root / 'usage_ledger.jsonl'


def reason(storage):
    with pytest.raises(StorageUnavailable) as exc:
        storage.validate()
    return exc.value.reason


# --- init and validate ---------------------------------------------------------------------------------------

def test_init_writes_a_strict_marker_and_validate_returns_a_stable_id(root):
    sid = init_storage(ledger(root))
    marker = json.loads((root / MARKER_NAME).read_text())
    assert set(marker) == {'format', 'storage_id', 'ledger_name', 'created_at'}
    assert marker['format'] == 1 and marker['storage_id'] == sid and marker['ledger_name'] == 'usage_ledger.jsonl'
    assert valid_storage_id(sid) and uuid.UUID(hex=sid).version == 4
    storage = LiveStorage(ledger(root))
    assert storage.validate() == sid == storage.validate()
    assert sorted(p.name for p in root.iterdir()) == [MARKER_NAME]       # the probe leaves nothing behind


def test_init_refuses_an_existing_marker(root):
    init_storage(ledger(root))
    with pytest.raises(StorageInitError, match='already provisioned'):
        init_storage(ledger(root))


@pytest.mark.parametrize('which', ['ledger', 'intents', 'breach'])
def test_init_refuses_unmarked_existing_evidence(root, which):
    path = {'ledger': ledger(root), 'intents': journal_path(ledger(root)), 'breach': breach_path(ledger(root))}[which]
    path.write_text('{}\n')
    with pytest.raises(StorageInitError, match='manual review'):
        init_storage(ledger(root))
    assert not (root / MARKER_NAME).exists()


def test_init_never_creates_the_root_and_refuses_a_relative_path(tmp_path):
    with pytest.raises(StorageInitError, match='does not exist'):
        init_storage(tmp_path / 'missing' / 'usage_ledger.jsonl')
    assert not (tmp_path / 'missing').exists()
    with pytest.raises(StorageInitError, match='absolute'):
        init_storage(Path('usage_ledger.jsonl'))


def test_the_operator_command_enforces_the_fixed_production_root(tmp_path, monkeypatch, capsys):
    import jobfit.config
    prod_root = tmp_path / 'prod'
    prod_root.mkdir()
    monkeypatch.setattr(jobfit.config, 'PROD_LEDGER_ROOT', prod_root.resolve())
    other = tmp_path / 'other'
    other.mkdir()
    assert main(['init', '--ledger', str(other / 'usage_ledger.jsonl')]) == 2
    assert main(['init', '--ledger', 'usage_ledger.jsonl']) == 2
    assert main(['init', '--ledger', str(jobfit.config.REPO_USAGE_LEDGER)]) == 2
    assert not (other / MARKER_NAME).exists()
    capsys.readouterr()
    assert main(['init', '--ledger', str(prod_root / 'usage_ledger.jsonl')]) == 0
    sid = json.loads(capsys.readouterr().out)['storage_id']
    assert main(['check', '--ledger', str(prod_root / 'usage_ledger.jsonl')]) == 0
    assert json.loads(capsys.readouterr().out)['storage_id'] == sid
    (prod_root / MARKER_NAME).unlink()
    assert main(['check', '--ledger', str(prod_root / 'usage_ledger.jsonl')]) == 2
    assert 'missing_marker' in capsys.readouterr().err


def test_validate_reports_a_missing_directory(tmp_path):
    assert reason(LiveStorage(tmp_path / 'gone' / 'usage_ledger.jsonl')) == 'missing_directory'
    assert not (tmp_path / 'gone').exists()


def test_validate_reports_a_missing_marker(root):
    assert reason(LiveStorage(ledger(root))) == 'missing_marker'


@pytest.mark.parametrize('body', [
    '{"format": 1, "storage_id": "',                                         # torn
    'not json',
    '[]',
    json.dumps({'format': 2, 'storage_id': uuid.uuid4().hex, 'ledger_name': 'usage_ledger.jsonl', 'created_at': 'x'}),
    json.dumps({'format': True, 'storage_id': uuid.uuid4().hex, 'ledger_name': 'usage_ledger.jsonl', 'created_at': 'x'}),
    json.dumps({'format': 1, 'storage_id': uuid.uuid1().hex, 'ledger_name': 'usage_ledger.jsonl', 'created_at': 'x'}),
    json.dumps({'format': 1, 'storage_id': uuid.uuid4().hex.upper(), 'ledger_name': 'usage_ledger.jsonl',
                'created_at': 'x'}),
    json.dumps({'format': 1, 'storage_id': 'abc', 'ledger_name': 'usage_ledger.jsonl', 'created_at': 'x'}),
    json.dumps({'format': 1, 'storage_id': uuid.uuid4().hex, 'ledger_name': 'usage_ledger.jsonl'}),
    json.dumps({'format': 1, 'storage_id': uuid.uuid4().hex, 'ledger_name': 'usage_ledger.jsonl', 'created_at': 'x',
                'extra': 1}),
])
def test_validate_rejects_an_invalid_marker(root, body):
    (root / MARKER_NAME).write_text(body)
    assert reason(LiveStorage(ledger(root))) == 'invalid_marker'


def test_validate_rejects_a_marker_for_another_ledger_name(root):
    init_storage(ledger(root))
    assert reason(LiveStorage(root / 'other.jsonl')) == 'ledger_name_mismatch'


def test_validate_reports_an_unwritable_root_through_the_injected_probe(root):
    init_storage(ledger(root))

    def failing_probe(path):
        raise PermissionError('read-only volume')
    assert reason(LiveStorage(ledger(root), probe=failing_probe)) == 'not_writable'


def test_all_evidence_and_lock_files_share_the_storage_root(root):
    paths = evidence_and_lock_paths(ledger(root))
    names = {p.name for p in paths}
    assert {'usage_ledger.jsonl', 'usage_ledger.jsonl.intents.jsonl', 'usage_ledger.jsonl.breach.jsonl',
            'usage_ledger.jsonl.lock', 'usage_ledger.jsonl.intents.jsonl.lock', 'usage_ledger.jsonl.breach.jsonl.lock',
            'usage_ledger.jsonl.io.lock'} == names
    assert all(p.parent == root for p in paths)


# --- C4: no implicit directory creation ------------------------------------------------------------------

def test_durable_append_and_file_locks_never_create_a_missing_directory(tmp_path):
    missing = tmp_path / 'unmounted'
    with pytest.raises(FileNotFoundError):
        append_durable(missing / 'usage_ledger.jsonl', '{}')
    with pytest.raises(FileNotFoundError):
        with FileLock.for_path(missing / 'usage_ledger.jsonl.lock').hold(exclusive=True):
            pass
    assert not missing.exists()
