"""Turn service results into plain JSON for the UI. No business rule lives here."""
from __future__ import annotations

from collections.abc import Mapping

from jobfit.recommend.service import JobResult, Recommendation
from jobfit.schemas.analysis import ConstraintState
from jobfit.scoring.ranking import SCORED

NOTE = 'Match % is CV evidence coverage of the required items, not a hiring probability.'


def job_card(r: JobResult, meta: Mapping | None = None) -> dict:
    meta = meta or {}
    units = {u.unit_id: u for u in (r.extraction.units if r.extraction else [])}
    rows = []
    for a in r.assessments:
        u = units.get(a.unit_id)
        rows.append({'unit_id': a.unit_id, 'requirement': u.text if u else a.unit_id,
                     'importance': u.importance.value if u else None,
                     'field': u.field.value if u else None,
                     'label': a.label.value if a.label else None, 'check_status': a.check_status.value,
                     'cv_quotes': list(a.cv_quotes)})
    conflicts = [c.message for c in r.constraints if c.state == ConstraintState.EXPLICIT_CONFLICT]
    return {'job_id': r.job_id, 'title': meta.get('title'), 'company': meta.get('company'),
            'location': meta.get('location'), 'url': meta.get('url'),
            'score_pct': r.score.score_pct, 'status': r.score.status.value,
            'scored': r.score.status in SCORED,
            'matched': r.score.matched, 'partial': r.score.partial, 'required_total': r.score.required_total,
            'soft_skills': {'total': r.score.soft_skill_total, 'matched': r.score.soft_skill_matched,
                            'partial': r.score.soft_skill_partial},
            'reasons': list(r.score.reasons), 'hold_reason': r.hold_reason,
            'explicit_conflicts': conflicts, 'excluded_units': r.excluded_units,
            'requirements': rows, 'matcher_model': r.matcher_model, 'used_fallback': r.used_fallback}


def _groups(rec: Recommendation, ids: list[str], cards: dict) -> dict:
    conflict = [j for j in ids if cards[j]['scored'] and cards[j]['explicit_conflicts']]
    return {'matches': [cards[j] for j in ids if cards[j]['scored'] and j not in conflict],
            'conflicts': [cards[j] for j in conflict],
            'not_fully_analyzed': [cards[j] for j in ids if not cards[j]['scored']]}


def recommendation(rec: Recommendation, meta: Mapping[str, Mapping]) -> dict:
    cards = {j: job_card(rec.jobs[j], meta.get(j)) for j in rec.order}
    states = rec.filter_states or {}
    for j, card in cards.items():
        card['filter_state'] = states.get(j)
    if rec.active_filters:
        blocks = [{'title': 'Matches your filters', 'filter_state': 'matches',
                   'groups': _groups(rec, [j for j in rec.order if states.get(j) == 'matches'], cards)},
                  {'title': 'Filter information missing in the posting', 'filter_state': 'unknown',
                   'groups': _groups(rec, [j for j in rec.order if states.get(j) == 'unknown'], cards)}]
    else:
        blocks = [{'title': 'Target-role jobs', 'filter_state': None, 'groups': _groups(rec, rec.order, cards)}]
    return {'cv_id': rec.cv_id, 'note': NOTE, 'blocks': blocks,
            'active_filters': list(rec.active_filters), 'empty_message': rec.empty_message,
            'analyzed': len(rec.analyzed_ids), 'held': len(rec.held_ids),
            'demoted_by_seniority_rule': rec.demoted_ids, 'versions': rec.versions}
