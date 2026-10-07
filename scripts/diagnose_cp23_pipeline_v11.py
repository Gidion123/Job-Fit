"""Diagnose every non-final Part B pair from immutable development artifacts."""
from collections import Counter
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1'
OUTPUT=ROOT/'evals/results/cp23/pipeline_v11/diagnosis_v1.json'
MARKDOWN=ROOT/'docs/checkpoint_2/supporting/CP23_Pipeline_v11_Diagnosis_20261004.md'


def read(path): return json.loads(path.read_text())


def diagnose():
    plan=read(RUN/'plan.json')
    ledger=[json.loads(s) for s in (ROOT/'reports/usage/usage_ledger.jsonl').read_text().splitlines() if s]
    calls=[r for r in ledger if r['run_id']==plan['run_id']]
    by_task={task:iter([r for r in calls if r['task']==task])
             for task in ('jd_extraction','evidence_matching')}
    jd_calls={}
    for path in sorted(RUN.glob('jd_*.json')):
        record=read(path)
        jd_calls[record['job_id']]=[next(by_task['jd_extraction']) for _ in range(record['attempts'])]
    if next(by_task['jd_extraction'],None) is not None: raise ValueError('Unmapped JD call')
    pairs=[]
    for cv,rank in plan['rankings'].items():
        for job in rank:
            record=read(RUN/f'match_{cv}_{job}.json')
            match_calls=[next(by_task['evidence_matching']) for _ in range(record.get('attempts',0))]
            score=record.get('score') or {}
            if score.get('status')=='final': continue
            jd=read(RUN/f'jd_{job}.json') if (RUN/f'jd_{job}.json').exists() else None
            extraction=(jd or {}).get('extraction') or {}
            needs=[u['unit_id'] for u in extraction.get('units',[]) if u.get('needs_review')]
            error=record.get('error_code') or (jd or {}).get('error_code')
            if record['status']=='held_source': cause='source_hold'
            elif record['status']=='failed_extraction':
                cause=('extraction_output_limit_suspected' if error=='IncompleteStructuredResponse'
                       else 'extraction_schema_or_mapping_failure')
            elif record['status']=='held_extraction': cause='looks_incomplete'
            elif record['status']=='failed':
                cause=('transport_timeout' if error=='APITimeoutError' else
                       'matching_output_limit_suspected' if any(c['error_type']=='IncompleteStructuredResponse' for c in match_calls)
                       else 'matching_invalid_output_unclassified')
            elif score.get('status')=='no_score': cause='zero_assessable_required_denominator'
            elif needs: cause='needs_review_structure_hold'
            else: cause='matching_required_unit_not_assessed'
            stage=('source' if cause=='source_hold' else 'extraction' if cause.startswith('extraction') or cause=='looks_incomplete'
                   else 'matching' if cause.startswith('matching') or cause=='transport_timeout' else 'scoring')
            relevant=jd_calls.get(job,[]) if stage=='extraction' else match_calls
            pairs.append({'cv_id':cv,'job_id':job,'stage':stage,'cause':cause,'pair_status':record['status'],
                'score_status':score.get('status'),'error_code':error,'needs_review_unit_ids':needs,
                'needs_review_count':len(needs),'jd_quality':extraction.get('jd_quality'),
                'required_total':score.get('required_total'),
                'call_output_tokens':[c['output_tokens'] for c in relevant],
                'call_input_tokens':[c['input_tokens'] for c in relevant],
                'call_error_types':[c['error_type'] for c in relevant],
                'finish_reason_persisted':False,
                'diagnostic_limit':('The client did not persist finish_reason; output at 16000 tokens plus '
                    'IncompleteStructuredResponse strongly suggests truncation but does not prove provider finish_reason.'
                    if 'output_limit' in cause else
                    'The final generic validator error did not retain its exact rule or raw first draft.'
                    if cause=='matching_invalid_output_unclassified' else None)})
    if next(by_task['evidence_matching'],None) is not None: raise ValueError('Unmapped matching call')
    if len(pairs)!=40: raise ValueError(f'Expected 40 non-final pairs, found {len(pairs)}')
    return {'schema_version':'cp23-pipeline-v11-diagnosis-v1','scope':'development_only',
        'source_run_id':plan['run_id'],'pairs':pairs,'cause_counts':dict(Counter(x['cause'] for x in pairs)),
        'technical_limit':'Old client saved error type and token use, not finish_reason or first invalid matching draft. '
                          'Unknown rules cannot be reconstructed as exact causes.','gold_or_source_changed':False}


def render(result):
    lines=['# CP2.3 Pipeline v1.1: Part B diagnosis','',
        'Development CV1/CV2 only. All 40 pairs without a final score are listed below. '
        'The old run and gold remain unchanged.','',
        '| CV | JD | Stage | Cause | Error / hold detail |',
        '| --- | --- | --- | --- | --- |']
    for r in result['pairs']:
        detail=(r['error_code'] or r['jd_quality'] or r['score_status'] or '')
        if r['needs_review_count']: detail+=f"; {r['needs_review_count']} needs_review unit(s)"
        if 'output_limit' in r['cause']: detail+=f"; output tokens {r['call_output_tokens']} of 16000"
        lines.append(f"| {r['cv_id']} | {r['job_id']} | {r['stage']} | {r['cause']} | {detail} |")
    lines+=['','## Interpretation','',
        '- Output-limit cases reached the old 16,000-token allowance and returned `IncompleteStructuredResponse`. '
        'The old client did not save `finish_reason`, so truncation is strongly indicated, not proven per request.',
        '- Generic invalid matching output does not retain the exact validator rule or first draft. '
        'Do not call it a code bug without a saved trace.',
        '- `needs_review` and zero-denominator holds follow the current approved rules. Changing them needs Dion\'s decision.',
        '- F00369 stays source-held. A similar posting is not its verified original source.',
        '','Machine-readable identities and token counts: '
        '[diagnosis_v1.json](../../../evals/results/cp23/pipeline_v11/diagnosis_v1.json).','']
    return '\n'.join(lines)


if __name__=='__main__':
    result=diagnose();OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    if OUTPUT.exists() or MARKDOWN.exists():raise SystemExit('Versioned diagnosis exists')
    with OUTPUT.open('x') as f:json.dump(result,f,indent=2)
    with MARKDOWN.open('x') as f:f.write(render(result))
    print(json.dumps({'pairs':len(result['pairs']),'cause_counts':result['cause_counts']}))
