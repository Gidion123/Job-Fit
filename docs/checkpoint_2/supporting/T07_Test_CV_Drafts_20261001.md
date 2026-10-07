# T07: Synthetic test CV drafts and review record

Date: 1 October 2026. Status: **DONE**. Dion approved the content and realism of both CVs on 1 October 2026. Content version remains 0.1; review_status is approved. Approval does not assign any evidence or relevance label.

## Scope and sources

Created the two files specified by T07. Neither file existed at the start. No human-reviewed CV was overwritten.

Drafting sources: T07 profile specifications, CV1 to CV3 for format and level of detail, guideline v1.2, and D-021, D-042, D-045, D-046. The current handoff, working brief, T03 report, and metadata audit were read to confirm the continuation point. No test JD text, retrieval output, or test label was inspected or used to write these CVs. The separate split test run reads corpus inputs internally and prints only test results.

Dion accepted T03 Part 1 on 1 October 2026: 214 development and 214 test jobs, all five pilot jobs in development, and no recorded probable duplicate crossing the split. D-045 remains approved, including 2 to 3 review hours per day and the late-test fallback. Neither approval needs to be requested again.

## Files and fixed reference date

| CV | File | Profile | Employment at the reference date |
| --- | --- | --- | --- |
| CV4 | `data/synthetic_cvs/cv_04_data_analyst_to_ds_id.md` | Nadia Kirana Wibowo, Surabaya, Indonesian CV, S1 Informatics, retail data analyst moving toward junior data science | 24 months |
| CV5 | `data/synthetic_cvs/cv_05_ml_engineer_3yr_en.md` | Arga Mahendra Prasetya, Jakarta, English CV, ML engineer at two fictional companies | 36 months |

Both files fix evaluation_reference_date to **2026-09-30**. The visible date line and metadata define "sekarang" or "present" using that date. The last completed month before drafting makes month-level counting clear. Later labeling and evaluation must retain this reference date for these CV versions. This does not change the application clock or other CVs.

## Chronology check

| CV | Item | Period | Employment months |
| --- | --- | --- | ---: |
| CV4 | S1 Informatics | September 2020 to August 2024 | Excluded |
| CV4 | Data Analyst, PT Contoh Ritel Timur | October 2024 to September 2026 | 24 |
| CV4 | Personal churn project | 2025 only | Excluded |
| CV4 | Introductory deep learning course | May 2026 | Excluded |
| CV5 | Bachelor of Informatics | September 2019 to August 2023 | Excluded |
| CV5 | Junior ML Engineer, PT Contoh Layanan Digital | October 2023 to March 2025 | 18 |
| CV5 | ML Engineer, PT Contoh Solusi Bahasa | April 2025 to September 2026 | 18 |
| CV5 | Personal prediction-monitor project | 2024 only | Excluded |
| CV5 | Introductory computer vision course | June 2026 | Excluded |

Counts use distinct calendar months at the stated month precision. Education ends before the first employment period. The two CV5 jobs are consecutive, with no overlap. Projects and courses fall within plausible periods but add no employment months. The year-only project dates do not establish a project duration. Employment totals do not prove the duration of every listed skill or suitability for any particular job.

## Quality checks performed

- **Level and scope:** CV4 works on SQL data preparation, retail dashboards, reporting, and A/B analysis. Its ML model is a personal notebook, with no production deep learning claim. CV5 has production NLP work, an internal RAG rollout, and deployment responsibilities shared with other engineers. It does not claim sole ownership of a large platform.
- **Evidence variation:** Git and R appear only in CV4's skills list. Kubernetes and Terraform appear only in CV5's skills list. Each CV has one year-only personal project and one completed course without a certificate. No evidence or relevance labels were assigned.
- **Plausible claims:** work and project scale is bounded. CV4's reporting improvement is modest. CV5's RAG rollout is limited and releases require manual approval. These are fictional profile details for human realism review, not measured JobFit results or guaranteed relevance scores.
- **Identity and contacts:** names, employers, and education providers were invented. Each file has one example.com email, no phone number, and no personal profile link or street address. The metadata clearly marks the content synthetic. Coincidental resemblance to real names cannot be ruled out.
- **Format and length:** both follow the Markdown sections of CV1 to CV3. Body length, excluding the metadata comment, is 271 whitespace-separated words for CV4 and 331 for CV5. CV1 to CV3 range from 228 to 305 words by the same count; CV5 is slightly longer because T07 requires two jobs plus project and course details.
- **Isolation and status at draft delivery:** both were test-only drafts with pending review (now approved; see the approval record below). They must not be used for tuning, prompt development, or configuration selection. No workbook, label file, embedding batch, or provider call was created by this task.

Mechanical checks used the project Python environment to verify metadata, date ordering, unique employment months, no overlap, example.com contacts, list-only skill placement, year-only project dates, course status, and word counts. These checks were followed by a manual content review. Hash checks also confirmed that CV1 to CV3, the split script and tests, both split ID files, and the manifest stayed unchanged. These are not model-quality measurements.

## Limited test-count reconciliation

The earlier verification records 81 passed and 1 skipped offline, and 82 passed with the database. The later T03 audit records 88 passed and 1 skipped in 7.70 seconds. The current tests/test_splits.py contains nine cases:

- The two original cases cover real split invariants and a transitive duplicate component forced into development.
- Five parameterized cases reject corrupted manifest fields: total, strata, output_hashes, input_hashes, and pilot_ids.
- One case rejects modified split-file contents.
- One case independently checks stratum counts and saved output hashes.

The seven additional cases account for the difference between the reported offline totals of 81 and 88. Fresh limited run: `env-job-fit/bin/python -m pytest -q tests/test_splits.py`, **9 passed in 6.58 seconds**. The full suite and database suite were not rerun for T07, and no split code or test was edited.

Provenance limit: the earlier JSON still contains its original 81/82 run results, but its saved test-file hash already matches the current file. That hash alone cannot establish the exact edit/run chronology. The reconciliation relies on the current case inventory, the earlier two-case source inspection, and the later audit narrative. The historical JSON was preserved.

## Original draft review STOP (closed on 1 October 2026)

Dion should review these five points, about 15 minutes per CV:

1. Whether the employment and education histories are realistic for two and three years of work.
2. Whether CV4's SQL, dashboard, and A/B responsibilities fit its level and the move toward junior data science.
3. Whether CV5's NLP, RAG, and deployment responsibilities are plausible with its team support and limited rollout.
4. Whether the skills-list, course, and personal-project evidence leaves believable limits.
5. Whether the natural language, profile details, and fixed reference date are clear enough for later annotation.

Historical draft STOP, now closed: Dion approved both CVs on 1 October 2026; see the final approval record below. Split acceptance and D-045 are settled. Approved CVs retain their test-only scope. Later test relevance labeling follows T06 after configuration freeze. Embedding work requires its own next instruction and paid-call readiness checks.

API cost for this session: **US$0**. No project API calls, git commands, file deletion, or workbook edits. STOP after delivering these drafts.

## Human approval and final provenance (1 October 2026)

Dion explicitly approved the existing CV4 and CV5 content and realism in this project chat. Only the administrative comments were updated. The CV bodies after the closing metadata comment are byte-for-byte unchanged; neither skills nor dates nor experience claims changed. Both remain test only. No labels were assigned, and neither CV enters development, model selection, prompt work, or the embedding run.

The machine-readable record is `evals/annotation_tasks/T07_approved_cv_manifest_v1.json`: approved date, reviewer, content version 0.1, draft SHA-256, approved full-file SHA-256, and unchanged body SHA-256. Full-file hashes change because approval metadata changes; body hashes preserve the content Dion reviewed. Checked both approved file hashes and body hashes against this record. T07 is complete; CP2.2 remains IN PROGRESS.

## Open pipeline work from the human-mediated review

1. **Explicit evaluation clock.** These CV versions use 2026-09-30. A future evaluation configuration must explicitly pass and log `analysis_date` for experience calculations. Do not silently use the computer date or rely on LLM interpretation of CV metadata. User-uploaded metadata cannot override system configuration. Check existing rules before changing any other CV reference date. This wiring is not implemented by T07.
2. **Original date precision.** The 24/36 month totals use the current inclusive calendar-month convention. The parser schema currently uses full dates; preserve month-year versus year-only precision rather than invent day values. Propose a representation and explain schema/constraint impacts to Dion before implementation. No parser/schema, experience rule, or label is changed here.

Total time in a job does not prove equal time with each technology. Analyst employment is not automatically Data Scientist experience. Use the supported activities and field of work. Develop the parser and prompts with development data and separate synthetic fixtures, never these test CVs. These open pipeline items do not cancel CV approval.
