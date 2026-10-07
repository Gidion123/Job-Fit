"""Frozen development extraction round; no model call from this module.

The plan uses the same seven JD texts, experimental prompt, guideline, wire
schema and attempt policy for all four D-029 round-one candidates. It uses
UTF-8 byte counts (an upper token bound for ordinary text) and the registry
routing ceilings, including one possible automatic repair per case.
"""
from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path

from jobfit.extraction.audited import AuditedExtraction, qualification_inventory_v1
from jobfit.llm.client import strict_schema
from jobfit.llm.pricing import estimate_cost, load_prices
from jobfit.llm.probe import ProbeClient, ProbeSession
from jobfit.llm.budget import BudgetExceeded
from jobfit.llm.structured import STRUCTURED_MAX_TOKENS, REPAIR_CONTEXT_MAX_BYTES

ROUND1 = ('deepseek-flash', 'gpt-6-luna', 'gemini-3.5-flash-lite', 'claude-haiku-4.5')
REPAIR_OVERHEAD_BYTES = REPAIR_CONTEXT_MAX_BYTES + 2048


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_plan(root: Path, sources: dict[str, str], *, run_id: str,
               prompt_file: str = 'prompts/jd_extraction_v1_3.md') -> dict:
    root = Path(root)
    cases_path = root/'evals/results/cp23_stage1_case_candidates_20261003_v4.json'
    ready_path = root/'evals/results/cp23_stage1_readiness_20261003_v4.json'
    bundle = root/'evals/gold/development_v13_reviewed_20261003_stage1_r3/manifest.json'
    cases = json.loads(cases_path.read_text())
    ready = json.loads(ready_path.read_text())
    if ready.get('status') != 'ready' or set(ready.get('gates', {}).values()) != {True}:
        raise ValueError('Stage-1 prerequisites are not all ready')
    if sha(bundle) != cases['gold_manifest_sha256'] or sha(bundle) != ready['receipts']['gold_manifest_sha256']:
        raise ValueError('Current reviewed gold differs from Stage-1 receipts')
    if sha(root/'data/processed/jobs_features.jsonl') != cases['source_corpus_sha256'] or sha(root/'evals/splits/dev_job_ids.txt') != cases['development_split_sha256']:
        raise ValueError('Frozen development corpus or split differs from Stage-1 case receipt')
    ids = [case['job_id'] for case in cases['cases']]
    if len(ids) != 7 or len(set(ids)) != 7 or set(sources) != set(ids):
        raise ValueError('Exactly the seven frozen development JD sources are required')
    for case in cases['cases']:
        if hashlib.sha256(sources[case['job_id']].encode()).hexdigest() != case['source_sha256']:
            raise ValueError('Development JD source changed')
    model_path = root/'config/models_v1.yaml'
    if prompt_file not in {'prompts/jd_extraction_v1_3.md', 'prompts/jd_extraction_v1_4_experimental.md'}:
        raise ValueError('Only explicitly versioned experimental JD prompts are allowed')
    prompt_path = root/prompt_file
    guide_path = root/'evals/annotation_guideline_v1_3.md'
    prices = load_prices(model_path)
    schema = strict_schema(AuditedExtraction.model_json_schema())
    prompt = prompt_path.read_text()+'\n\n'+guide_path.read_text()
    stages = []
    for model in ROUND1:
        for job_id in ids:
            payload = {'job_id': job_id, 'jd_text': sources[job_id],
                       'qualification_inventory': qualification_inventory_v1(sources[job_id])}
            messages = [{'role': 'system', 'content': prompt},
                        {'role': 'user', 'content': json.dumps({'untrusted_document_data': payload}, ensure_ascii=False)}]
            first = len(json.dumps(messages, ensure_ascii=False).encode())+len(json.dumps(schema).encode())+512
            repair = first+REPAIR_OVERHEAD_BYTES
            if repair > 100_000:
                raise ValueError('Case exceeds predeclared repair input limit')
            price = prices[model]
            upper = round(estimate_cost(price, first, STRUCTURED_MAX_TOKENS)+estimate_cost(price, repair, STRUCTURED_MAX_TOKENS), 9)
            stages.append({'stage_id': f'{model}/{job_id}', 'model': model, 'model_id': price.model_id,
                           'job_id': job_id, 'source_sha256': hashlib.sha256(sources[job_id].encode()).hexdigest(),
                           'first_input_token_upper': first, 'repair_input_token_upper': repair,
                           'output_token_upper_per_attempt': STRUCTURED_MAX_TOKENS,
                           'max_attempts': 2, 'conservative_upper_usd': upper})
    bound = sum(Decimal(str(s['conservative_upper_usd'])) for s in stages)
    return {'schema_version': 'cp23-stage2-extraction-plan-v1', 'run_id': run_id,
            'scope': 'development_only; four D-029 round-one models x seven fixed JDs; extraction stage only',
            'comparison_protocol': f'same JD source and {prompt_file}; first attempt and automatic repair reported separately',
            'prompt_status': 'experimental_not_default_or_selected', 'prompt_file': prompt_file,
            'model_reference_status': 'GPT-6 Sol deferred; requires separate guard/price and hard-case plan',
            'execution_status': 'preflight_only', 'paid_approval_required': True,
            'source_hashes': {'case_manifest': sha(cases_path), 'stage1_readiness': sha(ready_path),
                              'gold_manifest': sha(bundle), 'model_registry': sha(model_path),
                              'pipeline_config': sha(root/'config/pipeline_v1.yaml'),
                              'jd_prompt': sha(prompt_path), 'guideline': sha(guide_path),
                              'source_corpus': sha(root/'data/processed/jobs_features.jsonl'),
                              'split': sha(root/'evals/splits/split_manifest.json'),
                              'development_ids': sha(root/'evals/splits/dev_job_ids.txt')},
            'stages': stages, 'stage_count': len(stages), 'maximum_calls_including_repairs': 2*len(stages),
            'conservative_upper_usd': str(bound), 'api_calls': 0, 'actual_cost_usd': 0,
            'no_gold_answers_in_model_payload': True, 'no_candidate_winner': True,
            'stop_conditions': ['source, config, prompt, guide or gold hash change',
                                'uncertain transport charge', 'budget ceiling or project hard stop',
                                'schema/source-quote failure after one repair',
                                'semantic review fails or remains uncertain'],
            'limits': ['Source inventory checks are technical, not complete semantic annotation',
                       'Model output requires independent source-based alignment before F1',
                       'Matching, prompt comparison, quality reference and configuration selection are separate later steps']}


class Stage2ExtractionSession(ProbeSession):
    MAX_CEILING = Decimal('8.50')


class Stage2ExtractionClient(ProbeClient):
    """Persist per-stage attempt counts before dispatch; never retry transport ambiguity."""
    def __init__(self, client, session, stage: dict):
        super().__init__(client, session)
        self.stage = stage

    def chat_structured(self, model, messages, output_model, task, max_tokens=2000, temperature=0):
        s = self.session
        if s.data['status'] != 'running':
            raise BudgetExceeded('Comparison stage is not running')
        stage = s.data['active_job']
        model_key = stage.split('/', 1)[0]
        if model != model_key or task != 'jd_extraction':
            raise ValueError('Attempt differs from frozen stage')
        counts = s.data.setdefault('stage_attempts', {})
        if counts.get(stage, 0) >= 2 or max_tokens > STRUCTURED_MAX_TOKENS:
            raise BudgetExceeded('Frozen attempt/output limit reached')
        attempt = counts.get(stage, 0)
        wire_bytes = len(json.dumps(messages, ensure_ascii=False).encode()) + len(json.dumps(strict_schema(output_model.model_json_schema())).encode()) + 512
        planned_limit = self.stage['first_input_token_upper'] if attempt == 0 else self.stage['repair_input_token_upper']
        if wire_bytes > planned_limit:
            raise BudgetExceeded('Request exceeds frozen per-stage input allowance')
        counts[stage] = counts.get(stage, 0)+1
        s.save()
        try:
            return super().chat_structured(model, messages, output_model, task, max_tokens, temperature)
        finally:
            receipts = [r for r in self.client.ledger.records() if r.run_id == self.client.run_id]
            if receipts and receipts[-1].cost_source == 'uncertain_upper_bound':
                s.data['transport_uncertain'] = True
                s.save()
