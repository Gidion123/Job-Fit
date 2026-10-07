# Development Pools and Review Batches

**Stage:** CP2.2, T03 Part 2, T04 steps 1-2, T05 draft preparation  
**Date:** 1 October 2026  
**Status:** Pool construction complete; annotation drafts ready for human review. No expanded gold export.

## 1. Purpose

Prepare a comparable development pool for the six retrieval candidates and two review workbooks. The pool is a labeling sample, not a recommended-job list or a model-quality result. Human review precedes gold export and tuning.

## 2. Inputs and controls

- Frozen snapshot CP1_20260926 and frozen 214/214 job split under D-046.
- Approved synthetic CV1/CV2 only. CV3/CV4/CV5 and test labels are excluded.
- Existing two-model corpus vectors and approved-development query caches. No inference required.
- Guideline v1.2, approved D-045 review capacity, task instructions T03/T04/T05.
- Original pilot workbook and existing gold CSV are read-only. Their hashes remain unchanged.

## 3. Pool construction

Run B0 keyword, B1 FTS, dense OpenAI, hybrid OpenAI, dense Qwen, and hybrid Qwen inside the 214 development IDs. Each method returns up to 20 jobs; the labeling pool unions each method's top 10. RRF k=60 and branch depth=20 remain implementation defaults, not a configuration selected on evaluation results.

Select every new top-five candidate first, then seeded random remaining candidates to reach 20 new review rows per CV. An explicit guard blocks selection if the mandatory union exceeds the cap. No mandatory candidate was dropped in this run.

| CV | Pool rows | Existing gold in pool | New top-five union | New designated reviews |
| --- | ---: | ---: | ---: | ---: |
| CV1 | 29 | 1 | 17 | 20 |
| CV2 | 34 | 2 | 18 | 20 |
| Total | 63 | 3 | 35 | 40 |

All 10 approved pilot relevance labels remain in development, including the seven pairs outside the new pool. The target is still 10 existing plus 40 reviewed new labels, not 63 gold labels.

Evidence: `evals/pools/dev_pool.csv`, `evals/results/t03_dev_pool_20261001.json`. Code: `scripts/build_dev_pools.py`, `src/jobfit/search/pools.py`.

## 4. Extraction batch

| Batch ID | Job ID | Selection reason | Draft units |
| --- | --- | --- | ---: |
| D1 | F00103 | Indonesian internship with required/preferred qualifications and a location commitment | 36 |
| D2 | F00074 | LLM/RAG application engineering with qualified production experience | 26 |
| D3 | F00012 | Senior ML leadership with nested five-year/two-year experience conditions | 22 |

All selected jobs are new development jobs, not pilot jobs, with cleaned text at least 1,500 characters. The snapshot quality label is `full`; the task's wording `ok` does not exist in this snapshot. This uses the existing quality signal and does not introduce a new quality rule or guarantee completeness.

Workbook: `evals/labeling/dev_batch_01.xlsx`. It preserves the pilot column conventions, validation lists, editable review fields, and Timing formulas. A_Extraction has 84 pending units. B_Evidence is empty and must remain empty until the extraction review is approved.

Review questions include mixed-category alternatives, the phrase "menjadi prioritas", possible repeated weighting of a RAG umbrella and components, nested duration conditions, and vague focus-area qualifications. No new rule is approved by these drafts.

## 5. Relevance batch

Workbook: `evals/labeling/dev_batch_02.xlsx`. It contains 60 new CV/job drafts; the three already-gold pairs in the pool are omitted from its relevance sheet. Forty rows have `gold_review=yes`, sorted first in a seeded random order. Twenty others remain unreviewed candidates. All 60 rows are pending, and retrieval method origins, ranks, and scores are absent from the review workbook.

| CV | Draft 0 | Draft 1 | Draft 2 | Draft 3 | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| CV1 | 1 | 16 | 8 | 3 | 28 |
| CV2 | 1 | 21 | 10 | 0 | 32 |

These are draft judgments, not gold, not observed system accuracy, and not a percentage-to-relevance conversion. Most high-duration engineering jobs have limited support from these two early-career synthetic profiles. The absence of CV2 draft label 3 is a warning about positive-label diversity, not evidence that CV2 has no realistic jobs in the corpus.

F00020 is an apparent role-filter false positive: v0 assigns AI/ML engineering, but the JD describes teaching/mentoring. Both draft relevance labels are 0 under Part D's target-family condition. Questions records this for human review. The original taxonomy and snapshot remain unchanged.

Two other important review cases are whether CV2's marketing analytics is a "similar" professional DS position in F00036, and how a Communication degree relates to specific technical-degree clauses. A draft does not resolve these ambiguities for the annotator.

## 6. Verification

- Database-enabled project suite: **125 passed in 7.67 seconds**. Offline suite: 123 passed, two database tests skipped.
- Pool selection tests cover deterministic random filling, exclusion of existing gold, all mandatory top-five rows, and blocking an over-cap union.
- Read-only workbook QA verifies all exact JD and CV text, 84 exact source quotes, unique unit IDs, matching draft bundle content, complete pool-pair coverage, 20 designated reviews per CV, pending status, validations, filters, empty evidence sheet, and blank Timing outputs.
- Protected snapshot, split, guideline, pilot workbook, and approved relevance hashes are unchanged.
- All 15 worksheet previews rendered and inspected. Source cells retain full text; their row height is a preview. Long JDs also appear in `evals/labeling/sources/development_jds.md` for uninterrupted reading.
- API calls for this stage: **0**. Additional project API cost: **US$0**. Previously recorded total remains US$0.01226822.

Audit: `evals/results/development_workbook_qa_20261001.json`. Validation command: `env-job-fit/bin/python scripts/validate_development_review.py` before human edits. Its pending-draft assertions intentionally do not apply after human approval.

## 7. Limitations and review workflow

Pool-based relevance cannot establish recall against every relevant job in all 214 development jobs. Unjudged jobs are not automatically irrelevant. The pool favors candidates found by the six methods, so keep evaluation scope explicit.

Human review has not happened for this batch. No new label is gold, no model/prompt/K is selected, and no test labeling pool is created.

Guideline v1.2 Part E/D-038 calls for about 10% annotator-first blind labeling, while T05 requests drafts for every development row. Dion resolved the question in D-047: prepare all development drafts, then he reviews them. No four-row blind development subset is created. Held-out test stays blind-first. Report the development anchoring limitation; do not describe draft review as blind. No label is approved by this workflow decision.

## 8. Next actions

1. Dion reviews A_Extraction, resolves the relevant Questions, and records actual time. Review 84 units across three JDs; split sessions to fit the daily capacity.
2. Review C_Relevance from the completed drafts under D-047. Start with the 40 designated rows, 20 per CV, to fit the capacity plan; all 60 drafts are available if Dion reviews the whole pool.
3. After sheet A approval, draft evidence for CV1 x D1 and CV2 x D2, followed by human review.
4. Export only reviewed approved rows to development gold. Handle rejected and unresolved cases explicitly; unreviewed rows stay non-gold.
5. Continue the independent CV parser, JD extraction, evidence-matching and paste-JD vertical slice. Tuning requires the reviewed development labels. Held-out test remains separate.

## 9. Workbook template and validation repair

Dion reported a validation error in `review_action` and requested both development workbooks to follow the pilot template. The review lists were rebuilt with the same allowed values: `accepted`, `edited`, `rejected`, and `added`. Blank review cells are explicitly permitted, dropdowns are enabled, and invalid entries receive a specific message. Header styles, fonts and source-column widths follow the pilot. Review controls and time fields have readable widths. Existing tables, filters, sheet names, source text, labels, notes and Timing formulas are preserved. `gold_review` remains the required extra field for relevance selection.

The saved files were independently reopened and compared with a pre-edit snapshot. Every existing cell value and formula is unchanged. The pilot file hash is unchanged. Fifteen worksheet views were rendered and checked. Native XML contains one validation rule per relevant column, exact allowed lists, explicit blank handling and visible dropdown flags. Direct interaction with Microsoft Excel was not tested. The artifact exporter omitted two documented flags, so a targeted serialization correction added only `allowBlank` and `showDropDown`; no cell content was written by that correction.

Human review had already started: A_Extraction contains **83 pending and 1 approved** row. The approved row's action is still blank and was left for Dion to complete. C_Relevance retains **60 pending** rows. B_Evidence remains empty. The initial all-pending QA in section 6 is historical and must not be used to reset human edits.

Audit: `evals/results/labeling_template_repair_20261001.json`. No annotation rule, gold label, split or API cost changed.

## Complete development workbook (2 October 2026)

Current active file: `evals/labeling/JobFit_Development_Labeling_v0.1.xlsx`, under D-048. Earlier batch-specific results are historical.

| Section | Total rows | Previously approved | Pending review |
| --- | ---: | ---: | ---: |
| A_Extraction | 1,069 | 39 | 1,030 |
| B_Evidence | 1,387 | 21 | 1,366 |
| C_Relevance | 67 | 3 | 64 |

The workbook covers 54 development JDs and 67 CV1/CV2 pairs. The frozen pool itself remains 53 JDs and 63 pairs. Four optional pairs provide full CV1/CV2 coverage of the three originally selected extraction JDs, including the retained senior JD outside the relevance pool. All original 84 extraction rows and 60 relevance drafts, including human edits, remain unchanged. Applicable approved pilot rows are copied with their original provenance.

Independent saved-file checks passed: exact source/CV quotes, complete pair-to-unit coverage, unchanged protected sources and rows, development split isolation, 40 designated relevance reviews, saved dropdown rules, and 13 semantic spot checks. Timing formulas were checked with ordinary and midnight-crossing text times and numeric Excel times. All nine sheets were rendered and inspected. Native Microsoft Excel interaction was not exercised. Audit: `evals/results/development_combined_workbook_qa_20261002.json`. The validator describes the initial preparation snapshot; after human edits, do not restore old labels to make that snapshot check pass.

F00364 contains responsibilities without qualifications, so its zero A/B units are intentional. F00369 ends with an incomplete clause, which was not reconstructed. Questions and QA_Log record remaining semantic issues. Relevance remains an ordinal evidence judgment, not a mathematical conversion of match percentage.

The two original workbooks are archived byte-for-byte in `evals/labeling/archive/pre_combined_20261002/`. The pilot remains untouched. New draft labels are pending, and no gold export or tuning occurred. Project API calls for this preparation: 0. Additional cost: US$0; existing ledger total remains US$0.01226822.

Review priority remains D-045: A for D1/D2/D3, B for CV1×D1 and CV2×D2, and C filtered to `gold_review = yes`. Extra rows are optional. If extraction changes, recheck linked evidence and affected relevance before export. CP2.2 remains IN PROGRESS; the independent parser/extraction/matching vertical slice remains unfinished.

## Full first semantic audit and correction STOP (2 October 2026)

All 54 saved development JD sources, CV1/CV2, 1,069 A units, 1,387 B rows and 67 C judgments received a first semantic pass. This does not approve labels or guarantee remaining drafts. The [new audit report](Development_Labeling_Semantic_Audit_20261002.md) separates 51 clear draft errors, 38 ambiguous cases and 3 source/guideline limitations, with a detailed register, current-value evidence, dependent B/C identities and per-JD coverage. One discussion item references approved CV1/F00022/J1-U17; that human decision remains protected.

Important corrections concern repeated units, AND represented as OR, lost or invented qualifiers, technical practice labeled soft_skill, and quotations credited for more specific activities than they show. C explanations invent leadership in F00074 or promote listed dashboard skill into work in F00438. C is reassessed qualitatively after corrections, never calculated from MATCH counts. F00364's empty A/B and F00369's incomplete source remain intentional/limited.

The file was saved externally while the audit was running. Only two leading spaces in new B draft notes and the A freeze pane changed; labels, sources, review metadata and counts stayed unchanged. Latest audited hash is `8be2b05635cc4175f71e2a38cd39dfaa9f17f2f4e4d78d80b20b57516fe733ad`, captured at 09:13:08 WIB. Approved/pending counts remain A 39/1,030; B 21/1,366; C 3/64. No workbook edit was made by the audit. Historical initial QA was not rerun or overwritten; final separate mechanical audit passed 27 checks.

Next: read the summary (about 20–30 minutes), decide priority rule questions and authorize corrections before any workbook write. Preserve D-045 A D1/D2/D3, B CV1×D1/CV2×D2, C gold_review=yes; optional drafts are not mandatory. Actual remaining priority counts are 82 A + 62 B + 40 C, approximately 4.5 hours at the recorded planning averages before clarification/QA (roughly 5 hours with QA, 2–3 sessions). This is a planning estimate, not measured new review time. No API calls, gold export or tuning; ledger US$0.01226822. CP2.2 remains IN PROGRESS.


## Authorized pending corrections (2 October 2026)

The user authorized clear pending corrections and deferred new grouping/denominator/equivalence/language decisions. Applied A first: 13 A rows, then 33 B rows and 2 C rationales, all pending. Rechecked 14 linked B rows and 23 C pairs. All 63 approved rows, source sheets, human metadata, counts, groups, score membership and C values remain unchanged. 27 checks passed; no API/export/tuning. [Correction report](Development_Labeling_Pending_Corrections_20261002.md) and evals/results/development_labeling_pending_corrections_20261002.json record before/after and deferred decisions. Workbook is released for human review; do not write it during independent pipeline implementation. CP2.2 remains IN PROGRESS.
