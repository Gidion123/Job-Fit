# CP1.1F: JSearch COL02 audit

**Evidence received:** 26 September 2026. The response itself does not establish a trustworthy request timestamp.  
**Query:** `Data Scientist in Surabaya`; `country=id`; `language=id`; `num_pages=1`.  
**Response:** HTTP 200 OK in the saved screenshot; JSON `status=OK`; 4 returned jobs.  
**Raw evidence:** [response JSON](./CP1_JSearch_COL02_DataScientist_Surabaya_ID_Response.json) and [result screenshot](./CP1_JSearch_COL02_DataScientist_Surabaya_ID_Screenshot.png).  
**Decision scope:** Initial manual quality triage, not final ground-truth labeling or proof that a vacancy is active.

## Per-job triage

| # | Role / source | JD length | Initial disposition | Evidence and limitation |
| --- | --- | ---: | --- | --- |
| 1 | Data Analyst Staff at PT Mazuta Bima Tek / JobLeads | 1,652 characters | **HOLD as adjacent Data Analyst candidate** | Responsibilities include SQL, Python, cleaning, modeling, dashboards, and business analysis. It says both “Fresh Graduates are welcome to apply” and “1-2 years of experience”; record this seniority ambiguity instead of forcing one label. The tail contains application-form questions that need cleaning. It is not a Data Scientist vacancy, and its JobLeads apply link is not a direct company link. |
| 2 | Data Analyst at CV Green Mile Indonesia / JobLeads | 1,249 characters | **HOLD as adjacent Data Analyst candidate** | Substantive analytics/dashboard and basic Python/SQL requirements; explicitly welcomes fresh graduates. It is not a Data Scientist vacancy. Same employer, city and role family as #3, so deduplication is needed before counting. Apply link is not direct. |
| 3 | Data Analyst - Transform Data into Actionable Insights (Surabaya) at CV Green Mile Indonesia / Relidevega.blogspot.com | 3,435 characters | **HOLD; probable cross-source duplicate of #2, provenance review** | Same employer/city/role family as #2, with a longer English description. Distinct IDs and URLs do not prove a distinct vacancy. The result points to a blog, and the JD includes a separate generic `globaljob.sbs/form/jobs` application URL. Do not use or recommend that form without verifying the original employer posting. |
| 4 | Head of Data Science - Marketplace at PT. Digital Nusantara / Relidevega.blogspot.com | 1,374 characters | **HOLD; seniority hard-negative candidate, provenance review** | The JD explicitly asks for at least 8 years of experience and management of a data-science team. The title is in the target family but far beyond a fresh-graduate role. The result is from the same blog as #3 and includes the same generic external application form; the original employer provenance and vacancy status are unverified. |

## Aggregate checks

| Check | Result |
| --- | ---: |
| Returned job slots | 4 |
| Nonempty descriptions | 4/4 |
| Descriptions at least 500 characters | 4/4 |
| Apply/source links present | 4/4 |
| Direct company apply links (`job_apply_is_direct`) | 0/4 |
| Structured posting timestamps | 0/4 |
| Nonempty `job_city` and `job_country` | 4/4 each |
| Salary fields populated | 0/4 |
| Exact `job_id`, apply-URL or normalized company/title/city overlap with the previous eight JSearch benchmark files and COL01 (44 slots) | 0 found |
| Exact overlap among COL02 results by those keys | 0 found |
| Probable same-vacancy cluster requiring review | #2 and #3 |
| Clear new Data Scientist roles suitable for a fresh-graduate target after initial triage | 0 |
| Adjacent Data Analyst candidates to review against the corpus inclusion rubric | 2 (#1 and #2); **not yet counted as usable core jobs** |

The screenshot shows about 4.1 seconds for this single request. It is not a latency distribution. The relative `job_posted_at` strings (one, five or six days ago) are kept as supplied; no verified absolute posting date can be derived from the JSON. The response and screenshot contain no visible API key, but the raw source links are still unverified.

## Collection decision

The query for Data Scientist returned two Data Analyst postings and one very senior Data Science posting. This is evidence of role/seniority drift, not enough evidence of a new usable target-role job. Keep all four raw records for provenance and error analysis. Before admitting #1 or #2 to the broader AI/ML/Data sample, settle the inclusion rubric and verify their source pages; resolve #2/#3 as a probable cross-source duplicate. Do not enter the generic application form from #3/#4 as a trusted employer link.
