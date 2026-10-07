"""D-009/D-010 optional-filter behavior on synthetic metadata only."""
from datetime import date, datetime

import pytest

from jobfit.search.filters import FilterState, JobFilters, filter_jobs, filter_status


TODAY = date(2026, 9, 30)


def job(identity, **changes):
    record = {
        'final_cluster_id': identity, 'role_group': 'target',
        'role_family': 'data_science', 'analysis_geo': 'indonesia',
        'city_normalized': 'Jakarta', 'experience_bucket': '1-2y',
        'work_mode': 'hybrid', 'posted_at': '2026-09-28',
    }
    record.update(changes)
    return record


def test_empty_filters_keep_target_jobs_without_claiming_filter_match():
    result = filter_jobs([job('A'), job('B', role_family='genai_llm')], JobFilters(), analysis_date=TODAY)
    assert result.active_filters == ()
    assert result.eligible_ids == ('A', 'B')
    assert not result.unknown and not result.conflicts


def test_unknown_is_separate_and_can_be_hidden_without_silent_relaxation():
    jobs = [job('match'), job('unknown', experience_bucket=None), job('conflict', experience_bucket='5y+')]
    requested = JobFilters(experience_bucket='1-2y')
    result = filter_jobs(jobs, requested, analysis_date=TODAY)
    assert result.eligible_ids == ('match', 'unknown')
    assert [x.job_id for x in result.unknown] == ['unknown']
    assert [x.job_id for x in result.conflicts] == ['conflict']
    hidden = filter_jobs(jobs, JobFilters(experience_bucket='1-2y', include_unknown=False), analysis_date=TODAY)
    assert hidden.eligible_ids == ('match',)
    empty = filter_jobs([jobs[-1]], requested, analysis_date=TODAY)
    assert empty.eligible_ids == () and 'did not widen' in empty.empty_message


def test_conflict_wins_over_unknown_and_location_is_not_work_mode():
    result = filter_status(
        job('A', analysis_geo='remote_unverified', work_mode='onsite'),
        JobFilters(country_code='ID', work_mode='remote'), analysis_date=TODAY,
    )
    assert result.per_filter == {'country_code': FilterState.UNKNOWN, 'work_mode': FilterState.CONFLICTS}
    assert result.status is FilterState.CONFLICTS
    remote_claim = filter_status(
        job('B', work_mode='remote_mentioned'), JobFilters(work_mode='remote'), analysis_date=TODAY,
    )
    assert remote_claim.status is FilterState.UNKNOWN


def test_posting_window_uses_explicit_date_and_unknown_is_not_recent():
    filters = JobFilters(posted_within_days=7)
    assert filter_status(job('edge', posted_at='2026-09-23'), filters, analysis_date=TODAY).status is FilterState.MATCHES
    assert filter_status(job('old', posted_at='2026-09-22'), filters, analysis_date=TODAY).status is FilterState.CONFLICTS
    assert filter_status(job('future', posted_at='2026-10-01'), filters, analysis_date=TODAY).status is FilterState.UNKNOWN
    assert filter_status(job('missing', posted_at=None), filters, analysis_date=TODAY).status is FilterState.UNKNOWN


def test_reject_out_of_scope_duplicates_and_invalid_request():
    with pytest.raises(ValueError, match='target-role'):
        filter_jobs([job('A', role_group='adjacent')], JobFilters(), analysis_date=TODAY)
    with pytest.raises(ValueError, match='Duplicate'):
        filter_jobs([job('A'), job('A')], JobFilters(), analysis_date=TODAY)
    with pytest.raises(ValueError, match='Explicit analysis date'):
        filter_status(job('A'), JobFilters(), analysis_date=None)
    with pytest.raises(ValueError, match='Explicit analysis date'):
        filter_status(job('A'), JobFilters(), analysis_date=datetime(2026, 9, 30))
    with pytest.raises(ValueError, match='Unapproved'):
        JobFilters(experience_bucket='senior')
