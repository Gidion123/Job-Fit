# Development labeling

## Active workbook

For Microsoft Excel, open [JobFit_Development_Labeling_v1.3_Excel_compatible.xlsx](JobFit_Development_Labeling_v1.3_Excel_compatible.xlsx). Dion confirmed that the first compatibility repair opened without the recovery warning on 4 October 2026. The current copy also freezes only the JDs header, so its tall JD rows can be scrolled. It contains the same reviewed cells, styles, formulas, tables and data validations as the canonical [JobFit_Development_Labeling_v1.3.xlsx](JobFit_Development_Labeling_v1.3.xlsx). The copy restores missing namespace declarations in six OOXML parts and changes only the JDs view metadata. The canonical file remains byte-for-byte unchanged because existing gold manifests and experiment receipts record its SHA256. See the [repair receipt](../results/development_labeling_excel_compatibility_20261004.json).

Dion submitted full A/B/C review on 2 October 2026. The canonical v1.3 version incorporates the two QA corrections explicitly approved in chat. If a label is edited in the Excel copy later, reconcile it through the labeling workflow before updating gold; the two files will no longer be equivalent.

The CVs sheet intentionally contains only CV1 and CV2. CV3 through CV5 are reserved for held-out testing under D-046 and must not be added to the development labeling workbook.

| Sheet | Total rows | Approved | Pending | Rejected |
| --- | ---: | ---: | ---: | ---: |
| A_Extraction | 1,079 | 1,079 | 0 | 10 |
| B_Evidence | 1,406 | 1,404 | 2 | 16 |
| C_Relevance | 67 | 66 | 1 | 0 |

Approved rejected rows are retained as decision history and excluded from gold. Remaining actions: seven missing edit reasons, two cloud/AWS evidence rows, one related relevance pair, F00369 source resolution, and historical OR-group compatibility. See [review result](../../docs/checkpoint_2/supporting/Development_Labeling_Review_20261002.md) and [row follow-ups](../results/development_review_followups_20261002.csv).

## Retained history

| Location | Purpose |
| --- | --- |
| [Original submitted receipt](archive/review_receipts_20261002/JobFit_Development_Labeling_v0.1_A_B_C_review_v1.3_20261002.xlsx) | Unchanged human review submission before the two approved QA corrections |
| `JobFit_Development_Labeling_v0.1.xlsx` | Historical preparation/audit baseline required by existing safeguards; not the active review |
| `archive/pre_combined_20261002/` | Two earlier draft batches |
| `drafts/` | Frozen preparation manifest, scope and fingerprints |
| `sources/` | Source reference texts; F00369 supplement remains unverified |

Current guideline: [v1.3](../annotation_guideline_v1_3.md). Gold export is a separate validated operation. Multi-row OR branches must remain one logical alternative group where applicable. Historical label versions retain their provenance. Do not rerun preparation scripts to replace reviewed decisions.
