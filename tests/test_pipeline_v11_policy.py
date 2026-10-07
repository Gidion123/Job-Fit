from copy import deepcopy

import pytest
from pydantic import BaseModel

from jobfit.llm.client import TruncatedStructuredResponse
from jobfit.llm.output_policy import MODEL_OUTPUT_LIMIT, output_allowance
from jobfit.llm.structured import StageFailure, validated_call
from jobfit.scoring.hold_policy_v11 import score_with_hold_policy
from jobfit.schemas.requirements import JDExtraction
from jobfit.schemas.analysis import UnitAssessment


class Answer(BaseModel):
    answer: str


def test_output_allowance_scales_and_is_capped():
    assert output_allowance('jd_extraction',1000,1)==20_000
    assert output_allowance('jd_extraction',15_000,20)>20_000
    assert output_allowance('jd_extraction',1_000_000,500)==MODEL_OUTPUT_LIMIT
    with pytest.raises(ValueError):output_allowance('jd_extraction',-1,1)


def test_length_continuation_once_then_validation_repair():
    class Fake:
        calls=[]
        def chat_structured(self,model,messages,output_model,task,**kw):
            self.calls.append((deepcopy(messages),kw['max_tokens'],task))
            if len(self.calls)==1:raise TruncatedStructuredResponse('length')
            return Answer(answer='bad' if len(self.calls)==2 else 'good')
    client=Fake()
    result,calls=validated_call(client,model='fake',prompt='rules',payload={},output_model=Answer,
        task='fixture',validate=lambda a: (_ for _ in ()).throw(ValueError('invalid_source_quote')) if a.answer=='bad' else None,
        max_tokens=100,model_output_limit=500)
    assert result.answer=='good' and calls==3
    assert [limit for _,limit,_ in client.calls]==[100,200,200]
    assert [task for _,_,task in client.calls]==[
        'fixture','fixture_length_continuation','fixture_validation_repair']
    assert all(sum(m['role']=='system' for m in messages)==1 and messages[0]['role']=='system'
               for messages,_,_ in client.calls)
    assert client.calls[1][0][-1]['role']=='user'


def test_repeated_length_stops_as_truncated_without_validation_repair():
    class Fake:
        calls=0
        def chat_structured(self,*args,**kwargs):
            self.calls+=1
            raise TruncatedStructuredResponse('length')
    client=Fake()
    with pytest.raises(StageFailure) as error:
        validated_call(client,model='fake',prompt='rules',payload={},output_model=Answer,
            task='fixture',validate=lambda _:None,max_tokens=100,model_output_limit=500)
    assert error.value.code=='truncated' and error.value.attempts==2 and client.calls==2


def test_h2_excludes_only_small_unresolved_share_and_is_provisional():
    units=[{'unit_id':f'U{i}','text':f'Skill {i}','field':'skill_tool','importance':'required',
            'source_quotes':[f'Skill {i}'],'needs_review':i==1} for i in range(1,6)]
    extraction=JDExtraction.model_validate({'job_id':'J','units':units})
    assessed=[UnitAssessment(unit_id=f'U{i}',label='MATCH',cv_quotes=['evidence']) for i in range(2,6)]
    h1,_=score_with_hold_policy(extraction,assessed,policy='H1')
    h2,excluded=score_with_hold_policy(extraction,assessed,policy='H2')
    assert h1.status.value=='on_hold' and h1.score_pct is None
    assert h2.status.value=='provisional' and h2.score_pct==100 and h2.required_total==4
    assert excluded==[{'unit_id':'U1','text':'Skill 1',
        'reason':'model marked the requirement structure needs_review','importance':'required',
        'source_quotes':['Skill 1']}]


def test_h2_above_threshold_and_other_failure_stay_on_hold():
    units=[{'unit_id':f'U{i}','text':f'Skill {i}','field':'skill_tool','importance':'required',
            'source_quotes':[f'Skill {i}'],'needs_review':i<=2} for i in range(1,6)]
    extraction=JDExtraction.model_validate({'job_id':'J','units':units})
    score,excluded=score_with_hold_policy(extraction,[],policy='H2')
    assert score.status.value=='on_hold' and not excluded
    units[1]['needs_review']=False
    extraction=JDExtraction.model_validate({'job_id':'J','units':units})
    score,excluded=score_with_hold_policy(extraction,[],policy='H2')
    assert score.status.value=='on_hold' and len(excluded)==1


def test_h2_does_not_recount_an_unresolved_duplicate():
    rows=[{'unit_id':'A','text':'Python','normalized_name':'python','importance':'required',
           'field':'skill_tool','source_quotes':['Python'],'needs_review':True},
          {'unit_id':'A-copy','text':'Python','normalized_name':'python','importance':'required',
           'field':'skill_tool','source_quotes':['Python']}] + [
          {'unit_id':f'U{i}','text':f'Skill {i}','importance':'required','field':'skill_tool',
           'source_quotes':[f'Skill {i}']} for i in range(4)]
    extraction=JDExtraction.model_validate({'job_id':'J','units':rows})
    assessments=[UnitAssessment(unit_id=f'U{i}',label='MATCH',cv_quotes=['evidence']) for i in range(4)]
    score,excluded=score_with_hold_policy(extraction,assessments,policy='H2')
    assert score.required_total==4 and score.score_pct==100
    assert len(excluded)==1


def test_run_client_reserves_inflight_cap_before_concurrent_dispatch(monkeypatch,tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from jobfit.llm.ledger import UsageLedger,UsageRecord
    from jobfit.llm.pricing import ModelPrice
    from scripts import run_cp23_pipeline_v11 as runner
    entered=Event();release=Event()
    class Base:
        ledger=UsageLedger(tmp_path/'ledger.jsonl')
        guard=type('Guard',(),{'check':lambda self,upper:None})()
        def _price(self,model):return ModelPrice('fixture','fixture',0,1_000_000)
        def _chat_attempt(self,*args):
            entered.set();release.wait(2)
            self.ledger.append(UsageRecord(run_id='fixture',task='fixture',model='fixture',cost_usd=1))
            return Answer(answer='done')
    monkeypatch.setattr(runner,'CAP',1.5)
    client=runner.RunClient(Base(),0)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first=pool.submit(client.chat_structured,'fixture',[],Answer,'fixture',1)
        assert entered.wait(2)
        with pytest.raises(runner.RunCapReached):
            client.chat_structured('fixture',[],Answer,'fixture',1)
        release.set()
        assert first.result().answer=='done'
    assert len(client.base.ledger.records())==1


# D-072 H2v2 ---------------------------------------------------------------

def _h2v2_jd(flagged_field='skill_tool', flagged_text='Skill 1', flagged_importance='required',
             min_years=None, n=5):
    units=[{'unit_id':f'U{i}','text':f'Skill {i}','field':'skill_tool','importance':'required',
            'source_quotes':[f'Skill {i}']} for i in range(2,n+1)]
    flagged={'unit_id':'U1','text':flagged_text,'field':flagged_field,'importance':flagged_importance,
             'source_quotes':[flagged_text],'needs_review':True}
    if min_years is not None:
        flagged.update(kind='qualified',min_years=min_years)
    return JDExtraction.model_validate({'job_id':'J','units':[flagged,*units]})


def _all_match(n=5):
    return [UnitAssessment(unit_id=f'U{i}',label='MATCH',cv_quotes=['evidence']) for i in range(2,n+1)]


def test_h2v2_matches_h2_for_an_ordinary_skill_flag():
    extraction=_h2v2_jd()
    h2,ex2=score_with_hold_policy(extraction,_all_match(),policy='H2')
    v2,exv2=score_with_hold_policy(extraction,_all_match(),policy='H2v2')
    assert (v2.status,v2.score_pct,v2.required_total)==(h2.status,h2.score_pct,h2.required_total)
    assert exv2==ex2 and v2.status.value=='provisional'


@pytest.mark.parametrize('field,text,years',[
    ('experience_duration','3+ years of data science experience',3.0),
    ('education',"Bachelor's degree in Computer Science",None),
    ('other','Senior engineer able to lead the platform',None),
    ('knowledge_area','At least 2 years of LLM application work',None),
    ('other','Final-year student or recent graduate',None),
])
def test_h2v2_never_excludes_experience_level_or_education(field,text,years):
    extraction=_h2v2_jd(field,text,min_years=years)
    h2,_=score_with_hold_policy(extraction,_all_match(),policy='H2')
    v2,excluded=score_with_hold_policy(extraction,_all_match(),policy='H2v2')
    assert h2.status.value=='provisional'
    assert v2.status.value=='on_hold' and v2.score_pct is None and excluded==[]
    assert 'U1' in v2.reasons[-1]


@pytest.mark.parametrize('field,importance',[('skill_tool','preferred'),('soft_skill','required'),
                                             ('skill_tool','unknown'),('location','required')])
def test_h2v2_flag_outside_percentage_keeps_status(field,importance):
    extraction=_h2v2_jd(field,'Some flagged item',importance)
    assessed=_all_match()+[UnitAssessment(unit_id='U1',label='NO_MATCH')]
    plain,_=score_with_hold_policy(extraction.model_copy(update={'units':[u.model_copy(update={'needs_review':False})
                                   for u in extraction.units]}),assessed,policy='H2v2')
    v2,excluded=score_with_hold_policy(extraction,assessed,policy='H2v2')
    h2,_=score_with_hold_policy(extraction,assessed,policy='H2')
    assert excluded==[] and v2.status==plain.status and v2.score_pct==plain.score_pct
    if importance!='unknown':
        assert v2.status.value=='final' and h2.status.value=='provisional'


def test_h2v2_threshold_and_unknown_policy():
    units=[{'unit_id':f'U{i}','text':f'Skill {i}','field':'skill_tool','importance':'required',
            'source_quotes':[f'Skill {i}'],'needs_review':i<=2} for i in range(1,6)]
    extraction=JDExtraction.model_validate({'job_id':'J','units':units})
    score,excluded=score_with_hold_policy(extraction,[],policy='H2v2')
    assert score.status.value=='on_hold' and excluded==[]
    with pytest.raises(ValueError):
        score_with_hold_policy(extraction,[],policy='H3')


@pytest.mark.parametrize('text,expected',[('Sr. Data Scientist',True),('3–6 years of hands-on work',True),
    ('minimal 2 tahun pengalaman',True),('Tech Lead experience',True),('5+ yrs',True),
    ('lead data pipelines',False),('Python and SQL',False),('staffing reports',False)])
def test_seniority_heuristic_examples(text,expected):
    from jobfit.scoring.hold_policy_v11 import is_protected_unit
    from jobfit.schemas.requirements import RequirementUnit
    assert is_protected_unit(RequirementUnit(unit_id='U',text=text,importance='required',field='skill_tool'))==expected
