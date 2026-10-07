# CP2.2 pipeline implementation and live development checks

**Date:** 2 October 2026. **Status:** backend implemented and checked; CP2.2 remains IN PROGRESS. Expanded annotation review, extraction quality validation and corpus extraction are not complete.

## 1. Purpose and boundaries

Continue the interrupted implementation until a synthetic CV upload and pasted JD produce a source-checkable report. This work uses CV1 and pilot J1/F00022, both development data. It does not tune retrieval, use held-out CVs/JDs, approve annotations or change the scoring/annotation contract.

The active labeling workbook was read-only throughout this continuation. Its saved SHA-256 still matches the released correction snapshot: `7a1321180ae7785d3ab018b9317acf76f97769404e06375ad8370753cc195bc1`. All 63 previously approved rows remain protected. Human edits after this check are legitimate; never restore this snapshot to erase review.

## 2. Implemented behavior

| Component | Actual behavior and boundary |
| --- | --- |
| Upload text | PDF, DOCX, UTF-8 TXT and Markdown; in-memory processing. CV1 one/two-column PDF fixtures retain the source content. Image-only PDF returns a clear unsupported/OCR message without a model call. Complex PDF layouts still require preview |
| CV parser | Structured sections, evidence, employment and source-date strings. Exact quote/section validation; one repair maximum. Summary requires confirmation before comparison. Real-CV provider processing remains disabled pending consent |
| Dates | Configured 30 September 2026 reference date; year/month precision preserved, no invented day. Inclusive calendar months, overlap removed. Year-only dates remain unknown |
| Experience | Reviewed scope links can establish relevant duration. Confirmed whole employment provides only an upper bound for a shortfall, not proof of every technology's tenure |
| JD extraction | Versioned prompt, Pydantic, exact source quotes, identities and provenance. A populated explicit requirement section cannot silently become an empty successful extraction. Responsibilities-only sources may legitimately have zero units |
| Evidence matching | Complete unit/branch coverage, exact CV quotes, existing MATCH/PARTIAL/NO_MATCH rules. Processing failure is not NO_MATCH. Unresolved required units hold the score |
| Paste path | Cleaning, preview/quality warnings, extraction, matching, score and separate constraints. Paste/CV state remains session-memory only |
| Cache | Public corpus JD cache may persist; keys include content, prompt, schema, model/config, preprocessing, guideline, identity and output cap. CV/paste cache does not persist |
| API controls | No hidden SDK retries; at most one validation repair per stage; privacy routing, model allowlist, price ceilings, locked ledger and hard stop. SDK timeout is an inactivity timeout, not a guaranteed total wall-clock deadline |
| Scripts | `run_cp22_example.py` saves explicitly synthetic diagnostics; it can reuse a verified CV1 parse with identical source/PDF hashes. `run_batch_extraction.py` defaults to preflight, restricts IDs to frozen development and resumes successful versioned cache entries |

PyMuPDF and python-docx are in `requirements.txt`. Installed versions checked during the handoff: PyMuPDF 1.28.2 and python-docx 1.2.0. No OCR dependency or new UI/API was added.

## 3. Verification

Final command: `JOBFIT_DB_TESTS=1 env-job-fit/bin/python -m pytest -q`.

**161 passed, 0 skipped, 8.63 seconds.** Five warnings come from PyMuPDF SWIG deprecations. This includes local PostgreSQL/pgvector checks. Frozen development/test ID hashes remain unchanged.

Coverage includes PDF reading order/content, image-only failure, dates, quote rejection, section membership, one repair, schema invariants, cache isolation, failure-to-score behavior, OR coverage, budget accounting, response-model validation and the eight existing development fixtures. The eight fixtures pass automated checks; this does not substitute for the planned human acceptance check or estimate LLM accuracy.

Machine-readable evidence: [`cp22_pipeline_verification_20261002.json`](../../../evals/results/cp22_pipeline_verification_20261002.json). Its code hashes describe the final verified implementation, not every earlier intermediate run.

## 4. Real model checks, including failures

All runs use the registered `deepseek-flash` baseline through OpenRouter, not a model selected by CP2.3. Every billed attempt remains in the ledger.

| Run suffix, 2 October | Calls | Result | Cost US$ |
| --- | ---: | --- | ---: |
| `_01` | 4 | CV parse recovered; JD responses reached the 6,000-token cap and failed validation | 0.025907734 |
| `_02` | 2 | Low reasoning alone did not prevent CV response truncation | 0.014689476 |
| `_03` | 2 | 16,000-token output allowance; structured CV response still failed section/source validation | 0.023914152 |
| `_04` | 6 | Full live pipeline completed; 17 extracted units; score held because required units were unresolved | 0.059793906 |
| `_05` | 1 | Reused valid CV parse; JD model returned zero units despite clear qualifications. Historical result is retained as a failed quality case, not a successful extraction claim | 0.011907300 |
| `_06` | 2 | Reused valid CV parse; 21 units and matching completed on first attempts; provisional report | 0.023168232 |

Artifacts: `evals/results/cp22_live_cv1_j1_20261002_01.json` through `_06.json`. The complete live upload-to-report run is `_04`; `_06` reuses its validated synthetic CV parse, with identical original/PDF hashes. Automated fixture confirmation is explicitly marked `human_confirmation=false` and grants no annotation approval.

Operational fixes: increased output allowance from 6,000 to 16,000; explicitly requested supported low reasoning; repair receives a bounded previous structured response plus safe validation codes/field paths. Raw exceptions or document instructions are never promoted to system instructions. A typed response can pass SDK/Pydantic validation and still fail stage source checks: ledger `ok` is not a semantic-quality metric.

Prompt v1 is preserved. JD prompt **v1.1** fixes the overly broad unresolved-and/or instruction: approved D-041 and explicit AND splitting take precedence. It also spells out existing cross-field schema invariants. Annotation rules, gold labels and denominator code are unchanged. This is an implementation correction using development evidence, not a held-out improvement or a formal model benchmark.

## 5. Interpretation of the latest example

The latest raw model report gives **91.67%, provisional**, from `(5 MATCH + 0.5 × 1 PARTIAL) / 6 required units`. Experience and location constraints are UNKNOWN. This is evidence coverage over the model's extracted requirements, not a probability of being hired.

**It is not equivalent to the approved pilot result.** Pilot score v1 is 92.86% over seven required technical units. The following differences remain:

- The model treats the structured/unstructured-data requirement as unknown and unresolved; the approved pilot treats it as one required alternative group. This changes the denominator.
- Data architecture and data engineering remain combined and unresolved in the model extraction; the approved pilot splits them.
- Willingness to learn and learning independently are separated in the model output, whereas the pilot combines that scoped requirement. Equal total counts of 21 units do not imply semantic agreement.
- Several soft-skill judgments differ. They remain outside the main percentage. Exact matching quotes alone do not prove that a label is correct.

These discrepancies are development error-analysis items for CP2.3 after priority labels/rules are settled. No Macro-F1, extraction F1, ranking metric, calibration claim or human approval is inferred from this example. In particular, unresolved structural requirements can affect the provisional denominator; the percentage must not be promoted as a verified recommendation result. See the [readable example](CP22_Synthetic_Example_20261002.md).

## 6. Costs and batch status

- This continuation: **17 inference calls, US$0.15938080**.
- Entire project ledger: **US$0.17164902**, including earlier embedding work/diagnostics.
- Configured hard stop remains **US$8.50**. No budget change, top-up or subscription action occurred.
- Full development extraction is **not run**: 214 pending JDs, zero populated extraction-cache entries at preflight. The 214 held-out JDs remain deferred until configuration freeze; existing embedding vectors do not grant permission to inspect their extraction outputs for development.
- Latest batch preflight: **US$13.8128838 conservative upper bound**, assuming maximum output and repair/context allowance for every item. This is not an expected bill. It exceeds both the US$1 batch authorization threshold and the current hard stop, so the batch must not execute as configured. Earlier US$0.25–0.50 planning estimates are not validated by this live work.

Do not raise the guard or silently divide this batch to bypass approval. First resolve extraction quality, then propose a bounded staged run with an explicit overall spend ceiling and user approval. Preflight: [`cp22_development_batch_preflight_v3_20261002.json`](../../../evals/results/cp22_development_batch_preflight_v3_20261002.json).

## 7. Next steps

1. Dion reviews the released workbook: A D1/D2/D3, B CV1×D1 and CV2×D2, then the 40 C rows with `gold_review=yes`. Other drafts are optional. Do not write the active workbook during this review.
2. Reconcile dependent B/C rows after A edits and export only individually approved rows when authorized. No such export happened here.
3. Use approved development gold to assess extraction/matching, refine the prompt and compare models under CP2.3. Preserve these implementation failure cases and untouched test data.
4. Agree a feasible batch budget/scope after quality checks; keep per-job done/failed/deferred status. Human fixture acceptance and the planned initial pilot J4 extraction-quality measurement still need evidence.
5. Freeze the selected configuration before test labeling/evaluation. CP3 API, UI, TTL/session deletion and production wall-clock cancellation are separate work.

References: [OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs), [reasoning token controls](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens), [baseline model](https://openrouter.ai/deepseek/deepseek-v4.1-flash), [PyMuPDF text extraction](https://pymupdf.readthedocs.io/en/latest/recipes-text.html).

## Later offline audit continuation (2 October 2026)

The preceding live-run and database evidence is preserved. A subsequent account-continuation audit verified its code hashes, fixed clear cache/duration/budget/heading and legacy-exporter risks, and prepared alignment and review-export staging tools without paid calls or workbook writes. See [new audit](CP22_Pipeline_Audit_20261002.md) and [complete pending alignment](CP22_Pilot_Alignment_Review_20261002.md).

New selected offline tests:164 passed,0 skipped,five SWIG warnings; this is not a repeat of the earlier database suite. New audit cost US$0, ledger unchanged at US$0.171649020. The active workbook and actual gold were untouched. No prompt/model selection, semantic approval, full batch, or CP2.2 completion is inferred.
