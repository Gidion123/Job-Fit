# CP3 Stage Reports: Deployment, Streamlit, and Final Presentation

Checkpoints 15 to 21 of the bootcamp timeline, one report per checkpoint, following the same pattern as `checkpoint_1/` (CP1.1 to CP1.6). The checkpoint names come from the bootcamp template; each report says how JobFit adapts it. Presentation date: 11 October 2026.

Every report starts as a plan (status PLANNED / NOT RUN). Results, interpretation, limitations, and decisions are added only after the work is done, with links to the [experiment log](../experiments.md) and the [decision log](../decisions.md).

| Stage | Bootcamp checkpoint (template name) | JobFit scope | Report | Official date | Planned work | Status |
| --- | --- | --- | --- | --- | --- | --- |
| CP3.1 | 15. Deployment API menggunakan Flask/FastAPI | Public-beta API for both flows, safety controls and instrumentation | [API Deployment with FastAPI](CP3_01_FastAPI_Service.md) | 5 Oct 2026 | 5 Oct; CP3 additions 8 Oct | PARTIAL (demo flow done locally; Phase 2A settings and bounds done, full bound above the cap; Phase 2B dark safety layer and persistent production ledger done (local/CI); public path PLANNED) |
| CP3.2 | 16. Integrasi Database & GitHub Actions CI/CD | Production corpus, job sync, VPS and delivery | [Database Integration and CI/CD](CP3_02_Database_and_CICD.md) | 6 Oct 2026 | 6 Oct; CP3 additions 8-9 Oct | PARTIAL (CI green after Phase 1; not deployed) |
| CP3.3 | 17. Build Streamlit UI | Product experience: Find Jobs, Check a Job, stage-aware progress, "Improve My CV for This Job" | [Streamlit UI](CP3_03_Streamlit_UI.md) | 7 Oct 2026 | 7 Oct; CP3 additions 8-9 Oct | PARTIAL (demo flow done locally) |
| CP3.4 | 18. Testing End-to-End Application | Controlled public beta validation, privacy release gate and feature freeze | [End-to-End Testing](CP3_04_End_to_End_Testing.md) | 8 Oct 2026 | 9 Oct (formal freeze at the end of 9 Oct, D-100) | PARTIAL (local checks passed) |
| CP3.5 | 19. PPT Final Project / Portfolio | Final evidence, D-045, privacy and latency reports, deck and video | [Final Presentation and Portfolio](CP3_05_Final_Presentation_and_Portfolio.md) | 9 Oct 2026 | 10 Oct | PLANNED / NOT RUN |
| CP3.6 | 20. Finalisasi Portfolio & Rehearsal Presentation | Regression, rehearsal and release tag | [Finalization and Rehearsal](CP3_06_Finalization_and_Rehearsal.md) | 10 Oct 2026 | 10 Oct | PLANNED / NOT RUN |
| CP3.7 | 21. Final Project Presentation + Pemberian Tugas Portofolio | Present deployed JobFit with the saved-demo fallback | [Final Presentation and Submission](CP3_07_Final_Presentation_and_Submission.md) | 11 Oct 2026 | 11 Oct | PLANNED / NOT RUN |

The plan behind these reports is the [CP2-CP3 master plan](../master-plan.md).

**CP3 scope clarified (8 Oct 2026, [D-102](../decisions.md)):** JobFit is a production-grade AI engineering portfolio with a controlled public beta on one VPS, not an enterprise SaaS. Two first-class flows: **Find Jobs** (CV → retrieval → matching) and **Check a Job** (CV + pasted JD → matching; the JD is never added to the corpus). New requirements: stage-aware analysis progress and "Improve My CV for This Job" with a hard anti-fabrication rule. Tasks use the public-beta acceptance bar (safe, cost bounded, privacy aware, observable, honest about limits; manual recovery acceptable for rare uncertain states). Public live is still blocked by the D-096 bound until a separate decision.

**CP3 plan frozen (7 Oct 2026, D-095 to D-100):**
- **Product:** full public live JobFit on a SumoPod VPS, with the saved demo as the fallback (framing clarified on 8 Oct by D-102: controlled public beta, see above).
- **Budgets and limits:** a US$5 CP3 validation budget; a US$2/day production cap with deterministic phase bounds; one live analysis per IP per 24 h; one live analysis at a time. *(Amended for the public beta by D-103, 8 Oct: US$5/day and US$25 lifetime, per-phase beta bounds.)*
- **Job corpus:** a production corpus refreshed from JSearch twice a month (about every two weeks).
- **Monitoring:** Prometheus and Grafana with email alerts; Langfuse Cloud (Japan) with metadata only. *(8 Oct, D-103: self-hosted Prometheus and Grafana OSS with node_exporter, Grafana private through an SSH tunnel; email alerts P2 (post-beta); Langfuse Cloud free tier required for the final beta.)*
- **Evaluation:** D-045 to be completed with option B (planned, not yet completed).
- **Freeze:** the formal feature freeze is at the end of 9 October.

Official stage names are unchanged; the JobFit scope column is a subtitle only. Nothing new is marked done until its acceptance evidence exists.

How the documents divide the work:

| Document | Role |
| --- | --- |
| [Master plan](../master-plan.md) | Source of truth for what each stage must achieve, its acceptance criteria and Definition of Done |
| [CP3 execution plan](CP3_Execution_Plan.md) | Daily checklist: task, priority, dependency, owner, status, validation, evidence |
| CP3.1-CP3.7 reports (this folder) | Evidence and results |
| [Production corpus](../production-corpus.md) | Design of the mutable production job database and the sync |
| [Decision log](../decisions.md) | Why each choice was made |
| [Failure log](../failures.md) | Known defects (FAIL-35 resolved in Phase 1; FAIL-36 to FAIL-38 are open) |
| [Runbook, 6 Oct](Runbook_Freeze_Test_Deploy_20261006.md) | Freeze and held-out test steps. Its Railway deploy section is superseded by D-095 |

**Inputs from CP2 (closed 7 Oct 2026, D-094):** the frozen configuration D-087 with evidence prompt v1.1 (D-090), and two follow-ups from CP2. First, the mentor feedback in [D-093](../decisions.md): a clear waiting state for the long LLM analysis (check the existing progress bar and spinner first), and vacancy-specific CV guidance once the core flow is stable (part of the [CV coach plan](../cv-coach-plan.md)). Second, the privacy work deferred by [D-092](../decisions.md): privacy is implemented and covered by component tests only, so CP3.4 runs the end-to-end privacy checks and the original-vs-masked comparison, and CP3.5 reports them. Full list: [CP2 closeout audit, section 11](../checkpoint_2/CP2_Closeout_Audit_20261007.md#11-what-cp3-inherits).
