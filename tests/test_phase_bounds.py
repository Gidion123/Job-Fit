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


def test_appended_messages_fit_the_computed_bounds():
    appended = {m: pb.appended_message_bound(m, CONFIG['envelopes']['max_list_index_digits']) for m in (Out, Prior)}
    repair_context = 2 * REPAIR_CONTEXT_MAX_BYTES + pb.MESSAGE_FRAMING_BYTES
    prior = {'text': '"\\' * ((REPAIR_CONTEXT_MAX_BYTES - 20) // 4)}
    assert len(Prior.model_validate(prior).model_dump_json().encode()) <= REPAIR_CONTEXT_MAX_BYTES
    clients = [(Out, run_chain(C // 4, C, ['truncated', 'schema', 'truncated'])),
               (Out, run_chain(C // 4, C, ['invalid', 'truncated'])),
               (Prior, run_chain(C // 4, C, ['invalid', 'invalid'], output_model=Prior, invalid=prior))]
    seen_assistant = False
    for model, client in clients:
        for m in client.calls[-1]['messages'][2:]:
            size = len(json.dumps(m, ensure_ascii=False).encode()) + pb.MESSAGE_SEPARATOR_BYTES
            if m['role'] == 'assistant':
                seen_assistant = True
                assert size <= repair_context
            else:
                assert size <= appended[model]
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
    assert d['parse']['regions']['fixed_limit']['sequences'] == {'initial_then_repair': [16000, 16000]}
    for task in ('extraction', 'matching', 'fallback'):
        regions = d[task]['regions']
        assert d[task]['reachable'] is True and set(regions) == {'envelope', 'below_limit'}
        # envelope: derived L = C, so 2C and no continuation; below the limit: L <= C - 1, up to 3C - 1
        assert regions['envelope']['sequences'] == {'initial_then_repair': [C, C]}
        assert regions['below_limit']['sequences'] == {'continuation_first': [C - 1, C, C],
                                                       'repair_first': [C - 1, C - 1, C]}
        chain = real.chains[task]
        assert chain.cost() == max(r.cost() for r in chain.regions.values())
        assert d[task]['dominant_region'] == 'envelope'
    assert d['matching']['model'] == 'openai/gpt-6-sol' and d['fallback']['model'] == 'openai/gpt-6-luna'
    # Recorded in docs/checkpoint_3 (Phase 2A). A change here must update the report.
    assert out['full_analysis_upper_bound'] == '84.7704449' and out['within_cap'] is False


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
        assert sup.details[task]['regions'] == {'accounting_envelope_3C': sup.details[task]['regions']['accounting_envelope_3C']}
        assert sup.details[task]['regions']['accounting_envelope_3C']['sequences'] == {'accounting_envelope_3C': [C, C, C]}
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
    ({'envelopes': {'appended_message_max_bytes': 4096}}, 'AuditedExtraction repair message bound'),
    ({'envelopes': {'max_list_index_digits': None}}, 'max_list_index_digits'),
    ({'envelopes': {'max_list_index_digits': 0}}, 'max_list_index_digits'),
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


# --- every reachable attempt of the frozen stages fits the bound --------------------------------------------

class StageClient:
    """Plays a script against a real frozen stage and records every call as the frozen guard sees it.

    Steps: 'truncated' (finish_reason=length), 'prior' (a schema-valid output, up to the repair
    context limit, that fails the stage's validation, so it is sent back as the assistant prior) or
    'schema' (a schema-invalid output).
    """

    def __init__(self, steps, prior, invalid):
        self.steps, self.prior, self.invalid, self.calls = list(steps), prior, invalid, []

    def chat_structured(self, model, messages, output_model, task, max_tokens=2000, temperature=0.0):
        users = [m['content'] for m in messages if m['role'] == 'user']
        self.calls.append({'input_bytes': pb.guard_input_bytes(messages, output_model),
                           'attempt': pb.Attempt(max_tokens, sum(CONTINUATION_MARK in u for u in users),
                                                 sum(REPAIR_MARK in u for u in users))})
        step = self.steps.pop(0) if self.steps else 'schema'
        if step == 'truncated':
            raise TruncatedStructuredResponse('length')
        return self.prior if step == 'prior' else self.invalid


def largest_prior(model, build):
    """A quote-heavy valid output whose JSON is just under the frozen repair context limit."""
    n = (REPAIR_CONTEXT_MAX_BYTES - len(build('').model_dump_json().encode())) // 4
    prior = build('"\\' * n)
    assert REPAIR_CONTEXT_MAX_BYTES - 4 < len(prior.model_dump_json().encode()) <= REPAIR_CONTEXT_MAX_BYTES
    return prior.model_dump(mode='json')


def evidence_prior():
    from jobfit.matching.evidence_matcher import EvidenceResponse
    from jobfit.schemas.analysis import UnitAssessment
    return largest_prior(EvidenceResponse, lambda s: EvidenceResponse(assessments=[UnitAssessment(unit_id='z' + s)]))


def extraction_prior():
    from jobfit.extraction.audited import AuditedExtraction
    return largest_prior(AuditedExtraction, lambda s: AuditedExtraction(job_id='z' + s, qualification_coverage=[]))


EVIDENCE_INVALID = {'assessments': [{'unit_id': 1, 'branches': [{'branch_id': 1}] * 3}] * 13}
EXTRACTION_INVALID = {'job_id': 1, 'units': [{'unit_id': 1, 'branches': [{'branch_id': 1}] * 3}] * 13,
                      'qualification_coverage': [{'source_id': 1}] * 13}


def guard_cost(client, price):
    return sum((Decimal(c['input_bytes']) * price.input_per_m + Decimal(c['attempt'].max_tokens) * price.output_per_m)
               / pb.ONE_MILLION for c in client.calls)


def assert_sequence_within(client, chain, region):
    spec = chain.regions[region]
    seen = [c['attempt'] for c in client.calls]
    assert any(seen == s[:len(seen)] for s in spec.sequences.values()), seen
    for c in client.calls:          # every attempt, not only the first
        assert c['input_bytes'] <= spec.attempt_input_bytes(c['attempt'])
    assert guard_cost(client, spec.price) <= spec.cost() <= chain.cost()


HARD_TEXT = 'Data "x" \\ é\x01 ' * 10


def run_extract(text, steps):
    from jobfit.extraction.audited import ExtractionSpec
    from jobfit.extraction.jd_extractor import extract_jd
    client = StageClient(steps, extraction_prior(), EXTRACTION_INVALID)
    spec = ExtractionSpec(REPO_ROOT / PIPELINE['jd_prompt_file'], PIPELINE['jd_prompt_version'])
    result = extract_jd(text, job_id='J' * CONFIG['envelopes']['short_field_max_chars'], client=client,
                        model=PIPELINE['extraction_model'], spec=spec, dynamic_output=True)
    assert result.status == 'failed'
    return client


def run_match(cv_text, extraction, model, steps, durations=None):
    from jobfit.cv.parser import ParsedCV
    from jobfit.matching.evidence_matcher import match_evidence
    from jobfit.schemas.cv import CVProfile
    cv = ParsedCV(profile=CVProfile(cv_id='C' * CONFIG['envelopes']['short_field_max_chars'], raw_text=cv_text),
                  analysis_date=date(2026, 10, 7))
    client = StageClient(steps, evidence_prior(), EVIDENCE_INVALID)
    result = match_evidence(cv, extraction, client=client, model=model, duration_years=durations,
                            validator_version=PIPELINE['evidence_validator'],
                            guardrail_ids=tuple(PIPELINE['evidence_guardrails']), dynamic_output=True)
    assert result.status == 'failed'
    return client


def one_unit_extraction():
    from jobfit.schemas.requirements import JDExtraction
    return JDExtraction.model_validate({'job_id': 'J', 'units': [
        {'unit_id': 'u1', 'text': 'x', 'importance': 'required', 'source_quotes': ['x']}]})


ENVELOPE_SCRIPTS = [['prior', 'schema'], ['schema', 'prior'], ['truncated'], ['prior', 'truncated']]
BELOW_LIMIT_SCRIPTS = [['truncated', 'prior', 'truncated'],     # continuation first: C-1, C, C
                       ['prior', 'truncated', 'schema'],        # repair first: C-1, C-1, C
                       ['schema', 'truncated', 'prior'],
                       ['truncated', 'schema', 'schema']]


def test_every_attempt_of_frozen_extract_jd_at_the_envelope_fits(real):
    items = CONFIG['envelopes']['max_inventory_items']
    text = 'Requirements:\n' + ''.join(f'- {HARD_TEXT[:500]}\n' for _ in range(items))
    text += 'x' * (CONFIG['jd_text_max_chars'] - len(text))
    for steps in ENVELOPE_SCRIPTS:
        client = run_extract(text, steps)
        assert client.calls[0]['attempt'].max_tokens == C
        assert_sequence_within(client, real.chains['extraction'], 'envelope')


def test_every_attempt_of_frozen_match_evidence_at_the_envelope_fits(real):
    from jobfit.cv.text_extract import MAX_CHARACTERS
    from jobfit.schemas.requirements import JDExtraction
    env = CONFIG['envelopes']
    units = [{'unit_id': f'u{i}', 'text': HARD_TEXT[:60], 'importance': 'required',
              'source_quotes': [HARD_TEXT[:60]]} for i in range(env['max_units'])]
    extraction = JDExtraction.model_validate({'job_id': 'J', 'units': units})
    assert len(json.dumps(extraction.model_dump(mode='json'), ensure_ascii=False).encode()) <= env['extraction_json_max_bytes']
    cv_text = (HARD_TEXT * MAX_CHARACTERS)[:MAX_CHARACTERS]
    durations = {f'u{i}': 2.2250738585072014e-308 for i in range(env['max_units'])}
    for model, chain in ((PIPELINE['matching_model'], 'matching'), (PIPELINE['matching_fallback_model'], 'fallback')):
        for steps in ENVELOPE_SCRIPTS:
            client = run_match(cv_text, extraction, model, steps, durations)
            assert client.calls[0]['attempt'].max_tokens == C
            assert_sequence_within(client, real.chains[chain], 'envelope')


def largest_below_limit(first_limit):
    """Largest number of '"' characters whose frozen request still gets L < C (binary search)."""
    lo, hi = 1, 100_000
    assert first_limit(hi) == C and first_limit(lo) < C
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if first_limit(mid) < C else (lo, mid)
    return lo


def test_every_attempt_of_frozen_extract_jd_below_the_limit_fits(real):
    n = largest_below_limit(lambda n: run_extract('"' * n, ['truncated']).calls[0]['attempt'].max_tokens)
    assert run_extract('"' * n, ['truncated']).calls[0]['attempt'].max_tokens == C - 1
    for steps in BELOW_LIMIT_SCRIPTS:
        client = run_extract('"' * n, steps)
        assert_sequence_within(client, real.chains['extraction'], 'below_limit')
    seen = [c['attempt'].max_tokens for c in run_extract('"' * n, BELOW_LIMIT_SCRIPTS[0]).calls]
    assert seen == [C - 1, C, C]


def test_every_attempt_of_frozen_match_evidence_below_the_limit_fits(real):
    ext = one_unit_extraction()
    sol, luna = PIPELINE['matching_model'], PIPELINE['matching_fallback_model']
    n = largest_below_limit(lambda n: run_match('"' * n, ext, sol, ['truncated']).calls[0]['attempt'].max_tokens)
    for model, chain in ((sol, 'matching'), (luna, 'fallback')):
        for steps in BELOW_LIMIT_SCRIPTS:
            client = run_match('"' * n, ext, model, steps)
            assert client.calls[0]['attempt'].max_tokens == C - 1
            assert_sequence_within(client, real.chains[chain], 'below_limit')
    seen = [c['attempt'].max_tokens for c in run_match('"' * n, ext, sol, BELOW_LIMIT_SCRIPTS[1]).calls]
    assert seen == [C - 1, C - 1, C]


def test_below_limit_region_covers_every_allowance_under_the_limit(real):
    for task in ('extraction', 'matching', 'fallback'):
        chain = real.chains[task]
        below = chain.regions['below_limit']
        grid = list(range(1, C, 997)) + [C // 2, C // 2 + 1, C - 1]
        costs = [pb.ChainSpec(**{**below.__dict__, 'sequences': pb.reachable_sequences(L, C)}).cost() for L in grid]
        assert max(costs) == below.cost() <= chain.cost()


# --- C1: the smallest reachable unit count is 1 ---------------------------------------------------------------

def test_expected_units_reaching_output_allowance_are_at_least_one(monkeypatch):
    from jobfit.extraction import jd_extractor
    from jobfit.matching import evidence_matcher
    from jobfit.llm.output_policy import output_allowance
    from jobfit.schemas.requirements import JDExtraction
    seen = []

    def recorder(task, input_tokens, expected_units, *a):
        seen.append((task, expected_units))
        return output_allowance(task, input_tokens, expected_units, *a)
    monkeypatch.setattr(jd_extractor, 'output_allowance', recorder)
    monkeypatch.setattr(evidence_matcher, 'output_allowance', recorder)
    run_extract('A job description with no requirement list.', ['schema'])
    assert seen == [('jd_extraction', 1)]
    seen.clear()
    client = StageClient([], None, {})
    from jobfit.cv.parser import ParsedCV
    from jobfit.schemas.cv import CVProfile
    cv = ParsedCV(profile=CVProfile(cv_id='CV', raw_text='Python'), analysis_date=date(2026, 10, 7))
    result = evidence_matcher.match_evidence(cv, JDExtraction.model_validate({'job_id': 'J', 'units': []}),
                                             client=client, model='m', dynamic_output=True)
    assert result.status == 'done' and seen == [] and client.calls == []      # zero units: no call at all
    unit = {'unit_id': 'u1', 'text': 'x', 'importance': 'required', 'source_quotes': ['x']}
    with pytest.raises(ValueError, match='unique'):         # duplicate IDs cannot shrink len(units)
        JDExtraction.model_validate({'job_id': 'J', 'units': [unit] * 2})
    run_match('Python', one_unit_extraction(), 'm', ['schema'])
    assert seen == [('evidence_matching', 1)]


def test_t_max_is_the_largest_estimate_below_the_limit_for_every_reachable_unit_count(real):
    from jobfit.llm.output_policy import output_allowance
    for chain, task in (('extraction', 'jd_extraction'), ('matching', 'evidence_matching')):
        t_max = real.details[chain]['below_limit_max_estimate_tokens']
        assert t_max == pb.max_tokens_below_limit(task, C)
        assert output_allowance(task, t_max, 1) < C == output_allowance(task, t_max + 1, 1)
        for units in range(1, CONFIG['envelopes']['max_units'] + 1):
            assert output_allowance(task, t_max + 1, units) == C     # more units never allow a larger T


# --- F2: the inventory envelope -----------------------------------------------------------------------------

def test_frozen_inventory_quotes_never_exceed_the_jd_length():
    import random
    from jobfit.extraction.audited import qualification_inventory
    rng = random.Random(7)
    separators = ['\n', '\r\n', '\r', '\x0b', '\x0c', '\x1c', '\x85', ' ', ' ']
    headings = ['Requirements:', '## Qualifications', 'Kualifikasi', 'About you', 'requirement']
    for _ in range(1500):
        lines = []
        for _ in range(rng.randint(1, 60)):
            r = rng.random()
            if r < 0.15:
                line = rng.choice(headings)
            elif r < 0.6:
                line = rng.choice(['- ', '* ', '• ', '1. ', '12) ', '  -   ']) + ''.join(
                    rng.choice('ab"\\ é\t') for _ in range(rng.randint(1, 40)))
            elif r < 0.85:
                line = rng.choice([' ', '\t']) + ''.join(rng.choice('ab"\\') for _ in range(rng.randint(1, 40)))
            else:
                line = ''.join(rng.choice('ab ') for _ in range(rng.randint(0, 20)))
            lines.append(line + rng.choice(separators))
        text = ''.join(lines)
        assert sum(len(r['source_quote']) for r in qualification_inventory(text)) <= len(text)


def test_inventory_envelope_quotes_total_exactly_the_jd_limit():
    jd_chars, items = CONFIG['jd_text_max_chars'], CONFIG['envelopes']['max_inventory_items']
    records = pb.inventory_envelope(jd_chars, items)
    lengths = [len(r['source_quote']) for r in records]
    assert len(records) == items and sum(lengths) == jd_chars and max(lengths) - min(lengths) <= 1
    assert sum(len(r['source_quote']) for r in pb.inventory_envelope(jd_chars, 1)) == jd_chars


# --- C2: the repair-message bound ---------------------------------------------------------------------------

def frozen_repair_message(model, invalid, *, code=None):
    """The instruction the frozen validated_call appends after ``invalid`` (or a ValueError code)."""
    client = ScriptedClient([], invalid)
    validate = (lambda out: (_ for _ in ()).throw(ValueError(code))) if code else (lambda out: None)
    with pytest.raises(StageFailure):
        validated_call(client, model='m', prompt='p', payload={}, output_model=model, task='t',
                       validate=validate, max_tokens=1, model_output_limit=None)
    return client.calls[1]['messages'][-1]


def test_frozen_message_texts_are_captured_from_validated_call():
    texts = pb.frozen_message_texts()
    assert CONTINUATION_MARK in texts['continuation'] and REPAIR_MARK in texts['repair_suffix']
    assert texts['schema_repair_prefix'].startswith(texts['repair_prefix'] + 'schema_validation')


def test_real_frozen_repair_messages_fit_the_computed_bound():
    from jobfit.cv.parser import CVWire
    from jobfit.extraction.audited import AuditedExtraction
    from jobfit.matching.evidence_matcher import EvidenceResponse
    digits = CONFIG['envelopes']['max_list_index_digits']
    cases = [(EvidenceResponse, EVIDENCE_INVALID), (EvidenceResponse, {}),
             (AuditedExtraction, EXTRACTION_INVALID), (AuditedExtraction, {'zz': 1}),
             (CVWire, {'skills_list': ['a'] * 999_999 + [5]}),             # an error at list index 999,999
             (CVWire, {'sections': [{'x': 1}] * 13, 'employment': [{'x': 1}] * 13})]
    for model, invalid in cases:
        message = frozen_repair_message(model, invalid)
        assert 'Schema errors' in message['content']
        assert pb._json_bytes(message) + pb.MESSAGE_SEPARATOR_BYTES <= pb.appended_message_bound(model, digits)
    assert '999999' in frozen_repair_message(CVWire, cases[4][1])['content']
    longest = 'unbounded_required_duration_needs_clarification'
    message = frozen_repair_message(Out, {'value': 1}, code=longest)
    assert longest in message['content']
    assert pb._json_bytes(message) + pb.MESSAGE_SEPARATOR_BYTES <= pb.appended_message_bound(Out, digits)


def test_a_path_element_beyond_the_envelope_exceeds_the_modelled_attempt_and_would_be_refused():
    from jobfit.extraction.audited import AuditedExtraction
    digits = CONFIG['envelopes']['max_list_index_digits']
    model = AuditedExtraction
    base = [{'role': 'system', 'content': 'p'}, {'role': 'user', 'content': '{}'}]
    repair_context = 2 * REPAIR_CONTEXT_MAX_BYTES + pb.MESSAGE_FRAMING_BYTES
    content = '"' * ((repair_context - pb.MESSAGE_SEPARATOR_BYTES - pb._json_bytes(
        {'role': 'assistant', 'content': ''})) // 2)
    prior = {'role': 'assistant', 'content': content}
    spec = pb.ChainSpec('t', pb.Price('m', Decimal(1), Decimal(1)), pb._json_bytes(base), pb._strict_schema_bytes(model),
                        pb.appended_message_bound(model, digits), repair_context, {}, True)
    attempt = pb.Attempt(C, repairs=1)
    # Path elements are modelled as long as the longest property name or the index digits, whichever
    # is longer (22 characters here, which already covers a 7-digit index). One more is not covered.
    covered = max(pb._schema_names_and_depth(model)[0], digits)
    within = base + [prior, pb.worst_repair_message(model, covered)]
    beyond = base + [prior, pb.worst_repair_message(model, covered + 1)]
    assert pb.guard_input_bytes(within, model) <= spec.attempt_input_bytes(attempt)
    assert pb.guard_input_bytes(beyond, model) > spec.attempt_input_bytes(attempt)   # the Phase 2B wrapper refuses


def test_guard_input_bytes_is_the_frozen_client_formula():
    messages = [{'role': 'system', 'content': 'p'}, {'role': 'user', 'content': 'ü"' * 50}]
    expected = (len(json.dumps(messages, ensure_ascii=False).encode())
                + len(json.dumps(strict_schema(Out.model_json_schema())).encode()) + 512)
    assert pb.guard_input_bytes(messages, Out) == expected
    source = inspect.getsource(__import__('jobfit.llm.client', fromlist=['x']).OpenRouterClient._chat_attempt)
    assert 'len(json.dumps(messages, ensure_ascii=False).encode()) + len(json.dumps(schema).encode()) + 512' in source
