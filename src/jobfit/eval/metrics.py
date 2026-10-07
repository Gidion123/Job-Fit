"""Pure D-052 diagnostics. Publication still needs reviewed references and alignment."""
import math

LABELS = ('MATCH', 'PARTIAL', 'NO_MATCH')


def fraction(numerator, denominator, reason=None):
    result = {'numerator': numerator, 'denominator': denominator,
              'value': numerator / denominator if denominator else None}
    if reason or not denominator:
        result['reason'] = reason or 'zero_denominator'
    return result


def ranking_metrics(ranking, judgments, *, eligible_ids, k, protocol='evaluation-contract-v1'):
    """Original-rank metrics on a declared judged pool; never condense the ranking.

    Primary publication uses P@5 and NDCG@10. Values at other cutoffs are
    diagnostics with the same original-position rule. A shorter ranking has no
    approved convention and is unavailable at that cutoff.
    """
    if protocol != 'evaluation-contract-v1':
        raise ValueError('D-052 protocol required; historical condensed metrics need an explicit separate implementation')
    if type(k) is not int or k < 1 or len(ranking) != len(set(ranking)):
        raise ValueError('Positive K and unique ranked identities required')
    eligible = set(eligible_ids)
    if len(eligible) != len(eligible_ids) or not set(ranking) <= eligible:
        raise ValueError('Duplicate eligible ID or ranking outside declared filtered scope')
    if any(type(v) is not int or v not in range(4) for v in judgments.values()):
        raise ValueError('Relevance must be an explicit integer 0 to 3')
    available = {j: v for j, v in judgments.items() if j in eligible}
    relevant = {j for j, v in available.items() if v >= 2}
    top = ranking[:k]
    unjudged_top = [j for j in top if j not in available]
    short = len(top) < k
    true_top_relevant = sum(available.get(j, -1) >= 2 for j in top)
    reason = 'short_ranking_convention_pending' if short else 'missing_original_position_judgment' if unjudged_top else None
    precision = fraction(true_top_relevant, k, reason)
    if reason:
        precision['value'] = None
    recall = fraction(true_top_relevant, len(relevant), 'zero_judged_relevant_denominator' if not relevant else
                      'short_ranking_convention_pending' if short else None)
    if short:
        recall['value'] = None
    ideal = None
    ndcg = None
    ndcg_reason = reason
    if not reason:
        gain = lambda r: 2 ** r - 1
        dcg = lambda values: sum(gain(v) / math.log2(i + 2) for i, v in enumerate(values))
        ideal = dcg(sorted(available.values(), reverse=True)[:k])
        if ideal:
            ndcg = dcg([available[j] for j in top]) / ideal
        else:
            ndcg_reason = 'zero_ideal_dcg'
    return {
        'k': k, 'scope': 'labeled_pool_only',
        'ranking_protocol': 'D-052_original_positions',
        'recall_protocol': 'original_top_k_declared_judged_eligible_pool',
        'recall_at_k': recall,
        'filter_recall': fraction(len(relevant), sum(v >= 2 for v in judgments.values()),
                                  'zero_pre_filter_judged_relevant_denominator' if not any(v >= 2 for v in judgments.values()) else None),
        'precision_at_k': precision, 'ndcg_at_k': ndcg,
        'ndcg_reason': ndcg_reason, 'ndcg_ideal_dcg': ideal,
        'ndcg_ideal_scope': 'all_eligible_judged_pool', 'ndcg_gain': 'exponential',
        'coverage': {'ranked': len(ranking), 'judged_ranked': sum(j in available for j in ranking),
                     'unjudged_ranked': sum(j not in available for j in ranking),
                     'unjudged_original_top_k': len(unjudged_top),
                     'unjudged_original_top_k_ids': unjudged_top,
                     'judged_pool': len(judgments), 'judged_after_filter': len(available),
                     'eligible_jobs': len(eligible),
                     'judged_at_metric_cutoff': len(top) - len(unjudged_top),
                     'returned_at_metric_cutoff': len(top)}
    }


def _prediction(value):
    if isinstance(value, dict):
        state, label = value.get('status'), value.get('label')
        if state == 'done' and label in LABELS:
            return label
        if state in {'failed', 'needs_clarification', 'not_assessed'} and label is None:
            return None
        raise ValueError('Contradictory evidence status/label')
    if value in LABELS or value is None:
        return value
    raise ValueError('Invalid evidence prediction')


def evidence_metrics(gold, predictions, *, alignment_verified, protocol='evaluation-contract-v1'):
    """All-reference three-class accounting; failed output is a gold-class FN."""
    if protocol != 'evaluation-contract-v1':
        raise ValueError('D-052 evidence protocol required')
    if alignment_verified is not True:
        raise ValueError('Verified semantic alignment is required, not equal unit IDs')
    if any(v not in LABELS for v in gold.values()):
        raise ValueError('Invalid gold evidence class')
    if not predictions.keys() <= gold.keys():
        raise ValueError('Predictions contain unaligned identities')
    pred = {key: _prediction(value) for key, value in predictions.items()}
    matrix = {t: {p: 0 for p in (*LABELS, 'not_assessed')} for t in LABELS}
    for identity, truth in gold.items():
        matrix[truth][pred.get(identity) or 'not_assessed'] += 1
    rows = {}
    for label in LABELS:
        tp = matrix[label][label]
        fn = sum(matrix[label].values()) - tp
        fp = sum(matrix[t][label] for t in LABELS if t != label)
        support = tp + fn
        rows[label] = {
            'tp': tp, 'fp': fp, 'fn': fn, 'support': support,
            'precision': tp / (tp + fp) if tp + fp else None,
            'recall': tp / support if support else None,
            'f1': 2 * tp / (2 * tp + fp + fn) if support else None,
        }
    complete = all(rows[label]['support'] > 0 for label in LABELS)
    return {'classes': list(LABELS), 'confusion': matrix, 'per_class': rows,
            'class_support_complete': complete,
            'macro_f1': sum(rows[label]['f1'] for label in LABELS) / 3 if complete else None,
            'selection_blocker': None if complete else 'aggregate_gold_missing_one_or_more_classes',
            'coverage': fraction(sum(pred.get(i) is not None for i in gold), len(gold)),
            'protocol': 'D-052_all_reference_not_assessed_FN'}


def extraction_metrics(alignment, *, reference_complete):
    if reference_complete is not True or alignment.get('human_verified') is not True:
        raise ValueError('Whole-JD completeness and verified semantic alignment required')
    if alignment.get('unmapped_gold') or alignment.get('unmapped_model'):
        raise ValueError('Unmapped records require alignment review')
    gold_ids=alignment.get('gold_unit_ids')
    model_ids=alignment.get('model_unit_ids')
    if not isinstance(gold_ids,list) or not isinstance(model_ids,list) or not gold_ids or not model_ids:
        raise ValueError('Complete reference and model unit inventories are required')
    if len(gold_ids)!=len(set(gold_ids)) or len(model_ids)!=len(set(model_ids)):
        raise ValueError('Duplicate inventory identity')
    seen_g = set(); seen_m = set(); tp = fp = fn = split_merge = 0
    for row in alignment['rows']:
        g, m = row['gold_ids'], row['model_ids']
        if len(g) != len(set(g)) or len(m) != len(set(m)) or seen_g & set(g) or seen_m & set(m):
            raise ValueError('Duplicate aligned unit')
        seen_g.update(g); seen_m.update(m)
        if row.get('status') != 'verified' or type(row.get('semantic_equivalent')) is not bool:
            raise ValueError('Each mapping needs semantic verification')
        if len(g) > 1 and len(m) > 1:
            raise ValueError('Complex many-to-many alignment has no approved F1 convention')
        if len(g) > 1 or len(m) > 1:
            # D-054: independently assessable logical units count strictly.
            # A verified clause-level relation never creates multiple TPs.
            split_merge += 1
            fn += len(g); fp += len(m)
            continue
        if len(g) == len(m) == 1 and row['semantic_equivalent']:
            tp += 1
        else:
            fn += len(g); fp += len(m)
    if seen_g!=set(gold_ids) or seen_m!=set(model_ids):
        raise ValueError('Alignment omits or invents inventory identities')
    return {'tp': tp, 'fp': fp, 'fn': fn, 'split_merge_relations': split_merge,
            'alignment_policy': 'D-054_strict_independently_assessable_logical_units',
            'precision': fraction(tp, tp + fp), 'recall': fraction(tp, tp + fn),
            'f1': fraction(2 * tp, 2 * tp + fp + fn)}


def operational_summary(records):
    """Nearest-rank percentiles, live and cached separate; missing timings counted."""
    groups = {}
    for cached in [False, True]:
        rows = [r for r in records if bool(r.get('cached')) == cached]
        times = [r['latency_ms'] for r in rows if r.get('latency_ms') is not None]
        costs = [r.get('cost_usd') for r in rows]
        if any(not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0 for x in times):
            raise ValueError('Invalid latency')
        if any(x is None or not math.isfinite(x) or x < 0 for x in costs):
            raise ValueError('Missing/invalid cost is not zero')
        times.sort()
        pct = lambda p: times[max(0, math.ceil(p * len(times)) - 1)] if times else None
        groups['cached' if cached else 'live'] = {
            'records': len(rows), 'cost_usd': sum(costs),
            'latency_observed': len(times), 'latency_missing': len(rows) - len(times),
            'p50_ms': pct(.5), 'p95_ms': pct(.95), 'percentile_method': 'nearest_rank',
            'failures': sum(r.get('ok') is False for r in rows)}
    return groups
