"""Offline plan for remaining fixed v1.4 extraction cases after a recorded failure.

The terminal first case is an external, explicitly failed comparison observation.
This protocol continues only after a source-semantic failure has been recorded;
it never repairs or silently treats that failed case as a true positive.
"""
from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path

from jobfit.eval.stage2_extraction import Stage2ExtractionClient, Stage2ExtractionSession, build_plan


V4_RUN = 'cp23_stage2_round1_extraction_20261003_v4'
V5_RUN = 'cp23_stage2_round1_extraction_20261003_v5_continuation'
V4_PLAN = 'evals/results/cp23_stage2_round1_extraction_20261003_v4_preflight.json'
V4_RESULT = 'evals/results/cp23_stage2_round1_extraction_20261003_v4_01.json'
V4_CHECK = 'evals/results/cp23_stage2_round1_extraction_20261003_v4_01_semantic_check.json'
V4_STATE = 'reports/quality_probe/cp23_stage2_round1_extraction_20261003_v4.json'


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_continuation_plan(root: Path, sources: dict[str, str]) -> dict:
    root = Path(root)
    old_plan = json.loads((root/V4_PLAN).read_text())
    rebuilt = build_plan(root, sources, run_id=V4_RUN,
                         prompt_file='prompts/jd_extraction_v1_4_experimental.md')
    if old_plan != rebuilt:
        raise ValueError('Frozen v1.4 source/configuration plan changed')
    state = json.loads((root/V4_STATE).read_text())
    prior = json.loads((root/V4_RESULT).read_text())
    check = json.loads((root/V4_CHECK).read_text())
    if state.get('status') != 'stopped_semantic_issue' or len(state.get('results', [])) != 1:
        raise ValueError('Prior v1.4 stage is not a single terminal semantic failure')
    state_result = dict(state['results'][0])
    operational_check = state_result.pop('operational_check', None)
    if state.get('fingerprint') != sha(root/V4_PLAN) or state_result != prior:
        raise ValueError('Prior state or result differs from frozen plan')
    if prior.get('job_id') != old_plan['stages'][0]['stage_id'] or prior.get('status') != 'done':
        raise ValueError('Prior failed case identity is incompatible')
    if prior.get('result_sha256') != check.get('result_sha256'):
        raise ValueError('Prior semantic check does not identify the result')
    if any(v not in {'pass', 'fail', 'uncertain'} for v in check.get('checks', {}).values()) or all(v == 'pass' for v in check['checks'].values()):
        raise ValueError('Prior result has no semantic failure to carry forward')
    if not operational_check or operational_check.get('result_sha256') != check['result_sha256'] or operational_check.get('checks') != check['checks']:
        raise ValueError('Prior durable semantic check differs from source receipt')
    remaining = old_plan['stages'][1:]
    if len(remaining) != 27 or len({x['stage_id'] for x in remaining}) != 27:
        raise ValueError('Frozen remaining comparison scope is not 27 unique stages')
    upper = sum((Decimal(str(s['conservative_upper_usd'])) for s in remaining), Decimal('0'))
    return {
        'schema_version': 'cp23-stage2-continuation-plan-v1',
        'run_id': V5_RUN,
        'scope': 'development-only remaining 27 v1.4 extraction cases, four original candidates/seven original JDs',
        'protocol': 'same v1.4 prompt/source/model/schema; source-semantic failures are recorded as failures and do not end the whole comparison; one stage and source review at a time',
        'first_case_disposition': 'external_terminal_semantic_failure; never replay or count as TP',
        'prior_case': {'stage_id': old_plan['stages'][0]['stage_id'],
                       'result_file': V4_RESULT, 'result_sha256': sha(root/V4_RESULT),
                       'semantic_check_file': V4_CHECK, 'semantic_check_sha256': sha(root/V4_CHECK),
                       'durable_state_sha256': sha(root/V4_STATE)},
        'source_hashes': {**old_plan['source_hashes'], 'v4_plan': sha(root/V4_PLAN)},
        'stages': remaining,
        'stage_count': len(remaining),
        'maximum_calls_including_repairs': len(remaining)*2,
        'conservative_upper_usd': str(upper),
        'paid_approval_required': True,
        'execution_status': 'preflight_only',
        'no_gold_answers_in_model_payload': True,
        'no_candidate_winner': True,
        'stop_conditions': ['changed source/config/prompt/guideline/reference or prior failed-case receipt',
                            'uncertain transport charge or unresolved budget reservation',
                            'aggregate cap or project hard stop insufficient',
                            'untrusted process/schema failure after one repair',
                            'source check missing before next stage'],
        'semantic_failure_policy': 'record failed source-semantic case and continue to next frozen stage only after explicit receipt; never substitute a case or turn it into a TP',
    }


class Stage2ComparisonSession(Stage2ExtractionSession):
    """Continue after a fully recorded semantic failure, not after transport uncertainty."""
    def record_check(self, check):
        super().record_check(check)
        if self.data['status'] == 'stopped_semantic_issue':
            if self.data.get('transport_uncertain') or self.data.get('reservations'):
                return
            self.data.setdefault('semantic_failures', []).append(self.data['results'][-1]['job_id'])
            self.data['status'] = ('complete' if len(self.data['results']) == len(self.data['jobs']) else 'ready')
            self.save()


class Stage2ComparisonClient(Stage2ExtractionClient):
    """Retain each typed draft separately before downstream validation/repair."""
    def chat_structured(self, model, messages, output_model, task, max_tokens=2000, temperature=0):
        out = super().chat_structured(model, messages, output_model, task, max_tokens, temperature)
        stage_id = self.session.data['active_job']
        attempt = self.session.data['stage_attempts'][stage_id]
        payload = out.model_dump(mode='json')
        self.session.data.setdefault('typed_attempt_outputs', []).append({
            'stage_id': stage_id, 'attempt': attempt, 'output': payload,
            'output_sha256': hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
            'status': 'typed_draft_not_source_approved',
        })
        self.session.save()
        return out
