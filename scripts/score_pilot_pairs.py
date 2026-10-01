"""Score v1 on the approved pilot labels (development split).

Uses the gold extraction and evidence labels as the input, so the result shows what the
scoring rules give when extraction and matching are correct. It is not a system output.
Writes evals/results/cp21_pilot_scores.json.

Usage: python scripts/score_pilot_pairs.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from jobfit.schemas.analysis import UnitAssessment
from jobfit.schemas.requirements import JDExtraction, RequirementUnit
from jobfit.scoring.score import compute_score

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "evals" / "gold"
OUT = ROOT / "evals" / "results" / "cp21_pilot_scores.json"


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    units = load_jsonl(GOLD / "extraction_gold.jsonl")
    evidence = load_jsonl(GOLD / "evidence_gold.jsonl")
    with open(GOLD / "relevance_gold.csv", encoding="utf-8") as f:
        relevance = {(r["cv_id"], r["job_id"]): int(r["relevance"]) for r in csv.DictReader(f)}

    pairs = sorted({(r["cv_id"], r["job_id"]) for r in evidence})
    results = []
    for cv_id, job_id in pairs:
        extraction = JDExtraction(job_id=job_id, units=[
            RequirementUnit(unit_id=u["unit_no"], text=u["unit_text"], importance=u["importance"],
                            field=u["category"], min_years=u["min_years"])
            for u in units if u["job_id"] == job_id])
        assessments = [
            UnitAssessment(unit_id=e["unit_no"], label=e["label"], check_status=e["check_status"],
                           cv_quotes=[e["cv_quote"]] if e["cv_quote"] else [])
            for e in evidence if e["cv_id"] == cv_id and e["job_id"] == job_id]
        row = {"cv_id": cv_id, "job_id": job_id, "relevance_label": relevance.get((cv_id, job_id))}
        for name, flag in (("score_v1", False), ("soft_skills_in_score", True)):
            r = compute_score(extraction, assessments, soft_skills_in_score=flag)
            row[name] = {"score_pct": r.score_pct, "status": r.status.value, "matched": r.matched,
                         "partial": r.partial, "required_total": r.required_total,
                         "soft_skill_total": r.soft_skill_total, "soft_skill_matched": r.soft_skill_matched,
                         "soft_skill_partial": r.soft_skill_partial, "preferred_met": r.preferred_met,
                         "preferred_total": r.preferred_total,
                         "unknown_importance_total": r.unknown_importance_total,
                         "constraint_units_total": r.constraint_units_total}
        results.append(row)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"input": "evals/gold (development split)", "pairs": results}, indent=2), encoding="utf-8")
    for row in results:
        print(row["cv_id"], row["job_id"], "relevance", row["relevance_label"],
              "| v1", row["score_v1"]["score_pct"], row["score_v1"]["status"],
              "| soft skills in", row["soft_skills_in_score"]["score_pct"])


if __name__ == "__main__":
    main()
