from copy import deepcopy
import pytest
from jobfit.config import REPO_ROOT
from jobfit.eval.retrieval_evaluation import aggregate, checked_path, evaluate
from jobfit.eval import retrieval_evaluation

# The saved CV query embeddings are git-ignored local files. CI checkouts do not
# have them, so this module runs on Dion's machine and skips in CI.
pytestmark = pytest.mark.skipif(not any((REPO_ROOT / 'reports/embedding_queries').glob('*.json')),
                                reason='local query embedding cache not present (git-ignored)')


@pytest.fixture(scope='module')
def comparison():
    return evaluate(REPO_ROOT)


def test_real_reviewed_comparison_keeps_original_positions_and_two_queries(comparison):
    assert len(comparison['metrics']) == 12
    assert len(comparison['aggregate']) == 6
    assert all(r['query_count'] == 2 for r in comparison['aggregate'])
    assert not comparison['primary_publication_blocked_by_unjudged']
    assert comparison['judgment_inventory']['CV1']['judged'] == 38
    assert comparison['judgment_inventory']['CV2']['judged'] == 40
    assert comparison['winner'] is None and comparison['configuration_selected'] is False
    assert comparison['api_calls'] == comparison['cost_usd'] == 0
    assert all(m['filter_recall']['value'] is None for r in comparison['metrics'] for m in r['metrics'])


def test_macro_is_over_cvs_not_pooled_jobs(comparison):
    rows = [r for r in comparison['metrics'] if r['method'] == 'B0']
    result = aggregate(rows)[0]
    p5 = [next(m for m in r['metrics'] if m['k'] == 5)['precision_at_k']['value'] for r in rows]
    assert result['p_at_5_macro'] == sum(p5) / 2 == 0.5
    duplicated = deepcopy(rows)
    duplicated[1]['cv_id'] = 'CV1'
    with pytest.raises(ValueError, match='two development queries'):
        aggregate(duplicated)


def test_unjudged_deep_positions_are_not_claimed_irrelevant(comparison):
    for r in comparison['metrics']:
        m30 = next(m for m in r['metrics'] if m['k'] == 30)
        if m30['coverage']['unjudged_original_top_k']:
            assert m30['precision_at_k']['value'] is None
            assert m30['ndcg_at_k'] is None
    qwen = next(r for r in comparison['aggregate'] if r['method'] == 'hybrid_qwen')
    assert qwen['judged_original_top_k']['30'] == 46 < 60


def test_input_path_cannot_escape_repository(tmp_path):
    outside = tmp_path / 'outside.json'; outside.write_text('{}')
    repo = tmp_path / 'repo'; repo.mkdir()
    with pytest.raises(ValueError, match='external'):
        checked_path(repo, '../outside.json')


def test_changed_reviewed_judgments_stop_comparison(monkeypatch):
    original = retrieval_evaluation.file_hash
    def altered(path):
        if str(path).endswith('stage1_r3/relevance_gold.jsonl'):
            return 'a' * 64
        return original(path)
    monkeypatch.setattr(retrieval_evaluation, 'file_hash', altered)
    with pytest.raises(ValueError, match='Stale comparison input'):
        evaluate(REPO_ROOT)


def test_comparison_never_constructs_inference_client(monkeypatch):
    from jobfit.llm import client
    def forbidden(*args, **kwargs):
        raise AssertionError('No inference client is permitted')
    monkeypatch.setattr(client, 'OpenRouterClient', forbidden)
    result = evaluate(REPO_ROOT)
    assert result['api_calls'] == 0 and result['test_access'] is False
