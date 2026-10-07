# CP2.1: Model and System Selection

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 8. Model Selection (CNN/LSTM/DNN sesuai use case) · official date 28 Sep 2026  
**JobFit version of this checkpoint:** JobFit does not train a CNN, LSTM, or DNN (D-001). For an LLM and retrieval system, model selection means fixing the rules, the labeled data, the baselines, the model shortlist, and the selection rule before any model is compared.  
**Planned work:** 29 to 30 Sep 2026 · **Actual:** 29 Sep to 1 Oct 2026  
**Status:** DONE · two items carried over (section 11) · design basis: System Design v1.3

> **Final reconciled status (7 October 2026):** DONE; both carry-overs are resolved. D-043 was superseded by D-045 (approved 1 Oct) and D-044 was approved with option A (1 Oct) and applied in CP2.3 (Qwen selected by its Recall@20 rule). The test labels in section 11 were made after the D-087 freeze under D-053/D-088 (CP2.4). The sections below are the report as closed on 1 October; their "pending" and "empty ledger" statements describe that date (the ledger is US$10.53 on 7 October). Acceptance evidence is checked in the [CP2 closeout audit](CP2_Closeout_Audit_20261007.md). Next stage: [CP2.2](CP2_02_Modeling_Pipeline.md).

## Summary

- The rules of the system are now written and tested: annotation guideline v1.2, Pydantic schemas, score v1, constraint states, and ordering. 80 tests, including the 8 development fixtures.
- The labeling pilot is finished and approved by Dion: 71 requirement units from 4 JDs, 34 evidence labels, and 10 relevance labels. They are exported as the development split in `evals/gold/`.
- The pilot raised 21 rule questions. Dion decided them in D-032 to D-042. The biggest change: soft skills and location are shown separately and are not part of the match %.
- PostgreSQL with pgvector runs in Docker with the 632 jobs. Two baselines (keyword overlap and full-text search) ran and disagree completely on the top 10 for every CV.
- The LLM shortlist, the selection rule, the OpenRouter gateway, and the budget guard are ready. No paid API call was made in this stage (spend US$0).

## 1. Goal

Set the rules, the labels, the baselines, and the experiment matrix before the full system is built, so every later choice can be measured against something.

## 2. Inputs

| Input | Detail |
| --- | --- |
| Design | System Design v1.3, decisions D-001 to D-031 |
| Job data | Snapshot `CP1_20260926`: 632 EDA candidates, 428 in the four target role families |
| Synthetic CVs | CV1 Rina (fresh graduate, data science, Indonesian), CV2 Bima (career switcher to AI engineering, English), CV3 Dewi (junior ML engineer, about one year, English). No real CV is used (D-021) |
| Pilot jobs | J1 Jr. Data Scientist, J2 AI Developer, J3 AI Engineer (Indonesian JD), J4 Artificial Intelligence Engineer, J5 AI Engineer (AI Agent & RAG) |
| Accounts and tools | OpenRouter key in a git-ignored `.env` filled by Dion (credit US$9.22, key limit US$8.50); Docker on Dion's Mac |

## 3. What was done

1. **Guideline.** Wrote annotation guideline v0.1 (requirement units, evidence labels, constraint states, relevance 0 to 3), then revised it to v1.0, v1.1, and v1.2 from the pilot decisions.
2. **Schemas.** Defined Pydantic models for requirement units (simple, alternative group, qualified), CV profiles, per-unit assessments, constraints, and the score result.
3. **Scoring rules.** Implemented score v1, score status, constraint states for experience, location, and work authorization, and the list ordering.
4. **Fixtures.** Wrote 8 development cases from System Design v1.3 section 15, with the expected results written by hand before the code ran.
5. **Synthetic CVs.** Drafted three CVs; Dion checked them and kept them unchanged.
6. **Labeling pilot.** Followed the workflow in [annotation-workflow.md](../annotation-workflow.md): a language model drafted labels, a QA check looked for quote and rule errors, and Dion reviewed every row. One JD (J4) was labeled blind by Dion. Rule questions went to the Questions sheet and were decided by Dion.
7. **Database.** Started PostgreSQL 17 with pgvector in Docker (only reachable from the Mac, port 5434) and loaded the 632 jobs with a full-text index.
8. **Baselines.** Ran B0 (share of the job's v0 skills found in the CV) and B1 (PostgreSQL full-text search) for the three CVs over the 428 target jobs.
9. **Experiment matrix.** Wrote plans M01 to M12 in [experiments.md](../experiments.md), each with a hypothesis, a deciding metric, and a cost estimate.
10. **Cost control.** Built the OpenRouter client, the usage ledger (no CV or JD text), and the budget guard that stops a call before the hard stop.

## 4. Outputs

| Output | Location |
| --- | --- |
| Annotation guideline v1.2 (v0.1 kept for provenance) | `evals/annotation_guideline_v1.md` |
| Labeling workflow and roles | `docs/annotation-workflow.md` |
| Pilot workbook (JDs, CVs, extraction, evidence, relevance, timing, questions, QA log) | `evals/pilot/JobFit_Pilot_Labeling_v0.1.xlsx` |
| Pilot audit records (blind snapshot, draft review, cleanup manifest, review corrections) | `evals/pilot/audit/` |
| Development gold labels and split | `evals/gold/`, `evals/splits/dev_job_ids.txt` |
| Schemas, scoring, constraints, ordering | `src/jobfit/schemas/`, `src/jobfit/scoring/`, `src/jobfit/matching/constraints.py` |
| 8 development fixtures | `evals/fixtures/` |
| Database schema and loader; baselines | `src/jobfit/db/`, `src/jobfit/search/keyword.py`, `src/jobfit/search/fts.py`, `docker-compose.yml` |
| OpenRouter client, ledger, budget guard, model registry | `src/jobfit/llm/`, `config/models_v1.yaml` |
| Experiment matrix and two runs | `docs/experiments.md` (EXP-20261001-01, EXP-20261001-02) |
| Run outputs | `evals/results/cp21_baselines.json`, `evals/results/cp21_pilot_scores.json` |

## 5. Acceptance criteria

| Criterion | Result | Evidence |
| --- | --- | --- |
| Guideline v1 exists with a version number | Met: v1.2 (1 Oct 2026) | `evals/annotation_guideline_v1.md`, change log |
| Scoring rules pass the 8 development fixtures | Met: all 8 pass | `tests/test_scoring.py` |
| Pilot time per item recorded and used to propose gold sizes | Met: timing in the workbook; sizes proposed in D-043 (pending approval) | Timing sheet, D-043 |
| B0 and B1 run on the pilot pool and outputs saved | Met | EXP-20261001-01, `evals/results/cp21_baselines.json` |
| Every experiment candidate has a hypothesis and a metric | Met: M01 to M12 (M04b added, pending D-044) | `docs/experiments.md` |
| Every LLM call written to the usage ledger | Met for the code (covered by tests). No real call was made in CP2.1, so the ledger is still empty | `tests/test_budget_guard.py` |

## 6. Results

### 6.1 Rules and code

**Score v1** (System Design v1.3 section 8, changed by D-032 and D-033):

- Match % = (MATCH + 0.5 x PARTIAL) / number of required units.
- Soft skills are counted and shown separately ("soft skills asked: 9, with evidence: 4"). Location and work authorization are constraints, not score units.
- Score status: `final`, `provisional` (a unit of unknown importance or a label that needs clarification), `on_hold` (the CV or JD could not be read, or a required unit has no assessment), `no_score` (no required unit).
- Ordering: jobs without a known conflict first, then a block of jobs with an explicit conflict, then jobs that could not be fully analyzed. Ties keep the stage-1 order.

**Development fixtures** (expected values written by hand before the code ran; all pass):

| Fixture | Score | Status | Experience constraint |
| --- | --- | --- | --- |
| dev_01 clear match | 87.5% (3.5 of 4) | final | compatible |
| dev_02 experience too short | 83.33% | final | explicit conflict |
| dev_03 duration unknown | 75% | final | unknown |
| dev_04 OR alternative group | 50% | final | unknown |
| dev_05 repeated requirement | 66.67% (SQL counted once) | final | unknown |
| dev_06 ambiguous importance | 83.33% | provisional | unknown |
| dev_07 no assessable requirement | none | no score | unknown |
| dev_08 parsing failure | none | on hold | unknown |

**Tests:** 80 tests (24 from CP1, 56 new). `python -m pytest -q` gives 79 passed and 1 skipped; the skipped one is the database test, which runs with `JOBFIT_DB_TESTS=1` and passed on Dion's Docker database on 1 Oct 2026.

### 6.2 Synthetic CVs

Dion checked the three CVs and kept them unchanged, so the pilot did not tune the CVs to the jobs. Each CV has known limits that the labels must respect: in CV1 Git appears only in the skills list; in CV2 three years of marketing analytics is not AI engineering experience and the AWS course has no exam; in CV3 "about one year" is the junior role only. The CVs are cleaner than real CVs, so they cannot show robustness to messy PDF layouts.

### 6.3 Labeling pilot

**Scope and result (all approved by Dion, development data only):**

| Label type | Items | Detail |
| --- | --- | --- |
| A. Requirement units | 71 units from 4 JDs | J1 21, J2 13, J3 16, J4 21. Importance: 56 required, 13 preferred, 2 unknown. Categories: 25 skill/tool, 17 knowledge area, 17 soft skill, 5 experience, 4 education, 2 location, 1 other. 15 alternative groups |
| B. Evidence labels | 34 rows, 2 CV-job pairs | CV1 x J1: 9 MATCH, 5 PARTIAL, 7 NO_MATCH. CV2 x J2: 5 MATCH, 4 PARTIAL, 4 NO_MATCH. 1 row needs clarification |
| C. Relevance 0 to 3 | 10 labels, 2 CVs x 5 jobs | One 3 (CV1 x J1), one 2 (CV2 x J1), seven 1, one 0 (CV1 x J5) |

**Review of the model drafts:**

| Sheet | Model-draft rows | Accepted | Edited | Added by Dion | Acceptance rate |
| --- | --- | --- | --- | --- | --- |
| A (J1 to J3) | 48 | 45 | 3 | 2 | 94% |
| B | 32 | 31 | 1 | 2 | 97% |
| C | 10 | 10 | 0 | 0 | 100% (5 of 10 had been decided in discussion before the review) |

J4 was labeled blind: Dion extracted 13 units without seeing any draft. The QA check then found 8 mechanical fixes and 5 rule questions; after Dion's decisions J4 has 21 units. His original answers are frozen in `evals/pilot/audit/j4_blind_snapshot_20260930.json`, so the agreement between a model draft and the blind labels can be measured in CP2.2 when the extraction prompt runs on J4.

**Time per item (single annotator):**

| Task | Time | Per item |
| --- | --- | --- |
| Blind extraction, J4 | 60 min for 13 units | 4.6 min per unit |
| Review of extraction drafts, J1 to J3 | about 60 min for 50 units | about 1.2 min per unit |
| Review of evidence drafts | about 40 min for 34 rows | about 1.2 min per row |
| Review of relevance drafts | about 24 min for 10 labels | about 2.4 min per label |

Only the blind session has start and end times; the three review times are Dion's totals. Reviewing a draft was about 3.8 times faster than labeling from zero.

**Rule questions:** the pilot produced 21 questions (Q1 to Q21). Dion decided them in D-032 to D-042 (section 9).

### 6.4 Score on the approved labels (EXP-20261001-02)

Score v1 was computed from the approved extraction and evidence labels. This shows what the rules give when extraction and matching are correct; it is not a system output.

| Pair | Relevance label | Score v1 | Soft skills with evidence | Score with soft skills inside |
| --- | --- | --- | --- | --- |
| CV1 x J1 | 3 | 92.86% (provisional) | 4 of 9 | 59.38% |
| CV2 x J2 | 1 | 55.56% (provisional), plus an explicit experience conflict | 0 of 1 | 50.00% |

With soft skills outside the score, the pair labeled 3 and the pair labeled 1 are 37 points apart; with soft skills inside, only 9 points. This supports D-032, but two pairs are not proof. The check is repeated on more pairs in CP2.3 (M10, M11).

### 6.5 Database and baselines (EXP-20261001-01)

632 jobs loaded (428 target, 131 adjacent, 73 non-target), the same as CP1; loading twice gives the same result. No LLM and no embeddings were used.

| CV | B1 matched jobs | B0/B1 top-10 overlap | Rank of the pilot job labeled 3 (J1), B0 / B1 |
| --- | --- | --- | --- |
| CV1 Rina | 373 of 428 | 0 | 14 / 75 |
| CV2 Bima | 392 of 428 | 0 | not labeled 3 |
| CV3 Dewi | 381 of 428 | 0 | not labeled |

- The two baselines share no job in the top 10 for any CV, so the stage-1 method matters (hypothesis H3).
- B0 favors jobs with very short skill lists, where one matching skill gives 1.0. B1 matches almost every job and favors long JDs that repeat terms.
- The only pair labeled 3 is ranked 14 by B0 and 75 by B1. With one such pair, Recall@K cannot be computed yet.

### 6.6 Model selection setup

| Part | Choice | Status |
| --- | --- | --- |
| Gateway | OpenRouter for every LLM and embedding call; `data_collection: deny`, strict JSON schema, Pydantic validation on every output | D-030, D-031 |
| LLM shortlist | Round 1: DeepSeek V4.1 Flash (baseline), GPT-6 Luna, Gemini 3.5 Flash-Lite, Claude Haiku 4.5; GPT-6 Sol as quality reference on at most 10 hard cases; round 2 DeepSeek V4 Pro only if needed | D-029; ids and prices in `config/models_v1.yaml` |
| LLM selection rule (fixed before any result) | Safety gate (no unsupported claim, all quotes valid), then evidence Macro-F1, then extraction F1; a cheaper model wins within 0.03; tie on p95 latency | D-029 |
| Embedding model | `openai/text-embedding-3-small` (1536 dimensions); a second, multilingual candidate is proposed | D-020; D-044 pending |
| Budget | Guard at US$9 with a hard stop at US$8.50; key limit US$8.50; project ceiling US$15. Spent in CP2.1: US$0 | D-019, D-031 |
| Where models are compared | Shortlist and rule in CP2.1 (this stage); measured comparison on development data in CP2.3 (quality, cost per run, latency); one confirmation run on the test set in CP2.4 | D-029, D-044 |

## 7. Interpretation

| Finding | What it means | Decision | Checked next in |
| --- | --- | --- | --- |
| In the first draft, 9 of J1's 14 required units were soft skills, and CVs rarely prove them | Counting soft skills drags almost every score down and hides technical fit | Soft skills shown separately (D-032) | M10, M11 |
| Location sentences were scored like skills | A city in the CV does not prove willingness to commute | Location and work authorization are constraints (D-033) | Constraint labels in the test set |
| The same list was split in different ways | Scores change with the splitting rule | The conjunction decides (D-034, D-039); lists of experience areas are split (D-040) | Extraction F1 in CP2.4 |
| A narrow `cv_target` column gave 0 to 8 of 10 pairs | Relevance did not match how the app searches | Relevance judged in automatic mode (D-037) | Test relevance labels |
| Marketing years were read as AI experience | Duration rules were unclear | Only employment in the same field counts; a complete dated history is an upper bound (D-042) | Constraint code in CP2.2 |
| Reviewing drafts is about 3.8 times faster than blind labeling | The labeling budget is set by review speed | Model drafts plus full review, with a blind sample (D-038); gold sizes from the timing (D-043) | Test labels, 2 to 3 Oct |
| B0 and B1 disagree completely | A keyword method alone is not a safe stage 1 | Dense and hybrid search are tested (H3) | M04, CP2.3 |

## 8. Limitations

- **One annotator.** Every label was reviewed by one person, starting from model drafts. No inter-annotator agreement exists. The blind item (J4) and the edit rate are the only checks on anchoring.
- **High acceptance rates** (94% and 97%) can mean good drafts or a light review. The review times are totals reported after the work, not timed per row.
- **Small development set.** 4 JDs, 2 evidence pairs, and 10 relevance labels are enough to set rules, not to measure accuracy. Seven of ten relevance labels are 1, so the pilot cannot test ranking quality.
- **Synthetic CVs** are cleaner than real ones and were written for this project.
- **Same model family.** The drafting model is from OpenAI, and two LLM candidates are also from OpenAI. The assistant tools used in development include models from OpenAI and Anthropic. The fixed selection rule is applied to every candidate, and this is stated in the evaluation report.
- **The fixtures test the code, not the rules.** They were written by the same person who wrote the rules.
- **Model ids and prices** were checked on 29 Sep 2026. Two DeepSeek ids must be confirmed before CP2.3.

## 9. Decisions from this stage

| ID | Decision | Status |
| --- | --- | --- |
| D-029 | LLM shortlist and fixed selection rule | Approved |
| D-030, D-031 | OpenRouter as the only gateway; budget guard set to the credit actually bought | Approved |
| D-032 | Soft skills shown separately, not in the match % | Approved |
| D-033 | Location and work authorization are constraints | Approved |
| D-034, D-039, D-040 | How a JD list is split into units | Approved |
| D-035 | Skills-list-only evidence is PARTIAL; CV truth and depth not verified | Approved |
| D-036 | CV coach: minimal version after matching, full version later | Approved |
| D-037 | Relevance judged in automatic mode | Approved |
| D-038 | Labeling workflow: model drafts, full review, blind sample | Approved |
| D-041, D-042 | Pilot case decisions and the general rules behind them | Approved |
| D-043 | Gold-set sizes from the pilot timing | Pending approval |
| D-044 | Benchmark protocol and a second embedding candidate | Pending approval |

Full text: [decisions.md](../decisions.md).

## 10. Changes from the plan

- **One day late** (planned 29 to 30 Sep, done 1 Oct). The pilot raised 21 rule questions instead of the expected 3, and each needed a decision before the labels could be approved.
- **J4 was added as a blind item** because J1 to J3 had already been drafted before review, so they could only measure review time.
- **Recall@K for B0 and B1 was not computed.** The pilot has one pair labeled 3, which is not enough. The comparison moves to CP2.3 (development) and CP2.4 (test).
- **No LLM call was made**, so the planned LLM budget of under US$0.50 was not used.

## 11. Carry-over and next step

**Carry-over (does not block the start of CP2.2):**

1. Dion approves D-043 (test-set sizes) and chooses option A or B in D-044.
2. Test labels: about 2 hours of review (1 JD, 1 CV-job pair, 30 relevance labels for 3 CVs x 10 jobs; CV3 only in the test set), locked before any tuning in CP2.3.

**Next: CP2.2 (checkpoint 9):** CV parser, extraction prompt v1, evidence matcher, embeddings and hybrid search, and a full report for one CV and one JD. The first real LLM calls happen there and go through the budget guard.

## 12. Evidence

- Test run: `python -m pytest -q` (79 passed, 1 skipped) and `JOBFIT_DB_TESTS=1 python -m pytest -q` on Dion's machine.
- Runs: [EXP-20261001-01 and EXP-20261001-02](../experiments.md), outputs in `evals/results/`.
- Labels: `evals/gold/` (rebuilt with `python scripts/export_pilot_gold.py`), audit records in `evals/pilot/audit/`.
- Model-draft stage record: [supporting/CP2_01_Pilot_Draft_Review.md](supporting/archive/preparation/CP2_01_Pilot_Draft_Review.md).
- Commits: pushed by Dion.
