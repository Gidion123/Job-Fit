# T04: Complete development extraction and evidence drafts

Read guideline v1.2, `docs/annotation-workflow.md`, D-032 to D-048, and the pilot workbook as the template. No git commands, API calls, or new annotation-rule decisions.

## Current state

Use `evals/labeling/JobFit_Development_Labeling_v0.1.xlsx`. Under Dion's D-048 instruction, A/B/C are complete across the frozen development pool and explicitly retained optional pairs. A contains 1,069 units for 54 JDs; B contains 1,387 rows across 67 CV1/CV2 pairs (one pair has no qualification units). Previously approved rows remain unchanged. All new rows are pending drafts.

## Review order

1. Prioritize A for D1/F00103 (Indonesian JD), D2/F00074 (GenAI), D3/F00012 (senior/conditional). This is still the D-045 three-JD review target.
2. Then prioritize B for CV1×D1 and CV2×D2, still the D-045 two-pair target.
3. Additional full-pool rows are optional reviews. Draft availability never approves a label or increases mandatory gold size.

## Dependencies and rules

- Dion authorized B drafts before all A rows are approved. The former stop before B preparation is superseded. A edits require dependent B rows and affected C judgments to be checked again before export.
- Preserve JDs, CVs and already approved rows. Use neutral role names in administrative notes, but keep all source tool/skill names and verbatim quotes intact.
- F00364 has no qualifications: do not invent A/B units from responsibilities. F00369 has a truncated clause: do not reconstruct missing text.
- One editor at a time. Never set new rows to approved, overwrite reviewed work, or export pending rows as gold. CV3–CV5 and test JDs remain excluded.
- `scripts/validate_development_review.py` checks the initial preparation snapshot. After human edits, use review-aware QA; do not reset annotations to pass initial-snapshot assertions.
