"""D-104 structural data-minimization boundary for uploaded CVs; local and deterministic.

Keeps only the evidence-bearing professional sections. The identity/contact header, the
Summary/Profile/Objective family (a structural delimiter, never evidence) and privacy-only
sections are dropped. Heading lines that are kept stay verbatim. No model, network or data file.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
import unicodedata

BOUNDARY_NOT_FOUND = 'professional_boundary_not_found'
MASKING_FAILED = 'masking_failed'
MAX_HEADING_CHARS = 60
MAX_HEADER_LINES = 8          # non-empty lines of the identity/contact header used for owner provenance

SUMMARY_DELIMITER = frozenset({
    'summary', 'professional summary', 'career summary', 'profile', 'professional profile', 'personal profile',
    'about me', 'tentang saya', 'ringkasan', 'profil', 'profil profesional', 'profil pribadi', 'objective',
    'career objective', 'tujuan karier'})
EVIDENCE = frozenset({
    'experience', 'work experience', 'professional experience', 'employment history', 'pengalaman',
    'pengalaman kerja',
    'skills', 'technical skills', 'keahlian', 'kemampuan', 'keterampilan', 'skills & tools', 'hard skills',
    'projects', 'project', 'proyek',
    'education', 'pendidikan',
    'certifications', 'certification', 'sertifikasi',
    'training', 'pelatihan', 'courses', 'kursus',
    'publications', 'publikasi',
    'awards', 'achievements', 'prestasi',
    'languages', 'bahasa',
    'volunteering'})
PRIVACY = {   # heading -> category reported in the removal stats (counts only)
    **dict.fromkeys(('contact', 'contacts', 'contact information', 'contact details', 'kontak',
                     'informasi kontak'), 'contact'),
    **dict.fromkeys(('personal details', 'personal information', 'personal data', 'biodata', 'data pribadi',
                     'data diri', 'informasi pribadi'), 'personal'),
    **dict.fromkeys(('emergency contact', 'kontak darurat'), 'emergency_contact'),
    **dict.fromkeys(('references', 'referees', 'reference', 'referensi'), 'references'),
    **dict.fromkeys(('interests', 'minat'), 'interests'),
    **dict.fromkeys(('organizations', 'organisasi'), 'organizations'),
    **dict.fromkeys(('declaration', 'pernyataan', 'signature', 'tanda tangan'), 'declaration'),
}


class SanitizeRefused(Exception):
    """Fail closed with a fixed code; the message never carries CV text."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def normalize_source(text: str) -> str:
    """Reject lone surrogates, NFC, strip Unicode category Cf, line endings to \\n."""
    if any(0xD800 <= ord(ch) <= 0xDFFF for ch in text):
        raise SanitizeRefused(MASKING_FAILED)
    text = unicodedata.normalize('NFC', text)
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Cf')
    return text.replace('\r\n', '\n').replace('\r', '\n')


_MARKDOWN_HASHES = re.compile(r'^#{1,6}\s*')


def heading_key(line: str) -> str | None:
    """The normalized key of a whole-line heading candidate, used only for classification."""
    s = line.strip()
    if not s or len(s) > MAX_HEADING_CHARS:
        return None
    s = _MARKDOWN_HASHES.sub('', s).strip().strip('*_').strip()
    if s.endswith(':'):
        s = s[:-1].rstrip().strip('*_').strip()
    key = ' '.join(s.casefold().split()).replace(' and ', ' & ')
    return key or None


def classify(line: str) -> str | None:
    key = heading_key(line)
    if key in SUMMARY_DELIMITER:
        return 'summary'
    if key in EVIDENCE:
        return 'evidence'
    if key in PRIVACY:
        return 'privacy'
    return None


@dataclass(frozen=True)
class Structured:
    retained: str
    header: str = field(repr=False)     # identity/contact header only; transient, for the owner candidate
    removed: dict = field(default_factory=dict)


def split_structure(text: str) -> Structured:
    """Apply the D-104 boundary to normalized text; raise SanitizeRefused when no start exists."""
    lines = text.split('\n')
    kinds = [classify(line) for line in lines]
    summary_at = next((i for i, k in enumerate(kinds) if k == 'summary'), None)
    search_from = 0 if summary_at is None else summary_at + 1
    start = next((i for i in range(search_from, len(lines)) if kinds[i] == 'evidence'), None)
    if start is None:
        raise SanitizeRefused(BOUNDARY_NOT_FOUND)
    removed = {'header_lines': sum(1 for line in lines[:summary_at if summary_at is not None else start]
                                   if line.strip()),
               'summary_sections': int(summary_at is not None)}
    retained, dropping = [], False
    for line, kind in zip(lines[start:], kinds[start:]):
        if kind == 'summary' or kind == 'privacy':
            dropping = True
            category = 'summary_sections' if kind == 'summary' else PRIVACY[heading_key(line)]
            removed[category] = removed.get(category, 0) + 1
            continue
        if kind == 'evidence':
            dropping = False
        if not dropping:
            retained.append(line)
    if not any(line.strip() and kind is None for line, kind in zip(retained, map(classify, retained))):
        raise SanitizeRefused(BOUNDARY_NOT_FOUND)
    return Structured('\n'.join(retained), header_region(lines, kinds), removed)


def header_region(lines: list[str], kinds: list[str | None]) -> str:
    """Lines before the first recognised heading of any kind, capped at MAX_HEADER_LINES non-empty lines.

    The Summary block, earlier dropped sections and privacy sections are never part of it, so they can
    never establish the owner's identity.
    """
    header, count = [], 0
    for line, kind in zip(lines, kinds):
        if kind is not None:
            break
        if line.strip():
            count += 1
            if count > MAX_HEADER_LINES:
                break
        header.append(line)
    return '\n'.join(header)
