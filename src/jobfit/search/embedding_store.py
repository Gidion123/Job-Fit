"""Committed per-batch pgvector storage. Old versions are retained, never mixed."""
from dataclasses import asdict
import json
from jobfit.search.embeddings import validate_vector


def vector_literal(vector):
    return '[' + ','.join(str(float(x)) for x in vector) + ']'


class JobEmbeddingStore:
    def __init__(self, conn, run_id):
        self.conn, self.run_id = conn, run_id

    def contains(self, spec, doc):
        row = self.conn.execute(
            'SELECT 1 FROM job_embedding_versions WHERE job_id=%s AND profile_id=%s '
            'AND content_hash=%s AND input_hash=%s AND dimensions=%s AND model=%s',
            (doc.document_id, spec.profile_id, doc.source_hash, doc.input_hash, spec.dimensions, spec.model)
        ).fetchone()
        return row is not None

    def save_batch(self, spec, pairs):
        # The caller uses an autocommit connection: each transaction here is a
        # durable batch, not a nested savepoint under one long-running build.
        if not self.conn.autocommit:
            raise ValueError('embedding store requires autocommit for durable batch transactions')
        with self.conn.transaction():
            for doc, vector in pairs:
                validate_vector(vector, spec.dimensions)
                self.conn.execute(
                    'INSERT INTO job_embedding_versions '
                    '(job_id,profile_id,model,dimensions,preprocessing_version,profile_spec,'
                    'content_hash,input_hash,input_tokens,original_tokens,truncated,embedding,run_id) '
                    'VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s::vector,%s) '
                    'ON CONFLICT DO NOTHING',
                    (doc.document_id, spec.profile_id, spec.model, spec.dimensions,
                     spec.preprocessing_version, json.dumps(asdict(spec)), doc.source_hash,
                     doc.input_hash, doc.input_tokens, doc.original_tokens, doc.truncated,
                     vector_literal(vector), self.run_id))
