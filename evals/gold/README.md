# Gold Labels

Labels approved by the annotator, used as ground truth (D-016, D-038). Only rows with `review_status = approved` are written here. Rejected rows are left out.

| File | One record per | Main fields |
| --- | --- | --- |
| `extraction_gold.jsonl` | Requirement unit of a JD | `job_id`, `unit_no`, `unit_text`, `source_quote`, `importance`, `category`, `group_id`, `min_years` |
| `evidence_gold.jsonl` | Requirement unit x CV | `cv_id`, `job_id`, `unit_no`, `label`, `check_status`, `cv_quote`, `cv_section` |
| `relevance_gold.csv` | CV x job | `cv_id`, `job_id`, `relevance` (0 to 3) |

Every record also has `split`, `snapshot_id`, `label_source`, `review_action`, and `guideline_version`.

## Current content

| Split | Source | Extraction | Evidence | Relevance | Exported |
| --- | --- | --- | --- | --- | --- |
| development | Pilot workbook `evals/pilot/JobFit_Pilot_Labeling_v0.1.xlsx` | 71 units, 4 JDs (J1 to J4) | 34 rows, CV1 x J1 and CV2 x J2 | 10 labels, CV1 and CV2 x J1 to J5 | 1 Oct 2026 |
| test | Not labeled yet (D-043) | | | | |

Rebuild the development rows with `python scripts/export_pilot_gold.py`. The script stops if any row in the workbook is still pending, and it checks that every quote exists in the JD or CV text.

Each row keeps the guideline version it was labeled with (`v0.1` to `v1.2`). The rules added in v1.1 and v1.2 were checked against the pilot rows when they were decided (D-041, D-042); rows that did not change keep their old version number.
