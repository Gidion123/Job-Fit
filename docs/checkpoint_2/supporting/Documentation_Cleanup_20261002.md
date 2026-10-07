# Documentation cleanup

**Date:** 2 October 2026  
**Scope:**Navigation, historical-document placement, duplicate private copies and Finder metadata. No code, config, runtime rule, gold, raw corpus or snapshot edit. Separately approved workbook corrections are recorded in the review report.

## Removed

- Two private intermediate audit copies identical by SHA256 to their retained canonical CSV/report.
- 13 `.DS_Store` Finder metadata files. These are unrelated to application execution or labeling.

## Archived

- Completed T01/T02 task prompts in `evals/annotation_tasks/archive/completed/`.
- Pilot-draft preparation report in `docs/checkpoint_2/supporting/archive/preparation/`.
- Original human review receipt archived unchanged; the active QA workbook has one concise name.
- Relative Markdown links updated for moved files; archive indexes identify their historical role.

## Kept for execution and provenance

Older guidelines/prompts remain because gold/results/tests refer to those exact definitions. The working development workbook remains an audit/preparation baseline, distinct from the submitted review receipt. Four identical working/snapshot data pairs remain because frozen reproduction and current processing require distinct paths. Unique caches, billing records, probe state, source files and snapshots are preserved. No claim is made that all repeated bytes are useless duplicates.

## Current entry points

- [Documentation index](../../Documentation_Index.md)
- [Evaluation index](../../../evals/README.md)
- [Reviewed labeling receipt](../../../evals/labeling/README.md)
- [QA result](Development_Labeling_Review_20261002.md)

Before-edit document backups and exact move/delete/hash inventory are local in `_private_not_for_github/notes/artifact_work/review_submission_20261002/`. Cleanup is reversible for archived/edited documents; deleted duplicate content remains in canonical files. QA did not grant human label approval or export gold.
