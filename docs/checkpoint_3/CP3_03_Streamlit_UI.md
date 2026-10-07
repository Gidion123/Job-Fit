# CP3.3: Streamlit UI

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 17. Build Streamlit UI · official date 7 Oct 2026  
**JobFit version of this checkpoint:** Same as the template.  
**Planned work:** 7 Oct 2026 · **Actual:** 6 Oct 2026  
**Status:** DONE LOCALLY · screenshots and recording pending · design basis: System Design v1.3

> Plan sections are kept as written. Results are added below, with links to the [experiment log](../experiments.md). The plan for all stages is in the [master plan](../master-plan.md).

## 1. Goal of this stage

Build a demo that shows the value in under 3 minutes, without moving business logic into the UI.

## 2. Inputs and prerequisites

- Deployed API from checkpoint 16

## 3. Planned method

1. Demo CV or upload, then the parsing summary with the location suggestion.
2. Optional filters with the UNKNOWN option.
3. Recommendations with statuses and the text "K candidates from the search were analyzed".
4. Job detail with evidence per requirement.
5. Paste JD compare.
6. Minimal market insight and CV suggestions.
7. Delete session and feedback.
8. The "Demo with saved results" label.

## 3A. D-051 private upload and session UX

Use the [privacy contract](../privacy-threat-model.md): pre-upload notice that the server receives the file → local extraction/masking → editable exact outgoing text → explicit provider-processing consent → LLM parsing summary confirmation → optional filters/recommendations. Consent and parsing confirmation are distinct. Text edits invalidate consent and dependent results. Provide a visible “Hentikan & hapus sesi” action throughout the flow, truthful expiry/cleanup messaging and synthetic-demo fallback.

Never cache private documents/results globally. Implement actual browser liveness and best-effort departure notification; a server loop is not liveness. Distinguish browser reload from ordinary Streamlit reruns. A hidden tab alone is not exit; document suspension/expiry behavior and test it. UI reset alone is not server deletion.

- [ ] Preview, consent and parsing confirmation tested separately.
- [ ] Stop/delete, reload, hidden tab, navigation and disconnect verified with server state.
- [ ] No private payload/token in URLs, browser localStorage, shared caches or executable rendering.


## 4. Planned outputs

- Streamlit app
- screenshots
- demo script
- this stage report

## 5. Acceptance criteria

- A mentor can understand the value in under 3 minutes.
- The synthetic demo works.
- No business logic in the UI.

## 6. Evidence to keep

- screenshots
- short screen recording

## 7. Estimate and dependencies

- **Estimate:** About 1 working day.
- **Depends on:** Checkpoint 16 deployment.

## 8. Fallback if blocked

Build the core flow first; the minimal features and styling come last.

## 9. Checklist

- [ ] Demo CV or upload, then the parsing summary with the location suggestion.
- [ ] Optional filters with the UNKNOWN option.
- [ ] Recommendations with statuses and the text "K candidates from the search were analyzed".
- [ ] Job detail with evidence per requirement.
- [ ] Paste JD compare.
- [ ] Minimal market insight and CV suggestions.
- [ ] Delete session and feedback.
- [ ] The "Demo with saved results" label.
- [ ] Acceptance: A mentor can understand the value in under 3 minutes.
- [ ] Acceptance: The synthetic demo works.
- [ ] Acceptance: No business logic in the UI.

## 10. Results

Not run yet.

## 11. Interpretation and limitations

Not run yet.

## 12. Decisions from this stage

D-051 privacy design is approved; implementation outcomes and release acceptance are pending. Record outcomes in the [decision log](../decisions.md) without treating design approval as a test pass.

## 13. Next step

CP3.4 (checkpoint 18): end-to-end testing and feature freeze.

## Results (6 Oct 2026)

- **Built:** `ui/streamlit_app.py`, `ui/components.py`, `ui/api_client.py`. The UI calls the API only.
- **Covered:** demo CV with parsing summary and location suggestion; optional filters with a separate block for missing values; "K candidates from the search were analyzed"; scored, conflict and not-fully-analyzed groups; evidence per requirement and the job posting text; paste a job; market counts; CV suggestions and the CV coach; feedback; "Hentikan & hapus sesi"; the "Demo with saved results" label.
- **Privacy UX:** notice before upload, editable masked preview, consent for the exact text, liveness heartbeat every 30 s while the page is open, and an honest message when a session expired. Text from postings and CVs is escaped before Markdown, so it cannot add links or load images.
- **Tests:** `tests/test_ui_client.py` runs the app with Streamlit's test runner against the real wiring with live analysis off.
- **Pending:** screenshots and a short recording for the deck (Dion).
