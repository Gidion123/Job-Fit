"""Proposed fault-isolated continuation; requires separate protocol approval.

Preserve terminal v6 and its failed Gemini case. No request adaptation or retry
of a failed case. Only a settled failure receipt permits the next original case.
"""
from decimal import Decimal
import json
from pathlib import Path
from jobfit.eval.stage2_route_repair import RouteSession, build_route_plan, sha, V5_ID, RUN_ID as V6_ID

RUN_ID = 'cp23_stage2_round1_extraction_20261003_v7_remaining_cases'
PROPOSAL = 'evals/results/cp23_stage2_v7_remaining_cases_proposal_20261003_v1.json'


def build_remaining_plan(root, sources):
    root = Path(root)
    proposal = json.loads((root / PROPOSAL).read_text())
    old = build_route_plan(root, sources)
    state_path = root / proposal['predecessor_file']
    state = json.loads(state_path.read_text())
    if (sha(state_path) != proposal['predecessor_sha256']
            or state['status'] != 'stopped_process_failure'
            or state.get('reservations') or state.get('transport_uncertain')
            or len(state['results']) != 12
            or state['results'][-1]['job_id'] != 'gemini-3.5-flash-lite/F00815'
            or state['results'][-1]['error_code'] != 'BadRequestError'
            or any(not r.get('operational_check') for r in state['results'][:-1])):
        raise ValueError('Terminal predecessor changed or has unresolved observations')
    if proposal['stages'] != old['stages'][12:]:
        raise ValueError('Remaining original nine cases changed')
    ledger = [json.loads(line) for line in (root / 'reports/usage/usage_ledger.jsonl').read_text().splitlines()]
    prior = [r for r in ledger if r['run_id'] == V6_ID and not r['cached']]
    if (len(prior) != sum(state['stage_attempts'].values())
            or any(r['cost_source'] == 'uncertain_upper_bound' for r in prior)
            or prior[-1]['cost_source'] != 'rejected_request'):
        raise ValueError('Predecessor attempt charges are not settled')
    return dict(proposal, schema_version='cp23-stage2-remaining-cases-plan-v1',
        status='frozen_preflight', execution_status='preflight_only', paid_approval_required=True,
        source_hashes={**old['source_hashes'], 'v7_proposal': sha(root / PROPOSAL),
            'v6_terminal_state': sha(state_path),
            'v7_session': sha(root / 'src/jobfit/eval/stage2_remaining_cases.py'),
            'v7_runner': sha(root / 'scripts/run_cp23_stage2_remaining_cases.py')})


class RemainingSession(RouteSession):
    def spent(self):
        costs = [Decimal(str(r.cost_usd)) for r in self.ledger.records()
                 if r.run_id in {self.data['run_id'], V5_ID, V6_ID} and not r.cached]
        if any(not x.is_finite() or x < 0 for x in costs):
            raise ValueError('Invalid cumulative ledger cost')
        return sum(costs, Decimal(0))

    def record_check(self, check):
        if self.data['status'] != 'stopped_process_failure':
            return super().record_check(check)
        last = self.data['results'][-1]
        if (check.get('job_id') != last['job_id']
                or check.get('result_sha256') != last['result_sha256']
                or check.get('error_code') != last.get('error_code')
                or check.get('disposition') != 'retain_failed_case_no_retry'
                or not check.get('notes') or not check.get('checked_by')):
            raise ValueError('Failure receipt must identify the exact failed result')
        records = [r for r in self.ledger.records() if r.run_id == self.data['run_id'] and not r.cached]
        if (self.data.get('reservations') or self.data.get('transport_uncertain')
                or len(records) != sum(self.data.get('stage_attempts', {}).values())
                or any(r.cost_source == 'uncertain_upper_bound' for r in records)):
            raise ValueError('Failure has an unsettled attempt or uncertain charge')
        last['operational_check'] = dict(check, human_annotation_approval=False,
                                         alignment_status='pending', checks=None)
        self.data.setdefault('process_failures', []).append(last['job_id'])
        self.data['status'] = 'complete' if len(self.data['results']) == len(self.data['jobs']) else 'ready'
        self.save()
