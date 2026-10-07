# CP3.5: Final Presentation and Portfolio

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 19. PPT Final Project / Portfolio · official date 9 Oct 2026  
**JobFit version of this checkpoint:** Same as the template.  
**Planned work:** 9 Oct 2026; moved to 10 Oct (D-100) · **Actual:** not run yet\
**Status:** PLANNED / NOT RUN · D-045 blind candidates selected by ID (7 Oct); planned work on 10 Oct · design basis: System Design v1.3

> This report is a plan. It contains no results yet. Results, scores, mentor feedback, and deployment evidence are added only after the work is actually done, with links to the [experiment log](../experiments.md) instead of copied numbers. The plan for all stages is in the [master plan](../master-plan.md).

## CP3 final plan for this stage (7 Oct 2026, D-095 to D-100)

**JobFit scope:** final evidence, D-045 results, privacy and latency reports, deck and video. Planned work moves to 10 October, after the feature freeze (D-100). Stage definition: [master plan](../master-plan.md#cp35-final-presentation-and-portfolio-checkpoint-19).

### D-045 test extraction and evidence: option B (PLANNED / NOT YET COMPLETED)

D-045 will be completed as originally written, using option B (D-100). It needs 2 blind test extraction JDs and 1 blind CV3 evidence pair, plus the model-draft portion.

**Phase 0 candidate selection (7 Oct 2026, read-only, no inference, no model output opened).** Eligible items are test-split, target-role jobs whose job ID appears nowhere in:
- the CP2.4 labeling workbooks (`evals/labeling/test_relevance_cp24_test_v1_v1/`, every sheet);
- the CP2.4 outputs (`evals/results/cp24/`, paths and contents);
- the test gold and pools;
- any other tracked file outside the split lists and processed data (this also excludes the CP2.1 baseline rankings).

Of 214 test jobs, 69 appear in the CP2.4 material and 20 more in other tracked files, which leaves **125 eligible unseen jobs**. Selection used seed 20261001 on metadata only (role family, language, experience bucket); no description or model output was read:

| Item | Job ID | Selection rule (T04/T06 variety) |
| --- | --- | --- |
| T1 (blind extraction) | **F00398** | AI/ML engineering, entry level, English (18 eligible) |
| T2 (blind extraction) | **F00237** | Indonesian-language JD, software/AI, 1-2 years (7 eligible) |
| Blind evidence pair | **CV3 × F00398** | CV3 (junior ML engineer) × T1, as D-045 specifies |

The stop condition did not trigger: 2 eligible JDs and 1 eligible CV3 pair were verified.

**Blind workflow (planned):**
1. Build a blind workbook with T1 and T2 and CV3 only, and empty A_Extraction and B_Evidence sheets. No drafts.
2. Dion labels T1 and T2 extraction, then CV3 × T1 evidence, records the time, and locks the file (SHA-256 recorded).
3. Only then run the frozen D-087 pipeline on these items: 2 extractions and 1 match, about US$0.10 inside the US$5 validation budget.
4. Align with human verification and score with the strict metrics (D-052, D-054).
5. Separately import, align and score the CP2.4 workbook's A_Extraction and B_Evidence rows as **MODEL-ASSISTED, HUMAN-REVIEWED** (never relabelled as blind).
6. Report the blind group and the model-assisted group separately. Test labels are never used for tuning (D-046 rule 4, D-089).

### Other planned CP3.5 content

- **Privacy report (D-092):** the CP3.4 gate results and the PR-10 matching-quality impact.
- **Latency and cost table** from the CP3.4 measurements.
- **Monitoring screenshots.**
- README, deck and a 2-4 minute video. Validated and planned items are kept clearly apart.

## 1. Goal of this stage

Build the final story from evidence: problem, data, experiments, final system, evaluation, deployment, limitations.

## 2. Inputs and prerequisites

- All earlier stage reports
- Playbook section 12 (presentation story)

## 3. Planned method

1. Final deck draft.
2. README update with CP2 and CP3 results.
3. Demo video (2-4 minutes).
4. Limitations and what was deliberately not built.

## 4. Planned outputs

- final deck draft in `05_Checkpoint_3/`
- updated README
- demo video
- this stage report

## 5. Acceptance criteria

- Every big claim has evidence or a metric.
- The deck is not full of jargon without a story.

## 6. Evidence to keep

- deck file
- README commit
- video link

## 7. Estimate and dependencies

- **Estimate:** About 1 working day.
- **Depends on:** Checkpoint 18 results.

## 8. Fallback if blocked

Use screenshots from checkpoint 18 if a live recording fails.

## 9. Checklist

- [ ] Final deck draft.
- [ ] README update with CP2 and CP3 results.
- [ ] Demo video (2-4 minutes).
- [ ] Limitations and what was deliberately not built.
- [ ] Acceptance: Every big claim has evidence or a metric.
- [ ] Acceptance: The deck is not full of jargon without a story.

## 10. Results

Not run yet.

## 11. Interpretation and limitations

Not run yet.

## 12. Decisions from this stage

None yet. Decisions are recorded in the [decision log](../decisions.md) when they are made.

## 13. Next step

CP3.6 (checkpoint 20): rehearsal and final fixes.
