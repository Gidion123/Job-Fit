"""Runtime client: frozen rules, 240 s timeout, same adaptation as the sweep. No network."""
from types import SimpleNamespace

from jobfit.config import REPO_ROOT, get_settings
from jobfit.llm.runtime import build_runtime_client

V3 = REPO_ROOT / 'config/versions/pipeline_cp23_provisional_v3_20261004.yaml'


class FakeSDK:
    def __init__(self):
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def with_options(self, **kw):
        return self

    def create(self, **kw):
        self.calls.append(kw)
        return kw


def test_runtime_client_uses_v3_timeout_and_frozen_rules():
    sdk = FakeSDK()
    client = build_runtime_client(get_settings(), V3, sdk_client=sdk)
    assert client.chat_timeout_seconds == 240.0
    assert client._price('gpt-6-sol').model_id == 'openai/gpt-6-sol'
    assert 'openai/gpt-6-sol-20260922' in client._price('gpt-6-sol').response_model_aliases
    client.sdk.chat.completions.create(model='openai/gpt-6-sol', temperature=0.0, max_tokens=500_000, messages=[])
    assert 'temperature' not in sdk.calls[0] and sdk.calls[0]['max_tokens'] == 128000
    client.sdk.chat.completions.create(model='deepseek/deepseek-v4.1-flash', temperature=0.0, max_tokens=10, messages=[])
    assert sdk.calls[1]['temperature'] == 0.0      # models without a rule are untouched
