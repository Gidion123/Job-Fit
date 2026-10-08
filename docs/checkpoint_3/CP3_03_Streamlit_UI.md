# CP3.3: Streamlit UI

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 17. Build Streamlit UI · official date 7 Oct 2026  
**JobFit version of this checkpoint:** Same as the template.  
**Planned work:** 7 Oct 2026 · **Actual:** 6 Oct 2026  
**Status:** PARTIAL · demo flow DONE LOCALLY (6 Oct); public upload flow and mentor refinements PLANNED / NOT YET VALIDATED; product-experience scope set by D-102 (8 Oct) · design basis: System Design v1.3

> Plan sections are kept as written. Results are added below, with links to the [experiment log](../experiments.md). The plan for all stages is in the [master plan](../master-plan.md).

## Product experience target (8 Oct 2026, D-102): PLANNED

[D-102](../decisions.md) makes the UI part of the product goal: the public app should feel like a small, intentionally designed product, not a select box and raw JSON. Priority: clarity > trust > usability > product polish > decoration. Streamlit stays the technology.

- **First screen:** a short explanation of JobFit, public-beta wording, the privacy and consent explanation, and two obvious primary actions: **Find Jobs** (discovery) and **Check a Job** (paste a job description found elsewhere).
- **Stage-aware progress (refines Mentor A below):** real stages from the API. Find Jobs: analyzing your CV → searching relevant jobs → reading job requirements → matching your experience → preparing recommendations. Check a Job: analyzing your CV → reading job requirements → matching your experience → preparing your result. Completed, current and pending steps; counts such as "job i of N" only where real; no fake percentages.
- **Results:** Find Jobs first shows retrieval-stage **Relevant Jobs** without a match score; after the user chooses Analyze Fit, the analyzed job card shows the match score and what it means, strengths, gaps, supporting CV evidence and explanations; job detail; clear calls to action. See "Find Jobs filters and results" below.
- **"Improve My CV for This Job" (refines Mentor B below):** for a matched job or a pasted JD. Three kinds of suggestion: representation improvement (existing evidence only), possibly missing from the CV (add it only if you really did it, with its real context), true gap (stated plainly; wording cannot fix it). Shown as current statement → suggestion → why it helps → supporting CV evidence. JobFit never suggests inventing skills, experience, employers, years, certifications, projects, achievements, metrics, tools or impact. Coaching only: no CV editor, resume builder or cover-letter generator in CP3. See the [CV coach plan](../cv-coach-plan.md).
- **Coach scope (8 Oct anti-overengineering correction):** the deterministic, evidence-grounded version is sufficient for CP3. LLM-generated rewriting is P2 (post-beta) unless separately approved after a cost bound and an anti-fabrication evaluation.
- **States:** empty, failure, quota, busy, budget-exhausted and "Live AI analysis is temporarily unavailable. Please try again later.", each with the saved-demo fallback.
- **Layout:** consistent typography, spacing and components; reasonable on mobile and desktop.
- **Tests:** Streamlit test-runner cases for both flows, each progress sequence, each refusal state and the coaching anti-fabrication checks; screenshots of the deployed app.

### Find Jobs filters and results (Phase 3b acceptance; clarification, 8 Oct 2026)

A clarification of the accepted Find Jobs UX (D-010 optional filters, D-102 flows, D-103 search stage), not a new decision. Streamlit implementation is Phase 3b.

1. **Optional preferences before Find Jobs.**
   - Before running Find Jobs, the user may set supported preferences: target role (`role_family`, where the corpus metadata supports it); location or country; work mode (remote, hybrid or on-site, where available); posting recency (`posted_at`).
   - All of them are optional and default to *Any*. With nothing set, Find Jobs works normally: real CV → embedding → retrieval from the eligible production corpus → relevant jobs. The user is never forced to choose a location or role before using Find Jobs.
   - The CV stays the primary retrieval signal. Target role is a preference and refinement by default, not an automatic strict exclusion: related roles may still appear when retrieval finds them relevant, unless the UI explicitly offers and the user turns on a strict, exact-role mode. Location or country, work mode and recency may act as explicit constraints when the user chooses them.
   - The existing UNKNOWN / missing-metadata behaviour is preserved (D-010, `include_unknown` on by default): a job is never silently excluded only because optional metadata is missing, and an unknown value is shown as unknown.
2. **Retrieval-stage results.**
   - The first list is labelled **Relevant Jobs** (search-stage results), never as JobFit match rankings or CP2.4 final order.
   - An unanalyzed job shows no evidence-grounded match score.
   - Only the user's explicit **Analyze Fit** on a chosen job starts `job_analysis` (within the D-103 allowance).
3. **Refining the displayed results.**
   - After the list is shown, the user can refine the current results by role family, location, work mode and recency, and sort them.
   - Refinement is local and in-memory over the current retrieval-stage result set. Ordinary filter changes never trigger retrieval.
   - Under the D-103 allowance of one `search` per accepted session, changing result filters never consumes another search. If an explicit **Search again** action is added later, it must be visibly distinct from local result filtering and must respect the D-103 search allowance and the budget.
   - A clear **Reset filters** action restores the full returned list.
   - A refinement that leaves no jobs shows an understandable zero-results state, for example: "No jobs in these results match your filters. Clear filters to see all relevant jobs."
   - The filterable metadata for local refinement (`role_family`, location or country, `work_mode`, `posted_at`) comes with the Find Jobs search response. The UI does not call `GET /jobs/{job_id}` once per result just to get filter metadata (no N+1 calls); that endpoint stays for genuine job-detail views. Any API addition for this belongs to the Phase 3b or real-CV task.
4. **Cost semantics.**
   - Selecting or changing optional preferences by itself makes no provider call.
   - The explicit Find Jobs action runs one D-103 `search` phase and may incur its already bounded embedding cost (`search_max` US$0.0001648).
   - Once retrieval results exist, local filtering, sorting, reset and the zero-results state make no additional paid or deep-analysis call: no new search, no extraction, no Sol or Luna call, no `job_analysis`.
   - Paid, evidence-grounded analysis begins only when the user selects a job and chooses Analyze Fit.
5. **Tests (Phase 3b).** Streamlit tests cover:
   - Find Jobs with every preference left at *Any*;
   - target role used as a preference, not a strict exclusion (unless strict mode is on);
   - unknown-metadata jobs kept;
   - Relevant Jobs labelling with no match score on unanalyzed cards;
   - local refinement, sorting and reset making no API search, extraction or analysis call and no per-result metadata call (fake API call counter);
   - the zero-results state;
   - Analyze Fit as the only path to `job_analysis`.

## CP3 final plan for this stage (7 Oct 2026, D-095 to D-100)

**JobFit scope:** public upload flow, waiting experience and coach. Everything in this section is **PLANNED / NOT YET VALIDATED** unless marked otherwise. Stage definition: [master plan](../master-plan.md#cp33-streamlit-ui-checkpoint-17). Tasks: [CP3 execution plan](CP3_Execution_Plan.md).

- **Already done (local, 6 Oct):** see "Results (6 Oct 2026)" below.
- **Known defect:** FAIL-37. The upload text says names are masked, but uploads get no name or address masking today.
- **Public upload flow:**
  - a required name field and an optional address field (passed as reviewed identifiers);
  - masking text that lists exactly what is masked;
  - consent text naming OpenRouter and the routed providers, as recorded in CP3.4;
  - the upload allow-list `pdf`, `docx`, `txt`, `md` (unchanged from today);
  - `server.maxUploadSize` plus the Caddy body limit;
  - safe messages for unsupported, oversized, encrypted, scanned and malformed files, including rejected DOCX archives;
  - quota, busy and budget messages with a saved-demo fallback;
  - the client IP forwarded from Caddy's `X-Forwarded-For` with the internal token.
- **Mentor A (D-093), waiting UX:**
  - stage text (parsing, searching, reading job requirements i of N, checking evidence j of K);
  - elapsed time;
  - a measured typical range (after the CP3.4 baseline);
  - graceful timeout and error states;
  - cancel where safe (calls already in flight still finish and are billed, and the UI says so);
  - no fake percentages.
- **Mentor B (D-093), coach v1 refinement:**
  - each item shows the JD requirement and the CV evidence status (missing, or partial with the quoted line);
  - no-invention and no-guarantee wording;
  - no LLM coach.
- **Tests:** Streamlit test-runner cases for the upload states, waiting states and coach wording; coach checks (0 invented items; "not done" gives no bullet).
- **Acceptance:** see the master plan, CP3.3 points 5 and 10.
- **Status:** PARTIAL (demo flow done locally).

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
