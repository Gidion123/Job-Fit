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

Written in CP2.1 (checkpoint 8), 29 Sep 2026; stages aligned with the master plan and M04b added on 1 Oct 2026 (D-044, pending). This is the plan of what gets compared, fixed before any result is seen. Nothing here is a result. No deep learning model is trained in any row (D-001): every row compares search methods, LLMs through OpenRouter, prompts, or fixed rules.

All rows use snapshot `CP1_20260926`, development cases only, until the test set is locked in CP2.3. Model ids and prices are in `config/models_v1.yaml`. A model not in that file cannot be called by the code, so a new candidate needs a row here first.

| Plan id | Stage | Hypothesis | What is compared | Fixed settings | Metric (decides) | Also reported | Est. cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | CP2.1 | Scoring rules match System Design v1.3 section 8 | Rule outputs vs the 8 hand-written fixtures | Score v0, PARTIAL weight 0.5 | All fixtures pass (pytest) | Nothing else | US$0 |
| M02 | CP2.1 | Baselines give a reference point | B0 keyword/skill overlap (CP1 v0 skill list) vs B1 PostgreSQL FTS | Pilot pool, 2 synthetic CVs | Stage-1 Recall@10 on pilot labels (small, only a sanity check) | Latency | US$0 |
| M03 | CP2.2 | H9: extraction is accurate enough | Extraction prompt v1 on `deepseek-flash` | Guideline v1, development JDs | Extraction precision / recall / F1 vs gold | Schema validity, cost, p50/p95 latency | under US$0.20 |
| M04 | CP2.3 | H3: hybrid finds relevant jobs better | B0, B1, B2 dense (`openai/text-embedding-3-small`, 1536 dim), C hybrid FTS + dense RRF | Development CVs, filters off and one filter setting | Stage-1 Recall@K | Filter recall, latency | under US$0.10 (embeddings) |
| M04b | CP2.3 (only if D-044 option A is approved) | H7 and H3: a multilingual embedding model finds relevant jobs better | Dense and hybrid search with `openai/text-embedding-3-small` vs `qwen/qwen3-embedding-8b` | Same pool and K as M04; silver development labels (D-044) | Stage-1 Recall@20; a model wins only if at least 0.05 better | Indonesian-CV gap, cost of embedding the corpus, latency per CV | under US$0.05 |
| M05 | CP2.3 | H2: K between 10 and 30 is enough | K = 10, 20, 30 with the stage-1 winner of M04 | Same pool as M04 | Recall@K and cost per run | p95 latency | under US$0.50 |
| M06 | CP2.3 | H5: a low-cost LLM is within 3 points of the reference | Round 1: `deepseek-flash`, `gpt-6-luna`, `gemini-3.5-flash-lite`, `claude-haiku-4.5`; reference `gpt-6-sol` on at most 10 hard cases | Prompt v1, about 30 development cases, temperature 0 | D-029 rule: safety gate, then evidence Macro-F1, then extraction F1, then cost within 0.03, then p95 latency | Cost per run, schema validity | under US$2 |
| M07 | CP2.3 (only if needed) | H5 round 2 | `deepseek-v4-pro` | Same as M06 | Same as M06 | Same as M06 | under US$1 |
| M08 | CP2.3 | H6: prompt v2 is better than v1 | Prompt v1 vs v2 on the M06 winner | Same cases as M06 | Extraction F1 and evidence Macro-F1 | Cost, latency | under US$0.50 |
| M09 | CP2.3 (development), CP2.4 (test) | H7: embeddings work for an Indonesian CV with English JDs | Recall@K for the Indonesian CV vs the English CVs | M04 winner | Recall@K gap | Examples of misses | US$0 extra |
| M10 | CP2.3 | H1: PARTIAL weight 0.5 makes sense | 0.5 vs 0.25 vs 0.75 | Final pipeline, development | Error audit against relevance labels; NDCG@10 | Examples where the order changes | US$0 (cached) |
| M11 | CP2.3 (development), CP2.4 (test) | H4: evidence match % improves the order | Stage-1 order vs final match-% order | Final pipeline, development | NDCG@10 and P@5 | Safety: hard negatives in top 10 | US$0 (cached) |
| M12 | CP2.3 (only if ties are common) | H8: another tie-break | Stage-1 order (default) vs "more requirements met" | Final pipeline | NDCG@10 | Tie count | US$0 |

Rules for every row:

- Numbers go in the Runs section below, with the run id, git SHA, and ledger cost. Stage reports link to them.
- The test set is used once, in CP2.4, after the choices above are frozen. Only the chosen configuration runs on it, plus the stage-1 methods as a measurement (M11).
- Only synthetic CVs and public job descriptions are sent to OpenRouter (D-021, D-030).

## Runs

### EXP-20261001-01: Baselines B0 and B1 (plan M02)

| Field | Content |
| --- | --- |
| Date and stage | 1 Oct 2026, CP2.1 |
| Hypothesis | Baselines give a reference point (M02); prepares H3 |
| Configuration | B0: share of the job's v0 skills found in the CV (`skill_aliases_v0`). B1: PostgreSQL full-text search, `simple` configuration, title weight A and JD text weight B, `ts_rank_cd`, query = phrase OR of the aliases of the CV's v0 skills. No LLM, no embeddings |
| Data | Snapshot `CP1_20260926`; 632 jobs loaded into PostgreSQL 17 with pgvector (Docker); pool = 428 target jobs (automatic mode, D-009); CV1, CV2, CV3 synthetic |
| Metrics | No gold labels yet for this pool, so no Recall@K. Reported: ranks of the 5 pilot jobs, size of the B1 match set, overlap of the B0 and B1 top 10 |
| Cost and latency | US$0 (no API call); runs in seconds |
| Git SHA | Commit by Dion after this run |
| Output | `evals/results/cp21_baselines.json` |

Results (Dion's run on the Docker database; identical to an earlier dry run on a separate PostgreSQL 16 test database):

| CV | B1 matched jobs | B0/B1 top-10 overlap | Pilot job ranks, B0 / B1 |
| --- | --- | --- | --- |
| CV1 (Rina) | 373 of 428 | 0 | J1 14 / 75; J2 293 / 275; J3 265 / 105; J4 238 / 103; J5 315 / 278 |
| CV2 (Bima) | 392 of 428 | 0 | J1 77 / 208; J2 345 / 302; J3 149 / 61; J4 306 / 107; J5 61 / 21 |
| CV3 (Dewi) | 381 of 428 | 0 | J1 91 / 165; J2 136 / 203; J3 129 / 55; J4 130 / 67; J5 133 / 70 |

Result and decision:

- The two baselines disagree completely on the top 10 for every CV, so stage-1 method choice matters (H3 is worth testing).
- B0 favors jobs with very short v0 skill lists (one matching skill can give 1.0). B1 matches almost every job (373 to 392 of 428) and favors long JDs that repeat terms.
- The only pilot job labeled 3 (CV1 x J1) is ranked 14 by B0 and 75 by B1. One labeled pair cannot compare the methods; Recall@K is computed in CP2.3 on the test pool (D-043).
- Kept as reference baselines. No decision entry.

### EXP-20261001-02: Score v1 on the approved pilot labels (plan M01, check of D-032)

| Field | Content |
| --- | --- |
| Date and stage | 1 Oct 2026, CP2.1 |
| Hypothesis | Score v1 follows the relevance labels better when soft skills are shown separately (D-032) |
| Configuration | Score v1, PARTIAL weight 0.5; soft skills, location, and work authorization outside the percentage; comparison mode with soft skills inside. Input = approved extraction and evidence labels, not model output |
| Data | Development split: CV1 x J1 (21 units) and CV2 x J2 (13 units), guideline v1.2 |
| Metrics | Score %, score status, counts; relevance label of the same pair |
| Cost and latency | US$0 (no API call) |
| Git SHA | Commit by Dion after this run |
| Output | `evals/results/cp21_pilot_scores.json` (`scripts/score_pilot_pairs.py`) |

| Pair | Relevance label | Score v1 | Status | Required met | Soft skills with evidence | Score with soft skills inside |
| --- | --- | --- | --- | --- | --- | --- |
| CV1 x J1 | 3 | 92.86% | provisional (1 unit of unknown importance) | 6 MATCH + 1 PARTIAL of 7 | 2 MATCH + 2 PARTIAL of 9 | 59.38% |
| CV2 x J2 | 1 | 55.56% | provisional | 4 MATCH + 2 PARTIAL of 9 | 0 of 1 | 50.00% |

Result and decision:

- With soft skills outside, the gap between the pair labeled 3 and the pair labeled 1 is 37 points; with soft skills inside it is 9 points. This supports D-032, but two pairs prove nothing on their own. The real check is M10 and M11 on more pairs.
- Both scores are provisional because each JD has one requirement whose importance is unknown (D-042). The app shows this status next to the score.
- CV2 x J2 also has an explicit experience conflict (D-042), which the score does not include; it is shown as a constraint above the score (D-013).
- No decision entry; D-032 stays approved and is checked again in CP2.3.
