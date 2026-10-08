"""Deterministic phase bounds of the CP3 controlled public beta (D-103). No provider call is made.

Additive to the historical Phase 2A calculator (``phase_bounds.compute_phase_bounds``, D-096),
which stays unchanged and keeps reproducing the full-analysis bound of US$84.7704449. This module
reuses its building blocks (call-chain regions, reachable sequences, prices, frozen message texts)
and adds only what D-103 defines:

- three phases: ``parse`` (one CV parse), ``search`` (one CV query embedding, no LLM) and
  ``job_analysis`` (exactly one JD: extraction, Sol matching and the Luna fallback);
- byte envelopes measured with the canonical ``document_bytes`` (the bytes a value adds to the
  frozen guard's messages) instead of characters, from config/cp3/public_beta_bounds_v1.yaml.

Worst-case inputs. Cost grows with the guard's message bytes (the twice-encoded payload) and with
the frozen estimate (the once-encoded payload / 4), and both grow with each value's size. For any
character, once-encoded bytes <= twice-encoded bytes and UTF-8 bytes <= twice-encoded bytes. A
plain ASCII letter reaches equality in all three, so a value made of 'x' with ``document_bytes``
exactly at its envelope maximizes both quantities at once and bounds every admissible value.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from jobfit.config import EVIDENCE_PROMPT_FILE, GUIDELINE_FILE, REPO_ROOT, ConfigurationError
from jobfit.llm import phase_bounds as pb
from jobfit.llm.document_bytes import document_bytes
from jobfit.llm.output_policy import MODEL_OUTPUT_LIMIT, estimate_input_tokens, output_allowance
from jobfit.llm.structured import REPAIR_CONTEXT_MAX_BYTES, STRUCTURED_MAX_TOKENS

DEFAULT_BETA_CONFIG = REPO_ROOT / 'config/cp3/public_beta_bounds_v1.yaml'
VERSION = 'cp3-public-beta-bounds-v1'
DECISION = 'D-103'
PHASES = ('parse', 'search', 'job_analysis')
FROZEN_JD_MAX_CHARS = 100_000          # the frozen extract_jd refusal limit (checked against its source)
FILLER = 'x'
ENVELOPE_KEYS = ('cv_document_max_bytes', 'jd_document_max_bytes', 'max_inventory_items',
                 'extraction_document_max_bytes', 'max_units', 'short_field_max_chars',
                 'max_list_index_digits', 'appended_message_max_bytes')


@dataclass(frozen=True)
class BetaEnvelopes:
    cv_document_max_bytes: int
    jd_document_max_bytes: int
    max_inventory_items: int
    extraction_document_max_bytes: int
    max_units: int
    short_field_max_chars: int
    max_list_index_digits: int
    appended_message_max_bytes: int


@dataclass(frozen=True)
class PublicBetaBounds:
    parse_max: Decimal
    search_max: Decimal
    extraction_max: Decimal
    matching_max: Decimal
    fallback_max: Decimal
    version: str
    config_sha256: str
    envelopes: BetaEnvelopes
    details: dict = field(default_factory=dict, compare=False)
    chains: dict = field(default_factory=dict, compare=False, repr=False)

    @property
    def job_analysis_max(self) -> Decimal:
        return self.extraction_max + self.matching_max + self.fallback_max

    def phase_bounds(self) -> dict[str, Decimal]:
        return {'parse': self.parse_max, 'search': self.search_max, 'job_analysis': self.job_analysis_max}

    def breakdown(self) -> dict:
        return {'version': self.version, 'config_sha256': self.config_sha256,
                **{k: str(v) for k, v in self.phase_bounds().items()},
                'extraction_max': str(self.extraction_max), 'matching_max': str(self.matching_max),
                'fallback_max': str(self.fallback_max)}


def filler_text(max_document_bytes: int) -> str:
    """A string whose ``document_bytes`` is exactly ``max_document_bytes`` (see the module note)."""
    text = FILLER * (max_document_bytes - 4)
    if document_bytes(text) != max_document_bytes:
        raise ConfigurationError('the filler does not reach the envelope exactly')
    return text


def inventory_envelope(jd_document_max_bytes: int, max_items: int, short: int) -> list[dict]:
    """Inventory records with the most bytes an admissible JD can produce.

    The frozen qualification_inventory copies each JD line at most once into at most one record
    (a bullet's text, or a wrapped line joined with its newline), so the quotes' content bytes
    total at most the JD's content bytes. Source ids are the frozen 'Q01'... form.
    """
    total = jd_document_max_bytes - 4
    per_item, extra = divmod(total, max_items)
    return [{'source_id': f'Q{i + 1:02d}', 'source_quote': FILLER * (per_item + (i < extra))}
            for i in range(max_items)]


def _envelopes(raw: dict) -> BetaEnvelopes:
    missing = [k for k in ENVELOPE_KEYS if k not in raw]
    unknown = sorted(set(raw) - set(ENVELOPE_KEYS))
    if missing or unknown:
        raise ConfigurationError(f'public-beta envelopes: missing {missing}, unknown {unknown}')
    env = BetaEnvelopes(**{k: pb._positive_int(raw[k], k) for k in ENVELOPE_KEYS})
    for k in ('cv_document_max_bytes', 'jd_document_max_bytes', 'extraction_document_max_bytes'):
        if getattr(env, k) <= 4:
            raise ConfigurationError(f'{k} must be above 4 bytes')
    return env


def load_beta_config(config_path: Path = DEFAULT_BETA_CONFIG) -> tuple[dict, bytes]:
    config_path = Path(config_path)
    raw = config_path.read_bytes() if config_path.exists() else b''
    cfg = pb._load_yaml(config_path)
    if cfg.get('version') != VERSION or cfg.get('decision') != DECISION:
        raise ConfigurationError('public-beta bounds config has an unexpected version or decision')
    if tuple(cfg.get('phases') or ()) != PHASES:
        raise ConfigurationError('public-beta phases must be exactly parse, search, job_analysis')
    legacy = pb._load_yaml(pb.DEFAULT_CONFIG)
    for key in ('pipeline_config', 'route_rules', 'parse_model', 'parse_dynamic_output'):
        if cfg.get(key) != legacy.get(key):   # the same frozen sources as the Phase 2A bound
            raise ConfigurationError(f'public-beta {key} differs from the Phase 2A frozen source')
    return cfg, raw


def compute_public_beta_bounds(config_path: Path = DEFAULT_BETA_CONFIG, *,
                               models_file: Path = pb.MODELS_FILE) -> PublicBetaBounds:
    import json

    from jobfit.cv.parser import CVWire
    from jobfit.cv.text_extract import MAX_CHARACTERS
    from jobfit.extraction.audited import AuditedExtraction
    from jobfit.matching.evidence_matcher import EvidenceResponse

    cfg, raw = load_beta_config(config_path)
    env = _envelopes(cfg.get('envelopes') or {})
    pipeline = pb._load_yaml(REPO_ROOT / cfg['pipeline_config'])
    rules_path = REPO_ROOT / cfg['route_rules']
    if not rules_path.is_file():
        raise ConfigurationError('route rules file is missing')
    route_rules = json.loads(rules_path.read_text())['models']
    models = pb._load_yaml(models_file)
    if pipeline.get('max_validation_repairs') != 1 or pipeline.get('max_length_continuations') != 1:
        raise ConfigurationError('the bound models one repair and one continuation, as the frozen pipeline')
    # A beta envelope must stay inside the frozen limits (content bytes >= characters).
    if env.cv_document_max_bytes - 4 > MAX_CHARACTERS:
        raise ConfigurationError('cv_document_max_bytes is above the frozen CV character limit')
    pb._check_frozen_jd_limit(FROZEN_JD_MAX_CHARS)
    if env.jd_document_max_bytes - 4 > FROZEN_JD_MAX_CHARS:
        raise ConfigurationError('jd_document_max_bytes is above the frozen extract_jd limit')

    C = pb._positive_int(MODEL_OUTPUT_LIMIT, 'MODEL_OUTPUT_LIMIT')
    repair_context = 2 * REPAIR_CONTEXT_MAX_BYTES + pb.MESSAGE_FRAMING_BYTES
    short = env.short_field_max_chars

    def appended_for(schema_model) -> int:
        bound = pb.appended_message_bound(schema_model, env.max_list_index_digits)
        if bound > env.appended_message_max_bytes:
            raise ConfigurationError(f'the {schema_model.__name__} repair message bound is above '
                                     'appended_message_max_bytes')
        return bound

    def chain(task, price, prompt, payload, schema_model, *, dynamic, units, request_extra=None):
        # The same two-region construction as the Phase 2A calculator.
        base = pb._messages_bytes(prompt, {**payload, **(request_extra or {})})
        common = dict(task=task, price=price, schema_bytes=pb._strict_schema_bytes(schema_model),
                      appended_message_bytes=appended_for(schema_model), repair_context_bytes=repair_context)
        notes = {}
        if not dynamic:
            regions = {'fixed_limit': pb.ChainSpec(base_message_bytes=base,
                                                   sequences=pb.reachable_sequences(STRUCTURED_MAX_TOKENS, None),
                                                   reachable=True, **common)}
            return pb.ChainBound(task, price, regions, notes)
        L = output_allowance(task, estimate_input_tokens(prompt, payload, schema_model.model_json_schema()), units)
        regions = {'envelope': pb.ChainSpec(base_message_bytes=base, sequences=pb.reachable_sequences(L, C),
                                            reachable=True, **common)}
        if L == C:   # an input below the envelope may get L < C, where a continuation is reachable
            t_max = pb.max_tokens_below_limit(task, C)
            if t_max is not None:
                below = min(base, pb.base_bytes_below_limit(prompt, schema_model, t_max, request_extra))
                regions['below_limit'] = pb.ChainSpec(base_message_bytes=below,
                                                      sequences=pb.reachable_sequences(C - 1, C),
                                                      reachable=True, **common)
                notes['below_limit_max_estimate_tokens'] = t_max
        notes['initial_allowance'] = L
        return pb.ChainBound(task, price, regions, notes)

    cv_text = filler_text(env.cv_document_max_bytes)

    # parse: the frozen parse_cv payload {'cv_text': consented text}, fixed STRUCTURED_MAX_TOKENS.
    if cfg.get('parse_dynamic_output') is not False:
        raise ConfigurationError('parse_dynamic_output must be false (the CP2.4 parse used the default)')
    parse = chain('cv_parsing', pb.resolve_parse_model(cfg.get('parse_model'), models_file),
                  pb.CV_PARSE_PROMPT.read_text(), {'cv_text': cv_text}, CVWire, dynamic=False, units=1)

    # search: one embedding of the prepared CV text (a prefix of the normalized consented text);
    # the frozen embed guard counts its UTF-8 bytes + 100, and UTF-8 bytes <= content bytes.
    emb_key = pipeline.get('embedding_model')
    emb = (models.get('embeddings') or {}).get(emb_key)
    if not emb:
        raise ConfigurationError('embedding model is not in config/models_v1.yaml')
    embed_bytes = env.cv_document_max_bytes - 4 + pb.EMBED_OVERHEAD_BYTES
    search_max = Decimal(embed_bytes) * pb._price(emb.get('input_per_m'), emb_key) / pb.ONE_MILLION

    # job_analysis: the frozen extract_jd payload, then the frozen match_evidence request.
    jd_prompt = (REPO_ROOT / pipeline['jd_prompt_file']).read_text() + '\n\n' + GUIDELINE_FILE.read_text()
    ext_payload = {'job_id': pb.PAD * short, 'jd_text': filler_text(env.jd_document_max_bytes),
                   'qualification_inventory': inventory_envelope(env.jd_document_max_bytes,
                                                                 env.max_inventory_items, short)}
    extraction = chain('jd_extraction', pb._chat_price(pipeline.get('extraction_model'), models, route_rules),
                       jd_prompt, ext_payload, AuditedExtraction, dynamic=True, units=env.max_inventory_items)
    ev_prompt = EVIDENCE_PROMPT_FILE.read_text() + '\n\n' + GUIDELINE_FILE.read_text()
    match_payload = {'extraction': filler_text(env.extraction_document_max_bytes), 'cv_id': pb.PAD * short,
                     'analysis_date': '0000-00-00',
                     'verified_duration_years': {pb.PAD * short + str(i): pb.LONGEST_FLOAT
                                                 for i in range(env.max_units)},
                     'cv_text': cv_text}
    match_extra = {'max_tokens': C, 'registry': '0' * 64}
    matching = chain('evidence_matching', pb._chat_price(pipeline.get('matching_model'), models, route_rules),
                     ev_prompt, match_payload, EvidenceResponse, dynamic=True, units=env.max_units,
                     request_extra=match_extra)
    fallback = chain('evidence_matching', pb._chat_price(pipeline.get('matching_fallback_model'), models, route_rules),
                     ev_prompt, match_payload, EvidenceResponse, dynamic=True, units=env.max_units,
                     request_extra=match_extra)

    chains = {'parse': parse, 'extraction': extraction, 'matching': matching, 'fallback': fallback}
    details = {'version': VERSION, 'decision': DECISION, 'model_output_limit': C,
               'envelopes': {k: getattr(env, k) for k in ENVELOPE_KEYS},
               'embed_max_bytes': embed_bytes,
               **{name: c.describe() for name, c in chains.items()}}
    return PublicBetaBounds(parse_max=parse.cost(), search_max=search_max, extraction_max=extraction.cost(),
                            matching_max=matching.cost(), fallback_max=fallback.cost(), version=VERSION,
                            config_sha256=hashlib.sha256(raw).hexdigest(), envelopes=env,
                            details=details, chains=chains)


def public_beta_phase_eligible(settings, bounds: PublicBetaBounds) -> bool:
    """D-103: every beta phase bound fits the daily cap in complete prod public-live settings.

    Additive to the historical ``phase_bounds.public_live_eligible`` (full analysis, D-096), which
    keeps its meaning. Fails closed: any doubt returns False.
    """
    from jobfit.config import ProductionSettings, check_production_invariants
    if not isinstance(settings, ProductionSettings) or not isinstance(bounds, PublicBetaBounds):
        return False
    try:
        check_production_invariants(settings)
    except (ConfigurationError, AttributeError, TypeError, ValueError):
        return False
    if not (settings.live_enabled is True and settings.public_live is True and settings.environment == 'prod'):
        return False
    if bounds.version != VERSION:
        return False
    values = tuple(bounds.phase_bounds().values())
    if not all(isinstance(v, Decimal) and v.is_finite() and v > 0 for v in values):
        return False
    cap = Decimal(str(settings.daily_budget_usd))       # invariants: cap <= hard stop <= budget
    return all(v <= cap for v in values)
