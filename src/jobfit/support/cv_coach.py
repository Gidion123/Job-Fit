"""CV coach v1 (D-036, docs/cv-coach-plan.md). Deterministic, no model call.

For one analyzed job: at most three of the most important gaps (required, not found or only
partly supported, excluding years, location and work permits), each with the four fixed
questions. A bullet is assembled only from the user's own answers, with every part linked to
the answer it came from; the only added words are the fixed connectors in TEMPLATE_WORDS.
"Not done" gives no bullet, only learning or project ideas. Answers never change the score.
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


def gaps_for_job(card: dict, *, limit: int = 3) -> list[dict]:
    rows = [r for r in card.get('requirements', [])
            if r.get('importance') == 'required' and r.get('label') in ('NO_MATCH', 'PARTIAL')
            and r.get('field') not in NOT_EDITABLE]
    # Not found before partly supported (bigger gap first); keep the JD order inside each group.
    rows = sorted(rows, key=lambda r: 0 if r['label'] == 'NO_MATCH' else 1)[:limit]
    return [{'gap_index': i, 'requirement': r['requirement'], 'label': r['label'],
             'question_first': f"Have you worked on: {r['requirement']}?", 'questions': QUESTIONS}
            for i, r in enumerate(rows)]


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
