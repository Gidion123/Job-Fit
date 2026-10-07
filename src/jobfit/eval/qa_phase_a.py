"""Phase A (post-test quality optimization) helpers: leakage guard, development benchmark,
metrics and experiment registry (D-089). No model call happens in this module.

CP2.4 is locked from optimization: its labels, workbook, results and the held-out CVs
(CV3-CV5) can never be read or used here. Every file read goes through `dev_path`.
"""
from __future__ import annotations

import csv
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import random
import statistics

from jobfit.eval.metrics import evidence_metrics
from jobfit.schemas.analysis import CheckStatus, UnitAssessment
from jobfit.schemas.requirements import JDExtraction
from jobfit.scoring.score import effective_label

ROOT = Path(__file__).resolve().parents[3]
QA_DIR = ROOT / 'evals/results/quality_optimization'
REGISTRY = QA_DIR / 'experiment_registry.csv'
DEV_GOLD = ROOT / 'evals/gold/development_v13_reviewed_20261004_gap_r4'
SPLIT_SEED = 20261007
DEV_CVS = ('CV1', 'CV2')
FORBIDDEN_CVS = frozenset({'CV3', 'CV4', 'CV5'})
FORBIDDEN_PATHS = ('evals/gold/test_v13_cp24_r1', 'evals/labeling/test_relevance_cp24_test_v1_v1',
                   'evals/results/cp24', 'evals/pools/test_pool_cp24_test_v1_v1',
                   'data/synthetic_cvs/cv_03', 'data/synthetic_cvs/cv_04', 'data/synthetic_cvs/cv_05')
REGISTRY_COLUMNS = ['experiment_id', 'date', 'status', 'hypothesis_id', 'parent_experiment', 'model', 'prompt_file',
                    'prompt_version', 'prompt_sha256', 'dataset', 'dataset_sha256', 'sample_count', 'p_at_5',
                    'ndcg_at_10', 'macro_f1', 'quote_validity', 'hallucination_count', 'unsupported_positive_count',
                    'schema_failure_count', 'repair_count', 'hold_rate', 'fallback_count', 'run_to_run_agreement',
                    'total_cost_usd', 'cost_per_pair', 'median_latency', 'p95_latency', 'decision', 'decision_reason']
STATUSES = ('planned', 'dry_run', 'completed', 'rejected', 'finalist', 'selected', 'baseline', 'invalid', 'withdrawn')
ORDER = {'NO_MATCH': 0, 'PARTIAL': 1, 'MATCH': 2}
# Amendment 1 to D-089: failure classes. Transient provider/network/budget errors are not prompt errors.
TRANSIENT_CODES = frozenset({'APITimeoutError', 'APIConnectionError', 'RateLimitError', 'InternalServerError',
                             'ServiceUnavailableError', 'ReadTimeout', 'ConnectTimeout', 'ConnectError',
                             'RunCapReached', 'BudgetExceeded', 'PermissionDeniedError', 'AuthenticationError'})
PROMPT_CODES = frozenset({'truncated', 'schema_validation', 'invalid_structured_output_or_source', 'IncompleteStructuredResponse',
                          'UnexpectedResponseModel', 'invalid_source_quote', 'missing_source_quote', 'assessment_coverage',
                          'branch_coverage', 'group_label_must_be_resolved_by_scorer', 'unresolved_unit_needs_review',
                          'qualified_MATCH_needs_bounded_duration', 'unbounded_required_duration_needs_clarification',
                          'TruncatedStructuredResponse', 'ValidationError', 'JSONDecodeError'})


def failure_class(code) -> str:
    """prompt_induced (counts against the prompt), transient_operational (recover or invalidate), unclassified (Dion decides)."""
    if code in PROMPT_CODES:
        return 'prompt_induced'
    if code in TRANSIENT_CODES:
        return 'transient_operational'
    return 'unclassified'


class LeakageError(RuntimeError):
    """Raised when Phase A code touches CP2.4 test material."""


def digest(path: Path) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def dev_path(path) -> Path:
    """Resolve a path and refuse anything that belongs to the locked CP2.4 test."""
    p = Path(path)
    p = (ROOT / p) if not p.is_absolute() else p
    rel = p.resolve().as_posix()
    for bad in FORBIDDEN_PATHS:
        if f'/{bad}' in rel or rel.endswith(bad):
            raise LeakageError(f'Phase A may not read CP2.4 test material: {bad}')
    return p


def test_job_ids() -> set[str]:
    return set((ROOT / 'evals/splits/test_job_ids.txt').read_text().split())


def dev_job_ids() -> set[str]:
    return set((ROOT / 'evals/splits/dev_job_ids.txt').read_text().split())


def check_pairs(pairs) -> None:
    """Every optimization pair must be a development CV with a development job."""
    test, dev = test_job_ids(), dev_job_ids()
    for cv, job in pairs:
        if cv in FORBIDDEN_CVS or cv not in DEV_CVS:
            raise LeakageError(f'{cv} is a held-out CV; Phase A uses CV1-CV2 only')
        if job in test or job not in dev:
            raise LeakageError(f'{job} is not a development job')


def read_jsonl(path) -> list[dict]:
    return [json.loads(x) for x in dev_path(path).read_text().splitlines() if x.strip()]


# ---------------------------------------------------------------- fixed-input benchmark (gap_v2 gold)

def fixed_input_pairs(gold: Path = DEV_GOLD) -> dict[tuple[str, str], dict]:
    """gap_v2 gold A units as matcher input (requirement text only) and gold B labels as the answer.

    Units stay one unit each, as reviewed (alternatives written with '|' stay inside the text);
    a unit with min_years becomes a qualified unit. No gold evidence goes to the model.
    """
    units = read_jsonl(gold / 'extraction_gold_gap_v2.jsonl')
    labels = read_jsonl(gold / 'evidence_gold_gap_v2.jsonl')
    held = {(h['cv_id'], h['job_id'], h['unit_no']) for h in json.loads(dev_path(gold / 'held_gap_v2.json').read_text())
            if h.get('record') == 'B_Evidence'}
    by_job: dict[str, list[dict]] = {}
    for u in units:
        if u['review_status'] != 'approved' or u['split'] != 'development':
            raise ValueError('only approved development units can be used')
        if u['review_action'] == 'rejected':  # reviewer rejected the drafted unit; it has no label
            continue
        by_job.setdefault(u['job_id'], []).append(u)
    out: dict[tuple[str, str], dict] = {}
    for row in labels:
        key = (row['cv_id'], row['job_id'])
        if (row['cv_id'], row['job_id'], row['unit_no']) in held or row['review_status'] != 'approved':
            continue
        item = out.setdefault(key, {'labels': {}, 'sections': {}})
        item['labels'][row['unit_no']] = row['label']
        item['sections'][row['unit_no']] = row.get('cv_section')
    check_pairs(out)
    for (cv, job), item in out.items():
        rows = [u for u in by_job[job] if u['unit_no'] in item['labels']]
        item['extraction'] = JDExtraction.model_validate({
            'job_id': job, 'extractor_version': 'gold_gap_v2_fixed_input', 'jd_quality': 'ok',
            'units': [{'unit_id': u['unit_no'], 'text': u['unit_text'], 'importance': u['importance'],
                       'field': u['category'], 'min_years': u['min_years'],
                       'kind': 'qualified' if u['min_years'] is not None else 'simple',
                       'source_quotes': [u['source_quote']] if u.get('source_quote') else [],
                       'label_source': 'annotator'} for u in rows]})
        item['fields'] = {u['unit_no']: u['category'] for u in rows}
        item['importance'] = {u['unit_no']: u['importance'] for u in rows}
    return out


def split_fixed_input(pairs: dict, seed: int = SPLIT_SEED) -> dict[str, list[list[str]]]:
    """Split by job (a job never sits in both subsets), balancing unit counts per CV."""
    jobs = sorted({job for _, job in pairs})
    random.Random(seed).shuffle(jobs)
    subsets = {'optimization': [], 'confirmation': []}
    units = {name: Counter() for name in subsets}
    for job in jobs:
        cvs = [cv for cv, j in pairs if j == job]
        load = {name: sum(units[name][cv] for cv in cvs) for name in subsets}
        name = min(subsets, key=lambda n: (load[n], n))
        for cv in sorted(cvs):
            subsets[name].append([cv, job])
            units[name][cv] += len(pairs[(cv, job)]['labels'])
    return {name: sorted(v) for name, v in subsets.items()}


def reference_provenance(gold: Path = DEV_GOLD) -> dict:
    """Provenance of the development references, counted from the source metadata (never rewritten)."""
    def count(name):
        c = Counter()
        for r in read_jsonl(gold / name):
            ap = r.get('approval_provenance') or {}
            c[' | '.join(str(x) for x in (r.get('labeling_mode'), r.get('label_source'), r.get('review_status'),
                                           r.get('review_action'), ap.get('annotator'), ap.get('review_kind')))] += 1
        return dict(c)
    return {
        'fields': 'labeling_mode | label_source | review_status | review_action | annotator | review_kind',
        'fixed_input_answers (evidence_gold_gap_v2.jsonl)': count('evidence_gold_gap_v2.jsonl'),
        'fixed_input_units (extraction_gold_gap_v2.jsonl)': count('extraction_gold_gap_v2.jsonl'),
        'r3_anchor (evidence_gold.jsonl)': count('evidence_gold.jsonl'),
        'ranking_relevance (relevance_gold.jsonl)': count('relevance_gold.jsonl'),
        'statement': ('Development references are model-draft-assisted and human-reviewed (gap_v2: drafted with model '
                      'help, accepted by Dion, D-085). They are not independent human ground truth. If a draft came from '
                      'a model of the same family as the matcher, agreement can be inflated by correlated model '
                      'preferences; this risk is not measured. Phase A never edits these labels.'),
    }


# ---------------------------------------------------------------- confirmation seal

UNSEAL_FILE = QA_DIR / 'benchmark_v1/confirmation_unseal.json'


def confirmation_unsealed(path: Path = None, registry: Path = None) -> bool:
    """The confirmation subset opens only after exactly one finalist is recorded in the registry and an unseal record names it."""
    path = path or UNSEAL_FILE
    if not path.exists():
        return False
    rec = json.loads(path.read_text())
    finalists = [r['experiment_id'] for r in load_registry(registry or REGISTRY) if r['status'] == 'finalist']
    # Amendment 1: the finalist must also pass its repeat run on the optimization subset.
    return (len(finalists) == 1 and rec.get('finalist') == finalists[0]
            and rec.get('repeat') == f'{finalists[0]}-R2' and rec.get('repeat_passed') is True)


def ranking_pairs(rankings: dict[str, list[str]], buckets: dict[str, str | None], k: int = 10):
    """CV1-CV2 analyzed top K after the frozen seniority rule (same jobs the product analyzes)."""
    from jobfit.search.seniority import demote_senior
    out = {cv: demote_senior(rankings[cv], buckets)[:k] for cv in DEV_CVS}
    check_pairs([(cv, j) for cv, js in out.items() for j in js])
    return out


# ---------------------------------------------------------------- metrics

def unit_predictions(extraction: JDExtraction, assessments: list[dict]) -> dict[str, dict]:
    by_id = {a['unit_id']: UnitAssessment.model_validate(a) for a in assessments}
    out = {}
    for unit in extraction.units:
        label, status = effective_label(unit, by_id.get(unit.unit_id))
        out[unit.unit_id] = {'status': status.value,
                             'label': label.value if label is not None and status == CheckStatus.DONE else None}
    return out


def fixed_input_metrics(records: dict[tuple[str, str], dict], pairs: dict, subset: list) -> dict:
    """Unit-level matching quality on one subset. A missing, failed or unclear answer is wrong."""
    truth, pred, fields = {}, {}, {}
    failed_pairs, repairs, walls, errors, guard_changes = [], 0, [], Counter(), 0
    per_pair = {}
    for cv, job in subset:
        item = pairs[(cv, job)]
        for unit, label in item['labels'].items():
            truth[f'{cv}/{job}/{unit}'] = label
            fields[f'{cv}/{job}/{unit}'] = item['fields'][unit]
        rec = records.get((cv, job))
        if rec is None or rec['status'] != 'done':
            failed_pairs.append(f'{cv}/{job}')
            errors[(rec or {}).get('error_code') or 'not_run'] += 1
            continue
        repairs += max(0, int(rec.get('attempts') or 1) - 1)
        walls.append(rec['wall_ms'])
        guard_changes += sum(1 for f in rec.get('source_flags', []) if f.get('kind') == 'G1_G2')
        p = unit_predictions(item['extraction'], rec['assessments'])
        pred.update({f'{cv}/{job}/{u}': v for u, v in p.items()})
        agree = sum(p[u]['label'] == l for u, l in item['labels'].items())
        per_pair[f'{cv}/{job}'] = {'units': len(item['labels']), 'agree': agree}
    m = evidence_metrics(truth, pred, alignment_verified=True)
    over = under = unsupported = unassessed = 0
    unsupported_by_field = Counter()
    for key, gold in truth.items():
        got = (pred.get(key) or {}).get('label')
        if got is None:
            unassessed += 1
            continue
        if ORDER[got] > ORDER[gold]:
            over += 1
        elif ORDER[got] < ORDER[gold]:
            under += 1
        if gold == 'NO_MATCH' and got != 'NO_MATCH':
            unsupported += 1
            unsupported_by_field[fields[key]] += 1
    answered = [k for k in truth if (pred.get(k) or {}).get('label') is not None]
    agree_answered = sum(pred[k]['label'] == truth[k] for k in answered)
    classes = Counter(failure_class(c) for c, n in errors.items() for _ in range(n))
    return {
        'pairs': len(subset), 'units': len(truth), 'macro_f1': m['macro_f1'],
        'failure_classes': dict(classes), 'prompt_induced_failed_pairs': classes.get('prompt_induced', 0),
        'per_class_f1': {c: m['per_class'][c]['f1'] for c in m['classes']},
        'accuracy_all_units': sum((pred.get(k) or {}).get('label') == v for k, v in truth.items()) / len(truth),
        'accuracy_answered': agree_answered / len(answered) if answered else None,
        'confusion': m['confusion'], 'overclaim': over, 'underclaim': under,
        'unsupported_positive': unsupported, 'unsupported_positive_by_field': dict(unsupported_by_field),
        'fabricated_experience_proxy': unsupported_by_field.get('experience_duration', 0),
        'fabricated_skill_proxy': unsupported_by_field.get('skill_tool', 0) + unsupported_by_field.get('knowledge_area', 0),
        'fabricated_education_proxy': unsupported_by_field.get('education', 0),
        'unassessed_units': unassessed, 'failed_pairs': failed_pairs, 'error_codes': dict(errors),
        'repair_count': repairs, 'guardrail_changes': guard_changes,
        'latency_ms_p50': statistics.median(walls) if walls else None,
        'latency_ms_p95': sorted(walls)[max(0, round(.95 * len(walls)) - 1)] if walls else None,
        'per_pair': per_pair,
        'leave_one_pair_out_accuracy': {k: (sum(v['agree'] for kk, v in per_pair.items() if kk != k) /
                                            max(1, sum(v['units'] for kk, v in per_pair.items() if kk != k)))
                                        for k in per_pair},
    }


def quote_validity(records, cv_texts: dict[str, str]) -> dict:
    """Share of MATCH/PARTIAL items whose every quote is found word for word in the CV."""
    from jobfit.matching.quote_check import require_quotes
    total = bad = 0
    for (cv, _), rec in records.items():
        if rec.get('status') != 'done':
            continue
        for a in rec['assessments']:
            for item in (a.get('branches') or [a]):
                if item.get('label') in ('MATCH', 'PARTIAL'):
                    total += 1
                    try:
                        require_quotes(item['cv_quotes'], cv_texts[cv])
                    except Exception:
                        bad += 1
    return {'positive_items': total, 'invalid_quote_items': bad,
            'quote_validity': (total - bad) / total if total else None}


def run_to_run_agreement(a: dict, b: dict, pairs: dict, subset: list) -> dict:
    same = total = 0
    for cv, job in subset:
        ra, rb = a.get((cv, job)), b.get((cv, job))
        if not ra or not rb or ra['status'] != 'done' or rb['status'] != 'done':
            continue
        ext = pairs[(cv, job)]['extraction']
        pa, pb = unit_predictions(ext, ra['assessments']), unit_predictions(ext, rb['assessments'])
        for u in pa:
            total += 1
            same += pa[u]['label'] == pb[u]['label']
    return {'units': total, 'same': same, 'rate': same / total if total else None}


def label_transitions(a: dict, b: dict, pairs: dict, subset: list) -> dict:
    """Unit-level comparison of two runs on the same pairs: agreement, label transitions and where changes sit."""
    trans, by_field, field_total, by_pair, by_cv, imp, gold_side = (Counter() for _ in range(7))
    total = same = 0
    for cv, job in subset:
        ra, rb = a.get((cv, job)), b.get((cv, job))
        if not ra or not rb or ra['status'] != 'done' or rb['status'] != 'done':
            continue
        ext = pairs[(cv, job)]['extraction']
        pa, pb = unit_predictions(ext, ra['assessments']), unit_predictions(ext, rb['assessments'])
        for u in pa:
            la = pa[u]['label'] or f"UNASSESSED({pa[u]['status']})"
            lb = pb[u]['label'] or f"UNASSESSED({pb[u]['status']})"
            field = pairs[(cv, job)]['fields'][u]
            total += 1
            field_total[field] += 1
            if la == lb:
                same += 1
                continue
            trans[f'{la}->{lb}'] += 1
            by_field[field] += 1
            by_pair[f'{cv}/{job}'] += 1
            by_cv[cv] += 1
            imp[pairs[(cv, job)]['importance'][u]] += 1
            gold = pairs[(cv, job)]['labels'][u]
            gold_side['first_run_matches_gold' if la == gold else 'second_run_matches_gold' if lb == gold else 'neither_matches_gold'] += 1
    changed = total - same
    return {'units': total, 'same': same, 'changed': changed, 'agreement': same / total if total else None,
            'transitions': dict(trans.most_common()),
            'changed_by_field': {f: {'changed': by_field[f], 'units': field_total[f],
                                     'rate': by_field[f] / field_total[f]} for f in sorted(field_total)},
            'changed_by_pair': dict(by_pair.most_common()), 'changed_by_cv': dict(by_cv),
            'changed_by_importance': dict(imp), 'which_run_matches_gold': dict(gold_side)}


def ranking_quality(top: dict[str, list[str]], scores: dict, labels: dict, eligible, constraints=None) -> dict:
    """D-073 product order on the analyzed top K, D-052 metrics, macro over CV1-CV2 (both needed)."""
    from jobfit.eval.product_order import product_order_metrics
    per_cv = {}
    for cv in DEV_CVS:
        cons = {j: constraints[(cv, j)] for j in top[cv]} if constraints else None
        m = product_order_metrics(top[cv], {j: scores[(cv, j)] for j in top[cv]}, labels[cv],
                                  eligible_ids=eligible, constraints=cons)
        per_cv[cv] = {'p_at_5': m['p_at_5'], 'ndcg_at_10': m['ndcg_at_10'], 'order': m['order'],
                      'unscored_in_top10': m['unscored_in_final_top10'], 'unjudged': m['unjudged_final_top10']}
    macro = lambda f: (None if any(v[f] is None for v in per_cv.values())
                       else sum(v[f] for v in per_cv.values()) / len(per_cv))
    analyzed = sum(len(top[cv]) for cv in DEV_CVS)
    held = sum(len(v['unscored_in_top10']) for v in per_cv.values())
    return {'per_cv': per_cv, 'macro_p_at_5': macro('p_at_5'), 'macro_ndcg_at_10': macro('ndcg_at_10'),
            'hold_rate': held / analyzed, 'held_or_unscored': held, 'analyzed': analyzed}


# ---------------------------------------------------------------- registry

def load_registry(path: Path = REGISTRY) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline='') as fh:
        return list(csv.DictReader(fh))


def write_registry(rows: list[dict], path: Path = REGISTRY) -> None:
    ids = [r['experiment_id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('experiment_id must be unique')
    for r in rows:
        if r['status'] not in STATUSES:
            raise ValueError(f"unknown status {r['status']}")
        if set(r) - set(REGISTRY_COLUMNS):
            raise ValueError(f'unknown registry columns: {sorted(set(r) - set(REGISTRY_COLUMNS))}')
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    with tmp.open('w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=REGISTRY_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in REGISTRY_COLUMNS})
    tmp.replace(path)


def upsert(row: dict, *, new: bool, path: Path = REGISTRY) -> None:
    rows = load_registry(path)
    exists = any(r['experiment_id'] == row['experiment_id'] for r in rows)
    if new and exists:
        raise ValueError(f"{row['experiment_id']} already exists; experiment IDs are never reused")
    if not new and not exists:
        raise ValueError(f"{row['experiment_id']} is not registered")
    rows = [({**r, **row} if r['experiment_id'] == row['experiment_id'] else r) for r in rows]
    if new:
        rows.append(row)
    write_registry(rows, path)


def prompt_record(prompt_file: Path) -> dict:
    """Prompt path, sha256 and the sidecar metadata (which must carry the same sha256)."""
    p = dev_path(prompt_file)
    meta_path = p.with_suffix('.meta.json')
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    h = digest(p)
    if meta and meta.get('prompt_sha256') != h:
        raise ValueError(f'{p.name}: prompt changed after its metadata was written; make a new version')
    name = str(p.relative_to(ROOT)) if p.resolve().is_relative_to(ROOT.resolve()) else str(p)
    return {'prompt_file': name, 'prompt_sha256': h, **{k: v for k, v in meta.items() if k != 'prompt_sha256'}}


def write_once(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as fh:
        json.dump(value, fh, ensure_ascii=False, indent=1)
        fh.write('\n')


# ---------------------------------------------------------------- selection scorecard (D-089, amendment 1)

RULE_FILE = QA_DIR / 'selection_rule_v2.json'


def build_rule(base_runs: dict[str, dict], ranking_baseline: dict) -> dict:
    """Numbers fixed from the two baseline runs before any challenger result. base_runs: id -> metrics.json."""
    fi = {k: v['fixed_input_optimization'] for k, v in base_runs.items()}
    vals = lambda f: [x[f] for x in fi.values()]
    mean = lambda f: sum(vals(f)) / len(vals(f))
    loo = {}
    for pair in next(iter(fi.values()))['leave_one_pair_out_accuracy']:
        loo[pair] = sum(x['leave_one_pair_out_accuracy'][pair] for x in fi.values()) / len(fi)
    up_max = max(vals('unsupported_positive'))
    over_min = min(vals('overclaim'))
    return {
        'version': 'selection-rule-v2 (D-089 amendment 1)', 'baseline_runs': sorted(base_runs),
        'baseline': {'macro_f1_mean': mean('macro_f1'), 'accuracy_mean': mean('accuracy_all_units'),
                     'unsupported_positive_max': up_max, 'overclaim_min': over_min,
                     'underclaim_max': max(vals('underclaim')), 'unassessed_max': max(vals('unassessed_units')),
                     'prompt_induced_failed_pairs_max': max(x.get('prompt_induced_failed_pairs', len(x['failed_pairs'])) for x in fi.values()),
                     'leave_one_pair_out_accuracy_mean': loo,
                     'ranking_p_at_5': ranking_baseline['macro_p_at_5'], 'ranking_ndcg_at_10': ranking_baseline['macro_ndcg_at_10']},
        'hard_gates': {
            'quote_validity': 'must be 1.0 with 0 invalid quotes',
            'unsupported_positive_max': up_max,
            'prompt_induced_failed_pairs_max': 'baseline max (no worsening); transient failures excluded after recovery',
            'ranking_p_at_5_min': ranking_baseline['macro_p_at_5'],
            'ranking_ndcg_at_10_min': ranking_baseline['macro_ndcg_at_10'] - 0.02},
        'practical_improvement_reference_macro_f1': mean('macro_f1') + 0.02,
        'eligibility': {
            'path_A_quality': 'macro-F1 >= reference AND accuracy >= baseline mean AND, with any single pair left out, '
                              'accuracy >= the baseline mean on the same remaining pairs',
            'path_B_product_errors': 'unsupported positives <= 0.9 x baseline max AND overclaims <= 0.9 x baseline min AND '
                                     'macro-F1 >= baseline mean AND accuracy >= baseline mean AND the unsupported-positive '
                                     'reduction is spread over at least 3 pairs',
            'no_other_regression': 'underclaims <= baseline max + 5 AND unassessed units <= baseline max + 2'},
        'path_B_limits': {'unsupported_positive_max': int(0.9 * up_max), 'overclaim_max': int(0.9 * over_min)},
        'finalist_choice': ('exactly one provisional finalist among eligible challengers: lowest unsupported positives; '
                            'challengers within 2 of that lowest count stay; among them highest macro-F1, then highest '
                            'accuracy, then lowest experiment ID. None eligible: keep the baseline.'),
        'repeat': ('the finalist runs once more on the same optimization subset as <ID>-R2; the repeat must pass every hard '
                   'gate except ranking (not rerun) and be eligible on path A or B; only then the confirmation subset opens'),
        'error_categories': 'over/under/unassessed by field are reported for every challenger and read with the decision',
    }


def per_pair_unsupported(failures: dict) -> Counter:
    c = Counter()
    for e in failures['unit_errors']:
        if e['gold'] == 'NO_MATCH' and e['pred'] in ('MATCH', 'PARTIAL'):
            c['/'.join(e['unit'].split('/')[:2])] += 1
    return c


def scorecard(metrics: dict, rule: dict, *, failures: dict, baseline_failures: list[dict], with_ranking: bool = True) -> dict:
    fi, b = metrics['fixed_input_optimization'], rule['baseline']
    g = metrics['grounding']
    pif = fi.get('prompt_induced_failed_pairs', len(fi['failed_pairs']))
    gates = {
        'quote_validity_1': g['quote_validity'] == 1.0 and g['invalid_quote_items'] == 0,
        'unsupported_not_worse': fi['unsupported_positive'] <= rule['hard_gates']['unsupported_positive_max'],
        'prompt_failures_not_worse': pif <= b['prompt_induced_failed_pairs_max'],
        'no_unrecovered_transient': not fi.get('failure_classes', {}).get('transient_operational')
                                    and not fi.get('failure_classes', {}).get('unclassified'),
    }
    if with_ranking:
        r = metrics.get('ranking') or {}
        gates['ranking_p5_not_lower'] = r.get('macro_p_at_5') is not None and r['macro_p_at_5'] >= rule['hard_gates']['ranking_p_at_5_min'] - 1e-9
        gates['ranking_ndcg_within_0_02'] = r.get('macro_ndcg_at_10') is not None and r['macro_ndcg_at_10'] >= rule['hard_gates']['ranking_ndcg_at_10_min'] - 1e-9
    loo = fi['leave_one_pair_out_accuracy']
    base_up = Counter()
    for bf in baseline_failures:
        base_up.update(per_pair_unsupported(bf))
    base_up = {k: v / max(1, len(baseline_failures)) for k, v in base_up.items()}
    mine = per_pair_unsupported(failures)
    pairs_reduced = sum(1 for k, v in base_up.items() if mine.get(k, 0) < v)
    no_other = fi['underclaim'] <= b['underclaim_max'] + 5 and fi['unassessed_units'] <= b['unassessed_max'] + 2
    path_a = (fi['macro_f1'] >= rule['practical_improvement_reference_macro_f1'] - 1e-12
              and fi['accuracy_all_units'] >= b['accuracy_mean']
              and all(loo[k] >= b['leave_one_pair_out_accuracy_mean'][k] for k in loo))
    path_b = (fi['unsupported_positive'] <= rule['path_B_limits']['unsupported_positive_max']
              and fi['overclaim'] <= rule['path_B_limits']['overclaim_max']
              and fi['macro_f1'] >= b['macro_f1_mean'] and fi['accuracy_all_units'] >= b['accuracy_mean']
              and pairs_reduced >= 3)
    return {'gates': gates, 'gates_passed': all(gates.values()), 'path_A': path_a, 'path_B': path_b,
            'no_other_regression': no_other, 'pairs_with_fewer_unsupported': pairs_reduced,
            'eligible': all(gates.values()) and no_other and (path_a or path_b),
            'values': {'macro_f1': fi['macro_f1'], 'accuracy': fi['accuracy_all_units'],
                       'unsupported_positive': fi['unsupported_positive'], 'overclaim': fi['overclaim'],
                       'underclaim': fi['underclaim'], 'unassessed': fi['unassessed_units'], 'prompt_failed_pairs': pif}}


def pick_finalist(cards: dict[str, dict]) -> str | None:
    eligible = {k: c for k, c in cards.items() if c['eligible']}
    if not eligible:
        return None
    low = min(c['values']['unsupported_positive'] for c in eligible.values())
    near = {k: c for k, c in eligible.items() if c['values']['unsupported_positive'] <= low + 2}
    return sorted(near, key=lambda k: (-near[k]['values']['macro_f1'], -near[k]['values']['accuracy'], k))[0]
