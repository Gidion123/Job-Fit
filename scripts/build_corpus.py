#!/usr/bin/env python3
"""Rebuild the deduplicated corpus snapshot and progress counts after each collection batch.

    python3 scripts/build_corpus.py

Reads archived JSearch JSON (never modifies it) and writes:
  data/interim/jsearch_records.jsonl               one row per raw slot, with provenance
  data/interim/jsearch_canonical.csv               one row per exact-key cluster (most complete record)
  data/interim/jsearch_probable_duplicates_review.csv   cross-publisher pairs for manual review
  data/research/CP1_Corpus_Progress.json           counts toward the 100 / 300 / 600 / 1,000 gates
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jobfit.jobs.corpus import build  # noqa: E402


def main() -> None:
    report = build(ROOT)
    keys = ("raw_slots", "distinct_exact_clusters", "probable_duplicate_pairs", "pairs_reviewed",
            "pairs_merged_same", "distinct_final", "auditable_candidates_full_jd")
    for k in keys:
        print(f"{k:40s} {report[k]}")
    for k in ("jd_quality_canonical", "auditable_by_geo", "auditable_by_role_provisional", "auditable_by_seniority_provisional"):
        print(f"{k:40s} {json.dumps(report[k], ensure_ascii=False)}")
    print("by batch (first seen):")
    for b, v in report["by_batch_first_seen"].items():
        print(f"  {b:10s} responses={v['responses']:3d} slots={v['slots']:4d} new_clusters={v['new_clusters']:4d}")


if __name__ == "__main__":
    main()
