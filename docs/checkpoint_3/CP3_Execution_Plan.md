# CP3 Execution Plan (Daily Checklist)

**Created:** 7 Oct 2026 (Phase 0, documentation and plan freeze) · **Decisions:** [D-095 to D-102](../decisions.md) · **Scope clarified:** 8 Oct 2026 by D-102 (portfolio / controlled public beta)

What each document is for:
- The [master plan](../master-plan.md) is the source of truth for what each CP3 stage must achieve.
- This file is the working checklist.
- The CP3.1-CP3.7 reports hold the evidence and results.
- The [decision log](../decisions.md) explains why things were chosen.
- The [failure log](../failures.md) records known defects.

**Status values:** TODO, IN PROGRESS, DONE (only once the validation in the row has passed, with linked evidence), BLOCKED.

**Priorities:**
- **P0:** before public deployment.
- **P1:** before the feature freeze and public validation.
- **P2:** before the final report.
- **P3:** not before the presentation.
- **P2 (post-beta):** an optional enhancement after the controlled public beta (8 Oct anti-overengineering correction under D-102); never a beta or final-report blocker. Plain P2 rows stay required before the final report.

**Timeline:**
- 8 Oct: core engineering and the dark deployment.
- 9 Oct: deployed validation, the privacy release gate, public-live enablement, PR-10 and the formal feature freeze (end of day).
- 10 Oct: reports, deck, video and rehearsal.
- 11 Oct: presentation.

**Budgets:** CP3 validation US$5 in total. Production US$2/day.

## CP3 scope (D-102): production-grade AI engineering portfolio with a controlled public beta

- **North star:** JobFit shows end-to-end AI engineering on a real VPS that real public users can try in a limited, controlled way. It should behave like a small real product. It is not an enterprise SaaS.
- **Two first-class flows:** **Find Jobs** (CV → runtime embedding → production retrieval → extraction → evidence matching → scoring → explanation → optional CV improvement) and **Check a Job** (CV + pasted JD → extraction → evidence matching → scoring → explanation → CV improvement; no retrieval). A pasted JD is never ingested into the production corpus.
- **New product requirements:** stage-aware analysis progress driven by real pipeline stages (no fake percentages); "Improve My CV for This Job" with the hard anti-fabrication rule (representation improvement, possibly missing, true gap); a portfolio-ready UI (landing, public-beta wording, Find Jobs / Check a Job, job cards, strengths, gaps, evidence, empty, failure, unavailable and budget-exhausted states). Priority: clarity > trust > usability > polish > decoration.
- **Priority filter:** about 70% AI and product value, 30% infrastructure. "Does this materially improve the AI product or show AI-engineer competence?" Essential safety is never cut.
- **Public-beta acceptance bar:** safe enough for controlled public use, cost bounded, privacy aware, testable, observable, maintainable, understandable, deployable, honest about limits. Not required: perfect automatic recovery, enterprise availability, massive scale.
- **Failure philosophy and complexity budget:** unknown → fail closed → log or metric → manual operator review. A new reliability subsystem is added only when the D-102 seven-question check shows that fail closed + observability + documented manual recovery is not enough.
- **Public is not admin:** public users reach only the end-user app. SSH, Docker, PostgreSQL, secrets, deploy and restart controls, budget and gate configuration, operator recovery, admin endpoints, private logs and Grafana stay private (D-095 network boundary).
- **Open gates (each needs its own decision; D-102 resolves none of them):** the public-live cost bound (US$84.7704449 > US$2/day, D-096); Flow B in production (D-101 keeps `/analyze` closed until a pasted-JD bound and reservation exist); any LLM-generated CV wording (own bound, reservation and anti-fabrication evaluation); the D-100 dates, which are unchanged.

### Remaining work in recommended order (D-102; anti-overengineering correction 8 Oct)

Completed rows below keep their status and evidence. The remaining rows are worked in this order; the phase numbers are unchanged. Only what the single-VPS controlled public beta needs is a blocker; the rest is **P2 (post-beta)**.

| Step | Goal | Rows (phase) |
| --- | --- | --- |
| 1 | Foundation closeout | Persistent ledger (DONE); lean upload hardening; API hardening; Phase 2 closeout (Phase 2) |
| 2 | **Public-live cost/profile decision** (first unresolved governance blocker) | Dion and Codex decide how a real-user live flow fits the US$2/day cap; `full_analysis_upper_bound` is US$84.7704449. Nothing is lowered, changed or raised in this correction (Phase 3, first row) |
| 3 | Real-user AI path | FAIL-37 masking; consent adapter; `cv_source` contract; runtime embedding; production retriever; extraction cache; Flow B pasted JD (Phase 3) |
| 4 | Product UX | Upload flow UI, landing, Find Jobs / Check a Job, stage-aware progress, results, public-beta states, deterministic "Improve My CV for This Job" (Phases 3 and 3b) |
| 5 | Lean production packaging | Compose, Caddy, artifact manifest, a verified backup with a successful restore test, runbook, private admin interfaces (Phase 6) |
| 6 | Lean monitoring | Structured logs, `/metrics`, Prometheus, Grafana with application, AI-pipeline, LLM and cost, and basic VPS health (Phase 5) |
| 7 | Dark VPS deploy | VPS provisioning, first dark deploy, real-host persistence (Phases 7-8) |
| 8 | Privacy, quality and cost validation | Per-route privacy record, privacy release gate, owner live runs with latency and cost, PR-10, D-045 option B (Phases 7-8 and 9-11) |
| 9 | Controlled public beta | Enable public live if its gates pass; limited trial (Phases 7-8) |
| 10 | Final portfolio and reporting | Feature freeze, reports, README, deck, video, rehearsal, presentation (Phases 9-11) |

**Explicitly post-beta (P2 (post-beta)):** the automated twice-monthly job sync, the forced-command SSH user and scheduled `job-sync.yml`, dedupe-review automation (the D-098 design stays documented; the seeded production corpus is enough for the CP3 beta, and a one-time manual refresh may be run before the demo if needed); the Langfuse adapter; Grafana email alerts and dashboards beyond the one beta dashboard; automated nightly backup scheduling (unless trivial); LLM-written CV rewriting (deferred until a separate decision with a cost bound and an anti-fabrication evaluation).

## Phase 0. Documentation and plan freeze (7 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Update master plan, decisions D-095 to D-100, FAIL-36 to 38, CP3 reports, privacy model, coach plan, production corpus, indexes | P0 | Plan acceptance | Dion (AI-assisted) | DONE | *Phase 0 validation recorded at `aa2deed`:* docs-only diff (20 files); freeze verify `"ok": true`; pytest 671 passed / 9 skipped / 3 failed (exactly the known FAIL-35 baseline). *Closeout-patch validation:* link and anchor check over all of `docs/` + `README.md` (0 broken); `git diff --check` clean; docs-only diff; freeze verify `"ok": true` | Commit `aa2deed` |
| D-045 option B: select unseen blind candidates by job ID only (no inference, no model output) | P2 | — | Dion (AI-assisted) | DONE (selection only) | Absent from workbook, CP2.4 outputs, test gold, pools and other tracked files | [CP3.5 report](CP3_05_Final_Presentation_and_Portfolio.md) |

## Phase 1. Baseline green (7 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Re-apply the FAIL-35 test fix cleanly (no merge of the old branch, no attribution trailers) | P0 | Phase 0 review | Dion (AI-assisted) | DONE | Offline pytest 672 passed / 11 skipped / 0 failed (683 tests); GitHub Actions green | Commit `33c5584`; CI run [37641393567](https://github.com/Gidion123/Job-Fit/actions/runs/37641393567) (lint-and-test and docker-build both succeeded) |
| Pyflakes `F` fixes in `src/` and `ui/`, then add `F` to CI | P1 | FAIL-35 | Dion (AI-assisted) | DONE | `ruff check --select F src ui` clean; 6 issues fixed in non-frozen files; 2 F401 in D-087 frozen files exempted in `pyproject.toml`; ruff pinned to 0.16.8 | Commit `33c5584`; CI run [37641393567](https://github.com/Gidion123/Job-Fit/actions/runs/37641393567) |
| Freeze verify in CI | P1 | — | Dion (AI-assisted) | DONE | `"ok": true` locally and in CI | Commit `33c5584`; CI run [37641393567](https://github.com/Gidion123/Job-Fit/actions/runs/37641393567) |

## Phase 2. P0 production hardening (8 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Fail-closed settings (live and public live off by default; `JOBFIT_*` settings) | P0 | Phase 1 | Dion (AI-assisted) | DONE (Phase 2A; corrected 8 Oct) | 47 settings tests (`tests/test_production_settings.py`): the invariants are enforced on every construction, including `dataclasses.replace()`; pytest 795 passed / 11 skipped / 0 failed; ruff clean; freeze verify `"ok": true`. The live client is not yet wired to `client_settings()` (Phase 2B) | Commits `1574e31` and `aa33f10`; CI runs [37647812660](https://github.com/Gidion123/Job-Fit/actions/runs/37647812660) and [37715359289](https://github.com/Gidion123/Job-Fit/actions/runs/37715359289); [CP3.1 report](CP3_01_FastAPI_Service.md#results-7-oct-2026-phase-2a) |
| Alembic `0001` baseline and `0002` production schema (lifecycle, `dedupe_status`, `job_sources` unique on source and source id, `sync_runs`, extraction cache, quota, reservations) | P0 | Phase 1 | Dion (AI-assisted) | DONE; implementation independently verified and closed at `ac30594` (8 Oct; schema only, nothing deployed; Dion's local CP2 database not yet verified) | Up on an empty database and on a CP2-shaped database (verify, then stamp, then upgrade); 15 mismatch cases never stamped; guarded down and up; frozen retrieval unchanged on `0002`. Audit corrections (8 Oct): persisted `active_until`, `production_day` bound to `created_at`, race-safe guarded stamp, strict `0001` fresh guard; `0001` trusts a pre-existing `alembic_version` only by exact structure. 77 database tests on PostgreSQL 16.15 locally and 17.11 in CI, plus 15 offline tests (92 in CI run 37729333801; Docker `alembic heads` = `0002 (head)`); pytest 810 passed / 88 skipped / 0 failed; freeze verify `"ok": true`. Still to do: `verify` on Dion's local CP2 database before any seed | Commits `c5a4100`, `eb8afa5`, `8a89a4c`, `fc9d236`, `a04a629`, `4f45cd4`, `801f0bd`, `ac30594`; CI runs [37729333801](https://github.com/Gidion123/Job-Fit/actions/runs/37729333801), [37727182136](https://github.com/Gidion123/Job-Fit/actions/runs/37727182136), [37720133032](https://github.com/Gidion123/Job-Fit/actions/runs/37720133032) and [37720321946](https://github.com/Gidion123/Job-Fit/actions/runs/37720321946) (pg17 migration job: 67 passed); [CP3.2 report](CP3_02_Database_and_CICD.md#results-8-oct-2026-alembic-00010002) |
| Deterministic phase bounds (`parse_max`, `recommendation_upper_bound`, `full_analysis_upper_bound`) from versioned config | P0 | Settings | Dion (AI-assisted) | DONE (Phase 2A; corrected 8 Oct; the bound is above the cap, see below) | 76 bound tests (`tests/test_phase_bounds.py`): every reachable L in two regions; every attempt of the real frozen `extract_jd` and `match_evidence` within its modelled bytes and the summed guard cost within the chain bound; computed repair-message bounds; exact values; missing data fails closed; fail-closed eligibility; pytest 795 passed / 11 skipped / 0 failed; ruff clean; freeze verify `"ok": true` | Commits `9286fd9`, `3f20f55` and `aa33f10`; CI runs [37649258348](https://github.com/Gidion123/Job-Fit/actions/runs/37649258348), [37715183663](https://github.com/Gidion123/Job-Fit/actions/runs/37715183663) and [37715359289](https://github.com/Gidion123/Job-Fit/actions/runs/37715359289); [CP3.1 report](CP3_01_FastAPI_Service.md#results-7-oct-2026-phase-2a) |
| Concurrency-safe app client with separate parse and recommendation reservations (F2, FAIL-36) | P0 | Phase bounds | Dion (AI-assisted) | DONE (8 Oct, dark, D-101; local and CI, fake SDK only) | Serial and concurrent outputs identical; no call without a reservation; embedding only in the recommendation reservation; settled plus outstanding never above the cap; one ledger line per call; settlement only after the durable ledger record; settled whenever the ledger shows spend or an uncertain record, released only with zero; outstanding from the persisted `active_until`; per-call refusal above the modelled attempt; the four crash tests ([CP3.2 report](CP3_02_Database_and_CICD.md#recorded-for-phase-2b-implemented-8-oct-d-101)) | CP3.1 report |
| Persistent production ledger volume | P0 | — | Dion (AI-assisted) | DONE for Phase 2 acceptance (local/CI); deployed host persistence validation pending Phase 8 (independently verified and closed 8 Oct at `f5d6cf7`) | Crash-recovery test: deterministic application-level restart matrix R1-R7 on real PostgreSQL (`tests/test_live_restart_db.py`, SIGKILLed worker) and the storage-continuity tests passed (gated suite 194 passed); offline suite 936 passed, 190 skipped; CI Docker named-volume smoke passed (same `storage_id` after container replacement); freeze verify `"ok": true`; no migration or `models.py` change; production and public live stay off. Deployed-host persistence is a Phase 8 obligation; production compose and backup/restore packaging are Phase 6 | Commits `2cfd087`, `a9c6020`, `66b166c`, `39f74a8`, `f5d6cf7`; CI run [37759368396](https://github.com/Gidion123/Job-Fit/actions/runs/37759368396) (lint-and-test, db-migrations, docker-build green); [CP3.1 report](CP3_01_FastAPI_Service.md#results-8-oct-2026-persistent-production-ledger-storage) |
| Global live gate (1), per-IP ticket (HMAC, 48 h), internal service token, owner override, session rate limit | P0 | Schema | Dion (AI-assisted) | DONE (8 Oct, dark, D-101; audit corrections: committed 48 h retention, one-recommendation allowance; client-IP acquisition and provenance are deployment prerequisites) | Quota fairness tests (refusals before billing don't consume the ticket) | CP3.1 report |
| Upload hardening, lean but real (public-beta standard, D-102): `.pdf`/`.docx`/`.txt`/`.md` only; PDF header/signature sanity; DOCX valid OOXML/ZIP structure with a **decompression gate** (size and ratio limits); TXT/MD text-versus-binary sanity, decoding, size and character limits (no invented signature scheme for plain text); streamed size limit; page and character bounds; timeout; safe errors | P0 | — | Dion (AI-assisted) | TODO | Failure-path tests with canaries; 6 DOCX gate tests | CP3.1 report |
| `/docs` off, proxy headers, readiness with a database check, error taxonomy, request IDs and minimal JSON logs | P0 | — | Dion (AI-assisted) | TODO | API tests | CP3.1 report |
| Phase 2 closeout: confirm every Phase 2 row against its validation, record the closeout in the CP3.1 report (public-beta standard, D-102) | P0 | All Phase 2 rows | Dion (AI-assisted) | TODO | Closeout table with evidence links | CP3.1 report |

**Phase 2A result (7 Oct, corrected 8 Oct after the Codex review): the bound is above the cap.** With the frozen configuration and the CP3 envelopes in `config/cp3/phase_bounds_v1.yaml`, `full_analysis_upper_bound` is **US$84.7704449**. The first version reported US$84.7655888; the review found a US$0.0048561 understatement. That is US$82.7704449 above the US$2/day cap, so public live is **not eligible** under D-096 as written. D-096 is unchanged. The breakdown is in the [CP3.1 report](CP3_01_FastAPI_Service.md#results-7-oct-2026-phase-2a). Dion and Codex decide how to proceed before the reservation work (Phase 2B) starts. The Alembic migrations are still design only and wait for their own approval. *(Update 8 Oct: the Alembic migrations are implemented and closed (row above). D-101 resolved this for the Phase 2B safety layer only: it is built dark and fail closed, a recommendation is refused at the US$2 cap, and public live stays blocked by this bound. Results: [CP3.1 report](CP3_01_FastAPI_Service.md#results-8-oct-2026-phase-2b-dark-safety-layer); commits `44f93b2`, `52ff892`, `7d0715b`, `a38db69`.)*

## Phase 3. Public live data path: the real-user AI path (8 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| **Public-live cost/profile decision (the next explicit architecture decision; first unresolved governance blocker before large Phase 3 work):** `full_analysis_upper_bound` US$84.7704449 > US$2/day cap (D-096), so the current real-user live flow cannot serve the D-102 beta. Dion and Codex decide; this documentation does not lower the deterministic bound, change the frozen model, K, retrieval or scoring, or raise the cap | P0 | Phase 2A bounds | Dion and Codex | TODO (next decision) | Decision recorded; `public_live_eligible` follows it | Decision log |
| Name and address hints, correct masking text (FAIL-37) | P0 | — | Dion (AI-assisted) | TODO | Canary test; UI text test | CP3.1 and CP3.3 reports |
| Consent lease stored server-side; consent compatibility parse adapter (D-097), after checking `is_synthetic` use (stop if other dependencies exist) | P0 | Hardening | Dion (AI-assisted) | TODO | The 7 adapter tests; freeze verify | CP3.1 report |
| Public API contract `cv_source = demo / upload` (one pipeline) | P0 | Adapter | Dion (AI-assisted) | TODO | Backward-compatible API tests; no CV posted back | CP3.1 report |
| Runtime query embedding of the consented masked text | P0 | Adapter | Dion (AI-assisted) | TODO | Embedding tests; vector parity with the cache where available | CP3.1 report |
| Production retriever (active, canonical, target, current embedding) | P0 | Schema | Dion (AI-assisted) | TODO | Retrieval tests; no duplicate vacancy | CP3.1 report |
| Lazy extraction cache with parallel prefetch; seed from development saved records | P0 | Schema | Dion (AI-assisted) | TODO | Hit, miss, negative cache, invalidation tests | CP3.1 report |
| Upload flow UI, consent text with providers, limit and fallback messages, safe upload errors | P0 | API | Dion (AI-assisted) | TODO | Streamlit tests; screenshots | CP3.3 report |
| Stage events for the waiting UX: real pipeline stages per flow (CV, search, requirements, matching, result; "job i of N" counts only where real), the same stages that the latency metrics measure (D-102) | P1 | API | Dion (AI-assisted) | TODO | Tests: stage order per flow, no fake percentages | CP3.1 report |
| Flow B "Check a Job": pasted-JD analysis on the reserved runtime for a real CV. Needs a pasted-JD phase bound and reservation decision first (D-101 keeps `/analyze` closed in production; D-096 allows up to three per ticket). Pasted JDs stay session-only and are never ingested into the corpus | P0 | Cost bound decision; consent adapter | Dion (AI-assisted); decision Dion and Codex | TODO | API tests; no corpus write; quota and cap tests | CP3.1 report |

## Phase 3b. Product experience (D-102)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Landing and public-beta framing: what JobFit is, the two primary actions **Find Jobs** and **Check a Job**, privacy and consent explanation, clear calls to action | P1 | Upload flow UI | Dion (AI-assisted) | TODO | Streamlit tests; screenshots | CP3.3 report |
| Stage-aware progress UI driven by the stage events (completed, current, pending; honest messages; no fake percentages) | P1 | Stage events | Dion (AI-assisted) | TODO | Streamlit tests per flow | CP3.3 report |
| Result presentation: job cards, match score with its meaning, strengths, gaps, supporting evidence, explanations, job detail; consistent typography, spacing and components; reasonable mobile and desktop layout | P1 | Public path | Dion (AI-assisted) | TODO | Streamlit tests; screenshots | CP3.3 report |
| Public-beta states: empty, failure, quota, busy, "Live AI analysis is temporarily unavailable" and budget-exhausted, each with the saved-demo fallback | P1 | Phase 2B refusals | Dion (AI-assisted) | TODO | Streamlit tests per refusal code | CP3.3 report |
| "Improve My CV for This Job" for a matched job or a pasted JD: representation improvement (existing evidence only), possibly missing (add only if real), true gap (stated plainly); current statement → suggestion → why → supporting evidence; hard anti-fabrication rule. The deterministic, evidence-grounded version is sufficient for CP3 (builds on coach v1); LLM-generated rewriting is deferred (P2 (post-beta)) unless separately approved after a cost bound and an anti-fabrication evaluation | P1 | Matching result | Dion (AI-assisted) | TODO | Anti-fabrication evaluation: 0 invented items; no suggestion without supporting evidence for type A; "not done" gives no bullet | CP3.3 report; [CV coach plan](../cv-coach-plan.md) |

## Phase 4. Production job data lifecycle (post-beta; D-098 design kept)

The seeded production corpus (632 rows, 428 target-role jobs active) is sufficient for the CP3 controlled public beta. The D-098 sync architecture stays documented in [production-corpus.md](../production-corpus.md); its automation is not a beta blocker.

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Production query manifest (at most 80 requests per sync) | P2 (post-beta) | — | Dion (AI-assisted) | TODO | Manifest hash in the report | [production-corpus.md](../production-corpus.md) |
| `jobfit.jobs.sync` (normalize, exact dedupe, fuzzy `review_required`, classify, transaction, lifecycle, incremental embeddings, report) and the dedupe review command | P2 (post-beta) | Schema | Dion (AI-assisted) | TODO | Sync test suite including "the same vacancy never appears twice" | CP3.2 report |
| Forced-command SSH user and `job-sync.yml` (twice a month, about every two weeks) | P2 (post-beta) | Sync | Dion (AI-assisted); VPS steps Dion and Codex | TODO | One real sync and an idempotent re-run on the VPS | Sync reports |
| One-time manual corpus refresh before the demo, only if needed (operator-run; same dedupe and provenance rules; no scheduler) | P2 | Seed | Dion and Codex | TODO (optional) | Refresh report | Sync report |

## Phase 5. Observability (9 Oct; lean beta release bar)

**Required for the beta:** structured JSON logs, Prometheus metrics, Grafana, and visibility of the application, the AI pipeline, LLM usage and cost, and basic VPS health. Langfuse, email alerting and extra dashboards are optional **P2 (post-beta)** enhancements.

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `/metrics` (bounded labels) and structured JSON logs (`request_id`, `run_id`, session hash, route, status, duration, error code; no CV content) | P1 | Phase 2 | Dion (AI-assisted) | TODO | Canary tests on the metrics and log payloads | CP3.1 report |
| Prometheus, Grafana, node_exporter and one beta dashboard (application, AI pipeline, LLM and cost, basic VPS health) | P1 | VPS | Dion (AI-assisted); VPS steps Dion and Codex | TODO | Dashboard screenshots with live data | CP3.2 and CP3.4 reports |
| Langfuse Japan metadata-only adapter (D-099) | P2 (post-beta) | `/metrics` | Dion (AI-assisted) | TODO (optional) | Canary tests on the Langfuse payloads | CP3.1 report |
| Grafana email alerts (`GRAFANA_SMTP_*`) and additional dashboards (D-099) | P2 (post-beta) | Grafana | Dion (AI-assisted); VPS steps Dion and Codex | TODO (optional) | One test email; screenshots | CP3.2 and CP3.4 reports |
| AI-pipeline and LLM observability (D-102): per-stage latency (CV parse, embedding, retrieval, requirement extraction, matching, recommendation, total), analysis completions and refusals, LLM calls, failures, fallbacks and latency by model, estimated and settled spend, budget state; ledger storage and disk health. Existing metric naming conventions; bounded labels; no CV content | P1 | `/metrics` | Dion (AI-assisted) | TODO | Metric tests with privacy canaries | CP3.1 and CP3.2 reports |

## Phase 6. Deployment packaging (8 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `docker-compose.prod.yml`, Caddyfile, restart policies, log rotation, healthchecks (no SMTP or Langfuse dependency for the beta) | P0 | — | Dion (AI-assisted) | TODO | `docker compose … config` | CP3.2 report |
| Runtime artifact manifest and verifier; tokenizer built into the API image | P0 | — | Dion (AI-assisted) | TODO | Readiness fails on a mismatch | CP3.2 report |
| Backup and restore scripts: a verified backup and a successful restore test of the database and the whole ledger root before the beta (nightly scheduling is P2 (post-beta) unless trivial) | P0 | — | Dion (AI-assisted) | TODO | Row counts after restore (632 / 428) | CP3.2 report |
| VPS runbook with the two-layer validation commands and backup-before-migrate | P0 | — | Dion (AI-assisted) | TODO | Review | Runbook |
| Public is not admin (D-102): only Caddy publishes ports and serves only the end-user app; FastAPI, PostgreSQL, Prometheus, Grafana and every operator interface stay private (SSH tunnel); no admin endpoint reachable anonymously | P0 | Compose, Caddyfile | Dion (AI-assisted) | TODO | `docker compose … config` port check; external scan shows only 80/443 | CP3.2 and CP3.4 reports |

## Phases 7-8. VPS and deployed validation (8-9 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Provision SumoPod VPS (SSH, ufw, Docker, DNS, production key with limit; SMTP and the Langfuse Japan project only if the P2 (post-beta) items are taken up) | P0 | — | Dion and Codex | TODO | Runbook checklist | CP3.2 report |
| First deploy, dark (saved demo only) | P0 | Phase 6 | Dion and Codex | TODO | **A:** external public smoke through Caddy and Streamlit. **B:** internal API `e2e_check` inside the Docker network or over an SSH tunnel; FastAPI stays private | CP3.4 report |
| OpenRouter per-route privacy record (parse, embedding, extraction, matching) | P0 | VPS | Dion and Codex | TODO | Recorded; gaps reported before public live | Privacy model |
| Privacy release gate with canaries in every sink enabled for the beta, including upload failure paths (Langfuse only if enabled) | P1 | Deploy | Dion (AI-assisted) | TODO | 0 hits | CP3.4 report |
| Owner live runs, latency baseline, F2 measurement, quota, cap and busy tests, mentor UX check | P1 | Gate | Dion (AI-assisted) | TODO | Latency and cost table | CP3.4 report |
| Real-host persistence validation of the ledger storage (restart, container recreate, host reboot: same `storage_id`, lifetime spend unchanged) | P0 | First deploy | Dion and Codex | TODO | Recorded checks on the VPS | CP3.4 report |
| Enable public live, the controlled public beta (`JOBFIT_PUBLIC_LIVE=1`) | P1 | Gate passed; the public-live cost/profile decision satisfied (D-096) | Dion | TODO | Gate record | CP3.4 report |
| Limited public-beta trial and portfolio readiness (a few real users through Find Jobs and Check a Job; LinkedIn and portfolio link check) | P2 | Public beta enabled | Dion | TODO | Trial notes; no privacy or cost incident | CP3.4 and CP3.5 reports |

## Phases 9-11. Quality validation, freeze, final stages (9-11 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| PR-10 original vs masked (CV1/CV2, about US$2) | P2 (required before the final report; high-value AI evidence) | Deploy | Dion (AI-assisted) | TODO | D-100 thresholds | CP3.4 and CP3.5 reports |
| D-045 option B: Dion blind-labels F00398, F00237 and CV3 × F00398, locks the hash, then the frozen pipeline runs (about US$0.10) | P2 (required before the final report; high-value AI evidence) | Phase 0 selection | Dion (AI-assisted) | TODO | Strict metrics; groups reported separately | CP3.5 report |
| D-045 workbook (MODEL-ASSISTED, HUMAN-REVIEWED) import, alignment and scoring | P2 | — | Dion (AI-assisted) | TODO | Human-verified alignment | CP3.5 report |
| Coach refinement (source requirement, CV status, no-invention wording): now part of "Improve My CV for This Job" in Phase 3b (D-102) | P1 | — | Dion (AI-assisted) | TODO (moved to Phase 3b) | 0 invented items; "not done" gives no bullet | CP3.3 report |
| Formal feature freeze (end of 9 Oct) | P1 | All P0 and P1 | Dion (AI-assisted) | TODO | Final validation table | CP3.4 report |
| Reports, README, deck, video, rehearsal, tag, presentation | P2 | Freeze | Dion (AI-assisted) | TODO | Claims traceable to evidence | CP3.5-CP3.7 reports |
