# CP2.3 validator v1.1 and model choice proposal

**Date:** 4 October 2026. **Split:** development only. **Historical status at writing:** A1 complete offline; A2 then awaited Dion's model choice. Dion later approved DeepSeek Flash provisionally under D-068. The current interpretation is in [the main comparison](../CP2_03_Model_Comparison.md). This report does not by itself freeze the runtime configuration.

## Scope and rules

The primary operational view is B, which includes the repair-framing fix. The original A view remains in the historical Stage 2 report. D-066 amends D-029 for v1 after results were observed. Extraction and evidence matching are selected by their own quality metrics. A cheaper model qualifies only when it is within 0.03 of the best low-cost model on that task and has a complete process run. G1 and G2 are included in matching quality. The old and D-067 SQL references are both shown. The original gold remains unchanged.

The matching comparison uses 73 reviewed requirement units in four fixed CV and JD pairs. The extraction comparison uses 120 reviewed logical units in seven JDs for each round-one model. These are small, assisted development references, not held-out results.

## A1: source-bound validator v1.1

The [versioned validator](../../../src/jobfit/matching/quote_check_v11.py) retains the model's quote and resolves it to an original CV span. Only source spans are evaluated or displayed. Lexical tokens must be identical and in order. Punctuation, separator, Markdown and spacing differences may be normalized; a changed or invented word still fails. An OR-group parent label moves only when exactly one branch has clear quoted support. Ambiguity remains unassessed. Every change is flagged. The v1 runtime validator remains unchanged until the configuration decision.

| Matching scope and model | Valid stages before / after v1.1 | Outcome |
| --- | ---: | --- |
| Round one B, DeepSeek Flash | 4/4 to 4/4 | Complete |
| Round one B, GPT-6 Luna | 4/4 to 4/4 | Complete |
| Round one B, Gemini Flash-Lite | 1/4 to 2/4 | CV2/F00815 recovered by separator normalization |
| Round one B, Claude Haiku | 1/4 to 1/4 | Three stages still fail validation |
| Reference, GPT-6 Sol | 4/4 to 4/4 | Complete |
| Round two, DeepSeek Pro | 3/4 to 4/4 | CV1/F00036 recovered by separator normalization |

No parent OR label was safely moved in these saved final outputs. Gemini's remaining CV1/F00332 and CV2/F00018 quotes contain added words. Claude's CV1/F00332 and CV2/F00018 outputs claim `label_source=annotator`, although they came from the model. Claude's CV1/F00036 parent OR answers are ambiguous or unsupported by a listed branch. These are model-output failures under the fixed contract. No confirmed application-caused failure remains for a paid replay. The additional API cost under the A1 US$0.30 allowance is therefore **US$0**. The allowance is not a requirement to spend.

Source review of the newly recovered Gemini stage found Skills-only MATCH claims for prompt engineering and Git. G1 lowers both. Other PARTIAL labels in that stage cite a generic skills list that does not itself support pipeline, ETL, testing or CI/CD experience; these are reported as citation limitations, not silently approved evidence. The recovered DeepSeek Pro stage still has a possible overclaim that presenting results to a manager proves a nontechnical audience. Normalization proves source occurrence, not semantic entailment.

## Matching metrics on the same reviewed units

The table uses validator v1.1, B, G1/G2 and all 73 cases. Invalid stages contribute unassessed false negatives in their reviewed classes. The revised SQL interpretation treats PostgreSQL as an example, so G2 does not require both SQL and PostgreSQL. The old reference and its historical G2 behavior remain separately reproducible.

| Model | Valid pairs | Old reference Macro-F1 | D-067 reference Macro-F1 | Matching collection cost, USD | Request p95, seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| DeepSeek Flash | 4/4 | 0.777417 | **0.772296** | 0.040562 | 90.747 |
| GPT-6 Luna | 4/4 | 0.744424 | **0.730356** | 0.007206 | 21.880 |
| Gemini Flash-Lite | 2/4 | 0.458247 | 0.457051 | 0.058356 | 6.165 |
| Claude Haiku | 1/4 | 0.251754 | 0.249373 | 0.140864 | 12.619 |
| GPT-6 Sol reference | 4/4 | 0.832696 | 0.829449 | 0.167522 | 16.134 |
| DeepSeek Pro round two | 4/4 | 0.653116 | 0.642026 | 0.016740 | 140.562 |

Cost is the historical cost of collecting these matching outputs, not a new charge or a production price guarantee. p95 uses request attempts and is not a repeated-load service benchmark. The [reference comparison](../../../evals/results/cp23_sql_reference_comparison_20261004_v2.json) also contains the unguarded and answered-cases-only views for every model. The [validator record](../../../evals/results/cp23_stage2_validator_v11_20261004_v2.json) contains every recovered span, flag, coverage count and failure.

The DeepSeek Flash versus GPT-6 Luna difference is **0.041940** under the new reference, above the 0.03 threshold. The cheaper GPT-6 Luna therefore does not qualify under D-066, even though it is faster in this small sample. Under the old reference, the difference is 0.032992, also above the threshold. These margins are small enough that held-out results may reverse the ranking.

## Extraction and safety

The previously accepted seven-JD extraction F1 remains 0.861789 for DeepSeek Flash and 0.793651 for GPT-6 Luna, a difference of 0.068138. Both have complete seven-JD runs. Their saved F00815 extracted SQL units preserve PostgreSQL in parentheses as an example, so the D-067 interpretation does not change their accepted SQL alignment. Gemini's repaired F00815 extraction still awaits Dion's decision on three non-trivial mappings; its revised extraction F1 is withheld. The GPT-6 Sol four-JD reference must not be compared as if it covered all seven JDs.

Under the earlier source audit and the D-067 SQL interpretation, DeepSeek Flash has two confirmed unsupported positive labels after G1/G2 among 50 positive units in four complete pairs, **4%**. GPT-6 Luna also has two among 50, **4%**. The SQL work evidence is no longer counted as an unsupported positive. The other scope overclaims remain; the quote display and guardrails do not make them true. The newly recovered Gemini and DeepSeek Pro stages have additional source issues described above, and their incomplete or separate scopes prevent a comparable full-candidate safety rate here. These development findings require a held-out test and a runtime source-span check before public claims.

## A2 proposal for Dion

| Task | Proposed model | Measured basis | Main limitation |
| --- | --- | --- | --- |
| Offline JD extraction | DeepSeek Flash | 0.861789 versus 0.793651 extraction F1 over the same seven JDs; both runs complete | Small reviewed development sample; broad JD cache not built |
| Per-user evidence matching | DeepSeek Flash | 0.772296 versus 0.730356 guarded Macro-F1 on the same 73 units with D-067; both runs complete | Slower observed p95 and two unsupported positives remain |

GPT-6 Sol is a quality reference at 0.829449 guarded matching Macro-F1, not a proposed production model. A whole-project cost projection needs the planned run volume; the four-pair collection cost alone does not prove that a full test and demo exceed US$15. The provisional Hybrid Qwen, K 20 and PARTIAL weight 0.5 proposal remains separate from this model decision. No runtime setting, final ranking or chart was changed in A1/A2.

**Decision requested:** accept DeepSeek Flash for both extraction and matching as a provisional development choice, or request a different choice with its quality, cost and latency trade-off recorded. Part A3 begins only after that decision.

## Verification

The full local suite passed: **443 passed, 2 skipped, 0 failed**. The focused validator/reference checks passed: **11 passed**. The source, gold, workbook, split, pool and test-data files in the 601-file protection snapshot are unchanged. Exactly three previously modified test files differ from that older snapshot; no protected non-test file differs. Seven edited documentation files have no missing local link in the checked set. The API ledger has 207 records and still totals **US$1.2715167842**, including the historical uncertain reservation US$0.0210861. This A1 check made no API call and spent **US$0**, below the additional US$0.30 cap. No database or held-out evaluation was run.
