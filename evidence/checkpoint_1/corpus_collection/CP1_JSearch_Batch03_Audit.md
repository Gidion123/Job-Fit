# CP1.1F: JSearch Batch 03 results, corpus builder, and Batch 04 decisions

**Audit date:** 26 September 2026 · **Status:** collection succeeded; dedup + automatic flags via the corpus builder; per-record JD review not done yet.
**Input:** B03 manifest (24 requests allocated). Quota verified before the run: Basic, 176 remaining. **23 used**: `B03_CONT_AIE_ID` page 3 was empty, so page 4 was skipped automatically. Estimated remaining: 153.

## Results per query (new = cluster not seen before, in chronological order)

| Query | Slots | New | New with full JD |
| --- | ---: | ---: | ---: |
| AI Engineer Intern in Jakarta | 5 | 4 | 2 |
| Data Scientist Intern in Jakarta | 2 | 1 | 1 |
| Magang Data Science in Jakarta | 5 | 4 | 3 |
| AI Developer in Jakarta | 10 | 5 | 3 |
| MLOps Engineer in Jakarta | 5 | 4 | 2 |
| Computer Vision Engineer in Jakarta | 10 | 4 | 3 |
| AI Engineer in Tangerang | 10 | 8 | 6 |
| Data Scientist in Tangerang | 10 | 9 | 5 |
| AI Engineer in Semarang | 4 | 3 | 3 |
| Remote AI Engineer APAC (sg) | 3 | 3 | 3 |
| Machine Learning Engineer remote worldwide (us) | 10 | 9 | 9 |
| MLE Jakarta page 3 / page 4 | 10 / 9 | 8 / 4 | 5 / 3 |
| DS Jakarta page 3 / page 4 | 10 / 10 | 9 / 8 | 7 / 5 |
| Backend Engineer AI Jakarta page 2 | 10 | 8 | 3 |
| LLM Engineer Jakarta page 2 | 8 | 5 | 2 |
| **Empty (6):** NLP Engineer Jakarta, AI Engineer Bali, AI Engineer Medan, AI Engineer Indonesia p3, AI Engineer Bandung p2, AI Engineer Surabaya p2 | 0 | 0 | 0 |
| **Total** | **131** | **96** | **65** |

## Findings

1. **Signs of saturation in the Indonesian supply.** The national AI Engineer query ran out at page 3; Bandung and Surabaya ran out at page 2; LLM Engineer Jakarta gave no cursor after page 2. Jakarta DS/MLE were still productive up to page 4, but MLE dropped to 4 new clusters. This is an observation of JSearch/Google for Jobs supply on 26 September, not a measure of the job market.
2. **Intern/magang queries surfaced entry-level jobs**, but some of them were wrong-role (QA, product security, data analytics, data operation). They are useful for the junior stratum and as contrast cases.
3. **Remote outside `country=id` worked** (13 slots, 12 full JDs), but most of them say "US Remote/U.S. Based" or a specific time zone explicitly. Label: `remote_unverified`; Indonesian applicant eligibility must be proven from the JD.
4. **Specific vocabulary does not always exist in the Indonesian market:** NLP Engineer Jakarta 0; Bali and Medan 0 for AI Engineer.
5. **Summary JDs stay at ±29%** in B03 (38/131 slots).

## Corpus builder (new)

`python3 scripts/build_corpus.py` reads all archived JSON (without changing it) and writes `data/interim/jsearch_records.jsonl`, `data/interim/jsearch_canonical.csv`, `data/interim/jsearch_probable_duplicates_review.csv`, and `data/research/CP1_Corpus_Progress.json`. The logic lives in `src/jobs/corpus.py`, so the notebook and the pipeline use the same code. The B01 (44 new clusters) and B02 (67) counts match the earlier manual audit.

| Snapshot after B03 | Value |
| --- | ---: |
| Raw slots | 306 |
| Distinct jobs (exact-key clusters, upper bound) | 250 |
| After probable duplicates (lower bound, 11 pairs not reviewed yet) | 239 |
| **Auditable candidates** (full JD ≥700 characters, no generic external form) | **162** |
| Auditable candidates by geo (provisional) | Indonesia 137 · foreign 13 · remote_unverified 12 |
| Auditable candidates by role (title rule, provisional) | target 129 · adjacent 24 · content 5 · other 4 |
| Auditable candidates by seniority (title rule, provisional) | unspecified 96 · senior/lead 40 · junior/entry 17 · intern 9 |

The stratum labels above come from title/query rules that steer the collection. They are **not** final labels. Many "unspecified" seniority records will move once the experience requirement is read from the JD.

## Decisions

- **Gate 100 is passed in terms of candidates** (162), pending the provenance/dedup review. Next gate: 300 auditable candidates.
- Continue pagination only for probes whose last page gave ≥4 new clusters; probes without a cursor are treated as exhausted.
- The strata furthest behind the plan: foreign comparison, contrast, remote with verified eligibility, and junior. Batch 04 allocates requests to them, while also adding Indonesian probes that were not tried before.

Batch 04 prepared: [manifest](../../../data/research/CP1_JSearch_Batch04_Plan.json), 34 requests, free-only.
