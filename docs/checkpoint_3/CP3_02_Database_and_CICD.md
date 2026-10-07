# CP3.2: Database Integration and CI/CD

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 16. Integrasi Database & GitHub Actions CI/CD · official date 6 Oct 2026  
**JobFit version of this checkpoint:** PostgreSQL with pgvector, and GitHub Actions for CI/CD.  
**Planned work:** 6 Oct 2026 (hosting smoke deploy earlier, on 1-2 Oct) · **Actual:** 6 Oct 2026  
**Status:** PARTIAL · Docker and compose work locally; CI red (FAIL-35); SumoPod VPS, Alembic and job sync PLANNED (D-095, D-098); nothing deployed · design basis: System Design v1.3

> Plan sections are kept as written. Results are added below, with links to the [experiment log](../experiments.md). The plan for all stages is in the [master plan](../master-plan.md).

## CP3 final plan for this stage (7 Oct 2026, D-095 to D-100)

**JobFit scope:** production corpus, job sync, VPS and delivery. Everything in this section is **PLANNED / NOT YET VALIDATED** unless marked otherwise. Stage definition: [master plan](../master-plan.md#cp32-database-integration-and-cicd-checkpoint-16). Tasks: [CP3 execution plan](CP3_Execution_Plan.md). Corpus design: [production-corpus.md](../production-corpus.md).

- **Hosting change:** Railway (D-023) is replaced by a SumoPod VPS: Singapore, Ubuntu 24.04 LTS, 2 vCPU / 8 GB / 80 GB (D-095). Dion and Codex buy and configure it; this repository provides the deploy files and runbook. No Railway account was created.
- **Already done:** see "Results (6 Oct 2026)" below. Correction: CI is **red** because of FAIL-35, so "CI ready" below holds only once FAIL-35 is fixed.
- **Planned scope:**
  - **CI:**
    - re-apply FAIL-35 cleanly;
    - pin `ruff` plus `F`;
    - freeze verify;
    - prod compose config;
    - a pgvector service job (Alembic up, down/up where reversible, database-gated tests);
    - the internal `e2e_check` against compose.
    - No provider secrets in CI.
  - **Database (D-098):**
    - minimal Alembic (`0001` = the current `SCHEMA_SQL`; `0002` = lifecycle, `dedupe_status`, `job_sources` unique on `(source, source_job_id)`, `sync_runs`, extraction cache, quota, reservations);
    - upgrade only after a verified backup;
    - recovery = the previous tag plus a restore.
    - The CP2 `SCHEMA_SQL` and loader stay unchanged.
  - **Seed:** a restore-tested dump of 632 rows. The 428 target-role rows are active; all rows are canonical.
  - **Sync:**
    - twice a month (about every two weeks) through a GitHub Actions SSH forced command; credentials stay on the VPS;
    - a production query manifest (≤ 80 requests);
    - exact duplicates map to the canonical job with no new row;
    - fuzzy suspects are `review_required`, inactive and kept out of retrieval;
    - NEW / CONTENT_CHANGED / METADATA_CHANGED / UNCHANGED / STALE;
    - a coverage-aware lifecycle;
    - incremental embeddings;
    - a report.
  - **Deployment:**
    - `docker-compose.prod.yml` with Caddy (only 80/443 public), restart policies, log rotation and healthchecks;
    - a runtime artifact manifest and verifier (the tokenizer built into the API image);
    - a restore-tested initial dump; nightly backups;
    - manual tagged deploys;
    - a VPS runbook.
  - **Monitoring (D-099):**
    - Prometheus, Grafana and node_exporter;
    - email alerts through `GRAFANA_SMTP_*` / `GRAFANA_ALERT_*` placeholders;
    - sync gauges;
    - a backup-age metric.
- **Validation layers:**
  - A: external public smoke through Caddy and Streamlit (HTTPS, saved demo);
  - B: the internal API `e2e_check.py` inside the VPS Docker network or through an SSH tunnel.
  - FastAPI is never exposed publicly.
- **Tests to add:**
  - Alembic on an empty and a restored database;
  - the sync suite (normalization parity, identity order, exact-duplicate idempotency, `review_required` exclusion, **the same vacancy never appears twice in retrieval**, classification, coverage, lifecycle, rollback, dry run, no CP2 path writes);
  - the artifact verifier.
- **Costs:** JSearch uses the free tier (≤ 80 requests per sync); embeddings cost about US$0.0000064 per job (capped at US$0.10 per sync); VPS hosting is outside the LLM budget.
- **Acceptance:** see the master plan, CP3.2 points 5 and 10.
- **Limitations:** no provider expiration data has been seen, so staleness is inferred from coverage and age. Link liveness is not checked.
- **Status:** PARTIAL. Nothing is deployed.

## 1. Goal of this stage

Make the system reproducible from a fresh clone and deployable.

## 2. Inputs and prerequisites

- Checkpoint 15 API
- Railway account created by Dion (D-023 approved)

## 3. Planned method

1. Migrations for jobs, job_requirements (versioned cache), embeddings, demo_analysis_cache, feedback.
2. Idempotent snapshot loading.
3. GitHub Actions: lint, tests, Docker build, guideline fixtures.
4. Secrets through environment variables only.
5. Deploy the database and the API on the chosen host.
6. Precompute the saved demo results for the synthetic CVs.

## 3A. D-051 persistence and deployment gate

Follow [privacy-threat-model.md](../privacy-threat-model.md). PostgreSQL/pgvector stores public jobs and explicitly synthetic demo data only for these paths, not private CVs, profiles, vectors, pasted JDs or reports. Audit feedback so it cannot silently retain document/contact payloads. Volatile private session storage must have persistence/backups disabled; adding a shared store or replicas needs an explicit isolation/retention design. Check Streamlit/FastAPI/proxy temporary upload copies, host logs/traces/crash dumps, backup volumes, TLS and server-only secrets.

- [ ] No private-data migration or durable cache introduced.
- [ ] Synthetic-canary inspection of database, logs, temporary files and hosting persistence.
- [ ] CI runs privacy regression tests; deployed cleanup and session routing match the documented topology.


## 4. Planned outputs

- migration files
- CI workflow
- Dockerfiles
- deployed database and API
- this stage report

## 5. Acceptance criteria

- A fresh clone can create the schema and pass the tests without manual database work.
- No secrets in the repository.
- CI is green.

## 6. Evidence to keep

- CI screenshot
- Docker build proof
- schema

## 7. Estimate and dependencies

- **Estimate:** About 1 working day.
- **Depends on:** Railway account; the smoke deploy on 1-2 Oct; Dion's confirmation of the Hobby cost.

## 8. Fallback if blocked

If the chosen host is blocked, use the free fallback in System Design v1.3 section 16 and note the limits.

## 9. Checklist

- [ ] Migrations for jobs, job_requirements (versioned cache), embeddings, demo_analysis_cache, feedback.
- [ ] Idempotent snapshot loading.
- [ ] GitHub Actions: lint, tests, Docker build, guideline fixtures.
- [ ] Secrets through environment variables only.
- [ ] Deploy the database and the API on the chosen host.
- [ ] Precompute the saved demo results for the synthetic CVs.
- [ ] Acceptance: A fresh clone can create the schema and pass the tests without manual database work.
- [ ] Acceptance: No secrets in the repository.
- [ ] Acceptance: CI is green.

## 10. Results

Not run yet.

## 11. Interpretation and limitations

Not run yet.

## 12. Decisions from this stage

D-051 privacy design is approved; implementation outcomes and release acceptance are pending. Record outcomes in the [decision log](../decisions.md) without treating design approval as a test pass.

## 13. Next step

CP3.3 (checkpoint 17): Streamlit UI.

## Results (6 Oct 2026)

- **Docker:** `Dockerfile.api` (saved demo works with no database and no model call; live analysis off by default), `Dockerfile.ui`, and api/ui/db services in `docker-compose.yml`, all bound to 127.0.0.1. Two start-up bugs were found on Dion's Mac and fixed (FAIL-29 path, FAIL-30 file permissions).
- **CI:** `.github/workflows/tests.yml` runs ruff (syntax and undefined names), the offline tests, both image builds and a `/health` smoke check. It starts only after Dion pushes; a local simulation without git-ignored files gave 615 passed, 9 skipped.
- **Database:** the job corpus, embeddings and search already run on PostgreSQL with pgvector (CP2.1). Changes from the plan, on purpose: the demo cache is a versioned file bundle (`evals/demo/saved_demo_v4/`, D-022 key checks), JD requirements stay versioned JSON records, and feedback lives in memory with categories only. No private CV data is ever written to the database (D-051).
- **Secrets:** only through environment variables (`.env` for local work, host variables for deployment); `.env` is git-ignored and excluded from the images.
- **Pending (needs Dion):** Railway account and cost confirmation (D-023), loading the corpus snapshot into the hosted database, and the first deploy. Without the hosted database the deployed app still serves the saved demo.
