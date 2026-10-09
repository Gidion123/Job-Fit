"""D-104 / FAIL-37 calibration harness: fixtures, expected output, scoring and the gate registry.

Test and evaluation infrastructure only. Production code never imports this module, and the
annotation oracle below is a reference for checking the harness itself, not a sanitizer.

Fixture text carries inline tags that are test metadata only:

* ``[[DROP:kind]]...[[/DROP]]`` whole lines the sanitizer must remove (nested tags included);
* ``[[PII:kind]]...[[/PII]]`` text that must not survive; outside a DROP it becomes a placeholder;
* ``[[KEEP:kind]]...[[/KEEP]]`` professional evidence that must survive verbatim.

Adapters only ever receive the tag-stripped source text. The expected output follows a
versioned contract that mirrors the D-104 sanitizer:

1. ``ANNOTATION_RENDER``: DROP removes the whole region; PII outside DROP becomes its
   placeholder; KEEP and untagged text stay as they are.
2. ``SOURCE_NORMALIZE_V1``: reject lone surrogates, NFC, strip category ``Cf``, line endings to ``\\n``.
3. ``COMPARE_CANON_V1`` (both sides): strip trailing whitespace per line, collapse runs of blank
   lines, strip leading and trailing blank lines. No case folding, no inner-whitespace changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
import unicodedata

import yaml

FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'masking_fail37'
REPO_ROOT = Path(__file__).resolve().parents[1]
SETS = {'dev': 'dev.yaml', 'heldout': 'heldout_v1.yaml'}

SCHEMA = 'fail37-fixtures-v1'
HARNESS_VERSION = 'fail37-harness-v1'
NORMALIZATION = {'source': 'SOURCE_NORMALIZE_V1', 'render': 'ANNOTATION_RENDER_V1', 'compare': 'COMPARE_CANON_V1'}
BOUNDARY_CODE = 'professional_boundary_not_found'

DROP_KINDS = frozenset({'header', 'summary', 'privacy', 'interests', 'organizations'})
PII_KINDS = frozenset({'email', 'phone', 'id', 'profile', 'address', 'name', 'third'})
KEEP_KINDS = frozenset({'company', 'institution', 'project', 'tech', 'title', 'role', 'cert', 'date',
                        'skill', 'joblocation', 'evidence', 'heading'})
KINDS = {'DROP': DROP_KINDS, 'PII': PII_KINDS, 'KEEP': KEEP_KINDS}
PLACEHOLDER = {'email': '[EMAIL]', 'phone': '[PHONE]', 'id': '[IDENTITY_NUMBER]', 'profile': '[PROFILE]',
               'address': '[ADDRESS]', 'name': '[NAME]', 'third': '[NAME]'}
CONTACT_PII = frozenset({'email', 'phone', 'id', 'profile'})
CATEGORIES = frozenset({
    'summary_delimiter', 'summary_only', 'fallback_start', 'no_start', 'privacy_section', 'interests',
    'organizations', 'evidence_preservation', 'backstop_contact', 'backstop_address_standalone',
    'backstop_address_inline', 'label_person', 'label_role', 'owner_repeat', 'edit', 'adversarial', 'residual'})
FAIL_CLOSED_CATEGORIES = frozenset({'summary_only', 'no_start'})
LANGS = frozenset({'id', 'en', 'mixed'})

_TAG = re.compile(r'\[\[(?:(DROP|PII|KEEP):([a-z]+)|/(DROP|PII|KEEP))\]\]')


class FixtureError(ValueError):
    """A fixture violates the annotation schema."""


class Refused(Exception):
    """An adapter refused the input with a fixed code (the fail-closed path)."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class AnnotationLeak(AssertionError):
    """Fixture annotation syntax reached an adapter."""


# --- normalization contract ---------------------------------------------------------------------------------

def source_normalize(text: str) -> str:
    """SOURCE_NORMALIZE_V1: reject lone surrogates, NFC, strip category Cf, line endings to \\n."""
    if any(0xD800 <= ord(ch) <= 0xDFFF for ch in text):
        raise ValueError('lone surrogate')
    text = unicodedata.normalize('NFC', text)
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Cf')
    return text.replace('\r\n', '\n').replace('\r', '\n')


def compare_canon(text: str) -> str:
    """COMPARE_CANON_V1: per-line trailing whitespace, blank-line runs, outer blank lines."""
    lines, previous_blank = [], False
    for line in (raw.rstrip() for raw in text.split('\n')):
        if line or not previous_blank:
            lines.append(line)
        previous_blank = not line
    return '\n'.join(lines).strip('\n')


# --- annotation parsing and rendering ---------------------------------------------------------------------

@dataclass(frozen=True)
class Span:
    tag: str            # DROP | PII | KEEP
    kind: str
    start: int          # offsets into the tag-stripped source text
    end: int
    in_drop: bool


@dataclass(frozen=True)
class Annotated:
    source: str         # tag-stripped source text, the only thing an adapter ever sees
    spans: tuple[Span, ...]

    def of(self, tag: str, kind: str | None = None) -> list[Span]:
        return [s for s in self.spans if s.tag == tag and (kind is None or s.kind == kind)]


def parse_annotated(text: str) -> Annotated:
    if not isinstance(text, str):
        raise FixtureError('fixture text must be a string')
    out, spans, stack, cursor, boundaries = [], [], [], 0, []
    for m in _TAG.finditer(text):
        out.append(text[cursor:m.start()])
        cursor = m.end()
        pos = sum(len(p) for p in out)
        boundaries.append(pos)
        if m.group(1):
            tag, kind = m.group(1), m.group(2)
            if kind not in KINDS[tag]:
                raise FixtureError(f'unknown {tag} kind {kind!r}')
            if tag == 'DROP' and stack:
                raise FixtureError('DROP cannot be nested')
            if tag in ('PII', 'KEEP') and stack and stack[-1][0] in ('PII', 'KEEP'):
                raise FixtureError('PII and KEEP cannot nest or overlap')
            stack.append((tag, kind, pos))
        else:
            tag = m.group(3)
            if not stack or stack[-1][0] != tag:
                raise FixtureError(f'unbalanced closing {tag}')
            _, kind, start = stack.pop()
            in_drop = tag != 'DROP' and any(t == 'DROP' for t, _, _ in stack)
            spans.append(Span(tag, kind, start, pos, in_drop))
    if stack:
        raise FixtureError('unclosed tag')
    out.append(text[cursor:])
    source = ''.join(out)
    if '[[' in source or ']]' in source:
        raise FixtureError('stray annotation marker in source text')
    for pos in boundaries:
        for ch in (source[pos - 1:pos], source[pos:pos + 1]):
            if ch and (ch == '\r' or unicodedata.category(ch).startswith('M')):
                raise FixtureError('combining mark or \\r next to a tag boundary')
    for s in spans:
        if s.tag == 'DROP':
            if s.start and source[s.start - 1] != '\n':
                raise FixtureError('DROP must start at a line start')
            if s.end != len(source) and source[s.end - 1] != '\n':
                raise FixtureError('DROP must end at a line end')
        if s.end <= s.start:
            raise FixtureError('empty span')
    return Annotated(source, tuple(sorted(spans, key=lambda s: (s.start, -s.end))))


def annotation_render(ann: Annotated) -> str:
    """ANNOTATION_RENDER: DROP removes whole regions; PII outside DROP becomes its placeholder."""
    drops = [(s.start, s.end) for s in ann.of('DROP')]
    pii = {s.start: s for s in ann.of('PII') if not s.in_drop}
    pieces, i = [], 0
    while i < len(ann.source):
        drop = next((d for d in drops if d[0] == i), None)
        if drop:
            i = drop[1]
            continue
        if i in pii:
            pieces.append(PLACEHOLDER[pii[i].kind])
            i = pii[i].end
            continue
        pieces.append(ann.source[i])
        i += 1
    return ''.join(pieces)


def expected_text(ann: Annotated) -> str:
    return source_normalize(annotation_render(ann))


def span_text(ann: Annotated, span: Span) -> str:
    return source_normalize(ann.source[span.start:span.end])


def drop_line_variants(ann: Annotated) -> dict[str, set[str]]:
    """For each DROP kind, its lines raw and with nested PII masked (normalized, stripped)."""
    variants: dict[str, set[str]] = {}
    for d in ann.of('DROP'):
        inner = [s for s in ann.of('PII') if d.start <= s.start and s.end <= d.end]
        raw = ann.source[d.start:d.end]
        masked, cursor = [], d.start
        for s in inner:
            masked += [ann.source[cursor:s.start], PLACEHOLDER[s.kind]]
            cursor = s.end
        masked.append(ann.source[cursor:d.end])
        for block in (raw, ''.join(masked)):
            for line in source_normalize(block).split('\n'):
                if line.strip():
                    variants.setdefault(d.kind, set()).add(line.strip())
    return variants


# --- fixtures ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Case:
    id: str
    family: str
    category: str
    lang: str
    expect: str
    upload: Annotated
    expect_start: str | None = None
    prepend: Annotated | None = None
    append: Annotated | None = None
    note: str = ''

    @property
    def gated(self) -> bool:
        return self.category != 'residual'

    def expected(self) -> str:
        return expected_text(self.upload)

    def expected_edit(self) -> str:
        return (expected_text(self.prepend) if self.prepend else '') + self.expected().rstrip('\n') + '\n' + \
            (expected_text(self.append) if self.append else '')

    def drop_kinds(self) -> set[str]:
        kinds = {s.kind for s in self.upload.of('DROP')}
        for part in (self.prepend, self.append):
            if part:
                kinds |= {s.kind for s in part.of('DROP')}
        return kinds


def edit_input(case: Case, upload_output: str) -> str:
    return (case.prepend.source if case.prepend else '') + upload_output.rstrip('\n') + '\n' + \
        (case.append.source if case.append else '')


def fixture_path(set_name: str) -> Path:
    return FIXTURES / SETS[set_name]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cases(set_name: str) -> list[Case]:
    doc = yaml.safe_load(fixture_path(set_name).read_text(encoding='utf-8'))
    if not isinstance(doc, dict) or doc.get('schema') != SCHEMA or not isinstance(doc.get('cases'), list):
        raise FixtureError('fixture file must be a mapping with the current schema and a case list')
    cases = []
    for raw in doc['cases']:
        unknown = set(raw) - {'id', 'family', 'category', 'lang', 'expect', 'expect_start', 'text', 'edit', 'note'}
        if unknown:
            raise FixtureError(f'unknown fields {sorted(unknown)} in {raw.get("id")}')
        edit = raw.get('edit') or {}
        if set(edit) - {'prepend', 'append'}:
            raise FixtureError('edit takes prepend and append only')
        cases.append(Case(
            id=raw['id'], family=raw['family'], category=raw['category'], lang=raw['lang'], expect=raw['expect'],
            upload=parse_annotated(raw['text']), expect_start=raw.get('expect_start'),
            prepend=parse_annotated(edit['prepend']) if 'prepend' in edit else None,
            append=parse_annotated(edit['append']) if 'append' in edit else None, note=raw.get('note', '')))
    return cases


# --- adapters ---------------------------------------------------------------------------------------------

def call(adapter, text: str, marks=None):
    """Every adapter call goes through this guard: no annotation syntax may reach a sanitizer."""
    if '[[' in text or ']]' in text:
        raise AnnotationLeak('annotation marker in adapter input')
    return adapter(text, marks)


def v1_adapter(text: str, marks=None):
    """The historical CP2 masking (`mask_local` v1), unchanged, on tag-stripped source text."""
    from jobfit.privacy.masking import mask_local
    try:
        return mask_local(text).text, None
    except ValueError:
        raise Refused('masking_failed') from None


def v2_adapter(text: str, marks=None):
    """The D-104 sanitizer (`sanitize_upload`), on tag-stripped source text; marks carry over to edits."""
    from jobfit.privacy.masking import sanitize_upload
    from jobfit.privacy.structure import SanitizeRefused
    try:
        preview = sanitize_upload(text, marks=marks)
    except SanitizeRefused as exc:
        raise Refused(exc.code) from None
    return preview.text, preview.marks


def identity_adapter(text: str, marks=None):
    return text, None


class OracleAdapter:
    """Annotation-derived reference used only to self-test the harness. Not a detector."""

    def __init__(self, cases: list[Case]):
        self.table: dict[str, str | Refused] = {}
        for case in cases:
            if case.expect != 'ok':
                self.table[case.upload.source] = Refused(case.expect)
                continue
            expected = case.expected()
            self.table[case.upload.source] = expected
            self.table[expected] = expected
            if case.prepend or case.append:
                edited = case.expected_edit()
                self.table[edit_input(case, expected)] = edited
                self.table[edited] = edited

    def __call__(self, text: str, marks=None):
        result = self.table[text]
        if isinstance(result, Refused):
            raise result
        return result, marks


# --- scoring ----------------------------------------------------------------------------------------------

@dataclass
class CaseResult:
    case: Case
    correct: bool = False
    refused: str | None = None
    start_ok: bool = False
    idempotent: bool = False
    edit_ok: bool | None = None
    drop_leaks: dict = field(default_factory=dict)      # DROP kind -> leaked line count
    pii_leaks: dict = field(default_factory=dict)       # PII kind -> leaked span count
    placeholder_missing: int = 0
    keep_destroyed: int = 0


def _lines(text: str) -> set[str]:
    return {line.strip() for line in compare_canon(text).split('\n') if line.strip()}


def _diagnose(result: CaseResult, ann: Annotated, actual: str, expected: str) -> None:
    """Diagnostics only; compare against a normalized copy so raw Cf/NFD output cannot hide a leak."""
    try:
        actual = source_normalize(actual)
    except ValueError:
        pass
    out_lines = _lines(actual)
    for kind, variants in drop_line_variants(ann).items():
        result.drop_leaks[kind] = result.drop_leaks.get(kind, 0) + len(variants & out_lines)
    for s in ann.of('PII'):
        if span_text(ann, s).strip() in actual:
            result.pii_leaks[s.kind] = result.pii_leaks.get(s.kind, 0) + 1
    result.placeholder_missing += sum(max(0, expected.count(p) - actual.count(p)) for p in set(PLACEHOLDER.values()))
    result.keep_destroyed += sum(1 for s in ann.of('KEEP') if not s.in_drop and span_text(ann, s) not in actual)


def evaluate_case(case: Case, adapter) -> CaseResult:
    result = CaseResult(case)
    try:
        actual, marks = call(adapter, case.upload.source)
    except Refused as exc:
        result.refused = exc.code
        result.correct = case.expect != 'ok' and exc.code == case.expect
        return result
    if case.expect != 'ok':
        return result
    expected = case.expected()
    result.correct = compare_canon(actual) == compare_canon(expected)
    result.start_ok = compare_canon(actual).split('\n')[0] == case.expect_start
    _diagnose(result, case.upload, actual, expected)
    try:
        again, _ = call(adapter, actual, marks)
        result.idempotent = compare_canon(again) == compare_canon(actual)
    except Refused:
        result.idempotent = False
    if case.prepend or case.append:
        try:
            edited, _ = call(adapter, edit_input(case, actual), marks)
            result.edit_ok = compare_canon(edited) == compare_canon(case.expected_edit())
            for part in (case.prepend, case.append):
                if part:
                    _diagnose(result, part, edited, case.expected_edit())
        except Refused:
            result.edit_ok = False
        result.correct = result.correct and bool(result.edit_ok)    # an edit case is exact only if its edit is
    return result


def evaluate(cases: list[Case], adapter) -> list[CaseResult]:
    return [evaluate_case(case, adapter) for case in cases]


# --- gate registry (canonical D-104 C12; every gate listed with its phase) --------------------------------

def _in(*cats):
    return lambda r: r.case.category in cats


def _has_drop(kind):
    return lambda r: kind in r.case.drop_kinds() and r.case.expect == 'ok'


def _no_drop_leak(kind):
    return lambda r: r.refused is None and not r.drop_leaks.get(kind)


def _no_pii_leak(*kinds):
    return lambda r: r.refused is None and not any(r.pii_leaks.get(k) for k in kinds)


def _both(*preds):
    return lambda r: all(p(r) for p in preds)


def _ok_case(r):
    return r.case.expect == 'ok'


_correct = lambda r: r.correct                                               # noqa: E731
_any = lambda r: True                                                       # noqa: E731

# name: (phase, description, case selector, pass predicate). Phase 'api' gates need the
# provider spy and the sinks of commit 3; 'commit1' is evaluated by the v1 golden check.
HARD_GATES = {
    'exact_expected_output': ('calibration', 'every gated case equals its expected sanitized output', _any, _correct),
    'summary_delimiter_detected': ('calibration', 'Summary family used as the delimiter',
                                   _in('summary_delimiter'), _correct),
    'pre_summary_removed': ('calibration', 'all pre-summary content removed when Summary exists',
                            _has_drop('summary'), _no_drop_leak('header')),
    'summary_content_removed': ('calibration', 'Summary/Profile/Objective content removed',
                                _has_drop('summary'), _no_drop_leak('summary')),
    'first_evidence_after_summary_kept': ('calibration', 'output starts at the first evidence section after Summary',
                                          _in('summary_delimiter'), lambda r: r.start_ok),
    'fallback_start': ('calibration', 'without Summary the first evidence section is the start',
                       _in('fallback_start'), _both(_correct, lambda r: r.start_ok)),
    'summary_only_fails_closed': ('calibration', 'Summary with no later evidence section fails closed',
                                  _in('summary_only'), _correct),
    'no_summary_in_provider_payload': ('api', 'no Summary claim in the provider spy payload', None, None),
    'header_removed': ('calibration', 'identity/contact header removed', _has_drop('header'), _no_drop_leak('header')),
    'privacy_sections_removed': ('calibration', 'privacy-only sections removed',
                                 _has_drop('privacy'), _no_drop_leak('privacy')),
    'interests_removed': ('calibration', 'Interests/Minat removed', _has_drop('interests'), _no_drop_leak('interests')),
    'organizations_removed': ('calibration', 'Organizations/Organisasi removed',
                              _has_drop('organizations'), _no_drop_leak('organizations')),
    'resume_after_dropped_section': ('calibration', 'evidence sections after a dropped section resume',
                                     _in('privacy_section', 'interests', 'organizations'), _correct),
    'protected_evidence_destroyed_zero': ('calibration', 'no KEEP span destroyed',
                                          _ok_case, lambda r: r.refused is None and r.keep_destroyed == 0),
    'contact_pattern_leakage_zero': ('calibration', 'no email/phone/identity-number/profile leak',
                                     _ok_case, _no_pii_leak(*CONTACT_PII)),
    'owner_repeat_masked': ('calibration', 'high-confidence multi-token owner repeat masked',
                            _in('owner_repeat'), _both(_correct, _no_pii_leak('name', 'profile'))),
    'labelled_person_masked': ('calibration', 'person-name value after a strong label masked',
                               _in('label_person'), _both(_correct, _no_pii_leak('third'))),
    'supported_address_masked': ('calibration', 'supported detailed address masked',
                                 _in('backstop_address_standalone', 'backstop_address_inline'),
                                 _both(_correct, _no_pii_leak('address'))),
    'role_after_label_kept': ('calibration', 'role values after person-like labels kept', _in('label_role'), _correct),
    'inline_address_evidence_kept': ('calibration', 'evidence next to an inline address kept',
                                     _in('backstop_address_inline'),
                                     _both(_correct, lambda r: r.keep_destroyed == 0)),
    'raw_canary_sinks_zero': ('api', 'no raw canary in provider payloads, logs, errors, metrics or responses',
                              None, None),
    'edit_resanitization': ('calibration', 'every edit is sanitized again (API lifecycle checked in commit 3)',
                            lambda r: bool(r.case.prepend or r.case.append), lambda r: bool(r.edit_ok)),
    'no_start_fails_closed': ('calibration', 'no evidence start fails closed', _in('no_start'), _correct),
    'idempotency': ('calibration', 'sanitizing the output again changes nothing', _ok_case,
                    lambda r: r.refused is None and r.idempotent),
    'mask_local_v1_byte_identical': ('commit1', 'historical mask_local v1 output unchanged (golden digests)',
                                     None, None),
}


def gate_table(results: list[CaseResult], *, v1_golden_ok: bool | None = None) -> dict:
    gated = [r for r in results if r.case.gated]
    table = {}
    for name, (phase, description, select, passes) in HARD_GATES.items():
        if phase == 'api':
            table[name] = {'phase': phase, 'status': 'NOT_APPLICABLE_YET', 'description': description}
            continue
        if phase == 'commit1':
            status = 'NOT_EVALUATED' if v1_golden_ok is None else ('PASS' if v1_golden_ok else 'FAIL')
            table[name] = {'phase': phase, 'status': status, 'description': description}
            continue
        chosen = [r for r in gated if select(r)]
        failing = sorted(r.case.id for r in chosen if not passes(r))
        status = 'NO_CASES' if not chosen else ('PASS' if not failing else 'FAIL')
        table[name] = {'phase': phase, 'status': status, 'description': description,
                       'passed': len(chosen) - len(failing), 'total': len(chosen), 'failing_ids': failing}
    return table


# --- mask_local v1 golden ---------------------------------------------------------------------------------

V1_GOLDEN_SOURCES = {
    'CV1': ('data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md', 'Rina'),
    'CV2': ('data/synthetic_cvs/cv_02_career_switcher_ai_engineer_en.md', 'Bima'),
}


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def v1_golden_digests(dev_cases: list[Case]) -> dict:
    """sha256 of mask_local v1 output on tag-stripped sources: CV1/CV2 with the CP2 hints and each dev case."""
    from jobfit.privacy.masking import mask_local
    out = {}
    for key, (rel, name) in V1_GOLDEN_SOURCES.items():
        text = (REPO_ROOT / rel).read_text(encoding='utf-8')
        out[f'{key}_with_cp2_hint'] = _digest(mask_local(text, reviewed_identifiers={'name': (name,)}).text)
        out[f'{key}_no_hint'] = _digest(mask_local(text).text)
    for case in dev_cases:
        source = case.upload.source
        if '[[' in source or ']]' in source:
            raise AnnotationLeak('annotation marker in golden source')
        try:
            out[f'dev:{case.id}'] = _digest(mask_local(source).text)
        except ValueError:
            out[f'dev:{case.id}'] = 'refused'
    return out


def v1_golden_ok(dev_cases: list[Case]) -> bool:
    pinned = json.loads((FIXTURES / 'manifest.json').read_text(encoding='utf-8'))['v1_golden']
    current = v1_golden_digests(dev_cases)
    return all(current.get(key) == value for key, value in pinned.items())


# --- holdout discipline -----------------------------------------------------------------------------------

# The holdout execution gate is closed. The single approved first-pass run of the D-104 sanitizer
# happened at commit 8257f17 (sanitizer sha eba16fc5...); its receipt is historical evidence and no
# detector may run on the holdout again.
HOLDOUT_RUN_ALLOWED: frozenset[str] = frozenset()
HISTORICAL_HOLDOUT = {
    'receipt': 'evals/results/fail37_structural_calibration_20261009_v2_heldout_v1_first_pass.json',
    'receipt_sha256': '8fac62281176892b095d53c96c970c99d8dae9ba722048bd114fe922ccb37d6d',
    'sanitizer_sha256': 'eba16fc539941c587083e525c47927ba4225c33293f9d7ad5a1b1f8111b9bd8b',
    'fixture_sha256': 'b892c45f6b100b352b36da2be0ba5ea78286757f6056609647c42227e97e3cf9',
}
SANITIZER_SOURCES = ('src/jobfit/privacy/structure.py', 'src/jobfit/privacy/masking.py')


def check_holdout_run(set_name: str, adapter_name: str, single_run: bool = False) -> None:
    if set_name != 'dev' and (adapter_name not in HOLDOUT_RUN_ALLOWED or not single_run):
        raise PermissionError(f'{adapter_name!r} may not run on the locked holdout {set_name!r}')


def sanitizer_sha256() -> str:
    """Identity of the sanitizer source a v2 receipt was produced with."""
    digest = hashlib.sha256()
    for rel in SANITIZER_SOURCES:
        digest.update((REPO_ROOT / rel).read_bytes())
    return digest.hexdigest()


# --- receipts (counts and ids only; never text) -----------------------------------------------------------

def build_receipt(set_name: str, adapter_name: str, adapter, *, date: str, single_run: bool = False) -> dict:
    check_holdout_run(set_name, adapter_name, single_run)
    cases = load_cases(set_name)
    results = evaluate(cases, adapter)
    golden = v1_golden_ok(load_cases('dev')) if adapter_name in ('v1', 'v2') else None
    categories: dict[str, dict] = {}
    for r in results:
        c = categories.setdefault(r.case.category, {'total': 0, 'correct': 0})
        c['total'] += 1
        c['correct'] += int(r.correct)
    residual = [r for r in results if not r.case.gated]
    extra = {'sanitizer_sha256': sanitizer_sha256()} if adapter_name == 'v2' else {}
    if set_name != 'dev':
        extra['holdout_run'] = 'first_pass'
    return {**extra,
        'receipt': 'fail37-structural-calibration',
        'schema': SCHEMA, 'harness': HARNESS_VERSION, 'normalization': NORMALIZATION,
        'date': date, 'set': set_name, 'fixture_sha256': sha256_file(fixture_path(set_name)),
        'adapter': adapter_name, 'cases': len(cases),
        'gates': gate_table(results, v1_golden_ok=golden),
        'categories': dict(sorted(categories.items())),
        'residual': {'total': len(residual), 'correct': sum(r.correct for r in residual),
                     'ids': sorted(r.case.id for r in residual)},
        'diagnostics': {
            'exact_correct': sum(r.correct for r in results),
            'refused': sum(r.refused is not None for r in results),
            'drop_lines_leaked': sum(sum(r.drop_leaks.values()) for r in results),
            'pii_leaked': sum(sum(r.pii_leaks.values()) for r in results),
            'placeholder_missing': sum(r.placeholder_missing for r in results),
            'keep_destroyed': sum(r.keep_destroyed for r in results),
        },
        'note': 'Counts and case ids only; no fixture text. Synthetic fixtures; not a privacy guarantee.',
    }
