"""Loads the CP1 snapshot into PostgreSQL. Idempotent: running it again updates rows in place.

Source: data/processed/jobs_features.jsonl (910 clusters). Only the 632 EDA candidates
(`is_auditable = true`) are loaded; 428 of them are in the target role families.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import psycopg

from jobfit.config import REPO_ROOT, SNAPSHOT_ID
from jobfit.db.models import SCHEMA_SQL

DEFAULT_SOURCE = REPO_ROOT / "data" / "processed" / "jobs_features.jsonl"
EXPECTED = {"eda_candidates": 632, "target": 428}

COLUMNS = [
    "job_id", "job_uid", "content_hash", "snapshot_id", "title", "normalized_title", "company",
    "role_family", "role_group", "country_code", "city_normalized", "analysis_geo", "work_mode",
    "experience_bucket", "years_min", "years_max", "jd_language", "jd_quality", "posted_at",
    "apply_url", "google_url", "skills_v0", "description_clean",
]


def read_candidates(path: Path = DEFAULT_SOURCE) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if not r.get("is_auditable"):
                continue
            rows.append({
                "job_id": r["final_cluster_id"],
                "job_uid": r.get("job_uid"),
                "content_hash": r["content_hash"],
                "snapshot_id": SNAPSHOT_ID,
                "title": r["title"],
                "normalized_title": r.get("normalized_title"),
                "company": r.get("company"),
                "role_family": r.get("role_family"),
                "role_group": r.get("role_group"),
                "country_code": r.get("country_code"),
                "city_normalized": r.get("city_normalized"),
                "analysis_geo": r.get("analysis_geo"),
                "work_mode": r.get("work_mode"),
                "experience_bucket": r.get("experience_bucket"),
                "years_min": r.get("years_min"),
                "years_max": r.get("years_max"),
                "jd_language": r.get("jd_language"),
                "jd_quality": r.get("jd_quality"),
                "posted_at": r.get("posted_at") or r.get("posted_at_derived"),
                "apply_url": r.get("apply_url"),
                "google_url": r.get("google_url"),
                "skills_v0": list(r.get("skills") or []),
                "description_clean": r.get("description_clean") or "",
            })
    return rows


def load(conn: psycopg.Connection, rows: list[dict]) -> dict:
    placeholders = ", ".join(["%s"] * len(COLUMNS))
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in COLUMNS if c != "job_id")
    sql = (
        f"INSERT INTO jobs ({', '.join(COLUMNS)}) VALUES ({placeholders}) "
        f"ON CONFLICT (job_id) DO UPDATE SET {updates}, loaded_at = now()"
    )
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
        cur.executemany(sql, [[r[c] for c in COLUMNS] for r in rows])
        cur.execute("SELECT role_group, count(*) FROM jobs WHERE snapshot_id = %s GROUP BY role_group", (SNAPSHOT_ID,))
        by_group = dict(cur.fetchall())
        cur.execute("SELECT count(*) FROM jobs WHERE snapshot_id = %s", (SNAPSHOT_ID,))
        total = cur.fetchone()[0]
    conn.commit()
    return {"snapshot_id": SNAPSHOT_ID, "loaded": total, "by_role_group": by_group,
            "matches_cp1": total == EXPECTED["eda_candidates"] and by_group.get("target") == EXPECTED["target"]}


def summarize(rows: list[dict]) -> dict:
    return {"rows": len(rows), "by_role_group": dict(Counter(r["role_group"] for r in rows))}
