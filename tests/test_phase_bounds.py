"""Deterministic CP3 phase cost bounds (D-096; FAIL-38). Fake clients only, no provider call."""
import ast
import inspect
import itertools
import json
from datetime import date
from decimal import Decimal

import pytest
import yaml
from pydantic import BaseModel

from jobfit.config import REPO_ROOT, ConfigurationError, get_production_settings
from jobfit.llm import phase_bounds as pb
from jobfit.llm.client import TruncatedStructuredResponse, strict_schema
from jobfit.llm.output_policy import MODEL_OUTPUT_LIMIT as C
from jobfit.llm.structured import REPAIR_CONTEXT_MAX_BYTES, StageFailure, validated_call

CONFIG = yaml.safe_load(pb.DEFAULT_CONFIG.read_text())
PIPELINE = yaml.safe_load((REPO_ROOT / CONFIG['pipeline_config']).read_text())
CONTINUATION_MARK = 'This is the only length continuation.'
REPAIR_MARK = 'This is the only repair attempt.'


@pytest.fixture(scope='module')
def real():
    return pb.compute_phase_bounds()


def write_config(tmp_path, **changes):
    cfg = yaml.safe_load(pb.DEFAULT_CONFIG.read_text())
    envelopes = changes.pop('envelopes', None)
    if envelopes is not None:
        cfg['envelopes'].update(envelopes)
        cfg['envelopes'] = {k: v for k, v in cfg['envelopes'].items() if v is not None}
    cfg.update(changes)
    path = tmp_path / 'bounds.yaml'
    path.write_text(yaml.safe_dump(cfg))
    return path


# --- the frozen validated_call state machine ------------------------------------------------------

class Out(BaseModel):
    value: int


class Prior(BaseModel):
    text: str


class ScriptedClient:
    """Each step: 'truncated' (finish_reason=length), 'invalid' (fails validate) or 'schema'."""

    def __init__(self, steps, invalid=None):
        self.steps, self.calls = list(steps), []
        self.invalid = invalid or {'value': 0}

    def chat_structured(self, model, messages, output_model, task, max_tokens=2000, temperature=0.0):
        self.calls.append({'task': task, 'max_tokens': max_tokens, 'messages': [dict(m) for m in messages]})
        step = self.steps.pop(0) if self.steps else 'invalid'
        if step == 'truncated':
            raise TruncatedStructuredResponse('length')
        return {'value': 'not-an-int'} if step == 'schema' else self.invalid


def reject(out):
    raise ValueError('assessment_coverage')


def observed(client):
    """(max_tokens, continuations, repair contexts) per call, from the messages actually sent."""
    rows = []
    for call in client.calls:
        users = [m['content'] for m in call['messages'] if m['role'] == 'user']
        rows.append(pb.Attempt(call['max_tokens'], sum(CONTINUATION_MARK in u for u in users),
                               sum(REPAIR_MARK in u for u in users)))
    return rows


def run_chain(L, limit, steps, output_model=Out, invalid=None):
    client = ScriptedClient(steps, invalid)
    with pytest.raises(StageFailure):
        validated_call(client, model='m', prompt='p', payload={'x': 1}, output_model=output_model, task='t',
                       validate=reject, max_tokens=L, model_output_limit=limit)
    return client


LIMITS = {'L<C/2': C // 4, 'L=C/2': C // 2, 'C/2<L<C': 3 * C // 4, 'L=C': C}


@pytest.mark.parametrize('name', LIMITS)
def test_every_failure_script_stays_inside_the_reachable_sequences(name):
    L = LIMITS[name]
    sequences = pb.reachable_sequences(L, C)
    longest = max(len(s) for s in sequences.values())
    for steps in itertools.product(('truncated', 'invalid', 'schema'), repeat=4):
        client = run_chain(L, C, steps)
        seen = observed(client)
        assert any(seen == s[:len(seen)] for s in sequences.values()), (name, steps, seen)
        assert len(seen) <= longest
        assert sum(c['task'] == 't_length_continuation' for c in client.calls) <= 1
        assert sum(c['task'] == 't_validation_repair' for c in client.calls) <= 1


@pytest.mark.parametrize('name', ['L<C/2', 'L=C/2', 'C/2<L<C'])
def test_both_orders_are_reachable_below_the_output_limit(name):
    L = LIMITS[name]
    M = min(2 * L, C)
    sequences = pb.reachable_sequences(L, C)
    assert [a.max_tokens for a in sequences['continuation_first']] == [L, M, M]
    assert [a.max_tokens for a in sequences['repair_first']] == [L, L, M]
    assert observed(run_chain(L, C, ['truncated', 'invalid', 'truncated'])) == sequences['continuation_first']
    assert observed(run_chain(L, C, ['invalid', 'truncated', 'invalid'])) == sequences['repair_first']


def test_at_the_output_limit_only_initial_and_repair_are_reachable():
    sequences = pb.reachable_sequences(C, C)
    assert sequences == {'initial_then_repair': [pb.Attempt(C), pb.Attempt(C, repairs=1)]}
    assert [c['max_tokens'] for c in run_chain(C, C, ['truncated']).calls] == [C]
    assert observed(run_chain(C, C, ['invalid', 'truncated'])) == sequences['initial_then_repair']
    assert observed(run_chain(C, C, ['invalid', 'invalid', 'invalid'])) == sequences['initial_then_repair']


def test_without_an_output_limit_truncation_is_repaired_at_the_same_limit():
    sequences = pb.reachable_sequences(16000, None)
    assert observed(run_chain(16000, None, ['truncated'] * 3)) == sequences['initial_then_repair']


def test_the_3c_accounting_envelope_is_not_a_reachable_sequence():
    envelope = pb.accounting_envelope(C)
    assert [a.max_tokens for a in envelope] == [C, C, C]
    reachable = [s for L in range(1, C + 1, 4093) for s in pb.reachable_sequences(L, C).values()]
    reachable += pb.reachable_sequences(C - 1, C).values()
    at_limit = pb.reachable_sequences(C, C)['initial_then_repair']
    assert envelope not in reachable + [at_limit]
    # L < C: at most L + 2C < 3C output tokens (3C is a supremum, never reached); L = C: exactly 2C.
    assert all(sum(a.max_tokens for a in s) < 3 * C for s in reachable)
    assert sum(a.max_tokens for a in at_limit) == 2 * C


def test_appended_messages_fit_the_configured_envelopes():
    appended = CONFIG['envelopes']['appended_message_max_bytes'] + pb.MESSAGE_FRAMING_BYTES
    repair_context = 2 * REPAIR_CONTEXT_MAX_BYTES + pb.MESSAGE_FRAMING_BYTES
    prior = {'text': '"\\' * ((REPAIR_CONTEXT_MAX_BYTES - 20) // 4)}
    assert len(Prior.model_validate(prior).model_dump_json().encode()) <= REPAIR_CONTEXT_MAX_BYTES
    clients = [run_chain(C // 4, C, ['truncated', 'schema', 'truncated']),
               run_chain(C // 4, C, ['invalid', 'truncated']),
               run_chain(C // 4, C, ['invalid', 'invalid'], output_model=Prior, invalid=prior)]
    seen_assistant = False
    for client in clients:
        for m in client.calls[-1]['messages'][2:]:
            size = len(json.dumps(m, ensure_ascii=False).encode())
            if m['role'] == 'assistant':
                seen_assistant = True
                assert size <= repair_context
            else:
                assert size <= appended
    assert seen_assistant


def test_luna_runs_only_after_a_failed_sol_chain():
    from jobfit.cv.parser import ParsedCV
    from jobfit.matching.evidence_matcher import MatchingResult
    from jobfit.recommend.service import RecommendConfig, analyze_job
    from jobfit.schemas.cv import CVProfile
    from jobfit.schemas.requirements import JDExtraction

    config = RecommendConfig.from_yaml(REPO_ROOT / CONFIG['pipeline_config'])
    assert (config.matching_model, config.matching_fallback_model) == (PIPELINE['matching_model'],
                                                                         PIPELINE['matching_fallback_model'])
    cv = ParsedCV(profile=CVProfile(cv_id='CV', raw_text='Python'), analysis_date=date(2026, 10, 7))
    extraction = JDExtraction.model_validate({'job_id': 'J', 'units': [
        {'unit_id': 'u1', 'text': 'Python', 'importance': 'required', 'source_quotes': ['Python']}]})
    outcomes = {'done': MatchingResult([], 'done'), 'failed': MatchingResult([], 'failed', error_code='x'),
                'error': RuntimeError('boom')}
    for sol in outcomes:
        calls = []

        def matcher(cv_, ext, *, client, model, **kw):
            calls.append(model)
            out = outcomes[sol] if model == config.matching_model else MatchingResult([], 'failed')
            if isinstance(out, Exception):
                raise out
            return out
        analyze_job(cv, 'J', 1, extraction, None, client=object(), fallback_client=None, config=config,
                    matcher=matcher)
        expected = [config.matching_model] + ([] if sol == 'done' else [config.matching_fallback_model])
        assert calls == expected


# --- cost arithmetic -------------------------------------------------------------------------------

def test_chain_cost_is_the_exact_guard_formula_and_the_worse_order():
    price = pb.Price('m', Decimal('2'), Decimal('10'))
    spec = pb.ChainSpec('t', price, base_message_bytes=1000, schema_bytes=100, appended_message_bytes=50,
                        repair_context_bytes=200, sequences=pb.reachable_sequences(1000, 4000), reachable=True)
    # continuation first: inputs 1612, 1662, 1912 bytes; outputs 1000, 2000, 2000 tokens
    # repair first:       inputs 1612, 1862, 1912 bytes; outputs 1000, 1000, 2000 tokens
    assert spec.attempt_cost(pb.Attempt(1000)) == Decimal('0.013224')
    assert spec.cost() == Decimal('0.060372')


def test_attempt_cost_matches_the_frozen_client_guard_estimate():
    from jobfit.llm.pricing import ModelPrice, estimate_cost
    messages = [{'role': 'system', 'content': 'p'}, {'role': 'user', 'content': 'ü"' * 50}]
    schema = strict_schema(Out.model_json_schema())
    est_in = len(json.dumps(messages, ensure_ascii=False).encode()) + len(json.dumps(schema).encode()) + 512
    guard = estimate_cost(ModelPrice(key='m', model_id='m', input_per_m=3.0, output_per_m=15.0), est_in, 777)
    spec = pb.ChainSpec('t', pb.Price('m', Decimal('3'), Decimal('15')),
                        len(json.dumps(messages, ensure_ascii=False).encode()), pb._strict_schema_bytes(Out),
                        0, 0, {}, True)
    assert spec.attempt_cost(pb.Attempt(777)) == Decimal(str(guard))


def test_phase_totals_keep_parse_and_recommendation_separate():
    b = pb.PhaseBounds(parse_max=Decimal('0.5'), embed_max=Decimal('0.01'), extraction_max=Decimal('1'),
                       matching_max=Decimal('2'), fallback_max=Decimal('0.25'), bound_basis=pb.DERIVED,
                       config_sha256='x')
    assert b.recommendation_upper_bound == Decimal('3.26')
    assert b.full_analysis_upper_bound == Decimal('3.76')
    out = b.breakdown(2)
    assert out['difference_from_cap_usd'] == '1.76' and out['within_cap'] is False
    assert pb.PhaseBounds(**{**b.__dict__, 'parse_max': Decimal('1')}).recommendation_upper_bound == Decimal('3.26')


# --- the real configuration -------------------------------------------------------------------------

def test_real_configuration_gives_a_derived_bound(real):
    out = real.breakdown(2)
    print(json.dumps(out, indent=1))
    assert real.bound_basis == pb.DERIVED
    assert real.config_sha256 == __import__('hashlib').sha256(pb.DEFAULT_CONFIG.read_bytes()).hexdigest()
    d = real.details
    assert d['k'] == PIPELINE['stage1_k'] and d['model_output_limit'] == C
    assert real.parse_max == Decimal(d['parse']['chain_cost_usd'])          # embedding is not in parse
    assert real.extraction_max == d['k'] * Decimal(d['extraction']['chain_cost_usd'])
    assert real.matching_max == d['k'] * Decimal(d['matching']['chain_cost_usd'])
    assert real.fallback_max == d['k'] * Decimal(d['fallback']['chain_cost_usd'])
    assert real.recommendation_upper_bound == (real.embed_max + real.extraction_max + real.matching_max
                                               + real.fallback_max)
    assert real.full_analysis_upper_bound == real.parse_max + real.recommendation_upper_bound
    assert d['parse']['sequences'] == {'initial_then_repair': [16000, 16000]}
    for task in ('extraction', 'matching', 'fallback'):
        assert d[task]['reachable'] is True
        assert d[task]['sequences'] == {'initial_then_repair': [C, C]}   # derived L = C: 2C, no continuation
    assert d['matching']['model'] == 'openai/gpt-6-sol' and d['fallback']['model'] == 'openai/gpt-6-luna'
    # Recorded in docs/checkpoint_3 (Phase 2A). A change here must update the report.
    assert out['full_analysis_upper_bound'] == '84.7655888' and out['within_cap'] is False


def test_bound_above_the_daily_cap_makes_public_live_ineligible(real, tmp_path):
    def settings(daily, budget='1000000', hard_stop='1000000'):
        return get_production_settings({
            'JOBFIT_ENV': 'prod', 'DATABASE_URL': 'postgresql://u:p@db/prod', 'JOBFIT_INTERNAL_TOKEN': 'i' * 32,
            'JOBFIT_LIVE_ENABLED': '1', 'JOBFIT_PUBLIC_LIVE': '1', 'OPENROUTER_API_KEY': 'sk-test',
            'JOBFIT_OWNER_TOKEN': 'o' * 32, 'JOBFIT_IP_HMAC_KEY': 'h' * 32,
            'JOBFIT_USAGE_LEDGER': str(tmp_path / 'l.jsonl'), 'JOBFIT_DAILY_BUDGET_USD': daily,
            'API_BUDGET_USD': budget, 'API_HARD_STOP_USD': hard_stop})
    assert pb.public_live_eligible(settings('2', '5', '4.5'), real) is False
    assert pb.public_live_eligible(settings('100'), real) is True
    assert pb.public_live_eligible(get_production_settings({}), real) is False


def test_missing_unit_envelopes_fall_back_to_the_3c_supremum(real, tmp_path):
    sup = pb.compute_phase_bounds(write_config(tmp_path, envelopes={'max_units': None}))
    assert sup.bound_basis == pb.SUPREMUM
    for task in ('extraction', 'matching', 'fallback'):
        assert sup.details[task]['reachable'] is False
        assert sup.details[task]['sequences'] == {'accounting_envelope_3C': [C, C, C]}
    assert 'not reachable attempts' in sup.details['note']
    assert sup.parse_max == real.parse_max and sup.full_analysis_upper_bound > real.full_analysis_upper_bound
    huge = get_production_settings({
        'JOBFIT_ENV': 'prod', 'DATABASE_URL': 'postgresql://u:p@db/prod', 'JOBFIT_INTERNAL_TOKEN': 'i' * 32,
        'JOBFIT_LIVE_ENABLED': '1', 'JOBFIT_PUBLIC_LIVE': '1', 'OPENROUTER_API_KEY': 'sk-test',
        'JOBFIT_OWNER_TOKEN': 'o' * 32, 'JOBFIT_IP_HMAC_KEY': 'h' * 32,
        'JOBFIT_USAGE_LEDGER': str(tmp_path / 'l.jsonl'), 'JOBFIT_DAILY_BUDGET_USD': '1000000',
        'API_BUDGET_USD': '1000000', 'API_HARD_STOP_USD': '1000000'})
    assert pb.public_live_eligible(huge, sup) is False


@pytest.mark.parametrize('changes, message', [
    ({'parse_model': 'not-a-model'}, 'not in config/models_v1.yaml'),
    ({'parse_model': None}, 'model key is missing'),
    ({'parse_dynamic_output': True}, 'parse_dynamic_output'),
    ({'jd_text_max_chars': 99999}, 'frozen extract_jd limit'),
    ({'jd_text_max_chars': 0}, 'jd_text_max_chars'),
    ({'route_rules': 'config/versions/missing.json'}, 'route rules'),
    ({'envelopes': {'max_units': 0}}, 'max_units'),
    ({'envelopes': {'max_inventory_items': -1}}, 'max_inventory_items'),
    ({'envelopes': {'appended_message_max_bytes': None}}, 'appended_message_max_bytes'),
    ({'envelopes': {'extraction_json_max_bytes': 1.5}}, 'extraction_json_max_bytes'),
])
def test_invalid_configuration_fails_closed(tmp_path, changes, message):
    with pytest.raises(ConfigurationError, match=message):
        pb.compute_phase_bounds(write_config(tmp_path, **changes))


@pytest.mark.parametrize('field, value', [('input_per_m', None), ('output_per_m', 0), ('input_per_m', -1),
                                          ('output_per_m', 'nan')])
def test_missing_or_invalid_prices_fail_closed(tmp_path, field, value):
    models = yaml.safe_load(pb.MODELS_FILE.read_text())
    models['models'][CONFIG['parse_model']][field] = value
    path = tmp_path / 'models.yaml'
    path.write_text(yaml.safe_dump(models))
    with pytest.raises(ConfigurationError, match='price'):
        pb.compute_phase_bounds(models_file=path)


def test_invalid_limits_fail_closed():
    for bad in (0, -1, True, 1.5, None):
        with pytest.raises(ConfigurationError):
            pb.reachable_sequences(bad, C)
    with pytest.raises(ConfigurationError, match='above the model output limit'):
        pb.reachable_sequences(C + 1, C)
    with pytest.raises(ConfigurationError):
        pb.accounting_envelope(0)


# --- parse model: runtime source and test-only consistency evidence ------------------------------------

def test_parse_model_resolves_through_the_frozen_registry_only():
    price = pb.resolve_parse_model(CONFIG['parse_model'])
    assert price.model_id == 'deepseek/deepseek-v4.1-flash'
    source = inspect.getsource(pb)
    assert 'run_cp24_test' not in source and 'usage_ledger' not in source


def test_parse_model_matches_the_frozen_cp24_runner_and_ledger():
    tree = ast.parse((REPO_ROOT / 'scripts/run_cp24_test.py').read_text())
    values = [n.value.value for n in tree.body if isinstance(n, ast.Assign)
              and any(getattr(t, 'id', None) == 'PARSE_MODEL' for t in n.targets)]
    assert values == [CONFIG['parse_model']]
    rows = [json.loads(line) for line in (REPO_ROOT / 'reports/usage/usage_ledger.jsonl').read_text().splitlines()
            if '"cp24_test_parse_v1"' in line]
    rows = [r for r in rows if r['run_id'] == 'cp24_test_parse_v1']
    assert rows and {r['model'] for r in rows} == {pb.resolve_parse_model(CONFIG['parse_model']).model_id}
    assert {r['task'] for r in rows} <= {'cv_parsing', 'cv_parsing_validation_repair'}


# --- the envelopes cover requests built by the frozen stage code ------------------------------------------

class RecordingClient:
    def __init__(self):
        self.calls = []

    def chat_structured(self, model, messages, output_model, task, max_tokens=2000, temperature=0.0):
        self.calls.append((max_tokens, len(json.dumps(messages, ensure_ascii=False).encode()),
                           len(json.dumps(strict_schema(output_model.model_json_schema())).encode())))
        if len(self.calls) == 1:
            raise TruncatedStructuredResponse('length')
        raise ValueError('assessment_coverage')


def assert_within(client, chain):
    sequence = max(chain['sequences'].values(), key=len)
    for i, (max_tokens, message_bytes, schema_bytes) in enumerate(client.calls):
        assert max_tokens <= sequence[min(i, len(sequence) - 1)]
        assert schema_bytes == chain['schema_bytes']
        if i == 0:
            assert message_bytes <= chain['base_message_bytes']


HARD_TEXT = 'Data "x" \\ é\x01 ' * 10


def test_frozen_extract_jd_request_fits_the_extraction_envelope(real):
    from jobfit.extraction.audited import ExtractionSpec
    from jobfit.extraction.jd_extractor import extract_jd
    items = CONFIG['envelopes']['max_inventory_items']
    bullets = ''.join(f'- {HARD_TEXT[:500]}\n' for _ in range(items))
    text = 'Requirements:\n' + bullets
    text += 'x' * (CONFIG['jd_text_max_chars'] - len(text))
    assert len(text) == CONFIG['jd_text_max_chars']
    client = RecordingClient()
    spec = ExtractionSpec(REPO_ROOT / PIPELINE['jd_prompt_file'], PIPELINE['jd_prompt_version'])
    extract_jd(text, job_id='J' * CONFIG['envelopes']['short_field_max_chars'], client=client,
               model=PIPELINE['extraction_model'], spec=spec, dynamic_output=True)
    assert len(client.calls) >= 1
    assert_within(client, real.details['extraction'])


def test_frozen_match_evidence_request_fits_the_matching_envelope(real):
    from jobfit.cv.parser import ParsedCV
    from jobfit.matching.evidence_matcher import match_evidence
    from jobfit.schemas.cv import CVProfile
    from jobfit.schemas.requirements import JDExtraction
    env = CONFIG['envelopes']
    from jobfit.cv.text_extract import MAX_CHARACTERS
    cv_text = (HARD_TEXT * MAX_CHARACTERS)[:MAX_CHARACTERS]
    units = [{'unit_id': f'u{i}', 'text': HARD_TEXT[:60], 'importance': 'required',
              'source_quotes': [HARD_TEXT[:60]]} for i in range(env['max_units'])]
    extraction = JDExtraction.model_validate({'job_id': 'J', 'units': units})
    assert len(json.dumps(extraction.model_dump(mode='json'), ensure_ascii=False).encode()) <= env['extraction_json_max_bytes']
    cv = ParsedCV(profile=CVProfile(cv_id='C' * env['short_field_max_chars'], raw_text=cv_text),
                  analysis_date=date(2026, 10, 7))
    durations = {f'u{i}': 2.2250738585072014e-308 for i in range(env['max_units'])}
    for model, chain in ((PIPELINE['matching_model'], 'matching'), (PIPELINE['matching_fallback_model'], 'fallback')):
        client = RecordingClient()
        result = match_evidence(cv, extraction, client=client, model=model, duration_years=durations,
                                validator_version=PIPELINE['evidence_validator'],
                                guardrail_ids=tuple(PIPELINE['evidence_guardrails']), dynamic_output=True)
        assert result.status == 'failed' and len(client.calls) >= 1
        assert_within(client, real.details[chain])
