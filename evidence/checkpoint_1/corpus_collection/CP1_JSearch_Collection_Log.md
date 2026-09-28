> **EDA audit update, 26 September 2026:** Collection stays closed. The numbers below are the history at collection time; the latest EDA composition follows `data/processed/CP1_research_summary.json` and `docs/checkpoint_1/supporting/CP1_Research_Audit.md`. Corrections to location, zero-year experience, dates and interpretation do not change the raw/snapshot data.

# CP1.1F: JSearch initial corpus collection log

**Date started:** 25 September 2026  
**Target:** 50-100 usable, deduplicated AI/ML/Data/Software-AI job postings, Indonesia-first.  
**Source status:** JSearch provisional; Techmap access unresolved. See [source decision](../provider_benchmark/CP1_Provisional_Source_Decision.md).

## Starting point

- Archived JSearch benchmark: 8 response files, 40 result slots, 36 distinct company/title/location combinations by a preliminary heuristic.
- Account quota snapshot: 14/200 monthly requests used, 186 remaining on 25 September 2026. See [screenshot](../provider_benchmark/jsearch/CP1_JSearch_Quota_20260925_Screenshot.png).
- Benchmark results are seed evidence, not yet a cleaned final corpus.

## Query log

| Collection ID | Query | country | language | num_pages | State | Raw slots | Usable new jobs | Response / screenshot |
| --- | --- | --- | --- | ---: | --- | ---: | ---: | --- |
| COL01 | `Data Scientist in Bandung` | `id` | `id` | 1 | AUDITED, 200 OK | 4 | 1 core conditional; 1 hard-negative candidate | [JSON](./CP1_JSearch_COL01_DataScientist_Bandung_ID_Response.json) / [screenshot](./CP1_JSearch_COL01_DataScientist_Bandung_ID_Screenshot.png) / [audit](./CP1_JSearch_COL01_Audit.md) |
| COL02 | `Data Scientist in Surabaya` | `id` | `id` | 1 | AUDITED, 200 OK | 4 | 0 confirmed core; 2 adjacent Data Analyst candidates on hold | [JSON](./CP1_JSearch_COL02_DataScientist_Surabaya_ID_Response.json) / [screenshot](./CP1_JSearch_COL02_DataScientist_Surabaya_ID_Screenshot.png) / [audit](./CP1_JSearch_COL02_Audit.md) |

## Audit after each response

Record the actual HTTP/result status and the returned count. Inspect role relevance, location, seniority, full-description quality, source/apply URL, posting-date reliability, and overlap with earlier queries. Keep the raw text and provenance. A repeated posting or a short/polluted JD does not count automatically toward the 50-100 usable-job target. If the response is zero or an error, keep the evidence and record it as a query/coverage finding.

Do not store API keys in response files or screenshots.

For later scripted collection, the evidence standard is raw JSON plus request metadata, checksum, and audit. Screenshots are optional for exceptional UI/billing failures, not required for every successful API call. See [cost and evidence policy](../../../docs/checkpoint_1/supporting/CP1_JSearch_Cost_and_Evidence_Policy.md).

## Pilot 01 (26 September 2026)

I ran 12 scripted search requests: HTTP 200/OK on every archived response, six empty queries, 47 raw slots. Checksums, request IDs, echoed parameters, and counts were verified. The combined inventory now covers 22 responses / 95 raw slots; the final accepted count is still pending. The full local JD review and deduplication findings are in the [Pilot 01 audit](./CP1_JSearch_Pilot01_Audit.md) and the [per-record review](./CP1_JSearch_Pilot01_Record_Review.json).

Basic with 200 remaining was reported before this run; 188 after the 12 searches is an estimate, not a new account observation. Batch 02 (12 requests maximum, Free/Basic only) has been prepared but not run. CP1.1F stays active; Techmap stays deferred and the provider selection stays provisional.

## Quota dashboard confirmation (26 September 2026)

My dashboard screenshot confirms Current Plan Basic, 200 requests/month, Quota Used 12 (6%), Remaining 188/200, reset 26 October 2026. The API Usage Last 30 Days panel separately shows Total Requests 28; do not subtract 28 from the active-period quota or assume all numbers use the same period. The cause of the period/counting difference has not been verified yet.

Evidence: [dashboard after Pilot 01](./CP1_JSearch_Quota_AfterPilot01_20260926.png). The earlier estimate of 188 remaining is now supported by an account screenshot at the time it was taken; the runner still checks the latest usage before running.

Strategy I confirmed: use the free quota first, then switch to PAYG myself if still needed. Use the remaining quota for productive queries and for variations not covered yet; evaluate each batch before scaling up. No upgrade or paid request was run. When this folder was checked, there were no B02 responses yet; the next step is still to run the prepared batch 02 runner.

## Batch 02 revision before execution (26 September 2026)

The B02 manifest was revised to **v2** before any request was sent; v1 is archived as `data/research/CP1_JSearch_Batch02_Plan_v1_superseded.json`. Reason: three v1 queries already have unprefixed answers in the archive (`Data Scientist in Surabaya` = COL02, 4 slots; `Machine Learning Engineer in Jakarta` = JS-03D, 10 slots; `Machine Learning Engineer in Indonesia` = JS-03A, 0 slots), so repeating page 1 would most likely return only jobs that are already known.

v2 contents (still at most 12 requests, free-only): 7 new Indonesian queries without a seniority prefix, 1 remote MLE query (paired with REMOTE_MLE_JUNIOR), and 4 **page 2 cursor** continuations of productive benchmark queries (AI Engineer Indonesia, MLE Jakarta, DS Jakarta, GenAI Jakarta) using the cursors saved in the benchmark JSON. The cursor continuations run last because the 25 September cursors may have expired; a failure stops the run without retry (safe design).

The collector supports the optional manifest fields `start_cursor_file` and `start_page`; the metadata records `cursor_used` and `cursor_source`. This logic was tested locally with mock responses (no API request).

## Batch 02 v2 (run 26 September 2026)

12/12 requests succeeded; 80 raw slots; 67 new by strict keys (estimated ±57 distinct jobs after probable duplicates). The saved cursors were valid; remote with `country=id` stayed at 0. 35% of the JDs are aggregator summaries of ±500 characters. Details: [B02 audit](./CP1_JSearch_Batch02_Audit.md). Inventory: 34 files / 175 raw slots. Estimated remaining quota: 176.

Batch 03 (24 requests, free-only) was prepared with the generic runner `scripts/run_jsearch_batch.py`; the collector now supports `max_pages` per query for chained pagination.

## Batch 03 (run 26 September 2026)

23 requests used (page 4 of AI Engineer Indonesia was skipped automatically because page 3 was empty); 131 slots; 96 new clusters, 65 of them with full JDs; 6 empty probes. Estimated remaining quota: 153. Corpus builder `scripts/build_corpus.py` added. Snapshot: 306 slots → 250 distinct jobs (239 after probable duplicates) → **162 auditable candidates**. Details: [B03 audit](./CP1_JSearch_Batch03_Audit.md). Batch 04 (34 requests, free-only) prepared.

## Batch 04 (run 26 September 2026)

34 requests; 208 slots; 136 new clusters (107 full JDs). Dashboard: 119/200 remaining. Snapshot: 514 slots → 386 clusters → **259 auditable candidates**. Indonesia shows saturation; foreign/contrast are productive. Details: [B04 audit](./CP1_JSearch_Batch04_Audit.md). A `num_pages=3` test (B05A, 1 request) was prepared before the large B05 batch; the collector now reports the quota used after each run.

## B05A num_pages=3 test: attempt 1 failed (timeout), 26 September 2026

The `num_pages=3` request (MLE Singapore) stopped with `TimeoutError` at the 45-second limit; no file was saved; quota check after the run: 0 units used (before 119, after 119; provider usage can lag). Interpretation: the multi-page request is processed sequentially on the provider side and goes over the one-page timeout. This does not yet answer whether bundling is cheaper. Fix: the collector timeout is now `min(180, max(45, 50 × num_pages))` seconds and is recorded in the metadata. The test is repeated once; if it fails again, bundling is dropped and batches use `num_pages=1`.

Batch 05 (±85 requests, free-only) was prepared with `num_pages=1`, leaving ±30 requests for B06, to be targeted after the audit.

## B05A num_pages=3 test: attempt 2 succeeded, 26 September 2026

Quota before attempt 2: **116** (not 119). This means the timed-out attempt 1 was still charged **3 units**; the earlier "0 used" figure was provider usage lag. Attempt 2: 27 slots in 7.1 seconds, charged **3 units** (116 → 113).

**Conclusion:** on the Basic plan, `num_pages=N` charges N quota units. Page bundling does not save quota; it only reduces the number of calls. Decision: the next batches stay at `num_pages=1` with cursors (more controlled: it stops automatically on an empty page). Correction to the attempt 1 interpretation: the timeout was more likely a short slowdown on the provider side (attempt 2 took only 7 seconds), not only because of multiple pages. **Timed-out requests are still billed**; the collector still has no automatic retry. Total test cost: 6 units for 27 slots.

## Batch 05 (run 26 September 2026, stopped at request 66)

66/84 requests sent; safe stop because of HTTP 500 on the remote MLE cursor continuation (B03). 410 slots; 310 new clusters. Remaining quota 48 (dashboard 76% used). Snapshot: 951 slots → 721 clusters → **497 auditable candidates** (Indonesia 293 · foreign 159 · remote_unverified 45). Details: [B05 audit](./CP1_JSearch_Batch05_Audit.md). Resume manifest (17 requests, without the failed probe) prepared.

## B05 resume + Batch 06 (run 26 September 2026, free quota used up)

B05 resume: 15 requests (14 units). B06: 31 requests (31 units). Remaining free quota: 2. Snapshot: 1,238 slots → 887 clusters → **613 auditable candidates** (Indonesia 353 · foreign 201 · remote_unverified 59). Indonesia is saturated (±1.1 new full JDs/request). Details: [B06 audit](./CP1_JSearch_Batch06_Audit.md).

## PAYG cost ledger

| Batch | Max requests | Max cost (public rate US$0.005) | Cumulative max | My limit |
| --- | ---: | ---: | ---: | ---: |
| B07 (stopped at request 27, TimeoutError) | 27 sent | ≈US$0.14 (timed-out request assumed to be billed) | ≈US$0.14 | US$2.00 |
| B07 resume-trimmed (stopped at request 7, TimeoutError) | 7 sent | ≈US$0.04 | ≈US$0.17 | US$2.00 |

## Batch 07 (PAYG): stopped 26 September 2026; Indonesian stop rule met

Verified plan: Pay As You Go (remaining quota is not reported on this plan). 27 requests sent; request 27 (`MLOps Engineer in Surabaya`) hit **TimeoutError** after 45 seconds; the collector stopped without retry, as designed (earlier timeouts were shown to be billed). 26 responses saved: 27 slots, **6 new clusters, all with full JDs** → 0.23 new full JDs per request, 17 empty probes.

**Decision (stop rule set before B07):** Indonesian yield < 0.5 → Indonesian collection through JSearch is declared **saturated**. The rest of the Indonesian grid (47 probes), the industry probes, and the remote probes were **not sent**. The resume was trimmed to 27 requests: 20 contrast + 7 Indonesian cursor continuations whose last page still added ≥3 new full JDs. After the resume, the corpus is frozen for CP1. Snapshot before the resume: 1,265 slots → 893 clusters → 619 auditable candidates (Indonesia 359 · foreign 201 · remote_unverified 59).

## B07 resume: stopped 26 September 2026; collection closed

7 requests sent; request 7 (`QA Engineer in Jakarta`) hit **TimeoutError** again. That makes two timeouts in a row in B07, a sign of provider instability at that time. Cumulative PAYG cost ≈ **US$0.17** (34 requests, including 2 timeouts assumed to be billed) out of the US$2 limit.

**CP1 collection is closed** and the corpus is frozen at `data/interim/snapshots/CP1_20260926/` (records, canonical, the duplicate list for review, progress, and `SNAPSHOT_MANIFEST.json` with the SHA-256 of every raw file). Final snapshot: 1,314 slots → 937 distinct jobs (909 after 28 probable pairs) → **652 auditable candidates**. Provisional cross-tab (title): Indonesia target-family 218 · Indonesia adjacent/contrast 174 · foreign target 198 · remote_unverified 59.

## Post-collection (26 September 2026)

Duplicate review done (40 pairs: 29 SAME, 8 DIFFERENT, 3 UNSURE) → **910 final jobs, 632 auditable candidates**; see [CP1_Dedup_Review.md](./CP1_Dedup_Review.md). Inventory and data contract: `docs/checkpoint_1/supporting/CP1_Dataset_Inventory.md`, `docs/data-contract.md`. Cleaning through EDA: `notebooks/01_research.ipynb` (one notebook); insights: `docs/checkpoint_1/supporting/CP1_EDA_Insights.md`.
