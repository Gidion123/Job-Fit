"""Final matching repair in the existing authorized run; never reset its budget."""
from pathlib import Path
import sys
sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1] / 'src')]
import argparse
import fcntl
import hashlib
import json
import time

from scripts.run_cp22_repair_probe import RUN_ID, STATE, STAGES, SPEC
from scripts.run_batch_extraction import development_sources
from jobfit.config import REPO_ROOT, get_settings
from jobfit.cv.parser import ParsedCV
from jobfit.extraction.cache import ExtractionCache
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.closure_probe import ClosureProbeClient
from jobfit.llm.semantic_repair import SemanticRepairSession
from jobfit.matching.evidence_matcher import EvidenceResponse
from jobfit.pipeline import AnalysisContext, compare_pasted_jd


def sha(data):
    return hashlib.sha256(data).hexdigest()


class FinalMatchingRepairClient:
    """One dispatch only; retain the ordinary matcher validators and scorer."""
    def __init__(self, client, corrections, previous):
        self.client, self.corrections, self.previous = client, corrections, previous
        self.calls = 0

    def chat_structured(self, model, messages, output_model, task, **kwargs):
        if self.calls or task != 'evidence_matching' or output_model is not EvidenceResponse:
            raise RuntimeError('Final repair permits exactly one evidence-matching dispatch')
        self.calls += 1
        messages = [dict(m) for m in messages]
        messages[0]['content'] += ('\nFinal allowed source-review repair. Reassess the complete evidence output '
            'using the unchanged guideline and CV. Review these source findings; do not invent evidence '
            'or force a score. No gold labels are provided.\n' + json.dumps(self.corrections))
        payload = json.loads(messages[1]['content'])
        payload['untrusted_document_data']['previous_model_assessments'] = self.previous
        messages[1]['content'] = json.dumps(payload, ensure_ascii=False)
        return self.client.chat_structured(model, messages, output_model, 'evidence_matching_semantic_repair', **kwargs)


def repair_report(state, sources, client, receipt):
    parsed = ParsedCV.model_validate(state['results'][1]['parsed_cv'])
    prior = state['results'][2]
    cache = ExtractionCache()  # session memory only, no public cache mutation
    cache.put(prior['key'], {**prior['extraction'],
        'qualification_coverage': prior['coverage']['inventory_mappings']}, scope='session_jd')
    context = AnalysisContext(analysis_date=parsed.analysis_date, parsing_confirmed=True,
                              complete_work_history_confirmed=True)
    wrapped = FinalMatchingRepairClient(client, receipt['corrections'], state['results'][-1]['report']['assessments'])
    report = compare_pasted_jd(parsed, sources['F00332'], context=context, client=wrapped,
                              model='deepseek-flash', cache=cache, extraction_spec=SPEC)
    report.versions['semantic_repair_version'] = 'evidence-source-review-repair-v1'
    report.operations['matching']['stage_attempts_including_previous'] = 2
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('receipt', type=Path)
    p.add_argument('--execute', action='store_true')
    args = p.parse_args()
    with STATE.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        prior = json.loads(STATE.read_text()); last = prior['results'][-1]
        if last['job_id'] != 'CV1_F00332_match':
            raise ValueError('Only the final matching stage may be repaired')
        for name, h in last['provenance'].items():
            if (REPO_ROOT / name).is_file() and sha((REPO_ROOT / name).read_bytes()) != h:
                raise ValueError('Frozen implementation changed: ' + name)
        sources = {r['job_id']: r['text'] for r in development_sources(['F00034', 'F00332'])}
        for job, text in sources.items():
            if sha(text.encode()) != last['provenance'][job]:
                raise ValueError('Frozen source changed')
        cv = REPO_ROOT / 'data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md'
        if sha(cv.read_bytes()) != last['provenance']['CV1']:
            raise ValueError('Frozen CV changed')
        receipt = json.loads(args.receipt.read_text())
        c = OpenRouterClient(get_settings(), run_id=RUN_ID)
        s = SemanticRepairSession(STATE, run_id=RUN_ID, fingerprint=prior['fingerprint'],
                                 jobs=STAGES, ledger=c.ledger, ceiling='.40')
        if prior['status'] != 'awaiting_semantic_check' or prior.get('transport_uncertain'):
            raise ValueError('Closed or uncertain run cannot be repaired')
        if prior['stage_attempts'].get(last['job_id']) != 1:
            raise ValueError('No repair allowance left')
        s.check_budget(.0492); c.guard.check(.0492)
        print(json.dumps({'run_id': RUN_ID, 'spent_usd': str(s.spent()), 'upper_usd': .0492,
                          'aggregate_ceiling_usd': .40, 'execute': args.execute}), flush=True)
        if not args.execute:
            return
        if not c.verify_inference_key()['inference_key']:
            raise ValueError('Invalid inference key type')
        extension = {n: sha((REPO_ROOT / n).read_bytes()) for n in
                     ['scripts/repair_cp22_matching.py', 'src/jobfit/llm/semantic_repair.py']}
        s.begin_repair(receipt, sha(json.dumps(extension, sort_keys=True).encode()))
        start = time.perf_counter()
        output = {'job_id': last['job_id'], 'run_id': RUN_ID, 'provenance': last['provenance'],
                  'versions': {**last['versions'], 'semantic_repair_version': 'evidence-source-review-repair-v1'},
                  'replaces_result_sha256': last['result_sha256'], 'repair_extension_hashes': extension,
                  'semantic_repair_receipt_sha256': sha(args.receipt.read_bytes()),
                  'preview_confirmation': last['preview_confirmation']}
        try:
            r = repair_report(prior, sources, ClosureProbeClient(c, s), receipt)
            output.update(status='done' if r.status == 'done' else 'failed', report=r.model_dump(mode='json'))
        except BaseException as exc:
            output.update(status='failed', error_code=type(exc).__name__)
        output['latency_ms'] = int((time.perf_counter() - start) * 1000)
        output['result_sha256'] = sha(json.dumps(output, sort_keys=True).encode())
        s.finish_repair(output)
        path = REPO_ROOT / 'evals/results' / f'{RUN_ID}_04_semantic_repair.json'
        with path.open('x') as f:
            json.dump(output, f, indent=2)
        print(json.dumps({'status': s.data['status'], 'spent_usd': str(s.spent()), 'result': str(path)}))


if __name__ == '__main__':
    main()
