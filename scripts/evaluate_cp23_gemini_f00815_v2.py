"""Apply Dion's D-054/D-061/D-067 adjudication to repaired Gemini F00815.

This is assisted alignment acceptance on development data. It never edits gold.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from jobfit.eval.metrics import extraction_metrics

PROPOSAL = ROOT / "evals/results/cp23_stage2_repair_comparison_20261004_v2.json"
REPAIR = ROOT / "evals/results/cp23_stage2_repair_rerun_20261004_v1_08.json"
BASE = ROOT / "evals/results/cp23_stage2_round1_quality_evaluation_20261003_v1.json"
OUT = ROOT / "evals/results/cp23_gemini_f00815_alignment_20261004_v1.json"


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    proposal = read(PROPOSAL)["new_extraction_QA"]
    repaired = read(REPAIR)
    base = read(BASE)["extraction"]["gemini-3.5-flash-lite"]
    assert proposal["stage_id"] == repaired["stage_id"] == "gemini-3.5-flash-lite/F00815"
    assert repaired["status"] == "done"
    model_ids = [u["unit_id"] for u in repaired["extraction"]["units"]]
    assert len(model_ids) == 18
    rows = []
    for mapping in proposal["mappings"]:
        g, m = mapping["gold_ids"], mapping["model_ids"]
        equivalent = mapping["recommended_semantic_equivalent"]
        if g == ["P52-U10"]:
            # D-067: PostgreSQL is an SQL example; the model's SQL/PG route
            # preserves the assessable SQL requirement for this comparison.
            assert m == ["U11"] and mapping["relation"] == "one_to_one"
            equivalent = True
        if g in (["P52-U09"], ["P52-U12"]):
            assert mapping["relation"] == "split" and equivalent is False
        rows.append({"gold_ids": g, "model_ids": m, "status": "verified",
                     "semantic_equivalent": equivalent, "relation": mapping["relation"],
                     "note": mapping["note"]})
    gold_ids = [gid for row in rows for gid in row["gold_ids"]]
    assert len(gold_ids) == len(set(gold_ids)) == 16
    assert set(model_ids) == {mid for row in rows for mid in row["model_ids"]}
    alignment = {"human_verified": True, "verification_method": "Dion accepted strict D-054/D-061/D-067 assisted adjudication",
                 "gold_unit_ids": gold_ids, "model_unit_ids": model_ids,
                 "unmapped_gold": [], "unmapped_model": [], "rows": rows}
    case = extraction_metrics(alignment, reference_complete=True)
    assert (case["tp"], case["fp"], case["fn"]) == (14, 4, 2)
    assert (base["tp"], base["fp"], base["fn"]) == (69, 36, 51)
    total = {"tp": base["tp"] + case["tp"], "fp": base["fp"] + case["fp"],
             "fn": base["fn"] - 16 + case["fn"]}
    assert total["tp"] + total["fn"] == 120
    total["precision"] = total["tp"] / (total["tp"] + total["fp"])
    total["recall"] = total["tp"] / (total["tp"] + total["fn"])
    total["f1"] = 2 * total["tp"] / (2 * total["tp"] + total["fp"] + total["fn"])
    return {"schema_version": "cp23-gemini-f00815-alignment-v1", "date": "2026-10-04",
            "split": "development", "acceptance": "Dion requested the same strict D-054/D-061 mapping; D-067 governs SQL",
            "gold_changed": False, "api_calls": 0,
            "case": {"stage_id": proposal["stage_id"], "gold_units": 16, "model_units": 18,
                     "tp": case["tp"], "fp": case["fp"], "fn": case["fn"],
                     "f1": case["f1"]["value"], "rows": rows},
            "seven_jd_old": {"tp": base["tp"], "fp": base["fp"], "fn": base["fn"], "f1": base["f1"]},
            "seven_jd_new": total,
            "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in (PROPOSAL, REPAIR, BASE)}}


if __name__ == "__main__":
    value = build()
    with OUT.open("x") as stream:
        json.dump(value, stream, indent=2)
    print(value["case"]["tp"], value["case"]["fp"], value["case"]["fn"], value["case"]["f1"])
    print(value["seven_jd_new"])
