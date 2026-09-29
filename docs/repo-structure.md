# Repository Structure

Created on 29 September 2026 for CP2 and CP3. Every file below starts as a placeholder (a docstring or comment that states its purpose and planned stage) and is filled in the stage shown. Data files such as the gold labels and splits start empty. On 29 September 2026 the CP1 modules moved from `src/jobs/` and `src/viz/` into the application package as `src/jobfit/jobs/` and `src/jobfit/viz/`, so all code lives in one package (only the import paths changed, not the logic). The other CP1 parts (`notebooks/`, `data/raw|interim|processed|research/`, `evidence/`, `reports/figures/cp1/`, and the CP1 scripts and tests) are unchanged.

Stage codes: CP2.1 to CP2.7 are bootcamp checkpoints 8 to 14; CP3.1 to CP3.7 are checkpoints 15 to 21. See the [master plan](master-plan.md).

Why the layout looks like this:

- `src/jobfit/` holds all business logic. The API (`src/jobfit/api/`) and the UI (`ui/`) only call it, so the UI never contains business logic (Playbook checkpoint 17).
- `prompts/` are versioned files, not strings inside code (Canonical section 9).
- `evals/` keeps the guideline, fixtures, gold labels, and splits together, so the prompt, the code, and the labels use the same rules (System Design v1.3 section 15).
- `.github/workflows/` has only a `.gitkeep` for now. An empty workflow file would show as a failed workflow on GitHub; `ci.yml` is written in CP3.2.
- Secrets live only in `.env`, which git ignores (D-028).

## Root configuration

| Path | Purpose | Filled in |
| --- | --- | --- |
| `.env.example` | Names of the environment variables (no values). Copy to `.env` and fill it yourself | CP2.1 |
| `.dockerignore` | Files Docker must not copy into images (for example `env-job-fit/`, `.env`, raw data) | CP3.2 |
| `docker-compose.yml` | Local services: PostgreSQL with pgvector first; API and UI later | CP2.1 |
| `Dockerfile.api` | Image for the FastAPI service | CP3.2 |
| `Dockerfile.ui` | Image for the Streamlit UI | CP3.2 |
| `requirements.txt` | Runtime dependencies of the application (the research notebook keeps `requirements-research.txt`) | CP2.1 |
| `requirements-dev.txt` | Test and lint dependencies | CP2.1 |
| `pyproject.toml` | Package metadata (`jobfit`, src layout) and pytest settings (test path `tests/`, import paths `src/` and `.`) | CP2.1 |
| `LICENSE` | MIT license for the code; data and third-party content are excluded (see the README) | CP2.1 |
| `config/models_v1.yaml` | OpenRouter model ids and prices used by the budget guard; a new model must be added here and in `docs/experiments.md` first | CP2.1 |
| `alembic.ini` | Database migration settings | CP3.2 |
| `.github/workflows/.gitkeep` | Keeps the folder; `ci.yml` is added in CP3.2 (an empty workflow file would fail on GitHub) | CP3.2 |

## Application package `src/jobfit/`

| Path | Purpose | Filled in |
| --- | --- | --- |
| `src/jobfit/__init__.py` | Application package | CP2.1 |
| `src/jobfit/jobs/` | CP1 job-corpus rules: cleaning, corpus build and dedup, skills, transforms, research helpers. Reused by the application pipeline | CP1 (moved 29 Sep) |
| `src/jobfit/viz/style.py` | Shared chart style for all figures | CP1 (moved 29 Sep) |
| `src/jobfit/config.py` | Settings from environment variables; version constants (schema, prompt, guideline, preprocessing) | CP2.1 |
| `src/jobfit/schemas/__init__.py` | Pydantic schemas | CP2.1 |
| `src/jobfit/schemas/requirements.py` | JD requirement units: importance, alternative groups, qualified units | CP2.1 |
| `src/jobfit/schemas/cv.py` | CV evidence units and the parsing summary | CP2.1 |
| `src/jobfit/schemas/analysis.py` | Evidence labels, check status, constraint states, score, and the match report | CP2.1 |
| `src/jobfit/schemas/api.py` | Request and response models of the API | CP3.1 |
| `src/jobfit/llm/__init__.py` | LLM access | CP2.1 |
| `src/jobfit/llm/client.py` | One interface for all LLM providers (timeouts, retries, JSON validation, repair) | CP2.2 |
| `src/jobfit/llm/pricing.py` | Price table per model, used for cost estimates | CP2.1 |
| `src/jobfit/llm/ledger.py` | Usage ledger: one line per call, never CV or JD text (D-019) | CP2.1 |
| `src/jobfit/llm/budget.py` | Budget guard: estimate before a call or batch, hard stop from `.env` (D-031) | CP2.1 |
| `src/jobfit/cv/__init__.py` | CV processing | CP2.2 |
| `src/jobfit/cv/text_extract.py` | Text from PDF (PyMuPDF), DOCX (python-docx), or plain text | CP2.2 |
| `src/jobfit/cv/parser.py` | LLM parsing into evidence units and the parsing summary | CP2.2 |
| `src/jobfit/extraction/__init__.py` | JD extraction | CP2.2 |
| `src/jobfit/extraction/jd_extractor.py` | LLM extraction of requirement units into the schema | CP2.2 |
| `src/jobfit/extraction/cache.py` | Versioned extraction cache (content hash + versions) | CP2.2 |
| `src/jobfit/extraction/paste_jd.py` | Paste JD path: cleaning, quality signals, preview | CP2.2 |
| `src/jobfit/search/__init__.py` | Stage-1 candidate search | CP2.1 |
| `src/jobfit/search/filters.py` | Optional filters, filter status, UNKNOWN option | CP2.3 |
| `src/jobfit/search/keyword.py` | Baseline 0: keyword and skill overlap | CP2.1 |
| `src/jobfit/search/fts.py` | Baseline 1: PostgreSQL full-text search | CP2.1 |
| `src/jobfit/search/embeddings.py` | Embedding calls (OpenAI `text-embedding-3-small`, D-020) with truncation flags | CP2.2 |
| `src/jobfit/search/dense.py` | Baseline 2: dense search with pgvector | CP2.2 |
| `src/jobfit/search/hybrid.py` | Hybrid FTS + dense with RRF | CP2.2 |
| `src/jobfit/search/candidates.py` | Builds the CV query and returns the top K candidates | CP2.3 |
| `src/jobfit/matching/__init__.py` | Stage-2 evidence matching | CP2.2 |
| `src/jobfit/matching/evidence_matcher.py` | LLM matching of requirement units against CV evidence units | CP2.2 |
| `src/jobfit/matching/quote_check.py` | Checks that every quoted CV text exists word for word in the CV | CP2.2 |
| `src/jobfit/matching/constraints.py` | Constraint states: experience, location, work authorization | CP2.2 |
| `src/jobfit/scoring/__init__.py` | Deterministic scoring | CP2.1 |
| `src/jobfit/scoring/score.py` | Match %, denominator, score status (final, provisional, on hold, no score) | CP2.1 |
| `src/jobfit/scoring/ranking.py` | Ordering: no explicit conflict first, then match %, stable tie-break | CP2.1 |
| `src/jobfit/recommend/__init__.py` | Recommendation flow | CP2.3 |
| `src/jobfit/recommend/pipeline.py` | Filters, stage 1, stage 2, grouping, statuses for not analyzed and failed jobs | CP2.3 |
| `src/jobfit/support/__init__.py` | Minimal supporting features | CP3.1 |
| `src/jobfit/support/cv_suggestions.py` | Evidence-based CV suggestions with the claim guard | CP3.1 |
| `src/jobfit/support/market_insight.py` | SQL skill counts and a short cited explanation | CP3.1 |
| `src/jobfit/session/__init__.py` | Session data | CP3.1 |
| `src/jobfit/session/store.py` | Session storage with a TTL and delete-session | CP3.1 |
| `src/jobfit/db/__init__.py` | Database access | CP2.1 |
| `src/jobfit/db/models.py` | Tables: jobs, job_requirements, embeddings, demo_analysis_cache, feedback | CP2.1 |
| `src/jobfit/db/session.py` | Database connection | CP2.1 |
| `src/jobfit/db/load_snapshot.py` | Loads the CP1 snapshot into PostgreSQL, idempotent | CP2.1 |
| `src/jobfit/eval/__init__.py` | Evaluation code | CP2.1 |
| `src/jobfit/eval/metrics.py` | NDCG@10, P@5, Recall@K, filter recall, Macro-F1, extraction F1, safety checks | CP2.1 |
| `src/jobfit/eval/run_eval.py` | Runs an evaluation on a split and writes results with versions and git SHA | CP2.4 |
| `src/jobfit/api/__init__.py` | FastAPI service | CP3.1 |
| `src/jobfit/api/main.py` | FastAPI app, middleware, error mapping, rate and cost guard | CP3.1 |
| `src/jobfit/api/routes_cv.py` | `/cv/parse` | CP3.1 |
| `src/jobfit/api/routes_recommend.py` | `/recommendations`, `/jobs/{job_id}` | CP3.1 |
| `src/jobfit/api/routes_jobs.py` | `/jobs/paste`, `/analyze` | CP3.1 |
| `src/jobfit/api/routes_support.py` | `/tailor`, `/market/query` | CP3.1 |
| `src/jobfit/api/routes_session.py` | `DELETE /session`, `/feedback`, `/health` | CP3.1 |

## Streamlit UI `ui/`

| Path | Purpose | Filled in |
| --- | --- | --- |
| `ui/streamlit_app.py` | Streamlit entry point; calls the API only | CP3.3 |
| `ui/api_client.py` | Small HTTP client for the API | CP3.3 |
| `ui/components.py` | Job card, constraint line, evidence table, honest labels | CP3.3 |
| `ui/pages/.gitkeep` | Keeps the folder for extra Streamlit pages | CP3.3 |

## Database migrations `migrations/`

| Path | Purpose | Filled in |
| --- | --- | --- |
| `migrations/env.py` | Alembic environment | CP3.2 |
| `migrations/versions/.gitkeep` | Keeps the folder for migration files | CP3.2 |

## Prompts `prompts/`

| Path | Purpose | Filled in |
| --- | --- | --- |
| `prompts/jd_extraction_v1.md` | Prompt v1 for JD requirement extraction | CP2.2 |
| `prompts/cv_parsing_v1.md` | Prompt v1 for CV evidence units | CP2.2 |
| `prompts/evidence_matching_v1.md` | Prompt v1 for evidence matching | CP2.2 |
| `prompts/cv_suggestions_v1.md` | Prompt v1 for minimal CV suggestions | CP3.1 |
| `prompts/market_insight_v1.md` | Prompt v1 for the short market explanation | CP3.1 |

## Evaluation data `evals/`

| Path | Purpose | Filled in |
| --- | --- | --- |
| `evals/annotation_guideline_v1.md` | Annotation guideline (v0.1 first, v1 after the pilot) | CP2.1 |
| `evals/fixtures/dev_01_clear_match.json` | Development case 1: clear match | CP2.1 |
| `evals/fixtures/dev_02_experience_too_short.json` | Development case 2: experience too short | CP2.1 |
| `evals/fixtures/dev_03_duration_unknown.json` | Development case 3: duration not written | CP2.1 |
| `evals/fixtures/dev_04_or_alternative_group.json` | Development case 4: "or" alternative group | CP2.1 |
| `evals/fixtures/dev_05_repeated_requirement.json` | Development case 5: repeated requirement | CP2.1 |
| `evals/fixtures/dev_06_ambiguous_importance.json` | Development case 6: required or preferred is unclear | CP2.1 |
| `evals/fixtures/dev_07_no_assessable_requirement.json` | Development case 7: no requirement can be assessed | CP2.1 |
| `evals/fixtures/dev_08_parsing_failure.json` | Development case 8: parsing failure | CP2.1 |
| `evals/pilot/pilot_sample.csv` | Items chosen for the labeling pilot | CP2.1 |
| `evals/pilot/pilot_labels.csv` | Pilot labels (provisional until reviewed) | CP2.1 |
| `evals/pilot/pilot_timing.csv` | Time per item, used to set gold sizes | CP2.1 |
| `evals/gold/extraction_gold.jsonl` | Requirement extraction labels | CP2.2 |
| `evals/gold/evidence_gold.jsonl` | Requirement-evidence labels (MATCH, PARTIAL, NO_MATCH) | CP2.2 |
| `evals/gold/relevance_gold.csv` | Relevance 0-3 per CV profile and job | CP2.2 |
| `evals/splits/dev_job_ids.txt` | Development jobs (cluster level) | CP2.2 |
| `evals/splits/test_job_ids.txt` | Held-out test jobs, locked before CP2.3 | CP2.2 |
| `evals/results/.gitkeep` | Evaluation outputs | CP2.3 |

## Synthetic CVs `data/synthetic_cvs/`

| Path | Purpose | Filled in |
| --- | --- | --- |
| `data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md` | Synthetic CV 1: fresh graduate, data science, in Indonesian | CP2.1 |
| `data/synthetic_cvs/cv_02_career_switcher_ai_engineer_en.md` | Synthetic CV 2: career switcher to AI engineering, in English | CP2.1 |
| `data/synthetic_cvs/cv_03_junior_ml_engineer_1yr_en.md` | Synthetic CV 3: junior ML engineer with about 1 year, in English | CP2.1 |

## Scripts `scripts/` (new files)

| Path | Purpose | Filled in |
| --- | --- | --- |
| `scripts/load_snapshot_to_db.py` | Loads the snapshot into the local database | CP2.1 |
| `scripts/run_batch_extraction.py` | Batch JD extraction with a cost estimate first | CP2.2 |
| `scripts/build_embeddings.py` | Embeddings for jobs, requirement units, and CV evidence | CP2.2 |
| `scripts/run_experiment.py` | Runs one experiment configuration and writes a draft entry for `docs/experiments.md` | CP2.3 |
| `scripts/run_evaluation.py` | Runs the evaluation on a split | CP2.4 |
| `scripts/make_eval_figures.py` | Charts for CP2.5 | CP2.5 |
| `scripts/precompute_demo.py` | Saved demo results for the synthetic CVs (D-022) | CP3.2 |
| `scripts/usage_report.py` | Summary of the usage ledger | CP2.1 |

## Tests `tests/` (new files)

| Path | Purpose | Filled in |
| --- | --- | --- |
| `tests/test_schemas.py` | Schema validation | CP2.1 |
| `tests/test_scoring.py` | Score and score status against the 8 development fixtures | CP2.1 |
| `tests/test_ranking.py` | Ordering and tie-break rules | CP2.1 |
| `tests/test_budget_guard.py` | Budget guard and ledger (no CV text written) | CP2.1 |
| `tests/test_quote_check.py` | Quote validity | CP2.2 |
| `tests/test_constraints.py` | Constraint states | CP2.1 |
| `tests/test_filters.py` | Filter status, UNKNOWN option, no silent relaxation | CP2.3 |
| `tests/test_api.py` | API tests | CP3.1 |
| `tests/test_prompt_injection.py` | Pasted JDs with injected instructions | CP3.4 |
| `tests/e2e/test_e2e_flow.py` | End-to-end flow on the deployed app | CP3.4 |

## Reports and docs

| Path | Purpose | Filled in |
| --- | --- | --- |
| `reports/figures/cp2/.gitkeep` | CP2 evaluation charts | CP2.5 |
| `reports/figures/cp3/.gitkeep` | CP3 charts and screenshots | CP3.4 |
| `reports/usage/.gitkeep` | Usage ledger (`usage_ledger.jsonl`) | CP2.1 |
| `docs/privacy-threat-model.md` | Provider data policies, PII handling, threat model | CP3.4 |
| `docs/decisions.md` | Decision log (D-001 onward) | Ongoing |
| `docs/experiments.md` | Experiment matrix and runs | CP2.1 onward |
| `docs/failures.md` | Failure cases and fixes | CP2.2 onward |
| `docs/master-plan.md` | CP2 and CP3 plan, dates, and budget | CP2.1 |
