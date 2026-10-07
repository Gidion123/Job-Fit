# CP2.3 result versions

The original CP2.3 JSON files remain in `evals/results/` because frozen run plans and documentation link to those exact paths. New development end-to-end outputs are stored under `end_to_end_dev/` by run ID. This directory is a catalog for new versions; it is not a rewritten copy of historical results.

See `docs/checkpoint_2/CP2_03_Model_Comparison.md` for the current interpretation and `docs/path_map_20261004.md` for the path policy. Never replace an earlier run result to improve a metric. Test results are separate and must not be used to choose CP2.3 settings.
