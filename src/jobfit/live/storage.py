"""Provisioned production ledger storage root (CP3 Phase 2, persistent production ledger; D-101).

The authoritative Phase 2B filesystem evidence (the correlated ledger, ``<ledger>.intents.jsonl``,
``<ledger>.breach.jsonl`` and their lock files) lives in ONE directory, the storage root: the
ledger's parent. In production that root is the fixed mount point ``config.PROD_LEDGER_ROOT``
(``/var/lib/jobfit/ledger``), a named volume in the deployment.

The root is usable only after an explicit operator step writes the provisioning marker
``.jobfit-ledger-storage.json`` (format 1, a random uuid4 ``storage_id``, the ledger file name):

    python -m jobfit.live.storage init --ledger /var/lib/jobfit/ledger/usage_ledger.jsonl
    python -m jobfit.live.storage check --ledger /var/lib/jobfit/ledger/usage_ledger.jsonl

``init`` never creates directories and refuses an existing marker or unmarked existing evidence.
The image never contains a marker, so an unmounted or replaced volume cannot pass as provisioned:
live operations are refused (``ledger_storage_unavailable``) instead of starting from empty
evidence. Validation checks only what the process can prove: the root exists, the marker is
strictly valid for this ledger, and a probe file can be created, fsynced and removed. It does not
try to detect "Docker persistence"; the deployment makes persistence explicit.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from jobfit.live.evidence import breach_path, journal_path

MARKER_NAME = '.jobfit-ledger-storage.json'
MARKER_FORMAT = 1
MARKER_KEYS = frozenset({'format', 'storage_id', 'ledger_name', 'created_at'})
STORAGE_ID_RE = re.compile(r'[0-9a-f]{32}')


class StorageUnavailable(RuntimeError):
    """The storage root cannot be proven usable. ``reason`` is a fixed code, logged only."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class StorageInitError(ValueError):
    """Provisioning refused; nothing was written."""


def valid_storage_id(value) -> bool:
    """Exactly 32 lowercase hex characters of a version-4 UUID (``uuid.uuid4().hex``)."""
    if not isinstance(value, str) or not STORAGE_ID_RE.fullmatch(value):
        return False
    return uuid.UUID(hex=value).version == 4


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_probe(root: Path) -> None:
    """Create, write, fsync and remove one uniquely named probe file in the root."""
    probe = root / f'.jobfit-probe-{os.getpid()}-{uuid.uuid4().hex}'
    fd = os.open(probe, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, b'probe\n')
        os.fsync(fd)
    finally:
        os.close(fd)
        try:
            os.unlink(probe)
        except FileNotFoundError:
            pass


def evidence_files(ledger_path: Path) -> list[Path]:
    """The evidence files (never the lock files): ledger, intent journal, breach marker."""
    ledger_path = Path(ledger_path)
    return [ledger_path, journal_path(ledger_path), breach_path(ledger_path)]


def evidence_and_lock_paths(ledger_path: Path) -> list[Path]:
    ledger_path = Path(ledger_path)
    files = evidence_files(ledger_path)
    locks = [p.with_name(p.name + '.lock') for p in files] + [ledger_path.with_name(ledger_path.name + '.io.lock')]
    return files + locks


class LiveStorage:
    """The storage root of one production ledger path."""

    def __init__(self, ledger_path: Path, *, probe: Callable[[Path], None] = write_probe):
        self.ledger_path = Path(ledger_path)
        self.root = self.ledger_path.parent
        self.marker_path = self.root / MARKER_NAME
        self.probe = probe

    def read_marker(self) -> str:
        try:
            text = self.marker_path.read_text(encoding='utf-8')
        except FileNotFoundError:
            raise StorageUnavailable('missing_marker') from None
        except (OSError, UnicodeDecodeError):
            raise StorageUnavailable('invalid_marker') from None
        try:
            marker = json.loads(text)
        except json.JSONDecodeError:
            raise StorageUnavailable('invalid_marker') from None
        if (not isinstance(marker, dict) or set(marker) != MARKER_KEYS
                or type(marker['format']) is not int or marker['format'] != MARKER_FORMAT
                or not valid_storage_id(marker['storage_id']) or not isinstance(marker['created_at'], str)
                or not isinstance(marker['ledger_name'], str)):
            raise StorageUnavailable('invalid_marker')
        if marker['ledger_name'] != self.ledger_path.name:
            raise StorageUnavailable('ledger_name_mismatch')
        return marker['storage_id']

    def validate(self) -> str:
        """The storage id of a provisioned, writable root; StorageUnavailable otherwise."""
        try:
            is_dir = self.root.is_dir()
        except OSError:
            is_dir = False
        if not is_dir:
            raise StorageUnavailable('missing_directory')
        storage_id = self.read_marker()
        if any(p.parent != self.root for p in evidence_and_lock_paths(self.ledger_path)):
            raise StorageUnavailable('not_colocated')
        try:
            self.probe(self.root)
        except Exception:
            raise StorageUnavailable('not_writable') from None
        return storage_id


def init_storage(ledger_path: Path) -> str:
    """Write the provisioning marker into an existing, empty-of-evidence root. Returns the id."""
    ledger_path = Path(ledger_path)
    if not ledger_path.is_absolute():
        raise StorageInitError('the ledger path must be absolute')
    root = ledger_path.parent
    if not root.is_dir():
        raise StorageInitError('the storage root does not exist (it is never created here)')
    marker = root / MARKER_NAME
    if marker.exists():
        raise StorageInitError('the storage root is already provisioned')
    if any(p.exists() for p in evidence_files(ledger_path)):
        raise StorageInitError('evidence exists without a provisioning marker: manual review required')
    storage_id = uuid.uuid4().hex
    body = json.dumps({'format': MARKER_FORMAT, 'storage_id': storage_id, 'ledger_name': ledger_path.name,
                       'created_at': datetime.now(timezone.utc).isoformat(timespec='seconds')}, sort_keys=True)
    fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, (body + '\n').encode('utf-8'))
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_dir(root)
    return storage_id


def _check_production_path(raw: str) -> Path:
    """The C1 rules for the operator command, from the same constant as the settings."""
    from jobfit import config
    path = Path(raw)
    if not path.is_absolute():
        raise StorageInitError('the ledger path must be absolute')
    if path.resolve() == config.REPO_USAGE_LEDGER.resolve():
        raise StorageInitError('the ledger must not be the repository development ledger')
    if path.resolve().parent != config.PROD_LEDGER_ROOT:
        raise StorageInitError(f'the ledger must be a file directly in {config.PROD_LEDGER_ROOT}')
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='python -m jobfit.live.storage',
                                     description='Provision or check the production ledger storage root.')
    parser.add_argument('command', choices=('init', 'check'))
    parser.add_argument('--ledger', required=True, help='absolute production ledger path')
    args = parser.parse_args(argv)
    try:
        if args.command == 'init':
            storage_id = init_storage(_check_production_path(args.ledger))
        else:
            storage_id = LiveStorage(Path(args.ledger)).validate()
    except StorageInitError as exc:
        print(f'refused: {exc}', file=sys.stderr)
        return 2
    except StorageUnavailable as exc:
        print(f'unavailable: {exc.reason}', file=sys.stderr)
        return 2
    print(json.dumps({'storage_id': storage_id}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
