"""Evidence-based CV suggestions with the claim guard (minimal, deterministic, no model call).

Input: the presented job cards of one finished run. For required items that are only
partly supported or not found, it counts how many analyzed jobs ask for them and writes
a suggestion. Claim guard: a suggestion never tells the user to claim something the CV
does not show. "Not found" items are framed as learning gaps or as "add it only if true".
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

NOT_EDITABLE = {'experience_duration', 'location', 'work_authorization'}
GUARD = ('These suggestions only use what your CV already shows. Never add a skill or experience '
         'you do not have; items marked "not found" are learning gaps unless you really have them.')


def suggestions(cards: Sequence[dict], *, top: int = 8) -> dict:
    scored = [c for c in cards if c.get('scored')]
    gaps: dict[str, dict] = defaultdict(lambda: {'jobs': set(), 'labels': set(), 'quotes': []})
    for card in scored:
        for r in card.get('requirements', []):
            if r.get('importance') != 'required' or r.get('label') not in ('PARTIAL', 'NO_MATCH'):
                continue
            if r.get('field') in NOT_EDITABLE:
                continue   # years, location and work permits are facts, not CV wording
            key = ' '.join(r['requirement'].split()).strip().lower()
            g = gaps[key]
            g['text'] = r['requirement']
            g['soft'] = r.get('field') == 'soft_skill'
            g['jobs'].add(card['job_id'])
            g['labels'].add(r['label'])
            g['quotes'].extend(q for q in r.get('cv_quotes', []) if q not in g['quotes'])
    items = []
    for g in sorted(gaps.values(), key=lambda g: (-len(g['jobs']), g['text'])):
        partial = 'PARTIAL' in g['labels'] and g['quotes']
        if g.get('soft'):
            advice = ('Soft skill (shown next to the score, not in it). If true, show it with a short '
                      'example from a project or job, not only the word.')
            kind = 'soft_skill'
        elif partial:
            advice = ('Your CV shows related evidence. If it is accurate, describe it more directly '
                      '(what you did, the tool, the result) so the link to this requirement is clear.')
            kind = 'make_explicit'
        else:
            advice = ('Not found in your CV. Add it only if you really have this experience; '
                      'otherwise treat it as a learning gap.')
            kind = 'gap'
        items.append({'requirement': g['text'], 'jobs_asking': len(g['jobs']), 'kind': kind,
                      'advice': advice, 'cv_quotes': g['quotes'][:2]})
    return {'guard': GUARD, 'analyzed_scored_jobs': len(scored), 'items': items[:top],
            'note': 'Counted only over the scored jobs of this run; held jobs are not used.'}
