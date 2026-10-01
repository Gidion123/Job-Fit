# CP2.1 Supporting Record: Synthetic CV Check and First Label Drafts

**Date:** 29 September 2026 · **Stage:** CP2.1, pilot step 1 (pre-annotation) · **Guideline:** v0.1
**Status:** historical record. The drafts below were later reviewed and approved by the annotator under guideline v1.2. The final numbers are in the [CP2.1 report](../CP2_01_Model_and_System_Selection.md) and the decisions in D-032 to D-043.

This file records what the first model drafts looked like before any human review, so the later review can be compared with them. Workflow: [annotation-workflow.md](../../annotation-workflow.md).

## 1. What was drafted

| Item | Result |
| --- | --- |
| Synthetic CV check | All three CVs judged usable for the pilot; source text unchanged |
| A_Extraction | 48 draft units: J1 19, J3 16, J2 13 |
| B_Evidence | 32 draft labels: CV1 x J1 19, CV2 x J2 13 |
| C_Relevance | 10 draft ratings, with reasons and constraints |
| Questions | Q1 to Q3 answered as proposals; Q4 to Q16 added |
| Timing | Left empty. Drafting time is not human labeling time |

All rows started as `label_source = model_draft`, `review_status = pending`. Because J1 to J3 were drafted before review, they measure review time, not blind labeling time. J4 was added on 29 Sep as the blind item for that reason.

The draft before review is saved in [`evals/pilot/audit/draft_review_20260929.json`](../../../evals/pilot/audit/draft_review_20260929.json).

## 2. Synthetic CV check

| CV | Finding | Limits to keep in mind |
| --- | --- | --- |
| CV1 Rina (Indonesian, fresh graduate) | Dates fit together; Python and SQL use, dashboards, and thesis support the main skills | Git and some packages appear only in the skills list; thesis dates are year only; TOEFL is a stated score, not verified fluency |
| CV2 Bima (English, career switcher) | Marketing to analyst to bootcamp to AI projects; the timeline is consistent | The bootcamp is still running; three years of marketing analytics is not three years of AI engineering; an AWS course without the exam is not a certification |
| CV3 Dewi (English, junior ML engineer) | Internship Feb to Jul 2025, junior role Aug 2025 to now (about 14 months at the analysis date) | "About one year" describes the junior role only; side projects have year-only dates |

The CVs are cleaner than most real CVs, so they cannot show robustness to real PDF layouts or messy writing. They were not changed to fit the five pilot jobs.

## 3. Extraction drafts: points raised for review

- **J1:** the experience sentence has both "1-2 years" and "fresh graduates welcome", so importance was drafted as `unknown`. Responsibilities were not turned into requirements.
- **J3 (Indonesian JD):** `dan` lists were split, `atau` lists kept as one group; items in the sentence ending with `nilai tambah` were drafted as preferred.
- **J2:** the first nine suggestions were revised before review: a stitched quote was replaced with the exact JD sentence, the AND list of ML, NLP, and computer vision was split into three units, and the senior-only "3 years" condition was kept as conditional.

These points became pilot questions Q1 to Q16 and were decided by the annotator (D-032 to D-037, D-039 to D-042).

## 4. Evidence and relevance drafts

| Pair | MATCH | PARTIAL | NO_MATCH | Total |
| --- | ---: | ---: | ---: | ---: |
| CV1 x J1 | 7 | 5 | 7 | 19 |
| CV2 x J2 | 5 | 4 | 4 | 13 |

The first relevance drafts followed the narrow `cv_target` column literally, so 8 of 10 pairs got 0 only because the job title was outside that target. This led to D-037 (judge relevance in automatic mode), and the ratings were drafted again under v1.1 and v1.2.

J5 showed that the CP1 field `experience_bucket = not_stated` misses "5+ Years as an Engineer" in the JD text (recorded as FAIL-01 in [failures.md](../../failures.md)).

## 5. Checks done on the drafts

- Every JD quote (48) and every CV quote of a MATCH or PARTIAL label (21) was found word for word in its source.
- Every evidence row points to an existing extraction unit; unit ids are unique.
- No API call was made and no row was marked approved.
