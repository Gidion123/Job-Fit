"""Production retrieval offline checks: tokenizer artifacts fail closed; cards carry filter metadata."""
from dataclasses import replace

import pytest

from jobfit.api.presenter import retrieval_card
from jobfit.search import production
from jobfit.search.embeddings import load_specs


def test_a_missing_or_changed_query_tokenizer_fails_closed():
    spec = next(s for s in load_specs() if 'qwen' in s.model)
    with pytest.raises(production.ProductionRetrievalUnavailable) as exc:
        production.load_query_tokenizer(replace(spec, tokenizer_revision='0' * 64))
    assert exc.value.code == 'production_retrieval_unavailable'


def test_retrieval_cards_carry_the_metadata_for_local_filters_and_no_score():
    meta = production.card_metadata({'title': 'ML Engineer', 'company': 'Acme', 'role_family': 'genai_llm',
                                     'country_code': 'ID', 'city_normalized': 'Jakarta', 'work_mode': 'hybrid',
                                     'posted_at': '2026-10-01', 'apply_url': 'https://x'})
    card = retrieval_card('J1', 1, meta)
    assert card['stage'] == 'retrieval' and card['analyzed'] is False and card['match_score'] is None
    for key in ('role_family', 'country_code', 'city', 'work_mode', 'posted_at'):
        assert card[key] == meta[key]
    assert card['location'] == 'Jakarta, ID'
