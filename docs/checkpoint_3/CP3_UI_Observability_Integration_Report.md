# CP3 UI v3 + production observability integration candidate

**Status:** local, uncommitted candidate on `claude/cp3-ui-observability-integration`; base `d7420a918399708d1b8b66501a2b0a61b0ba5327`. No source worktree, VPS service, production configuration, database, or ledger was changed. This report is the combined deployment handoff; the imported UI and observability handoffs describe their earlier separate worktrees.

## Integrated files and conflict decisions

All 46 changed paths in the two source worktrees were read from their actual working trees, including untracked files: 19 unique to UI v3, 25 unique to observability, and 2 shared. The UI paths cover `.streamlit/config.toml`, `Dockerfile.ui`, `docker-compose.owner-local.yml`, both UI checkpoint documents, the synthetic FAIL-37 sanitizer receipt, `src/jobfit/privacy/{masking,structure}.py`, the four UI/API/privacy tests, and `ui/{components,streamlit_app,texts,theme}.py` plus the font and license. The observability paths cover `Dockerfile.api`, API wiring, live evidence/operation/client and recommendation adapters, its privacy and observability tests, `src/jobfit/observability/`, `deploy/observability/` (including the latest network overrides), the dashboard merge script, traceability/audit reports, and validation logs. The complete path list is available from `git status --short -uall` in this worktree.

The shared `requirements.txt` contains both `streamlit>=1.64,<2` and `prometheus-client>=0.26,<0.27`. In `src/jobfit/api/main.py`, two textual conflicts at analysis admission were resolved by using UI v3's `analysis_limit` **and** observability's generated `request_id`. This preserves both the UI session-limit contract and admission-to-async log correlation. The D-103 public allowance remains parse 1 / search 1 / job_analysis 3; owner-local `JOBFIT_SESSION_ANALYSIS_LIMIT=10` must not enter production. No frozen file, budget calculation, ledger settlement, schema, or authentication rule was changed.

The first combined test run exposed three observability tests whose `caplog` assertions depended on running before production logging configuration. Only `tests/test_observability.py` was adjusted to capture records from the private JobFit logger directly. Production logging code and privacy behavior were not changed; the corrected tests and full suite pass together.

## Combined local validation

| Gate | Result |
| --- | --- |
| Full offline pytest (two known macOS deselections) | **1449 passed, 248 skipped, 2 deselected, 0 failed** |
| Isolated disposable PostgreSQL runtime/ledger suite | **50 passed, 0 failed** |
| Ruff CI selectors `E9,F63,F7,F82` over `src scripts ui tests`; `F` over `src ui` | **PASS / PASS** |
| D-087 receipt verification | **PASS**, `ok=true`, `changed_files=[]` |
| `git diff --check` | **PASS** |
| Merged application Compose against the local read-only production Compose reference | API=`application_net,database_net,jobfit_observability`; DB=`database_net`; UI=`application_net`; no added ports |
| Merged monitoring Compose against a synthetic three-service fixture | Prometheus=`monitoring,jobfit_observability`; Grafana and Node Exporter=`monitoring`; no added ports |
| Local combined UI image | **PASS**; Streamlit 1.65.0 and bundled config/font verified without network |
| Local combined API image | **PASS**; FastAPI 0.143.0, `prometheus-client` 0.26.0, and combined API/wiring/metrics imports verified without network |

The first PostgreSQL invocation was denied by the local command sandbox's loopback restriction; the same tests passed when granted access to the **disposable** container on `127.0.0.1:15438`. No existing database or volume was used. The two pytest deselections are the previously known macOS `/var` versus `/private/var` path check and injected `__CF_USER_TEXT_ENCODING` worker environment check; neither is counted as a pass. All tests used synthetic data and fake providers.

## Observability contract and limits

| Area | Local status |
| --- | --- |
| CPU, RAM, disk | Existing four Node Exporter infrastructure panels are retained by the dashboard merge; actual provisioned dashboard still needs owner-side comparison. **PARTIAL until deployed.** |
| API scrape/process, PostgreSQL and ledger health | `up`, native `process_start_time_seconds`, read-only PostgreSQL availability, ledger readability and accounting snapshot availability are implemented and tested. **PARTIAL until live scrape.** |
| Requests, errors, latency and analysis outcomes | Bounded HTTP RED metrics distinguish accepted/duplicate from actual async completed/held/failed/refused/unknown. **PASS locally.** |
| AI pipeline | Parse, embedding, retrieval, extraction, matching, active D-103 `job_analysis` and async overall-analysis boundaries are timed. The legacy `recommendation` phase is not executed; no timing is fabricated. A whole CV-to-search-to-analysis journey timer is absent. **PARTIAL.** |
| LLM | Durable attempt counts include repair and fallback; failure, duration and known token usage are bounded. Model names are provider-qualified, without a separate provider label. **PARTIAL for the requested provider dimension.** |
| Cost/budget | Per-attempt upper estimates, actual/estimated/uncertain accounted cost and read-only persisted settled spend/budget balances are separate. Unknown snapshots are not reported as zero. **PASS locally.** |
| Logging/privacy | Content-free JSON; generated request correlation; authenticated `/metrics`; bounded labels; no CV/JD/prompt/token/IP payload. **PASS locally; deployed canaries pending.** |
| Grafana | One dashboard, UID `jobfit-overview`, Prometheus datasource and original four panels preserved by merge tests; zero-error query fixed. Actual provisioned JSON and render remain owner-side checks. **PARTIAL.** |
| Backup-age signal | No source in this scoped implementation. **MISSING**, outside this integration. |
| Langfuse, deployed privacy gate, successful DB+ledger restore | **DEFERRED TO PUBLIC-BETA GATES** under D-103 and CP3 release criteria. |

## MacBook validation commands

From this integration worktree:

```sh
../project-job-fit/env-job-fit/bin/python -m pytest -q --deselect=tests/test_owner_local_compose.py::test_the_profile_is_owner_only_and_passes_the_production_invariants --deselect=tests/test_upload_guard.py::test_the_worker_gets_an_allow_listed_environment_and_isolated_mode -p no:cacheprovider
# Only with a newly created disposable local PostgreSQL server; never point this at owner-local or production DB:
JOBFIT_MIGRATION_TESTS=1 JOBFIT_MIGRATION_ADMIN_URL=postgresql://combined_test:synthetic-test-only@127.0.0.1:15438/postgres ../project-job-fit/env-job-fit/bin/python -m pytest -q tests/test_observability_db.py tests/test_real_cv_runtime_db.py tests/test_public_beta_runtime_db.py tests/test_live_runtime_db.py -p no:cacheprovider
RUFF_CACHE_DIR=/private/tmp/jobfit-cp3-combined-ruff ruff check --select E9,F63,F7,F82 src scripts ui tests
RUFF_CACHE_DIR=/private/tmp/jobfit-cp3-combined-ruff ruff check --select F src ui
../project-job-fit/env-job-fit/bin/python scripts/prepare_cp23_freeze.py --verify evals/freeze/cp23_freeze_draft_v2
git diff --check
docker build --pull=false -f Dockerfile.api -t jobfit-cp3-combined-api:local .
docker build --pull=false -f Dockerfile.ui -t jobfit-cp3-combined-ui:local .
```

## One deployment: owner-side requirements after independent approval

1. Confirm the actual VPS checkout still starts at `d7420a9`, and review the combined diff including untracked files. Back up the existing application and monitoring Compose files, Caddy config, provisioned dashboard JSON, Prometheus config, prior API/UI image IDs, and the paired database+ledger according to the owner runbook. Keep secrets private; do not reset or restore DB/ledger for this code update.
2. Merge the latest `api-network.override.yml` with the **actual** `/opt/jobfit/docker-compose.prod.yml`, and `monitoring-network.override.yml` with the **actual** monitoring Compose. Inspect the effective networks and ports before applying. Preserve API `127.0.0.1:8000`, UI `127.0.0.1:8501`, DB without a published port, and the existing monitoring network and datasource. The shared external network must be `jobfit-observability`.
3. Verify the token file is readable by the Prometheus container's mapped `nobody` UID through a read-only mount, within a root-only host directory; do not make it world-readable or print its bytes. Append the scrape job to the existing Prometheus configuration. Merge the actual file-provisioned dashboard JSON with the provided script; preserve UID `jobfit-overview`, datasource and four infrastructure panels. Do not use Grafana UI import.
4. Build and deploy the **combined API and UI images together** from this reviewed source while keeping `JOBFIT_LIVE_ENABLED=0`, `JOBFIT_PUBLIC_LIVE=0`, `JOBFIT_REAL_CV_ENABLED=0`, production `analysis_limit=3`, existing secrets, Caddy HTTPS/Basic Authentication, PostgreSQL data and ledger. Reload only affected monitoring components. Do not use `docker-compose.owner-local.yml` for production.
5. Smoke-test `/health`, UI `/_stcore/health`, unauthorized `/metrics` (401), authorized private scrape, Prometheus `up`, process/DB/ledger signals, JSON log canaries, dashboard preservation, and the synthetic saved-demo UI flow. Retain old images/configurations for rollback. If any check fails, revert API/UI images and affected Compose/monitoring/dashboard files together; never roll back the database or ledger merely to revert code.

**Remaining deployment blockers:** actual VPS merged Compose, token UID/readability, provisioned dashboard diff/render, live scrape and dark-mode smoke test are not validated from this MacBook. Langfuse and the privacy/recovery release gates remain mandatory before public-beta activation. No commit, push, merge, SSH, deployment or paid LLM call was made during this integration.
