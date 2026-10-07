"""Stability comparison logic. Offline."""
from scripts import run_extraction_stability as st


def p(units, required, texts):
    return {'units': units, 'required': required, 'needs_review': 0, 'jd_quality': 'ok', 'texts': texts}


def test_compare_counts_ranges_and_overlap():
    out = st.compare({'F00332': [p(3, 2, ['a', 'b', 'c']), p(3, 2, ['a', 'b', 'c']), p(4, 3, ['a', 'b', 'c', 'd'])],
                      'F00036': [p(2, 1, ['x', 'y']), None, p(2, 1, ['x', 'y'])]})
    a, b = out['jobs']['F00332'], out['jobs']['F00036']
    assert a['unit_count_range'] == [3, 4] and a['required_count_range'] == [2, 3]
    assert a['text_jaccard_pairs'] == [1.0, 0.75, 0.75]
    assert b['failed_runs'] == 1 and b['text_jaccard_median'] == 1.0
    assert out['denominator_stable_jobs'] == 1 and a['gold']['units'] > 0


def test_saved_profiles_exist_for_preregistered_jobs():
    assert all(st.saved_profile(j) is not None for j in st.JOBS)
    assert st.norm('Python (pandas) & SQL') == 'python pandas sql'
