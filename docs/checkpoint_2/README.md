# CP2 Stage Reports: Model Selection, Tuning, and Evaluation

Checkpoints 8 to 14 of the bootcamp timeline, one report per checkpoint, following the same pattern as `checkpoint_1/` (CP1.1 to CP1.6). The checkpoint names come from the bootcamp template; each report says how JobFit adapts it. Presentation date: 4 October 2026.

Every report starts as a plan (status PLANNED / NOT RUN). Results, interpretation, limitations, and decisions are added only after the work is done, with links to the [experiment log](../experiments.md) and the [decision log](../decisions.md).

| Stage | Bootcamp checkpoint (template name) | Report | Official date | Planned work | Status |
| --- | --- | --- | --- | --- | --- |
| CP2.1 | 8. Model Selection (CNN/LSTM/DNN sesuai use case) | [Model and System Selection](CP2_01_Model_and_System_Selection.md) | 28 Sep 2026 | 29-30 Sep 2026 (labeling pilot on the evening of 29 Sep) | DONE |
| CP2.2 | 9. Modeling Deep Learning | [Modeling the Extraction, Search, and Evidence Pipeline](CP2_02_Modeling_Pipeline.md) | 29 Sep 2026 | 1-3 Oct 2026 | DONE (D-050) |
| CP2.3 | 10. Hyperparameter Tuning | [System Tuning](CP2_03_System_Tuning.md) and [Model Comparison](CP2_03_Model_Comparison.md) | 30 Sep 2026 | 2 to 6 Oct 2026 | DONE (freeze D-087; D-091; D-092) |
| CP2.4 | 11. Modeling + Evaluation Metrics | [Evaluation Metrics](CP2_04_Evaluation_Metrics.md) | 1 Oct 2026 | 3 Oct 2026 (ran 6-7 Oct) | DONE |
| CP2.5 | 12. Visualisasi Evaluation Result | [Evaluation Result Visualization](CP2_05_Evaluation_Visualization.md) | 2 Oct 2026 | 3 to 4 Oct 2026 (held-out figures 7 Oct) | DONE |
| CP2.6 | 13. Recommendation & Summary | [Recommendation and Summary](CP2_06_Recommendation_and_Summary.md) | 3 Oct 2026 | 4 Oct 2026 (final 7 Oct) | DONE |
| CP2.7 | 14. PPT Check Point 2 + Mentoring | [CP2 Presentation and Mentoring](CP2_07_Presentation_and_Mentoring.md) | 4 Oct 2026 | 3-4 Oct 2026 (deck draft on 3 Oct) | DONE (presented 4 Oct; D-093) |
| CP2.8 | Phase A: post-test quality optimization (development only) | [CP2.8 Post-Test Quality Optimization](CP2_08_Post_Test_Quality_Optimization.md) | after CP2.4 | 7 Oct 2026 | CLOSED, KEEP BASELINE (D-090) |

The plan behind these reports is the [CP2-CP3 master plan](../master-plan.md).

Supporting record for CP2.1: [model-draft stage of the pilot](supporting/archive/preparation/CP2_01_Pilot_Draft_Review.md) (synthetic CV check and first label drafts, 29 Sep 2026; the decisions that followed are D-032 to D-043).


**CP2 is closed (7 October 2026, [D-094](../decisions.md)).** Before closing it I checked every acceptance criterion against the files in the repository; see the [CP2 closeout audit](CP2_Closeout_Audit_20261007.md). Two CP2.3 items were settled at the end (D-091 extraction scope, D-092 privacy deferral), and the mentor feedback was written up as D-093. What CP3 picks up is in [section 11 of the audit](CP2_Closeout_Audit_20261007.md#11-what-cp3-inherits).

What each stage did:

- **CP2.1** set the labeling rules, schemas, scoring, the pilot labels, the B0/B1 baselines and the model selection rule.
- **CP2.2** built the source-grounded pipeline: CV parsing, JD extraction, evidence matching and retrieval.
- **CP2.3** chose every setting on development data and froze it (D-087). Privacy is implemented and covered by component tests, but end-to-end validation is CP3 work (D-092).
- **CP2.4** ran the frozen system once on the held-out split.
- **CP2.5** turned the development and held-out results into figures with their denominators.
- **CP2.6** wrote up the final architecture, the keep/remove decisions and the error analysis.
- **CP2.7** presented the work on 4 October and took the mentor feedback into CP3 (D-093).
- **CP2.8** tried prompt changes on development data after the test and kept the baseline (D-090). It does not change the held-out result.

**Held-out headline (CP2.4, CV3-CV5 only):** P@5 0.533 -> 0.733 (3/3 CVs); NDCG@10 0.805 -> 0.960 for CV3 and CV4 only (CV5 unavailable because F00070 is unjudged). CV1-CV2 are a separate diagnostic. The labels are AI-assisted, reviewed by one person and blind to the ranking (D-088); the CP2.4 report explains the OpenAI-family limitation.

**Historical note (4 October):** this page used to describe CP2.3 as provisional (D-068, pipeline v1.1 at 42/60) with the held-out evaluation still open. That state is kept in the [CP2.3 report](CP2_03_System_Tuning.md), the [pipeline v1.1 report](supporting/CP23_Pipeline_v11_20261004.md) and the [presentation summary](supporting/CP2_Presentation_Summary_20261004.md).
