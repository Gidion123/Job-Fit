"""D-064 reference/round-two experiment. Default zero-call preflight.

New plan/state only; never reset old failures. Settled failures are observations.
Unknown costs, source drift and interrupted requests stop further dispatch.
"""
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'src')]
import argparse,hashlib,json,time,fcntl
from dataclasses import replace
from decimal import Decimal
from jobfit.config import REPO_ROOT,get_settings
from jobfit.llm.client import OpenRouterClient,strict_schema
from jobfit.llm.probe import ProbeClient,ProbeSession
from jobfit.llm.budget import BudgetExceeded
from jobfit.eval.portable_repair import portable_messages,PortableSDKAdapter
from jobfit.extraction.audited import ExtractionSpec
from jobfit.extraction.jd_extractor import extract_jd
from jobfit.matching.evidence_matcher import match_evidence
from scripts.run_batch_extraction import development_sources
from scripts.run_cp23_stage2_matching import inputs

RUN='cp23_stage2_reference_round2_20261003_v1'
PROPOSAL=REPO_ROOT/'evals/results/cp23_stage2_reference_round2_proposal_20261003_v2.json'
PLAN=REPO_ROOT/'evals/results'/f'{RUN}_plan.json'
APPROVAL=REPO_ROOT/'evals/results'/f'{RUN}_approval.json'
STATE=REPO_ROOT/'reports/quality_probe'/f'{RUN}.json'
SPEC=ExtractionSpec(REPO_ROOT/'prompts/jd_extraction_v1_4_experimental.md','jd-prompt-v1.4-experimental')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def execution_plan():
    p=json.loads(PROPOSAL.read_text())
    for path,digest in p['source_hashes'].items():
        if sha(REPO_ROOT/path)!=digest:raise ValueError('Approved source/protocol changed: '+path)
    metadata=json.loads((REPO_ROOT/'evals/results/cp23_stage2_followup_provider_preflight_20261003_v1.json').read_text())
    aliases={}
    for model,response in metadata.items():
        eps=response['data']['endpoints']
        aliases[model]=sorted({e['name'].split(' | ',1)[1] for e in eps if ' | ' in e['name']})
        price=p['prices']['gpt-6-sol' if model=='openai/gpt-6-sol' else 'deepseek-v4-pro']
        eligible=[e for e in eps if 'structured_outputs' in e['supported_parameters']
            and Decimal(e['pricing']['prompt'])*1_000_000<=Decimal(str(price['input_per_m']))
            and Decimal(e['pricing']['completion'])*1_000_000<=Decimal(str(price['output_per_m']))]
        if not eligible:raise ValueError('No verified structured endpoint within the frozen price ceiling')
        if model=='openai/gpt-6-sol' and any('temperature' in e['supported_parameters'] for e in eps):
            raise ValueError('Reference temperature adaptation no longer matches the inspected metadata')
    files=['scripts/run_cp23_stage2_followup.py','src/jobfit/eval/portable_repair.py',
        'src/jobfit/llm/client.py','src/jobfit/llm/probe.py','src/jobfit/llm/structured.py',
        'src/jobfit/extraction/jd_extractor.py','src/jobfit/matching/evidence_matcher.py',
        'src/jobfit/eval/fixed_requirements.py','scripts/run_cp23_stage2_matching.py']
    return dict(p,run_id=RUN,proposal_sha256=sha(PROPOSAL),response_model_aliases=aliases,
        code_hashes={f:sha(REPO_ROOT/f) for f in files},status='frozen_preflight_only',
        actual_inference_calls=0,approval_required=True,
        executor_note='Implementation of the approved 19-stage scope; public exact dated aliases only, no fuzzy matching')

class FollowupClient(OpenRouterClient):
    def __init__(self,*args,aliases,**kwargs):
        super().__init__(*args,**kwargs)
        for name in ['gpt-6-sol','deepseek-v4-pro']:
            old=self.prices[name];new=replace(old,response_model_aliases=tuple(aliases[old.model_id]))
            self.prices[name]=self.prices[old.model_id]=new
    @property
    def sdk(self):return PortableSDKAdapter(super().sdk)

class FollowupSession(ProbeSession):
    MAX_CEILING=Decimal('6.40')
    def finish_case(self,result):
        if self.data['status']!='running' or result['stage_id']!=self.data['active_job']:
            raise ValueError('Unexpected follow-up result')
        if self.data['reservations'] or self.data.get('transport_uncertain'):
            self.data['status']='stopped_uncertain_cost';self.save();return
        self.data['results'].append(result)
        self.data['status']='complete' if len(self.data['results'])==len(self.data['jobs']) else 'ready'
        self.save()

class FollowupStageClient(ProbeClient):
    def __init__(self,client,session,stage):super().__init__(client,session);self.stage=stage
    def chat_structured(self,model,messages,output_model,task,max_tokens=2000,temperature=0):
        s=self.session;stage=self.stage
        if s.data['status']!='running' or s.data['active_job']!=stage['stage_id']:
            raise ValueError('Unbound stage')
        expected='jd_extraction' if stage['kind']=='extraction' else 'evidence_matching'
        if model!=stage['model'] or task!=expected or max_tokens!=16000 or temperature!=0:
            raise ValueError('Request differs from the accepted protocol')
        attempts=s.data.setdefault('stage_attempts',{});n=attempts.get(stage['stage_id'],0)
        if n>=2:raise BudgetExceeded('One repair maximum')
        wire=portable_messages(messages)
        size=len(json.dumps(wire,ensure_ascii=False).encode())+len(json.dumps(strict_schema(output_model.model_json_schema())).encode())+512
        bound=stage['first_input_token_upper'] if n==0 else stage['repair_input_token_upper']
        if size>bound:raise BudgetExceeded('Input exceeds frozen stage bound')
        attempts[stage['stage_id']]=n+1;s.save()
        before=len([r for r in self.client.ledger.records() if r.run_id==RUN])
        try:
            out=super().chat_structured(model,wire,output_model,task,max_tokens,temperature)
            s.data.setdefault('typed_attempt_outputs',[]).append(dict(stage_id=stage['stage_id'],attempt=n+1,
                output=out.model_dump(mode='json'),status='typed_draft_not_semantically_approved'))
            s.save();return out
        finally:
            rows=[r for r in self.client.ledger.records() if r.run_id==RUN]
            if len(rows)<=before or rows[-1].cost_source=='uncertain_upper_bound':
                s.data.update(status='stopped_uncertain_cost',transport_uncertain=True);s.save()

def require_approval(plan):
    r=json.loads(APPROVAL.read_text())
    if (r.get('decision_id'),r.get('approved_by'),r.get('plan_sha256'),r.get('ceiling_usd'))!=('D-064','Dion',sha(PLAN),'6.40'):
        raise ValueError('Exact follow-up approval required')
    if r.get('proposal_sha256')!=sha(PROPOSAL):raise ValueError('Approved proposal changed')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--stages',type=int,default=1);args=p.parse_args()
    if not 1<=args.stages<=19:raise ValueError('Invalid stage count')
    plan=execution_plan()
    if PLAN.exists():
        if json.loads(PLAN.read_text())!=plan:raise ValueError('Frozen follow-up plan changed')
    else:
        with PLAN.open('x') as f:json.dump(plan,f,indent=2)
    print(json.dumps(dict(status='preflight',stages=19,max_calls=38,bound=plan['conservative_upper_usd'],cap='6.40')),flush=True)
    if not args.execute:return
    require_approval(plan);STATE.parent.mkdir(parents=True,exist_ok=True)
    with STATE.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        client=FollowupClient(get_settings(),run_id=RUN,aliases=plan['response_model_aliases'])
        session=FollowupSession(STATE,run_id=RUN,fingerprint=sha(PLAN),jobs=[s['stage_id'] for s in plan['stages']],ledger=client.ledger,ceiling='6.40')
        if session.data['status'] not in ['ready','complete'] or session.data.get('transport_uncertain'):
            raise ValueError('Interrupted/uncertain request requires reconciliation, not redispatch')
        if session.data['status']=='complete':return
        remaining=sum((Decimal(str(s['conservative_upper_usd'])) for s in plan['stages'][len(session.data['results']):]),Decimal(0))
        session.check_budget(remaining);client.guard.check(float(remaining))
        if not client.verify_inference_key()['inference_key']:raise ValueError('Inference key is not ordinary')
        for _ in range(args.stages):
            if session.data['status']!='ready':break
            if execution_plan()!=plan:raise ValueError('Approved inputs/code changed')
            stage=plan['stages'][len(session.data['results'])]
            wrapper=FollowupStageClient(client,session,stage);session.begin(stage['stage_id']);start=time.perf_counter()
            base=dict(stage_id=stage['stage_id'],model=stage['model'],kind=stage['kind'],job_id=stage['job_id'])
            if stage['kind']=='extraction':
                text=development_sources([stage['job_id']])[0]['text']
                if hashlib.sha256(text.encode()).hexdigest()!=stage['source_sha256']:raise ValueError('Source changed')
                out=extract_jd(text,job_id=stage['job_id'],client=wrapper,model=stage['model'],cache=None,scope='corpus_jd',spec=SPEC)
                base.update(extraction=out.extraction.model_dump(mode='json') if out.extraction else None,coverage=out.coverage,prompt_version=SPEC.prompt_version)
            else:
                cv,ex=inputs(stage)
                out=match_evidence(cv,ex,client=wrapper,model=stage['model'],duration_years=stage['duration_input'],cache=None)
                base.update(cv_id=stage['cv_id'],assessments=[a.model_dump(mode='json') for a in out.assessments],fixed_requirements_sha256=stage['fixed_requirements_sha256'])
            base.update(status=out.status,attempts=out.attempts,error_code=out.error_code,stage_wall_ms=round((time.perf_counter()-start)*1000),semantic_review='pending',metrics=None)
            path=REPO_ROOT/'evals/results'/f'{RUN}_{len(session.data["results"])+1:02d}.json'
            with path.open('x') as f:json.dump(base,f,indent=2,ensure_ascii=False)
            base.update(result_file=str(path.relative_to(REPO_ROOT)),result_sha256=sha(path));session.finish_case(base)
            print(json.dumps({k:base[k] for k in ['stage_id','status','attempts','error_code']}),flush=True)
        print(json.dumps(dict(status=session.data['status'],completed=len(session.data['results']),spent_usd=str(session.spent()))),flush=True)

if __name__=='__main__':main()
