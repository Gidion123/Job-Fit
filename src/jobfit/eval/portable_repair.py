"""Experimental portable repair framing; not the active request adapter.

Moves only an application-generated repair instruction into the original system
message. Model/source content remains user/assistant data. First calls unchanged.
This is a compatibility proposal, not a proven diagnosis of historical HTTP400.
"""
from copy import deepcopy
from types import SimpleNamespace

REPAIR_PREFIX='The previous response failed validation ('

def portable_messages(messages):
    out=deepcopy(messages)
    if len(out)<3 or out[-1].get('role')!='system':return out
    instruction=out[-1].get('content','')
    if (out[0].get('role')!='system' or not isinstance(instruction,str)
        or not instruction.startswith(REPAIR_PREFIX) or len(instruction.encode())>2048
        or any(m.get('role')=='system' for m in out[1:-1])):
        raise ValueError('Only bounded application repair messages may be reframed')
    # Never concatenate source data or the assistant response into system text.
    out[0]['content']+='\n\n'+instruction
    out.pop()
    if out[-1]['role']=='assistant':
        out.append({'role':'user','content':'Return the complete corrected structured result under the system validation instructions.'})
    return out

class PortableSDKAdapter:
    def __init__(self,sdk):
        self.sdk=sdk
        self.chat=SimpleNamespace(completions=SimpleNamespace(create=self.create))
    def with_options(self,**kwargs):return type(self)(self.sdk.with_options(**kwargs))
    def get(self,*args,**kwargs):return self.sdk.get(*args,**kwargs)
    def create(self,**kwargs):
        kwargs=dict(kwargs);kwargs['messages']=portable_messages(kwargs['messages'])
        # Public 3-Oct metadata for every GPT Sol endpoint omits temperature.
        # The adapter applies only to this explicitly named reference model.
        if kwargs.get('model')=='openai/gpt-6-sol':kwargs.pop('temperature',None)
        return self.sdk.chat.completions.create(**kwargs)
