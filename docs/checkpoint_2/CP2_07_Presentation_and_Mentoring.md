# CP2.7: CP2 Presentation and Mentoring

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 14. PPT Check Point 2 + Mentoring · official date 4 Oct 2026  
**JobFit version of this checkpoint:** Same as the template: CP2 presentation and mentoring.  
**Planned work:** 3 to 4 Oct 2026 · **Actual:** development figures, a one-page content summary, and a 12-slide deck prepared on 4 Oct; mentor session not recorded yet  
**Status:** IN PROGRESS · blocks CP2 closure (closeout audit, 7 Oct 2026; section 14) · design basis: System Design v1.3 and measured CP2 development results

> The deck is ready for Dion's review and rehearsal. This report does not claim that the deck was submitted or the mentor session occurred. The plan for all stages is in the [master plan](../master-plan.md).

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

## 9. Checklist

- [x] Build the deck following Playbook section 6.
- [x] Include the CV-first flow with optional filters as a proposal, and the reason import link is out of v1.
- [x] Show real metrics, failures, and limitations; missing results are shown as missing, not estimated.
- [ ] Rehearse once with timing.
- [ ] Present, then write down the mentor's feedback.
- [ ] Upload the deck to the LMS (Dion).
- [ ] Acceptance: The mentor sees a measurable selection, tuning, and evaluation process.
- [ ] Acceptance: The mentor's feedback is recorded in docs/decisions.md as new entries.

## 10. Results

Six [development figures](CP2_05_Evaluation_Visualization.md), a [one-page content summary](supporting/CP2_Presentation_Summary_20261004.md), and the [12-slide CP2 deck](../../../04_Checkpoint_2/JobFit_CP2_Presentation_20261004_v3.pptx) (v3; v2 is kept) are ready. The deck uses an editable table excerpt from reviewed development labels, native editable charts, and speaker notes paced for a 15-minute session. Two editable diagrams show the CV-first user flow and the planned privacy boundary between private session data and public job data. The mentor question slide was removed at Dion's request. The deck distinguishes completed CP2.1 and CP2.2 work from provisional CP2.3 development results and the unrun CP2.4 test evaluation. Rehearsal, LMS proof, and mentor feedback remain pending.

## 11. Interpretation and limitations

The deck is based on development results available on 4 October 2026. Provisional model and retrieval choices are not test-set findings. The timing is an estimate from speaker notes; Dion has not rehearsed it yet.

## 12. Decisions from this stage

None yet. Decisions are recorded in the [decision log](../decisions.md) when they are made.

## 13. Next step

CP3.1 (checkpoint 15): FastAPI service.

## 14. Closeout audit (7 October 2026)

The [CP2 closeout audit](CP2_Closeout_Audit_20261007.md) searched the whole repository for CP2.7 evidence. Nothing in this report's checklist was changed, because no new evidence was found.

| Item | Evidence in the repository | Status |
| --- | --- | --- |
| Deck | This report (12-slide v3 prepared on 4 Oct) and the [one-page summary](supporting/CP2_Presentation_Summary_20261004.md). The deck file is stored outside the repository (`04_Checkpoint_2/`), as planned, so it cannot be checked here | Reported, not verifiable from the repository |
| Rehearsal with timing | None | Missing |
| Presentation and mentor session | The master plan said "presented and mentored 4-5 Oct; mentor notes to be added". That line first appears in the 7 Oct snapshot commit with no source, and the same master plan listed "Mentor feedback at CP2" as Open | Owner-reported, not evidenced |
| Mentor feedback written down | None | Missing |
| Mentor feedback as new entries in `docs/decisions.md` | None: D-001 to D-090 contain no entry sourced from the CP2 mentor session | Missing |
| LMS upload proof | None | Missing |

The deck content predates the CP2.4 held-out test and shows development results only. The CP2.7 fallback allows that ("present the method and what is missing"); the deck is not expected to contain CP2.4 numbers.

**What Dion needs to add before CP2 can close:**

1. The mentor-session date and a short feedback summary in section 10 of this report (or a note that the session did not take place, with the reason).
2. One decision entry per piece of mentor feedback that changes or confirms scope (D-091 onward), or one entry recording that the feedback changes nothing.
3. LMS upload proof (screenshot or receipt path), or a note that the bootcamp did not require an upload for checkpoint 14.
4. The rehearsal timing if a rehearsal happened; otherwise mark step 4 as not done, with the reason.
5. The deck file path or a copy, if it should be kept with the project evidence.

