# Scripts

| Script | Purpose | Status |
| --- | --- | --- |
| `refresh_cp1_docs.py` | Rebuilds the CP1 inventory and insights from the JSON summary (offline) | Active |
| `build_corpus.py` | Rebuilds `data/interim/` from raw (offline) | Active, optional |
| `jsearch_collection.py` | JSearch collection module: query plan, bounded requests, evidence inventory | CP1 collection history |
| `run_jsearch_pilot.py` | Runs the 12-query pilot | CP1 collection history |
| `run_jsearch_batch02.py` | Runs batch 02 | CP1 collection history |
| `run_jsearch_batch.py` | Runs a batch manifest in `data/research/` | CP1 collection history |

The CP1 collection is closed. The collection scripts are kept for provenance and do not need to be run again to rebuild the EDA. The API key is read through a hidden prompt or an environment variable, and it is never saved to a file.
