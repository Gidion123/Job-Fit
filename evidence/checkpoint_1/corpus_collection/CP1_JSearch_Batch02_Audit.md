# CP1.1F: JSearch Batch 02 (v2) results and next-batch decisions

**Audit date:** 26 September 2026 · **Status:** technical collection succeeded; automatic audit + title review done; per-record JD review not done yet.
**Input:** 12 requests (plan v2, free-only). Quota verified before the run: Basic, 188 remaining → estimated 176 after the run (not re-checked on the dashboard yet).

## Summary of numbers

| Metric | Value |
| --- | ---: |
| Requests / HTTP 200 | 12 / 12 (SHA-256 matches 12/12) |
| Raw slots | 80 (6.7 slots/request; pilot 3.9) |
| New by strict keys (job_id, job_uid, apply URL, company+title+location, JD content hash) | 67 |
| *Probable* cross-publisher duplicates (pair review not done yet) | ±10 → estimated ±57 new distinct jobs (±4.7/request) |
| "Summary" JDs of 400-530 characters | 28/80 (35%): JobLeads 14, Jobrapido 8, Jooble 3, Loker.id 2, Findojobs 1 |
| Empty queries | 1 (remote) |

The ±57 figure is a heuristic estimate, **not** an accepted count. Combined inventory after B02: 34 files, 175 raw slots, 154 company/title/city keys (still not a final unique count).

## Findings

1. **The saved cursor is still valid.** The cursor from the 25 September response worked. Page 2 of four productive queries gave 31 slots, and 28 of them are new by strict keys. Pagination is the best source of yield right now.
2. **A seniority prefix narrows the results (supports H1, not causal evidence).** Pilot → B02 pairs: Backend Engineer AI Jakarta 0 → 10; Generative AI Engineer Yogyakarta 0 → 1; Senior AI Engineer Bandung 7 → AI Engineer Bandung 10. The retrieval times differ, so this is a diagnostic observation.
3. **Remote with `country=id` + `work_from_home=true` is consistently empty (4/4 probes).** The remote strategy must change; do not conclude "there are no remote jobs".
4. **35% of the JDs are ±500-character summaries from aggregators.** The text is complete per sentence (not cut off), but there is no requirement list and `job_highlights` is empty. They are fit for title/role analysis but **not fit** for gold set extraction. Some of the same jobs appear in full at another publisher (e.g., DOT Indonesia via Glints with 2,072 characters vs AI Jobs Map), so dedup must pick the record with the most complete JD as canonical.
5. **Target queries still bring contrast.** Examples: Frontend Engineer (Human-in-the-Loop), Junior Solutions/Software Engineer, Lead Data Engineer, Senior Kotlin Engineer, "Data Analis" for a restaurant. These are useful as wrong-role cases; the final label follows the JD.
6. **Seniority variation shows up naturally.** Intern (AI Engineer Intern, AI & Data Science Internship), Junior Data Scientist ×2, up to Senior/Lead. Labels still come from the JD content, not from the query.
7. **New locations outside Java** appear from national queries (Bali/Buleleng, Semarang).

## Decisions

- Keep cursor pagination for queries whose previous page had ≥8 slots; stop when new slots < 3.
- Add entry-level vocabulary (Intern/Magang) and real title vocabulary (AI Developer, MLOps, Computer Vision, NLP), plus new cities.
- Test two remote strategies outside `country=id`; the results need evidence from the JD that Indonesian applicants are eligible.
- Add the flag `jd_quality = summary_only` at the corpus builder stage; summary records count as slots/titles, not automatically as auditable JDs.

Batch 03 prepared: [manifest](../../../data/research/CP1_JSearch_Batch03_Plan.json), 24 requests, free-only, to be run with the generic runner `scripts/run_jsearch_batch.py`.
