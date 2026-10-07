# CP2 Closeout Audit

**Date:** 7 October 2026. **Branch:** `cp2-closeout-20261007`. **First pass:** audited at commit `8ca6b41`, results committed as `de53544`. **Second pass:** after Dion supplied the mentor-session confirmation, the mentor feedback and two decisions (D-091, D-092; feedback recorded as D-093), committed as `daf48bc`. **Final pass:** after Dion confirmed the CP2.7 LMS upload; closure recorded as D-094. **Model calls:** none in any pass. **Scope:** CP2.1 to CP2.7 acceptance against the [master plan](../master-plan.md), plus the CP2.8 post-test extension. Frozen artifacts were read and hash-checked, never edited.

## 1. Verdict

**Final pass (current): CP2 — CLOSED (7 October 2026, [D-094](../decisions.md)).**

Every CP2.1-CP2.7 acceptance criterion and evidence item is PASS or resolved by an approved decision (section 3), and every CP2.1-CP2.8 primary report is complete and current (section 13). Freeze integrity and reproducibility pass (sections 10 and 11). The open CP3 work in section 12 is carried forward by decisions; it is not a CP2 gap.

| Pass | Verdict | Open items at that pass |
| --- | --- | --- |
| First (historical) | NOT YET CLOSED | D-050 extraction carry-over; D-051 paired comparison; CP2.7 session and mentor feedback; LMS proof (rehearsal was also listed, wrongly, as blocking) |
| Second (historical) | NOT YET CLOSED | LMS proof only. D-091, D-092 and D-093 plus the confirmed 4 Oct session resolved everything else; rehearsal was re-read as non-blocking |
| Final (current) | **CLOSED** | None. Dion confirmed the LMS upload; the submission evidence is kept in the LMS, outside the repository |

## 2. Status of each stage

| Stage | First pass | Second pass | Final pass (current) | Basis |
| --- | --- | --- | --- | --- |
| CP2.1 Model and System Selection | DONE | DONE | DONE | Section 3 |
| CP2.2 Modeling Pipeline | DONE under D-050 | DONE; carry-over resolved by D-091 | DONE | Section 3 |
| CP2.3 System Tuning | DONE for tuning and freeze; two carry-overs without a disposition | DONE: D-087; D-091; D-092 | DONE (privacy implemented and component/unit tested; end-to-end validation and paired comparison deferred to CP3.4/CP3.5 by D-092) | Section 4 |
| CP2.4 Evaluation Metrics | DONE | DONE | DONE (`cp24-report-contract-v1`) | Section 6 |
| CP2.5 Evaluation Visualization | DONE | DONE | DONE | Section 7 |
| CP2.6 Recommendation and Summary | DONE | DONE | DONE | Section 3 |
| CP2.7 Presentation and Mentoring | IN PROGRESS, blocks closure | Acceptance met; LMS proof open | DONE | Section 5 |
| CP2.8 Phase A (post-test, development only) | CLOSED, KEEP BASELINE | unchanged | CLOSED, KEEP BASELINE (D-090) | Section 8 |

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
| Planned-scale development extraction | NOT REQUIRED for CP2.2 by D-050 | D-050 moved it to CP2.3 as an explicit carry-over; resolved there by D-091 | See CP2.3 | No |
| Test split locked before checkpoint 10 | PASS | `evals/splits/dev_job_ids.txt`, `test_job_ids.txt` (214 / 214, T03 1 Oct); both hashes are in the D-087 receipt and verify | | No |

### CP2.3 (checkpoint 10)

| Requirement | Status | Evidence | Note, limitation | Blocks closure |
| --- | --- | --- | --- | --- |
| Every change has a development before/after and a keep/remove decision | PASS | EXP-20261003 to EXP-20261006-R4; D-044, D-065 to D-086 | Two development CVs only | No |
| Test set not used for tuning | PASS | D-087 frozen before any test processing; `freeze_receipt_APPROVED.json`; `prepare_cp23_freeze.py --verify` ok | | No |
| Spend within the budget guard | PASS | Ledger US$10.53 against the US$18.5 hard stop (D-070) | | No |
| Stage-1 method, K, prompt and model recorded under the D-029 rule (as amended by D-066) | PASS | D-044 (Qwen), D-083 (Sol matching, Luna fallback), D-077 (DeepSeek Flash extraction), D-078/D-086 (K 10, weight 0.5, seniority rule), D-084 (Hybrid Qwen kept), D-087 (freeze) | Earlier provisional choices D-068 (DeepSeek matching, K 20) were superseded, not deleted | No |
| Freeze prepared and approved (D-053) | PASS | `evals/freeze/cp23_freeze_draft_v2/` (57 file hashes; receipt sha256 `18c1d17c…`), D-087 | | No |
| D-050 carried extraction: auditable per-JD status and executed scope, or an approved revised disposition | **PASS (approved disposition, D-091)**; first pass: PARTIAL | 214-JD inventory of 3 Oct (`evals/results/cp22_development_extraction_plan_20261003.json`); per-JD status of the executed 52-JD scope (`evals/results/cp23/pipeline_v11/coverage_summary_v2.json`: 51 attempted, 48 process-valid); [D-091](../decisions.md) | 162 development JDs never extracted; exhaustive extraction is optional future work. The criterion's own alternative ("or an explicitly approved revised scope/budget disposition") is met | No |
| D-051 CP2.3 privacy work: masking/consent boundary, session primitives, synthetic CV1/CV2 masking impact | **PASS (approved deferral, D-092)**; first pass: PARTIAL | Implemented: masking, consent binding, session controls; all CP2.4 parses masked. Component/unit tested: `test_privacy_controls.py`, `test_cp23_masking_quotes.py`, `test_api_privacy.py` (fake run, PR-01 to PR-07 and PR-09, not a deployed host), mechanical quote receipt; [D-092](../decisions.md) | End-to-end privacy validation: **not performed**. Original-vs-masked comparison: **not performed**. Both deferred to CP3.4 (run) and CP3.5 (report). No end-to-end or no-quality-effect claim; real-CV processing stays disabled | No |

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

| Requirement | Type in the master plan | First pass | Second pass (current) | Evidence | Blocks closure |
| --- | --- | --- | --- | --- | --- |
| Deck built (Playbook section 6) | Step 1; "deck file" in evidence to keep | PARTIAL | PASS (stored outside the repository by plan design) | CP2.7 report: deck v3 recorded on 4 Oct at `04_Checkpoint_2/`; session confirmed by Dion | No |
| Rehearse once with timing | Step 4 only | MISSING | Not recorded; **non-blocking** | None | No: not an acceptance criterion and not an evidence item |
| Present, then write down mentor feedback | Step 5; "feedback notes" in evidence to keep | MISSING | PASS | Session on 4 Oct 2026 (D-069 amendment note; 4 Oct audit report opens "After the CP2 presentation"); Dion's confirmation and feedback on 7 Oct; CP2.7 section 10 | No |
| Upload the deck to the LMS | Step 6; "LMS proof" in evidence to keep | MISSING | MISSING in the second pass; **final: PASS (owner-confirmed external LMS submission)** | Dion's confirmation on 7 Oct; the submission record is kept in the LMS, outside the repository; no artifact, ID, timestamp or URL is reproduced | No |
| Acceptance: mentor sees a measurable process | Acceptance criterion | MISSING | PASS | Dion's confirmation of the session; the deck presented the measured CP2.1-CP2.3 development comparisons | No |
| Acceptance: mentor feedback recorded in `docs/decisions.md` as new entries | Acceptance criterion | MISSING | PASS | [D-093](../decisions.md) | No |

## 4. Resolution of the first-pass blockers

| Blocker | Previous status (first pass) | New evidence or decision | Final status | Rationale |
| --- | --- | --- | --- | --- |
| CP2.3: D-050 carried extraction | PARTIAL, blocking: 52 of 214 development JDs extracted, no approved revised scope | [D-091](../decisions.md), approved by Dion on 7 Oct | PASS (approved disposition) | The master-plan criterion explicitly allows "an explicitly approved revised scope/budget disposition". Every K/weight/order cell of D-078 lies inside the reordered top 30, which the 52-JD scope covers; failed or held JDs stayed holds. No test data was used. The 162 unextracted JDs are not claimed extracted |
| CP2.3: D-051 privacy work (paired comparison; end-to-end validation) | PARTIAL, blocking: paired comparison prepared, not run, no decision | [D-092](../decisions.md), approved by Dion on 7 Oct, with his clarification that privacy has not been validated end-to-end | PASS (approved deferral) | Status by level: implemented; component/unit tested (API tests with a fake run, not a deployed host); end-to-end validated **no**; paired comparison **no**. Both open items feed no frozen setting and are deferred to CP3.4 (run) and CP3.5 (report); the master-plan privacy table already places deployed privacy acceptance in CP3.4. CP2 makes no end-to-end or no-quality-effect claim; real-CV processing stays disabled |
| CP2.7: session and mentor feedback | MISSING, blocking | Dion confirmed the session and supplied the feedback (7 Oct); repository traces date it to 4 Oct; feedback recorded as [D-093](../decisions.md) | PASS | Both CP2.7 acceptance criteria are met; feedback notes are saved in CP2.7 section 10 and D-093 |
| CP2.7: rehearsal | MISSING, listed as blocking | Plan re-read | Non-blocking (not recorded) | Step 4 of the method only; it is neither an acceptance criterion nor an evidence item. The first pass over-weighted it |
| CP2.7: LMS proof | MISSING, blocking | Second pass: none, still open. Final pass: Dion confirmed the upload | **PASS (owner-confirmed external LMS submission)** | "LMS proof" is an evidence item and the status rule requires saved evidence. The evidence is saved in the LMS itself; the plan already keeps CP2.7 evidence outside the repository (deck in `04_Checkpoint_2/`, proof of work in the Timeline file, section 9 of the plan) |

Neither D-091 nor D-092 changes D-087, the CP2.4 result or any frozen file, and neither came from a new run.

## 5. CP2.7 evidence and the rehearsal/LMS determination

**First pass (historical):** searched all Markdown, JSON, YAML and text files for mentor, LMS, rehearsal, deck and "presented". Found the one-page summary, the CP2.7 report and the unsourced master-plan line; no session record. That search missed two dated traces because it did not search for "presentation".

**Second pass:** a search for "presentation" found:

- `evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1/cap_and_deadline_amendment_v2.json` (D-069): "At 08:13 WIB Dion said the presentation was in about six hours" on 4 October 2026.
- [`supporting/CP23_Audit_Fixes_20261004.md`](supporting/CP23_Audit_Fixes_20261004.md), dated 4 October 2026: "After the CP2 presentation I audited all CP2 work."

Together with Dion's confirmation and the feedback he supplied, these date the session to **4 October 2026**, early afternoon WIB by the D-069 note; the exact time and attendees were not captured. The earlier master-plan wording "4-5 Oct" is not supported beyond 4 October.

**Rehearsal and LMS, read literally from the master plan (CP2.7, section 8):**

| Item | Where it appears | Acceptance criterion? | Evidence to keep? | Determination |
| --- | --- | --- | --- | --- |
| Rehearsal with timing | Step 4 ("Rehearse once with timing") | No | No | Non-blocking; not recorded |
| LMS upload proof | Step 6 ("Upload the deck to the LMS (Dion)"), outputs ("LMS upload proof"), evidence to keep ("LMS proof") | No | **Yes** | Required by the status rule "DONE only when its acceptance criteria are met and its evidence is saved". Second pass: missing. **Final pass: satisfied, owner-confirmed, evidence kept in the LMS** |

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

All items are resolved. First pass: D-050 disposition (D-091), D-051 disposition (D-092), mentor session and feedback (confirmed; D-093). Second pass: LMS proof. Final pass: Dion confirmed the LMS upload on 7 October. No human action remains for CP2.

## 10. Validation run in this audit

Environment: Python 3.11 virtual environment in the session scratchpad with `requirements.txt` and `requirements-dev.txt` (as CI), no `.env`, no API key, no database.

| Command | Result |
| --- | --- |
| `python scripts/prepare_cp23_freeze.py --verify evals/freeze/cp23_freeze_draft_v2` | `"ok": true`, `changed_files: []` (before and after the edits) |
| `python -m pytest -q` | 671 passed, 9 skipped, **3 failed** (before and after the edits). Same result as GitHub Actions run 37604915026 on `8ca6b41` |
| `API_BUDGET_USD=19 API_HARD_STOP_USD=18.5 python -m pytest -q` (public `.env.example` values) | 672 passed, 9 skipped, 2 failed |
| `ruff check --select E9,F63,F7,F82 src scripts ui tests` (CI lint) | All checks passed |
| Receipt hash checks (cp25 tables, Phase A figures) | 21 of 21 match |
| Second pass: same freeze verify, full suite and lint after all second-pass edits | `"ok": true`; 671 passed, 9 skipped, 3 failed (same FAIL-35 tests); lint clean |
| Second pass: `API_BUDGET_USD=19 API_HARD_STOP_USD=18.5 python -m pytest -q tests/test_heldout_report.py tests/test_qa_phase_a.py tests/test_product_order.py tests/test_privacy_controls.py tests/test_cp23_masking_quotes.py tests/test_api_privacy.py tests/test_scoring.py tests/test_cp24_parse_recovery.py` | 117 passed |
| Second pass: receipt hashes; `git diff --name-only 8ca6b41` outside `docs/` and `README.md` | 21 of 21 match; no file outside documentation changed |
| Final pass: freeze verify; full suite; the same 117 targeted tests; CI lint; receipt hashes; `git diff --name-only 8ca6b41` | `"ok": true`; 671 passed, 9 skipped, 3 failed (FAIL-35, unchanged); 117 passed; lint clean; 21 of 21; only `docs/` and `README.md` changed |

**CP2 evidence validation: PASS.** Repository CI has known environment/test-hygiene failures tracked as FAIL-35; the full suite is not green. The 3 failures are environmental and not caused by CP2 evidence (FAIL-35): `tests/test_splits.py` (2 tests) read the git-ignored raw snapshot `data/interim/snapshots/CP1_20260926/jsearch_records.jsonl` without a skip guard, and `tests/test_qa_phase_a.py::test_budget_plan_stays_below_hard_stop_and_covers_need` uses the code default hard stop US$4.5 when `.env` is absent. CI is therefore red on this snapshot. This is a CP3.2 (CI) fix and was not changed here.

## 11. Freeze integrity

**PASS** in all three passes (last checked in the final pass). `prepare_cp23_freeze.py --verify` reports no changed file among the 57 frozen hashes (configuration v4, JD prompt v1.4 experimental, evidence prompt v1.1, splits, gold r4, `docs/evaluation.md`, metric contracts). This audit changed only documentation files; `git diff --stat` lists no file under `evals/`, `config/`, `prompts/`, `src/`, `scripts/`, `tests/`, `notebooks/` or `reports/`. Protected items unchanged: the D-087 receipt and its APPROVED copy, `evals/gold/test_v13_cp24_r1/`, `evals/results/cp24/` (report, run, supplementary, tables), the 214/214 split, `prompts/evidence_matching_v1_1.md`, and `evals/results/quality_optimization/selection_rule_v2.json`.

## 12. CP2 to CP3 handoff

CP2 is closed (D-094). CP3 inherits the following; none of it is done in this closeout, and none of it changes D-087 or the CP2.4 result.

1. **Frozen system (D-087):** Hybrid FTS + Qwen3 dense with RRF, seniority rule over the top 30, K = 10, PARTIAL weight 0.5, experience block, H2v2, DeepSeek Flash JD extraction (JD prompt v1.4 experimental), GPT-6 Sol matching with Luna fallback, product order. CP3.1's checkpoint-13 input.
2. **Evidence-matching prompt v1.1**, kept by Phase A (D-090).
3. **D-093 A, latency waiting-state UX:** the mentor saw about 95 s of LLM wait. CP3 makes the waiting state explicit (progress, current step, a "thinking" indicator), checking the existing per-job progress bar and spinner in `ui/streamlit_app.py` rather than duplicating them. A perceived-wait mitigation; no latency reduction is claimed unless measured.
4. **D-093 B, vacancy-specific CV improvement guidance**, after the core flow is stable: extends the CV coach plan ([D-036](../decisions.md), [cv-coach-plan.md](../cv-coach-plan.md)) and CV coach v1. Grounded in actual CV evidence, actual JD requirements and identified gaps; no invented experience, no encouragement to misrepresent skills, no promise of higher true suitability.
5. **D-092 end-to-end privacy validation (CP3.4):** privacy is implemented and component/unit tested only. CP3.4 validates the integrated system end to end: leakage, log and output checks, consent and session behavior, PR-01 to PR-10 including the PR-08 provider policy check. Real-CV processing stays disabled until this and the D-051 release gates pass.
6. **Original-vs-masked matching comparison (CP3.4, D-092):** the PR-10 paired comparison; no claim that masking does not affect matching quality before it runs.
7. **FAIL-35 CI/test-hygiene repair (CP3.2):** skip guards for the raw-snapshot split tests and explicit budget values for the Phase A budget test, so the full suite and CI can be green.
8. **Hosting and deployment (CP3.2):** Railway deploy (D-023) with live analysis off by default.
9. **Deployed end-to-end validation (CP3.4):** happy path and critical failure paths on the deployed app, log PII checks, latency and cost, then the feature freeze.
10. **CP3.5 final reporting:** the D-045 test extraction and evidence results (labels not yet made) and the final privacy evaluation and matching-quality impact report (D-092).

## 13. Per-stage report completeness (final pass)

Each CP2 point has one current primary report. Historical text in each report is labeled with its date. "Updated" means changed during this closeout.

| Stage | Primary report | Final status | Evidence current | Report complete | Changes in this closeout |
| --- | --- | --- | --- | --- | --- |
| CP2.1 | [CP2_01_Model_and_System_Selection.md](CP2_01_Model_and_System_Selection.md) | DONE | Yes | Yes (REPORT UPDATED) | Final reconciled status; D-043/D-044 resolved |
| CP2.2 | [CP2_02_Modeling_Pipeline.md](CP2_02_Modeling_Pipeline.md) | DONE (under D-050; carry-over closed by D-091) | Yes | Yes (REPORT UPDATED) | D-091 resolution; frozen JD prompt noted |
| CP2.3 | [CP2_03_System_Tuning.md](CP2_03_System_Tuning.md), with [CP2_03_Model_Comparison.md](CP2_03_Model_Comparison.md) | DONE (D-087, D-091, D-092) | Yes | Yes (REPORT UPDATED; comparison REPORT COMPLETE with supersession note) | Objective, scope, method, final table, D-091, D-092 with privacy status by level, figures, audit trail |
| CP2.4 | [CP2_04_Evaluation_Metrics.md](CP2_04_Evaluation_Metrics.md) | DONE | Yes | Yes (REPORT UPDATED) | D-045 deferral cited; figures 9-10 embedded; final status |
| CP2.5 | [CP2_05_Evaluation_Visualization.md](CP2_05_Evaluation_Visualization.md) | DONE | Yes | Yes (REPORT UPDATED in the first pass) | Summary reconciled with held-out figures |
| CP2.6 | [CP2_06_Recommendation_and_Summary.md](CP2_06_Recommendation_and_Summary.md) | DONE | Yes | Yes (REPORT UPDATED) | Architecture diagram, keep/remove table, held-out error table, handoff |
| CP2.7 | [CP2_07_Presentation_and_Mentoring.md](CP2_07_Presentation_and_Mentoring.md) | DONE | Yes | Yes (REPORT UPDATED) | Session and date evidence, feedback, D-093, LMS owner confirmation, three-pass audit trail |
| CP2.8 | [CP2_08_Post_Test_Quality_Optimization.md](CP2_08_Post_Test_Quality_Optimization.md) | CLOSED, KEEP BASELINE | Yes | Yes (REPORT UPDATED) | Figures A1-A4 embedded; historical plan sections labeled; claim boundary |

Result: no primary report is missing or partial; the documentation condition for closure is met.
