"""D-022 saved demo: replay, key and the shipped bundle. Offline."""
from datetime import date

from jobfit.cv.parser import ParsedCV
from jobfit.recommend.saved_demo import ReplayMatcher, demo_key
from jobfit.schemas.cv import CVProfile
from jobfit.schemas.requirements import JDExtraction

CV = ParsedCV(profile=CVProfile(cv_id='CV1', raw_text='Python'), analysis_date=date(2026, 9, 30))
EXT = JDExtraction.model_validate({'job_id': 'J', 'units': [
    {'unit_id': 'u1', 'text': 'Python', 'importance': 'required', 'field': 'skill_tool', 'source_quotes': ['Python']}]})


def test_replay_returns_saved_answer_or_a_failure_never_a_guess():
    rec = {('CV1', 'J', 'sol'): {'status': 'done', 'assessments': [{'unit_id': 'u1', 'label': 'MATCH', 'cv_quotes': ['Python']}]},
           ('CV1', 'J', 'luna'): {'status': 'failed', 'error_code': 'timeout'}}
    m = ReplayMatcher(rec)
    assert m(CV, EXT, model='sol').assessments[0].label.value == 'MATCH'
    assert m(CV, EXT, model='luna').error_code == 'timeout'
    missing = m(CV, EXT, model='other')
    assert missing.status == 'failed' and missing.error_code == 'not_saved'


def test_key_changes_with_any_input():
    base = dict(cv_id='CV1', cv_sha256='a', config_sha256='b', rules_sha256='c', seniority=True)
    k = demo_key(**base)
    assert all(demo_key(**{**base, f: v}) != k for f, v in
               [('cv_id', 'CV2'), ('cv_sha256', 'x'), ('config_sha256', 'x'), ('rules_sha256', 'x'), ('seniority', False)])


def test_shipped_bundle_matches_current_files():
    from jobfit.api.wiring import load_saved_demo
    lookup = load_saved_demo()
    for cv in ('CV1', 'CV2'):
        for rule in (True, False):
            result = lookup(cv, rule)
            assert result is not None and result['blocks'][0]['groups']['matches']
    assert lookup('CV3', True) is None
