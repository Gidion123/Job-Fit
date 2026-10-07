"""Compare old and D-067 SQL references on identical saved development outputs."""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from jobfit.eval.matching_evaluation import reference_rows
from jobfit.eval.metrics import evidence_metrics
from jobfit.matching.guardrails import apply_guardrails
from jobfit.scoring.score import effective_label
from jobfit.schemas.analysis import CheckStatus, UnitAssessment
from scripts.run_cp23_stage2_matching import inputs

VALIDATED = ROOT / "evals/results/cp23_stage2_validator_v11_20261004_v2.json"
REFERENCE = ROOT / "evals/results/cp23_f00815_sql_reference_20261004_v2.json"
OUT = ROOT / "evals/results/cp23_sql_reference_comparison_20261004_v2.json"
BUNDLE = ROOT / "evals/gold/development_v13_reviewed_20261003_stage1_r3"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    validated, reference = read(VALIDATED), read(REFERENCE)
    assert reference["original_gold_unchanged"] and reference["new_reference"]["evidence_label"] == "MATCH"
    plans = {
        "round_one_B": read(ROOT / "evals/results/cp23_stage2_fixed_matching_20261003_v1_plan.json")["stages"],
        "reference_round_two": read(ROOT / "evals/results/cp23_stage2_reference_round2_20261003_v1_plan.json")["stages"],
    }
    report = {}
    for scope, stages in plans.items():
        by_sid = {s["stage_id"]: s for s in stages if scope == "round_one_B" or s.get("kind") == "matching"}
        truth = {}
        predictions = defaultdict(dict)
        guarded_predictions = defaultdict(dict)
        old_guarded_predictions = defaultdict(dict)
        valid_prefixes = defaultdict(set)
        for result in (r for r in validated["stages"] if r["scope"] == scope):
            stage = by_sid[result["stage_id"]]
            cv, extraction = inputs(stage)
            prefix = f"{stage['cv_id']}/{stage['job_id']}/"
            for unit, label in reference_rows(BUNDLE, stage, cv, extraction).items():
                truth[prefix + unit] = label
            if result["after_status"] != "done":
                continue
            valid_prefixes[stage["model"]].add(prefix)
            units = {u.unit_id: u for u in extraction.units}
            for raw in result["source_grounded_assessments"]:
                unit = units[raw["unit_id"]]
                value, status = effective_label(unit, UnitAssessment.model_validate(raw))
                predictions[stage["model"]][prefix + unit.unit_id] = {
                    "label": value.value if value and status == CheckStatus.DONE else None,
                    "status": status.value}
                guard_unit = unit.model_dump(mode="json")
                old_adjusted, _ = apply_guardrails(guard_unit, raw, cv.profile.raw_text)
                old_value, old_status = effective_label(unit, UnitAssessment.model_validate(old_adjusted))
                old_guarded_predictions[stage["model"]][prefix + unit.unit_id] = {
                    "label": old_value.value if old_value and old_status == CheckStatus.DONE else None,
                    "status": old_status.value}
                # D-067 treats PostgreSQL as an example of SQL. The historical
                # fixed adapter says SQL/PostgreSQL, which otherwise triggers G2
                # as though both named tools were independently mandatory.
                # Adapt this one evaluation view without editing gold or source.
                if stage["job_id"] == "F00815" and unit.unit_id == "P52-U10":
                    guard_unit["text"] = "SQL (PostgreSQL example)"
                adjusted, _ = apply_guardrails(guard_unit, raw, cv.profile.raw_text)
                value, status = effective_label(unit, UnitAssessment.model_validate(adjusted))
                guarded_predictions[stage["model"]][prefix + unit.unit_id] = {
                    "label": value.value if value and status == CheckStatus.DONE else None,
                    "status": status.value}
        key = "CV2/F00815/P52-U10"
        assert truth[key] == reference["old_reference"]["evidence_label"]
        changed_truth = dict(truth)
        changed_truth[key] = reference["new_reference"]["evidence_label"]
        report[scope] = {}
        for model in sorted({s["model"] for s in by_sid.values()}):
            row = {}
            for reference_name, labels in (("old", truth), ("new", changed_truth)):
                guard_predictions = (old_guarded_predictions if reference_name == "old"
                                     else guarded_predictions)
                answered = {k: v for k, v in labels.items()
                            if any(k.startswith(prefix) for prefix in valid_prefixes[model])}
                row[reference_name] = {
                    "all_cases": evidence_metrics(labels, predictions[model], alignment_verified=True),
                    "answered_cases_only": evidence_metrics(answered, predictions[model], alignment_verified=True)
                        if answered else None,
                    "all_cases_guarded": evidence_metrics(labels, guard_predictions[model], alignment_verified=True),
                    "answered_cases_only_guarded": evidence_metrics(answered, guard_predictions[model], alignment_verified=True)
                        if answered else None,
                }
            report[scope][model] = row
    return {"schema_version": "cp23-sql-reference-comparison-v2", "date": "2026-10-04",
            "old_and_new_reference_applied_to_every_model": True, "gold_changed": False,
            "guardrail_adapter": "F00815 P52-U10 is SQL with PostgreSQL as an example under D-067; G2 does not treat both as mandatory",
            "api_calls": 0, "truth_change": {"key": "CV2/F00815/P52-U10", "old": "PARTIAL", "new": "MATCH"},
            "results": report,
            "input_sha256": {str(p.relative_to(ROOT)): sha(p) for p in (VALIDATED, REFERENCE)}}


if __name__ == "__main__":
    output = build()
    with OUT.open("x") as file:
        json.dump(output, file, indent=2)
    for scope, models in output["results"].items():
        for model, values in models.items():
            print(scope, model,
                  round(values["old"]["all_cases_guarded"]["macro_f1"], 6),
                  round(values["new"]["all_cases_guarded"]["macro_f1"], 6))
