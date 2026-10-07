"""Fixed-input matching evaluation. QA readiness is separate from approval."""
from collections import Counter
import hashlib
import json
from pathlib import Path
from jobfit.eval.metrics import evidence_metrics
from jobfit.matching.quote_check import require_quotes
from jobfit.scoring.score import effective_label
from jobfit.schemas.analysis import UnitAssessment


def reference_rows(bundle, stage, cv, extraction):
    path=Path(bundle)/'evidence_gold.jsonl'
    rows=[json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    selected=[r for r in rows if r['cv_id']==stage['cv_id'] and r['job_id']==stage['job_id']]
    units={u.unit_id:u for u in extraction.units}
    if len(selected)!=len(units) or {r['unit_no'] for r in selected}!=set(units):
        raise ValueError('Whole fixed-input evidence reference is required')
    for row in selected:
        if row['review_status']!='approved' or row['split']!='development' or row['check_status']!='done' or row['review_action']=='rejected':
            raise ValueError('Unreviewed, held or incomplete evidence reference')
        if row['unit_text']!=units[row['unit_no']].text:
            raise ValueError('Evidence requirement meaning changed')
        if row['label']=='NO_MATCH':
            if row.get('cv_quote'):raise ValueError('Negative reference cannot cite unrelated evidence')
        else:require_quotes([row['cv_quote']],cv.profile.raw_text)
    return {r['unit_no']:r['label'] for r in selected}


def evaluate(result, reference, extraction, *, fixed_input_alignment_verified=False):
    if fixed_input_alignment_verified is not True:
        raise ValueError('Source-checked fixed-input adapter acceptance required')
    predictions={}
    if result['status']=='done':
        rows=[UnitAssessment.model_validate(r) for r in result['assessments']]
        if len(rows)!=len(extraction.units) or {r.unit_id for r in rows}!={u.unit_id for u in extraction.units}:
            raise ValueError('Final assessment identities changed')
        by_id={r.unit_id:r for r in rows}
        for unit in extraction.units:
            label,status=effective_label(unit,by_id[unit.unit_id])
            predictions[unit.unit_id]=dict(status=status.value,
                label=label.value if label is not None and status.value=='done' else None)
    elif result['status']!='failed':
        raise ValueError('Unknown final process status')
    return evidence_metrics(reference,predictions,alignment_verified=True)


def reference_inventory(bundle, stages, load_inputs):
    pairs=[];counts=Counter();seen=set()
    for stage in stages:
        key=(stage['cv_id'],stage['job_id'])
        if key in seen:continue
        seen.add(key);cv,ex=load_inputs(stage)
        gold=reference_rows(bundle,stage,cv,ex)
        counts.update(gold.values())
        pairs.append(dict(cv_id=key[0],job_id=key[1],units=len(gold),
            classes=dict(Counter(gold.values())),or_groups=sum(bool(u.branches) for u in ex.units),
            fixed_input_sha256=stage['fixed_requirements_sha256']))
    return dict(status='source_and_coverage_checked; fixed adapter acceptance pending',
        pairs=pairs,units=sum(counts.values()),classes=dict(counts),all_three_classes_present=len(counts)==3,
        gold_sha256=hashlib.sha256((Path(bundle)/'evidence_gold.jsonl').read_bytes()).hexdigest(),
        model_calls=0,metrics=None,fixed_input_alignment_verified=False)
