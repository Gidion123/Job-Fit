"""Minimal CV suggestions (claim guard) and market counts. Offline."""
import pytest

from jobfit.support.cv_suggestions import suggestions
from jobfit.support.market_insight import skill_counts


def card(job, reqs, scored=True):
    return {'job_id': job, 'scored': scored, 'requirements': reqs}


def req(text, label, imp='required', quotes=()):
    return {'requirement': text, 'label': label, 'importance': imp, 'cv_quotes': list(quotes)}


def test_suggestions_count_gaps_and_never_suggest_claims():
    cards = [card('A', [req('Docker', 'NO_MATCH'), req('SQL', 'PARTIAL', quotes=['Used SQL in class'])]),
             card('B', [req('docker', 'NO_MATCH'), req('Python', 'MATCH'), req('AWS', 'NO_MATCH', imp='preferred')]),
             card('C', [req('Kubernetes', 'NO_MATCH')], scored=False)]
    out = suggestions(cards)
    assert out['analyzed_scored_jobs'] == 2
    first = out['items'][0]
    assert first['requirement'].lower() == 'docker' and first['jobs_asking'] == 2 and first['kind'] == 'gap'
    assert 'only if you really have' in first['advice']
    sql = next(i for i in out['items'] if i['requirement'] == 'SQL')
    assert sql['kind'] == 'make_explicit' and sql['cv_quotes'] == ['Used SQL in class']
    assert all(i['requirement'] not in ('Python', 'AWS', 'Kubernetes') for i in out['items'])
    assert 'Never add a skill' in out['guard']


def test_market_counts_cite_their_base():
    jobs = {'1': {'role_family': 'data_science', 'skills': ['python', 'sql']},
            '2': {'role_family': 'data_science', 'skills': ['python']},
            '3': {'role_family': 'genai_llm', 'skills': ['llm']}}
    out = skill_counts(jobs, role_family='data_science')
    assert out['postings'] == 2 and out['skills'][0] == {'skill': 'python', 'jobs': 2, 'share': 1.0}
    assert 'In 2 searchable postings' in out['explanation']
    with pytest.raises(ValueError):
        skill_counts(jobs, role_family='marketing')


def test_years_and_location_are_not_suggested_and_soft_skills_are_labelled():
    cards = [card('A', [dict(req('3 years of Python', 'NO_MATCH'), field='experience_duration'),
                        dict(req('Based in Jakarta', 'NO_MATCH'), field='location'),
                        dict(req('Teamwork', 'NO_MATCH'), field='soft_skill')])]
    items = suggestions(cards)['items']
    assert [i['requirement'] for i in items] == ['Teamwork'] and items[0]['kind'] == 'soft_skill'
