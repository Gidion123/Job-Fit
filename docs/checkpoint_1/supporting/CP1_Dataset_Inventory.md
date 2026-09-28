# JobFit: CP1 Dataset Inventory

Audit date: 26 September 2026. Collection is **CLOSED**. Source of the EDA numbers: `data/processed/CP1_research_summary.json`, produced by `notebooks/01_research.ipynb`. v0.1 labels are a rule-based baseline; accuracy will be measured against the CP2 gold set.

## 1. Corpus and sources

| Metric | Value |
| --- | ---: |
| Stored responses | 235 |
| API result slots | 1,314 |
| Exact-key clusters | 937 |
| Final clusters after dedup decisions | 910 |
| EDA candidates (`is_auditable`) | 632 |
| JD full / summary / insufficient | 667 / 236 / 7 |
| Full JDs held back for a generic external form | 35 |
| EDA candidate publishers | 109 |
| EDA candidate employers | 505 |
| Collection period | 25 to 26 September 2026 |

Exclusive funnel: **910 = 236 summary + 7 insufficient + 35 full held back + 632 EDA candidates**. `full` means a length of ≥700 characters, not a JD that has been checked as complete. `auditable` means a candidate for analysis/review, not a verified job posting or one that is sure to be active. Final clusters are an estimate of the number of job postings. False merges and remaining duplicates are still possible.

JSearch/OpenWeb Ninja `/search-v2` is used as **provisional**. Techmap is **deferred** because of checkout problems and has no benchmark data results yet. Greenhouse/Lever are not used yet. The final provider choice is still OPEN, as stated in the Canonical.

Collection stopped because the yield on the Indonesia queries tested in B07 was only 6 new full JDs in 26 successful responses (0.23/request; 17 empty). This is a limit observed for those queries, sources and times, not proof that the whole Indonesian supply is used up. The 1,000 target is not filled up with foreign jobs just to reach the number.

## 2. Provenance and dedup review

- 460 raw/response and metadata files were verified with SHA-256 against the original manifest.
- Five frozen derived files were verified with the extra manifest `RESEARCH_INPUT_HASHES.json`. The original manifest was not changed.
- An offline rebuild from raw produced records, canonical CSV and probable-review CSV identical to the snapshot. The progress creation timestamp changed, as expected.
- 40 **dedup decisions**, reviewed against the text evidence: 29 SAME, 8 DIFFERENT, 3 UNSURE. The 29 SAME edges remove 27 clusters because some edges are redundant. Dedup is still v0; the 3 UNSURE pairs are flagged for re-check.
- All raw data, decisions, batch audits and snapshots are kept. The canonical source is chosen by heuristic length/quality, not by publisher authenticity.

## 3. Collection history

| Batch | Responses | Slots | Final clusters first seen |
| --- | ---: | ---: | ---: |
| Benchmark | 8 | 40 | 35 |
| COL01/02 | 2 | 8 | 8 |
| B01 | 12 | 47 | 43 |
| B02 | 12 | 80 | 62 |
| B03 | 23 | 131 | 90 |
| B04 | 34 | 208 | 130 |
| B05A | 1 | 27 | 24 |
| B05 + resume | 80 | 469 | 332 |
| B06 | 31 | 228 | 136 |
| B07 + resume | 32 | 76 | 50 |

The log records 4 failed requests (3 timeouts, 1 HTTP 500). Historical cost: free quota 198/200 units and PAYG 34 requests, about US$0.17, based on the collection notes; this is not a current price offer. **This audit did not send any API requests.**

## 4. EDA populations after the location fix

`geo_stratum` keeps the old collection design. `analysis_geo` uses the country field or the publisher location text; the query country does not fill in an empty country. The remote probe becomes a separate group. TikTok Los Angeles (`US`) is removed from the Indonesia group. Ten targets without location evidence become UNKNOWN.

| analysis_geo | Target | Adjacent | Non-target | Total |
| --- | ---: | ---: | ---: | ---: |
| foreign | 186 | 3 | 1 | 190 |
| indonesia | 175 | 126 | 71 | 372 |
| remote_unverified | 57 | 2 | 1 | 60 |
| unknown | 10 | 0 | 0 | 10 |

Total targets: 428; all candidates: 632. Compared with the initial plan, coverage of Indonesia and verified remote jobs is still short. In total, 60 candidates from remote queries are not yet verified as open to applicants from Indonesia.

## 5. Experience signals

| Group | Entry | 1-2 years | 3-4 years | 5+ years | Not detected |
| --- | ---: | ---: | ---: | ---: | ---: |
| ID_T (175) | 14 | 35 | 38 | 31 | 57 |
| FOR_T (186) | 20 | 17 | 36 | 43 | 70 |
| REM_T (57) | 7 | 5 | 7 | 17 | 21 |
| UNKNOWN_T (10) | 0 | 1 | 2 | 2 | 5 |

Indonesia early-career pool: **49/175**, based on entry/≤2 years. This is **not** a set of job postings that surely fit fresh graduates. There are 69 signals of 3+ years and 57 UNKNOWN. The highest per-mention number can still come from a preference, an alternative or a multi-level posting. Titles without a level that have 3+ years: 128/405.

37 of the 49 jobs in the early-career pool have no level word. A bachelor's degree is mentioned in 28/49, a master's in 6/49, and 19 have no detected education level. An education mention does not mean it is required. Pool members changed during the audit even though the total stayed 49: the Los Angeles intern left, and a Junior Data Scientist posting with 0 to 4 years joined.

## 6. Metadata and quality limits

- EDA candidates: structured city 20%, country 45%, date 30%, salary 3%, highlights 0%. The exact percentages are in the summary.
- All 910 clusters: provider date 275, relative 357, UNKNOWN 278. Relative dates use the timestamp of the same record; 20 old estimates were dropped because the manual responses have no timestamp.
- EDA candidate languages: {'en': 564, 'id': 65, 'mixed': 2, 'other_script': 1}. This is a heuristic, not a measured classifier.
- Remote, direct-link, location, skill, education and seniority flags are rule-based v0, not gold labels. Masking covers only emails and Indonesian phone number patterns; it is not full anonymization.
- **260 candidates** have a review flag. The preference/alternative flag is broad on purpose for triage; it is not a count of confirmed errors. Review queue: `data/processed/CP1_human_review_queue.jsonl`.

## 7. Next evaluation datasets (CP2)

| Set (per the Canonical) | Target | Status |
| --- | --- | --- |
| A. Raw Job Corpus | early CP1: 50-100 | 632 EDA candidates, collection closed |
| B. Extraction Gold | ±50 JDs | Not labeled yet |
| C. Evidence Matching | ±100 pairs | Not yet; needs synthetic CVs and labels |
| D. Ranking | 40-60 jobs, relevance 0-3 | Not yet; sampled from the corpus |
| E. RAG evaluation | 15-20 questions | Not yet |
| F. CV Safety | 20-30 scenarios | Not yet |
| G. Hard negatives | growing | Seeds: wrong-role, multi-level, seniority, location |

Separate development/regression from the held-out test before tuning. Cases already used to change the rules are not independent evidence of accuracy. Do not call the review queue a gold set.

## 8. Artifacts and reproduction

See `notebooks/README.md` to run the notebook from a clean kernel. All processed files and the 14 figures are produced by a single notebook. `docs/data-contract.md` explains the fields and provenance. `scripts/refresh_cp1_docs.py` keeps this document and the insights in sync with the summary.

Raw data and snapshots are not published without a terms review. Historical files in evidence explain the decisions made at the time; **the latest EDA numbers follow the summary and the audit**, not the old provisional numbers.

Next step: **PPT CP1.7**, mentor feedback, then the gold set and CP2 experiments.
