# CP2.7: CP2 Presentation and Mentoring

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers
**Bootcamp checkpoint:** 14. PPT Check Point 2 + Mentoring · official date 4 Oct 2026
**JobFit version of this checkpoint:** Same as the template: CP2 presentation and mentoring.
**Planned work:** 3 to 4 Oct 2026 · **Actual:** deck, figures and one-page summary prepared on 4 Oct; presented and mentored on 4 Oct 2026; feedback written up on 7 Oct (D-093)
**Status:** DONE · design basis: System Design v1.3 and measured CP2 development results

> The plan for all stages is in the [master plan](../master-plan.md). Sections 1 to 8 are the plan; sections 9 to 13 are what happened.

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
6. Upload the deck to the LMS (Dion). This is a bootcamp task handled outside the repository and is not tracked here.

## 4. Planned outputs

- CP2 deck in `04_Checkpoint_2/`
- mentor feedback summary
- this stage report

## 5. Acceptance criteria

- The mentor sees a measurable selection, tuning, and evaluation process.
- The mentor's feedback is recorded in docs/decisions.md as new entries.

## 6. Evidence to keep

- deck file
- feedback notes

## 7. Estimate and dependencies

- **Estimate:** About half a day for the deck, plus the session.
- **Depends on:** Checkpoints 11 to 13.

## 8. Fallback if blocked

If a result is not ready, present the method and what is missing, with the reason.

## 9. Checklist

- [x] Build the deck following Playbook section 6 (12 slides, v3, 4 Oct).
- [x] Include the CV-first flow with optional filters as a proposal, and the reason import link is out of v1.
- [x] Show real metrics, failures, and limitations; missing results are shown as missing, not estimated. The deck used development results only, because CP2.4 had not run yet; the fallback allows this.
- [ ] Rehearse once with timing. I did not record a timed rehearsal. This is a method step, not an acceptance criterion.
- [x] Present, then write down the mentor's feedback (presented 4 Oct; feedback in section 10).
- [x] Acceptance: The mentor sees a measurable selection, tuning, and evaluation process.
- [x] Acceptance: The mentor's feedback is recorded in docs/decisions.md as new entries ([D-093](../decisions.md)).

## 10. Results

**Deck.** The 12-slide deck `JobFit_CP2_Presentation_20261004_v3.pptx` (v2 kept) is in the project folder `04_Checkpoint_2/`, outside this repository, as planned. It uses six development figures from [CP2.5](CP2_05_Evaluation_Visualization.md), editable charts, speaker notes for a 15-minute talk, and two diagrams (the CV-first flow and the privacy boundary). It kept the finished CP2.1-CP2.2 work apart from the provisional CP2.3 results and the CP2.4 test, which had not run yet. A [one-page summary](supporting/CP2_Presentation_Summary_20261004.md) of the content is in the repository.

**Session.** I presented on 4 October 2026, probably in the early afternoon WIB. I did not write down the exact time or the attendees, but two files from that day date it:
- the D-069 amendment (`evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1/cap_and_deadline_amendment_v2.json`) notes at 08:13 WIB that the presentation was about six hours away;
- the [4 October audit report](supporting/CP23_Audit_Fixes_20261004.md) starts with "After the CP2 presentation".

**Mentor feedback.** The original Indonesian wording is in [D-093](../decisions.md).

| # | Feedback | What I do with it |
| --- | --- | --- |
| 1 | LLM latency is high, about 95 seconds. | Noted. The deck showed a DeepSeek Flash matching request p95 of about 91 s (D-068); 95 s is the mentor's figure. |
| 2 | Add a waiting state, like a progress or "thinking" animation, so the user knows the system is still working and does not get bored. | CP3 (D-093 A). The CP3 UI already has a per-job progress bar and a spinner, so I will check those against this feedback first. This improves the wait; it does not make the model faster. |
| 3 | Once the core features work, add CV improvement suggestions for the target vacancy so the user can raise the match. | CP3, after the core flow is stable (D-093 B). This extends the CV coach plan (D-036) and CV coach v1. Suggestions must come from the real CV, the JD requirements and the gaps found; they never invent experience and do not promise a better real fit. |

Both points are CP3 work. They do not change the D-087 freeze, the CP2.4 result or any CP2 setting.

## 11. Interpretation and limitations

- The deck showed the development state on 4 October. Some of its choices (DeepSeek matching, K = 20) were replaced later (D-083, D-086, D-087). That is expected, since the plan allowed presenting work in progress.
- There are no minutes, recording or attendee list, only the two dated traces above and my own record of the feedback.
- The 95-second figure describes the system as presented on 4 October, not the frozen configuration measured in CP2.4.

## 12. Decisions from this stage

- [D-093](../decisions.md): mentor feedback recorded and taken into CP3 (waiting-state UX; vacancy-specific CV guidance).

## 13. Next step

CP3.1 uses this feedback as its checkpoint-14 input (see the master plan). The full CP3 handoff is in the [CP2 closeout audit](CP2_Closeout_Audit_20261007.md#11-what-cp3-inherits). CP2 was closed by [D-094](../decisions.md).

**History.** Until 7 October this report said the mentor session was not recorded, and the master plan said "presented and mentored 4-5 Oct; mentor notes to be added" without a source. The first closeout pass therefore treated CP2.7 as open. It was closed once I confirmed the session and wrote up the feedback (D-093), and the two dated traces above were found.
