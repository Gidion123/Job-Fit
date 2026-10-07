"""Current eight synthetic acceptance cases, distinct from historical fixtures."""
import hashlib,json
from datetime import date
from pathlib import Path
import pytest
from jobfit.matching.constraints import experience_constraint,experience_years
from jobfit.schemas.cv import ExperienceEntry,ParseStatus
from jobfit.schemas.requirements import JDExtraction
from jobfit.schemas.analysis import UnitAssessment
from jobfit.scoring.score import compute_score,merge_duplicate_units
ROOT=Path(__file__).resolve().parents[1]
CASES=sorted((ROOT/'evals/fixtures/v1_3').glob('dev_*.json'))

@pytest.mark.parametrize('path',CASES,ids=lambda p:p.stem)
def test_current_fixture_source_trace_and_expected_behavior(path):
    d=json.loads(path.read_text());rev=d['revision']
    assert hashlib.sha256((ROOT/rev['source_file']).read_bytes()).hexdigest()==rev['source_sha256']
    assert d['synthetic'] and d['guideline_version']=='v1.3' and not rev['human_independent_approval']
    ex=JDExtraction.model_validate(d['extraction'])
    aa=[UnitAssessment.model_validate(a) for a in d['assessments']]
    for u in ex.units:
        assert all(q in d['synthetic_jd_context'] for q in u.source_quotes)
    for a in aa:
        assert all(q in d['synthetic_cv_context'] for q in a.cv_quotes)
        for b in a.branches:
            assert all(q in d['synthetic_cv_context'] for q in b.cv_quotes)
    r=compute_score(ex,aa,ParseStatus(d['cv_parse_status']));expected=d['expected']
    assert r.status.value==expected['status'] and r.required_total==expected['required_total']
    if expected['score_pct'] is None:assert r.score_pct is None
    else:assert r.score_pct==pytest.approx(expected['score_pct'],abs=.01)
    for k in ('matched','partial','preferred_total','preferred_met','unknown_importance_total','met_display'):
        if k in expected:assert getattr(r,k)==expected[k]
    e=d['experience'];years=experience_years([ExperienceEntry.model_validate(x) for x in e['cv_entries']],date.fromisoformat(d['analysis_date']))
    assert experience_constraint(e['min_years'],years).state.value==expected['constraint_state']


def test_eight_cases_and_qualified_sql_is_not_discarded_as_duplicate():
    assert len(CASES)==8
    d=json.loads(next(p for p in CASES if 'repeated' in p.name).read_text())
    units,merged=merge_duplicate_units(JDExtraction.model_validate(d['extraction']).units)
    assert merged=={'u5':'u1'} and len(units)==4
    assert len(next(u for u in units if u.unit_id=='u1').source_quotes)==2
    assert any('complex' in u.text.lower() for u in units)
