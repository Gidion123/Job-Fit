# CP3.2: Database Integration and CI/CD

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 16. Integrasi Database & GitHub Actions CI/CD · official date 6 Oct 2026  
**JobFit version of this checkpoint:** PostgreSQL with pgvector, and GitHub Actions for CI/CD.  
**Planned work:** 6 Oct 2026 (hosting smoke deploy earlier, on 1-2 Oct) · **Actual:** not run yet  
**Status:** PLANNED / NOT RUN · design basis: System Design v1.3

> This report is a plan. It contains no results yet. Results, scores, mentor feedback, and deployment evidence are added only after the work is actually done, with links to the [experiment log](../experiments.md) instead of copied numbers. The plan for all stages is in the [master plan](../master-plan.md).

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

None yet. Decisions are recorded in the [decision log](../decisions.md) when they are made.

## 13. Next step

CP3.3 (checkpoint 17): Streamlit UI.
