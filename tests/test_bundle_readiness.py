import json
import hashlib
from pathlib import Path
import pytest
from jobfit.eval.bundle_readiness import prepare_reviewed_bundle, inspect_acceptance_probe, check_source_hashes
ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT/'evals/gold/development_v13_reviewed_20261002_r2'
RETRIEVAL=ROOT/'evals/results/cp22_retrieval_top30_20261002_03.json'


def test_reviewed_bundle_is_inventoried_without_claiming_metrics_ready():
    r=prepare_reviewed_bundle(ROOT,BUNDLE,RETRIEVAL)
    assert r['gold_inventory']=={'A':1058,'B':1364,'C':69}
    assert r['verified_top30_runs']==12 and r['status']=='blocked'
    assert r['metrics'] is None and r['winner'] is None and r['api_calls']==0
    assert len(r['judgment_coverage'])==12


def test_cv_markdown_hash_is_protected_but_export_time_readme_is_not(tmp_path):
    import hashlib
    cv=tmp_path/'data/synthetic_cvs/cv.md';cv.parent.mkdir(parents=True)
    cv.write_text('approved synthetic CV')
    expected=hashlib.sha256(cv.read_bytes()).hexdigest()
    check_source_hashes(tmp_path,{'data/synthetic_cvs/cv.md':expected,
                                  'evals/gold/README.md':'historical-documentation-hash'})
    cv.write_text('changed synthetic CV')
    with pytest.raises(ValueError,match='cv.md'):
        check_source_hashes(tmp_path,{'data/synthetic_cvs/cv.md':expected})


@pytest.mark.parametrize('fault',['scope','duplicate','shallow','stale'])
def test_invalid_saved_retrieval_cannot_be_used(fault,tmp_path):
    d=json.loads(RETRIEVAL.read_text());r=d['runs'][0]
    if fault=='scope':r['split']='test'
    elif fault=='duplicate':d['runs'].append(dict(r))
    elif fault=='shallow':r['ranking']=r['ranking'][:20]
    else:r['corpus_sha256']='stale'
    p=tmp_path/'bad.json';p.write_text(json.dumps(d))
    with pytest.raises(ValueError):prepare_reviewed_bundle(ROOT,BUNDLE,p)


PROBE=ROOT/'reports/quality_probe/cp22_extraction_repair_v13_20261003.json'

def test_scoped_acceptance_does_not_promote_baseline_or_enable_metrics(tmp_path):
    # Synthetic receipt: historical source hashes must not be rewritten as code evolves.
    result={'job_id':'CV1_F00332_match','status':'done','versions':{'fixture':'synthetic'},
            'report':{'score':{'status':'on_hold'}},
            'provenance':{'src/jobfit/llm/structured.py':hashlib.sha256((ROOT/'src/jobfit/llm/structured.py').read_bytes()).hexdigest()}}
    digest=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    result.update(result_sha256=digest,operational_check={'result_sha256':digest,
        'checks':{k:'pass' for k in ['quotes','coverage','grouping','qualifiers','importance']},
        'human_annotation_approval':False})
    fixture=tmp_path/'synthetic_probe.json'
    fixture.write_text(json.dumps({'status':'complete','run_id':'synthetic','jobs':[result['job_id']],'results':[result]}))
    r=prepare_reviewed_bundle(ROOT,BUNDLE,RETRIEVAL,fixture)
    assert r['scoped_live_acceptance']['status']=='operationally_checked'
    assert r['scoped_live_acceptance']['baseline_promoted'] is False
    assert r['status']=='blocked' and r['metrics'] is None
    assert not any('broad' in x.lower() or 'promotion' in x.lower() for x in r['blockers'])
    assert r['carryover_notes']  # D-050: later materialization cannot block its own prerequisite comparison


@pytest.mark.parametrize('fault',['incomplete','reservation','unchecked','tampered','test_scope'])
def test_unverified_acceptance_cannot_open_readiness(fault,tmp_path):
    d=json.loads(PROBE.read_text())
    if fault=='incomplete':d['status']='awaiting_semantic_check'
    elif fault=='reservation':d['reservations']=[{'upper_usd':.02}]
    elif fault=='unchecked':d['results'][-1]['operational_check']['checks']['quotes']='uncertain'
    elif fault=='tampered':d['results'][-1]['report']['score']['score_pct']=100
    else:d['jobs'][-1]=d['results'][-1]['job_id']='CV3_F00332_match'
    p=tmp_path/'probe.json';p.write_text(json.dumps(d))
    with pytest.raises(ValueError):inspect_acceptance_probe(ROOT,p)


def test_historical_acceptance_does_not_certify_changed_repair_code():
    with pytest.raises(ValueError,match='Acceptance source/configuration has changed'):
        inspect_acceptance_probe(ROOT,PROBE)
