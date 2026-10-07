# JobFit Documentation

| Location | Contents | Applies to |
| --- | --- | --- |
| [`data-contract.md`](data-contract.md) | Field definitions, data units, and corpus lineage | All checkpoints |
| [`checkpoint_1/`](checkpoint_1/README.md) | CP1.1 to CP1.6 reports, one file per stage | CP1 (done) |
| [`checkpoint_1/supporting/`](checkpoint_1/supporting/) | CP1 inventory, insights, audit, handoff, and API policy | CP1 |
| [`repo-structure.md`](repo-structure.md) | What every folder and file of the application is for, and in which stage it is filled | CP2 and CP3 |
| [`master-plan.md`](master-plan.md) | Dates, dependencies, budget, labeling plan, and the plan for every CP2 and CP3 stage; the source of truth for CP3.1-CP3.7 scope, acceptance and Definition of Done | CP2 and CP3 |
| [`checkpoint_2/`](checkpoint_2/README.md) | CP2.1 to CP2.7 reports (bootcamp checkpoints 8 to 14), CP2.8 Phase A and the [CP2 closeout audit](checkpoint_2/CP2_Closeout_Audit_20261007.md) | CP2 (closed 7 Oct 2026, D-094) |
| [`checkpoint_2/supporting/`](checkpoint_2/supporting/) | Versioned implementation, audits and review evidence; historical preparation in archive/ | CP2 |
| [`checkpoint_3/`](checkpoint_3/README.md) | CP3.1 to CP3.7 reports (bootcamp checkpoints 15 to 21); evidence and results | CP3 (plan frozen 7 Oct 2026, D-095 to D-100) |
| [`checkpoint_3/CP3_Execution_Plan.md`](checkpoint_3/CP3_Execution_Plan.md) | Daily CP3 checklist: task, priority, dependency, owner, status, validation, evidence | CP3 |
| [`production-corpus.md`](production-corpus.md) | Mutable production job database: seed, query manifest, twice-monthly sync, dedupe, lifecycle, extraction cache (D-098, planned) | CP3 |
| [`privacy-threat-model.md`](privacy-threat-model.md) | Privacy design (D-051) and the CP3 public live privacy model and release gate (section 11, planned) | CP2 and CP3 |

Project logs:

| File | Contents |
| --- | --- |
| [`decisions.md`](decisions.md) | Decision log: what was decided, by whom, what it replaced, and why (D-001 onward) |
| [`experiments.md`](experiments.md) | Experiment matrix and every experiment run, with metrics, cost, and git SHA |
| [`failures.md`](failures.md) | Failure cases found in testing and what was done about them |
| [`annotation-workflow.md`](annotation-workflow.md) | How labels are made: model draft, QA check, annotator review, approval, export (D-038) |
| [`cv-coach-plan.md`](cv-coach-plan.md) | CV coach (D-036): v1 built (deterministic); CP3 refinements planned (D-093 B) |

The project reference documents (Canonical v2.1, Execution Playbook v2.1, Research v2, PRE-CP0 v2) and the system design history (v1.0 to v1.3) are in the project folder outside this repository.


Historical labeling record (2 October): [review submission and follow-ups](checkpoint_2/supporting/Development_Labeling_Review_20261002.md). Evaluation files: [evals README](../evals/README.md). Older versions are kept for provenance; use the current indexes, not older preparation instructions.
