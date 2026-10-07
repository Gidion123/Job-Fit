"""Validate the approved D-052 metric receipt separately from data readiness."""
import hashlib
from pathlib import Path
from jobfit.config import REPO_ROOT

CONTRACT_VERSION = 'evaluation-contract-v1.1'
POLICY = {
    'relevant_grades': [2, 3],
    'ndcg_gain': 'exponential',
    'ranking_positions': 'original',
    'p_at_5': 'five_present_and_judged_denominator_5',
    'ndcg_at_10': 'ten_present_and_judged_else_unavailable',
    'short_ranking': 'unavailable_pending_convention',
    'recall': 'original_top_k_judged_eligible_pool',
    'failed_evidence': 'all_reference_not_assessed_false_negative',
    'macro_f1': 'all_three_aggregate_gold_classes_required',
    'extraction_split_merge': 'D-054_strict_independently_assessable_1_to_many_or_many_to_1;many_to_many_unavailable',
}


def validate_metric_contract(receipt, root=REPO_ROOT):
    if (receipt.get('version') != CONTRACT_VERSION or receipt.get('decision_id') != 'D-052+D-054'
            or receipt.get('review_status') != 'approved_conventions'
            or receipt.get('policy') != POLICY):
        raise ValueError('Expected approved D-052 metric contract; historical conventions are not primary')
    source = Path(root) / 'docs/evaluation.md'
    if receipt.get('source_document') != 'docs/evaluation.md' or receipt.get('source_sha256') != hashlib.sha256(source.read_bytes()).hexdigest():
        raise ValueError('Metric contract source changed or receipt is stale')
    return True


def comparison_gates_ready(readiness):
    gates = readiness.get('gates') or {}
    required = {'contract', 'references', 'alignment', 'coverage', 'implementation'}
    receipts = readiness.get('receipts') or {}
    required_receipts = {'reference_sha256', 'alignment_sha256', 'coverage_sha256'}
    return (readiness.get('status') == 'ready'
            and required <= gates.keys() and all(gates[k] is True for k in required)
            and required_receipts <= receipts.keys()
            and all(isinstance(receipts[k], str) and len(receipts[k]) == 64
                    and all(c in '0123456789abcdef' for c in receipts[k])
                    for k in required_receipts)
            and readiness.get('held_reference_ids') == [])
