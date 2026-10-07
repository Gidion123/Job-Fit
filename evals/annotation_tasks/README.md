# Annotation Task Prompts

Written task prompts for the drafting model (pre-annotation), plus the annotator's review guide. Process and roles: [docs/annotation-workflow.md](../../docs/annotation-workflow.md). Sizes and phases: D-045. Split and test rules: D-046.

Each prompt states its scope, the files the model may change, and the checks it must report. Give one task at a time, with the workbook closed in Excel.

| File | Task | When | Status |
| --- | --- | --- | --- |
| [T02_workbook_cleanup.md](archive/completed/T02_workbook_cleanup.md) | Pilot workbook: neutral field names, layout, J4 changes | 30 Sep | Done |
| [T01_relabel_pilot_relevance_v1.md](archive/completed/T01_relabel_pilot_relevance_v1.md) | Pilot relevance drafts under guideline v1.1 | 1 Oct | Done |
| [T03_split_and_dev_pools.md](T03_split_and_dev_pools.md) | Job-level split, then the development pools | Split now; pools after embeddings (CP2.2) | Part 1 accepted; Part 2 complete (29/34 rows, top-five coverage fits cap) |
| [T04_dev_batch_extraction_evidence.md](T04_dev_batch_extraction_evidence.md) | 3 new development JDs (extraction), then 2 evidence pairs | After T03 split | Full review submitted:1,078 A /1,405 B; follow-up QA before export |
| [T05_dev_relevance.md](T05_dev_relevance.md) | Development relevance: silver for the pool, 40 rows for gold review | After T03 pools | All67 C reviewed, including40 designated new rows; no new gold export |
| [T06_test_batches.md](T06_test_batches.md) | Test relevance (blind, CV1 to CV5) and test extraction/evidence (2 blind, 2 drafted) | Relevance after CP2.3; extraction can start after T03 split | Open |
| [T07_test_cvs.md](T07_test_cvs.md) | Two synthetic test CVs (CV4, CV5), written without looking at test jobs | Before the test pool (by 3 Oct) | Done: content version 0.1 approved by Dion (1 Oct 2026) |
| [REVIEW_GUIDE.md](REVIEW_GUIDE.md) | How Dion reviews a batch | Every batch | |

T07 draft files, fixed reference date, checks, and review points: [T07 review record](../../docs/checkpoint_2/supporting/T07_Test_CV_Drafts_20261001.md). Both CVs have human-approved content version 0.1 and remain test only. Approval provenance: [manifest](T07_approved_cv_manifest_v1.json). No label approval is implied.


Current status:[development review submission](../../docs/checkpoint_2/supporting/Development_Labeling_Review_20261002.md). Do not rerun T03/T04/T05 preparation; workbook review is complete and QA follow-ups remain. Completed T01/T02 are in archive/completed.
