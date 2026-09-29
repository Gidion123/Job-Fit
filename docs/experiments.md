# JobFit Experiment Log

One entry per experiment run in CP2 and CP3. Stage reports link here instead of copying numbers, so every number has one source.

## Entry format

| Field | Content |
| --- | --- |
| Run id | `EXP-YYYYMMDD-NN` |
| Date and stage | For example 2 Oct 2026, CP2.3 |
| Hypothesis | Which hypothesis from System Design v1.3 section 21 (H1 to H9) |
| Configuration | Stage-1 method, K, LLM model id, prompt version, embedding model and dimensions, guideline version |
| Data | Split (development or test), number of cases, snapshot `CP1_20260926` |
| Metrics | The metrics named in the hypothesis, with denominators |
| Cost and latency | From the usage ledger; live and cached separately |
| Git SHA | Commit of the code that ran |
| Result and decision | Keep / remove / needs more data, with a link to the docs/decisions.md entry if a decision was made |

## Experiment matrix

Written in CP2.1 (checkpoint 8), 29 Sep 2026. This is the plan of what gets compared, fixed before any result is seen. Nothing here is a result. No deep learning model is trained in any row (D-001): every row compares search methods, LLMs through OpenRouter, prompts, or fixed rules.

All rows use snapshot `CP1_20260926`, development cases only, until the test set is locked in CP2.3. Model ids and prices are in `config/models_v1.yaml`. A model not in that file cannot be called by the code, so a new candidate needs a row here first.

| Plan id | Stage | Hypothesis | What is compared | Fixed settings | Metric (decides) | Also reported | Est. cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | CP2.1 | Scoring rules match System Design v1.3 section 8 | Rule outputs vs the 8 hand-written fixtures | Score v0, PARTIAL weight 0.5 | All fixtures pass (pytest) | Nothing else | US$0 |
| M02 | CP2.1 | Baselines give a reference point | B0 keyword/skill overlap (CP1 v0 skill list) vs B1 PostgreSQL FTS | Pilot pool, 2 synthetic CVs | Stage-1 Recall@10 on pilot labels (small, only a sanity check) | Latency | US$0 |
| M03 | CP2.2 | H9: extraction is accurate enough | Extraction prompt v1 on `deepseek-flash` | Guideline v1, development JDs | Extraction precision / recall / F1 vs gold | Schema validity, cost, p50/p95 latency | under US$0.20 |
| M04 | CP2.3 | H3: hybrid finds relevant jobs better | B0, B1, B2 dense (`openai/text-embedding-3-small`, 1536 dim), C hybrid FTS + dense RRF | Development CVs, filters off and one filter setting | Stage-1 Recall@K | Filter recall, latency | under US$0.10 (embeddings) |
| M05 | CP2.3 | H2: K between 10 and 30 is enough | K = 10, 20, 30 with the stage-1 winner of M04 | Same pool as M04 | Recall@K and cost per run | p95 latency | under US$0.50 |
| M06 | CP2.3 | H5: a low-cost LLM is within 3 points of the reference | Round 1: `deepseek-flash`, `gpt-6-luna`, `gemini-3.5-flash-lite`, `claude-haiku-4.5`; reference `gpt-6-sol` on at most 10 hard cases | Prompt v1, about 30 development cases, temperature 0 | D-029 rule: safety gate, then evidence Macro-F1, then extraction F1, then cost within 0.03, then p95 latency | Cost per run, schema validity | under US$2 |
| M07 | CP2.3 (only if needed) | H5 round 2 | `deepseek-v4-pro` | Same as M06 | Same as M06 | Same as M06 | under US$1 |
| M08 | CP2.4 | H6: prompt v2 is better than v1 | Prompt v1 vs v2 on the M06 winner | Same cases as M06 | Extraction F1 and evidence Macro-F1 | Cost, latency | under US$0.50 |
| M09 | CP2.4 | H7: embeddings work for an Indonesian CV with English JDs | Recall@K for the Indonesian CV vs the English CVs | M04 winner | Recall@K gap | Examples of misses | US$0 extra |
| M10 | CP2.5 | H1: PARTIAL weight 0.5 makes sense | 0.5 vs 0.25 vs 0.75 | Final pipeline, development | Error audit against relevance labels; NDCG@10 | Examples where the order changes | US$0 (cached) |
| M11 | CP2.5 | H4: evidence match % improves the order | Stage-1 order vs final match-% order | Final pipeline, development | NDCG@10 and P@5 | Safety: hard negatives in top 10 | US$0 (cached) |
| M12 | CP2.5 (only if ties are common) | H8: another tie-break | Stage-1 order (default) vs "more requirements met" | Final pipeline | NDCG@10 | Tie count | US$0 |

Rules for every row:

- Numbers go in the Runs section below, with the run id, git SHA, and ledger cost. Stage reports link to them.
- The test set is used once, after the choices above are frozen (CP3).
- Only synthetic CVs and public job descriptions are sent to OpenRouter (D-021, D-030).

## Runs

No runs yet.
