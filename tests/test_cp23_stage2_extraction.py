"""Stage-2 preflight and paid-dispatch boundaries use no network or API key."""
import importlib.util
import json
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import BaseModel

from jobfit.config import REPO_ROOT
from jobfit.eval.stage2_extraction import build_plan, Stage2ExtractionClient, Stage2ExtractionSession, ROUND1
from jobfit.llm.budget import BudgetExceeded, BudgetGuard
from jobfit.llm.ledger import UsageLedger, UsageRecord
from jobfit.llm.pricing import load_prices
from scripts.run_batch_extraction import development_sources

spec = importlib.util.spec_from_file_location('stage2_cli', REPO_ROOT/'scripts/run_cp23_stage2_extraction.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


def sources():
    m = json.loads((REPO_ROOT/'evals/results/cp23_stage1_case_candidates_20261003_v4.json').read_text())
    return {r['job_id']: r['text'] for r in development_sources([x['job_id'] for x in m['cases']])}


def test_preflight_fixes_exact_cases_models_attempts_and_gates():
    p = build_plan(REPO_ROOT, sources(), run_id='offline-test')
    assert p['stage_count'] == 28 and p['maximum_calls_including_repairs'] == 56
    assert {s['model'] for s in p['stages']} == set(ROUND1)
    assert len({s['job_id'] for s in p['stages']}) == 7
    assert all(s['repair_input_token_upper'] > s['first_input_token_upper'] for s in p['stages'])
    assert all(s['repair_input_token_upper'] <= 100_000 for s in p['stages'])
    assert p['no_gold_answers_in_model_payload'] is True and p['execution_status'] == 'preflight_only'
    assert float(p['conservative_upper_usd']) > 1


def test_new_prompt_is_separately_fingerprinted_and_does_not_change_scope():
    source = sources()
    old = build_plan(REPO_ROOT, source, run_id='old-protocol')
    new = build_plan(REPO_ROOT, source, run_id='new-protocol',
                     prompt_file='prompts/jd_extraction_v1_4_experimental.md')
    assert old['source_hashes']['jd_prompt'] != new['source_hashes']['jd_prompt']
    assert [(s['model'], s['job_id']) for s in old['stages']] == [(s['model'], s['job_id']) for s in new['stages']]
    assert new['prompt_status'] == 'experimental_not_default_or_selected'
    assert new['conservative_upper_usd'] != old['conservative_upper_usd']


def test_changed_source_or_scope_cannot_reuse_plan():
    s = sources()
    first = next(iter(s))
    s[first] += ' changed'
    with pytest.raises(ValueError, match='source changed'):
        build_plan(REPO_ROOT, s, run_id='offline-test')
    s = sources()
    s.pop(first)
    with pytest.raises(ValueError, match='seven'):
        build_plan(REPO_ROOT, s, run_id='offline-test')


def test_paid_approval_requires_exact_run_plan_and_full_bound(tmp_path):
    plan = build_plan(REPO_ROOT, sources(), run_id=cli.RUN_ID)
    receipt = {'decision': 'approved', 'approved_by': 'Dion', 'scope': cli.RUN_ID,
               'plan_sha256': 'f'*64, 'aggregate_cap_usd': '3.20'}
    p = tmp_path/'approval.json'
    p.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match='match frozen'):
        cli.approved_receipt(p, plan, plan_sha256='a'*64)
    receipt['plan_sha256'] = 'a'*64
    receipt['aggregate_cap_usd'] = '1.00'
    p.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match='conservative batch'):
        cli.approved_receipt(p, plan, plan_sha256='a'*64)
    receipt['aggregate_cap_usd'] = '3.20'
    p.write_text(json.dumps(receipt))
    assert cli.approved_receipt(p, plan, plan_sha256='a'*64) == Decimal('3.20')


class SmallWire(BaseModel):
    value: int


class FakeClient:
    run_id = 'fake-comparison'
    def __init__(self, ledger):
        self.ledger = ledger
        self.prices = load_prices(REPO_ROOT/'config/models_v1.yaml')
        self.guard = BudgetGuard(ledger, cap_usd=1.0, hard_stop_usd=1.0)
    def chat_structured(self, model, messages, output_model, task, max_tokens=2000, temperature=0):
        self.ledger.append(UsageRecord(run_id=self.run_id, task=task, model=model,
                                       cost_usd=0.001, cost_source='reported'))
        return SmallWire(value=1)


def test_fake_client_caps_attempts_and_rejects_unplanned_payload(tmp_path):
    ledger = UsageLedger(tmp_path/'ledger.jsonl')
    stage = {'stage_id': 'deepseek-flash/F00332', 'first_input_token_upper': 1500,
             'repair_input_token_upper': 2000}
    s = Stage2ExtractionSession(tmp_path/'state.json', run_id='fake-comparison',
                                fingerprint='fixed', jobs=[stage['stage_id']], ledger=ledger, ceiling='0.10')
    s.begin(stage['stage_id'])
    c = Stage2ExtractionClient(FakeClient(ledger), s, stage)
    messages = [{'role': 'user', 'content': 'synthetic fixture'}]
    assert c.chat_structured('deepseek-flash', messages, SmallWire, 'jd_extraction').value == 1
    assert c.chat_structured('deepseek-flash', messages, SmallWire, 'jd_extraction').value == 1
    with pytest.raises(BudgetExceeded, match='attempt'):
        c.chat_structured('deepseek-flash', messages, SmallWire, 'jd_extraction')
    assert len(ledger.records()) == 2
    s.finish({'job_id': stage['stage_id'], 'status': 'done', 'result_sha256': 'r'})
    assert s.data['status'] == 'awaiting_semantic_check'
    with pytest.raises(BudgetExceeded, match='not running'):
        c.chat_structured('deepseek-flash', messages, SmallWire, 'jd_extraction')


def test_fake_client_does_not_dispatch_oversize_or_wrong_model(tmp_path):
    ledger = UsageLedger(tmp_path/'ledger.jsonl')
    stage = {'stage_id': 'deepseek-flash/F00332', 'first_input_token_upper': 100,
             'repair_input_token_upper': 100}
    s = Stage2ExtractionSession(tmp_path/'state.json', run_id='fake-comparison',
                                fingerprint='fixed', jobs=[stage['stage_id']], ledger=ledger, ceiling='0.10')
    s.begin(stage['stage_id'])
    c = Stage2ExtractionClient(FakeClient(ledger), s, stage)
    with pytest.raises(BudgetExceeded, match='allowance'):
        c.chat_structured('deepseek-flash', [{'role': 'user', 'content': 'x'*1000}], SmallWire, 'jd_extraction')
    with pytest.raises(ValueError, match='frozen stage'):
        c.chat_structured('gpt-6-luna', [{'role': 'user', 'content': 'x'}], SmallWire, 'jd_extraction')
    assert not ledger.records()
