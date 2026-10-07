"""D-060: scoped accounting for the explicitly adjudicated Claude/F00036 relation.

Preserve original mapping; create accounting-only omissions/additions. This
does not approve any other mapping or mark the whole alignment verified.
"""
from copy import deepcopy

STAGE='claude-haiku-4.5/F00036'
GOLD={'P09-U08','P09-U09'}
MODEL={'U11','U12','U13'}

def apply_approved_complex_policy(alignment, receipt):
    if receipt.get('decision_id')!='D-060' or receipt.get('approved_by')!='Dion' or receipt.get('stage_id')!=STAGE:
        raise ValueError('Exact D-060 case approval required')
    if alignment.get('stage_id')!=STAGE:
        raise ValueError('D-060 is not a blanket many-to-many rule')
    result=deepcopy(alignment);expanded=[];found=0
    for row in result['rows']:
        if len(row['gold_ids'])>1 and len(row['model_ids'])>1:
            if set(row['gold_ids'])!=GOLD or set(row['model_ids'])!=MODEL:
                raise ValueError('Unapproved complex relation')
            found+=1
            result['original_complex_relation']=deepcopy(row)
            for side,ids in [('gold',row['gold_ids']),('model',row['model_ids'])]:
                for ident in ids:
                    expanded.append(dict(gold_ids=[ident] if side=='gold' else [],
                        model_ids=[ident] if side=='model' else [],status='verified',semantic_equivalent=False,
                        accounting_only=True,note='D-060 strict accounting: 0 TP, 2 FN, 3 FP; no new source unit'))
        else:expanded.append(row)
    if found!=1:raise ValueError('D-060 relation absent or repeated')
    result['rows']=expanded
    result['complex_accounting_decision']='D-060'
    return result
