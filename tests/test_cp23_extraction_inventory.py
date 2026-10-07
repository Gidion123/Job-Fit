from copy import deepcopy
import pytest
from jobfit.config import REPO_ROOT
from jobfit.eval.extraction_inventory import inventory, summarize


def test_inventory_preserves_failed_rejection_without_duplicate_draft():
    r = inventory(REPO_ROOT)
    assert len(r['rows']) == 28
    assert len({x['stage_id'] for x in r['rows']}) == 28
    assert r['additional_process_observations'][0]['error_code'] == 'NotFoundError'
    assert all(x['extraction_f1'] is None and x['alignment_status'] == 'pending' for x in r['rows'])
    assert r['model_winner'] is None and not r['configuration_selected']


def test_source_pass_is_not_f1_and_rejected_cost_is_retained():
    row = {'model': 'gpt-6-luna', 'model_id': 'openai/gpt-6-luna', 'process_status': 'done',
           'source_qa_status': 'pass', 'attempts': 1, 'source_checks': {}}
    records = [{'model': row['model_id'], 'cost_usd': 0.1},
               {'model': row['model_id'], 'cost_usd': 0, 'ok': False}]
    result = next(x for x in summarize([row], records) if x['model'] == row['model'])
    assert result['source_qa_all_pass'] == 1 and result['extraction_f1'] is None
    assert result['ledger_cost_usd'] == '0.1' and result['ledger_calls_including_rejections'] == 2
    bad = deepcopy(records); bad[0]['cost_usd'] = -1
    with pytest.raises(ValueError, match='Invalid inventory ledger'):
        summarize([row], bad)
