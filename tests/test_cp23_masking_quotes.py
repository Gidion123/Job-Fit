"""Synthetic development gold must remain traceable after local masking."""
import json

from scripts.check_cp23_masking_quotes import check


def test_saved_evidence_quotes_have_exact_masked_source_mapping():
    receipt = check()
    assert receipt['all_changed_quotes_mapped_exactly'] is True
    assert receipt['semantic_equivalence_approved'] is False
    assert receipt['api_calls'] == 0
    assert set(receipt['results']) == {'CV1', 'CV2'}
    assert sum(x['changed_quote_rows'] for x in receipt['results'].values()) == 13
    assert sum(x['changed_unique_source_quotes'] for x in receipt['results'].values()) == 2
    serialized = json.dumps(receipt).lower()
    assert 'rina.putri@' not in serialized and 'bima.sitorus@' not in serialized
