"""Offline, no-inference preflight for four reviewed fixed-input evidence pairs."""
from pathlib import Path
import sys
sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1]/'src')]

from datetime import date
from decimal import Decimal
import hashlib
import json

from jobfit.config import REPO_ROOT
from jobfit.cv.parser import ParsedCV
from jobfit.cv.text_extract import extract_text
from jobfit.eval.fixed_requirements import fixed_reviewed_requirements
from jobfit.eval.run_eval import CV_FILES
from jobfit.llm.client import strict_schema
from jobfit.llm.pricing import load_prices, estimate_cost
from jobfit.llm.structured import STRUCTURED_MAX_TOKENS, REPAIR_CONTEXT_MAX_BYTES
from jobfit.matching.constraints import experience_years
from jobfit.matching.evidence_matcher import match_evidence
from jobfit.schemas.cv import CVProfile
from scripts.run_batch_extraction import development_sources

ROUND1 = ('deepseek-flash', 'gpt-6-luna', 'gemini-3.5-flash-lite', 'claude-haiku-4.5')
OUT = REPO_ROOT/'evals/results/cp23_stage2_matcher_preflight_20261003_v1.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class CaptureNoInference:
    def __init__(self):
        self.messages = None
        self.output_model = None
    def chat_structured(self, model, messages, output_model, task, max_tokens=2000, temperature=0):
        self.messages, self.output_model = messages, output_model
        raise RuntimeError('preflight_no_inference')


def prepare(root=REPO_ROOT):
    root = Path(root)
    manifest = json.loads((root/'evals/results/cp23_stage1_case_candidates_20261003_v4.json').read_text())
    bundle = root/'evals/gold/development_v13_reviewed_20261003_stage1_r3'
    if sha(bundle/'manifest.json') != manifest['gold_manifest_sha256']:
        raise ValueError('Reviewed bundle changed')
    pairs = manifest['pairs']
    if len(pairs) != 4 or {(p['cv_id'], p['job_id']) for p in pairs} != {
            ('CV1','F00332'), ('CV1','F00036'), ('CV2','F00815'), ('CV2','F00018')}:
        raise ValueError('Fixed matcher pair scope changed')
    sources = {r['job_id']: r['text'] for r in development_sources([p['job_id'] for p in pairs])}
    cv1_path = root/'evals/results/cp22_extraction_repair_v13_20261003_02.json'
    cv1_saved = json.loads(cv1_path.read_text())
    cv1 = ParsedCV.model_validate(cv1_saved['parsed_cv'])
    cv_paths = {cv: root/'data/synthetic_cvs'/name for cv, name in CV_FILES.items()}
    cv_text = {cv: extract_text(p.read_bytes(), p.name).text for cv,p in cv_paths.items()}
    if cv1.profile.raw_text != cv_text['CV1'] or cv1.analysis_date != date(2026,9,30):
        raise ValueError('Saved CV1 parse is stale or uses a different date')
    # Matcher-only input is raw synthetic CV text. CV2 has no scoped duration
    # minimum in its two fixed pairs; this fixture does not claim CV2 parsing QA.
    cv2 = ParsedCV(profile=CVProfile(cv_id='CV2',is_synthetic=True,raw_text=cv_text['CV2']),
                   analysis_date=date(2026,9,30))
    cvs = {'CV1':cv1, 'CV2':cv2}
    prices = load_prices(root/'config/models_v1.yaml')
    stages = []
    for model in ROUND1:
        for pair in pairs:
            cv_id,job_id = pair['cv_id'],pair['job_id']
            fixed = fixed_reviewed_requirements(bundle,job_id,sources[job_id])
            durations = {}
            basis = 'not_applicable'
            if (cv_id,job_id) == ('CV1','F00036'):
                upper = experience_years(cv1.profile.experience,cv1.analysis_date)
                if upper is None or upper >= 2:
                    raise ValueError('CV1 all-employment upper bound no longer proves 2-year shortfall')
                durations = {'P09-U02':upper}
                basis = 'all_employment_upper_bound_only; not DS-role tenure; 2026-09-30'
            capture = CaptureNoInference()
            result = match_evidence(cvs[cv_id],fixed,client=capture,model=model,duration_years=durations,cache=None)
            if result.status != 'failed' or capture.messages is None or capture.output_model is None:
                raise ValueError('No-inference capture did not stop at the model boundary')
            first = len(json.dumps(capture.messages,ensure_ascii=False).encode()) + len(json.dumps(strict_schema(capture.output_model.model_json_schema())).encode())+512
            repair = first+REPAIR_CONTEXT_MAX_BYTES+2048
            if repair>100_000:
                raise ValueError('Matcher input exceeds predeclared limit')
            upper_cost = round(estimate_cost(prices[model],first,STRUCTURED_MAX_TOKENS)+estimate_cost(prices[model],repair,STRUCTURED_MAX_TOKENS),9)
            stages.append({'model':model,'model_id':prices[model].model_id,'cv_id':cv_id,'job_id':job_id,
                           'fixed_requirements_sha256':hashlib.sha256(json.dumps(fixed.model_dump(mode='json'),sort_keys=True).encode()).hexdigest(),
                           'cv_sha256':sha(cv_paths[cv_id]),'jd_source_sha256':hashlib.sha256(sources[job_id].encode()).hexdigest(),
                           'duration_input':durations,'duration_basis':basis,'logical_units':len(fixed.units),
                           'or_groups':sum(bool(u.branches) for u in fixed.units),
                           'first_input_token_upper':first,'repair_input_token_upper':repair,
                           'output_token_upper_per_attempt':STRUCTURED_MAX_TOKENS,'max_attempts':2,
                           'conservative_upper_usd':upper_cost})
    return {'schema_version':'cp23-stage2-matcher-preflight-v1','status':'offline_preflight_only',
            'scope':'four reviewed fixed-input CV1/CV2 development pairs x four D-029 models',
            'model_calls':0,'gold_CV_answers_in_payload':False,'gold_version':sha(bundle/'manifest.json'),
            'cv1_saved_parse_sha256':sha(cv1_path),'cv2_status':'raw-text-only matcher fixture; no parser-quality claim',
            'analysis_date':'2026-09-30','attempt_policy':'first and at most one automatic repair, reported separately',
            'stages':stages,'stage_count':len(stages),'maximum_calls_including_repairs':len(stages)*2,
            'conservative_upper_usd':str(sum((Decimal(str(s['conservative_upper_usd'])) for s in stages),Decimal(0))),
            'requires_separate_paid_approval_if_over_usd1':True,'winner':None,
            'limits':['No matching inference performed', 'Shared OR qualifiers use the source-checked fixed adapter',
                      'CV1 scoped duration uses a verified all-employment upper bound only; no technology tenure inference',
                      'A separate guarded executor and provider recheck are required before paid matching']}


if __name__ == '__main__':
    result = prepare()
    with OUT.open('x') as file:
        json.dump(result,file,indent=2)
    print(json.dumps({'status':result['status'],'stages':result['stage_count'],
                      'conservative_upper_usd':result['conservative_upper_usd'],
                      'model_calls':0}))
