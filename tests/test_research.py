from pathlib import Path
import pandas as pd
import pytest
from src.jobs.research import analysis_geo, standardized_skill_comparison, verify_snapshot


def test_remote_cohort_is_disjoint_and_missing_country_unknown():
    assert analysis_geo('ID', 'remote_unverified') == 'remote_unverified'
    assert analysis_geo(None, 'indonesia') == 'unknown'
    assert analysis_geo('US', 'indonesia') == 'foreign'


def test_standardization_removes_constructed_role_composition_effect():
    # Within each role, identical skill rates. Unequal role mixes produce a spurious raw gap.
    def row(role, skills):
        return {'role_family': role, 'clean_length': 2000, 'skills': skills}
    a = pd.DataFrame([row('DS', ['sql'])]*9 + [row('AI', [])]*3)
    b = pd.DataFrame([row('DS', ['sql'])]*3 + [row('AI', [])]*9)
    result = standardized_skill_comparison(a, b, ['sql'])
    assert result['skills']['sql']['difference_pp'] == pytest.approx(0)
    assert sum(r['weight'] for r in result['strata']) == pytest.approx(1)
    assert result['retained_n'] == {'ID': 12, 'foreign': 12}


def test_standardization_reports_missing_common_support():
    a = pd.DataFrame([{'role_family': 'DS', 'clean_length': 2000, 'skills': ['sql']}])
    assert standardized_skill_comparison(a, a, ['sql'])['status'] == 'insufficient_common_support'


@pytest.mark.skipif(not (Path(__file__).resolve().parents[1] / 'data' / 'raw').exists(),
                    reason='raw JSearch data is kept locally, not in the public repository')
def test_frozen_inputs_match_manifest():
    assert verify_snapshot(Path(__file__).resolve().parents[1])['raw_inputs_verified'] == 460


def test_processed_summary_and_populations_reconcile():
    import json
    root = Path(__file__).resolve().parents[1]
    jobs = pd.read_json(root/'data/processed/jobs_features.jsonl', lines=True)
    summary = json.loads((root/'data/processed/CP1_research_summary.json').read_text())
    aud = jobs[jobs.is_auditable]
    target = aud[aud.role_group.eq('target')]
    assert jobs.final_cluster_id.is_unique
    assert summary['populations']['AUD'] == len(aud)
    assert summary['populations']['TGT'] == len(target)
    for name, geo in [('ID_T','indonesia'), ('FOR_T','foreign'), ('REM_T','remote_unverified'), ('UNKNOWN_T','unknown')]:
        assert summary['populations'][name] == int(target.analysis_geo.eq(geo).sum())
    pool = target[target.analysis_geo.eq('indonesia') & target.experience_bucket.isin(['entry', '1-2y'])]
    assert set(summary['experience_screen_pool_ID']['record_ids']) == set(pool.record_id)
    assert summary['experience_screen_pool_ID']['education_mentions']['bachelor']['n'] == int(pool.education_levels.apply(lambda x: 'bachelor' in x).sum())
    assert int(aud.country_code.eq('US').sum()) > 0
    assert not ((aud.country_code == 'US') & (aud.analysis_geo == 'indonesia')).any()
