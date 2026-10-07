# CP3.1: API Deployment with FastAPI

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 15. Deployment API menggunakan Flask/FastAPI · official date 5 Oct 2026  
**JobFit version of this checkpoint:** FastAPI (Flask is not used).  
**Planned work:** 5 Oct 2026 · **Actual:** 6 Oct 2026  
**Status:** PARTIAL · demo-CV flow DONE LOCALLY (6 Oct); public live path and safety controls PLANNED / NOT YET VALIDATED (D-095 to D-097) · design basis: System Design v1.3

> Plan sections are kept as written. Results are added below, with links to the [experiment log](../experiments.md). The plan for all stages is in the [master plan](../master-plan.md).

## CP3 final plan for this stage (7 Oct 2026, D-095 to D-100)

**JobFit scope:** public live API, safety controls and instrumentation. Everything in this section is **PLANNED / NOT YET VALIDATED** unless marked otherwise. The stage definition is in the [master plan](../master-plan.md#cp31-api-deployment-with-fastapi-checkpoint-15), and the task list is in the [CP3 execution plan](CP3_Execution_Plan.md).

- **Objective:** move from "demo CVs only" to safe public analysis of arbitrary uploaded CVs (D-095), without changing any D-087 frozen file (D-097).
- **Already done (local, 6 Oct):** see "Results (6 Oct 2026)" below. Evidence: `tests/test_api*.py`, `scripts/e2e_check.py`, EXP-20261006-CP3.
- **Planned scope:**
  - **Settings and budget (D-096, FAIL-38):**
    - fail-closed settings;
    - a persistent production ledger;
    - deterministic phase bounds: `parse_max`, `recommendation_upper_bound` and `full_analysis_upper_bound`, which must be at most the US$2/day cap, otherwise a blocker;
    - separate parse and recommendation reservations (reserve, settle, release; embedding is charged only to the recommendation reservation; no billable call without an active reservation);
    - one live analysis at a time;
    - one ticket per IP per 24 h (HMAC, consumed at the first billable call);
    - an internal service token;
    - an owner override for the per-IP limit only;
    - a session rate limit.
  - **Public path (D-097):**
    - the consent lease stored server-side;
    - the **consent compatibility adapter around the frozen CP2 parser**, entered only through `SessionStore.dispatch`, with 7 required tests (stop and report if `is_synthetic` has another dependency);
    - the `cv_source = demo | upload` contract;
    - runtime query embedding of the consented masked text;
    - a production retriever (active, canonical, target-role jobs);
    - a lazy extraction cache with parallel prefetch;
    - a concurrency-safe app client (FAIL-36).
  - **Privacy:**
    - name and address hints with correct masking text (FAIL-37);
    - upload hardening, limited to the formats the current extractor supports: `.pdf` (text only, ≤ 30 pages, not encrypted), `.docx`, `.txt`, `.md`; ≤ 10 MB; ≤ 100,000 characters;
    - an allow-list and a signature check;
    - a streamed size limit before buffering;
    - a **DOCX decompression gate** (entry count, total uncompressed size, compression ratio, `word/document.xml` required);
    - an extraction timeout;
    - safe errors.
  - **Operations:**
    - `/docs` off; proxy headers;
    - readiness with a database check;
    - an error taxonomy;
    - request IDs and JSON logs;
    - `/metrics`;
    - a Langfuse Japan adapter, metadata only (D-099);
    - stage events for the waiting UX (D-093 A).
- **Architecture:** Browser → Caddy → Streamlit → (internal token and client IP) → FastAPI → PostgreSQL / OpenRouter / Langfuse. FastAPI is never public.
- **Tests to add:**
  - settings fail closed;
  - phase bounds and reservations;
  - quota fairness;
  - the 7 adapter tests;
  - upload failure paths, including the 6 DOCX gate tests;
  - canaries in logs, metrics and the Langfuse payload;
  - serial and concurrent `Recommendation` outputs identical on a fake SDK, with one ledger line per call;
  - freeze verify.
- **Costs:** no paid calls in this stage's development (fake SDKs only). Live measurement happens in CP3.4 inside the US$5 validation budget.
- **Failures:** FAIL-36, FAIL-37 and FAIL-38 are OPEN and are fixed in this stage; FAIL-38 is partly addressed in Phase 2A. FAIL-35 was resolved in Phase 1.
- **Acceptance:** see the master plan, CP3.1 points 5 and 10.
- **Limitations:** one API process with in-memory sessions; latency is not claimed until measured.
- **Status:** PARTIAL. Phase 1 is done (FAIL-35 resolved). Phase 2A (fail-closed settings and phase bounds) is done; see "Results (7 Oct 2026, Phase 2A)" below. The full bound is above the cap, so public live is not eligible. Next: a decision by Dion and Codex, then Phase 2B.

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

## Results (7 Oct 2026, Phase 2A)

Local and CI only. Nothing is deployed, no paid call was made, and no D-087 frozen file changed (freeze verify `"ok": true`).

### Fail-closed production settings (commit `1574e31`)

- **Code:** `get_production_settings()` and `ProductionSettings` in `src/jobfit/config.py`. `Settings` and `get_settings()` are unchanged, so CP2 scripts and runners behave as before. `live_enabled()` in `src/jobfit/api/wiring.py` now reads these settings, and live mode is **off by default** (FAIL-38 found it on by default in code).
- **Rules:** any violation raises `ConfigurationError`, and error messages never contain the value.
  - `JOBFIT_ENV` must be `dev` or `prod`, and both flags must be `0` or `1`.
  - `JOBFIT_PUBLIC_LIVE=1` requires `JOBFIT_LIVE_ENABLED=1` and `JOBFIT_ENV=prod`.
  - `prod` always requires an explicit `DATABASE_URL` that is not the development default, plus `JOBFIT_INTERNAL_TOKEN` (at least 32 characters), even when live is off.
  - Live mode requires `OPENROUTER_API_KEY`.
  - Live mode in `prod` also requires:
    - `JOBFIT_OWNER_TOKEN`;
    - `JOBFIT_USAGE_LEDGER`, which must not be the repository ledger;
    - `JOBFIT_DAILY_BUDGET_USD`, `API_BUDGET_USD` and `API_HARD_STOP_USD`, each finite and above 0, with daily cap ≤ hard stop ≤ budget.
  - Public live also requires `JOBFIT_IP_HMAC_KEY`.
  - Secrets are hidden from `repr`.
- **Two budgets, two enforcers:**
  - `API_BUDGET_USD` and `API_HARD_STOP_USD` are the lifetime ceiling of the production ledger, enforced by the frozen `BudgetGuard` through `client_settings()`.
  - `JOBFIT_DAILY_BUDGET_USD` is the D-096 calendar-day cap. Nothing enforces it yet: the Phase 2B reservation adapter will.
- **Tests:** 29 in `tests/test_production_settings.py`. `.env.example` documents the variables, all off.
- **Validation:** pytest 701 passed / 11 skipped / 0 failed; ruff clean; freeze verify `"ok": true`; CI run [37647812660](https://github.com/Gidion123/Job-Fit/actions/runs/37647812660) green.

### Deterministic phase cost bounds (commit `9286fd9`)

- **Code:** `src/jobfit/llm/phase_bounds.py`, with the CP3 assumptions in `config/cp3/phase_bounds_v1.yaml`.
- **Frozen sources (read only):**
  - from the D-087 v4 pipeline config: the models, `stage1_k` = 10, one validation repair and one length continuation;
  - prices from `config/models_v1.yaml`, with Sol and Luna priced at the request-rule ceilings in `route_rules_cp23_v1.json`, as the runtime client does;
  - the output policy (`output_allowance`, C = `MODEL_OUTPUT_LIMIT` = 131,072);
  - the prompts, guideline and schemas;
  - the CV character limit (100,000) and the frozen `extract_jd` length limit (100,000, checked at load).
- **The CP3 config holds only what has no frozen source:**
  - the parse model `deepseek-flash`. At runtime it is resolved through `config/models_v1.yaml` only. In tests only, it is checked against the frozen CP2.4 runner constant and the CP2.4 ledger rows (`deepseek/deepseek-v4.1-flash`).
  - input envelopes: 120 requirement units, 120 inventory items, 131,072 bytes of extraction JSON, 4,096 bytes per appended message, 64 characters per identifier. Phase 2B must enforce them at admission.
- **Method:**
  - **Per call:** the frozen client's own guard estimate: (message bytes + strict-schema bytes + 512) × input price + `max_tokens` × output price. Characters are padded to their worst-case escaped size.
  - **Per chain:** the frozen `validated_call` state machine. If L < C, both reachable orders are costed (L, M, M and L, L, M with M = min(2L, C)) and the larger is used. If L = C, only initial + repair (C, C) is reachable.
  - **Per job:** the Luna chain is added to the Sol chain, because the frozen `analyze_job` runs Luna only after a failed Sol chain.
  - **If a unit envelope is missing,** a 3C accounting envelope replaces the derived chain. It is labelled as not reachable, and public live becomes ineligible.
- **Result** (`bound_basis = derived`; config SHA-256 `374672a6…fd8d`):

| Bound | US$ | How it is made |
| --- | ---: | --- |
| `parse_max` | 0.4718478 | `deepseek-flash`, initial + repair at 16,000 tokens each (parse uses the non-dynamic limit, as in CP2.4); input 0.4334478, output 0.0384 |
| `embed_max` | 0.0040010 | `qwen3-embedding-8b`, 4 bytes × 100,000 characters + 100 |
| `extraction_max` | 11.9100480 | K = 10 × 1.1910048 (`deepseek-flash`, derived L = C, so C + C) |
| `matching_max` | 68.9330400 | K = 10 × 6.893304 (Sol, C + C; per chain: input 4.271864, output 2.62144) |
| `fallback_max` | 3.4466520 | K = 10 × 0.3446652 (Luna, C + C) |
| `recommendation_upper_bound` | 84.2937410 | embed + extraction + matching + fallback |
| `full_analysis_upper_bound` | **84.7655888** | parse + recommendation |
| Daily cap (D-096) | 2.0000000 | `JOBFIT_DAILY_BUDGET_USD` |
| Difference from the cap | **+82.7655888** | full bound − cap |

- **What this means:**
  - The full-analysis bound is about 42× the US$2/day cap, so `public_live_eligible()` returns false and public live stays **ineligible** under D-096 as written.
  - The bound is a deterministic worst case:
    - every character at its largest escaped size;
    - all K jobs uncached;
    - every chain failing and repaired at the maximum allowance;
    - every Sol chain followed by Luna.
  - It is not a typical or measured cost. Typical cost will be measured in CP3.4.
  - D-096, the cap, the output limits and the admission rules are **unchanged**. Dion and Codex decide the next step before Phase 2B (reservations) starts.
- **Tests:** 37 in `tests/test_phase_bounds.py`:
  - every failure script of the real `validated_call` at L < C/2, L = C/2, C/2 < L < C and L = C stays inside the modelled sequences, with at most one repair and one continuation;
  - Luna only after a Sol failure;
  - exact Decimal arithmetic, matching the frozen guard estimate;
  - fail-closed handling of a missing or invalid model, price, limit or envelope;
  - the 3C envelope is never a reachable sequence;
  - requests built by the frozen `extract_jd` and `match_evidence` at the envelope limits fit the modelled bytes;
  - the real breakdown above is pinned.
- **Validation:** pytest 738 passed / 11 skipped / 0 failed; ruff clean; freeze verify `"ok": true`; CI run [37649258348](https://github.com/Gidion123/Job-Fit/actions/runs/37649258348).
- **Still open (FAIL-38 stays OPEN):**
  - the production ledger volume;
  - enforcing the daily cap with persisted reservations;
  - the global live gate and the per-IP ticket.

All of these are Phase 2B. The Alembic migrations are design only and wait for separate approval.
