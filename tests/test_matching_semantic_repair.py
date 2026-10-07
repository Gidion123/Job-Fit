import copy
import json
from pathlib import Path
import pytest
from scripts.repair_cp22_matching import FinalMatchingRepairClient, repair_report
from scripts.run_batch_extraction import development_sources
from jobfit.matching.evidence_matcher import EvidenceResponse

ROOT = Path(__file__).resolve().parents[1]


class Fake:
    def __init__(self, response):
        self.response, self.calls = response, []

    def chat_structured(self, model, messages, output_model, task, **kwargs):
        self.calls.append((task, messages))
        return output_model.model_validate(self.response)


def inputs():
    # Saved synthetic development result is replay input, not gold or an API call.
    names = ['01_semantic_repair', '02', '03_semantic_repair', '04']
    state = {'results': [json.loads((ROOT / 'evals/results' /
        f'cp22_extraction_repair_v13_20261003_{n}.json').read_text()) for n in names]}
    source = development_sources(['F00332'])[0]['text']
    return state, {'F00332': source}


def test_repair_reuses_exact_extraction_and_ordinary_score_validation():
    state, sources = inputs()
    before = copy.deepcopy(state)
    client = Fake({'assessments': state['results'][-1]['report']['assessments']})
    result = repair_report(state, sources, client, {'corrections': ['Inspect source evidence']})
    assert len(client.calls) == 1 and client.calls[0][0] == 'evidence_matching_semantic_repair'
    assert result.operations['extraction']['cache_hit']
    assert result.extraction.model_dump(mode='json') == state['results'][2]['extraction']
    assert result.score.model_dump(mode='json') == state['results'][-1]['report']['score']
    assert state == before  # historical response remains intact


def test_bad_quote_is_failed_not_negative_and_no_second_dispatch():
    state, sources = inputs()
    response = copy.deepcopy(state['results'][-1]['report']['assessments'])
    response[1]['cv_quotes'] = ['Invented evidence not in this CV']
    client = Fake({'assessments': response})
    result = repair_report(state, sources, client, {'corrections': ['Inspect source evidence']})
    assert len(client.calls) == 1
    assert result.status == 'matching_failed' and result.score.score_pct is None
    assert all(a.label is None and a.check_status.value == 'failed' for a in result.assessments)


def test_repair_cannot_dispatch_another_stage_or_retry():
    fake = Fake({'assessments': []})
    wrapped = FinalMatchingRepairClient(fake, ['source finding'], [])
    args = ('baseline', [{'role': 'system', 'content': 'rules'},
                        {'role': 'user', 'content': '{"untrusted_document_data": {}}'}], EvidenceResponse)
    with pytest.raises(RuntimeError):
        wrapped.chat_structured(*args, 'jd_extraction')
    assert not fake.calls
    wrapped.chat_structured(*args, 'evidence_matching')
    with pytest.raises(RuntimeError):
        wrapped.chat_structured(*args, 'evidence_matching')
    assert len(fake.calls) == 1
