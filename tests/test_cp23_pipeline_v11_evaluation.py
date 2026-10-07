"""The development evaluator never promotes missing stages into a metric."""

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/evaluate_cp23_pipeline_v11.py'
SPEC = importlib.util.spec_from_file_location('evaluate_cp23_pipeline_v11', SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_main_run_preserves_original_positions_and_missing_scores():
    result = module.evaluate()
    assert len(result['results']) == 36
    assert result['no_missing_as_zero'] is True
    assert result['product_order_valid'] is False
    assert all(row['candidate_count'] == row['k'] for row in result['results'])
    for row in result['results']:
        assert set(row['missing_score_ids']).isdisjoint(row['score_ranked_ids'] or [])
        if row['missing_score_ids']:
            assert row['score_order']['p_at_5'] is None
            assert row['score_order']['ndcg_at_10'] is None


def test_continuation_requires_complete_receipt(monkeypatch, tmp_path):
    monkeypatch.setattr(module, 'NEW', tmp_path)
    (tmp_path / 'plan_v1.json').write_text('{}')
    (tmp_path / 'summary_v1.json').write_text('{}')
    with pytest.raises(ValueError, match='continuation is incomplete'):
        module.evaluate(include_continuation=True)
