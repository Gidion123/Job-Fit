"""D-103 public-beta runtime pieces, offline (fake SDK; no network, no DB).

Covers the reservation-label compatibility mapping, the beta phase windows and call model, the
canonical-byte envelopes at the runtime boundary (through the actual frozen serialization), the
in-memory session allowance gated by a proven durable ticket, and the one-job analysis (frozen
analyze_job equivalence, and the extraction-envelope hold with 0 Sol and 0 Luna calls).
"""
import json
import time
import uuid
from datetime import date
from decimal import Decimal
from functools import lru_cache
from types import SimpleNamespace

import pytest
import yaml

from jobfit.config import REPO_ROOT
from jobfit.live import budget_store as store
from jobfit.live.beta_envelope import cv_fits, extraction_fits, jd_fits
from jobfit.live.common import LiveSafetyRefusal
from jobfit.live.deadlines import EMBED_TIMEOUT_SECONDS, GRACE_SECONDS, max_attempts, phase_window
from jobfit.live.evidence import IntentJournal, journal_path
from jobfit.live.quota import BETA_LIMITS, BetaAllowances, BetaClaim
from jobfit.live.reserved_client import (BETA_CHAIN_PHASE, CHAIN_PHASE, CallModel, OperationState,
                                         bind_reserved_client)
from jobfit.llm.document_bytes import document_bytes
from jobfit.llm.public_beta_bounds import DEFAULT_BETA_CONFIG, compute_public_beta_bounds
from jobfit.llm.runtime import build_runtime_client
from jobfit.recommend.beta_analysis import analyze_one_job, job_analysis_refusal
from jobfit.recommend.service import RecommendConfig, analyze_job
from jobfit.schemas.requirements import JDExtraction
from tests.test_cv_upload_pipeline import parsed
from tests.test_live_unit import CONFIG, LUNA, SOL, Answer, FakeSDK, bounds as legacy_bounds, response, settings
from tests.test_live_recommend_equivalence import answer as evidence_answer

CFG = yaml.safe_load(CONFIG.read_text())


@lru_cache(maxsize=1)
def beta():
    return compute_public_beta_bounds()


def env():
    return beta().envelopes


@lru_cache(maxsize=1)
def beta_model():
    return CallModel(beta(), CONFIG, phase_config=DEFAULT_BETA_CONFIG, chain_phase=BETA_CHAIN_PHASE)


class BetaLive:
    """One admitted beta operation without a database (the runner's binding, as in test_live_unit.Live)."""

    def __init__(self, tmp_path, phase, sdk=None, quota=None, on_first_intent=None):
        tmp_path.mkdir(parents=True, exist_ok=True)
        self.sdk = sdk if sdk is not None else FakeSDK()
        self.op_key = 'idem:' + str(uuid.uuid4())
        inner = build_runtime_client(settings(tmp_path), CONFIG, run_id=self.op_key, sdk_client=self.sdk)
        self.op = OperationState(self.op_key, phase, beta().phase_bounds()[phase], phase_window(phase, beta(), 240.0),
                                 anchor_mono=time.monotonic(), quota=quota, on_first_intent=on_first_intent)
        self.ledger_path = tmp_path / 'ledger.jsonl'
        self.client = bind_reserved_client(inner, self.op, beta_model(), self.ledger_path)

    def intents(self):
        return [r for r in IntentJournal(journal_path(self.ledger_path)).read() if r['type'] == 'intent']


# --- the reservation-label compatibility mapping (no migration) ------------------------------------------

def test_the_reservation_label_mapping_is_one_explicit_table():
    assert store.RESERVATION_LABEL == {'parse': 'parse', 'recommendation': 'recommendation',
                                       'search': 'recommendation', 'job_analysis': 'recommendation'}
    for phase, label in store.RESERVATION_LABEL.items():
        assert store.reservation_label(phase) == label
    for bad in ('', 'Job_analysis', 'embed', None):
        with pytest.raises(ValueError):
            store.reservation_label(bad)


def test_every_label_is_allowed_by_the_unchanged_0002_check_constraint():
    text = (REPO_ROOT / 'migrations/versions/0002_cp3_production.py').read_text()
    assert "CHECK (phase IN ('parse', 'recommendation'))" in text
    assert set(store.RESERVATION_LABEL.values()) == {'parse', 'recommendation'}


# --- windows and the call model ------------------------------------------------------------------------

def test_beta_windows_come_from_the_beta_chains_and_the_frozen_timeouts():
    b, chat = beta(), 240.0
    search, job = phase_window('search', b, chat), phase_window('job_analysis', b, chat)
    assert search.calls_wall == EMBED_TIMEOUT_SECONDS + GRACE_SECONDS
    assert [max_attempts(b.chains[c]) for c in ('extraction', 'matching', 'fallback')] == [3, 3, 3]
    assert job.calls_wall == 9 * (chat + GRACE_SECONDS)
    assert 0 < search.window < job.window < 24 * 3600
    assert phase_window('parse', b, chat).calls_wall == 2 * (chat + GRACE_SECONDS)


def test_the_legacy_call_model_is_unchanged_and_the_beta_one_is_exact():
    legacy = CallModel(legacy_bounds(), CONFIG)
    assert legacy.chain_phase == CHAIN_PHASE and 'recommendation' in CHAIN_PHASE.values()
    assert legacy.embed_max_tokens == 4 * int(legacy_bounds().details['cv_max_chars']) + 100
    m = beta_model()
    assert m.chain_phase == BETA_CHAIN_PHASE and 'recommendation' not in BETA_CHAIN_PHASE.values()
    assert m.embed_max_tokens == beta().details['embed_max_bytes'] == env().cv_document_max_bytes - 4 + 100


@pytest.mark.parametrize('phase,call', [
    ('search', lambda c: c.chat_structured(SOL, [{'role': 'user', 'content': 'x'}], Answer, 'evidence_matching',
                                           max_tokens=100)),
    ('search', lambda c: c.chat_structured('deepseek-flash', [{'role': 'user', 'content': 'x'}], Answer,
                                           'cv_parsing', max_tokens=100)),
    ('job_analysis', lambda c: c.embed(['query'], model='qwen', dimensions=8)),
    ('job_analysis', lambda c: c.chat_structured('deepseek-flash', [{'role': 'user', 'content': 'x'}], Answer,
                                                 'cv_parsing', max_tokens=100)),
    ('parse', lambda c: c.chat_structured(SOL, [{'role': 'user', 'content': 'x'}], Answer, 'evidence_matching',
                                          max_tokens=100)),
])
def test_a_call_outside_its_beta_phase_is_refused_before_the_sdk(tmp_path, phase, call):
    live = BetaLive(tmp_path, phase)
    with pytest.raises(LiveSafetyRefusal):
        call(live.client)
    assert live.op.fatal_refusal in ('phase_mismatch', 'call_outside_model') and live.sdk.calls == []


def test_a_job_analysis_matching_call_runs_and_keeps_its_real_phase_in_the_evidence(tmp_path):
    live = BetaLive(tmp_path, 'job_analysis', sdk=FakeSDK(lambda kw: response(kw['model'])))
    assert live.client.chat_structured(SOL, [{'role': 'user', 'content': 'x'}], Answer, 'evidence_matching',
                                       max_tokens=100).answer == 'ok'
    assert len(live.sdk.calls) == 1 and live.op.fatal_refusal is None
    assert [(i['phase'], i['chain']) for i in live.intents()] == [('job_analysis', 'matching')]


# --- canonical-byte envelopes at the runtime boundary ----------------------------------------------------

class KwSDK:
    """Records the complete frozen request (messages and max_tokens), then stops it."""

    def __init__(self):
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def with_options(self, **kw):
        return self

    def create(self, **kw):
        self.calls.append(kw)
        raise RuntimeError('captured')


def frozen_request(tmp_path, run):
    sdk = KwSDK()
    client = build_runtime_client(settings(tmp_path), CONFIG, run_id='probe', sdk_client=sdk)
    client.guard = SimpleNamespace(check=lambda cost: None)
    try:
        run(client)
    except Exception:
        pass
    return sdk.calls[0]


def text_at(limit, unit):
    """A text of exactly ``limit`` document bytes made of ``unit`` plus ASCII padding."""
    text = ''
    while document_bytes(text + unit) <= limit:
        text += unit
    text += 'x' * (limit - document_bytes(text))
    assert document_bytes(text) == limit
    return text


UNITS = {'ascii': 'a', 'multibyte': 'é', 'cjk': '履', 'emoji': '🚀', 'quote': '"', 'backslash': '\\',
         'control': 'a\n\t'}


@pytest.mark.parametrize('name', sorted(UNITS))
def test_a_cv_at_the_envelope_fits_the_modelled_parse_attempt_and_one_byte_more_is_refused(tmp_path, name):
    from jobfit.cv.parser import CVWire, parse_cv
    from jobfit.cv.text_extract import TextResult
    from jobfit.llm.structured import STRUCTURED_MAX_TOKENS
    limit = env().cv_document_max_bytes
    text = text_at(limit, UNITS[name])
    assert cv_fits(env(), text, 'CVX') and not cv_fits(env(), text + 'x', 'CVX')
    kw = frozen_request(tmp_path, lambda c: parse_cv(TextResult(text=text), cv_id='CVX', analysis_date=date(2026, 10, 8),
                                                      client=c, model='deepseek-flash', is_synthetic=True))
    assert kw['max_tokens'] == STRUCTURED_MAX_TOKENS
    assert beta_model().chat_fits('parse', 'initial', kw['messages'], CVWire, kw['max_tokens'])


def jd_at_limit(unit):
    """Requirements with 32 bullets (the inventory envelope), padded to the JD envelope exactly."""
    head = 'Requirements:\n' + ''.join(f'- Skill {i} {unit}\n' for i in range(env().max_inventory_items))
    pad = env().jd_document_max_bytes - document_bytes(head)
    text = head + 'x' * pad
    assert document_bytes(text) == env().jd_document_max_bytes
    return text


@pytest.mark.parametrize('name', sorted(UNITS))
def test_a_jd_at_the_envelope_fits_the_modelled_extraction_attempt(tmp_path, name):
    from jobfit.extraction.audited import AuditedExtraction, ExtractionSpec, qualification_inventory
    from jobfit.extraction.jd_extractor import extract_jd
    text = jd_at_limit(UNITS[name])
    assert len(qualification_inventory(text)) == env().max_inventory_items
    assert jd_fits(env(), text, 'pasted') and not jd_fits(env(), text + 'x', 'pasted')
    spec = ExtractionSpec(REPO_ROOT / CFG['jd_prompt_file'], CFG['jd_prompt_version'])
    kw = frozen_request(tmp_path, lambda c: extract_jd(text, job_id='pasted', client=c, model=CFG['extraction_model'],
                                                       cache=None, scope='session_jd', spec=spec, dynamic_output=True))
    assert beta_model().chat_fits('extraction', 'initial', kw['messages'], AuditedExtraction, kw['max_tokens'])


def test_too_many_inventory_items_or_a_long_job_id_is_refused():
    many = 'Requirements:\n' + ''.join(f'- S{i}\n' for i in range(env().max_inventory_items + 1))
    assert not jd_fits(env(), many, 'pasted')
    assert not jd_fits(env(), 'Requirements:\n- Python\n', 'j' * (env().short_field_max_chars + 1))
    assert not jd_fits(env(), 'lone surrogate \ud800', 'pasted')


def extraction_at(limit, units=4, job='J01', unit_text='Python'):
    rows = [{'unit_id': f'u{i}', 'text': unit_text, 'field': 'skill_tool', 'importance': 'required',
             'source_quotes': [unit_text]} for i in range(units)]
    ext = JDExtraction.model_validate({'job_id': job, 'units': rows})
    pad = limit - document_bytes(ext.model_dump(mode='json'))
    rows[0]['text'] = unit_text + 'x' * pad
    ext = JDExtraction.model_validate({'job_id': job, 'units': rows})
    assert document_bytes(ext.model_dump(mode='json')) == limit
    return ext


def test_an_extraction_at_the_envelope_fits_the_modelled_matching_attempt(tmp_path):
    from jobfit.matching.evidence_matcher import EvidenceResponse, match_evidence
    limit = env().extraction_document_max_bytes
    ext = extraction_at(limit)
    assert extraction_fits(env(), ext) and not extraction_fits(env(), extraction_at(limit + 1))
    assert not extraction_fits(env(), extraction_at(20000, units=env().max_units + 1))
    cv = parsed()
    assert cv_fits(env(), cv.profile.raw_text, cv.profile.cv_id)
    for model, chain in ((SOL, 'matching'), (LUNA, 'fallback')):
        kw = frozen_request(tmp_path / chain, lambda c: match_evidence(cv, ext, client=c, model=model,
                                                                        dynamic_output=True))
        assert beta_model().chat_fits(chain, 'initial', kw['messages'], EvidenceResponse, kw['max_tokens'])


# --- the session allowance, gated by a proven durable ticket ---------------------------------------------

def claim(a, session, phase, op, outcome):
    got = a.claim(session, phase, op, lambda: outcome)
    assert isinstance(got, BetaClaim)
    return got


def test_a_proven_consumed_ticket_opens_one_parse_one_search_and_three_job_analyses():
    a = BetaAllowances()
    assert BETA_LIMITS == {'parse': 1, 'search': 1, 'job_analysis': 3}
    first = claim(a, 's', 'parse', 'op1', 'consumed')
    assert first.quota is not None and a.remaining('s') is None       # nothing before the proven consume
    assert first.quota() == 'consumed' and first.on_first_intent() is True
    assert a.remaining('s') == {'parse': 0, 'search': 1, 'job_analysis': 3}
    assert a.claim('s', 'parse', 'op2', lambda: pytest.fail('no second ticket')) == 'allowance_exhausted'
    for i in range(3):
        c = a.claim('s', 'job_analysis', f'ja{i}', lambda: pytest.fail('no second ticket'))
        assert c.quota is None and c.on_first_intent() is True
    assert a.claim('s', 'job_analysis', 'ja3', lambda: 'consumed') == 'allowance_exhausted'
    s = a.claim('s', 'search', 'se', lambda: 'consumed')
    assert s.quota is None and s.on_first_intent()
    assert a.claim('s', 'search', 'se2', lambda: 'consumed') == 'allowance_exhausted'
    assert a.claim('s', 'recommendation', 'r', lambda: 'consumed') == 'phase_not_admitted'


@pytest.mark.parametrize('outcome', ['refused', 'unavailable', 'unknown', 'raises'])
def test_no_proven_consume_creates_no_allowance(outcome):
    a = BetaAllowances()

    def consume():
        if outcome == 'raises':
            raise OSError('lost')
        return outcome
    c = a.claim('s', 'job_analysis', 'op1', consume)
    assert c.quota() == ('unknown' if outcome == 'raises' else outcome)
    assert a.remaining('s') is None and c.on_first_intent() is False
    again = a.claim('s', 'job_analysis', 'op2', lambda: 'refused')     # still needs the durable ticket
    assert again.quota is not None and again.quota() == 'refused' and a.remaining('s') is None


@pytest.mark.parametrize('outcome', ['consumed', 'refused', 'unavailable', 'unknown'])
def test_the_ticket_outcome_gates_the_provider_call_in_the_operation(tmp_path, outcome):
    a = BetaAllowances()
    c = a.claim('s', 'parse', 'idem:x', lambda: outcome)
    live = BetaLive(tmp_path, 'parse', quota=c.quota, on_first_intent=c.on_first_intent)
    msgs = [{'role': 'user', 'content': 'synthetic text'}]
    if outcome == 'consumed':
        assert live.client.chat_structured('deepseek-flash', msgs, Answer, 'cv_parsing', max_tokens=16000).answer == 'ok'
        assert len(live.sdk.calls) == 1 and a.remaining('s') == {'parse': 0, 'search': 1, 'job_analysis': 3}
    else:
        with pytest.raises(LiveSafetyRefusal):
            live.client.chat_structured('deepseek-flash', msgs, Answer, 'cv_parsing', max_tokens=16000)
        assert live.sdk.calls == [] and a.remaining('s') is None
        assert live.op.fatal_refusal == {'refused': 'quota_refused', 'unavailable': 'quota_unavailable',
                                         'unknown': 'quota_outcome_unknown'}[outcome]


def test_a_refusal_before_the_first_intent_never_uses_the_allowance():
    a = BetaAllowances()
    first = claim(a, 's', 'parse', 'op1', 'consumed')
    first.quota()
    first.on_first_intent()
    ja = claim(a, 's', 'job_analysis', 'ja1', 'consumed')
    a.release_if_pending('s', 'ja1')                       # e.g. busy, budget, input_too_large
    assert a.remaining('s')['job_analysis'] == 3 and ja.on_first_intent() is False
    pending = claim(a, 's', 'search', 'se1', 'consumed')
    assert a.claim('s', 'search', 'se2', lambda: 'consumed') == 'allowance_exhausted'   # one at a time
    a.release_if_pending('s', 'se1')
    assert pending.on_first_intent() is False and a.remaining('s')['search'] == 1
    # an operation that stopped before its ticket attempt leaves nothing behind
    b = BetaAllowances()
    claim(b, 't', 'parse', 'p1', 'consumed')
    b.release_if_pending('t', 'p1')
    assert b.remaining('t') is None and b.sessions() == set()


def test_one_ticket_attempt_per_session_at_a_time_and_a_retry_of_the_same_operation():
    a = BetaAllowances()
    c = claim(a, 's', 'parse', 'op1', 'consumed')
    assert a.claim('s', 'search', 'op2', lambda: 'consumed') == 'busy'
    c.quota()
    assert a.claim('s', 'parse', 'op1', lambda: pytest.fail('no ticket')).quota is None   # the same operation


def test_a_restart_loses_the_session_and_never_grants_the_ip_another_ticket():
    a = BetaAllowances()
    c = claim(a, 's', 'parse', 'op1', 'consumed')
    c.quota()
    c.on_first_intent()
    restarted = BetaAllowances()                           # new process: in-memory state is gone
    again = restarted.claim('s', 'job_analysis', 'op2', lambda: 'refused')   # the durable row is still there
    assert again.quota() == 'refused' and restarted.remaining('s') is None


def test_drop_forgets_the_session():
    a = BetaAllowances()
    claim(a, 's', 'parse', 'op1', 'consumed').quota()
    a.drop('s')
    assert a.remaining('s') is None and a.sessions() == set()


# --- the one-job analysis ---------------------------------------------------------------------------------

def plain_client(tmp_path, sdk):
    return build_runtime_client(settings(tmp_path), CONFIG, sdk_client=sdk)


def cached(job='J01'):
    from tests.test_live_recommend_equivalence import extraction
    return extraction(job)


def test_the_one_job_analysis_equals_the_frozen_analyze_job(tmp_path):
    config, cv = RecommendConfig.from_yaml(CONFIG), parsed()
    for job in ('J01', 'J04', 'J07', 'J08'):           # scored, Luna fallback, no extraction, both chains failed
        a_sdk, b_sdk = FakeSDK(evidence_answer), FakeSDK(evidence_answer)
        ours = analyze_one_job(cv, job, envelopes=env(), client=plain_client(tmp_path / f'a{job}', a_sdk),
                               config=config, cached=cached(job))
        frozen = analyze_job(cv, job, 1, *cached(job), client=plain_client(tmp_path / f'b{job}', b_sdk),
                             fallback_client=None, config=config)
        assert ours == frozen
        assert [(k['model'], k['messages']) for k in a_sdk.calls] == [(k['model'], k['messages']) for k in b_sdk.calls]


def test_an_oversized_cached_extraction_is_refused_before_any_reservation():
    cv = parsed()
    big = extraction_at(env().extraction_document_max_bytes + 1)
    assert job_analysis_refusal(env(), cv, 'J01', cached=(big, None)) == 'input_too_large'
    assert job_analysis_refusal(env(), cv, 'J01', cached=cached('J01')) is None
    assert job_analysis_refusal(env(), cv, 'pasted', jd_text='Requirements:\n- Python\n') is None
    assert job_analysis_refusal(env(), cv, 'pasted', jd_text=jd_at_limit('a') + 'x') == 'input_too_large'
    long_cv = cv.model_copy(update={'profile': cv.profile.model_copy(
        update={'raw_text': 'x' * env().cv_document_max_bytes})})
    assert job_analysis_refusal(env(), long_cv, 'J01', cached=cached('J01')) == 'input_too_large'
    with pytest.raises(ValueError):
        job_analysis_refusal(env(), cv, 'J01')


def test_an_oversized_extraction_holds_the_job_with_no_matching_call(tmp_path):
    cv, sdk = parsed(), FakeSDK(evidence_answer)
    big = extraction_at(env().extraction_document_max_bytes + 1)
    r = analyze_one_job(cv, 'J01', envelopes=env(), client=plain_client(tmp_path, sdk),
                        config=RecommendConfig.from_yaml(CONFIG), cached=(big, None))
    assert sdk.calls == [] and r.score.score_pct is None and 'beta_envelope_exceeded' in r.hold_reason
    assert r.extraction == big and r.assessments == [] and r.attempts == []


def oversized_extraction_answer(job_id, jd_quote, units):
    rows = [{'unit_id': f'u{i}', 'text': jd_quote, 'field': 'skill_tool', 'importance': 'required',
             'source_quotes': [jd_quote]} for i in range(units)]
    return json.dumps({'job_id': job_id, 'units': rows, 'jd_quality': 'ok',
                       'qualification_coverage': [{'source_id': 'Q01', 'unit_ids': [r['unit_id'] for r in rows]}]})


def test_a_live_extraction_above_the_envelope_is_settled_and_matching_is_held(tmp_path):
    """Through the beta ReservedClient: the extraction call runs and is in the evidence; no Sol, no Luna."""
    from jobfit.extraction.audited import ExtractionSpec
    jd = 'Requirements:\n- Python\n'
    units = env().max_units + 1

    def respond(kw):
        assert kw['model'] not in (SOL, LUNA), 'no matching call may be made'
        return response(kw['model'], oversized_extraction_answer('pasted', 'Python', units))
    live = BetaLive(tmp_path, 'job_analysis', sdk=FakeSDK(respond))
    cv = parsed()
    assert job_analysis_refusal(env(), cv, 'pasted', jd_text=jd) is None
    r = analyze_one_job(cv, 'pasted', envelopes=env(), client=live.client, config=RecommendConfig.from_yaml(CONFIG),
                        jd_text=jd, spec=ExtractionSpec(REPO_ROOT / CFG['jd_prompt_file'], CFG['jd_prompt_version']),
                        extraction_model=CFG['extraction_model'])
    assert 'beta_envelope_exceeded' in r.hold_reason and len(r.extraction.units) == units
    assert len(live.sdk.calls) == 1 and live.op.fatal_refusal is None
    assert [(i['phase'], i['chain']) for i in live.intents()] == [('job_analysis', 'extraction')]
    assert Decimal(0) < live.op.committed_upper <= beta().extraction_max
