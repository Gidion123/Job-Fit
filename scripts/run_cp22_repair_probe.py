"""Extraction repair v1.3 experiment, one stage per invocation; semantic check gates continuation."""
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'src')]
import argparse,fcntl,hashlib,json,time
from datetime import date
import yaml
from jobfit.config import REPO_ROOT,get_settings,runtime_versions
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.closure_probe import ClosureProbeSession,ClosureProbeClient
from jobfit.extraction.cache import ExtractionCache
from jobfit.extraction.audited import ExtractionSpec
from jobfit.extraction.jd_extractor import extract_jd
from jobfit.extraction.paste_jd import preview_pasted_jd
from jobfit.cv.text_extract import extract_text
from jobfit.cv.parser import parse_cv,ParsedCV
from jobfit.pipeline import compare_pasted_jd,AnalysisContext
from scripts.run_batch_extraction import development_sources
RUN_ID='cp22_extraction_repair_v13_20261003'
STAGES=['F00034','CV1_parse','F00332_paste','CV1_F00332_match']
STATE=REPO_ROOT/'reports/quality_probe'/f'{RUN_ID}.json'
SPEC=ExtractionSpec(REPO_ROOT/'prompts/jd_extraction_v1_3.md','jd-prompt-v1.3')

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group();g.add_argument('--execute',action='store_true');g.add_argument('--record-check',type=Path);a=p.parse_args()
    STATE.parent.mkdir(parents=True,exist_ok=True)
    with STATE.with_suffix('.lock').open('a') as f:
        fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        sources={r['job_id']:r['text'] for r in development_sources(['F00034','F00332'])}
        cv_path=REPO_ROOT/'data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md'
        cfg=yaml.safe_load((REPO_ROOT/'config/pipeline_v1.yaml').read_text())
        paths=['config/models_v1.yaml','config/pipeline_v1.yaml','evals/annotation_guideline_v1_3.md',
               'prompts/jd_extraction_v1_3.md','src/jobfit/extraction/audited.py','src/jobfit/extraction/coverage.py','src/jobfit/extraction/paste_jd.py','prompts/evidence_matching_v1_1.md','prompts/cv_parsing_v1.md',
               'src/jobfit/llm/probe.py','src/jobfit/llm/closure_probe.py','src/jobfit/llm/client.py',
               'src/jobfit/llm/structured.py','src/jobfit/pipeline.py','src/jobfit/cv/parser.py',
               'src/jobfit/extraction/jd_extractor.py','src/jobfit/matching/evidence_matcher.py',
               'scripts/run_cp22_repair_probe.py','evals/results/cp22_repair_reference_compatibility_20261003.json','evals/results/cp22_repair_provider_verification_20261003.json']
        versions=runtime_versions()
        versions.update(jd_prompt_version=SPEC.prompt_version,jd_prompt_file=str(SPEC.prompt_file.relative_to(REPO_ROOT)),jd_prompt_sha256=sha(SPEC.prompt_file.read_bytes()),extraction_coverage_contract=SPEC.coverage_contract)
        hashes={n:sha((REPO_ROOT/n).read_bytes()) for n in paths}
        hashes.update({j:sha(t.encode()) for j,t in sources.items()});hashes['CV1']=sha(cv_path.read_bytes())
        c=OpenRouterClient(get_settings(),run_id=RUN_ID)
        s=ClosureProbeSession(STATE,run_id=RUN_ID,fingerprint=sha(json.dumps(hashes,sort_keys=True).encode()),jobs=STAGES,ledger=c.ledger,ceiling='.40')
        if a.record_check:
            s.record_check(json.loads(a.record_check.read_text()));print(json.dumps({'status':s.data['status'],'spent':str(s.spent())}));return
        if s.data.get('transport_uncertain'):raise ValueError('Uncertain transport receipt requires reconciliation; no retry')
        if s.data['status'] not in {'ready','complete'}:raise ValueError('Probe stopped or waiting for inspection')
        if s.data['status']=='complete':print('Probe complete');return
        stage=STAGES[len(s.data['results'])]
        # Conservative remaining cap from fixed approved plan; per-request checks also enforced.
        bounds={j:.0984 for j in STAGES}  # 2 attempts * (100000 input *.30 +16000 output *1.20)/1M
        remaining=sum(bounds[j] for j in STAGES[len(s.data['results']):])
        s.check_budget(remaining);c.guard.check(remaining)
        print(json.dumps({'stage':stage,'remaining_upper_usd':remaining,'spent':str(s.spent()),'ceiling':'.40','versions':versions,'mode':'execute' if a.execute else 'preflight'}),flush=True)
        if not a.execute:return
        if not c.verify_inference_key()['inference_key']:raise ValueError('Invalid inference key type')
        s.begin(stage);start=time.perf_counter();client=ClosureProbeClient(c,s)
        output={'job_id':stage,'run_id':RUN_ID,'provenance':hashes,'versions':versions}
        cache=ExtractionCache(REPO_ROOT/'reports/extraction_cache')
        try:
            if stage=='F00034':
                r=extract_jd(sources['F00034'],job_id='F00034',client=client,model=cfg['model'],cache=cache,scope='corpus_jd',spec=SPEC)
                output.update(status=r.status,extraction=r.extraction.model_dump(mode='json') if r.extraction else None,attempts=r.attempts,error_code=r.error_code,cache_hit=r.cache_hit,coverage=r.coverage)
            elif stage=='CV1_parse':
                text=extract_text(cv_path.read_bytes(),cv_path.name)
                r=parse_cv(text,cv_id='CV1',analysis_date=date.fromisoformat(cfg['analysis_date']),client=client,model=cfg['model'],is_synthetic=True)
                output.update(status='done' if r.profile.parse_status.value=='ok' else 'failed',parsed_cv=r.model_dump(mode='json'),preview=r.summary(),attempts=r.attempts)
            elif stage=='F00332_paste':
                r=preview_pasted_jd(sources['F00332'],client=client,model=cfg['model'],cache=cache,extraction_spec=SPEC)
                output.update(status=r.result.status,extraction=r.result.extraction.model_dump(mode='json') if r.result.extraction else None,key=r.result.key,attempts=r.result.attempts,error_code=r.result.error_code,cleaned_source_sha256=sha(r.cleaned_text.encode()),coverage=r.result.coverage)
            else:
                parsed=ParsedCV.model_validate(s.data['results'][1]['parsed_cv'])
                prior=s.data['results'][2]
                if any(u.get('needs_review') for u in prior['extraction']['units']):raise ValueError('Unresolved structure forbids dependent paid matching')
                cache.put(prior['key'],{**prior['extraction'],'qualification_coverage':prior['coverage']['inventory_mappings']},scope='session_jd')
                context=AnalysisContext(analysis_date=parsed.analysis_date,parsing_confirmed=True,complete_work_history_confirmed=True)
                r=compare_pasted_jd(parsed,sources['F00332'],context=context,client=client,model=cfg['model'],cache=cache,extraction_spec=SPEC)
                output.update(status='done' if r.status=='done' else 'failed',report=r.model_dump(mode='json'),preview_confirmation='delegated automatic synthetic-fixture check; not production user approval')
        except BaseException as exc:
            output.update(status='failed',error_code=type(exc).__name__)
        output['latency_ms']=int((time.perf_counter()-start)*1000)
        output['result_sha256']=sha(json.dumps(output,sort_keys=True).encode())
        s.finish(output)
        resultfile=REPO_ROOT/'evals/results'/f'{RUN_ID}_{len(s.data["results"]):02d}.json'
        with resultfile.open('x') as out:json.dump(output,out,indent=2)
        print(json.dumps({'stage':stage,'status':s.data['status'],'attempts':output.get('attempts'),'spent':str(s.spent()),'result':str(resultfile)}),flush=True)

if __name__=='__main__':main()
