"""Duplicate leakage and reproducibility gates for the T03 split."""
from scripts.make_splits import PILOT, load_inputs, split_jobs
import copy
import json
import pytest


def test_real_split_coverage_pilot_duplicates_and_reproducibility():
    jobs, pairs, _ = load_inputs()
    dev, test, _ = split_jobs(jobs, pairs)
    assert len(dev) == len(test) == 214
    assert not set(dev) & set(test)
    assert set(dev) | set(test) == {j["final_cluster_id"] for j in jobs}
    assert PILOT <= set(dev)
    assert all((a in dev) == (b in dev) for a, b in pairs)
    assert split_jobs(list(reversed(jobs)), list(reversed(pairs)))[:2] == (dev, test)
    from scripts.make_splits import ROOT
    assert (ROOT / "evals/splits/dev_job_ids.txt").read_text().splitlines() == dev
    assert (ROOT / "evals/splits/test_job_ids.txt").read_text().splitlines() == test


def test_transitive_duplicate_component_forced_by_pilot():
    jobs = [{"final_cluster_id": str(i), "role_family": "a" if i % 2 else "b",
             "experience_bucket": "unknown"} for i in range(8)]
    dev, test, _ = split_jobs(jobs, [("0", "1"), ("1", "2")], pilot={"2"})
    assert {"0", "1", "2"} <= set(dev)
    assert not set(dev) & set(test)
    assert len(dev) + len(test) == 8


@pytest.mark.parametrize("field", ["total", "strata", "output_hashes", "input_hashes", "pilot_ids"])
def test_manifest_corruption_is_rejected(field):
    from scripts.make_splits import ROOT, validate_frozen
    out = ROOT / "evals/splits"
    manifest = json.loads((out / "split_manifest.json").read_text())
    damaged = copy.deepcopy(manifest)
    damaged[field] = None
    content = {name: (out / name).read_text() for name in manifest["output_hashes"]}
    with pytest.raises(ValueError, match="manifest differs"):
        validate_frozen(damaged, manifest, out, content)


def test_modified_split_file_is_rejected(tmp_path):
    from scripts.make_splits import validate_frozen
    (tmp_path / "dev_job_ids.txt").write_text("WRONG\n")
    with pytest.raises(ValueError, match="deterministic rebuild"):
        validate_frozen({}, {}, tmp_path, {"dev_job_ids.txt": "EXPECTED\n"})


def test_all_stratum_counts_and_saved_hashes_are_correct():
    from collections import Counter
    from scripts.make_splits import ROOT, sha
    jobs, _, _ = load_inputs()
    out = ROOT / "evals/splits"
    manifest = json.loads((out / "split_manifest.json").read_text())
    dev = set((out / "dev_job_ids.txt").read_text().splitlines())
    total = Counter(j["role_family"] + " / " + j["experience_bucket"] for j in jobs)
    counts = Counter(j["role_family"] + " / " + j["experience_bucket"]
                     for j in jobs if j["final_cluster_id"] in dev)
    for key, n in total.items():
        assert manifest["strata"][key] == {"total": n, "development": counts[key], "test": n-counts[key]}
        assert abs(2 * counts[key] - n) <= 1
    for name, digest in manifest["output_hashes"].items():
        assert sha(out / name) == digest
