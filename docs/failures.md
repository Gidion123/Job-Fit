# JobFit Failure Log

Failures found during development, evaluation, and testing. Each failure becomes a regression case when possible (Playbook standard S5).

## Entry format

| Field | Content |
| --- | --- |
| Id | `FAIL-NN` |
| Date and stage | For example 3 Oct 2026, CP2.4 |
| Category | Filter miss, stage-1 miss, extraction error, matching error, ordering error, safety, system |
| What happened | Short description with the job id and the synthetic CV id (never real CV text) |
| Why | Root cause, if known |
| Fix or decision | What changed, or why it was kept as a known limitation |
| Regression case | Path of the fixture or test that now covers it |

## Failures

### FAIL-01. v0 experience rule misses "5+ Years as an Engineer"

| Field | Content |
| --- | --- |
| Id | FAIL-01 |
| Date and stage | 29 Sep 2026, CP2.1 (found in the labeling pilot) |
| Category | Extraction error (CP1 rule-based v0) |
| What happened | Job F00114 (pilot J5, "AI Engineer (AI Agent & RAG)") asks for "5+ Years as an Engineer" and "2+ years shipping production LLM features". The CP1 v0 field `experience_bucket` says `not_stated`. |
| Why | `extract_years` in `src/jobfit/jobs/transform.py` only accepts a year mention when a context word (experience, pengalaman, work in, background) is within 80 characters. Neither sentence has one. The rule was built for precision, so it misses short phrasing like this. |
| Fix or decision | Kept as a known limitation. The CP1 snapshot and its numbers stay frozen. CP2 uses the LLM extractor for requirements, and this job is a development check for it: the extractor must return both duration units. |
| Regression case | Planned for CP2.2: pilot J5 (F00114) in the development extraction set. |
