# Evaluation assets

Current development ground truth is the versioned `gold/development_v13_reviewed_20261002_r2` bundle. Do not merge it by concatenation with historical pilot exports. Read the bundle manifest, held records and source-completeness limitations before evaluation. Current readiness is `results/cp23_reviewed_bundle_readiness_20261002.json`; no test evaluation or tuning has been performed.

| Path | Role |
| --- | --- |
| [labeling/README.md](labeling/README.md) | Current reviewed development workbook and follow-ups |
| [annotation_guideline_v1_3.md](annotation_guideline_v1_3.md) | Current manual and runtime guideline |
| `annotation_guideline_v1.md`, `annotation_guideline_v0.1.md` | Historical rule definitions required to interpret existing labels/results |
| `pilot/` | Original pilot workbook and audit provenance |
| `gold/` | Previously exported human-approved development labels; new submission not promoted yet |
| `silver/` | Unreviewed labels for exploration only |
| `splits/` | Frozen development/test membership; never regenerated during labeling cleanup |
| [annotation_tasks/README.md](annotation_tasks/README.md) | Current tasks and completed-task archive |
| `fixtures/` | Development acceptance cases; automated tests do not grant human sign-off |
| `results/` | Versioned experiment and audit evidence |

Current development QA:[review report](../docs/checkpoint_2/supporting/Development_Labeling_Review_20261002.md). Historical versions are retained for reproducibility. Identical files in a frozen snapshot and its working counterpart have different roles and are not removable duplicates.
