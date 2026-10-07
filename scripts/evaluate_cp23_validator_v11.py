"""Offline D-066 matching revalidation; never calls a provider or edits saved runs."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from jobfit.eval.matching_evaluation import reference_rows
from jobfit.eval.metrics import evidence_metrics
from jobfit.matching.evidence_matcher import EvidenceResponse, match_evidence
from jobfit.matching.guardrails import apply_guardrails
from jobfit.matching.quote_check_v11 import normalize_assessments_v11
from jobfit.scoring.score import effective_label
from jobfit.schemas.analysis import CheckStatus, UnitAssessment
from scripts.run_cp23_stage2_matching import inputs


ROUND = "cp23_stage2_fixed_matching_20261003_v1"
REPLAY = "cp23_stage2_repair_rerun_20261004_v1"
FOLLOW = "cp23_stage2_reference_round2_20261003_v1"
OUT = ROOT / "evals/results/cp23_stage2_validator_v11_20261004_v2.json"


def load(path: Path):
    return json.loads(path.read_text())


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OfflineClient:
    def __init__(self, assessments):
        self.assessments = assessments
        self.calls = 0

    def chat_structured(self, model, messages, output_model, task, **kwargs):
        self.calls += 1
        return EvidenceResponse.model_validate({"assessments": self.assessments})


def stages_for(run: str):
    plan_path = ROOT / "evals/results" / f"{run}_plan.json"
    state_path = ROOT / "reports/quality_probe" / f"{run}.json"
    plan, state = load(plan_path), load(state_path)
    return plan, state, plan_path, state_path


def build():
    round_plan, round_state, round_plan_path, round_state_path = stages_for(ROUND)
    follow_plan, follow_state, follow_plan_path, follow_state_path = stages_for(FOLLOW)
    replay_path = ROOT / "reports/quality_probe" / f"{REPLAY}.json"
    replay_state = load(replay_path)
    replay_by_id = {r["stage_id"]: r for r in replay_state["results"] if "CV" in r["stage_id"]}
    original_by_id = {r["stage_id"]: r for r in round_state["results"]}
    follow_by_id = {r["stage_id"]: r for r in follow_state["results"]}
    rows = []
    truth_by_scope = defaultdict(dict)
    predictions = defaultdict(lambda: defaultdict(dict))
    predictions_guarded = defaultdict(lambda: defaultdict(dict))

    for scope, plan, state, saved in (
        ("round_one_B", round_plan, round_state, original_by_id),
        ("reference_round_two", follow_plan, follow_state, follow_by_id),
    ):
        for stage in plan["stages"]:
            if scope == "reference_round_two" and stage.get("kind") != "matching":
                continue
            sid = stage["stage_id"]
            original = saved[sid]
            selected = replay_by_id.get(sid, original) if scope == "round_one_B" else original
            cv, extraction = inputs(stage)
            truth = reference_rows(ROOT / "evals/gold/development_v13_reviewed_20261003_stage1_r3", stage, cv, extraction)
            pair_prefix = f"{stage['cv_id']}/{stage['job_id']}/"
            for uid, label in truth.items():
                truth_by_scope[scope][pair_prefix + uid] = label
            # A replay contains the final typed repair. A stopped/invalid output
            # without typed content is never reconstructed from an imagined answer.
            raw = (selected.get("typed_repair", {}).get("assessments")
                   if selected is not original and selected.get("typed_repair") else None)
            if raw is None and selected.get("status") == "done":
                raw = selected.get("assessments")
            if raw is None:
                typed = [r for r in state.get("typed_attempt_outputs", []) if r["stage_id"] == sid]
                if typed:
                    raw = max(typed, key=lambda r: r["attempt"])["output"].get("assessments")
            record = {"scope": scope, "stage_id": sid, "model": stage["model"],
                      "cv_id": stage["cv_id"], "job_id": stage["job_id"],
                      "before_status": selected.get("status"), "before_error": selected.get("error_code"),
                      "after_status": "failed", "after_error": None, "flags": [],
                      "source_grounded_assessments": None, "answered_units": 0,
                      "reference_units": len(truth), "api_calls": 0}
            if raw is None:
                record["after_error"] = "missing_saved_typed_final_output"
                rows.append(record)
                continue
            try:
                normalized, flags = normalize_assessments_v11(raw,
                    [u.model_dump(mode="json") for u in extraction.units], cv.profile.raw_text)
                if any(a.get("label_source") != "model_draft" for a in normalized):
                    raise ValueError("model_cannot_claim_annotator")
                client = OfflineClient(normalized)
                check = match_evidence(cv, extraction, client=client,
                    model=stage["model"], duration_years=stage.get("duration_input", {}))
                record["flags"] = flags
                record["after_status"] = check.status
                record["after_error"] = check.error_code
                if check.status == "done":
                    record["source_grounded_assessments"] = normalized
                    for a in normalized:
                        unit = next(u for u in extraction.units if u.unit_id == a["unit_id"])
                        value, status = effective_label(unit, UnitAssessment.model_validate(a))
                        key = pair_prefix + a["unit_id"]
                        prediction = {"label": value.value if value and status == CheckStatus.DONE else None,
                                      "status": status.value}
                        predictions[scope][stage["model"]][key] = prediction
                        guarded, changes = apply_guardrails(unit.model_dump(mode="json"), a, cv.profile.raw_text)
                        value_g, status_g = effective_label(unit, UnitAssessment.model_validate(guarded))
                        predictions_guarded[scope][stage["model"]][key] = {
                            "label": value_g.value if value_g and status_g == CheckStatus.DONE else None,
                            "status": status_g.value}
                        record["answered_units"] += int(prediction["label"] is not None)
                        for change in changes:
                            record["flags"].append({"kind": "G1_G2", **change})
            except ValueError as exc:
                record["after_error"] = str(exc) if str(exc) in {
                    "assessment_coverage", "ambiguous_source_span", "changed_or_invented_word",
                    "ambiguous_parent_group_label", "unresolved_parent_with_labeled_branches",
                    "empty_quote", "empty_quote_tokens", "model_cannot_claim_annotator"} else type(exc).__name__
            rows.append(record)

    summary = {}
    for scope in ("round_one_B", "reference_round_two"):
        models = sorted({r["model"] for r in rows if r["scope"] == scope})
        summary[scope] = {}
        for model in models:
            own = [r for r in rows if r["scope"] == scope and r["model"] == model]
            answered_prefixes = {f"{r['cv_id']}/{r['job_id']}/" for r in own if r["after_status"] == "done"}
            complete_truth = truth_by_scope[scope]
            answered_truth = {k: v for k, v in complete_truth.items()
                              if any(k.startswith(prefix) for prefix in answered_prefixes)}
            pred = predictions[scope][model]
            guarded = predictions_guarded[scope][model]
            summary[scope][model] = {
                "stages_before": sum(r["before_status"] == "done" for r in own),
                "stages_after": sum(r["after_status"] == "done" for r in own),
                "stage_count": len(own),
                "all_cases": evidence_metrics(complete_truth, pred, alignment_verified=True),
                "answered_cases_only": evidence_metrics(answered_truth, pred, alignment_verified=True)
                    if answered_truth else None,
                "all_cases_guarded": evidence_metrics(complete_truth, guarded, alignment_verified=True),
                "answered_cases_only_guarded": evidence_metrics(answered_truth, guarded, alignment_verified=True)
                    if answered_truth else None,
                "answered_cases": sum(r["after_status"] == "done" for r in own),
                "normalized_quote_count": sum(f["kind"] == "quote_normalized" for r in own for f in r["flags"]),
                "unique_parent_moves": sum(f["kind"] == "parent_moved_unique_branch" for r in own for f in r["flags"]),
            }
    return {"schema_version": "cp23-validator-v11-offline-v1", "date": "2026-10-04",
            "run_id": "cp23_stage2_validator_v11_20261004_v2", "scope": "saved development outputs only",
            "api_calls": 0, "validator_default_changed": False,
            "summary": summary, "stages": rows,
            "hashes": {str(p.relative_to(ROOT)): sha(p) for p in
                       (round_plan_path, round_state_path, follow_plan_path, follow_state_path, replay_path,
                        ROOT / "src/jobfit/matching/quote_check_v11.py", Path(__file__))},
            "limits": ["Raw model quotes and original saved outputs remain unchanged.",
                       "A source span is accepted only when its lexical tokens are contiguous and identical.",
                       "Answered-case metrics exclude invalid stages and must never replace all-case metrics.",
                       "G1/G2 coverage is bounded; semantic unsupported-positive review remains separate."]}


if __name__ == "__main__":
    result = build()
    with OUT.open("x") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    for scope, models in result["summary"].items():
        for model, item in models.items():
            print(scope, model, item["stages_before"], item["stages_after"],
                  item["all_cases"]["macro_f1"])
