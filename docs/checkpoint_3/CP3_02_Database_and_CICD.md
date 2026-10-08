# CP3.2: Database Integration and CI/CD

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 16. Integrasi Database & GitHub Actions CI/CD · official date 6 Oct 2026  
**JobFit version of this checkpoint:** PostgreSQL with pgvector, and GitHub Actions for CI/CD.  
**Planned work:** 6 Oct 2026 (hosting smoke deploy earlier, on 1-2 Oct) · **Actual:** 6 Oct 2026  
**Status:** PARTIAL · Docker and compose work locally; CI green since Phase 1 (7 Oct, FAIL-35 resolved); Alembic `0001`/`0002` DONE with migration tests (8 Oct); SumoPod VPS and job sync PLANNED (D-095, D-098); nothing deployed · design basis: System Design v1.3

> Plan sections are kept as written. Results are added below, with links to the [experiment log](../experiments.md). The plan for all stages is in the [master plan](../master-plan.md).

## CP3 final plan for this stage (7 Oct 2026, D-095 to D-100)

**JobFit scope:** production corpus, job sync, VPS and delivery. Everything in this section is **PLANNED / NOT YET VALIDATED** unless marked otherwise. Stage definition: [master plan](../master-plan.md#cp32-database-integration-and-cicd-checkpoint-16). Tasks: [CP3 execution plan](CP3_Execution_Plan.md). Corpus design: [production-corpus.md](../production-corpus.md).

- **Hosting change:** Railway (D-023) is replaced by a SumoPod VPS: Singapore, Ubuntu 24.04 LTS, 2 vCPU / 8 GB / 80 GB (D-095). Dion and Codex buy and configure it; this repository provides the deploy files and runbook. No Railway account was created.
- **Already done:** see "Results (6 Oct 2026)" below. CI was red because of FAIL-35 until Phase 1.
- **Phase 1 result (7 Oct 2026, commit `33c5584`, DONE):**
  - **FAIL-35 resolved (tests only):** the two raw-snapshot split tests skip when that git-ignored file is absent; the Phase A budget test sets its own budget values.
  - **CI workflow (`.github/workflows/tests.yml`):**
    - ruff pinned to 0.16.8;
    - the existing `E9,F63,F7,F82` check on `src scripts ui tests` kept;
    - a new `ruff check --select F src ui`;
    - a new CP2 freeze verify step (`prepare_cp23_freeze.py --verify`, which exits 2 on drift);
    - pytest, the Docker builds and the `/health` smoke check unchanged.
  - **Pyflakes fixes:** 6 behaviour-preserving fixes (5 unused imports and 1 f-string without placeholders) in `eval/development_gold.py`, `eval/run_eval.py`, `pipeline.py`, `support/cv_coach.py` and `viz/style.py`.
  - **Frozen-file exemption:** the two unused imports in the D-087 frozen files `cv/parser.py` and `llm/client.py` stay. `pyproject.toml` exempts F401 for exactly those two files, never globally.
  - **Not in scope:** `scripts/` and `tests/` still have 37 Pyflakes findings; they remain covered by the narrower `E9,F63,F7,F82` check.
  - **Results:**
    - offline pytest 672 passed / 11 skipped / 0 failed (683 tests);
    - ruff clean;
    - freeze verify `"ok": true`;
    - GitHub Actions run [37641393567](https://github.com/Gidion123/Job-Fit/actions/runs/37641393567) green (lint-and-test and docker-build).
- **Planned scope:**
  - **CI:**
    - re-apply FAIL-35 cleanly (DONE, Phase 1);
    - pin `ruff` plus `F` (DONE, Phase 1);
    - freeze verify (DONE, Phase 1);
    - prod compose config;
    - a pgvector service job (Alembic up, down/up where reversible, database-gated tests);
    - the internal `e2e_check` against compose.
    - No provider secrets in CI.
  - **Database (D-098):**
    - minimal Alembic (`0001` = the current `SCHEMA_SQL`; `0002` = lifecycle, `dedupe_status`, `job_sources` unique on `(source, source_job_id)`, `sync_runs`, extraction cache, quota, reservations);
    - upgrade only after a verified backup;
    - recovery = the previous tag plus a restore.
    - The CP2 `SCHEMA_SQL` and loader stay unchanged.
  - **Seed:** a restore-tested dump of 632 rows. The 428 target-role rows are active; all rows are canonical.
  - **Sync:**
    - twice a month (about every two weeks) through a GitHub Actions SSH forced command; credentials stay on the VPS;
    - a production query manifest (≤ 80 requests);
    - exact duplicates map to the canonical job with no new row;
    - fuzzy suspects are `review_required`, inactive and kept out of retrieval;
    - NEW / CONTENT_CHANGED / METADATA_CHANGED / UNCHANGED / STALE;
    - a coverage-aware lifecycle;
    - incremental embeddings;
    - a report.
  - **Deployment:**
    - `docker-compose.prod.yml` with Caddy (only 80/443 public), restart policies, log rotation and healthchecks;
    - a runtime artifact manifest and verifier (the tokenizer built into the API image);
    - a restore-tested initial dump; nightly backups;
    - manual tagged deploys;
    - a VPS runbook.
  - **Monitoring (D-099):**
    - Prometheus, Grafana and node_exporter;
    - email alerts through `GRAFANA_SMTP_*` / `GRAFANA_ALERT_*` placeholders;
    - sync gauges;
    - a backup-age metric.
- **Validation layers:**
  - A: external public smoke through Caddy and Streamlit (HTTPS, saved demo);
  - B: the internal API `e2e_check.py` inside the VPS Docker network or through an SSH tunnel.
  - FastAPI is never exposed publicly.
- **Tests to add:**
  - Alembic on an empty and a restored database;
  - the sync suite (normalization parity, identity order, exact-duplicate idempotency, `review_required` exclusion, **the same vacancy never appears twice in retrieval**, classification, coverage, lifecycle, rollback, dry run, no CP2 path writes);
  - the artifact verifier.
- **Costs:** JSearch uses the free tier (≤ 80 requests per sync); embeddings cost about US$0.0000064 per job (capped at US$0.10 per sync); VPS hosting is outside the LLM budget.
- **Acceptance:** see the master plan, CP3.2 points 5 and 10.
- **Limitations:** no provider expiration data has been seen, so staleness is inferred from coverage and age. Link liveness is not checked.
- **Status:** PARTIAL. Nothing is deployed.

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

## 3A. D-051 persistence and deployment gate

Follow [privacy-threat-model.md](../privacy-threat-model.md). PostgreSQL/pgvector stores public jobs and explicitly synthetic demo data only for these paths, not private CVs, profiles, vectors, pasted JDs or reports. Audit feedback so it cannot silently retain document/contact payloads. Volatile private session storage must have persistence/backups disabled; adding a shared store or replicas needs an explicit isolation/retention design. Check Streamlit/FastAPI/proxy temporary upload copies, host logs/traces/crash dumps, backup volumes, TLS and server-only secrets.

- [ ] No private-data migration or durable cache introduced.
- [ ] Synthetic-canary inspection of database, logs, temporary files and hosting persistence.
- [ ] CI runs privacy regression tests; deployed cleanup and session routing match the documented topology.


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

D-051 privacy design is approved; implementation outcomes and release acceptance are pending. Record outcomes in the [decision log](../decisions.md) without treating design approval as a test pass.

## 13. Next step

CP3.3 (checkpoint 17): Streamlit UI.

## Results (6 Oct 2026)

- **Docker:** `Dockerfile.api` (saved demo works with no database and no model call; live analysis off by default), `Dockerfile.ui`, and api/ui/db services in `docker-compose.yml`, all bound to 127.0.0.1. Two start-up bugs were found on Dion's Mac and fixed (FAIL-29 path, FAIL-30 file permissions).
- **CI:** `.github/workflows/tests.yml` runs ruff (syntax and undefined names), the offline tests, both image builds and a `/health` smoke check. It starts only after Dion pushes; a local simulation without git-ignored files gave 615 passed, 9 skipped.
- **Database:** the job corpus, embeddings and search already run on PostgreSQL with pgvector (CP2.1). Changes from the plan, on purpose: the demo cache is a versioned file bundle (`evals/demo/saved_demo_v4/`, D-022 key checks), JD requirements stay versioned JSON records, and feedback lives in memory with categories only. No private CV data is ever written to the database (D-051).
- **Secrets:** only through environment variables (`.env` for local work, host variables for deployment); `.env` is git-ignored and excluded from the images.
- **Pending (needs Dion):** Railway account and cost confirmation (D-023), loading the corpus snapshot into the hosted database, and the first deploy. Without the hosted database the deployed app still serves the saved demo.

## Results (8 Oct 2026, Alembic 0001/0002)

Local and CI only. No production database exists yet, nothing is deployed, and the local CP2 evaluation database was not touched. No D-087 frozen file changed (freeze verify `"ok": true`), and no paid call was made.

### What was built (commits `c5a4100`, `eb8afa5`, `8a89a4c`, `fc9d236`, `a04a629`)

- **Alembic infrastructure:**
  - `alembic.ini`, `migrations/env.py`, `src/jobfit/db/migrate.py`; `alembic>=1.16,<2` in `requirements.txt`. SQLAlchemy was already a dependency.
  - **Raw SQL only:** no models and no autogenerate.
  - **Explicit URL:** the URL must be passed explicitly (`DATABASE_URL` or a programmatic config attribute). There is no fallback to the local development database, the URL is never printed, and it is converted to the psycopg 3 driver.
  - **Single transaction:** each command runs in one transaction, so a failed upgrade leaves no partial schema and no version row.
  - **No offline mode:** offline SQL generation is refused.
- **`0001` (exact CP2 baseline):**
  - It holds an immutable literal copy of today's `SCHEMA_SQL` (SHA-256 `38abfee0…50b3`) and never imports application code. `src/jobfit/db/models.py` and the CP2 loader are unchanged.
  - It refuses to run if `public` already holds any application object (table, view, sequence, function or type; extension-owned objects such as pgvector's are allowed). Such a database, including an existing CP2 database, is verified and stamped instead. The refusal rolls back the whole Alembic transaction, so no version table remains.
  - The downgrade drops the three tables. It runs only with `JOBFIT_ALLOW_DESTRUCTIVE_DOWNGRADE=1` and `JOBFIT_ENV != prod`.
- **Catalog verification and guarded stamp:**
  - **`src/jobfit/db/catalog.py`** (read-only) fingerprints the application schema in `public`: relations, columns (type, nullability, default, generated expression, identity, collation), constraints, indexes, triggers, functions, user types and extensions. Extension-owned objects are excluded.
  - **Alembic's version table is excluded only when it has exactly Alembic's structure.** Any other table of that name, or a look-alike such as `alembic_versions`, stays in the fingerprint and fails. The revision is checked separately by `revision_state()`, which returns `absent`, `empty`, `malformed` or the revision.
  - **`scripts/db_baseline.py verify`** is read-only. It compares the target with a reference built fresh on the same server: a scratch database upgraded to `0001`, fingerprinted, then dropped. It requires `revision_state = absent`.
  - **`scripts/db_baseline.py stamp`** (race-safe since the 8 Oct audit correction) runs on one dedicated connection:
    1. It takes the JobFit schema advisory lock at session level. `migrations/env.py` takes the same key in every migration transaction, so no cooperating JobFit migration can run until the stamp has finished, including its post-commit check.
    2. In one transaction it locks the three CP2 tables (`EXCLUSIVE`: no DDL or writes on them until commit). It re-validates the exact baseline with no version table, writes the version row through Alembic on the same connection, and validates again (revision `0001`, exact baseline) before committing. Any difference rolls the whole transaction back.
    3. After the commit, still holding the lock, it checks once more. On drift it removes the stamp only if it is provably its own: the same version table it created (same oid), holding `0001`, with a schema that really differs. In any other case (the revision changed, the table was replaced, or the difference has vanished on recheck) it changes nothing and reports a blocker (exit 3) for manual review.
    - **Assumption:** during the maintenance window the app is stopped and schema changes are made only through JobFit tooling. PostgreSQL cannot stop an unrelated session from creating new objects in `public`. Such drift is detected; the only way it could survive is a crash of the stamp process between its commit and its post-commit check.
  - Any difference fails closed, reported structurally with no row data. A pgvector version difference also fails unless `--allow-vector-version` is passed.
  - **Pinned fingerprints:** `migrations/catalog/0001.json` and `0002.json`. Neither contains `alembic_version`.
- **`0002` (additive production schema):**
  - **New `jobs` columns:** `is_active` (default false), `dedupe_status` (`canonical` / `review_required`), `dedupe_suspect_of`, `first_seen_at`, `last_seen_at`, `covered_miss_count`, `inactive_since`. Checks:
    - an active job is canonical, has seen times and has no `inactive_since`;
    - a suspect points at another job.
  - **New tables:**
    - `sync_runs`, with at most one `running` row;
    - `job_sources`, whose primary key is (`source`, `source_job_id`);
    - `job_query_hits`;
    - `jd_extraction_cache`;
    - `budget_reservations`;
    - `live_quota`, keyed by a 64-hex HMAC.
  - **No change to `0001`.** No `0001` column, constraint or index changes, so the frozen dense, full-text and hybrid search and the CP2 loader work unchanged (tested).
- **`jd_extraction_cache` state contract**, traced from the frozen `ExtractionCache` (only successes are `put`; `get` checks scope, key, a dict value and its hash):
  - **`ok`:** an object `value` and a 64-hex `value_hash`; no `error_code`, no `expires_at`.
  - **`failed`:** no value and no hash; an identifier-shaped `error_code`; `expires_at` later than `created_at` (the 7-day negative cache is decided by the Phase 3 provider from `expires_at`, so it is testable with a frozen clock).
  - **Deviation from the proposal:** the error-code pattern is `^[A-Za-z_][A-Za-z0-9_]{0,63}$`, not `^[A-Za-z_]{1,64}$`. `validated_call` can report any exception class name, and class names may contain digits. A test checks that every enumerable `StageFailure` code fits, and the database accepts all of them.
- **`budget_reservations`:**
  - `numeric(20,10)` amounts; no NaN, infinity, zero or negative reservation;
  - `phase` is `parse` or `recommendation`;
  - **`production_day`** defaults to the Asia/Jakarta date, and a CHECK requires it to equal the Asia/Jakarta date of `created_at` (audit correction). An explicit `created_at` therefore needs a matching `production_day`;
  - **`active_until timestamptz NOT NULL`** (audit correction) has no default. The reservation creator supplies it, and it must be later than `created_at`. It persists how long the reservation can still be active, so whether an earlier-day reservation still counts is decided from stored state, never from the current deployment's configuration;
  - `operation_key` is unique;
  - state checks: reserved means not closed; settled means closed with an amount; released means closed with exactly 0.
  - **A guard trigger** (an addition to the proposal):
    - keeps the identity, amount, `production_day`, `created_at` and `active_until` fixed while a reservation is open;
    - makes a closed reservation immutable, so a settled reservation can never be rewritten as released;
    - forbids deleting an open reservation, so it always keeps counting.
  - **What the database cannot prove:** it has no access to the authoritative production ledger, so it cannot show that a reservation had zero ledger spend and no `uncertain_upper_bound` record. That check, before any release, belongs to Phase 2B (see below).
- **`src/jobfit/db/lifecycle.py`** (an addition, used by the retention test) holds the production retrieval filter and the 60-day hard delete. It deletes the versioned vectors first, because the `0001` foreign key has no cascade, and never touches rows with `inactive_since` NULL. Those are the retained non-target CP1 rows, which the seed leaves inactive.
- **CI:**
  - a `db-migrations` job runs the offline and database tests against a disposable `pgvector/pgvector:pg17` service; its password exists only inside that job;
  - the API image now carries `alembic.ini`, `migrations/` and `scripts/db_baseline.py`, and CI checks `alembic heads` inside it.

### Test results

**Offline (every CI run):** 14 tests. They cover:
- the revision chain;
- the immutable literal and its hash;
- no application imports in the revisions;
- the explicit URL;
- the downgrade guards;
- every `StageFailure` code against the cache constraint;
- the pins;
- `0002` as a strict addition to `0001`.

**Database-gated** (`tests/test_migrations_db.py`): 53 tests in the first version, 69 after the 8 Oct audit corrections. All passed locally on PostgreSQL 16.15 with pgvector 0.6.0, and in CI on PostgreSQL 17.11 (`pgvector/pgvector:pg17`):
- first version: 67 passed, 0 skipped, offline and database together (run [37720321946](https://github.com/Gidion123/Job-Fit/actions/runs/37720321946));
- after the corrections: 83 passed, 0 skipped (run [37727182136](https://github.com/Gidion123/Job-Fit/actions/runs/37727182136)).

The pins were generated on PostgreSQL 16 and match PostgreSQL 17 exactly:

| Area | Tests |
| --- | --- |
| Exact baseline | Empty database upgrades to the pinned `0001` then `0002`; raw `SCHEMA_SQL` equals Alembic `0001` once the version table is excluded |
| Verify and stamp | A CP2-shaped database with rows verifies, stamps (revision `0001`, schema unchanged) and upgrades to `0002` with identical rows, vectors and search vectors |
| Fail closed | 15 mismatches are never stamped and nothing is written:<br>• index missing or extra; extra column<br>• nullability, vector type, CHECK, default, generated column, FK action<br>• extra table; a look-alike version table; extra function<br>• empty, stamped and malformed version tables<br>An empty database without the extension also fails |
| `0001` guard | An existing CP2 database is refused and left unchanged, with no version table |
| Frozen-code compatibility | Dense, full-text and hybrid search give identical results on `0001` and `0002`; the CP2 loader still works |
| `0002` constraints | Lifecycle and dedupe; sources and sync runs; 23 invalid partial cache states rejected, both complete states accepted; reservation amounts, states, immutability and the release-means-zero rule; cascades (versioned vectors must be deleted explicitly) |
| Reservation lifetime and day (audit) | `active_until` required, accepted when later than `created_at`, rejected when equal or earlier, immutable while open and after closing. `production_day` equals the Jakarta date of `created_at`: default insert accepted, inconsistent day rejected, and at the boundary 16:59:59.999999 UTC belongs to 8 Oct while 17:00:00 UTC belongs to 9 Oct; still immutable |
| Guarded stamp (audit) | The `verify` report contract is unchanged. Drift committed between the stamp's validation and its version write rolls the stamp back (no version table). DDL on a CP2 table during the stamp is blocked. **Two connections:** a normal `alembic upgrade` waits on the advisory key until the stamp's post-commit check has finished, then upgrades to `0002`. Post-commit drift removes only the stamp's own version table. An advanced revision, a replaced version table, or a difference that vanishes on recheck are all left untouched (blocker) |
| `0001` fresh guard (audit) | A stale table, sequence, view, function or enum type makes `0001` refuse, with nothing created and no version table. A database holding only the pgvector extension upgrades to the pinned `0002` |
| Retention | The 60-day cleanup deletes only the expired lifecycle-managed row. Both retained non-target rows survive and are never retrieved |
| Quota | Two concurrent ticket consumptions for one IP: exactly one succeeds, both from no row and from a row older than 24 hours |
| Downgrade | Refused without the flag and under `JOBFIT_ENV=prod`; with the flag, `0002 → 0001 → base → head` returns to the pinned schemas |

### Recorded for Phase 2B (not implemented)

- **Admission:** `settled_spend_today + outstanding + new_bound <= daily cap`, under a transaction-level advisory lock.
  - Outstanding counts:
    - every `reserved` row of today, including crashed rows, until the end of its day;
    - earlier-day `reserved` rows while their persisted `active_until` is in the future.

    In SQL terms: `status = 'reserved' AND (production_day = today_jakarta OR active_until > now())`.
  - The reservation creator sets `active_until` at insert from its enforced operation deadline plus `request_timeout_seconds` (240 s, frozen v4). Later configuration changes never change an existing reservation's meaning.
- **Settlement order:** provider call → durable ledger record (`UsageLedger.append` fsyncs; the frozen client writes one record per call, including `uncertain_upper_bound` on failure) → database settle or release.
  - A crash in between double-counts spend, which is acceptable and fails closed.
  - Settle or release by ledger evidence. Ledger spend above zero, or any `uncertain_upper_bound` record, means **settled**. Only zero spend with no uncertain billable record may be **released**. The database enforces only that a release records exactly 0 and that closed rows never change.
  - Crash tests:
    - a kill after the ledger write;
    - a kill before any call;
    - an attempt to settle while a call is in flight;
    - an attempt to settle with a ledger record missing.
- **Per-call refusal:** before forwarding, the 2B wrapper refuses any call whose exact guard input bytes exceed the modelled attempt (`phase_bounds.guard_input_bytes` against `ChainSpec.attempt_input_bytes`).
- **Ticket:** consumed by the single conditional upsert tested above, only at the first billable parse; the owner token never calls it.

**CI:** run [37720133032](https://github.com/Gidion123/Job-Fit/actions/runs/37720133032) (`fc9d236`) and run [37720321946](https://github.com/Gidion123/Job-Fit/actions/runs/37720321946) (`a04a629`: lint-and-test, db-migrations, docker-build with `alembic heads` = `0002 (head)` inside the API image) both passed.

**After the audit corrections** (`4f45cd4`, `801f0bd`), run [37727182136](https://github.com/Gidion123/Job-Fit/actions/runs/37727182136) passed all three jobs. Locally the default suite gives 809 passed, 80 skipped (the 69 gated database tests skip without a server), 0 failed; ruff is clean and freeze verify is `"ok": true`.

### Not done yet

- `db_baseline.py verify` has not been run on Dion's local CP2 database (the seed source). It must pass before any seed. A mismatch stops for a decision and is never force-stamped.
  - `verify` opens that database read-only.
  - It builds its reference in a separate scratch database on the same server, created and dropped by `verify`, which needs the CREATEDB privilege.
  - The CP2 database itself is not modified.
- There is no production database, backup or restore yet.
- The sync, the seed command, the extraction-cache provider and all Phase 2B runtime work are still to do.
