import pytest
from jobfit.matching.guardrails import apply_guardrails
CV='## Experience\nUsed SQL for reports.\n## Skills\nSQL, PostgreSQL, Git\n'
def run(text,quote,label='MATCH'):
    a={'unit_id':'u','label':label,'cv_quotes':[quote],'branches':[]}
    result,changes=apply_guardrails({'text':text},a,CV)
    assert a['label']==label
    return result,changes

def test_skills_only_and_real_usage():
    r,c=run('Git','Git');assert r['label']=='PARTIAL' and c[0]['flags']==['skills_list_only']
    r,c=run('SQL','Used SQL for reports.');assert r['label']=='MATCH' and not c

@pytest.mark.parametrize('join',['/', ' and ', ', '])
def test_partial_named_item_coverage(join):
    r,c=run('SQL'+join+'PostgreSQL','Used SQL for reports.')
    assert r['label']=='PARTIAL' and 'partial_item_coverage' in c[0]['flags']

@pytest.mark.parametrize('label',['PARTIAL','NO_MATCH',None])
def test_never_raises(label):
    r,c=run('Git','Git',label);assert r['label']==label and not c

def test_or_not_made_into_and():
    r,c=run('SQL or PostgreSQL','Used SQL for reports.');assert r['label']=='MATCH' and not c

def test_ambiguous_occurrence_not_assumed_skills_only():
    a={'unit_id':'u','label':'MATCH','cv_quotes':['SQL'],'branches':[]}
    r,c=apply_guardrails({'text':'SQL'},a,CV);assert r['label']=='MATCH' and not c

def test_skills_item_does_not_fill_conjunction_usage_gap():
    a={'unit_id':'u','label':'MATCH','cv_quotes':['Used SQL for reports.','SQL, PostgreSQL, Git'],'branches':[]}
    r,c=apply_guardrails({'text':'SQL/PostgreSQL'},a,CV)
    assert r['label']=='PARTIAL' and c[0]['supported_items']==['SQL']


# Plain-text CVs (PDF/DOCX uploads have no Markdown heading marks) -----------

PLAIN_CV = """Rina Putri
Jakarta
RINGKASAN
Lulusan statistika yang suka data.
Pengalaman
Data Analyst Intern, PT Contoh
- Membersihkan data transaksi dengan Python dan SQL.
Keahlian:
Python, SQL, Git, Docker
Pendidikan
S1 Statistika
"""


def test_plain_text_skills_section_is_detected():
    from jobfit.matching.guardrails import skills_only
    assert skills_only('Git', PLAIN_CV) and skills_only('Docker', PLAIN_CV)
    # Python also appears under Pengalaman, so it is not skills-list-only.
    assert not skills_only('Python', PLAIN_CV)
    # The Pendidikan heading ends the Skills section.
    assert not skills_only('S1 Statistika', PLAIN_CV)


def test_plain_text_skills_only_match_is_lowered():
    a = {'unit_id': 'U1', 'label': 'MATCH', 'cv_quotes': ['Python, SQL, Git, Docker']}
    result, changes = apply_guardrails({'text': 'Docker'}, a, PLAIN_CV)
    assert result['label'] == 'PARTIAL' and changes[0]['flags'] == ['skills_list_only']


def test_markdown_behaviour_unchanged_for_heading_with_colon_variants():
    from jobfit.matching.guardrails import skills_only
    md = "# Name\n## Skills\nGit, Docker\n## Experience\nUsed Docker daily.\n"
    assert skills_only('Git', md) and not skills_only('Docker', md)
