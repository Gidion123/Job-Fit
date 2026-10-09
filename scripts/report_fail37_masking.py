"""Write a counts-only FAIL-37 / D-104 calibration receipt.

The receipt holds gate results, counts and case ids only, never fixture text. The locked
holdout is refused for every adapter except the D-104 sanitizer (v2), and for v2 only with the
explicit --single-holdout-run flag. Synthetic fixtures; not a privacy guarantee.

Example: python scripts/report_fail37_masking.py --adapter v1 --set dev --date 2026-10-09 \
    --out evals/results/fail37_structural_calibration_20261009_v1_baseline.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from tests import masking_calibration as mc  # noqa: E402

ADAPTERS = {'v1': mc.v1_adapter, 'identity': mc.identity_adapter, 'v2': mc.v2_adapter}


def render(receipt: dict) -> str:
    return json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + '\n'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--adapter', choices=sorted(ADAPTERS), required=True)
    parser.add_argument('--set', choices=sorted(mc.SETS), required=True)
    parser.add_argument('--date', required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--single-holdout-run', action='store_true',
                        help='the one approved first-pass D-104 run on the locked holdout (v2 only)')
    args = parser.parse_args(argv)
    try:
        receipt = mc.build_receipt(args.set, args.adapter, ADAPTERS[args.adapter], date=args.date,
                                   single_run=args.single_holdout_run)
    except PermissionError as exc:
        print(f'refused: {exc}', file=sys.stderr)
        return 2
    if args.out:
        args.out.write_text(render(receipt), encoding='utf-8')
    else:
        print(render(receipt), end='')
    return 0


if __name__ == '__main__':
    sys.exit(main())
