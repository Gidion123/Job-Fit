"""Offline eight-fixture evidence and v1.3 probe plan. No execution switch/client."""
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'src')]
import argparse
from decimal import Decimal
import hashlib
import json
import yaml
from jobfit.config import REPO_ROOT, get_settings, runtime_versions, GUIDELINE_FILE, JD_PROMPT_FILE
from jobfit.llm.ledger import UsageLedger
from jobfit.llm.client import strict_schema
from jobfit.llm.structured import STRUCTURED_MAX_TOKENS, REPAIR_CONTEXT_MAX_BYTES
from jobfit.schemas.requirements import JDExtraction
from jobfit.extraction.cache import ExtractionCache
from jobfit.extraction.jd_extractor import extract_jd
from scripts.run_batch_extraction import development_sources
from scripts.run_cp22_example import fixture_results


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    output=a.output.resolve()
    if output.parent!=(REPO_ROOT/'evals/results').resolve() or output.suffix!='.json':raise ValueError('New result JSON only')
    if output.exists():raise ValueError('Preserve historical evidence')
    cfg=yaml.safe_load((REPO_ROOT/'config/pipeline_v1.yaml').read_text())
    price=yaml.safe_load((REPO_ROOT/'config/models_v1.yaml').read_text())['models'][cfg['model']]
    inp=Decimal(str(price['input_per_m']));out=Decimal(str(price['output_per_m']))
    rows=UsageLedger(REPO_ROOT/'reports/usage/usage_ledger.jsonl').records()
    spent=sum((Decimal(str(r.cost_usd)) for r in rows if not r.cached),Decimal(0))
    uncertain=sum((Decimal(str(r.cost_usd)) for r in rows if not r.cached and r.cost_source=='uncertain_upper_bound'),Decimal(0))
    settings=get_settings()
    source={r['job_id']:r['text'] for r in development_sources(['F00034','F00022'])}
    prompt=JD_PROMPT_FILE.read_text()+'\n\n'+GUIDELINE_FILE.read_text()
    schema=json.dumps(strict_schema(JDExtraction.model_json_schema()))
    cache=ExtractionCache(REPO_ROOT/'reports/extraction_cache')
    class NoInference:
        def chat_structured(self,*args,**kwargs):raise RuntimeError('OfflinePreflightOnly')
    stages=[]
    for job,scope in [('F00034','corpus_jd'),('F00022','session_jd')]:
        cached=extract_jd(source[job],job_id=job,client=NoInference(),model=cfg['model'],cache=cache,scope=scope)
        messages=[{'role':'system','content':prompt},{'role':'user','content':json.dumps({'untrusted_document_data':{'job_id':job,'jd_text':source[job]}},ensure_ascii=False)}]
        tokens=len(json.dumps(messages,ensure_ascii=False).encode())+len(schema.encode())+2048+REPAIR_CONTEXT_MAX_BYTES
        cost=Decimal(0) if cached.cache_hit else 2*(tokens*inp+STRUCTURED_MAX_TOKENS*out)/Decimal(1_000_000)
        stages.append({'stage':'jd_extraction','job_id':job,'scope':scope,'cache_hit':cached.cache_hit,
                       'input_token_upper_per_attempt':tokens,'attempts_max':2,'upper_usd':str(cost)})
    # Future matcher payload depends on extracted output. Enforce this input ceiling
    # including schema + repair before sending; refuse rather than exceed the plan.
    for stage in ['cv_parsing','evidence_matching']:
        tokens=100000
        stages.append({'stage':stage,'cv_id':'CV1','job_id':'F00022' if stage=='evidence_matching' else None,
            'scope':'session_only','input_token_upper_per_attempt':tokens,'attempts_max':2,
            'upper_usd':str(2*(tokens*inp+STRUCTURED_MAX_TOKENS*out)/Decimal(1_000_000)),
            'bound_condition':'Future executor must reject actual request+schema+repair byte bound above100000 before dispatch'})
    bound=sum(Decimal(s['upper_usd']) for s in stages)
    result={'mode':'preflight_only','proposed_run_id':'cp22_v13_acceptance_probe_after_closure_20261002',
        'execution_authorized_in_this_session':False,'new_api_calls':0,'session_cost_usd':0,
        'baseline':price['id'],'price_source':'local routing ceilings; last official evidence cp22_probe_provider_20261002.json; reverify before any future paid run',
        'versions':runtime_versions(),'analysis_date':cfg['analysis_date'],'stages':stages,
        'maximum_calls':8,'max_output_tokens_per_call':STRUCTURED_MAX_TOKENS,
        'conservative_upper_usd':str(bound),'proposed_aggregate_ceiling_usd':'0.40',
        'fits_proposed_ceiling':bound<=Decimal('.40'),'ledger_records':len(rows),
        'ledger_total_including_reservations_usd':str(spent),'uncertain_reservation_usd':str(uncertain),
        'hard_stop_usd':str(settings.api_hard_stop_usd),
        'remaining_guard_including_reservation_usd':str(Decimal(str(settings.api_hard_stop_usd))-spent),
        'fits_project_guard':bound+spent<=Decimal(str(settings.api_hard_stop_usd)),
        'source_sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in source.items()},
        'cv_sha256':hashlib.sha256((REPO_ROOT/'data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md').read_bytes()).hexdigest(),
        'sequence':['F00034 extraction; inspect role alternatives/duration/portfolio','CV1 parse preview and confirmation','F00022 pasted extraction; inspect D-049 composite/importance/categories/qualifiers','CV1 x F00022 evidence/report only if structure resolved without new rules'],
        'stop_conditions':['Terminal stage failure after at most one repair','Important semantic error, omitted/invented requirement or source qualifier','Unresolved structure: record hold, stop next paid stage','Aggregate spend+reservations+next conservative estimate exceeds ceiling or project guard','Input bound exceeded or source/prompt/model/config hash changed'],
        'quality_status':'Technical semantic diagnostic only; no compatible whole-JD reviewed gold/alignment receipt yet, no F1',
        'reuse_policy':'No reuse of interrupted started artifact. Public JD cache exact version only; CV/paste/evidence session memory only. Check any approved successful parse reuse by content/schema/prompt/date hashes first; do not silently re-infer.',
        'executor_status':'Plan only. Separate guarded staged executor required before future execution; do not use closed v1.2 driver or ungated full-chain command.',
        'fixture_results':fixture_results(),
        'fixture_sources':{str(p.relative_to(REPO_ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((REPO_ROOT/'evals/fixtures').glob('dev_*.json'))},
        'human_fixture_review_status':'pending','fixture_date_policy':'Preserve original2026-09-29; live development reference remains2026-09-30'}
    with output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['mode','maximum_calls','conservative_upper_usd','fits_proposed_ceiling','ledger_total_including_reservations_usd','uncertain_reservation_usd','remaining_guard_including_reservation_usd','new_api_calls']}))

if __name__=='__main__':main()
