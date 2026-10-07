"""Experience upper-bound conflict rule. Offline."""
from datetime import date

from jobfit.cv.parser import ParsedCV
from jobfit.matching.experience_rule import constraint_lookup, experience_conflicts
from jobfit.schemas.analysis import ConstraintState
from jobfit.schemas.cv import CVProfile, ExperienceEntry, PartialDate
from jobfit.schemas.requirements import JDExtraction

REF = date(2026, 9, 30)


def cv(entries):
    return ParsedCV(profile=CVProfile(cv_id='X', raw_text='x', experience=entries), analysis_date=REF)


JUNIOR = cv([ExperienceEntry(title='Intern', start_partial=PartialDate(year=2026, month=2),
                             end_partial=PartialDate(year=2026, month=5))])
SENIOR = cv([ExperienceEntry(title='Analyst', start_partial=PartialDate(year=2020, month=1), is_present=True)])
UNDATED = cv([ExperienceEntry(title='Analyst', start_partial=PartialDate(year=2020), is_present=True)])


def ext(*units):
    return JDExtraction.model_validate({'job_id': 'J', 'units': list(units)})


EXP3 = {'unit_id': 'e', 'text': '3 years as data scientist', 'importance': 'required', 'field': 'experience_duration',
        'kind': 'qualified', 'min_years': 3, 'source_quotes': ['3 years']}


def states(found):
    return [c.state for c in found]


def test_short_total_history_is_an_explicit_conflict():
    found = experience_conflicts(ext(EXP3), JUNIOR, history_confirmed=True)
    assert states(found) == [ConstraintState.EXPLICIT_CONFLICT] and '0.33' in found[0].message


def test_long_history_is_never_called_compatible():
    assert states(experience_conflicts(ext(EXP3), SENIOR, history_confirmed=True)) == [ConstraintState.UNKNOWN]


def test_unconfirmed_or_undated_history_stays_unknown():
    assert states(experience_conflicts(ext(EXP3), JUNIOR, history_confirmed=False)) == [ConstraintState.UNKNOWN]
    assert states(experience_conflicts(ext(EXP3), UNDATED, history_confirmed=True)) == [ConstraintState.UNKNOWN]


def test_preferred_and_alternative_minimums_are_ignored():
    pref = dict(EXP3, unit_id='p', importance='preferred')
    alt = {'unit_id': 'a', 'text': 'S1 or 3 years', 'importance': 'required', 'field': 'education', 'kind': 'alternative_group',
           'source_quotes': ['S1 or 3 years'], 'branches': [{'branch_id': 'b1', 'text': 'S1'}, {'branch_id': 'b2', 'text': '3 years', 'min_years': 3}]}
    assert experience_conflicts(ext(pref, alt), JUNIOR, history_confirmed=True) == []


def test_lookup_adapter_for_recommend():
    look = constraint_lookup(JUNIOR, history_confirmed=True)
    assert states(look('J', ext(EXP3))) == [ConstraintState.EXPLICIT_CONFLICT]
