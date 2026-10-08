# Production Job Corpus and Sync

**Decision:** [D-098](decisions.md) · **Stage:** [CP3.2](checkpoint_3/CP3_02_Database_and_CICD.md) · **Status:** PLANNED / NOT YET IMPLEMENTED (7 Oct 2026)

This document describes the job database that the public JobFit deployment will search, and how it will stay fresh. Nothing here has been built or run yet. When parts are implemented and tested, the status lines below change and the evidence is linked from the CP3.2 report.

## 1. Two corpora, kept apart

| | Frozen CP2 evaluation corpus | Mutable CP3 production corpus |
| --- | --- | --- |
| Contents | Snapshot `CP1_20260926` (632 auditable jobs), split manifest, gold labels, freeze receipts | The VPS PostgreSQL database |
| Built by | `scripts/load_snapshot_to_db.py` with `SCHEMA_SQL` in `src/jobfit/db/models.py` (unchanged) | Alembic migrations, a one-time seed, then the sync |
| Changes | Never. D-087 and D-089 lock it | Twice a month through the sync |
| Used for | Reproducing CP2 results | Public recommendations |

Production code never writes to CP2 evaluation paths (`evals/freeze/`, `evals/gold/`, `evals/results/`, `evals/splits/`, the snapshot). A CI test will check that the sync module neither imports nor writes them. **CP2 held-out and test labels are never used** for prompt, threshold, ranking, model-selection or retrieval tuning (D-046 rule 4, D-089), even though historical test jobs are served in production.

**Pasted job descriptions are not corpus input (8 Oct 2026, D-102).** A JD that a user pastes for "Check a Job" is a session or request input only. It is never inserted into the production corpus automatically; the corpus changes only through the seed and the controlled sync below, with dedupe, provenance and lifecycle rules.

**Beta priority (8 Oct 2026, anti-overengineering correction under D-102).** The seeded production corpus (632 rows; 428 target-role jobs active) is sufficient for the CP3 controlled public beta. The sync automation in sections 3 to 5 (query manifest, `jobfit.jobs.sync`, forced-command SSH trigger, scheduled `job-sync.yml`) and the dedupe-review automation are P2 (post-beta). The design stays as written. A one-time, operator-run refresh with the same dedupe and provenance rules may be done before the demo if needed.

## 2. Seed

- **Source:** a `pg_dump` of the verified local database (632 CP1 rows with Qwen3-Embedding-8B vectors). Its SHA-256 and row counts are recorded, and it is restore-tested before the first deployment.
- **Steps:** restore, then `python scripts/db_baseline.py verify` (read-only, must report `ok`), then `python scripts/db_baseline.py stamp` (guarded and locked; the app is stopped and schema changes are made only through JobFit tooling), then `alembic upgrade head`, then the seed command. A bare `alembic stamp` is never used, and a verification mismatch stops for a decision; the database is never force-stamped. The Alembic revisions exist since 8 Oct ([CP3.2 report](checkpoint_3/CP3_02_Database_and_CICD.md#results-8-oct-2026-alembic-00010002)); the seed command does not exist yet.
- **Active rows:** the 428 target-role rows (dev and test) are set active and retrievable. The 204 non-target rows stay in the table but are excluded from retrieval, as in CP2: they are seeded inactive with `inactive_since` NULL, so the 60-day hard delete (which applies only to rows the sync deactivated) never removes them.
- **Dedupe status:** all 632 rows get `dedupe_status = 'canonical'`, because CP1 already deduplicated them with human review.
- **Provider identity:** `job_sources` rows come from the snapshot's canonical file, one per CP1 member record. `first_seen_at` and `last_seen_at` come from the processed features.

## 3. Query manifest (new requirement)

The CP1 collection used research manifests (`data/research/CP1_JSearch_Batch0*_Plan.json`). There is no stable production manifest, and without one a scheduled sync is not reproducible.

- **File:** `config/sync/jsearch_production_v1.json`, with the same schema as the CP1 batch manifests (query_id, query, country, language, work_from_home, num_pages, `max_requests`, `free_only`).
- **Queries:** chosen from the CP1 target-role probes with the best target yield.
- **Cap:** at most 80 requests per sync, so two syncs a month fit the 200-requests-a-month free tier. The pay-as-you-go fallback is about US$0.40 per sync at US$0.005 per request.
- **Versioning:** the manifest is versioned, and its hash is written into every sync report.

## 4. Trigger and security boundary

- **Schedule:** `.github/workflows/job-sync.yml` with cron `23 19 1,15 * *` (UTC, about 02:23 WIB on the 2nd and 16th), plus `workflow_dispatch` and a `concurrency` group.
  - This is **twice a month, roughly every two weeks**; it is not exact 14-day scheduling. The gap of 13 to 17 days fits the lifecycle rules below.
  - Scheduled workflows only run from the default branch, so the schedule starts after Dion merges CP3 into `main`. Until then, syncs are triggered by hand over SSH.
- **GitHub secrets:** only `SYNC_SSH_KEY`, `SYNC_SSH_HOST` and `SYNC_SSH_KNOWN_HOSTS`.
- **On the VPS:** a dedicated `jobfit-sync` user whose `authorized_keys` entry is `restrict,command="/opt/jobfit/bin/run-sync"`. That script runs the one-shot sync container under `flock`.
- **Credentials:** `JSEARCH_API_KEY` and `DATABASE_URL` never leave the VPS.

## 5. Sync pipeline

The command is `python -m jobfit.jobs.sync --manifest … [--dry-run]`. It is non-interactive (the CP1 wrappers needed a terminal).

1. **Lock and open a run.** Take the lock and open a `sync_runs` row with the manifest hash and the code version.
2. **Fetch.** Check JSearch usage before and after. Paginate as the manifest says, with no automatic retry of billed requests, and record each query as `completed` or `failed`.
3. **Normalize.** A new `jobs/normalize.py` reuses the functions in `jobs/corpus.py` and `jobs/transform.py` to produce:
   - the clean description;
   - `content_hash`;
   - the normalized title;
   - role family and role group;
   - years and experience bucket;
   - language;
   - `jd_quality`;
   - skills.

   Only auditable records become candidates. A parity test on committed fixtures compares the output with the CP1 features.
4. **Exact dedupe inside the batch.** Use the CP1 exact keys (union-find, as in `corpus.cluster_exact`). Within each cluster, one record is canonical (best JD quality, then longest description); the others count as `duplicate_exact`.
5. **Exact identity match against the database.** Try the keys strongest first:
   1. `(source, source_job_id)` in `job_sources`, which is unique on that pair;
   2. the normalized apply URL;
   3. `content_hash`;
   4. company, title and place.

   - **A hit** maps the observation to the existing canonical job. No new `jobs` row is created; the observation is upserted into `job_sources`.
   - **A miss** creates a candidate with `job_id = 'J' + sha256(source|source_job_id)[:16]`.
6. **Fuzzy duplicates (new candidates only).** Use the CP1 rules: same company with title Jaccard ≥ 0.6, or JD 5-gram Jaccard ≥ 0.5, checked against active canonical jobs and within the batch.
   - A suspect is **not merged**. It is stored with `dedupe_status = 'review_required'`, `is_active = false` and `dedupe_suspect_of`, so it stays out of public retrieval.
   - A small command resolves it: `python -m jobfit.jobs.dedupe_review --job <id> --same|--different`.
7. **Classify each job:**
   - **NEW:** no match and not suspected.
   - **CONTENT_CHANGED:** the clean JD text (`content_hash`) or the title changed. The job is re-embedded and its extraction cache entry is invalidated, and derived features are recomputed.
   - **METADATA_CHANGED:** for example the apply URL, publisher, source timestamps, company display, location or work mode changed. The row is updated with no re-embedding and no extraction invalidation. A test pins which fields belong to which list.
   - **UNCHANGED:** only `last_seen_at` and the query hits are updated.
   - **STALE / INACTIVE:** see step 9.
8. **Write.** One transaction covers jobs, `job_sources`, query hits, dedupe status and lifecycle. Any error rolls back.
9. **Lifecycle (coverage-aware).**
   - A job counts as missed only when a query that found it before *completed* in this sync, so a failed query never counts as a miss.
   - A job becomes inactive after 2 covered misses (about 4 weeks), after 30 days without being seen, or when a trusted provider expiration passes. No expiration field was seen in the CP1 responses; this will be checked again on a live response.
   - Inactive jobs are excluded from retrieval.
   - After 60 days inactive, the job, its vectors and its cache rows are hard-deleted.
   - This is a project policy for JobFit, not an industry rule.
10. **Embeddings.** Only canonical NEW and CONTENT_CHANGED jobs are embedded, and `review_required` suspects are not. The step can be resumed. It has a US$0.10 cap per sync, at about US$0.0000064 per job.
11. **No JD extraction during the sync.** Extraction is lazy (section 7).
12. **Report.** Write counts to `sync_runs` and a JSON file in `/var/lib/jobfit/sync_reports/`:
    - pages and requests;
    - jobs fetched, new, content_changed, metadata_changed, unchanged, deactivated, deleted, duplicate_exact and review_required;
    - embeddings queued, completed and failed;
    - the error code.

    Per-job details go only to structured logs.

**Production retrieval filter:** `is_active AND dedupe_status = 'canonical' AND role_group = 'target'`, plus a current embedding. The same vacancy must never appear twice in retrieval.

## 6. Recovery

- **Re-run:** dispatch the workflow or run the script on the VPS. Re-running is safe because the sync is idempotent.
- **Partial fetch:** the failed queries are treated as not covered.
- **Quota exhausted:** the sync aborts before any lifecycle update.
- **Embedding failure:** the next run retries.
- **Schema migrations:** take and verify a backup first. Downgrade is not a recovery path; recovery means the previous app tag plus a database restore.

## 7. Lazy JD extraction cache

- **Storage:** the table `jd_extraction_cache`, keyed by the existing `ExtractionCache` key. That key covers content hash, model, prompt, schema, guideline, scope and context, so a changed JD automatically misses.
- **Lookup:** a hit with status `ok` is used. A miss runs the frozen `extract_jd` with the frozen configuration (DeepSeek Flash, JD prompt v1.4), validates the result and stores it. A failure is cached for 7 days so a broken JD is not paid for again and again.
- **Prefetch:** runs in parallel (cap 5) before `recommend()`, under the recommendation budget reservation ([D-096](decisions.md)).
- **Seed:** only the development saved extraction records. CP2.4 test-run extractions are not copied.

## 8. Monitoring

Gauges read from the latest `sync_runs` row: last success time, status, duration and job counts by outcome. There are no job IDs in labels. Alerts fire when the last sync failed or when there has been no successful sync in 16 days ([D-099](decisions.md)).

## 9. Planned tests

- normalization parity;
- identity-match order;
- exact-duplicate ingestion is idempotent and creates no second row;
- a fuzzy suspect is `review_required`, inactive and not retrieved;
- **the same vacancy never appears twice in retrieval;**
- a second run on the same fixture gives 0 NEW, 0 CONTENT_CHANGED and 0 METADATA_CHANGED;
- CONTENT_CHANGED re-embeds and invalidates the extraction, while METADATA_CHANGED does neither;
- the coverage rule;
- lifecycle thresholds with a frozen clock;
- transaction rollback;
- a dry run writes nothing;
- a database-gated end-to-end test on a pgvector service in CI;
- no writes to CP2 paths.
