# Data Splits

Rules: D-046. Split by job cluster: a job and its duplicates are always on the same side. The split is written before any tuning and is not changed afterwards.

| File | Content | Status |
| --- | --- | --- |
| `dev_job_ids.txt` | Development half of the 428 target jobs, including the 5 pilot jobs | Frozen 1 Oct 2026: 214 jobs |
| `test_job_ids.txt` | Test half of the 428 target jobs | Frozen 1 Oct 2026: 214 jobs |

- CV1 and CV2 are used with both halves; CV3 (Dewi) only with the test half.
- Test labels and test results are never used to choose a model, prompt, weight, or K.

Manifest and checks: `split_manifest.json`; report: `docs/checkpoint_2/supporting/T03_Job_Split_20261001.md`. Re-run `python scripts/make_splits.py` only to verify the frozen outputs; it rejects changed inputs or contents.
