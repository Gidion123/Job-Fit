# CP2.4: Evaluation Metrics

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 11. Modeling + Evaluation Metrics · official date 1 Oct 2026  
**JobFit version of this checkpoint:** The chosen configuration is measured on the held-out test set with the metrics of System Design v1.3 section 14.  
**Planned work:** 3 Oct 2026 · **Actual:** freeze approved 6 Oct (D-087); test run and labels 6-7 Oct; evaluated 7 Oct 2026  
**Status:** DONE (headline under `cp24-report-contract-v1`; supplementary descriptive metrics in 10b; evidence/extraction F1 on test not measured, reason in 10b) · design basis: System Design v1.3

> Results are in sections 10 and 10b; figures in [CP2.5](CP2_05_Evaluation_Visualization.md) (notebook `notebooks/02_cp2_heldout_evaluation.ipynb`, run by Dion on 7 Oct 2026). The plan for all stages is in the [master plan](../master-plan.md).

## 1. Goal of this stage

Measure the chosen configuration on the held-out test set and report the metrics in the priority order of System Design v1.3 section 14.

> D-052 establishes development metric conventions in [evaluation.md](../evaluation.md). Carry the agreed conventions into the frozen test protocol; do not choose them using test outcomes. Any unresolved test-specific short-ranking/reference detail must be settled before test execution. Stage-1 development preparation does not authorize opening held-out labels.

## 2. Inputs and prerequisites

- Approved configuration and test protocol frozen in CP2.3, including D-051 preprocessing and D-053 coverage/pool rules
- Frozen split/duplicate isolation rechecked without moving any JD; exact review counts and batching agreed before test workbook preparation
- Test labels reviewed by Dion (gold)
- Evaluation scripts

## 3. Planned method

1. After freeze and separate inference preflight, preserve stage-1 and final application rankings on the same test universe; prepare blind judgments for their per-CV top 10 union under D-053. Compute original-rank NDCG@10/P@5 only with required coverage and common pool/paired CV scope. Final application order retains existing constraints and holds.
2. Evidence Macro-F1, precision and recall per class, confusion matrix, share of assessed units.
3. Extraction precision, recall, F1, and schema validity.
4. Labeled-pool Recall@K as a coverage-qualified diagnostic only; filter recall requires pre-filter relevant judgments or is reported not measured.
5. Safety: hard-negative false positives in the top 10, quote validity, unsupported claims.
6. Latency p50/p95 and cost per run, live and cached separately.
7. Save failure examples in docs/failures.md.

### Privacy preprocessing version at freeze (D-051)

The chosen masking/preprocessing and quote-source convention must be included in the frozen configuration when evaluated. Carry the CP2.3 synthetic privacy robustness results separately; do not use held-out labels to choose masking rules. Any masked-source test evaluation requires a predeclared compatible reference transformation and the existing freeze gate. Do not alter original CVs/gold or claim an unmasked benchmark validates the private-upload path. See [privacy contract](../privacy-threat-model.md).


## 4. Planned outputs

- evaluation scripts
- evaluation report draft
- gold labels with the guideline version
- docs/failures.md entries
- this stage report

## 5. Acceptance criteria

- No "good" claim without a metric.
- Each result records the git SHA, prompt and model versions, cost, and latency.
- Only gold (reviewed) labels are used as ground truth.
- The limitations are written: single annotator, gold size, synthetic CVs, snapshot date.

## 6. Evidence to keep

- metric tables
- evaluation output files
- docs/failures.md
- ledger totals

## 7. Estimate and dependencies

- **Estimate:** The historical half-day/under US$1 estimate is not authorization. Re-estimate frozen-run inference and human review after the top 10 union count, within 2-3 review hours/day and the existing budget guard.
- **Depends on:** Test labels complete and reviewed. This is the most important dependency of CP2.

## 8. Fallback if blocked

If labels are incomplete, report only eligible CV/metric combinations, planned/completed counts and all missing/held reasons. P@5 and NDCG@10 remain unavailable where required original positions lack judgments. Paired comparisons use the same eligible CV subset and judged pool. Never condense ranks, choose only favorable CVs, or treat provisional labels as gold. CV1/CV2 results are familiar-profile/new-job confirmation; CV3-CV5 are held-out-profile/new-job confirmation.

## 9. Checklist

- [x] Original-rank NDCG@10/P@5 for stage-1 versus final application order, with common judged pool and paired eligible CV coverage.
- [ ] Evidence Macro-F1, precision and recall per class, confusion matrix, share of assessed units. Not measured on test (reason in 10b); development values in CP2.3/CP2.5.
- [x] Extraction schema validity (FAIL-33; held jobs in 10b). Extraction precision/recall/F1 not measured on test (reason in 10b).
- [x] Recall limitations and coverage reported (labeled-pool Recall@10 in 10b); filter recall marked not measured.
- [x] Safety: hard negatives in the top 10 and quote validity (10b). Unsupported claims not measurable without test evidence gold.
- [x] Latency p50/p95 and cost per run, live and cached separately (10b).
- [x] Save failure examples in docs/failures.md (FAIL-32, FAIL-33, FAIL-34).
- [x] Acceptance: No "good" claim without a metric.
- [x] Acceptance: Each result records the git SHA, prompt and model versions, cost, and latency (freeze receipt hashes, HEAD 8cfb359d, config v4, 10b).
- [x] Acceptance: Only reviewed labels are used (test_v13_cp24_r1: AI-assisted, human-reviewed, D-088).
- [x] Acceptance: The limitations are written: single annotator, gold size, synthetic CVs, snapshot date.

- [x] D-053 freeze receipt, split isolation, blind pool manifest and original-rank coverage gates verified.
- [x] Per-CV and familiar/held-out-profile groups reported; test results never tune the configuration.

## 10. Results

Run on 7 October 2026 by Dion with `scripts/evaluate_cp24_test.py` on run `cp24_test_v1` and labels `test_v13_cp24_r1` (D-088). Report: `evals/results/cp24/heldout_report_v1.json` (contract `cp24-report-contract-v1`). Freeze D-087 unchanged; nothing was tuned after the result.

**Headline, CV3-CV5 (held-out profiles, held-out jobs)**

| Metric | Stage 1 | Final product order | Coverage |
| --- | --- | --- | --- |
| P@5 macro | 0.533 | 0.733 | 3/3 CV complete (CV3, CV4, CV5) |
| NDCG@10 macro | 0.805 | 0.960 | 2/3 CV complete (CV3, CV4 only). CV5 omitted: F00070 is unjudged at final position 6 |

| CV | P@5 stage 1 -> final | NDCG@10 stage 1 -> final | Judged / pooled pairs |
| --- | --- | --- | --- |
| CV3 | 0.2 -> 0.4 | 0.762 -> 0.950 | 14 / 14 |
| CV4 | 0.8 -> 1.0 | 0.847 -> 0.970 | 12 / 12 |
| CV5 | 0.6 -> 0.8 | 0.582 -> unavailable (`missing_original_position_judgment`) | 14 / 15 |

The NDCG 0.960 is NOT a CV3-CV5 number. It covers CV3 and CV4 only, and the stage-1 macro 0.805 uses the same two CVs so the pair is comparable.

**Supplementary diagnostic, CV1-CV2 (familiar development profiles on held-out jobs).** Never pooled with the headline. P@5 0.30 -> 0.70, NDCG@10 0.688 -> 0.892 (2/2 CV). CV1 0.4 -> 0.6 and 0.845 -> 0.899; CV2 0.2 -> 0.8 and 0.530 -> 0.884.

**Test size:** 3 synthetic held-out CVs in the headline; 68 pooled pairs over CV1-CV5 (D-053 top-10 union), 67 judged and 1 unjudged (CV5/F00070, source-quality hold).

## 10b. Supplementary descriptive results (master-plan steps 4-6)

Computed offline from the saved test run by `scripts/cp24_supplementary_offline.py` (`evals/results/cp24/supplementary_v2/summary.json`, receipt with input hashes). No call, no choice; the headline above is unchanged.

**Process and safety per CV (final top 10)**

| CV | One-CV wall time (s) | Final / provisional / held / no score | Sol done / Luna after a cap refusal / held after a cap refusal / held before matching | Quote validity | Relevance-0 jobs in top 10 | Relevance <= 1 in top 5 |
| --- | --- | --- | --- | --- | --- | --- |
| CV3 | 37.2 | 6 / 1 / 3 / 0 | 6 / 1 / 0 / 3 | 75/75 | F00501 (pos 5) | F00290 (pos 3, rel 1), F00374 (pos 4, rel 1), F00501 (pos 5, rel 0) |
| CV4 | 39.6 | 7 / 2 / 1 / 0 | 5 / 5 / 0 / 0 | 129/129 | none | none |
| CV5 | 84.6 | 5 / 0 / 4 / 1 | 6 / 0 / 3 / 1 | 62/62 | none | F00290 (pos 5, rel 1) |
| CV1 (supplementary) | 87.2 | 5 / 2 / 3 / 0 | 7 / 2 / 0 / 1 | 96/96 | none | F00313 (pos 3, rel 1), F00206 (pos 5, rel 1) |
| CV2 (supplementary) | 80.6 | 7 / 1 / 2 / 0 | 6 / 3 / 0 / 1 | 157/157 | none | F00853 (pos 4, rel 1) |

- Quote validity: 519/519 MATCH/PARTIAL items quote the CV word for word.
- Hard negatives: one relevance-0 job in any final top 10 (CV3/F00501, a Data Engineer post outside the target families, at position 5).
- Matching path (FAIL-34): the runner's own cost cap refused 14 of 44 Sol calls before sending them (the in-flight reservation reached US$2.50 while the real spend was US$0.94). Luna then finished 11, and 3 became holds. So the headline describes the system as run, fallback included, not a pure Sol run. Three of CV5's five unscored jobs (F00071, F00599, F00651) come from this cap, not from the model or the JD.

**Labeled-pool Recall@10 (judged relevant jobs in the D-053 pool)**

| CV | Stage 1 | Final |
| --- | --- | --- |
| CV3 | 2/2 | 2/2 |
| CV4 | 6/6 | 6/6 |
| CV5 | 7/11 | 8/11 |
| CV1 | 3/4 | 4/4 |
| CV2 | 3/5 | 5/5 |

The pool is the union of both top 10s, so this recall only says which order keeps more of the relevant pooled jobs in its top 10; it is not recall over the whole job set. Filter recall: not measured (no optional filter in the test run).

**Cost and latency (usage ledger, run IDs `cp24_test_*`)**

| Phase | Calls | US$ | Call latency p50 / p95 (s) |
| --- | --- | --- | --- |
| extraction | 31 | 0.465 | 41.9 / 165.3 |
| matching | 46 | 0.940 | 27.6 / 44.4 |
| parse | 6 | 0.037 | 38.8 / 77.7 |
| queries | 1 | 0.000 | 2.7 / 2.7 |
| **Total** | | **1.442** | |

One-CV wall time (matching, K = 10, parallel): median 80.6 s (min 37.2, max 87.2). JD extraction is offline and cached per job, so a live user request pays only parsing, the query vector and matching; matching was about US$0.94 / 5 CVs = US$0.19 per CV at K = 10.

**Not measured on test, with the reason**

- Evidence Macro-F1 and extraction F1: the test workbook's A/B sheets were AI-assisted drafts that D-088 did not import (C only), and pipeline units differ from gold units (needs alignment). Development values stand: CP2.3 and CP2.5 (figures 3 and 4).
- Unsupported claims: needs unit-level evidence gold on test.
- Reproducibility record: freeze receipt `cp23_freeze_draft_v2` (57 file hashes, D-087), git HEAD at reporting time `8cfb359d` (Dion commits the reports), prompt and model versions in `config/versions/pipeline_cp23_freeze_candidate_v4_20261006.yaml`.

## 11. Interpretation and limitations

- Final order is higher than stage 1 on every complete headline cell. But each P@5 step of 0.2 is one job in the top 5, and the headline has only three CVs. This is indicative, not a general result.
- Labels are AI-assisted (ChatGPT) and human-reviewed by one reviewer, blind to ranking. They are not independent human gold (D-088).
- Because the labeling assistant and matcher are both OpenAI-family models, correlated model preferences may inflate apparent agreement. The direction and magnitude of this bias were not independently measured. This matters most for the part of the gain that comes from the LLM match order (see CP2.5 figure 11).
- CV5 has 5 of 10 final top-10 jobs without a score (4 held, 1 no score). Three of them come from the runner's cost cap (FAIL-34), one from an incomplete JD, and one is F00070 (no requirements). The product order puts them last; this is a coverage limit, not a relevance claim.
- 14 of 44 Sol calls were refused by the run cap and went to Luna or a hold (FAIL-34), so the headline is the system as run with fallback, not a pure Sol measurement.
- Synthetic CVs, one job snapshot, single run per CV (no repeated-run variance).
- Evidence Macro-F1 and extraction F1 are not measured on test (section 10b); latency, cost, quote validity and hard negatives are in 10b.

## 12. Decisions from this stage

None. The result is reported as is under D-087 and D-088; no model, prompt, K, weight, rule or metric was changed. Decisions are recorded in the [decision log](../decisions.md) when they are made.

## 13. Next step

Done: CP2.5 figures 9-11 and the CP2.6 summary. CP2.4 stays locked from optimization (D-089).

Protocol authority: [D-053 held-out confirmation](../evaluation.md#7-held-out-confirmation-protocol-d-053). Test exposure followed by configuration changes makes reuse a regression check, not new independent confirmation.

## Readiness (6 Oct 2026)

- Freeze candidate and draft receipt: D-086, `evals/freeze/cp23_freeze_draft_v2/`.
- Runner: `scripts/run_cp24_test.py` in six phases (parse CV3-CV5, query vectors, stage 1 on the 214 test jobs, extraction of the analyzed jobs, matching, pool file). Every phase refuses to run without `freeze_receipt_APPROVED.json` and with any file drift. Caps: parse and queries US$0.20 each, extraction US$1.00, matching US$2.50.
- Blind pool and workbook: `scripts/build_cp23_test_workbook.py` (top-10 union per CV, D-053; dry run prints the pair count and effort first).
- Metrics: D-052 conventions, product order (D-073).
- **Report contract (frozen in `cp23_freeze_draft_v2`):** the headline held-out result is CV3-CV5 only. CV1-CV2 are a separate familiar-profile diagnostic. No pooled CV1-CV5 metric is produced; `src/jobfit/eval/heldout_report.py` (`check_contract`) rejects it, and `scripts/evaluate_cp24_test.py` prints only the CV3-CV5 headline. Tested in `tests/test_heldout_report.py`.
- Freeze draft: `evals/freeze/cp23_freeze_draft_v2/` (v1 superseded).

