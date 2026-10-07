"""Read-only inventory of original v1.4 cases across preserved run versions.

Operational QA outcomes are not extraction F1 or human-approved alignment.
The rejected GPT transport observation is retained separately from its v6 draft.
"""
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from jobfit.eval.stage2_extraction import ROUND1

BASE = 'cp23_stage2_round1_extraction_20261003_'
V4, V5, V6, V7 = BASE + 'v4', BASE + 'v5_continuation', BASE + 'v6_route_repair', BASE + 'v7_remaining_cases'


def summarize(rows, records):
    result = []
    for model in ROUND1:
        cases = [r for r in rows if r['model'] == model]
        ids = {r['model_id'] for r in cases}
        usage = [r for r in records if r['model'] in ids and not r.get('cached')]
        costs = [Decimal(str(r['cost_usd'])) for r in usage]
        if any(not x.is_finite() or x < 0 for x in costs):
            raise ValueError('Invalid inventory ledger cost')
        result.append({'model': model, 'planned_cases': len(cases),
                       'attempted_cases': sum(r['process_status'] != 'not_attempted' for r in cases),
                       'process_successes': sum(r['process_status'] == 'done' for r in cases),
                       'process_failures': sum(r['process_status'] == 'failed' for r in cases),
                       'source_qa_all_pass': sum(r['source_qa_status'] == 'pass' for r in cases),
                       'source_qa_fail_or_uncertain': sum(r['source_qa_status'] == 'fail_or_uncertain' for r in cases),
                       'source_qa_pending': sum(r['source_qa_status'] == 'pending' for r in cases),
                       'checks': {key: dict(Counter(r.get('source_checks', {}).get(key, 'not_available') for r in cases))
                                  for key in ('quotes', 'coverage', 'grouping', 'qualifiers', 'importance')},
                       'attempts_including_repairs': sum(r.get('attempts', 0) for r in cases),
                       'ledger_calls_including_rejections': len(usage),
                       'ledger_cost_usd': str(sum(costs, Decimal(0))),
                       'extraction_f1': None, 'alignment_status': 'candidate_specific_review_pending'})
    return result


def inventory(root):
    root = Path(root)
    read = lambda p: json.loads((root / p).read_text())
    hash_file = lambda p: hashlib.sha256((root / p).read_bytes()).hexdigest()
    plan_path = 'evals/results/' + V4 + '_preflight.json'
    plan = read(plan_path)
    inputs = {plan_path: hash_file(plan_path)}
    observations = {}
    extra_rejections = []
    for run in (V4, V5, V6, V7):
        state_path = 'reports/quality_probe/' + run + '.json'
        if not (root / state_path).exists():
            continue
        state = read(state_path)
        inputs[state_path] = hash_file(state_path)
        for i, durable in enumerate(state['results'], 1):
            path = f'evals/results/{run}_{i:02d}.json'
            r = read(path)
            inputs[path] = hash_file(path)
            base = dict(durable); check = base.pop('operational_check', None)
            if base != r:
                raise ValueError('Result differs from durable state')
            if check:
                check_path = f'evals/results/{run}_{i:02d}_semantic_check.json'
                receipt = read(check_path)
                inputs[check_path] = hash_file(check_path)
                if any(check.get(k) != v for k, v in receipt.items()):
                    raise ValueError('Source QA receipt differs from durable state')
            content = dict(r); expected = content.pop('result_sha256')
            if hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest() != expected:
                raise ValueError('Result semantic identity changed')
            if run == V5 and r['job_id'] == 'gpt-6-luna/F00332':
                extra_rejections.append({'stage_id': r['job_id'], 'status': r['status'],
                                         'error_code': r['error_code'], 'result_file': path,
                                         'disposition': 'terminal rejected request retained; adapted v6 dispatch separately identified'})
                continue
            if r['job_id'] in observations:
                raise ValueError('Duplicate model/JD observation would bias comparison')
            checks = check.get('checks') if check else None
            process_check = None
            if r['status'] == 'failed':
                process_path = f'evals/results/{run}_{i:02d}_process_check.json'
                if not check:
                    process_check = read(process_path)
                    inputs[process_path] = hash_file(process_path)
                else:
                    process_check = check
                if (process_check.get('job_id') != r['job_id'] or process_check.get('result_sha256') != r['result_sha256']
                        or process_check.get('disposition') != 'retain_failed_case_no_retry'
                        or process_check.get('error_code') != r['error_code']):
                    raise ValueError('Failed-case receipt does not identify retained process failure')
            observations[r['job_id']] = dict(r, result_file=path,
                source_checks=checks, source_qa_status=('pass' if all(v == 'pass' for v in checks.values())
                    else 'fail_or_uncertain') if checks else ('process_failed' if r['status'] == 'failed' else 'pending'),
                source_notes=check['notes'] if check else (process_check['notes'] if process_check else None))
    rows = []
    for stage in plan['stages']:
        r = observations.pop(stage['stage_id'], None)
        if r and (r['model_id'] != stage['model_id'] or r['source_sha256'] != stage['source_sha256']):
            raise ValueError('Observation source or model differs from frozen case')
        rows.append({'stage_id': stage['stage_id'], 'model': stage['model'], 'model_id': stage['model_id'],
                     'job_id': stage['job_id'], 'process_status': r['status'] if r else 'not_attempted',
                     'attempts': r.get('attempts', 0) if r else 0,
                     'source_qa_status': r['source_qa_status'] if r else 'not_attempted',
                     'source_checks': (r.get('source_checks') or {}) if r else {},
                     'source_notes': r.get('source_notes') if r else None,
                     'unit_count': len(r['extraction']['units']) if r and r.get('extraction') else None,
                     'result_file': r['result_file'] if r else None,
                     'result_sha256': r['result_sha256'] if r else None,
                     'error_code': r.get('error_code') if r else None,
                     'latency_ms': r.get('latency_ms') if r else None,
                     'alignment_status': 'pending', 'extraction_f1': None})
    if observations:
        raise ValueError('Unexpected unplanned comparison observation')
    ledger_path = 'reports/usage/usage_ledger.jsonl'
    inputs[ledger_path] = hash_file(ledger_path)
    ledger = [json.loads(line) for line in (root / ledger_path).read_text().splitlines()]
    selected = [r for r in ledger if r['run_id'] in {V4, V5, V6, V7}]
    complete = all((r['process_status'] == 'done' and r['source_qa_status'] in {'pass', 'fail_or_uncertain'}) or (r['process_status'] == 'failed' and r['source_qa_status'] == 'process_failed') for r in rows)
    return {'schema_version': 'cp23-stage2-v14-observation-inventory-v1',
            'status': 'extraction_collection_complete_with_retained_failures' if complete else 'partial_collection',
            'scope': 'four original candidates x same seven development JDs, fixed experimental v1.4',
            'rows': rows, 'summary': summarize(rows, selected), 'additional_process_observations': extra_rejections,
            'input_hashes': inputs, 'model_winner': None, 'configuration_selected': False,
            'extraction_f1': None, 'evidence_macro_f1': None,
            'limitations': ['Source QA is delegated, not new human-approved candidate alignment.',
                            'GPT-only unsupported temperature omission; provider default differs from explicit0 for other candidates.',
                            'Retained terminal DeepSeek/F00332 v4 case and v5 remaining DeepSeek cases were collected earlier.',
                            'No paid evidence matching or reference-model comparison in this extraction scope.',
                            'D-029 model selection requires verified extraction/evidence metrics and safety judgments.'],
            'test_access': False, 'gold_written': False}
