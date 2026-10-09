"""Public-beta runtime client: per-request zero-data-retention routing (CP3, D-051 / C1 decision).

Every provider request this client sends, chat completions and embeddings alike, carries
``provider.data_collection = "deny"`` and ``provider.zdr = true`` in addition to the frozen client's
own routing controls (``require_parameters``, the per-model ``max_price`` ceilings), which are kept
unchanged. The guarantee is application-level and testable; an account-level OpenRouter ZDR setting
can be added later as defence in depth but is not relied on.

No fallback: if no endpoint satisfies the frozen model, routing, price ceiling and ZDR together,
the provider refuses and the frozen client fails the call; nothing retries without ZDR and no
price ceiling is raised. A request that already asks for weaker routing is refused before the SDK.

It is also embedding-capable: the frozen ``RuntimeClient`` SDK adapter exposes chat only, so the
D-103 ``search`` query embedding goes to the raw SDK's embeddings endpoint, through the same ZDR
enforcement. Nothing frozen is edited.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import yaml

from jobfit.config import Settings
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.runtime import RULES_FILE, RuntimeClient

ZDR_PROVIDER = {'data_collection': 'deny', 'zdr': True}


class ZdrRoutingViolation(RuntimeError):
    """A request asked for routing weaker than deny + ZDR; it is never sent."""


def enforce_zdr(kwargs: dict) -> dict:
    """A copy of the request kwargs with deny + ZDR added; the frozen routing controls are kept."""
    extra = dict(kwargs.get('extra_body') or {})
    provider = dict(extra.get('provider') or {})
    if provider.get('data_collection', 'deny') != 'deny' or provider.get('zdr', True) is not True:
        raise ZdrRoutingViolation('weaker provider routing requested')
    provider.update(ZDR_PROVIDER)
    extra['provider'] = provider
    return {**kwargs, 'extra_body': extra}


class ZdrSdk:
    """SDK facade: chat through the frozen request adapter, embeddings through the raw SDK; ZDR on both."""

    def __init__(self, chat_sdk, raw_sdk):
        self._chat_sdk, self._raw_sdk = chat_sdk, raw_sdk
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._chat_create))
        self.embeddings = SimpleNamespace(create=self._embed_create)

    def with_options(self, **kwargs) -> 'ZdrSdk':
        raw = self._raw_sdk.with_options(**kwargs) if hasattr(self._raw_sdk, 'with_options') else self._raw_sdk
        return ZdrSdk(self._chat_sdk.with_options(**kwargs), raw)

    def get(self, *args, **kwargs):
        return self._raw_sdk.get(*args, **kwargs)

    def _chat_create(self, **kwargs):
        return self._chat_sdk.chat.completions.create(**enforce_zdr(kwargs))

    def _embed_create(self, **kwargs):
        return self._raw_sdk.embeddings.create(**enforce_zdr(kwargs))


class PublicBetaRuntimeClient(RuntimeClient):
    """The frozen runtime client (same request adaptation, prices and guard) with ZDR routing."""

    @property
    def sdk(self):
        return ZdrSdk(super().sdk, OpenRouterClient.sdk.fget(self))


def build_public_beta_client(settings: Settings, config_path, *, run_id: str = 'app', rules_file=RULES_FILE,
                             sdk_client=None) -> PublicBetaRuntimeClient:
    """Same construction as the frozen ``build_runtime_client`` (rules, timeout, prices), ZDR client class."""
    cfg = yaml.safe_load(Path(config_path).read_text())
    rules = json.loads(Path(rules_file).read_text())['models']
    wanted = [m for m in (cfg['matching_model'], cfg.get('matching_fallback_model')) if m]
    missing = [m for m in wanted if m not in rules]
    if missing:
        raise ValueError(f'No frozen request rules for {missing}')
    client = PublicBetaRuntimeClient(settings, sdk_client=sdk_client, run_id=run_id,
                                     chat_timeout_seconds=float(cfg['request_timeout_seconds']))
    return client.configure({m: rules[m] for m in wanted})
