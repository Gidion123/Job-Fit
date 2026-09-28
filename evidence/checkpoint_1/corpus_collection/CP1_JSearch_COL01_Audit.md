# CP1.1F: JSearch COL01 audit

**Request date:** 25 September 2026  
**Query:** `Data Scientist in Bandung`; `country=id`; `language=id`; `num_pages=1`  
**Response:** HTTP 200 OK in the saved screenshot; JSON `status=OK`; 4 returned jobs.  
**Raw evidence:** [response JSON](./CP1_JSearch_COL01_DataScientist_Bandung_ID_Response.json) and [result screenshot](./CP1_JSearch_COL01_DataScientist_Bandung_ID_Screenshot.png).  
**Decision scope:** Initial manual data-quality triage, not final ground-truth labeling.

## Per-job triage

| # | Role / source | JD length | Initial disposition | Evidence and limitation |
| --- | --- | ---: | --- | --- |
| 1 | Data Scientist at PT BPR Karyajatnika Sadaya / JobLeads | 3,811 characters | **KEEP, conditional core job** | Relevant Data Scientist responsibilities and explicit requirements, including 2-3 years of experience. Useful for the corpus and as a seniority hard-negative case for fresh graduates. The tail contains an application question and repeated bank advertisement text; clean it while keeping the original JSON. `posted_at` is only relative text (“4 hari yang lalu”, "4 days ago"); a structured timestamp is absent. |
| 2 | Data Scientist: Analitik & ML untuk Keputusan Bisnis at the same employer / JobLeads | 479 characters | **HOLD as probable duplicate; exclude from usable-core count** | Same employer, Bandung location, relative posting text, and a short paraphrase of job #1's responsibilities. URL and `job_id` differ, so duplication is plausible rather than proven. The summary leaves out explicit qualifications and is not enough for requirement extraction. Resolve against source pages/content before final deduplication. |
| 3 | Data Intelligence Analyst at PT Tricada Intronik / Glints | 3,552 characters | **KEEP as adjacent-role / hard-negative candidate** | Full BI/analytics JD with SQL, dashboards, KPI and 2+ years; no clear Data Scientist or ML-modeling requirement. Useful for testing a Data Scientist role-family gate. Do not count it as a confirmed target-role job until the inclusion rubric is settled. Posted date is absent. |
| 4 | Data Analyst at Taiyo Shop Indo Online / Loker.id | 56 characters | **REJECT from usable corpus; keep raw evidence** | A one-sentence vacancy mention without responsibilities or requirements. `job_location` says Kabupaten Bandung Barat, while `job_city` says Kota Bandung, so the location fields also need review. Posted date is absent. |

## Aggregate checks

| Check | Result |
| --- | ---: |
| Returned job slots | 4 |
| Nonempty descriptions | 4/4 |
| Descriptions at least 500 characters | 2/4 |
| Apply/source links present | 4/4 |
| Direct company apply links | 0/4 (`job_apply_is_direct=false`) |
| Structured posting timestamps | 0/4 |
| Nonempty `job_city` and `job_country` | 1/4 each |
| Salary fields populated | 0/4 |
| Exact `job_id`, apply-URL, or company/title/location overlap with the archived 40 JSearch result slots | 0 found |
| Clear new core target-role jobs after initial triage | 1, conditional on cleaning |
| Additional adjacent-role / hard-negative candidates | 1 |

The screenshot shows a single-request duration of about 6.6 seconds. This is only a UI observation for COL01, **not** a p50/p95 latency measurement.

## Findings for the collection strategy

1. A query for a target title can return adjacent analyst roles; role-family relevance needs explicit review before the sample is counted.
2. `job_description != null` is not enough: one response is a short summary and one has only 56 characters.
3. A distinct provider `job_id` and URL do not rule out a duplicate vacancy; same-company paraphrases need content/source checks.
4. A relative `job_posted_at` must stay raw text; do not convert it to a verified `posted_at` or replace it with `first_seen_at`.
5. The raw response gives candidate postings, not proof that the linked vacancies are still active on 25 September. Source-page verification is a later data-quality step.

**Next:** Expand the provisional JSearch sample with one more role/location query, then apply the same audit. Keep the 50-100-job target based on usable, deduplicated records rather than result slots.

