> **Coordination closure, 2 October2026:** the user-confirmed follow-up supersedes the required-cloud suggestion and pending-note/status snapshot below. Cloud and AWS in F00018 are both preferred under “Will be a plus”. All A/B/C review statuses were completed under delegated QA; rejected decisions remain retained. Active workbook v1.3 is not edited by this technical continuation. F00369 source hold and historical-version/group compatibility remain unresolved. See [current technical/acceptance summary](CP22_Acceptance_Review_20261002.md). The original review observations below remain historical evidence.

# Development labeling review submission

**Date:** 2 October 2026  
**Status:** Human review submitted; QA follow-ups open; gold not exported  
**Original submitted receipt:** [JobFit_Development_Labeling_v0.1_A_B_C_review_v1.3_20261002.xlsx](../../../evals/labeling/archive/review_receipts_20261002/JobFit_Development_Labeling_v0.1_A_B_C_review_v1.3_20261002.xlsx)  
**Guideline:** [v1.3](../../../evals/annotation_guideline_v1_3.md)  
**Input SHA256:** `e78f418ec7dfbb1f2e85af94117e103adf5ebb3f6036d0131c53320c1f573128`

## Original submission result

Dion stated that all labeling was reviewed and submitted this saved workbook. Every populated A/B/C record has review_status=approved and a valid action. Rejected rows remain as history and must not become gold. The approval counts below represent the workbook's human decisions, not an independent accuracy measurement.

| Sheet | Rows | Approved decisions | Rejected | Retained rows |
| --- | ---: | ---: | ---: | ---: |
| A_Extraction | 1,078 | 1,078 | 10 | 1,068 |
| B_Evidence | 1,405 | 1,405 | 16 | 1,389 |
| C_Relevance | 67 | 67 | 0 | 67 |

Scope:54 development JDs,67 CV1/CV2 pairs. All40 designated new relevance rows are reviewed; the additional reviewed rows may expand development evaluation after validation. Test scope is unchanged. Three alternative groups have multiple worksheet branch rows: reconstruct each as one logical OR unit when appropriate, not multiple score contributions.

## Mechanical verification

All populated rows were checked for identity uniqueness, allowed values, JD/CV quote membership, retained A-to-B text/reference equality, and retained evidence coverage for every C pair. These checks passed except the review-note/source/semantic follow-ups below. All54 jobs are in development; no test CV was added. CV source bodies match the working baseline. Sources are unchanged for53 JDs; F00369 differs as described below.

Repeated-qualification review: AUD-028 is resolved because P21-U03 was rejected and P21-U08 retained. AUD-078 is resolved through explicit notes; unchanged label values alone did not mean these cases remained errors. Nested minimums and language conventions need their stated scope carried into evaluation. Existing v0.1/v1.2 records retain provenance and are not silently relabeled v1.3.

## Follow-ups before gold promotion

### Missing reasons in the submitted receipt (nine rows; seven still open)

| A unit | Excel row |
| --- | ---: |
| D2-U08 | 47 |
| P02-U05 | 134 |
| P04-U11 | 149 |
| P04-U18 | 156 |
| P05-U01 | 162 |
| P07-U01a | 170 |
| P07-U01b | 171 |
| P07-U17 | 187 |
| P07-U27 | 198 |

Fill a concise reason consistent with the actual edit. QA does not invent the annotator's reasoning. The labels themselves are populated.

### Source lineage: F00369

The submitted JD extends "A portfolio of pro" to "A portfolio of projects showcasing innovative solutions to real-world ML problems." Dion explained that the extension came from a very similar Google posting. This is not verified as the original JD. The frozen corpus is unchanged. Hold this JD and its related evaluation records until the original source is verified, or use only the original available text with explicitly reviewed dependent units. Do not treat the extension as original-source gold or silently replace the workbook source.

### Two approved local semantic corrections

- P04-U18/F00018: "Practical experience with cloud platforms (AWS stack is preferred...)" makes AWS preferred, not general cloud experience. Proposed representation: required general cloud experience plus preferred AWS, preserving quote and rechecking B/C. Approved by Dion in this chat and applied to the active QA version.
- P07-U17/F00029: debugging is a practice, so knowledge_area is more appropriate than skill_tool under D-049. Approved by Dion in this chat and applied to the active QA version.
- P07-G1 has two branch rows with different guideline versions. Preserve its OR meaning and provenance; verify compatibility before evaluation. Do not count both degree and equivalent experience as independent required units.

### Dependency and policy confirmations

Changes since the original preparation affect113 A records across32 JDs (including added records). Against the latest saved working book, the inventory flags26 jobs for A-semantic/rejection differences. These baselines answer different questions; neither is a reliable timestamp of the user's final B/C recheck. Dion explicitly confirmed B/C were reviewed after the final A changes in the submitted receipt. This confirmation does not cover the subsequent cloud split; only its two B and one C dependencies were reopened. Do not fabricate acknowledgment tokens or review times.

Questions still have20 blank decision cells, including questions already partly answered by D-049 or row notes. Blank administrative answers do not automatically invalidate all labels; resolve or map those that affect the evaluated subset. Timing has missing end times, so actual total review duration cannot be reported. NDCG gain, short P@5, and evidence-failure/absent-class conventions remain evaluation-contract decisions.

## Next step

1. Resolve the small follow-up list; preserve the submitted workbook as the review receipt.
2. Confirm dependent B/C and guideline compatibility on the evaluation subset; prepare a validated approved-only candidate export under explicit export scope.
3. Finish CP2.2's fixture/manual and v1.3 live checks, then compare LLMs, embeddings and retrieval settings on development in CP2.3.
4. Freeze configuration before blind test evaluation. CP2.2 remains IN PROGRESS.

Evidence: [audit JSON](../../../evals/results/development_review_submission_20261002.json), [row follow-ups](../../../evals/results/development_review_followups_20261002.csv). The initial audit was read-only. The subsequent workbook changes below implement Dion's explicit approvals. No actual gold export, model inference or database mutation occurred; session API cost was US$0.


## Approved QA corrections and active workbook

Dion explicitly approved the cloud/importance split and debugging category correction. Active workbook: [JobFit_Development_Labeling_v1.3.xlsx](../../../evals/labeling/JobFit_Development_Labeling_v1.3.xlsx). The original submitted receipt is archived unchanged.

- P04-U18 is now required practical cloud-platform experience, knowledge_area.
- New P04-U18-AWS is preferred AWS-stack experience, skill_tool. A approval records Dion's explicit decision; it does not approve new B evidence.
- P07-U17 debugging is knowledge_area; no unit text/evidence label or score membership changed.
- Existing B CV2×F00018/P04-U18 and new AWS B row remain PARTIAL drafts, pending verification. C CV2×F00018 retains previous value 2 as pending recheck. No unrelated approvals were reset.
- Active counts: 1,079 A (all approved, 10 rejected), 1,406 B (1,404 approved, 2 pending, 16 rejected), 67 C (66 approved, 1 pending).
- Seven edited A notes still need reasons: D2-U08, P02-U05, P04-U11, P05-U01, P07-U01a, P07-U01b, P07-U27. See the current follow-up CSV for exact row locations.

XML preservation verification: 29 package parts unchanged; source sheets JDs/CVs and Timing/Questions/QA_Log exactly preserved. Only README/A/B/C cell changes and A/B table extents were patched. Existing cell styles, panes, widths, dropdown rules and formulas are preserved; new rows inherit existing formats/validation. No actual gold export or paid call.

## Final saved-file verification

The active version passed complete identity, enum, source-quote, A-to-B reference and pair-coverage checks. Its only mechanical follow-ups are the seven missing edit reasons and three intentionally reopened pending records. All 54 JDs remain within development and all 67 pairs use CV1/CV2. The source-lineage and historical semantic exceptions above remain open; mechanical validation is not a claim of perfect semantic accuracy. All 66 local links checked across current indexes and moved reports resolve. Verification: [saved-file QA](../../../evals/results/development_review_final_verification_20261002.json).
