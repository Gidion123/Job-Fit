"""Audit-safe recovery for a CP2.4 parse or extraction record that failed only on a provider timeout.

Use `--cv CVx` for a parse record or `--job F0xxxx` for a JD extraction record. A record that
failed for any other reason (for example `schema_validation` after the one frozen repair) is
refused: it stays failed and the job is held in the product order (D-073), never retried here.

The frozen runner (`scripts/run_cp24_test.py`, hashed in the D-087 freeze) treats an
existing `{CV}_parse.json` as done, also when it records a failure. This helper does not
change the frozen runner. It moves (never deletes, never edits) the failed record into
`failed_attempts/` with a receipt holding its sha256, size and reason, so the unchanged
frozen `parse` phase retries that one CV with the same model, prompt and settings.

Guards: approved freeze with no drift; the record is `status: failed` for that CV; every
warning is an API timeout (no validation or content failure); at most 2 archived attempts
per CV; other CVs are never touched. Dry run unless --execute. No model call.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

OUT = ROOT / 'evals/results/cp24/test_run_v1'
TIMEOUT_MARKERS = ('APITimeoutError', 'ReadTimeout', 'Timeout')
MAX_ARCHIVED = 2


def check(cv: str, out: Path = OUT) -> dict:
    path = out / f'{cv}_parse.json'
    if not path.exists():
        raise SystemExit(f'{path.name} does not exist; nothing to recover')
    raw = path.read_bytes()
    row = json.loads(raw)
    warnings = (row.get('parsed') or {}).get('warnings') or []
    if row.get('cv_id') != cv or row.get('status') != 'failed':
        raise SystemExit(f'{path.name} is not a failed record for {cv}; refusing')
    if not warnings or not all(any(m in w for m in TIMEOUT_MARKERS) for w in warnings if 'cv_parsing' in w) \
            or not any('cv_parsing' in w for w in warnings):
        raise SystemExit('The failure is not a pure API timeout; a retry would not be audit-safe. Ask Claude.')
    archive = out / 'failed_attempts'
    done = sorted(archive.glob(f'{cv}_parse_attempt*.json')) if archive.exists() else []
    done = [p for p in done if not p.name.endswith('_receipt.json')]
    if len(done) >= MAX_ARCHIVED:
        raise SystemExit(f'{cv} already failed {len(done)} archived time(s); stop and review instead of retrying')
    n = len(done) + 1
    return {'cv': cv, 'source': path, 'target': archive / f'{cv}_parse_attempt{n}.json',
            'receipt': archive / f'{cv}_parse_attempt{n}_receipt.json', 'attempt': n,
            'sha256': sha256(raw).hexdigest(), 'bytes': len(raw), 'warnings': warnings,
            'masked_digest': row.get('masked_digest')}


def check_job(job: str, out: Path = OUT) -> dict:
    """Same guards for a JD extraction record written by the frozen extraction phase."""
    path = out / f'jd_{job}.json'
    if not path.exists():
        raise SystemExit(f'{path.name} does not exist; nothing to recover')
    raw = path.read_bytes()
    row = json.loads(raw)
    if row.get('job_id') != job or row.get('status') != 'failed':
        raise SystemExit(f'{path.name} is not a failed record for {job}; refusing')
    code = str(row.get('error_code') or '')
    if not any(m in code for m in TIMEOUT_MARKERS):
        raise SystemExit(f'{job} failed with {code!r}, not a provider timeout. It stays failed and is held '
                         '(D-073); the frozen retry policy (one validation repair) is already used.')
    archive_dir = out / 'failed_attempts'
    done = [p for p in (sorted(archive_dir.glob(f'jd_{job}_attempt*.json')) if archive_dir.exists() else [])
            if not p.name.endswith('_receipt.json')]
    if len(done) >= MAX_ARCHIVED:
        raise SystemExit(f'{job} already failed {len(done)} archived time(s); stop and review instead of retrying')
    n = len(done) + 1
    return {'cv': job, 'source': path, 'target': archive_dir / f'jd_{job}_attempt{n}.json',
            'receipt': archive_dir / f'jd_{job}_attempt{n}_receipt.json', 'attempt': n,
            'sha256': sha256(raw).hexdigest(), 'bytes': len(raw), 'warnings': [f'jd_extraction: {code} '
            f"({row.get('attempts')} attempt(s))"], 'masked_digest': None}


def archive(plan: dict, out: Path = OUT) -> None:
    plan['target'].parent.mkdir(parents=True, exist_ok=True)
    if plan['target'].exists() or plan['receipt'].exists():
        raise SystemExit('Archive target already exists; refusing to overwrite')
    os.rename(plan['source'], plan['target'])          # move, same bytes; never delete
    if sha256(plan['target'].read_bytes()).hexdigest() != plan['sha256']:
        raise SystemExit('Archived file changed during the move; investigate')
    receipt = {'schema_version': 'cp24-failed-attempt-receipt-v1', 'record_id': plan['cv'], 'attempt': plan['attempt'],
               'original_path': str(plan['source'].relative_to(ROOT)) if plan['source'].is_relative_to(ROOT) else str(plan['source']),
               'archived_path': str(plan['target'].relative_to(ROOT)) if plan['target'].is_relative_to(ROOT) else str(plan['target']),
               'sha256': plan['sha256'], 'bytes': plan['bytes'], 'failure': plan['warnings'],
               'masked_digest': plan['masked_digest'],
               'reason': 'Operational provider timeout only. Retried by the unchanged frozen phase with the same '
                         'model, prompt, schema, validator and settings (D-087). No test outcome was read.',
               'archived_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    with plan['receipt'].open('x') as f:
        json.dump(receipt, f, indent=1)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    who = ap.add_mutually_exclusive_group(required=True)
    who.add_argument('--cv', choices=['CV3', 'CV4', 'CV5'])
    who.add_argument('--job', help='test JD id, for example F00206')
    ap.add_argument('--freeze', type=Path, required=True)
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args(argv)
    from scripts.run_corpus_extraction import require_freeze
    require_freeze(args.freeze if args.freeze.is_absolute() else ROOT / args.freeze)
    plan = check(args.cv) if args.cv else check_job(args.job)
    print(json.dumps({k: str(v) for k, v in plan.items()}, indent=1))
    if not args.execute:
        print('Dry run. Nothing was moved.')
        return 0
    archive(plan)
    phase = 'parse' if args.cv else 'extraction'
    print(f'Archived. Now rerun: python scripts/run_cp24_test.py {phase} --freeze {args.freeze} --execute')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
