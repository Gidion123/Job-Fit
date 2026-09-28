# CP1.1F: B05 resume + Batch 06 (free quota used up, final free-tier position)

**Audit date:** 26 September 2026 · **Status:** collection succeeded; dedup + automatic flags; per-record JD review not done yet.

## Execution and quota

| Run | Requests sent | Quota (before → after) | Note |
| --- | ---: | --- | --- |
| B05 resume | 15 of 17 | 48 → 34 (14 units) | 2 requests not sent because the previous page was empty (automatic stop rule); 7 cursor continuations empty |
| B06 | 31 of 31 | 33 → 2 (31 units) | 3 probes empty or almost empty |

Remaining free quota: **2** (resets 26 October 2026).

## Yield

- **Indonesia is saturated.** B06 Indonesia (16 requests) gave ±18 new full JDs (±1.1/request). "Lowongan Data Scientist Jakarta" and "Lowongan AI Engineer Jakarta" gave 10 slots each but **0 new jobs**; "Ilmuwan Data Jakarta" gave 0 slots. Many Indonesian cursor continuations in the B05 resume were empty (Senior AI Engineer Bandung, DS Yogyakarta, MLOps, Magang DS, AI Engineer Intern).
- **Foreign comparison reached ±200** auditable candidates; no new requests were allocated to it.
- **Contrast** stays productive (4-7 new full JDs per continuation).
- **Remote**: of the 59 full `remote_unverified` JDs, a keyword search found only ±8 with global/APAC phrases and **0 that mention Indonesia**; 6 are explicitly limited to the US. The target "200 remote with verified Indonesian eligibility" is expected to become a reported shortfall.

## Final free-tier snapshot

1,238 slots → 887 clusters (859 after 28 probable pairs) → **613 auditable candidates** · Indonesia 353 · foreign 201 · remote_unverified 59. Role (title, provisional): target 467 · adjacent 109 · other 22 · content 15.

## Decision

Batch 07 is the first PAYG batch (105 requests, at most US$0.53 at the public rate), under my limit of US$2: 80 requests for the untested Indonesian role × city grid and Jakarta industry modifiers, 20 contrast, 5 remote. Cursor continuations are picked automatically only when the last page added ≥3 new full JDs. **Stop rule:** if Indonesia gives < 0.5 new full JDs per request in B07, Indonesian collection through JSearch is declared saturated and the corpus is frozen for CP1.
