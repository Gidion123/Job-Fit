"""Freeze a deterministic, duplicate-safe development/test split (T03 Part 1)."""
from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261001
PILOT = {"F00016", "F00022", "F00034", "F00073", "F00114"}
ROLES = {"ai_ml_engineering", "data_science", "genai_llm", "software_ai"}
INPUTS = [
    "data/processed/jobs_features.jsonl",
    "data/interim/dedup_decisions.csv",
    "data/interim/jsearch_probable_duplicates_review.csv",
    "data/interim/snapshots/CP1_20260926/jsearch_records.jsonl",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inputs(root: Path = ROOT):
    jobs = [json.loads(line) for line in (root / INPUTS[0]).read_text().splitlines() if line.strip()]
    jobs = [j for j in jobs if j["is_auditable"] and j["role_family"] in ROLES]
    records = [json.loads(line) for line in (root / INPUTS[3]).read_text().splitlines()]
    mapping = {r["record_id"]: r["final_cluster_id"] for r in records}
    ids = {j["final_cluster_id"] for j in jobs}
    if len(jobs) != 428 or len(ids) != 428 or not PILOT <= ids:
        raise ValueError("Expected 428 distinct target jobs and all five pilot jobs")
    frozen_ids = {r["final_cluster_id"] for r in records}
    if not ids <= frozen_ids:
        raise ValueError("Feature IDs do not belong to the frozen snapshot")
    integrity = json.loads((root / "data/interim/snapshots/CP1_20260926/RESEARCH_INPUT_HASHES.json").read_text())
    expected = {item["path"]: item["sha256"] for item in integrity["inputs"]}
    if INPUTS[3] not in expected or sha(root / INPUTS[3]) != expected[INPUTS[3]]:
        raise ValueError("Frozen record mapping hash missing or changed")
    pairs = set()
    audit = Counter()
    for filename in INPUTS[1:3]:
        with (root / filename).open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("decision", "").strip().upper() == "DIFFERENT":
                    audit["different_rows_excluded"] += 1
                    continue
                a, b = row["record_a"], row["record_b"]
                if a not in mapping or b not in mapping:
                    raise ValueError(f"Unmapped duplicate pair in {filename}")
                x, y = mapping[a], mapping[b]
                if x in ids and y in ids:
                    pairs.add(tuple(sorted((x, y))))
                else:
                    audit["rows_outside_target_pool"] += 1
    return jobs, sorted(pairs), dict(audit)


def split_jobs(jobs, pairs, pilot=PILOT, seed=SEED):
    """Balance strata while keeping entire connected components together.

    Pilot placement and duplicate safety take precedence over exact balance.
    A seeded greedy assignment is improved by deterministic component moves.
    """
    by_id = {j["final_cluster_id"]: j for j in jobs}
    parent = {i: i for i in by_id}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a, b in pairs:
        if a not in parent or b not in parent:
            raise ValueError("Duplicate pair outside supplied pool")
        parent[find(a)] = find(b)
    grouped = {}
    for i in sorted(by_id):
        grouped.setdefault(find(i), []).append(i)
    groups = sorted(grouped.values(), key=lambda g: g[0])
    rng = random.Random(seed)
    rng.shuffle(groups)
    strata = {i: (j["role_family"], j["experience_bucket"]) for i, j in by_id.items()}
    totals = Counter(strata.values())
    counts = [Counter(strata[i] for i in g) for g in groups]
    forced = {n for n, g in enumerate(groups) if set(g) & set(pilot)}
    selected = set(forced)

    def count_selection(selection):
        c = Counter()
        for n in selection:
            c.update(counts[n])
        return c

    def cost(c):
        return 100 * (sum(c.values()) - len(jobs) / 2) ** 2 + sum(
            (c[s] - totals[s] / 2) ** 2 for s in totals)

    def objective(selection):
        return cost(count_selection(selection))

    for n in range(len(groups)):
        if n not in selected and objective(selected | {n}) < objective(selected):
            selected.add(n)
    # Single component moves, followed by swaps, improve stratum balance.
    while True:
        current_counts = count_selection(selected)
        current = cost(current_counts)
        best, candidate = current, None
        for n in range(len(groups)):
            if n in forced:
                continue
            proposal = selected ^ {n}
            changed = current_counts.copy()
            if n in selected:
                changed.subtract(counts[n])
            else:
                changed.update(counts[n])
            value = cost(changed)
            if value < best:
                best, candidate = value, proposal
        if candidate is None:
            for a in sorted(selected - forced):
                for b in range(len(groups)):
                    if b in selected:
                        continue
                    # Unequal sizes are handled by single moves; swaps balance strata.
                    if len(groups[a]) != len(groups[b]) or counts[a] == counts[b]:
                        continue
                    proposal = (selected - {a}) | {b}
                    changed = current_counts.copy()
                    changed.subtract(counts[a])
                    changed.update(counts[b])
                    value = cost(changed)
                    if value < best:
                        best, candidate = value, proposal
        if candidate is None:
            break
        selected = candidate
    dev = sorted(i for n in selected for i in groups[n])
    test = sorted(set(by_id) - set(dev))
    return dev, test, groups


def validate_frozen(manifest, expected, out, content):
    """Check metadata as well as bytes before accepting an existing split."""
    for key, value in expected.items():
        if key != "created_at_utc" and manifest.get(key) != value:
            raise ValueError(f"Frozen split manifest differs: {key}")
    for name, text in content.items():
        if not (out / name).exists() or (out / name).read_text() != text:
            raise ValueError("Frozen split differs from deterministic rebuild")


def main(root: Path = ROOT):
    jobs, pairs, audit = load_inputs(root)
    dev, test, groups = split_jobs(jobs, pairs)
    out = root / "evals/splits"
    content = {"dev_job_ids.txt": "".join(i + "\n" for i in dev),
               "test_job_ids.txt": "".join(i + "\n" for i in test)}
    inputs = {p: sha(root / p) for p in INPUTS}
    manifest_path = out / "split_manifest.json"
    strata = {}
    dev_set = set(dev)
    for j in jobs:
        key = j["role_family"] + " / " + j["experience_bucket"]
        row = strata.setdefault(key, {"total": 0, "development": 0, "test": 0})
        row["total"] += 1
        row["development" if j["final_cluster_id"] in dev_set else "test"] += 1
    manifest = {"snapshot_id": "CP1_20260926", "seed": SEED,
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "algorithm": "seeded component greedy with move/swap stratum balancing v1",
                "input_hashes": inputs, "total": len(jobs), "development": len(dev), "test": len(test),
                "pilot_ids": sorted(PILOT), "strata": dict(sorted(strata.items())),
                "duplicate_pairs": [list(p) for p in pairs], "duplicate_audit": audit,
                "multi_job_components": [g for g in groups if len(g) > 1],
                "output_hashes": {name: hashlib.sha256(text.encode()).hexdigest()
                                  for name, text in content.items()}}
    if manifest_path.exists():
        validate_frozen(json.loads(manifest_path.read_text()), manifest, out, content)
        print("OK: existing frozen split reproduced; no files changed")
        return
    out.mkdir(parents=True, exist_ok=True)
    for name, text in content.items():
        (out / name).write_text(text)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: manifest[k] for k in ["total", "development", "test", "strata", "multi_job_components"]}, indent=2))


if __name__ == "__main__":
    main()
