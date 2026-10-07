# CP3.4: End-to-End Testing

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 18. Testing End-to-End Application · official date 8 Oct 2026  
**JobFit version of this checkpoint:** Same as the template, on the deployed app.  
**Planned work:** 8 Oct 2026 (feature freeze at the end of the day) · **Actual:** 6 Oct 2026 (local part)  
**Status:** PARTIAL · local checks passed; deployed and live checks pending · design basis: System Design v1.3

> Plan sections are kept as written. Results are added below, with links to the [experiment log](../experiments.md). The plan for all stages is in the [master plan](../master-plan.md).

## 1. Goal of this stage

Test the real user journey and the critical failure paths on the deployed app, then freeze features.

## 2. Inputs and prerequisites

- Deployed app from checkpoints 16 and 17

## 3. Planned method

1. End-to-end run on the deployed app for each synthetic CV.
2. Provider failure: a clear error or an explicit demo-mode offer.
3. Prompt-injection fixtures in pasted JDs.
4. PII check of the logs.
5. p50/p95 latency and cost per run, live and cached separately.
6. Record the feature freeze.

## 3A. D-051 security acceptance before real uploads

Execute all PR-01-PR-10 scenarios in [privacy-threat-model.md](../privacy-threat-model.md) on the deployed topology using synthetic identifiers. Two isolated browser sessions must never read, mutate or delete one another's CV/report. Test deletion and expiry during in-flight model work, discarded late responses, independent cleanup when no request follows, actual disconnect/idle/absolute bounds and reload/background behavior. Inspect both LLM and embedding payloads, logs, database, cache, temporary upload copies and provider-failure routing. Consent is not a substitute for these checks.

- [ ] PR-01-PR-10 have reproducible outcomes and safe synthetic evidence.
- [ ] Measured access-revocation and cleanup bounds support exact product wording.
- [ ] Missing endpoint/privacy or upload controls fail closed, never downgrade silently.
- [ ] Real-CV gate stays disabled on critical failure; do not claim security from offline tests alone.


## 4. Planned outputs

- E2E checklist
- security and reliability results
- performance snapshot
- this stage report

## 5. Acceptance criteria

- The happy path and the critical failure paths pass on the deployed app.
- No raw CV in the logs.
- The feature freeze is recorded.

## 6. Evidence to keep

- checklist
- test outputs
- latency and cost table

## 7. Estimate and dependencies

- **Estimate:** About 1 working day.
- **Depends on:** Checkpoint 17.

## 8. Fallback if blocked

If the deployment is unstable, record a backup demo video and fix only critical bugs.

## 9. Checklist

- [ ] End-to-end run on the deployed app for each synthetic CV.
- [ ] Provider failure: a clear error or an explicit demo-mode offer.
- [ ] Prompt-injection fixtures in pasted JDs.
- [ ] PII check of the logs.
- [ ] p50/p95 latency and cost per run, live and cached separately.
- [ ] Record the feature freeze.
- [ ] Acceptance: The happy path and the critical failure paths pass on the deployed app.
- [ ] Acceptance: No raw CV in the logs.
- [ ] Acceptance: The feature freeze is recorded.

## 10. Results

Not run yet.

## 11. Interpretation and limitations

Not run yet.

## 12. Decisions from this stage

D-051 privacy design is approved; implementation outcomes and release acceptance are pending. Record outcomes in the [decision log](../decisions.md) without treating design approval as a test pass.

## 13. Next step

CP3.5 (checkpoint 19): final deck and portfolio.

## Results (6 Oct 2026, local)

- **Script:** `scripts/e2e_check.py --base <url> [--live] [--write]` writes a report without CV text or canary values.
- **Local run (API started from exactly the image file set, live off):** 27 of 27 checks passed: saved demo for CV1 and CV2, no invented score for held jobs, suggestions with the claim guard, coach bullets from answers only, job detail, market, feedback, invalid inputs, masking canaries, wrong-digest consent refused, upload parsing gated, delete and no access after delete. The server log had no canary.
- **Pending:** the same script on the deployed URL; `--live` for one live run and the prompt-injection fixture (about US$0.30); p50/p95 latency and cost for live runs; recording the feature freeze.
