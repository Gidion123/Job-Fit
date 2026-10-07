from copy import deepcopy
import pytest
from pydantic import BaseModel
from scripts.run_cp23_repair_rerun import Replay,digest,strict_schema
class Output(BaseModel):value:int
class Fake:
    def __init__(self):self.calls=0
    def chat_structured(self,*args,**kw):self.calls+=1;return Output(value=2)
def setup():
    messages=[{'role':'system','content':'rules'},{'role':'user','content':'source'},{'role':'assistant','content':'draft'},{'role':'user','content':'repair'}]
    expected={'repair_messages_sha256':digest(messages),'schema_sha256':digest(strict_schema(Output.model_json_schema())),'output_upper':16000}
    fake=Fake();return Replay({'value':1},expected,fake),fake,messages

def test_first_is_local_repair_only_once():
    replay,fake,messages=setup()
    assert replay.chat_structured('m',messages[:2],Output,'task',max_tokens=16000).value==1
    assert fake.calls==0
    assert replay.chat_structured('m',messages,Output,'task',max_tokens=16000).value==2
    with pytest.raises(RuntimeError):replay.chat_structured('m',messages,Output,'task',max_tokens=16000)
    assert fake.calls==1

@pytest.mark.parametrize('change',['prompt','limit'])
def test_changed_repair_cannot_dispatch(change):
    replay,fake,messages=setup();replay.chat_structured('m',messages[:2],Output,'task',max_tokens=16000)
    if change=='prompt':messages[0]['content']='different'
    with pytest.raises(RuntimeError):replay.chat_structured('m',messages,Output,'task',max_tokens=15999 if change=='limit' else 16000)
    assert fake.calls==0
