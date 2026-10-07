"""Conservative source-coverage diagnostic, never a semantic recall metric.

Only explicit bulleted qualification sections are supported. An uncovered bullet
requires review; a covered bullet does not establish that its whole meaning was
extracted. No automatic requirement, importance, or denominator is invented.
"""
import re

COVERAGE_VERSION = 'qualification-bullet-coverage-v1'
_HEADING = re.compile(r'(?i)^(?:required\s+)?(?:qualifications?(?:\s+and\s+requirements)?|requirements?|kualifikasi|persyaratan)\s*:?$')
_END = re.compile(r'(?i)^(?:responsibilities|job responsibilities|tanggung jawab|benefits|what we offer|about us|about the company)\s*:?$')
_BULLET = re.compile(r'^\s*(?:[•*\-]|\d+[.)])\s+(.+)')


def qualification_coverage(text, units):
    bullets = []
    active = False
    for raw in text.splitlines():
        line = raw.strip()
        heading = line.strip('#* ').strip()
        if _HEADING.fullmatch(heading):
            active = True
            continue
        if not active:
            continue
        if _END.fullmatch(heading):
            active = False
            continue
        match = _BULLET.match(raw)
        if match:
            bullets.append(match.group(1))
        elif line and bullets:
            # A non-bulleted heading/prose might start another section. Limit
            # this diagnostic rather than guessing boundaries or wrapped text.
            active = False
    quotes = [q for u in units for q in u.source_quotes if q.strip()]
    uncovered = [i + 1 for i, b in enumerate(bullets)
                 if not any(q in b or b in q for q in quotes)]
    return {'version': COVERAGE_VERSION,
            'status': ('review_required' if uncovered else 'no_uncovered_bullets') if bullets else 'not_assessed',
            'bullet_count': len(bullets), 'uncovered_bullet_indices': uncovered,
            'semantic_completeness_verified': False}
