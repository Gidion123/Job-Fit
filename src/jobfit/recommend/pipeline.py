"""Assemble D-010/D-013 result groups from completed search and analysis inputs.

Retrieval and model calls remain caller-owned. This function never invents a
score for a missing result or silently relaxes an optional filter.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from jobfit.schemas.analysis import JobAnalysis
from jobfit.scoring.ranking import OrderedGroup, order_group
from jobfit.search.filters import FilterResult, FilterState


@dataclass(frozen=True)
class RecommendationGroups:
    matching_filters: OrderedGroup
    unknown_filters: OrderedGroup
    analyzed_ids: tuple[str, ...]
    not_analyzed_count: int
    eligible_count: int
    active_filters: tuple[str, ...]
    include_unknown: bool

    @property
    def first_group_title(self) -> str:
        return 'Matches your filters' if self.active_filters else 'Target-role jobs'


def assemble_recommendations(
    filtered: FilterResult,
    candidate_ids: Sequence[str],
    analyses: Mapping[str, JobAnalysis],
) -> RecommendationGroups:
    """Group only selected candidates; callers supply explicit held analyses.

    `candidate_ids` are the stage-1 order after filtering. The remaining
    eligible jobs are counted as not analyzed, without a made-up order or score.
    """
    candidates = tuple(candidate_ids)
    eligible = set(filtered.eligible_ids)
    if len(candidates) != len(set(candidates)) or not set(candidates) <= eligible:
        raise ValueError('Candidate identities must be unique and eligible under active filters')
    if set(analyses) != set(candidates):
        raise ValueError('Every selected candidate needs a result, including an explicit held result')
    states = {item.job_id: item.status for item in filtered.matches + filtered.unknown}
    matching, unknown = [], []
    for rank, job_id in enumerate(candidates, 1):
        item = analyses[job_id]
        if item.job_id != job_id or item.stage1_rank != rank:
            raise ValueError('Analysis identity and original stage-1 rank must match')
        (matching if states[job_id] is FilterState.MATCHES else unknown).append(item)
    return RecommendationGroups(
        matching_filters=order_group(matching),
        unknown_filters=order_group(unknown),
        analyzed_ids=candidates,
        not_analyzed_count=len(eligible)-len(candidates),
        eligible_count=len(eligible),
        active_filters=filtered.active_filters,
        include_unknown=filtered.include_unknown,
    )
