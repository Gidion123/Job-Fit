"""Deterministic worst-case cost bounds for the live phases (D-096). No provider call is made.

The bounds follow the frozen runtime exactly where it decides cost:

- per call, the frozen OpenRouter client's own guard estimate: input bytes of the JSON messages
  plus the strict schema plus 512, times the input price, plus max_tokens times the output price;
- per call chain, the frozen ``validated_call`` state machine: one initial attempt, at most one
  validation repair at the current limit and, only with a model output limit, at most one length
  continuation at M = min(2L, C) when M > L. Both orders are reachable, so the larger is used;
- per job, the frozen ``analyze_job``: the Luna fallback chain runs after a failed Sol chain, so the
  two are added.

Models, K, prices, limits, prompts and schemas come from their frozen sources. Only CP3 envelopes
come from config/cp3/phase_bounds_v1.yaml. If the initial allowance L cannot be derived (a unit
envelope is missing), a 3C accounting envelope is used instead. It is not a reachable call
sequence: it is a fail-closed upper bound, and public live stays ineligible.
"""
from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import yaml

from jobfit.config import EVIDENCE_PROMPT_FILE, GUIDELINE_FILE, REPO_ROOT, ConfigurationError
from jobfit.llm.output_policy import MODEL_OUTPUT_LIMIT, estimate_input_tokens, output_allowance
from jobfit.llm.structured import REPAIR_CONTEXT_MAX_BYTES, STRUCTURED_MAX_TOKENS

DEFAULT_CONFIG = REPO_ROOT / 'config/cp3/phase_bounds_v1.yaml'
MODELS_FILE = REPO_ROOT / 'config/models_v1.yaml'
CV_PARSE_PROMPT = REPO_ROOT / 'prompts/cv_parsing_v1.md'
GUARD_OVERHEAD_BYTES = 512        # frozen OpenRouterClient._chat_attempt: + 512 for framing
EMBED_OVERHEAD_BYTES = 100        # frozen OpenRouterClient._embed_attempt: + 100 per text
MESSAGE_FRAMING_BYTES = 64        # {"role": ..., "content": ...} around one appended message
PAD = '\x01'                      # JSON-escapes to \u0001: the most bytes per character
LONGEST_FLOAT = 2.2250738585072014e-308   # 23 characters: the longest JSON form of a finite float
ONE_MILLION = Decimal(1_000_000)
DERIVED = 'derived'
SUPREMUM = 'fail_closed_supremum'


@dataclass(frozen=True)
class Attempt:
    max_tokens: int
    continuations: int = 0   # appended continuation messages before this attempt
    repairs: int = 0         # appended repair context (prior output + instruction) before this attempt


def reachable_sequences(initial_limit: int, output_limit: int | None) -> dict[str, list[Attempt]]:
    """Reachable call sequences of the frozen validated_call for an initial allowance L.

    ``output_limit`` is the model output limit passed to validated_call (None = no continuation).
    """
    L = _positive_int(initial_limit, 'initial allowance')
    if output_limit is None:
        return {'initial_then_repair': [Attempt(L), Attempt(L, repairs=1)]}
    C = _positive_int(output_limit, 'model output limit')
    if L > C:
        raise ConfigurationError('initial allowance is above the model output limit')
    M = min(2 * L, C)
    if M > L:
        return {'continuation_first': [Attempt(L), Attempt(M, continuations=1), Attempt(M, 1, 1)],
                'repair_first': [Attempt(L), Attempt(L, repairs=1), Attempt(M, 1, 1)]}
    return {'initial_then_repair': [Attempt(L), Attempt(L, repairs=1)]}


def accounting_envelope(output_limit: int) -> list[Attempt]:
    """Fail-closed 3C accounting envelope; deliberately NOT a reachable call sequence."""
    C = _positive_int(output_limit, 'model output limit')
    return [Attempt(C), Attempt(C, continuations=1), Attempt(C, 1, 1)]


@dataclass(frozen=True)
class Price:
    model_id: str
    input_per_m: Decimal
    output_per_m: Decimal


@dataclass(frozen=True)
class ChainSpec:
    """Everything one call chain needs: bytes of the base messages and the schema, and its limit."""
    task: str
    price: Price
    base_message_bytes: int
    schema_bytes: int
    appended_message_bytes: int
    repair_context_bytes: int
    sequences: dict[str, list[Attempt]]
    reachable: bool

    def attempt_cost(self, a: Attempt) -> Decimal:
        input_bytes = (self.base_message_bytes + a.continuations * self.appended_message_bytes
                       + a.repairs * (self.repair_context_bytes + self.appended_message_bytes)
                       + self.schema_bytes + GUARD_OVERHEAD_BYTES)
        return (Decimal(input_bytes) * self.price.input_per_m
                + Decimal(a.max_tokens) * self.price.output_per_m) / ONE_MILLION

    def cost(self) -> Decimal:
        return max(sum((self.attempt_cost(a) for a in seq), Decimal(0)) for seq in self.sequences.values())

    def describe(self) -> dict:
        return {'task': self.task, 'model': self.price.model_id, 'reachable': self.reachable,
                'base_message_bytes': self.base_message_bytes, 'schema_bytes': self.schema_bytes,
                'sequences': {k: [a.max_tokens for a in v] for k, v in self.sequences.items()},
                'chain_cost_usd': str(self.cost())}


@dataclass(frozen=True)
class PhaseBounds:
    parse_max: Decimal
    embed_max: Decimal
    extraction_max: Decimal
    matching_max: Decimal
    fallback_max: Decimal
    bound_basis: str
    config_sha256: str
    details: dict = field(default_factory=dict, compare=False)

    @property
    def recommendation_upper_bound(self) -> Decimal:
        return self.embed_max + self.extraction_max + self.matching_max + self.fallback_max

    @property
    def full_analysis_upper_bound(self) -> Decimal:
        return self.parse_max + self.recommendation_upper_bound

    def breakdown(self, daily_cap_usd: float | Decimal | None = None) -> dict:
        out = {k: str(getattr(self, k)) for k in ('parse_max', 'embed_max', 'extraction_max', 'matching_max',
                                                  'fallback_max', 'recommendation_upper_bound',
                                                  'full_analysis_upper_bound')}
        out['bound_basis'] = self.bound_basis
        out['config_sha256'] = self.config_sha256
        if daily_cap_usd is not None:
            cap = Decimal(str(daily_cap_usd))
            out['daily_cap_usd'] = str(cap)
            out['difference_from_cap_usd'] = str(self.full_analysis_upper_bound - cap)
            out['within_cap'] = self.full_analysis_upper_bound <= cap
        return out


def public_live_eligible(settings, bounds: PhaseBounds) -> bool:
    """D-096: eligible only in complete prod public-live settings with a derived bound within the cap."""
    if not (getattr(settings, 'public_live', False) and getattr(settings, 'environment', None) == 'prod'):
        return False
    if bounds.bound_basis != DERIVED or settings.daily_budget_usd is None:
        return False
    return bounds.full_analysis_upper_bound <= Decimal(str(settings.daily_budget_usd))


# --- loading -------------------------------------------------------------------------------------

def _positive_int(value, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ConfigurationError(f'{name} must be a positive integer')
    return value


def _price(value, name: str, *, allow_zero: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ConfigurationError(f'{name} price is missing or invalid')
    d = Decimal(str(value))
    if not d.is_finite() or d < 0 or (d == 0 and not allow_zero):
        raise ConfigurationError(f'{name} price must be finite and positive')
    return d


def _load_yaml(path: Path) -> dict:
    try:
        return yaml.safe_load(Path(path).read_text(encoding='utf-8')) or {}
    except FileNotFoundError:
        raise ConfigurationError(f'missing configuration file {Path(path).name}') from None


def _chat_price(key: str, models: dict, route_rules: dict) -> Price:
    if not key:
        raise ConfigurationError('model key is missing')
    if key in route_rules:   # RuntimeClient.configure prices Sol/Luna from the frozen route rules
        r = route_rules[key]
        return Price(r['model_id'], _price(r.get('ceiling_in'), key), _price(r.get('ceiling_out'), key))
    m = (models.get('models') or {}).get(key)
    if not m:
        raise ConfigurationError(f'model {key} is not in config/models_v1.yaml')
    return Price(m['id'], _price(m.get('input_per_m'), key), _price(m.get('output_per_m'), key))


def resolve_parse_model(key: str, models_file: Path = MODELS_FILE) -> Price:
    """Runtime check of the CP3 parse model: it must resolve through the frozen model registry."""
    return _chat_price(key, _load_yaml(models_file), {})


def _json_bytes(obj) -> int:
    return len(json.dumps(obj, ensure_ascii=False).encode('utf-8'))


def _messages_bytes(prompt: str, payload: dict) -> int:
    # Same construction as the frozen validated_call, measured like the frozen client guard.
    messages = [{'role': 'system', 'content': prompt},
                {'role': 'user', 'content': json.dumps({'untrusted_document_data': payload}, ensure_ascii=False)}]
    return _json_bytes(messages)


def _strict_schema_bytes(model) -> int:
    from jobfit.llm.client import strict_schema
    return len(json.dumps(strict_schema(model.model_json_schema())).encode())


def _check_frozen_jd_limit(value: int) -> None:
    from jobfit.extraction import jd_extractor
    if f'len(text)>{value:_}' not in inspect.getsource(jd_extractor.extract_jd):
        raise ConfigurationError('jd_text_max_chars does not match the frozen extract_jd limit')


def compute_phase_bounds(config_path: Path = DEFAULT_CONFIG, *, models_file: Path = MODELS_FILE) -> PhaseBounds:
    from jobfit.cv.parser import CVWire
    from jobfit.cv.text_extract import MAX_CHARACTERS
    from jobfit.extraction.audited import AuditedExtraction
    from jobfit.matching.evidence_matcher import EvidenceResponse

    config_path = Path(config_path)
    raw = config_path.read_bytes() if config_path.exists() else b''
    cfg = _load_yaml(config_path)
    pipeline = _load_yaml(REPO_ROOT / cfg.get('pipeline_config', ''))
    rules_path = REPO_ROOT / cfg.get('route_rules', '')
    if not rules_path.is_file():
        raise ConfigurationError('route rules file is missing')
    route_rules = json.loads(rules_path.read_text())['models']
    models = _load_yaml(models_file)

    if pipeline.get('max_validation_repairs') != 1 or pipeline.get('max_length_continuations') != 1:
        raise ConfigurationError('the bound models one repair and one continuation, as the frozen pipeline')
    k = _positive_int(pipeline.get('stage1_k'), 'stage1_k')
    env = cfg.get('envelopes') or {}
    short = _positive_int(env.get('short_field_max_chars'), 'short_field_max_chars')
    appended = _positive_int(env.get('appended_message_max_bytes'), 'appended_message_max_bytes') + MESSAGE_FRAMING_BYTES
    ext_json = _positive_int(env.get('extraction_json_max_bytes'), 'extraction_json_max_bytes')
    jd_chars = _positive_int(cfg.get('jd_text_max_chars'), 'jd_text_max_chars')
    _check_frozen_jd_limit(jd_chars)
    cv_chars = _positive_int(MAX_CHARACTERS, 'MAX_CHARACTERS')
    max_units = env.get('max_units')
    max_items = env.get('max_inventory_items')
    derived = max_units is not None and max_items is not None
    if derived:
        max_units = _positive_int(max_units, 'max_units')
        max_items = _positive_int(max_items, 'max_inventory_items')
    else:   # input-side counts still need a bound: one unit per 32 bytes of extraction JSON, one item per JD character
        max_units, max_items = ext_json // 32, jd_chars
    repair_context = 2 * REPAIR_CONTEXT_MAX_BYTES + MESSAGE_FRAMING_BYTES   # quotes double when re-escaped
    C = _positive_int(MODEL_OUTPUT_LIMIT, 'MODEL_OUTPUT_LIMIT')
    guideline = GUIDELINE_FILE.read_text()

    def chain(task, price, prompt, payload, schema_model, *, dynamic, units, request_extra=None):
        # The allowance is sized from ``payload``; the request may carry extra context keys.
        if dynamic and derived:
            L = output_allowance(task, estimate_input_tokens(prompt, payload, schema_model.model_json_schema()), units)
            sequences, reachable = reachable_sequences(L, C), True
        elif dynamic:
            sequences, reachable = {'accounting_envelope_3C': accounting_envelope(C)}, False
        else:
            sequences, reachable = reachable_sequences(STRUCTURED_MAX_TOKENS, None), True
        return ChainSpec(task, price, _messages_bytes(prompt, {**payload, **(request_extra or {})}),
                         _strict_schema_bytes(schema_model),
                         appended, repair_context, sequences, reachable)

    # Parse: CV parse prompt, consented CV text up to the extractor's character limit.
    parse_key = cfg.get('parse_model')
    parse_price = resolve_parse_model(parse_key, models_file)
    parse_dynamic = cfg.get('parse_dynamic_output')
    if parse_dynamic is not False:
        raise ConfigurationError('parse_dynamic_output must be false (the CP2.4 parse used the default)')
    parse = chain('cv_parsing', parse_price, CV_PARSE_PROMPT.read_text(), {'cv_text': PAD * cv_chars},
                  CVWire, dynamic=False, units=1)

    # Embedding: one call, raw UTF-8 bytes of the consented text (at most 4 per character) + 100.
    emb_key = pipeline.get('embedding_model')
    emb = (models.get('embeddings') or {}).get(emb_key)
    if not emb:
        raise ConfigurationError('embedding model is not in config/models_v1.yaml')
    embed_max = Decimal(4 * cv_chars + EMBED_OVERHEAD_BYTES) * _price(emb.get('input_per_m'), emb_key) / ONE_MILLION

    # Extraction: JD prompt v1.4 + guideline, JD text up to the frozen limit, its inventory.
    jd_prompt = (REPO_ROOT / pipeline['jd_prompt_file']).read_text() + '\n\n' + guideline
    per_item = max(1, jd_chars // max_items)
    ext_payload = {'job_id': PAD * short, 'jd_text': PAD * jd_chars,
                   'qualification_inventory': [{'source_id': f'Q{i + 1:02d}', 'source_quote': PAD * per_item}
                                               for i in range(max_items)]}
    extraction = chain('jd_extraction', _chat_price(pipeline.get('extraction_model'), models, route_rules),
                       jd_prompt, ext_payload, AuditedExtraction, dynamic=True, units=max_items)

    # Matching and fallback: evidence prompt + guideline, extraction JSON, durations and CV text.
    ev_prompt = EVIDENCE_PROMPT_FILE.read_text() + '\n\n' + guideline
    match_payload = {'extraction': '"' * (ext_json // 2), 'cv_id': PAD * short, 'analysis_date': '0000-00-00',
                     'verified_duration_years': {PAD * short + str(i): LONGEST_FLOAT for i in range(max_units)},
                     'cv_text': PAD * cv_chars}
    # The frozen match_evidence request also carries max_tokens and the 64-hex registry hash.
    match_extra = {'max_tokens': C, 'registry': '0' * 64}
    matching = chain('evidence_matching', _chat_price(pipeline.get('matching_model'), models, route_rules),
                     ev_prompt, match_payload, EvidenceResponse, dynamic=True, units=max_units,
                     request_extra=match_extra)
    fallback = chain('evidence_matching', _chat_price(pipeline.get('matching_fallback_model'), models, route_rules),
                     ev_prompt, match_payload, EvidenceResponse, dynamic=True, units=max_units,
                     request_extra=match_extra)

    details = {'k': k, 'model_output_limit': C, 'cv_max_chars': cv_chars, 'jd_max_chars': jd_chars,
               'envelopes': dict(env), 'parse': parse.describe(), 'extraction': extraction.describe(),
               'matching': matching.describe(), 'fallback': fallback.describe(),
               'note': ('3C accounting envelope: conservative fail-closed bound, not reachable attempts'
                        if not derived else 'reachable call chains from the derived initial allowance')}
    return PhaseBounds(parse_max=parse.cost(), embed_max=embed_max, extraction_max=k * extraction.cost(),
                       matching_max=k * matching.cost(), fallback_max=k * fallback.cost(),
                       bound_basis=DERIVED if derived else SUPREMUM,
                       config_sha256=hashlib.sha256(raw).hexdigest(), details=details)
