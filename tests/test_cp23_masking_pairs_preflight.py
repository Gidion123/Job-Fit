"""Paid masking comparison cannot inherit a changed quote reference."""
import json

import pytest

from scripts import run_cp23_masking_pairs as paired


def test_four_fixed_pairs_have_unchanged_source_quotes():
    assert paired.fixed_pair_quote_preflight() == 'cp23-masking-quote-compatibility-v1'


def test_stale_quote_receipt_blocks_paired_run(monkeypatch, tmp_path):
    altered=json.loads(paired.QUOTE_RECEIPT.read_text())
    altered['results']['CV1']['source_sha256']='stale'
    path=tmp_path/'receipt.json';path.write_text(json.dumps(altered))
    monkeypatch.setattr(paired,'QUOTE_RECEIPT',path)
    with pytest.raises(ValueError,match='stale'):
        paired.fixed_pair_quote_preflight()
