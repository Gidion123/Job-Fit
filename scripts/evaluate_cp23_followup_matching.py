"""Offline D-064 fixed-input evidence evaluation and complete source QA.

The D-063 adapter is reused, not new extraction alignments. Final positives,
OR branches and retained drafts are audited without editing labels or outputs.
"""
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'src')]
import argparse,hashlib,json,re
from collections import Counter,defaultdict
from decimal import Decimal
from jobfit.config import REPO_ROOT
from jobfit.schemas.analysis import UnitAssessment
from jobfit.scoring.score import effective_label
from jobfit.eval.metrics import evidence_metrics,operational_summary
from jobfit.eval.matching_evaluation import reference_rows
from jobfit.matching.evidence_matcher import match_evidence
from scripts.run_cp23_stage2_matching import inputs,BUNDLE
from scripts.run_cp23_stage2_followup import RUN,PLAN,STATE
from scripts.evaluate_cp23_stage2_round1 import accepted_packet
from scripts.audit_cp23_stage2_matching import ReplayFirst

FINDINGS={
 ('gpt-6-sol/matching/CV1/F00332','P30-U06'):('interpretation_question','Dashboard delivery for a marketing team is not explicit collaboration; PARTIAL versus reviewed NO_MATCH is kept as a rubric question.'),
 ('gpt-6-sol/matching/CV2/F00815','P52-U10'):('unsupported_positive_fixed_scope','Quoted BigQuery SQL activity does not demonstrate PostgreSQL in context. Full MATCH exceeds the accepted SQL/PostgreSQL obligation; original JD example wording remains a reference-interpretation limitation.'),
 ('gpt-6-sol/matching/CV2/F00018','P04-U15'):('interpretation_question','Professional working proficiency is not an explicit strong-upper-intermediate level or standardized test result; no automatic CEFR conversion.'),
 ('deepseek-v4-pro/matching/CV1/F00332','P30-U10'):('interpretation_question','A thesis title does not expressly establish project ownership; trait inference is kept separate from a confirmed technical unsupported claim.'),
 ('deepseek-v4-pro/matching/CV1/F00332','P30-U11'):('insufficient_cited_context','The MATCH agrees with the reference, but its cleaning/joining quote does not explicitly describe exploration; cohort analysis elsewhere is not cited.'),
 ('deepseek-v4-pro/matching/CV1/F00332','P30-U14'):('unsupported_positive_fixed_scope','Cohort analysis is cited, but no anomaly detection is described anywhere in the CV. Full MATCH exceeds the combined reviewed trend/anomaly obligation.'),
 ('deepseek-v4-pro/matching/CV1/F00332','P30-U15'):('unsupported_positive','Presenting cohort findings does not state actionable recommendations; full MATCH exceeds the quoted and full-CV evidence, as in the retained round-one error.'),
 ('deepseek-v4-pro/matching/CV2/F00815','P52-U10'):('unsupported_positive_fixed_scope','BigQuery SQL activity does not demonstrate PostgreSQL use in context. Keep the accepted fixed reference and disclose the example-like original wording as an interpretation limitation.'),
 ('deepseek-v4-pro/matching/CV2/F00018','P04-U12'):('unsupported_positive','FastAPI deployment and an answer-accuracy evaluation do not describe well-structured software modules; full MATCH exceeds the source evidence.'),
 ('deepseek-v4-pro/matching/CV2/F00018','P04-U15'):('interpretation_question','Professional working proficiency does not explicitly establish the specified strong-upper-intermediate threshold.'),
}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def evaluate():
    _,receipt=accepted_packet()
    plan=json.loads(PLAN.read_text());state=json.loads(STATE.read_text())
    if state['status']!='complete' or len(state['results'])!=19:raise ValueError('D-064 collection incomplete')
    stages={s['stage_id']:s for s in plan['stages']};gold={};pred=defaultdict(dict);cases=[]
    for result in state['results']:
        if result['kind']!='matching':continue
        if sha(REPO_ROOT/result['result_file'])!=result['result_sha256']:raise ValueError('Paid result changed')
        stage=stages[result['stage_id']];cv,ex=inputs(stage);refs=reference_rows(BUNDLE,stage,cv,ex)
        units={u.unit_id:u for u in ex.units}; rows=[]
        for unit,label in refs.items():gold['/'.join([stage['cv_id'],stage['job_id'],unit])]=label
        if result['status']=='done':
            assessments={a.unit_id:a for a in map(UnitAssessment.model_validate,result['assessments'])}
            if set(assessments)!=set(units) or len(result['assessments'])!=len(units):raise ValueError('Fixed assessment coverage changed')
            for unit in ex.units:
                a=assessments[unit.unit_id];label,status=effective_label(unit,a)
                identity='/'.join([stage['cv_id'],stage['job_id'],unit.unit_id])
                pred[stage['model']][identity]=dict(label=label.value if label and status.value=='done' else None,status=status.value)
                quotes=[q for item in [a,*a.branches] for q in item.cv_quotes]
                if any(not q.strip() or q not in cv.profile.raw_text for q in quotes):raise ValueError('Final quote invalid')
                kind,note=FINDINGS.get((stage['stage_id'],unit.unit_id),('checked_no_additional_source_entailment_issue','Full CV, fixed obligation and each OR branch reviewed; disagreement alone is not proof of an unsupported claim.'))
                rows.append(dict(unit_id=unit.unit_id,requirement=unit.text,gold_label=refs[unit.unit_id],
                    effective_label=label.value if label else None,check_status=status.value,
                    assessment=a.model_dump(mode='json'),semantic_status=kind,note=note))
        attempts=[]
        for typed in state.get('typed_attempt_outputs',[]):
            if typed['stage_id']!=stage['stage_id']:continue
            replay=ReplayFirst(typed['output'])
            match_evidence(cv,ex,client=replay,model=stage['model'],duration_years=stage['duration_input'])
            trigger=re.search(r'validation \(([^)]+)\)',replay.repair).group(1) if replay.repair else None
            quotes=[q for a in typed['output']['assessments'] for item in [a,*a.get('branches',[])] for q in item.get('cv_quotes',[])]
            attempts.append(dict(attempt=typed['attempt'],offline_validation='passed' if replay.calls==1 else 'failed',
                first_observed_trigger=trigger,quote_occurrences=len(quotes),invalid_quote_occurrences=sum(not q.strip() or q not in cv.profile.raw_text for q in quotes)))
        cases.append(dict(stage_id=stage['stage_id'],model=stage['model'],status=result['status'],attempts=result['attempts'],
            error_code=result['error_code'],stage_wall_ms=result['stage_wall_ms'],reviewed_logical_units=len(rows),
            rows=rows,typed_attempt_diagnostics=attempts,result_file=result['result_file'],result_sha256=result['result_sha256']))
    if len(gold)!=73 or len(cases)!=8:raise ValueError('Fixed common scope changed')
    ledger=[json.loads(line) for line in (REPO_ROOT/'reports/usage/usage_ledger.jsonl').read_text().splitlines() if line.strip()]
    live=[r for r in ledger if r['run_id']==RUN]
    if len(live)!=sum(r['attempts'] for r in state['results']):raise ValueError('Attempt/ledger mismatch')
    by_model={}
    for model in ['gpt-6-sol','deepseek-v4-pro']:
        model_cases=[c for c in cases if c['model']==model]
        canonical=next(s['model_id'] for s in plan['stages'] if s['model']==model)
        records=[r for r in live if r['model']==canonical]
        by_model[model]=dict(metrics=evidence_metrics(gold,pred[model],alignment_verified=True),
            process_valid_matching=sum(c['status']=='done' for c in model_cases),original_matching_cases=4,
            operations_all_extraction_and_matching=operational_summary(records),
            operations_by_task={task:operational_summary([r for r in records if r['task']==task]) for task in ['jd_extraction','evidence_matching']},
            matching_cost_usd=str(sum((Decimal(str(r['cost_usd'])) for r in records if r['task']=='evidence_matching'),Decimal(0))),
            safety_findings=dict(Counter(row['semantic_status'] for c in model_cases for row in c['rows'] if row['semantic_status']!='checked_no_additional_source_entailment_issue')))
    return dict(schema_version='cp23-followup-evidence-v1',scope='same four reviewed development pairs;73 fixed units/model',
        fixed_adapter_acceptance='D-063',verification_method=receipt['verification_method'],extraction_metrics=None,
        extraction_gate='D-064 new candidate alignment acceptance required',evidence_support=dict(Counter(gold.values())),by_model=by_model,
        cases=cases,reviewed_final_logical_units=sum(c['reviewed_logical_units'] for c in cases),
        source_QA_provenance='delegated source QA; no independent human annotation of predictions',
        api_calls=len(live),run_cost_usd=str(sum((Decimal(str(r['cost_usd'])) for r in live),Decimal(0))),
        ledger_accounted_usd=str(sum((Decimal(str(r['cost_usd'])) for r in ledger if not r.get('cached')),Decimal(0))),
        historical_uncertain_cost_usd=str(sum((Decimal(str(r['cost_usd'])) for r in ledger if r.get('cost_source')=='uncertain_upper_bound'),Decimal(0))),
        paid_scope=dict(original_stages=19,maximum_calls=38,cap_usd='6.40',hard_stop_usd='8.50'),
        hashes={str(PLAN.relative_to(REPO_ROOT)):sha(PLAN),str(STATE.relative_to(REPO_ROOT)):sha(STATE)},
        winner=None,gold_changed=False,workbook_written=False,
        limits=['Evidence is measured on fixed reviewed requirements, not end-to-end extraction outputs.',
            'Reference model is a comparator, not truth or an automatic runtime default.',
            'Original SQL/PostgreSQL wording is example-like; fixed gold asks PostgreSQL-specific context. Any reference correction needs explicit adjudication/versioning.',
            'Valid source quotes do not by themselves prove the whole claimed requirement.',
            'New extraction mappings remain pending; unlike73/120-unit aggregate scopes cannot be compared.',
            'Small development set, no production latency benchmark or independent test confirmation.'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);a=p.parse_args()
    out=evaluate()
    with Path(a.output).open('x') as f:json.dump(out,f,indent=2,ensure_ascii=False)
    print(json.dumps({m:dict(macro_f1=r['metrics']['macro_f1'],safety=r['safety_findings']) for m,r in out['by_model'].items()}))
    print(out['run_cost_usd'],out['ledger_accounted_usd'])
