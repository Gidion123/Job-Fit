"""Post-labeling command: runs offline on r3 and never turns missing labels into zero."""
from scripts import run_post_labeling as post

R3 = post.ROOT / 'evals/gold/development_v13_reviewed_20261003_stage1_r3'


def test_runs_on_r3_and_reports_unavailable_cells():
    res = post.build(R3)
    assert res['api_calls'] == 0
    assert res['d078_decision']['status'] == 'unavailable'
    methods = {r['method'] for r in res['retriever_comparison']['rows']}
    assert {'hybrid_qwen', 'B0', 'fusion_hybrid_qwen_B0'} <= methods
    assert res['retriever_comparison']['proposed_rule']['status'] == 'approved_D-084'
    assert all(v['result'].startswith('unavailable') for v in res['retriever_comparison']['proposed_rule_verdicts'])


def test_missing_r4_stops_with_a_clear_message(tmp_path):
    import pytest
    with pytest.raises(SystemExit, match='not found'):
        post.main(['--gold', str(tmp_path / 'nope')])
