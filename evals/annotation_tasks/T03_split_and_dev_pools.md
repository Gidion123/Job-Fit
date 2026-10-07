# T03: Job-level split, then the development pools

Read first: `docs/decisions.md` D-045 and D-046, `evals/splits/README.md`, `docs/repo-structure.md`. No git commands. No paid API call in part 1.

## Part 1. Split (do now, before any tuning)

Write `scripts/make_splits.py` and `tests/test_splits.py`.

- Input: the 428 target jobs of snapshot `CP1_20260926` (`data/processed/jobs_features.jsonl`, `is_auditable` and `role_family` in ai_ml_engineering, data_science, genai_llm, software_ai). Job id = `final_cluster_id`.
- Probable duplicates: `data/interim/dedup_decisions.csv` and `data/interim/jsearch_probable_duplicates_review.csv`. Any pair that may be the same job goes to the same side.
- Pilot jobs F00016, F00022, F00034, F00073, F00114 are forced into development.
- Split 50/50, stratified by `role_family` x `experience_bucket`, seed `20261001`.
- Write `evals/splits/dev_job_ids.txt` and `evals/splits/test_job_ids.txt` (one id per line, sorted) and `evals/splits/split_manifest.json` (seed, counts per stratum, input file hashes, date).
- Tests: the two files are disjoint, their union is the 428 target jobs, pilot jobs are in dev, every duplicate pair is on one side, the same seed gives the same files.
- Report the counts per stratum. After this, the split files are never edited by hand.

## Part 2. Development pools (only after CP2.2 has embeddings for both models)

Write `scripts/build_dev_pools.py`.

- For CV1 and CV2, run every stage-1 candidate inside the development half only: B0, B1, dense and hybrid (RRF) with `openai/text-embedding-3-small`, dense and hybrid with `qwen/qwen3-embedding-8b`.
- Pool = union of the top 10 of every candidate. Write `evals/pools/dev_pool.csv`: `cv_id, job_id, title, best_rank, methods_top10, in_top5_any, already_gold, gold_review`.
- `already_gold = yes` for the 10 pilot relevance labels.
- `gold_review = yes`: first every job in the top 5 of any candidate, then random others (seed `20261001`) until 20 new rows per CV. Never more than 20 new per CV.
- Report pool size per CV and the number of `gold_review` rows.
