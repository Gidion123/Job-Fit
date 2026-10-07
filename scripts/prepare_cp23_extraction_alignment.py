"""Complete pending semantic mapping packet for the 27 retained extraction drafts.

Explicit source-based relation proposals, not automatic similarity alignment.
No gold edits, inference, verified flags, F1 or configuration choice.
"""
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'src')]
from collections import Counter
import argparse, hashlib, json
from jobfit.config import REPO_ROOT
from jobfit.eval.alignment import alignment_review
from scripts.run_batch_extraction import development_sources

INV='evals/results/cp23_stage2_v14_observation_inventory_20261003_v3.json'
GOLD='evals/gold/development_v13_reviewed_20261003_stage1_r3/extraction_gold.jsonl'
PREFIX={'F00332':'P30','F00036':'P09','F00309':'P26','F00354':'P32','F00815':'P52','F00010':'P02','F00018':'P04'}

# Each item is gold number(s), model number(s). Empty sides are added explicitly
# below, so all independently assessable units enter the review inventory once.
def one(g,m): return ([g],[m])
def seq(n): return [one(i,i) for i in range(1,n+1)]
MAPS={
 ('F00332','deepseek-flash'):seq(13)+[([14],[14,15]),one(15,16),one(16,17)],
 ('F00332','gpt-6-luna'):seq(7)+[([8],[8,9,10,11])]+[one(g,g+3) for g in range(9,14)]+[([14],[17,18]),one(15,19),one(16,20)],
 ('F00332','gemini-3.5-flash-lite'):[([1],[1,2,3,4])]+[one(g,g+3) for g in range(2,17)],
 ('F00332','claude-haiku-4.5'):seq(10)+[([11,12,13],[11]),([14,15],[12]),one(16,13)],
 ('F00036','deepseek-flash'):[one(g,g+2) for g in range(1,18)],
 ('F00036','gpt-6-luna'):[one(1,7),one(2,8),one(3,9),one(4,3),one(5,4),one(6,5),one(7,10)]+[one(g,g+3) for g in range(8,18)],
 ('F00036','gemini-3.5-flash-lite'):seq(7)+[([8,9],[8]),one(10,9),one(11,10),one(12,11),one(13,12),([14,15],[13]),([16,17],[14])],
 ('F00036','claude-haiku-4.5'):[one(1,1),one(2,2),([3],[3,4,5]),([4,5,6],[6]),([7],[7,8,9,10]),([8,9],[11,12,13]),([10,11,12],[14]),one(13,15),([14,15],[16]),([16,17],[17])],
 ('F00309','deepseek-flash'):seq(9),('F00309','gpt-6-luna'):seq(9),('F00309','gemini-3.5-flash-lite'):seq(9),('F00309','claude-haiku-4.5'):seq(9),
 ('F00354','deepseek-flash'):seq(15)+[one(16,17),one(17,16)]+[one(g,g) for g in range(18,29)]+[([29],list(range(29,35)))],
 ('F00354','gpt-6-luna'):seq(15)+[one(16,17),one(17,16)]+[one(g,g) for g in range(18,29)]+[([29],list(range(29,35)))],
 ('F00354','gemini-3.5-flash-lite'):[([1],list(range(1,9)))]+[one(g,g+7) for g in range(2,7)]+[(list(range(7,11)),[14]),one(11,15),one(12,16),one(13,17),one(14,18),one(15,19),one(16,21),one(17,20)]+[one(g,g+4) for g in range(18,29)]+[([29],list(range(33,39)))],
 ('F00354','claude-haiku-4.5'):seq(15)+[one(16,17),one(17,16)]+[one(g,g) for g in range(18,29)]+[([29],list(range(29,35)))],
 ('F00815','deepseek-flash'):seq(8)+[([9],[9,10]),one(10,11),one(11,12),one(12,13),([13,14,15],[14]),one(16,15)],
 ('F00815','gpt-6-luna'):seq(8)+[([9],[9,10])]+[one(g,g+1) for g in range(10,17)],
 ('F00815','claude-haiku-4.5'):seq(16),
 ('F00010','deepseek-flash'):seq(9),('F00010','gpt-6-luna'):seq(9),('F00010','gemini-3.5-flash-lite'):seq(9),
 ('F00010','claude-haiku-4.5'):seq(3)+[([4],[4,5,6]),([5],[7,8,9]),([6,7],[10]),one(8,11),one(9,12)],
 ('F00018','deepseek-flash'):seq(17)+[([18,'18-AWS'],[18])]+[one(g,g) for g in range(19,24)],
 ('F00018','gpt-6-luna'):seq(17)+[([18,'18-AWS'],[18])]+[one(g,g) for g in range(19,24)],
 ('F00018','gemini-3.5-flash-lite'):seq(6)+[([7,8],[7])]+[one(g,g-1) for g in range(9,18)],
 ('F00018','claude-haiku-4.5'):[([1,2],[1])]+[one(g,g-1) for g in range(3,11)]+[([11],[10,11,12])]+[one(g,g+1) for g in range(12,18)],
}
# Meaning/type concerns per source-reviewed final output. Relations stay pending;
# no boolean here is a human approval or a new extraction metric definition.
FLAGS={
 ('F00332','deepseek-flash'):{1:'Missing considered-other-discipline branch',13:'SQL activity category differs'},
 ('F00332','gpt-6-luna'):{1:'Education classified other',11:'Concept classified other',12:'Concept classified other',13:'SQL activity category differs',15:'Actionable activity classified other'},
 ('F00332','gemini-3.5-flash-lite'):{13:'SQL activity category differs',15:'Actionable activity classified other'},
 ('F00332','claude-haiku-4.5'):{1:'Fresh-graduate alternative missing'},
 ('F00036','deepseek-flash'):{8:'EDA made tool-choice-dependent instead of independent obligation',9:'Named visualization tool classified concept',13:'Reviewed stakeholder activity versus soft-skill category; source interpretation needs adjudication'},
 ('F00036','gpt-6-luna'):{8:'EDA made tool-choice-dependent',13:'Reviewed stakeholder activity versus soft-skill category; adjudication needed'},
 ('F00036','gemini-3.5-flash-lite'):{3:'Parent singles out Python and omits data-manipulation/analysis qualifier; inspect complete source-grounded unit',7:'Parent singles out Pandas although explicit OR branches include other libraries; shared experience is inherited from parent',13:'Reviewed stakeholder activity versus soft-skill category; adjudication needed'},
 ('F00036','claude-haiku-4.5'):{1:'Degree OR stored simple; Informatics translated IT rather than Informatics',13:'Reviewed stakeholder activity versus soft-skill category; adjudication needed'},
 ('F00309','gpt-6-luna'):{**{i:'Explicit preferred section changed to required' for i in range(1,10)},9:'Preferred changed required and education classified other'},
 ('F00309','gemini-3.5-flash-lite'):{7:'Unnamed visualization concept classified skill_tool',8:'Unnamed storytelling concept classified skill_tool'},
 ('F00309','claude-haiku-4.5'):{9:'Equivalent-experience OR stored simple without assessable branches'},
 ('F00354','deepseek-flash'):{17:'Documentation concept classified soft_skill',22:'Time-series qualifier missing',23:'Unnamed framework classified skill_tool'},
 ('F00354','gpt-6-luna'):{13:'Git/codebase group classified other',17:'Documentation classified other',22:'Time-series qualifier missing',23:'Unnamed framework classified skill_tool'},
 ('F00354','gemini-3.5-flash-lite'):{17:'Documentation concept classified soft_skill',**{i:'Required source changed preferred' for i in range(18,29)},22:'Required changed preferred and time-series qualifier absent',23:'Required changed preferred; unnamed framework classified skill_tool'},
 ('F00354','claude-haiku-4.5'):{1:'Education OR stored simple',**{i:'Familiarity strengthened to experience' for i in range(7,11)},11:'Method classified soft_skill',12:'Method classified soft_skill',13:'Git/codebase OR stored simple',17:'Documentation classified soft_skill',**{i:'Required source changed preferred' for i in range(18,29)},22:'Required changed preferred and time-series qualifier absent',23:'Required changed preferred; unnamed framework classified skill_tool'},
 ('F00815','deepseek-flash'):{1:'Role experience classified other',3:'LLM alternative group stored simple',11:'Vector alternatives stored simple and classified knowledge_area'},
 ('F00815','gpt-6-luna'):{1:'Role experience classified other; gold stored simple whereas model uses OR'},
 ('F00815','claude-haiku-4.5'):{1:'No numeric duration but classified experience_duration',7:'Understanding strengthened to experience',8:'Understanding strengthened to experience',9:'Equivalent-framework route omitted'},
 ('F00010','deepseek-flash'):{4:'Shared proficiency present in parent; inherited by branches per active matcher prompt, not automatically a qualifier error',5:'Shared deployment present in parent; inherited by branches, not automatically a qualifier error',8:'Coding-assistant alternatives stored simple'},
 ('F00010','gpt-6-luna'):{8:'Unresolved coding-assistant composite'},
 ('F00010','gemini-3.5-flash-lite'):{1:'Role alternatives stored without branches',4:'Parent proficiency applies to branches; ordinary depth word is not a separate obligation under D-035/D-042',5:'Parent deployment scope applies to branches; no independent bare-cloud matching is authorized',8:'Reviewed similar-assistant route versus source example-list interpretation needs adjudication'},
 ('F00010','claude-haiku-4.5'):{1:'Role alternatives stored without branches',8:'Coding-assistant alternatives stored simple'},
 ('F00018','deepseek-flash'):{11:'Parent practical-use-case qualifier is inherited by branches under active matcher prompt',20:'Parent experience qualifier is inherited by branches',22:'Parent practical-experience qualifier is inherited by branches'},
 ('F00018','gpt-6-luna'):{1:'Comfortable understanding strengthened to hands-on experience',11:'One-or-more alternative stored simple'},
 ('F00018','gemini-3.5-flash-lite'):{3:'Hands-on production retained; ordinary strong depth word is not a separate obligation',4:'Hands-on RAG retained; ordinary strong depth word is not a separate obligation',5:'Hands-on agentic retained; ordinary strong depth word is not a separate obligation',11:'Parent practical-use-case qualifier is inherited by branches',17:'Ordinary excellent depth word is not a separate obligation'},
 ('F00018','claude-haiku-4.5'):{3:'Nonnumeric experience misclassified duration',4:'Strong hands-on qualifier absent',5:'Strong hands-on qualifier absent',7:'Nonnumeric experience misclassified duration',8:'Nonnumeric experience misclassified duration',9:'Nonnumeric experience misclassified duration',10:'Nonnumeric experience misclassified duration',12:'Generic engineering concept classified tool'},
}

# Material semantic failures after reviewing complete parent/branch meaning.
# Category alone is separate under D-061; source importance is mandatory.
# Ordinary depth wording follows D-035/D-042, not a new exact-string rule.
CONTENT_FAILURES={
 ('F00332','deepseek-flash'):{1},
 ('F00332','claude-haiku-4.5'):{1},
 ('F00036','deepseek-flash'):{8},
 ('F00036','gpt-6-luna'):{8},
 ('F00036','gemini-3.5-flash-lite'):{3},
 ('F00036','claude-haiku-4.5'):{1},
 ('F00309','claude-haiku-4.5'):{9},
 ('F00354','deepseek-flash'):{22},
 ('F00354','gpt-6-luna'):{22},
 ('F00354','gemini-3.5-flash-lite'):{22},
 ('F00354','claude-haiku-4.5'):{1,13,22},
 ('F00815','deepseek-flash'):{3,11},
 ('F00815','claude-haiku-4.5'):{7,8,9},
 ('F00010','deepseek-flash'):{8},
 ('F00010','gpt-6-luna'):{8},
 ('F00010','gemini-3.5-flash-lite'):{1},
 ('F00010','claude-haiku-4.5'):{1,8},
 ('F00018','gpt-6-luna'):{1,11},
}
# Key numbers always identify gold records, never model row offsets.

def gid(job,n):
    return PREFIX[job]+'-U'+(f'{n:02d}' if isinstance(n,int) else '18-AWS')

def prepare(root=REPO_ROOT):
    root=Path(root)
    inv=json.loads((root/INV).read_text())
    gold=[json.loads(x) for x in (root/GOLD).read_text().splitlines()]
    sources={r['job_id']:r['text'] for r in development_sources(list(PREFIX))}
    reviews=[]
    for item in inv['rows']:
        job,model=item['job_id'],item['model']
        refs=[r for r in gold if r['job_id']==job]
        if item['process_status']!='done':
            reviews.append(dict(stage_id=item['stage_id'],status='retained_process_failure',gold_units=len(refs),model_units=0,
                review_required='D-052 failure accounting; do not omit this original case from aggregate metrics',metrics=None))
            continue
        path=root/item['result_file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=inv['input_hashes'][item['result_file']]:raise ValueError('Result changed')
        units=json.loads(path.read_text())['extraction']['units']
        proposals=[]; seen_g=set();seen_m=set()
        for gn,mn in MAPS[(job,model)]:
            gi=[gid(job,n) for n in gn];mi=[f'U{n:02d}' for n in mn]
            concerns=[FLAGS.get((job,model),{}).get(n) for n in gn]
            concerns=[c for c in concerns if c]
            if len(gn)>1 or len(mn)>1:concerns.append('Strict D-054 structural split/merge: no automatic TP; many-to-many remains held')
            proposals.append(dict(gold_ids=gi,model_ids=mi,note='; '.join(concerns) or 'Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row.'))
            seen_g.update(gi);seen_m.update(mi)
        for r in refs:
            if r['unit_no'] not in seen_g:proposals.append(dict(gold_ids=[r['unit_no']],model_ids=[],note='Reviewed source obligation omitted from final model draft'))
        for u in units:
            if u['unit_id'] not in seen_m:proposals.append(dict(gold_ids=[],model_ids=[u['unit_id']],note='Model addition outside reviewed inventory; opening-paragraph umbrella/location applicability needs adjudication where noted in source QA'))
        report=alignment_review(refs,units,proposals)
        by_gold={gid(job,n) for n in CONTENT_FAILURES.get((job,model),set())}
        for row in report['rows']:
            one_to_one=row['relation']=='one_to_one'
            same_importance=one_to_one and row['gold'][0]['importance']==row['model'][0]['importance']
            content_equivalent=one_to_one and not bool(set(row['gold_ids'])&by_gold)
            row.update(recommended_semantic_equivalent=bool(content_equivalent and same_importance),
                primary_rule='D-061 meaning/material scope/AND-OR/importance; category separate',
                same_importance=bool(same_importance) if one_to_one else None,
                same_category=(row['gold'][0]['category']==row['model'][0]['field']) if one_to_one else None,
                recommendation_provenance='source-based QA proposal; not independent human annotation')
        report.update(stage_id=item['stage_id'],job_id=job,model=model,full_jd=sources[job],
            source_sha256=hashlib.sha256(sources[job].encode()).hexdigest(),result_file=item['result_file'],result_sha256=item['result_sha256'],
            source_qa=item['source_notes'],relations=dict(Counter(r['relation'] for r in report['rows'])),
            reviewed_by='QA check; pending human candidate-specific acceptance')
        if report['unmapped_gold'] or report['unmapped_model']:raise ValueError('Incomplete proposed inventories')
        reviews.append(report)
    return dict(schema_version='cp23-stage2-full-alignment-review-v1',status='complete_proposals_pending_acceptance',
        source_hashes={INV:hashlib.sha256((root/INV).read_bytes()).hexdigest(),GOLD:hashlib.sha256((root/GOLD).read_bytes()).hexdigest()},
        cases=reviews,original_cases=28,process_valid_cases=27,human_verified=False,metrics=None,
        approved_conventions=['D-060 scoped Claude/F00036 complex relation:0TP/2FN/3FP',
                              'D-061 primary equivalence includes importance; category separate'],
        interpretation_gates=['Accept the concrete recommended semantic relations; existing record approval does not approve new model alignments',
            'Shared OR qualifiers inherit from parent under evidence prompt v1.1; historical missing-branch-qualifier flags are not automatically errors',
            'Ordinary proficiency-depth words are not independent obligations under D-035/D-042',
            'Retain missing-case FN accounting; no survivor-only model comparison'],
        workbook_written=False,gold_written=False,api_calls=0)

def render(packet):
    lines=['# CP2.3 Stage-2 candidate-specific extraction alignment review','',
        '3 October 2026. Complete proposals for 27 final drafts plus one retained process failure. D-060/D-061 conventions approved; concrete recommended mappings still await acceptance. No candidate-specific human approval or formal F1 is claimed.',
        '', '## Review boundaries','',
        'Gold and original outputs are unchanged. Primary proposed equivalence follows D-061, with category accuracy separate. Structural splits/merges follow D-054; the exact Claude/F00036 complex relation follows D-060. All original cases remain in the comparison denominator. Recommended booleans remain QA proposals, not accepted relations.', '',
        '**Reassessment of historical source QA:** the active evidence prompt explicitly inherits shared parent qualifiers into every OR branch. Missing repeated words in a branch are not automatically a semantic failure when the parent retains the scope. Ordinary proficiency-depth words also follow D-035/D-042, rather than becoming new obligations. Original QA notes below are historical observations; current mapping notes distinguish these cases from genuine missing context. Neither correction changes gold or authorizes a candidate winner.', '',
        '| Candidate / JD | Gold units | Model units | Proposed relations |','|---|---:|---:|---|']
    for c in packet['cases']:
        lines.append(f"| {c['stage_id']} | {len(c.get('gold_unit_ids',[])) or c.get('gold_units')} | {len(c.get('model_unit_ids',[]))} | {c.get('relations',c['status'])} |")
    lines+=['','## Complete row inventory','', 'Each row below is a proposal awaiting acceptance, including apparent equivalents. Full original JD, branch qualifiers, quotes and typed records are retained in the paired JSON.']
    for c in packet['cases']:
        lines+=['',f"### {c['stage_id']}",'']
        if 'rows' not in c:lines.append('Process failure retained; no final draft, no invented alignment.');continue
        lines += [c['source_qa'],'','| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |','|---|---|---|---|']
        for r in c['rows']:
            gt='; '.join(x['unit_no']+': '+x['unit_text'] for x in r['gold']) or '(none)'
            mt='; '.join(x['unit_id']+': '+x['text'] for x in r['model']) or '(none)'
            clean=lambda s:s.replace('|',' / ').replace('\n',' ')
            lines.append(f"| {clean(gt)} | {clean(mt)} | {r['relation']} / {r['recommended_semantic_equivalent']} | {clean(r['note'])} |")
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    packet=prepare()
    if a.output.exists() or a.report.exists():raise ValueError('Preserve existing review packets')
    a.output.write_text(json.dumps(packet,indent=2,ensure_ascii=False));a.report.write_text(render(packet))
    print(json.dumps({'cases':28,'drafts':27,'status':packet['status'],'api_calls':0}))
