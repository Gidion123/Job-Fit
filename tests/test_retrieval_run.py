"""Technical retrieval safety, without labels, real vectors, API or database."""
from pathlib import Path
from types import SimpleNamespace as NS
import json
import pytest
from jobfit.eval import retrieval_run as runner
from jobfit.search import keyword, hybrid
from jobfit.search.embeddings import EmbeddingSpec


def test_ranking_scope_duplicates_and_nonfinite():
    for rows in [[{'job_id':'test','score':1}],
                 [{'job_id':'dev','score':1}]*2,
                 [{'job_id':'dev','score':float('nan')}]]:
        with pytest.raises(ValueError): runner.checked_ranking(rows,{'dev'},30)


def test_failure_is_recorded_without_exception_text_or_label():
    def fail(): raise RuntimeError('private database URL must not reach output')
    times=iter([1,1.02])
    r=runner.measure('B1',fail,eligible={'dev'},k=30,context={},clock=lambda:next(times))
    assert r['status']=='failed' and r['error_type']=='RuntimeError'
    assert r['ranking']==[] and r['latency_ms']==pytest.approx(20)
    assert 'private' not in json.dumps(r) and 'label' not in r


def test_success_records_actual_depth_and_timing():
    times=iter([1,1.004])
    r=runner.measure('B0',lambda:[{'job_id':'dev','score':0}],eligible={'dev'},k=30,
                     context={'eligible_count':1},clock=lambda:next(times))
    assert r['status']=='success' and r['returned_count']==1
    assert r['latency_ms']==pytest.approx(4)


@pytest.mark.parametrize('changed',['snapshot_id','content_hash','skills_v0','description_clean','role_group'])
def test_database_drift_rejected(changed):
    source={'dev':{'content_hash':'h','title':'T','normalized_title':None,'description_clean':'Python',
                   'role_group':'target','skills':['python']}}
    row=dict(job_id='dev',snapshot_id=runner.SNAPSHOT_ID,content_hash='h',title='T',normalized_title=None,
             description_clean='Python',role_group='target',skills_v0=['python'])
    runner.validate_jobs(source,[row])
    row[changed]='wrong'
    with pytest.raises(ValueError):runner.validate_jobs(source,[row])


def test_query_cache_missing_never_falls_back(tmp_path,monkeypatch):
    d=tmp_path/'data/synthetic_cvs';d.mkdir(parents=True)
    for file in runner.CV_FILES.values():(d/file).write_text('Skills: Python')
    spec=EmbeddingSpec('fixture/model',2,'v1',100,'fake','1')
    with pytest.raises(ValueError,match='no inference fallback'):
        runner.cached_queries(tmp_path,[spec],{spec.profile_id:NS(encode=lambda s:list(s.encode()))})


def test_ties_are_deterministic_not_input_order():
    jobs=[{'job_id':j,'skills_v0':['python']} for j in ['b','a']]
    assert [r['job_id'] for r in keyword.rank({'python'},jobs)]==['a','b']
    rows=hybrid.rrf([[{'job_id':'b'},{'job_id':'a'}],[{'job_id':'a'},{'job_id':'b'}]],k=60,top_k=30)
    assert [r['job_id'] for r in rows]==['a','b']


def test_output_refuses_existing_artifact(tmp_path,monkeypatch):
    import importlib.util,sys
    spec=importlib.util.spec_from_file_location('retrieval_cli',Path(__file__).parents[1]/'scripts/run_retrieval_comparison.py')
    cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
    d=tmp_path/'evals/results';d.mkdir(parents=True)
    out=d/'old.json';out.write_text('historic')
    monkeypatch.setattr(cli,'REPO_ROOT',tmp_path)
    monkeypatch.setattr(sys,'argv',['runner','--output',str(out)])
    monkeypatch.setattr(cli,'connect',lambda:pytest.fail('must refuse before DB'))
    with pytest.raises(FileExistsError):cli.main()
    assert out.read_text()=='historic'
