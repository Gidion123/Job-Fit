# CP1: Cross-publisher duplicate review

**Date:** 26 September 2026 · **Snapshot:** `data/interim/snapshots/CP1_20260926/` · **Status:** 40/40 pairs decided; the 3 UNSURE pairs are flagged for re-check.

## Method

1. **Exact-key dedup (automatic):** `job_id`, `job_uid`, normalized apply URL, JD content hash (≥200 characters), and a company+title+location key → 1,314 slots become **937 clusters**.
2. **Probable duplicate candidates (automatic, not merged automatically):**
   - *Detector A (company_title):* the same normalized employer name (without PT/Tbk/Sdn Bhd) and a title token Jaccard ≥ 0.6.
   - *Detector B (content, new):* word 5-gram Jaccard of the JD content ≥ 0.5. It catches syndicated copies that use the legal entity name or the recruiter name (e.g., Grab ↔ PT Solusi Transportasi Indonesia; LSEG ↔ Refinitiv; Pintarnya ↔ PT Emas Pandai Indonesia). The hash uses `zlib.crc32`, so the results are deterministic across runs.
3. **Pair-by-pair review:** each pair was reviewed against the text evidence: title, employer, location, publisher, posting age, content snippet, and sentence differences when needed. Decision: `SAME` (merged), `DIFFERENT`, or `UNSURE` (kept separate, conservative).

Decisions are saved in `data/interim/dedup_decisions.csv` (with a reason per pair) and are read automatically by `scripts/build_corpus.py`. The canonical record of each final cluster is the record with the most complete JD.

## Results

| Decision | Number of pairs |
| --- | ---: |
| SAME | 29 |
| DIFFERENT | 8 |
| UNSURE | 3 |

| Stage | Count |
| --- | ---: |
| Raw slots | 1,314 |
| Exact-key clusters | 937 |
| **Final distinct jobs** (after 29 SAME) | **910** |
| **Final auditable candidates** (full JD ≥700 characters, no generic external form) | **632** |

Auditable candidates by geo: Indonesia 373 · foreign 199 · remote_unverified 60. By role (title rule, provisional): target 456 · adjacent 119 · other 35 · content 22.

## Patterns found (input for data quality and EDA)

- **Employer names are not consistent across publishers:** brand vs legal entity (Grab/PT Solusi Transportasi Indonesia, Avanade/PT Avanade Teknologi), capitalization variants (Dot/DOT, Code.id/CODE.ID).
- **The location of one job differs across publishers** (Jakarta Pusat vs Timur; Yogyakarta vs Tangerang for BitHealth). Location must be treated as a publisher claim, not a single fact.
- **Aggregator summaries** (JobLeads, Jobrapido, Jooble, Trabajo) often paraphrase jobs that are also available in full at other publishers.
- **Job blogs** (Relidevega.blogspot, the "Lowongan Kerja …" template) copy or translate the original JD; low provenance.
- **Company templates are not duplicates:** Telkomsel, gojek, Agoda, and XLSMART use the same boilerplate for different roles. The content detector surfaces them, and the review rejects them.

## Limitations

- The review was done against the text evidence only. The 3 UNSURE pairs, plus 5 random SAME pairs, are flagged for re-check.
- The detectors only catch duplicates with a similar employer/title or similar JD content. Duplicates with a different employer **and** heavily paraphrased content (e.g., an aggregator summary of a job that was originally in another language) can slip through. The 910 figure is the best estimate, not a guarantee.
- `UNSURE` is treated as separate jobs (this raises the count slightly).
