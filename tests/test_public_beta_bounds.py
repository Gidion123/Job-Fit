"""D-103 controlled public-beta bounds: versioned profile, exact bounds, canonical bytes. Offline only.

No provider call: the frozen code runs against fake SDKs. The historical Phase 2A bound and its
eligibility check are asserted unchanged.
"""
import dataclasses
import json
from datetime import date
from decimal import Decimal
from functools import lru_cache

import pytest
import yaml

from jobfit.config import REPO_ROOT, ConfigurationError, get_production_settings
from jobfit.llm import phase_bounds as pb
from jobfit.llm import public_beta_bounds as beta
from jobfit.llm.document_bytes import document_bytes, text_content_bytes

LEGACY_FULL = Decimal('84.7704449')
EXPECTED = {'parse': Decimal('0.0614679'), 'search': Decimal('0.0001648'),
            'extraction': Decimal('0.4141854'), 'matching': Decimal('3.416284'),
            'fallback': Decimal('0.1708142'), 'job_analysis': Decimal('4.0012836')}
SAMPLES = {
    'ascii': 'Built a Python ETL pipeline for 3 teams.',
    'multibyte': 'résumé · Ingeniería de datos · 履歴書 · Москва',
    'emoji': 'ML 🚀 shipped 👩‍💻 on time ✅',
    'quotes': 'She said "deploy" and "ship it".',
    'backslashes': r'C:\data\models\v2 and \\server\share',
    'control': 'tab\there\nnew line\rcr\x01\x1f\x7f end',
    'mixed': '"\\\x02 🚀 é\n',
}


@lru_cache(maxsize=1)
def bounds():
    return beta.compute_public_beta_bounds()


@pytest.fixture
def prod_root(tmp_path, monkeypatch):
    import jobfit.config
    monkeypatch.setattr(jobfit.config, 'PROD_LEDGER_ROOT', tmp_path.resolve())
    return tmp_path.resolve()


def beta_settings(root, daily='5', hard_stop='25', budget='25', public='1', live='1'):
    return get_production_settings({
        'JOBFIT_ENV': 'prod', 'DATABASE_URL': 'postgresql://u:p@db/prod', 'JOBFIT_INTERNAL_TOKEN': 'i' * 32,
        'JOBFIT_LIVE_ENABLED': live, 'JOBFIT_PUBLIC_LIVE': public, 'OPENROUTER_API_KEY': 'sk-test',
        'JOBFIT_OWNER_TOKEN': 'o' * 32, 'JOBFIT_IP_HMAC_KEY': 'h' * 32,
        'JOBFIT_USAGE_LEDGER': str(root / 'usage_ledger.jsonl'), 'JOBFIT_DAILY_BUDGET_USD': daily,
        'API_BUDGET_USD': budget, 'API_HARD_STOP_USD': hard_stop})


# --- historical Phase 2A evidence is unchanged ------------------------------------------------------------

def test_the_phase_2a_bound_and_config_are_unchanged():
    legacy = pb.compute_phase_bounds()
    assert legacy.full_analysis_upper_bound == LEGACY_FULL
    assert pb.DEFAULT_CONFIG == REPO_ROOT / 'config/cp3/phase_bounds_v1.yaml'
    assert yaml.safe_load(pb.DEFAULT_CONFIG.read_text())['version'] == 'cp3-phase-bounds-v1'


@pytest.mark.parametrize('daily', ['2', '5'])
def test_legacy_full_analysis_eligibility_keeps_its_meaning(prod_root, daily):
    settings = beta_settings(prod_root, daily=daily)
    assert pb.public_live_eligible(settings, pb.compute_phase_bounds()) is False


# --- the versioned beta profile -------------------------------------------------------------------------

def test_the_beta_bounds_are_exact_and_pinned():
    b = bounds()
    assert b.version == 'cp3-public-beta-bounds-v1'
    got = {'parse': b.parse_max, 'search': b.search_max, 'extraction': b.extraction_max,
           'matching': b.matching_max, 'fallback': b.fallback_max, 'job_analysis': b.job_analysis_max}
    assert got == EXPECTED
    assert b.phase_bounds() == {k: EXPECTED[k] for k in ('parse', 'search', 'job_analysis')}
    assert b.job_analysis_max == b.extraction_max + b.matching_max + b.fallback_max
    assert b.details['embed_max_bytes'] == 16384 - 4 + pb.EMBED_OVERHEAD_BYTES


def test_every_beta_phase_fits_the_five_dollar_cap_and_none_fits_two():
    phase = bounds().phase_bounds()
    assert all(v <= Decimal('5') for v in phase.values())
    assert phase['job_analysis'] > Decimal('2')


def test_a_fresh_find_jobs_first_analysis_fits_the_configured_daily_cap(prod_root):
    """parse + search + the first job_analysis of a new Find Jobs session, all on one day."""
    b, settings = bounds(), beta_settings(prod_root)
    first = b.parse_max + b.search_max + b.job_analysis_max
    assert first == Decimal('4.0629163')
    assert first <= Decimal(str(settings.daily_budget_usd)) == Decimal('5')


def test_the_beta_uses_the_same_frozen_sources_as_phase_2a():
    legacy, cfg = (yaml.safe_load(p.read_text()) for p in (pb.DEFAULT_CONFIG, beta.DEFAULT_BETA_CONFIG))
    for key in ('pipeline_config', 'route_rules', 'parse_model', 'parse_dynamic_output'):
        assert cfg[key] == legacy[key]
    b, legacy_bounds = bounds(), pb.compute_phase_bounds()
    for chain in ('parse', 'extraction', 'matching', 'fallback'):
        assert b.chains[chain].price == legacy_bounds.chains[chain].price


def write_config(tmp_path, **changes):
    cfg = yaml.safe_load(beta.DEFAULT_BETA_CONFIG.read_text())
    for key, value in changes.items():
        if key.startswith('env_'):
            if value is None:
                cfg['envelopes'].pop(key[4:])
            else:
                cfg['envelopes'][key[4:]] = value
        elif value is None:
            cfg.pop(key)
        else:
            cfg[key] = value
    path = tmp_path / 'beta.yaml'
    path.write_text(yaml.safe_dump(cfg))
    return path


@pytest.mark.parametrize('changes, message', [
    ({'version': 'cp3-public-beta-bounds-v2'}, 'unexpected version'),
    ({'decision': 'D-096'}, 'unexpected version'),
    ({'phases': ['parse', 'recommendation']}, 'phases'),
    ({'pipeline_config': 'config/pipeline_v1.yaml'}, 'pipeline_config differs'),
    ({'route_rules': 'config/versions/other.json'}, 'route_rules differs'),
    ({'parse_model': 'gpt-6-sol'}, 'parse_model differs'),
    ({'env_max_units': None}, 'missing'),
    ({'env_surprise': 1}, 'unknown'),
    ({'env_max_units': 0}, 'positive integer'),
    ({'env_cv_document_max_bytes': True}, 'positive integer'),
    ({'env_extraction_document_max_bytes': 4}, 'above 4 bytes'),
    ({'env_cv_document_max_bytes': 100_005}, 'frozen CV character limit'),
    ({'env_jd_document_max_bytes': 100_005}, 'frozen extract_jd limit'),
    ({'env_appended_message_max_bytes': 100}, 'repair message bound'),
])
def test_an_invalid_beta_profile_fails_closed(tmp_path, changes, message):
    with pytest.raises(ConfigurationError, match=message):
        beta.compute_public_beta_bounds(write_config(tmp_path, **changes))


def test_a_missing_beta_profile_fails_closed(tmp_path):
    with pytest.raises(ConfigurationError):
        beta.compute_public_beta_bounds(tmp_path / 'absent.yaml')


# --- additive per-phase eligibility ---------------------------------------------------------------------

def test_beta_eligibility_is_additive_and_fails_closed(prod_root):
    b = bounds()
    good = beta_settings(prod_root)
    assert beta.public_beta_phase_eligible(good, b) is True
    assert pb.public_live_eligible(good, pb.compute_phase_bounds()) is False     # legacy meaning kept
    assert beta.public_beta_phase_eligible(beta_settings(prod_root, daily='2'), b) is False
    assert beta.public_beta_phase_eligible(beta_settings(prod_root, public='0'), b) is False
    assert beta.public_beta_phase_eligible(object(), b) is False
    assert beta.public_beta_phase_eligible(good, pb.compute_phase_bounds()) is False
    assert beta.public_beta_phase_eligible(good, dataclasses.replace(b, version='other')) is False
    assert beta.public_beta_phase_eligible(good, dataclasses.replace(b, matching_max=Decimal('NaN'))) is False
    assert beta.public_beta_phase_eligible(good, dataclasses.replace(b, matching_max=Decimal('9'))) is False


def test_the_beta_budget_settings_keep_the_existing_invariant(prod_root):
    s = beta_settings(prod_root)
    assert (s.daily_budget_usd, s.api_hard_stop_usd, s.api_budget_usd) == (5.0, 25.0, 25.0)
    with pytest.raises(ConfigurationError, match='must not be above'):
        beta_settings(prod_root, daily='30')
    with pytest.raises(ConfigurationError, match='must not be above'):
        beta_settings(prod_root, hard_stop='26')


# --- the canonical byte measure through the actual frozen serialization path ----------------------------

class Stop(Exception):
    pass


class CapturingSDK:
    def __init__(self):
        self.messages = []
        from types import SimpleNamespace
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def with_options(self, **kw):
        return self

    def create(self, **kw):
        self.messages.append(kw['messages'])
        raise Stop('captured')


class RecordingGuard:
    def __init__(self):
        self.costs = []

    def check(self, cost):
        self.costs.append(cost)


def frozen_client(tmp_path):
    from jobfit.config import Settings
    from jobfit.llm.runtime import build_runtime_client
    sdk = CapturingSDK()
    client = build_runtime_client(Settings(openrouter_api_key='k' * 40, usage_ledger=tmp_path / 'ledger.jsonl'),
                                  REPO_ROOT / 'config/versions/pipeline_cp23_freeze_candidate_v4_20261006.yaml',
                                  run_id='probe', sdk_client=sdk)
    client.guard = RecordingGuard()
    return client, sdk


def guard_measure(messages) -> int:
    """The frozen OpenRouterClient guard's message measure (the est_in message term)."""
    return len(json.dumps(messages, ensure_ascii=False).encode())


def run_validated(tmp_path, value):
    from pydantic import BaseModel

    from jobfit.llm.structured import StageFailure, validated_call

    class Out(BaseModel):
        answer: str
    client, sdk = frozen_client(tmp_path)
    with pytest.raises((Stop, StageFailure)):
        validated_call(client, model='deepseek-flash', prompt='p', payload={'before': 1, 'doc': value, 'after': 2},
                       output_model=Out, task='cv_parsing', validate=lambda o: None, max_tokens=100)
    return client, sdk


@pytest.mark.parametrize('name', sorted(SAMPLES))
def test_document_bytes_equals_the_frozen_validated_call_and_guard_measure(tmp_path, name):
    from jobfit.llm.client import estimate_cost, strict_schema
    value = SAMPLES[name]
    base_client, base_sdk = run_validated(tmp_path / 'base', '')
    client, sdk = run_validated(tmp_path / 'value', value)
    measured = guard_measure(sdk.messages[0])
    assert measured - guard_measure(base_sdk.messages[0]) == document_bytes(value) - document_bytes('')
    # The same number drives the frozen guard's recorded upper cost.
    from pydantic import BaseModel

    class Out(BaseModel):
        answer: str
    schema = len(json.dumps(strict_schema(Out.model_json_schema())).encode())
    price = client._price('deepseek-flash')
    assert client.guard.costs[0] == estimate_cost(price, measured + schema + 512, 100)


def frozen_parse_messages(tmp_path, cv_text):
    from jobfit.cv.parser import parse_cv
    from jobfit.cv.text_extract import TextResult
    client, sdk = frozen_client(tmp_path)
    try:
        parse_cv(TextResult(text=cv_text), cv_id='CVX', analysis_date=date(2026, 10, 8), client=client,
                 model='deepseek-flash', is_synthetic=True)
    except Stop:
        pass
    return sdk.messages[0]


def frozen_extract_messages(tmp_path, jd_text):
    from jobfit.extraction.audited import ExtractionSpec
    from jobfit.extraction.jd_extractor import extract_jd
    cfg = yaml.safe_load((REPO_ROOT / 'config/versions/pipeline_cp23_freeze_candidate_v4_20261006.yaml').read_text())
    client, sdk = frozen_client(tmp_path)
    try:
        extract_jd(jd_text, job_id='pasted', client=client, model=cfg['extraction_model'], cache=None,
                   scope='session_jd', spec=ExtractionSpec(REPO_ROOT / cfg['jd_prompt_file'], cfg['jd_prompt_version']),
                   dynamic_output=True)
    except Stop:
        pass
    return sdk.messages[0]


def contained(messages, value) -> bool:
    """The value's twice-encoded form sits in the guard-measured messages with document_bytes bytes."""
    twice = json.dumps(json.dumps(value, ensure_ascii=False), ensure_ascii=False)[1:-1]
    return twice in json.dumps(messages, ensure_ascii=False) and len(twice.encode()) == document_bytes(value)


@pytest.mark.parametrize('name', ['ascii', 'multibyte', 'emoji', 'quotes', 'backslashes', 'mixed'])
def test_document_bytes_matches_the_frozen_parse_and_extraction_payloads(tmp_path, name):
    text = 'Data analyst. ' + SAMPLES[name] + ' Python SQL.'
    assert contained(frozen_parse_messages(tmp_path / 'p', text), text)
    jd = 'Requirements:\n- Python and SQL ' + SAMPLES[name] + '\n- Docker\n'
    assert contained(frozen_extract_messages(tmp_path / 'e', jd), jd)


def test_document_bytes_matches_the_frozen_matching_payload(tmp_path):
    from jobfit.extraction.saved_records import load_record
    from jobfit.matching.evidence_matcher import match_evidence
    from jobfit.recommend.service import extraction_from_record
    from tests.test_cv_upload_pipeline import parsed
    cv = parsed()
    rows = [json.loads(line) for line in (REPO_ROOT / 'data/processed/jobs_features.jsonl').read_text().splitlines()]
    extraction = next(e for e, _ in (extraction_from_record(load_record(r['final_cluster_id'])) for r in rows) if e)
    client, sdk = frozen_client(tmp_path)
    try:
        match_evidence(cv, extraction, client=client, model='gpt-6-sol', dynamic_output=True)
    except Stop:
        pass
    messages = sdk.messages[0]
    assert contained(messages, extraction.model_dump(mode='json'))
    assert contained(messages, cv.profile.raw_text)


@pytest.mark.parametrize('name', sorted(SAMPLES))
def test_the_worst_case_argument_holds_per_value(name):
    """Once-encoded <= twice-encoded and UTF-8 <= content bytes, so the ASCII filler is the worst case."""
    value = SAMPLES[name]
    once = len(json.dumps(value, ensure_ascii=False).encode())
    assert once <= document_bytes(value)
    assert len(value.encode()) <= text_content_bytes(value)
    filler = beta.filler_text(1000)
    assert document_bytes(filler) == 1000 and len(json.dumps(filler).encode()) == 998


def test_text_that_is_not_valid_utf8_cannot_be_measured():
    with pytest.raises(UnicodeEncodeError):
        document_bytes('lone surrogate \ud800')


# --- the inventory envelope assumption and corpus coverage (reported, not tuned) -------------------------

@lru_cache(maxsize=1)
def corpus():
    rows = [json.loads(line) for line in (REPO_ROOT / 'data/processed/jobs_features.jsonl').read_text().splitlines()]
    return [r for r in rows if r.get('role_group') == 'target' and r.get('description_clean')]


def test_inventory_quotes_never_exceed_their_jd_bytes():
    from jobfit.extraction.audited import qualification_inventory
    for row in corpus():
        text = row['description_clean']
        inventory = qualification_inventory(text)
        assert sum(text_content_bytes(q['source_quote']) for q in inventory) <= text_content_bytes(text)


def test_envelope_coverage_of_the_corpus_and_the_saved_extractions():
    from jobfit.extraction.audited import qualification_inventory
    from jobfit.extraction.saved_records import load_record
    from jobfit.recommend.service import extraction_from_record
    env = bounds().envelopes
    jds = corpus()
    jd_fit = sum(document_bytes(r['description_clean']) <= env.jd_document_max_bytes
                 and len(qualification_inventory(r['description_clean'])) <= env.max_inventory_items for r in jds)
    extractions = [e for e, _ in (extraction_from_record(load_record(r['final_cluster_id'])) for r in jds) if e]
    ext_fit = sum(document_bytes(e.model_dump(mode='json')) <= env.extraction_document_max_bytes
                  and len(e.units) <= env.max_units for e in extractions)
    print(f'corpus JDs within the beta envelope: {jd_fit}/{len(jds)}; saved extractions: {ext_fit}/{len(extractions)}')
    assert len(extractions) > 0 and ext_fit == len(extractions)
    assert jd_fit / len(jds) >= 0.99
