#!/usr/bin/env python3
"""Run any JSearch batch manifest using verified Free/Basic quota only.

Usage:
    python3 scripts/run_jsearch_batch.py data/research/CP1_JSearch_Batch03_Plan.json
    python3 scripts/run_jsearch_batch.py data/research/CP1_JSearch_Batch03_Plan.json --dry-run

The request cap is read from the manifest's "max_requests". The key is read through a
hidden prompt, passed only to the child process environment, and never written to disk.
"""

import getpass
import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        raise SystemExit("Usage: python3 scripts/run_jsearch_batch.py <plan.json> [--dry-run]")
    plan = (root / args[0]).resolve() if not Path(args[0]).is_absolute() else Path(args[0])
    manifest = json.loads(plan.read_text(encoding="utf-8"))
    cap = int(manifest["max_requests"])
    command = [sys.executable, str(root / "scripts/jsearch_collection.py"), "collect",
               "--plan", str(plan), "--max-requests", str(cap)]
    if manifest.get("free_only", True):
        command.append("--free-only")
    if "--dry-run" in sys.argv:
        raise SystemExit(subprocess.run(command, check=False).returncode)
    if not sys.stdin.isatty():
        raise SystemExit("Run interactively in Terminal. No key requested or saved.")
    if not manifest.get("free_only", True):
        price = float(manifest.get("price_per_request_usd", 0.005))
        print(f"PAID batch: up to {cap} requests; at the published PAYG rate of US${price}/request "
              f"that is at most about US${cap * price:.2f} (excluding tax). Check your plan in the account first.")
        if input(f"Type {cap} to confirm, anything else to cancel: ").strip() != str(cap):
            raise SystemExit("Cancelled; no key requested, no requests sent.")
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
