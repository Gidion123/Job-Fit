# CP3 Stage Reports: Deployment, Streamlit, and Final Presentation

Checkpoints 15 to 21 of the bootcamp timeline, one report per checkpoint, following the same pattern as `checkpoint_1/` (CP1.1 to CP1.6). The checkpoint names come from the bootcamp template; each report says how JobFit adapts it. Presentation date: 11 October 2026.

Every report starts as a plan (status PLANNED / NOT RUN). Results, interpretation, limitations, and decisions are added only after the work is done, with links to the [experiment log](../experiments.md) and the [decision log](../decisions.md).

| Stage | Bootcamp checkpoint (template name) | Report | Official date | Planned work | Status |
| --- | --- | --- | --- | --- | --- |
| CP3.1 | 15. Deployment API menggunakan Flask/FastAPI | [API Deployment with FastAPI](CP3_01_FastAPI_Service.md) | 5 Oct 2026 | 5 Oct 2026 | DONE LOCALLY |
| CP3.2 | 16. Integrasi Database & GitHub Actions CI/CD | [Database Integration and CI/CD](CP3_02_Database_and_CICD.md) | 6 Oct 2026 | 6 Oct 2026 (hosting smoke deploy earlier, on 1-2 Oct) | PARTIAL (deploy pending) |
| CP3.3 | 17. Build Streamlit UI | [Streamlit UI](CP3_03_Streamlit_UI.md) | 7 Oct 2026 | 7 Oct 2026 | DONE LOCALLY |
| CP3.4 | 18. Testing End-to-End Application | [End-to-End Testing](CP3_04_End_to_End_Testing.md) | 8 Oct 2026 | 8 Oct 2026 (feature freeze at the end of the day) | PARTIAL (local checks passed) |
| CP3.5 | 19. PPT Final Project / Portfolio | [Final Presentation and Portfolio](CP3_05_Final_Presentation_and_Portfolio.md) | 9 Oct 2026 | 9 Oct 2026 | PLANNED / NOT RUN |
| CP3.6 | 20. Finalisasi Portfolio & Rehearsal Presentation | [Finalization and Rehearsal](CP3_06_Finalization_and_Rehearsal.md) | 10 Oct 2026 | 10 Oct 2026 | PLANNED / NOT RUN |
| CP3.7 | 21. Final Project Presentation + Pemberian Tugas Portofolio | [Final Presentation and Submission](CP3_07_Final_Presentation_and_Submission.md) | 11 Oct 2026 | 11 Oct 2026 | PLANNED / NOT RUN |

The plan behind these reports is the [CP2-CP3 master plan](../master-plan.md).

**Inputs from CP2 (closed 7 Oct 2026, D-094):** the frozen configuration D-087 with evidence prompt v1.1 (D-090); the checkpoint-14 mentor feedback [D-093](../decisions.md) (A: a clear waiting state for the long LLM analysis, checked against the existing progress bar and spinner in the UI; B: vacancy-specific CV improvement guidance after the core flow is stable, extending the [CV coach plan](../cv-coach-plan.md)); and the privacy validation deferred by [D-092](../decisions.md): privacy is implemented and component/unit tested only, so CP3.4 runs the end-to-end privacy validation (leakage, logs, outputs, consent and session behavior) and the original-vs-masked comparison, and CP3.5 reports the final privacy evaluation and matching-quality impact. See the [CP2 closeout audit, section 12](../checkpoint_2/CP2_Closeout_Audit_20261007.md#12-cp2-to-cp3-handoff).
