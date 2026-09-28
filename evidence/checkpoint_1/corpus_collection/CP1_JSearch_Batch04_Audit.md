# CP1.1F: JSearch Batch 04 results and next decisions

**Audit date:** 26 September 2026 · **Status:** collection succeeded; dedup + automatic flags via the corpus builder; per-record JD review not done yet.
**Quota:** 153 before the run (verified by the collector); 34 requests used; my dashboard after the run: 119/200 remaining (41% used), which matches the calculation.

## Summary

| Metric | Value |
| --- | ---: |
| Requests / raw slots | 34 / 208 |
| New clusters / new with full JD | 136 / 107 (3.1 new full JDs per request) |
| Empty probes | 5 (AI Developer Indonesia, Remote MLE APAC, AI Engineer remote SEA, Remote LLM worldwide, AI Trainer Indonesia) |

## Yield per group (new clusters with full JD per request)

| Group | Requests | New full JD | Per request |
| --- | ---: | ---: | ---: |
| Indonesia: new probes (including AI Engineer Jakarta p1-3) | 13 | 21 | 1.6 |
| Indonesia: cursor continuation (DS/MLE/BAI/AIDEV/CV Jakarta, Tangerang) | 8 | 34 | 4.3 |
| Remote (sg/us) | 5 | 8 | 1.6 |
| Foreign comparison (Singapore, Kuala Lumpur) | 4 | 28 | 7.0 |
| Role contrast (Data Analyst, Data Engineer, Prompt Engineer, AI Trainer) | 4 | 18 | 4.5 |

## Findings

1. **Indonesian saturation is getting clearer.** "AI Engineer in Jakarta" (never queried directly before) gave only 3 new clusters from 10 slots on page 1; new city probes (Bekasi, Malang, Semarang) gave 1-3 slots. The DS Jakarta continuation was still productive up to page 6.
2. **Remote with APAC/Asia/SEA phrases is almost empty** (1 slot from 3 probes). Remote US gives results, but Indonesian applicant eligibility is usually absent or not stated.
3. **Foreign and contrast are very productive** (7.0 and 4.5 per request). They easily meet their targets, but they must not be used to fill the Indonesian gap just so the total reaches 1,000.
4. **Queries with a "Junior" prefix in Jakarta** gave 10 slots, but only 3 new ones and 0 new full JDs.

## Snapshot after B04

514 slots → 386 clusters (368 after 18 probable pairs) → **259 auditable candidates** (Indonesia 198 · foreign 41 · remote_unverified 20). Seniority from title: unspecified 163 · senior/lead 65 · junior 20 · intern 11 (provisional).

## Decisions

- Before a large batch, test once whether `num_pages=3` on `/search-v2` returns up to 30 slots and how many quota units are charged ([B05A manifest](../../../data/research/CP1_JSearch_Batch05A_NumPagesTest_Plan.json), 1 request). The collector now prints the quota used per run (before vs after).
- Batch 05 (±100 requests) will be designed after the test result: it uses almost all of the remaining free quota, with a small reserve.
- Risk noted: the target of 600 Indonesian jobs may not be reached through JSearch alone. The option already in the source document is a direct-company supplement (Greenhouse/Lever). This decision is postponed until the JSearch free quota is used up and the saturation numbers are measured.
