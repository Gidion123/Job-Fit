# JobFit CP2-CP3 Master Plan

Created: 29 September 2026 · Based on System Design v1.3 (`02_System_Design/`, outside this repository) and the [decision log](decisions.md) · Maps to the Execution Playbook: CP2 = checkpoints 8 to 14, CP3 = checkpoints 15 to 21.

This is the single work plan for CP2 and CP3. Each checkpoint also has its own report file ([checkpoint_2/](checkpoint_2/README.md), [checkpoint_3/](checkpoint_3/README.md)). The reports and this plan come from the same stage list, so they say the same thing.

**Status values:** PLANNED / NOT RUN · IN PROGRESS · DONE · BLOCKED. A stage is DONE only when its acceptance criteria are met and its evidence is saved.

**Three kinds of dates (D-027):**

- **Official:** from the bootcamp Timeline file. It never changes.
- **Planned work:** the revised schedule after System Design v1.3.
- **Actual:** filled in when the stage is really done.

---

## 1. Where the project stands (29 September 2026)

**Done (CP1), and reused in CP2:**

- Snapshot `CP1_20260926`: 910 estimated unique jobs, 632 EDA candidates, 428 in the target role families.
- Cleaning and features: `role_family`, `experience_bucket`, location, `work_mode`, `posted_at`, v0 skills, `content_hash`. These become the filters, the stage-1 keyword baseline, and the cache keys.
- Research notebook, 24 passing tests, CP1 reports, CP1 presentation.
- Design package: System Design v1.3, docs/decisions.md (D-001 to D-031), Canonical and Playbook v2.1, this plan, stage report plans, and the empty repository structure for the application (`docs/repo-structure.md`).

**Not done yet (all of CP2 and CP3):**

| Area | Status |
| --- | --- |
| Annotation guideline, schemas, scoring rules, development fixtures | Not started |
| Synthetic CVs and the labeling pilot | Not started |
| CV parser, JD extraction, evidence matching, paste JD path | Not started |
| Stage-1 baselines (keyword, FTS, dense, hybrid) and the recommendation list | Not started |
| Gold sets, splits, evaluation scripts | Not started |
| Usage ledger and budget guard | Not started |
| docs/experiments.md and docs/failures.md entries | Files exist, no entries yet |
| FastAPI, PostgreSQL/pgvector migrations, Streamlit, CI, Docker, deployment | Not started |

**Out of scope for v1 (D-025):** import link, auto-apply, cover letter, Strong/Realistic/Stretch labels.
**Deferred:** second job-data provider, reranker, automatic refresh, official support for adjacent roles.
**Minimal version:** market insight, evidence-based CV suggestions.

---

## 2. Dates

| # | Stage | Template name | JobFit report | Official | Planned work | Actual | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | CP2.1 | Model Selection (CNN/LSTM/DNN sesuai use case) | [Model and System Selection](checkpoint_2/CP2_01_Model_and_System_Selection.md) | 28 Sep 2026 | 29-30 Sep 2026 (labeling pilot on the evening of 29 Sep) | started 29 Sep 2026 | IN PROGRESS |
| 9 | CP2.2 | Modeling Deep Learning | [Modeling the Extraction, Search, and Evidence Pipeline](checkpoint_2/CP2_02_Modeling_Pipeline.md) | 29 Sep 2026 | 30 Sep-1 Oct 2026 | not run yet | PLANNED / NOT RUN |
| 10 | CP2.3 | Hyperparameter Tuning | [System Tuning](checkpoint_2/CP2_03_System_Tuning.md) | 30 Sep 2026 | 2 Oct 2026 | not run yet | PLANNED / NOT RUN |
| 11 | CP2.4 | Modeling + Evaluation Metrics | [Evaluation Metrics](checkpoint_2/CP2_04_Evaluation_Metrics.md) | 1 Oct 2026 | 3 Oct 2026 | not run yet | PLANNED / NOT RUN |
| 12 | CP2.5 | Visualisasi Evaluation Result | [Evaluation Result Visualization](checkpoint_2/CP2_05_Evaluation_Visualization.md) | 2 Oct 2026 | 3 Oct 2026 | not run yet | PLANNED / NOT RUN |
| 13 | CP2.6 | Recommendation & Summary | [Recommendation and Summary](checkpoint_2/CP2_06_Recommendation_and_Summary.md) | 3 Oct 2026 | 3 Oct 2026 | not run yet | PLANNED / NOT RUN |
| 14 | CP2.7 | PPT Check Point 2 + Mentoring | [CP2 Presentation and Mentoring](checkpoint_2/CP2_07_Presentation_and_Mentoring.md) | 4 Oct 2026 | 3-4 Oct 2026 (deck draft on 3 Oct) | not run yet | PLANNED / NOT RUN |
| 15 | CP3.1 | Deployment API menggunakan Flask/FastAPI | [API Deployment with FastAPI](checkpoint_3/CP3_01_FastAPI_Service.md) | 5 Oct 2026 | 5 Oct 2026 | not run yet | PLANNED / NOT RUN |
| 16 | CP3.2 | Integrasi Database & GitHub Actions CI/CD | [Database Integration and CI/CD](checkpoint_3/CP3_02_Database_and_CICD.md) | 6 Oct 2026 | 6 Oct 2026 (hosting smoke deploy earlier, on 1-2 Oct) | not run yet | PLANNED / NOT RUN |
| 17 | CP3.3 | Build Streamlit UI | [Streamlit UI](checkpoint_3/CP3_03_Streamlit_UI.md) | 7 Oct 2026 | 7 Oct 2026 | not run yet | PLANNED / NOT RUN |
| 18 | CP3.4 | Testing End-to-End Application | [End-to-End Testing](checkpoint_3/CP3_04_End_to_End_Testing.md) | 8 Oct 2026 | 8 Oct 2026 (feature freeze at the end of the day) | not run yet | PLANNED / NOT RUN |
| 19 | CP3.5 | PPT Final Project / Portfolio | [Final Presentation and Portfolio](checkpoint_3/CP3_05_Final_Presentation_and_Portfolio.md) | 9 Oct 2026 | 9 Oct 2026 | not run yet | PLANNED / NOT RUN |
| 20 | CP3.6 | Finalisasi Portfolio & Rehearsal Presentation | [Finalization and Rehearsal](checkpoint_3/CP3_06_Finalization_and_Rehearsal.md) | 10 Oct 2026 | 10 Oct 2026 | not run yet | PLANNED / NOT RUN |
| 21 | CP3.7 | Final Project Presentation + Pemberian Tugas Portofolio | [Final Presentation and Submission](checkpoint_3/CP3_07_Final_Presentation_and_Submission.md) | 11 Oct 2026 | 11 Oct 2026 | not run yet | PLANNED / NOT RUN |

**Tightest day: 3 October** (checkpoints 11, 12, 13, and the deck draft). If it slips, the checks of the minimal features move to checkpoint 18. Core evaluation is not cut.

**Feature freeze: 8 October 2026** (D-026).

---

## 3. Dependencies and approvals

| What | Owner | Needed by | Blocks | Status |
| --- | --- | --- | --- | --- |
| OpenRouter account, credit, privacy settings, and `OPENROUTER_API_KEY` in `.env` (D-028, D-030) | Dion | 30 Sep | Every LLM and embedding step | Key and credit done (US$9.22); privacy settings and key limit to confirm |
| Docker Engine starts and runs a container | Dion (run), Claude (check) | 30 Sep | Local PostgreSQL, FTS baseline | Done: `hello-world` ran on 29 Sep |
| Review of the synthetic CVs | Dion | Evening of 29 Sep, before the pilot | Pilot, gold labels | Open |
| Labeling pilot (timed) | Dion | Evening of 29 Sep | Gold sizes, guideline v1 | Open |
| Railway account on the Trial credit (D-023 approved) | Dion | 1 Oct | Smoke deploy, checkpoint 16 | Approved; account not created yet |
| Development labels reviewed (gold) | Dion | 2 Oct morning | Checkpoint 10 | Open |
| Test labels reviewed (gold) | Dion | 3 Oct morning | Checkpoint 11 | Open |
| Mentor feedback at CP2 | Mentor | 4 Oct | CP3 scope confirmation | Open |

---

## 4. Critical path

```text
guideline v0.1 → pilot (timed) → guideline v1 → split frozen → development labels → tuning (checkpoint 10)
                                                             → test labels ───────────→ evaluation (checkpoint 11) → charts → decisions → CP2 deck
in parallel: schemas + scoring + fixtures → CV parser + extraction + matcher → batch extraction → stage-1 search → recommendation list
in parallel: hosting smoke deploy (1-2 Oct) → API (5 Oct) → database + CI (6 Oct) → Streamlit (7 Oct) → E2E + freeze (8 Oct)
```

Labeling is the longest chain and depends on one person. It starts on day one and runs next to the implementation (D-015).

---

## 5. Priorities and cut order (D-026)

1. **Protected, never cut:** core evaluation, tests, privacy, deployment, the explanation of limitations.
2. **Cut first:** UI polish.
3. **Then:** extra experiments (fewer configurations, fewer model comparisons).
4. **Only with a new docs/decisions.md entry:** the minimal market insight or CV suggestions.

---

## 6. Budget

- **API cap:** all OpenRouter top-ups for CP2 and CP3 stay at or under US$15 (D-019). Credit available: US$9.22. The app guard is set to US$9 with a hard stop at US$8.50 (D-031). Hosting is counted separately.
- **Estimates before any run:** System Design v1.3 section 11. Expected LLM use is well under the cap.
- **Guard:**
  - Every call goes to `reports/usage/usage_ledger.jsonl`.
  - Each batch is estimated before it starts.
  - Calls stop when the estimated total would pass the hard stop in `.env` (now US$8.50).
  - The OpenRouter API key has its own credit limit as a second stop.
- **Estimate for all CP2 and CP3 LLM work** (29 Sep 2026, before any real call; token counts are assumptions and are checked against the ledger after the first calls in CP2.2):

  | Work | Estimate |
  | --- | --- |
  | CP2.2 prompt v1 on development cases, about 3 rounds of fixes | about US$0.25 |
  | Batch extraction of 428 target JDs, twice (baseline, then the chosen model) | about US$0.50 to 1.00 |
  | Embeddings for all 632 jobs and the CVs | under US$0.02 |
  | CP2.3 model comparison round 1, run twice (4 models x 30 cases, GPT-6 Sol on 10) | about US$1.60 |
  | CP2.3 round 2 (`deepseek-v4-pro`, only if needed) | about US$0.25 |
  | CP2.3 K experiment and CP2.4 prompt v2 | about US$0.50 |
  | CP3 demo, end-to-end tests, precomputed demo results (about 60 runs with K = 20) | about US$0.80 (GPT-6 Luna) to US$7.80 (Claude Haiku 4.5) |
  | **Total** | **about US$4 to 6 if a low-cost model wins, about US$15 if Claude Haiku 4.5 wins** (before a 1.5x safety buffer) |

  The model choice matters more than anything else. If Claude Haiku 4.5 wins by the D-029 rule, CP3 uses cached results for the demo so that a top-up stays small.
- **Hosting:** Railway (D-023, approved), estimated at US$5-12 per month. The Trial credit is used first; the concrete cost is confirmed with Dion before subscribing to the Hobby plan.

---

## 7. Labeling plan (D-015, D-016)

1. **Evening of 29 Sep:** guideline v0.1, then a pilot. For example: 5 JDs for extraction, about 20 requirement-evidence pairs, 2 CVs × 5 jobs for relevance. Dion records the time per item.
2. **After the pilot:** propose realistic gold sizes and a daily labeling load from the measured time, in a new docs/decisions.md entry. If sizes are below the Canonical targets, record the original and revised targets, the reason, the mandatory case coverage, and the impact on the conclusions.
3. **Freeze the split:** at the job-cluster level; development first, then the test set.
4. **Continue during implementation:** development labels by 2 Oct morning, test labels by 3 Oct morning.
5. **Rules:**
   - AI may suggest labels (`ai_suggested = true`).
   - Only labels that Dion reviewed become gold.
   - Unreviewed labels stay provisional.
   - No inter-annotator agreement is reported.
   - The single-annotator limitation is written in the evaluation report.

---

## 8. Stage plans

### CP2.1: Model and System Selection (checkpoint 8)

Template name: Model Selection (CNN/LSTM/DNN sesuai use case) · Official: 28 Sep 2026 · Planned work: 29-30 Sep 2026 (labeling pilot on the evening of 29 Sep) · Report: [CP2_01_Model_and_System_Selection.md](checkpoint_2/CP2_01_Model_and_System_Selection.md)

JobFit version: For an LLM and retrieval system, model selection means comparing search methods, LLM candidates, and prompt versions, not training a CNN/LSTM/DNN (D-001). This stage also sets the annotation guideline, the scoring rules, and the experiment matrix.

1. **Goal.** Set the rules, the baselines, and the experiment matrix before the full system is built, so every later choice is measured against something.
2. **Inputs and prerequisites.**
   - System Design v1.3 and docs/decisions.md (D-001 to D-031)
   - CP1 processed data: 632 EDA candidates, 428 in the target role families
   - `OPENROUTER_API_KEY` in the git-ignored local `.env` that Dion fills himself (D-028, D-030, D-031); never in chat or commits
   - Docker Engine running on the Mac (CLI 29.4.3, Compose v5.1.3; `docker run --rm hello-world` succeeded on 29 Sep 2026)
3. **Steps.**
   1. Write the annotation guideline v0.1: requirement units, evidence labels, constraint states (compatible / unknown / explicit conflict), relevance 0-3, and label record fields (`ai_suggested`, `status`, `reviewed_by`, `guideline_version`).
   2. Define the Pydantic schemas for JD requirement units and CV evidence units, with example outputs.
   3. Implement the deterministic scoring rules: match %, score status (final / provisional / on hold / no score), constraint states, ordering, and stable tie-break.
   4. Write the 8 development fixtures from System Design v1.3 section 15 and run them as tests.
   5. Draft 2-3 synthetic CVs (at least one in Indonesian); Dion checks that they are realistic.
   6. Labeling pilot: a small development sample (for example 5 JDs, about 20 requirement-evidence pairs, 2 CVs x 5 jobs). AI may suggest provisional labels; Dion decides and records the time per item. Then revise the guideline to v1.
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
9. **Status and next step.** PLANNED / NOT RUN. Next: CP2.2 (checkpoint 9): CV parser, extraction prompt v1, evidence matcher, and the 1 CV + 1 JD report.

### CP2.2: Modeling the Extraction, Search, and Evidence Pipeline (checkpoint 9)

Template name: Modeling Deep Learning · Official: 29 Sep 2026 · Planned work: 30 Sep-1 Oct 2026 · Report: [CP2_02_Modeling_Pipeline.md](checkpoint_2/CP2_02_Modeling_Pipeline.md)

JobFit version: The "deep learning modeling" of JobFit is the pipeline of pretrained models: LLM extraction, embeddings, search, and evidence matching (D-001). No neural network is trained.

1. **Goal.** Build the vertical slice: one CV and one JD produce a structured, checkable evidence report. Then prepare the pieces for the recommendation list: cached extraction for the target jobs and the dense and hybrid search.
2. **Inputs and prerequisites.**
   - Checkpoint 8 outputs (guideline v1, schemas, scoring rules, fixtures, local database, ledger)
   - OpenRouter credit available (D-030)
   - Synthetic CVs reviewed by Dion
3. **Steps.**
   1. CV text extraction (PyMuPDF, python-docx) and LLM parsing into evidence units with a parsing summary.
   2. JD extraction prompt v1 with Pydantic validation and at most 1 repair attempt.
   3. Evidence-matching prompt v1: MATCH / PARTIAL / NO_MATCH per requirement unit, with CV quotes checked to exist word for word in the CV.
   4. Constraint check: experience duration (v1.2 counting rules), location against a confirmed location, work-authorization statements.
   5. Paste JD path end to end: clean, quality signals, extract, preview, match report.
   6. Run the 8 development cases and check them by hand.
   7. Batch extraction of the 428 target JDs into the versioned cache with the baseline `deepseek-flash`, estimated first. It is re-run if another model is chosen in CP2.3.
   8. Embeddings (model per D-020), Baseline 2 dense, and the hybrid FTS + dense search with RRF.
   9. Freeze the development / held-out test split at the job-cluster level.
4. **Files and outputs.** prompt files v1 in `prompts/`; CV parser, extractor, matcher modules and tests; extraction cache; an example report for a synthetic CV; `evals/splits/`; this stage report.
5. **Tests and acceptance criteria.**
   - One CV and one pasted JD produce a structured report whose quotes exist in the CV.
   - The 8 development cases pass the manual check.
   - Cache keys include schema, prompt, model, preprocessing, and guideline versions.
   - The extraction status (done / failed) is known for all 428 target jobs.
   - The test split is locked before checkpoint 10 starts.
6. **Evidence to keep.** example report; manual check sheet for the 8 cases; extraction success count; ledger totals; commit links.
7. **Estimate and dependencies.** About 1.5 working days. LLM cost: about US$0.25-0.50 for the batch extraction plus small test runs. Depends on: OpenRouter key in `.env` by the evening of 30 Sep (for extraction and the dense baseline).
8. **Fallback.** If the OpenAI embedding fails on the Indonesian-CV cases, use the local `multilingual-e5-small`. If extraction fails for some jobs, mark them "could not be analyzed" and continue. If extraction quality is poor, keep it for prompt v2 in checkpoint 10 instead of blocking.
9. **Status and next step.** PLANNED / NOT RUN. Next: CP2.3 (checkpoint 10): choose the stage-1 method, K, prompt, and model on the development set.

### CP2.3: System Tuning (checkpoint 10)

Template name: Hyperparameter Tuning · Official: 30 Sep 2026 · Planned work: 2 Oct 2026 · Report: [CP2_03_System_Tuning.md](checkpoint_2/CP2_03_System_Tuning.md)

JobFit version: Tuning means choosing system settings with measurements: stage-1 search method, K, prompt version, LLM model, and the PARTIAL weight.

1. **Goal.** Choose the configuration with measurements on the development set, not by changing settings without a metric.
2. **Inputs and prerequisites.**
   - Checkpoint 9 outputs
   - Development labels reviewed by Dion
   - Locked test split (not used here)
3. **Steps.**
   1. Compare the stage-1 methods (B0, B1, B2, hybrid RRF) with Recall@K on the development pool.
   2. Choose K for stage 2 from 10, 20, 30 by recall, latency, and cost.
   3. Compare extraction prompt v1 and v2.
   4. LLM comparison round 1 (D-029) on about 30 development cases: `deepseek-flash`, GPT-6 Luna, Gemini 3.5 Flash-Lite, Claude Haiku 4.5, all through OpenRouter, with GPT-6 Sol on at most 10 hard cases as the quality reference. Choose with the fixed selection rule. Round 2 only if the rule asks for it.
   5. Audit the PARTIAL weight (0.5) against the relevance labels.
   6. Build the recommendation list end to end: filters, filter status, UNKNOWN option, ordering rules, statuses for not analyzed and failed jobs.
   7. Keep labeling the test set (Dion).
4. **Files and outputs.** experiment table in docs/experiments.md with config snapshots; quality vs latency vs cost table; working recommendation list (script or endpoint); this stage report.
5. **Tests and acceptance criteria.**
   - Every change has a before/after on the development set, and the keep/remove decision is written.
   - The test set is not used for tuning.
   - Spend stays within the budget guard.
   - The chosen stage-1 method, K, prompt, and model are recorded in docs/decisions.md, with the D-029 rule applied as written.
6. **Evidence to keep.** docs/experiments.md entries; config snapshots; ledger totals.
7. **Estimate and dependencies.** About 1 working day. LLM cost: under US$2 for round 1 and the prompt comparison. Depends on: Development labels reviewed; checkpoint 9 pipeline working.
8. **Fallback.** If time is short, cut the LLM comparison to 15 cases and test only K = 10 and 20. If a comparison is not complete, record the choice as provisional, not proven.
9. **Status and next step.** PLANNED / NOT RUN. Next: CP2.4 (checkpoint 11): run the chosen configuration on the held-out test set.

### CP2.4: Evaluation Metrics (checkpoint 11)

Template name: Modeling + Evaluation Metrics · Official: 1 Oct 2026 · Planned work: 3 Oct 2026 · Report: [CP2_04_Evaluation_Metrics.md](checkpoint_2/CP2_04_Evaluation_Metrics.md)

JobFit version: The chosen configuration is measured on the held-out test set with the metrics of System Design v1.3 section 14.

1. **Goal.** Measure the chosen configuration on the held-out test set and report the metrics in the priority order of System Design v1.3 section 14.
2. **Inputs and prerequisites.**
   - Configuration chosen in checkpoint 10
   - Test labels reviewed by Dion (gold)
   - Evaluation scripts
3. **Steps.**
   1. NDCG@10 and P@5 of the recommendation list, stage-1 order vs match-% order.
   2. Evidence Macro-F1, precision and recall per class, confusion matrix, share of assessed units.
   3. Extraction precision, recall, F1, and schema validity.
   4. Filter recall and stage-1 Recall@K.
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
7. **Estimate and dependencies.** About half a day, on 3 Oct together with checkpoints 12 and 13. LLM cost: under US$1. Depends on: Test labels complete and reviewed. This is the most important dependency of CP2.
8. **Fallback.** If the test labels are not complete, report on the reviewed subset with its size and say so. Provisional labels are never used as gold.
9. **Status and next step.** PLANNED / NOT RUN. Next: CP2.5 (checkpoint 12): turn the results into clear charts.

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
9. **Status and next step.** PLANNED / NOT RUN. Next: CP2.6 (checkpoint 13): error analysis and freezing the v1 architecture.

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
9. **Status and next step.** PLANNED / NOT RUN. Next: CP2.7 (checkpoint 14): CP2 presentation and mentoring.

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
   6. Upload the deck to the LMS (Dion).
4. **Files and outputs.** CP2 deck in `04_Checkpoint_2/`; LMS upload proof; mentor feedback summary; this stage report.
5. **Tests and acceptance criteria.**
   - The mentor sees a measurable selection, tuning, and evaluation process.
   - The mentor's feedback is recorded in docs/decisions.md as new entries.
6. **Evidence to keep.** deck file; LMS proof; feedback notes.
7. **Estimate and dependencies.** About half a day for the deck, plus the session. Depends on: Checkpoints 11 to 13.
8. **Fallback.** If a result is not ready, present the method and what is missing, with the reason.
9. **Status and next step.** PLANNED / NOT RUN. Next: CP3.1 (checkpoint 15): FastAPI service.

### CP3.1: API Deployment with FastAPI (checkpoint 15)

Template name: Deployment API menggunakan Flask/FastAPI · Official: 5 Oct 2026 · Planned work: 5 Oct 2026 · Report: [CP3_01_FastAPI_Service.md](checkpoint_3/CP3_01_FastAPI_Service.md)

JobFit version: FastAPI (Flask is not used).

1. **Goal.** Make the business logic callable through a consistent, tested API.
2. **Inputs and prerequisites.**
   - Modules frozen in checkpoint 13
   - Mentor feedback from checkpoint 14
3. **Steps.**
   1. Endpoints: `/health`, `/cv/parse`, `/recommendations`, `/jobs/{job_id}`, `/jobs/paste`, `/analyze`, `/tailor` (minimal), `/market/query` (minimal), `DELETE /session`, `/feedback`.
   2. Request and response schemas.
   3. Session storage with a TTL.
   4. Timeouts, error mapping, and the rate/cost guard.
   5. API tests and an OpenAPI check.
4. **Files and outputs.** FastAPI app in `src/`; API tests; OpenAPI screenshot; this stage report.
5. **Tests and acceptance criteria.**
   - The core flow works without Streamlit.
   - Invalid input fails with a clear error.
   - The budget guard is active on every LLM call.
6. **Evidence to keep.** test output; OpenAPI screenshot.
7. **Estimate and dependencies.** About 1 working day. Depends on: Checkpoint 13 decisions.
8. **Fallback.** Build the core endpoints first (`/cv/parse`, `/recommendations`, `/analyze`, `/jobs/paste`); the minimal ones follow later the same day or on 6 Oct.
9. **Status and next step.** PLANNED / NOT RUN. Next: CP3.2 (checkpoint 16): database migrations, CI, and deployment of the database.

### CP3.2: Database Integration and CI/CD (checkpoint 16)

Template name: Integrasi Database & GitHub Actions CI/CD · Official: 6 Oct 2026 · Planned work: 6 Oct 2026 (hosting smoke deploy earlier, on 1-2 Oct) · Report: [CP3_02_Database_and_CICD.md](checkpoint_3/CP3_02_Database_and_CICD.md)

JobFit version: PostgreSQL with pgvector, and GitHub Actions for CI/CD.

1. **Goal.** Make the system reproducible from a fresh clone and deployable.
2. **Inputs and prerequisites.**
   - Checkpoint 15 API
   - Railway account created by Dion (D-023 approved)
3. **Steps.**
   1. Migrations for jobs, job_requirements (versioned cache), embeddings, demo_analysis_cache, feedback.
   2. Idempotent snapshot loading.
   3. GitHub Actions: lint, tests, Docker build, guideline fixtures.
   4. Secrets through environment variables only.
   5. Deploy the database and the API on the chosen host.
   6. Precompute the saved demo results for the synthetic CVs.
4. **Files and outputs.** migration files; CI workflow; Dockerfiles; deployed database and API; this stage report.
5. **Tests and acceptance criteria.**
   - A fresh clone can create the schema and pass the tests without manual database work.
   - No secrets in the repository.
   - CI is green.
6. **Evidence to keep.** CI screenshot; Docker build proof; schema.
7. **Estimate and dependencies.** About 1 working day. Depends on: Railway account; the smoke deploy on 1-2 Oct; Dion's confirmation of the Hobby cost.
8. **Fallback.** If the chosen host is blocked, use the free fallback in System Design v1.3 section 16 and note the limits.
9. **Status and next step.** PLANNED / NOT RUN. Next: CP3.3 (checkpoint 17): Streamlit UI.

### CP3.3: Streamlit UI (checkpoint 17)

Template name: Build Streamlit UI · Official: 7 Oct 2026 · Planned work: 7 Oct 2026 · Report: [CP3_03_Streamlit_UI.md](checkpoint_3/CP3_03_Streamlit_UI.md)

JobFit version: Same as the template.

1. **Goal.** Build a demo that shows the value in under 3 minutes, without moving business logic into the UI.
2. **Inputs and prerequisites.**
   - Deployed API from checkpoint 16
3. **Steps.**
   1. Demo CV or upload, then the parsing summary with the location suggestion.
   2. Optional filters with the UNKNOWN option.
   3. Recommendations with statuses and the text "K candidates from the search were analyzed".
   4. Job detail with evidence per requirement.
   5. Paste JD compare.
   6. Minimal market insight and CV suggestions.
   7. Delete session and feedback.
   8. The "Demo with saved results" label.
4. **Files and outputs.** Streamlit app; screenshots; demo script; this stage report.
5. **Tests and acceptance criteria.**
   - A mentor can understand the value in under 3 minutes.
   - The synthetic demo works.
   - No business logic in the UI.
6. **Evidence to keep.** screenshots; short screen recording.
7. **Estimate and dependencies.** About 1 working day. Depends on: Checkpoint 16 deployment.
8. **Fallback.** Build the core flow first; the minimal features and styling come last.
9. **Status and next step.** PLANNED / NOT RUN. Next: CP3.4 (checkpoint 18): end-to-end testing and feature freeze.

### CP3.4: End-to-End Testing (checkpoint 18)

Template name: Testing End-to-End Application · Official: 8 Oct 2026 · Planned work: 8 Oct 2026 (feature freeze at the end of the day) · Report: [CP3_04_End_to_End_Testing.md](checkpoint_3/CP3_04_End_to_End_Testing.md)

JobFit version: Same as the template, on the deployed app.

1. **Goal.** Test the real user journey and the critical failure paths on the deployed app, then freeze features.
2. **Inputs and prerequisites.**
   - Deployed app from checkpoints 16 and 17
3. **Steps.**
   1. End-to-end run on the deployed app for each synthetic CV.
   2. Provider failure: a clear error or an explicit demo-mode offer.
   3. Prompt-injection fixtures in pasted JDs.
   4. PII check of the logs.
   5. p50/p95 latency and cost per run, live and cached separately.
   6. Record the feature freeze.
4. **Files and outputs.** E2E checklist; security and reliability results; performance snapshot; this stage report.
5. **Tests and acceptance criteria.**
   - The happy path and the critical failure paths pass on the deployed app.
   - No raw CV in the logs.
   - The feature freeze is recorded.
6. **Evidence to keep.** checklist; test outputs; latency and cost table.
7. **Estimate and dependencies.** About 1 working day. Depends on: Checkpoint 17.
8. **Fallback.** If the deployment is unstable, record a backup demo video and fix only critical bugs.
9. **Status and next step.** PLANNED / NOT RUN. Next: CP3.5 (checkpoint 19): final deck and portfolio.

### CP3.5: Final Presentation and Portfolio (checkpoint 19)

Template name: PPT Final Project / Portfolio · Official: 9 Oct 2026 · Planned work: 9 Oct 2026 · Report: [CP3_05_Final_Presentation_and_Portfolio.md](checkpoint_3/CP3_05_Final_Presentation_and_Portfolio.md)

JobFit version: Same as the template.

1. **Goal.** Build the final story from evidence: problem, data, experiments, final system, evaluation, deployment, limitations.
2. **Inputs and prerequisites.**
   - All earlier stage reports
   - Playbook section 12 (presentation story)
3. **Steps.**
   1. Final deck draft.
   2. README update with CP2 and CP3 results.
   3. Demo video (2-4 minutes).
   4. Limitations and what was deliberately not built.
4. **Files and outputs.** final deck draft in `05_Checkpoint_3/`; updated README; demo video; this stage report.
5. **Tests and acceptance criteria.**
   - Every big claim has evidence or a metric.
   - The deck is not full of jargon without a story.
6. **Evidence to keep.** deck file; README commit; video link.
7. **Estimate and dependencies.** About 1 working day. Depends on: Checkpoint 18 results.
8. **Fallback.** Use screenshots from checkpoint 18 if a live recording fails.
9. **Status and next step.** PLANNED / NOT RUN. Next: CP3.6 (checkpoint 20): rehearsal and final fixes.

### CP3.6: Finalization and Rehearsal (checkpoint 20)

Template name: Finalisasi Portfolio & Rehearsal Presentation · Official: 10 Oct 2026 · Planned work: 10 Oct 2026 · Report: [CP3_06_Finalization_and_Rehearsal.md](checkpoint_3/CP3_06_Finalization_and_Rehearsal.md)

JobFit version: Same as the template.

1. **Goal.** Reduce the risk of the demo or the presentation failing.
2. **Inputs and prerequisites.**
   - Checkpoint 19 outputs
3. **Steps.**
   1. Full regression run.
   2. Rehearse with timing; prepare backup screenshots and video.
   3. Proofread the README and the documents.
   4. Release candidate tag (Dion runs git).
   5. Upload the deck to the LMS (Dion).
4. **Files and outputs.** final deck; release candidate; rehearsal notes; this stage report.
5. **Tests and acceptance criteria.**
   - No new features.
   - The live app, the backup demo, and the metrics are consistent.
6. **Evidence to keep.** regression output; LMS proof; tag link.
7. **Estimate and dependencies.** About half a day plus rehearsal. Depends on: Checkpoint 19.
8. **Fallback.** If a bug appears, fix only if it is critical; otherwise note it as a known issue.
9. **Status and next step.** PLANNED / NOT RUN. Next: CP3.7 (checkpoint 21): final presentation and submission.

### CP3.7: Final Presentation and Submission (checkpoint 21)

Template name: Final Project Presentation + Pemberian Tugas Portofolio · Official: 11 Oct 2026 · Planned work: 11 Oct 2026 · Report: [CP3_07_Final_Presentation_and_Submission.md](checkpoint_3/CP3_07_Final_Presentation_and_Submission.md)

JobFit version: Same as the template.

1. **Goal.** Present the value, the process, and the trade-offs, and submit the project and portfolio links.
2. **Inputs and prerequisites.**
   - Final deck, live app, backup video
3. **Steps.**
   1. Present for 15-20 minutes, following the mentor's direction.
   2. Live demo, with the saved-results demo as the safe option.
   3. Explain actual results and limitations.
   4. Submit the links (project, demo, deck, portfolio) as the mentor asks.
   5. Write the mentor's final feedback and a short retrospective.
4. **Files and outputs.** submission proof; final feedback notes; retrospective draft; this stage report.
5. **Tests and acceptance criteria.**
   - Can answer why, alternatives, trade-offs, metrics, and failures for the main components.
6. **Evidence to keep.** submission proof; links.
7. **Estimate and dependencies.** The presentation day. Depends on: Checkpoint 20.
8. **Fallback.** Use the backup video if the live demo fails.
9. **Status and next step.** PLANNED / NOT RUN. Next: Project done; possible next-version work is listed in docs/decisions.md.
---

## 9. After each stage

1. Set the stage status and the actual date in section 2 of this plan and in the stage report.
2. Fill the report's results, interpretation, limitations, and decisions with real outcomes. Link to the [experiment log](experiments.md) instead of copying numbers.
3. Add any new decision to the [decision log](decisions.md).
4. Dion commits and pushes (Claude never runs git), then puts the link to the stage report in the "Real" column of the Timeline file as proof of work.
