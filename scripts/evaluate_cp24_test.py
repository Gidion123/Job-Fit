"""CP2.4 held-out evaluation under the frozen report contract (src/jobfit/eval/heldout_report.py).

Inputs: the test run file (scripts/run_cp24_test.py pool) and the imported blind test labels
(JSONL rows with cv_id, job_id, relevance_0_3, review_status approved). Refuses without an
APPROVED freeze receipt and with any file drift. The headline is CV3-CV5 only; CV1-CV2 are a
separate familiar-profile diagnostic; no pooled CV1-CV5 number is produced.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.eval.heldout_report import build_report, headline_text


def load_labels(path: Path) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get('review_status') != 'approved':
            continue
        out.setdefault(row['cv_id'], {})[row['job_id']] = int(row['relevance_0_3'])
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run', type=Path)
    ap.add_argument('labels', type=Path)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args(argv)
    run = json.loads(args.run.read_text())
    from scripts.run_corpus_extraction import require_freeze
    require_freeze(ROOT / run['freeze_folder'])
    eligible = sorted((ROOT / 'evals/splits/test_job_ids.txt').read_text().split())
    report = build_report(run, load_labels(args.labels), eligible=eligible)
    print(headline_text(report))
    if args.write:
        folder = ROOT / 'evals/results/cp24'
        n = 1
        while (folder / f'heldout_report_v{n}.json').exists():
            n += 1
        (folder / f'heldout_report_v{n}.json').write_text(json.dumps(report, indent=1) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
