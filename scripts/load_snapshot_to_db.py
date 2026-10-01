"""Loads the CP1 snapshot (632 EDA candidates) into the local PostgreSQL database.

Usage (database running with `docker compose up -d db`):
    python scripts/load_snapshot_to_db.py
Safe to run again: existing rows are updated in place.
"""
from __future__ import annotations

import json
import sys

from jobfit.db.load_snapshot import EXPECTED, load, read_candidates, summarize
from jobfit.db.session import connect


def main() -> int:
    rows = read_candidates()
    print("Read from snapshot:", json.dumps(summarize(rows)))
    with connect() as conn:
        result = load(conn, rows)
    print("Loaded into PostgreSQL:", json.dumps(result))
    if not result["matches_cp1"]:
        print(f"WARNING: expected {EXPECTED['eda_candidates']} rows and {EXPECTED['target']} target jobs.")
        return 1
    print("OK: matches the CP1 numbers (632 EDA candidates, 428 target).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
