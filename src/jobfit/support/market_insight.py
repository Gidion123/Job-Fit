"""Skill counts over the searchable job corpus with a short cited explanation (minimal).

Deterministic counts from the CP1 skill taxonomy (`skills` per job), no model call.
The explanation cites the counts it is built from; it never estimates the wider market.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping

ROLE_FAMILIES = ('ai_ml_engineering', 'data_science', 'genai_llm', 'software_ai')


def skill_counts(jobs: Mapping[str, Mapping], *, role_family: str | None = None, top: int = 15) -> dict:
    if role_family is not None and role_family not in ROLE_FAMILIES:
        raise ValueError('role_family must be one of the four target families')
    pool = [j for j in jobs.values() if j.get('role_group', 'target') == 'target'
            and (role_family is None or j.get('role_family') == role_family)]
    counts = Counter(s for j in pool for s in set(j.get('skills') or []))
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top]   # ties by name: deterministic
    rows = [{'skill': s, 'jobs': n, 'share': round(n / len(pool), 3)} for s, n in ranked] if pool else []
    if rows:
        lead = rows[0]
        text = (f"In {len(pool)} searchable postings{' for ' + role_family if role_family else ''}, "
                f"{lead['skill']} appears in {lead['jobs']} ({lead['share']:.0%}). "
                'Counts come from the CP1 skill list of each posting, not from the whole job market.')
    else:
        text = 'No postings match this filter.'
    return {'postings': len(pool), 'role_family': role_family, 'skills': rows, 'explanation': text,
            'source': 'jobs_features.jsonl skills (CP1 taxonomy v0)'}
