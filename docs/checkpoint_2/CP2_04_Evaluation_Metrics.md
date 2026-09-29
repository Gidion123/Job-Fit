# CP2.4: Evaluation Metrics

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 11. Modeling + Evaluation Metrics · official date 1 Oct 2026  
**JobFit version of this checkpoint:** The chosen configuration is measured on the held-out test set with the metrics of System Design v1.3 section 14.  
**Planned work:** 3 Oct 2026 · **Actual:** not run yet  
**Status:** PLANNED / NOT RUN · design basis: System Design v1.3

> This report is a plan. It contains no results yet. Results, scores, mentor feedback, and deployment evidence are added only after the work is actually done, with links to the [experiment log](../experiments.md) instead of copied numbers. The plan for all stages is in the [master plan](../master-plan.md).

## 1. Goal of this stage

Measure the chosen configuration on the held-out test set and report the metrics in the priority order of System Design v1.3 section 14.

## 2. Inputs and prerequisites

- Configuration chosen in checkpoint 10
- Test labels reviewed by Dion (gold)
- Evaluation scripts

## 3. Planned method

1. NDCG@10 and P@5 of the recommendation list, stage-1 order vs match-% order.
2. Evidence Macro-F1, precision and recall per class, confusion matrix, share of assessed units.
3. Extraction precision, recall, F1, and schema validity.
4. Filter recall and stage-1 Recall@K.
5. Safety: hard-negative false positives in the top 10, quote validity, unsupported claims.
6. Latency p50/p95 and cost per run, live and cached separately.
7. Save failure examples in docs/failures.md.

## 4. Planned outputs

- evaluation scripts
- evaluation report draft
- gold labels with the guideline version
- docs/failures.md entries
- this stage report

## 5. Acceptance criteria

- No "good" claim without a metric.
- Each result records the git SHA, prompt and model versions, cost, and latency.
- Only gold (reviewed) labels are used as ground truth.
- The limitations are written: single annotator, gold size, synthetic CVs, snapshot date.

## 6. Evidence to keep

- metric tables
- evaluation output files
- docs/failures.md
- ledger totals

## 7. Estimate and dependencies

- **Estimate:** About half a day, on 3 Oct together with checkpoints 12 and 13. LLM cost: under US$1.
- **Depends on:** Test labels complete and reviewed. This is the most important dependency of CP2.

## 8. Fallback if blocked

If the test labels are not complete, report on the reviewed subset with its size and say so. Provisional labels are never used as gold.

## 9. Checklist

- [ ] NDCG@10 and P@5 of the recommendation list, stage-1 order vs match-% order.
- [ ] Evidence Macro-F1, precision and recall per class, confusion matrix, share of assessed units.
- [ ] Extraction precision, recall, F1, and schema validity.
- [ ] Filter recall and stage-1 Recall@K.
- [ ] Safety: hard-negative false positives in the top 10, quote validity, unsupported claims.
- [ ] Latency p50/p95 and cost per run, live and cached separately.
- [ ] Save failure examples in docs/failures.md.
- [ ] Acceptance: No "good" claim without a metric.
- [ ] Acceptance: Each result records the git SHA, prompt and model versions, cost, and latency.
- [ ] Acceptance: Only gold (reviewed) labels are used as ground truth.
- [ ] Acceptance: The limitations are written: single annotator, gold size, synthetic CVs, snapshot date.

## 10. Results

Not run yet.

## 11. Interpretation and limitations

Not run yet.

## 12. Decisions from this stage

None yet. Decisions are recorded in the [decision log](../decisions.md) when they are made.

## 13. Next step

CP2.5 (checkpoint 12): turn the results into clear charts.
