"""FTS + dense reciprocal rank fusion; scores are retrieval scores, not match %."""
from jobfit.search import dense, fts


def rrf(rankings, *, k=60, top_k=20):
    if k <= 0 or top_k < 1:
        raise ValueError('RRF k and top_k must be positive')
    scores = {}
    for rows in rankings:
        seen = set()
        for position, row in enumerate(rows, 1):
            job_id = row['job_id']
            if job_id in seen:
                raise ValueError('duplicate job in ranking')
            seen.add(job_id)
            scores[job_id] = scores.get(job_id, 0) + 1 / (k + position)
    ordered = sorted(scores, key=lambda job_id: (-scores[job_id], job_id))[:top_k]
    return [{'job_id': job_id, 'score': scores[job_id]} for job_id in ordered]


def rank(conn, cv_skills, query, spec, *, job_ids, top_k=20, branch_depth=20, k=60):
    if branch_depth < top_k:
        raise ValueError('branch_depth must cover top_k')
    dense_rows = dense.rank(conn, query, spec, job_ids=job_ids, top_k=branch_depth)
    fts_rows = fts.rank(conn, cv_skills, top_k=branch_depth, job_ids=job_ids)
    return rrf([fts_rows, dense_rows], k=k, top_k=top_k)
