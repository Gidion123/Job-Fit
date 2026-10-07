# CP3.1: API Deployment with FastAPI

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 15. Deployment API menggunakan Flask/FastAPI · official date 5 Oct 2026  
**JobFit version of this checkpoint:** FastAPI (Flask is not used).  
**Planned work:** 5 Oct 2026 · **Actual:** 6 Oct 2026  
**Status:** DONE LOCALLY · deployed check pending (CP3.4) · design basis: System Design v1.3

> Plan sections are kept as written. Results are added below, with links to the [experiment log](../experiments.md). The plan for all stages is in the [master plan](../master-plan.md).

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

## 3A. D-051 privacy implementation gate

Implement the [privacy contract](../privacy-threat-model.md), reusing CP2.3 primitives. Bind read/analyze/delete/feedback and pending work to authenticated possession of the owning session credential; no login feature is required. Add lease/idle/absolute expiry, immediate invalidation, bounded cleanup and cancellation/late-result disposal. Never place private CV data or derivatives in PostgreSQL or shared caches. Implement temporary-upload cleanup, consent bound to exact masked text, and provider/embedding privacy gates. Final session heartbeat/delete route schemas are implementation details to document in OpenAPI.

- [ ] Owner authorization and cross-session denial on all private operations.
- [ ] Actual browser-origin lease, idle/absolute timers, revoke/delete and cleanup tests.
- [ ] Consent/version enforcement before every CV-derived provider call; no raw fallback.
- [ ] Safe upload/resource limits, exception cleanup and no private log payloads.
- [ ] Real-CV enablement remains blocked until D-051 release checks and consent; synthetic demo remains available.


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

D-051 privacy design is approved; implementation outcomes and release acceptance are pending. Record outcomes in the [decision log](../decisions.md) without treating design approval as a test pass.

## 13. Next step

CP3.2 (checkpoint 16): database migrations, CI, and deployment of the database.

## Results (6 Oct 2026)

- **Built:** `src/jobfit/api/main.py` (routes), `src/jobfit/schemas/api.py` (request models), `src/jobfit/api/presenter.py` (response JSON), `src/jobfit/api/wiring.py` (real dependencies). Every planned endpoint exists; see [EXP-20261006-CP3](../experiments.md). The OpenAPI page is at `/docs` when the API runs.
- **Core flow without Streamlit:** saved demo, live run, job detail, paste and analyze, CV suggestions and coach, market counts, feedback and delete all work over HTTP (`tests/test_api.py`, `tests/test_api_cp31.py`, `scripts/e2e_check.py`).
- **Privacy (D-051, section 3A):** owner checks on every private route and run; cross-session reads, swaps and deletes are refused; lease 2 minutes, idle 30 minutes (the heartbeat does not reset it), absolute 2 hours; a sweeper removes expired sessions with their runs and pasted JDs; deletion drops late results; consent is bound to the exact masked text and an edit clears it; uploads keep no original bytes; feedback stores categories only. `tests/test_api_privacy.py` covers PR-01 to PR-07 and PR-09 at API level.
- **Kept closed on purpose:** provider processing of uploaded real CVs (`/cv/parse` answers 403). D-051 still has open items (city and company policy, verified zero-retention endpoints), so only the synthetic demo CVs are analyzed.
- **Budget guard:** every model call goes through the OpenRouter client and its project guard; live runs are limited to 3 per session and 1 at a time; the Docker image starts with live analysis off.
- **Limits:** v1 runs one API process with in-memory sessions; more replicas need a shared session store and a new privacy review.
