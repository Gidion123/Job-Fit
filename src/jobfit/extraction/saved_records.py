"""Which saved JD extraction counts for a development job (same rule as the evaluated runs).

The newest evaluated record wins, even when it failed: an older success is never
used in place of a newer failure (scripts/run_cp23_luna_matching.jd_path).
Order: corpus extraction run, follow-up v2, pipeline v1.1 redo, end-to-end v1.
"""
from __future__ import annotations

import json
from pathlib import Path

from jobfit.config import REPO_ROOT

CP23 = REPO_ROOT / 'evals/results/cp23'
PRECEDENCE = (
    'corpus_extraction_development_v1/jd_{job}.json',
    'pipeline_v11/jd_hold_{job}_v11_v2.json',
    'pipeline_v11/jd_{job}_v11.json',
    'end_to_end_dev/cp23_end_to_end_dev_20261004_v1/jd_{job}.json',
)


def record_path(job: str, *, include_corpus: bool = True) -> Path | None:
    for pattern in PRECEDENCE if include_corpus else PRECEDENCE[1:]:
        path = CP23 / pattern.format(job=job)
        if path.exists():
            return path
    return None


def load_record(job: str, *, include_corpus: bool = True) -> dict | None:
    path = record_path(job, include_corpus=include_corpus)
    return json.loads(path.read_text()) if path else None
