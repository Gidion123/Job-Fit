"""Offline evaluation of the CP3 evidence-matching cost/quality/latency comparison. No provider call.

Reads only saved artifacts: the run folder written by run_cp3_llm_cost_quality_comparison.py
(plan.json, pairs/*.json, requests.jsonl, summary.json) and the project usage ledger.

Same accounting as D-079: all 73 reference units; a failed, unrun or unassessed unit stays in
the denominator as a false negative; G1/G2 with the SQL example adapter and the D-067 reference
are applied here (headline); the unguarded result is a diagnostic. Actual cost is the cost the
provider reported (ledger and per-request usage); estimates are reported separately.

The comparison against Sol is descriptive. The historical D-029/D-066 reference
(challenger Macro-F1 >= Sol - 0.03) is printed, never applied: model selection is the owner's.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from math import ceil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.eval.matching_evaluation import reference_rows
from jobfit.eval.metrics import evidence_metrics
from jobfit.eval.qa_phase_a import quote_validity
from scripts.evaluate_cp23_model_sweep import SQL_KEY, predictions
from scripts.evaluate_cp23_uncertainty import error_profile, paired_bootstrap
from scripts.run_cp3_llm_cost_quality_comparison import CONFIG, benchmark, load_config

SCHEMA_VERSION = 'cp3-llm-cost-quality-comparison-v1'
STRUCTURED_ERRORS = {'ValidationError', 'JSONDecodeError'}
LATENCY_NOTE = ('Sequential single-worker latency on one machine and one network path; '
                'not a load or concurrency benchmark.')


def percentile(values, q):
    """Nearest-rank percentile; None for no data."""
    data = sorted(v for v in values if v is not None)
    if not data:
        return None
    return data[max(0, ceil(q * len(data)) - 1)]


def ratio(a, b):
    return None if a is None or b in (None, 0) else a / b


def rounded(value, digits=9):
    return None if value is None else round(value, digits)


def load_run(run_dir: Path) -> tuple[dict, dict, list[dict], dict]:
    plan = json.loads((run_dir / 'plan.json').read_text())
    pairs = {}
    for path in sorted((run_dir / 'pairs').glob('*.json')):
        row = json.loads(path.read_text())
        pairs[(row['model'], row['cv_id'], row['job_id'])] = row
    requests_path = run_dir / 'requests.jsonl'
    requests = [json.loads(x) for x in requests_path.read_text().splitlines() if x.strip()] \
        if requests_path.exists() else []
    summary = json.loads((run_dir / 'summary.json').read_text()) if (run_dir / 'summary.json').exists() else {}
    return plan, pairs, requests, summary


def load_ledger(run_id: str, path: Path | None):
    from jobfit.config import get_settings
    from jobfit.llm.ledger import UsageLedger
    ledger = UsageLedger(path or get_settings().usage_ledger)
    return [r for r in ledger.records() if r.run_id == run_id]


def request_process(rows: list[dict], pair_failed: bool) -> dict:
    """Classify the attempts of one pair. A returned output that the validator rejected is followed
    by another attempt, or is the last attempt of a failed pair."""
    out = Counter()
    for i, r in enumerate(rows):
        out['requests'] += 1
        out[r['kind']] += 1
        if r['outcome'] == 'returned':
            if i + 1 < len(rows) or pair_failed:
                out['validation_failures'] += 1
        else:
            out['failed_requests'] += 1
            if r['outcome'] in STRUCTURED_ERRORS:
                out['structured_output_failures'] += 1
            elif r['outcome'] == 'TruncatedStructuredResponse':
                out['truncations'] += 1
            elif r.get('transport_error') or not r.get('sent'):
                out['transport_or_admission_failures'] += 1
    return out


def model_report(key, item, pairs_plan, loaded, truth, run_pairs, requests, ledger, n_units):
    plain, guarded, walls, statuses, done = {}, {}, [], {}, {}
    for s in pairs_plan:
        row = run_pairs.get((key, s['cv_id'], s['job_id']))
        name = f"{s['cv_id']}/{s['job_id']}"
        if row is None:
            statuses[name] = 'missing'
            continue
        statuses[name] = row['status'] if row['status'] == 'done' else f"{row['status']}:{row['error_code']}"
        if row.get('wall_ms') is not None:
            walls.append(row['wall_ms'])
        if row['status'] != 'done':
            continue
        cv, extraction = loaded[(s['cv_id'], s['job_id'])]
        p, g = predictions(s, cv, extraction, row['assessments'])
        plain.update(p)
        guarded.update(g)
        done[(s['cv_id'], s['job_id'])] = row
    metrics = evidence_metrics(truth, guarded, alignment_verified=True)
    diagnostic = evidence_metrics(truth, plain, alignment_verified=True)
    errors = error_profile(truth, guarded)
    cv_texts = {cv: c.profile.raw_text for (cv, _), (c, _) in loaded.items()}
    quotes = quote_validity(done, cv_texts)
    assessed = sum((guarded.get(k) or {}).get('label') is not None for k in truth)

    mine = [r for r in requests if r['model'] == key]
    process = Counter()
    for s in pairs_plan:
        rows = sorted((r for r in mine if (r['cv_id'], r['job_id']) == (s['cv_id'], s['job_id'])),
                      key=lambda r: r['attempt'])
        row = run_pairs.get((key, s['cv_id'], s['job_id']))
        process.update(request_process(rows, pair_failed=row is not None and row['status'] != 'done'))
    latencies = [r['latency_ms'] for r in mine if r.get('sent') and r.get('latency_ms') is not None]

    calls = [r for r in ledger if r.model == item['model_id']]
    actual = sum(r.cost_usd for r in calls if r.cost_source == 'reported')
    estimated = sum(r.cost_usd for r in calls if r.cost_source != 'reported')
    reported_by_requests = sum(r['cost_usd_reported'] or 0.0 for r in mine)
    tokens = {name: sum(r.get(name) or 0 for r in mine)
              for name in ('input_tokens', 'output_tokens', 'reasoning_tokens', 'total_tokens')}
    valid = len(done)
    return {
        'model_id': item['model_id'], 'role': item.get('role'), 'pair_status': statuses,
        'process': {'valid_pairs': valid, 'pairs': len(pairs_plan), 'assessed_units': assessed, 'units': n_units,
                    'unassessed_units': n_units - assessed,
                    'requests': process['requests'], 'main_requests': process['main'],
                    'repair_attempts': process['validation_repair'],
                    'continuation_attempts': process['length_continuation'],
                    'structured_output_failures': process['structured_output_failures'],
                    'validation_failures': process['validation_failures'],
                    'truncations': process['truncations'], 'failed_requests': process['failed_requests'],
                    'transport_or_admission_failures': process['transport_or_admission_failures'],
                    'model_fallbacks': sum(r.get('model_id_requested') not in (None, item['model_id']) for r in mine),
                    'providers': sorted({str(r['provider']) for r in mine if r.get('provider')})},
        'quality': {'macro_f1': metrics['macro_f1'], 'macro_f1_unguarded_diagnostic': diagnostic['macro_f1'],
                    'confusion': metrics['confusion'],
                    'per_class': {c: {k: v[k] for k in ('precision', 'recall', 'f1', 'support')}
                                  for c, v in metrics['per_class'].items()},
                    'overclaims': errors['claims_stronger_than_gold'],
                    'underclaims': errors['claims_weaker_than_gold'],
                    'match_overclaims': errors['match_overclaim'],
                    'positive_on_gold_no_match': errors['positive_claim_on_gold_no_match'],
                    'quote_validity': quotes['quote_validity'], 'positive_items': quotes['positive_items'],
                    'invalid_quotes': quotes['invalid_quote_items'],
                    'unsupported_positives': errors['positive_claim_on_gold_no_match'] + quotes['invalid_quote_items'],
                    'unassessed_units': errors['not_assessed']},
        'cost': {'actual_usd': rounded(actual), 'estimated_or_uncertain_usd': rounded(estimated),
                 'ledger_requests': len(calls), 'reported_by_requests_usd': rounded(reported_by_requests),
                 'reconciled_with_ledger': abs(reported_by_requests - actual) < 1e-9,
                 'tokens': tokens,
                 'per_request_usd': rounded(ratio(actual, len(calls))),
                 'per_valid_pair_usd': rounded(ratio(actual, valid)),
                 'per_reference_unit_usd': rounded(ratio(actual, n_units)),
                 'per_assessed_unit_usd': rounded(ratio(actual, assessed))},
        'latency': {'attempt_ms_p50': percentile(latencies, 0.5), 'attempt_ms_p95': percentile(latencies, 0.95),
                    'attempts_measured': len(latencies), 'pair_wall_ms': walls,
                    'pair_wall_ms_p50': percentile(walls, 0.5), 'pair_wall_ms_p95': percentile(walls, 0.95),
                    'model_wall_ms': sum(walls)},
    }, guarded


def compare(models: dict, preds: dict, truth: dict, baseline: str, reporting: dict) -> dict:
    base = models[baseline]
    rng = random.Random(reporting['bootstrap_seed'])
    out = {}
    for key, m in models.items():
        if key == baseline:
            continue
        q, bq = m['quality'], base['quality']
        cost_ratio = ratio(m['cost']['per_valid_pair_usd'], base['cost']['per_valid_pair_usd'])
        delta = None if q['macro_f1'] is None or bq['macro_f1'] is None else q['macro_f1'] - bq['macro_f1']
        boot = paired_bootstrap(truth, preds[key], preds[baseline], rng)
        out[key] = {
            'delta_macro_f1': delta,
            'delta_macro_f1_bootstrap': {k: boot[k] for k in ('unit_bootstrap_95', 'pair_bootstrap_95')},
            'cost_ratio_per_valid_pair': cost_ratio,
            'latency_ratio_attempt_p50': ratio(m['latency']['attempt_ms_p50'], base['latency']['attempt_ms_p50']),
            'latency_ratio_attempt_p95': ratio(m['latency']['attempt_ms_p95'], base['latency']['attempt_ms_p95']),
            'delta_overclaims': q['overclaims'] - bq['overclaims'],
            'historical_reference': {
                'rule': f"challenger_macro_f1 >= sol_macro_f1 - {reporting['historical_reference_margin']}",
                'met': None if delta is None else delta >= -reporting['historical_reference_margin'] - 1e-12,
                'applied': False, 'note': 'D-029 rule 3 / D-066, descriptive only; no automatic promotion'},
            'flags': {
                'all_pairs_valid': m['process']['valid_pairs'] == m['process']['pairs'],
                'quote_validity_100': q['quote_validity'] == 1.0,
                'unsupported_positives_not_increased': q['unsupported_positives'] <= bq['unsupported_positives'],
                'cost_materially_lower': None if cost_ratio is None
                else cost_ratio <= reporting['materially_lower_cost_ratio']},
            'decision': 'owner'}
    return out


def build(run_dir: Path, config: dict | None = None, ledger_records=None, ledger_path: Path | None = None) -> dict:
    config = config or load_config(CONFIG)
    plan, run_pairs, requests, summary = load_run(run_dir)
    if plan['run_id'] != config['run_id']:
        raise ValueError('Run folder does not belong to this experiment configuration')
    pairs_plan, loaded = benchmark(config)              # dev-only identity and hash checks again
    gold = ROOT / config['benchmark']['gold_bundle']
    truth = {}
    for s in pairs_plan:
        cv, extraction = loaded[(s['cv_id'], s['job_id'])]
        for unit, label in reference_rows(gold, s, cv, extraction).items():
            truth[f"{s['cv_id']}/{s['job_id']}/{unit}"] = label
    truth[SQL_KEY] = 'MATCH'                            # D-067 reference
    ledger = ledger_records if ledger_records is not None else load_ledger(plan['run_id'], ledger_path)
    models, preds = {}, {}
    for key, item in plan['models'].items():
        models[key], preds[key] = model_report(key, item, pairs_plan, loaded, truth, run_pairs, requests, ledger,
                                               len(truth))
    prompts = sorted({r['prompt_sha256'] for r in requests})
    inputs_by_pair = {}
    for row in run_pairs.values():
        inputs_by_pair.setdefault(f"{row['cv_id']}/{row['job_id']}", set()).add(row['input_sha256'])
    return {
        'schema_version': SCHEMA_VERSION, 'run_id': plan['run_id'], 'split': 'development', 'api_calls': 0,
        'baseline': config['baseline'], 'units': len(truth), 'classes': dict(sorted(Counter(truth.values()).items())),
        'reference': 'D-067; all 73 units; failed/unassessed units count as false negatives; G1/G2 in evaluation',
        'integrity': {'system_prompt_sha256': prompts, 'same_prompt_for_all_requests': len(prompts) <= 1,
                      'same_inputs_for_all_models': all(len(v) == 1 for v in inputs_by_pair.values()),
                      'reasoning_param_sent': any(r.get('reasoning_param_sent') for r in requests)},
        'models': models,
        'versus_baseline': compare(models, preds, truth, config['baseline'], config['reporting']),
        'estimated_cost_preflight': {'conservative_max_usd': plan['conservative_max_cost'],
                                     'estimate_usd': plan.get('estimated_cost')},
        'run': {'total_wall_ms': summary.get('total_wall_ms'), 'stopped': summary.get('models')},
        'latency_note': LATENCY_NOTE,
        'selection': 'Owner decision. This report does not promote or change the production model.',
        'limits': [('Four CV/JD pairs (two synthetic development CVs) and 73 units: a few points of Macro-F1 '
                    'are within noise; see the bootstrap intervals.'),
                   'One run per model; outputs are not deterministic across runs.',
                   'Prices and routes change; costs are what the provider reported for this run.',
                   LATENCY_NOTE]}


def fmt(x, spec):
    return '-' if x is None else format(x, spec)


def markdown(report: dict) -> str:
    lines = [f"# CP3 LLM cost/quality comparison: {report['run_id']}", '',
             'Development data only. Owner decision; no automatic promotion.', '',
             '| Model | Valid pairs | Macro-F1 | Overclaims | Quote validity | Cost (US$) | p50 (s) | p95 (s) |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for key, m in report['models'].items():
        lat = m['latency']
        lines.append(f"| {key} | {m['process']['valid_pairs']}/{m['process']['pairs']} | "
                     f"{fmt(m['quality']['macro_f1'], '.3f')} | {m['quality']['overclaims']} | "
                     f"{fmt(m['quality']['quote_validity'], '.3f')} | {fmt(m['cost']['actual_usd'], '.4f')} | "
                     f"{fmt(lat['attempt_ms_p50'] and lat['attempt_ms_p50'] / 1000, '.1f')} | "
                     f"{fmt(lat['attempt_ms_p95'] and lat['attempt_ms_p95'] / 1000, '.1f')} |")
    lines += ['', f"Versus {report['baseline']}:", '',
              ('| Challenger | ΔMacro-F1 | Cost ratio | Latency ratio (p50) | ΔOverclaims | ≥ Sol − 0.03 (reference only) | '
               'All pairs valid | Quotes 100% | Unsupported positives not increased | Cost materially lower |'),
              '| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |']
    for key, c in report['versus_baseline'].items():
        f = c['flags']
        lines.append(f"| {key} | {fmt(c['delta_macro_f1'], '+.3f')} | {fmt(c['cost_ratio_per_valid_pair'], '.3f')} | "
                     f"{fmt(c['latency_ratio_attempt_p50'], '.2f')} | {c['delta_overclaims']:+d} | "
                     f"{c['historical_reference']['met']} | {f['all_pairs_valid']} | {f['quote_validity_100']} | "
                     f"{f['unsupported_positives_not_increased']} | {f['cost_materially_lower']} |")
    lines += ['', report['latency_note'], '', report['selection'], '']
    return '\n'.join(lines)


def write_report(run_dir: Path, report: dict) -> None:
    for name, text in (('comparison.json', json.dumps(report, indent=1, sort_keys=True) + '\n'),
                       ('comparison.md', markdown(report))):
        path = run_dir / name
        if path.exists() and path.read_text() != text:
            raise SystemExit(f'{path.name} exists with different content; keep it and use a new folder')
        path.write_text(text)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config', type=Path, default=CONFIG)
    parser.add_argument('--run-dir', type=Path, help='defaults to <output_dir>/<run_id> from the config')
    parser.add_argument('--ledger', type=Path, help='defaults to the project usage ledger')
    parser.add_argument('--write', action='store_true', help='write comparison.json and comparison.md')
    args = parser.parse_args(argv)
    config = load_config(args.config)
    run_dir = args.run_dir or ROOT / config['output_dir'] / config['run_id']
    if not (run_dir / 'plan.json').exists():
        raise SystemExit(f'No executed run at {run_dir}; the comparison has not been run.')
    report = build(run_dir, config, ledger_path=args.ledger)
    print(markdown(report))
    if args.write:
        write_report(run_dir, report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
