"""Alignment review tables, not automatic semantic matching or evaluation metrics."""
from copy import deepcopy

def alignment_review(gold: list[dict],model_units: list[dict],proposals: list[dict]) -> dict:
    if any(r.get('review_status')!='approved' or r.get('split')!='development' or r.get('review_action')=='rejected' for r in gold):
        raise ValueError('Only approved non-rejected development reference labels are permitted')
    g={r['unit_no']:r for r in gold};m={r['unit_id']:r for r in model_units}
    if len(g)!=len(gold) or len(m)!=len(model_units):raise ValueError('Duplicate alignment identities')
    seen_g=set();seen_m=set();rows=[]
    for p in proposals:
        gi=p['gold_ids'];mi=p['model_ids']
        if not gi and not mi:raise ValueError('Empty alignment')
        if len(set(gi))!=len(gi) or len(set(mi))!=len(mi):raise ValueError('Repeated identity inside mapping')
        if not set(gi)<=g.keys() or not set(mi)<=m.keys():raise ValueError('Unknown alignment identity')
        if seen_g&set(gi) or seen_m&set(mi):raise ValueError('A unit cannot be double counted in alignment')
        relation=('model_addition' if not gi else 'model_omission' if not mi else
                  'one_to_one' if len(gi)==len(mi)==1 else 'model_merge' if len(gi)>1 and len(mi)==1 else
                  'model_split' if len(gi)==1 and len(mi)>1 else 'complex_pending')
        seen_g.update(gi);seen_m.update(mi)
        rows.append({'relation':relation,'gold_ids':gi,'model_ids':mi,'status':'proposed_pending_alignment_review',
                     'note':p['note'],'gold':deepcopy([g[k] for k in gi]),'model':deepcopy([m[k] for k in mi]),
                     'same_source_anchor':all(set(x.get('source_quotes',[]))&{r['source_quote'] for r in [g[k] for k in gi]} for x in [m[k] for k in mi]) if gi and mi else False})
    return {'status':'pending_alignment_review','human_verified':False,'rows':rows,
            'gold_unit_ids':sorted(g),'model_unit_ids':sorted(m),
            'unmapped_gold':sorted(set(g)-seen_g),'unmapped_model':sorted(set(m)-seen_m),
            'metrics':None,'metric_gate':'No F1/Macro-F1 until semantic relations and complete inventories are reviewed. D-054 strictly counts verified one-to-many/many-to-one units; equal IDs/counts or shared quotes do not establish equivalence.'}
