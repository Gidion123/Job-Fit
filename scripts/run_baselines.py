"""Runs Baseline 0 (skill overlap) and Baseline 1 (PostgreSQL FTS) for the synthetic CVs.

Pool: the target role families (automatic mode, D-009), 428 jobs. No LLM and no API cost.
Output: evals/results/cp21_baselines.json, plus a short table in the terminal.
Usage:  python scripts/run_baselines.py
"""
from __future__ import annotations

import json
import sys
from datetime import date

from jobfit.config import REPO_ROOT, SNAPSHOT_ID
from jobfit.db.session import connect
from jobfit.search import fts, keyword

CVS = {
    "CV1": "data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md",
    "CV2": "data/synthetic_cvs/cv_02_career_switcher_ai_engineer_en.md",
    "CV3": "data/synthetic_cvs/cv_03_junior_ml_engineer_1yr_en.md",
}
PILOT_JOBS = {"J1": "F00022", "J2": "F00073", "J3": "F00034", "J4": "F00016", "J5": "F00114"}
TOP_K = 20


def main() -> int:
    out = {"date": date.today().isoformat(), "snapshot_id": SNAPSHOT_ID, "pool": "role_group = target",
           "top_k": TOP_K, "methods": {"B0": "skill overlap, skills_v0", "B1": "PostgreSQL FTS, simple config, ts_rank_cd"},
           "cvs": {}}
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT job_id, title, skills_v0 FROM jobs WHERE role_group = 'target' AND snapshot_id = %s", (SNAPSHOT_ID,))
            jobs = [{"job_id": j, "title": t, "skills_v0": s} for j, t, s in cur.fetchall()]
        titles = {j["job_id"]: j["title"] for j in jobs}
        print(f"Pool: {len(jobs)} target jobs")
        for cv_id, path in CVS.items():
            skills = keyword.cv_skills((REPO_ROOT / path).read_text(encoding="utf-8"))
            b0_all = keyword.rank(skills, jobs)
            b1_all = fts.rank(conn, skills, top_k=len(jobs))
            b0_rank = {r["job_id"]: i + 1 for i, r in enumerate(b0_all)}
            b1_rank = {r["job_id"]: i + 1 for i, r in enumerate(b1_all)}
            b0, b1 = b0_all[:TOP_K], b1_all[:TOP_K]
            overlap10 = len({r["job_id"] for r in b0[:10]} & {r["job_id"] for r in b1[:10]})
            out["cvs"][cv_id] = {
                "cv_skills_v0": sorted(skills),
                "B0_top": [{**r, "title": titles[r["job_id"]]} for r in b0],
                "B1_top": [{**r, "title": titles[r["job_id"]]} for r in b1],
                "B1_matching_jobs": len(b1_all),
                "overlap_at_10": overlap10,
                "pilot_job_ranks": {p: {"job_id": j, "B0": b0_rank.get(j), "B1": b1_rank.get(j)} for p, j in PILOT_JOBS.items()},
            }
            print(f"\n{cv_id}: {len(skills)} v0 skills; B1 matched {len(b1_all)} jobs; top-10 overlap B0/B1 = {overlap10}")
            for p, j in PILOT_JOBS.items():
                print(f"  {p} {j}: B0 rank {b0_rank.get(j)}, B1 rank {b1_rank.get(j)}")
    dest = REPO_ROOT / "evals" / "results" / "cp21_baselines.json"
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nSaved {dest.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
