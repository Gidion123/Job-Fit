# Data

| Folder | Contents | Can it be changed? |
| --- | --- | --- |
| `raw/jsearch/` | Original JSearch responses per query (`.json`) + request metadata (`.meta.json`) | **No.** Source of all derived data |
| `interim/` | Output of `scripts/build_corpus.py`: records per slot, canonical clusters, duplicate candidates, dedup decisions | Rebuilt from raw |
| `interim/snapshots/CP1_20260926/` | Frozen snapshot read by the notebook, with a manifest and hashes | **No.** A new snapshot is made as a new version |
| `processed/` | Notebook output: clean corpus, features, review queue, and the CP1 numbers summary | Rebuilt by the notebook |
| `research/` | Query plans and collection batch manifests | History, not changed |

`raw/` and the two `jsearch_records.jsonl` files are kept locally and are not in the public repository. They hold full API responses, including recruiter contact details that appear in some job descriptions. The processed files have contact details removed.

Field definitions are in [`docs/data-contract.md`](../docs/data-contract.md). The official CP1 numbers are in [`processed/CP1_research_summary.json`](processed/CP1_research_summary.json).
