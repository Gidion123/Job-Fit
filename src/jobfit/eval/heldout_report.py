"""CP2.4 held-out report contract (D-053), frozen before any test result exists.

- PRIMARY (headline): CV3, CV4, CV5. Held-out profiles AND held-out jobs. Only these CVs
  may form the headline held-out metric.
- SUPPLEMENTARY: CV1, CV2. Familiar profiles (used in development) on held-out jobs. A
  diagnostic only; never part of the headline.
- There is no pooled CV1-CV5 metric. `build_report` has no code path that averages across
  the two groups, and `check_contract` rejects any report that contains one.
Metrics follow D-052 (original positions, P@5 and NDCG@10, missing labels never zero) on the
product order (D-073). Each group's macro uses only CVs where both orders are available
(paired common subset); the CV count and every omitted CV with its reason are reported.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from jobfit.eval.metrics import ranking_metrics

CONTRACT_VERSION = 'cp24-report-contract-v1'
PRIMARY = ('CV3', 'CV4', 'CV5')
SUPPLEMENTARY = ('CV1', 'CV2')
ROLES = {'primary_heldout': 'headline: held-out profiles and held-out jobs',
         'supplementary_familiar': 'diagnostic: development profiles on held-out jobs; never part of the headline'}
FORBIDDEN_KEYS = ('pooled', 'all_cvs', 'cv1_cv5', 'overall', 'combined')


def _metrics(order: Sequence[str], judged: Mapping[str, int], eligible: Sequence[str]) -> dict:
    p5 = ranking_metrics(list(order), dict(judged), eligible_ids=list(eligible), k=5)
    n10 = ranking_metrics(list(order), dict(judged), eligible_ids=list(eligible), k=10)
    return {'p_at_5': p5['precision_at_k']['value'], 'ndcg_at_10': n10['ndcg_at_k'],
            'p5_reason': p5['precision_at_k'].get('reason'), 'ndcg_reason': n10['ndcg_reason'],
            'unjudged_top10': n10['coverage']['unjudged_original_top_k_ids']}


def _group(name: str, cvs: Sequence[str], per_cv: Mapping[str, dict]) -> dict:
    out = {'role': ROLES[name], 'cvs': list(cvs)}
    for metric in ('p_at_5', 'ndcg_at_10'):
        usable = [cv for cv in cvs if per_cv[cv]['stage1'][metric] is not None and per_cv[cv]['final'][metric] is not None]
        omitted = {cv: {'stage1': per_cv[cv]['stage1']['p5_reason' if metric == 'p_at_5' else 'ndcg_reason'],
                        'final': per_cv[cv]['final']['p5_reason' if metric == 'p_at_5' else 'ndcg_reason']}
                   for cv in cvs if cv not in usable}
        mean = lambda order: (sum(per_cv[cv][order][metric] for cv in usable) / len(usable)) if usable else None
        out[metric] = {'stage1_macro': mean('stage1'), 'final_macro': mean('final'),
                       'cv_count': len(usable), 'planned_cv_count': len(cvs), 'omitted': omitted}
    return out


def build_report(run: Mapping, judgments: Mapping[str, Mapping[str, int]], *, eligible: Sequence[str]) -> dict:
    cvs = set(run['cvs'])
    if cvs != set(PRIMARY) | set(SUPPLEMENTARY):
        raise ValueError(f'The test run must cover exactly CV1-CV5, got {sorted(cvs)}')
    if not set(judgments) <= cvs:
        raise ValueError('Judgments for an unknown CV')
    per_cv = {}
    for cv in sorted(cvs):
        judged = judgments.get(cv, {})
        per_cv[cv] = {'group': 'primary_heldout' if cv in PRIMARY else 'supplementary_familiar',
                      'stage1': _metrics(run['cvs'][cv]['stage1_ids'], judged, eligible),
                      'final': _metrics(run['cvs'][cv]['final_order'], judged, eligible),
                      'judged_pairs': len(judged)}
    report = {'contract': CONTRACT_VERSION, 'run_id': run.get('run_id'),
              'headline': 'primary_heldout',
              'primary_heldout': _group('primary_heldout', PRIMARY, per_cv),
              'supplementary_familiar': _group('supplementary_familiar', SUPPLEMENTARY, per_cv),
              'per_cv': per_cv,
              'rules': ['Headline = primary_heldout (CV3-CV5) only.',
                        'CV1-CV2 are a familiar-profile diagnostic, never pooled with CV3-CV5.',
                        'Missing labels are never zero; omitted CVs are listed with reasons.']}
    check_contract(report)
    return report


def check_contract(report: Mapping) -> None:
    """Reject any report that breaks the separation. Used by the builder and by tests."""
    if report.get('contract') != CONTRACT_VERSION or report.get('headline') != 'primary_heldout':
        raise ValueError('Report does not follow the frozen CP2.4 contract')
    if tuple(report['primary_heldout']['cvs']) != PRIMARY or tuple(report['supplementary_familiar']['cvs']) != SUPPLEMENTARY:
        raise ValueError('Group membership changed')

    def walk(node, path=''):
        if isinstance(node, Mapping):
            for k, v in node.items():
                if any(f in str(k).lower() for f in FORBIDDEN_KEYS):
                    raise ValueError(f'Pooled metric key not allowed: {path}/{k}')
                walk(v, f'{path}/{k}')
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f'{path}[{i}]')
    walk(report)


def headline_text(report: Mapping) -> str:
    """The one sentence a report or slide may use as the held-out result."""
    check_contract(report)
    g = report['primary_heldout']
    n, p = g['ndcg_at_10'], g['p_at_5']
    fmt = lambda v: 'unavailable' if v is None else f'{v:.3f}'
    return (f"Held-out test (CV3-CV5, {n['cv_count']} of 3 CVs with complete labels): final order NDCG@10 "
            f"{fmt(n['final_macro'])} (stage 1 {fmt(n['stage1_macro'])}), P@5 {fmt(p['final_macro'])} "
            f"(stage 1 {fmt(p['stage1_macro'])}). CV1-CV2 are reported separately as a familiar-profile diagnostic.")
