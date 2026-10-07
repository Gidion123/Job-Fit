# CP3 Execution Plan (Daily Checklist)

**Created:** 7 Oct 2026 (Phase 0, documentation and plan freeze) · **Decisions:** [D-095 to D-100](../decisions.md)

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

**Timeline:**
- 8 Oct: core engineering and the dark deployment.
- 9 Oct: deployed validation, the privacy release gate, public-live enablement, PR-10 and the formal feature freeze (end of day).
- 10 Oct: reports, deck, video and rehearsal.
- 11 Oct: presentation.

**Budgets:** CP3 validation US$5 in total. Production US$2/day.

## Phase 0. Documentation and plan freeze (7 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Update master plan, decisions D-095 to D-100, FAIL-36 to 38, CP3 reports, privacy model, coach plan, production corpus, indexes | P0 | Plan acceptance | Dion (AI-assisted) | DONE | *Phase 0 validation recorded at `aa2deed`:* docs-only diff (20 files); freeze verify `"ok": true`; pytest 671 passed / 9 skipped / 3 failed (exactly the known FAIL-35 baseline). *Closeout-patch validation:* link and anchor check over all of `docs/` + `README.md` (0 broken); `git diff --check` clean; docs-only diff; freeze verify `"ok": true` | Commit `aa2deed` |
| D-045 option B: select unseen blind candidates by job ID only (no inference, no model output) | P2 | — | Dion (AI-assisted) | DONE (selection only) | Absent from workbook, CP2.4 outputs, test gold, pools and other tracked files | [CP3.5 report](CP3_05_Final_Presentation_and_Portfolio.md) |

## Phase 1. Baseline green (7 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Re-apply the FAIL-35 test fix cleanly (no merge of the old branch, no attribution trailers) | P0 | Phase 0 review | Dion (AI-assisted) | TODO | Offline pytest 0 failed; CI green | CI run link |
| Pyflakes `F` fixes in `src/` and `ui/`, then add `F` to CI | P1 | FAIL-35 | Dion (AI-assisted) | TODO | `ruff` clean | CI |
| Freeze verify in CI | P1 | — | Dion (AI-assisted) | TODO | `"ok": true` | CI |

## Phase 2. P0 production hardening (8 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Fail-closed settings (live and public live off by default; `JOBFIT_*` settings) | P0 | Phase 1 | Dion (AI-assisted) | TODO | Settings tests | CP3.1 report |
| Alembic `0001` baseline and `0002` production schema (lifecycle, `dedupe_status`, `job_sources` unique on source and source id, `sync_runs`, extraction cache, quota, reservations) | P0 | Phase 1 | Dion (AI-assisted) | TODO | Up on an empty and a restored database; down and up where reversible | CP3.2 report |
| Deterministic phase bounds (`parse_max`, `recommendation_upper_bound`, `full_analysis_upper_bound`) from versioned config | P0 | Settings | Dion (AI-assisted) | TODO | Exact values; missing data fails closed; a full bound above the cap blocks public live | CP3.1 report |
| Concurrency-safe app client with separate parse and recommendation reservations (F2, FAIL-36) | P0 | Phase bounds | Dion (AI-assisted) | TODO | Serial and concurrent outputs identical; no call without a reservation; embedding only in the recommendation reservation; settled plus outstanding never above the cap; one ledger line per call | CP3.1 report |
| Persistent production ledger volume | P0 | — | Dion (AI-assisted) | TODO | Crash-recovery test | CP3.1 report |
| Global live gate (1), per-IP ticket (HMAC, 48 h), internal service token, owner override, session rate limit | P0 | Schema | Dion (AI-assisted) | TODO | Quota fairness tests (refusals before billing don't consume the ticket) | CP3.1 report |
| Upload hardening: `.pdf`/`.docx`/`.txt`/`.md` only, signature check, streamed size limit, page and character bounds, **DOCX decompression gate**, timeout, safe errors | P0 | — | Dion (AI-assisted) | TODO | Failure-path tests with canaries; 6 DOCX gate tests | CP3.1 report |
| `/docs` off, proxy headers, readiness with a database check, error taxonomy, request IDs and minimal JSON logs | P0 | — | Dion (AI-assisted) | TODO | API tests | CP3.1 report |

## Phase 3. Public live data path (8 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Name and address hints, correct masking text (FAIL-37) | P0 | — | Dion (AI-assisted) | TODO | Canary test; UI text test | CP3.1 and CP3.3 reports |
| Consent lease stored server-side; consent compatibility parse adapter (D-097), after checking `is_synthetic` use (stop if other dependencies exist) | P0 | Hardening | Dion (AI-assisted) | TODO | The 7 adapter tests; freeze verify | CP3.1 report |
| Public API contract `cv_source = demo / upload` (one pipeline) | P0 | Adapter | Dion (AI-assisted) | TODO | Backward-compatible API tests; no CV posted back | CP3.1 report |
| Runtime query embedding of the consented masked text | P0 | Adapter | Dion (AI-assisted) | TODO | Embedding tests; vector parity with the cache where available | CP3.1 report |
| Production retriever (active, canonical, target, current embedding) | P0 | Schema | Dion (AI-assisted) | TODO | Retrieval tests; no duplicate vacancy | CP3.1 report |
| Lazy extraction cache with parallel prefetch; seed from development saved records | P0 | Schema | Dion (AI-assisted) | TODO | Hit, miss, negative cache, invalidation tests | CP3.1 report |
| Upload flow UI, consent text with providers, limit and fallback messages, safe upload errors | P0 | API | Dion (AI-assisted) | TODO | Streamlit tests; screenshots | CP3.3 report |
| Stage events for the waiting UX | P1 | API | Dion (AI-assisted) | TODO | Tests | CP3.1 report |

## Phase 4. Production job data lifecycle (9 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Production query manifest (at most 80 requests per sync) | P1 | — | Dion (AI-assisted) | TODO | Manifest hash in the report | [production-corpus.md](../production-corpus.md) |
| `jobfit.jobs.sync` (normalize, exact dedupe, fuzzy `review_required`, classify, transaction, lifecycle, incremental embeddings, report) and the dedupe review command | P1 | Schema | Dion (AI-assisted) | TODO | Sync test suite including "the same vacancy never appears twice" | CP3.2 report |
| Forced-command SSH user and `job-sync.yml` (twice a month, about every two weeks) | P1 | Sync | Dion (AI-assisted); VPS steps Dion and Codex | TODO | One real sync and an idempotent re-run on the VPS | Sync reports |

## Phase 5. Observability (9 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `/metrics` (bounded labels), Langfuse Japan metadata-only adapter | P1 | Phase 2 | Dion (AI-assisted) | TODO | Canary tests on the metrics and Langfuse payloads | CP3.1 report |
| Prometheus, Grafana, node_exporter, two dashboards, email alerts (`GRAFANA_SMTP_*`) | P1 | VPS | Dion (AI-assisted); VPS steps Dion and Codex | TODO | One test email; screenshots | CP3.2 and CP3.4 reports |

## Phase 6. Deployment packaging (8 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `docker-compose.prod.yml`, Caddyfile, restart policies, log rotation, healthchecks | P0 | — | Dion (AI-assisted) | TODO | `docker compose … config` | CP3.2 report |
| Runtime artifact manifest and verifier; tokenizer built into the API image | P0 | — | Dion (AI-assisted) | TODO | Readiness fails on a mismatch | CP3.2 report |
| Backup and restore scripts; restore-tested initial dump; nightly backup (P1) | P0 / P1 | — | Dion (AI-assisted) | TODO | Row counts after restore (632 / 428) | CP3.2 report |
| VPS runbook with the two-layer validation commands and backup-before-migrate | P0 | — | Dion (AI-assisted) | TODO | Review | Runbook |

## Phases 7-8. VPS and deployed validation (8-9 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Provision SumoPod VPS (SSH, ufw, Docker, DNS, SMTP, production key with limit, Langfuse Japan project) | P0 | — | Dion and Codex | TODO | Runbook checklist | CP3.2 report |
| First deploy, dark (saved demo only) | P0 | Phase 6 | Dion and Codex | TODO | **A:** external public smoke through Caddy and Streamlit. **B:** internal API `e2e_check` inside the Docker network or over an SSH tunnel; FastAPI stays private | CP3.4 report |
| OpenRouter per-route privacy record (parse, embedding, extraction, matching) | P0 | VPS | Dion and Codex | TODO | Recorded; gaps reported before public live | Privacy model |
| Privacy release gate with canaries in every sink, including upload failure paths | P1 | Deploy | Dion (AI-assisted) | TODO | 0 hits | CP3.4 report |
| Owner live runs, latency baseline, F2 measurement, quota, cap and busy tests, mentor UX check | P1 | Gate | Dion (AI-assisted) | TODO | Latency and cost table | CP3.4 report |
| Enable public live (`JOBFIT_PUBLIC_LIVE=1`) | P1 | Gate passed; `full_analysis_upper_bound` ≤ cap | Dion | TODO | Gate record | CP3.4 report |

## Phases 9-11. Quality validation, freeze, final stages (9-11 Oct)

| Task | Pri | Depends on | Owner | Status | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| PR-10 original vs masked (CV1/CV2, about US$2) | P2 | Deploy | Dion (AI-assisted) | TODO | D-100 thresholds | CP3.4 and CP3.5 reports |
| D-045 option B: Dion blind-labels F00398, F00237 and CV3 × F00398, locks the hash, then the frozen pipeline runs (about US$0.10) | P2 | Phase 0 selection | Dion (AI-assisted) | TODO | Strict metrics; groups reported separately | CP3.5 report |
| D-045 workbook (MODEL-ASSISTED, HUMAN-REVIEWED) import, alignment and scoring | P2 | — | Dion (AI-assisted) | TODO | Human-verified alignment | CP3.5 report |
| Coach refinement (source requirement, CV status, no-invention wording) | P1 | — | Dion (AI-assisted) | TODO | 0 invented items; "not done" gives no bullet | CP3.3 report |
| Formal feature freeze (end of 9 Oct) | P1 | All P0 and P1 | Dion (AI-assisted) | TODO | Final validation table | CP3.4 report |
| Reports, README, deck, video, rehearsal, tag, presentation | P2 | Freeze | Dion (AI-assisted) | TODO | Claims traceable to evidence | CP3.5-CP3.7 reports |
