# CP1.1F: JSearch Batch 05 results, HTTP 500 stop, and position toward 1,000

**Audit date:** 26 September 2026 · **Status:** 66 of 84 requests sent; safe stop on HTTP 500; dedup + automatic flags via the corpus builder; per-record JD review not done yet.
**Quota:** 113 before the run (verified); 48 after (65 units charged for 66 requests; the HTTP 500 request seems not to be billed, or usage was not updated yet). The user's dashboard: 76% used (152/200), which is consistent.

## Stop

`B05_CONT_MACHINE_LEARNING_ENGINEER_REMOTE_W` page 2 (saved cursor from the B03 remote probe) returned **HTTP 500**. The collector stopped without retry, as designed. 18 requests were not sent. The failed probe was removed from the [resume manifest](../../../data/research/CP1_JSearch_Batch05_Resume_Plan.json) (13 probes / 17 requests, query IDs stay B05). The cause of the 500 is not known yet. Hypothesis: the cursor for `work_from_home` queries is unstable. This is an observation, not a conclusion.

## Yield per group (new clusters with full JD per request sent)

| Group | Requests | New full JD | Per request | Note |
| --- | ---: | ---: | ---: | --- |
| Indonesia: new probes | 30 | 46 | 1.5 | 6 empty probes (AI Engineer Depok, DS Medan, CV Bandung, AI Intern Indonesia, Fresh Graduate DS Indonesia, Graduate Program DS) |
| Foreign: new probes | 11 | 41 | 3.7 | HCMC ×2 and Bangkok empty |
| Foreign: cursor continuation | 10 | 56 | 5.6 | |
| Remote (us/gb) | 3 | 26 | 8.7 | Indonesian eligibility not verified yet |
| Role contrast: new probes | 11 | 57 | 5.2 | Data Annotator Indonesia empty |

## Findings

1. **Indonesian supply is already saturated for the target vocabulary.** New city/title probes gave on average 1.5 new full JDs per request. General terms (Machine Learning / Artificial Intelligence / Data Science in Jakarta) and derived titles (AI Specialist, AI Product Engineer) still gave slots, but with a lot of overlap.
2. **Entry-level keywords in recruiting language ("Fresh Graduate", "Graduate Program") were empty.** Entry-level jobs are more likely to be identified from the JD content (experience requirement) than from the title/query.
3. **Comparison markets are widely available**: Singapore, Kuala Lumpur, and Manila are productive; Vietnam and Bangkok were empty with `country=vn/th` + English queries.
4. **Remote US/GB is easy to get**, but Indonesian applicant eligibility is usually not stated or is limited by country. These stay `remote_unverified`.

## Snapshot after B05 (partial) + B05A

951 slots → 721 clusters (697 after 24 probable pairs) → **497 auditable candidates** · Indonesia 293 · foreign 159 · remote_unverified 45. Role (title, provisional): target 390 · adjacent 82 · content 14 · other 11. Seniority (title, provisional): unspecified 313 · senior/lead 133 · junior 26 · intern 25. **Gate 300 is passed in terms of candidates.**

Builder fix: `B05A_*` files were counted as B01 before; they are now recognized as batch B05A.

## Position against the 1,000 composition plan

| Axis (plan) | Plan | Current auditable candidates | Note |
| --- | ---: | ---: | --- |
| Indonesia | 600 | 293 | new yield 1.5/request and falling; likely to stall far below 600 through JSearch |
| Remote with verified Indonesian eligibility | 200 | 0 verified (45 unverified) | JSearch rarely states eligibility |
| Foreign comparison | 200 | 159 | easy to fill |
| Contrast (across geos) | 200 | ±107 (adjacent + content + other, provisional) | easy to fill |

The final composition decision (accept the Indonesian shortfall vs add an Indonesian source) was raised for my decision; see the collection log.
