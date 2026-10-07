"""Offline version/hold regressions; fixtures are not human annotation approval."""
from datetime import date
import json
import pytest
from jobfit.config import REPO_ROOT, GUIDELINE_FILE, GUIDELINE_VERSION, JD_PROMPT_FILE, EVIDENCE_PROMPT_FILE, runtime_versions
from jobfit.cv.parser import ParsedCV
from jobfit.schemas.cv import CVProfile
from jobfit.eval.fixture_client import FixtureClient
from jobfit.extraction.cache import ExtractionCache
from jobfit.pipeline import AnalysisContext, compare_pasted_jd
from jobfit.extraction import jd_extractor as extractor
from jobfit.eval.run_eval import compare_llm_artifacts

REF=date(2026,9,30)

@pytest.mark.parametrize('importance',['required','preferred','unknown'])
@pytest.mark.parametrize('clause',['knowledge of A and/or B','at least two of A, B, C','end-to-end RAG with uncertain umbrella overlap'])
def test_unsupported_composite_holds_report_without_excluding_it(importance,clause):
    jd='Qualifications:\nPython required.\n'+clause
    def extraction(payload):
        return {'job_id':payload['job_id'],'units':[
            {'unit_id':'known','text':'Python','importance':'required','field':'skill_tool','source_quotes':['Python']},
            {'unit_id':'unresolved','text':clause,'importance':importance,'field':'knowledge_area','source_quotes':[clause],'needs_review':True}]}
    evidence={'assessments':[{'unit_id':'known','label':'MATCH','cv_quotes':['Used Python in a project.']},
                             {'unit_id':'unresolved','label':None,'check_status':'failed','cv_quotes':[]}]}
    cv=ParsedCV(profile=CVProfile(cv_id='CV1',raw_text='Used Python in a project.'),analysis_date=REF)
    c=FixtureClient([extraction,evidence])
    report=compare_pasted_jd(cv,jd,context=AnalysisContext(REF,parsing_confirmed=True),client=c,model='deepseek-flash')
    assert report.score.status.value=='on_hold' and report.score.score_pct is None
    assert len(report.extraction.units)==2 and report.assessments[1].label is None
    assert report.score.required_total==(2 if importance=='required' else 1)
    assert report.denominator_status=='pending_structure_review'
    assert report.status=='structure_review_required' and report.versions['guideline_version']=='v1.3'

def test_actual_wire_uses_new_rule_files_and_keeps_historical_prompt_intact():
    assert GUIDELINE_VERSION=='v1.3' and GUIDELINE_FILE.name=='annotation_guideline_v1_3.md'
    assert 'D-041 already resolves' in (REPO_ROOT/'prompts/jd_extraction_v1_1.md').read_text()
    captured=[]
    class Capture:
        def chat_structured(self,model,messages,output_model,task,**kw):
            captured.append(messages)
            return output_model.model_validate({'job_id':'DEV','units':[]})
    result=extractor.extract_jd('Responsibilities: Build dashboards.',job_id='DEV',client=Capture(),model='deepseek-flash')
    prompt=captured[0][0]['content']
    assert GUIDELINE_FILE.read_text() in prompt and JD_PROMPT_FILE.read_text() in prompt
    assert 'D-041 already resolves' not in prompt
    assert result.guideline_version=='v1.3' and result.extraction.extractor_version.startswith('jd-prompt-v1.2/')
    assert EVIDENCE_PROMPT_FILE.name=='evidence_matching_v1_1.md'

def test_legacy_cached_extraction_is_not_reused_or_relabelled(tmp_path,monkeypatch):
    answer={'job_id':'DEV','units':[{'unit_id':'u','text':'Python','importance':'required','source_quotes':['Python']}]}
    cache=ExtractionCache(tmp_path)
    with monkeypatch.context() as m:
        m.setattr(extractor,'GUIDELINE_VERSION','v1.2')
        m.setattr(extractor,'GUIDELINE_FILE',REPO_ROOT/'evals/annotation_guideline_v1.md')
        m.setattr(extractor,'JD_PROMPT_FILE',REPO_ROOT/'prompts/jd_extraction_v1_1.md')
        m.setattr(extractor,'JD_PROMPT_VERSION','jd-prompt-v1.1')
        old=extractor.extract_jd('Python',job_id='DEV',client=FixtureClient([answer]),model='deepseek-flash',cache=cache,scope='corpus_jd')
    prior=(tmp_path/f'{old.key}.json').read_bytes()
    c=FixtureClient([answer])
    current=extractor.extract_jd('Python',job_id='DEV',client=c,model='deepseek-flash',cache=cache,scope='corpus_jd')
    assert not current.cache_hit and len(c.calls)==1 and current.key!=old.key
    assert (tmp_path/f'{old.key}.json').read_bytes()==prior and len(list(tmp_path.glob('*.json')))==2

def test_failed_matching_does_not_override_structure_failure_or_become_no_match():
    cv=ParsedCV(profile=CVProfile(cv_id='CV1',raw_text='Python'),analysis_date=REF)
    def extraction(p):return {'job_id':p['job_id'],'units':[{'unit_id':'x','text':'A and/or B','importance':'required','source_quotes':['A and/or B'],'needs_review':True}]}
    c=FixtureClient([extraction,TimeoutError('private transport text')])
    report=compare_pasted_jd(cv,'Qualifications: A and/or B',context=AnalysisContext(REF,parsing_confirmed=True),client=c,model='deepseek-flash')
    assert report.status=='matching_failed' and report.score.score_pct is None
    assert report.assessments[0].label is None and report.operations['matching']['error_code']=='TimeoutError'

def test_missing_guideline_compatibility_blocks_historical_gold_comparison():
    from pathlib import Path
    import json
    root=Path(__file__).resolve().parents[1]
    receipt=json.loads((root/'evals/results/cp23_metric_contract_D052_D054_20261003_v1.json').read_text())
    r={'model':'m','split':'development','cv_ids':['CV1'],'case_ids':['A'],'execution_kind':'fake_client',
       'prompt_hashes':{},'input_hashes':{},'gold_sha256':'g','guideline_sha256':'v1.3',
       'requirement_hashes':{'A':'fixed'},'attempt_kind':'first_attempt','reviewer_assisted':False}
    with pytest.raises(ValueError,match='compatibility'):
        compare_llm_artifacts([r],readiness={'status':'ready'},contract=receipt,registered_models={'m'})

def test_unknown_importance_alone_does_not_become_structure_hold():
    cv=ParsedCV(profile=CVProfile(cv_id='CV1',raw_text='Python project'),analysis_date=REF)
    def extraction(p):return {'job_id':p['job_id'],'units':[
        {'unit_id':'p','text':'Python','importance':'required','source_quotes':['Python']},
        {'unit_id':'q','text':'ambiguous experience','importance':'unknown','source_quotes':['experience']}]}
    evidence={'assessments':[{'unit_id':'p','label':'MATCH','cv_quotes':['Python project']},
                             {'unit_id':'q','label':'NO_MATCH','cv_quotes':[]}]}
    report=compare_pasted_jd(cv,'Python required; experience ambiguous',context=AnalysisContext(REF,parsing_confirmed=True),
                            client=FixtureClient([extraction,evidence]),model='deepseek-flash')
    assert report.score.status.value=='provisional' and report.score.score_pct==100
    assert report.denominator_status=='identified_units'
