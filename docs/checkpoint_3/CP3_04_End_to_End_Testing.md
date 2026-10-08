# CP3.4: End-to-End Testing

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 18. Testing End-to-End Application · official date 8 Oct 2026  
**JobFit version of this checkpoint:** Same as the template, on the deployed app.  
**Planned work:** 8 Oct 2026 (feature freeze at the end of the day); moved to 9 Oct with the formal freeze at the end of 9 Oct (D-100) · **Actual:** 6 Oct 2026 (local part)\
**Status:** PARTIAL · local checks passed (27/27); deployed validation, privacy release gate and freeze PLANNED for 9 Oct (D-100); controlled public beta acceptance bar set by D-102 (8 Oct) · design basis: System Design v1.3

> Plan sections are kept as written. Results are added below, with links to the [experiment log](../experiments.md). The plan for all stages is in the [master plan](../master-plan.md).

## Controlled public beta validation (8 Oct 2026, D-102): PLANNED

The deployed checks use the [D-102](../decisions.md) public-beta bar: safe enough for controlled public use, cost bounded, privacy aware, testable, observable, deployable and honest about residual limitations; not enterprise availability.

- **Flows:** Find Jobs and Check a Job end to end on the deployed stack (owner token while dark), including stage-aware progress and "Improve My CV for This Job" with its anti-fabrication checks.
- **States:** quota, busy, budget-exhausted and "temporarily unavailable" refusals show honest messages and the saved demo.
- **Real-host persistence:** the ledger storage survives an API restart, a container recreate and a host reboot with the same `storage_id` and unchanged lifetime spend (the Phase 8 obligation from the persistent-ledger work).
- **Boundary:** an external check shows only ports 80 and 443; no admin or observability interface is reachable anonymously.
- **Limited beta trial:** a few real users try both flows after public live is allowed by its gate and the separate cost-bound decision.

## CP3 final plan for this stage (7 Oct 2026, D-095 to D-100)

**JobFit scope:** deployed validation, privacy release gate and feature freeze. Everything in this section is **PLANNED / NOT YET VALIDATED**. Stage definition: [master plan](../master-plan.md#cp34-end-to-end-testing-checkpoint-18). Tasks: [CP3 execution plan](CP3_Execution_Plan.md).

- **Date change:** the formal feature freeze moves to the **end of 9 October 2026** (D-100). The presentation stays on 11 October.
- **Two-layer deployed validation:**
  - **A, external public:** Internet → Caddy → Streamlit. Checks HTTPS, page availability, the saved demo, the real-CV UI journey once enabled, and user-visible failure states.
  - **B, internal API:** `scripts/e2e_check.py` against the private FastAPI, run inside the VPS Docker network or through an SSH tunnel to a localhost-only port. FastAPI is never exposed publicly for testing.
- **Privacy release gate** (for public real-CV live, D-095):
  - PR-01 to PR-10 with synthetic canaries in every sink enabled for the beta: responses, provider payloads, logs, database dump, temporary files, `/metrics` and upload failure paths (including DOCX gate rejections); the Langfuse export (Langfuse is required for the final beta since D-103);
  - PR-08 fail-closed;
  - the [D-104](../decisions.md#d-104-structural-cv-data-minimization-boundary-for-the-real-cv-public-beta) structural boundary checks: header, Summary-family and privacy-section removal, start at the first evidence-bearing section, `professional_boundary_not_found` fail-closed, and no Summary text in provider payloads. PR-10's masked arm will use the D-104 sanitized text; the D-100 thresholds are unchanged (6 of 781 quoted CV1/CV2 gold evidence rows cite Summary and are disclosed);
  - the **OpenRouter per-route privacy record** (CV parse, query embedding, JD extraction, evidence matching). A gap is reported before public live and never fixed by changing the model, prompt, K or weights.
  - `JOBFIT_PUBLIC_LIVE=1` only after the gate passes.
- **Cost and abuse checks:**
  - the configured `full_analysis_upper_bound` is at most the US$2/day cap;
  - quota fairness (refusals before billing don't consume the ticket);
  - the daily cap;
  - the busy gate.
- **Paid owner runs (inside the US$5 validation budget):**
  - public-live E2E;
  - a latency baseline with stage timings;
  - FAIL-36 confirmation (an offline fake-SDK proof first, then a live measurement; no claim about the mentor's 95 s without a measurement);
  - PR-10, original vs masked on CV1/CV2 (about US$2, D-100 thresholds).
- **Other checks:**
  - no duplicate vacancy in production retrieval on the verified seeded corpus (a VPS sync test with an idempotent re-run is post-beta; an optional manual corpus refresh before the demo is allowed, not required);
  - metrics and the beta Grafana dashboard checked with live data, with screenshots (a test alert email is P2 (post-beta));
  - mentor A/B checks on the deployed app.
- **Feature freeze record:** the final validation table (command, passed, skipped, failed, reason for each skip), 0 unexpected offline failures, freeze verify ok, the gate status.
- **Fallback:** if the gate is not green by the freeze, public live stays off and the presentation uses owner-token live plus the saved demo, stated in this report.
- **Status:** PARTIAL (local 27/27 only).

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
