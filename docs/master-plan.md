# JobFit CP2-CP3 Master Plan

## Current outcome, 8 October 2026: CP3 scope clarified (D-102)

**North star:** JobFit is a production-grade AI engineering portfolio with a controlled public beta. It shows end-to-end AI engineering on one real VPS that real public users can try in a limited, controlled way, and it should feel like a small real product. It is not an enterprise SaaS. [D-102](decisions.md) clarifies D-026, D-036, D-093 and D-095; it changes no frozen or accepted work (D-087, D-096 bounds and cap, D-097 to D-101, the Alembic work, the persistent production ledger).

- **Two first-class flows:**
  ```text
  Flow A, Find Jobs:    CV → parse / mask / consent → runtime embedding → production retrieval → requirement extraction
                           → evidence matching → scoring and ranking → explanation → job cards → optional CV improvement
  Flow B, Check a Job:  CV + pasted JD → requirement extraction → evidence matching → scoring → explanation
                           → strengths and gaps → CV improvement          (no retrieval; the JD is never added to the corpus)
  ```
- **New product requirements:** stage-aware analysis progress from real pipeline stages (no fake percentages); "Improve My CV for This Job" with a hard anti-fabrication rule (representation improvement, possibly missing, true gap); a portfolio-ready UI. UI priority: clarity > trust > usability > polish > decoration.
- **Priority filter:** about 70% AI and product value, 30% infrastructure. Essential safety, privacy and evaluation are never cut.
- **Public-beta bar:** safe for controlled public use, cost bounded, privacy aware, testable, observable, maintainable, deployable and honest about limits. Unknown → fail closed → log or metric → manual review is acceptable for rare uncertain states. Enterprise HA, multi-region and distributed recovery are out of scope.
- **Public is not admin:** public users get only the end-user app; every operator, database, secret and dashboard interface stays private.
- **Recommended order of the remaining work (anti-overengineering correction, 8 Oct):** foundation closeout → **public-live cost/profile decision** → real-user AI path → product UX → lean production packaging → lean monitoring → dark VPS deploy → privacy, quality and cost validation (including PR-10 and D-045 option B) → controlled public beta → final portfolio and reporting. Details and rows: [CP3 execution plan](checkpoint_3/CP3_Execution_Plan.md#remaining-work-in-recommended-order-d-102-anti-overengineering-correction-8-oct).
- **Post-beta (not blockers):** automated job sync, forced-command SSH, scheduled `job-sync.yml` and dedupe-review automation (D-098 design kept; the seeded corpus is enough, with an optional one-time manual refresh); Langfuse, email alerts and extra dashboards; automated nightly backups (a verified backup and restore test is still required); LLM-written CV rewriting.
- **Open gates (separate decisions needed):** first, the public-live cost/profile decision, the next explicit Dion and Codex architecture decision before large Phase 3 work (US$84.7704449 > US$2/day; D-096 still blocks public live; the bound, the frozen configuration and the cap stay unchanged until then); Flow B in production (D-101 keeps `/analyze` closed until a pasted-JD bound exists); any LLM-written CV wording; the D-100 dates stay as they are unless a decision moves them.

## Current outcome, 7 October 2026

### CP3 plan frozen (7 Oct 2026, D-095 to D-100)

Dion and Codex approved the CP3 final execution plan:
- **Product:** full public live JobFit on a SumoPod VPS (Singapore), with the saved demo as the zero-cost fallback. *(Framing clarified on 8 Oct by D-102: a production-grade AI engineering portfolio with a controlled public beta; see above.)*
- **Budgets:** a US$5 CP3 validation budget; a US$2/day production cap with deterministic phase bounds; one live analysis per IP per 24 h; one live analysis at a time.
- **Job corpus:** a production corpus refreshed from JSearch twice a month (about every two weeks), with exact dedupe and fuzzy suspects held back for review.
- **Monitoring:** Prometheus and Grafana with email alerts; Langfuse Cloud (Japan) with metadata only.
- **Evaluation:** D-045 to be completed with option B (planned, not yet completed).
- **Freeze:** the formal feature freeze is at the end of 9 October. The presentation stays on 11 October.

Everything below for CP3.1-CP3.7 is **PLANNED** unless a line says it is done locally; nothing is deployed or validated on a host yet. The daily checklist is the [CP3 execution plan](checkpoint_3/CP3_Execution_Plan.md), and the corpus design is in [production-corpus.md](production-corpus.md).

| Stage (official name) | JobFit scope | Status |
| --- | --- | --- |
| CP3.1 API Deployment with FastAPI | Public-beta API for both flows, safety controls and instrumentation | PARTIAL: demo flow done locally; Phase 2A fail-closed settings and phase bounds done (7 Oct; the full bound is above the US$2/day cap, so public live is not eligible); Phase 2B dark cost-safety runtime done (8 Oct, D-101); persistent production ledger DONE for Phase 2 acceptance (local/CI; deployed-host validation pending Phase 8); public path PLANNED |
| CP3.2 Database Integration and CI/CD | Production corpus, job sync, VPS and delivery | PARTIAL: CI green after Phase 1 (FAIL-35 resolved); Alembic `0001`/`0002` done with migration tests (8 Oct); not deployed |
| CP3.3 Streamlit UI | Product experience: Find Jobs and Check a Job, stage-aware progress, "Improve My CV for This Job" (D-102) | PARTIAL: demo flow done locally |
| CP3.4 End-to-End Testing | Controlled public beta validation, privacy release gate and feature freeze | PARTIAL: local 27/27; deployed checks PLANNED |
| CP3.5 Final Presentation and Portfolio | Final evidence, D-045, privacy and latency reports, deck and video | PLANNED |
| CP3.6 Finalization and Rehearsal | Regression, rehearsal and release tag | PLANNED |
| CP3.7 Final Presentation and Submission | Present deployed JobFit with the saved-demo fallback | PLANNED |

### CP2

**CP2 is closed (D-094).** Before starting CP3 I checked every CP2.1-CP2.7 acceptance criterion against the files in the repository; the result is in the [CP2 closeout audit](checkpoint_2/CP2_Closeout_Audit_20261007.md).

| Stage | Status |
| --- | --- |
| CP2.1 Model and System Selection | DONE |
| CP2.2 Modeling Pipeline | DONE (under D-050; carry-over closed by D-091) |
| CP2.3 System Tuning | DONE (freeze D-087; D-091; D-092) |
| CP2.4 Evaluation Metrics | DONE |
| CP2.5 Evaluation Visualization | DONE |
| CP2.6 Recommendation and Summary | DONE |
| CP2.7 Presentation and Mentoring | DONE (presented 4 Oct; feedback in D-093) |
| CP2.8 Phase A (post-test, development only) | CLOSED, KEEP BASELINE (D-090) |

- **Frozen system (D-087):** Hybrid FTS + Qwen3 dense with RRF, seniority rule over the stage-1 top 30, K = 10 analyzed, DeepSeek Flash JD extraction (JD prompt v1.4 experimental), GPT-6 Sol matching with GPT-6 Luna fallback, evidence prompt v1.1, quote check v1.1 with G1/G2, H2v2 holds, PARTIAL weight 0.5, experience block, product order.
- **Held-out result (CV3-CV5 only):** P@5 0.533 -> 0.733 (3/3 CVs). NDCG@10 0.805 -> 0.960 for CV3 and CV4 only; CV5's final NDCG is unavailable because F00070 is unjudged, and unjudged jobs are never counted as 0. CV1-CV2 are a separate diagnostic and are never pooled with the headline. The labels are AI-assisted, reviewed by one person and blind to the ranking (D-088). Because the labeling assistant and the matcher are both OpenAI-family models, correlated preferences may inflate agreement; I did not measure how much.
- **Phase A (CP2.8):** a development-only prompt study after the test. No challenger qualified, so prompt v1.1 stays (D-090). It does not change the CP2.4 result.
- **Closed on 7 Oct:** D-091 accepts the 52 development JDs that were actually extracted; the other 162 could not affect any CP2 choice. D-092 records privacy as implemented and component/unit tested, but not validated end to end; the end-to-end checks and the original-vs-masked comparison move to CP3.4 and CP3.5. D-093 records the mentor feedback for CP3: a waiting-state UX for the ~95 s LLM wait, and vacancy-specific CV guidance once the core flow is stable.
- **CP3 started from** section 11 of the closeout audit; its scope is now set by D-095 to D-100 (above).
- **Ledger:** US$10.53, including US$0.25 of uncertain reservations, against the US$18.5 hard stop.

The notes below are dated snapshots, kept to show how the project got here. Where they disagree with this section, this section is current.

## Historical status snapshots, 3-4 October 2026

**Historical outcome, 4 October 2026:** CP2.3 remains IN PROGRESS. D-068 provisionally selects Hybrid Qwen and DeepSeek Flash on development. The capped Part B check saved all 60 pair records, with 20 final numeric scores. The later versioned pipeline v1.1 experiment raised process-valid JD extraction from 37/51 to 48/51 and produced 26 final plus 16 explicitly provisional H2 scores, or 42/60 usable, below its 54/60 target. No final-order cell is complete across 36 CV/K/weight/H1-or-H2 settings, and one-CV K20 end-to-end latency is still unmeasured. [Pipeline v1.1 report](checkpoint_2/supporting/CP23_Pipeline_v11_20261004.md) records the unchanged holds, semantic limitations and US$0.6281001646 of accounted cost against its US$3.00 cap. K20 and PARTIAL weight 0.5 remain provisional. Eight development figures and a [presentation summary](checkpoint_2/supporting/CP2_Presentation_Summary_20261004.md) are ready. D-050 broad extraction and D-051 privacy impact remain open; CP2.4 test evaluation has not run. CP2.2 remains DONE under D-050. **Audit update (D-072 to D-076):** [audit fixes report](checkpoint_2/supporting/CP23_Audit_Fixes_20261004.md).

**Historical D-064 reference snapshot, before the repair replay:** The separate reference and round-two run completed 19 stages in 25 calls for US$0.4054182374. Fixed-input evidence was measured: GPT Sol Macro-F1 0.818094 and DeepSeek Pro 0.496283, including its failed pair. Its new extraction mappings remain pending. The ledger then totaled US$1.1735639842, including US$0.0210861 of historical uncertain cost. The later repair replay and current ledger are stated above. [Reference results](checkpoint_2/supporting/CP23_Stage2_LLM_Comparison_20261003.md#9-d-064-measured-follow-up-and-current-closure-boundary).

**Historical extraction-only takeover snapshot:** Stage 2 extraction collection completed under D-059 (28/28 attempted; 27 final process-valid drafts, one retained process failure). Source QA and exact cost/timing inventory are recorded; candidate alignment/F1 and evidence matching remain open. Stage 3 retrieval/embedding is measured on the reviewed development scope; no winner or K is selected. Later privacy, filters, configuration freeze and broad extraction remain open. Latest targeted tests: 73 passed, zero skips; protected inputs: 72/72 unchanged. Project ledger accounting: US$0.6114589178 including US$0.0210861 historical uncertain cost.

## Historical continuation outcome: 3 October 2026, before the repair replay

CP2.2 is **DONE under D-050**. CP2.3 is **IN PROGRESS**: Stage 1 has five ready gates; current immutable development gold is `development_v13_reviewed_20261003_stage1_r3` (1,058 A / 1,364 B / 78 C; A/B/C holds 45/39/2). Stage 2 has a D-066/D-067 model proposal, not an approved model or configuration freeze. Earlier extraction collection used the approved v6 GPT request adaptation and D-059 v7 failure disposition. V5/v6/v7 share US$3.16 cumulatively; the project hard stop remains US$8.50.

Stage 3 retrieval quality is **measured for automatic/no-optional-filter scope**: six methods, two CV queries, 214 frozen development jobs, complete original top 10 labels. The [English Stage 3 report](checkpoint_2/supporting/CP23_Stage3_Retrieval_Comparison_20261003.md) records metrics, coverage and limitations. No new embedding or inference was needed. Optional filters, final evidence ranking, D-051 synthetic privacy and D-050 broad extraction are not complete. Test evaluation remains after configuration/protocol freeze.

The [CP2.3 report](checkpoint_2/CP2_03_System_Tuning.md) is the current stage summary. Older dated evidence below remains historical. No reviewed workbook, gold, JD/CV source, split, pool, active prompt or active configuration was changed during this continuation.

Created: 29 September 2026 · Based on System Design v1.3 (`02_System_Design/`, outside this repository) and the [decision log](decisions.md) · Maps to the Execution Playbook: CP2 = checkpoints 8 to 14, CP3 = checkpoints 15 to 21.

This is the single work plan for CP2 and CP3. Each checkpoint also has its own report file ([checkpoint_2/](checkpoint_2/README.md), [checkpoint_3/](checkpoint_3/README.md)). The reports and this plan come from the same stage list, so they say the same thing.

**Status values:** PLANNED / NOT RUN · IN PROGRESS · DONE · BLOCKED. A stage is DONE only when its acceptance criteria are met and its evidence is saved.

**Three kinds of dates (D-027):**

- **Official:** from the bootcamp Timeline file. It never changes.
- **Planned work:** the revised schedule after System Design v1.3.
- **Actual:** filled in when the stage is really done.

---

## Approved privacy implementation plan: D-051, 3 October 2026

Detailed source: [privacy-threat-model.md](privacy-threat-model.md). Design approved; runtime/public security not implemented or verified. Server-temporary upload → local full-text masking → editable outgoing preview/consent → session-scoped model processing. No private CV/profile/vector/results in permanent database, public corpus, global cache or logs. Explicit stop/delete plus best-effort exit signal and server liveness/TTL expiry; no guaranteed instant deletion on browser close. The two-minute disconnect lease and fallback/cleanup timings are targets pending measured validation. Company/institution/city handling remains open.

| Stage | Newly explicit privacy work | Completion evidence |
| --- | --- | --- |
| CP2.3 | Local masking/consent boundary, session primitives, synthetic CV1/CV2 masking impact and policy feasibility | Versioned tests/paired results; no real CV, source-gold overwrite or test use |
| CP3.1 | Session authorization, TTL/lease/delete, task revocation, provider gates and upload cleanup. CP3 additions (planned): name and address hints, consent lease stored server-side, consent compatibility parse adapter entered only through `SessionStore.dispatch`, `cv_source` contract, upload hardening with the DOCX decompression gate, IP pseudonymisation | API isolation/failure tests; the 7 adapter tests; upload failure-path canaries |
| CP3.2 | Volatile private state, no database/backup persistence, safe hosting/logs/secrets/TLS; FastAPI private behind Caddy; quota table stores only HMACs | Storage and deployment inspection |
| CP3.3 | Notices, masked preview, consent naming the recorded providers, correct masking text, safe upload errors, stop/delete, browser liveness and honest reload/expiry UX | Browser checks |
| CP3.4 | PR-01-PR-10 deployed privacy acceptance (the release gate for public real-CV live, D-095); OpenRouter per-route privacy record | Two-user isolation, payload/log/metrics/Langfuse/database checks with canaries, upload failure paths, measured deletion timing |

**CP2.3 outcome (7 Oct, D-092):** masking, consent and session controls are implemented and covered by component/unit tests (the API tests use a fake run, not a deployed host). I have not validated privacy end to end, and the original-vs-masked quality comparison has not run. Both are CP3 work: CP3.4 runs them and CP3.5 reports the results.

Keep real-CV processing disabled until release gates and separate consent. In CP3 the release gate is the CP3.4 privacy gate (D-095): `JOBFIT_PUBLIC_LIVE=1` only after it passes. This adds a defined implementation workstream to CP2.3; it does not reopen CP2.2, change metrics/model-selection rules or authorize new inference. Report schedule impact rather than silently dropping core evaluation or security.


## 1. Where the project stands (historical snapshot, 2 October 2026)

This section is kept as it was on 2 October. For the current state, see [Current outcome, 7 October 2026](#current-outcome-7-october-2026) and section 2.

**Done in CP1, reused in CP2:**

- Snapshot `CP1_20260926`: 910 estimated unique jobs, 632 EDA candidates, 428 in the target role families.
- Cleaning and features: `role_family`, `experience_bucket`, location, `work_mode`, `posted_at`, v0 skills, `content_hash`. These are the filters, the stage-1 keyword baseline, and the cache keys.
- Research notebook, CP1 reports, CP1 presentation, design package (System Design v1.3, Canonical and Playbook v2.1).

**Done in CP2.1 (29 Sep to 1 Oct), details in the [CP2.1 report](checkpoint_2/CP2_01_Model_and_System_Selection.md):**

- Annotation guideline v1.2, labeling workflow, and decisions D-032 to D-042 from the pilot.
- Schemas, scoring rules (score v1), constraint rules, ordering, and the 8 development fixtures; 79 tests pass (1 database test runs on demand).
- Pilot labels approved by Dion and exported as the development split: 71 extraction units, 34 evidence rows, 10 relevance labels.
- OpenRouter client, usage ledger, and budget guard (zero usage at CP2.1 closure; subsequent embedding costs are in EXP-20261001-05).
- PostgreSQL 17 with pgvector in Docker; 632 jobs loaded; baselines B0 and B1 run (EXP-20261001-01).

**Open:**

| Area | Status |
| --- | --- |
| Gold-set sizes v2 and phased labeling (D-045) | Approved on 1 Oct 2026; 2 to 3 hours daily and fallback confirmed |
| Benchmark protocol (D-044) and split rules (D-046) | Approved on 1 Oct (option A; blind-first test) |
| Privacy design and implementation (D-051) | Architecture approved: local masking, preview/consent, isolated volatile sessions, stop/delete and automatic expiry. CP2.3 synthetic implementation/testing; CP3 integration. City/company/institution and final timing details remain open; see privacy contract |
| CV parser, JD extraction, evidence matching, paste JD path | CP2.2 implemented with source validation, configured dates, PDF/DOCX input and session-only paste flow. Offline and database checks pass; live development verification and batch extraction status are tracked in the stage report. CP2.2 implementation acceptance DONE under D-050; model quality is not yet measured |
| Dense and hybrid search | Implemented and live build verified: 632 job + 2 development query vectors per model; 123 database-enabled tests passed (EXP-20261001-05) |
| CV4/CV5 | Content version 0.1 approved by Dion; test only (T07 DONE) |
| Development/test labels, tuning, evaluation | T03 pools frozen. Current reviewed bundle: 1,058 A / 1,364 B / 78 C, holds45/39/2. Development extraction experiments and Stage 3 retrieval comparison are running/measured; final configuration and held-out evaluation remain pending. |
| FastAPI, migrations, Streamlit, CI, Docker images, deployment | CP3, not started |

**Out of scope for v1 (D-025):** import link, auto-apply, cover letter, Strong/Realistic/Stretch labels.
**Deferred:** second job-data provider, reranker, automatic refresh, official support for adjacent roles.
**Minimal version:** market insight, evidence-based CV suggestions.

---

## 2. Dates

| # | Stage | Template name | JobFit report | Official | Planned work | Actual | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | CP2.1 | Model Selection (CNN/LSTM/DNN sesuai use case) | [Model and System Selection](checkpoint_2/CP2_01_Model_and_System_Selection.md) | 28 Sep 2026 | 29-30 Sep 2026 (labeling pilot on the evening of 29 Sep) | 29 Sep to 1 Oct 2026 | DONE |
| 9 | CP2.2 | Modeling Deep Learning | [Modeling the Extraction, Search, and Evidence Pipeline](checkpoint_2/CP2_02_Modeling_Pipeline.md) | 29 Sep 2026 | 1-2 Oct 2026 (moved: CP2.1 ended on 1 Oct) | 1 to 3 Oct 2026; closed under D-050 | DONE |
| 10 | CP2.3 | Hyperparameter Tuning | [System Tuning](checkpoint_2/CP2_03_System_Tuning.md) | 30 Sep 2026 | 2 Oct 2026 | 3 to 6 Oct: gold r4, D-078/D-084 applied, freeze candidate v4 (D-086); freeze approved 6 Oct (D-087); carry-overs resolved 7 Oct (D-091, D-092) | DONE |
| 11 | CP2.4 | Modeling + Evaluation Metrics | [Evaluation Metrics](checkpoint_2/CP2_04_Evaluation_Metrics.md) | 1 Oct 2026 | 3 Oct 2026 | 6-7 Oct: test run after the D-087 freeze, labels D-088, report `heldout_report_v1.json` on 7 Oct | DONE |
| 12 | CP2.5 | Visualisasi Evaluation Result | [Evaluation Result Visualization](checkpoint_2/CP2_05_Evaluation_Visualization.md) | 2 Oct 2026 | 3 Oct 2026 | 4 Oct: development figures 1-8; 7 Oct: held-out figures 9-11 (notebook 02) | DONE |
| 13 | CP2.6 | Recommendation & Summary | [Recommendation and Summary](checkpoint_2/CP2_06_Recommendation_and_Summary.md) | 3 Oct 2026 | 3 Oct 2026 | 4 Oct: provisional development summary; 7 Oct: final summary after the held-out test | DONE |
| 14 | CP2.7 | PPT Check Point 2 + Mentoring | [CP2 Presentation and Mentoring](checkpoint_2/CP2_07_Presentation_and_Mentoring.md) | 4 Oct 2026 | 3-4 Oct 2026 (deck draft on 3 Oct) | Deck v3 on 4 Oct; presented and mentored 4 Oct; feedback written up 7 Oct (D-093) | DONE |
| 15 | CP3.1 | Deployment API menggunakan Flask/FastAPI | [API Deployment with FastAPI](checkpoint_3/CP3_01_FastAPI_Service.md) | 5 Oct 2026 | 5 Oct 2026 | 6 Oct: all endpoints, privacy controls and tests (local); 7 Oct: public live scope planned (D-095 to D-097) | PARTIAL (demo flow done locally; public path PLANNED) |
| 16 | CP3.2 | Integrasi Database & GitHub Actions CI/CD | [Database Integration and CI/CD](checkpoint_3/CP3_02_Database_and_CICD.md) | 6 Oct 2026 | 6 Oct 2026 (hosting smoke deploy earlier, on 1-2 Oct) | 6 Oct: Docker and compose work locally; 7 Oct: SumoPod VPS, Alembic and job sync planned (D-095, D-098); 7 Oct Phase 1: FAIL-35 resolved, CI green (run [37641393567](https://github.com/Gidion123/Job-Fit/actions/runs/37641393567)) | PARTIAL |
| 17 | CP3.3 | Build Streamlit UI | [Streamlit UI](checkpoint_3/CP3_03_Streamlit_UI.md) | 7 Oct 2026 | 7 Oct 2026 | 6 Oct: full UI with privacy UX (local); public upload flow and mentor refinements planned | PARTIAL (demo flow done locally) |
| 18 | CP3.4 | Testing End-to-End Application | [End-to-End Testing](checkpoint_3/CP3_04_End_to_End_Testing.md) | 8 Oct 2026 | 9 Oct 2026 (formal feature freeze at the end of 9 Oct, D-100) | 6 Oct: local end-to-end 27/27; deployed and live checks planned | PARTIAL |
| 19 | CP3.5 | PPT Final Project / Portfolio | [Final Presentation and Portfolio](checkpoint_3/CP3_05_Final_Presentation_and_Portfolio.md) | 9 Oct 2026 | 10 Oct 2026 | 7 Oct: D-045 blind candidates selected (IDs only) | PLANNED / NOT RUN |
| 20 | CP3.6 | Finalisasi Portfolio & Rehearsal Presentation | [Finalization and Rehearsal](checkpoint_3/CP3_06_Finalization_and_Rehearsal.md) | 10 Oct 2026 | 10 Oct 2026 | not run yet | PLANNED / NOT RUN |
| 21 | CP3.7 | Final Project Presentation + Pemberian Tugas Portofolio | [Final Presentation and Submission](checkpoint_3/CP3_07_Final_Presentation_and_Submission.md) | 11 Oct 2026 | 11 Oct 2026 | not run yet | PLANNED / NOT RUN |

**CP2.8 (not a bootcamp checkpoint):** Phase A post-test quality optimization on development data, 7 Oct 2026, CLOSED with KEEP BASELINE (D-089, D-090); [report](checkpoint_2/CP2_08_Post_Test_Quality_Optimization.md). It never changes the CP2.4 result.

**CP2 closure (7 Oct 2026):** CLOSED (D-094); see the [closeout audit](checkpoint_2/CP2_Closeout_Audit_20261007.md).

**Tightest day: 3 October** (checkpoints 11, 12, 13, and the deck draft). If it slips, the checks of the minimal features move to checkpoint 18. Core evaluation is not cut.

**Feature freeze:** planned for 8 October 2026 (D-026); moved to the **end of 9 October 2026** by D-100 because the public live scope grew. The 11 October presentation does not move.

---

## 3. Dependencies and approvals

| What | Owner | Needed by | Blocks | Status |
| --- | --- | --- | --- | --- |
| OpenRouter account, credit, privacy settings, and `OPENROUTER_API_KEY` in `.env` (D-028, D-030) | Dion | 30 Sep | Every LLM and embedding step | Done:regular inference key verified after Dion replaced the management key; both embedding candidates ran. Local hard stop now US$18.5 (D-070); ledger US$3.09 on 4 October, US$10.53 on 7 October after CP2.4 and Phase A |
| Docker Engine starts and runs a container | Dion | 30 Sep | Local PostgreSQL, FTS baseline | Done: `hello-world` ran on 29 Sep |
| Review of the synthetic CVs | Dion | Evening of 29 Sep, before the pilot | Pilot, gold labels | Done |
| Labeling pilot (timed) | Dion | Evening of 29 Sep | Gold sizes, guideline v1 | Done on 1 Oct (guideline v1.2) |
| Gold sizes (D-045) | Dion | 1 Oct evening | Labeling batches | Approved on 1 Oct 2026; D-044 and D-046 approved |
| Development gold, phase 1 (D-045) | Dion + QA | 2 Oct evening | CP2.3 tuning | Reviewed-record export `development_v13_reviewed_20261002_r2` exists; source/version/whole-JD holds and model alignment still gate quality metrics |
| Railway account on the Trial credit (D-023) | Dion | 1 Oct | Smoke deploy, checkpoint 16 | Superseded by D-095 (SumoPod VPS); no Railway account was created |
| SumoPod VPS (Singapore, Ubuntu 24.04, 2 vCPU / 8 GB / 80 GB), SSH keys, ufw, Docker, domain (`JOBFIT_PUBLIC_HOST`) | Dion + Codex | 8 Oct | First deploy (CP3.2) | Open |
| Production OpenRouter key with a credit limit; recorded per-route privacy settings | Dion + Codex | 9 Oct | Public live (CP3.4 gate) | Open |
| SMTP sender and receiver for alerts (`GRAFANA_SMTP_*`, `GRAFANA_ALERT_*`) | Dion + Codex | 9 Oct | Email alerts (CP3.2) | Open; optional since 8 Oct (email alerts are P2 (post-beta)) |
| Langfuse Cloud project in the Japan region (Hobby) | Dion + Codex | 9 Oct | Tracing (CP3.1) | Open; optional since 8 Oct (Langfuse is P2 (post-beta)) |
| Development labels reviewed (gold) | Dion | 2 Oct morning | Checkpoint 10 | Reviewed-record bundle exported and validated; only compatible complete references may be used for each metric; held/unjudged records remain explicit |
| Test relevance labels, blind (D-045 phase 2) | Dion | 3 Oct | Checkpoint 11 | Done 7 Oct: D-053 top-10 union, 68 pairs over CV1-CV5, 67 judged + 1 held (F00070); AI-assisted, human-reviewed, blind to ranking (D-088, `test_v13_cp24_r1`) |
| Test extraction and evidence (D-045 phase 3) | Dion | 10 Oct | Final report (CP3.5) | Open, method final (D-100, option B): blind candidates F00398, F00237 and CV3 × F00398 selected by ID on 7 Oct; Dion labels them blind first, then the frozen pipeline runs (about US$0.10); the CP2.4 workbook stays MODEL-ASSISTED, HUMAN-REVIEWED and is reported separately. PLANNED / NOT YET COMPLETED |
| Mentor feedback at CP2 | Mentor | 4 Oct | CP3 scope confirmation; CP2 closure | Done: session 4 Oct; feedback recorded 7 Oct as D-093 (CP3 input: waiting-state UX; vacancy-specific CV guidance) |

---

## 4. Critical path

```text
guideline v0.1 → pilot (timed) → guideline v1.3 → split frozen → reviewed development records
                                                              → compatible references + metric conventions → CP2.3 comparison
                                                              → configuration choice → quality-gated development extraction (D-050)
                                                              → freeze → held-out test evaluation (CP2.4) → charts → CP2 deck
in parallel: schemas + scoring + fixtures → CP2.2 parser/extraction/matcher + stage-1 search → CP2.3 recommendation list
in parallel: hosting smoke deploy (1-2 Oct) → API (5 Oct) → database + CI (6 Oct) → Streamlit (7 Oct) → E2E + freeze (8 Oct)   [original plan]
CP3 (D-095 to D-100): docs freeze + CI green (7 Oct) → P0 hardening + public path + packaging + dark deploy (8 Oct)
                      → sync + monitoring + privacy gate + public live + PR-10 + freeze (9 Oct) → reports/deck/rehearsal (10 Oct) → present (11 Oct)
CP3 order after D-102 (8 Oct, with the anti-overengineering correction): foundation closeout → public-live cost/profile decision
                      → real-user AI path (both flows) → product UX → lean packaging → lean monitoring → dark VPS deploy
                      → privacy, quality and cost validation → controlled public beta → final portfolio and reporting; the D-100 dates are unchanged
```

Labeling is the longest chain and depends on one person. It starts on day one and runs next to the implementation (D-015).

---

## 5. Priorities and cut order (D-026)

1. **Protected, never cut:** core evaluation, tests, privacy, deployment, the explanation of limitations.
2. **Cut first:** UI polish.
3. **Then:** extra experiments (fewer configurations, fewer model comparisons).
4. **Only with a new docs/decisions.md entry:** the minimal market insight or CV suggestions.

**CP3 clarification (D-102, 8 Oct 2026):** the list above is kept as the original rule. For CP3, decorative polish is still cut first, but product clarity (the two primary flows, honest progress, result presentation, failure and unavailable states) is part of the product goal, and job-specific CV improvement is a first-class requirement (recorded in D-093 and D-102). Core evaluation, tests, privacy, deployment and the explanation of limitations are still never cut.

---

## 6. Budget

- **API cap:** D-070 replaced the US$15 ceiling with the credit actually bought (about US$19.22). The app guard is US$19 with a hard stop at US$18.5. Ledger after pipeline v1.1: US$3.09; on 7 October, after the CP2.4 test run (US$1.44) and Phase A (US$2.38): US$10.53 including US$0.25 uncertain reservations. Hosting is counted separately.
- **Estimates before any run:** System Design v1.3 section 11. Expected LLM use is well under the cap.
- **Guard:**
  - Every call goes to `reports/usage/usage_ledger.jsonl`.
  - Each batch is estimated before it starts.
  - Calls stop when the estimated total would pass the hard stop in `.env` (now US$18.5, D-070).
  - The OpenRouter API key has its own credit limit as a second stop.
- **Estimate for all CP2 and CP3 LLM work** (29 Sep 2026, before any real call; token counts are assumptions and are checked against the ledger after the first calls in CP2.2):

  | Work | Estimate |
  | --- | --- |
  | CP2.2 prompt v1 on development cases, about 3 rounds of fixes | about US$0.25 |
  | Batch extraction of 428 target JDs, twice (baseline, then the chosen model) | about US$0.50 to 1.00 |
  | Embeddings for all 632 jobs and the CVs (about 0.5M tokens) | under US$0.02 |
  | Second embedding model for the comparison, if D-044 option A is approved | under US$0.01 |
  | CP2.3 model comparison round 1, run twice (4 models x 30 cases, GPT-6 Sol on 10) | about US$1.60 |
  | CP2.3 round 2 (`deepseek-v4-pro`, only if needed) | about US$0.25 |
  | CP2.3 K/prompt experiments and CP2.4 frozen confirmation | about US$0.50 |
  | CP3 demo, end-to-end tests, precomputed demo results (about 60 runs with K = 20) | about US$0.80 (GPT-6 Luna) to US$7.80 (Claude Haiku 4.5) |
  | **Total** | **about US$4 to 6 if a low-cost model wins, about US$15 if Claude Haiku 4.5 wins** (before a 1.5x safety buffer) |

  The model choice matters more than anything else. If Claude Haiku 4.5 wins by the D-029 rule, CP3 uses cached results for the demo so that a top-up stays small.
- **Hosting:** originally Railway (D-023); now a SumoPod VPS (D-095), paid by Dion outside the LLM budget.
- **CP3 budgets (D-096):**
  - **CP3 validation:** US$5 in total, counted on the development ledger. I report before anything would cross it.
  - **Production:** a US$2/day hard cap on a dedicated OpenRouter key with its own credit limit. It is enforced by deterministic phase bounds and persisted reservations, and the production ledger is authoritative.
  - **JSearch:** sync requests use the free tier (≤ 80 requests per sync); the pay-as-you-go fallback is about US$0.40 per sync.

---

## 7. Labeling plan (D-015, D-016, D-045, D-046)

1. **Pilot (done 29 Sep to 1 Oct):** 4 JDs (71 units), 34 evidence rows, 10 relevance labels; guideline v1.2; exported as development gold.
2. **Split (D-046):** the 428 target jobs are split by job cluster into a development half and a test half before any tuning. Pilot jobs stay in development, CV3 is test only, duplicates stay on one side.
3. **Phase 1, development (2 Oct, about 3.5 h of Dion's time):** 3 new extraction JDs, 2 new evidence pairs, 40 new relevance labels for CV1 and CV2 from the development pools. The drafting model writes drafts and silver labels; Dion reviews. Tasks: [`evals/annotation_tasks/`](../evals/annotation_tasks/README.md).
4. **Phase 2, test relevance (3 Oct, about 2 h):** 36 labels (CV1 to CV3 x 12 jobs of the frozen configuration), labeled blind by Dion, then a QA check.
5. **Phase 3, test expansion (5 to 7 Oct, about 6 h):** two new synthetic test CVs (CV4, CV5) with 24 blind relevance labels, 4 test JDs for extraction (2 blind), and 3 CV-JD evidence pairs (1 blind). Reported in the final evaluation, with the configuration unchanged.
   **Actual outcome (7 Oct):** phase 2 followed D-053 instead of the fixed 36/24 targets: one blind top-10-union pool over CV1-CV5 (68 pairs) labeled after the D-087 freeze, with ChatGPT assistance and Dion's review (D-088). The phase 3 test extraction and evidence labels were not made; D-045 assigns those results to the final report (CP3.5).
6. **Rules:**
   - A language model may draft labels (`label_source = model_draft`), following [annotation-workflow.md](annotation-workflow.md).
   - Only labels Dion reviewed and approved are gold. Unreviewed drafts are silver: used only to explore, never as ground truth.
   - Test labels and results never choose a model, prompt, weight, or K.
   - No inter-annotator agreement is reported; the single-annotator limitation is written in the evaluation report.

---

## 8. Stage plans

### CP2.1: Model and System Selection (checkpoint 8)

Template name: Model Selection (CNN/LSTM/DNN sesuai use case) · Official: 28 Sep 2026 · Planned work: 29-30 Sep 2026 (labeling pilot on the evening of 29 Sep) · Report: [CP2_01_Model_and_System_Selection.md](checkpoint_2/CP2_01_Model_and_System_Selection.md)

JobFit version: For an LLM and retrieval system, model selection means comparing search methods, LLM candidates, and prompt versions, not training a CNN/LSTM/DNN (D-001). This stage also sets the annotation guideline, the scoring rules, and the experiment matrix.

1. **Goal.** Set the rules, the baselines, and the experiment matrix before the full system is built, so every later choice is measured against something.
2. **Inputs and prerequisites.**
   - System Design v1.3 and docs/decisions.md (D-001 to D-037)
   - CP1 processed data: 632 EDA candidates, 428 in the target role families
   - `OPENROUTER_API_KEY` in the git-ignored local `.env` that Dion fills himself (D-028, D-030, D-031); never in chat or commits
   - Docker Engine running on the Mac (CLI 29.4.3, Compose v5.1.3; `docker run --rm hello-world` succeeded on 29 Sep 2026)
3. **Steps.**
   1. Write the annotation guideline v0.1: requirement units, evidence labels, constraint states (compatible / unknown / explicit conflict), relevance 0-3, and label record fields (`label_source`, `review_status`, `review_action`, `guideline_version`).
   2. Define the Pydantic schemas for JD requirement units and CV evidence units, with example outputs.
   3. Implement the deterministic scoring rules: match %, score status (final / provisional / on hold / no score), constraint states, ordering, and stable tie-break.
   4. Write the 8 development fixtures from System Design v1.3 section 15 and run them as tests.
   5. Draft 2-3 synthetic CVs (at least one in Indonesian); Dion checks that they are realistic.
   6. Labeling pilot: a small development sample (for example 5 JDs, about 20 requirement-evidence pairs, 2 CVs x 5 jobs). A language model may draft labels; Dion decides and records the time per item. Then revise the guideline to v1.
   7. Start local PostgreSQL with pgvector (Docker Compose) and load the 632 EDA candidates.
   8. Run Baseline 0 (keyword/skill overlap with the CP1 v0 skill list) and Baseline 1 (PostgreSQL FTS) on the pilot pool.
   9. Write the experiment matrix in docs/experiments.md (stage-1 methods, K, LLM candidates, prompt versions), each with a hypothesis and a metric.
   10. Build the usage ledger and budget guard before the first LLM call.
4. **Files and outputs.** `evals/annotation_guideline_v1.md`; `evals/fixtures/` (8 development cases); `evals/pilot/` (pilot labels and timing); `data/synthetic_cvs/`; schema and scoring modules in `src/` with tests in `tests/`; `docker-compose.yml`; `docs/experiments.md` (matrix); `reports/usage/usage_ledger.jsonl`; this stage report.
5. **Tests and acceptance criteria.**
   - The guideline v1 exists and has a version number.
   - The scoring rules pass the 8 development fixtures (pytest).
   - The pilot time per item is recorded and used to propose gold sizes (a new docs/decisions.md entry).
   - B0 and B1 run on the pilot pool and their outputs are saved.
   - Every experiment candidate has a hypothesis and a metric.
   - Every LLM call is written to the usage ledger.
6. **Evidence to keep.** pytest output; pilot timing table; docs/experiments.md matrix; ledger total for the stage; commit links (Dion pushes).
7. **Estimate and dependencies.** About 1.5 working days. Dion: about 30 minutes to review the synthetic CVs and about 1.5-2 hours for the pilot. LLM cost: under US$0.50. Depends on: Docker Engine (checked: `hello-world` ran on 29 Sep); OpenRouter key in `.env`; Dion's review of the synthetic CVs before the pilot.
8. **Fallback.** If Docker does not start, use Postgres.app on the Mac and note it. If the pilot takes too long, cut it to 3 JDs and 1 CV, but still time it. Guideline v1 is finished by the end of 30 Sep in any case.
9. **Status and next step.** DONE (29 Sep to 1 Oct 2026). Every acceptance criterion is met except that no LLM call has been made yet, so the ledger is still empty (the guard is tested with mocked calls). Two changes from the plan: the pilot took until 1 Oct because the review raised 21 rule questions (D-032 to D-042), and Recall@K for B0 and B1 could not be computed because the pilot has only one job labeled 3 (EXP-20261001-01). Carried over: D-043 and D-044 approval, test labels (about 2 hours of Dion's time). Next: CP2.2 (checkpoint 9): CV parser, extraction prompt v1, evidence matcher, and the 1 CV + 1 JD report.

### CP2.2: Modeling the Extraction, Search, and Evidence Pipeline (checkpoint 9)

Template name: Modeling Deep Learning · Official: 29 Sep 2026 · Planned work: 30 Sep-1 Oct 2026 · Report: [CP2_02_Modeling_Pipeline.md](checkpoint_2/CP2_02_Modeling_Pipeline.md)

JobFit version: The "deep learning modeling" of JobFit is the pipeline of pretrained models: LLM extraction, embeddings, search, and evidence matching (D-001). No neural network is trained.

1. **Goal.** Build the vertical slice: one CV and one JD produce a structured, checkable evidence report. Then prepare the pieces for the recommendation list: cached extraction for the target jobs and the dense and hybrid search.
2. **Inputs and prerequisites.**
   - Checkpoint 8 outputs (guideline v1, schemas, scoring rules, fixtures, local database, ledger)
   - OpenRouter credit available (D-030)
   - Synthetic CVs reviewed by Dion (done)
   - D-045 approved; split written by D-046 rules before any tuning
3. **Steps.**
   1. CV text extraction (PyMuPDF, python-docx) and LLM parsing into evidence units with a parsing summary.
   2. Default JD extraction prompt v1.2 under guideline v1.3, plus explicitly versioned experimental v1.3 with source inventory. Pydantic validation and at most one repair per stage; no automatic default promotion.
   3. Evidence-matching prompt v1.1: MATCH / PARTIAL / NO_MATCH per requirement unit, with CV quotes checked to exist word for word in the CV.
   4. Constraint check: experience duration (v1.2 counting rules), location against a confirmed location, work-authorization statements.
   5. Paste JD path end to end: clean, quality signals, extract, preview, match report.
   6. Run the 8 development cases and check them by hand.
   7. Prepare a feasible versioned development extraction plan on the214frozen IDs; broad execution remains subject to budget/quality gates. The214held-out JDs stay deferred until configuration freeze. Preserve compatible successes; do not automatically re-infer after configuration changes.
   8. Embeddings (model per D-020, plus the second candidate if D-044 option A is approved), Baseline 2 dense, and the hybrid FTS + dense search with RRF.
   9. Write the job-level split (D-046) and the development pools for CV1 and CV2; the drafting model writes silver relevance labels and Dion reviews the gold subset (D-045 phase 1). The test pool is picked only after CP2.3 freezes the configuration.
4. **Files and outputs.** prompt files v1 in `prompts/`; CV parser, extractor, matcher modules and tests; extraction cache; an example report for a synthetic CV; `evals/splits/`; this stage report.
5. **Tests and acceptance criteria.**
   - One CV and one pasted JD produce a structured report whose quotes exist in the CV.
   - The 8 development cases pass the manual check.
   - Cache keys include schema, prompt, model, preprocessing, and guideline versions.
   - D-050: provide a feasible, versioned extraction plan and preserve per-job execution status; broad development materialization follows CP2.3 configuration evaluation. The original all-target/per-job execution criterion is carried forward explicitly, not marked executed. Held-out processing still waits for freeze.
   - The test split is locked before checkpoint 10 starts.
6. **Evidence to keep.** example report; manual check sheet for the 8 cases; extraction success count; ledger totals; commit links.
7. **Estimate and dependencies.** About 1.5 working days. LLM cost: about US$0.25-0.50 for the batch extraction plus small test runs. Depends on: OpenRouter key in `.env` by the evening of 30 Sep (for extraction and the dense baseline).
8. **Fallback.** If the OpenAI embedding fails on the Indonesian-CV cases, use the local `multilingual-e5-small`. If extraction fails for some jobs, mark them "could not be analyzed" and continue. If extraction quality is poor, keep it for prompt v2 in checkpoint 10 instead of blocking.
9. **Status and next step.** DONE on 3 October under D-050. Backend, embeddings, twelve comparable top 30 retrievals, eight delegated fixtures, reviewed-record export and the experimental source-checked live chain are evidenced. The user explicitly moved broad extraction after CP2.3 configuration evaluation. Its unexecuted status and budget conflict remain visible; no scope, label or quality claim is hidden. Next: CP2.3 reference/alignment and metric gates, then authorized comparisons.

### CP2.3: System Tuning (checkpoint 10)

**Current status:** see item 9 below. The dated notes that follow are from 3-4 October and describe the state on those days, so their "current", "next" and "NOT RUN" statements are out of date.

**Historical D-054 update, 3 October 2026:** Stage 1 prerequisites are **READY**; see the [closure section](checkpoint_2/supporting/CP23_Stage1_Evaluation_Preparation_20261003.md#6-d-054-closure-and-current-stage-1-status-3-october) and [five-gate receipt](../evals/results/cp23_stage1_readiness_20261003_v4.json). The immutable r3 reviewed bundle contains 1,058 A / 1,364 B / 78 C and covers all 70 distinct original-top-ten development CV/JD pairs. Case-scoped B/C changes and split/merge policy are approved under D-054; A/B source holds remain where stated. Earlier Stage-1 blocked snapshots below are historical. Stage 2 candidate quality comparison, winner and freeze are **NOT RUN**. Every new model output still needs source QA and semantic alignment before a metric claim. CP2.2 remains DONE; D-050 broad extraction and D-051 privacy work remain later CP2.3 tasks.

**Stage-2 preflight:** [Four-model/seven-JD extraction plan](checkpoint_2/supporting/CP23_Stage2_Comparison_Preflight_20261003.md) has a US$3.191929 conservative upper bound including one repair per case; the proposed US$3.20 aggregate cap requires explicit batch approval under the standing US$1 rule. Offline safeguards passed 41 targeted tests; paid comparison, four fixed-input matching pairs and GPT-6 Sol reference remain unrun. This is a preflight, not a tuning result.

**Stage-2 execution update:** Dion approved the exact US$3.20 cap. The first DeepSeek/F00332 extraction ran once (US$0.00478664,394.786s), but delegated semantic review found merged AND requirements and an unrepresented OR; the durable batch stopped after 1/28cases. No four-model comparison or winner exists. The four-pair fixed-input OR adapter was prepared/tested offline (73logical units,13groups), but no matching call ran. Current ledger US$0.295557024 including the old uncertain reservation. See the linked Stage-2 report and FAIL-15; the prior paragraph is the historical pre-dispatch snapshot. A revised prompt/protocol needs a new plan and applicable budget approval before paid rerun.

**Stage-2 v1.4 offline continuation:** A versioned prompt candidate clarifying approved AND/OR rules and a new same-case v4 preflight are ready; bound US$3.2232974, proposed cap US$3.23. The active runtime prompt remains v1.2. Forty-four selected offline tests pass; no v1.4 inference or winner at this snapshot. The v3 failed output remains preserved. See section 6 of the Stage-2 supporting report.

**Historical documentation boundary (3 October):** The [CP2.3 report](checkpoint_2/supporting/CP23_Progress_Log.md) now tracks all eight stages and gives the Stage-3 retrieval protocol explicitly. The 44-pass count above is an earlier v1.4 snapshot; a later offline matcher-payload preflight passed **45 selected tests** and is documented in [Stage-2 report section 6](checkpoint_2/supporting/CP23_Stage2_Comparison_Preflight_20261003.md#6-new-offline-v14-protocol-pending-its-own-batch-approval). Twelve existing top 30 rankings are input artifacts, not a completed Stage-3 quality comparison. No model, embedding, prompt or K is selected.

**Latest Stage-2 execution (D-056):** Dion approved the exact v1.4 US$3.23 extraction plan. DeepSeek/F00332 used two paid attempts (US$0.022156197), but source-semantic QA found an incomplete education alternative and a strict split/merge alignment issue. The v4 batch stopped after 1/28cases, as its quality gate requires. The total ledger is US$0.317713221 including US$0.0210861 historic uncertain reservation. Other models, evidence matching and Stage-3 quality comparison remain unrun. See [Stage-2 report section 7](checkpoint_2/supporting/CP23_Stage2_Comparison_Preflight_20261003.md#7-actual-v14-first-stage-and-source-semantic-stop); earlier preflight/approval language above is historical.

**Next Stage-2 gate:** A [versioned same-protocol continuation proposal](checkpoint_2/supporting/CP23_Stage2_Comparison_Preflight_20261003.md#8-proposed-same-protocol-continuation-no-paid-dispatch) retains that failed case and covers the 27 unrun cases. It records semantic failures instead of abandoning all candidate measurements, with one source review between stages; process/transport and budget stops remain. The additional conservative bound is US$3.1559888, proposed cap US$3.16. Its offline executor tests passed16/16, but no v5 inference can run without Dion's distinct protocol/budget approval. This is not a Stage-2 completion or model selection.

**Stage-1 update (D-052, 3 October):** conventions and scope now follow [evaluation.md](evaluation.md). Prepare seven compatible JD references/four CV1/CV2 pairs and all eligible relevance records; report top 10 union gaps before requesting extra review. Fix original-rank precision/coverage and failure/class accounting in the evaluator with synthetic tests. Dataset/alignment readiness remains separate from approved metric conventions. Formal tuning and paid inference are not part of this preparation. D-050 broad extraction and D-051 privacy work remain in the subsequent plan.

**Stage-1 execution receipt (3 October):** the [offline preparation report](checkpoint_2/supporting/CP23_Stage1_Evaluation_Preparation_20261003.md) records seven source-checked development JD candidates, four complete fixed-input evidence pairs, and original-top10 union coverage of 61 judged / 6 new unjudged / 3 held CV-JD pairs. D-052 evaluator changes passed 72 targeted offline tests; no quality metric or winner was produced. Contract, source-reference and implementation preparation are ready; semantic model alignment and complete primary judgment coverage still block formal comparison. D-050 broad extraction remains after configuration evaluation; D-051 synthetic privacy implementation is separate. D-053 affects only the later held-out protocol.

**Stage-1 review handoff (3 October):** six missing original-top10 C cases now have source-checked model-assisted drafts in `evals/labeling/drafts/cp23_stage1_relevance_review_20261003_v1.md`/`.json`, all pending Dion's review; they are neither gold nor a new workbook. The two F00332 label differences, split/merge F1 convention, and holds CV1/F00022, CV2/F00114, CV1/F00369 are itemized in the same [Stage-1 report](checkpoint_2/supporting/CP23_Stage1_Evaluation_Preparation_20261003.md#5-stage-1-closure-audit-and-review-boundary-3-october). The follow-up QA receipt verifies six source/CV excerpt sets and 24 protected input hashes. Stage 1 remains **IN PROGRESS** for semantic alignment and complete original-rank judgment coverage; Stage 2 waits for versioned human decisions, dependency checks and regenerated readiness. No paid comparison or configuration selection has run.


Template name: Hyperparameter Tuning · Official: 30 Sep 2026 · Planned work: 2 Oct 2026 · Report: [CP2_03_System_Tuning.md](checkpoint_2/CP2_03_System_Tuning.md)

JobFit version: Tuning means choosing system settings with measurements: stage-1 search method, K, prompt version, LLM model, and the PARTIAL weight.

1. **Goal.** Choose the configuration with measurements on the development set, not by changing settings without a metric.
2. **Inputs and prerequisites.**
   - Checkpoint 9 outputs
   - Reviewed-record development gold, with compatible complete references and verified model alignment for each reported metric
   - Locked test split (not used here)
3. **Steps.**
   1. Compare B0, B1, dense and hybrid with both approved embedding candidates on comparable development scope. D-044 option A is approved: silver is exploratory only; every configuration choice must be confirmed with reviewed development gold (D-045). Report labeled-pool Recall@K and judgment coverage; do not treat unjudged items as0.
   2. Choose K for stage 2 from 10, 20, 30 by recall, latency, and cost.
   3. Compare explicitly versioned prompts within a human-verified compatible guideline/gold scope; active JD prompt v1.2 follows guideline v1.3.
   4. LLM comparison round1 (D-029) on approved D-045 subsets (7extraction JDs,4evidence pairs;50relevance judgments for ranking): `deepseek-flash`, GPT-6 Luna, Gemini 3.5 Flash-Lite, Claude Haiku 4.5, all through OpenRouter, with GPT-6 Sol on at most 10 hard cases as the quality reference. Choose with the fixed selection rule. Round 2 only if the rule asks for it.
   5. Audit the PARTIAL weight (0.5) against the relevance labels.
   6. Build the recommendation list end to end: filters, filter status, UNKNOWN option, ordering rules, statuses for not analyzed and failed jobs.
   7. Keep labeling the test set (Dion).
   8. Carry D-050's broad development extraction forward **after** development configuration evaluation. Use the selected, versioned configuration; resume only compatible accepted artifacts; enforce source/spec/semantic quality receipts, per-JD status and the existing budget guard. The five remaining priority IDs are a separate unexecuted preflight, not an implicit first paid batch. The full 214-JD conservative bound exceeds the hard stop, so resolve any budget/scope gap explicitly before dispatch. Held-out extraction remains after freeze.
4. **Files and outputs.** experiment table in docs/experiments.md with config snapshots; quality vs latency vs cost table; working recommendation list (script or endpoint); this stage report.
5. **Tests and acceptance criteria.**
   - Every change has a before/after on the development set, and the keep/remove decision is written.
   - The test set is not used for tuning.
   - Spend stays within the budget guard.
   - The chosen stage-1 method, K, prompt, and model are recorded in docs/decisions.md, with the D-029 rule applied as written.
   - The D-050 carried extraction has an auditable per-JD development status and executed scope, or an explicitly approved revised scope/budget disposition; a partial probe or cost estimate is not counted as full materialization.
6. **Evidence to keep.** docs/experiments.md entries; config snapshots; ledger totals.
7. **Estimate and dependencies.** Historical estimate: about 1 working day and under US$2 for round 1 and the prompt comparison. This excludes D-050 broad development extraction; the current 214-JD conservative upper bound is US$21.0576 and cannot be dispatched under the US$8.50 guard. Re-estimate each comparison and any later batch with current prices, repair allowance, ledger headroom, compatible references and quality stop rules. Depends on reviewed development gold and the CP2.2 pipeline.
8. **Fallback.** Follow the approved D-045 fallback and report its scope; no silent change to review sizes/K. Historical proposal was15cases and K10/20 only, not current authorization. Incomplete comparisons cannot establish a winner.
9. **Status and next step.** DONE. Gold r4 was imported (D-085); the D-078 rule chose K 10, weight 0.5 and the seniority rule; Hybrid Qwen stayed under D-084; GPT-6 Sol matches with a Luna fallback (D-083); the experience block joined the freeze (D-086). Dion approved freeze receipt `evals/freeze/cp23_freeze_draft_v2/` on 6 Oct (D-087; v1 superseded). The closeout found two items without a decision, and both were settled on 7 Oct: D-091 accepts the 52 development JDs that were actually extracted (the other 162 could not affect any CP2 choice), and D-092 moves the end-to-end privacy checks and the original-vs-masked comparison to CP3.4/CP3.5 (privacy is implemented and component/unit tested only). Next: CP2.4 (done).

### CP2.4: Evaluation Metrics (checkpoint 11)

Template name: Modeling + Evaluation Metrics · Official: 1 Oct 2026 · Planned work: 3 Oct 2026 · Report: [CP2_04_Evaluation_Metrics.md](checkpoint_2/CP2_04_Evaluation_Metrics.md)

JobFit version: The chosen configuration is measured on the held-out test set with the metrics of System Design v1.3 section 14.

1. **Goal.** Measure the chosen configuration on the held-out test set and report the metrics in the priority order of System Design v1.3 section 14.
2. **Inputs and prerequisites.**
   - Configuration and test protocol approved/frozen in CP2.3 under D-053
   - Test labels reviewed by Dion (gold)
   - Evaluation scripts
3. **Steps.**
   1. Blind top 10-union judgments for the frozen stage-1 and final application orders; original-position NDCG@10/P@5 with common judged pool and paired eligible CV scope.
   2. Evidence Macro-F1, precision and recall per class, confusion matrix, share of assessed units.
   3. Extraction precision, recall, F1, and schema validity.
   4. Labeled-pool Recall@K with coverage limitations; filter recall only with pre-filter relevant judgments, otherwise not measured.
   5. Safety: hard-negative false positives in the top 10, quote validity, unsupported claims.
   6. Latency p50/p95 and cost per run, live and cached separately.
   7. Save failure examples in docs/failures.md.
4. **Files and outputs.** evaluation scripts; evaluation report draft; gold labels with the guideline version; docs/failures.md entries; this stage report.
5. **Tests and acceptance criteria.**
   - No "good" claim without a metric.
   - Each result records the git SHA, prompt and model versions, cost, and latency.
   - Only gold (reviewed) labels are used as ground truth.
   - The limitations are written: single annotator, gold size, synthetic CVs, snapshot date.
6. **Evidence to keep.** metric tables; evaluation output files; docs/failures.md; ledger totals.
7. **Estimate and dependencies.** Historical half-day/under US$1 estimates require fresh inference preflight and actual top 10-union review counts under D-053. Human capacity is 2-3 hours/day. Depends on: Test labels complete and reviewed. This is the most important dependency of CP2.
8. **Fallback.** Report only coverage-eligible CV/metric combinations, with planned/completed counts and hold reasons. Do not condense ranks, impute missing labels or select favorable CVs. Paired comparisons require the same eligible CV subset and pool. Pending labels are never gold.
9. **Status and next step.** DONE (6-7 Oct 2026). Test run `cp24_test_v1` after the D-087 freeze (US$1.44); labels `test_v13_cp24_r1` (D-088: AI-assisted, human-reviewed, blind to ranking, one reviewer); report `evals/results/cp24/heldout_report_v1.json` under `cp24-report-contract-v1`. Headline CV3-CV5: P@5 0.533 -> 0.733 (3/3 CVs); NDCG@10 0.805 -> 0.960 for CV3-CV4 only (2/3 CVs; CV5 unavailable, F00070 unjudged). CV1-CV2 supplementary only. Test extraction and evidence F1 are not measured; D-045 assigns them to CP3.5. Locked from optimization by D-089. Historical readiness note: the runner and workbook builder refused to run before an approved freeze.

### CP2.5: Evaluation Result Visualization (checkpoint 12)

Template name: Visualisasi Evaluation Result · Official: 2 Oct 2026 · Planned work: 3 Oct 2026 · Report: [CP2_05_Evaluation_Visualization.md](checkpoint_2/CP2_05_Evaluation_Visualization.md)

JobFit version: Same as the template: charts of the evaluation results.

1. **Goal.** Make the experiment and evaluation results easy for the mentor and recruiters to understand.
2. **Inputs and prerequisites.**
   - Checkpoint 10 and 11 results
3. **Steps.**
   1. Stage-1 comparison chart (Recall@K per method).
   2. NDCG@10 and P@5: stage-1 order vs final order.
   3. Evidence confusion matrix.
   4. Quality vs cost vs latency chart.
   5. Hard-negative and failure examples as short cases.
4. **Files and outputs.** `reports/figures/cp2/`; PPT-ready assets; this stage report.
5. **Tests and acceptance criteria.**
   - Every chart shows its configuration, version, and denominator.
   - The comparisons are correct (same split, same labels).
6. **Evidence to keep.** figure files; the script that makes them.
7. **Estimate and dependencies.** About 2-3 hours. Depends on: Checkpoint 11 results.
8. **Fallback.** Use clear tables instead of polished charts.
9. **Status and next step.** DONE. Development figures 1-8 (4 Oct, `scripts/build_cp2_figures.py`), held-out figures 9-11 and tables (7 Oct, `notebooks/02_cp2_heldout_evaluation.ipynb`, receipt `evals/results/cp24/cp25_tables_v1/receipt.json`), Phase A figures A1-A4. Next: CP2.6.

### CP2.6: Recommendation and Summary (checkpoint 13)

Template name: Recommendation & Summary · Official: 3 Oct 2026 · Planned work: 3 Oct 2026 · Report: [CP2_06_Recommendation_and_Summary.md](checkpoint_2/CP2_06_Recommendation_and_Summary.md)

JobFit version: Error analysis, keep/remove decisions, and freezing the v1 architecture.

1. **Goal.** Freeze the v1 architecture based on the evidence, and write what was learned.
2. **Inputs and prerequisites.**
   - Checkpoints 10 to 12 results
   - docs/failures.md
3. **Steps.**
   1. Error analysis by category: filter miss, stage-1 miss, extraction error, matching error, ordering error.
   2. Final decisions: stage-1 method, K, model, prompt, PARTIAL weight.
   3. Keep/remove decisions for everything tested.
   4. Limitations and next-version ideas (import link, adjacent roles, reranker).
4. **Files and outputs.** docs/decisions.md entries; docs/failures.md; architecture v1 diagram; this stage report.
5. **Tests and acceptance criteria.**
   - The final architecture can be explained as consequences of the experiments.
6. **Evidence to keep.** docs/decisions.md entries; error analysis table.
7. **Estimate and dependencies.** About 2-3 hours. Depends on: Checkpoints 11 and 12.
8. **Fallback.** If time is short, keep the error analysis to the top 3 error categories with examples.
9. **Status and next step.** DONE (final summary 7 Oct 2026, after the held-out test). Final choices trace to D-083, D-086, D-087 and D-090; the 4 Oct provisional summary (DeepSeek matching, K 20) is kept as history. Next: CP2.7.

### CP2.7: CP2 Presentation and Mentoring (checkpoint 14)

Template name: PPT Check Point 2 + Mentoring · Official: 4 Oct 2026 · Planned work: 3-4 Oct 2026 (deck draft on 3 Oct) · Report: [CP2_07_Presentation_and_Mentoring.md](checkpoint_2/CP2_07_Presentation_and_Mentoring.md)

JobFit version: Same as the template: CP2 presentation and mentoring.

1. **Goal.** Show the model and system selection, tuning, and evaluation, and get the mentor's feedback on the CV-first flow and the deployment scope.
2. **Inputs and prerequisites.**
   - Checkpoints 8 to 13 results
   - Playbook section 6 (CP2 minimum content)
3. **Steps.**
   1. Build the deck following Playbook section 6.
   2. Include the CV-first flow with optional filters as a proposal, and the reason import link is out of v1.
   3. Show real metrics, failures, and limitations; missing results are shown as missing, not estimated.
   4. Rehearse once with timing.
   5. Present, then write down the mentor's feedback.
   6. Upload the deck to the LMS (Dion). This is a bootcamp task handled outside the repository and is not tracked here.
4. **Files and outputs.** CP2 deck in `04_Checkpoint_2/`; mentor feedback summary; this stage report.
5. **Tests and acceptance criteria.**
   - The mentor sees a measurable selection, tuning, and evaluation process.
   - The mentor's feedback is recorded in docs/decisions.md as new entries.
6. **Evidence to keep.** deck file; feedback notes.
7. **Estimate and dependencies.** About half a day for the deck, plus the session. Depends on: Checkpoints 11 to 13.
8. **Fallback.** If a result is not ready, present the method and what is missing, with the reason.
9. **Status and next step.** DONE. I presented on 4 Oct 2026 with deck v3 (kept in `04_Checkpoint_2/`, outside the repository). Both acceptance criteria are met: the mentor saw the measured selection, tuning and evaluation process, and the feedback is recorded as D-093. I did not record a timed rehearsal; that is a method step, not an acceptance criterion. Earlier versions of this line said "DONE (presented and mentored 4-5 Oct). Mentor notes to be added" without a source, and the first closeout pass treated CP2.7 as open until the feedback was written up. Next: CP3.1 takes D-093 as its checkpoint-14 input.

### CP3.1: API Deployment with FastAPI (checkpoint 15)

Template name: Deployment API menggunakan Flask/FastAPI · Official: 5 Oct 2026 · Planned work: 5 Oct 2026; CP3 additions 8 Oct 2026 · Report: [CP3_01_FastAPI_Service.md](checkpoint_3/CP3_01_FastAPI_Service.md)

**JobFit scope:** public-beta API for both flows (Find Jobs; Check a Job with a pasted JD), safety controls and instrumentation (D-102). JobFit version: FastAPI (Flask is not used). Daily checklist: [CP3 execution plan](checkpoint_3/CP3_Execution_Plan.md).

1. **Goal.** Make the business logic callable through a consistent, tested API, safe enough for arbitrary public CVs.
2. **Inputs and prerequisites.**
   - Modules frozen in checkpoint 13 (D-087)
   - Mentor feedback from checkpoint 14 (D-093)
   - CP3 decisions D-095 to D-100, D-101 (Phase 2B safety semantics) and D-102 (portfolio / controlled public beta scope)
3. **Steps.**
   - **Completed (6 Oct, local only):**
     - all planned endpoints;
     - request and response schemas;
     - session TTL (lease, idle, absolute) with owner checks;
     - consent bound to the exact masked text;
     - upload cleanup;
     - per-session run limits;
     - API tests covering PR-01 to PR-07 and PR-09 with a fake run.
   - **Completed (7 Oct, Phase 2A, local and CI; see the [CP3.1 report](checkpoint_3/CP3_01_FastAPI_Service.md#results-7-oct-2026-phase-2a)):**
     - fail-closed settings, with live and public live off by default (commit `1574e31`);
     - deterministic phase bounds from versioned config (commit `9286fd9`, corrected in `3f20f55` and `aa33f10` after the 8 Oct Codex review). `full_analysis_upper_bound` = US$84.7704449, which is US$82.7704449 above the US$2/day cap, so public live is **not eligible** under D-096. D-096 is unchanged; Dion and Codex decide the next step.
   - **Owner additions, planned (D-095, D-096):**
     - a persistent production ledger: **DONE for Phase 2 acceptance (local/CI); deployed host persistence validation pending Phase 8** (independently closed 8 Oct at `f5d6cf7`; [CP3.1 report](checkpoint_3/CP3_01_FastAPI_Service.md#results-8-oct-2026-persistent-production-ledger-storage));
     - the D-096 condition `full_analysis_upper_bound` ≤ US$2/day cap. The bounds now exist (see Completed above), and the condition is **not met**;
     - **separate parse and recommendation reservations** (reserve, settle, release; embedding only in the recommendation reservation; no billable call without a reservation);
     - one live analysis at a time;
     - one ticket per IP per 24 h (HMAC, consumed at the first billable call);
     - an internal service token for the forwarded client IP;
     - an owner override for the per-IP limit only;
     - a session rate limit;
     - `/docs` off;
     - proxy headers;
     - readiness with a database check;
     - an error taxonomy.
   - **Public-live scope, planned (D-097):**
     - the consent lease stored server-side;
     - the **consent compatibility adapter around the frozen CP2 parser** (entered only through `SessionStore.dispatch`; 7 required tests; stop if `is_synthetic` has another dependency);
     - the `cv_source = demo | upload` API contract (one pipeline; no CV posted back by the browser);
     - runtime query embedding of the consented masked text;
     - a production retriever over active, canonical, target-role jobs;
     - a lazy JD extraction cache with parallel prefetch;
     - a concurrency-safe app client (FAIL-36).
   - **Privacy requirements, planned:**
     - name and address hints and correct masking text (FAIL-37);
     - **upload hardening:**
       - only `.pdf` / `.docx` / `.txt` / `.md`, which the current extractor already supports;
       - an extension allow-list and a signature check;
       - a streamed size limit before buffering;
       - the existing page and character bounds;
       - a **DOCX decompression gate** (entry count, uncompressed size, compression ratio, `word/document.xml` required);
       - an extraction timeout;
       - safe errors with no file content.
   - **Monitoring, planned (D-099):**
     - request IDs and JSON logs (minimal version in P0);
     - `/metrics` with bounded labels;
     - a Langfuse Japan adapter, metadata only;
     - canary tests for logs, metrics and Langfuse payloads.
     - *(8 Oct, anti-overengineering correction under D-102: the beta needs the JSON logs and `/metrics`; the Langfuse adapter is P2 (post-beta).)*
   - **Mentor additions, planned (D-093 A):** stage events for the waiting UX.
4. **Files and outputs.**
   - The FastAPI app in `src/`.
   - New non-frozen modules for the app client, phase bounds, the consent adapter, the observability package and the extraction cache.
   - API tests.
   - This stage report.
5. **Tests and acceptance criteria.**
   - The core flow works without Streamlit.
   - Invalid input fails with a clear error.
   - Every LLM and embedding call needs an active phase reservation, and settled spend plus outstanding reservations never exceeds the cap.
   - Serial and concurrent `Recommendation` outputs are identical on a fake SDK, with one ledger line per call.
   - No provider call without a valid consent lease (the 7 adapter tests).
   - Every upload failure path is safe, including the 6 DOCX gate tests, with canaries.
   - `prepare_cp23_freeze.py --verify` stays `"ok": true`.
6. **Evidence to keep.** Test output; the OpenAPI screenshot (taken locally, since `/docs` is off in production); the phase-bound config record.
7. **Estimate and dependencies.** Core changes on 8 Oct. Depends on: Phase 1 green CI (FAIL-35, done 7 Oct); the CP3.2 Alembic schema for the cache, quota and reservation tables.
8. **Fallback.** If the public path is not ready by the freeze, public live stays off. The VPS then serves the saved demo, plus owner-token live runs, and the report says so.
9. **Status and next step.** PARTIAL.
   - DONE LOCALLY: the demo-CV flow (6 Oct, EXP-20261006-CP3).
   - DONE (7 Oct, Phase 2A; corrected 8 Oct): fail-closed settings and the deterministic phase bounds. The full bound (US$84.7704449) is above the US$2/day cap, so public live is not eligible. The live client is not yet wired to `client_settings()` (Phase 2B).
   - PLANNED / NOT YET VALIDATED: the rest of the public live path and the safety controls.
   - Next: Dion and Codex decide on the bound result, then Phase 2B (reservations, quota, upload hardening, adapter). The Alembic schema it needs is in place (CP3.2, 8 Oct).
   - DONE (8 Oct, Phase 2B, D-101): the dark, fail-closed cost-safety runtime (reservations, correlated ledger, phase-scoped gate, ticket, internal token, owner override, idempotency). A recommendation is refused at the US$2/day cap; public live stays blocked by the D-096 bound ([results](checkpoint_3/CP3_01_FastAPI_Service.md#results-8-oct-2026-phase-2b-dark-safety-layer)). Upload hardening and the consent adapter remain.
10. **Definition of Done.**
    - All P0 items implemented with their tests.
    - Offline suite: 0 unexpected failures.
    - Freeze verify passes.
    - No CV content in logs, metrics, traces or errors (canary tests).
    - `.env.example` updated.
    - This report and the execution plan updated with evidence.

### CP3.2: Database Integration and CI/CD (checkpoint 16)

Template name: Integrasi Database & GitHub Actions CI/CD · Official: 6 Oct 2026 · Planned work: 6 Oct 2026; CP3 additions 8-9 Oct 2026 · Report: [CP3_02_Database_and_CICD.md](checkpoint_3/CP3_02_Database_and_CICD.md)

**JobFit scope:** production corpus, job sync, VPS and delivery. JobFit version: PostgreSQL with pgvector, GitHub Actions, and a SumoPod VPS (D-095 replaces the Railway target of D-023). Target (D-102): one VPS for a controlled public beta, built to a public-beta standard, with every operator and observability interface private.

1. **Goal.** Make the system reproducible from a fresh clone and deployable, with a production job corpus that stays fresh.
2. **Inputs and prerequisites.**
   - The checkpoint 15 API
   - A SumoPod VPS (Singapore, Ubuntu 24.04 LTS, 2 vCPU / 8 GB / 80 GB), bought and configured by Dion and Codex
   - D-098 production corpus decision
3. **Steps.**
   - **Completed:**
     - idempotent snapshot load;
     - Docker images and compose (local);
     - the GitHub Actions workflow.
     - The workflow was red because of FAIL-35 until Phase 1 (7 Oct, commit `33c5584`); it is now green.
   - **Planned, CI (P0/P1):**
     - re-apply the FAIL-35 fix cleanly (DONE, Phase 1);
     - pin `ruff` and add `F` for `src` and `ui`, with the two D-087 frozen files exempted for F401 (DONE, Phase 1);
     - freeze verify (DONE, Phase 1);
     - `docker compose … config`;
     - a pgvector service job (Alembic up, and down/up where reversible; database-gated tests);
     - the internal `e2e_check` against the composed stack.
     - No provider secrets in CI.
   - **Database, planned (D-098):**
     - a minimal Alembic baseline (`0001` = current `SCHEMA_SQL`; `0002` = lifecycle, `dedupe_status`, `job_sources` unique on source and source job id, `sync_runs`, extraction cache, quota, reservations);
     - upgrade-first deploys only after a verified backup;
     - recovery = the previous tag plus a restore.
     - The CP2 `SCHEMA_SQL` and loader stay unchanged.
   - **Production corpus and sync, planned** ([production-corpus.md](production-corpus.md)):
     - seed from a restore-tested dump (632 rows; 428 target active; all canonical);
     - a production query manifest (≤ 80 requests per sync);
     - `jobfit.jobs.sync`:
       - normalize;
       - exact duplicates mapped to the canonical job with no new row;
       - fuzzy suspects `review_required` and inactive, kept out of retrieval;
       - NEW / CONTENT_CHANGED / METADATA_CHANGED / UNCHANGED / STALE;
       - coverage-aware lifecycle (2 syncs / 30 d / 60 d);
       - incremental embeddings;
       - a report;
     - a dedupe review command;
     - a GitHub Actions trigger, twice a month (about every two weeks), using a forced-command SSH key. JSearch and database secrets stay on the VPS.
     - *(8 Oct, anti-overengineering correction under D-102: this sync automation is P2 (post-beta). The design stays; the seeded corpus is enough for the beta, with an optional one-time manual refresh before the demo.)*
   - **Deployment, planned (D-095):**
     - `docker-compose.prod.yml` with Caddy (only 80/443 public), restart policies, log rotation and healthchecks;
     - a runtime artifact manifest and verifier (the tokenizer built into the API image);
     - a restore-tested initial dump before the first deploy; nightly backups before the freeze *(8 Oct: a verified backup and a successful restore test are required before the beta; nightly scheduling is P2 (post-beta) unless trivial)*;
     - manual tagged deploys;
     - a VPS runbook.
   - **Monitoring, planned (D-099):** Prometheus, Grafana and node_exporter; email alerts through `GRAFANA_SMTP_*`; a backup-age metric; sync gauges. *(8 Oct lean beta bar: structured logs, Prometheus, Grafana with application, AI-pipeline, LLM and cost, and basic VPS health are required; email alerts, extra dashboards and sync gauges are P2 (post-beta).)*
4. **Files and outputs.**
   - CI workflows (`tests.yml`, `job-sync.yml`), Alembic revisions, the sync module, deploy files, the runbook, `production-corpus.md`.
   - This stage report.
5. **Tests and acceptance criteria.**
   - A fresh clone creates the schema and passes the tests.
   - No secrets in the repository or the workflows.
   - CI is green.
   - **Two-layer deployed validation:**
     - A: Internet → Caddy → Streamlit over HTTPS shows the page and the saved demo;
     - B: the internal API `e2e_check.py` passes inside the VPS Docker network or through an SSH tunnel. FastAPI is never public.
   - Alembic works on an empty and a restored database.
   - The restore test matches the row counts.
   - A real sync and an idempotent re-run give 0 NEW, 0 CONTENT_CHANGED and 0 METADATA_CHANGED, with exact duplicates counted and no second row.
   - **The same vacancy never appears twice in production retrieval.**
6. **Evidence to keep.** CI links; the row-count table; the restore log; sync reports; deploy-tag notes.
7. **Estimate and dependencies.** CI on 7 Oct; schema and packaging on 8 Oct; sync on 9 Oct. Depends on: VPS provisioning, DNS, SMTP, and the production OpenRouter key (Dion and Codex).
8. **Fallback.** If the scheduled sync is not on `main` before the presentation, the sync is shown with a manual SSH-triggered run. If the VPS is blocked, the saved demo runs locally and the report states the limit.
9. **Status and next step.** PARTIAL. Docker, compose and the CI workflow exist; CI is green after Phase 1 (FAIL-35 resolved; run [37641393567](https://github.com/Gidion123/Job-Fit/actions/runs/37641393567)); nothing is deployed; the production corpus and sync are PLANNED. Alembic `0001` (exact CP2 baseline) and `0002` (production schema) are DONE with a verified-stamp path and migration tests in CI (8 Oct, [results](checkpoint_3/CP3_02_Database_and_CICD.md#results-8-oct-2026-alembic-00010002)). Next: `verify` on the local CP2 database, then packaging and the sync.
10. **Definition of Done.**
    - CI green.
    - The production stack deployed and checked through both validation layers.
    - Backup and restore tested.
    - A sync run and an idempotent re-run recorded.
    - The runbook and this report updated with evidence.

### CP3.3: Streamlit UI (checkpoint 17)

Template name: Build Streamlit UI · Official: 7 Oct 2026 · Planned work: 7 Oct 2026; CP3 additions 8-9 Oct 2026 · Report: [CP3_03_Streamlit_UI.md](checkpoint_3/CP3_03_Streamlit_UI.md)

**JobFit scope:** product experience: Find Jobs and Check a Job, public upload flow, stage-aware progress and "Improve My CV for This Job" (D-102). JobFit version: the template (Streamlit), with no business logic in the UI.

1. **Goal.** A demo that shows the value in under 3 minutes, and a safe, honest public upload flow.
2. **Inputs and prerequisites.**
   - The deployed API from checkpoint 16
   - D-093 mentor feedback, refined by D-102 (stage-aware progress; "Improve My CV for This Job")
3. **Steps.**
   - **Completed (6 Oct, local):**
     - demo CVs and the saved demo;
     - filters;
     - recommendation cards;
     - job detail with evidence;
     - paste and compare;
     - market counts;
     - CV suggestions and coach v1;
     - feedback and delete;
     - the privacy notice, an editable masked preview and consent.
   - **Public-live and privacy additions, planned:**
     - a required name field and an optional address field (FAIL-37);
     - masking text that lists exactly what is masked;
     - consent text naming the providers as recorded;
     - an upload allow-list matching the API (`pdf`, `docx`, `txt`, `md`);
     - Streamlit `maxUploadSize` and the Caddy body limit;
     - safe messages for unsupported, oversized, encrypted, scanned and malformed files, including rejected DOCX archives;
     - quota, busy and budget messages with a saved-demo fallback;
     - client-IP forwarding with the internal token.
   - **Mentor additions, planned (D-093):**
     - A: stage text, job i of K, elapsed time, a measured typical range, graceful timeout and error states, and cancel where safe. No fake percentages.
     - B: each coach item shows its source requirement and the CV evidence status, with no-invention and no-guarantee wording. No LLM coach (stands until a D-102 gate decision on LLM-written CV wording).
   - **Product experience, planned (D-102):**
     - a landing with public-beta wording and the two primary actions, **Find Jobs** and **Check a Job** (pasted JD);
     - stage-aware progress driven by the real pipeline stages of each flow (completed, current, pending), aligned with the latency metrics;
     - job cards and detail with the match score, strengths, gaps, supporting evidence and explanations;
     - empty, failure, unavailable and budget-exhausted states with the saved-demo fallback;
     - "Improve My CV for This Job": representation improvement from existing evidence only, possibly missing (add only if real), true gap stated plainly; current statement → suggestion → why → supporting evidence; the hard anti-fabrication rule. Any LLM-written wording needs its own bound, reservation, evaluation and decision;
     - consistent typography, spacing and components; reasonable mobile and desktop layout. Priority: clarity > trust > usability > polish > decoration.
4. **Files and outputs.** The Streamlit app; screenshots; a short recording; this stage report.
5. **Tests and acceptance criteria.**
   - A mentor understands the value in under 3 minutes.
   - The synthetic demo works.
   - No business logic in the UI.
   - The screen never looks frozen longer than the poll interval.
   - Every upload failure shows a safe, specific message.
   - Coach checks: 0 invented items, and "not done" gives no bullet.
   - Both flows are reachable from the first screen, and each refusal code has a specific, honest message (D-102).
   - "Improve My CV for This Job": 0 invented skills, experience, metrics or tools; every representation suggestion cites existing CV evidence (D-102).
6. **Evidence to keep.** Screenshots (including the waiting states and upload errors); a short recording.
7. **Estimate and dependencies.** The upload flow on 8 Oct; waiting UX and coach on 9 Oct. Depends on: the CP3.1 public path and stage events.
8. **Fallback.** Core flow first; styling last.
9. **Status and next step.** PARTIAL: DONE LOCALLY for the demo flow; the public upload flow and the mentor refinements are PLANNED / NOT YET VALIDATED.
10. **Definition of Done.**
    - The public upload journey and the waiting UX are checked on the deployed app (CP3.4).
    - Streamlit tests pass.
    - Screenshots saved.
    - This report updated.

### CP3.4: End-to-End Testing (checkpoint 18)

Template name: Testing End-to-End Application · Official: 8 Oct 2026 · Planned work: 9 Oct 2026 (formal feature freeze at the end of 9 Oct, D-100) · Report: [CP3_04_End_to_End_Testing.md](checkpoint_3/CP3_04_End_to_End_Testing.md)

**JobFit scope:** controlled public beta validation (both flows, real-host persistence, public-beta states), privacy release gate and feature freeze. Acceptance uses the D-102 public-beta bar, not enterprise reliability. JobFit version: the template, on the deployed VPS stack.

1. **Goal.** Test the real public journey and the critical failure paths on the deployed app, pass the privacy release gate, then freeze features.
2. **Inputs and prerequisites.**
   - The deployed app from checkpoints 16 and 17 (P0 done)
   - D-092 privacy deferral
   - D-096 budgets
3. **Steps (all PLANNED unless noted).**
   - **Two-layer validation:**
     - A: external public smoke and journey through Caddy and Streamlit (HTTPS, saved demo, the real-CV journey once enabled, user-visible failures);
     - B: the internal API `e2e_check.py` inside the VPS Docker network or through an SSH tunnel. FastAPI stays private.
   - **Privacy release gate:**
     - PR-01 to PR-10, with synthetic canaries through every sink: responses, provider payloads, logs, database, temporary files, `/metrics`, Langfuse export and upload failure paths;
     - PR-08 fail-closed;
     - the OpenRouter per-route privacy record (parse, embedding, extraction, matching). A gap is reported before public live and never fixed by changing the model, prompt, K or weights.
   - **Cost and abuse:**
     - `full_analysis_upper_bound` ≤ the cap;
     - quota fairness;
     - the daily cap;
     - the busy gate.
   - **Owner-run paid checks** (inside the US$5): public-live E2E, a latency baseline with stage timings, and FAIL-36 confirmation (offline fake proof plus a live measurement).
   - **Sync:** a VPS sync test, with no duplicate vacancy in retrieval.
   - **Monitoring:** one test alert email; screenshots.
   - **Mentor A/B validation** on the deployed app.
   - **PR-10** (original vs masked, CV1/CV2, about US$2).
   - **Enable public live** only after the gate passes.
   - **Record the feature freeze.**
4. **Files and outputs.** `evals/results/cp34/*`; the E2E checklist; the latency and cost table; the gate record; this stage report.
5. **Tests and acceptance criteria.**
   - Both validation layers pass.
   - Canary scan: 0 hits.
   - The gate passes before `JOBFIT_PUBLIC_LIVE=1`.
   - The latency and cost table is recorded honestly. No claim about the mentor's 95 s without a measurement.
   - 0 unexpected offline failures at the freeze.
   - Freeze verify ok.
6. **Evidence to keep.** Checklists, test outputs, the gate record, the latency and cost table, alert and dashboard screenshots.
7. **Estimate and dependencies.** 9 Oct. Depends on: the deployed stack with all P0 items.
8. **Fallback.** If the gate is not green by the freeze, public live stays off: the presentation uses owner-token live plus the saved demo, and the report says so. A backup video is recorded.
9. **Status and next step.** PARTIAL. Local end-to-end 27/27 (6 Oct); all deployed checks are PLANNED / NOT YET VALIDATED.
10. **Definition of Done.**
    - The final validation table complete (command, passed, skipped, failed, reason for each skip).
    - The gate status recorded.
    - The freeze recorded in the decision log.
    - This report updated.

### CP3.5: Final Presentation and Portfolio (checkpoint 19)

Template name: PPT Final Project / Portfolio · Official: 9 Oct 2026 · Planned work: 10 Oct 2026 (after the freeze) · Report: [CP3_05_Final_Presentation_and_Portfolio.md](checkpoint_3/CP3_05_Final_Presentation_and_Portfolio.md)

**JobFit scope:** final evidence, D-045 results, privacy and latency reports, deck and video. The story keeps the AI system at the center: design, pipelines, retrieval, LLM orchestration, evidence grounding, evaluation, cost engineering, then deployment and monitoring (D-102). JobFit version: the template.

1. **Goal.** Build the final story from evidence: problem, data, experiments, final system, evaluation, deployment, limitations.
2. **Inputs and prerequisites.**
   - All earlier stage reports
   - Playbook section 12 (presentation story)
   - CP3.4 results
3. **Steps.**
   - Final deck draft; README update with CP2 and CP3 results; a 2-4 minute demo video; limitations and what was deliberately not built.
   - **D-045, option B (D-100), PLANNED / NOT YET COMPLETED:**
     - Phase 0 selected unseen candidates by job ID only: F00398, F00237 and CV3 × F00398.
     - Dion labels them blind first and locks the file hash.
     - Only then does the frozen pipeline run (about US$0.10).
     - The existing workbook (MODEL-ASSISTED, HUMAN-REVIEWED) is imported, aligned and scored.
     - The two groups are reported separately.
     - Test labels are never used for tuning.
   - **Privacy report** (D-092): the CP3.4 gate results and the PR-10 matching-quality impact.
   - **Latency and cost report;** monitoring screenshots.
4. **Files and outputs.** The final deck in `05_Checkpoint_3/`; the updated README; the demo video; the D-045 result files; this stage report.
5. **Tests and acceptance criteria.**
   - Every big claim has evidence or a metric.
   - Validated and planned items are clearly separated.
   - The deck is not full of jargon without a story.
6. **Evidence to keep.** The deck file, the README commit, the video link, the D-045 hashes.
7. **Estimate and dependencies.** 10 Oct. Depends on: the CP3.4 results; Dion's blind-labeling time.
8. **Fallback.** Use screenshots from CP3.4 if a live recording fails. D-045 is not descoped without Dion's approval.
9. **Status and next step.** PLANNED / NOT RUN (the D-045 candidate selection is done).
10. **Definition of Done.**
    - The D-045, PR-10, privacy, and latency and cost results reported.
    - The deck, video and README done.
    - This report updated.

### CP3.6: Finalization and Rehearsal (checkpoint 20)

Template name: Finalisasi Portfolio & Rehearsal Presentation · Official: 10 Oct 2026 · Planned work: 10 Oct 2026 · Report: [CP3_06_Finalization_and_Rehearsal.md](checkpoint_3/CP3_06_Finalization_and_Rehearsal.md)

**JobFit scope:** regression, rehearsal and release tag. JobFit version: the template.

1. **Goal.** Reduce the risk of the demo or the presentation failing.
2. **Inputs and prerequisites.** Checkpoint 19 outputs.
3. **Steps.**
   1. Full regression run, as the final validation table in the [CP3 execution plan](checkpoint_3/CP3_Execution_Plan.md):
      - offline and database-gated pytest; ruff; freeze verify; both Docker builds; prod compose config;
      - Alembic; restore;
      - validation layers A and B;
      - the canary scan; sync idempotency; the phase bounds;
      - green GitHub Actions.
   2. Rehearse with timing, including the owner-token step for a shared presentation network; prepare backup screenshots and video.
   3. Proofread the README and the documents.
   4. Release tag (Dion runs git).
   5. Upload the deck to the LMS (Dion). This is a bootcamp task handled outside the repository and is not tracked here.
4. **Files and outputs.** The final deck; a release candidate; rehearsal notes; this stage report.
5. **Tests and acceptance criteria.** No new features. The live app, the backup demo and the metrics are consistent.
6. **Evidence to keep.** Regression output; the tag link.
7. **Estimate and dependencies.** About half a day plus rehearsal. Depends on: checkpoint 19.
8. **Fallback.** If a bug appears, fix it only if it is critical; otherwise note it as a known issue.
9. **Status and next step.** PLANNED / NOT RUN. Next: CP3.7.
10. **Definition of Done.**
    - Regression table complete with 0 unexpected failures.
    - Rehearsal timed.
    - Tag created.
    - CP3 work merged to `main` by Dion after review (D-095).

### CP3.7: Final Presentation and Submission (checkpoint 21)

Template name: Final Project Presentation + Pemberian Tugas Portofolio · Official: 11 Oct 2026 · Planned work: 11 Oct 2026 · Report: [CP3_07_Final_Presentation_and_Submission.md](checkpoint_3/CP3_07_Final_Presentation_and_Submission.md)

**JobFit scope:** present the deployed public JobFit, with the saved demo as the safe fallback. JobFit version: the template.

1. **Goal.** Present the value, the process and the trade-offs, and submit the project and portfolio links.
2. **Inputs and prerequisites.** Final deck, live app, backup video.
3. **Steps.**
   1. Present for 15-20 minutes, following the mentor's direction.
   2. Live demo on the deployed app (public live if the gate passed; otherwise owner-token live), with the saved demo as the safe option.
   3. Explain actual results and limitations, including the planned-versus-validated status of every CP3 item.
   4. Submit the links (project, demo, deck, portfolio) as the mentor asks.
   5. Write the mentor's final feedback and a short retrospective.
4. **Files and outputs.** Submission proof; final feedback notes; a retrospective draft; this stage report.
5. **Tests and acceptance criteria.** Can answer why, alternatives, trade-offs, metrics and failures for the main components.
6. **Evidence to keep.** Submission proof; links.
7. **Estimate and dependencies.** The presentation day. Depends on: checkpoint 20.
8. **Fallback.** Use the backup video if the live demo fails.
9. **Status and next step.** PLANNED / NOT RUN. Next: project done; possible next-version work is listed in docs/decisions.md.
10. **Definition of Done.**
    - Presented and links submitted.
    - Mentor feedback recorded as a decision.
    - Retrospective written.
---

## 9. After each stage

1. Set the stage status and the actual date in section 2 of this plan and in the stage report.
2. Fill the report's results, interpretation, limitations, and decisions with real outcomes. Link to the [experiment log](experiments.md) instead of copying numbers.
3. Add any new decision to the [decision log](decisions.md), and any new failure to the [failure log](failures.md).
4. If the public project state changed (a checkpoint closed, a major feature or deployment milestone, a new headline result), update the current-status parts of the root `README.md` in the same change. The README is the public progress snapshot; it summarizes and links, and never claims more than the stage reports.
5. Dion commits and pushes (only Dion runs git), then puts the link to the stage report in the "Real" column of the Timeline file as proof of work.


## Historical execution note: 2 October 2026

CP2.2 remains IN PROGRESS. Controlled v1.2 pilot extraction stopped after J3 structural uncertainty; J4 completed after one repair, F00073 unattempted. Following D-049, runtime guideline v1.3 and new stage prompts are implemented and tested offline (213passes); no live v1.3 quality claim. CP2.3 metric/comparison/readiness tools are prepared, but formal tuning/selection remains NOT RUN pending reviewed development inputs, semantic alignment/completeness and metric conventions. See [CP2.2 audit](checkpoint_2/supporting/CP22_Pipeline_Audit_20261002.md) and [CP2.3 preparation](checkpoint_2/CP2_03_System_Tuning.md). The active workbook remains under human review; no automatic label export or approval. Eight human fixture approvals remain pending. No acceptance checkbox was promoted from tests alone.


## Historical: development review submission (2 October 2026)

See [review report](checkpoint_2/supporting/Development_Labeling_Review_20261002.md). No change to official dates, test split, budget, or metric contract. Record actual labeling time only after Timing is complete. CP2.2 remains IN PROGRESS. Next dependency is valid approved-only staging, followed by acceptance checks and development benchmarking, not additional bulk labeling.


## Historical technical closure note: 2 October 2026

[CP2.2 closure checklist](checkpoint_2/CP2_02_Modeling_Pipeline.md) now separates implemented work, independent preparation, human fixture/semantic acceptance and cost/scope gates from CP2.3-only evaluation dependencies. [Single acceptance summary](checkpoint_2/supporting/CP22_Acceptance_Review_20261002.md) covers the same eight fixtures, local top 30 retrieval and a preflight-only v1.3 proposal. Latest workbook review closure is accepted as reported; no full labeling redo requested. F00018 cloud/AWS both preferred; F00369 source provenance unresolved. Current ledger US$0.21270144 includes US$0.0210861 uncertain reservation from a separate interrupted run. This technical task cost US$0. CP2.2 IN PROGRESS; CP2.3 tuning NOT RUN. Earlier costs, review counts, dates and estimates are historical unless explicitly identified as current.


### Historical: 3 October 2026 explicit CP2.2 closure decision

D-050 supersedes earlier IN PROGRESS/broad-outcome blocker statements for CP2.2. The user approved implementation closure and deferred mass extraction until CP2.3 configuration evaluation. Current evidence is in the main English CP2.2 report. Broad extraction, model-quality measurement and configuration selection are not claimed done; old scope/experiment entries remain historical. No default prompt/model/K winner, metric choice, gold change or additional paid batch follows from this decision.

## CP2.3-CP2.4 protocol amendment, 3 October 2026 (D-053; executed 6-7 October under D-087 and D-088)

Before held-out processing, approve and freeze configuration **and** test protocol per [evaluation.md section 7](evaluation.md#7-held-out-confirmation-protocol-d-053): models, embedding, prompts, preprocessing/masking, K/filters/order/repair, metric and alignment conventions, split hashes and pool construction. The test relevance pool is the union of original top 10 retrieval and top 10 final recommendations per CV, with review counts/effort checked before workbook creation. D-052 development comparison remains unchanged; this is not permission to open test during stage 1. D-050 broad development extraction still needs its own quality/budget plan; D-051 privacy gates still apply. No freeze or test execution is claimed by this update.

CP2.4 uses blind labels for the selected system’s top 10-union pool, replacing the historical fixed 12/CV target. Report exact effort before preparation; capacity remains 2-3 hours/day. Original-position P@5/NDCG@10 need full required judgments, with common judged-pool IDCG and paired eligible CVs. Recall is labeled-pool diagnostic, filter recall needs pre-filter labels. Familiar-profile CV1/CV2 and held-out-profile CV3-CV5 are reported separately. Historical half-day/under US$1 estimates must be recalculated; no additional API authorization follows. Partial-label fallback cannot condense ranking or imply corpus-wide recall. See the current [CP2.4 report](checkpoint_2/CP2_04_Evaluation_Metrics.md).
