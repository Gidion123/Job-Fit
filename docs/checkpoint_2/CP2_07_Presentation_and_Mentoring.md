# CP2.7: CP2 Presentation and Mentoring

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 14. PPT Check Point 2 + Mentoring · official date 4 Oct 2026  
**JobFit version of this checkpoint:** Same as the template: CP2 presentation and mentoring.  
**Planned work:** 3 to 4 Oct 2026 · **Actual:** deck, figures and one-page summary prepared on 4 Oct; presentation and mentoring session held on 4 Oct 2026 (exact time not captured); feedback recorded on 7 Oct (D-093); deck uploaded to the LMS (confirmed by Dion on 7 Oct; the submission evidence is kept in the LMS, outside this repository)  
**Status:** DONE (7 Oct 2026). Both acceptance criteria are met and all three evidence-to-keep items are accounted for (section 14). Design basis: System Design v1.3 and measured CP2 development results.

> The plan for all stages is in the [master plan](../master-plan.md). Sections 1 to 8 are the plan as written. Final status and evidence are in sections 9 to 14.

## 1. Goal of this stage

Show the model and system selection, tuning, and evaluation, and get the mentor's feedback on the CV-first flow and the deployment scope.

## 2. Inputs and prerequisites

- Checkpoints 8 to 13 results
- Playbook section 6 (CP2 minimum content)

## 3. Planned method

1. Build the deck following Playbook section 6.
2. Include the CV-first flow with optional filters as a proposal, and the reason import link is out of v1.
3. Show real metrics, failures, and limitations; missing results are shown as missing, not estimated.
4. Rehearse once with timing.
5. Present, then write down the mentor's feedback.
6. Upload the deck to the LMS (Dion).

## 4. Planned outputs

- CP2 deck in `04_Checkpoint_2/`
- LMS upload proof
- mentor feedback summary
- this stage report

## 5. Acceptance criteria

- The mentor sees a measurable selection, tuning, and evaluation process.
- The mentor's feedback is recorded in docs/decisions.md as new entries.

## 6. Evidence to keep

- deck file
- LMS proof
- feedback notes

## 7. Estimate and dependencies

- **Estimate:** About half a day for the deck, plus the session.
- **Depends on:** Checkpoints 11 to 13.

## 8. Fallback if blocked

If a result is not ready, present the method and what is missing, with the reason.

## 9. Checklist (final, 7 October 2026)

- [x] Build the deck following Playbook section 6 (12-slide v3, 4 Oct).
- [x] Include the CV-first flow with optional filters as a proposal, and the reason import link is out of v1.
- [x] Show real metrics, failures, and limitations; missing results are shown as missing, not estimated (development results only; CP2.4 had not run, as the fallback allows).
- [ ] Rehearse once with timing. Not recorded. A plan step, not an acceptance criterion or evidence item, so it does not block (section 14).
- [x] Present, then write down the mentor's feedback (session 4 Oct; feedback recorded 7 Oct, section 10).
- [x] Upload the deck to the LMS (Dion). Completed; confirmed by Dion on 7 Oct. The LMS submission evidence stays in the LMS and is not committed to this repository; no screenshot, receipt ID, timestamp or URL is recorded here.
- [x] Acceptance: The mentor sees a measurable selection, tuning, and evaluation process (session confirmed by Dion; the deck presented the measured CP2.1-CP2.3 development comparisons).
- [x] Acceptance: The mentor's feedback is recorded in docs/decisions.md as new entries ([D-093](../decisions.md)).

## 10. Results

**Deck and materials (4 Oct).** Six development figures from [CP2.5](CP2_05_Evaluation_Visualization.md), a [one-page content summary](supporting/CP2_Presentation_Summary_20261004.md), and the 12-slide deck `JobFit_CP2_Presentation_20261004_v3.pptx` (v2 kept). The deck is stored outside this repository in the project folder `04_Checkpoint_2/`, as the plan specifies. It has editable charts, speaker notes for a 15-minute session, and two diagrams (CV-first flow; privacy boundary). It separated completed CP2.1-CP2.2 work from provisional CP2.3 development results and the not-yet-run CP2.4 test.

**Session.** Held on 4 October 2026. Date evidence: the D-069 amendment (`evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1/cap_and_deadline_amendment_v2.json`) records that at 08:13 WIB Dion said the presentation was about six hours away, and the [4 October audit report](supporting/CP23_Audit_Fixes_20261004.md) opens "After the CP2 presentation". The exact time and attendees were not captured. Dion confirmed on 7 October that the session took place and supplied the mentor's feedback.

**Mentor feedback** (original wording in [D-093](../decisions.md)):

| # | Feedback | Disposition |
| --- | --- | --- |
| 1 | LLM latency is high, about 95 seconds. | Recorded as an observation from the presentation. The deck reported a DeepSeek Flash matching request p95 of about 91 s (D-068); the ~95 s figure is the mentor's. |
| 2 | Add a waiting-state UX, such as a progress or "thinking" animation, so the user knows processing is ongoing. | CP3 input (D-093 A). The CP3 UI already has a per-job progress bar and a spinner; CP3 checks them against this feedback. A perceived-wait mitigation, not a latency reduction. |
| 3 | Once the core features work, add vacancy-specific CV improvement guidance so the user can raise the match. | CP3 input after the core flow is stable (D-093 B), extending the CV coach plan (D-036) and CV coach v1. Suggestions stay grounded in real CV evidence, JD requirements and gaps; no invented experience; no guarantee of higher true suitability. |

**Disposition:** both recommendations go to CP3. Neither changes the D-087 freeze, the CP2.4 held-out result, evaluation thresholds or CP2 tuning, and neither triggers paid inference.

## 11. Interpretation and limitations

- The deck showed development results available on 4 October; provisional choices in it (DeepSeek matching, K = 20) were later replaced (D-083, D-086, D-087). This is expected under the fallback and does not affect the session's acceptance.
- The session record rests on Dion's confirmation plus the two dated repository traces above; no minutes, recording or attendee list are stored.
- The mentor's latency figure refers to the system as presented on 4 October, not to the frozen configuration measured later in CP2.4.

## 12. Decisions from this stage

- [D-093](../decisions.md): CP2 mentor feedback recorded and accepted as CP3 input (latency waiting-state UX; vacancy-specific CV improvement guidance).
- [D-094](../decisions.md): CP2 formally closed, including the owner-confirmed LMS submission.

## 13. Next step and handoff

CP3.1 takes the mentor feedback from this checkpoint as an input (master plan, CP3.1 prerequisites). CP3 inherits D-093 A and B; see the [CP2 closeout audit, section 12](CP2_Closeout_Audit_20261007.md#12-cp2-to-cp3-handoff). CP2.7 is DONE; CP2 is closed by [D-094](../decisions.md).

## 14. Closeout audit trail

**First pass (7 October, commit `de53544`), historical:** the repository had no record of the session, the feedback, a decision entry, a rehearsal or LMS proof. The master plan's earlier line "presented and mentored 4-5 Oct; mentor notes to be added" had no source. This report then said "mentor session not recorded yet" and was IN PROGRESS. The first pass also missed the two dated traces of the 4 October session cited in section 10.

**Second pass (7 October), historical:** session, feedback and D-093 resolved; LMS proof still open (table below, last row as it stood then).

| Item | Requirement source | Previous status | New evidence | Final status |
| --- | --- | --- | --- | --- |
| Mentor sees a measurable process | Master plan CP2.7, acceptance criteria | Missing | Dion's confirmation of the 4 Oct session; dated traces (D-069 amendment, 4 Oct audit report) | PASS |
| Feedback recorded as new decision entries | Master plan CP2.7, acceptance criteria | Missing | D-093 | PASS |
| Feedback notes | Master plan CP2.7, evidence to keep | Missing | Section 10 and D-093 | PASS |
| Deck file | Master plan CP2.7, evidence to keep | Reported, not verifiable | Session confirmed; deck v3 path recorded on 4 Oct; stored outside the repository by plan design | PASS (outside the repository) |
| Rehearsal with timing | Master plan CP2.7, step 4 only | Missing | None | Not recorded. Non-blocking: not an acceptance criterion and not an evidence item |
| LMS upload proof | Master plan CP2.7, step 6 and evidence to keep; the plan's status rule says a stage is DONE only when its acceptance criteria are met **and its evidence is saved** | Missing | None; not confirmed by Dion | **Open. Blocks CP2 closure** |

**Final pass (7 October), current:** Dion confirmed that the CP2.7 material was uploaded to the LMS.

| Item | Requirement source | Second-pass status | Final status | Evidence |
| --- | --- | --- | --- | --- |
| LMS upload and proof | Master plan CP2.7, step 6 and "Evidence to keep: LMS proof" | Missing, blocking | **PASS: owner-confirmed external LMS submission** | Dion's confirmation (7 Oct). The submission record is kept in the LMS, outside the Git repository, in the same way the deck file is kept in `04_Checkpoint_2/` and proof of work goes to the Timeline file (master plan section 9). No LMS artifact, ID, timestamp or URL is reproduced here |

All CP2.7 acceptance criteria and evidence items are now met. **CP2.7: DONE.**
