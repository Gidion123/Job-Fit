"""D-022 saved demo: replay saved matching results through the same service code.

The demo answers only for the exact synthetic CV, saved stage-1 list and pipeline
configuration in its key. Anything else is refused, never approximated. The page
labels it "Demo with saved results".
"""
from __future__ import annotations

from hashlib import sha256
import json
from collections.abc import Mapping

from jobfit.matching.evidence_matcher import MatchingResult
from jobfit.schemas.analysis import UnitAssessment

DEMO_VERSION = 'saved-demo-v2'   # v2: config v4 (D-086), demo history confirmed


def demo_key(*, cv_id: str, cv_sha256: str, config_sha256: str, rules_sha256: str, seniority: bool) -> str:
    raw = json.dumps({'v': DEMO_VERSION, 'cv': cv_id, 'cv_sha': cv_sha256, 'config': config_sha256,
                      'rules': rules_sha256, 'seniority': bool(seniority)}, sort_keys=True)
    return sha256(raw.encode()).hexdigest()


class ReplayMatcher:
    """Same signature as match_evidence. Returns the saved answer for (cv, job, model)."""

    def __init__(self, records: Mapping[tuple[str, str, str], Mapping]):
        self.records = dict(records)
        self.used: list[tuple[str, str, str]] = []

    def __call__(self, cv, extraction, *, client=None, model: str, **_):
        key = (cv.profile.cv_id, extraction.job_id, model)
        row = self.records.get(key)
        self.used.append(key)
        if row is None:
            return MatchingResult([UnitAssessment(unit_id=u.unit_id, check_status='failed') for u in extraction.units],
                                  'failed', error_code='not_saved')
        if row['status'] != 'done':
            return MatchingResult([UnitAssessment(unit_id=u.unit_id, check_status='failed') for u in extraction.units],
                                  'failed', error_code=row.get('error_code') or row['status'])
        return MatchingResult([UnitAssessment.model_validate(a) for a in row['assessments']], 'done', cache_hit=True)
