# CP1.1E: Provisional job-data source decision

**Project:** JobFit Intelligence  
**Date:** 25 September 2026  
**Decision status:** PROVISIONAL for the initial Checkpoint 1 corpus; final primary-provider selection remains OPEN.

## Problem and planned comparison

Checkpoint 1 needs 50-100 real AI/ML/Data/Software-AI job postings with usable descriptions and provenance. The approved sequence was to compare JSearch and Techmap through actual queries before selecting the primary provider. JSearch has been benchmarked; Techmap's API subscription is blocked at RapidAPI checkout. See [Techmap access report](./techmap/CP1_Techmap_Access_Blocker_Report.md). A quality comparison between the two providers is therefore not possible yet.

## Evidence audited locally

Eight JSearch response JSON files and eight screenshots are present in `jsearch/`. The response parameters and job counts were read from the JSON files, not inferred from the file names.

| Audit item | Finding |
| --- | ---: |
| Requests represented | 8 |
| Requests with 10 results | 4 |
| Requests with zero results | 4 |
| Total result slots | 40 |
| Distinct normalized company + title + location combinations | 36 |
| Repeated combination groups | 4 |
| Results with nonempty `job_description` | 40/40 |
| Descriptions shorter than 500 characters | 8/40 |
| Results with nonempty `job_apply_link` | 40/40 |
| Results with structured `job_posted_at_datetime_utc` | 0/40 |
| Results with `job_city` | 7/40 |
| Results with `job_country` | 7/40 |

The 36 distinct combinations are a **heuristic**, not a final unique-job count. All 40 `job_id` values are distinct, yet four company/title/location combinations repeat across queries. Deduplication must use additional URL/content checks. A nonempty description is not proof of a complete, clean JD. The eight short descriptions need review. Structured posting timestamps are absent in this sample; `first_seen_at` must not be used in place of `posted_at`.

The `JS02` JSON and PNG file names have their `Response`/`Screenshot` suffixes reversed. Their file types and contents are valid; correct the names or document this discrepancy before using them in a formal evidence index.

The previous handoff also records wrong-role and seniority contamination, query localization/city sensitivity, and cross-query duplicates. Those observations are still relevant but were not relabeled in this audit.

### Account quota snapshot

My OpenWeb Ninja dashboard screenshot on 25 September 2026 shows an active JSearch BASIC plan with **14 of 200 requests used**, leaving **186 requests** in that displayed period; the dashboard says the quota resets in 25 days. The screenshot is saved as [quota evidence](./jsearch/CP1_JSearch_Quota_20260925_Screenshot.png). Eight benchmark JSON responses are archived here; the dashboard's other six calls are not represented by these eight files and are not counted as additional benchmark results.

## Alternatives and trade-offs

| Option | Benefit | Cost or limitation |
| --- | --- | --- |
| Wait for RapidAPI support and the Techmap test | Keeps the original side-by-side comparison | Delays the corpus, cleaning, EDA, and the 27 September CP1 presentation |
| Start an unrelated marketplace API benchmark | Could add another source candidate | New criteria/terms and setup; no evidence it will improve Indonesia AI/ML coverage |
| Use JSearch for the initial corpus while Techmap stays pending | Accessible source with real Indonesia results and saved responses | Query sensitivity, duplicates, weak structured dates/location, variable JD quality; no final comparative score |

## Decision

Use **JSearch as the provisional collection source for the Checkpoint 1 sample**, subject to its account quota and source terms. Keep Techmap as an unbenchmarked candidate. Do **not** label JSearch the final primary provider, produce a JSearch-vs-Techmap weighted score, or treat the Techmap checkout failure as data-quality evidence.

This is a documented exception to the handoff's original instruction to complete the actual Techmap benchmark before corpus collection. The user asked to skip the blocked Techmap test for now. The exception protects the 21-day critical path while making the missing comparison visible in the CP1 documentation. Revisit the provider decision if RapidAPI support restores access or Techmap supplies a relevant sample.

## Collection conditions for CP1.1F

1. Check the live JSearch request quota before collection batches. The 25 September dashboard snapshot shows 186 remaining; this may change after new calls. The [public JSearch page](https://www.openwebninja.com/api/jsearch) advertises a direct-portal free tier, but the user's account is the authority for the available quota.
2. Record each query, the country/language/city parameters, request time, response file name, and raw result count.
3. Keep the provider, publisher, source/apply URL, raw JD, location text, and raw posting-date text. Keep `posted_at` unknown when no reliable structured timestamp exists.
4. Dedupe across queries and assess JD completeness before counting 50-100 usable jobs.
5. Keep API keys out of JSON evidence, screenshots, code, and logs. Review the source/redistribution terms before publishing a raw corpus. See [OpenWeb Ninja terms](https://www.openwebninja.com/terms).

## Next gate

**CP1.1F: collect the initial 50-100-job sample.** Start with a small, versioned query plan and one new request, audit the result, then expand. The final Checkpoint 1 report must state that Techmap was deferred because of access and that the source choice was provisional.
