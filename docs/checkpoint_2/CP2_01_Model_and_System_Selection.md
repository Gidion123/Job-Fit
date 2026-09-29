# CP2.1: Model and System Selection

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 8. Model Selection (CNN/LSTM/DNN sesuai use case) · official date 28 Sep 2026  
**JobFit version of this checkpoint:** For an LLM and retrieval system, model selection means comparing search methods, LLM candidates, and prompt versions, not training a CNN/LSTM/DNN (D-001). This stage also sets the annotation guideline, the scoring rules, and the experiment matrix.  
**Planned work:** 29-30 Sep 2026 (labeling pilot on the evening of 29 Sep) · **Actual:** started 29 Sep 2026  
**Status:** IN PROGRESS · design basis: System Design v1.3

> This report is updated as the work happens. Only finished items are ticked. Results, scores, mentor feedback, and deployment evidence are added only after the work is actually done, with links to the [experiment log](../experiments.md) instead of copied numbers. The plan for all stages is in the [master plan](../master-plan.md).

## 1. Goal of this stage

Set the rules, the baselines, and the experiment matrix before the full system is built, so every later choice is measured against something.

## 2. Inputs and prerequisites

- System Design v1.3 and docs/decisions.md (D-001 to D-031)
- CP1 processed data: 632 EDA candidates, 428 in the target role families
- `OPENROUTER_API_KEY` in the git-ignored local `.env` that Dion fills himself (D-028, D-030, D-031); never in chat or commits
- Docker Engine running on the Mac (CLI 29.4.3, Compose v5.1.3; `docker run --rm hello-world` succeeded on 29 Sep 2026)

## 3. Planned method

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

## 4. Planned outputs

- `evals/annotation_guideline_v1.md`
- `evals/fixtures/` (8 development cases)
- `evals/pilot/` (pilot labels and timing)
- `data/synthetic_cvs/`
- schema and scoring modules in `src/` with tests in `tests/`
- `docker-compose.yml`
- `docs/experiments.md` (matrix)
- `reports/usage/usage_ledger.jsonl`
- this stage report

## 5. Acceptance criteria

- The guideline v1 exists and has a version number.
- The scoring rules pass the 8 development fixtures (pytest).
- The pilot time per item is recorded and used to propose gold sizes (a new docs/decisions.md entry).
- B0 and B1 run on the pilot pool and their outputs are saved.
- Every experiment candidate has a hypothesis and a metric.
- Every LLM call is written to the usage ledger.

## 6. Evidence to keep

- pytest output
- pilot timing table
- docs/experiments.md matrix
- ledger total for the stage
- commit links (Dion pushes)

## 7. Estimate and dependencies

- **Estimate:** About 1.5 working days. Dion: about 30 minutes to review the synthetic CVs and about 1.5-2 hours for the pilot. LLM cost: under US$0.50.
- **Depends on:** Docker Engine (checked: `hello-world` ran on 29 Sep); OpenRouter key in `.env`; Dion's review of the synthetic CVs before the pilot.

## 8. Fallback if blocked

If Docker does not start, use Postgres.app on the Mac and note it. If the pilot takes too long, cut it to 3 JDs and 1 CV, but still time it. Guideline v1 is finished by the end of 30 Sep in any case.

## 9. Checklist

- [x] Write the annotation guideline v0.1: requirement units, evidence labels, constraint states (compatible / unknown / explicit conflict), relevance 0-3, and label record fields (`ai_suggested`, `status`, `reviewed_by`, `guideline_version`). (v0.1 done; v1 comes after the pilot)
- [x] Define the Pydantic schemas for JD requirement units and CV evidence units, with example outputs.
- [x] Implement the deterministic scoring rules: match %, score status (final / provisional / on hold / no score), constraint states, ordering, and stable tie-break.
- [x] Write the 8 development fixtures from System Design v1.3 section 15 and run them as tests.
- [ ] Draft 2-3 synthetic CVs (at least one in Indonesian); Dion checks that they are realistic. (3 drafts done; waiting for Dion's review)
- [ ] Labeling pilot: a small development sample (for example 5 JDs, about 20 requirement-evidence pairs, 2 CVs x 5 jobs). AI may suggest provisional labels; Dion decides and records the time per item. Then revise the guideline to v1.
- [ ] Start local PostgreSQL with pgvector (Docker Compose) and load the 632 EDA candidates.
- [ ] Run Baseline 0 (keyword/skill overlap with the CP1 v0 skill list) and Baseline 1 (PostgreSQL FTS) on the pilot pool.
- [x] Write the experiment matrix in docs/experiments.md (stage-1 methods, K, LLM candidates, prompt versions), each with a hypothesis and a metric.
- [x] Build the usage ledger and budget guard before the first LLM call.
- [ ] Acceptance: The guideline v1 exists and has a version number.
- [x] Acceptance: The scoring rules pass the 8 development fixtures (pytest).
- [ ] Acceptance: The pilot time per item is recorded and used to propose gold sizes (a new docs/decisions.md entry).
- [ ] Acceptance: B0 and B1 run on the pilot pool and their outputs are saved.
- [x] Acceptance: Every experiment candidate has a hypothesis and a metric.
- [ ] Acceptance: Every LLM call is written to the usage ledger.

## 10. Results

Progress as of 29 Sep 2026. The pilot, the database load, and the baselines have not run yet.

### 10.1 Done

| Item | Where | Status |
| --- | --- | --- |
| Annotation guideline v0.1 (parts A to E, open questions Q1 to Q3) | `evals/annotation_guideline_v1.md` | Draft, to become v1 after the pilot |
| 3 synthetic CVs: fresh graduate data science (Indonesian), career switcher to AI engineer (English), junior ML engineer with 1 year (English) | `data/synthetic_cvs/` | Drafts, waiting for Dion's review |
| Pilot workbook (5 JDs, 2 CVs, sheets for extraction, evidence, relevance, timing, questions) and pilot sample list | `evals/pilot/` | Ready, not labeled yet |
| Pydantic schemas: requirement units (simple, alternative group, qualified), CV profile, per-unit assessment, constraint result, score result, job analysis | `src/jobfit/schemas/` | Done |
| Score v0 and score status (final / provisional / on hold / no score), duplicate merge, alternative-group table | `src/jobfit/scoring/score.py` | Done |
| Ordering (no conflict, then conflict block, then "could not be fully analyzed"; ties keep stage-1 order) | `src/jobfit/scoring/ranking.py` | Done |
| Constraint states for experience (overlap counted once, "present" uses the analysis date), location, work authorization | `src/jobfit/matching/constraints.py` | Done |
| 8 development fixtures (hand-written, synthetic) | `evals/fixtures/dev_01` to `dev_08` | Done |
| OpenRouter client with budget check before each call, usage ledger without prompt text, model registry | `src/jobfit/llm/`, `config/models_v1.yaml` | Done, not called yet (no key used) |
| Local database definition (pgvector) | `docker-compose.yml` | Written, not started yet |
| Repository cleanup: project logs moved to `docs/`, CP1 modules moved into `src/jobfit/`, `pyproject.toml`, MIT license for the code, placeholder files labeled with their planned stage | whole repository | Done |
| OpenRouter only, budget guard set to the available credit (US$9, hard stop US$8.50; balance US$9.22) | [D-031](../decisions.md) | Done |
| Experiment matrix M01 to M12 | [experiment log](../experiments.md) | Done |

### 10.2 Test run

`python3 -m pytest -q` on 29 Sep 2026 (Cowork Linux VM, Python 3.10.12): **73 passed**. Of these, 49 are new CP2.1 tests: `test_scoring.py` (8 fixtures for score and for the experience constraint, plus the alternative-group table, duplicate merge, on-hold cases, overlapping experience), `test_constraints.py`, `test_ranking.py`, `test_schemas.py`, `test_budget_guard.py`. The other 24 are the CP1 tests. The same run still needs to be repeated on Dion's Mac inside `env-job-fit`.

Fixture results (expected values were written by hand from System Design v1.3 before the code was run):

| Fixture | Expected score | Status | Experience constraint |
| --- | --- | --- | --- |
| dev_01 clear match | 87.5% (3.5 of 4) | final | compatible |
| dev_02 experience too short | 83.33% | final | explicit conflict |
| dev_03 duration unknown | 75% | final | unknown |
| dev_04 OR alternative group | 50% | final | unknown |
| dev_05 repeated requirement | 66.67% (SQL counted once) | final | unknown |
| dev_06 ambiguous importance | 83.33% | provisional | unknown |
| dev_07 no assessable requirement | none | no score | unknown |
| dev_08 parsing failure | none | on hold | unknown |

### 10.3 Not done yet

Guideline v1, Dion's review of the synthetic CVs, the labeling pilot and its timing, the gold-size decision, the database load, B0 and B1, and any LLM call (so the usage ledger is still empty).

## 11. Interpretation and limitations

- The fixtures only prove that the code follows the written rules. They do not prove the rules are good. That is tested later with labels (M10, M11 in docs/experiments.md).
- The fixtures are small and hand-written by the same person who wrote the rules, so they can share the same blind spots. The pilot is the first real check.
- Two rules were not stated in System Design v1.3 and were chosen for v0: a `needs_clarification` unit that has a label still counts in the score, and a required unit with no assessment at all puts the score on hold. Both are written in the code docstrings and will be confirmed after the pilot.
- Model ids and prices in `config/models_v1.yaml` were taken from the OpenRouter pages on 29 Sep 2026. Two DeepSeek ids still need to be confirmed before CP2.3 because OpenRouter lists several versions.

## 12. Decisions from this stage

None yet. Decisions are recorded in the [decision log](../decisions.md) when they are made.

## 13. Next step

CP2.2 (checkpoint 9): CV parser, extraction prompt v1, evidence matcher, and the 1 CV + 1 JD report.
