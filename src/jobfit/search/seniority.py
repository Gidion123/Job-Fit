"""D-074 stage-1 seniority rule for early-career users (development candidate).

JobFit serves early-career AI and data job seekers. In the development labels,
every job whose posting asks for three or more years was judged not relevant for
CV1 and CV2. This rule moves those jobs below the others, keeping the original
order inside each group. It removes nothing, so the user can still scroll to
them, and the user can switch the rule off.

The bucket comes from CP1 `experience_bucket` (years parsed from the JD text).
`not_stated` is never demoted: unknown is not the same as senior.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

DEMOTED_BUCKETS = frozenset({'3-4y', '5y+'})
RULE_VERSION = 'seniority-demote-3y-v1'


def demote_senior(ranking: Sequence[str], buckets: Mapping[str, str | None], *,
                  enabled: bool = True, demoted: frozenset[str] = DEMOTED_BUCKETS) -> list[str]:
    """Stable partition: jobs outside `demoted` first, then demoted jobs, each in stage-1 order."""
    ids = list(ranking)
    if len(ids) != len(set(ids)):
        raise ValueError('Ranking identities must be unique')
    if not enabled:
        return ids
    keep = [j for j in ids if buckets.get(j) not in demoted]
    low = [j for j in ids if buckets.get(j) in demoted]
    return keep + low
