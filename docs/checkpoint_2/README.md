# CP2 Stage Reports: Model Selection, Tuning, and Evaluation

Checkpoints 8 to 14 of the bootcamp timeline, one report per checkpoint, following the same pattern as `checkpoint_1/` (CP1.1 to CP1.6). The checkpoint names come from the bootcamp template; each report says how JobFit adapts it. Presentation date: 4 October 2026.

Every report starts as a plan (status PLANNED / NOT RUN). Results, interpretation, limitations, and decisions are added only after the work is done, with links to the [experiment log](../experiments.md) and the [decision log](../decisions.md).

| Stage | Bootcamp checkpoint (template name) | Report | Official date | Planned work | Status |
| --- | --- | --- | --- | --- | --- |
| CP2.1 | 8. Model Selection (CNN/LSTM/DNN sesuai use case) | [Model and System Selection](CP2_01_Model_and_System_Selection.md) | 28 Sep 2026 | 29-30 Sep 2026 (labeling pilot on the evening of 29 Sep) | DONE |
| CP2.2 | 9. Modeling Deep Learning | [Modeling the Extraction, Search, and Evidence Pipeline](CP2_02_Modeling_Pipeline.md) | 29 Sep 2026 | 1-3 Oct 2026 | DONE (D-050) |
| CP2.3 | 10. Hyperparameter Tuning | [System Tuning](CP2_03_System_Tuning.md) and [Model Comparison](CP2_03_Model_Comparison.md) | 30 Sep 2026 | 2 to 6 Oct 2026 | DONE: freeze D-087; extraction scope accepted (D-091); privacy implemented and component/unit tested, end-to-end validation and paired masking comparison deferred to CP3.4/CP3.5 (D-092) |
| CP2.4 | 11. Modeling + Evaluation Metrics | [Evaluation Metrics](CP2_04_Evaluation_Metrics.md) | 1 Oct 2026 | 3 Oct 2026 (actual 6-7 Oct) | DONE: held-out report `heldout_report_v1.json` (D-087, D-088) |
| CP2.5 | 12. Visualisasi Evaluation Result | [Evaluation Result Visualization](CP2_05_Evaluation_Visualization.md) | 2 Oct 2026 | 3 to 4 Oct 2026 (held-out 7 Oct) | DONE: figures 1-11, Phase A A1-A4 |
| CP2.6 | 13. Recommendation & Summary | [Recommendation and Summary](CP2_06_Recommendation_and_Summary.md) | 3 Oct 2026 | 4 Oct 2026 (final 7 Oct) | DONE: final summary after the held-out test |
| CP2.7 | 14. PPT Check Point 2 + Mentoring | [CP2 Presentation and Mentoring](CP2_07_Presentation_and_Mentoring.md) | 4 Oct 2026 | 3-4 Oct 2026 (deck draft on 3 Oct) | Presented and mentored 4 Oct; feedback recorded (D-093). LMS proof not saved: blocks CP2 closure |
| CP2.8 | Phase A: post-test quality optimization (development only) | [CP2.8 Post-Test Quality Optimization](CP2_08_Post_Test_Quality_Optimization.md) | after CP2.4 | 7 Oct 2026 | CLOSED: KEEP BASELINE (D-090) |

The plan behind these reports is the [CP2-CP3 master plan](../master-plan.md).

Supporting record for CP2.1: [model-draft stage of the pilot](supporting/archive/preparation/CP2_01_Pilot_Draft_Review.md) (synthetic CV check and first label drafts, 29 Sep 2026; the decisions that followed are D-032 to D-043).


**CP2 closure (7 October 2026, second pass): NOT YET CLOSED, one evidence item open.** The [CP2 closeout audit](CP2_Closeout_Audit_20261007.md) checks every CP2.1-CP2.7 acceptance criterion against saved files. All acceptance criteria now pass or are resolved by explicit decisions (D-091 extraction scope, D-092 privacy-validation deferral, D-093 mentor feedback). The only open item is the CP2.7 LMS upload proof, an "evidence to keep" item that the master plan requires before a stage is DONE; Dion names its location or records that no upload was required. Rehearsal is not a closure item.

**Story of CP2:** CP2.1 fixed the rules, gold pilot, baselines and selection rule; CP2.2 built the source-grounded pipeline (CV, JD extraction, evidence matching, retrieval); CP2.3 chose every setting on development data and froze it (D-087), with the D-050/D-051 carry-overs resolved by D-091/D-092 (privacy implemented and component/unit tested; end-to-end privacy validation deferred to CP3); CP2.4 ran the frozen system once on the held-out split; CP2.5 visualized development and held-out results with their denominators; CP2.6 gave the final architecture, keep/remove decisions and error analysis; CP2.7 presented the work and handed the mentor feedback to CP3 (D-093); CP2.8 tested prompt changes on development data only and kept the baseline (D-090). CP2.8 does not modify the CP2.4 held-out claim.

| Stage | Primary report | Final status | Evidence current | Report complete |
| --- | --- | --- | --- | --- |
| CP2.1 | [Model and System Selection](CP2_01_Model_and_System_Selection.md) | DONE | Yes | Yes |
| CP2.2 | [Modeling Pipeline](CP2_02_Modeling_Pipeline.md) | DONE (D-050; carry-over closed by D-091) | Yes | Yes |
| CP2.3 | [System Tuning](CP2_03_System_Tuning.md) (+ [Model Comparison](CP2_03_Model_Comparison.md)) | DONE (D-087, D-091, D-092) | Yes | Yes |
| CP2.4 | [Evaluation Metrics](CP2_04_Evaluation_Metrics.md) | DONE | Yes | Yes |
| CP2.5 | [Evaluation Visualization](CP2_05_Evaluation_Visualization.md) | DONE | Yes | Yes |
| CP2.6 | [Recommendation and Summary](CP2_06_Recommendation_and_Summary.md) | DONE | Yes | Yes |
| CP2.7 | [Presentation and Mentoring](CP2_07_Presentation_and_Mentoring.md) | Acceptance met; LMS proof open | Yes | Yes |
| CP2.8 | [Post-Test Quality Optimization](CP2_08_Post_Test_Quality_Optimization.md) | CLOSED, KEEP BASELINE | Yes | Yes |

**Held-out headline (CP2.4, CV3-CV5 only):** P@5 0.533 -> 0.733 (3/3 CVs); NDCG@10 0.805 -> 0.960 for CV3 and CV4 only (CV5 unavailable: F00070 unjudged). CV1-CV2 are a separate diagnostic. Labels are AI-assisted, human-reviewed and blind to ranking (D-088), with the OpenAI-family limitation stated in the CP2.4 report.

**Historical note (4 October):** the paragraph that stood here described CP2.3 as provisional (D-068, pipeline v1.1 at 42/60) with held-out evaluation open. That state is kept in the [CP2.3 report](CP2_03_System_Tuning.md), the [pipeline v1.1 report](supporting/CP23_Pipeline_v11_20261004.md) and the [presentation summary](supporting/CP2_Presentation_Summary_20261004.md).
