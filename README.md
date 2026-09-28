# JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis

JobFit helps early-career job seekers in AI and data find jobs that fit their real profile. It compares a CV with job postings, shows which requirements are met, partly met, or missing, and points to the exact CV text behind each result. The goal is honest matching: no match claim without evidence.

Final project for the Data Science and Machine Learning bootcamp at Dibimbing (Batch 42).

![Status](https://img.shields.io/badge/status-CP1%20complete-brightgreen)
![Next](https://img.shields.io/badge/next-CP2%20in%20progress-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Tests](https://img.shields.io/badge/tests-24%20passing-brightgreen)

## Project status

| Checkpoint | Focus | Dates | Status |
| --- | --- | --- | --- |
| CP1 | Data collection, cleaning, feature transformation, EDA | until 27 Sep 2026 | Done |
| CP2 | Gold set, retrieval baselines, evidence matching, evaluation | 28 Sep to 4 Oct 2026 | In progress |
| CP3 | API, database, app, testing, deployment | 5 to 11 Oct 2026 | Planned |

This README is updated at the end of every checkpoint.

## Problem

Job boards show many postings, but early-career candidates cannot easily tell which ones are realistic for them. Many postings labeled "AI" are not AI roles, many titles without a level still ask for 3+ years of experience, and "match scores" in existing tools rarely explain why. JobFit focuses on three questions:

1. Which jobs fit my target role and experience level?
2. For each requirement in a job, is there evidence in my CV?
3. Which skill gaps matter most for the jobs I want?

## CP1 results (done)

CP1 built and explored the job corpus. All numbers come from `data/processed/CP1_research_summary.json`, which the notebook produces.

**Corpus funnel**

| Step | Count |
| --- | ---: |
| API result slots collected (JSearch / Google for Jobs) | 1,314 |
| Estimated unique jobs after dedup | 910 |
| EDA candidates (full job description, no generic form) | 632 |
| Target-role jobs (AI, ML, data science, GenAI) | 428 |
| Indonesian target jobs | 175 |
| Early-career pool (entry level or up to 2 years) | 49 |

![Corpus funnel](reports/figures/cp1/fig01_funnel.png)

**Main findings**

- 128 of 405 titles with no level marker still ask for 3+ years of experience. The title alone is not a safe filter.
- 49 of 463 titles that mention AI are not target roles. Role labels need the job description, not only the title.
- Skill needs differ by role: statistics appears in 78% of data science jobs but only 2% of GenAI jobs.
- RAG appears in 53% of jobs that mention LLMs and only 4% of jobs that do not.
- 79.6% of the 372 Indonesian EDA candidates are in Jabodetabek (Greater Jakarta), and work mode is unclear in 76.3% of them.

These findings shaped the design: filter by target role first, check experience from the job text, and match skills per requirement with evidence.

All CP1 role, level, and skill labels are rule-based v0. Their accuracy will be measured against the CP2 gold set.

Full reports: [CP1.1 to CP1.6](docs/checkpoint_1/README.md).

## Roadmap

### CP2: Matching and evaluation (next)

- Build a gold set with an annotation guideline for requirement and evidence labels.
- Compare retrieval baselines: keyword, full-text search, dense embeddings, and hybrid search (RRF).
- Build a vertical slice: one CV and one pasted job description in, per-requirement results with CV evidence out.
- Evaluate with Evidence Macro-F1, NDCG@10 and P@5 for retrieval, and safety checks (citation accuracy, zero unsupported claims).

### CP3: Product and deployment

- Backend API with FastAPI and PostgreSQL with pgvector.
- Streamlit app for the full flow: filter jobs, pick jobs, compare with a CV, see match results and gaps.
- End-to-end tests and CI/CD.
- Deployment and final presentation.

## Repository structure

```text
project-job-fit/
├── config/          Skill alias list (v0)
├── data/
│   ├── raw/         JSearch API responses (collection provenance)
│   ├── interim/     Dedup output and the frozen snapshot CP1_20260926
│   ├── processed/   Clean corpus, features, and the CP1 summary
│   └── research/    Collection batch plans
├── docs/            Checkpoint reports and the data contract
├── evidence/        Collection evidence, provider benchmark, related work
├── notebooks/       CP1 research notebook
├── reports/figures/ EDA charts
├── scripts/         Collection scripts and the doc refresh script
├── src/             Python modules (jobs: cleaning, corpus, features, skills; viz: chart style)
└── tests/           Tests for data rules and collection guards
```

## Getting started

Requirements: Python 3.11.

```bash
git clone <repo-url>
cd project-job-fit

python3.11 -m venv env-job-fit
source env-job-fit/bin/activate        # Windows: env-job-fit\Scripts\activate
python -m pip install -r requirements-research.txt
```

Reproduce CP1 (runs offline, no API key needed). The notebook needs the raw JSearch snapshot, which is not included in this public repository (see [Data](#data)). All notebook outputs, processed files, and figures are already committed, so the results can be read without running anything.

```bash
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/01_research.ipynb
python scripts/refresh_cp1_docs.py
python -m pytest -q tests/
```

The notebook reads the frozen snapshot in `data/interim/snapshots/CP1_20260926/` and checks its hashes before running, so the outputs stay the same across runs. More details are in [notebooks/README.md](notebooks/README.md).

The collection scripts in `scripts/` are kept for provenance. They are not needed to rebuild the EDA and they need a JSearch API key, which is never stored in this repository.

## Data

- Source: JSearch API (OpenWeb Ninja), which returns Google for Jobs results. Snapshot `CP1_20260926`.
- Scope: AI and data roles, mainly Indonesia, with a foreign comparison group.
- The corpus is a query-based sample. Percentages describe this corpus, not the whole job market.
- Included: processed corpus and features (`data/processed/`), dedup outputs, snapshot manifest and hashes, and small API response samples in `evidence/`.
- Not included: raw API responses (`data/raw/`) and `jsearch_records.jsonl`. They contain full responses and recruiter contact details from some job descriptions. The processed files have contact details removed.
- Field definitions are in the [data contract](docs/data-contract.md).
- Job posting content belongs to the original publishers. The data is used for this study only.

## Tech stack

- CP1: Python, pandas, NumPy, matplotlib, Jupyter, pytest
- Planned for CP2 and CP3: sentence embeddings, PostgreSQL with pgvector, FastAPI, Streamlit, GitHub Actions

## Author

Gidion Depari, Dibimbing Data Science and Machine Learning Batch 42
