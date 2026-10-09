"""Per-request ZDR routing of the public-beta runtime client (C1 decision). Offline, fake SDK.

Every chat and embedding request carries provider.data_collection = "deny" and provider.zdr = true,
on top of the frozen request (same messages, model, max_tokens and price ceilings). No fallback to
a non-ZDR endpoint and no raised price ceiling.
"""
import copy
import json
import time
import uuid

import pytest

from jobfit.live.deadlines import phase_window
from jobfit.live.reserved_client import BETA_CHAIN_PHASE, CallModel, OperationState, bind_reserved_client
from jobfit.live.runtime_client import (PublicBetaRuntimeClient, ZdrRoutingViolation, ZdrSdk,
                                        build_public_beta_client, enforce_zdr)
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.public_beta_bounds import DEFAULT_BETA_CONFIG, compute_public_beta_bounds
from jobfit.llm.runtime import build_runtime_client
from jobfit.recommend.service import RecommendConfig, analyze_job
from tests.test_cv_upload_pipeline import parsed
from tests.test_live_recommend_equivalence import answer as evidence_answer, extraction
from tests.test_live_unit import CONFIG, LUNA, SOL, Answer, FakeSDK, settings

MSGS = [{'role': 'user', 'content': 'masked CV text'}]


def chat(client):
    return client.chat_structured('deepseek-flash', MSGS, Answer, 'cv_parsing', max_tokens=1000)


def test_chat_requests_add_deny_and_zdr_and_keep_the_frozen_request(tmp_path):
    frozen_sdk, zdr_sdk = FakeSDK(), FakeSDK()
    chat(build_runtime_client(settings(tmp_path / 'a'), CONFIG, sdk_client=frozen_sdk))
    chat(build_public_beta_client(settings(tmp_path / 'b'), CONFIG, sdk_client=zdr_sdk))
    (frozen,), (zdr,) = frozen_sdk.calls, zdr_sdk.calls
    provider = zdr['extra_body']['provider']
    assert provider['zdr'] is True and provider['data_collection'] == 'deny'
    assert provider['max_price'] == frozen['extra_body']['provider']['max_price']          # ceiling unchanged
    assert provider['require_parameters'] is True
    expected = copy.deepcopy(frozen)
    expected['extra_body']['provider']['zdr'] = True
    assert zdr == expected                                     # nothing else differs from the frozen request


def test_embedding_requests_add_deny_and_zdr_and_keep_the_frozen_request(tmp_path):
    frozen_sdk, zdr_sdk = FakeSDK(), FakeSDK()
    OpenRouterClient(settings(tmp_path / 'a'), sdk_client=frozen_sdk).embed(
        ['masked CV text'], model='qwen3-embedding-8b', task='cv_query_embedding', dimensions=4)
    build_public_beta_client(settings(tmp_path / 'b'), CONFIG, sdk_client=zdr_sdk).embed(
        ['masked CV text'], model='qwen3-embedding-8b', task='cv_query_embedding', dimensions=4)
    (frozen,), (zdr,) = frozen_sdk.calls, zdr_sdk.calls
    expected = copy.deepcopy(frozen)
    expected['extra_body']['provider']['zdr'] = True
    assert zdr == expected
    assert zdr['extra_body']['provider']['data_collection'] == 'deny'
    assert zdr['extra_body']['provider']['max_price'] == frozen['extra_body']['provider']['max_price']


def test_the_reserved_search_embedding_goes_through_zdr(tmp_path):
    bounds = compute_public_beta_bounds()
    sdk = FakeSDK()
    inner = build_public_beta_client(settings(tmp_path), CONFIG, run_id='op', sdk_client=sdk)
    op = OperationState('idem:' + str(uuid.uuid4()), 'search', bounds.search_max,
                        phase_window('search', bounds, 240.0), anchor_mono=time.monotonic())
    model = CallModel(bounds, CONFIG, phase_config=DEFAULT_BETA_CONFIG, chain_phase=BETA_CHAIN_PHASE)
    client = bind_reserved_client(inner, op, model, tmp_path / 'ledger.jsonl')
    assert client.embed(['masked CV text ' * 50], model='qwen3-embedding-8b', task='cv_query_embedding',
                        dimensions=4)
    (call,) = sdk.calls
    assert call['extra_body']['provider']['zdr'] is True and op.fatal_refusal is None


def test_every_matching_call_including_the_luna_fallback_is_zdr(tmp_path):
    sdk = FakeSDK(evidence_answer)
    client = build_public_beta_client(settings(tmp_path), CONFIG, sdk_client=sdk)
    result = analyze_job(parsed(), 'J04', 1, *extraction('J04'), client=client, fallback_client=None,
                         config=RecommendConfig.from_yaml(CONFIG))      # J04: Sol fails, Luna answers
    assert result.used_fallback and {k['model'] for k in sdk.calls} == {SOL, LUNA}
    assert all(k['extra_body']['provider']['zdr'] is True and k['extra_body']['provider']['data_collection'] == 'deny'
               for k in sdk.calls)


def test_no_zdr_endpoint_fails_closed_without_a_non_zdr_retry(tmp_path):
    def no_endpoint(kw):
        raise RuntimeError('404 No endpoints found matching your data policy')
    sdk = FakeSDK(no_endpoint)
    client = build_public_beta_client(settings(tmp_path), CONFIG, sdk_client=sdk)
    with pytest.raises(Exception):
        chat(client)
    assert len(sdk.calls) == 1 and sdk.calls[0]['extra_body']['provider']['zdr'] is True


@pytest.mark.parametrize('provider', [{'data_collection': 'allow'}, {'zdr': False}, {'zdr': 'yes'}])
def test_weaker_routing_is_refused_before_the_sdk(provider):
    request = {'model': 'm', 'extra_body': {'provider': provider}}
    before = json.dumps(request, sort_keys=True)
    with pytest.raises(ZdrRoutingViolation):
        enforce_zdr(request)
    assert json.dumps(request, sort_keys=True) == before          # the caller's request is not mutated


def test_the_sdk_facade_keeps_zdr_after_with_options_and_passes_get_through(tmp_path):
    sdk = FakeSDK()
    sdk.get = lambda *a, **kw: {'data': {'ok': True}}
    facade = build_public_beta_client(settings(tmp_path), CONFIG, sdk_client=sdk).sdk
    assert isinstance(facade, ZdrSdk) and isinstance(facade.with_options(max_retries=0), ZdrSdk)
    assert facade.get('/key', cast_to=dict) == {'data': {'ok': True}}
    assert isinstance(build_public_beta_client(settings(tmp_path), CONFIG, sdk_client=sdk), PublicBetaRuntimeClient)
    facade.with_options(max_retries=0).chat.completions.create(model=SOL, messages=MSGS, max_tokens=5)
    assert sdk.calls[-1]['extra_body']['provider'] == {'data_collection': 'deny', 'zdr': True}
