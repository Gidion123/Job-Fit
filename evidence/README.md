# Evidence

Raw evidence for every claim in the reports: API responses, screenshots, per-batch audits, and related work tests. Files here are **not changed** after they are saved, because they are the data provenance.

## checkpoint_1/

| Folder | Contents |
| --- | --- |
| `provider_benchmark/` | Comparison of data sources. `jsearch/`: benchmark queries JS01 to JS05 (JSON responses + screenshots) and quota. `techmap/`: report on the access barriers and payment/CS screenshots. Decision: `CP1_Provisional_Source_Decision.md` |
| `corpus_collection/` | Corpus collection: pilot, COL01 and COL02, audits of batches 02 to 06, dedup review, collection log, and audit verification |
| `related_work/jobsentinel/` | Screenshots from testing JobSentinel (JSN), with their README |

## Naming convention

`CP1_<Source>_<Code>_<Description>_<Response|Screenshot|Audit>.<ext>`

Naming exception: the JS02 API response is named `CP1_JSearch_JS02_AIEngineer_ID_id_Screenshot.json`, even though it holds a JSON response (it should be `_Response.json`). This name is **kept on purpose**, because its path is locked by a hash in `data/interim/snapshots/CP1_20260926/SNAPSHOT_MANIFEST.json` and the file name is used as the source ID of 10 records in the data. The name stays permanently because the CP1 corpus is the final corpus. The file content is correct; only the end of the name is wrong. Its paired screenshot already has the right name (`_Screenshot.png`).
