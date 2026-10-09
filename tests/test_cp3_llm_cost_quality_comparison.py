"""CP3 evidence-matching cost/quality comparison: offline only. Fakes replace every provider call.

The fake SDK replays the saved D-079 Sol outputs for the four fixed development pairs, so the
real matcher, validator, ledger, recorder and evaluator run end to end without a network call.
"""
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.run_cp3_llm_cost_quality_comparison as run
from jobfit.config import Settings
from jobfit.eval.qa_phase_a import LeakageError
from jobfit.llm.ledger import UsageLedger
from scripts.evaluate_cp3_llm_cost_quality_comparison import build, markdown, percentile
from scripts.run_cp23_luna_matching import CappedClient

ROOT = Path(__file__).resolve().parents[1]
SAVED = ROOT / 'evals/results/cp23/model_sweep_v1'
NEW_FILES = ['config/cp3/llm_cost_quality_comparison_v1.yaml', 'scripts/run_cp3_llm_cost_quality_comparison.py',
             'scripts/evaluate_cp3_llm_cost_quality_comparison.py', 'tests/test_cp3_llm_cost_quality_comparison.py',
             'docs/checkpoint_3/supporting/CP3_LLM_Cost_Quality_Comparison.md']
COST = {'openai/gpt-6-sol': 0.02, 'openai/gpt-6-luna': 0.001, 'anthropic/claude-haiku-5.5': 0.002}
LATENCY_MS = {'openai/gpt-6-sol': 2000, 'openai/gpt-6-luna': 1000, 'anthropic/claude-haiku-5.5': 1500}


@pytest.fixture(scope='module')
def config():
    return run.load_config()


@pytest.fixture(scope='module')
def bench(config):
    return run.benchmark(config)


def saved_outputs():
    out = {}
    for path in SAVED.glob('gpt-6-sol__*.json'):
        row = json.loads(path.read_text())
        out[(row['cv_id'], frozenset(a['unit_id'] for a in row['assessments']))] = row['assessments']
    return out


class Clock:
    def __init__(self):
        self.now = 0.0

    def perf_counter(self):
        return self.now


class FakeSDK:
    """Stands in for the OpenAI SDK. with_options returns a new object sharing the same log."""

    def __init__(self, log, script, clock, options=None):
        self.log, self.script, self.clock, self.options = log, script, clock, options or {}
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.saved = saved_outputs()

    def with_options(self, **kwargs):
        return FakeSDK(self.log, self.script, self.clock, {**self.options, **kwargs})

    def get(self, *a, **k):
        raise AssertionError('no key check in offline tests')

    def create(self, **kw):
        data = json.loads(kw['messages'][1]['content'])['untrusted_document_data']
        units = frozenset(u['unit_id'] for u in data['extraction']['units'])
        pair = (data['cv_id'], data['extraction']['job_id'])
        n = sum(1 for e in self.log if e['model'] == kw['model'] and e['pair'] == pair) + 1
        self.log.append({'model': kw['model'], 'pair': pair, 'n': n, 'options': self.options, 'kwargs': kw,
                         'messages': json.dumps(kw['messages'], sort_keys=True)})   # snapshot: the list grows later
        self.clock.now += LATENCY_MS[kw['model']] / 1000
        action = self.script.get((kw['model'], pair, n), 'valid')
        if action == 'transport':
            raise ConnectionError('fake transport failure')
        assessments = deepcopy(self.saved[(data['cv_id'], units)])
        if action == 'incomplete':
            assessments = assessments[1:]
        content = 'not json' if action == 'garbage' else json.dumps({'assessments': assessments})
        usage = SimpleNamespace(prompt_tokens=1000, completion_tokens=500, total_tokens=1500, cost=COST[kw['model']],
                                completion_tokens_details=SimpleNamespace(reasoning_tokens=100),
                                prompt_tokens_details=None)
        return SimpleNamespace(id=f'req-{len(self.log)}', model=kw['model'], usage=usage, provider='FakeProvider',
                               choices=[SimpleNamespace(finish_reason='length' if action == 'truncated' else 'stop',
                                                        message=SimpleNamespace(content=content))])


META = {'found': True, 'endpoints': 1, 'structured_endpoints': 1, 'min_output_limit': None,
        'temperature_supported': True, 'response_aliases': [], 'cheapest_structured_price_per_m': (0.1, 0.5)}


def receipt_for(config, tmp_path, fetch=None):
    settings = replace(Settings(), usage_ledger=tmp_path / 'ledger.jsonl', api_budget_usd=20, api_hard_stop_usd=19)
    return run.preflight(config, check_network=True, settings=settings,
                         fetch=fetch or (lambda model_id: dict(META)), search=lambda f: [])


@pytest.fixture(scope='module')
def executed(tmp_path_factory, config):
    """One full fake run: Luna truncates then fails validation once; Haiku fails one pair completely."""
    tmp = tmp_path_factory.mktemp('cp3run')
    receipt, plan, loaded = receipt_for(config, tmp)
    settings = replace(Settings(), usage_ledger=tmp / 'ledger.jsonl', api_budget_usd=20, api_hard_stop_usd=19)
    log, clock = [], Clock()
    script = {('openai/gpt-6-luna', ('CV1', 'F00332'), 1): 'truncated',
              ('openai/gpt-6-luna', ('CV1', 'F00332'), 2): 'incomplete',
              ('anthropic/claude-haiku-5.5', ('CV2', 'F00018'), 1): 'garbage',
              ('anthropic/claude-haiku-5.5', ('CV2', 'F00018'), 2): 'garbage'}
    out = tmp / config['run_id']
    recorder = run.Recorder(out / 'requests.jsonl')
    client = run.RecordingClient(settings, sdk_client=FakeSDK(log, script, clock), run_id=config['run_id'],
                                 chat_timeout_seconds=240.0, recorder=recorder)
    client.configure(receipt['models'])
    capped = CappedClient(client, 0.0, cap=receipt['run_cap_usd'])
    original = run.time
    run.time = clock
    try:
        run.write_once(out / 'plan.json', receipt)
        with client.ledger.exclusive():
            summary = run.run_benchmark(capped, recorder, receipt, plan, loaded, out)
    finally:
        run.time = original
    run.write_once(out / 'summary.json', {'run_id': config['run_id'], 'models': summary, 'total_wall_ms': 1})
    ledger = [r for r in UsageLedger(tmp / 'ledger.jsonl').records()]
    return SimpleNamespace(out=out, log=log, recorder=recorder, client=client, ledger=ledger, receipt=receipt)


# 1. dry run: zero provider calls -------------------------------------------------------------------------------

def test_dry_run_makes_no_provider_or_network_call(monkeypatch, capsys):
    def boom(*a, **k):
        raise AssertionError('provider or network call in a dry run')
    monkeypatch.setattr('jobfit.llm.client.OpenRouterClient._chat_attempt', boom)
    monkeypatch.setattr(run.SweepAdapter, 'create', boom)
    monkeypatch.setattr(run, 'fetch_metadata', boom)
    monkeypatch.setattr('httpx.get', boom)
    monkeypatch.setattr(run, 'execute', boom)
    assert run.main(['--skip-network-check']) == 0
    printed = capsys.readouterr().out
    assert 'DRY RUN' in printed and '"execute_ready": false' in printed and '"units": 73' in printed


def test_execute_is_refused_offline_and_when_preflight_has_problems(monkeypatch, config, tmp_path):
    def boom(*a, **k):
        raise AssertionError('paid call attempted')
    monkeypatch.setattr(run, 'execute', boom)
    with pytest.raises(SystemExit, match='metadata check is required'):
        run.main(['--execute', '--skip-network-check'])
    missing = lambda model_id: {'found': False} if 'haiku' in model_id else dict(META)
    receipt, _, _ = receipt_for(config, tmp_path, fetch=missing)
    assert any('claude-haiku-5.5: id anthropic/claude-haiku-5.5 not found (not substituted' in p
               for p in receipt['problems'])
    assert receipt['models']['claude-haiku-5.5']['model_id'] == 'anthropic/claude-haiku-5.5'
    assert receipt['execute_ready'] is False


def test_preflight_reports_counts_cap_and_hashes(config, tmp_path):
    receipt, _, _ = receipt_for(config, tmp_path)
    assert receipt['units'] == 73 and len(receipt['pairs']) == 4
    assert receipt['requests'] == {'expected_main': 12, 'worst_case_with_repair_and_continuation': 36}
    assert receipt['execute_ready'] is True and receipt['problems'] == []
    assert receipt['run_cap_usd'] == receipt['conservative_max_cost']['total_usd'] > receipt['estimated_cost']['total_usd']
    assert set(receipt['models']) == {'gpt-6-sol', 'gpt-6-luna', 'claude-haiku-5.5'}
    assert receipt['protected_sha256'] == config['protected_sha256']
    assert all(m['verified'] for m in receipt['models'].values())


# 2-3. development data only ------------------------------------------------------------------------------------

def test_development_pairs_and_files_are_accepted(config):
    assert run.check_dev_only(config) == list(run.APPROVED_PAIRS)
    run.verify_protected(config)                       # includes evals/splits/test_job_ids.txt: no false positive


@pytest.mark.parametrize('pairs', [
    [['CV3', 'F00332'], ['CV1', 'F00036'], ['CV2', 'F00815'], ['CV2', 'F00018']],
    [['CV1', 'F00332'], ['CV1', 'F00036'], ['CV2', 'F00815'], ['CV5', 'F00018']],
    [['CV1', 'F00001'], ['CV1', 'F00036'], ['CV2', 'F00815'], ['CV2', 'F00018']],
    [['CV1', 'F00332'], ['CV1', 'F00036'], ['CV2', 'F00815']]])
def test_other_cvs_and_pairs_are_rejected(config, pairs):
    with pytest.raises(LeakageError):
        run.check_dev_only({**config, 'benchmark': {**config['benchmark'], 'pairs': pairs}})


def test_test_split_jobs_and_held_out_paths_are_rejected(config, monkeypatch):
    test_job = min((ROOT / 'evals/splits/test_job_ids.txt').read_text().split())
    monkeypatch.setattr(run, 'APPROVED_PAIRS', (('CV1', test_job),) + run.APPROVED_PAIRS[1:])
    bad = {**config, 'benchmark': {**config['benchmark'], 'pairs': [list(p) for p in run.APPROVED_PAIRS]}}
    with pytest.raises(LeakageError, match='not a development job'):
        run.check_dev_only(bad)
    monkeypatch.undo()
    for path in ('evals/gold/test_v13_cp24_r1/evidence_gold.jsonl', 'evals/results/cp24/heldout_report_v1.json',
                 'data/synthetic_cvs/cv_03_junior_ml_engineer_1yr_en.md'):
        with pytest.raises(LeakageError):
            run.check_dev_only({**config, 'protected_sha256': {**config['protected_sha256'], path: '0' * 64}})


def test_a_changed_input_hash_stops_the_run(config):
    changed = {**config['protected_sha256'], 'prompts/evidence_matching_v1_1.md': '0' * 64}
    with pytest.raises(ValueError, match='Protected input changed'):
        run.verify_protected({**config, 'protected_sha256': changed})


# 4-5. identical inputs and prompt across models ----------------------------------------------------------------

def test_every_model_gets_identical_inputs_and_prompt(executed):
    pairs = [json.loads(p.read_text()) for p in (executed.out / 'pairs').glob('*.json')]
    assert len(pairs) == 12
    by_pair = {}
    for row in pairs:
        by_pair.setdefault((row['cv_id'], row['job_id']), set()).add(row['input_sha256'])
    assert all(len(v) == 1 for v in by_pair.values())
    assert len({r['prompt_sha256'] for r in executed.recorder.rows}) == 1
    first = {}
    for entry in executed.log:                         # the exact request messages, per pair and model
        if entry['n'] == 1:
            first.setdefault(entry['pair'], set()).add(entry['messages'])
    assert all(len(v) == 1 for v in first.values())
    assert not any('reasoning' in e['kwargs']['extra_body'] for e in executed.log)   # no reasoning/effort tuning
    assert not any(r['reasoning_param_sent'] for r in executed.recorder.rows)


# recording adapter: with_options keeps the recorder; main, repair and continuation are all recorded -------------

def test_with_options_keeps_the_recording_adapter_and_sink(executed):
    adapter = executed.client.sdk
    wrapped = adapter.with_options(max_retries=0, timeout=240.0)
    assert isinstance(wrapped, run.RecordingAdapter) and wrapped.recorder is executed.recorder
    assert wrapped.sdk.options == {'max_retries': 0, 'timeout': 240.0}
    assert all(e['options'] == {'max_retries': 0, 'timeout': 240.0} for e in executed.log)


def test_main_continuation_and_repair_attempts_are_all_recorded(executed):
    luna = [r for r in executed.recorder.rows if r['model'] == 'gpt-6-luna' and r['job_id'] == 'F00332']
    assert [r['kind'] for r in luna] == ['main', 'length_continuation', 'validation_repair']
    assert [r['outcome'] for r in luna] == ['TruncatedStructuredResponse', 'returned', 'returned']
    assert luna[1]['max_tokens_requested'] == 2 * luna[0]['max_tokens_requested']
    assert all(r['sent'] and r['reasoning_tokens'] == 100 and r['cost_usd_reported'] == 0.001 for r in luna)
    assert len(executed.recorder.rows) == len(executed.log) == len(executed.ledger) == 4 + 6 + 5
    on_disk = (executed.out / 'requests.jsonl').read_text().splitlines()
    assert [json.loads(x) for x in on_disk] == executed.recorder.rows


# 6-9. evaluation ------------------------------------------------------------------------------------------------

@pytest.fixture(scope='module')
def report(executed, config):
    return build(executed.out, config, ledger_records=executed.ledger)


def test_failed_units_stay_in_the_denominator(report):
    haiku, sol = report['models']['claude-haiku-5.5'], report['models']['gpt-6-sol']
    assert report['units'] == 73 and report['classes'] == {'MATCH': 36, 'NO_MATCH': 16, 'PARTIAL': 21}   # r3 + D-067
    assert haiku['process']['valid_pairs'] == 3 and haiku['process']['assessed_units'] == 73 - 24
    assert haiku['process']['unassessed_units'] == 24 == haiku['quality']['unassessed_units']
    assert sum(sum(row.values()) for row in haiku['quality']['confusion'].values()) == 73
    assert sum(row['not_assessed'] for row in haiku['quality']['confusion'].values()) == 24
    assert haiku['quality']['macro_f1'] < sol['quality']['macro_f1']
    assert haiku['process']['structured_output_failures'] == 2 and haiku['process']['repair_attempts'] == 1
    assert report['versus_baseline']['claude-haiku-5.5']['flags']['all_pairs_valid'] is False


def test_saved_sol_outputs_reproduce_the_d079_headline(report):
    expected = json.loads((ROOT / 'evals/results/cp23/dev_eval_v2_20261004/model_sweep_stage1_v1.json').read_text())
    sol = report['models']['gpt-6-sol']
    assert sol['quality']['macro_f1'] == pytest.approx(expected['models']['gpt-6-sol']['macro_f1_all_cases_guarded'])
    assert sol['process']['valid_pairs'] == 4 and sol['quality']['quote_validity'] == 1.0
    assert report['models']['gpt-6-luna']['quality']['macro_f1'] == pytest.approx(sol['quality']['macro_f1'])


def test_process_counts_for_truncation_and_validation_repair(report):
    p = report['models']['gpt-6-luna']['process']
    assert (p['valid_pairs'], p['requests'], p['continuation_attempts'], p['repair_attempts']) == (4, 6, 1, 1)
    assert (p['truncations'], p['validation_failures'], p['failed_requests'], p['model_fallbacks']) == (1, 1, 1, 0)


def test_cost_is_attributed_to_the_right_model(report):
    cost = {k: m['cost'] for k, m in report['models'].items()}
    assert cost['gpt-6-sol']['actual_usd'] == pytest.approx(4 * 0.02)
    assert cost['gpt-6-luna']['actual_usd'] == pytest.approx(6 * 0.001)
    assert cost['claude-haiku-5.5']['actual_usd'] == pytest.approx(5 * 0.002)
    assert all(c['reconciled_with_ledger'] and c['estimated_or_uncertain_usd'] == 0 for c in cost.values())
    assert cost['gpt-6-sol']['tokens'] == {'input_tokens': 4000, 'output_tokens': 2000, 'reasoning_tokens': 400,
                                           'total_tokens': 6000}
    assert cost['gpt-6-sol']['per_valid_pair_usd'] == pytest.approx(0.02)
    assert cost['claude-haiku-5.5']['per_valid_pair_usd'] == pytest.approx(0.010 / 3)
    vs = report['versus_baseline']
    assert vs['gpt-6-luna']['cost_ratio_per_valid_pair'] == pytest.approx(0.0015 / 0.02)
    assert vs['gpt-6-luna']['flags']['cost_materially_lower'] is True
    assert report['estimated_cost_preflight']['conservative_max_usd']['total_usd'] > 0


def test_latency_is_preserved(report, executed):
    sol = report['models']['gpt-6-sol']['latency']
    assert sol['attempt_ms_p50'] == sol['attempt_ms_p95'] == 2000 and sol['attempts_measured'] == 4
    assert sol['pair_wall_ms'] == [2000] * 4
    luna = report['models']['gpt-6-luna']['latency']
    assert luna['pair_wall_ms'] == [3000, 1000, 1000, 1000]
    assert report['versus_baseline']['gpt-6-luna']['latency_ratio_attempt_p50'] == pytest.approx(0.5)
    assert percentile([1, 2, 3, 4, 100], 0.5) == 3 and percentile([1, 2, 3, 4, 100], 0.95) == 100
    assert percentile([], 0.5) is None and 'not a load' in report['latency_note']


def test_comparison_is_descriptive_and_never_promotes(report):
    for c in report['versus_baseline'].values():
        assert c['decision'] == 'owner' and c['historical_reference']['applied'] is False
        assert 'sol_macro_f1 - 0.03' in c['historical_reference']['rule']
    assert report['versus_baseline']['gpt-6-luna']['historical_reference']['met'] is True
    assert report['integrity'] == {'system_prompt_sha256': report['integrity']['system_prompt_sha256'],
                                   'same_prompt_for_all_requests': True, 'same_inputs_for_all_models': True,
                                   'reasoning_param_sent': False}
    table = markdown(report)
    assert '| Model | Valid pairs | Macro-F1 | Overclaims | Quote validity | Cost (US$) | p50 (s) | p95 (s) |' in table


def test_evaluation_output_is_deterministic(report, executed, config):
    again = build(executed.out, config, ledger_records=executed.ledger)
    assert json.dumps(again, sort_keys=True) == json.dumps(report, sort_keys=True)
    assert markdown(again) == markdown(report)


# 10. no D-087 change ---------------------------------------------------------------------------------------------

def test_d087_freeze_is_unchanged_and_new_files_are_outside_it():
    from scripts.prepare_cp23_freeze import verify
    folder = ROOT / 'evals/freeze/cp23_freeze_draft_v2'
    assert verify(folder) == []
    frozen = json.loads((folder / 'freeze_receipt_APPROVED.json').read_text())['files_sha256']
    assert not set(NEW_FILES) & set(frozen)
