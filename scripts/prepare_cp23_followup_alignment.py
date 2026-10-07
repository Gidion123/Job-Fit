"""D-064 source-reviewed alignment proposals; no approval or metric fabrication.

Fresh artifacts only. Paid outputs, sources, reviewed labels and runtime stay intact.
"""
from pathlib import Path
import sys
sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1]/'src')]
import argparse, hashlib, json
from collections import Counter
from jobfit.config import REPO_ROOT
from jobfit.eval.alignment import alignment_review
from scripts.prepare_cp23_extraction_alignment import GOLD, gid
from scripts.run_cp23_stage2_followup import RUN, PLAN, STATE
from scripts.run_batch_extraction import development_sources

def one(g, m): return ([g], [m])
def seq(n): return [one(i, f'U{i:02d}') for i in range(1, n+1)]

MAPS = {
    ('gpt-6-sol', 'F00332'): seq(7)+[([8], ['U08','U09'])]+[one(g, f'U{g+1:02d}') for g in range(9,14)]+[([14], ['U15','U16']),one(15,'U17'),one(16,'U18')],
    ('gpt-6-sol', 'F00036'): [one(1,'U07'),one(2,'U08'),one(3,'U09'),one(4,'U02'),one(5,'U03'),one(6,'U04'),one(7,'U10')]+[one(g,f'U{g+3:02d}') for g in range(8,18)],
    ('gpt-6-sol', 'F00815'): seq(8)+[([9],['U09','U10'])]+[one(g,f'U{g+1:02d}') for g in range(10,17)],
    ('gpt-6-sol', 'F00018'): seq(17)+[([18,'18-AWS'],['U18'])]+[one(g,f'U{g:02d}') for g in range(19,24)],
    ('deepseek-v4-pro', 'F00332'): seq(13)+[([14,15],['U14']),one(16,'U15')],
    ('deepseek-v4-pro', 'F00036'): [one(g,m) for g,m in enumerate(['U01','U02','U03','U04a','U04b','U04c','U05','U06a','U06b','U07a','U07b','U07c','U08','U09a','U09b','U10a','U10b'],1)],
    ('deepseek-v4-pro', 'F00309'): [one(g,f'U{g:03d}') for g in range(1,10)],
    ('deepseek-v4-pro', 'F00354'): seq(6)+[([7,8,9,10],['U07'])]+[one(g,m) for g,m in [(11,'U08'),(12,'U09'),(13,'U10'),(14,'U11'),(15,'U12'),(16,'U14'),(17,'U13')]]+[one(g,f'U{g-3:02d}') for g in range(18,29)]+[([29],[f'U{i:02d}' for i in range(26,32)])],
    ('deepseek-v4-pro', 'F00815'): seq(12)+[([13,14,15],['U13']),one(16,'U14')],
    ('deepseek-v4-pro', 'F00010'): seq(9),
    ('deepseek-v4-pro', 'F00018'): seq(6)+[([7,8],['U07'])]+[one(g,f'U{g-1:02d}') for g in range(9,19)]+[one(g,f'U{g-1:02d}') for g in range(19,24)],
}
CONTENT_FAILURES = {
    ('gpt-6-sol','F00036'):{8:'EDA becomes dependent on a named visualization tool rather than the independent reviewed EDA obligation.'},
    ('gpt-6-sol','F00815'):{3:'Reviewed LLM-framework alternative group stored as a simple example-list unit; no assessable branches.',11:'Reviewed vector-technology alternatives stored as a simple example-list unit; no assessable branches.'},
    ('gpt-6-sol','F00018'):{22:'Reviewed Spark/Dask alternative remains unresolved simple composite with needs_review.'},
    ('deepseek-v4-pro','F00036'):{8:'EDA becomes dependent on a named visualization tool instead of the independent reviewed EDA obligation.'},
    ('deepseek-v4-pro','F00354'):{7:'Four AND-listed libraries merged into a single OR choice; reviewed inventory has four independent library obligations.',22:'Validation loses the time-series qualifier.',29:'The reviewed composite interest requirement is split into six units; no automatic TP under D-054.'},
    ('deepseek-v4-pro','F00815'):{9:'FastAPI/Flask branches omit the source and reviewed equivalent-framework route.',13:'Git/testing/CI-CD AND obligations merged into one OR group.'},
    ('deepseek-v4-pro','F00010'):{4:'Explicit similar-framework route omitted from assessable branches although retained in parent text.',5:'Explicit similar-cloud route omitted from assessable branches although retained in parent text.'},
    ('deepseek-v4-pro','F00018'):{11:'One-or-more use-case alternatives stored simple with no assessable branches.'},
}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def prepare():
    plan=json.loads(PLAN.read_text());state=json.loads(STATE.read_text())
    expected={s['stage_id'] for s in plan.get('stages',[]) if s['kind']=='extraction'}
    observed=[r['stage_id'] for r in state['results'] if r['kind']=='extraction']
    if len(expected)!=11 or len(observed)!=11 or set(observed)!=expected:
        raise ValueError('Entire D-064 original extraction scope must finish before review packet')
    gold=[json.loads(line) for line in (REPO_ROOT/GOLD).read_text().splitlines()]
    sources={s['job_id']:s['text'] for s in development_sources(sorted({r['job_id'] for r in state['results']}))}
    # Matching may proceed independently. Bind immutable extraction result files,
    # not the live state file that accumulates unrelated matching observations.
    cases=[]; hashes={str(PLAN.relative_to(REPO_ROOT)):sha(PLAN),GOLD:sha(REPO_ROOT/GOLD)}
    for result in state['results']:
        if result['kind']!='extraction': continue
        key=(result['model'],result['job_id']);job=key[1]
        path=REPO_ROOT/result['result_file']
        if sha(path)!=result['result_sha256']: raise ValueError('Paid output changed')
        hashes[result['result_file']]=sha(path)
        refs=[g for g in gold if g['job_id']==job]
        if result['status']!='done':
            cases.append(dict(stage_id=result['stage_id'],model=key[0],job_id=job,status='retained_process_failure',gold_units=len(refs),model_units=0,metrics=None,result_file=result['result_file']))
            continue
        units=result['extraction']['units']; proposals=[];seen_g=set();seen_m=set()
        for gn,mi in MAPS[key]:
            gi=[gid(job,n) for n in gn]
            notes=[CONTENT_FAILURES.get(key,{}).get(n) for n in gn]
            notes=[n for n in notes if n]
            if len(gn)>1 or len(mi)>1: notes.append('Strict D-054: independently assessable gold/model units are unmatched; no automatic TP for split/merge.')
            proposals.append(dict(gold_ids=gi,model_ids=mi,note=' '.join(notes) or 'Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately.'))
            seen_g.update(gi);seen_m.update(mi)
        for g in refs:
            if g['unit_no'] not in seen_g: proposals.append(dict(gold_ids=[g['unit_no']],model_ids=[],note='Reviewed obligation omitted.'))
        for u in units:
            if u['unit_id'] not in seen_m: proposals.append(dict(gold_ids=[],model_ids=[u['unit_id']],note='Outside reviewed inventory. A source-supported opening statement is still FP against the fixed reference; FP is not automatically fabrication.'))
            if any(not q.strip() or q not in sources[job] for q in u['source_quotes']): raise ValueError('Source quote invalid')
        case=alignment_review(refs,units,proposals)
        bad={gid(job,n) for n in CONTENT_FAILURES.get(key,{})}
        for row in case['rows']:
            one_to_one=row['relation']=='one_to_one'
            same_importance=one_to_one and row['gold'][0]['importance']==row['model'][0]['importance']
            row.update(recommended_semantic_equivalent=bool(one_to_one and same_importance and not set(row['gold_ids'])&bad),
                same_importance=same_importance,same_category=bool(one_to_one and row['gold'][0]['category']==row['model'][0]['field']),
                primary_rule='D-061 meaning/material scope/AND-OR/importance; category separate',
                recommendation_provenance='source-based assisted QA proposal; no independent human annotation')
        if case['unmapped_gold'] or case['unmapped_model']: raise ValueError('Incomplete mapping inventory')
        case.update(stage_id=result['stage_id'],model=key[0],job_id=job,result_file=result['result_file'],gold_units=len(refs),model_units=len(units),
            source_quote_check='all exact',full_jd=sources[job],source_sha256=hashlib.sha256(sources[job].encode()).hexdigest(),
            unresolved_model_units=[u['unit_id'] for u in units if u['needs_review']],
            whole_jd_scope='four common reference JDs' if key[0]=='gpt-6-sol' else 'seven common development JDs')
        cases.append(case)
    relations=Counter(r['relation'] for c in cases for r in c.get('rows',[]))
    return dict(schema_version='cp23-followup-alignment-review-v1',status='pending_human_acceptance_of_assisted_QA',
        human_verified=False,metrics=None,cases=cases,relations=dict(relations),original_extraction_cases=11,
        source_hashes=hashes,approved_conventions=['D-054 strict split/merge','D-061 category separate'],
        limits=['D-063 did not accept these new candidate outputs.',
            'Primary equivalence and operational needs_review are distinct; unresolved flags can hold live scores even on equivalent extraction text.',
            'Reference model is not ground truth; same reviewed source units and rubric apply.',
            'Reference scope73 gold units; round-two scope120; never compare unlike aggregate scopes.'],
        workbook_written=False,gold_written=False,api_calls=0)

def render(packet):
    lines=['# D-064 reference and round-two extraction alignment review','',
        '3 October 2026. Source-reviewed proposals for the new candidate outputs. Approval of D-064 authorizes execution; it does not approve these alignments. D-063 applies to the earlier candidate packet and fixed matcher adapter only.',
        '', '## Review and accounting','',
        'Recommended equivalents retain meaning, material qualifiers, logical alternatives and importance. Category errors are reported separately under D-061. D-054 strictly counts independently assessable splits/merges as unmatched units. No gold, source or prediction was corrected. No formal extraction F1 or model winner is published here.',
        '', '| Model / JD | Gold units | Model units | Proposed relations |','|---|---:|---:|---|']
    for c in packet['cases']:
        lines.append(f"| {c['stage_id']} | {c['gold_units']} | {c['model_units']} | {dict(Counter(r['relation'] for r in c.get('rows',[])))} |")
    lines+=['','The GPT reference scope has four whole JDs/73 units. DeepSeek Pro has seven whole JDs/120 units. Reference comparisons must use the common four-JD subset of each other model, retaining original failures. Unresolved model flags remain operational concerns independently of semantic equivalence.',
        '', '## Complete proposed inventory','',
        'Every gold/model unit appears exactly once in the JSON inventory. Full source, original quotes, alternative branches and category/importance checks are attached there. Apparent equivalents below also require acceptance; the table is assisted QA, not independent annotation.']
    clean=lambda s:str(s).replace('|',' / ').replace('\n',' ')
    for c in packet['cases']:
        lines+=['',f"### {c['stage_id']}",'']
        if not c.get('rows'):lines.append('Original process failure retained; no invented alignment.');continue
        lines+=['| Gold IDs and text | Model IDs and text | Relation / recommended equivalent | Review note |','|---|---|---|---|']
        for r in c['rows']:
            gt='; '.join(x['unit_no']+': '+x['unit_text'] for x in r['gold']) or '(none)'
            mt='; '.join(x['unit_id']+': '+x['text'] for x in r['model']) or '(none)'
            note=r['note']
            if r['relation']=='one_to_one' and not r['same_category']:note+=' Category differs; reported separately.'
            if r['relation']=='one_to_one' and not r['same_importance']:note+=' Importance differs; primary equivalence fails.'
            lines.append(f"| {clean(gt)} | {clean(mt)} | {r['relation']} / {r['recommended_semantic_equivalent']} | {clean(note)} |")
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--report');a=p.parse_args()
    out=prepare()
    if Path(a.output).exists() or (a.report and Path(a.report).exists()):raise ValueError('Preserve previous artifacts')
    with Path(a.output).open('x') as f:json.dump(out,f,indent=2,ensure_ascii=False)
    if a.report:Path(a.report).write_text(render(out))
    print(json.dumps({k:out[k] for k in ['status','original_extraction_cases','relations']}))
