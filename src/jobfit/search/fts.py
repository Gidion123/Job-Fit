"""Baseline 1 (B1): PostgreSQL full-text search over title (weight A) and JD text (weight B).

The query is built from the CV: every alias of every v0 skill found in the CV becomes a phrase
query, joined with OR. Skills defined only by a regex (for example R) are skipped, because their
names are too short to search safely. Ranking uses ts_rank_cd; ties keep job_id order.
"""
from __future__ import annotations

import yaml
from psycopg import sql

from jobfit.jobs.skills import DEFAULT_ALIAS_FILE


def query_phrases(cv_skill_set: set[str], alias_file=DEFAULT_ALIAS_FILE) -> list[str]:
    spec = yaml.safe_load(open(alias_file, encoding="utf-8"))["skills"]
    phrases: list[str] = []
    for name in sorted(cv_skill_set):
        for alias in spec.get(name, {}).get("aliases", []):
            alias = alias.strip()
            if len(alias) >= 2 and alias not in phrases:
                phrases.append(alias)
    return phrases


def build_query(phrases: list[str], scoped: bool = False) -> tuple[sql.Composed, list[str]]:
    if not phrases:
        raise ValueError("no query phrases: the CV has no v0 skills")
    tsq = sql.SQL(" || ").join(sql.SQL("phraseto_tsquery('simple', {})").format(sql.Placeholder()) for _ in phrases)
    query = sql.SQL(
        "WITH q AS (SELECT ({tsq}) AS query) "
        "SELECT j.job_id, ts_rank_cd(j.search, q.query) AS score "
        "FROM jobs j, q WHERE j.search @@ q.query AND j.role_group = ANY(%s) "
        "{scope} "
        "ORDER BY score DESC, j.job_id LIMIT %s"
    ).format(tsq=tsq, scope=sql.SQL("AND j.job_id = ANY(%s)" if scoped else ""))
    return query, phrases


def rank(conn, cv_skill_set: set[str], top_k: int = 20, role_groups=("target",), *, job_ids=None) -> list[dict]:
    if top_k < 1:
        raise ValueError("top_k must be positive")
    phrases = query_phrases(cv_skill_set)
    if not phrases or job_ids is not None and not job_ids:
        return []
    query, params = build_query(phrases, scoped=job_ids is not None)
    scope_params = [sorted(set(job_ids))] if job_ids is not None else []
    with conn.cursor() as cur:
        cur.execute(query, [*params, list(role_groups), *scope_params, top_k])
        return [{"job_id": j, "score": round(float(s), 4)} for j, s in cur.fetchall()]
