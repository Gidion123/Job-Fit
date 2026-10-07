"""Offline H1/H2 counterfactual on saved Part B outputs. Never edits live scoring."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from jobfit.schemas.requirements import JDExtraction, Importance, CONSTRAINT_FIELDS, SEPARATE_FIELDS
from jobfit.schemas.analysis import UnitAssessment
from jobfit.scoring.score import compute_score, merge_duplicate_units

RUN=ROOT/'evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1'
OUT=ROOT/'evals/results/cp23/pipeline_v11/hold_options_v1.json'


def simulate():
    plan=json.loads((RUN/'plan.json').read_text())
    cases=[];changed=[]
    for cv,rank in plan['rankings'].items():
        for job in rank:
            row=json.loads((RUN/f'match_{cv}_{job}.json').read_text())
            before=(row.get('score') or {}).get('status')
            after=before;new_pct=(row.get('score') or {}).get('score_pct')
            reason=None;required_total=unresolved_required=None
            jd_path=RUN/f'jd_{job}.json'
            if row['status']=='done' and jd_path.exists():
                record=json.loads(jd_path.read_text())
                raw=record.get('extraction')
                if raw and raw['jd_quality']=='ok':
                    extraction=JDExtraction.model_validate(raw)
                    flagged=[u for u in extraction.units if u.needs_review]
                    if flagged:
                        units,_=merge_duplicate_units(extraction.units)
                        required=[u for u in units if u.importance==Importance.REQUIRED and
                                  u.field not in CONSTRAINT_FIELDS and u.field not in SEPARATE_FIELDS]
                        unresolved=[u for u in required if u.needs_review]
                        required_total=len(required);unresolved_required=len(unresolved)
                        fraction=len(unresolved)/len(required) if required else None
                        if required and fraction<=.2:
                            filtered=extraction.model_copy(update={'units':[u for u in extraction.units if not u.needs_review]})
                            assessments=[UnitAssessment.model_validate(a) for a in row['assessments']]
                            score=compute_score(filtered,assessments)
                            if score.score_pct is not None:
                                after='provisional';new_pct=score.score_pct
                                reason='H2 excludes unresolved units and marks the remaining score provisional'
                            else:reason='Other score hold remains after exclusion'
                        else:reason='More than 20 percent of required units unresolved, or denominator zero'
            item={'cv_id':cv,'job_id':job,'H1_status':before,'H2_status':after,
                  'H1_score_pct':(row.get('score') or {}).get('score_pct'),'H2_score_pct':new_pct,
                  'required_units_before':required_total,'unresolved_required':unresolved_required,
                  'required_fraction_unresolved':(unresolved_required/required_total if required_total else None),
                  'H2_reason':reason}
            cases.append(item)
            if before!=after: changed.append(item)
    usable=lambda key:sum(r[key] in ('final','provisional') for r in cases)
    return {'schema_version':'cp23-hold-options-v1','scope':'development_only',
            'status':'offline_proposal_not_approved','H1_usable_pairs':usable('H1_status'),
            'H2_usable_pairs':usable('H2_status'),'pairs_total':len(cases),
            'changed_pairs':changed,'changed_unique_jobs':sorted({r['job_id'] for r in changed}),
            'cases':cases,'H2_rule':'At most 20 percent of logical required score units may be unresolved. '
                      'Remove every needs_review unit, including nonrequired ones, then force provisional status. '
                      'JD looks_incomplete and other holds remain.',
            'warning':'H2 changes the D-006 denominator and is not applied without Dion approval.'}


if __name__=='__main__':
    result=simulate();OUT.parent.mkdir(parents=True,exist_ok=True)
    if OUT.exists():raise SystemExit('Versioned simulation exists')
    with OUT.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({'H1_usable_pairs':result['H1_usable_pairs'],'H2_usable_pairs':result['H2_usable_pairs'],
                      'changed_pairs':len(result['changed_pairs']),'changed_jobs':len(result['changed_unique_jobs'])}))
