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
| `build_embeddings.py`, `setup_embedding_tokenizers.py` | Versioned two-model embedding build and tokenizer setup; preflight, cost guard and resume | CP2.2, implemented; corpus build complete |
| `build_cv_upload_fixtures.py` | Synthetic development CV1 single-column, two-column and image-only PDF fixtures | CP2.2, fixtures already created |
| `run_cp22_example.py` | Preflight or paid synthetic CV1 PDF + pilot J1 pasted-JD integration check; saves diagnostic report with versions and costs | CP2.2, implemented; not a model benchmark |
| `run_batch_extraction.py` | Frozen development-only JD extraction with versioned cache and preflight; no test JD processing before freeze | CP2.2, implemented; full batch not executed |
| `usage_report.py`, `run_experiment.py`, `run_evaluation.py`, `make_eval_figures.py`, `precompute_demo.py` | Remaining planned scripts; inspect their current implementation before use | CP2.2 onward |

The CP1 collection is closed. The collection scripts are kept for provenance and do not need to be run again to rebuild the EDA. The API key is read through a hidden prompt or an environment variable, and it is never saved to a file.

## CP2.2 continuation

Use the project environment, a new run ID each time, and inspect existing result files first. These commands only estimate; do not add `--execute` merely to repeat a completed diagnostic:

```bash
cd "/Users/gidion/Downloads/Final Project-Job Fit/project-job-fit"
env-job-fit/bin/python scripts/run_cp22_example.py --run-id my_cp22_preflight
env-job-fit/bin/python scripts/run_batch_extraction.py --run-id my_dev_batch_preflight
```

The batch script rejects held-out IDs and refuses execution above its approval ceiling. Raising `--approved-budget-usd` requires Dion's explicit approval; it does not bypass the project's hard stop. Failed source validation is not NO_MATCH. No script here approves workbook labels, exports pending rows as gold, or establishes model accuracy.
