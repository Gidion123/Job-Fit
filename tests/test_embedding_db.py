"""Opt-in PostgreSQL integration with TEMP fixture tables; no API calls."""
import os
from dataclasses import replace
import pytest
from jobfit.db.session import connect
from jobfit.db.models import SCHEMA_SQL
from jobfit.search.embedding_store import JobEmbeddingStore
from jobfit.search.embeddings import EmbeddingSpec, prepare
from jobfit.search.dense import QueryEmbedding, rank
from jobfit.search import hybrid

pytestmark = pytest.mark.skipif(not os.getenv('JOBFIT_DB_TESTS'), reason='requires local JobFit database')


class Tokenizer:
    def encode(self, text):
        return list(text)


def test_real_pgvector_isolation_filters_stale_hashes_and_batch_rollback():
    spec = EmbeddingSpec('fixture/model',2,'fixture-v1',100,'fixture','1')
    doc = lambda name, source: prepare(name,'python sql '+name,spec,Tokenizer(),source)
    with connect() as conn:
        conn.autocommit = True
        before = conn.execute('SELECT job_id,content_hash FROM jobs ORDER BY job_id').fetchall()
        conn.execute(SCHEMA_SQL)
        conn.execute('CREATE TEMP TABLE jobs (LIKE public.jobs INCLUDING ALL)')
        conn.execute('CREATE TEMP TABLE job_embedding_versions (LIKE public.job_embedding_versions INCLUDING ALL)')
        for name in ('DEV_A','DEV_B','TEST_C'):
            conn.execute('INSERT INTO jobs(job_id,content_hash,snapshot_id,title,description_clean,role_group) '
                         "VALUES (%s,'current','fixture','python sql','python sql','target')", (name,))
        store = JobEmbeddingStore(conn,'fixture')
        store.save_batch(spec,[(doc('DEV_A','current'),[1.,0.]),(doc('DEV_B','current'),[0.,1.]),
                               (doc('TEST_C','current'),[1.,0.])])
        store.save_batch(spec,[(doc('DEV_A','old'),[0.,1.])])
        other = replace(spec, dimensions=3, model='other/model')
        store.save_batch(other,[(doc('DEV_A','current'),[0.,0.,1.])])
        query = QueryEmbedding(spec.profile_id,[1.,0.])
        rows = rank(conn,query,spec,job_ids={'DEV_A','DEV_B'})
        assert [r['job_id'] for r in rows] == ['DEV_A','DEV_B']
        assert rows[0]['score'] == pytest.approx(1)
        assert rows[1]['score'] == pytest.approx(0)
        fused = hybrid.rank(conn,{'python','sql'},query,spec,job_ids={'DEV_A','DEV_B'},top_k=2)
        assert {r['job_id'] for r in fused} == {'DEV_A','DEV_B'}
        bad = doc('DEV_B','new')
        with pytest.raises(ValueError):
            store.save_batch(spec,[(bad,[1.,0.]), (doc('DEV_A','new'),[1.])])
        assert not store.contains(spec,bad)
        assert store.contains(spec,doc('DEV_A','current'))
        after = conn.execute('SELECT job_id,content_hash FROM public.jobs ORDER BY job_id').fetchall()
        assert after == before and len(after) == 632
