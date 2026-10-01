# Data Splits

| File | Content | Status |
| --- | --- | --- |
| `dev_job_ids.txt` | The 5 pilot jobs (J1 to J5). Used for tuning in CP2.3 | Filled 1 Oct 2026 |
| `test_job_ids.txt` | Held-out test jobs (D-043): 10 jobs per CV from the 428 target jobs, none from the pilot jobs or their dedup clusters | Locked before any tuning in CP2.3 |

Split by job cluster: a job and its duplicates are always in the same split. Synthetic CV3 (Dewi) is used only with test jobs.
