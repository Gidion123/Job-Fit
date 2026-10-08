"""Deterministic worst-case cost bounds for the live phases (D-096). No provider call is made.

The bounds follow the frozen runtime exactly where it decides cost:

- per call, the frozen OpenRouter client's own guard estimate: input bytes of the JSON messages
  plus the strict schema plus 512, times the input price, plus max_tokens times the output price;
- per call chain, the frozen ``validated_call`` state machine: one initial attempt, at most one
  validation repair at the current limit and, only with a model output limit, at most one length
  continuation at M = min(2L, C) when M > L. Both orders are reachable, so the larger is used;
- per job, the frozen ``analyze_job``: the Luna fallback chain runs after a failed Sol chain, so the
  two are added.

A dynamic chain is bounded over every reachable initial allowance L, in two regions:

- ``envelope``: L from the largest admissible input (the CP3 envelopes, padded with the costliest
  character). It bounds every input, but its L may be C, where no continuation is reachable;
- ``below_limit``: every input whose L is below C. Such an input has at most ``T_max`` estimated
  tokens (the largest T with the frozen ``output_allowance(task, T, 1) < C``; one unit is the
  smallest count that reaches the call), so its request is bounded from T_max, and L <= C - 1.

Models, K, prices, limits, prompts and schemas come from their frozen sources. Only CP3 envelopes
come from config/cp3/phase_bounds_v1.yaml. If the initial allowance L cannot be derived (a unit
envelope is missing), a 3C accounting envelope is used instead. It is not a reachable call
sequence: it is a fail-closed upper bound, and public live stays ineligible.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import re
import textwrap
import typing
from dataclasses import dataclass, field
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

from jobfit.config import EVIDENCE_PROMPT_FILE, GUIDELINE_FILE, REPO_ROOT, ConfigurationError
from jobfit.llm.output_policy import MODEL_OUTPUT_LIMIT, estimate_input_tokens, output_allowance
from jobfit.llm.structured import REPAIR_CONTEXT_MAX_BYTES, STRUCTURED_MAX_TOKENS

DEFAULT_CONFIG = REPO_ROOT / 'config/cp3/phase_bounds_v1.yaml'
MODELS_FILE = REPO_ROOT / 'config/models_v1.yaml'
CV_PARSE_PROMPT = REPO_ROOT / 'prompts/cv_parsing_v1.md'
GUARD_OVERHEAD_BYTES = 512        # frozen OpenRouterClient._chat_attempt: + 512 for framing
EMBED_OVERHEAD_BYTES = 100        # frozen OpenRouterClient._embed_attempt: + 100 per text
MESSAGE_FRAMING_BYTES = 64        # {"role": ..., "content": ...} around the assistant prior output
MESSAGE_SEPARATOR_BYTES = 2       # ", " between two messages in the guard's json.dumps(messages)
MAX_SCHEMA_ISSUES = 12            # frozen schema_error_codes keeps the first 12 errors
# Smallest expected_units that reaches output_allowance: jd_extractor passes max(len(inventory), 1);
# match_evidence returns before the call when there are no units.
MIN_REACHABLE_UNITS = 1
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
    """One region of a call chain: bytes of the base messages and the schema, and its limits."""
    task: str
    price: Price
    base_message_bytes: int
    schema_bytes: int
    appended_message_bytes: int
    repair_context_bytes: int
    sequences: dict[str, list[Attempt]]
    reachable: bool

    def attempt_input_bytes(self, a: Attempt) -> int:
        """Largest guard input bytes of this attempt (same quantity as guard_input_bytes)."""
        return (self.base_message_bytes + a.continuations * self.appended_message_bytes
                + a.repairs * (self.repair_context_bytes + self.appended_message_bytes)
                + self.schema_bytes + GUARD_OVERHEAD_BYTES)

    def attempt_cost(self, a: Attempt) -> Decimal:
        return (Decimal(self.attempt_input_bytes(a)) * self.price.input_per_m
                + Decimal(a.max_tokens) * self.price.output_per_m) / ONE_MILLION

    def cost(self) -> Decimal:
        return max(sum((self.attempt_cost(a) for a in seq), Decimal(0)) for seq in self.sequences.values())

    def describe(self) -> dict:
        return {'reachable': self.reachable, 'base_message_bytes': self.base_message_bytes,
                'schema_bytes': self.schema_bytes, 'appended_message_bytes': self.appended_message_bytes,
                'repair_context_bytes': self.repair_context_bytes,
                'sequences': {k: [a.max_tokens for a in v] for k, v in self.sequences.items()},
                'chain_cost_usd': str(self.cost())}


@dataclass(frozen=True)
class ChainBound:
    """A call chain bounded over all its regions: the cost is the largest region cost."""
    task: str
    price: Price
    regions: dict[str, ChainSpec]
    notes: dict = field(default_factory=dict, compare=False)

    @property
    def reachable(self) -> bool:
        return all(r.reachable for r in self.regions.values())

    @property
    def dominant_region(self) -> str:
        return max(self.regions, key=lambda k: self.regions[k].cost())

    def cost(self) -> Decimal:
        return self.regions[self.dominant_region].cost()

    def describe(self) -> dict:
        return {'task': self.task, 'model': self.price.model_id, 'reachable': self.reachable,
                'dominant_region': self.dominant_region, 'chain_cost_usd': str(self.cost()),
                'regions': {k: r.describe() for k, r in self.regions.items()}, **self.notes}


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
    chains: dict = field(default_factory=dict, compare=False, repr=False)

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


def guard_input_bytes(messages: list[dict], output_model: type[BaseModel]) -> int:
    """The frozen client guard's input bytes for one call (OpenRouterClient._chat_attempt).

    A Phase 2B reservation wrapper compares this, for each call it forwards, with
    ChainSpec.attempt_input_bytes of the modelled attempt and refuses any call above it.
    """
    return _json_bytes(messages) + _strict_schema_bytes(output_model) + GUARD_OVERHEAD_BYTES


# --- frozen message texts and the repair-message bound ---------------------------------------------

class _ProbeOut(BaseModel):
    value: int


class _ProbeClient:
    def __init__(self, steps):
        self.steps, self.messages = list(steps), []

    def chat_structured(self, model, messages, output_model, task, max_tokens=2000, temperature=0.0):
        self.messages = [dict(m) for m in messages]
        step = self.steps.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


@lru_cache(maxsize=1)
def frozen_message_texts() -> dict:
    """The appended message texts, captured by running the frozen validated_call with a probe client."""
    from pydantic import ValidationError

    from jobfit.llm.client import TruncatedStructuredResponse
    from jobfit.llm.structured import schema_error_codes, validated_call

    def run(steps, limit):
        client = _ProbeClient(steps)
        validated_call(client, model='probe', prompt='p', payload={}, output_model=_ProbeOut, task='probe',
                       validate=lambda out: None, max_tokens=1, model_output_limit=limit)
        return client.messages

    plain_code = 'invalid_structured_output_or_source'
    first = run([TruncatedStructuredResponse('length'), ValueError('probe'), {'value': 1}], 2)
    second = run([{'value': 'x'}, {'value': 1}], None)
    try:
        _ProbeOut.model_validate({'value': 'x'})
    except ValidationError as exc:
        issues = json.dumps(schema_error_codes(exc, _ProbeOut))
    repair, schema_repair = first[3]['content'], second[2]['content']
    if (len(first) != 4 or plain_code not in repair or not schema_repair.endswith(issues)
            or 'schema_validation' not in schema_repair):
        raise ConfigurationError('the frozen validated_call messages do not have the expected form')
    prefix, suffix = repair.split(plain_code)
    return {'continuation': first[2]['content'], 'repair_prefix': prefix, 'repair_suffix': suffix,
            'schema_repair_prefix': schema_repair[:-len(issues)]}


@lru_cache(maxsize=1)
def _longest_repair_code() -> int:
    """Superset of the codes validated_call can name: every identifier-like string in its source."""
    from jobfit.llm.structured import validated_call
    tree = ast.parse(textwrap.dedent(inspect.getsource(validated_call)))
    return max(len(n.value) for n in ast.walk(tree)
               if isinstance(n, ast.Constant) and isinstance(n.value, str) and re.fullmatch(r'[A-Za-z_]+', n.value))


def _longest_error_type() -> int:
    from pydantic_core.core_schema import ErrorType
    return max(len(t) for t in typing.get_args(ErrorType))


def _schema_names_and_depth(model: type[BaseModel]) -> tuple[int, int]:
    """Longest property name and nesting depth of the JSON schema; recursive schemas fail closed."""
    schema = model.model_json_schema()
    defs = schema.get('$defs', {})
    names: set[str] = set()

    def depth(node, seen) -> int:
        if isinstance(node, list):
            return max((depth(x, seen) for x in node), default=0)
        if not isinstance(node, dict):
            return 0
        if '$ref' in node:
            ref = node['$ref'].split('/')[-1]
            if ref in seen:
                raise ConfigurationError(f'{model.__name__} has a recursive schema; repair messages are unbounded')
            return depth(defs[ref], seen | {ref})
        best = 0
        for key, value in node.items():
            if key == 'properties':
                names.update(value)
                best = max(best, 1 + max((depth(v, seen) for v in value.values()), default=0))
            elif key in ('items', 'additionalProperties', 'anyOf', 'oneOf', 'allOf', 'prefixItems'):
                best = max(best, 1 + depth(value, seen))
        return best

    d = depth({k: v for k, v in schema.items() if k != '$defs'}, frozenset())
    return max(map(len, names | {'<field>'})), d


def worst_repair_message(model: type[BaseModel], index_digits: int) -> dict:
    """A repair message at least as large as any the frozen validated_call can append for ``model``.

    It carries 12 issues, each with the longest pydantic error type and a path of 2 elements per
    schema nesting level (field or index, plus a union tag), each element as long as the longest
    property name, '<field>' or a list index of ``index_digits`` digits. Error input, context and
    messages never enter the frozen repair text.
    """
    texts = frozen_message_texts()
    longest_name, depth = _schema_names_and_depth(model)
    element = 'y' * max(longest_name, _positive_int(index_digits, 'max_list_index_digits'))
    issue = {'type': 'x' * _longest_error_type(), 'path': [element] * (2 * depth + 2)}
    candidates = [texts['continuation'],
                  texts['repair_prefix'] + 'x' * _longest_repair_code() + texts['repair_suffix'],
                  texts['schema_repair_prefix'] + json.dumps([issue] * MAX_SCHEMA_ISSUES)]
    return max(({'role': 'user', 'content': c} for c in candidates), key=_json_bytes)


def appended_message_bound(model: type[BaseModel], index_digits: int) -> int:
    """Bytes one appended continuation or repair instruction can add to the guard's message bytes."""
    return _json_bytes(worst_repair_message(model, index_digits)) + MESSAGE_SEPARATOR_BYTES


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


def max_tokens_below_limit(task: str, output_limit: int) -> int | None:
    """Largest estimated input T with the frozen output_allowance(task, T, 1) below the limit."""
    def below(t):
        return output_allowance(task, t, MIN_REACHABLE_UNITS, output_limit) < output_limit
    if not below(0):
        return None
    hi = 1
    while below(hi):
        hi *= 2
    lo = hi // 2           # below(lo) holds, below(hi) does not
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if below(mid) else (lo, mid)
    return lo


def base_bytes_below_limit(prompt: str, schema_model, max_tokens: int, request_extra: dict | None) -> int:
    """Largest guard message bytes of a request whose estimate is at most ``max_tokens`` tokens.

    The frozen estimate serializes the payload once (ensure_ascii=False) and is at most 4 bytes per
    token; the request serializes the same payload once more inside the user message, which at
    most doubles it (only '"' and '\\' grow, from 2 to 4 bytes; control characters are escaped
    already). Extra request keys are counted twice as well.
    """
    estimate_overhead = _json_bytes({'prompt': prompt, 'payload': {}, 'schema': schema_model.model_json_schema()}) - 2
    payload = max(4 * max_tokens - estimate_overhead, 2)
    extra = _json_bytes(request_extra) - 2 + MESSAGE_SEPARATOR_BYTES if request_extra else 0
    inner = _json_bytes({'untrusted_document_data': {}}) - 2 + payload + extra
    return _json_bytes([{'role': 'system', 'content': prompt}, {'role': 'user', 'content': ''}]) + 2 * inner


def inventory_envelope(jd_chars: int, max_items: int) -> list[dict]:
    """Inventory records whose quotes total exactly the JD character limit.

    The frozen qualification_inventory reads each line of the JD once and puts it in at most one
    record (a bullet's text, or a wrapped line joined by one newline), so its quotes total at most
    len(text). Phase 2B enforces the item count before any billable call.
    """
    per_item, extra = divmod(jd_chars, max_items)
    return [{'source_id': f'Q{i + 1:02d}', 'source_quote': PAD * (per_item + (i < extra))} for i in range(max_items)]


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
    appended_ceiling = _positive_int(env.get('appended_message_max_bytes'), 'appended_message_max_bytes')
    index_digits = _positive_int(env.get('max_list_index_digits'), 'max_list_index_digits')
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

    def appended_for(schema_model) -> int:
        bound = appended_message_bound(schema_model, index_digits)
        if bound > appended_ceiling:
            raise ConfigurationError(f'the {schema_model.__name__} repair message bound is above '
                                     'appended_message_max_bytes')
        return bound

    def chain(task, price, prompt, payload, schema_model, *, dynamic, units, request_extra=None):
        # The allowance is sized from ``payload``; the request may carry extra context keys.
        base = _messages_bytes(prompt, {**payload, **(request_extra or {})})
        common = dict(task=task, price=price, schema_bytes=_strict_schema_bytes(schema_model),
                      appended_message_bytes=appended_for(schema_model), repair_context_bytes=repair_context)
        notes = {}
        if dynamic and derived:
            L = output_allowance(task, estimate_input_tokens(prompt, payload, schema_model.model_json_schema()), units)
            regions = {'envelope': ChainSpec(base_message_bytes=base, sequences=reachable_sequences(L, C),
                                             reachable=True, **common)}
            if L == C:   # an input below the envelope may get L < C, where a continuation is reachable
                t_max = max_tokens_below_limit(task, C)
                if t_max is not None:
                    below = min(base, base_bytes_below_limit(prompt, schema_model, t_max, request_extra))
                    regions['below_limit'] = ChainSpec(base_message_bytes=below,
                                                       sequences=reachable_sequences(C - 1, C),
                                                       reachable=True, **common)
                    notes['below_limit_max_estimate_tokens'] = t_max
        elif dynamic:
            regions = {'accounting_envelope_3C': ChainSpec(base_message_bytes=base,
                                                           sequences={'accounting_envelope_3C': accounting_envelope(C)},
                                                           reachable=False, **common)}
        else:
            regions = {'fixed_limit': ChainSpec(base_message_bytes=base,
                                                sequences=reachable_sequences(STRUCTURED_MAX_TOKENS, None),
                                                reachable=True, **common)}
        return ChainBound(task, price, regions, notes)

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
    ext_payload = {'job_id': PAD * short, 'jd_text': PAD * jd_chars,
                   'qualification_inventory': inventory_envelope(jd_chars, max_items)}
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

    chains = {'parse': parse, 'extraction': extraction, 'matching': matching, 'fallback': fallback}
    details = {'k': k, 'model_output_limit': C, 'cv_max_chars': cv_chars, 'jd_max_chars': jd_chars,
               'envelopes': dict(env), **{name: c.describe() for name, c in chains.items()},
               'note': ('3C accounting envelope: conservative fail-closed bound, not reachable attempts'
                        if not derived else 'reachable call chains over every reachable initial allowance')}
    return PhaseBounds(parse_max=parse.cost(), embed_max=embed_max, extraction_max=k * extraction.cost(),
                       matching_max=k * matching.cost(), fallback_max=k * fallback.cost(),
                       bound_basis=DERIVED if derived else SUPREMUM,
                       config_sha256=hashlib.sha256(raw).hexdigest(), details=details, chains=chains)
