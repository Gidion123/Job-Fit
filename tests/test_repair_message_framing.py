"""Repair roles and retry limits without a provider request."""
from copy import deepcopy
import pytest
from pydantic import BaseModel
from jobfit.llm.structured import validated_call, StageFailure

class Output(BaseModel):
    value: int

@pytest.mark.parametrize('problem', ['application', 'schema'])
def test_first_and_repair_have_one_leading_system_and_user_repair(problem):
    calls=[]
    class Fake:
        def chat_structured(self, model, messages, output_model, task, **kwargs):
            calls.append(deepcopy(messages))
            if len(calls)==1:
                if problem=='schema':
                    return output_model.model_validate({'value':'invalid'})
                return Output(value=0)
            return Output(value=1)
    def validate(out):
        if out.value==0: raise ValueError('invalid_source_quote')
    out,attempts=validated_call(Fake(),model='fixture',prompt='fixed rules',payload={'text':'fixture'},
        output_model=Output,task='fixture',validate=validate)
    assert out.value==1 and attempts==2
    for messages in calls:
        assert [i for i,m in enumerate(messages) if m['role']=='system']==[0]
        assert messages[0]['content']=='fixed rules'
    assert calls[1][-1]['role']=='user'
    assert calls[1][-1]['content'].startswith('The previous response failed validation (')
    if problem=='application':
        assert calls[1][-2]=={'role':'assistant','content':'{"value":0}'}
    else:
        assert 'Schema errors (field paths only)' in calls[1][-1]['content']

def test_repair_failure_never_dispatches_third_call():
    calls=[]
    class Fake:
        def chat_structured(self,model,messages,output_model,task,**kwargs):
            calls.append(deepcopy(messages));return Output(value=0)
    def validate(out):raise ValueError('invalid_source_quote')
    with pytest.raises(StageFailure) as error:
        validated_call(Fake(),model='fixture',prompt='rules',payload={},output_model=Output,
            task='fixture',validate=validate)
    assert len(calls)==2 and error.value.attempts==2
    assert error.value.code=='invalid_source_quote'
    assert [m['role'] for m in calls[1]]==['system','user','assistant','user']

def test_eight_historical_repairs_are_reconstructible_but_over_cap():
    from scripts.prepare_cp23_repair_rerun import prepare
    from decimal import Decimal
    report=prepare()
    assert len(report['stages'])==8 and report['api_calls']==0
    assert report['status']=='blocked_aggregate_cost_cap'
    assert Decimal(report['conservative_upper_usd']) > Decimal(report['cap_usd'])
    assert all(row['repair_roles']==['system','user','assistant','user'] for row in report['stages'])
    assert report['stages'][-1]['first_trigger']=='qualification_inventory_unsupported_mapping'
