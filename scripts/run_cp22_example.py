"""Development-only synthetic CV1 x pilot J1 example, with preflight by default.

--execute invokes the configured baseline through the existing budget/ledger.
Saved results are synthetic evaluation evidence, not a production CV cache or gold.
No workbook access. No held-out data, tuning, label export, or database mutation.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import argparse
from datetime import date
import hashlib
import json
import re
import yaml

from jobfit.config import REPO_ROOT, get_settings
from jobfit.cv.parser import parse_cv, ParsedCV
from jobfit.extraction.jd_extractor import JD_PROMPT_FILE
from jobfit.cv.text_extract import extract_text
from jobfit.extraction.cache import ExtractionCache
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.structured import STRUCTURED_MAX_TOKENS, schema_error_codes
from pydantic import ValidationError
from jobfit.pipeline import AnalysisContext, compare_pasted_jd
from jobfit.schemas.analysis import UnitAssessment
from jobfit.schemas.cv import ExperienceEntry, ParseStatus
from jobfit.schemas.requirements import JDExtraction
from jobfit.scoring.score import compute_score
from jobfit.matching.constraints import experience_constraint, experience_years


def pilot_jd():
    with (REPO_ROOT/'data/processed/jobs_features.jsonl').open() as f:
        for line in f:
            row=json.loads(line)
            if row['final_cluster_id']=='F00022':
                return row['description_clean']
    raise ValueError('Frozen pilot F00022 source missing')


def fixture_results():
    results = []
    for path in sorted((REPO_ROOT/'evals/fixtures').glob('dev_*.json')):
        row = json.loads(path.read_text())
        ex = JDExtraction.model_validate(row['extraction'])
        assessments = [UnitAssessment.model_validate(a) for a in row['assessments']]
        score = compute_score(ex, assessments, ParseStatus(row['cv_parse_status']))
        years = experience_years([ExperienceEntry.model_validate(e) for e in row['experience']['cv_entries']], date.fromisoformat(row['analysis_date']))
        constraint = experience_constraint(row['experience']['min_years'], years)
        actual = score.model_dump(mode='json') | {'constraint_state': constraint.state.value, 'met_display': score.met_display}
        expected = {k:v for k,v in row['expected'].items() if k!='merged_quotes_for_u1'}
        mismatches = {k:{'expected':v,'actual':actual.get(k)} for k,v in expected.items() if actual.get(k)!=v}
        results.append({'fixture_id':row['fixture_id'],'passed':not mismatches,'mismatches':mismatches,'result':actual})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--resume-cv-from',help='Existing synthetic CV1 result filename under evals/results')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',args.run_id): raise ValueError('Invalid run id')
    output = REPO_ROOT/'evals/results'/f'{args.run_id}.json'
    if output.exists(): raise ValueError('Run artifact already exists; choose a new run id')
    cfg = yaml.safe_load((REPO_ROOT/'config/pipeline_v1.yaml').read_text())
    reference = date.fromisoformat(cfg['analysis_date'])
    cv_path = REPO_ROOT/'evals/fixtures/cp22_uploads/cv1_2_column.pdf'
    source_path = REPO_ROOT/'data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md'
    text = extract_text(cv_path.read_bytes(), cv_path.name)
    canonical = extract_text(source_path.read_bytes(), source_path.name)
    if text.status!='ok' or re.sub(r'\s+','',text.text)!=re.sub(r'\s+','',canonical.text):
        raise ValueError('Synthetic PDF differs from approved development CV1')
    jd = pilot_jd()
    if 'F00022' not in (REPO_ROOT/'evals/splits/dev_job_ids.txt').read_text().splitlines():
        raise ValueError('Pilot job is not development')
    settings = get_settings()
    client = OpenRouterClient(settings,run_id=args.run_id)
    price = client.prices[cfg['model']]
    # A deliberately loose bound includes up to 100k input tokens and the output cap
    # tokens for each of six calls (3 stages, at most one repair per stage).
    bound = 6*(100_000*price.input_per_m+STRUCTURED_MAX_TOKENS*price.output_per_m)/1_000_000
    client.guard.check(bound)
    preflight = {'mode':'live' if args.execute else 'preflight','model':price.model_id,
        'reasoning':price.reasoning,'max_output_tokens':STRUCTURED_MAX_TOKENS,
        'analysis_date':reference.isoformat(),'cv':'CV1','job_id':'F00022','split':'development',
        'maximum_calls':6,'conservative_bound_usd':bound,'ledger_before_usd':client.ledger.total_spent(),
        'remaining_guard_usd':settings.api_hard_stop_usd-client.ledger.total_spent()}
    print(json.dumps(preflight,indent=2),flush=True)
    if bound>1: raise ValueError('Batch over US$1 needs separate user approval')
    if not args.execute: return
    if not client.verify_inference_key()['inference_key']: raise ValueError('Inference key check failed')
    result = {'preflight':preflight,'cv_source_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),
        'pdf_sha256':hashlib.sha256(cv_path.read_bytes()).hexdigest(),
        'jd_sha256':hashlib.sha256(jd.encode()).hexdigest(),'fixture_results':fixture_results(),
        'status':'started','limits':['Synthetic development plumbing check, not a held-out quality metric.',
        'Configured baseline is not selected by tuning. No human label approval is granted.']}
    from jobfit.config import runtime_versions
    result['versions']=runtime_versions()
    result['jd_prompt_file']=JD_PROMPT_FILE.name
    result['jd_prompt_sha256']=hashlib.sha256(JD_PROMPT_FILE.read_bytes()).hexdigest()
    class SyntheticAuditClient:
        # Only this fixed synthetic development harness retains typed wire outputs.
        # Production parsing/matching still has no persistent CV cache.
        def chat_structured(self, *args, **kwargs):
            try:
                out=client.chat_structured(*args, **kwargs)
            except ValidationError as exc:
                schema=kwargs.get('output_model',args[2] if len(args)>2 else None)
                result.setdefault('schema_validation_issues',[]).append(schema_error_codes(exc,schema))
                raise
            result.setdefault('synthetic_wire_outputs',[]).append({
                'task':kwargs.get('task',args[3] if len(args)>3 else None),
                'output':out.model_dump(mode='json')})
            return out
    audit_client=SyntheticAuditClient()
    try:
        if args.resume_cv_from:
            if Path(args.resume_cv_from).name!=args.resume_cv_from: raise ValueError('Use a result filename, not a path')
            old=json.loads((REPO_ROOT/'evals/results'/args.resume_cv_from).read_text())
            if any(old.get(k)!=result[k] for k in ['cv_source_sha256','pdf_sha256']):raise ValueError('CV resume source mismatch')
            cv=ParsedCV.model_validate(old['parsed_cv'])
            if (cv.profile.cv_id!='CV1' or not cv.profile.is_synthetic or cv.analysis_date!=reference
                    or cv.profile.raw_text!=text.text or cv.profile.parse_status.value!='ok'):
                raise ValueError('Only the verified synthetic CV1 parse can be resumed')
            result['cv_resume_source']=args.resume_cv_from
        else:
            cv = parse_cv(text,cv_id='CV1',analysis_date=reference,is_synthetic=True,client=audit_client,model=cfg['model'])
        result['parsed_cv'] = cv.model_dump(mode='json')
        result['parsing_summary'] = cv.summary()
        # The scripted example confirms only the known synthetic employment spans.
        # The user-facing path still requires explicit preview confirmation.
        spans = [(e.title, (e.start_partial.year,e.start_partial.month) if e.start_partial else None,
                  (e.end_partial.year,e.end_partial.month) if e.end_partial else None) for e in cv.profile.experience]
        expected = [('Data Analyst Intern',(2026,2),(2026,5)),('Asisten Praktikum Analisis Regresi',(2025,2),(2025,6))]
        confirmed = cv.profile.parse_status.value=='ok' and sorted(spans)==sorted(expected)
        result['parsing_confirmation'] = {'kind':'synthetic_fixture_check','passed':confirmed,'human_confirmation':False}
        if not confirmed:
            result['status']='parsing_review_required'
        else:
            context=AnalysisContext(reference,parsing_confirmed=True,complete_work_history_confirmed=True)
            report=compare_pasted_jd(cv,jd,context=context,client=audit_client,model=cfg['model'],cache=ExtractionCache())
            result['report']=report.model_dump(mode='json')
            result['status']=report.status
    except Exception as exc:
        result['status']='failed'
        result['error_type']=type(exc).__name__
        raise
    finally:
        rows=[r for r in client.ledger.records() if r.run_id==args.run_id]
        result['calls']=len(rows)
        result['run_cost_usd']=sum(r.cost_usd for r in rows if not r.cached)
        result['ledger_after_usd']=client.ledger.total_spent()
        output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps({k:result[k] for k in ['status','calls','run_cost_usd','ledger_after_usd']},indent=2))
        print('Saved '+str(output.relative_to(REPO_ROOT)))


if __name__=='__main__': main()
