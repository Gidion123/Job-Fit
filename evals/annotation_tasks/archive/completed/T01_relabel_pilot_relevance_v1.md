# T01: Re-draft pilot relevance labels under guideline v1.1

**Give this to Codex only after T02 is done, and after Dion has finished reviewing sheets A_Extraction and B_Evidence and closed the workbook in Excel.**

---

You are helping with JobFit, a job-matching project. You draft labels; a human (Dion) reviews every row. Follow these instructions exactly.

## Read first

1. `evals/annotation_guideline_v1.md` (guideline v1.1). Part D and Part A6 matter most.
2. `docs/decisions.md`, entries D-032 to D-042, and `docs/annotation-workflow.md`.
3. The workbook `evals/pilot/JobFit_Pilot_Labeling_v0.1.xlsx`, sheets `JDs`, `CVs`, `A_Extraction`, `B_Evidence`, `C_Relevance`.

## Task

Re-draft all 10 rows in sheet `C_Relevance` (CV1 and CV2 against J1 to J5) under guideline v1.1 Part D.

- Judge in **automatic mode**: the target is the four target role families (AI/ML engineering, data science, GenAI/LLM, software AI). All five pilot jobs are inside them. The `cv_target` column is only a preference note and must not produce a 0 by itself (D-037).
- Base the rating on CV evidence for the **technical** required requirements and on constraints. Soft skills and location do not lower relevance by themselves (D-032, D-033). An explicit experience conflict gives at most 1.
- Where a unit in `A_Extraction` or `B_Evidence` is `review_status = approved`, use that version, not the earlier draft.
- For J4 and J5 there are no evidence rows. Read the JD and the CV directly.

## How to fill each C_Relevance row

| Column | Value |
| --- | --- |
| `relevance_0_3` | Your new rating |
| `main_reason` | One or two sentences naming the concrete CV evidence and the main gaps |
| `constraint_note` | The constraint that drove the rating, quoting the JD words, or empty |
| `label_source` | `model_draft` |
| `review_status` | `pending` |
| `guideline_version` | `v1.1` |
| `review_action` | leave empty (the annotator fills it) |
| `draft_note` | Old rating for comparison, in the form `v0.1 draft: 0` |

Do not put tool names (Claude, Codex, OpenAI, Anthropic) in any cell.

## Do not

- Do not change sheets `A_Extraction`, `B_Evidence`, `JDs`, `CVs`, `Timing`, or `README`. In particular, do not add or edit any J4 extraction rows: J4 is Dion's blind item.
- Do not change any row where `review_status = approved`.
- Do not change any other file in the repository except the manifest below. No git commands, no API calls, no new decisions. If a rule is unclear, write it in the `Questions` sheet as a question for Dion and continue.
- Do not raise or lower a rating to get a particular distribution of 0 to 3.

## Output

1. The saved workbook, same name and format.
2. A manifest `evals/pilot/relevance_redraft_manifest_20260930.json` with: date, guideline version, the 10 old and new ratings, and the checks below.

## Checks to run and report

- Exactly 10 `C_Relevance` rows changed; no other sheet changed (compare cell values before and after).
- Every row has a rating from 0 to 3, a `main_reason`, a `draft_note` with the old rating, `guideline_version = v1.1`, `review_status = pending`, `label_source = model_draft`.
- Any JD words quoted in `constraint_note` appear exactly in the JD text.
- A short table of old versus new ratings, with one line per changed rating explaining why.
