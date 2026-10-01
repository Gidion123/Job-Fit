"""Baseline 0 (B0): skill overlap with the CP1 rule-based skill list (skill_aliases_v0).

Score = share of the job's v0 skills that also appear in the CV. Ties keep job_id order, so
the result is deterministic. This is an internal stage-1 score; it is never shown as a match %.
"""
from __future__ import annotations

from collections.abc import Iterable

from jobfit.jobs.skills import extract_skills


def cv_skills(cv_text: str) -> set[str]:
    return set(extract_skills(cv_text))


def rank(cv_skill_set: set[str], jobs: Iterable[dict], top_k: int | None = None) -> list[dict]:
    """jobs: dicts with job_id and skills_v0. Returns dicts with job_id, score, matched."""
    out = []
    for job in jobs:
        job_skills = set(job.get("skills_v0") or [])
        matched = sorted(job_skills & cv_skill_set)
        score = len(matched) / len(job_skills) if job_skills else 0.0
        out.append({"job_id": job["job_id"], "score": round(score, 4), "matched": matched,
                    "job_skill_count": len(job_skills)})
    out.sort(key=lambda r: (-r["score"], -len(r["matched"]), r["job_id"]))
    return out[:top_k] if top_k else out
