# CP3 production observability handoff (10 October 2026)

This change is local and uncommitted on `claude/cp3-production-observability` at base `d7420a918399708d1b8b66501a2b0a61b0ba5327`. It has **not** been integrated, deployed, or validated on the VPS. The owner reported that Prometheus, Grafana, Node Exporter, and four infrastructure panels already work. The repository does not contain the active `/opt/jobfit-monitoring/compose.yml`, Prometheus configuration, or the exported Grafana dashboard, so these artifacts require a comparison with the actual files before deployment. `main` and its uncommitted files were left untouched.

## Decision and safety boundary

D-087 freezes the CP2 intelligence and 57 hashed files; D-097 permits non-frozen runtime adapters. D-096 and D-101 make the ledger and budget reservations authoritative. D-099 requires bounded metrics and privacy-safe logs. D-102 and D-103 call for a lean beta, with daily US$5 and lifetime US$25 limits. D-103 separately requires Langfuse before final controlled public beta; this change does not supply Langfuse. D-095 and the privacy threat model keep observability private. The older D-099 two-dashboard and alerts proposal was superseded for this beta by the D-102/D-103 priority updates and the owner's one-dashboard instruction.

No live gate, public gate, owner gate, model, prompt, retrieval rule, score, budget or ledger settlement was changed. The only new dependency is `prometheus-client`; `Dockerfile.api` disables Uvicorn's raw access log. One JSON formatter handles application events. HTTP admission and asynchronous analysis outcome events share a server-generated request ID; stage logs contain only bounded stage/outcome, status, and duration. It never formats arbitrary messages, arguments, exception traces, request bodies, or headers. Docker log rotation must remain enabled in the active Compose.

## Metrics contract

| Metric family | Type | Labels | Source and meaning |
| --- | --- | --- | --- |
| `jobfit_http_requests_total` | counter | method, route, status | Completed ASGI HTTP responses, including `/metrics`; unknown routes become `unmatched`. |
| `jobfit_http_duration_seconds` | histogram | method, route | HTTP wall time, including response send. |
| `jobfit_analysis_requests_total` | counter | outcome | D-103 `/analyze` and `/jobs/{job_id}/analyze` HTTP responses: `accepted`, idempotent `duplicate`, `refused`, or `failure`. Legacy saved `/recommendations` is excluded. Accepted is **not** completed. |
| `jobfit_analysis_outcomes_total` | counter | outcome | Actual asynchronous `completed`, `held`, `failed`, `refused`, or `unknown` outcomes. `JobResult` is classified before presentation; no dictionary is treated as proof of success. |
| `jobfit_stage_executions_total` | counter | stage, outcome | Executed pipeline and runtime boundaries. |
| `jobfit_stage_duration_seconds` | histogram | stage, outcome | Wall time for the same boundaries. Nested stage times must not be summed. |
| `jobfit_llm_attempts_total` | counter | model, chain, kind, outcome | One observation after a correlated ledger line is durable. Failed provider attempts count. |
| `jobfit_llm_duration_seconds` | histogram | model, chain | Attempt latency when recorded. |
| `jobfit_llm_tokens_total` | counter | model, direction | Only attempts with known token usage. |
| `jobfit_llm_usage_observations_total` | counter | model | Attempts with known token usage. |
| `jobfit_llm_fallbacks_total` | counter | model | Ledgered initial fallback attempts. |
| `jobfit_llm_upper_bound_usd_total` | counter | model | Sum of reserved per-attempt upper estimates; **not** billed cost. |
| `jobfit_llm_accounted_cost_usd_total` | counter | model, source | Per-process cost observations by reported, token-estimated, uncertain, or rejected source; **not** a budget balance. |
| `jobfit_budget_rejections_total` | counter | reason | Runtime `budget` or `lifetime` refusals. |
| `jobfit_ledger_storage_readable` | gauge | none | Marker, ledger and journal can be read; this is **not** a write or durability probe. |
| `jobfit_postgres_available` | gauge | none | A short read-only `SELECT 1` succeeds in production. This is availability, not a write or schema check. |
| `process_start_time_seconds` | gauge | none | Native Prometheus process collector on Linux; a changed timestamp indicates process restart. |
| `up{job="jobfit-api"}` | gauge | job | Prometheus scrape availability, created by Prometheus rather than the API. |
| `jobfit_accounting_snapshot_available` | gauge | none | 1 only if a read-only, consistent ledger and PostgreSQL snapshot is available. |
| `jobfit_accounting_*_usd`, `jobfit_accounting_ledger_bytes` | gauges | none | Persisted reported, token-estimated, uncertain, settled, daily settled, daily liability, open reserved, unledgered upper bound, recorded spend, limits, remaining amounts, and ledger bytes. The named fields are defined in `CostSnapshot.__call__`. |

Allowed stage labels include `cv_parse`, `query_embedding`, `retrieval`, `extraction`, `matching`, `parse`, `search`, `job_analysis`, legacy `recommendation`, and `overall_analysis`. In the active D-103 flow, `job_analysis` is the recommendation/analysis execution boundary; the old `recommendation` runtime phase is refused and has no fabricated normal timing sample. Model, chain, kind, route, method, outcome, and cost-source labels are bounded by allow-lists. There are no CV, JD, job, session, run, request, IP, token, prompt, or evidence labels. In dark mode, AI/LLM counters have no execution samples. The production cost collector uses explicit production settings and read-only persisted evidence even while live is off. If the ledger or database cannot be reconciled, it emits availability `0` and omits balances instead of publishing a guessed zero. Process counters reset on restart; persisted gauges do not derive from those counters. The ledger remains authoritative.

Useful PromQL: request rate `sum(rate(jobfit_http_requests_total{job="jobfit-api",route!="/metrics"}[5m]))`; 5xx fraction `(sum(rate(jobfit_http_requests_total{job="jobfit-api",status=~"5..",route!="/metrics"}[5m])) or vector(0)) / sum(rate(jobfit_http_requests_total{job="jobfit-api",route!="/metrics"}[5m]))`; latency p95 `histogram_quantile(0.95,sum by (le)(rate(jobfit_http_duration_seconds_bucket{job="jobfit-api",route!="/metrics"}[5m])))` (substitute 0.5 for p50).

## Local MacBook review and validation

From this worktree, use the project virtualenv and the existing test commands:

```sh
../project-job-fit/env-job-fit/bin/python -m pytest -q tests/test_observability.py tests/test_fail37_api_privacy.py
../project-job-fit/env-job-fit/bin/python scripts/prepare_cp23_freeze.py --verify evals/freeze/cp23_freeze_draft_v2
RUFF_CACHE_DIR=/private/tmp/jobfit-ruff-cache ruff check --select E9,F63,F7,F82 src scripts ui tests
RUFF_CACHE_DIR=/private/tmp/jobfit-ruff-cache ruff check --select F src ui
```

The PostgreSQL integration tests require an isolated local test database and the existing `JOBFIT_MIGRATION_TESTS`/`JOBFIT_MIGRATION_ADMIN_URL` test settings. Never point them at the CP2 or production database. Inspect `git diff --check`, `git status --short`, the metric payload for synthetic canaries, and the dashboard output before integration. No real CV or paid provider call is required.

## Owner-side deployment procedure, after review and integration approval

1. On the VPS, identify the **actual** application Compose, monitoring Compose, Prometheus config, Grafana dashboard source/export, datasource name, API token source, and container user IDs. Keep the existing four infrastructure panels and dashboard UID `jobfit-overview`. Make versioned backups of those files, the active dashboard JSON, and the API image/tag. The production database and ledger must be backed up together; the previously reported backup has checksum verification but no restore test, so do not claim recovery is validated.
2. The owner inspected the VPS network assignments: API=`application_net`+`database_net`, DB=`database_net`, UI=`application_net`, and Prometheus/Grafana/Node Exporter=`monitoring`. The overrides explicitly retain the API's two networks and Prometheus's `monitoring` network while adding only `jobfit_observability` to those two services. The shared external network is named `jobfit-observability`. Merge each override with its **actual** Compose project and inspect `docker compose config --no-interpolate --format json` before applying; the owner's network report is not a substitute for this merged-config check. Verify every service network, unchanged ports, API loopback binding, no database port, and unchanged monitoring services/datasource. Do not replace the projects, remove existing networks, reset Grafana volumes, or run `down -v`.
3. Mount an owner-created token file read-only at `/run/secrets/jobfit_internal_token`; its bytes must match `JOBFIT_INTERNAL_TOKEN` used by the API. Prometheus runs as `nobody`, so a root-owned `0600` host file is **not** readable through this bind mount. On a standard rootful Linux Docker host, the narrow option is a root-owned `0700` host secrets directory and a token file owned by the container's **mapped numeric UID** (normally `65534`), group root, mode `0400`, mounted `:ro`. Confirm the container UID and any user-namespace mapping first; after the mount, verify readability inside the container without printing the bytes. This changes file ownership: another host process with that UID could read the file if it can reach the path, so keep the parent directory root-only and do not mount it elsewhere. Do not make the file world-readable. Compose `secrets` backed by a host file do not reliably remap UID/mode, so merely adding `uid`/`mode` fields is not a fix. Never commit or print the token. Append `prometheus-job.yml` as one entry under the existing `scrape_configs`; do not replace the current Node Exporter job. Run the installed `promtool check config` before reload. The job uses `http_headers` with a file-backed `X-JobFit-Internal-Token`, an internal Docker DNS alias, and 30-second scrape interval. Verify the target becomes `UP`; unauthorized `/metrics` must remain `401`.
4. Build and start **only** the reviewed API service, preserving dark settings (`JOBFIT_LIVE_ENABLED=0`, `JOBFIT_PUBLIC_LIVE=0`, `JOBFIT_REAL_CV_ENABLED=0`) and the current DB/ledger volumes. Apply the monitoring network merge and reload or restart only Prometheus as required by the actual setup. Verify `/health`, authorized `/metrics`, the target's `up{job="jobfit-api"}`, log JSON, bounded labels, no synthetic canaries, and unchanged existing infrastructure panels. Cost availability may legitimately be `0` if production ledger evidence is unprovisioned in dark mode; no balance should then appear as zero.
5. Identify the **actual file-provisioned dashboard JSON** and its provisioning configuration on the VPS. Make an unchanged versioned backup of that JSON file. Copy that file for local review and generate a candidate with `python scripts/prepare_observability_dashboard.py --input <copy-of-provisioned-jobfit-overview.json> --output <candidate.json> --datasource-name Prometheus` (use the actual existing datasource identifier if different). Review the diff: UID `jobfit-overview`, all four existing infrastructure panels, and each existing datasource reference must remain intact. After independent approval, replace the same provisioned JSON file using the reviewed candidate and reload/restart Grafana provisioning as required by the active setup. Do **not** use Grafana UI import. The script supports a plain provisioned dashboard JSON and an export wrapper, and refuses a second append.

6. Validate all private endpoints from the owner tunnel and externally verify only the intended public ports are reachable. A production privacy release gate, a successful backup restore test, and the separate Langfuse task remain prerequisites before final controlled public-beta activation.

Rollback: preserve the old image/tag and configuration files first. Restore the previous dashboard JSON with UID `jobfit-overview`, the backed-up Prometheus config and monitoring Compose, then the prior API image and application Compose; restart only affected services and verify existing four infrastructure panels and `/health`. Remove the observability network only after no containers use it. Do not roll back or edit the ledger, database, production seed, or budget rows as part of an observability rollback.

## Remaining limits

The worktree has not been deployed or checked against the active VPS Compose or dashboard. Grafana panels show no AI samples while live is disabled. The readable gauge is not a filesystem write probe. HTTP accepted and idempotent duplicate counts are separate from actual asynchronous completed, held, failed, and refused counts. A crashed process can lose its in-memory completion sample, so counters are not an authoritative operation ledger. LLM counters are per-process observations and can miss a crash between a durable ledger append and telemetry emission; budget gauges use persisted state. Langfuse, email alerts, and successful backup restore are outside this change. The owner must complete VPS validation and the privacy release gate before claiming production monitoring or public-beta readiness.
