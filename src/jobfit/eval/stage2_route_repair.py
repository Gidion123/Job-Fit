"""Approved experimental GPT request adaptation; never change frozen v5 state.

Omit unsupported temperature only for GPT Luna and accept its published dated ID.
Privacy, prices, source, schema, prompt and per-case source review are unchanged.
"""
from dataclasses import replace
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from jobfit.eval.stage2_continuation import Stage2ComparisonSession, build_continuation_plan
from jobfit.llm.client import OpenRouterClient

RUN_ID = 'cp23_stage2_round1_extraction_20261003_v6_route_repair'
PROPOSAL = 'evals/results/cp23_stage2_v6_route_repair_proposal_20261003_v1.json'
V5_STATE = 'reports/quality_probe/cp23_stage2_round1_extraction_20261003_v5_continuation.json'
V5_ID = 'cp23_stage2_round1_extraction_20261003_v5_continuation'
GPT_ID = 'openai/gpt-6-luna'
GPT_ALIAS = 'openai/gpt-6-luna-20260922'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_route_plan(root, sources):
    root = Path(root)
    proposal = json.loads((root / PROPOSAL).read_text())
    old = build_continuation_plan(root, sources)
    prior = json.loads((root / V5_STATE).read_text())
    if (sha(root / V5_STATE) != proposal['predecessor_terminal_state_sha256']
            or prior['status'] != 'stopped_process_failure'
            or prior.get('reservations') or prior.get('transport_uncertain')
            or len(prior['results']) != 7 or prior['results'][-1]['job_id'] != 'gpt-6-luna/F00332'
            or prior['results'][-1].get('error_code') != 'NotFoundError'):
        raise ValueError('Terminal rejected predecessor changed or has an unsettled request')
    if any(not r.get('operational_check') for r in prior['results'][:6]):
        raise ValueError('Predecessor semantic checks are incomplete')
    if proposal['stages'] != old['stages'][6:]:
        raise ValueError('Remaining original 21 source/model cases changed')
    metadata = root / proposal['metadata_file']
    if sha(metadata) != proposal['metadata_sha256']:
        raise ValueError('Route metadata changed')
    endpoints = json.loads(metadata.read_text())[GPT_ID]['endpoints']
    if not endpoints or any('temperature' in e['supported_parameters'] for e in endpoints):
        raise ValueError('GPT parameter adaptation does not match inspected metadata')
    upper = sum((Decimal(str(s['conservative_upper_usd'])) for s in proposal['stages']), Decimal(0))
    return dict(proposal, schema_version='cp23-stage2-route-repair-plan-v1',
                status='frozen_preflight', execution_status='preflight_only',
                conservative_upper_usd=str(upper),
                source_hashes={**old['source_hashes'], 'proposal': sha(root / PROPOSAL),
                               'route_adapter': sha(root / 'src/jobfit/eval/stage2_route_repair.py'),
                               'runner': sha(root / 'scripts/run_cp23_stage2_route_repair.py')},
                paid_approval_required=True, no_gold_answers_in_model_payload=True,
                no_candidate_winner=True)


class TemperatureAdapter:
    """SDK adapter: no relaxed provider policy or automatic transport retries."""
    def __init__(self, sdk):
        self.sdk = sdk
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def with_options(self, **kwargs):
        return TemperatureAdapter(self.sdk.with_options(**kwargs))

    def get(self, *args, **kwargs):
        return self.sdk.get(*args, **kwargs)

    def create(self, **kwargs):
        if kwargs.get('model') == GPT_ID:
            kwargs.pop('temperature', None)
        return self.sdk.chat.completions.create(**kwargs)


class RouteClient(OpenRouterClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        price = replace(self.prices[GPT_ID], response_model_aliases=(GPT_ALIAS,))
        self.prices[GPT_ID] = self.prices['gpt-6-luna'] = price

    @property
    def sdk(self):
        return TemperatureAdapter(super().sdk)


class RouteSession(Stage2ComparisonSession):
    """One cumulative ceiling for both v5 and v6, including rejected requests."""
    def spent(self):
        costs = [Decimal(str(r.cost_usd)) for r in self.ledger.records()
                 if r.run_id in {self.data['run_id'], V5_ID} and not r.cached]
        if any(not x.is_finite() or x < 0 for x in costs):
            raise ValueError('Invalid cumulative ledger cost')
        return sum(costs, Decimal(0))
