"""Exact cosine search; explicit profile and eligible IDs prevent split mixing."""
from dataclasses import dataclass
from jobfit.search.embeddings import validate_vector
from jobfit.search.embedding_store import vector_literal


@dataclass(frozen=True)
class QueryEmbedding:
    profile_id: str
    vector: list[float]


def rank(conn, query: QueryEmbedding, spec, *, job_ids, top_k=20):
    if query.profile_id != spec.profile_id:
        raise ValueError('query and job embedding profiles differ')
    validate_vector(query.vector, spec.dimensions)
    if top_k < 1:
        raise ValueError('top_k must be positive')
    if not job_ids:
        return []
    # Apply all scope/version filters before LIMIT. Stale source hashes excluded.
    rows = conn.execute(
        'SELECT e.job_id, 1 - (e.embedding <=> %s::vector) AS score '
        'FROM job_embedding_versions e JOIN jobs j ON j.job_id=e.job_id '
        'WHERE e.profile_id=%s AND e.model=%s AND e.dimensions=%s '
        'AND e.preprocessing_version=%s AND e.content_hash=j.content_hash '
        'AND e.job_id=ANY(%s) ORDER BY score DESC, e.job_id LIMIT %s',
        (vector_literal(query.vector), spec.profile_id, spec.model, spec.dimensions,
         spec.preprocessing_version, sorted(set(job_ids)), top_k)).fetchall()
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('ambiguous current embeddings; inspect input hashes')
    return [{'job_id': job_id, 'score': float(score)} for job_id, score in rows]
