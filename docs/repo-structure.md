# Repository Structure

Created on 29 September 2026 for CP2 and CP3. This file retains the original implementation plan; some entries below describe historical placeholders and should be read with the current status note. On 29 September 2026 the CP1 modules moved from `src/jobs/` and `src/viz/` into the application package as `src/jobfit/jobs/` and `src/jobfit/viz/`, so all code lives in one package. The other CP1 parts (`notebooks/`, `data/raw|interim|processed|research/`, `evidence/`, `reports/figures/cp1/`, and the CP1 scripts and tests) are unchanged.

**Current CP2.3 files, 4 October 2026:** [main model comparison](checkpoint_2/CP2_03_Model_Comparison.md), [concise stage report](checkpoint_2/CP2_03_System_Tuning.md), [historical progress log](checkpoint_2/supporting/CP23_Progress_Log.md), [provisional configuration](../config/versions/pipeline_cp23_provisional_20261004.yaml), six [development figures](../reports/figures/cp2/), and the capped development runner `scripts/run_cp23_end_to_end_dev.py`. Original prompt and result paths remain stable to preserve frozen source and config hashes. The version path policy is in [path map](path_map_20261004.md). `evals/staging/` is ignored rather than deleted; it occupied about 14 MB at this check. No test set or real CV belongs in the development runner.

The Part B offline evaluator is `scripts/evaluate_cp23_end_to_end_dev.py`. The synthetic masking quote check is `scripts/check_cp23_masking_quotes.py`, with a [text-free identity and hash receipt](../evals/results/cp23_masking_quote_compatibility_20261004_v1.json). Its tests are `tests/test_cp23_masking_quotes.py`. The optional-filter checks are in `tests/test_filters.py`.

The stopped Part B run is documented in [the English supporting report](checkpoint_2/supporting/CP23_PartB_Development_Run_20261004.md) and versioned extraction, partial-run, evaluation and protection receipts under `evals/results/cp23/end_to_end_dev/`. The four-pair masking runner remains separate and has a quote-transfer preflight in `tests/test_cp23_masking_pairs_preflight.py`; it was not paid-run after the transport failures.

`src/jobfit/recommend/pipeline.py` now assembles already filtered and analyzed results into D-013 display groups. It requires an explicit analysis result, including on-hold status, for each selected candidate. It does not call retrieval or a model. `tests/test_recommendation_groups.py` checks group separation, stable ties, and rejection of missing or out-of-scope inputs.

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
| `alembic.ini` | Alembic settings (raw-SQL revisions; the URL comes only from `DATABASE_URL`) | CP3.2 |
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
| `src/jobfit/recommend/pipeline.py` | Deterministic result grouping from completed filter, retrieval and analysis inputs. API orchestration remains CP3 | CP2.3 |
| `src/jobfit/support/__init__.py` | Minimal supporting features | CP3.1 |
| `src/jobfit/support/cv_suggestions.py` | Evidence-based CV suggestions with the claim guard | CP3.1 |
| `src/jobfit/support/market_insight.py` | SQL skill counts and a short cited explanation | CP3.1 |
| `src/jobfit/session/__init__.py` | Session data | CP3.1 |
| `src/jobfit/session/store.py` | Session storage with a TTL and delete-session | CP3.1 |
| `src/jobfit/db/__init__.py` | Database access | CP2.1 |
| `src/jobfit/db/models.py` | Tables: jobs, job_requirements, embeddings, demo_analysis_cache, feedback | CP2.1 |
| `src/jobfit/db/session.py` | Database connection | CP2.1 |
| `src/jobfit/db/load_snapshot.py` | Loads the CP1 snapshot into PostgreSQL, idempotent | CP2.1 |
| `src/jobfit/db/migrate.py` | Alembic config for one explicit database URL | CP3.2 |
| `src/jobfit/db/catalog.py` | Read-only schema fingerprint and Alembic revision state | CP3.2 |
| `src/jobfit/db/lifecycle.py` | Production retrieval filter and the 60-day hard delete | CP3.2 |
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
| `migrations/env.py` | Alembic environment (explicit URL, psycopg 3, one transaction per command) | CP3.2 |
| `migrations/versions/0001_cp2_baseline.py` | Exact CP2 baseline: immutable copy of `SCHEMA_SQL`; refuses an existing database | CP3.2 |
| `migrations/versions/0002_cp3_production.py` | Additive production schema (lifecycle, dedupe, sources, query hits, sync runs, extraction cache, reservations, quota) | CP3.2 |
| `migrations/catalog/0001.json`, `0002.json` | Pinned schema fingerprints | CP3.2 |
| `migrations/script.py.mako` | Revision template | CP3.2 |

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
| `evals/annotation_guideline_v1.md` | Annotation guideline v1.2 (v0.1 first, v1.0 to v1.2 after the pilot) | CP2.1 |
| `evals/fixtures/dev_01_clear_match.json` | Development case 1: clear match | CP2.1 |
| `evals/fixtures/dev_02_experience_too_short.json` | Development case 2: experience too short | CP2.1 |
| `evals/fixtures/dev_03_duration_unknown.json` | Development case 3: duration not written | CP2.1 |
| `evals/fixtures/dev_04_or_alternative_group.json` | Development case 4: "or" alternative group | CP2.1 |
| `evals/fixtures/dev_05_repeated_requirement.json` | Development case 5: repeated requirement | CP2.1 |
| `evals/fixtures/dev_06_ambiguous_importance.json` | Development case 6: required or preferred is unclear | CP2.1 |
| `evals/fixtures/dev_07_no_assessable_requirement.json` | Development case 7: no requirement can be assessed | CP2.1 |
| `evals/fixtures/dev_08_parsing_failure.json` | Development case 8: parsing failure | CP2.1 |
| `evals/pilot/pilot_sample.csv` | Items chosen for the labeling pilot | CP2.1 |
| `evals/pilot/JobFit_Pilot_Labeling_v0.1.xlsx` | Pilot labeling workbook: JDs, CVs, extraction, evidence, relevance, timing, rule questions, QA log | CP2.1 |
| `evals/pilot/audit/` | Audit records of the pilot: blind-sample snapshot, draft review, cleanup manifest, review corrections (kept unchanged as evidence) | CP2.1 |
| `evals/gold/README.md` | Format and current content of the gold files | CP2.1 |
| `evals/gold/extraction_gold.jsonl` | Requirement extraction labels (development rows exported 1 Oct) | CP2.1 (dev), CP2.3 (test) |
| `evals/gold/evidence_gold.jsonl` | Requirement-evidence labels (MATCH, PARTIAL, NO_MATCH) | CP2.1 (dev), CP2.3 (test) |
| `evals/gold/relevance_gold.csv` | Relevance 0-3 per CV profile and job | CP2.1 (dev), CP2.3 (test) |
| `evals/splits/README.md` | How the splits are made | CP2.1 |
| `evals/splits/dev_job_ids.txt` | Development half of the target jobs (pilot jobs only until the split is written, D-046) | CP2.1, CP2.2 |
| `evals/pools/` | Development and test pools for relevance labeling (D-046) | CP2.2, CP2.3 |
| `evals/labeling/` | Labeling workbooks after the pilot (development and test batches) | CP2.2 onward |
| `evals/silver/` | Unreviewed model drafts, exploration only (D-044, D-045) | CP2.2 onward |
| `evals/splits/test_job_ids.txt` | Held-out test jobs, locked before any tuning in CP2.3 | CP2.2 |
| `evals/results/cp21_baselines.json` | Output of the B0 and B1 baselines (EXP-20261001-01) | CP2.1 |

## Synthetic CVs `data/synthetic_cvs/`

| Path | Purpose | Filled in |
| --- | --- | --- |
| `data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md` | Synthetic CV 1: fresh graduate, data science, in Indonesian | CP2.1 |
| `data/synthetic_cvs/cv_02_career_switcher_ai_engineer_en.md` | Synthetic CV 2: career switcher to AI engineering, in English | CP2.1 |
| `data/synthetic_cvs/cv_03_junior_ml_engineer_1yr_en.md` | Synthetic CV 3: junior ML engineer with about 1 year, in English | CP2.1 |
| `data/synthetic_cvs/cv_04_data_analyst_to_ds_id.md` | Synthetic test-only CV 4: Surabaya data analyst, 24 employment months as of 30 Sep 2026, in Indonesian. Approved content v0.1, test only | T07, CP2.2 |
| `data/synthetic_cvs/cv_05_ml_engineer_3yr_en.md` | Synthetic test-only CV 5: Jakarta ML engineer, 36 employment months across two companies as of 30 Sep 2026, in English. Approved content v0.1, test only | T07, CP2.2 |

## Scripts `scripts/` (new files)

| Path | Purpose | Filled in |
| --- | --- | --- |
| `scripts/load_snapshot_to_db.py` | Loads the snapshot into the local database | CP2.1 |
| `scripts/db_baseline.py` | Verifies an existing CP2 database against Alembic `0001` (read-only) and stamps it only on an exact match | CP3.2 |
| `scripts/run_baselines.py` | Runs B0 (skill overlap) and B1 (FTS) for the synthetic CVs; writes `evals/results/cp21_baselines.json` | CP2.1 |
| `scripts/run_batch_extraction.py` | Batch JD extraction with a cost estimate first | CP2.2 |
| `scripts/build_embeddings.py` | Estimated, guarded, resumable build for 632 job vectors and CV1/CV2 query vectors on both candidate models; development smoke checks | CP2.2 |
| `scripts/run_experiment.py` | Runs one experiment configuration and writes a draft entry for `docs/experiments.md` | CP2.3 |
| `scripts/run_evaluation.py` | Runs the evaluation on a split | CP2.4 |
| `scripts/make_eval_figures.py` | Charts for CP2.5 | CP2.5 |
| `scripts/precompute_demo.py` | Saved demo results for the synthetic CVs (D-022) | CP3.2 |
| `scripts/usage_report.py` | Summary of the usage ledger | CP2.1 |
| `scripts/export_pilot_gold.py` | Exports approved pilot labels to `evals/gold/` (development split) | CP2.1 |

## Tests `tests/` (new files)

| Path | Purpose | Filled in |
| --- | --- | --- |
| `tests/test_schemas.py` | Schema validation | CP2.1 |
| `tests/test_scoring.py` | Score and score status against the 8 development fixtures | CP2.1 |
| `tests/test_ranking.py` | Ordering and tie-break rules | CP2.1 |
| `tests/test_budget_guard.py` | Budget guard and ledger (no CV text written) | CP2.1 |
| `tests/test_quote_check.py` | Quote validity | CP2.2 |
| `tests/test_constraints.py` | Constraint states | CP2.1 |
| `tests/test_baselines.py` | Baselines B0 and B1 (the database test runs only with `JOBFIT_DB_TESTS=1`) | CP2.1 |
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
| `docs/cv-coach-plan.md` | CV coach plan (D-036) | CP3, after matching |
| `docs/annotation-workflow.md` | Labeling process and roles (D-038) | CP2.1 |
| `evals/annotation_tasks/` | Written task prompts for the drafting model (D-038) | CP2.1 onward |
| `evals/annotation_guideline_v0.1.md` | Guideline used in the first pilot draft, kept for provenance (superseded) | CP2.1 |
| `docs/checkpoint_2/supporting/` | Supporting records for CP2 reports | CP2.1 onward |
| `docs/experiments.md` | Experiment matrix and runs | CP2.1 onward |
| `docs/failures.md` | Failure cases and fixes | CP2.2 onward |
| `docs/master-plan.md` | CP2 and CP3 plan, dates, and budget | CP2.1 |

### T03 split implementation (1 October 2026)

`scripts/make_splits.py` builds and verifies the frozen job split. `tests/test_splits.py` checks coverage, duplicate safety, pilot placement, deterministic rebuilding, and transitive duplicate components. The manifest is `evals/splits/split_manifest.json`; the stage evidence is `docs/checkpoint_2/supporting/T03_Job_Split_20261001.md`.

`evals/results/t03_split_verification_20261001.json` records fresh Phase 0 and T03 Part 1 checks after the handoff, including source/output hashes, stratum counts, duplicate validation, actual test results, and project API cost (EXP-20261001-03). It contains metadata only, with no CV/JD text or secrets.

### T07 synthetic test CV drafts (1 October 2026)

`docs/checkpoint_2/supporting/T07_Test_CV_Drafts_20261001.md` records the CV4/CV5 drafts, fixed reference date, chronology and content checks, limited split-test reconciliation, and the human review STOP. Both CV files remain test only; content version 0.1 is approved by Dion. Approval hashes are in `evals/annotation_tasks/T07_approved_cv_manifest_v1.json`. No test labeling or tuning result is claimed.


### CP2.2 embedding implementation (1 October 2026)

- Configuration: `config/retrieval_v1.yaml`, `config/tokenizers_v1.json`, embedding entries in `config/models_v1.yaml`.
- Storage and recovery: `src/jobfit/search/embedding_store.py`, `query_cache.py`, `response_cache.py`; new versioned pgvector table in `src/jobfit/db/models.py`. The legacy table is retained.
- Execution: `scripts/setup_embedding_tokenizers.py`, `scripts/build_embeddings.py`; implemented `embeddings.py`, `dense.py`, and `hybrid.py`; development-scoped FTS.
- Tests: `tests/test_embeddings.py` and `tests/test_embedding_db.py`. Final full suite with database: 123 passed.
- Local ignored operational caches: `reports/tokenizers/`, `reports/embedding_queries/`, `reports/embedding_receipts/`, usage lock files. No CV/JD input text in query/receipt caches.
- Report: `docs/checkpoint_2/supporting/CP22_Embedding_Implementation_20261001.md`; audit: `evals/results/embedding_continuation_audit_20261001.json`. Live build complete: 632 job + 2 query vectors per model, four scoped search checks passed; cache preflight zero pending. Failure history preserved.


### Development pooling and review workbooks (1 October 2026)

- `src/jobfit/search/pools.py`, `scripts/build_dev_pools.py`, `tests/test_dev_pools.py`: deterministic six-method development pools, with a guard against silently dropping mandatory top-five candidates.
- `evals/pools/dev_pool.csv`, `evals/results/t03_dev_pool_20261001.json`: frozen-development-only pool and retrieval provenance.
- `scripts/prepare_development_review.py`, `evals/labeling/drafts/development_review_v1.json`: explicit pending annotation drafts, never gold or evaluation output.
- `evals/labeling/JobFit_Development_Labeling_v0.1.xlsx`: active pilot-format workbook with full A/B/C drafts, 54 JD and 67 pairs. Older development books are preserved in `evals/labeling/archive/pre_combined_20261002/`. D-045 priority review remains unchanged.
- `evals/labeling/sources/development_jds.md`: full source text for reading long JDs without Excel row-height limits.
- `scripts/validate_development_review.py`, `evals/results/development_workbook_qa_20261001.json`: read-only initial draft QA, hashes and counts. Pending-draft assertions intentionally stop applying after human edits.
- Stage evidence: `docs/checkpoint_2/supporting/T03_T04_T05_Development_Review_20261001.md`. No new labels exported; latest database-enabled suite 125 passed.

### Combined development review (2 October 2026)

- `evals/labeling/drafts/development_combined_manifest_v1.json`: source hashes, protected existing rows, requirement fingerprints and review subset.
- `evals/labeling/sources/development_combined_sources.md`: uninterrupted full JD/CV source text.
- `scripts/validate_combined_labeling.py`, `evals/results/development_combined_workbook_qa_20261002.json`: initial preparation QA. Human review can legitimately change draft values afterwards.
- Pool and workbook preparers refuse regeneration when the active review workbook exists.

### Full first development semantic audit (2 October 2026)

- `docs/checkpoint_2/supporting/Development_Labeling_Semantic_Audit_20261002.md`: scope, findings, decision groups, limits, priority review and correction STOP.
- `docs/checkpoint_2/supporting/Development_Labeling_Semantic_Audit_Findings_20261002.md`: detailed source-backed proposals, separated into clear errors, ambiguous cases and source/guideline limitations.
- `evals/results/development_labeling_semantic_audit_20261002.json`: current row values, source quotes, dependencies, snapshot/save reconciliation and 27 read-only mechanical checks. Does not approve or export labels.
- `evals/results/development_labeling_semantic_audit_coverage_20261002.csv`: complete per-JD semantic reading coverage (54 development JDs, 1,069 A / 1,387 B / 67 C).
- Audit snapshots/helpers and intermediate diagnostics stay private under `notes/artifact_work/semantic_audit_20261002/`; no application module or historical QA output was modified.


Pending-label correction evidence (2 October 2026):
- `docs/checkpoint_2/supporting/Development_Labeling_Pending_Corrections_20261002.md`: corrections and deferred decisions.
- `evals/results/development_labeling_pending_corrections_20261002.json`: before/after, dependency checks, protected hashes and saved version.

### CP2.2 upload and evidence backend (2 October 2026)

- Implemented cv/text_extract.py, cv/parser.py, cv/dates.py and additive partial dates in schemas/cv.py.
- Implemented extraction/jd_extractor.py, paste_jd.py, cache.py, matching/evidence_matcher.py, quote_check.py and source-scoped pipeline.py.
- llm/structured.py: safe feedback and one repair; client.py: billed errors, incomplete/wrong-model rejection. config/pipeline_v1.yaml: evaluation date/baseline. Prompts: CV/evidence v1, JD v1.1; old JD v1 retained.
- scripts/build_cv_upload_fixtures.py and evals/fixtures/cp22_uploads/: approved development CV1 PDF fixtures, not held-out CVs.
- scripts/run_cp22_example.py: preflight/live synthetic diagnostics and source-hash-checked parse reuse. Saved synthetic results are evaluation artifacts, not a production CV cache.
- scripts/run_batch_extraction.py: frozen-development-only preflight/cache/resume. reports/extraction_cache/ is ignored public-JD cache; full batch is not run.
- tests/test_cv_upload_pipeline.py and test_cp22_contract.py cover the pipeline. Final database-enabled suite 161 passed.
- docs/checkpoint_2/supporting/CP22_Pipeline_Implementation_20261002.md, CP22_Synthetic_Example_20261002.md, evals/results/cp22_pipeline_verification_20261002.json: actual checks, live failure history, semantic limits and costs. CP2.2 remains IN PROGRESS.

## CP2.2 offline audit additions (2 October 2026)

- `src/jobfit/eval/alignment.py`: explicit proposed unit mappings with split/merge/omission accounting; no automatic semantic equivalence or metrics.
- `src/jobfit/eval/review_export.py`: pure review candidate validation/dependency checks and exclusive temporary staging; no workbook reader or actual gold promotion.
- `scripts/prepare_cp22_alignment_review.py`: no-inference report from saved run 06 and approved development pilot; exclusive output path.
- `tests/test_cp22_audit_regressions.py`, `test_review_export.py`, `test_alignment.py`: fake-client and temporary-data regressions.
- `docs/checkpoint_2/supporting/CP22_Pipeline_Audit_20261002.md` and `CP22_Pilot_Alignment_Review_20261002.md`: implementation findings, complete proposed pilot mapping, limits and next steps.
- `evals/results/cp22_pipeline_audit_20261002.json`, `cp22_pipeline_audit_final_tests_20261002.xml`, `cp22_pilot_alignment_review_20261002.json`, `cp22_pilot_remaining_preflight_20261002.json`: actual offline checks and preflight evidence.

`export_pilot_gold.py` is historical and now stops when the frozen split exists. Never use it to update expanded-development labels. Requirements already include PyMuPDF and python-docx; this continuation adds no dependency.

The intermediate `cp22_pipeline_audit_tests_20261002.xml` (161 passing selected tests) is also preserved; the final XML contains164 after three batch-ceiling cases.


## Controlled probe, evaluation tools and v1.3 runtime (2 October 2026)

- `src/jobfit/llm/probe.py`, `scripts/run_pilot_probe.py`, `tests/test_pilot_probe.py`: persistent aggregate spend, baseline identity and sequential semantic-stop protocol. Operational state under `reports/quality_probe/`; no label approval.
- `src/jobfit/eval/metrics.py`, `run_eval.py`, `scripts/run_evaluation.py`, `tests/test_evaluation_tools.py`: metric/comparison functions and development-only readiness CLI; formal evaluation requires approved provenance/completeness/alignment/contract. No workbook adapter or actual gold promotion here.
- `prompts/jd_extraction_v1_2.md`, `evidence_matching_v1_1.md`: D-049/v1.3 runtime prompts. Older prompts preserved. `config/pipeline_v1.yaml` declares stage versions; exact prior config at `config/archive/pipeline_v1_pre_D049_20261002.yaml`.
- `src/jobfit/config.py`, extractor, matcher, pipeline and driver updates: explicit version/hash propagation, cache separation and composite structural hold. `tests/test_guideline_v13_runtime.py`: offline migration regressions.
- `evals/results/cp22_pilot_probe_review_20261002.json`, provider/preflight/J3/J4 operational and proposed-alignment artifacts: actual historical v1.2 probe,3calls, stopped before F00073.
- `evals/results/cp22_v13_adoption_20261002.json`, `cp22_v13_final_tests_20261002.xml`, `cp23_readiness_v13_20261002.json`: current offline adoption/readiness evidence. Intermediate results retain original versions.
- Existing CP2.2 audit/contract and CP2.3 report contain findings, limits and a short decision list. No additional dependencies; requirements.txt unchanged.


## Evaluation documentation navigation (2 October 2026)

- `evals/labeling/README.md`: current reviewed receipt and historical-baseline roles.
- `evals/README.md`: active guideline, gold, split and provenance map.
- `evals/annotation_tasks/archive/completed/`: completed T01/T02 prompts, not rerun tasks.
- `docs/checkpoint_2/supporting/archive/preparation/`: pilot-draft preparation report.
- `docs/checkpoint_2/supporting/Development_Labeling_Review_20261002.md`: current QA result and follow-ups.
- `evals/results/development_review_submission_20261002.json`, `development_review_followups_20261002.csv`: machine-readable QA.

Runtime guideline/prompt/schema files, snapshot duplicates, and the working baseline remain at their referenced paths to preserve execution and audit lineage. No pipeline, source, workbook or gold changed in this cleanup.


## Technical retrieval and acceptance closure (2 October 2026)

- `src/jobfit/eval/retrieval_run.py`, `scripts/run_retrieval_comparison.py`, `tests/test_retrieval_run.py`: read-only development top 30 runner, exact cached queries/profiles/source checks, provenance/timing/ties; no labels, API fallback or pool changes.
- `scripts/prepare_cp22_acceptance.py`: preflight-only plan and unchanged eight-fixture outputs; no execute flag or inference client instance.
- `docs/checkpoint_2/supporting/CP22_Acceptance_Review_20261002.md`: one review aid for eight cases, technical retrieval, probe estimate and next ownership.
- `evals/results/cp22_retrieval_top30_20261002_03.json`: final local rankings; `_01` failed sandbox access and `_02` successful previous metadata preserved.
- `evals/results/cp22_acceptance_preflight_20261002.json`, `cp23_readiness_technical_closure_20261002.json`: no-paid-call plan, fixture hashes, readiness with explicit holds. Targeted JUnit files preserve first failure and final passes.
- No new dependencies or changes to requirements. Active workbook is v1.3 per coordination note and was not opened by this work. Sources, gold, frozen split/pool and historical run artifacts are preserved.


## CP2.2 takeover additions (2 October 2026)

- `src/jobfit/extraction/coverage.py`: conservative explicit-list coverage diagnostic; used on fresh and cached extraction before matching.
- `src/jobfit/eval/development_gold.py`, `scripts/export_development_gold.py`: immutable approved-only bundle and dependency/source holds.
- `src/jobfit/eval/bundle_readiness.py`, `scripts/run_evaluation.py --reviewed-bundle ... --retrieval ...`: current inventory/scope checks without metrics.
- `src/jobfit/llm/closure_probe.py`, `scripts/run_cp22_closure_probe.py`: guarded terminal staged probe; current F00034 run is stopped and cannot be restarted.
- `evals/fixtures/v1_3/`: eight versioned synthetic fixture revisions; root fixtures remain historical.
- `evals/gold/development_v13_reviewed_20261002_r2/`: authoritative reviewed development bundle, manifest, holds, logical groups and coverage; no test labels.
- Tests: closure probe, development gold, fixture acceptance v1.3, source coverage guard, reviewed-bundle readiness and upload pipeline regression.
- Current report: `docs/checkpoint_2/CP2_02_Modeling_Pipeline.md`; superseded full report/preflight review preserved in `supporting/archive/`.


## 3 October 2026: scoped extraction repair and continuation

- `prompts/jd_extraction_v1_3.md`, `src/jobfit/extraction/audited.py`: experimental qualification inventory and wire validation; default selection unchanged.
- `scripts/run_cp22_repair_probe.py`, `scripts/repair_cp22_semantics.py`, `src/jobfit/llm/semantic_repair.py`: original staged run and bounded source repair, preserving prior results and aggregate spend.
- `scripts/repair_cp22_matching.py`, `tests/test_matching_semantic_repair.py`: final single-dispatch matching repair through ordinary validators and score code; no workbook or gold write.
- `src/jobfit/eval/bundle_readiness.py`, `scripts/run_evaluation.py`, `tests/test_bundle_readiness.py`: explicit completed-probe receipt checks; readiness remains blocked for formal metrics.
- `docs/checkpoint_2/supporting/CP22_Extraction_Repair_20261003.md`: one experiment record across the account handoff, linked from the main CP2.2 report.
- `evals/results/cp22_extraction_repair_v13_20261003_*.json`, `cp22_repair_*_20261003.json`: first/repaired model outputs, operational checks and proposed semantic alignment; no human approval fabricated.
- `evals/results/cp22_development_extraction_plan_20261003.json`, `cp23_readiness_after_repair_20261003.json`, `cp22_resume_verification_20261003.json`, `cp22_resume_final_offline_20261003.xml`: zero-call preflight, readiness and verification. No dependency added.


## D-051 privacy documentation (3 October 2026)

`docs/privacy-threat-model.md` is the detailed approved design and PR-01-PR-10 acceptance matrix. The decision log and CP2.3/CP2.4/CP3.1-CP3.4 reports assign implementation and validation. Runtime security is not claimed implemented. Private discussion/handoff notes point to this source; they are not separate competing specifications. No new runtime module, dependency or private-data table was added by the documentation update.


## D-052 evaluation preparation (3 October 2026)

`docs/evaluation.md` is the approved evaluation-contract-v1, distinct from individual reference/alignment approval. CP2.3 section13B delegates stage-1 manifest/coverage checks and evaluator compatibility work. No runtime implementation, paid run or benchmark result was created by the documentation update. The execution brief is private in `JobFit_Codex2_CP23_Stage1_Prompt.md`.

Stage-1 execution added `src/jobfit/eval/contract.py` for D-052 policy/receipt and gate checks; updated `metrics.py`, `alignment.py`, `run_eval.py` and `scripts/run_evaluation.py` for original-position metrics, complete-unit inventories and explicit historical mode. `scripts/prepare_cp23_stage1.py` creates versioned read-only case and top 10-gap manifests. New offline regression tests are in `tests/test_cp23_stage1_prep.py` and updated `tests/test_evaluation_tools.py` / `tests/test_guideline_v13_runtime.py`. The current report is `docs/checkpoint_2/supporting/CP23_Stage1_Evaluation_Preparation_20261003.md`; current artifacts are `evals/results/cp23_metric_contract_D052_20261003_v2.json`, `cp23_stage1_case_candidates_20261003_v3.json`, `cp23_stage1_top10_gaps_20261003_v3.json`/`.csv`, `cp23_stage1_readiness_20261003_v3.json`, `cp23_stage1_offline_tests_20261003_v2.xml` and `cp23_stage1_protected_verification_20261003_v3.json`. Earlier revisions remain historical. There was no model call, benchmark, workbook/gold/source edit or new dependency.

The Stage-1 follow-up added `evals/labeling/drafts/cp23_stage1_relevance_review_20261003_v1.json` and `.md` for six source-checked **pending** C decisions, `evals/results/cp23_stage1_hold_and_decision_review_20261003_v1.json` for three holds/two semantic questions/a proposed split-merge rule, and `evals/results/cp23_stage1_followup_validation_20261003_v1.json` for read-only integrity checks. `evals/results/cp23_stage1_followup_offline_tests_20261003_v1.xml` records the rerun of 72 selected offline tests. These are review/QA artifacts, not gold or benchmark results. The existing CP2.3 supporting report contains the concise review boundary.

**D-054 current Stage-1 state:** `evals/gold/development_v13_reviewed_20261003_stage1_r3/` is the immutable amendment (1,058 A / 1,364 B / 78 C) with an amendment receipt, preserving the r2 bundle. `src/jobfit/eval/stage1_amendment.py` and `tests/test_stage1_amendment.py` implement/test the approved case-scoped promotion. `evals/results/cp23_stage1_user_review_receipt_20261003_v2.json`, `cp23_F00332_alignment_approval_20261003_v1.json`, `cp23_metric_contract_D052_D054_20261003_v1.json`, the v4 case/gap/readiness manifests and the post-amendment verification receipt document provenance and all five ready prerequisite gates. `docs/evaluation.md` is now evaluation-contract-v1.1. Earlier drafts/receipts remain historical; no workbook edit.

**Stage-2 extraction preflight:** `src/jobfit/eval/stage2_extraction.py` builds a frozen seven-JD/four-model conservative cost plan and durable attempt limiter. `scripts/run_cp23_stage2_extraction.py` requires an exact plan-hash approval receipt before any paid mode and pauses between cases for source-based review. `tests/test_cp23_stage2_extraction.py` covers scope/source mutation, approval and fake-client limits. Current artifact: `evals/results/cp23_stage2_round1_extraction_20261003_v3_preflight.json`; report: `docs/checkpoint_2/supporting/CP23_Stage2_Comparison_Preflight_20261003.md`; selected offline JUnit v3. v1/v2 preflight and earlier failed/corrected XML remain historical. No paid run or new dependency.

**Stage-2 first run and matching preparation:** Dion's exact-cap receipt, one DeepSeek/F00332 result and source-semantic stop receipt are `evals/results/cp23_stage2_extraction_budget_approval_20261003_v1.json` and `cp23_stage2_round1_extraction_20261003_v3_01*.json`. The append-only ledger records the one provider-reported charge; the run is stopped, not silently restarted. `src/jobfit/eval/fixed_requirements.py`, `tests/test_cp23_fixed_requirements.py` and `evals/results/cp23_stage2_fixed_matcher_inputs_20261003_v1.json` create/check four gold-backed matcher inputs (73logical units,13OR groups) without gold CV answers or paid matching. Selected offline XML: `cp23_stage2_offline_tests_20261003_v1.xml`. Earlier preflight-only statement above is historical.

**v1.4 and matcher-only preflights:** `prompts/jd_extraction_v1_4_experimental.md` is a new versioned candidate; `evals/results/cp23_stage2_v14_prompt_revision_20261003_v1.json` and `cp23_stage2_round1_extraction_20261003_v4_preflight.json` preserve its hash and same-case cost bound without changing the active prompt. `scripts/prepare_cp23_stage2_matching.py` captures the ordinary matcher payload offline, preserving reviewed fixed inputs and CV1's source-verified parse; `evals/results/cp23_stage2_matcher_preflight_20261003_v1.json` records16stages, no model call and a separate cost bound. Final selected offline JUnit: `cp23_stage2_v14_offline_tests_20261003_v2.xml` (45passes). No new dependency.

**v1.4 result and proposed continuation:** `cp23_stage2_round1_extraction_20261003_v4_01.json` and its semantic-check receipt preserve the two-attempt DeepSeek/F00332 result and terminal source-semantic stop; FAIL-16 and the Stage-2 report describe its cost/limits. `src/jobfit/eval/stage2_continuation.py`, `scripts/run_cp23_stage2_continuation.py` and `tests/test_cp23_stage2_continuation.py` implement/test a separately approvable, same-protocol 27-case continuation that records semantic failures without substituting cases. `cp23_stage2_round1_extraction_20261003_v5_continuation_preflight.json` freezes its sources, prior failed result and US$3.1559888 bound; `cp23_stage2_continuation_offline_tests_20261003_v2.xml` records16passing targeted tests. No v5 paid call or new dependency.


**Current Stage 2/Stage3 continuation (3 October 2026):** `src/jobfit/eval/stage2_route_repair.py` and `scripts/run_cp23_stage2_route_repair.py` adapt the GPT request in an explicitly versioned v6 run, with cumulative predecessor costs and unchanged privacy/source controls. The frozen proposal, plan-bound approval and endpoint metadata live in `evals/results/`; per-case outputs and source QA receipts remain separately auditable. `tests/test_cp23_stage2_route_repair.py` verifies parameter and cumulative-budget behavior.

`src/jobfit/eval/retrieval_evaluation.py`, `scripts/evaluate_cp23_retrieval.py` and `tests/test_cp23_retrieval_evaluation.py` implement hash-bound, inference-free Stage 3 evaluation of current reviewed C against saved top 30 rankings. Current result `cp23_stage3_retrieval_evaluation_20261003_v2.json` and per-CV CSV are in `evals/results/`; the English report is `docs/checkpoint_2/supporting/CP23_Stage3_Retrieval_Comparison_20261003.md`. No gold/workbook/source/configuration mutation or selected winner.


### CP2.3 partial comparison inventory and proposed failure continuation

- `src/jobfit/eval/extraction_inventory.py`, `tests/test_cp23_extraction_inventory.py`: immutable common-case result/source-check inventory; no F1 or winner inferred.
- `evals/results/cp23_stage2_v14_observation_inventory_20261003_v1.json` and `_observations_20261003_v1.csv`:19attempted/28original cases; failed/unattempted are explicit.
- `src/jobfit/eval/stage2_remaining_cases.py`, `scripts/run_cp23_stage2_remaining_cases.py`, `tests/test_cp23_stage2_remaining_cases.py`: proposed v7 settled-failure receipt gate, cumulative v5/v6/v7 budget, no failed-case retry.
- `evals/results/cp23_stage2_v7_remaining_cases_proposal_20261003_v1.json` and `cp23_stage2_round1_extraction_20261003_v7_remaining_cases_preflight.json`: **awaiting protocol approval, no inference**.
- `evals/results/cp23_takeover_targeted_tests_20261003_v3.xml`:73passing offline tests; v2preserves a test-fixture setup failure.


### Current CP2.3 extraction collection closure

- `scripts/summarize_cp23_extraction.py`: read-only reproducible case/cost/timing inventory with fresh-output protection.
- `evals/results/cp23_stage2_v14_observation_inventory_20261003_v3.json` and `cp23_stage2_v14_observations_20261003_v3.csv`: current 28-case collection, 27 final drafts and one retained failure; no candidate F1 or winner.
- `evals/results/cp23_stage2_v7_remaining_cases_approval_20261003_v1.json`: D-059 approved continuation; v7 completed all nine remaining cases. Earlier awaiting-approval notes are historical.
- `evals/results/cp23_takeover_targeted_tests_20261003_v4.xml`: latest 73 passing tests.
- `evals/results/cp23_takeover_protected_inputs_20261003_v2.json`: final source/input preservation and code/artifact hashes.


### Stage-2 closure preparation additions (3 October 2026)

- `scripts/prepare_cp23_extraction_alignment.py`: complete source-based relation proposals, zero inference/no gold edits; current packet/report v2 corrects qualifier interpretation. Earlier v1 remains historical.
- `scripts/run_cp23_stage2_matching.py`, `src/jobfit/eval/stage2_matching.py`: plan-bound separate matching approval, aggregate budget, durable per-stage attempt records and stop on uncertain cost. Default preflight only.
- `src/jobfit/eval/matching_evaluation.py`: reviewed 73-unit reference inventory, branch-aware labels and complete failed/unassessed FN accounting; accepted fixed-input alignment is mandatory before metrics.
- `tests/test_cp23_stage2_matching.py`, `tests/test_cp23_matching_evaluation.py`, `tests/test_cp23_extraction_alignment_packet.py`: targeted matching/ref/alignment protections.
- Preliminary `src/jobfit/privacy/` and implemented `src/jobfit/session/store.py`, with `tests/test_privacy_controls.py`: synthetic-only local masking/consent/ownership/expiry prototype, paused while Stage 2 closes. No API/UI integration, automatic cleanup scheduler, complete anonymization, provider ZDR feasibility or real-CV release claim.


### Stage-2 accepted round-one evaluation additions (3 October 2026)

- `scripts/evaluate_cp23_stage2_round1.py`: hash-bound D-063 metric calculation; all original failed cases retained.
- `scripts/audit_cp23_stage2_matching.py`: offline first-draft replay and delegated source/entailment findings; no inference or prediction correction.
- `src/jobfit/eval/strict_complex_alignment.py`: D-060 case-scoped accounting, not a blanket mapping rule.
- `src/jobfit/eval/portable_repair.py`: proposed repair framing only; active client and frozen paid protocols remain unchanged.
- `tests/test_cp23_round1_quality.py`: receipt/content binding and untrusted-data boundaries for the proposed adapter.
- English stage summary: `docs/checkpoint_2/supporting/CP23_Stage2_LLM_Comparison_20261003.md`; accepted metrics/QA/approval and unexecuted reference/round-two proposals are in `evals/results/`. No added dependency.


### Current D-064 follow-up and version retention

- `scripts/run_cp23_stage2_followup.py` and `src/jobfit/eval/portable_repair.py`: executed, separately approved19-stage experiment with frozen inputs, request bounds and durable state. Earlier proposal-only entries are historical.
- `scripts/prepare_cp23_followup_alignment.py`: complete11-output,188-relation source-review packet; no candidate acceptance fabricated.
- `scripts/evaluate_cp23_followup_matching.py`: accepted fixed-input metrics, complete final source QA, typed-attempt replay and original failed-case accounting.
- `scripts/evaluate_cp23_followup_extraction.py`: new-receipt gate, same-scope full-seven/common-four tables, original failures retained; not run before acceptance.
- `tests/test_cp23_followup_evaluation.py`: incomplete-run, payment-versus-mapping-approval and reference-denominator protection.
- `prompts/README.md` and `evals/results/cp23_prompt_version_inventory_20261003_v1.json`: prompt lifecycle, exact content/hashes and repair-format provenance.
- Current measured results and limits are in the Stage-2 comparison report section 9; paid collection complete, selection still open. No new dependency.


## Repair-framing and freeze preparation additions

- `src/jobfit/matching/guardrails.py`: offline G1/G2 proposal, no runtime adoption.
- `scripts/prepare_cp23_repair_rerun.py` and `run_cp23_repair_rerun.py`: original blocked preflight and separately approved repair-only replay.
- `scripts/analyze_cp23_repair_views.py`: A/B and guardrail evidence through the existing round-one evaluator CLI.
- `scripts/evaluate_cp23_gold_upper_bound.py`: retained-ID oracle score coverage and ordering gates.
- `tests/test_repair_message_framing.py`, `test_repair_replay_guard.py`, `test_evidence_guardrails.py`, `test_gold_upper_bound.py`: offline regression checks.
- Versioned results use `cp23_stage2_repair_*`, `cp23_gold_input_upper_bound_*`, and `cp23_embedding_D044_selection_*`.
- Supporting reports: `CP23_Gold_Input_Upper_Bound_20261004.md`, `CP23_Freeze_Proposal_20261004.md`, and historical `CP23_Progress_Log_20261003.md`.

### Part B completion and presentation coverage, 4 October 2026

- `scripts/run_cp23_end_to_end_dev.py`: unchanged D-068 model/source plan, with D-069 US$2.50 total cap, immutable original plan, versioned amendment, resume skip and presentation cutoff. No timeout stage was replayed.
- `scripts/evaluate_cp23_end_to_end_dev.py`: final-order metrics require all original top-K candidates to have numeric scores. A scored-subset diagnostic is named separately and cannot select K or weight. The v1 partial evaluation is historical; v2 reads the completed collection.
- `scripts/build_cp23_partb_figure.py`: creates `reports/figures/cp2/fig07_partb_coverage_20261004_v1.png` from saved pair records. The first six figures remain intact.
- `scripts/audit_cp23_partb_saved_quotes.py`: read-only exact-substring and unit-identity audit for process-valid development outputs. Its receipt does not certify semantic entailment.
- `evals/results/cp23/end_to_end_dev/`: original stage files, cap amendment, A3 snapshot, completed-run receipt v3, D-052 evaluation v2 and protected-input check v2. V2 receipt remains to show its corrected float formatting; v3 is the current receipt.
- `tests/test_cp23_end_to_end_dev.py`: offline resume, cutoff and missing-top-K metric regression checks. No new dependency or database change.

## Added 4 to 6 October 2026

| Path | Purpose |
| --- | --- |
| `src/jobfit/recommend/service.py` | One-CV flow: stage 1, seniority rule, top K, cached extraction, Sol matching (Luna fallback), H2v2, experience block, product order, filters |
| `src/jobfit/recommend/saved_demo.py`, `scripts/build_demo_bundle.py`, `evals/demo/` | D-022 saved demo replayed through the same code; versioned bundles |
| `src/jobfit/llm/runtime.py`, `config/versions/route_rules_cp23_v1.json` | Runtime client with the frozen request rules and the 240 s timeout |
| `src/jobfit/matching/experience_rule.py` | D-086 experience conflict block |
| `src/jobfit/extraction/saved_records.py` | Which saved extraction counts for a job (newest evaluated record wins) |
| `src/jobfit/eval/d078.py`, `scripts/run_post_labeling.py` | D-078 rule and the post-labeling run |
| `src/jobfit/eval/test_pool.py`, `scripts/prepare_cp23_freeze.py`, `scripts/build_cp23_test_workbook.py`, `scripts/run_cp24_test.py` | D-053 freeze receipt, held-out run and blind pool |
| `src/jobfit/api/` (`main.py`, `presenter.py`, `wiring.py`), `src/jobfit/schemas/api.py` | FastAPI service (CP3.1) |
| `src/jobfit/support/cv_suggestions.py`, `cv_coach.py`, `market_insight.py` | Minimal suggestions, CV coach v1 (D-036), market counts |
| `ui/` | Streamlit app (CP3.3) |
| `Dockerfile.api`, `Dockerfile.ui`, `docker-compose.yml`, `.github/workflows/tests.yml` | Images, local stack and CI (CP3.2) |
| `scripts/e2e_check.py` | CP3.4 end-to-end checks against a running API |
| `scripts/import_dev_gap_r4.py`, `evals/gold/development_v13_reviewed_20261004_gap_r4/` | D-085 gold r4 |
| `docs/checkpoint_3/Runbook_Freeze_Test_Deploy_20261006.md` | Step-by-step for Dion |
