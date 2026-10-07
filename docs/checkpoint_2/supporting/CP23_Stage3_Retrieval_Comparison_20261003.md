# CP2.3 Stage 3: Development Retrieval and Embedding Comparison

**Date:** 3 October 2026. **Status:** measured for the approved automatic/no-optional-filter condition; filter comparison deferred. No final configuration selected.

## 1. Question and comparison scope

Which stage-1 method retrieves reviewed CV-compatible jobs on the same development universe? This comparison measures candidate retrieval, before requirement extraction and evidence-based final ordering. Retrieval similarity/overlap is never reported as a match percentage.

The six candidates are B0 skill overlap, B1 PostgreSQL FTS, dense OpenAI, dense Qwen, hybrid OpenAI and hybrid Qwen. All use the same 214 frozen development jobs, CV1/CV2, original ranked positions and reviewed eligible C judgments. The embedding candidates are text-embedding-3-small (1,536 dimensions) and Qwen3-Embedding-8B (4,096 dimensions). No new vectors, database writes or API calls were needed.

## 2. Verified inputs and metric contract

- Saved rankings: `evals/results/cp22_retrieval_top30_20261002_03.json`, twelve successful top 30 runs.
- References: immutable `development_v13_reviewed_20261003_stage1_r3`, 38 C judgments for CV1 and 40 for CV2. Relevant grades are 2 and 3: 13 for CV1 and 11 for CV2.
- Five Stage-1 gates, linked receipt hashes, gold manifest/files, split, corpus, query caches, CV hashes and saved retrieval code/configuration hashes were verified against current bytes. Evaluator/script hashes are in the output receipt.
- D-052/D-054 contract: P@5 denominator five with all original five judged; NDCG@10 uses exponential gain and the entire same eligible judged pool for IDCG. No condensed rankings.
- All six methods have complete original top 10 judgments for both CVs. The union contains 70 distinct CV–JD pairs; 120 top 10 positions include repeated identities across methods.
- Recall@10/20/30 is relative to the declared judged eligible pool, not corpus recall. Unknown deeper positions are not labeled zero.

## 3. Results: macro means over two CV queries

| Method | P@5 | NDCG@10 | Pool Recall@10 | Pool Recall@20 | Pool Recall@30 | Judged top 20 / 40 | Judged top 30 / 60 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B0 | 0.500 | 0.604 | 0.451 | 0.490 | 0.573 | 24 | 29 |
| B1 | 0.400 | 0.450 | 0.297 | 0.343 | 0.472 | 26 | 35 |
| dense_openai | 0.200 | 0.378 | 0.168 | 0.213 | 0.252 | 29 | 34 |
| dense_qwen | 0.300 | 0.547 | 0.245 | 0.420 | 0.587 | 29 | 37 |
| hybrid_openai | 0.200 | 0.380 | 0.136 | 0.472 | 0.510 | 40 | 48 |
| hybrid_qwen | 0.300 | 0.522 | 0.343 | 0.549 | 0.671 | 38 | 46 |

Macro averaging gives each CV equal weight; 78 job judgments are not 78 independent CV queries. Per-CV values and explicit recall numerators/denominators are retained in the JSON and CSV.

## 4. Interpretation and design consequences

1. **Dense Qwen has higher NDCG@10 than dense OpenAI for both CVs:** CV1 0.615 vs 0.315; CV2 0.478 vs 0.442. Its average P@5 is also higher (0.30 vs 0.20). This supports keeping Qwen in the development shortlist; it does not prove superiority on unseen CVs or the full deployment corpus.
2. **B0 has the highest mean P@5 and NDCG@10 in this small scope.** Its result depends on the CV: CV1 P@5=0.60, while B1 reaches 0.60 for CV2. Do not assume hybrid is always better or promote B0 without final-stage evaluation and the agreed decision rule.
3. **Hybrid Qwen retrieves more known relevant items at depth 30:** mean labeled-pool recall rises from 0.343 at 10 to 0.671 at 30. B0 has better immediate top 5 precision, while hybrid Qwen supplies a broader known-relevant candidate set for evidence matching. These serve different pipeline roles.
4. **K cannot be selected from this table alone.** Top30 contains 14–31 unjudged positions per method across the two CVs. New relevance judgments, operational extraction/matching cost and final recommendation quality would be needed for stronger K claims. Current K10/20/30 remain candidates.
5. **Local timings are observations, not production benchmarks.** B0 invocations were about 0.36–0.42 ms, dense 4.14–6.99 ms, and FTS/hybrid 23.25–48.63 ms. These exclude query embedding, connection, preparation, LLM work and UI/network time; fixed-order/warm-cache effects remain.

## 5. Limitations and gates

- Only two familiar synthetic development CVs, with pool-based assisted labels reviewed by one annotator. No held-out estimate, uncertainty interval or statistical superiority claim.
- The same pooled C set is used for IDCG across methods, but it was collected from candidate methods and is incomplete beyond top 10. Recall is biased toward judged items and must not be described as corpus recall.
- CV1/F00369 is a human-approved C=1 on archived truncated source and occurs at B1 position7. It is explicitly source-limited; its A/B remain held. No replacement source was invented.
- Optional filters and filter recall remain unmeasured; the runner condition is automatic target-role retrieval.
- Hybrid used RRF k60 and run-local branch depth 30. Active default branch depth 20 is unchanged.
- Stage-2 extraction/evidence results and later end-to-end ranking remain separate gates. At the original measurement boundary, no selection occurred. Section 8 now applies D-044 to the embedding; method, LLM and K still await freeze.

## 6. Verification and artifacts

- Targeted offline suite: **64 passed, zero skipped**, covering evaluator provenance, original-position metrics, stale C rejection, no inference fallback, path containment, cumulative budget and GPT parameter adaptation, plus existing runner/metric tests. Database/live calls are not represented by this offline result.
- `evals/results/cp23_takeover_targeted_tests_20261003_v1.xml`.
- Current result: `evals/results/cp23_stage3_retrieval_evaluation_20261003_v2.json`; per-CV CSV: `evals/results/cp23_stage3_retrieval_metrics_20261003_v1.csv`.
- Earlier v1 is the initial calculation receipt; v2 adds evaluator/code and existing query-cache provenance. Numerical results are identical; no labels or rankings were altered.
- Reproduce into a new result version if inputs/code change; the CLI intentionally refuses to overwrite an existing result.
- API cost for Stage 3: **US$0**, with no new inference or embedding.

## 7. Next step

Complete the separately authorized Stage-2 collection and source/alignment review. Then compare extraction/evidence quality, investigate K and final recommendation ordering, implement the D-051 synthetic privacy checks, and request approval for a concrete configuration before opening the held-out evaluation. D-050 broad extraction still requires its own accepted scope/budget disposition.


## 8. D-044 rule applied for freeze preparation

Embedding: **Qwen3-Embedding-8B selected by the D-044 rule** on the existing reviewed development pool. Dense Recall@20 improves by 0.206294; hybrid improves by 0.076923. Both exceed 0.05. No new embeddings or rankings were generated. The rule result does not change runtime configuration before the freeze decision.

Hybrid Qwen has the highest labeled-pool Recall@20 (0.548951) and Recall@30 (0.671329). B0 has the highest P@5 (0.500000). Stage-1 method and K remain proposals. Only two development CVs support the result; missing deeper relevance is not zero. [Rule receipt](../../../evals/results/cp23_embedding_D044_selection_20261004_v1.json).
