# JobFit CP2 presentation summary

**4 October 2026. All measured results below are development results, not held-out test results.**

## Problem

A CV can share words with a job description while missing a required skill, duration or location condition. JobFit aims to rank jobs that fit the CV and show the exact evidence and gaps behind each match percentage.

## Approach

The user reviews the parsed CV, may set optional job filters, and receives a ranked list. Stage 1 retrieves candidate jobs. Stage 2 extracts JD requirements, matches each requirement against the CV, shows source quotes and constraints, and computes evidence coverage. A pasted JD is available for a job absent from the database. The CP1 source is a 632-job analysis snapshot with 428 target-role jobs; CP2 retrieval comparisons use the locked 214-job development half.

## What we compared

- Six stage-1 methods: keyword B0, PostgreSQL FTS B1, dense OpenAI, dense Qwen, hybrid OpenAI and hybrid Qwen, on two synthetic development CVs.
- Four low-cost LLMs on seven reviewed JDs and four fixed CV/JD evidence pairs, plus GPT-6 Sol as a matching quality reference. The four pairs contain 73 requirement units.
- Versioned prompt, validator and guardrail behavior. Original failed runs remain in the experiment record. A repair-framing bug was corrected without rerunning successful first attempts.

## Provisional choice and why

Qwen wins the pre-registered embedding Recall@20 rule. Hybrid Qwen's labeled-pool Recall@10/20/30 is **0.343 / 0.549 / 0.671** on the two development CVs. B0 still has better P@5, so hybrid remains provisional. DeepSeek Flash has extraction F1 **0.862** versus GPT-6 Luna **0.794**. After source-bound validator v1.1, approved guardrails and the D-067 SQL reference, DeepSeek matching Macro-F1 is **0.772** versus Luna **0.730**. D-066's 0.03 rule therefore selects DeepSeek Flash for both tasks on development. Gemini's strict seven-JD extraction F1 after the repaired F00815 mapping is **0.683**.

K=20 and PARTIAL weight 0.5 remain provisional. Gold-input score ordering had missing A/B, so it did not establish an optimum. GPT-6 Sol reached **0.829** matching Macro-F1 on the same four-pair reference and remains a quality reference, not a production model.

## What failed and what remains

Exact quote occurrence did not always support the full MATCH claim. DeepSeek still has **2 unsupported positives among 50 positive units** after deterministic guards. Its observed matching request p95 was about **91 seconds**, versus 22 seconds for Luna. CP3 therefore needs concurrent matching, cached JD extraction and a precomputed synthetic demo. The K=20 matching-only cost projection with cached JDs is about **US$0.203 per CV** for DeepSeek, **US$0.036** for Luna and **US$0.838** for Sol. These exclude CV parsing, query embedding and retry/load effects.

## Next step

Part B found an important scale limit: 14 of 51 attempted JD extractions failed, and only 20 of 60 CV/JD pairs had final scores. Pipeline v1.1 raised process-valid extraction from **37/51 to 48/51**. With D-071's explicitly provisional H2 rule, **42/60 pairs** have a final or provisional score, below the **54/60** target. The bounded follow-up did not raise that number. None of the 36 H1/H2 final-order CV/K/weight metric cells has complete top-K analysis, so H4, K20 and PARTIAL weight 0.5 remain unconfirmed. One-CV K20 end-to-end time is still unmeasured. The v1.1 run accounted **US$0.6281001646** against its US$3.00 cap, including a US$0.0501633 uncertain reservation. The [v1.1 report](CP23_Pipeline_v11_20261004.md) records the remaining source, model and semantic failures. CP2.4 uses the untouched test split only after a final development configuration and D-053 protocol freeze. Real CV processing remains disabled until privacy release gates are verified.

**Figures:** [retrieval](../../../reports/figures/cp2/fig01_retrieval_methods.png), [embedding](../../../reports/figures/cp2/fig02_embedding_recall20.png), [LLM quality](../../../reports/figures/cp2/fig03_llm_quality.png), [confusion](../../../reports/figures/cp2/fig04_matching_confusion.png), [guardrails](../../../reports/figures/cp2/fig05_guardrail_effect.png), [cost/latency](../../../reports/figures/cp2/fig06_cost_latency.png), [original coverage](../../../reports/figures/cp2/fig07_partb_coverage_20261004_v1.png), and [v1.1 coverage](../../../reports/figures/cp2/fig08_pipeline_v11_coverage_20261004_v3.png).
