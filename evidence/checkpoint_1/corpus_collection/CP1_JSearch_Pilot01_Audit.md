# CP1.1F: JSearch Pilot 01 results and next-batch decisions

Audit date: 26 September 2026. Status: **technical collection succeeded; initial audit done; CP1 not closed yet**.

## Summary

- 12 search requests, all HTTP 200 / status OK; 6 queries returned results and 6 were empty.
- 47 raw slots (3.92 slots/request). This is not yet a count of unique usable jobs.
- 12/12 SHA-256 checksums, request IDs, slot counts, and response parameters match the local metadata.
- Distribution by **source query**: Indonesia target 8; remote Indonesia 0; foreign comparison 20; role contrast 19. This distribution is not the same as the actual job labels.
- 12/47 descriptions are under 500 characters (25.5%); length is only an indicator, not an automatic eligibility rule.
- 38/47 do not have both structured city and country filled. The job_location text is often available; do not say that all locations are missing.
- 28/47 have no structured posting timestamp; 19 do. Do not treat retrieved_at as posted_at.
- Only 2/47 are marked job_is_remote=true, while several other JDs mention remote/hybrid; there is a metadata-text conflict.
- All job_apply_is_direct values are false, even for Grab Careers and RTX Careers URLs. The provider flag needs to be compared with the URL and source evidence, not treated as the single truth. Source URLs were not opened or verified externally in this audit.
- Initial review of the 47 JDs: **11 target candidates, 15 contrast candidates, 20 hold, 1 reject insufficient**. Candidates are not yet counted as the final corpus; these labels are not a gold evaluation.
- Combined inventory: **22 response JSON files, 95 raw slots**, including 48 old slots; 88 heuristic company/title/city keys. This is not 88 verified unique jobs.

## Results per query

| Query ID | Query | Slots |
| --- | --- | ---: |
| CONTROL_ANL_BAN | Data Analyst in Bandung | 10 |
| CONTROL_CNT_JAK | AI Content Creator in Jakarta | 9 |
| GLOBAL_SG_BAI_SENIOR | Senior Backend Engineer AI in Singapore | 10 |
| GLOBAL_US_AIE_JUNIOR | Junior AI Engineer in United States | 10 |
| ID_AIE_BAN_SENIOR | Senior AI Engineer in Bandung | 7 |
| ID_BAI_JAK_MID | Mid Level Backend Engineer AI in Jakarta | 0 |
| ID_DAS_SUR_MID | Mid Level Data Scientist in Surabaya | 0 |
| ID_GEN_YOG_JUNIOR | Junior Generative AI Engineer in Yogyakarta | 0 |
| ID_MLE_JAK_JUNIOR | Junior Machine Learning Engineer in Jakarta | 1 |
| REMOTE_DAS_MID | Remote Mid Level Data Scientist in Indonesia | 0 |
| REMOTE_GEN_SENIOR | Remote Senior Generative AI Engineer in Indonesia | 0 |
| REMOTE_MLE_JUNIOR | Remote Junior Machine Learning Engineer in Indonesia | 0 |

## Duplication and sources

1. CONTROL_ANL_BAN #4 (Taiyo) and #9 (BPR summary) repeat COL01 #4 and #2: the apply URL, job_uid, and description are identical even though the job_id changed. Do not use job_id as the only deduplication key.
2. CONTROL_ANL_BAN #8 and #10 (YO AI Labs) have the same description, company, title, and location at two different publishers. Keep both raw evidence records; treat them as one job candidate for source review.
3. Potential duplicates: SJS #1/#3, Hays/Haystack US #1/#2, re-zoo-me/RTX SG #3/#8. Different company names do not rule out syndication. SJS #7 is similar to #1 but has different qualifications, so do not merge it automatically.
4. Neuronworks from Blogspot includes the generic globaljob.sbs form. Hold for provenance; the company origin is not verified yet.

After setting aside the two old repeats and one identical internal copy, at most 44 additional candidates still need checking. This number is an initial ceiling, not an accepted/unique usable count. Further possible duplication and quality issues will lower it.

## Insights that affect the design

- **Query seniority does not become the label.** OCBC accepts fresh graduates/maximum 2 years; SL2 needs 2+ years; BERANI needs 1+ year even though it appeared in a senior query. Hays is titled Junior but asks for 3-5 years of software experience. Store title seniority and the experience requirement separately.
- **The query location is not the job location.** OCBC mentions Tangerang; the BALLAS metadata says Lembang, but the Location section of the JD mentions Tokyo/Osaka and weekly office attendance. BALLAS is held as a location conflict.
- **Remote is not a global work permit.** Hays requires US work authorization without sponsorship. Insight Global mentions CST, with no evidence that it accepts Indonesian candidates. YO AI Labs says Global Fully Remote: there is evidence of a global claim, but acceptance of Indonesia still needs verification.
- **Freshness needs evidence.** Penguin Random House states apply-by 9/1/2026; in a US context this is likely 1 September, which had already passed at retrieval time. Flag it as likely stale, but do not conclude yet that the job is closed. RTX has a date of 2026-09-18 in the JD that can be extracted with provenance.
- **Some controls are useful.** Creative/content roles use AI but do not do AI engineering. Keep them as wrong-role contrast so matching does not only look at the word AI.
- **An empty query is a retrieval observation.** It does not prove yet that there are no remote/mid-level jobs or no jobs in that city. Seniority prefixes and word/location combinations may narrow the results; batch 02 tests this hypothesis.

## Operational decision

Status stays: PRE-CP0 frozen and CP1.1F, JSearch provisional, Techmap deferred. The 1,000 corpus target still applies, with gates at 50-100, then 300/600/1,000; senior/global data is still kept for variation and evaluation as planned.

**Batch 02: maximum 12 requests, verified Basic/Free only.**

- Five Indonesian queries repeat the pilot role/city pairs with the Junior/Mid Level/Senior prefix removed.
- Five other Indonesian queries expand the roles/cities.
- Two remote queries remove the seniority prefix while keeping country=id, language=en and the remote filter. This tests a step-by-step change; another strategy is needed if they are still empty.
- Adding control and foreign queries is postponed by one batch because the pilot already gave 19 and 20 slots in those two groups. The senior/global dataset is not discarded.
- Take one page per query, then audit the new yield, relevance, duplication and coverage before pagination/scale. The pilot total becomes at most 24 requests.
- The original plan of 113 probes stays archived. The batch 02 manifest is saved separately; it does not change the frozen scope decision.

## Quota and cost

My Terminal output reported Basic with 200 remaining before the pilot. The arithmetic estimate after 12 searches is 188; **the actual remaining quota has not been re-checked** and may differ if there was other usage. The 14/200 snapshot from 25 September is historical evidence, not the latest status. The next batch reads the usage again and stops if the plan is not verified Free/Basic, the quota is unknown, or the quota is used up. There is no automatic upgrade. The final billed amount is not inferred from this output.

## Files and next steps

- Raw data and metadata: `data/raw/jsearch/` (kept locally, not in the public repository).
- [Per-record review of the 47 JDs](./CP1_JSearch_Pilot01_Record_Review.json).
- [Combined inventory](../../../data/research/CP1_JSearch_Seed_Inventory.json).
- [Batch 02 manifest](../../../data/research/CP1_JSearch_Batch02_Plan.json).

Run it in the local Terminal; the key is entered through a hidden prompt and is not saved:

```bash
cd project-job-fit
python3 scripts/run_jsearch_batch02.py
```

To see the queries without sending requests: `python3 scripts/run_jsearch_batch02.py --dry-run`.

Batch 02 **is only prepared; it had not been run when this audit was written**. After it finishes, audit the JSON and metadata first. Screenshots are not needed for successful responses. This step completes the pilot sampling; it does not close the CP1 gate or start experiments before the dataset understanding/feasibility work is done.
