"""The result page keeps filter, constraint and failure states separate."""
from datetime import date

import pytest

from jobfit.recommend.pipeline import assemble_recommendations
from jobfit.schemas.analysis import JobAnalysis, ScoreResult, ConstraintResult
from jobfit.search.filters import JobFilters, filter_jobs


def job(identity, *, country='indonesia', country_code=None):
    return {'final_cluster_id': identity, 'role_group': 'target',
            'analysis_geo': country, 'country_code': country_code, 'role_family': 'data_science'}


def analysis(identity, rank, score, *, conflict=False, held=False):
    return JobAnalysis(
        job_id=identity, stage1_rank=rank,
        score=ScoreResult(status='on_hold' if held else 'final', score_pct=None if held else score),
        constraints=[ConstraintResult(kind='experience', state='explicit_conflict' if conflict else 'unknown')],
    )


def test_filter_and_constraint_groups_do_not_hide_held_jobs_or_raise_unknown():
    filtered = filter_jobs(
        [job('low'), job('unknown', country='remote_unverified'), job('conflict'),
         job('high'), job('held'), job('not_selected'), job('out', country='foreign', country_code='US')],
        JobFilters(country_code='ID'), analysis_date=date(2026, 9, 30),
    )
    ranked = ['low', 'unknown', 'conflict', 'high', 'held']
    analyzed = {
        'low': analysis('low', 1, 40), 'unknown': analysis('unknown', 2, 99),
        'conflict': analysis('conflict', 3, 98, conflict=True),
        'high': analysis('high', 4, 90), 'held': analysis('held', 5, None, held=True),
    }
    view = assemble_recommendations(filtered, ranked, analyzed)
    assert view.first_group_title == 'Matches your filters'
    assert view.matching_filters.job_ids() == {
        'no_conflict': ['high', 'low'], 'has_conflict': ['conflict'], 'not_fully_analyzed': ['held'],
    }
    assert view.unknown_filters.job_ids()['no_conflict'] == ['unknown']
    assert view.not_analyzed_count == 1 and view.eligible_count == 6
    assert 'out' not in view.analyzed_ids


def test_missing_failed_analysis_and_out_of_scope_candidates_are_rejected():
    filtered = filter_jobs([job('A'), job('B', country='remote_unverified')],
                           JobFilters(country_code='ID', include_unknown=False),
                           analysis_date=date(2026, 9, 30))
    with pytest.raises(ValueError, match='explicit held result'):
        assemble_recommendations(filtered, ['A'], {})
    with pytest.raises(ValueError, match='eligible'):
        assemble_recommendations(filtered, ['A', 'B'], {'A': analysis('A', 1, 50), 'B': analysis('B', 2, 80)})
    with pytest.raises(ValueError, match='rank'):
        assemble_recommendations(filtered, ['A'], {'A': analysis('A', 2, 50)})


def test_no_optional_filters_use_target_role_title_and_stable_ties():
    filtered = filter_jobs([job('A'), job('B')], JobFilters(), analysis_date=date(2026, 9, 30))
    view = assemble_recommendations(filtered, ['A', 'B'],
                                    {'A': analysis('A', 1, 60), 'B': analysis('B', 2, 60)})
    assert view.first_group_title == 'Target-role jobs'
    assert view.matching_filters.job_ids()['no_conflict'] == ['A', 'B']
