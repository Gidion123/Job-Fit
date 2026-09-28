#!/usr/bin/env python3
"""Prompt locally for a JSearch key without displaying or saving it, then run 12 capped queries."""

import getpass
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    if not sys.stdin.isatty():
        raise SystemExit("Run this interactively in Terminal; no key was requested or saved.")
    key = getpass.getpass("Paste your OpenWeb Ninja JSearch API key (hidden): ").strip()
    if not key:
        raise SystemExit("Empty key; no requests sent.")
    env = os.environ.copy()
    env["JSEARCH_API_KEY"] = key
    script = Path(__file__).with_name("jsearch_collection.py")
    try:
        completed = subprocess.run(
            [sys.executable, str(script), "collect", "--pilot", "--free-only", "--execute", "--max-requests", "12"],
            env=env, check=False,
        )
    finally:
        env.pop("JSEARCH_API_KEY", None)
        key = ""
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
