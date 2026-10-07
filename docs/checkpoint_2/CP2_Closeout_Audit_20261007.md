# CP2 Closeout Audit

**Date:** 7 October 2026 · **Branch:** `cp2-closeout-20261007` · **Result:** CP2 closed ([D-094](../decisions.md)) · **Model calls:** none

Before starting CP3, I went through every CP2.1-CP2.7 acceptance criterion in the [master plan](../master-plan.md) and checked it against files that actually exist in the repository, not against the DONE labels in the stage reports. CP2.8 (Phase A) was checked too, since it happened after the held-out test and must not change it. Frozen files were only read and hash-checked.

## 1. Result

CP2 is closed. Every acceptance criterion is met or covered by an approved decision (section 3), every stage has a current report (section 12), and the freeze and the saved results still verify (sections 9 and 10). What is left goes to CP3 (section 11).

The audit took three passes on the same day:

| Pass | Commit | Open items | What closed them |
| --- | --- | --- | --- |
| 1 | `de53544` | D-050 broad extraction had no approved scope; the D-051 paired masking comparison had no decision; no record of the CP2.7 mentor session or feedback | Left open: each needed an explicit decision, not a quiet change of status |
| 2 | `daf48bc` | None of the above | I approved D-091 (extraction scope) and D-092 (privacy deferral), confirmed the 4 October session and recorded the mentor feedback as D-093 |
| 3 | this pass | None | Final consistency check, then D-094 |

Two corrections from the first pass: I wrongly treated the CP2.7 rehearsal as blocking (it is only a method step, not an acceptance criterion), and I missed two dated traces of the 4 October session (section 5). The early passes also tracked the bootcamp LMS upload as repository evidence. That is an external bootcamp task, so it is no longer tracked here.

## 2. Status per stage

| Stage | Status | Notes |
| --- | --- | --- |
| CP2.1 Model and System Selection | DONE | |
| CP2.2 Modeling Pipeline | DONE | Done under D-050; its carry-over was closed in CP2.3 by D-091 |
| CP2.3 System Tuning | DONE | D-087 freeze; D-091; D-092 |
| CP2.4 Evaluation Metrics | DONE | `cp24-report-contract-v1` |
| CP2.5 Evaluation Visualization | DONE | |
| CP2.6 Recommendation and Summary | DONE | |
| CP2.7 Presentation and Mentoring | DONE | Session 4 Oct; feedback in D-093 |
| CP2.8 Phase A (post-test, development only) | CLOSED, KEEP BASELINE | D-090 |

## 3. Requirements and evidence

Requirements come from the master plan, section 8 ("Tests and acceptance criteria" and "Evidence to keep" for each stage), plus the D-051 privacy table at the top of the plan. Every PASS points to a file in this commit.

### CP2.1

| Requirement | Status | Evidence | Note |
| --- | --- | --- | --- |
| Guideline v1 with a version number | PASS | `evals/annotation_guideline_v1.md` (v1.2), later `evals/annotation_guideline_v1_3.md` (D-049) | |
| Schemas | PASS | `src/jobfit/schemas/` | |
| Scoring rules pass the 8 development fixtures | PASS | `tests/test_scoring.py`, `evals/fixtures/`; pass in this audit | The fixtures test the code, not the rules |
| Pilot time per item recorded and used for gold sizes | PASS | Pilot workbook timing sheet; D-043, replaced by D-045 | The CP2.1 report listed D-043/D-044 as pending; both were settled on 1 Oct |
| B0 and B1 run on the pilot pool, outputs saved | PASS | `evals/results/cp21_baselines.json`, EXP-20261001-01 | Recall@K could not be computed on the pilot (only one relevance-3 pair) |
| Experiment matrix with hypothesis and metric | PASS | `docs/experiments.md`, M01 to M12 | |
| Budget guard before the first LLM call; every call logged | PASS | `src/jobfit/llm/`, `tests/test_budget_guard.py`, `reports/usage/usage_ledger.jsonl` (780 records, US$10.528495) | Includes US$0.2489 of uncertain reservations |

### CP2.2

| Requirement | Status | Evidence | Note |
| --- | --- | --- | --- |
| One CV and one pasted JD give a structured report with exact CV quotes | PASS | `evals/results/cp22_extraction_repair_v13_20261003_04_semantic_repair.json`, `cp22_repair_semantic_review_20261003.json` | Passed after three bounded repairs; not evidence of unattended quality |
| 8 development cases pass the manual check | PASS | `evals/fixtures/v1_3/`, [acceptance review](supporting/CP22_Acceptance_Review_20261002.md) | Delegated review, not eight independent approvals |
| Cache keys include schema, prompt, model, preprocessing and guideline versions | PASS | CP2.2 report section 3; cache tests | |
| Planned-scale development extraction | Moved to CP2.3 by D-050 | Closed there by D-091 | |
| Test split locked before checkpoint 10 | PASS | `evals/splits/dev_job_ids.txt`, `test_job_ids.txt` (214/214, 1 Oct); both hashes are in the D-087 receipt and still verify | |

### CP2.3

| Requirement | Status | Evidence | Note |
| --- | --- | --- | --- |
| Every change has a development before/after and a keep/remove decision | PASS | EXP-20261003 to EXP-20261006-R4; D-044, D-065 to D-086 | Only two development CVs |
| Test set not used for tuning | PASS | D-087 was approved before any test processing; `freeze_receipt_APPROVED.json` | |
| Spend within the budget guard | PASS | Ledger US$10.53 against the US$18.5 hard stop (D-070) | |
| Stage-1 method, K, prompt and model recorded under the D-029 rule (amended by D-066) | PASS | D-044, D-077, D-083, D-078/D-086, D-084, D-087 | The provisional D-068 choices (DeepSeek matching, K 20) were replaced, not deleted |
| Freeze prepared and approved (D-053) | PASS | `evals/freeze/cp23_freeze_draft_v2/` (57 file hashes; receipt sha256 `18c1d17c…`), D-087 | |
| D-050 carried extraction: per-JD status and executed scope, or an approved revised scope | PASS by D-091 (was PARTIAL in pass 1) | 214-JD inventory of 3 Oct (`evals/results/cp22_development_extraction_plan_20261003.json`); per-JD status for the 52 JDs actually used (`evals/results/cp23/pipeline_v11/coverage_summary_v2.json`: 51 attempted, 48 process-valid) | The other 162 development JDs were never extracted. They could not affect any K/weight/order comparison, because all of those use only the top 30 |
| D-051 CP2.3 privacy work | Deferred by D-092 (was PARTIAL in pass 1) | Implemented: masking, consent tied to the masked text, session controls; all CP2.4 parses ran on masked text. Component/unit tests: `test_privacy_controls.py`, `test_cp23_masking_quotes.py`, `test_api_privacy.py` (fake run, not a deployed host), plus the masked-quote receipt | Not done: end-to-end privacy validation and the original-vs-masked comparison. Both moved to CP3.4 (run) and CP3.5 (report). Real-CV processing stays disabled |

### CP2.4

| Requirement | Status | Evidence | Note |
| --- | --- | --- | --- |
| Approved freeze before held-out processing | PASS | D-087; `freeze_receipt_APPROVED.json` | |
| Reviewed test labels used as ground truth | PASS, with a disclosed deviation | `evals/gold/test_v13_cp24_r1/` (67 judged, 1 held), D-088 | AI-assisted (ChatGPT), reviewed by one person, blind to ranking. Not independent human gold. D-088 records the deviation from D-053's "no model suggestions" |
| Original-position P@5 / NDCG@10 with coverage, common pool and paired CVs | PASS | `evals/results/cp24/heldout_report_v1.json` (section 6) | |
| No "good" claim without a metric | PASS | CP2.4 sections 10, 10b, 11 | |
| Git SHA, prompt and model versions, cost and latency per result | PASS | Freeze receipt hashes, config v4, CP2.4 10b | The report names HEAD `8cfb359d` because the files were committed later, in `8ca6b41`. The 57 freeze hashes identify the evaluated files |
| Limitations written | PASS | CP2.4 section 11 | |
| Safety: hard negatives in top 10, quote validity | PASS | `evals/results/cp24/supplementary_v2/summary.json`: 519/519 positive items quote the CV; one relevance-0 job in any final top 10 (CV3/F00501) | Unsupported claims need test evidence gold, which does not exist yet |
| Latency p50/p95 and cost | PASS | CP2.4 10b; ledger runs `cp24_test_*`, US$1.442 | |
| Failure examples logged | PASS | FAIL-32, FAIL-33, FAIL-34 | |
| Evidence Macro-F1 and extraction F1 on test | Deferred by D-045 | D-045 reports these on development gold at CP2.4 and moves the test numbers to the final report (CP3.5) | D-088 imported only the relevance sheet, so this is still open for CP3.5 |

### CP2.5

| Requirement | Status | Evidence | Note |
| --- | --- | --- | --- |
| Stage-1 comparison chart | PASS | `reports/figures/cp2/fig01_retrieval_methods.png` (development) | |
| P@5 and NDCG@10, stage 1 vs final | PASS | fig09 (headline CV3-CV5), fig10 (CV1-CV2 supplementary), fig11 (post-hoc decomposition) | |
| Evidence confusion matrix | PASS on development | fig04 | Test evidence gold is deferred (D-045) |
| Quality vs cost vs latency | PASS | fig06 (development); CP2.4 10b table (test) | |
| Hard-negative and failure cases | PASS | CP2.5 short-case table | |
| Every chart shows configuration, version and denominator | PASS | fig09-fig11 captions carry split, coverage and the D-088 note | Phase A figures carry their denominators in the report text only |
| Same split and labels in each comparison | PASS | `evals/results/cp24/cp25_tables_v1/receipt.json`; all 16 hashes match | |
| Figure script saved | PASS | `scripts/build_cp2_figures.py`; notebooks 02 and 03 | |

### CP2.6

| Requirement | Status | Evidence | Note |
| --- | --- | --- | --- |
| Error analysis by category | PASS | CP2.6 development error analysis and held-out error table | Filter misses not measurable (no optional filter in the test run) |
| Final stage-1 method, K, model, prompt, PARTIAL weight | PASS | D-086, D-087, CP2.6 final summary | |
| Keep/remove decisions | PASS | CP2.6 keep/remove table, each row tied to a decision | |
| Limitations and next-version ideas | PASS | CP2.6 final summary | |
| Architecture v1 diagram | PASS | Mermaid diagram in CP2.6, built from the D-087 receipt | Added during this closeout |
| Architecture explained by the experiments | PASS | CP2.6 final summary and keep/remove table | |

### CP2.7

| Requirement | Status | Evidence | Note |
| --- | --- | --- | --- |
| Deck built | PASS | Deck v3 (4 Oct) in `04_Checkpoint_2/`, outside the repository as planned | |
| Rehearse once with timing | Not recorded | | A method step only; not an acceptance criterion |
| Present, then write down mentor feedback | PASS (was missing in pass 1) | Session on 4 Oct 2026 (section 5); feedback in CP2.7 section 10 | |
| Acceptance: mentor sees a measurable process | PASS | Session confirmed; the deck showed the measured CP2.1-CP2.3 comparisons | |
| Acceptance: mentor feedback recorded as new decision entries | PASS | [D-093](../decisions.md) | |

## 4. How the open items were resolved

- **D-050 extraction scope (D-091).** The plan's criterion allows either full per-JD execution or an approved revised scope. I approved the scope that was actually used: the 52 JDs in the top 30 of CV1 and CV2. All K/weight/order cells in D-078 sit inside that top 30, so the other 162 JDs could not change any choice. No test data was involved.
- **D-051 privacy (D-092).** Privacy is implemented and covered by component tests, but it has not been validated end to end, and the original-vs-masked comparison has not run. Neither result feeds a frozen setting, and the plan already puts deployed privacy acceptance in CP3.4. So both moved to CP3.4 (run) and CP3.5 (report), with real-CV processing kept off until then.
- **CP2.7 session and feedback (D-093).** I confirmed the session and wrote up the mentor's feedback; two files from that day date it to 4 October.

None of these changed D-087, the CP2.4 result or any frozen file, and none came from a new run.

## 5. Dating the CP2.7 session

The first pass searched for mentor, rehearsal, deck and "presented" and found no session record. Searching for "presentation" in pass 2 found two traces from 4 October:

- `evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1/cap_and_deadline_amendment_v2.json` (D-069): "At 08:13 WIB Dion said the presentation was in about six hours."
- [`supporting/CP23_Audit_Fixes_20261004.md`](supporting/CP23_Audit_Fixes_20261004.md), dated 4 October: "After the CP2 presentation I audited all CP2 work."

So the session was on 4 October 2026, probably early afternoon WIB. The exact time and attendees were not recorded. The older master-plan wording "4-5 Oct" only holds for 4 October.

## 6. Held-out result check

Source: `evals/results/cp24/heldout_report_v1.json`, contract `cp24-report-contract-v1`, run `cp24_test_v1`, labels `test_v13_cp24_r1`.

| Group | Metric | Stage 1 | Final | Coverage |
| --- | --- | --- | --- | --- |
| Headline CV3-CV5 | P@5 macro | 0.5333 | 0.7333 | 3/3 CVs |
| Headline CV3-CV5 | NDCG@10 macro | 0.8047 | 0.9604 | 2/3 CVs (CV3, CV4 only) |
| Supplementary CV1-CV2 | P@5 macro | 0.3000 | 0.7000 | 2/2 CVs |
| Supplementary CV1-CV2 | NDCG@10 macro | 0.6875 | 0.8918 | 2/2 CVs |

- I recomputed the macros by hand from `per_cv`: P@5 (0.2 + 0.8 + 0.6) / 3 = 0.533 and (0.4 + 1.0 + 0.8) / 3 = 0.733; NDCG@10 (0.7621 + 0.8473) / 2 = 0.8047 and (0.9504 + 0.9704) / 2 = 0.9604. CV5's stage-1 NDCG (0.582) is left out so both orders cover the same CVs.
- F00070 (CV5, final position 6) is held as `unscorable_source_quality`: the JD lists responsibilities only. It is not among the 67 judged rows and is never counted as 0, so CV5's final NDCG@10 is unavailable.
- There is no pooled CV1-CV5 metric in the report, the tables or the figures.
- Pool: 68 pairs, 67 judged. Judged per CV: CV1 14, CV2 13, CV3 14, CV4 12, CV5 14.
- The run's own cost cap refused 14 of 44 Sol calls; 11 finished on Luna and 3 became holds (FAIL-34). The headline describes the system as it ran, not a pure Sol run.

## 7. Notebooks

| Check | Notebook 02 (held-out) | Notebook 03 (Phase A) |
| --- | --- | --- |
| Saved outputs | 7 code cells run in order, 0 errors, 3 images; Python 3.11.16 | 13 code cells run in order, 0 errors, 4 images; Python 3.11.16 |
| Self-check printed | "Report reproduced from labels: OK"; 67 judged, 1 unjudged (CV5, F00070) | "Leakage check: OK"; 10 registered experiments, 5 with results |
| Numbers match the source files | Yes: `heldout_report_v1.json`, `cp25_tables_v1/*.csv` | Yes: `experiment_registry.csv` and the Phase A analysis files |
| Hashes | All 16 in `cp25_tables_v1/receipt.json` match | Notebook and all 4 figure hashes in `reports/figures/phase_a/receipt_v1.json` match |

The saved outputs are enough to show the figures and tables came from the saved results, so I did not rerun anything. Notebook 03 still prints "QA-E03 not run yet" and "planned after Wave 1 review" for runs the registry marks withdrawn. I left those outputs alone, because editing them would break the notebook hash in the Phase A receipt.

## 8. Phase A (CP2.8)

KEEP BASELINE (D-090) checks out against the saved files. The baseline ran twice on the 411-unit optimization subset (macro-F1 0.7139 and 0.7146; 382/411 units identical). QA-E01 passed the hard gates but was not eligible (macro-F1 0.6992, overclaims 61 > 60). QA-E02 traded recall for precision: macro-F1 0.7397, accuracy 0.7859, unsupported positives 59 to 37, overclaims 67-68 to 40. It stopped after Stage A because underclaims rose from 19-20 to 33, past the locked limit of 25, so no ranking stage ran. QA-E03 did not run (its folder has dry-run plans only). There was no finalist and no repeat, and the confirmation subset is still sealed. QA-H04 is only an idea; no prompt or run exists. The rule file hash (`3ab3111a…`) matches. Phase A never touched CP2.4.

## 9. Validation

Offline only, in a Python 3.11 environment with `requirements.txt` and `requirements-dev.txt` (as in CI), with no `.env`, no API key and no database.

| Check | Result (same in all passes) |
| --- | --- |
| `python scripts/prepare_cp23_freeze.py --verify evals/freeze/cp23_freeze_draft_v2` | `"ok": true`, no changed files |
| `python -m pytest -q` | 671 passed, 9 skipped, 3 failed (FAIL-35). GitHub Actions run 37604915026 on `8ca6b41` gives the same result |
| Targeted CP2 tests with the `.env.example` budget values (`test_heldout_report`, `test_qa_phase_a`, `test_product_order`, `test_privacy_controls`, `test_cp23_masking_quotes`, `test_api_privacy`, `test_scoring`, `test_cp24_parse_recovery`) | 117 passed |
| `ruff check --select E9,F63,F7,F82 src scripts ui tests` | Clean |
| Receipt hashes (CP2.5 tables, Phase A figures) | 21/21 match |
| `git diff --name-only 8ca6b41` | Only `docs/` and `README.md` |

The CP2 evidence checks pass, but the full test suite and CI are not green. The three failures come from the test setup, not from CP2 results (FAIL-35):

- two tests in `tests/test_splits.py` read the git-ignored raw snapshot without a skip guard;
- `test_budget_plan_stays_below_hard_stop_and_covers_need` falls back to the code default hard stop of US$4.5 when `.env` is missing.

Fixing them is CP3.2 work.

## 10. Freeze integrity

PASS. `prepare_cp23_freeze.py --verify` reports no change among the 57 frozen hashes (configuration v4, JD prompt v1.4 experimental, evidence prompt v1.1, splits, gold r4, `docs/evaluation.md`, metric contracts). The closeout changed documentation only. Unchanged: the D-087 receipt and its approved copy, `evals/gold/test_v13_cp24_r1/`, `evals/results/cp24/`, the 214/214 split, `prompts/evidence_matching_v1_1.md` and `evals/results/quality_optimization/selection_rule_v2.json`.

## 11. What CP3 inherits

None of this was done during the closeout, and none of it changes D-087 or the CP2.4 result.

1. **The frozen system (D-087):** Hybrid FTS + Qwen3 dense with RRF, seniority rule over the top 30, K = 10, PARTIAL weight 0.5, experience block, H2v2, DeepSeek Flash JD extraction (JD prompt v1.4 experimental), GPT-6 Sol matching with Luna fallback, product order.
2. **Evidence prompt v1.1**, kept by Phase A (D-090).
3. **Waiting-state UX (D-093 A).** The mentor saw about 95 s of LLM wait. CP3 should make the wait visible (progress, current step, a "thinking" indicator). There is already a per-job progress bar and a spinner in `ui/streamlit_app.py`; check them against the feedback before building anything new. This makes the wait easier to sit through; it does not make the model faster.
4. **Vacancy-specific CV guidance (D-093 B)**, once the core flow is stable. This extends the existing [CV coach plan](../cv-coach-plan.md) (D-036) and CV coach v1. Suggestions must come from the real CV, the real JD and the gaps found, and never invent experience or promise a better real fit.
5. **End-to-end privacy validation (D-092, CP3.4):** leakage, log and output checks, consent and session behavior, PR-01 to PR-10 including the PR-08 provider policy check. Real-CV processing stays off until this passes.
6. **Original-vs-masked matching comparison (D-092, CP3.4):** the PR-10 paired run. Until then, no claim that masking has no effect on matching.
7. **CI repair (FAIL-35, CP3.2):** skip guards for the raw-snapshot tests and explicit budget values for the Phase A test.
8. **Railway deployment (CP3.2, D-023)**, with live analysis off by default.
9. **Deployed end-to-end checks (CP3.4):** happy path, failure paths, log PII checks, latency and cost, then the feature freeze.
10. **Final reporting (CP3.5):** the D-045 test extraction and evidence results (labels not made yet) and the privacy and matching-impact report (D-092).

## 12. Stage reports

Each CP2 stage has one current report, with older text marked by date.

| Stage | Report | Status | Updated in this closeout |
| --- | --- | --- | --- |
| CP2.1 | [CP2_01_Model_and_System_Selection.md](CP2_01_Model_and_System_Selection.md) | DONE | Final status note; D-043/D-044 marked as settled |
| CP2.2 | [CP2_02_Modeling_Pipeline.md](CP2_02_Modeling_Pipeline.md) | DONE | D-091 note; frozen JD prompt noted |
| CP2.3 | [CP2_03_System_Tuning.md](CP2_03_System_Tuning.md) and [CP2_03_Model_Comparison.md](CP2_03_Model_Comparison.md) | DONE | Final status section with D-091, D-092 and figures; supersession note on the comparison report |
| CP2.4 | [CP2_04_Evaluation_Metrics.md](CP2_04_Evaluation_Metrics.md) | DONE | D-045 deferral cited; figures 9-10 added |
| CP2.5 | [CP2_05_Evaluation_Visualization.md](CP2_05_Evaluation_Visualization.md) | DONE | Summary brought in line with the held-out figures |
| CP2.6 | [CP2_06_Recommendation_and_Summary.md](CP2_06_Recommendation_and_Summary.md) | DONE | Architecture diagram, keep/remove table, held-out error table, handoff |
| CP2.7 | [CP2_07_Presentation_and_Mentoring.md](CP2_07_Presentation_and_Mentoring.md) | DONE | Session date, mentor feedback, D-093 |
| CP2.8 | [CP2_08_Post_Test_Quality_Optimization.md](CP2_08_Post_Test_Quality_Optimization.md) | CLOSED, KEEP BASELINE | Figures A1-A4 added; old plan sections marked historical |

No stage report is missing or incomplete.
