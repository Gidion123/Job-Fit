from jobfit.search.seniority import demote_senior
import pytest


def test_demotes_three_plus_years_and_keeps_order():
    ranking = ['A', 'B', 'C', 'D', 'E', 'F']
    buckets = {'A': '5y+', 'B': 'entry', 'C': '3-4y', 'D': 'not_stated', 'E': '1-2y', 'F': None}
    assert demote_senior(ranking, buckets) == ['B', 'D', 'E', 'F', 'A', 'C']


def test_not_stated_and_unknown_are_never_demoted():
    assert demote_senior(['A', 'B'], {'A': 'not_stated'}) == ['A', 'B']


def test_rule_can_be_switched_off():
    assert demote_senior(['A', 'B'], {'A': '5y+'}, enabled=False) == ['A', 'B']


def test_duplicate_ids_rejected():
    with pytest.raises(ValueError):
        demote_senior(['A', 'A'], {})
