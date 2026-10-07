"""Offline boundary tests for the Stage-1 candidate source selector."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('cp23_stage1_prep', ROOT/'scripts/prepare_cp23_stage1.py')
PREP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREP)


def test_selected_sources_rejects_heldout_and_duplicate_source(tmp_path, monkeypatch):
    split = tmp_path/'evals/splits'
    split.mkdir(parents=True)
    (split/'dev_job_ids.txt').write_text('DEV\n')
    (split/'test_job_ids.txt').write_text('TEST\n')
    corpus = tmp_path/'data/processed'
    corpus.mkdir(parents=True)
    rows = [{'final_cluster_id':'DEV','description_clean':'A'},
            {'final_cluster_id':'DEV','description_clean':'duplicate'},
            {'final_cluster_id':'TEST','description_clean':'held out'}]
    (corpus/'jobs_features.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    monkeypatch.setattr(PREP, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='development'):
        PREP.selected_sources({'TEST'})
    with pytest.raises(ValueError, match='Duplicate'):
        PREP.selected_sources({'DEV'})


def test_cli_cannot_silently_select_legacy_pilot_path(tmp_path):
    report = tmp_path/'readiness.json'
    result = subprocess.run([sys.executable, str(ROOT/'scripts/run_evaluation.py'),
                             '--output',str(report)],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode == 2
    assert '--historical-pilot' in result.stderr
    assert not report.exists()
