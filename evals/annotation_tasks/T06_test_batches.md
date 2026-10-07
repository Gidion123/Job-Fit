# T06: Test batches (blind first)

Read first: D-045, D-046, D-052, D-053 and [evaluation contract section7](../../docs/evaluation.md#7-held-out-confirmation-protocol-d-053). Historical top12 and condensed-ranking instructions are superseded. Test labels never choose a model, prompt, weight, or K. No git commands, no API calls.

## Batch T-A. Test extraction and evidence (after configuration/protocol freeze)

This task remains closed during development tuning. Preserve the four-JD/three-pair plan and blind versus draft-assisted provenance.

1. Pick 4 test JDs from `evals/splits/test_job_ids.txt` with the same variety rules as T04 (Indonesian JD, entry or junior, GenAI/LLM, senior or many unknown fields). Call them T1 to T4.
2. Create `evals/labeling/test_batch_blind.xlsx` with T1 and T2 only, CV3, and empty A_Extraction and B_Evidence sheets. **No drafts in this file.** Dion labels T1 and T2 extraction, then CV3 x T1 evidence, and records the time.
3. Only after Dion says the blind file is finished: freeze a JSON snapshot of his rows in `evals/pilot/audit/` style (`evals/labeling/audit/test_blind_snapshot_<date>.json`), then run the QA check (quotes exact, fields complete, guideline rules). Findings go to QA_Log as proposals. Do not change his labels.
4. Then create `evals/labeling/test_batch_drafted.xlsx` with T3 and T4: extraction drafts, and after Dion approves them, evidence drafts for CV1 x T3 and CV2 x T4. These rows keep `label_source = model_draft`.

## Batch T-B. Test relevance (only after CP2.3 has frozen the configuration)

1. Use only separately authorized frozen-run outputs: for CV1/CV2/CV3 initially, and CV4/CV5 in the planned expansion, form the union of original top10 stage-1 and top10 final recommendations inside the same test universe/filters. Deduplicate by (cv_id, job_id). Preserve separate ranking/provenance artifacts. Report exact counts and review effort before creating workbooks; agree practical batches within2–3 hours/day. Save the resulting `evals/pools/test_pool.csv` with configuration/protocol/run IDs and source hashes only when preparation is authorized. Do not rerun candidates, call APIs, change K, or relabel to improve test outcomes.
2. Create `evals/labeling/test_batch_relevance.xlsx`: JDs, CVs, C_Relevance with empty `relevance_0_3`, rows shuffled (seed `20261001`), no rank, no score, no method identity, no draft. Keep the provenance manifest outside the blind workbook.
3. After Dion finishes: snapshot his labels, then QA check for missing fields and constraint notes that disagree with D-042. Proposals only.

## Metric coverage

Use original-position P@5/NDCG@10 only when required judgments are complete. No condensed ranking. Compare both orders on a common eligible judged pool and paired CV subset. Report familiar-profile CV1/CV2 separately from held-out-profile CV3–CV5. Recall is labeled-pool diagnostic; filter recall is not measured without pre-filter judgments. Missing labels/failed outputs stay explicit. See D-053.

## Export

Approved rows go to `evals/gold/` with split `test`. Blind rows have `label_source = annotator`; drafted rows `model_draft`. Report the two groups separately.
