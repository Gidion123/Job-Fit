"""D-064 addendum: one repair replay per frozen saved draft, no fresh first call."""
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'src')]
import json,time,fcntl
from decimal import Decimal
from scripts.prepare_cp23_repair_rerun import ROOT,RUN,read,sha,digest,prepare
from scripts.run_cp23_stage2_matching import PLAN,STATE,inputs
from scripts.run_batch_extraction import development_sources
from jobfit.config import get_settings
from jobfit.llm.client import OpenRouterClient,strict_schema
from jobfit.llm.probe import ProbeSession,ProbeClient
from jobfit.matching.evidence_matcher import match_evidence
from jobfit.extraction.jd_extractor import extract_jd
from jobfit.extraction.audited import ExtractionSpec

class ReplaySession(ProbeSession):MAX_CEILING=Decimal('0.65')
class Replay:
    def __init__(self,draft,expected,client):self.draft=draft;self.expected=expected;self.client=client;self.calls=0;self.returned=None;self.failure=None
    def chat_structured(self,model,messages,output_model,task,**kw):
        self.calls+=1
        if self.calls==1:return output_model.model_validate(self.draft)
        if self.calls!=2:raise RuntimeError('Replay permits only one network attempt')
        if digest(messages)!=self.expected['repair_messages_sha256'] or digest(strict_schema(output_model.model_json_schema()))!=self.expected['schema_sha256']:
            raise RuntimeError('Request fingerprint changed')
        if kw.get('max_tokens')!=self.expected['output_upper']:raise RuntimeError('Token limit changed')
        try:
            out=self.client.chat_structured(model,messages,output_model,task,**kw)
            self.returned=out.model_dump(mode='json');return out
        except Exception as exc:
            self.failure=type(exc).__name__;raise

def main():
    approval_path=ROOT/'evals/results'/f'{RUN}_approval.json';approval=read(approval_path)
    original=ROOT/'evals/results'/f'{RUN}_plan.json';plan=read(original)
    if approval['plan_sha256']!=sha(original) or approval['approved_by']!='Dion' or approval['cap_usd']!='0.65':raise ValueError('Exact approval required')
    for p,h in approval['execution_hashes'].items():
        if sha(ROOT/p)!=h:raise ValueError('Execution input changed: '+p)
    if prepare()['stages']!=plan['stages']:raise ValueError('Reconstructed stages changed')
    raw=OpenRouterClient(get_settings(),run_id=RUN)
    state=ROOT/'reports/quality_probe'/f'{RUN}.json'
    with state.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        session=ReplaySession(state,run_id=RUN,fingerprint=sha(approval_path),jobs=[r['stage_id'] for r in plan['stages']],ledger=raw.ledger,ceiling='0.65')
        if session.data['status'] not in ['ready','complete']:raise ValueError('Interrupted or stopped state: no redispatch')
        remaining=sum(Decimal(s['upper_usd']) for s in plan['stages'][len(session.data['results']):])
        session.check_budget(remaining);raw.guard.check(float(remaining))
        print(json.dumps({'stages':plan['stages'],'remaining_upper_usd':str(remaining),'spent_usd':str(session.spent()),'cap_usd':'0.65'}),flush=True)
        if not raw.verify_inference_key()['inference_key']:raise ValueError('Inference key type not verified')
        matching=read(STATE);stages={s['stage_id']:s for s in read(PLAN)['stages']}
        for expected in plan['stages'][len(session.data['results']):]:
            for p,h in approval['execution_hashes'].items():
                if sha(ROOT/p)!=h:raise ValueError('Frozen input changed')
            sid=expected['stage_id'];session.begin(sid);begin=time.perf_counter()
            if sid in stages:
                s=stages[sid];draft=next(a['output'] for a in matching['typed_attempt_outputs'] if a['stage_id']==sid and a['attempt']==1)
                cv,ex=inputs(s);replay=Replay(draft,expected,ProbeClient(raw,session))
                out=match_evidence(cv,ex,client=replay,model=s['model'],duration_years=s['duration_input'])
                payload={'assessments':[a.model_dump(mode='json') for a in out.assessments]}
            else:
                old=read(ROOT/expected['hash_provenance']['container'])
                draft=next(a['output'] for a in old['typed_attempt_outputs'] if a['stage_id']==sid and a['attempt']==1)
                replay=Replay(draft,expected,ProbeClient(raw,session))
                out=extract_jd(development_sources(['F00815'])[0]['text'],job_id='F00815',client=replay,model='gemini-3.5-flash-lite',
                    spec=ExtractionSpec(ROOT/'prompts/jd_extraction_v1_4_experimental.md','jd-prompt-v1.4-experimental'))
                payload={'extraction':out.extraction.model_dump(mode='json') if out.extraction else None}
            ledger=[r for r in raw.ledger.records() if r.run_id==RUN]
            unknown=bool(replay.failure and replay.failure not in ['ValidationError','JSONDecodeError','IncompleteStructuredResponse'])
            if ledger and ledger[-1].cost_source=='uncertain_upper_bound':unknown=True
            result=dict(stage_id=sid,status=out.status,error_code=out.error_code,attempts=1,original_first_reused=True,
                typed_repair=replay.returned,stage_wall_ms=round((time.perf_counter()-begin)*1000),
                draft_sha256=expected['draft_sha256'],semantic_review='pending',transport_or_unknown_failure=unknown,**payload)
            p=ROOT/'evals/results'/f'{RUN}_{len(session.data["results"])+1:02d}.json'
            with p.open('x') as f:json.dump(result,f,indent=2,ensure_ascii=False)
            session.data['results'].append({**result,'result_file':str(p.relative_to(ROOT)),'result_sha256':sha(p)})
            session.data['status']='stopped_unknown_failure' if unknown else ('complete' if len(session.data['results'])==8 else 'ready')
            session.save()
            print(json.dumps({'stage_id':sid,'status':out.status,'error':out.error_code,'spent_usd':str(session.spent())}),flush=True)
            if unknown:break
        summary={'run_id':RUN,'status':session.data['status'],'stages':len(session.data['results']),'cost_usd':str(session.spent()),'cap_usd':'0.65','api_calls':len([r for r in raw.ledger.records() if r.run_id==RUN])}
        with (ROOT/'evals/results'/f'{RUN}_summary.json').open('x') as f:json.dump(summary,f,indent=2)
        print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
