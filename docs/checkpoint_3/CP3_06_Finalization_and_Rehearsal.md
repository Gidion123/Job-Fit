# CP3.6: Finalization and Rehearsal

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 20. Finalisasi Portfolio & Rehearsal Presentation · official date 10 Oct 2026  
**JobFit version of this checkpoint:** Same as the template.  
**Planned work:** 10 Oct 2026 · **Actual:** not run yet  
**Status:** PLANNED / NOT RUN · design basis: System Design v1.3

> This report is a plan. It contains no results yet. Results, scores, mentor feedback, and deployment evidence are added only after the work is actually done, with links to the [experiment log](../experiments.md) instead of copied numbers. The plan for all stages is in the [master plan](../master-plan.md).

## CP3 final plan for this stage (7 Oct 2026, D-095 to D-100)

**JobFit scope:** regression, rehearsal and release tag. PLANNED.
- **Regression:** the final validation table in the [CP3 execution plan](CP3_Execution_Plan.md) and the [master plan](../master-plan.md#cp36-finalization-and-rehearsal-checkpoint-20):
  - offline and database-gated pytest; ruff; freeze verify; both Docker builds; prod compose config;
  - Alembic; restore;
  - validation layers A (external public) and B (internal API);
  - the canary scan; phase bounds within the cap; sync idempotency only if the post-beta sync exists;
  - green GitHub Actions.
- **Rehearsal:** includes the owner-token step for a shared presentation network.
- **After review:** Dion merges the CP3 work into `main` (D-095).

## 1. Goal of this stage

Reduce the risk of the demo or the presentation failing.

## 2. Inputs and prerequisites

- Checkpoint 19 outputs

## 3. Planned method

1. Full regression run.
2. Rehearse with timing; prepare backup screenshots and video.
3. Proofread the README and the documents.
4. Release candidate tag (Dion runs git).
5. Upload the deck to the LMS (Dion). This is a bootcamp task handled outside the repository and is not tracked here.

## 4. Planned outputs

- final deck
- release candidate
- rehearsal notes
- this stage report

## 5. Acceptance criteria

- No new features.
- The live app, the backup demo, and the metrics are consistent.

## 6. Evidence to keep

- regression output
- tag link

## 7. Estimate and dependencies

- **Estimate:** About half a day plus rehearsal.
- **Depends on:** Checkpoint 19.

## 8. Fallback if blocked

If a bug appears, fix only if it is critical; otherwise note it as a known issue.

## 9. Checklist

- [ ] Full regression run.
- [ ] Rehearse with timing; prepare backup screenshots and video.
- [ ] Proofread the README and the documents.
- [ ] Release candidate tag (Dion runs git).
- [ ] Acceptance: No new features.
- [ ] Acceptance: The live app, the backup demo, and the metrics are consistent.

## 10. Results

Not run yet.

## 11. Interpretation and limitations

Not run yet.

## 12. Decisions from this stage

None yet. Decisions are recorded in the [decision log](../decisions.md) when they are made.

## 13. Next step

CP3.7 (checkpoint 21): final presentation and submission.
