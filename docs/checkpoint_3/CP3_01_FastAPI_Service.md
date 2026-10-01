# CP3.1: API Deployment with FastAPI

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 15. Deployment API menggunakan Flask/FastAPI · official date 5 Oct 2026  
**JobFit version of this checkpoint:** FastAPI (Flask is not used).  
**Planned work:** 5 Oct 2026 · **Actual:** not run yet  
**Status:** PLANNED / NOT RUN · design basis: System Design v1.3

> This report is a plan. It contains no results yet. Results, scores, mentor feedback, and deployment evidence are added only after the work is actually done, with links to the [experiment log](../experiments.md) instead of copied numbers. The plan for all stages is in the [master plan](../master-plan.md).

## 1. Goal of this stage

Make the business logic callable through a consistent, tested API.

## 2. Inputs and prerequisites

- Modules frozen in checkpoint 13
- Mentor feedback from checkpoint 14

## 3. Planned method

1. Endpoints: `/health`, `/cv/parse`, `/recommendations`, `/jobs/{job_id}`, `/jobs/paste`, `/analyze`, `/tailor` (minimal), `/market/query` (minimal), `DELETE /session`, `/feedback`.
   `/tailor` follows the CV coach plan (D-036, [cv-coach-plan.md](../cv-coach-plan.md)) and is built only after matching is complete.
2. Request and response schemas.
3. Session storage with a TTL.
4. Timeouts, error mapping, and the rate/cost guard.
5. API tests and an OpenAPI check.

## 4. Planned outputs

- FastAPI app in `src/`
- API tests
- OpenAPI screenshot
- this stage report

## 5. Acceptance criteria

- The core flow works without Streamlit.
- Invalid input fails with a clear error.
- The budget guard is active on every LLM call.

## 6. Evidence to keep

- test output
- OpenAPI screenshot

## 7. Estimate and dependencies

- **Estimate:** About 1 working day.
- **Depends on:** Checkpoint 13 decisions.

## 8. Fallback if blocked

Build the core endpoints first (`/cv/parse`, `/recommendations`, `/analyze`, `/jobs/paste`); the minimal ones follow later the same day or on 6 Oct.

## 9. Checklist

- [ ] Endpoints: `/health`, `/cv/parse`, `/recommendations`, `/jobs/{job_id}`, `/jobs/paste`, `/analyze`, `/tailor` (minimal), `/market/query` (minimal), `DELETE /session`, `/feedback`.
- [ ] Request and response schemas.
- [ ] Session storage with a TTL.
- [ ] Timeouts, error mapping, and the rate/cost guard.
- [ ] API tests and an OpenAPI check.
- [ ] Acceptance: The core flow works without Streamlit.
- [ ] Acceptance: Invalid input fails with a clear error.
- [ ] Acceptance: The budget guard is active on every LLM call.

## 10. Results

Not run yet.

## 11. Interpretation and limitations

Not run yet.

## 12. Decisions from this stage

None yet. Decisions are recorded in the [decision log](../decisions.md) when they are made.

## 13. Next step

CP3.2 (checkpoint 16): database migrations, CI, and deployment of the database.
