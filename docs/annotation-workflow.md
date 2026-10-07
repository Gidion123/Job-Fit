# Annotation Workflow

**Decisions:** D-015, D-016, D-038, D-047 · **Guideline:** [v1.3 for current manual review](../evals/annotation_guideline_v1_3.md); [v1.2 historical reference](../evals/annotation_guideline_v1.md) · **Applies to:** every labeling batch in CP2 and CP3

JobFit uses **model-assisted labeling** (pre-annotation with human review). A language model drafts labels, quality checks catch mechanical errors, and the annotator reviews and decides every row. This keeps labeling fast while every label that is used is a human decision.

## Stages

```text
1. PRE-ANNOTATION   A language model drafts labels following the guideline
        ↓            label_source = model_draft, review_status = pending
2. QA CHECK         Automatic and manual checks: exact quotes, complete fields,
        ↓            guideline rules. Findings go to the QA_Log sheet
3. REVIEW           The annotator reviews every row: accepted / edited / rejected / added
        ↓            Start and end time of each session are recorded
4. APPROVAL GATE    Only approved rows are used. The next stage starts only when
        ↓            every row of the batch is decided
5. EXPORT           Approved rows go to evals/gold/ (CSV or JSONL) with the guideline
                     version and the review statistics
```

## Roles

| Role | Who | Does | Does not |
| --- | --- | --- | --- |
| Pre-annotation | Codex (OpenAI) | Drafts labels in the labeling workbook, following a written task prompt in `evals/annotation_tasks/` | Decide rules, change sources, edit other files |
| QA check and documentation | Claude (Anthropic) | Checks drafts and the annotator's rows, writes the QA log, guideline, code, and decision entries | Approve labels |
| Annotator and decision owner | Dion | Reviews and approves every row, labels the blind sample, decides every rule question | |

Only one assistant edits a given file at a time. The workbook must be closed in Excel while an assistant works on it.

## Rules

1. **Every used label is approved by the annotator.** Rows with `review_status = pending` are never used for evaluation.
   - **Silver labels (D-044, D-045):** model drafts that the annotator has not reviewed. They are stored in `evals/silver/`, used only to explore (for example to compare search methods early), and every configuration choice is confirmed on gold. A spot check never turns a whole batch into gold; only the rows the annotator reviewed and approved become gold.
   - **Test labels are blind first (D-046):** the annotator labels test items without seeing any draft. The drafting model then only checks quotes, completeness, and rule consistency. A test item that starts from a model draft keeps `label_source = model_draft` and is reported separately.
2. **Rule questions are decided by the annotator**, recorded in the Questions sheet and in [decisions.md](decisions.md). The model that drafts labels never decides a rule.
3. **Blind sample and development exception.** D-038's original approximately 10% blind sample includes pilot J4. Its original answers are frozen before QA suggestions. Dion approved D-047 for the current expanded development batches: complete model drafts followed by human review, with no blind development subset. Do not report that review as blind agreement. Held-out test remains blind-first under D-046; preserve its original answers before QA suggestions.
4. **Sources are read-only.** Job descriptions and CVs in the workbook are never edited.
5. **Every change is recorded:** `review_action` on the row, and a QA_Log entry for fixes proposed by a QA check. `accepted` means the draft content was kept unchanged; any change to the content (including importance or a split) is `edited`; a row created because of the reviewer's decision is `added` with `label_source = annotator`. Rows that are still pending have no `review_action`.

## Quality numbers reported

| Number | How it is computed | Why |
| --- | --- | --- |
| Acceptance rate | Share of model-draft rows with `review_action = accepted` | Shows how much the annotator changed. A rate near 100% is a warning sign of shallow review |
| Blind agreement | Agreement between the model draft and the annotator on the blind sample | Measures draft quality without anchoring |
| Review time per item | From the Timing sheet | Sets the gold-set size (D-043) |

## Known limitation

The drafts come from one model family (OpenAI), and some LLM candidates compared in CP2 are from the same family. Labels drafted this way may favor similar models. Current development batches are draft-first under D-047 and may anchor the reviewer. Human edits and the separate blind-first test reduce this risk; the evaluation report must state the provenance and limitation.

## Current development preparation exception (D-048, 2 Oct 2026)

D-048 originally used `evals/labeling/JobFit_Development_Labeling_v0.1.xlsx` for preparation. The current reviewed receipt is listed in [labeling README](../evals/labeling/README.md). The pilot remains intact and the two older development books are archived. Dion authorized complete A/B/C drafts before extraction approval. This changes draft preparation order only. Approved rows are retained, new rows remain pending, and human approval is required before gold export. A changes invalidate dependent B judgments and can affect C. Recheck them before export. D-045 review priorities and D-046 held-out test procedure remain unchanged. Role-neutral administrative wording must not alter JD/CV content, tool names used as skills, or verbatim evidence quotes.


## Guideline transition (D-049, 2 Oct 2026)

Current manual review uses v1.3: no redundant umbrella contribution, contextual importance, technical-category distinction, and preservation of and/or/composites. Existing labels keep their actual versions until individually re-reviewed. A structural or semantic A edit requires B/C recheck. No workbook or gold was changed by publishing these rules. Runtime v1.3 adoption was subsequently verified offline; historical v1.2 remains a reference; do not pass a v1.3 guideline to the old prompt that hard-codes the conflicting D-041 precedent. Read the v1.3 adoption checklist before export or evaluation.


## Completed review submission (2 October 2026)

Dion submitted all A/B/C decisions. Current receipt, counts and follow-ups: [review report](checkpoint_2/supporting/Development_Labeling_Review_20261002.md). Approved status alone does not resolve source changes, missing review notes, group semantics or dependent recheck. Do not rerun preparation scripts on the receipt. No new gold has been promoted.
