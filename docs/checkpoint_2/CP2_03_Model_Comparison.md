# CP2.3 Model Comparison

**Date:** 4 October 2026. **Status:** development choice recorded in D-068; end-to-end check and held-out confirmation are separate gates. This is the main CP2.3 comparison report. All quality numbers here use development data.

## 1. Question and setup

JobFit must find suitable jobs for a CV and explain each requirement match. We compared candidate retrieval, JD extraction, and CV evidence matching separately. Retrieval used 214 locked development jobs and two synthetic CVs. The extraction reference contained seven reviewed JDs and 120 logical requirements. The evidence reference contained four fixed CV/JD pairs and 73 requirements. One annotator reviewed model-assisted labels. The 214 test jobs and CV3 through CV5 were not used to choose settings.

The selection rules are [D-029 as amended for v1 by D-066](../decisions.md), the pre-registered embedding rule [D-044](../decisions.md), and the original-position metric contract [D-052](../decisions.md). Extraction F1 uses strict split and merge accounting under D-054. Evidence Macro-F1 counts invalid or unassessed requirements as false negatives in their gold class. Development labels are small and assisted, so the results are not a population accuracy estimate.

## 2. Embedding comparison

| Embedding | Dimensions | Dense Recall@20 | Hybrid Recall@20 | Input price per million tokens |
| --- | ---: | ---: | ---: | ---: |
| OpenAI text-embedding-3-small | 1,536 | 0.213 | 0.472 | US$0.02 |
| Qwen3-Embedding-8B | 4,096 | 0.420 | 0.549 | US$0.01 |

Qwen exceeds OpenAI by 0.206 in dense and 0.077 in hybrid Recall@20. Both exceed D-044's 0.05 threshold, so **Qwen is selected for the development configuration**. Prices are the configured endpoint ceilings, not measured operating bills. The observed embedding comparison covers only two CV queries. See the [retrieval result](../../evals/results/cp23_stage3_retrieval_evaluation_20261003_v2.json) and [D-044 result](../../evals/results/cp23_embedding_D044_selection_20261004_v1.json).

## 3. Stage-1 retrieval comparison

All six methods used the same 214-job development universe, original positions, and judged eligible pool. P@5 and NDCG@10 have complete top-cutoff judgments. Recall@20 is relative to the labeled pool, not all relevant jobs in the corpus.

| Method | P@5 | NDCG@10 | Labeled-pool Recall@20 | Recall@30 |
| --- | ---: | ---: | ---: | ---: |
| Keyword B0 | **0.500** | **0.604** | 0.490 | 0.573 |
| PostgreSQL FTS B1 | 0.400 | 0.450 | 0.343 | 0.472 |
| Dense OpenAI | 0.200 | 0.378 | 0.213 | 0.252 |
| Dense Qwen | 0.300 | 0.547 | 0.420 | 0.587 |
| Hybrid OpenAI | 0.200 | 0.380 | 0.472 | 0.510 |
| Hybrid Qwen | 0.300 | 0.522 | **0.549** | **0.671** |

Hybrid Qwen is the provisional candidate generator because it retrieved the most known relevant jobs at depths 20 and 30. B0 ranked the first five better in this sample. Retrieval scores are candidate-selection scores, never match percentages. Optional filter quality is still unmeasured. The [Stage-3 report](supporting/CP23_Stage3_Retrieval_Comparison_20261003.md) keeps per-CV results and judgment coverage.

## 4. LLM comparison

The original round-one requests remain historical. A request-repair framing bug was fixed, and the bug-fixed B view is primary under D-066. Validator v1.1 resolves only source-identical words across punctuation, separators, and spacing, and preserves the original CV span. G1/G2 lower bounded unsupported MATCH labels. D-067's SQL example interpretation was applied equally to every candidate. Failed stages remain unassessed.

| Candidate and scope | Extraction F1, seven JDs | Valid matching pairs | Guarded evidence Macro-F1, all 73 units | Matching request p95 | Matching collection cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| DeepSeek Flash, round one B | **0.862** | 4/4 | 0.772 | 90.747 s | US$0.040562 |
| GPT-6 Luna, round one B | 0.794 | 4/4 | 0.730 | 21.880 s | US$0.007206 |
| Gemini Flash-Lite, round one B | 0.683 | 2/4 | 0.457 | 6.165 s | US$0.058356 |
| Claude Haiku 4.5, round one B | 0.542 | 1/4 | 0.249 | 12.619 s | US$0.140864 |
| DeepSeek Pro, round two | Not comparable on an accepted seven-JD extraction alignment | 4/4 after source normalization | 0.642 | 140.562 s | US$0.016740 |
| GPT-6 Sol, quality reference | Four-JD reference only | 4/4 | **0.829** | 16.134 s | US$0.167522 |

The answered-cases-only matching view is retained in the [validator result](../../evals/results/cp23_stage2_validator_v11_20261004_v2.json) and [revised-reference result](../../evals/results/cp23_sql_reference_comparison_20261004_v2.json). It must not replace the all-cases denominator when a model fails. The original A results, repair replay, request counts, per-class confusion and costs are in the [Stage-2 record](supporting/CP23_Stage2_LLM_Comparison_20261003.md). Gemini's seven-JD F1 includes the later strict F00815 mapping: 14 TP, 4 FP and 2 FN for that JD, with no special exception. See the [mapping result](../../evals/results/cp23_gemini_f00815_alignment_20261004_v1.json).

DeepSeek Flash exceeds Luna by 0.068 in extraction F1 and 0.042 in guarded evidence Macro-F1. The matching gap exceeds D-066's 0.03 cheaper-model switch threshold. D-068 therefore selects DeepSeek Flash for both tasks provisionally. GPT-6 Sol is a quality reference, not the production candidate. DeepSeek still has two confirmed unsupported positive claims among 50 positive units on the reviewed development pairs. Showing a source quote makes the claim auditable but does not make it true.

## 5. Prompt versions and validator

The full hashes and content are in the [prompt inventory](../../evals/results/cp23_prompt_version_inventory_20261003_v1.json). Historical files remain at their original paths so frozen run hashes can be checked.

| Task and version | Change and measurement | SHA-256 |
| --- | --- | --- |
| JD v1 | Initial source-grounded extraction | `0e17816b88703fdc26e341894c6ea87e8a79ba7f6dcfe2694a855458f63e6ad4` |
| JD v1.1 | Schema and annotation precedent clarification, historical | `8c91296b0861a82654ede5bec46f60d324cc08dcee3d62bc690d7a36136052d0` |
| JD v1.2 | Historical configured verification baseline | `35525ee62f8aa7f79307d8d8b95141e85c7d30fa06b359a9dcb48c3a6cad1836` |
| JD v1.3 | Source inventory experiment; failures retained | `0afe4b95155c7225bafd62e9216344cd886a4d6ba2e005fd746652b6ed97a224` |
| JD v1.4 experimental | Qualification inventory and explicit AND/OR instructions; measured in Stage 2 and selected provisionally | `9fe62242b5f24f4f4b5560218653bf8db68df09ede5465a3fc01ca4e6bc087e7` |
| Evidence v1 | Initial rubric, historical | `bbaaddea09a4364d5365376dc51ade462ffab9487149d0d6a9753991f5757816` |
| Evidence v1.1 | Fixed-input matching comparison and provisional selection | `19576d1940ad74015954f7014ba816f428ac835e726d89b3bfd107eb93e81d1f` |

Validator v1.1 and G1/G2 are separate from the prompt. The selected configuration is in [the provisional version file](../../config/versions/pipeline_cp23_provisional_20261004.yaml). The original `config/pipeline_v1.yaml` remains byte-identical to its frozen baseline because historical plans hash that path. CP3 must promote the selected version through an explicit migration and regression check.

## 6. Experiment timeline

| Run | Purpose and result | Cost and record |
| --- | --- | --- |
| CP2.1 B0/B1 | Establish lexical baselines | [Experiments](../experiments.md) |
| Stage 3 retrieval | Six comparable development rankings; Qwen selected by D-044 | US$0; [result](../../evals/results/cp23_stage3_retrieval_evaluation_20261003_v2.json) |
| Stage 2 round one | Four LLMs on seven JDs and four evidence pairs | US$0.472589 combined extraction and matching; [report](supporting/CP23_Stage2_LLM_Comparison_20261003.md) |
| D-064 follow-up | GPT-6 Sol reference and DeepSeek Pro round two | US$0.405418; [report](supporting/CP23_Stage2_LLM_Comparison_20261003.md) |
| Repair replay | Eight bug-affected repair requests; B view created | US$0.097953; [result](../../evals/results/cp23_stage2_repair_comparison_20261004_v2.json) |
| Validator v1.1 and D-067 | Offline source spans and revised reference, no new API calls | US$0; [result](../../evals/results/cp23_sql_reference_comparison_20261004_v2.json) |
| Provisional freeze D-068 | Hybrid Qwen, DeepSeek Flash, K20 and weight 0.5 provisional | US$0; [decision](../decisions.md) |

Each collection cost is a scoped run cost, not a sum of all project spend. The project ledger and historical uncertain reservation are tracked separately.

## 7. Failures and fixes

The first Stage-2 repairs used an invalid later system message for some provider routes. The fix sent the repair instruction as a user turn and retained one repair attempt. Eight affected repairs were replayed without repeating successful first drafts. Validator v1.1 then recovered one Gemini and one DeepSeek Pro final output offline; remaining invalid words, provenance claims and ambiguous OR groups stayed failures. G1/G2 lowered literal skills-list and conjunction overclaims but did not remove every semantic scope error. Historical outcomes are preserved in the [failure log](../failures.md), [Stage-2 record](supporting/CP23_Stage2_LLM_Comparison_20261003.md) and [A1/A2 report](supporting/CP23_Validator_v11_and_A2_Proposal_20261004.md).

## 8. Provisional configuration and limits

| Setting | Development choice | Limit |
| --- | --- | --- |
| Candidate retrieval | Hybrid FTS and Qwen dense with RRF | B0 had higher P@5; optional filters not validated |
| Candidate depth | K=20, provisional | End-to-end ordering and runtime still needed |
| JD extraction | DeepSeek Flash, JD v1.4, cached after source checks | Broad development coverage incomplete |
| CV evidence matching | DeepSeek Flash, evidence v1.1, validator v1.1, G1/G2 | About 91-second observed request p95; residual unsupported positives |
| Match percentage | Required-unit evidence coverage with PARTIAL 0.5, provisional | Percentage is not hiring probability; hold incomplete analyses |
| Privacy | Synthetic CVs only in development; local masking and session controls under D-051 | Public real-CV release gates remain open |

The [K=20 cost projection](../../evals/results/cp23_k20_cost_projection_20261004_v1.json) estimates cached-JD matching at US$0.203 for DeepSeek, US$0.036 for Luna and US$0.838 for Sol per CV. These are linear small-sample estimates, excluding parsing, embedding, repairs, hosting and concurrent load. Part B stopped twice on transport timeouts, then completed collection of the 31 untouched pairs under D-069. Its [run report](supporting/CP23_PartB_Development_Run_20261004.md) records 37 process-valid and 14 failed JD extractions, all 60 saved pair records, 20 final numeric scores, cost and unavailable final-order metrics. It does not confirm the K20 projection or a one-CV end-to-end wall time. Held-out evaluation follows the frozen D-053 protocol and cannot be used for retuning.
