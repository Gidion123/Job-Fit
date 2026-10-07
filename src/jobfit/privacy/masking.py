"""Versioned local direct-identifier masking; no model, disk or network.

Pattern detection is incomplete. Names and detailed addresses require reviewed
hints. Employer/institution and city policy remains undecided: preserve these
in synthetic experiments and block real-CV enablement pending that decision.
"""
from dataclasses import dataclass, field
import hashlib
import re

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
