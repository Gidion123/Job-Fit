"""CV coach v1: about 10 scenarios (D-036): unsupported claims = 0, every part cites an answer,
"not done" gives no bullet, at most three gaps, years/location never coached."""
import pytest

from jobfit.support.cv_coach import (NOT_VERIFIED_NOTE, REPRESENTATION_GUIDANCE, TRUE_GAP_NOTE, bullet, gaps_for_job,
                                     not_verified, representation_items, requirement_groups, true_gaps,
                                     unsupported_words)

CARD = {'job_id': 'A', 'requirements': [
    {'requirement': 'Docker', 'label': 'NO_MATCH', 'importance': 'required', 'field': 'skill_tool'},
    {'requirement': 'SQL', 'label': 'PARTIAL', 'importance': 'required', 'field': 'skill_tool'},
    {'requirement': '3 years of ML', 'label': 'NO_MATCH', 'importance': 'required', 'field': 'experience_duration'},
    {'requirement': 'Based in Jakarta', 'label': 'NO_MATCH', 'importance': 'required', 'field': 'location'},
    {'requirement': 'Computer vision', 'label': 'NO_MATCH', 'importance': 'required', 'field': 'knowledge_area'},
    {'requirement': 'Airflow', 'label': 'NO_MATCH', 'importance': 'required', 'field': 'skill_tool'},
    {'requirement': 'Python', 'label': 'MATCH', 'importance': 'required', 'field': 'skill_tool'},
    {'requirement': 'Spark', 'label': 'NO_MATCH', 'importance': 'preferred', 'field': 'skill_tool'}]}

SCENARIOS = [
    {'what_when': 'Final-year thesis, 2025', 'own_part': 'built an image classifier for product defects',
     'tools': 'PyTorch and ResNet-18', 'result': '92% accuracy on 3,000 photos'},
    {'what_when': 'Internship at PT Contoh, Feb to May 2026', 'own_part': 'packaged a reporting script',
     'tools': 'Docker', 'result': ''},
    {'what_when': 'Bootcamp capstone 2026', 'own_part': 'wrote SQL queries for a churn dashboard',
     'tools': 'PostgreSQL, Looker Studio', 'result': 'used by 3 classmates'},
    {'what_when': 'Personal project, 2024', 'own_part': 'scheduled a daily data pipeline', 'tools': 'Airflow',
     'result': None},
    {'what_when': 'Kaggle competition 2025', 'own_part': 'trained a gradient boosting model',
     'tools': 'LightGBM', 'result': 'top 20 percent'},
    {'what_when': 'Freelance, 2023', 'own_part': 'cleaned survey data', 'tools': '', 'result': ''},
    {'what_when': 'Campus lab 2024', 'own_part': 'labelled images', 'tools': 'CVAT', 'result': '1200 images'},
]


def test_at_most_three_gaps_and_never_years_or_location():
    gaps = gaps_for_job(CARD)
    assert [g['requirement'] for g in gaps] == ['Docker', 'Computer vision', 'Airflow']
    assert all(len(g['questions']) == 4 for g in gaps)


@pytest.mark.parametrize('answers', SCENARIOS)
def test_bullet_uses_only_answers(answers):
    out = bullet('Docker', True, answers)
    assert unsupported_words(out['bullet'], answers) == set()
    assert all(p['source'] in answers or p['source'] == 'template' for p in out['parts'])
    assert all(ch not in out['bullet'] for ch in ('%',)) or '%' in (answers.get('result') or '')


def test_not_done_gives_no_bullet_only_ideas():
    out = bullet('Computer vision', False, None)
    assert out['bullet'] is None and out['ideas'] and out['parts'] == []


def test_missing_core_answers_refused():
    with pytest.raises(ValueError):
        bullet('Docker', True, {'what_when': '', 'own_part': 'x', 'tools': 'y', 'result': ''})


def test_no_number_is_added_when_none_given():
    out = bullet('SQL', True, SCENARIOS[1])
    assert not any(ch.isdigit() for ch in out['bullet'].replace('2026', ''))


# ---- D-105: "Improve My CV for This Job", four mutually exclusive categories ----

def categories(card):
    """requirement text -> the set of categories it appears in."""
    out = {}
    for name, items, key in (('A', representation_items(card), 'requirement'), ('B', gaps_for_job(card, limit=99),
                             'requirement'), ('V', not_verified(card), 'requirement')):
        for item in items:
            out.setdefault(item[key], set()).add(name)
    return out


def test_partial_with_evidence_is_a_only_and_no_match_is_b_only():
    card = {**CARD, 'requirements': [dict(r, cv_quotes=['Wrote SQL for weekly reports.'])
                                     if r['requirement'] == 'SQL' else r for r in CARD['requirements']]}
    cats = categories(card)
    assert cats['SQL'] == {'A'}                                    # PARTIAL + quote: A only, never the questions
    assert cats['Docker'] == cats['Computer vision'] == cats['Airflow'] == {'B'}
    assert 'SQL' not in [g['requirement'] for g in gaps_for_job(card)]
    item = representation_items(card)[0]
    assert item['current'] == ['Wrote SQL for weekly reports.'] and item['guidance'] == REPRESENTATION_GUIDANCE
    assert item['asked'] == 'This job asks for: SQL'
    assert all(len(v) == 1 for v in cats.values())                # every requirement in at most one category


def test_a_never_turns_a_job_term_into_a_candidate_claim():
    """JD asks for AWS; the CV only says cloud infrastructure: nothing may say the candidate used AWS."""
    card = {'job_id': 'J', 'explicit_conflicts': [], 'requirements': [
        {'unit_id': 'U1', 'requirement': 'AWS', 'label': 'PARTIAL', 'importance': 'required', 'field': 'skill_tool',
         'cv_quotes': ['Deployed backend services to cloud infrastructure.']}]}
    (item,) = representation_items(card)
    candidate_side = ' '.join(item['current'] + item['evidence'] + [item['guidance']])
    assert 'aws' not in candidate_side.casefold()
    assert item['requirement'] == 'AWS' and item['asked'].startswith('This job asks for:')
    assert set(item) == {'requirement', 'asked', 'current', 'guidance', 'evidence'}   # no rewritten CV line


def test_unconfirmed_years_and_location_are_not_verified_never_true_gaps():
    card = dict(CARD, explicit_conflicts=[])                        # history not confirmed: no D-086 conflict
    assert true_gaps(card) == []
    assert [v['requirement'] for v in not_verified(card)] == ['3 years of ML', 'Based in Jakarta']
    assert all(v['note'] == NOT_VERIFIED_NOTE for v in not_verified(card))
    assert categories(card)['3 years of ML'] == {'V'} and categories(card)['Based in Jakarta'] == {'V'}


def test_a_confirmed_conflict_is_c_only_deduplicated_and_without_advice():
    rows = [dict(r, unit_id=f'U{i}') for i, r in enumerate(CARD['requirements'])]
    message = 'U2: the JD asks for at least 3 years; the whole CV work history is about 1 years. JD: 3 years of ML'
    card = {'job_id': 'A', 'requirements': rows, 'explicit_conflicts': [message, message]}
    (gap,) = true_gaps(card)
    assert gap == {'conflict': message, 'note': TRUE_GAP_NOTE}
    assert 'project' not in gap['note'].casefold() and 'learn' not in gap['note'].casefold()
    assert '3 years of ML' not in [v['requirement'] for v in not_verified(card)]     # C, not "not verified"
    assert '3 years of ML' not in [g['requirement'] for g in gaps_for_job(card)]      # nor B
    assert '3 years of ML' not in [a['requirement'] for a in representation_items(card)]   # nor A
    assert [v['requirement'] for v in not_verified(card)] == ['Based in Jakarta']    # location absence is no conflict


# ---- the Analyze Fit view grouping (conflict > not verified > strengths / evidence gaps) ----

def rows(*specs):
    return [{'unit_id': u, 'requirement': text, 'label': label, 'importance': 'required', 'field': field,
             'cv_quotes': ['Some evidence.'] if label == 'PARTIAL' else []} for u, text, label, field in specs]


GROUP_CARD = {'job_id': 'G', 'explicit_conflicts': [], 'requirements': rows(
    ('u1', 'Python', 'MATCH', 'skill_tool'),
    ('u2', 'SQL', 'PARTIAL', 'skill_tool'),
    ('u3', 'Docker', 'NO_MATCH', 'skill_tool'),
    ('u4', '3 years of ML', 'NO_MATCH', 'experience_duration'),
    ('u5', '2 years of analytics', 'PARTIAL', 'experience_duration'),
    ('u6', 'Based in Jakarta', 'NO_MATCH', 'location'))}


def test_unconfirmed_background_requirements_are_not_verified_never_gaps():
    groups = requirement_groups(GROUP_CARD)
    assert groups == {'conflict': [], 'not_verified': ['u4', 'u5', 'u6'], 'strengths': ['u1'], 'gaps': ['u2', 'u3']}
    assert {u for item in not_verified(GROUP_CARD) for u in item['unit_ids']} == {'u4', 'u5', 'u6'}
    assert [a['requirement'] for a in representation_items(GROUP_CARD)] == ['SQL']        # editable PARTIAL: A too


def test_a_confirmed_conflict_is_only_a_conflict_with_explicit_precedence():
    card = dict(GROUP_CARD, explicit_conflicts=['u4: the JD asks for at least 3 years; the CV history is 1 year.',
                                                'u1: an evidence-labelled unit with a confirmed constraint'])
    groups = requirement_groups(card)
    assert groups['conflict'] == ['u1', 'u4']                                 # conflict wins over MATCH and not verified
    assert groups['not_verified'] == ['u5', 'u6'] and groups['strengths'] == [] and groups['gaps'] == ['u2', 'u3']
    every = [u for g in groups.values() for u in g]
    assert len(every) == len(set(every))                                      # exclusive


def test_groups_cover_each_required_unit_once_and_skip_unchecked_and_preferred_rows():
    card = dict(GROUP_CARD, requirements=GROUP_CARD['requirements'] + [
        {'unit_id': 'u7', 'requirement': 'Spark', 'label': 'NO_MATCH', 'importance': 'preferred',
         'field': 'skill_tool', 'cv_quotes': []},
        {'unit_id': 'u8', 'requirement': 'Kafka', 'label': None, 'importance': 'required', 'field': 'skill_tool',
         'cv_quotes': []}])
    every = [u for g in requirement_groups(card).values() for u in g]
    assert sorted(every) == ['u1', 'u2', 'u3', 'u4', 'u5', 'u6']
