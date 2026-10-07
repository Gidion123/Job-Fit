"""Read-only workbook -> versioned reviewed-record gold. Explicit --promote required."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import argparse,csv,json,io
import openpyxl
from jobfit.config import REPO_ROOT
from jobfit.eval.development_gold import read_workbook,plan,promote,sha
from jobfit.search.embeddings import cv_body
from jobfit.eval.review_export import identity,SHEETS

BUNDLE='development_v13_reviewed_20261002'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--promote',action='store_true')
    p.add_argument('--bundle',default=BUNDLE,help='New versioned bundle; existing plans/exports are never overwritten')
    a=p.parse_args()
    if not a.bundle or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in a.bundle):
        raise ValueError('Invalid bundle name')
    root=REPO_ROOT;workbook=root/'evals/labeling/JobFit_Development_Labeling_v1.3.xlsx'
    snap,whash=read_workbook(workbook)
    manifest=json.loads((root/'evals/splits/split_manifest.json').read_text())
    for name,h in manifest['output_hashes'].items():
        if sha(root/'evals/splits'/name)!=h:raise ValueError('Frozen split changed')
    dev=set((root/'evals/splits/dev_job_ids.txt').read_text().splitlines())
    canonical={}
    for line in (root/'data/processed/jobs_features.jsonl').read_text().splitlines():
        r=json.loads(line)
        if r['final_cluster_id'] in dev:canonical[r['final_cluster_id']]=r['description_clean']
    cvs={r['cv_id']:cv_body(root/'data/synthetic_cvs'/r['file']) for r in snap['CVs']}
    workbook_counts={s:len(snap[s]) for s in SHEETS}
    legacyA=[json.loads(l) for l in (root/'evals/gold/extraction_gold.jsonl').read_text().splitlines()]
    legacyB=[json.loads(l) for l in (root/'evals/gold/evidence_gold.jsonl').read_text().splitlines()]
    awjobs={r['job_id'] for r in snap['JDs']};bwpairs={(r['cv_id'],r['job_id']) for r in snap['B_Evidence']}
    ai={(r['job_id'],r['unit_no']):r for r in legacyA}
    for r in legacyA:
        if r['job_id'] not in awjobs:
            snap['A_Extraction'].append(dict(r,_origin='historical_extraction_gold.jsonl'))
    for r in legacyB:
        if (r['cv_id'],r['job_id']) not in bwpairs:
            snap['B_Evidence'].append(dict(r,unit_text=ai[(r['job_id'],r['unit_no'])]['unit_text'],_origin='historical_evidence_gold.jsonl'))
    pilot=root/'evals/pilot/JobFit_Pilot_Labeling_v0.1.xlsx'
    w=openpyxl.load_workbook(io.BytesIO(pilot.read_bytes()),read_only=True,data_only=True)
    rr=iter(w['C_Relevance'].values);cols=next(rr);legacyC=[dict(zip(cols,r)) for r in rr if r[0] in {'CV1','CV2'}];w.close()
    with (root/'evals/gold/relevance_gold.csv').open() as f:exported={(r['cv_id'],r['job_id']):r for r in csv.DictReader(f)}
    cpairs={(r['cv_id'],r['job_id']) for r in snap['C_Relevance']}
    for r in legacyC:
        key=(r['cv_id'],r['job_id'])
        if key not in cpairs and key in exported:
            if r['review_status']!='approved' or int(exported[key]['relevance'])!=r['relevance_0_3']:raise ValueError('Pilot relevance provenance mismatch')
            snap['C_Relevance'].append(dict(r,_origin='historical_pilot_workbook_and_relevance_gold.csv'))
    alljobs={r['job_id'] for sheet in SHEETS for r in snap[sheet]}
    for j in sorted(alljobs-awjobs):snap['JDs'].append({'job_id':j,'jd_text':canonical[j]})
    private=root.parent/'_private_not_for_github/notes'
    receiptfile=private/'JobFit_Codex1_To_Codex2_20261002_Review_Closure.md'
    receipt={'source':'user-confirmed review closure coordination note + current explicit export authorization',
       'source_sha256':sha(receiptfile),'user_confirmed_BC_after_final_A':True,
       'confirmation_scope':'User confirms B/C checked after final A in reviewed submission; delegated cloud/AWS follow-up from closure note. No per-row review date inferred.',
       'reviewed_at':None,'independent_annotation_claim':False}
    report=plan(snap,development_ids=dev,canonical_jds=canonical,canonical_cvs=cvs,approval_receipt=receipt)
    report['workbook_counts']=workbook_counts
    report['historical_pilot_additions']={sheet:len(snap[sheet])-workbook_counts[sheet] for sheet in SHEETS}
    protected=[root/'data/processed/jobs_features.jsonl',root/'evals/splits/split_manifest.json',root/'evals/pools/dev_pool.csv',pilot]
    protected += list((root/'evals/gold').glob('*.*'))
    protected += [root/'data/synthetic_cvs'/r['file'] for r in snap['CVs']]
    hashes={str(p.relative_to(root)):sha(p) for p in protected if p.is_file()}
    stage=root/'evals/staging'/a.bundle;stage.mkdir(parents=True,exist_ok=True)
    stagefile=stage/('promotion_plan.json' if a.promote else 'validation_plan.json')
    with stagefile.open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    if a.promote:
        m=promote(report,root/'evals/gold'/a.bundle,workbook=workbook,workbook_sha256=whash,source_hashes=hashes)
        print(json.dumps({'promoted':m['counts'],'workbook_unchanged':sha(workbook)==whash,'bundle':a.bundle},indent=2))
    else:print(json.dumps({'counts':report['counts'],'historical_additions':report['historical_pilot_additions'],'plan':str(stagefile)},indent=2))

if __name__=='__main__':main()
