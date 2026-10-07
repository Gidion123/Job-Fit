"""CV coach v1: about 10 scenarios (D-036): unsupported claims = 0, every part cites an answer,
"not done" gives no bullet, at most three gaps, years/location never coached."""
import pytest

from jobfit.support.cv_coach import bullet, gaps_for_job, unsupported_words

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
