# CP2.3: Gold-input upper bound

## Why

Check whether score v1 can reorder the same retrieved candidates using reviewed A/B as oracle inputs. This is an offline upper-bound diagnostic conditional on the reviewed inventory, not a measured recommendation system. It does not certify complete extraction of every original JD.

## Method

Six methods, CV1/CV2, original K = 10, 20, 30, and PARTIAL weights 0.25, 0.5, 0.75 give 108 cells. Existing score v1 provides required counts and exclusions. Logical units come from the immutable bundle; OR counts once and uses the reviewed best label. Runtime remains weight 0.5. Score ties retain retrieval order. D-052 uses the same eligible judged pool and original positions.

A missing or held A/B record is not analyzed, never zero. When any top-K score is unavailable, a complete score ordering is unavailable: placing the unknown candidate last or pinning its position would introduce a new convention. The artifact retains every original ID, available score/component and exact missing reason. No candidate is dropped.

## Result

**0 of 108 complete score-order cells.** There are 104 distinct CV/job pairs without usable scores somewhere in the union of original top 30 lists. Original P@5/NDCG@10 remain measured. Score-order P@5/NDCG@10 are unavailable, so this run cannot select K or a PARTIAL weight.

| Method | CV | Analyzable / K10 | Analyzable / K20 | Analyzable / K30 |
| --- | --- | --- | --- | --- |
| B0 | CV1 | 9/10 | 11/20 | 12/30 |
| B0 | CV2 | 8/10 | 9/20 | 11/30 |
| B1 | CV1 | 9/10 | 10/20 | 12/30 |
| B1 | CV2 | 9/10 | 11/20 | 12/30 |
| dense_openai | CV1 | 8/10 | 9/20 | 10/30 |
| dense_openai | CV2 | 8/10 | 11/20 | 11/30 |
| dense_qwen | CV1 | 7/10 | 9/20 | 10/30 |
| dense_qwen | CV2 | 8/10 | 12/20 | 15/30 |
| hybrid_openai | CV1 | 6/10 | 13/20 | 17/30 |
| hybrid_openai | CV2 | 5/10 | 15/20 | 19/30 |
| hybrid_qwen | CV1 | 6/10 | 14/20 | 17/30 |
| hybrid_qwen | CV2 | 8/10 | 14/20 | 17/30 |

## Next

Retain weight 0.5 as the existing hypothesis, not a demonstrated optimum. For K/method freeze, either approve a documented provisional scope based on retrieval coverage/cost or request a bounded complete A/B subset. This is not a request to label all 104 pairs. The current data cannot supply the full requested ordering comparison without changing review scope.

[Full result and missing IDs](../../../evals/results/cp23_gold_input_upper_bound_20261004_v1.json). API cost US$0. Sources, labels, pool and retrieval rankings are unchanged.

