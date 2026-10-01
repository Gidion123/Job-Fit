# Annotation Workflow

**Decisions:** D-015, D-016, D-038 · **Guideline:** [annotation_guideline_v1.md](../evals/annotation_guideline_v1.md) · **Applies to:** every labeling batch in CP2 and CP3

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
2. **Rule questions are decided by the annotator**, recorded in the Questions sheet and in [decisions.md](decisions.md). The model that drafts labels never decides a rule.
3. **Blind sample.** About 10% of items are labeled by the annotator without any draft (`label_source = annotator`). The first one is pilot J4. The annotator's original blind answers are frozen in a JSON snapshot before any QA suggestion is applied.
4. **Sources are read-only.** Job descriptions and CVs in the workbook are never edited.
5. **Every change is recorded:** `review_action` on the row, and a QA_Log entry for fixes proposed by a QA check. `accepted` means the draft content was kept unchanged; any change to the content (including importance or a split) is `edited`; a row created because of the reviewer's decision is `added` with `label_source = annotator`. Rows that are still pending have no `review_action`.

## Quality numbers reported

| Number | How it is computed | Why |
| --- | --- | --- |
| Acceptance rate | Share of model-draft rows with `review_action = accepted` | Shows how much the annotator changed. A rate near 100% is a warning sign of shallow review |
| Blind agreement | Agreement between the model draft and the annotator on the blind sample | Measures draft quality without anchoring |
| Review time per item | From the Timing sheet | Sets the gold-set size (D-043) |

## Known limitation

The drafts come from one model family (OpenAI), and some LLM candidates compared in CP2 are from the same family. Labels drafted this way may favor similar models. The blind sample and the annotator's edits reduce this risk, and the evaluation report states it.
