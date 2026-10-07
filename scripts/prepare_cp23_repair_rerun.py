"""Offline repair-only preflight. Never dispatches a provider call."""
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'src')]
import json,hashlib,re
from copy import deepcopy
from decimal import Decimal
from jobfit.config import REPO_ROOT as ROOT
from jobfit.llm.client import strict_schema
from jobfit.llm.pricing import load_prices
from jobfit.matching.evidence_matcher import match_evidence
from jobfit.extraction.jd_extractor import extract_jd
from jobfit.extraction.audited import ExtractionSpec
from scripts.run_cp23_stage2_matching import PLAN,STATE,inputs
from scripts.run_batch_extraction import development_sources
RUN='cp23_stage2_repair_rerun_20261004_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(o):return hashlib.sha256(json.dumps(o,sort_keys=True).encode()).hexdigest()
class Capture:
    def __init__(self,draft):self.draft=draft;self.calls=[]
    def chat_structured(self,model,messages,output_model,task,**kwargs):
        self.calls.append((deepcopy(messages),output_model,kwargs))
        if len(self.calls)==1:return output_model.model_validate(self.draft)
        raise RuntimeError('offline_capture_no_network')
def prepare():
    metric=read(ROOT/'evals/results/cp23_stage2_round1_quality_evaluation_20261003_v1.json')
    for p in [PLAN,STATE]:
        if sha(p)!=metric['hashes'][str(p.relative_to(ROOT))]:raise ValueError('Historical matching plan/state changed')
    plan,state=read(PLAN),read(STATE);stages={s['stage_id']:s for s in plan['stages']}
    prices=load_prices(ROOT/'config/models_v1.yaml');rows=[];excluded=[]
    def capture_row(stage,draft,cap,provenance):
        if len(cap.calls)!=2:raise ValueError('Expected failed saved first draft and repair')
        messages,schema,kwargs=cap.calls[-1]
        if [m['role'] for m in messages]!=['system','user','assistant','user']:
            raise ValueError('Saved assistant draft absent or invalid framing; not replayable')
        price=prices[stage['model']];out=kwargs['max_tokens']
        n=len(json.dumps(messages,ensure_ascii=False).encode())+len(json.dumps(strict_schema(schema.model_json_schema())).encode())+512
        cost=(Decimal(n)*Decimal(str(price.input_per_m))+Decimal(out)*Decimal(str(price.output_per_m)))/Decimal(1000000)
        rows.append(dict(stage_id=stage['stage_id'],model_id=price.model_id,draft_sha256=digest(draft),
            hash_provenance=provenance,repair_roles=[m['role'] for m in messages],
            repair_messages_sha256=digest(messages),schema_sha256=digest(strict_schema(schema.model_json_schema())),
            first_trigger=re.search(r'validation \(([^)]+)\)',messages[-1]['content']).group(1),
            input_upper=n,output_upper=out,input_per_m=price.input_per_m,output_per_m=price.output_per_m,
            upper_usd=str(cost),status='replayable_but_budget_blocked'))
    for result in state['results']:
        if result['status']!='failed':
            excluded.append(dict(stage_id=result['stage_id'],reason='Succeeded; replay prohibited'));continue
        if result['error_code']!='BadRequestError' or result['attempts']!=2:
            excluded.append(dict(stage_id=result['stage_id'],reason='Not a rejected repair'));continue
        stage=stages[result['stage_id']]
        draft=next(a['output'] for a in state['typed_attempt_outputs'] if a['stage_id']==stage['stage_id'] and a['attempt']==1)
        cv,ex=inputs(stage);cap=Capture(draft)
        match_evidence(cv,ex,client=cap,model=stage['model'],duration_years=stage['duration_input'])
        capture_row(stage,draft,cap,{'container':str(STATE.relative_to(ROOT)),'container_sha256':sha(STATE),
            'receipt':'original quality evaluation hashes bind the complete state including first drafts'})
    path=ROOT/'reports/quality_probe/cp23_stage2_round1_extraction_20261003_v6_route_repair.json'
    exstate=read(path);res=exstate['results'][-1]
    if (res['job_id'],res['error_code'],res['attempts'])!=('gemini-3.5-flash-lite/F00815','BadRequestError',2):raise ValueError('Extraction failure differs')
    a=next(a for a in exstate['typed_attempt_outputs'] if a['stage_id']==res['job_id'] and a['attempt']==1)
    if digest(a['output'])!=a['output_sha256']:raise ValueError('Extraction draft hash mismatch')
    cap=Capture(a['output']);text=development_sources(['F00815'])[0]['text']
    spec=ExtractionSpec(ROOT/'prompts/jd_extraction_v1_4_experimental.md','jd-prompt-v1.4-experimental')
    extract_jd(text,job_id='F00815',client=cap,model=res['model'],spec=spec)
    capture_row({'stage_id':res['job_id'],'model':res['model']},a['output'],cap,
        {'container':str(path.relative_to(ROOT)),'container_sha256':sha(path),'recorded_output_sha256':a['output_sha256']})
    ledger=[json.loads(l) for l in (ROOT/'reports/usage/usage_ledger.jsonl').read_text().splitlines() if l.strip()]
    total=sum((Decimal(str(r['cost_usd'])) for r in ledger if not r.get('cached')),Decimal(0))
    upper=sum((Decimal(r['upper_usd']) for r in rows),Decimal(0))
    return dict(run_id=RUN,status='blocked_aggregate_cost_cap',api_calls=0,cap_usd='0.30',
        conservative_upper_usd=str(upper),ledger_before_usd=str(total),project_remaining_usd=str(Decimal('8.50')-total),
        stages=rows,excluded=excluded,prices='Unchanged project request price ceilings; no live provider check or dispatch',
        budget_reason='All eight unchanged repairs do not fit the approved aggregate worst-case cap. No token limit reduction or subset selection authorized.',
        ledger_sha256=sha(ROOT/'reports/usage/usage_ledger.jsonl'))
if __name__=='__main__':
    result=prepare()
    with (ROOT/'evals/results'/f'{RUN}_plan.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))
