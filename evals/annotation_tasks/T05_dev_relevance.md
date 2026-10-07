# T05: Development relevance drafts and human review

Read guideline v1.2 Part D and D-037, D-042, D-044 to D-048. Use `evals/labeling/JobFit_Development_Labeling_v0.1.xlsx`, sheet C_Relevance. All development rows are drafted first under D-047/D-048. Held-out test remains blind-first.

## Current scope

The frozen pool contains 63 pairs: 3 already approved pilot judgments and 60 pending drafts. The combined book preserves all of these and adds 4 optional pairs for the selected extraction JDs, giving 67 judgments total. All added labels are pending. CV1/CV2 only. Original ordering and review selection are retained; no retrieval ranks or scores are shown.

## Review and export

- Filter `gold_review = yes`: 40 designated new reviews, 20 per CV, remain the D-045 priority. Other pairs may be reviewed individually.
- Review label 0–3, main_reason and constraint_note under the evidence-based rubric. Relevance is not an arithmetic match-percent calculation.
- If A or B changes materially, recheck affected C judgments before export.
- Approved rows can later be exported to development gold. Never-reviewed rows remain silver, and pending designated review rows block the planned batch export. No export has occurred in this preparation.
- Test data or results never choose models, prompts, weights or K. Do not regenerate the frozen pool or active review workbook.
