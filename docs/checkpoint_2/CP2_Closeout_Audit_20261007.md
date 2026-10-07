# CP2 Closeout Audit

**Date:** 7 October 2026. **Branch:** `cp2-closeout-20261007`, audited at commit `8ca6b41`. **Model calls:** none. **Scope:** CP2.1 to CP2.7 acceptance against the [master plan](../master-plan.md), plus the CP2.8 post-test extension. Frozen artifacts were read and hash-checked, never edited.

## 1. Verdict

**CP2 — NOT YET CLOSED.**

The technical work of CP2 is complete and reproducible: the configuration was frozen (D-087), the held-out test ran, its report reproduces exactly from the saved labels, and the figures and tables match their receipts byte for byte. CP2 cannot be marked closed for two reasons, and both need Dion:

1. **CP2.7 has no saved evidence** of a rehearsal, the mentor session, mentor feedback, a decision entry sourced from that feedback, or LMS upload proof (section 5).
2. **Two CP2.3 carry-overs have no approved disposition**: the D-050 broad development extraction and the D-051 paired masked-input comparison. Both are written as acceptance items, and no decision accepts their reduced scope (section 4). Closing either one by doing the work would need paid inference, which this offline closeout must not run. Closing it by decision is Dion's call.

The short human checklist is in section 9.

## 2. Status of each stage

| Stage | Status after the audit | Basis |
| --- | --- | --- |
| CP2.1 Model and System Selection | DONE | Section 3 |
| CP2.2 Modeling Pipeline | DONE under D-050 | Section 3 |
| CP2.3 System Tuning | DONE for development tuning and freeze (D-086, D-087); two carry-overs without an approved disposition | Section 4 |
| CP2.4 Evaluation Metrics | DONE (`cp24-report-contract-v1`) | Section 6 |
| CP2.5 Evaluation Visualization | DONE | Section 7 |
| CP2.6 Recommendation and Summary | DONE | Section 3 |
| CP2.7 Presentation and Mentoring | IN PROGRESS, blocks closure | Section 5 |
| CP2.8 Phase A (post-test, development only) | CLOSED, KEEP BASELINE (D-090) | Section 8 |

## 3. Requirements-to-evidence matrix

Requirement source: `docs/master-plan.md` section 8, the "Tests and acceptance criteria" and "Evidence to keep" of each stage, plus the D-051 privacy table at the top of the master plan. Status values: PASS, PARTIAL, MISSING, NOT REQUIRED / DEFERRED (only when a valid decision says so). A stage report's DONE was never accepted alone; every PASS below points to a file that exists in this commit.

### CP2.1 (checkpoint 8)

| Requirement | Status | Evidence | Note, limitation | Blocks closure |
| --- | --- | --- | --- | --- |
| Guideline v1 with a version number | PASS | `evals/annotation_guideline_v1.md` (v1.2), later `evals/annotation_guideline_v1_3.md` (D-049) | | No |
| Schemas defined | PASS | `src/jobfit/schemas/` | | No |
| Scoring rules pass the 8 development fixtures | PASS | `tests/test_scoring.py`, `evals/fixtures/`; passes in this audit (section 10) | Fixtures test the code, not the rules | No |
| Pilot time per item recorded and used for gold sizes | PASS | Pilot workbook timing sheet; D-043, superseded by D-045 (approved 1 Oct) | The CP2.1 report still lists D-043/D-044 as pending; that is historical, both were resolved | No |
| B0 and B1 run on the pilot pool, outputs saved | PASS | `evals/results/cp21_baselines.json`, EXP-20261001-01 | Recall@K not computable on the pilot (one relevance-3 pair) | No |
| Experiment matrix with a hypothesis and metric per candidate | PASS | `docs/experiments.md` M01 to M12 | | No |
| Ledger and budget guard before the first LLM call; every call logged | PASS | `src/jobfit/llm/`, `tests/test_budget_guard.py`, `reports/usage/usage_ledger.jsonl` (780 records, US$10.528495 at this audit) | Ledger includes US$0.2489 of uncertain upper-bound reservations | No |

### CP2.2 (checkpoint 9)

| Requirement | Status | Evidence | Note, limitation | Blocks closure |
| --- | --- | --- | --- | --- |
| One CV and one pasted JD give a structured report with exact CV quotes | PASS | `evals/results/cp22_extraction_repair_v13_20261003_04_semantic_repair.json`, `cp22_repair_semantic_review_20261003.json` | Assisted operational acceptance after three bounded repairs, not unattended quality | No |
| 8 development cases pass the manual check | PASS | `evals/fixtures/v1_3/`, [acceptance review](supporting/CP22_Acceptance_Review_20261002.md) | Delegated review, not eight independent human approvals (stated in the report) | No |
| Cache keys include schema, prompt, model, preprocessing and guideline versions | PASS | CP2.2 report section 3; cache tests in the offline suite | | No |
| Planned-scale development extraction | NOT REQUIRED for CP2.2 by D-050 | D-050 moved it to CP2.3 as an explicit carry-over | See CP2.3 | No (for CP2.2) |
| Test split locked before checkpoint 10 | PASS | `evals/splits/dev_job_ids.txt`, `test_job_ids.txt` (214 / 214, T03 1 Oct); both hashes are in the D-087 receipt and verify | | No |

### CP2.3 (checkpoint 10)

| Requirement | Status | Evidence | Note, limitation | Blocks closure |
| --- | --- | --- | --- | --- |
| Every change has a development before/after and a keep/remove decision | PASS | EXP-20261003 to EXP-20261006-R4; D-044, D-065 to D-086 | Two development CVs only | No |
| Test set not used for tuning | PASS | D-087 frozen before any test processing; `freeze_receipt_APPROVED.json`; `prepare_cp23_freeze.py --verify` ok | | No |
| Spend within the budget guard | PASS | Ledger US$10.53 against the US$18.5 hard stop (D-070) | | No |
| Stage-1 method, K, prompt and model recorded under the D-029 rule (as amended by D-066) | PASS | D-044 (Qwen), D-083 (Sol matching, Luna fallback), D-077 (DeepSeek Flash extraction), D-078/D-086 (K 10, weight 0.5, seniority rule), D-084 (Hybrid Qwen kept), D-087 (freeze) | Earlier provisional choices D-068 (DeepSeek matching, K 20) were superseded, not deleted | No |
| Freeze prepared and approved (D-053) | PASS | `evals/freeze/cp23_freeze_draft_v2/` (57 file hashes; receipt sha256 `18c1d17c…`), D-087 | | No |
| D-050 carried extraction: auditable per-JD status and executed scope, or an approved revised disposition | **PARTIAL** | Per-JD inventory for all 214 development JDs on 3 Oct (`evals/results/cp22_development_extraction_plan_20261003.json`, 212 not run); per-JD status for the executed scope of 52 JDs (Hybrid Qwen top 30 of CV1/CV2: 51 attempted, 48 process-valid; `evals/results/cp23/pipeline_v11/coverage_summary_v2.json`) | 162 development JDs were never extracted. The frozen design extracts only the analyzed top K, so full materialization was not needed for CP2.4, but no decision accepts this reduced scope. The CP2.3 report itself said not to mark DONE until this is satisfied or accepted | **Yes**: needs Dion's decision |
| D-051 CP2.3 privacy work: masking/consent boundary, session primitives, synthetic CV1/CV2 masking impact | **PARTIAL** | `src/jobfit/privacy/masking.py`; `tests/test_privacy_controls.py`, `test_cp23_masking_quotes.py`, `test_cp23_masking_pairs_preflight.py`; mechanical quote check `evals/results/cp23_masking_quote_compatibility_20261004_v1.json` (13 changed rows, all traceable) | The paired original-versus-masked matching comparison ("versioned tests/paired results" in the master-plan privacy table) was prepared but not run; the CP2.3 report calls it "deferred" without a decision. Real-CV processing stays disabled (`/cv/parse` answers 403), so no privacy claim depends on it | **Yes**: needs Dion's decision |

### CP2.4 (checkpoint 11)

| Requirement | Status | Evidence | Note, limitation | Blocks closure |
| --- | --- | --- | --- | --- |
| Approved freeze before held-out processing | PASS | D-087; `freeze_receipt_APPROVED.json` (`approval.decision = D-087`) | | No |
| Reviewed test labels used as ground truth | PASS with disclosed deviation | `evals/gold/test_v13_cp24_r1/` (67 judged, 1 held), D-088 | AI-assisted (ChatGPT), human-reviewed by one reviewer, blind to ranking. Not independent human gold. Deviates from the D-053 "no model suggestions" wording; D-088 records the correction | No |
| Original-position P@5 / NDCG@10 with coverage, common pool and paired CVs | PASS | `evals/results/cp24/heldout_report_v1.json` (section 6) | | No |
| No "good" claim without a metric | PASS | CP2.4 report sections 10, 10b, 11 | | No |
| Each result records git SHA, prompt and model versions, cost and latency | PASS with limitation | Freeze receipt hashes, config v4, cost/latency table in CP2.4 10b | The report names HEAD `8cfb359d` because the files were not yet committed; the artifacts were first committed in `8ca6b41` (7 Oct). The 57 freeze hashes, not the SHA, identify the evaluated files | No |
| Limitations written (single annotator, gold size, synthetic CVs, snapshot) | PASS | CP2.4 section 11 | | No |
| Safety: hard negatives in top 10, quote validity | PASS | `evals/results/cp24/supplementary_v2/summary.json`: 519/519 positive items quote the CV; one relevance-0 job in any final top 10 (CV3/F00501) | Unsupported claims need unit-level test evidence gold: not measurable | No |
| Latency p50/p95 and cost, live and cached | PASS | CP2.4 10b; ledger run IDs `cp24_test_*` total US$1.442 | | No |
| Failure examples in `docs/failures.md` | PASS | FAIL-32, FAIL-33, FAIL-34 | | No |
| Evidence Macro-F1 and extraction F1 on test | DEFERRED by D-045 | D-045 "What is reported when": CP2.4 reports extraction and evidence metrics on development gold; test extraction and evidence go to the final report (CP3.5) | D-088 imported only the C sheet, so this CP3.5 dependency is still open | No (CP3.5) |

### CP2.5 (checkpoint 12)

| Requirement | Status | Evidence | Note, limitation | Blocks closure |
| --- | --- | --- | --- | --- |
| Stage-1 comparison chart (Recall@K per method) | PASS | `reports/figures/cp2/fig01_retrieval_methods.png` (development) | | No |
| NDCG@10 and P@5, stage 1 versus final | PASS | fig09 (headline CV3-CV5), fig10 (CV1-CV2 supplementary), fig11 (post-hoc decomposition) | | No |
| Evidence confusion matrix | PASS (development) | fig04 | Test evidence gold deferred (D-045) | No |
| Quality vs cost vs latency | PASS | fig06 (development); CP2.4 10b table (test) | | No |
| Hard-negative and failure cases | PASS | CP2.5 short-case table | | No |
| Every chart shows configuration, version and denominator | PASS with limitation | fig09-fig11 captions carry split, coverage and the D-088 disclosure; fig01-fig08 captions/report | Phase A figures A1-A4 carry denominators only in the CP2.5/CP2.8 text | No |
| Same split, same labels in each comparison | PASS | `evals/results/cp24/cp25_tables_v1/receipt.json`; all 16 input/output hashes match | | No |
| Script that makes the figures saved | PASS | `scripts/build_cp2_figures.py`; `notebooks/02_cp2_heldout_evaluation.ipynb`; `notebooks/03_post_test_quality_optimization.ipynb` | | No |

### CP2.6 (checkpoint 13)

| Requirement | Status | Evidence | Note, limitation | Blocks closure |
| --- | --- | --- | --- | --- |
| Error analysis by category | PASS | CP2.6 development error analysis; test error table added in this audit from `supplementary_v2/summary.json` | Filter misses not measurable (no optional filter in the test run) | No |
| Final stage-1 method, K, model, prompt, PARTIAL weight | PASS | D-086, D-087, CP2.6 final summary | | No |
| Keep/remove decisions for everything tested | PASS | Final keep/remove table added to CP2.6 in this audit, each row traced to a decision | | No |
| Limitations and next-version ideas | PASS | CP2.6 final summary | | No |
| Architecture v1 diagram | PASS (added in this audit) | Mermaid diagram in CP2.6, built only from the D-087 freeze receipt | Not present before this audit | No |
| Final architecture explained as consequences of the experiments | PASS | CP2.6 final summary and keep/remove table | | No |

### CP2.7 (checkpoint 14)

| Requirement | Status | Evidence | Note, limitation | Blocks closure |
| --- | --- | --- | --- | --- |
| Deck built (Playbook section 6) | PARTIAL | CP2.7 report: 12-slide deck v3 prepared 4 Oct, stored outside the repository in `04_Checkpoint_2/` as planned; [one-page summary](supporting/CP2_Presentation_Summary_20261004.md) in the repository | The deck file cannot be checked from the repository. Its content predates CP2.4 and uses development results only (allowed by the CP2.7 fallback) | Needs Dion to confirm |
| Rehearse once with timing | MISSING | None | | **Yes** |
| Present, then write down mentor feedback | MISSING | The master plan says "presented and mentored 4-5 Oct; mentor notes to be added". That line first appears in the 7 Oct snapshot commit, has no source, and the same master plan lists "Mentor feedback at CP2" as Open. The CP2.7 report says the session was not recorded | Owner-reported, not evidenced. Not counted as false or as true | **Yes** |
| Upload the deck to the LMS | MISSING | None | | **Yes** |
| Acceptance: mentor sees a measurable process | MISSING | No session record | | **Yes** |
| Acceptance: mentor feedback recorded in `docs/decisions.md` as new entries | MISSING | D-001 to D-090 contain no entry sourced from the CP2 mentor session | | **Yes** |

## 4. The two CP2.3 carry-overs

Both were open on 4 October and the later DONE status did not resolve them.

- **D-050 broad development extraction.** D-050 moved full development extraction "after CP2.3 configuration evaluation". The executed scope is the 52-JD development union used by Part B and pipeline v1.1. The frozen product extracts JDs per analyzed job and caches them, and CP2.4 extracted its 26 analyzed test jobs the same way. A decision is needed that either accepts the executed scope as the CP2 extraction scope (with full materialization deferred or dropped), or schedules a budgeted run.
- **D-051 paired masked comparison.** The masking code, consent binding, session controls and a mechanical quote check exist; the paired quality comparison on CV1/CV2 did not run. A decision is needed that either defers it to CP3 with real-CV processing kept off, or schedules it.

This audit does not decide either item. Writing a decision for Dion would invent an approval.

## 5. CP2.7 evidence search

Searched the whole repository (all Markdown, JSON, YAML and text files, `evidence/`, `docs/`, `evals/`) for mentor, LMS, rehearsal, deck and presentation records. Found: the 4 October one-page summary, the CP2.7 report, the planned-only CP3 reports, and the unsourced master-plan line. Not found: any deck file, rehearsal timing, mentor notes, LMS screenshot or receipt, or a CP2 mentor decision.

## 6. Held-out result verification

Source: `evals/results/cp24/heldout_report_v1.json`, contract `cp24-report-contract-v1`, run `cp24_test_v1`, labels `test_v13_cp24_r1`.

| Group | Metric | Stage 1 | Final | Coverage |
| --- | --- | --- | --- | --- |
| Headline CV3-CV5 | P@5 macro | 0.5333 | 0.7333 | 3/3 CVs |
| Headline CV3-CV5 | NDCG@10 macro | 0.8047 | 0.9604 | **2/3 CVs (CV3, CV4 only)** |
| Supplementary CV1-CV2 | P@5 macro | 0.3000 | 0.7000 | 2/2 CVs |
| Supplementary CV1-CV2 | NDCG@10 macro | 0.6875 | 0.8918 | 2/2 CVs |

- Recomputed by hand from `per_cv`: P@5 (0.2 + 0.8 + 0.6) / 3 = 0.533 and (0.4 + 1.0 + 0.8) / 3 = 0.733; NDCG@10 (0.7621 + 0.8473) / 2 = 0.8047 and (0.9504 + 0.9704) / 2 = 0.9604. CV5's stage-1 NDCG (0.582) is left out of the macro so that both orders cover the same CVs.
- **F00070** (CV5, final position 6) is in `held_test_r1.json` as `unscorable_source_quality` (the JD has responsibilities only and zero extraction units). It is absent from the 67 judged rows, never 0. CV5's final NDCG@10 is unavailable (`missing_original_position_judgment`).
- No pooled CV1-CV5 metric exists in the report, the tables or the figures.
- Pool: 68 pairs, 67 judged, 1 unjudged. Per-CV judged: CV1 14, CV2 13, CV3 14, CV4 12, CV5 14.
- Matching ran as the system ran: 14 of 44 Sol calls were refused by the run's own cost cap, 11 finished on Luna and 3 became holds (FAIL-34). The headline is not a pure Sol measurement.

## 7. Notebook verification

| Check | Notebook 02 (held-out) | Notebook 03 (Phase A) |
| --- | --- | --- |
| Persisted outputs | 7 code cells, execution counts 1-7, all with outputs, 0 errors, 3 images; Python 3.11.16 | 13 code cells, counts 1-13, all with outputs, 0 errors, 4 images; Python 3.11.16 |
| Reproduction printout | "Report reproduced from labels: OK"; 67 judged, 1 unjudged (CV5, F00070) | "Leakage check: OK"; 10 registered experiments, 5 with results |
| Numbers against authoritative files | Group macros and per-CV values equal `heldout_report_v1.json` and `cp25_tables_v1/*.csv` | Baseline, R1/R2, E01 and E02 values equal `experiment_registry.csv`, `stage_a_check_QA-E02_v1.json`, `wave1_selection_v1.json`, `phase_a_conclusion_v1.json` |
| Hashes | All 10 inputs and 6 outputs in `cp25_tables_v1/receipt.json` match | Notebook sha256 and all 4 figure hashes in `reports/figures/phase_a/receipt_v1.json` match |
| Frozen inputs untouched | Freeze verify ok; label bundle and report hashes equal the receipt | Phase A refuses CP2.4 paths (`LeakageError`, tested) |

Conclusion: the persisted outputs prove the figures and tables came from the saved artifacts; no re-execution or paid inference was needed. Two harmless wording leftovers in notebook 03 outputs ("QA-E03 not run yet", "planned after Wave 1 review") describe runs that the registry marks withdrawn; they were not edited, because editing owner-run outputs would break the notebook hash in the Phase A receipt.

## 8. CP2.8 (Phase A) status

Verified KEEP BASELINE (D-090). Evidence prompt v1.1 stays. Baseline repeated twice on the 20-pair, 411-unit optimization subset (macro-F1 0.7139 / 0.7146; 382/411 units identical). QA-E01: hard gates pass, not eligible (macro-F1 0.6992, overclaims 61 > 60). QA-E02: a precision/recall trade-off (macro-F1 0.7397, accuracy 0.7859, unsupported positives 59 to 37, overclaims 67-68 to 40), stopped at Stage A because underclaims rose from 19-20 to 33, over the locked no-regression limit of 25; no ranking stage ran. QA-E03 not run (adaptive stopping; its folder holds dry-run plans only). No finalist, no repeat, confirmation subset sealed. QA-H04 is future work only; no prompt or run exists. Rule file sha256 `3ab3111a…` matches. Phase A never touched CP2.4 and does not change the held-out result.

## 9. Human closeout checklist (Dion)

1. **CP2.7:** add the deck file reference or copy (or confirm the v3 path), the rehearsal timing if it happened, the mentor-session date and notes, and the LMS upload proof. If the session did not happen or the LMS upload is not required by the bootcamp, record that explicitly.
2. **CP2.7:** record the mentor feedback as new decision entries (D-091 onward), or record that the mentor gave no feedback that changes scope.
3. **CP2.3:** decide the D-050 broad-extraction disposition (accept the executed 52-JD development scope, or schedule a budgeted run).
4. **CP2.3:** decide the D-051 paired masked comparison (defer to CP3 with real-CV processing kept off, or schedule it).
5. Then update the CP2.7 status, the master plan section 2 row 14, and the CP2 index, and mark CP2 closed.

## 10. Validation run in this audit

Environment: Python 3.11 virtual environment in the session scratchpad with `requirements.txt` and `requirements-dev.txt` (as CI), no `.env`, no API key, no database.

| Command | Result |
| --- | --- |
| `python scripts/prepare_cp23_freeze.py --verify evals/freeze/cp23_freeze_draft_v2` | `"ok": true`, `changed_files: []` (before and after the edits) |
| `python -m pytest -q` | 671 passed, 9 skipped, **3 failed** (before and after the edits). Same result as GitHub Actions run 37604915026 on `8ca6b41` |
| `API_BUDGET_USD=19 API_HARD_STOP_USD=18.5 python -m pytest -q` (public `.env.example` values) | 672 passed, 9 skipped, 2 failed |
| `ruff check --select E9,F63,F7,F82 src scripts ui tests` (CI lint) | All checks passed |
| Receipt hash checks (cp25 tables, Phase A figures) | 21 of 21 match |

The 3 failures are environmental and not caused by CP2 evidence (FAIL-35): `tests/test_splits.py` (2 tests) read the git-ignored raw snapshot `data/interim/snapshots/CP1_20260926/jsearch_records.jsonl` without a skip guard, and `tests/test_qa_phase_a.py::test_budget_plan_stays_below_hard_stop_and_covers_need` uses the code default hard stop US$4.5 when `.env` is absent. CI is therefore red on this snapshot. This is a CP3.2 (CI) fix and was not changed here.

## 11. Freeze integrity

**PASS.** `prepare_cp23_freeze.py --verify` reports no changed file among the 57 frozen hashes (configuration v4, JD prompt v1.4 experimental, evidence prompt v1.1, splits, gold r4, `docs/evaluation.md`, metric contracts). This audit changed only documentation files; `git diff --stat` lists no file under `evals/`, `config/`, `prompts/`, `src/`, `scripts/`, `tests/`, `notebooks/` or `reports/`. Protected items unchanged: the D-087 receipt and its APPROVED copy, `evals/gold/test_v13_cp24_r1/`, `evals/results/cp24/` (report, run, supplementary, tables), the 214/214 split, `prompts/evidence_matching_v1_1.md`, and `evals/results/quality_optimization/selection_rule_v2.json`.

## 12. CP2 to CP3 handoff

After the checklist in section 9 is done, CP3 continues from the master plan: CP3.1 needs the frozen checkpoint-13 modules (D-087) and the checkpoint-14 mentor feedback. CP3.1 and CP3.3 are already done locally and CP3.2/CP3.4 are partial, so the next CP3 work is the CP3.2 CI fix (FAIL-35), the hosting deploy, and the deployed CP3.4 checks before the 8 October feature freeze. The deployed demo uses the D-087 configuration with evidence prompt v1.1 (D-090). The CP3.5 final report owes the D-045 test extraction and evidence results, which are not yet labeled.
