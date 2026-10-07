# CP2.3 Audit Fixes and Offline Re-evaluation

**Date:** 4 October 2026. **Split:** development only (CV1, CV2). **Model calls:** none. **Decisions:** D-072 to D-076.

After the CP2 presentation I audited all CP2 work. The reported numbers were correct: I recomputed P@5, NDCG@10 and Recall@20/30 for all six retrieval methods and the matching Macro-F1, and they matched. The problems were in how strong some conclusions looked. This report lists each finding, what I changed and what the saved data now shows. Gold, workbook, sources, split, prompts and earlier results were not changed.

## 1. Summary

| Finding | Fix | Result |
| --- | --- | --- |
| H2 removed experience, seniority and education requirements from the score | D-072 H2v2 keeps these pairs on hold; flags outside the percentage no longer make a score provisional | 33 of 60 usable pairs (H2: 42). Nine misleading scores removed, two scores corrected to final |
| Final-order metrics were never available (0 of 36 cells) | D-073 measures the real product order, held jobs last | H4, K and weight can now be compared on development |
| Senior jobs were the main cause of irrelevant results | D-074 seniority rule (development candidate) | Hybrid Qwen P@5 CV1 0.2 to 0.6, CV2 0.4 to 0.8 |
| DeepSeek versus Luna was decided on a difference inside noise | D-075 bootstrap intervals; D-076 Luna check approved | DeepSeek minus Luna 0.042, interval -0.067 to 0.148 |
| G1 only worked on Markdown CVs | Plain-text Skills heading detection | Same result on all development data; now works on plain text |
| One test failed after a README edit | Test checks the frozen plan | Full suite green: 508 passed, 2 skipped |

## 2. H2v2 (D-072)

Nine of the 16 provisional H2 scores had dropped a requirement such as "8-10 years of progressive experience" or a degree. For a fresh graduate these are usually not met, so dropping them made senior jobs look better. CV1 x F00208 (principal role) scored 39.47%.

H2v2 keeps a pair on hold when an unresolved scored requirement is about experience, level or education. Detection uses the category, `min_years`, OR branches and a small documented seniority/years pattern. Other rules stay as in D-071.

| Policy (saved v1.1 outputs, weight 0.5) | Usable pairs of 60 |
| --- | ---: |
| H1 | 26 |
| H2 | 42 |
| H2v2 | 33 |

Check: the script reproduced every saved H1 and H2 score exactly before computing anything new (0 mismatches).

## 3. Product-order metrics (D-073)

The product already has a clear order: scored jobs by percentage, conflict jobs next, held jobs last. Measuring this order means a held relevant job is pushed down, so failures still cost points. Every cell reports how many top-K jobs were not scored.

Stage 1 (Hybrid Qwen), macro over two CVs: P@5 0.30, NDCG@10 0.522.

| Final order, weight 0.5 | K=10 P@5 | K=10 NDCG@10 | K=20 P@5 | K=20 NDCG@10 |
| --- | ---: | ---: | ---: | ---: |
| H1 | 0.40 | 0.543 | 0.40 | 0.553 |
| H2 | 0.40 | 0.534 | 0.50 | 0.530 |
| H2v2 | 0.40 | 0.551 | 0.50 | unavailable (CV2/F00629 unlabeled) |

`docs/evaluation.md` is unchanged on purpose: the approved D-052 receipt hashes that file, so the amendment lives in D-073 and in `src/jobfit/eval/product_order.py`.

Reading: ordering by evidence raises P@5 but NDCG@10 moves only a little. Two CVs cannot show a significant difference. K=30 cells need four more relevance labels.

## 4. Seniority rule (D-074)

In the judged pool, every job asking for 3 or more years was not relevant for CV1 (14 of 14) and 16 of 17 were not relevant for CV2. The rule moves buckets `3-4y` and `5y+` below the other jobs and keeps the order inside each group. `not_stated` is never moved.

| Hybrid Qwen | P@5 before | P@5 after | NDCG@10 before | NDCG@10 after |
| --- | ---: | ---: | ---: | ---: |
| CV1 | 0.2 | 0.6 | 0.355 | 0.525 |
| CV2 | 0.4 | 0.8 | 0.689 | unavailable (2 new jobs unlabeled) |

With the rule, the final order for CV1 at K=10 (H2v2) reaches P@5 0.4 and NDCG@10 0.581. The rule was found after seeing development labels, so it must be frozen before the test and confirmed there.

## 5. Uncertainty (D-075)

| Matching comparison (73 units, 4 pairs) | Difference | 95% unit interval | 95% pair interval |
| --- | ---: | --- | --- |
| DeepSeek minus Luna, reported view | 0.042 | -0.067 to 0.148 | -0.042 to 0.091 |
| DeepSeek minus Luna, before G1/G2 and D-067 | 0.016 | -0.091 to 0.122 | -0.117 to 0.091 |
| GPT-6 Sol minus DeepSeek | 0.057 | -0.021 to 0.143 | -0.024 to 0.116 |

| Error direction against gold | DeepSeek | Luna |
| --- | ---: | ---: |
| Label stronger than gold | 6 | 3 |
| Label weaker than gold | 9 | 16 |
| MATCH precision | 0.84 | 0.96 |

Retrieval: labeled-pool recall favours hybrid because B0 has 15 to 16 unjudged jobs in its top 30 and Hybrid Qwen only 6 to 8. For CV1, B0 finds 8 of 13 relevant jobs in its top 20 and Hybrid Qwen 6. So "Hybrid Qwen is best" is not established; Qwen over OpenAI holds on both CVs.

## 6. Guardrail G1 on plain text

G1 found the Skills section only through Markdown `#` headings. It now also accepts plain heading lines with known English or Indonesian section names. On the five synthetic CVs (526 quote checks) and all 341 saved development assessments the output is identical to before, so no earlier result changes.

## 7. Luna matching check (D-076, not run yet)

`scripts/run_cp23_luna_matching.py` runs Luna on the same 60 pairs and measures one-CV K=20 wall time for Luna and DeepSeek with 20 workers. Cap US$0.40; offline preflight estimate US$0.30. It must run on Dion's machine because the key is only in the local `.env`. Then `scripts/evaluate_cp23_luna_matching.py --write` writes the comparison.

## 8. Files

- Code: `src/jobfit/scoring/hold_policy_v11.py` (H2v2), `src/jobfit/eval/product_order.py`, `src/jobfit/search/seniority.py`, `src/jobfit/matching/guardrails.py`.
- Scripts: `scripts/evaluate_cp23_product_order.py`, `scripts/evaluate_cp23_seniority_rule.py`, `scripts/evaluate_cp23_uncertainty.py`, `scripts/run_cp23_luna_matching.py`, `scripts/evaluate_cp23_luna_matching.py`.
- Tests: `tests/test_pipeline_v11_policy.py`, `tests/test_product_order.py`, `tests/test_seniority.py`, `tests/test_evidence_guardrails.py`, `tests/test_luna_matching_plan.py`, `tests/test_cp23_stage2_followup.py`.
- Results: `evals/results/cp23/dev_eval_v2_20261004/`.

## 9. Still open

- Run the Luna check and decide the matching model (D-068 stays provisional until then).
- Label seven missing development relevance pairs (CV1: F00060, F00129; CV2: F00418, F00556, F00629, F00645, F00682). This completes the K=20/K=30 and seniority cells.
- Choose K and weight, then freeze the configuration with H2v2 and the seniority rule before the test (D-053).
- After the freeze: extract all target JDs, label the test pool blind, run CP2.4.
- Build the one-CV orchestrator in `src/` for the CP3 API.
