"""Versioned local direct-identifier masking; no model, disk or network.

`mask_local` (v1) is the historical CP2 pattern masking, kept byte-identical for CP2
reproducibility. `sanitize_upload` (v2) is the D-104 structural data-minimization boundary
for uploaded CVs: it keeps only evidence-bearing sections (see `structure`) and then runs
deterministic backstops (contact patterns, detailed addresses, a multi-token owner-name
repeat and person names after strong labels). Masking is not anonymization and can miss
identifiers; the user reviews the exact text before consent.
"""
from dataclasses import dataclass, field
import hashlib
import hmac
import re
import secrets

VERSION = 'local-pattern-masking-v1'
_ALLOWED = {'name', 'address', 'identity_number'}
_PATTERNS = {
    'email': re.compile(r'(?i)(?<![\w.+-])[\w.+-]+@[\w.-]+\.[a-z]{2,}(?![\w-])'),
    'phone': re.compile(r'(?<![\w])(?:\+62|\+\d{1,3}[ -]|08|\(\d{3}\))[\d ()-]{7,}\d(?![\w])'),
    'identity_number': re.compile(r'(?i)\b(?:NIK|KTP|passport|paspor|ID number)\s*[:#]?\s*([A-Z0-9-]{6,})'),
    'profile': re.compile(r'(?i)(?:https?://)?(?:www\.)?(?:linkedin\.com/in/[\w%-]+/?|github\.com/[\w-]+/?(?![\w/]))'),
}

@dataclass(frozen=True)
class MaskedPreview:
    text: str = field(repr=False)
    version: str
    digest: str
    counts: dict[str, int]
    warnings: tuple[str, ...]
    removed: dict[str, int] = field(default_factory=dict)       # v2: structural removal counts only
    owner_repeat_guard: str | None = None                       # v2: 'active' | 'not_established'
    marks: 'OwnerMarks | None' = field(default=None, repr=False, compare=False)


def mask_local(text: str, *, reviewed_identifiers: dict[str, tuple[str, ...]] | None = None) -> MaskedPreview:
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Local extraction has no usable text; no raw fallback')
    hints = reviewed_identifiers or {}
    if not set(hints) <= _ALLOWED:
        raise ValueError('Only reviewed direct-identifier hints are allowed')
    spans = []
    for kind, pattern in _PATTERNS.items():
        for match in pattern.finditer(text):
            span = match.span(1) if kind == 'identity_number' else match.span()
            spans.append((*span, kind))
    for kind, values in hints.items():
        for value in values:
            if not isinstance(value, str) or not value.strip():
                raise ValueError('Empty or invalid identifier hint')
            # Escape hints; they are exact text, never executable regular expressions.
            for match in re.finditer(re.escape(value), text, re.IGNORECASE):
                spans.append((*match.span(), kind))
    # Keep nonoverlapping spans in source order, longest match first at each start.
    chosen = []
    end = -1
    for start, stop, kind in sorted(set(spans), key=lambda v: (v[0], -v[1], v[2])):
        if start >= end:
            chosen.append((start, stop, kind)); end = stop
    pieces = []; cursor = 0; counts = {}
    for start, stop, kind in chosen:
        pieces.extend([text[cursor:start], f'[{kind.upper()}]']); cursor = stop
        counts[kind] = counts.get(kind, 0) + 1
    pieces.append(text[cursor:]); masked = ''.join(pieces)
    return MaskedPreview(masked, VERSION, hashlib.sha256(masked.encode()).hexdigest(), counts,
        ('Review the exact outgoing text: pattern masking may miss identifiers.',
         'Employer/institution and city policy remains pending; real-CV processing is blocked.'))


# --- v2: D-104 structural sanitizer for uploaded CVs ---------------------------------------------------------

VERSION_V2 = 'local-structural-masking-v2'
_PLACEHOLDER = {'email': '[EMAIL]', 'phone': '[PHONE]', 'identity_number': '[IDENTITY_NUMBER]',
                'profile': '[PROFILE]', 'address': '[ADDRESS]', 'name': '[NAME]'}
_BULLET = r'(?:[-*•]\s+)?'

# Person-name shape shared by the owner candidate and the labelled-person backstop: 2-4 capitalised or
# all-caps letter tokens; lowercase particles and initials allowed; a bounded rejection list.
_PARTICLES = frozenset({'bin', 'binti', 'van', 'von', 'de', 'der', 'da', 'al', 'el'})
_TITLES = frozenset({'dr', 'ir', 'prof', 'drs', 'h', 'hj', 'mr', 'mrs', 'ms'})
_REJECT = frozenset({
    # CV and section words
    'summary', 'profile', 'profil', 'experience', 'pengalaman', 'skills', 'keahlian', 'education', 'pendidikan',
    'projects', 'proyek', 'contact', 'kontak', 'resume', 'curriculum', 'vitae', 'cv', 'biodata', 'references',
    # roles and job-title words
    'head', 'lead', 'chief', 'director', 'manager', 'engineer', 'engineering', 'analyst', 'analytics', 'scientist',
    'science', 'developer', 'intern', 'consultant', 'specialist', 'officer', 'staff', 'assistant', 'senior',
    'junior', 'principal', 'team', 'vp', 'data', 'machine', 'learning', 'software', 'product', 'research',
    'kepala', 'divisi', 'manajer', 'direktur', 'ketua', 'staf', 'tim', 'koordinator', 'bagian', 'supervisor',
    # organisation markers
    'pt', 'tbk', 'persero', 'universitas', 'university', 'institut', 'institute', 'politeknik', 'sekolah', 'sma',
    'smk', 'bank', 'inc', 'ltd', 'llc', 'corp', 'group', 'labs', 'studio', 'foundation', 'yayasan', 'company',
    # connectors and coarse place words
    'of', 'and', 'for', 'the', 'at', 'di', 'dan', 'indonesia', 'jakarta', 'kota', 'kabupaten',
    'selatan', 'utara', 'barat', 'timur', 'pusat'})
_LETTER_TOKEN = re.compile(r"[^\W\d_](?:[^\W\d_'’-]*[^\W\d_])?\.?")


def _name_tokens(value: str) -> list[str] | None:
    """The tokens of a person-name-shaped value (titles stripped), or None."""
    value = value.split(',')[0].strip()
    if not value or len(value) > 60 or any(ch.isdigit() or ch in '@/[]' for ch in value):
        return None
    tokens = value.split()
    while tokens and tokens[0].rstrip('.').casefold() in _TITLES:
        tokens = tokens[1:]
    if not 2 <= len(tokens) <= 4:
        return None
    for token in tokens:
        bare = token.rstrip('.').casefold()
        if bare in _REJECT or not _LETTER_TOKEN.fullmatch(token):
            return None
        if token.casefold() in _PARTICLES:
            continue
        if not token[0].isupper() or (token.endswith('.') and len(token) > 2):
            return None
    if all(t.casefold() in _PARTICLES for t in tokens):
        return None
    return [t.rstrip('.') for t in tokens]


class OwnerMarks:
    """Volatile keyed fingerprints of the owner's name sequences and profile handles.

    Holds only HMAC-SHA256 digests under a random per-upload key: no raw value and no reversible
    map. Never serialized; the representation shows a count only.
    """
    __slots__ = ('_key', '_digests')

    def __init__(self, key: bytes | None = None, digests: frozenset[bytes] = frozenset()):
        self._key = key or secrets.token_bytes(32)
        self._digests = frozenset(digests)

    def __repr__(self) -> str:
        return f'OwnerMarks(<{len(self._digests)} fingerprints>)'

    def __bool__(self) -> bool:
        return bool(self._digests)

    def __reduce__(self):
        raise TypeError('OwnerMarks are volatile and cannot be serialized')

    def fingerprint(self, value: str) -> bytes:
        return hmac.new(self._key, value.casefold().encode('utf-8'), hashlib.sha256).digest()

    def knows(self, value: str) -> bool:
        return self.fingerprint(value) in self._digests

    def extended(self, values) -> 'OwnerMarks':
        return OwnerMarks(self._key, self._digests | {self.fingerprint(v) for v in values})


_EMAIL_LOCAL = re.compile(r'(?i)(?<![\w.+-])([\w.+-]+)@[\w.-]+\.[a-z]{2,}(?![\w-])')
# URL candidates: one character class (no alternation or nesting), so Markdown links, parentheses and
# angle brackets split off and the scan stays linear. Only http(s) or no scheme, and exact hosts.
_URL_PIECE = re.compile(r'[^\s()<>\[\]"\'`]+')
_GITHUB_HOSTS = frozenset({'github.com', 'www.github.com'})
_LINKEDIN_HOSTS = frozenset({'linkedin.com', 'www.linkedin.com'})
_GITHUB_HANDLE = re.compile(r'[A-Za-z0-9-]+')
_LINKEDIN_HANDLE = re.compile(r'[\w%-]+')


def _url_parts(start: int, piece: str) -> tuple[str, str, int] | None:
    """(lowercase host, path, source offset of the path) for a scheme-less or http(s) URL piece."""
    head = piece[:8].casefold()
    skip = 8 if head.startswith('https://') else 7 if head.startswith('http://') else 0
    if not skip and '://' in piece:
        return None
    host, sep, path = piece[skip:].partition('/')
    if not sep:
        return None
    return host.casefold(), path, start + skip + len(host) + 1


def _header_handles(header: str) -> list[str]:
    """Profile handles established from the header: GitHub profile roots and LinkedIn /in/ only."""
    handles = []
    for m in _URL_PIECE.finditer(header):
        parts = _url_parts(m.start(), m.group())
        if parts is None:
            continue
        host, path, _ = parts
        segments = path.rstrip('.,;:').split('/')
        if segments and segments[-1] == '':
            segments = segments[:-1]                     # one trailing slash
        if host in _GITHUB_HOSTS and len(segments) == 1 and _GITHUB_HANDLE.fullmatch(segments[0]):
            handles.append(segments[0])                  # github.com/<handle> only, never github.com/<org>/<repo>
        elif host in _LINKEDIN_HOSTS and len(segments) == 2 and segments[0].casefold() == 'in' \
                and _LINKEDIN_HANDLE.fullmatch(segments[1]):
            handles.append(segments[1])
    return handles
_OWNER_LABEL = re.compile(r'(?i)^\s*' + _BULLET + r'(?:nama lengkap|nama|full name|name)\s*[:\-–]\s*(.+)$')


def _contact_lines(lines: list[str]) -> set[int]:
    return {i for i, line in enumerate(lines)
            if any(_PATTERNS[k].search(line) for k in ('email', 'phone', 'profile'))}


def owner_values(header: str) -> list[str]:
    """High-confidence owner name sequences and profile handles, from the identity/contact header only.

    `header` is the region before the first recognised heading (see `structure.header_region`); the
    Summary, earlier dropped sections and privacy sections never reach this function.
    """
    from jobfit.privacy.structure import classify
    lines = header.split('\n')
    contacts = _contact_lines(lines)
    handles = _header_handles(header)
    hint_tokens = set()
    for local in (m.group(1) for m in _EMAIL_LOCAL.finditer(header)):
        hint_tokens |= {t for t in re.split(r'[^a-z]+', local.casefold()) if len(t) > 1}
    for handle in handles:
        hint_tokens |= {t for t in re.split(r'[^a-z]+', handle.casefold()) if len(t) > 1}
    name, in_privacy = None, False
    for i, line in enumerate(lines):                     # an explicit label outside a privacy section
        kind = classify(line)
        if kind is not None:
            in_privacy = kind == 'privacy'
            continue
        m = _OWNER_LABEL.match(line)
        if m and not in_privacy:
            name = _name_tokens(m.group(1).strip())
            break
    if name is None and contacts:                        # the first name-shaped line, corroborated
        for i, line in enumerate(lines):
            if classify(line) is not None or _OWNER_LABEL.match(line):
                continue
            first = re.split(r'\s[|·•–-]\s|\|', line.strip().lstrip('#').strip(), maxsplit=1)[0]
            tokens = _name_tokens(first)
            if tokens is None:
                continue
            near = any(abs(i - j) <= 2 for j in contacts)
            overlap = {t.casefold() for t in tokens} & hint_tokens
            name = tokens if near or overlap else None
            break
    values = [f'h:{h}' for h in handles]
    if name:
        folded = [t.casefold() for t in name]
        values += [' '.join(folded[i:j]) for i in range(len(folded)) for j in range(i + 2, len(folded) + 1)]
    return values


_WORD = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*")


def _owner_spans(text: str, marks: OwnerMarks | None) -> list[tuple[int, int, str]]:
    if not marks:
        return []
    spans = []
    words = list(_WORD.finditer(text))
    i = 0
    while i < len(words):
        for size in (4, 3, 2):
            window = words[i:i + size]
            if len(window) < size:
                continue
            gaps = [text[a.end():b.start()] for a, b in zip(window, window[1:])]
            if all(g and not g.strip(' \t') and len(g) <= 3 for g in gaps) and \
                    marks.knows(' '.join(w.group().casefold() for w in window)):
                spans.append((window[0].start(), window[-1].end(), 'name'))
                i += size
                break
        else:
            i += 1
    for m in _URL_PIECE.finditer(text):             # GitHub repository URLs: only the account segment
        parts = _url_parts(m.start(), m.group())
        if parts is None or parts[0] not in _GITHUB_HOSTS:
            continue
        _, path, offset = parts
        account = path.split('/', 1)[0].rstrip('.,;:')
        if account and marks.knows(f'h:{account}'):     # a known owner handle; repository path preserved
            spans.append((offset, offset + len(account), 'profile'))
    return spans


_PERSON_LABEL = re.compile(
    r'(?im)^(\s*' + _BULLET + r'(?:supervisor|reporting manager|reporting to|contact person|pic|mentor|'
    r'atasan langsung|atasan|pembimbing|narahubung|referee|reference)\s*[:\-–]\s*)([^\n]*)$')
_VALUE_END = re.compile(r'[,(|·]|\s-\s|\s–\s')


def _label_spans(text: str) -> list[tuple[int, int, str]]:
    spans = []
    for m in _PERSON_LABEL.finditer(text):
        value = m.group(2)
        cut = _VALUE_END.search(value)
        segment = (value[:cut.start()] if cut else value).rstrip()
        if _name_tokens(segment) is not None:
            start = m.start(2)
            spans.append((start, start + len(segment), 'name'))
    return spans


_STREET = r'(?:jalan|jln\.?|jl\.?|gang|gg\.?|perumahan|perum\.|kompleks|komplek|komp\.)'
_ADDRESS_LABEL = re.compile(r'(?im)^(\s*' + _BULLET + r'(?:home address|address|alamat|domisili|tempat tinggal)'
                            r'\s*[:\-–]\s*)(\S[^\n]*)$')
_STREET_TRIGGER = re.compile(r'(?i)(?<![\w.])' + _STREET + r'(?=\s)')
_RT_RW = re.compile(r'(?i)\b(?:RT|RW)\.?\s*\d{1,3}(?:\s*/\s*(?:RT|RW)\.?\s*\d{1,3})?\b')
_INTL = re.compile(r'\b\d{1,5}[A-Za-z]?\s+(?:[A-Z][\w\'-]*\s+){1,4}(?:Street|Road|Avenue|Lane|Boulevard|St\.|Rd\.|'
                   r'Ave\.|Ln\.|Blvd\.)')
_STREET_TOKEN = re.compile(
    r'\s+(?:(?i:no\.|no(?=\s)|blok|kav\.|unit|apt\.|lantai|lt\.)|(?i:rt|rw)\.?\s*\d{1,3}(?:\s*/\s*(?i:rt|rw)\.?'
    r'\s*\d{1,3})?|\d+[A-Za-z]?(?:[/-]\d+[A-Za-z]?)*|[A-Z][\w\'-]*)(?=$|[\s,;:.()|·•])')
_PLACEHOLDER_ONLY = re.compile(r'\[(?:EMAIL|PHONE|IDENTITY_NUMBER|PROFILE|ADDRESS|NAME)\]')


def _address_spans(text: str) -> list[tuple[int, int, str]]:
    spans = []
    for m in _ADDRESS_LABEL.finditer(text):
        value = m.group(2).rstrip()
        if not _PLACEHOLDER_ONLY.fullmatch(value):
            spans.append((m.start(2), m.start(2) + len(value), 'address'))
    offset = 0
    for line in text.split('\n'):
        body = line.lstrip()
        lead = len(line) - len(body)
        bullet = re.match(_BULLET, body)
        lead += bullet.end() if bullet else 0
        standalone = _STREET_TRIGGER.match(line, lead) or _INTL.match(line, lead) or _RT_RW.match(line, lead)
        if standalone:                                   # a standalone address line: trigger to line end
            spans.append((offset + lead, offset + len(line.rstrip()), 'address'))
        else:
            for trig in _STREET_TRIGGER.finditer(line):  # inline: only the bounded address component
                end, pos, tokens = trig.end(), trig.end(), 0
                while (tok := _STREET_TOKEN.match(line, pos)):
                    pos = end = tok.end()
                    tokens += 1
                if tokens:
                    spans.append((offset + trig.start(), offset + end, 'address'))
            for m in (*_INTL.finditer(line), *_RT_RW.finditer(line)):
                spans.append((offset + m.start(), offset + m.end(), 'address'))
        offset += len(line) + 1
    return spans


# v2 reuses the v1 patterns, except that the profile pattern cannot stop inside a hyphenated GitHub handle
# (v1 matches "github.com/example" in "github.com/example-sari/repo" and leaves part of the handle behind).
_PATTERNS_V2 = {**_PATTERNS, 'profile': re.compile(
    r'(?i)(?:https?://)?(?:www\.)?(?:linkedin\.com/in/[\w%-]+/?|github\.com/[\w-]+/?(?![\w/-]))')}


def _pattern_spans(text: str) -> list[tuple[int, int, str]]:
    spans = []
    for kind, pattern in _PATTERNS_V2.items():
        for match in pattern.finditer(text):
            spans.append((*(match.span(1) if kind == 'identity_number' else match.span()), kind))
    return spans


def _apply(text: str, spans) -> tuple[str, dict[str, int]]:
    protected = [m.span() for m in _PLACEHOLDER_ONLY.finditer(text)]
    chosen, end = [], -1
    for start, stop, kind in sorted(set(spans), key=lambda v: (v[0], -v[1], v[2])):
        if start >= end and stop > start and not any(a < stop and start < b for a, b in protected):
            chosen.append((start, stop, kind))
            end = stop
    pieces, cursor, counts = [], 0, {}
    for start, stop, kind in chosen:
        pieces += [text[cursor:start], _PLACEHOLDER[kind]]
        cursor = stop
        counts[kind] = counts.get(kind, 0) + 1
    pieces.append(text[cursor:])
    return ''.join(pieces), counts


def sanitize_upload(text: str, *, marks: OwnerMarks | None = None) -> MaskedPreview:
    """D-104 sanitizer for uploaded or edited CV text. Raises `SanitizeRefused` (fixed code) to fail closed.

    `marks` are the owner fingerprints kept from the upload, so an edit that reintroduces the name
    is masked again. The returned preview carries the (possibly extended) marks; never the raw header.
    """
    from jobfit.privacy.structure import MASKING_FAILED, SanitizeRefused, normalize_source, split_structure
    if not isinstance(text, str) or (marks is not None and not isinstance(marks, OwnerMarks)):
        raise SanitizeRefused(MASKING_FAILED)
    failed = False
    try:
        structured = split_structure(normalize_source(text))
        owner = (marks if marks is not None else OwnerMarks()).extended(owner_values(structured.header))
        retained = structured.retained
        spans = _pattern_spans(retained) + _owner_spans(retained, owner) + _label_spans(retained) + \
            _address_spans(retained)
        masked, counts = _apply(retained, spans)
    except SanitizeRefused:
        raise
    except Exception:                                    # never a raw-text fallback, never the text in errors
        failed = True
    if failed:                                           # raised outside the handler: no chained context
        raise SanitizeRefused(MASKING_FAILED)
    guard = 'active' if owner else 'not_established'
    warnings = ['Check the exact text below. The contact header, the summary and personal sections were '
                'removed locally and remaining contact details were masked; automatic masking can miss things.']
    if guard == 'not_established':
        warnings.append('Your name could not be identified from the removed header; check that it does not '
                        'appear in the text below.')
    return MaskedPreview(masked, VERSION_V2, hashlib.sha256(masked.encode()).hexdigest(), counts, tuple(warnings),
                         removed=dict(structured.removed), owner_repeat_guard=guard, marks=owner)
