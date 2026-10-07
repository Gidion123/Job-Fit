# CP2.3 freeze proposal: 4 October 2026

**Decision requested, not frozen.** Development evidence only. Eight replay calls cost **US$0.09795280**, below the explicitly approved **US$0.65** cap (preflight US$0.6485602). Total ledger **US$1.2715167842** includes historical uncertain **US$0.0210861**. No additional call is requested by this proposal.

| Setting | Proposed value | Evidence and main limit |
| --- | --- | --- |
| Primary comparison | B, after repair-framing fix | Removes the rejected application repair step; six matching failures remain. Gemini extraction F1 still needs new mapping acceptance. A remains historical. |
| Stage-1 method | Hybrid Qwen, conditional proposal | Highest pool Recall@20 0.548951 and @30 0.671329. B0 P@5 0.50 beats 0.30. No complete final-order comparison. |
| Embedding | Qwen3-Embedding-8B | Selected by D-044: dense gain 0.206294, hybrid gain 0.076923. Two development CVs only. |
| K | 20 as a provisional cost/coverage compromise | K30 gains recall but costs about 50% more matching calls. Gold-input ordering is unavailable, so K20 is not a measured optimum. |
| LLM | No unconditional winner; DeepSeek Flash plus guards is a low-cost fallback proposal | Best round-one B+guard Macro-F1 0.777417, extraction F1 0.861789; two scope overclaims remain. GPT Sol reference 0.818094 exceeds it by about 0.040677, outside the 0.03 tie. D-029 therefore does not automatically select this fallback. |
| Prompts | Measured JD v1.4, evidence v1.1 | JD version remains experimental until approval. No new prompt search. |
| PARTIAL weight | Retain 0.5 provisionally | All 108 oracle-order cells have missing A/B. The 0.25/0.5/0.75 sensitivity cannot establish an optimum. |
| Guardrails | G1/G2 if D-065 approved | Four original unsupported findings corrected; semantic scope failures remain. Offline only so far. |

**Cost basis for K:** DeepSeek matching cost US$0.040561914 over four original stages. Linear matching-only projections are K10 US$0.101404785, K20 US$0.202809570 and K30 US$0.304214355. They exclude CV parsing, JD extraction, provider changes, retries and load effects; they are not actual complete user-run bills. Cached corpus extraction changes the product cost profile. All failed requests remain in the ledger.

## Decisions needed

1. Accept B as primary while retaining A. Accept or amend the new Gemini/F00815 mapping proposal: P52-U09 maps to U09/U10 as a split; P52-U10 maps to incompatible SQL OR U11; P52-U12 maps to U13/U14 as a split with changed importance. Other listed one-to-one mappings are proposed equivalents. Existing follow-up reference mappings also remain pending; this run does not approve them.
2. Approve or reject D-065 and choose a safety policy below. No zero-claim winner is manufactured from one valid Claude pair.
3. For missing A/B, approve a clearly provisional method/K/weight freeze or choose a bounded further review scope. Do not request all 104 missing pairs by default. Full gold-input reordering is unavailable; unknown candidates were not removed or assigned zero.

| D-029 safety option | Measured implication | Trade-off |
| --- | --- | --- |
| (a) Keep zero unsupported claims | No fully covered round-one candidate passes. Further testing needs separate scope/budget. | Strongest unchanged gate; freeze delayed. |
| (b) Evaluate model plus guards and displayed quotes | Remaining B+guard findings: DeepSeek 2/50 positive units (4%); GPT 2/50 (4%); Gemini 1/13 (7.69%); Claude 0/13, but only 1/4 pairs valid. | More practical fallback, but a shown quote does not remove a false claim. Public user-system safety is not measured here. |
| (c) Zero for MATCH only; unconfirmed MATCH becomes PARTIAL "needs checking" | Scope errors outside G1/G2 still need a defined confirmation rule. GPT's two unsupported PARTIAL claims would remain. | More cautious display; new whole-system policy and tests are required. It is not already implemented or proven safe. |

**Recommendation:** use B for diagnosis and adopt G1/G2 only with their limits recorded. Keep the strict safety gate unless Dion explicitly accepts a provisional demo scope. Do not call CP2.3 DONE from this proposal. D-051 privacy acceptance, optional-filter scope and D-050 broad extraction need explicit closure/disposition. Presentation charts start only after the freeze decision; no test access occurred.

**Pre-freeze checks:** the full local suite has 433 passed, 2 skipped and 0 failed. Of 601 previously hashed protected files, 598 are unchanged; the other three are test files edited for the requested test fixes and historical-receipt regression. No protected source, gold, workbook, split, pool, prompt or test data changed. Seven current documents have no missing local links. The API ledger is US$1.2715167842 including US$0.0210861 of historical uncertain cost. [Verification receipt](../../../evals/results/cp23_freeze_precheck_20261004_v1.json). `evals/staging/` is 14,664,273 bytes and remains untouched. Dion may choose to archive or ignore it later; it is not part of the freeze decision.

[Stage-2 results](CP23_Stage2_LLM_Comparison_20261003.md#10-repair-framing-fix-and-rerun-4-october) | [Retrieval](CP23_Stage3_Retrieval_Comparison_20261003.md#8-d-044-rule-applied-for-freeze-preparation) | [Gold-input limits](CP23_Gold_Input_Upper_Bound_20261004.md) | [Machine-readable A/B evidence](../../../evals/results/cp23_stage2_repair_comparison_20261004_v2.json)
