"""The observed one-of-nine response must never yield a misleading percentage."""
from jobfit.extraction.coverage import qualification_coverage
from jobfit.extraction.jd_extractor import extract_jd
from jobfit.extraction.cache import ExtractionCache
from jobfit.eval.fixture_client import FixtureClient
from jobfit.extraction.audited import ExtractionSpec, qualification_inventory
from jobfit.config import REPO_ROOT
from jobfit.schemas.requirements import JDQuality, RequirementUnit


def unit(quote='Python'):
    return RequirementUnit(unit_id='u1',text=quote,importance='required',field='skill_tool',source_quotes=[quote])


def test_clear_omission_is_not_schema_success_or_semantic_recall():
    text='Kualifikasi\n\n• Python\n\n• SQL\n\nTanggung Jawab\n\n• Build dashboards'
    r=qualification_coverage(text,[unit()])
    assert r['bullet_count']==2 and r['uncovered_bullet_indices']==[2]
    assert not r['semantic_completeness_verified']
    full=qualification_coverage(text,[unit('Python'),unit('SQL')])
    assert full['status']=='no_uncovered_bullets' and not full['semantic_completeness_verified']
    assert qualification_coverage('Responsibilities\n- Python',[unit()])['status']=='not_assessed'


def test_runtime_guard_rechecks_cache_without_rewriting_response(tmp_path):
    text='Requirements\n- Python\n- SQL'
    cache=ExtractionCache(tmp_path)
    client=FixtureClient([{'job_id':'DEV','units':[unit().model_dump(mode='json')]}])
    first=extract_jd(text,job_id='DEV',client=client,model='deepseek-flash',cache=cache,scope='corpus_jd')
    assert first.extraction.jd_quality=='looks_incomplete' and first.coverage['uncovered_bullet_indices']==[2]
    assert first.extraction.jd_quality is JDQuality.LOOKS_INCOMPLETE
    assert first.extraction.model_dump(mode='json')['jd_quality']=='looks_incomplete'
    assert cache.get(first.key,scope='corpus_jd')['jd_quality']=='ok'
    second=extract_jd(text,job_id='DEV',client=FixtureClient([]),model='deepseek-flash',cache=cache,scope='corpus_jd')
    assert second.cache_hit and second.extraction.jd_quality=='looks_incomplete'
    assert second.coverage==first.coverage


def test_one_bullet_is_not_forced_into_one_unit_and_qualifiers_not_certified():
    r=qualification_coverage('Qualifications\n- Python and SQL',[unit('Python')])
    assert r['status']=='no_uncovered_bullets' and not r['semantic_completeness_verified']


def test_flattened_inline_qualification_heading_cannot_be_empty_success():
    spec=ExtractionSpec(REPO_ROOT/'prompts/jd_extraction_v1_4_experimental.md','jd-prompt-v1.4-experimental')
    client=FixtureClient([{'job_id':'DEV','units':[],'qualification_coverage':[]}]*2)
    result=extract_jd('Role summary. Qualifications and Experience: Python and SQL required for production work.',
        job_id='DEV',client=client,model='deepseek-flash',spec=spec)
    assert result.status=='failed'
    assert result.error_code=='empty_extraction_despite_requirement_section'
    assert len(client.calls)==2


def test_preferred_competencies_heading_has_a_source_inventory():
    text='Responsibilities\n- Build reports\n\nPreferred competencies and qualifications\n\n• Python\n\n• SQL'
    inventory=qualification_inventory(text)
    assert [x['source_quote'] for x in inventory]==['Python','SQL']
    spec=ExtractionSpec(REPO_ROOT/'prompts/jd_extraction_v1_4_experimental.md','jd-prompt-v1.4-experimental')
    client=FixtureClient([{'job_id':'DEV','units':[],'qualification_coverage':[]}]*2)
    result=extract_jd(text,job_id='DEV',client=client,model='deepseek-flash',spec=spec)
    assert result.status=='failed' and result.error_code=='qualification_inventory_incomplete'


def test_known_f00034_regression_from_preserved_source_and_response():
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    rows=[json.loads(line) for line in (root/'data/processed/jobs_features.jsonl').read_text().splitlines()]
    text=next(r['description_clean'] for r in rows if r['final_cluster_id']=='F00034')
    quote='Minimal S1 Teknik Informatika, Ilmu Komputer, Data Science, Artificial Intelligence, atau bidang terkait.'
    r=qualification_coverage(text,[unit(quote)])
    assert r['bullet_count']==9 and r['uncovered_bullet_indices']==list(range(2,10))
