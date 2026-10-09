"""CV coach (D-036 v1, refined by D-105; docs/cv-coach-plan.md). Deterministic, no model call.

"Improve My CV for This Job" puts every required requirement of one analyzed job in at most one
of four categories (mutually exclusive):

- A, representation improvement (``representation_items``): PARTIAL, editable field. Shows the
  exact CV evidence, the job's requirement as the job's words, and one fixed guidance sentence. No
  rewritten CV line is produced, so a JD term can never become a claim about the candidate.
- B, possibly missing from the CV (``gaps_for_job``): NOT FOUND, editable field; at most three,
  each with the four fixed questions. A bullet is assembled only from the user's own answers, with
  every part linked to the answer it came from; the only added words are the fixed connectors in
  TEMPLATE_WORDS. "Not done" gives no bullet, only learning ideas. (v1 also put PARTIAL here; D-105
  moves PARTIAL to A.)
- C, true gap (``true_gaps``): only a confirmed factual conflict (the D-086 experience conflict,
  which needs a confirmed complete work history). No learning or project advice.
- Not verified (``not_verified``): a years, location or work-permit requirement this CV does not
  establish, with no confirmed conflict. Absence is never presented as a gap.

``requirement_groups`` gives the Analyze Fit view the same categorization (conflict > not verified >
strengths and evidence gaps), so the UI only renders it.

Answers stay in the session and never change the score.
"""
from __future__ import annotations

import re

QUESTIONS = {'what_when': 'What was the project or job, and when?',
             'own_part': 'Which part did you do yourself?',
             'tools': 'Which tools or methods did you use?',
             'result': 'What was the result? Is there a number? (leave empty if none)'}
TEMPLATE_WORDS = {'using', 'result'}
NOT_EDITABLE = {'experience_duration', 'location', 'work_authorization'}
MAX_ANSWER = 300


REPRESENTATION_GUIDANCE = ('If accurate, make this line more specific: what you did, which tool or method, and '
                           'the result. Name a tool or skill only if you actually used it.')
TRUE_GAP_NOTE = 'A fact about your background, not wording; changing the CV cannot fix it.'
NOT_VERIFIED_NOTE = 'Not verified from this CV.'


def _required(card: dict, labels: tuple[str, ...]) -> list[dict]:
    return [r for r in card.get('requirements', [])
            if r.get('importance') == 'required' and r.get('label') in labels]


def _dedupe(texts) -> list[str]:
    seen, out = set(), []
    for text in texts:
        key = ' '.join(str(text).split()).casefold()
        if key and key not in seen:
            seen.add(key)
            out.append(text)
    return out


def gaps_for_job(card: dict, *, limit: int = 3) -> list[dict]:
    """B: required, not found in the CV, editable field; JD order; at most ``limit``."""
    rows = [r for r in _required(card, ('NO_MATCH',)) if r.get('field') not in NOT_EDITABLE][:limit]
    return [{'gap_index': i, 'requirement': r['requirement'], 'label': r['label'],
             'question_first': f"Have you worked on: {r['requirement']}?", 'questions': QUESTIONS}
            for i, r in enumerate(rows)]


def representation_items(card: dict) -> list[dict]:
    """A: required, partly supported, editable field. Evidence and fixed guidance only, never a rewrite."""
    return [{'requirement': r['requirement'], 'asked': f"This job asks for: {r['requirement']}",
             'current': list(r.get('cv_quotes', [])), 'guidance': REPRESENTATION_GUIDANCE,
             'evidence': list(r.get('cv_quotes', []))}
            for r in _required(card, ('PARTIAL',)) if r.get('field') not in NOT_EDITABLE]


def true_gaps(card: dict) -> list[dict]:
    """C: confirmed factual conflicts only (D-086 explicit conflicts), deduplicated; no advice."""
    return [{'conflict': c, 'note': TRUE_GAP_NOTE} for c in _dedupe(card.get('explicit_conflicts') or [])]


def _conflicted_units(card: dict) -> set[str]:
    """Units named by a confirmed D-086 conflict ("U3: the JD asks for ...": the message starts with its unit id)."""
    return {str(c).split(':', 1)[0].strip() for c in card.get('explicit_conflicts') or []}


def not_verified(card: dict) -> list[dict]:
    """Years, location or work-permit requirements this CV does not establish, without a confirmed conflict.

    Deduplicated by requirement text; ``unit_ids`` lists every unit behind one item.
    """
    conflicted = _conflicted_units(card)
    rows = [r for r in _required(card, ('NO_MATCH', 'PARTIAL'))
            if r.get('field') in NOT_EDITABLE and r.get('unit_id') not in conflicted]
    items: dict[str, dict] = {}
    for r in rows:
        key = ' '.join(r['requirement'].split()).casefold()
        item = items.setdefault(key, {'requirement': r['requirement'], 'unit_ids': [], 'note': NOT_VERIFIED_NOTE})
        if r.get('unit_id') is not None:
            item['unit_ids'].append(r['unit_id'])
    return list(items.values())


def requirement_groups(card: dict) -> dict[str, list[str]]:
    """The Analyze Fit view of the required units, each in exactly one group (presentation contract, D-105).

    Precedence: a confirmed D-086 ``conflict`` first, then ``not_verified`` (an unconfirmed years, location
    or work-permit requirement), then ``strengths`` (MATCH) and ``gaps`` (PARTIAL or NO_MATCH, editable).
    Unchecked rows stay ungrouped (they remain in the evidence table). Labels and the score are unchanged.
    """
    required = [r for r in card.get('requirements', []) if r.get('importance') == 'required' and r.get('unit_id')]
    conflicted = _conflicted_units(card)
    groups: dict[str, list[str]] = {'conflict': [], 'not_verified': [], 'strengths': [], 'gaps': []}
    taken: set[str] = set()
    groups['conflict'] = [r['unit_id'] for r in required if r['unit_id'] in conflicted]
    taken.update(groups['conflict'])
    unverified = {u for item in not_verified(card) for u in item['unit_ids']}
    groups['not_verified'] = [r['unit_id'] for r in required if r['unit_id'] in unverified and r['unit_id'] not in taken]
    taken.update(groups['not_verified'])
    for r in required:
        if r['unit_id'] in taken:
            continue
        if r.get('label') == 'MATCH':
            groups['strengths'].append(r['unit_id'])
        elif r.get('label') in ('PARTIAL', 'NO_MATCH'):
            groups['gaps'].append(r['unit_id'])
    return groups


def _clean(text: str | None) -> str:
    text = ' '.join((text or '').split())[:MAX_ANSWER]
    return text.rstrip('.')


def bullet(requirement: str, done: bool, answers: dict | None) -> dict:
    if not done:
        return {'bullet': None, 'parts': [],
                'ideas': [f'Learn the basics of: {requirement}.',
                          'Build a small project that uses it, then describe that project on your CV.',
                          'Run the matching again after you update your CV; answers never change the score.']}
    a = {k: _clean((answers or {}).get(k)) for k in QUESTIONS}
    if not a['own_part'] or not a['what_when']:
        raise ValueError('Answer at least what you did yourself and which project or job it was')
    parts = [{'text': a['own_part'][0].upper() + a['own_part'][1:], 'source': 'own_part'}]
    if a['tools']:
        parts += [{'text': 'using', 'source': 'template'}, {'text': a['tools'], 'source': 'tools'}]
    text = ' '.join(p['text'] for p in parts)
    if a['result']:
        text += f"; result: {a['result']}"
        parts += [{'text': 'result', 'source': 'template'}, {'text': a['result'], 'source': 'result'}]
    text += f" ({a['what_when']})."
    parts.append({'text': a['what_when'], 'source': 'what_when'})
    return {'bullet': text, 'parts': parts, 'ideas': [],
            'note': 'Built only from your answers. Check it, then accept, edit, reject or copy it.'}


def unsupported_words(bullet_text: str, answers: dict) -> set[str]:
    """Words in the bullet that come from neither the answers nor the fixed connectors."""
    source = ' '.join(str(v or '') for v in answers.values()).casefold()
    allowed = set(re.findall(r'\w+', source)) | TEMPLATE_WORDS
    return {w for w in re.findall(r'\w+', bullet_text.casefold()) if w not in allowed}
