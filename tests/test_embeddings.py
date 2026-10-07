"""Offline fixtures only. No corpus labels, test CVs, network, or paid calls."""
from dataclasses import replace
from types import SimpleNamespace as NS
import json
import math
import pytest
from jobfit.config import Settings
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.budget import BudgetExceeded
from jobfit.search.embeddings import EmbeddingSpec, prepare, build, batches
from jobfit.search.query_cache import SyntheticQueryCache
from jobfit.search.response_cache import ResponseCache
from jobfit.search import hybrid, dense, fts

SPEC = EmbeddingSpec('fixture/model', 2, 'fixture-v1', 12, 'fixture-byte', '1')


class Tokenizer:
    def encode(self, text):
        return list(text.encode('utf-8'))


def doc(name='D1', text='hello', spec=SPEC):
    return prepare(name, text, spec, Tokenizer())


class SDK:
    def __init__(self, data=None, error=None, model='openai/text-embedding-3-small'):
        self.calls = 0
        self.data = data if data is not None else [NS(index=1, embedding=[0., 1.]), NS(index=0, embedding=[1., 0.])]
        self.error, self.model = error, model
        self.embeddings = NS(create=self.create)

    def with_options(self, **kwargs):
        self.options = kwargs
        return self

    def create(self, **kwargs):
        self.calls += 1
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return NS(id='fixture-request', model=self.model, data=self.data,
                  usage=NS(prompt_tokens=8, cost=0.00001))


def client(tmp_path, sdk, hard_stop=4.5):
    return OpenRouterClient(replace(Settings(), usage_ledger=tmp_path/'ledger.jsonl',
                                   api_hard_stop_usd=hard_stop), sdk_client=sdk)


def test_embedding_reorders_indices_enforces_privacy_and_logs_no_text(tmp_path):
    sdk = SDK()
    c = client(tmp_path, sdk)
    assert c.embed(['PRIVATE A','PRIVATE B'], dimensions=2) == [[1.,0.],[0.,1.]]
    assert sdk.options == {'max_retries':0, 'timeout':60.0}
    assert sdk.kwargs['encoding_format'] == 'float'
    assert sdk.kwargs['extra_body']['provider'] == {
        'require_parameters':True, 'data_collection':'deny', 'max_price':{'prompt':0.02,'request':0}}
    assert 'response_format' not in sdk.kwargs and 'dimensions' not in sdk.kwargs
    row = c.ledger.records()[0]
    assert row.ok and row.request_id == 'fixture-request' and row.cost_source == 'reported'
    assert row.batch_size == 2 and row.dimensions == 2
    assert 'PRIVATE' not in c.ledger.path.read_text()


@pytest.mark.parametrize('data', [
    [NS(index=0, embedding=[1.,0.])],
    [NS(index=0, embedding=[1.,0.]), NS(index=0, embedding=[0.,1.])],
    [NS(index=0, embedding=[1.]), NS(index=1, embedding=[0.,1.])],
    [NS(index=0, embedding=[math.nan,0.]), NS(index=1, embedding=[0.,1.])],
    [NS(index=0, embedding=[0.,0.]), NS(index=1, embedding=[0.,1.])],
])
def test_rejects_invalid_batch_and_retains_billed_cost(tmp_path, data):
    c = client(tmp_path, SDK(data=data))
    with pytest.raises(ValueError):
        c.embed(['a','b'], dimensions=2)
    row = c.ledger.records()[0]
    assert not row.ok and row.cost_usd == 0.00001


def test_rejects_wrong_response_model(tmp_path):
    c = client(tmp_path, SDK(model='another/model'))
    with pytest.raises(ValueError):
        c.embed(['a','b'], dimensions=2)


def test_accepts_explicit_openai_response_alias_and_keeps_canonical_ledger_id(tmp_path):
    c = client(tmp_path, SDK(model='text-embedding-3-small'))
    assert len(c.embed(['a','b'], dimensions=2)) == 2
    assert c.ledger.records()[0].model == 'openai/text-embedding-3-small'


def test_alias_does_not_accept_similarly_named_different_model(tmp_path):
    c = client(tmp_path, SDK(model='text-embedding-3-large'))
    with pytest.raises(ValueError):
        c.embed(['a','b'], dimensions=2)


def test_accepts_explicit_qwen_response_alias_without_allowing_it_for_openai(tmp_path):
    c = client(tmp_path, SDK(model='Qwen/Qwen3-Embedding-8B'))
    assert len(c.embed(['a','b'], model='qwen/qwen3-embedding-8b', dimensions=2)) == 2
    with pytest.raises(ValueError):
        c.embed(['a','b'], model='openai/text-embedding-3-small', dimensions=2)


def test_budget_blocks_before_request(tmp_path):
    sdk = SDK()
    c = client(tmp_path, sdk, 0)
    with pytest.raises(BudgetExceeded):
        c.embed(['a','b'], dimensions=2)
    assert sdk.calls == 0 and not c.ledger.records()


def test_uncertain_failure_reserves_cost_without_error_text(tmp_path):
    sdk = SDK(error=TimeoutError('SENSITIVE DATA'))
    c = client(tmp_path, sdk)
    with pytest.raises(TimeoutError):
        c.embed(['a','b'], dimensions=2)
    row = c.ledger.records()[0]
    assert not row.ok and row.cost_source == 'uncertain_upper_bound' and row.cost_usd > 0
    assert sdk.calls == 1 and 'SENSITIVE' not in c.ledger.path.read_text()


def test_empty_inputs_never_call_provider(tmp_path):
    sdk = SDK()
    c = client(tmp_path, sdk)
    with pytest.raises(ValueError):
        c.embed([' '], dimensions=2)
    assert sdk.calls == 0


def test_truncation_preserves_unicode_prefix_and_counts():
    source = 'éé🙂🙂xx'
    prepared = doc(text=source)
    assert source.startswith(prepared.text) and '\ufffd' not in prepared.text
    assert prepared.original_tokens == len(source.encode())
    assert prepared.truncated and prepared.input_tokens <= 12
    assert prepared.input_hash != prepared.source_hash


def test_batch_token_limit_and_size():
    documents = [doc(str(i), '12345') for i in range(5)]
    assert [len(b) for b in batches(documents, size=3, max_tokens=11)] == [2,2,1]
    with pytest.raises(ValueError):
        list(batches(documents, max_tokens=4))


class MemoryStore:
    def __init__(self):
        self.rows = {}
    def key(self, spec, d):
        return spec.profile_id, d.document_id, d.source_hash, d.input_hash
    def contains(self, spec, d):
        return self.key(spec,d) in self.rows
    def save_batch(self, spec, pairs):
        self.rows.update({self.key(spec,d):v for d,v in pairs})


class FakeClient:
    def __init__(self, fail_call=None):
        self.calls, self.fail_call = 0, fail_call
    def embed(self, texts, model, dimensions):
        self.calls += 1
        if self.calls == self.fail_call:
            raise RuntimeError('fixture failure')
        return [[1.] + [0.]*(dimensions-1) for _ in texts]


def test_resume_preserves_committed_batches_and_skips_successes():
    docs = [doc(str(i)) for i in range(5)]
    store = MemoryStore()
    first = build(docs, SPEC, FakeClient(2), store, batch_size=2)
    assert (first['succeeded'], first['failed'], first['not_attempted']) == (2,2,1)
    assert len(store.rows) == 2
    second_client = FakeClient()
    second = build(docs, SPEC, second_client, store, batch_size=2)
    assert second['cached'] == 2 and second['succeeded'] == 3 and second['failed'] == 0
    assert second_client.calls == 2 and len(store.rows) == 5
    no_calls = FakeClient()
    assert build(docs,SPEC,no_calls,store)['cached'] == 5 and no_calls.calls == 0


@pytest.mark.parametrize('change', [{'model':'other/model'}, {'dimensions':3},
                                    {'preprocessing_version':'v2'}, {'max_input_tokens':10},
                                    {'tokenizer_revision':'2'}])
def test_cache_separates_model_dimensions_preprocessing_and_tokenizer(change):
    store = MemoryStore()
    build([doc()], SPEC, FakeClient(), store)
    spec = replace(SPEC, **change)
    assert build([doc(spec=spec)], spec, FakeClient(), store)['cached'] == 0


def test_changed_source_and_input_do_not_reuse_vectors():
    store = MemoryStore()
    build([doc()], SPEC, FakeClient(), store)
    assert build([doc(text='changed')], SPEC, FakeClient(), store)['cached'] == 0


def test_synthetic_query_cache_rejects_test_cv_and_checks_profile(tmp_path):
    cache = SyntheticQueryCache(tmp_path)
    d = doc('CV1')
    cache.save_batch(SPEC, [(d,[1.,0.])])
    assert cache.get(SPEC,d) == [1.,0.]
    assert not cache.contains(replace(SPEC, preprocessing_version='v2'), d)
    with pytest.raises(ValueError):
        cache.contains(SPEC, doc('CV4'))
    row = json.loads(cache.path(SPEC,d).read_text())
    row['input_hash'] = 'wrong'
    cache.path(SPEC,d).write_text(json.dumps(row))
    with pytest.raises(ValueError):
        cache.get(SPEC,d)


def test_failed_query_cache_write_can_resume_from_receipt(tmp_path, monkeypatch):
    cache = SyntheticQueryCache(tmp_path / 'queries')
    d = doc('CV1')
    original_dump = json.dump
    def interrupted_dump(value, output):
        output.write('{')
        raise OSError('fixture write interruption')
    monkeypatch.setattr(json, 'dump', interrupted_dump)
    with pytest.raises(OSError):
        cache.save_batch(SPEC, [(d, [1., 0.])])
    assert not cache.contains(SPEC, d)
    monkeypatch.setattr(json, 'dump', original_dump)
    with_receipt = ResponseCache(tmp_path / 'receipts.sqlite3')
    with_receipt.save_batch(SPEC, [(d, [1., 0.])])
    no_calls = FakeClient()
    result = build([d], SPEC, no_calls, cache, response_cache=with_receipt)
    assert result['recovered'] == 1 and no_calls.calls == 0
    assert cache.get(SPEC, d) == [1., 0.]
    with_receipt.close()


@pytest.mark.parametrize('data, expected', [
    ({'is_management_key': True}, False),
    ({'is_management_key': False}, True),
    ({}, False),
    ({'is_management_key': 'false'}, False),
])
def test_key_preflight_distinguishes_management_and_inference(tmp_path, data, expected):
    class KeySDK(SDK):
        def get(self, path, cast_to):
            assert path == '/key' and cast_to is dict
            return {'data': {**data, 'label': 'PRIVATE ACCOUNT'}}
    sdk = KeySDK()
    c = client(tmp_path, sdk)
    status = c.verify_inference_key()
    assert status['inference_key'] is expected
    assert sdk.calls == 0 and not c.ledger.records()
    assert 'PRIVATE' not in json.dumps(status)


def test_rrf_uses_ranks_and_stable_tie_not_raw_scores():
    a = [{'job_id':'B','score':999},{'job_id':'A','score':0.01}]
    b = [{'job_id':'A','score':50},{'job_id':'B','score':1}]
    result = hybrid.rrf([a,b],k=60)
    assert [r['job_id'] for r in result] == ['A','B']
    assert result[0]['score'] == pytest.approx(1/61+1/62)
    with pytest.raises(ValueError):
        hybrid.rrf([a+a])


def test_dense_rejects_mixed_query_profile_before_database():
    with pytest.raises(ValueError):
        dense.rank(None, dense.QueryEmbedding('wrong',[1.,0.]), SPEC, job_ids=['D1'])


def test_fts_applies_scope_before_limit_and_empty_scope_no_database():
    query, _ = fts.build_query(['python'], scoped=True)
    text = query.as_string()
    assert text.index('j.job_id = ANY') < text.index('LIMIT')
    assert fts.rank(None, {'python'}, job_ids=[]) == []
    assert fts.rank(None, set(), job_ids=['D1']) == []


def test_successful_api_response_survives_database_write_failure(tmp_path):
    class FailingStore(MemoryStore):
        def save_batch(self, spec, pairs):
            raise OSError('database unavailable')
    receipts = ResponseCache(tmp_path/'receipts.sqlite3')
    docs = [doc('D1'),doc('D2')]
    first = FakeClient()
    failed = build(docs,SPEC,first,FailingStore(),response_cache=receipts)
    assert failed['failed'] == 2 and first.calls == 1
    receipts.close()
    reopened = ResponseCache(tmp_path/'receipts.sqlite3')
    second = FakeClient()
    result = build(docs,SPEC,second,MemoryStore(),response_cache=reopened)
    assert result['succeeded'] == result['recovered'] == 2 and second.calls == 0
    assert reopened.get(replace(SPEC, preprocessing_version='v2'),docs[0]) is None
    reopened.close()


def test_auth_rejection_is_logged_once_without_charge(tmp_path):
    class AuthenticationFailure(Exception):
        status_code = 401
    sdk = SDK(error=AuthenticationFailure('never log this'))
    c = client(tmp_path,sdk)
    with pytest.raises(AuthenticationFailure):
        c.embed(['a','b'],dimensions=2)
    row = c.ledger.records()[0]
    assert sdk.calls == 1 and not row.ok and row.cost_usd == 0
    assert row.cost_source == 'rejected_request'
