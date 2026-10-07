# Review Guide (annotator)

Short checklist for every batch. Rules: [guideline v1.3](../annotation_guideline_v1_3.md). Process: annotation-workflow.md.

## Before you start

- Close the workbook in other apps. Write the start time in Timing.
- Read the JD (and the CV) once from start to end before looking at the rows.

## Extraction (sheet A)

- Is every requirement in the requirement sections extracted, and nothing from responsibilities or benefits?
- Is each unit independently assessable without losing qualifiers? Keep alternatives in one OR group and split explicitly cumulative AND requirements. Apply D-039/D-040 to examples and lists; do not decide from a conjunction alone.
- Importance: explicit Required stays required; explicit preference gives preferred; genuinely contradictory signals follow D-042/D-049.
- Category: soft skill, location, and work authorization are separate (D-032, D-033).

## Evidence (sheet B)

- MATCH needs use with context; skills list only is PARTIAL (D-035).
- Work-experience minimums count only employment in the same field (D-042).
- The CV quote supports the label, not only the keyword.

## Relevance (sheet C)

- Judge in automatic mode: the four target role families (D-037).
- An explicit conflict caps the label at 1.
- Write a short `main_reason`.

## For every row

| You did | review_action | review_status |
| --- | --- | --- |
| Kept the draft as it is | accepted | approved |
| Changed anything (text, split, importance, label) | edited, with a `review_note` | approved |
| Draft is wrong and should not be used | rejected, with a `review_note` | approved |
| Added a missing row | added (`label_source = annotator`) | approved |
| Not sure yet | leave it pending, write the question in Questions | pending |

Blind test batches: fill the labels yourself; there is no draft to accept.

## When you finish

Write the end time in Timing. Rows still pending are never used. If you accepted almost everything, spot-check 5 random rows again.

## Active combined workbook (2 October 2026)

Open the current receipt listed in [labeling README](../labeling/README.md). Review A first, then linked B and C. Start with A D1/D2/D3, B CV1×D1 and CV2×D2, and C `gold_review = yes` (40 rows). Full-pool drafts are available but optional. Set `review_action` to accepted, edited, rejected, or added and `review_status` to approved only for rows you have decided. Explain edits/rejections in review_note; unresolved rows stay pending. Record Timing, save, and close Excel before requesting edits. A changes require rechecking dependent B and affected C. Existing approved pilot rows are historical and need not be approved again.


All rows were submitted as reviewed on2October2026. Follow the small QA list in the review report; the original full review instructions above are retained for subsequent batches, not a request to repeat completed review.
