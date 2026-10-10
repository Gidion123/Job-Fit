# Local validation, 10 October 2026 (Asia/Jakarta)

- Base branch: `origin/cp3-development-20261007`, HEAD `d7420a918399708d1b8b66501a2b0a61b0ba5327`. Implementation worktree: `claude/cp3-production-observability`. No commit, push, merge or deployment.
- Full offline suite, excluding two independently reproduced macOS baseline failures: **1417 passed, 247 skipped, 2 deselected** in 108.12 s. Command: `../project-job-fit/env-job-fit/bin/python -m pytest -q --deselect=tests/test_owner_local_compose.py::test_the_profile_is_owner_only_and_passes_the_production_invariants --deselect=tests/test_upload_guard.py::test_the_worker_gets_an_allow_listed_environment_and_isolated_mode`.
- The unrestricted initial full suite was **1409 passed, 245 skipped, 3 failed**. One failure was a legacy privacy test expecting `/metrics` to return 404; it was updated to inspect the authorized metric payload for raw canaries, and the focused privacy/observability tests pass. The other two were the same macOS baseline failures below.
- Baseline macOS failures: `test_owner_local_compose` compares `/private/var` with `/var` in the production ledger path invariant; `test_upload_guard` sees macOS-injected `__CF_USER_TEXT_ENCODING` in a child process. The associated test and production files were not modified for this task. See `macos_baseline.log` for exact tracebacks. These are **not** claimed as passes.
- Focused observability plus privacy after the final logging change: **54 passed** in 2.57 s (`-p no:cacheprovider`).
- Isolated PostgreSQL integration suite: **49 passed** earlier against a temporary pgvector:pg17 container using port 127.0.0.1:15437 and tmpfs storage. After the logging change, the directly affected observability and real-CV DB tests were rerun: **10 passed** in 1.52 s. A subsequent exception-safety guard was covered by the final 54-test focused run; the DB suite was not rerun after that guard. The temporary container was inspected to confirm no volume mounts, then removed. No CP2 or production database/volume was used.
- Ruff: CI-selected `E9,F63,F7,F82` across `src scripts ui tests`, `F` across `src ui`, and full Ruff across changed Python files: **all passed**.
- D-087 freeze verification: `ok: true`, `changed_files: []`. `git diff --check` passed. Grafana panel JSON parses.
- Local read-only Compose merge with the untracked `main` production Compose reference: API retained `application_net`, `database_net`, `127.0.0.1:8000`, and existing json-file rotation; new `jobfit_observability` was added. UI and DB networks were unchanged. Actual VPS Compose was not inspected.
- Prometheus `http_headers` with `files` syntax was checked against the official configuration reference; `promtool` against the actual VPS configuration has **not** run. Dashboard merge is offline and covered by the focused tests, but the actual VPS dashboard export is unavailable locally.
- Dark mode, public live, real-CV live, provider credentials, production ledger, production database, VPS and paid provider calls were left untouched.


## Targeted corrections and final local validation (10 October 2026)

- Relevant offline API, privacy, real-CV, live-runtime and observability suite: **263 PASS, 11 SKIP, 0 FAIL** in 39.34 s. The 11 skips are PostgreSQL integration cases without the gated test database.
- Dedicated PostgreSQL integration run on a disposable `pgvector/pgvector:pg17` container with synthetic credentials, localhost port 15438 and tmpfs storage: **11 PASS, 0 FAIL, 0 SKIP** in 1.88 s. The container was removed immediately afterward; existing CP2/owner databases and volumes were not used.
- Final focused observability plus real-CV API run: **62 PASS, 0 FAIL, 0 SKIP** in 3.50 s.
- Ruff: CI-selected `E9,F63,F7,F82` across `src scripts ui tests`: **PASS**; `F` across `src ui`: **PASS**; full Ruff on new observability files, dashboard script and tests: **PASS**. An unrestricted `ruff check src scripts ui tests` is **FAIL** with 1,852 repository-wide style violations, many in unrelated legacy files. No broad formatting or frozen-file edits were performed.
- D-087 freeze: **PASS**, `ok=true`, `changed_files=[]`. `git diff --check`: **PASS**.
- Synthetic monitoring Compose merge: **PASS** with Prometheus on `default` and `jobfit_observability`; Grafana and Node Exporter stayed on `default`. Actual VPS Compose was not accessed; that validation is **STILL PARTIAL**.
- Synthetic file-provisioned dashboard merge: **PASS** for UID, four original panels and exact Prometheus datasource reference. Actual VPS provisioned file and Grafana rendering remain **STILL PARTIAL**.
- Public-beta release gates (Langfuse, deployed privacy/canary, restore exercise) are **DEFERRED TO PUBLIC-BETA GATES**. Backup-age visibility is **MISSING** in this narrow correction scope.

## Final Docker network compatibility correction (10 October 2026)

- Owner read-only VPS inspection reported API on `application_net` and `database_net`, DB on `database_net`, UI on `application_net`, and Prometheus/Grafana/Node Exporter on `monitoring`. Actual Compose files were not copied or opened locally.
- Corrected the monitoring override from `default` to `monitoring`, and made the API override explicitly retain both original API networks. Both connect to the same external network named `jobfit-observability`.
- Local `docker compose` v5.1.3 merged the untracked production API Compose reference with the corrected API override: API=`application_net,database_net,jobfit_observability`, DB=`database_net`, UI=`application_net`. Existing published ports were byte-for-byte unchanged in parsed configuration; DB remained on an internal network without a published port. **PASS**.
- A temporary three-service monitoring fixture matching the owner-reported `monitoring` network merged with the corrected monitoring override: Prometheus=`monitoring,jobfit_observability`, Grafana=`monitoring`, Node Exporter=`monitoring`. Existing published ports were unchanged and the external network name was exact. **PASS**. This is not a validation of the actual VPS monitoring Compose.
- The read-only token bind mount needs a host file readable by Prometheus's mapped numeric UID (`nobody`, usually 65534). A root-owned `0600` file is incompatible; no production file or permission was changed. README documents a restrictive `0400` owner-UID option and its security tradeoff. Actual VPS UID mapping, token-file metadata, and in-container read test remain **STILL PARTIAL**.
