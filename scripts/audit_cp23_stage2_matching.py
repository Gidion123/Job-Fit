"""Preserve all first drafts and source checks; attach delegated semantic QA.

No model calls, label corrections, human approval flags, or winner selection.
"""
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'src')]
import argparse,json,re
from collections import Counter
from scripts.run_cp23_stage2_matching import PLAN,STATE,inputs
from jobfit.matching.evidence_matcher import match_evidence
from jobfit.schemas.analysis import UnitAssessment
from jobfit.scoring.score import effective_label
from jobfit.eval.matching_evaluation import reference_rows
from scripts.run_cp23_stage2_matching import BUNDLE

# Source-based findings, not new labels. Uncertain interpretations are kept
# distinct from positive claims that clearly exceed the quoted CV evidence.
FINDINGS={
 ('deepseek-flash/CV1/F00332','P30-U08'):('interpretation_question','Learning behavior inferred from projects/certificate; do not silently change the approved PARTIAL reference.'),
 ('deepseek-flash/CV1/F00332','P30-U10'):('interpretation_question','Building a thesis model does not explicitly state ownership; the trait interpretation requires caution.'),
 ('deepseek-flash/CV1/F00332','P30-U15'):('unsupported_positive','Cohort presentation/dashboard and teaching do not state actionable recommendations. Full MATCH exceeds the quoted scope.'),
 ('deepseek-flash/CV1/F00036','P09-U11'):('interpretation_question','Regression/model use does not expressly document inferential procedure; the reviewed reference is PARTIAL.'),
 ('deepseek-flash/CV2/F00815','P52-U10'):('unsupported_positive','BigQuery SQL is used, but PostgreSQL occurs only in the skills list. Full SQL/PostgreSQL MATCH is not supported for the entire fixed obligation.'),
 ('deepseek-flash/CV2/F00018','P04-U01'):('insufficient_cited_context','The MATCH label agrees with gold, but the supplied quotes only list algorithms/topics. Relevant project evidence elsewhere is not cited.'),
 ('deepseek-flash/CV2/F00018','P04-U12'):('unsupported_positive','API/container work and report scripts do not explicitly show structured modules. Full MATCH exceeds the quoted scope.'),
 ('deepseek-flash/CV2/F00018','P04-U15'):('interpretation_question','Professional working proficiency cannot automatically be converted into the specified upper-intermediate standard.'),
 ('gpt-6-luna/CV1/F00036','P09-U11'):('interpretation_question','Regression teaching does not explicitly demonstrate the requested inferential procedure; no reference correction is assumed.'),
 ('gpt-6-luna/CV2/F00018','P04-U06'):('unsupported_positive','An AWS Cloud Practitioner course is not evidence of the named Bedrock service. Vendor overlap cannot create PARTIAL for an unmentioned service.'),
 ('gpt-6-luna/CV2/F00018','P04-U21'):('unsupported_positive','Docker/FastAPI bootcamp topics do not mention ML pipeline orchestration. Related MLOps vocabulary is not evidence of this distinct requirement.'),
 ('claude-haiku-4.5/CV2/F00815','P52-U04'):('unsupported_positive','Prompt engineering is only in the skills list in the cited evidence; MATCH conflicts with D-035/B1.'),
 ('claude-haiku-4.5/CV2/F00815','P52-U10'):('unsupported_positive','BigQuery SQL plus PostgreSQL in a skills list does not support full SQL/PostgreSQL MATCH.'),
 ('claude-haiku-4.5/CV2/F00815','P52-U13'):('unsupported_positive','Git is only in the quoted skills list; MATCH conflicts with D-035/B1.'),
}

class ReplayFirst:
    def __init__(self,out):self.out=out;self.calls=0;self.repair=None
    def chat_structured(self,model,messages,output_model,task,**kwargs):
        self.calls+=1
        if self.calls==1:return output_model.model_validate(self.out)
        self.repair=messages[-1]['content']
        raise RuntimeError('offline_diagnostic_no_second_call')

def audit():
    plan=json.loads(PLAN.read_text());state=json.loads(STATE.read_text())
    stages={s['stage_id']:s for s in plan['stages']};results={r['stage_id']:r for r in state['results']}
    cases=[]
    for attempt in state['typed_attempt_outputs']:
        stage=stages[attempt['stage_id']];result=results[stage['stage_id']];cv,ex=inputs(stage)
        replay=ReplayFirst(attempt['output']);match_evidence(cv,ex,client=replay,model=stage['model'],duration_years=stage['duration_input'])
        code=re.search(r'validation \(([^)]+)\)',replay.repair).group(1) if replay.repair else None
        first_quotes=[q for a in attempt['output']['assessments'] for item in [a,*a.get('branches',[])] for q in item.get('cv_quotes',[])]
        rows=[];gold=reference_rows(BUNDLE,stage,cv,ex)
        if result['status']=='done':
            units={u.unit_id:u for u in ex.units}
            for a in map(UnitAssessment.model_validate,result['assessments']):
                unit=units[a.unit_id];label,status=effective_label(unit,a)
                kind,note=FINDINGS.get((stage['stage_id'],a.unit_id),('checked_no_additional_source_entailment_issue','Reviewed against the full CV and fixed requirement; reference disagreement is not itself an unsupported claim.'))
                rows.append(dict(unit_id=a.unit_id,requirement=unit.text,gold_label=gold[a.unit_id],
                    effective_label=label.value if label else None,check_status=status.value,
                    assessment=a.model_dump(mode='json'),semantic_status=kind,note=note))
        cases.append(dict(stage_id=stage['stage_id'],final_status=result['status'],attempts=result['attempts'],
            first_typed_validation='passed' if replay.calls==1 else 'failed',first_validation_trigger=code,
            first_quote_occurrences=len(first_quotes),first_invalid_quote_occurrences=sum(not q.strip() or q not in cv.profile.raw_text for q in first_quotes),
            final_error=result['error_code'],units=len(ex.units),reviewed_final_units=len(rows),rows=rows,
            provenance='delegated source QA; no independent human prediction annotation',
            failed_final_is_not_assessed=result['status']=='failed'))
    counts=Counter(row['semantic_status'] for c in cases for row in c['rows'])
    return dict(schema_version='cp23-matching-semantic-QA-v1',cases=cases,counts=dict(counts),
        review_scope='all nine process-valid final cases and all sixteen typed first attempts',
        final_cases=16,process_valid_cases=sum(c['final_status']=='done' for c in cases),reviewed_final_logical_units=sum(c['reviewed_final_units'] for c in cases),
        original_predictions_changed=False,gold_changed=False,api_calls=0,winner=None,
        limits=['Exact quote occurrence is not semantic support for the complete requirement',
            'First validation trigger is one observed error, not an exhaustive diagnosis',
            'Seven repair requests were rejected with HTTP400-class errors; provider body was not retained, so exact root cause is unknown',
            'Changing a repair message sequence requires a new experiment; no failed case was retried',
            'Confirmed unsupported positives block the tested configurations under D-029; ambiguous interpretations are reported separately'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);args=p.parse_args()
    result=audit()
    with Path(args.output).open('x') as f:json.dump(result,f,indent=2,ensure_ascii=False)
    print(json.dumps({k:result[k] for k in ['final_cases','process_valid_cases','reviewed_final_logical_units','counts']}))
