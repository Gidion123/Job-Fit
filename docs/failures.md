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

None recorded yet.
