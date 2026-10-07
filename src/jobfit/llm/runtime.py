"""Runtime client for the D-083 configuration (Sol matching, Luna fallback).

Same request adaptation as the evaluated runs (scripts/run_cp23_model_sweep.py,
SweepClient/SweepAdapter): temperature is left out where the endpoint does not
support it, max_tokens is clamped to the published output limit, and the dated
response ids are accepted. Rules come from a frozen file, not from the network,
and the chat timeout comes from the version file (240 s), not the 90 s default.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import yaml

from jobfit.config import REPO_ROOT, Settings
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.pricing import ModelPrice

RULES_FILE = REPO_ROOT / 'config/versions/route_rules_cp23_v1.json'


class _Adapter:
    def __init__(self, sdk, rules):
        self.sdk, self.rules = sdk, rules
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def with_options(self, **kwargs):
        return _Adapter(self.sdk.with_options(**kwargs), self.rules)

    def get(self, *args, **kwargs):
        return self.sdk.get(*args, **kwargs)

    def create(self, **kwargs):
        rule = self.rules.get(kwargs.get('model'))
        if rule:
            if not rule['temperature_supported']:
                kwargs.pop('temperature', None)
            if rule['min_output_limit']:
                kwargs['max_tokens'] = min(kwargs['max_tokens'], rule['min_output_limit'])
        return self.sdk.chat.completions.create(**kwargs)


class RuntimeClient(OpenRouterClient):
    def configure(self, models: dict) -> 'RuntimeClient':
        self.rules = {}
        for key, item in models.items():
            base = self.prices.get(key)
            price = ModelPrice(key, item['model_id'], item['ceiling_in'], item['ceiling_out'],
                               tuple(item['metadata']['response_aliases']), base.reasoning if base else None)
            self.prices[key] = self.prices[item['model_id']] = price
            self.rules[item['model_id']] = item['metadata']
        return self

    @property
    def sdk(self):
        return _Adapter(super().sdk, getattr(self, 'rules', {}))


def build_runtime_client(settings: Settings, config_path: str | Path, *, run_id: str = 'app',
                         rules_file: Path = RULES_FILE, sdk_client=None) -> RuntimeClient:
    cfg = yaml.safe_load(Path(config_path).read_text())
    rules = json.loads(Path(rules_file).read_text())['models']
    wanted = [m for m in (cfg['matching_model'], cfg.get('matching_fallback_model')) if m]
    missing = [m for m in wanted if m not in rules]
    if missing:
        raise ValueError(f'No frozen request rules for {missing}')
    client = RuntimeClient(settings, sdk_client=sdk_client, run_id=run_id,
                           chat_timeout_seconds=float(cfg['request_timeout_seconds']))
    return client.configure({m: rules[m] for m in wanted})
