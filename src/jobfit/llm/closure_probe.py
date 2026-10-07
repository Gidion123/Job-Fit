"""Explicitly authorized v1.3 staged probe; old US$0.20 protocol is unchanged."""
from decimal import Decimal
import json
from jobfit.llm.probe import ProbeSession, ProbeClient
from jobfit.llm.client import strict_schema
from jobfit.llm.budget import BudgetExceeded

class ClosureProbeSession(ProbeSession):
    MAX_CEILING=Decimal('0.40')

class ClosureProbeClient(ProbeClient):
    def chat_structured(self,model,messages,output_model,task,max_tokens=2000,temperature=0):
        s=self.session
        if s.data['status']!='running':raise BudgetExceeded('Probe not running')
        tokens=len(json.dumps(messages,ensure_ascii=False).encode())+len(json.dumps(strict_schema(output_model.model_json_schema())).encode())+512
        if tokens>100000 or max_tokens>16000:raise BudgetExceeded('Approved input/output allowance exceeded')
        counts=s.data.setdefault('stage_attempts',{})
        stage=s.data['active_job']
        if sum(counts.values())>=8 or counts.get(stage,0)>=2:raise BudgetExceeded('Approved attempt limit reached')
        # Prechecks before consuming a slot; persistent count prevents crash retry loops.
        s.check_budget(0)
        counts[stage]=counts.get(stage,0)+1
        s.data.setdefault('request_bounds',[]).append(dict(stage=stage,input_tokens_upper=tokens,max_output_tokens=max_tokens,task=task))
        s.save()
        try:
            return super().chat_structured(model,messages,output_model,task,max_tokens,temperature)
        finally:
            # A transport uncertainty is terminal, even if a ledger upper bound exists.
            rows=[r for r in self.client.ledger.records() if r.run_id==self.client.run_id]
            if rows and rows[-1].cost_source=='uncertain_upper_bound':
                s.data['transport_uncertain']=True;s.save()
