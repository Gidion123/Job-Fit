# CP3.1: API Deployment with FastAPI

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 15. Deployment API menggunakan Flask/FastAPI · official date 5 Oct 2026  
**JobFit version of this checkpoint:** FastAPI (Flask is not used).  
**Planned work:** 5 Oct 2026 · **Actual:** 6 Oct 2026  
**Status:** PARTIAL · demo-CV flow DONE LOCALLY (6 Oct); Phase 2B dark cost-safety layer DONE (8 Oct, D-101; local and CI only); persistent production ledger DONE for Phase 2 acceptance (local/CI; deployed-host validation pending Phase 8); public live path PLANNED and public live BLOCKED by the D-096 bound; scope clarified by D-102 (8 Oct) · design basis: System Design v1.3

> Plan sections are kept as written. Results are added below, with links to the [experiment log](../experiments.md). The plan for all stages is in the [master plan](../master-plan.md).

## Scope clarification (8 Oct 2026, D-102): public-beta acceptance criteria

From 8 October the remaining CP3 work follows [D-102](../decisions.md): JobFit is a production-grade AI engineering portfolio with a **controlled public beta** on one VPS, not an enterprise SaaS. For this report that means:

- **Two API flows:** Find Jobs (`cv_source` demo or upload → runtime embedding → production retrieval → matching) and Check a Job (CV + pasted JD → extraction → matching, no retrieval). The pasted JD stays a session input and is never written to the production corpus. In production, Check a Job is one `job_analysis` operation with its own bound and reservation (D-103); the public flow stays closed until the real-CV consent adapter exists.
- **Acceptance bar for the remaining rows (upload hardening, API hardening, the public path):** safe enough for controlled public use, cost bounded, privacy aware, testable, observable, maintainable, deployable and honest about residual limitations. Rare uncertain infrastructure states may end in safe refusal + logs and metrics + manual operator recovery. Enterprise availability and automatic recovery from every theoretical failure are not acceptance criteria. The completed Phase 2A, Phase 2B and persistent-ledger work is not reopened.
- **API additions planned by D-102:** stage events that drive both the progress UI and the per-stage latency metrics; refusal codes mapped to honest user-facing states ("Live AI analysis is temporarily unavailable"); the inputs for "Improve My CV for This Job" (JD requirements, CV evidence, the match and gap result) under the anti-fabrication rule.
- **Public is not admin:** no operator or administrative endpoint is reachable by public users; the owner mechanism never weakens the cap, consent or safety controls.
- **Still blocked:** public live. The cost gate is resolved by [D-103](#results-8-oct-2026-d-103-public-beta-cost-profile) (per-phase beta bounds under US$5/day); public live still needs the real-CV consent adapter, the CP3.4 privacy release gate and `public_beta_phase_eligible`.
- **Anti-overengineering correction (8 Oct):** the public-live cost/profile decision is the first unresolved governance blocker and comes before large Phase 3 work; this documentation does not lower the bound, change the frozen model, K, retrieval or scoring, or raise the cap. Upload hardening stays lean but real: PDF header/signature sanity; DOCX valid OOXML/ZIP structure with decompression limits; TXT/MD text-versus-binary sanity, decoding, size and character limits (no invented signature scheme for plain text); timeout; safe errors.

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
    - a Langfuse Cloud adapter, metadata only (D-099; required for the final beta since D-103, separate P1 task, free hosted tier);
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
- **Status:** PARTIAL. Phase 1 is done (FAIL-35 resolved). Phase 2A (fail-closed settings and phase bounds) is done and was corrected after the 8 Oct review; see "Results (7 Oct 2026, Phase 2A)" below. The full bound is above the cap, so public live is not eligible. Next: a decision by Dion and Codex, then Phase 2B. Phase 2B (the dark cost-safety runtime, D-101) is done; see "Results (8 Oct 2026, Phase 2B dark safety layer)" below. Public live stays blocked by the D-096 bound.

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

Local and CI only. Nothing is deployed, no paid call was made, and no D-087 frozen file changed (freeze verify `"ok": true`). The first version (commits `1574e31`, `9286fd9`, `0ba10d6`) was corrected on 8 Oct after an independent review by Codex; see "Correctness review (8 Oct 2026)" below. The values in this section are the corrected ones.

### Fail-closed production settings (commit `1574e31`, invariants enforced on construction in `aa33f10`)

- **Code:** `ProductionSettings`, `check_production_invariants()` and `get_production_settings()` in `src/jobfit/config.py`. `Settings` and `get_settings()` are unchanged, so CP2 scripts and runners behave as before. `live_enabled()` in `src/jobfit/api/wiring.py` now reads these settings, and live mode is **off by default** (FAIL-38 found it on by default in code).
- **One set of rules:** `check_production_invariants()` holds all of them.
  - It runs in `ProductionSettings.__post_init__`, so direct construction and `dataclasses.replace()` are validated too.
  - It runs again inside `public_live_eligible()`.
  - `get_production_settings()` only parses the environment.
  - Any violation raises `ConfigurationError`, and error messages never contain the value.
- **The rules:**
  - `JOBFIT_ENV` must be `dev` or `prod`, and both flags must be `0` or `1`.
  - `JOBFIT_PUBLIC_LIVE=1` requires `JOBFIT_LIVE_ENABLED=1` and `JOBFIT_ENV=prod`.
  - `prod` always requires an explicit `DATABASE_URL` that is not the development default, plus `JOBFIT_INTERNAL_TOKEN` (at least 32 characters), even when live is off.
  - Live mode requires `OPENROUTER_API_KEY`.
  - Live mode in `prod` also requires:
    - `JOBFIT_OWNER_TOKEN`;
    - `JOBFIT_USAGE_LEDGER`, which must not be the repository ledger;
    - `JOBFIT_DAILY_BUDGET_USD`, `API_BUDGET_USD` and `API_HARD_STOP_USD`, each a finite number above 0, with daily cap ≤ hard stop ≤ budget.
  - Public live also requires `JOBFIT_IP_HMAC_KEY`.
  - Secrets are hidden from `repr`.
- **Two budgets, two enforcers:**
  - `API_BUDGET_USD` and `API_HARD_STOP_USD` are the lifetime ceiling of the production ledger, consumed by the frozen `BudgetGuard`. `ProductionSettings.client_settings()` provides them, with the production ledger, to the frozen client.
  - **The live client is not wired to it yet.** `wiring.py` still builds the live client with `get_settings()`, which means the repository ledger and the `.env` budgets. Switching the live client to `client_settings()` is Phase 2B work.
  - `JOBFIT_DAILY_BUDGET_USD` is the D-096 calendar-day cap. Nothing enforces it yet: the Phase 2B reservation adapter will.
- **Tests:** 47 in `tests/test_production_settings.py`. `.env.example` documents the variables, all off.

### Deterministic phase cost bounds (commit `9286fd9`, corrected in `3f20f55` and `aa33f10`)

- **Code:** `src/jobfit/llm/phase_bounds.py`, with the CP3 assumptions in `config/cp3/phase_bounds_v1.yaml`.
- **Frozen sources (read only):**
  - from the D-087 v4 pipeline config: the models, `stage1_k` = 10, one validation repair and one length continuation;
  - prices from `config/models_v1.yaml`, with Sol and Luna priced at the request-rule ceilings in `route_rules_cp23_v1.json`, as the runtime client does;
  - the output policy (`output_allowance`, C = `MODEL_OUTPUT_LIMIT` = 131,072);
  - the prompts, guideline and schemas;
  - the CV character limit (100,000) and the frozen `extract_jd` length limit (100,000, checked at load);
  - the appended message texts, captured by running the frozen `validated_call` with a probe client.
- **The CP3 config holds only what has no frozen source:**
  - the parse model `deepseek-flash`. At runtime it is resolved through `config/models_v1.yaml` only. In tests only, it is checked against the frozen CP2.4 runner constant and the CP2.4 ledger rows (`deepseek/deepseek-v4.1-flash`).
  - input envelopes: 120 requirement units, 120 inventory items, 131,072 bytes of extraction JSON, 64 characters per identifier. Phase 2B must enforce them at admission.
  - `max_list_index_digits: 6` and the `appended_message_max_bytes: 8192` ceiling (see the repair-message bound below).
- **Method:**
  - **Per call:** the frozen client's own guard estimate: (message bytes + strict-schema bytes + 512) × input price + `max_tokens` × output price. Characters are padded to their worst-case escaped size.
  - **Per chain:** the frozen `validated_call` state machine. If L < C, both reachable orders are costed (L, M, M and L, L, M with M = min(2L, C)) and the larger is used. If L = C, only initial + repair (C, C) is reachable.
  - **Every reachable L is covered, in two regions** (the chain cost is the larger):
    - **`envelope`:** L from the largest admissible input. Here L = C, so the chain is C, C.
    - **`below_limit`:** every input whose L is below C. The smallest unit count that reaches `output_allowance` is 1:
      - extraction passes `max(len(inventory), 1)`;
      - matching returns before the call when there are no units;
      - unit IDs are unique.
    - So such an input has at most `T_max` estimated tokens: 43,562 for extraction and 56,478 for matching. That is the largest T where the frozen `output_allowance(task, T, 1) < C`.
    - Its request is at most 2 × the estimated payload bytes, plus the prompt.
    - It is costed at L = C − 1 with the continuation (up to 3C − 1 output tokens).
  - **Repair messages:** bounded per output model from the frozen code and the schemas:
    - at most 12 issues;
    - the longest pydantic error type;
    - a path of 2 elements per schema nesting level, each element as long as the longest property name, `<field>` or a list index of `max_list_index_digits` digits;
    - error input, context and messages never enter the message.
    - Computed bounds: 3,467 bytes for `CVWire`, 5,771 for `AuditedExtraction`, 4,091 for `EvidenceResponse`. Loading fails if any bound is above the 8,192-byte ceiling.
    - List-index digits are the one component no frozen limit bounds. So `max_list_index_digits` is an **enforced envelope, not a proof**. The Phase 2B wrapper must refuse, before the provider, any call whose exact guard input bytes (`guard_input_bytes`) exceed the modelled bytes for that attempt (`ChainSpec.attempt_input_bytes`).
  - **Inventory:** the frozen `qualification_inventory` reads each JD line once into at most one record, so quotes total at most the JD length. The envelope's quotes total exactly 100,000 characters.
  - **Per job:** the Luna chain is added to the Sol chain, because the frozen `analyze_job` runs Luna only after a failed Sol chain.
  - **If a unit envelope is missing,** a 3C accounting envelope replaces the derived chain. It is labelled as not reachable, and public live becomes ineligible.
- **Result** (`bound_basis = derived`; config SHA-256 `cc300534…0feb`):

| Bound | US$ | How it is made |
| --- | ---: | --- |
| `parse_max` | 0.4716399 | `deepseek-flash`, initial + repair at 16,000 tokens each (parse uses the non-dynamic limit, as in CP2.4); input 0.4332399, output 0.0384 |
| `embed_max` | 0.0040010 | `qwen3-embedding-8b`, 4 bytes × 100,000 characters + 100 |
| `extraction_max` | 11.9165610 | K = 10 × 1.1916561 (`deepseek-flash`; envelope region C + C) |
| `matching_max` | 68.9316600 | K = 10 × 6.893166 (Sol; envelope region C + C; input 4.271726, output 2.62144) |
| `fallback_max` | 3.4465830 | K = 10 × 0.3446583 (Luna; envelope region C + C) |
| `recommendation_upper_bound` | 84.2988050 | embed + extraction + matching + fallback |
| `full_analysis_upper_bound` | **84.7704449** | parse + recommendation |
| Daily cap (D-096) | 2.0000000 | `JOBFIT_DAILY_BUDGET_USD` |
| Difference from the cap | **+82.7704449** | full bound − cap |

The envelope region dominates every chain. The `below_limit` region, costed at its worst order (repair first: C−1, C−1, C), is:

| Chain | `below_limit` (L = C − 1) | `envelope` (L = C) | Margin |
| --- | ---: | ---: | ---: |
| Extraction | 0.7784085 (input 0.3065517, output 0.4718568) | 1.1916561 | 0.4132476 |
| Sol matching | 6.629152 (input 2.697012, output 3.93214) | 6.893166 | 0.264014 |
| Luna fallback | 0.3314576 (input 0.1348506, output 0.196607) | 0.3446583 | 0.0132007 |

- **What this means:**
  - The full-analysis bound is about 42× the US$2/day cap, so `public_live_eligible()` returns false and public live stays **ineligible** under D-096 as written.
  - `public_live_eligible()` fails closed. It is false for:
    - anything that is not a `ProductionSettings` and a `PhaseBounds`;
    - any settings object that fails the invariants, even one built without validation;
    - live off;
    - a supremum basis;
    - a negative, NaN or infinite bound.
  - The bound is a deterministic worst case:
    - every character at its largest escaped size;
    - all K jobs uncached;
    - every chain failing and repaired at the maximum allowance;
    - every Sol chain followed by Luna.
  - It is not a typical or measured cost. Typical cost will be measured in CP3.4.
  - D-096, the cap, the output limits and the admission rules are **unchanged**. Dion and Codex decide the next step before Phase 2B (reservations) starts.
- **Tests:** 76 in `tests/test_phase_bounds.py`. They cover:
  - every failure script of the real `validated_call` at L < C/2, L = C/2, C/2 < L < C and L = C;
  - **every attempt** (initial, continuation, repair, continuation-then-repair, repair-then-continuation) of the real frozen `extract_jd` and `match_evidence` (Sol and Luna), in both regions. The tests check each call's frozen guard bytes against its modelled attempt, and the summed frozen guard cost against the chain bound. The `below_limit` inputs are found by binary search, to the largest input with L = C − 1;
  - the smallest reachable unit count and `T_max` for every unit count up to 120;
  - real frozen repair messages, including an error at list index 999,999 and the longest validation code, within the computed bound, and a path element beyond the envelope exceeding the modelled attempt (what the Phase 2B wrapper refuses);
  - an inventory fuzz test against the frozen `qualification_inventory`;
  - fail-closed eligibility, using genuinely unvalidated objects (`object.__new__` and `object.__setattr__`);
  - Luna only after a Sol failure;
  - exact Decimal arithmetic;
  - fail-closed configuration;
  - the pinned breakdown above.
- **Validation:** pytest 795 passed / 11 skipped / 0 failed; ruff clean; freeze verify `"ok": true`. CI runs:
  - [37715183663](https://github.com/Gidion123/Job-Fit/actions/runs/37715183663) (`3f20f55`);
  - `aa33f10` and the docs head are recorded in the execution plan.

### Correctness review (8 Oct 2026)

Codex reviewed the first version. A read-only investigation (frozen code driven by fake clients; no provider call) gave:

| # | Finding | Verdict | Correction |
| --- | --- | --- | --- |
| 1 | The bound costed only the L derived from the maximum input; a smaller input can get L = C − 1 (a CV of 98,417 `"` characters for matching, a JD of 69,241 for extraction), where a continuation allows up to 3C − 1 output tokens | PARTIALLY CONFIRMED: the method gap was real, but the envelope region still dominates (table above) | Two-region bound over every reachable L (`3f20f55`) |
| 2 | Inventory quotes could overlap or repeat | DISPROVED: the frozen loop reads each line once into at most one record | Envelope quotes now total exactly the JD limit, instead of relying on 119 unused items' overhead (`3f20f55`) |
| 3 | Only the first attempt was tested against the bound; the 4,096-byte appended-message envelope was asserted, not proven (the conservative `AuditedExtraction` repair message is 5,771 bytes) | CONFIRMED | Every attempt tested; per-model message bounds computed from the frozen code; list-index digits made an enforced envelope (`3f20f55`) |
| 4 | `public_live_eligible()` returned True for contradictory or unvalidated settings (live off, missing secrets, hard stop below the cap, a duck-typed object, a negative bound) and raised a raw `decimal` error on a NaN cap; the report said the lifetime ceiling was enforced "through `client_settings()`" | CONFIRMED | Invariants on construction and fail-closed eligibility (`aa33f10`); the wiring status is stated truthfully above |

**Effect on the figure.** The first version reported `full_analysis_upper_bound` = US$84.7655888. The corrected bound is **US$84.7704449**, US$0.0048561 higher. The difference comes from the proven extraction repair-message bound and the exact inventory envelope; the parse and matching message bounds are slightly lower. The conclusion is unchanged.

- **Still open (FAIL-38 stays OPEN):**
  - the production ledger volume;
  - wiring the live client to `client_settings()`;
  - enforcing the daily cap with persisted reservations, and the per-call refusal above the modelled attempt;
  - the global live gate and the per-IP ticket;
  - the `AppDeps.live_enabled` default (`True` in `src/jobfit/api/main.py`; production wiring always passes `live_enabled()`).

All of these are Phase 2B. The Alembic schema they need (`budget_reservations`, `live_quota`) exists since 8 Oct ([CP3.2 report](CP3_02_Database_and_CICD.md#results-8-oct-2026-alembic-00010002)).

## Results (8 Oct 2026, Phase 2B dark safety layer)

Local and CI only, with fake SDKs: no paid call, nothing deployed, no D-087 frozen file changed (freeze verify `"ok": true`), no migration change. The decision is [D-101](../decisions.md).

**Status: dark, fail-closed safety layer DONE. Public live stays BLOCKED by the current D-096 bound** (`full_analysis_upper_bound` US$84.7704449 > US$2/day; `public_live_eligible` false). Under the real configuration a parse passes admission, but `/cv/parse` stays unwired until the Phase 3 consent adapter; a recommendation (US$84.2988050) is always refused with `budget`, owner included; `/analyze` is closed in production. No paid production path is enabled.

### What was built (commits `44f93b2`, `52ff892`, `7d0715b`, `a38db69`)

New non-frozen package `src/jobfit/live/`:

| Module | Responsibility |
| --- | --- |
| `keys.py` | 64-bit advisory keys (live gate, budget lock, per-operation owner lock); `idem:` + canonical UUIDv4 operation keys |
| `deadlines.py` | Per-call wall W (frozen timeout + 30 s) and the operation horizon from the reachable Phase 2A call model: parse 660 s (window 720 s), recommendation 24,990 s (window 25,050 s) |
| `budget_store.py` | Admission under the budget lock: duplicate key, **any open reservation refuses** (persisted gate backstop), untrusted evidence, the daily cap with cross-midnight carry-over, the lifetime hard stop (recorded spend + open liability + new bound); settlement and release; unknown COMMIT outcomes reported, never guessed |
| `evidence.py` | Durable intent journal, correlated production ledger (frozen format + `operation_key` + `attempt_id`, short synchronized I/O), breach marker, per-attempt settlement |
| `reserved_client.py` | The D-097 concurrency-safe client: one frozen `RuntimeClient` per operation with only that instance's `guard` and `ledger` rebound; calls go straight to the frozen `_chat_attempt`/`_embed_attempt` (no whole-call lock: FAIL-36), are checked against the modelled attempt, the phase and the horizon, and carry a call-scoped attempt context; fatal, sticky `RuntimeError` refusals |
| `operation.py` | The runner: phase-scoped gate, preflight, reconciliation of expired unowned rows, owner lock, admission, watchdog, drain, settlement; the idempotency registry |
| `quota.py` | The per-IP ticket (one conditional upsert, 48 h retention), IP HMAC (IPv6 by /64), constant-time token checks, the session rate limit (10 new sessions per IP pseudonym per hour, in memory) |

API (`src/jobfit/api/main.py`, `wiring.py`) and UI client:
- in `prod`, every route but `/health` needs the internal service token; the client IP is accepted only with it; `POST /session` is rate-limited;
- a live recommendation needs an `Idempotency-Key`: a retry gets the same run, another session or phase gets 409;
- the owner token bypasses only the ticket; non-owner live needs public live and the parse ticket, so it is refused for now;
- `prod` live runs only through the runtime with `ProductionSettings.client_settings()` (production ledger and lifetime budgets); `dev` keeps the CP2 behaviour;
- `AppDeps.live_enabled` now defaults to off;
- the UI client sends the internal token and one key per user action. It **supports** forwarding a client IP, but nothing populates it yet: acquiring the IP (the Caddy header, Streamlit access to it) is a deployment prerequisite.

### Evidence and settlement rules

- No provider call without a durable intent; an attempt is in flight only once its intent is durable and is closed exactly once.
- A ledger line wins over its intent (no double counting). An intent with no line counts its upper bound and is uncertain. Released only with zero spend, nothing uncertain and every intent ledgered; otherwise settled. A provider exception never leads to a release.
- Duplicate, orphan, unattributed, torn or corrupt evidence fails closed: no settlement, no admission.
- A reported cost above the intent's upper bound is kept (never clamped), settled at full value, and writes the breach marker.

### Test results

- **Offline** (every CI run): `tests/test_live_unit.py` (38: keys, derived windows, correlation under out-of-order concurrent completion, serial and concurrent outputs identical, request kwargs byte-identical to the frozen path, sticky fatal refusals including the frozen Luna fallback refused with 0 SDK calls after a Sol intent failure, corrupt-ledger normalization with no validation repair, quota outcomes, horizon, phase and model refusals, ledger-write and `done` failures, the evidence rules, synchronized I/O under concurrent reads), `tests/test_live_api.py` (16: ingress, rate limit, IP pseudonyms, owner-only dark live, idempotency, closed `/analyze`, prod wiring with no development fallback) and one UI-client test.
- **Database-gated** (CI `db-migrations` job): `tests/test_live_db.py` (22: real bounds admit parse and refuse recommendation at US$2, inclusive cap boundary, the open-row backstop, global key conflicts, lifetime formula, carry-over, admission time after the lock, settlement, concurrency, the ticket, ambiguous commits) and `tests/test_live_runtime_db.py` (12: the runner end to end, the gate between operations, a lost coordinator never letting a second operation overlap, the watchdog, an unwritable breach marker, restart idempotency, ambiguous admission and settlement commits).
- **Local totals:** default suite 865 passed, 122 skipped (the gated tests), 0 failed; gated matrix 126 passed on PostgreSQL 16.15 (92 migration + 34 live); ruff clean; freeze verify `"ok": true`.

### Manual review of a breach marker

A breach marker (`<JOBFIT_USAGE_LEDGER>.breach.jsonl`), an unreadable or corrupt ledger or journal, or a `reserved` row that cannot be reconciled stops all live admission. Clearing it is a manual, recorded procedure:
1. Keep the app running in its dark state (no admission happens anyway). Copy the ledger, the intent journal and the breach file aside, read-only.
2. Read the breach rows (reason, operation key, attempt id) and the matching ledger lines and intents. Compare the reported cost with the OpenRouter production-key activity for that request.
3. Settle every affected open reservation from that evidence only (`jobfit.live.budget_store.close` in a reviewed one-off session; never release unless zero spend is proven), and record the case in `docs/failures.md`. An expired reservation with no evidence at all (kept `reserved` by the reconciler since the persistent-ledger change) is closed conservatively at its `reserved_usd` unless zero spend is proven from the provider's activity.
4. Never edit or truncate the authoritative ledger. A torn final line is moved to a separate quarantine file only after step 2, with its hash recorded.
5. Move the breach file aside (renamed with the date) only after the review is recorded. Admission resumes on its own once no breach file exists and the evidence parses.

### Audit corrections (8 Oct 2026, after the independent audit of `3223b16..1f76ad7`)

The audit returned TARGETED REVISION REQUIRED. The architecture, cap, bounds and D-101 design are unchanged; these gaps were closed (commits `6c04247`, `b1efa4d`, `e9faf12`, `1f856dd`):

- **48 h quota retention (D-096).** The purge ran in the same transaction as the ticket consume, so a clean refusal rolled it back. It now has its own committed lifecycle: a separate committed purge before every consume (a purge failure fails the ticket closed), a startup purge, and an hourly purge from the API sweeper (failures are logged and retried, and never stop session expiry).
- **UI idempotency.** Streamlit made a new key on every click. A pending live-action key now stays in the Streamlit session until the server acknowledges the action with a run id, so a retry after a lost response reuses it and the action runs once. The fingerprint is an opaque SHA-256 of the demo CV id, the seniority switch and the canonical filters, never CV content.
- **D-097 acceptance.** A new test runs the frozen `recommend()` (the frozen `match_evidence`, `validated_call`, Sol then Luna, scoring and product order) twice on a deterministic fake SDK: serialized through the frozen client and concurrently through the reserved client. The `Recommendation` objects are equal, including scored, held and fallback jobs; calls overlap only in the concurrent run.
- **One recommendation per ticket (D-096).** A session allowance follows `no_ticket → ticket_held → pending(op) → used(op)`:
  - the Phase 3 parse will mark `ticket_held`;
  - a non-owner recommendation claims `pending(op)` after its idempotency claim; a retry of the same action never claims again;
  - the claim becomes `used(op)` only at the first durable provider intent, through a callback attempted exactly once before the attempt opens. A failed finalize is a sticky `allowance_finalize_failed` refusal with no SDK call;
  - a busy, budget, run-limit or other pre-billing stop returns `pending(op)` to `ticket_held`; session delete and expiry drop the state;
  - the owner never touches the allowance.
- **Accepted operational constants:** 10 new sessions per IP pseudonym per hour (provisional MVP default), the hourly quota purge and the startup purge.
- **Tests now:** `tests/test_live_unit.py` 48, `tests/test_live_api.py` 26, `tests/test_live_recommend_equivalence.py` 1, `tests/test_ui_client.py` 9, `tests/test_live_db.py` 25, `tests/test_live_runtime_db.py` 13. Default suite 890 passed, 126 skipped (the gated tests), 0 failed; gated matrix 130 passed on PostgreSQL 16.15 (92 migration + 38 live); ruff clean; freeze verify `"ok": true`.
- **Deployment prerequisites (not part of Phase 2B code):** the persistent production ledger volume (its storage contract was later closed for Phase 2 acceptance at `f5d6cf7`; mounting it on the deployed host remains); acquiring the client IP (the Caddy header and Streamlit access to it). Phase 2B is not declared closed; that follows the independent correction audit.

### Findings and not done yet

- **Finding:** the frozen `RuntimeClient` adapter has no `embeddings` endpoint, so the Phase 3 runtime query embedding must wrap the base frozen `OpenRouterClient` (as the embedding test does).
- The production ledger volume (FAIL-38): closed for Phase 2 acceptance (local/CI) at `f5d6cf7` (see the next section); the production compose volume is Phase 6 and deployed-host persistence validation is Phase 8.
- The Caddy header and the Streamlit header access are deployment details: client-IP provenance is not claimed end to end until the deployed Caddy validation passes.
- The public parse (consent adapter), runtime embedding, the extraction cache and live latency measurement are Phase 3 and CP3.4 work. The idempotency registry and the session rate limit are in memory (one API process).

## Results (8 Oct 2026, persistent production ledger storage)

Local and CI only, fake SDKs: no paid call, nothing deployed, no D-087 frozen file changed (freeze verify `"ok": true`), no migration, `models.py` unchanged. Production live and public live stay off; public live stays blocked by the D-096 bound. Plan revision 7 was independently accepted before implementation; the decision text is the D-101 addition "persistent production ledger storage".

**Status: DONE for Phase 2 acceptance (local/CI); deployed host persistence validation pending Phase 8.** Independently verified and closed on 8 Oct 2026 at final HEAD `f5d6cf76cd588623b88d322a0dd5371f52d51b19` (audit range `9dc8ac8..f5d6cf7`).
- Implementation: commits `2cfd087`, `a9c6020`, `66b166c`, `39f74a8`, `f5d6cf7`.
- CI green: run [37759368396](https://github.com/Gidion123/Job-Fit/actions/runs/37759368396) (lint-and-test, db-migrations, docker-build including the named-volume smoke).
- Crash/restart evidence: the deterministic application-level R1-R7 matrix and the storage-continuity tests passed (gated suite 194 passed locally on PostgreSQL 16.15 and in CI on pg17); offline suite 936 passed, 190 skipped.
- Named-volume persistence: the CI `docker-build` smoke passed (same `storage_id` after container replacement, intent line survived, a container without the volume is unprovisioned).
- D-087 freeze intact (`"ok": true`); no migration; `models.py` unchanged; no paid call.
- Production live and public live stay off; public live stays blocked by the D-096 bound.
- **Still open:** persistence on a deployed host is a Phase 8 obligation; the production compose service, Caddy, restart policy, logging, healthcheck packaging and backup/restore packaging stay Phase 6.
- The residual limitations below stay documented and accepted.

### Storage contract

| Item | Rule |
| --- | --- |
| Root | `/var/lib/jobfit/ledger` (`config.PROD_LEDGER_ROOT`); prod live requires `JOBFIT_USAGE_LEDGER` absolute (checked before any `resolve()`, in the parser and in the invariant layer) and directly in that root; a symlinked root that resolves elsewhere fails. No new environment variable. |
| Co-location | The ledger, `<ledger>.intents.jsonl`, `<ledger>.breach.jsonl`, `.lock` files and `.io.lock` are all in the root. |
| Provisioning | `python -m jobfit.live.storage init --ledger /var/lib/jobfit/ledger/usage_ledger.jsonl` writes the marker `.jobfit-ledger-storage.json` (`format` 1, uuid4 `storage_id`, ledger name) with `O_EXCL` and fsync; it never creates directories and refuses an existing marker or unmarked existing evidence. `check` prints the `storage_id`. The image has no marker. |
| Validation | Root exists → marker strictly valid → co-located → write probe (create, fsync, unlink). Reasons: `missing_directory`, `missing_marker`, `invalid_marker`, `ledger_name_mismatch`, `not_writable` (logs only). |
| No implicit mkdir | `append_durable()` and `FileLock.hold()` no longer create directories. (The frozen `UsageLedger` mkdir sites are unreachable in live.) |
| Image | `Dockerfile.api` creates `/var/lib/jobfit/ledger` (owner `jobfit`, mode 700, no marker) and declares it a `VOLUME`. |
| Startup | The app always starts; `/health` reports `live_storage_ready` (true/false; null when live is off); the saved demo works with invalid storage; startup reconciliation runs only on valid storage. |
| Live operation | Preflight validation (`ledger_storage_unavailable`, 503, nothing reserved, no ticket); revalidation immediately before admission (`ledger_storage_mismatch` if the id changed, before any insert); `process_id` = `<storage_id>:<pid>`. |
| Every attempt | After the durable intent and the first-intent allowance finalize, before the SDK: the current storage must still be the admitted one, else sticky `ledger_storage_unavailable` / `ledger_storage_mismatch` with no SDK call for this and every later attempt; the independent `storage_continuity_failed` flag makes the runner skip settlement (row stays `reserved`) and registers the operation in the process-local `settlement_blocked` set. |
| Settlement | Blocked check → current storage → reservation binding → evidence → storage again → close; any failure leaves the row `reserved`. |
| Reconciliation | Only on valid storage with trustworthy global evidence; never releases an expired reservation without evidence. `reconcile(at=)` / `expired_open(at=)` are test seams (None = database clock). |
| Admission | `duplicate_operation` → `ledger_storage_mismatch` → `busy` → `evidence_fail_closed` (including settled history above recorded spend) → `budget` → `lifetime`, with one `recorded_spend()` snapshot per transaction. |
| DB witness | Closed reservation rows are never purged by code; a purge needs an approved durable lifetime watermark first. |

### Crash and restart matrix (verified)

| ID | Scenario (subprocess worker killed with SIGKILL at a flushed barrier; fresh runtime over the same root) | Result |
| --- | --- | --- |
| R1 | Completed operation, worker exited | Marker unchanged; 1 intent and 1 ledger line visible; `recorded_spend()` = settled US$0.01; a same-key replay is `duplicate_operation` with 0 SDK calls; with a test hard stop of c + parse bound − 1e-10 a new admission is refused `lifetime`, while the same limit on an empty root and database admits |
| R2 | Killed inside the provider call (exactly one durable intent, no ledger line, checked before and after the kill) | Before expiry `busy`; `reconcile(at=active_until+1s)` settles at exactly the intent's upper bound, never releases; 0 SDK calls during recovery; the next operation runs once |
| R2b | Killed after admission, before any client call (zero intents before and after); and evidence deleted while the marker survives | Reconciliation defers twice; row stays `reserved` with `settled_usd` NULL; admission `busy` |
| R3 | Breach marker after restart | `evidence_fail_closed`; reconciliation closes nothing |
| R4 | Torn ledger tail / corrupt intent line / unattributed ledger line | `evidence_fail_closed`; reconciliation closes nothing |
| R5a1 | Ledger line lost, intent and marker kept | `recorded_spend()` = upper bound U ≥ actual c (no downward reset); C7(b) does not fire; a hard stop that c would fit and U would not refuses `lifetime` |
| R5a2 | Ledger line and intent lost, marker and settled DB row kept | `evidence_fail_closed` from the database witness, before budget and lifetime |
| R5b | Root re-initialized (new `storage_id`) with an open old-storage row; bare or malformed `process_id` rows | `ledger_storage_mismatch` before `busy`; the old row stays `reserved` |
| R6 | Marker deleted / root removed / probe failure | `ledger_storage_unavailable`; reconciliation touches nothing; a removed root is not recreated |
| R7 | Development ledger, relative path, `/tmp`, in-repository path | `ConfigurationError` before any runtime exists |

Storage-continuity tests (real PostgreSQL): a swap between preflight and admission refuses with 0 rows; a swap before the first attempt leaves one intent, 0 SDK calls, the allowance finalized once, the row `reserved`; a swap between attempts stops every later attempt including the frozen repair; a lost marker before an attempt is `ledger_storage_unavailable`; a lost root fails the frozen lifetime check's ledger read first (`evidence_fail_closed`) with no intent written; restoring the original storage before settlement never settles or releases the operation, in the runner or in same-process reconciliation, also when another fatal reason won the first slot; a swap after preflight without any attempt failure defers settlement (four variants, including a swap between the evidence read and the bracket check). Offline: the check runs once per attempt with identical results on stable storage; concurrent attempts after a failure make no SDK call; the frozen Luna fallback and repair stay blocked; a bounded 21-thread `fail_storage`/`set_fatal`/`wait_drained` regression shows no deadlock and first-fatal-wins.

### Docker named-volume smoke (CI `docker-build`)

A named volume is provisioned with `init` in one container; a second container appends an intent line and is removed; a third, new container's `check` prints the same `storage_id` and reads the intent back; a container without the volume reports `missing_marker`. This proves survival across container replacement on a named volume only.

### Tests and totals

`tests/test_live_storage.py` 23 (new), `tests/test_production_settings.py` 57 (+10), `tests/test_live_unit.py` 58 (+10), `tests/test_live_api.py` 29 (+3), `tests/test_live_db.py` 51 (+26), `tests/test_live_runtime_db.py` 30 (+17), `tests/test_live_restart_db.py` 21 (new) with the worker `tests/live_restart_worker.py`. Default suite 936 passed, 190 skipped (the gated tests), 0 failed; gated matrix 194 passed on PostgreSQL 16.15 (92 migration + 102 live); ruff clean; freeze verify `"ok": true`.

### Residual limitations (accepted)

- With the current ledger and journal format there is no independent durable attempt count: a clean removal of one matching intent-and-ledger pair from an open crashed operation, while other valid evidence and the same marker remain, is not detectable from the remaining files.
- `settlement_blocked` is process-local: if the process crashes after detecting a temporary storage swap and the original storage is restored before the restart, nothing durable records the mismatch.
- An expired reservation with no evidence blocks all live admission (`busy`) until an operator closes it (manual review above). This is deliberate.
- These are outside the Phase 2 guarantee (accidental volume loss and misconfiguration). Phase 6 backup and restore must treat the PostgreSQL database and the entire ledger root as one recovery set.

## Results (8 Oct 2026, D-103 public-beta cost profile)

[D-103](../decisions.md#d-103-controlled-public-beta-cost-profile-amends-d-096-for-the-public-beta) was implemented dark in three commits (local and CI, fake SDKs only, zero provider calls): `5d07b0c` (bounds), `c3a718e` (runtime and quota), `40ed823` (API contract). Production and public live stay off; nothing is deployed.

### Exact public-beta bounds (`config/cp3/public_beta_bounds_v1.yaml`, `cp3-public-beta-bounds-v1`)

| Item | Bound (US$) | Dominant region | Notes |
| --- | --- | --- | --- |
| `parse` | 0.0614679 | fixed limit | CV ≤ 16,384 canonical bytes |
| `search` | 0.0001648 | — | one Qwen3 embedding of ≤ 16,380 + 100 guard bytes |
| extraction | 0.4141854 | envelope (initial allowance 55,878) | JD ≤ 16,384 bytes, inventory ≤ 32 |
| matching (Sol) | 3.416284 | envelope (initial allowance 55,271) | extraction ≤ 24,576 bytes, ≤ 48 units |
| fallback (Luna) | 0.1708142 | envelope (initial allowance 55,271) | same request as Sol |
| **`job_analysis`** | **4.0012836** | | extraction + matching + fallback |
| Phase 2A full analysis | 84.7704449 | | historical, unchanged |

Config sha256 `ccb1254a92147a26e0392e4394cd9a59824bda0b7a7e1a3fb2ef609d424335a3`. Every beta phase fits the US$5 cap; `job_analysis` does not fit US$2. The legacy `public_live_eligible()` is still false at US$2 and US$5.

**Envelope coverage (reported, not tuned).** 637/637 corpus JDs fit the JD envelope (bytes and ≤ 32 inventory items) and 47/47 matchable saved extractions fit the extraction envelope. Provenance: the 637 are every `role_group == 'target'` row (all with a non-empty `description_clean`) of the CP2 snapshot `data/processed/jobs_features.jsonl` (910 rows, all splits; the development split holds 214 of them). This is not the seeded production corpus (632 rows, 428 active target-role jobs, CP3.2) and not the D-091 extraction scope. The 47 are the matchable records (status `done` and `jd_quality` `ok`, the frozen `extraction_from_record` rule) among the 51 saved extraction records that `load_record` finds for those rows (48 `done`, 3 `failed`; one `done` record is not `ok`).

### Runtime and API (what was built)

- **Canonical bytes:** `jobfit.llm.document_bytes` is proven equal to the frozen `validated_call` → `OpenRouterClient` measure (ASCII, multibyte, CJK, emoji, quotes, backslashes, control characters, mixed), and the guard's recorded upper cost uses that number. A CV, JD and extraction exactly at their envelopes fit the modelled parse, extraction, Sol and Luna attempts through the real frozen `parse_cv`, `extract_jd` and `match_evidence`; one byte more is refused.
- **Runtime:** `LiveRuntime` with `PublicBetaBounds` admits `parse`, `search` and `job_analysis` with their own windows (search 90 s of calls + 60 s; job_analysis 9 × W(chat) + 120 s) and call model; `recommendation` is refused `phase_not_admitted` before any connection.
- **Reservation labels:** one mapping keeps the unchanged `0002` CHECK constraint: `search` and `job_analysis` are stored as `recommendation`, at their exact beta bound; the real phase is in the intents, the ledger, the report and the admission log.
- **Envelopes:** refused before reservation (`input_too_large`); an extraction above its envelope is held (`beta_envelope_exceeded`) with 0 Sol and 0 Luna calls and the extraction settled from evidence.
- **Session allowance:** created only on a proven `consumed` ticket; `refused`, `unavailable`, `unknown` (and an exception) create none and stop the call before the SDK; then 1 parse, 1 search, ≤ 3 job analyses; refusals before the first intent never count; a restart gives no second durable ticket.
- **API contract (no Streamlit change):** `POST /jobs/search` (stage `retrieval`, `final_order: false`, `analyzed: false`, `match_score: null`), `POST /jobs/{job_id}/analyze` and production `POST /analyze` (one `job_analysis`, stage `analyzed`, `match_score` only when scored). In production these routes are owner-only (non-owners get 503) until the real-CV consent adapter exists; the owner bypasses only the ticket and the allowance. Production wiring builds the runtime with the beta bounds.

### Tests and totals

`tests/test_public_beta_bounds.py` 47, `tests/test_public_beta_runtime.py` 43, `tests/test_public_beta_runtime_db.py` 9 (real PostgreSQL), `tests/test_public_beta_api.py` 13; `tests/test_live_api.py` 29 (the production-wiring assertion now checks the beta phases). Default suite 1039 passed, 199 skipped (the gated tests), 0 failed; the full gated run 1227 passed, 11 skipped, 0 failed on PostgreSQL 16.15; ruff clean; freeze verify `"ok": true`. No change to D-087 frozen files, migrations, `src/jobfit/db/models.py`, `config/cp3/phase_bounds_v1.yaml` or `src/jobfit/llm/phase_bounds.py`.

### Not done (by design)

- The real-CV public path (consent adapter, `cv_source`, runtime query embedding, production retriever) is not built: public Find Jobs and Check a Job stay closed. The `search` phase is exercised by tests; the demo-CV search uses cached query embeddings and makes no provider call.
- No real-provider validation: any live check of the bounds needs its own approved validation step and budget.
- Langfuse (required for the final beta since D-103) is a separate P1 task.
