# T02: Clean up the pilot workbook (professional layout, neutral provenance fields)

**Before you give this to Codex:** close the workbook in Excel. The file must not be open while Codex works on it.

---

You are helping with JobFit, a job-matching project. This task changes the **layout and field names** of one labeling workbook and applies a few label changes that Dion has already decided. You do not make new labeling decisions. Follow these instructions exactly.

## File

`evals/pilot/JobFit_Pilot_Labeling_v0.1.xlsx` (keep this file name).

Before any change, save a copy as `evals/pilot/JobFit_Pilot_Labeling_v0.1.backup_20260930.xlsx` (this pattern is git-ignored).

## Read first

- `evals/annotation_guideline_v1.md`
- `docs/decisions.md`, entries D-032 to D-042
- `docs/annotation-workflow.md`

## Part 1. Field names in A_Extraction, B_Evidence, C_Relevance

| Old column | New column | Value mapping |
| --- | --- | --- |
| `ai_suggested` | `label_source` | `TRUE` becomes `model_draft`; `FALSE` becomes `annotator` |
| `status` | `review_status` | `provisional` becomes `pending`; `gold` becomes `approved` |
| `notes` | `draft_note` for rows with `label_source = model_draft`; `review_note` for rows with `label_source = annotator` | Create both columns. Move each existing note into the right one without changing its text, except the tool names in Part 4 |
| `review_action` | `review_action` (unchanged) | |
| `wait_for_rule` | delete the column | |

Final column order:

- **A_Extraction:** `pilot_id, job_id, unit_no, unit_text, source_quote, importance, category, group_id, min_years, label_source, review_status, review_action, draft_note, review_note, guideline_version`
- **B_Evidence:** `cv_id, job_id, unit_no, unit_text, label, check_status, cv_quote, cv_section, label_source, review_status, review_action, draft_note, review_note, guideline_version`
- **C_Relevance:** `cv_id, cv_target, pilot_id, job_id, job_title, relevance_0_3, main_reason, constraint_note, label_source, review_status, review_action, draft_note, review_note, guideline_version`

For C_Relevance, `draft_note` stays empty for now; `main_reason` and `constraint_note` keep their text.

Data validation lists (apply to every data row, and 30 empty rows below):

- `label_source`: `model_draft,annotator`
- `review_status`: `pending,approved`
- `review_action`: `accepted,edited,rejected,added`
- Keep the existing lists for `importance`, `category`, `label`, `check_status`, `cv_section`, `relevance_0_3`.

## Part 2. Label changes already decided by Dion (J4 rows only)

Change only what is listed. For every row you touch, set `guideline_version = v1.1`.

1. **J4-U02** (decision D2): `unit_text` = `Bachelor's degree in Computer Science | Artificial Intelligence | Data Science | related field`, `group_id` = `G4`, `review_action` = `edited`, `review_status` = `approved`, `label_source` = `annotator`.
2. **J4-U12** (decision D4, rule D-039): becomes `REST APIs`, category `skill_tool`, `review_action` = `edited`, `review_status` = `approved`, `label_source` = `annotator`. Add three new rows with the same `source_quote` ("Familiarity with REST APIs, Git, Docker, and CI/CD practices."), importance `required`, category `skill_tool`: **J4-U18** `Git`, **J4-U19** `Docker`, **J4-U20** `CI/CD practices`.
3. **J4-U13** (decision D5, rule D-039): becomes `SQL databases`, category `skill_tool`, `source_quote` = `Working knowledge of SQL and NoSQL databases.`, `review_action` = `edited`, `review_status` = `approved`, `label_source` = `annotator`. Add **J4-U21** `NoSQL databases`, same quote, required, `skill_tool`.
4. **New soft-skill rows** (decision D3), importance `required`, category `soft_skill`:
   - **J4-U14** `Problem-solving`, quote `Strong problem-solving skills and a willingness to learn new technologies.`
   - **J4-U15** `Willingness to learn new technologies`, same quote
   - **J4-U16** `Good communication`, quote `Good communication skills and the ability to work effectively with cross-functional teams.`
   - **J4-U17** `Work effectively with cross-functional teams`, same quote
5. For all new rows J4-U14 to J4-U21: `pilot_id` = `J4`, `job_id` = `F00016`, `label_source` = `model_draft`, `review_action` = `accepted`, `review_status` = `approved`, `draft_note` = `Proposed in QA check (see QA_Log D3, D4, D5); accepted by the annotator.`
6. **Do not change J4-U08 to J4-U11.** Decision D1 is still open. Keep them `pending`.
7. Keep J4 rows sorted by `unit_no`. Rows J4 without any `unit_text` (empty placeholders) are deleted.

Every `source_quote` you write must appear word for word in the J4 text in the `JDs` sheet (a trailing period may be included or left out).

## Part 3. Sheets

1. **Rename `Claude_Check` to `QA_Log`** with columns: `id, type, location, finding, proposal, reference, decision, decision_note`.
   - `type`: `fix` (was FIXED), `decision` (was DECIDE), `todo` (was TODO).
   - `location` joins the old `sheet` and `unit_or_row` columns, for example `A_Extraction: J4-U02`.
   - `decision` and `decision_note` take Dion's `your_decision` and `your_note` values unchanged.
   - Add one column at the end, `status`: `closed` for rows already applied (F1 to F8, D2 to D7), `open` for D1.
2. **Rewrite the `README` sheet** with exactly the text below, one paragraph or table row per row, column A (and B for the tables).
3. **Timing:** keep all times and the minutes formula. Replace any note that names a tool with a neutral note (Part 4).
4. **Questions:** keep all rows. Rename the columns to `id, location, question, proposal, decision`. Put the question number (Q1, Q2, ...) in `id`. Fill `decision` for decided questions: Q1 `D-032`, Q2 `D-035`, Q6 `D-034`, Q9 `D-037`, Q16 `D-033`, Q17 `D-039`; leave others empty.
5. Sheet order: `README, JDs, CVs, A_Extraction, B_Evidence, C_Relevance, Timing, Questions, QA_Log`.
6. **Do not change `JDs` or `CVs` at all.**

### README text

```
JobFit Pilot Labeling Workbook
Pilot for CP2.1. Development data only; none of these items may enter the held-out test set.

Purpose
This workbook holds the pilot labels used to test the annotation guideline, measure review time, and build the first development labels.

Sheets
JDs | Source job descriptions (read-only)
CVs | Synthetic CVs (read-only)
A_Extraction | Requirement units extracted from each JD
B_Evidence | Evidence labels: each requirement unit against a CV
C_Relevance | Overall relevance of each CV to each job (0 to 3)
Timing | Start and end time of every review session
Questions | Open and decided rule questions, with the decision ID
QA_Log | Findings from quality checks and how they were resolved

Workflow (docs/annotation-workflow.md)
1. Pre-annotation | A language model drafts labels following the guideline (label_source = model_draft, review_status = pending).
2. QA check | Automatic and manual checks: exact quotes, complete fields, guideline rules. Findings go to QA_Log.
3. Review | The annotator reviews every row and records review_action (accepted, edited, rejected, added) and the time spent.
4. Approval | Only rows with review_status = approved are used. The next stage starts only when every row of the batch is decided.
5. Export | Approved rows are exported to evals/gold/ with the guideline version and the review statistics.
About 10% of items are labeled by the annotator without any draft (blind sample). Labeling rules are decided only by the annotator.

Fields
label_source | model_draft = drafted by a language model, then reviewed; annotator = created by the annotator
review_status | pending = not decided yet; approved = decided by the annotator
review_action | accepted = draft kept as is; edited = changed by the annotator; rejected = kept for the record but not used; added = new row from the annotator
draft_note | Reasoning attached to the draft
review_note | The annotator's note
guideline_version | Guideline version used for the row (see evals/annotation_guideline_v1.md)

Rules
Annotation guideline v1.1: evals/annotation_guideline_v1.md. Decisions: docs/decisions.md.
```

## Part 4. Neutral wording in cells

This rule covers process text only (notes, README, QA_Log, Timing, Questions). Source text is never changed: the JDs and CVs sheets, and copies of source text such as `source_quote`, `cv_quote`, and `unit_text`, keep words like "OpenAI embeddings" when they are part of a CV or JD.

No process cell may contain the words `Claude`, `Codex`, `ChatGPT`, `OpenAI`, `Anthropic`, `AI-prepared`, `AI proposal`, `AI suggestion`, or `human gold`. Replace them with neutral terms: `model draft`, `draft proposal`, `QA check`, `annotator`, `approved`. Change only these words; do not rewrite the rest of a sentence.

## Part 5. Formatting

- Font Arial 10 in every sheet; header row bold, white text on fill `1F4E79`.
- Freeze the header row in every data sheet; wrap text in quote, note, and reason columns; sensible column widths.
- Conditional formatting on `review_status`: `pending` light yellow `FFF2CC`, `approved` light green `E2EFDA`. On `review_action`: `rejected` light gray `EDEDED` for the whole row.
- No formula errors.

## Do not

- Do not change any label content except Part 2. Do not change `JDs`, `CVs`, or times in `Timing`.
- Do not change any other file except the backup copy and the manifest below. No git commands, no API calls, no new decisions.

## Output and checks to report

Write `evals/pilot/cleanup_manifest_20260930.json` with the checks below, then report them:

1. Row counts before and after for A, B, C (A: J4 grows from 13 to 21 units; others unchanged).
2. For every row outside Part 2, the label content columns are identical before and after (compare values).
3. Every `source_quote` in A and every `cv_quote` in B appears word for word in the JD or CV text.
4. `JDs` and `CVs` are byte-identical in cell values before and after.
5. Search result for the forbidden words in Part 4: zero hits.
6. Counts of `label_source` and `review_status` values per sheet.
7. Formula check: zero errors.
