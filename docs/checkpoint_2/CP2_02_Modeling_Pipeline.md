# CP2.2: Modeling the Extraction, Search, and Evidence Pipeline

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 9. Modeling Deep Learning · official date 29 Sep 2026  
**JobFit version of this checkpoint:** The "deep learning modeling" of JobFit is the pipeline of pretrained models: LLM extraction, embeddings, search, and evidence matching (D-001). No neural network is trained.  
**Planned work:** 30 Sep-1 Oct 2026 · **Actual:** not run yet  
**Status:** PLANNED / NOT RUN · design basis: System Design v1.3

> This report is a plan. It contains no results yet. Results, scores, mentor feedback, and deployment evidence are added only after the work is actually done, with links to the [experiment log](../experiments.md) instead of copied numbers. The plan for all stages is in the [master plan](../master-plan.md).

## 1. Goal of this stage

Build the vertical slice: one CV and one JD produce a structured, checkable evidence report. Then prepare the pieces for the recommendation list: cached extraction for the target jobs and the dense and hybrid search.

## 2. Inputs and prerequisites

- Checkpoint 8 outputs (guideline v1, schemas, scoring rules, fixtures, local database, ledger)
- OpenRouter credit available (D-030)
- Synthetic CVs reviewed by Dion

## 3. Planned method

1. CV text extraction (PyMuPDF, python-docx) and LLM parsing into evidence units with a parsing summary.
2. JD extraction prompt v1 with Pydantic validation and at most 1 repair attempt.
3. Evidence-matching prompt v1: MATCH / PARTIAL / NO_MATCH per requirement unit, with CV quotes checked to exist word for word in the CV.
4. Constraint check: experience duration (v1.2 counting rules), location against a confirmed location, work-authorization statements.
5. Paste JD path end to end: clean, quality signals, extract, preview, match report.
6. Run the 8 development cases and check them by hand.
7. Batch extraction of the 428 target JDs into the versioned cache with the baseline `deepseek-flash`, estimated first. It is re-run if another model is chosen in CP2.3.
8. Embeddings (model per D-020), Baseline 2 dense, and the hybrid FTS + dense search with RRF.
9. Freeze the development / held-out test split at the job-cluster level.

## 4. Planned outputs

- prompt files v1 in `prompts/`
- CV parser, extractor, matcher modules and tests
- extraction cache
- an example report for a synthetic CV
- `evals/splits/`
- this stage report

## 5. Acceptance criteria

- One CV and one pasted JD produce a structured report whose quotes exist in the CV.
- The 8 development cases pass the manual check.
- Cache keys include schema, prompt, model, preprocessing, and guideline versions.
- The extraction status (done / failed) is known for all 428 target jobs.
- The test split is locked before checkpoint 10 starts.

## 6. Evidence to keep

- example report
- manual check sheet for the 8 cases
- extraction success count
- ledger totals
- commit links

## 7. Estimate and dependencies

- **Estimate:** About 1.5 working days. LLM cost: about US$0.25-0.50 for the batch extraction plus small test runs.
- **Depends on:** OpenRouter key in `.env` by the evening of 30 Sep (for extraction and the dense baseline).

## 8. Fallback if blocked

If the OpenAI embedding fails on the Indonesian-CV cases, use the local `multilingual-e5-small`. If extraction fails for some jobs, mark them "could not be analyzed" and continue. If extraction quality is poor, keep it for prompt v2 in checkpoint 10 instead of blocking.

## 9. Checklist

- [ ] CV text extraction (PyMuPDF, python-docx) and LLM parsing into evidence units with a parsing summary.
- [ ] JD extraction prompt v1 with Pydantic validation and at most 1 repair attempt.
- [ ] Evidence-matching prompt v1: MATCH / PARTIAL / NO_MATCH per requirement unit, with CV quotes checked to exist word for word in the CV.
- [ ] Constraint check: experience duration (v1.2 counting rules), location against a confirmed location, work-authorization statements.
- [ ] Paste JD path end to end: clean, quality signals, extract, preview, match report.
- [ ] Run the 8 development cases and check them by hand.
- [ ] Batch extraction of the 428 target JDs into the versioned cache with the baseline `deepseek-flash`, estimated first. It is re-run if another model is chosen in CP2.3.
- [ ] Embeddings (model per D-020), Baseline 2 dense, and the hybrid FTS + dense search with RRF.
- [ ] Freeze the development / held-out test split at the job-cluster level.
- [ ] Acceptance: One CV and one pasted JD produce a structured report whose quotes exist in the CV.
- [ ] Acceptance: The 8 development cases pass the manual check.
- [ ] Acceptance: Cache keys include schema, prompt, model, preprocessing, and guideline versions.
- [ ] Acceptance: The extraction status (done / failed) is known for all 428 target jobs.
- [ ] Acceptance: The test split is locked before checkpoint 10 starts.

## 10. Results

Not run yet.

## 11. Interpretation and limitations

Not run yet.

## 12. Decisions from this stage

None yet. Decisions are recorded in the [decision log](../decisions.md) when they are made.

## 13. Next step

CP2.3 (checkpoint 10): choose the stage-1 method, K, prompt, and model on the development set.
