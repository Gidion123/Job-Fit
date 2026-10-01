# Scripts

| Script | Purpose | Status |
| --- | --- | --- |
| `refresh_cp1_docs.py` | Rebuilds the CP1 inventory and insights from the JSON summary (offline) | Active |
| `build_corpus.py` | Rebuilds `data/interim/` from raw (offline) | Active, optional |
| `jsearch_collection.py` | JSearch collection module: query plan, bounded requests, evidence inventory | CP1 collection history |
| `run_jsearch_pilot.py` | Runs the 12-query pilot | CP1 collection history |
| `run_jsearch_batch02.py` | Runs batch 02 | CP1 collection history |
| `run_jsearch_batch.py` | Runs a batch manifest in `data/research/` | CP1 collection history |
| `load_snapshot_to_db.py` | Loads the 632 EDA candidates of snapshot `CP1_20260926` into the local PostgreSQL | CP2.1, active |
| `run_baselines.py` | Runs B0 (skill overlap) and B1 (full-text search) for the synthetic CVs | CP2.1, active |
| `export_pilot_gold.py` | Exports the approved pilot labels to `evals/gold/` (development split) | CP2.1, active |
| `score_pilot_pairs.py` | Score v1 on the approved pilot labels; writes `evals/results/cp21_pilot_scores.json` | CP2.1, active |
| `usage_report.py`, `run_batch_extraction.py`, `build_embeddings.py`, `run_experiment.py`, `run_evaluation.py`, `make_eval_figures.py`, `precompute_demo.py` | Placeholders, filled in the stage written in `docs/repo-structure.md` | CP2.2 onward |

The CP1 collection is closed. The collection scripts are kept for provenance and do not need to be run again to rebuild the EDA. The API key is read through a hidden prompt or an environment variable, and it is never saved to a file.
