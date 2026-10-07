"""Plan-bound matcher benchmark; no extraction, gold edits or automatic selection."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from jobfit.llm.budget import BudgetExceeded
from jobfit.llm.client import strict_schema
from jobfit.llm.probe import ProbeClient, ProbeSession


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class MatchingSession(ProbeSession):
    MAX_CEILING = Decimal('1.85')

    def finish_matching(self, result):
        if self.data['status'] != 'running' or result['stage_id'] != self.data['active_job']:
            raise ValueError('Unexpected matching result')
        if self.data.get('reservations') or self.data.get('transport_uncertain'):
            self.data['status'] = 'stopped_uncertain_cost'
            self.save()
            return
        self.data['results'].append(result)
        # A settled invalid output is an observation, never a negative label or a retry.
        self.data['status'] = 'complete' if len(self.data['results']) == len(self.data['jobs']) else 'ready'
        self.save()


class MatchingClient(ProbeClient):
    def __init__(self, client, session, stage):
        super().__init__(client, session)
        self.stage = stage

    def chat_structured(self, model, messages, output_model, task, max_tokens=2000, temperature=0):
        s = self.session
        if s.data['status'] != 'running' or s.data['active_job'] != self.stage['stage_id']:
            raise BudgetExceeded('Matching stage is not running')
        if model != self.stage['model'] or task != 'evidence_matching' or temperature != 0:
            raise ValueError('Request differs from matching plan')
        counts = s.data.setdefault('stage_attempts', {})
        attempt = counts.get(self.stage['stage_id'], 0)
        if attempt >= 2 or max_tokens != self.stage['output_token_upper_per_attempt']:
            raise BudgetExceeded('Matching attempt/output limit')
        size = len(json.dumps(messages, ensure_ascii=False).encode()) + len(json.dumps(strict_schema(output_model.model_json_schema())).encode()) + 512
        limit = self.stage['first_input_token_upper'] if attempt == 0 else self.stage['repair_input_token_upper']
        if size > limit:
            raise BudgetExceeded('Matching input exceeds plan')
        counts[self.stage['stage_id']] = attempt + 1
        s.save()
        before = len([r for r in self.client.ledger.records() if r.run_id == self.client.run_id])
        try:
            out = super().chat_structured(model, messages, output_model, task, max_tokens, temperature)
            payload = out.model_dump(mode='json')
            s.data.setdefault('typed_attempt_outputs', []).append({
                'stage_id': self.stage['stage_id'], 'attempt': attempt+1, 'output': payload,
                'status': 'typed_draft_not_semantically_approved'})
            s.save()
            return out
        finally:
            rows = [r for r in self.client.ledger.records() if r.run_id == self.client.run_id]
            # Crash/no receipt and ambiguous transport cannot trigger a repair or next stage.
            if len(rows) <= before or rows[-1].cost_source == 'uncertain_upper_bound':
                s.data['transport_uncertain'] = True
                s.data['status'] = 'stopped_uncertain_cost'
                s.save()


def require_approval(plan_path, receipt_path):
    receipt = json.loads(Path(receipt_path).read_text())
    if receipt.get('approved_by') != 'Dion' or receipt.get('plan_sha256') != sha(plan_path) or receipt.get('ceiling_usd') != '1.85':
        raise ValueError('Exact separate matching approval required')
    return receipt
