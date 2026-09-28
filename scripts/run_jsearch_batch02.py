#!/usr/bin/env python3
"""Run the 12-query adaptive batch using verified Free/Basic quota only."""

import getpass
import os
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    command = [sys.executable, str(root / "scripts/jsearch_collection.py"),
               "collect", "--plan", str(root / "data/research/CP1_JSearch_Batch02_Plan.json"),
               "--free-only", "--max-requests", "12"]
    if "--dry-run" in sys.argv:
        raise SystemExit(subprocess.run(command, check=False).returncode)
    if not sys.stdin.isatty():
        raise SystemExit("Run interactively in Terminal. No key requested or saved.")
    key = getpass.getpass("Paste your OpenWeb Ninja JSearch API key (hidden): ").strip()
    if not key:
        raise SystemExit("Empty key; no requests sent.")
    env = os.environ.copy()
    env["JSEARCH_API_KEY"] = key
    try:
        result = subprocess.run(command + ["--execute"], env=env, check=False)
    finally:
        env.pop("JSEARCH_API_KEY", None)
        key = ""
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
