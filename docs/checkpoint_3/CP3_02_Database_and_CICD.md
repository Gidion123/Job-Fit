# CP3.2: Database Integration and CI/CD

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 16. Integrasi Database & GitHub Actions CI/CD · official date 6 Oct 2026  
**JobFit version of this checkpoint:** PostgreSQL with pgvector, and GitHub Actions for CI/CD.  
**Planned work:** 6 Oct 2026 (hosting smoke deploy earlier, on 1-2 Oct) · **Actual:** 6 Oct 2026  
**Status:** PARTIAL · Docker and CI ready; hosting deploy waits for Dion · design basis: System Design v1.3

> Plan sections are kept as written. Results are added below, with links to the [experiment log](../experiments.md). The plan for all stages is in the [master plan](../master-plan.md).

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
