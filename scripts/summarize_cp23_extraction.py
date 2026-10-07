"""Read-only common-case inventory, ledger cost and extraction timings.

Requires new output paths; never calls a model, reads test contents, or edits gold.
"""
import argparse
import csv
from decimal import Decimal
import json
from pathlib import Path
import statistics
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from jobfit.config import REPO_ROOT
from jobfit.eval.extraction_inventory import inventory, V4, V5, V6, V7


def summarize_run(root):
    result = inventory(root)
    for summary in result['summary']:
        rows = [r for r in result['rows'] if r['model'] == summary['model'] and r['process_status'] != 'not_attempted']
        latency = [r['latency_ms'] / 1000 for r in rows]
        counts = [r['unit_count'] for r in rows if r['process_status'] == 'done']
        summary['stage_latency_seconds'] = dict(median=statistics.median(latency), min=min(latency), max=max(latency),
            scope='extraction wall time incl validation and allowed repair; excludes earlier key check, source QA and other pipeline stages') if latency else None
        summary['unit_count_range_valid_finals'] = [min(counts), max(counts)] if counts else None
    ledger = [json.loads(line) for line in (root / 'reports/usage/usage_ledger.jsonl').read_text().splitlines()]
    def cost(records):
        return str(sum((Decimal(str(r['cost_usd'])) for r in records if not r['cached']), Decimal(0)))
    result['cost_accounting'] = dict(total_ledger_usd=cost(ledger),
        historical_uncertain_usd=cost([r for r in ledger if r['cost_source'] == 'uncertain_upper_bound']),
        v5_v6_v7_cumulative_usd=cost([r for r in ledger if r['run_id'] in {V5, V6, V7}]),
        v6_v7_this_takeover_usd=cost([r for r in ledger if r['run_id'] in {V6, V7}]),
        original_v14_comparison_including_v4_usd=cost([r for r in ledger if r['run_id'] in {V4, V5, V6, V7}]),
        aggregate_ceiling_usd='3.16', project_hard_stop_usd='8.50')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--csv', type=Path, required=True)
    args = parser.parse_args()
    for path in (args.output, args.csv):
        if path.resolve().parent != (REPO_ROOT / 'evals/results').resolve():
            raise ValueError('Output must be a direct evals/results artifact')
        if path.exists():
            raise ValueError('Choose fresh artifact paths; historical results are immutable')
    result = summarize_run(REPO_ROOT)
    with args.output.open('x') as file:
        json.dump(result, file, indent=2); file.write('\n')
    fields = ['model', 'job_id', 'process_status', 'attempts', 'unit_count', 'source_qa_status', 'error_code', 'latency_ms', 'result_file']
    with args.csv.open('x', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields); writer.writeheader()
        writer.writerows({key: row.get(key) for key in fields} for row in result['rows'])
    print(json.dumps(dict(status=result['status'], cases=len(result['rows']), model_winner=None)))


if __name__ == '__main__':
    main()
