"""Offline audit helpers for CP1. All outputs are exploratory signals, not gold labels."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


def verify_snapshot(root: Path) -> dict:
    snapshot = root / "data/interim/snapshots/CP1_20260926"
    raw = json.loads((snapshot / "SNAPSHOT_MANIFEST.json").read_text())
    audit = json.loads((snapshot / "RESEARCH_INPUT_HASHES.json").read_text())
    for item in raw["raw_inputs"] + audit["inputs"]:
        path = root / item["path"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Snapshot integrity mismatch: {item['path']}")
    return {"raw_inputs_verified": len(raw["raw_inputs"]), "frozen_derived_inputs_verified": len(audit["inputs"]),
            "input_hashes": audit["inputs"]}


def analysis_geo(country, sampling_stratum: str) -> str:
    # Remote probes remain a separate, disjoint cohort even if a country was mentioned.
    if sampling_stratum == "remote_unverified":
        return "remote_unverified"
    if country == "ID":
        return "indonesia"
    if isinstance(country, str) and country:
        return "foreign"
    return "unknown"


def standardized_skill_comparison(id_jobs, foreign_jobs, skills, min_cell=3):
    """Direct standardization to pooled role x length-bin weights on common support.

    Fixed bins in characters: <1500, 1500-2499, 2500-3999, 4000-5999, >=6000.
    Each retained cell needs min_cell records in EACH region. No causal interpretation;
    employer, publisher, seniority, language, exact length and query selection may confound.
    """
    groups = []
    for region, df in [("ID", id_jobs), ("foreign", foreign_jobs)]:
        df = df.copy()
        df["region"] = region
        df["length_bin"] = pd.cut(df.clean_length, [0, 1500, 2500, 4000, 6000, float("inf")],
                                   right=False, labels=["<1500", "1500-2499", "2500-3999", "4000-5999", ">=6000"])
        groups.append(df)
    combined = pd.concat(groups)
    counts = combined.groupby(["role_family", "length_bin", "region"], observed=True).size().unstack("region", fill_value=0)
    counts = counts.reindex(columns=["ID", "foreign"], fill_value=0)
    counts = counts[(counts.ID >= min_cell) & (counts.foreign >= min_cell)].copy()
    if counts.empty:
        return {"method": "role_x_length_direct_standardization", "status": "insufficient_common_support", "skills": {}}
    counts["weight"] = counts.sum(axis=1) / counts.sum().sum()
    result = {}
    for skill in skills:
        rates = {}
        for region in ["ID", "foreign"]:
            rate = 0.0
            for (role, length), row in counts.iterrows():
                cell = combined[(combined.region == region) & (combined.role_family == role) & (combined.length_bin == length)]
                rate += row.weight * cell.skills.apply(lambda s: skill in s).mean()
            rates[region + "_pct"] = 100 * rate
        rates["difference_pp"] = rates["ID_pct"] - rates["foreign_pct"]
        result[skill] = rates
    return {"method": "role_x_length_direct_standardization", "status": "descriptive_only", "min_cell_per_region": min_cell,
            "eligible_n": {"ID": len(id_jobs), "foreign": len(foreign_jobs)},
            "retained_n": {"ID": int(counts.ID.sum()), "foreign": int(counts.foreign.sum())},
            "strata": counts.reset_index().to_dict(orient="records"), "skills": result}


def skill_counts(df, skills):
    return {s: {"n": int(df.skills.apply(lambda v: s in v).sum()), "of": len(df),
                "pct": float(100 * df.skills.apply(lambda v: s in v).mean()) if len(df) else None} for s in skills}
