# Prompt versions and experiment provenance

Every prompt used by an experiment is retained. Dion reaffirmed this requirement on 3 October 2026. Once a prompt has been used, changes receive a new versioned file; earlier content and run results remain available. A newer experimental file does not become the runtime default automatically.

## Current inventory

| Task | Version / file | Purpose and status |
|---|---|---|
| CV parsing | [v1](cv_parsing_v1.md) | Existing parsing prompt; synthetic development inputs only during current evaluation. |
| JD extraction | [v1](jd_extraction_v1.md) | Historical initial extraction instructions. |
| JD extraction | [v1.1](jd_extraction_v1_1.md) | Historical schema/precedent clarification. Contains the former D-041 precedent; preserve for reproduction, not current annotation guidance. |
| JD extraction | [v1.2](jd_extraction_v1_2.md) | Historical configured verification baseline under guideline v1.3 / D-049. |
| JD extraction | [v1.3](jd_extraction_v1_3.md) | Experimental complete-source inventory and coverage contract; retained failed development observations. |
| JD extraction | [v1.4 experimental](jd_extraction_v1_4_experimental.md) | Explicit coordination audit and generic AND/OR examples. Used for Stage-2 comparison and selected provisionally under D-068. The legacy runtime config is not yet migrated. |
| Evidence matching | [v1](evidence_matching_v1.md) | Historical initial evidence rubric. |
| Evidence matching | [v1.1](evidence_matching_v1_1.md) | Provisional matching prompt and fixed-input Stage-2 experiment rubric. |
| Evidence matching | [v1.2-qa-e01](evidence_matching_v1_2_qa_e01.md) | Phase A challenger QA-E01 (QA-H01). Not eligible (D-090). Not a runtime default. Metadata in the `.meta.json` file. |
| Evidence matching | [v1.2-qa-e02](evidence_matching_v1_2_qa_e02.md) | Phase A challenger QA-E02 (QA-H02). Precision/recall trade-off, not eligible (D-090); basis for future QA-H04. Not a runtime default. |
| Evidence matching | [v1.2-qa-e03](evidence_matching_v1_2_qa_e03.md) | Phase A challenger QA-E03 (QA-H03). Never run (adaptive stopping, D-090). Not a runtime default. |

The legacy runtime default is read from [pipeline configuration](../config/pipeline_v1.yaml). The [D-068 provisional development version](../config/versions/pipeline_cp23_provisional_20261004.yaml) is passed explicitly to the end-to-end check. Keeping the legacy file unchanged preserves frozen experiment hashes. CP3 promotion needs a new versioned migration and regression check. Planned supporting prompts are not evidence of a completed experiment.

## Required record for each experiment

Retain the prompt file and SHA-256, the actual guideline file/version/hash appended to it, schema and preprocessing versions, model/request settings, source/split hashes, run ID, approval scope, outcome, failures and measured cost. Record why a new version was created and which predecessor it changes in [experiments](../docs/experiments.md). An experiment report must distinguish a proposal, a request actually sent, a process-valid result and a semantically reviewed result.

The [dated inventory](../evals/results/cp23_prompt_version_inventory_20261003_v1.json) preserves prompt hashes/content and the request-repair implementation snapshots at this checkpoint. Frozen run plans bind the applicable versions; the inventory is not an approval to rerun them. Future changes create a new inventory version instead of overwriting this one.

## Repair framing is versioned separately

The initial matching/extraction rubric is unchanged in D-064. The experimental [portable repair adapter](../src/jobfit/eval/portable_repair.py) moves only the application-owned repair instruction into the initial system message, preserving source/model content in its original data roles. This is a request-format experiment, not a new matching rubric or proof of the historical HTTP 400 root cause. Its code hash, the structured-call template hash and the frozen D-064 plan are retained in the inventory. The GPT Sol omission of unsupported temperature is a separate documented request setting.

A future rubric change, repair-format change or schema change must be identified separately so a measured gain is not incorrectly attributed to the model alone. Old failed requests and their costs remain part of their original experiment.
