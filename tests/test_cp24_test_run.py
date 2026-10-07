"""CP2.4 runner: refuses without approved freeze; pure helpers. No call, no DB."""
import pytest

from scripts import run_cp24_test as t


def test_refuses_without_approved_freeze(tmp_path):
    with pytest.raises(SystemExit):
        t.main(['stage1', '--freeze', str(tmp_path)])


def test_analyzed_jobs_apply_seniority_then_k():
    out = t.analyzed_jobs({'CV3': ['A', 'B', 'C', 'D']}, {'A': '5y+'}, k=2)
    assert out == {'CV3': ['B', 'C']}


def test_run_file_keeps_original_stage1_order_and_top10():
    stage1 = {'CV1': [f'J{i}' for i in range(30)]}
    final = {'CV1': [f'J{i}' for i in range(10, 0, -1)]}
    run = t.run_file(stage1, final, t.ROOT / 'evals/freeze/x', 'r')
    assert run['cvs']['CV1']['stage1_ids'] == stage1['CV1'][:10] and run['freeze_folder'] == 'evals/freeze/x'
    with pytest.raises(ValueError):
        t.run_file(stage1, {}, t.ROOT, 'r')


def test_first_name_hint_and_query_cache_scope(tmp_path):
    assert t.first_name(t.ROOT / t.CVS['CV1']) == 'Rina'
    cache = t.HeldOutQueryCache(tmp_path)

    class Doc:
        document_id, source_hash, input_hash = 'CV9', 'a', 'b'

    class Spec:
        profile_id = 'p'
    with pytest.raises(ValueError):
        cache.path(Spec, Doc)
