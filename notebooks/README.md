# JobFit Research Notebook (Checkpoint 1)

One notebook: **`01_research.ipynb`**, with five main sections plus setup. The explanation pattern is **Why, Result, What it means, Note, Next**, plus a glossary and a mapping to the 7 CP1 stages at the start. The extra headings I added are kept.

| Section | Playbook | Output |
| --- | --- | --- |
| 1. Data and data understanding | CP1.1-1.2 | raw hashes + frozen derived files, funnel, data unit, goals, and research questions (1.4) |
| 2. Data quality | CP1.3 | `jobs_clean.jsonl`, `jobs_clean_meta.csv` |
| 3. Transformation | CP1.4 | `jobs_features.jsonl`, `jobs_features.csv`, review queue |
| 4. EDA | CP1.5 | 14 figures, including the three agreed extra ones |
| 5. Insight | CP1.6 | `CP1_research_summary.json` |

The three extra EDA figures stay: skills per role, GenAI skill bundles, and the early-career pool for beginners, including education. Posting date is only in section 2.6. There is no posting age figure and no extra junior versus senior figure. The existing title × experience figure is kept.

## Running from a clean kernel

From Terminal, go to the project root (the folder that has `src/`, `scripts/`, `data/`). Use the research Python environment, not another Python without the dependencies.

```bash
cd project-job-fit
python -m pip install -r requirements-research.txt
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/01_research.ipynb
python scripts/refresh_cp1_docs.py
python -m pytest -q tests/
```

Last full run: 27 September 2026, on Python 3.11.15 with the versions in `requirements-research.txt` (pandas 2.3.3, numpy 2.3.5, matplotlib 3.10.6). The versions of every run are recorded in `CP1_research_summary.json`. The notebook kernel must point to an environment with those dependencies.

All processed files and the 14 PNGs are made by the notebook. The notebook reads `data/interim/snapshots/CP1_20260926/` and checks the raw and derived hashes; it does not silently read the latest interim files. It does not need an API key or internet.

`python scripts/build_corpus.py` is optional, to rebuild interim from raw. It does not change the frozen snapshot that the notebook reads. The audit compared the offline rebuild output with the snapshot. To replace the snapshot in the future, make a new version and do an explicit review.

## How to read the results

- Unit of analysis = estimated job cluster; dedup is still v0, and the 3 UNSURE pairs are flagged for re-check.
- `is_auditable` means an EDA candidate based on length and source filters, not a verified job.
- The early-career pool (entry/≤2 years) does not yet mean the skill, education, location, or work authorization requirements are met.
- `geo_stratum` is the collection stratum; EDA uses `analysis_geo`, with UNKNOWN when there is no country evidence.
- `CP1_human_review_queue.jsonl` (the review queue) is not a gold set yet. Development/regression cases are kept separate from the CP2 held-out test.
- If the rules or data change, check the notebook text, run it again, then regenerate the two documents with `refresh_cp1_docs.py`. The interpretation text still needs review; the script does not treat it as correct automatically.

Read `docs/checkpoint_1/supporting/CP1_Research_Audit.md` and `docs/checkpoint_1/supporting/CP1_Current_Handoff.md` for the status, revisions, and the steps toward the PPT.

## Companion reports per stage

The [CP1.1 to CP1.6 reports](../docs/checkpoint_1/README.md) explain the work step by step. The notebook explanations were expanded with what the results mean, examples, trade-offs, and implications for JobFit. The code and my Run All output stay the same; the text changes do not need a re-run.

## 02_cp2_heldout_evaluation.ipynb (CP2.4-CP2.6)

Makes the held-out tables and figures 9-11 from the saved CP2.4 report, run files and labels `test_v13_cp24_r1`. No API call, no tuning. It refuses to overwrite existing outputs.

```bash
cd project-job-fit
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/02_cp2_heldout_evaluation.ipynb
```

Outputs: `reports/figures/cp2/fig09_cp24_heldout_primary_v1.png`, `fig10_cp24_supplementary_familiar_v1.png`, `fig11_cp24_order_decomposition_v1.png`, and `evals/results/cp24/cp25_tables_v1/` (CSV + `receipt.json`).

## 03_post_test_quality_optimization.ipynb (Phase A, D-089)

The experiment story for Phase A: baseline, failure taxonomy, hypotheses, prompt experiments, comparison, selection, confirmation and conclusion. It only reads `evals/results/quality_optimization/` (no model call, no hard-coded metric) and checks that nothing there points at CP2.4 material. Sections without results yet say so.

```bash
cd project-job-fit
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/03_post_test_quality_optimization.ipynb
```
