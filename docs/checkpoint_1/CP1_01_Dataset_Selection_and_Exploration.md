# CP1.1: Dataset Selection and Initial Exploration

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Data basis:** snapshot `CP1_20260926`, collected 25 to 26 September 2026  
**Status:** report complete; collection closed; JSearch is still a provisional source.

## 1. Goal of this stage

JobFit needs real job postings to understand job requirements, prepare search, and compare requirements with CV evidence. So a dataset with only titles, companies, and locations is not enough. The JD text and its data origin must be available so results can be traced back.

The initial Playbook target was 50 to 100 job postings. Corpus development was later aimed at 1,000 varied job postings. These count targets helped plan the collection, but the decision to continue or stop was still based on quality, variety, yield, and cost.

## 2. Why JSearch?

JSearch (OpenWeb Ninja) pulls job postings from Google for Jobs. With one API, we get job postings from many publishers at once (LinkedIn, Glints, Indeed, and others), complete with their JD text. The JD text is the most important part, because the requirements are there.

The local JSearch benchmark has 8 responses with 40 slots in total: 4 queries returned 10 results each and 4 queries returned nothing. All slots have description text and an apply link, but 8 descriptions are shorter than 500 characters. A structured posting date was not available in that early benchmark sample.

This result shows that access to Indonesian data is possible, but quality depends on the query and the publisher. Also, `job_id` is not enough as the only dedup key, because the same company, title, and location combination can repeat with different IDs.

| Alternative | Available evidence | Decision and trade-off |
| --- | --- | --- |
| JSearch/OpenWeb Ninja | Stored responses, Indonesian coverage exists, can be collected in stages | Used for the CP1 corpus; accepts the risks of an aggregator, duplication, and empty metadata |
| Techmap/RapidAPI | Checkout access had problems; no responses yet to assess the data | Deferred; the access failure is not treated as evidence that its data quality is lower |
| Other marketplace providers | Not tested with the same criteria yet | No new benchmark added without a clear need |
| Greenhouse/Lever/direct-company | Not a source for this corpus yet | Still an alternative; cannot be claimed to improve coverage yet |

**Decision:** using JSearch provisionally lets cleaning and EDA move forward. This is not a conclusion that JSearch is the best of all alternatives. The final provider choice is still OPEN, as stated in the Canonical.

## 3. How the data was collected

Collection was done in stages: benchmark, COL01/02, pilot B01, then B02 to B07, including resumed runs. Queries covered AI/ML/Data/Software AI roles, Indonesian cities, experience levels, foreign comparisons, remote, and comparison roles that could become hard negatives.

For each automated response, the metadata stores the parameters, UTC time, page/cursor, HTTP status, duration, slot count, request ID, and response checksum. Older manual responses do not always have a timestamp; the missing value is not silently filled with an estimate. The country and seniority in a query are part of the sampling design, not confirmed labels of the job.

The historical data records 235 successful responses, 4 failed requests, and a cost of 198/200 free-quota units plus 34 PAYG requests of about US$0.17. This is the recorded collection cost, not the current service price or a cost projection for a public app.

## 4. Collection results and counting units

| Stage | Count | Meaning |
| --- | ---: | --- |
| API result slots | 1,314 | One appearance of a result; it can appear again in another query |
| Exact-key clusters | 937 | Grouping by ID, URL, content, and field combinations |
| Final clusters | 910 | Estimated unique jobs after dedup decisions |
| JD summary | 236 | Length 200 to 699 characters |
| JD insufficient | 7 | Length under 200 characters |
| Full JDs held back | 35 | Contain a flagged generic external form |
| EDA candidates | 632 | JD ≥700 characters and passes the basic source filter |

The final partition is **910 = 236 + 7 + 35 + 632**. Of the 667 `full` JDs, 35 were held back because of a generic external form, leaving 632 EDA candidates. The term full is a length rule, not a guarantee that all requirements are present. Being an EDA candidate also does not mean the source is official or that the job is still open.

![Figure 1. Corpus funnel: from API slots to EDA candidates](../../reports/figures/cp1/fig01_funnel.png)

Dedup includes 40 pair decisions reviewed against the text evidence: 29 SAME, 8 DIFFERENT, 3 UNSURE. Some SAME decisions overlap, so the cluster reduction is 27 (937 to 910). Dedup is still v0 and the 3 UNSURE pairs are flagged for re-check, so 910 is an estimate, not a guaranteed unique count.

**Insight:** about 3 in 10 slots are duplicates (1,314 to 910). Without dedup, a job that appears in many queries would look more important than it really is, and its skills would be counted many times. Also, the skill analysis uses only the 632 EDA candidates, so its findings apply to those 632 jobs, not automatically to all 910.

## 5. Why stop before 1,000?

In the first 26 successful responses of B07, only 6 new full JDs were found, or about 0.23 per request; 17 responses were empty. This is below the stop rule of 0.5 new full JDs per request on the tested probe.

Adding more queries of that pattern would likely add more cost and duplication than new information. Filling the gap with foreign jobs would also change the corpus composition and move away from the focus on Indonesian users. So the collection was closed, and the coverage gap is reported openly.

The conclusion we can draw is that the yield of the **tested queries/sources/time window** is already low. We have not proven that all Indonesian job postings on the internet, or even all JSearch data, have been exhausted.

## 6. What can this dataset support, and what can it not support yet?

The 632 candidates are enough for initial exploration, checking the baseline rules, and preparing evaluation sampling. The size does not prove market representativeness. Most labels are also rule-based v0 (their accuracy will be measured against the CP2 gold set), so this data is not yet a gold set for extraction, evidence matching, or ranking.

The next priority is to understand the character and limits of the data, then prepare the manually labeled gold set in CP2. No extra collection was done while writing this report.

## 7. Evidence and stage outputs

- [Provisional source decision](../../evidence/checkpoint_1/provider_benchmark/CP1_Provisional_Source_Decision.md)
- [Dataset inventory and batch details](supporting/CP1_Dataset_Inventory.md)
- [Historical collection log](../../evidence/checkpoint_1/corpus_collection/CP1_JSearch_Collection_Log.md)
- [Snapshot manifest](../../data/interim/snapshots/CP1_20260926/SNAPSHOT_MANIFEST.json)
- [Research notebook](../../notebooks/01_research.ipynb), sections 1.1 to 1.3.

**Acceptance:** the sample can be opened, provenance is available, unit definitions are clear, and limitations are recorded. Verifying that every job posting is genuine and still open, and comparing with Techmap data, are not done yet and are not claimed as done.

**Next:** [CP1.2: Data Understanding and Goals](CP1_02_Data_Understanding_and_Goals.md).
