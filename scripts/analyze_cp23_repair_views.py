"""Original and repaired views plus offline proposed guardrails. No gold writes."""
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'src')]
import json,hashlib
from copy import deepcopy
from collections import defaultdict,Counter
from decimal import Decimal
from scripts.run_cp23_stage2_matching import PLAN,STATE,BUNDLE,inputs,RUN as ORIGINAL_RUN
from scripts.prepare_cp23_repair_rerun import ROOT,RUN,read,sha
from scripts.audit_cp23_stage2_matching import FINDINGS
from jobfit.eval.matching_evaluation import reference_rows
from jobfit.eval.metrics import evidence_metrics,operational_summary
from jobfit.schemas.analysis import UnitAssessment
from jobfit.scoring.score import effective_label
from jobfit.matching.guardrails import apply_guardrails
NEW_FINDINGS={
 'P09-U05':('unsupported_positive','Generic machine learning basics does not name or demonstrate unsupervised learning; PARTIAL cites the wrong scope.'),
 'P09-U09':('unsupported_positive','Matplotlib MATCH comes only from Skills, not visualization use.'),
 'P09-U10':('insufficient_cited_context','The cited course list does not name descriptive statistics. The gold MATCH cites cohort analysis elsewhere in the CV. Treat weak citation separately from a confirmed unsupported label.'),
 'P09-U11':('unsupported_positive','Inferential statistics MATCH cites only the Skills list.'),
 'P09-U08':('interpretation_question','Cohort analysis supports analysis; exploratory workflow is not explicitly described.'),
 'P09-U13':('interpretation_question','Presentation to a division manager does not establish the audience is nontechnical.')}

def build(original):
    plan=read(PLAN);state=read(STATE);stages={s['stage_id']:s for s in plan['stages']}
    replay=read(ROOT/'reports/quality_probe'/f'{RUN}.json')
    overlay={r['stage_id']:r for r in replay['results']}
    truth={};view={};new_qa=[]
    for name,guard in [('A',False),('B',False),('A_guardrails',True),('B_guardrails',True)]:
        pred=defaultdict(dict);changes=[];findings=[];counts=Counter();valid=Counter();positives=Counter()
        for old in state['results']:
            sid=old['stage_id'];s=stages[sid];cv,ex=inputs(s)
            gold=reference_rows(BUNDLE,s,cv,ex)
            for u,lab in gold.items():truth[f'{s["cv_id"]}/{s["job_id"]}/{u}']=lab
            selected=overlay.get(sid,old) if name.startswith('B') else old
            if selected['status']!='done':continue
            valid[s['model']]+=1
            units={u.unit_id:u for u in ex.units}
            for a in selected['assessments']:
                unit=units[a['unit_id']];isnew=sid in overlay and name.startswith('B')
                kind,note=(NEW_FINDINGS.get(a['unit_id'],('checked_no_additional_issue','Checked fixed requirement, full CV and source quotes.')) if isnew else
                    FINDINGS.get((sid,a['unit_id']),('checked_no_additional_issue','Historical full source QA retained.')))
                adjusted=deepcopy(a);changed=[]
                if guard:adjusted,changed=apply_guardrails(unit.model_dump(mode='json'),a,cv.profile.raw_text)
                changes.extend(dict(stage_id=sid,**c) for c in changed)
                label,status=effective_label(unit,UnitAssessment.model_validate(adjusted))
                pred[s['model']][f'{s["cv_id"]}/{s["job_id"]}/{a["unit_id"]}']={'label':label.value if label and status.value=='done' else None,'status':status.value}
                positives[s['model']]+=int(label is not None and label.value in ['MATCH','PARTIAL'])
                corrected=bool(changed) and kind=='unsupported_positive'
                if kind=='unsupported_positive' and not corrected:counts[s['model']]+=1
                if kind!='checked_no_additional_issue':findings.append(dict(stage_id=sid,unit_id=a['unit_id'],kind=kind,note=note,guardrail_corrected=corrected,changes=changed))
                if isnew and not guard:
                    qs=[q for item in [a,*a.get('branches',[])] for q in item.get('cv_quotes',[])]
                    new_qa.append(dict(stage_id=sid,unit_id=a['unit_id'],requirement=unit.text,assessment=a,all_quotes_exact=all(q in cv.profile.raw_text for q in qs),semantic_status=kind,note=note))
        models=sorted({s['model'] for s in plan['stages']})
        view[name]={'by_model':{m:{'metrics':evidence_metrics(truth,pred[m],alignment_verified=True),'process_valid':valid[m],
                'unsupported_positives':counts[m],'positive_units':positives[m],
                'unsupported_rate_among_positive_units':counts[m]/positives[m] if positives[m] else None} for m in models},
            'findings':findings,'changes':changes,'runtime_default_changed':False}
    # A is a strict reproduction, never a replacement of historical metrics.
    for m,x in view['A']['by_model'].items():
        if x['metrics']!=original['evidence'][m]['metrics']:raise ValueError('Original evidence metrics changed')
    ledger=[json.loads(l) for l in (ROOT/'reports/usage/usage_ledger.jsonl').read_text().splitlines() if l.strip()]
    aliases={s['model_id']:s['model'] for s in plan['stages']}
    operations={}
    for viewname in ['A','B']:
        groups=defaultdict(list)
        for r in ledger:
            if r['run_id']==ORIGINAL_RUN or (viewname=='B' and r['run_id']==RUN and r['task']=='evidence_matching'):
                groups[aliases[r['model']]].append(r)
        operations[viewname]={m:operational_summary(rs) for m,rs in groups.items()}
    # Proposed mapping from full source review; no human approval is manufactured.
    extraction=overlay['gemini-3.5-flash-lite/F00815']['extraction']
    mappings=[]
    for g,mods,equivalent,note in [(i,[i],True,'Meaning/importance retained; category tracked separately.') for i in range(1,9)]+[
        (9,[9,10],False,'One reviewed building/deployment obligation split into two; equivalent-framework route omitted.'),
        (10,[11],False,'SQL/PostgreSQL reviewed obligation changed into OR. Original example-like wording remains a reference limitation.'),
        (11,[12],True,'Vector alternatives retained.'),(12,[13,14],False,'Required cloud OR split; AWS branch changed to preferred.'),
        (13,[15],True,'Git retained.'),(14,[16],True,'Testing retained.'),(15,[17],True,'CI/CD retained.'),(16,[18],True,'Technical bachelor alternatives retained.')]:
        mappings.append({'gold_ids':[f'P52-U{g:02}'],'model_ids':[f'U{i:02}' for i in mods],
            'relation':'one_to_one' if len(mods)==1 else 'split','recommended_semantic_equivalent':equivalent,'status':'pending_human_acceptance','note':note})
    from scripts.run_batch_extraction import development_sources
    source=development_sources(['F00815'])[0]['text']
    extraction_qa={'stage_id':'gemini-3.5-flash-lite/F00815','gold_units':16,'model_units':len(extraction['units']),
        'all_quotes_exact':all(q in source for u in extraction['units'] for q in u['source_quotes']),
        'category_issue':'U01 experience_duration versus reviewed knowledge_area, tracked separately under D-061',
        'mappings':mappings,'human_verified':False,'primary_f1':None,
        'reason':'New repaired extraction requires its own concrete mapping acceptance; D-063 only binds historical drafts.'}
    return {'schema_version':'cp23-repair-views-v1','run_id':RUN,'scope':'development only','views':view,'operations':operations,
        'original_extraction':original['extraction'],'bug_fixed_extraction':{m:(dict(f1=None,status='pending_new_mapping_acceptance') if m=='gemini-3.5-flash-lite' else x) for m,x in original['extraction'].items()},
        'new_matching_QA':new_qa,'new_extraction_QA':extraction_qa,'original_eight_findings':8,
        'new_confirmed_findings':3,'new_interpretation_questions':2,'new_insufficient_citation':1,
        'replay_actual_usd':read(ROOT/'evals/results'/f'{RUN}_summary.json')['cost_usd'],
        'replay_cap_usd':'0.65','replay_conservative_upper_usd':'0.6485602',
        'ledger_accounted_usd':str(sum((Decimal(str(r['cost_usd'])) for r in ledger if not r.get('cached')),Decimal(0))),
        'historical_uncertain_usd':'0.0210861','api_calls_in_analysis':0,'winner':None,
        'hashes':{str(p.relative_to(ROOT)):sha(p) for p in [PLAN,STATE,ROOT/'reports/quality_probe'/f'{RUN}.json']},
        'primary_recommendation':'B after repair framing fix, subject to Dion approval and new extraction mapping acceptance',
        'limits':['No repeated first attempt. Invalid repairs stay not_assessed.',
          'Guardrails are an offline proposal and only address literal scope/list evidence, not all entailment.',
          'Safety rate denominator is effective positive logical-unit predictions on process-valid stages, not all73 units.',
          'Costs include historical rejected attempts and the new replay. Request percentiles are not production latency.']}
