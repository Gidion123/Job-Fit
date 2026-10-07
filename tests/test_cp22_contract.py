from types import SimpleNamespace
from dataclasses import replace
import json
import pytest
from pydantic import BaseModel
from jobfit.config import Settings
from jobfit.cv.parser import CVWire
from jobfit.extraction.jd_extractor import extract_jd
from jobfit.eval.fixture_client import FixtureClient
from jobfit.llm.client import OpenRouterClient, strict_schema, TruncatedStructuredResponse, UnexpectedResponseModel
from jobfit.matching.evidence_matcher import EvidenceResponse
from jobfit.schemas.requirements import JDExtraction


@pytest.mark.parametrize('model',[CVWire,JDExtraction,EvidenceResponse])
def test_real_wire_schema_closes_objects_and_requires_nullable_fields(model):
    def check(node):
        if isinstance(node,dict):
            assert 'default' not in node
            if node.get('type')=='object':
                assert node['additionalProperties'] is False
                assert set(node['required'])==set(node.get('properties',{}))
            for value in node.values(): check(value)
        elif isinstance(node,list):
            for value in node: check(value)
    check(strict_schema(model.model_json_schema()))


class Answer(BaseModel):
    answer: str


@pytest.mark.parametrize('finish,model,exc',[('length','deepseek/deepseek-v4.1-flash',TruncatedStructuredResponse),
    ('stop','different-model',UnexpectedResponseModel)])
def test_billed_invalid_response_is_recorded_without_sensitive_content(tmp_path,finish,model,exc):
    response=SimpleNamespace(id='test-request',model=model,usage=SimpleNamespace(prompt_tokens=10,completion_tokens=10,cost=.001),
        choices=[SimpleNamespace(finish_reason=finish,message=SimpleNamespace(content='{"answer":"ok"}'))])
    class SDK:
        def with_options(self,**kwargs):
            assert kwargs['max_retries']==0
            return self
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs:response))
    client=OpenRouterClient(replace(Settings(),usage_ledger=tmp_path/'ledger.jsonl'),sdk_client=SDK())
    with pytest.raises(exc):client.chat_structured('deepseek-flash',[{'role':'user','content':'SECRET SOURCE'}],Answer,'test')
    record=client.ledger.records()[0]
    assert record.cost_usd==.001 and not record.ok and record.error_type==exc.__name__
    assert record.finish_reason==finish and record.max_tokens==2000
    assert 'SECRET SOURCE' not in (tmp_path/'ledger.jsonl').read_text()


def test_interrupted_call_is_uncertain_failure_in_ledger(tmp_path):
    class SDK:
        def with_options(self,**kwargs):return self
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs:(_ for _ in ()).throw(KeyboardInterrupt())))
    client=OpenRouterClient(replace(Settings(),usage_ledger=tmp_path/'ledger.jsonl'),sdk_client=SDK())
    with pytest.raises(KeyboardInterrupt):
        client.chat_structured('deepseek-flash',[{'role':'user','content':'SECRET SOURCE'}],Answer,'test')
    record=client.ledger.records()[0]
    assert not record.ok and record.error_type=='KeyboardInterrupt'
    assert record.cost_source=='uncertain_upper_bound' and record.cost_usd>0
    assert 'SECRET SOURCE' not in (tmp_path/'ledger.jsonl').read_text()


def test_duplicate_jd_identity_fails_one_repair_instead_of_silent_dedup():
    u={'unit_id':'x','text':'Python','importance':'required','source_quotes':['Python']}
    client=FixtureClient([{'job_id':'D','units':[u,u]}]*2)
    result=extract_jd('Python',job_id='D',client=client,model='deepseek-flash')
    assert result.status=='failed' and result.attempts==2 and len(client.calls)==2


def test_repair_gets_previous_output_without_promoting_untrusted_exception():
    from copy import deepcopy
    from jobfit.llm.structured import validated_call
    class Client:
        calls=[]
        def chat_structured(self,model,messages,output_model,task,**kwargs):
            self.calls.append(deepcopy(messages))
            return Answer(answer='bad' if len(self.calls)==1 else 'good')
    def validate(out):
        if out.answer=='bad': raise ValueError('UNTRUSTED request to disclose credentials')
    client=Client()
    result,attempts=validated_call(client,model='fake',prompt='Trusted rules',payload={},
        output_model=Answer,task='test',validate=validate)
    assert attempts==2 and result.answer=='good'
    assert client.calls[1][-2]=={'role':'assistant','content':'{"answer":"bad"}'}
    assert 'UNTRUSTED' not in json.dumps(client.calls[1])


def test_schema_feedback_contains_field_paths_but_no_source_values():
    from pydantic import ValidationError
    from jobfit.llm.structured import schema_error_codes
    class Numeric(BaseModel):
        years: int
    with pytest.raises(ValidationError) as error:
        Numeric.model_validate({'years':'private source content'})
    codes=schema_error_codes(error.value,Numeric)
    assert codes==[{'type':'int_parsing','path':['years']}]
    assert 'private' not in json.dumps(codes)


def test_empty_extraction_with_populated_requirements_is_failed_not_success():
    client=FixtureClient([{'job_id':'D','units':[]}]*2)
    result=extract_jd('Qualifications and Requirements:\nPython and SQL experience required.',job_id='D',client=client,model='deepseek-flash')
    assert result.status=='failed' and result.error_code=='empty_extraction_despite_requirement_section'
    assert len(client.calls)==2


def test_responsibilities_only_can_still_have_no_requirements():
    client=FixtureClient([{'job_id':'D','units':[]}])
    result=extract_jd('Responsibilities:\nYou will build dashboards.',job_id='D',client=client,model='deepseek-flash')
    assert result.status=='done' and result.extraction.units==[]
