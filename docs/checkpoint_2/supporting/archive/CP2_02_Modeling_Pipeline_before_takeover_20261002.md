# CP2.2: Modeling the Extraction, Search, and Evidence Pipeline

**Project:** JobFit: Evidence-Grounded Job Matching and Skill-Gap Analysis for Early-Career AI & Data Job Seekers  
**Bootcamp checkpoint:** 9. Modeling Deep Learning · official date 29 Sep 2026  
**JobFit version of this checkpoint:** The "deep learning modeling" of JobFit is the pipeline of pretrained models: LLM extraction, embeddings, search, and evidence matching (D-001). No neural network is trained.  
**Planned work:** 1-2 Oct 2026 (moved: CP2.1 ended on 1 Oct) · **Actual:** started 1 Oct 2026  
**Status:** IN PROGRESS · design basis: System Design v1.3

> Current status, 2 October2026: runtime guideline v1.3, JD prompt v1.2, evidence prompt v1.1. Upload/parser/extractor/matcher/paste backend, versioned cache and two-model retrieval are implemented. Local top30 technical retrieval is verified; v1.3 semantic acceptance and human fixture review remain open. Workbook v1.3 review closure is reported under delegated QA; no actual gold export. Read the [single acceptance/technical summary](supporting/CP22_Acceptance_Review_20261002.md) and closure checklist below. Dated results below preserve their historical scope, versions and costs.

## 1. Goal of this stage

Build the vertical slice: one CV and one JD produce a structured, checkable evidence report. Then prepare the pieces for the recommendation list: cached extraction for the target jobs and the dense and hybrid search.

## 2. Inputs and prerequisites

- Checkpoint 8 outputs (guideline v1, schemas, scoring rules, fixtures, local database, ledger)
- OpenRouter credit available (D-030)
- Synthetic CVs reviewed by Dion (done)
- Approved D-044, D-045, and D-046; the job split is frozen, and test relevance selection follows configuration approval
- Rules the prompts and code must follow: guideline v1.3 (D-049, retaining applicable D-032 to D-042). In particular, the experience constraint uses only `required` experience units, never `unknown` or conditional ones (pilot J2-U07 versus J2-U08)

## 3. Planned method

1. CV text extraction (PyMuPDF, python-docx) and LLM parsing into evidence units with a parsing summary.
2. JD extraction prompt v1.2 with Pydantic validation and at most 1 repair attempt.
3. Current evidence-matching prompt v1.1: MATCH / PARTIAL / NO_MATCH per requirement unit, with CV quotes checked to exist word for word in the CV.
4. Constraint check: experience duration (v1.2 counting rules), location against a confirmed location, work-authorization statements.
5. Paste JD path end to end: clean, quality signals, extract, preview, match report.
6. Run the 8 development cases and check them by hand.
7. Prepare versioned extraction for 214 development JDs, with an approved budget after preflight. Defer extraction inspection of 214 held-out JDs until configuration freeze. Record deferred status explicitly; no claim that all 428 are extracted.
8. Embeddings (model per D-020, plus the second candidate if D-044 option A is approved), Baseline 2 dense, and the hybrid FTS + dense search with RRF.
9. Preserve the frozen 214/214 job split (D-046). Build development labeling pools under T03 Part 2 after embeddings; select the test relevance pool only after configuration approval under T06. A labeling pool is separate from the job split.

## 4. Planned outputs

- active versioned prompt files in `prompts/` (historical versions retained)
- CV parser, extractor, matcher modules and tests
- extraction cache
- an example report for a synthetic CV
- `evals/splits/`
- this stage report

## 5. Acceptance criteria

- One CV and one pasted JD produce a structured report whose quotes exist in the CV.
- The 8 development cases pass the manual check.
- Cache keys include schema, prompt, model, preprocessing, and guideline versions.
- Development extraction has per-job done / failed status; held-out extraction is explicitly deferred until freeze. The original all-428 criterion remains incomplete until those deferred jobs are processed.
- The test split is locked before checkpoint 10 starts.

## 6. Evidence to keep

- example report
- manual check sheet for the 8 cases
- extraction success count
- ledger totals
- commit links

## 7. Estimate and dependencies

- **Historical estimate:** About 1.5 working days and US$0.25-0.50 for batch extraction. These are not measured results. Current implementation diagnostics cost US$0.15938080; the conservative full-development preflight exceeds the configured guard. See the latest report before approving a batch.
- **Depends on:** OpenRouter key in `.env` by the evening of 30 Sep (for extraction and the dense baseline).

## 8. Fallback if blocked

If the OpenAI embedding fails on the Indonesian-CV cases, use the local `multilingual-e5-small`. If extraction fails for some jobs, mark them "could not be analyzed" and continue. If extraction quality is poor, keep it for prompt v2 in checkpoint 10 instead of blocking.

## 9. Checklist

- [x] CV text extraction (PyMuPDF, python-docx) and LLM parsing into evidence units with a parsing summary.
- [x] Current JD extraction prompt v1.2 (historical versions retained) with Pydantic/source validation and at most 1 repair attempt.
- [x] Current evidence-matching prompt v1.1: MATCH / PARTIAL / NO_MATCH per requirement unit, with CV quotes checked to exist word for word in the CV.
- [x] Constraint check: experience duration (v1.2 counting rules), location against a confirmed location, work-authorization statements.
- [x] Paste JD path end to end: clean, quality signals, extract, preview, match report.
- [ ] Run the 8 development cases and check them by hand.
- [ ] Development batch extraction: preflight and resume script implemented; v1.3 development extraction is not broadly executed; 214 test jobs deferred. Two historical v1.2 public-JD cache results remain versioned separately. Needs feasible approved budget and quality checks.
- [x] Two-model job/query embeddings, Baseline2 dense, and hybrid FTS + dense RRF implemented; live build and development smoke checks verified. Model/K selection remains CP2.3.
- [x] Freeze the disjoint 214/214 job split before tuning (D-046); build the six-method development pools under T03 Part 2. Test labeling pool remains pending configuration approval.
- [x] Acceptance: One CV and one pasted JD produce a structured report whose quotes exist in the CV.
- [ ] Acceptance: The 8 development cases pass the manual check.
- [x] Acceptance: Cache keys include schema, prompt, model, preprocessing, and guideline versions.
- [ ] Acceptance: complete per-job extraction outcomes after approved staged execution; held-out jobs stay deferred until freeze.
- [x] Acceptance: The test split is locked before checkpoint 10 starts.

## 10. Historical results by execution stage

These paragraphs describe earlier snapshots, including old drafts, parser gaps and ledger values. Current status is in the opening summary and closure checklist; do not restore earlier workbook state.

T03 Part 1 is accepted: 214 development and 214 test jobs, all 5 pilot jobs in development, no recorded duplicate crossing. See [split report](supporting/T03_Job_Split_20261001.md).

T07 is DONE: CV4/CV5 content version 0.1 was approved by Dion on 1 October. Approved file and unchanged body hashes match the [approval manifest](../../evals/annotation_tasks/T07_approved_cv_manifest_v1.json). Both remain test only. See [T07 review record](supporting/T07_Test_CV_Drafts_20261001.md).

Embedding storage, tokenization, durable receipts, budget controls, exact dense search, and hybrid RRF are implemented. Final database-enabled suite: **123 passed in 8.39 seconds**. Actual corpus estimate: **US$0.01208639**, conservative bound **US$0.06603606** for both models with 632 jobs + CV1/CV2 per model.

The live build is **complete**: 632 job vectors and 2 CV1/CV2 query vectors per model, four valid development-only retrieval checks, unchanged source inventory, no truncation. Post-build preflight finds zero pending inputs and no additional inference cost. The management-key issue was resolved by Dion replacing the local key; native response aliases were fixed with strict per-model allowlists. Historical failures and billed diagnostics are retained.

Successful build cost **US$0.01209273**; total ledger including diagnostics **US$0.01226822**. See [embedding implementation report](supporting/CP22_Embedding_Implementation_20261001.md), [EXP-20261001-04 and05](../experiments.md), and FAIL-03/04.

Development pools are complete: CV1 has 29 rows and CV2 has 34. All mandatory top-five candidates fit the cap of 20 new reviews per CV. T04 extraction drafts (84 units, three JDs) and T05 relevance drafts (60 rows, 40 designated reviews) are ready in `evals/labeling/`. At this historical preparation step new annotations were pending and B_Evidence was empty; the subsequent combined workbook and review receipt supersede that state. Latest database-enabled suite: **125 passed in 7.67 seconds**, additional API cost **US$0**. See [development review report](supporting/T03_T04_T05_Development_Review_20261001.md) and EXP-20261001-06.

## 11. Historical interpretation at the initial embedding/pool stage

Passing local tests establishes implementation behavior, not embedding or ranking quality. Both models accepted requests carrying the required provider restrictions; this is not an independent privacy audit. No model or K was selected. Development workbooks now exist, but no expanded gold is exported. The mentoring role F00020 is flagged for human role review; unknown degree equivalence and duration applicability need care. D-047 resolves the blind-sample question: current development batches use complete drafts followed by human review; test stays blind-first. This paragraph describes the initial preparation state. Later implementation completed evaluation-clock/date-precision handling and the vertical slice. Current CP2.2 acceptance remains open; see the latest review and implementation records.

## 12. Decisions from this stage

D-047: Dion approved complete draft-first review for current expanded development batches. This does not approve labels or change the held-out test procedure. See the [decision log](../decisions.md).

## 13. Next step

The user-confirmed coordination closure reports completed review in the active v1.3 workbook. Do not redo labeling or edit it here. Next pipeline work is the existing eight-case acceptance, v1.3 semantic checks under a separately scoped probe, and a feasible extraction plan. Approved-only export/provenance and compatibility checks remain separate; no test tuning. See the current closure checklist at the end.

## Initial implementation evidence (1 Oct 2026)

D-045 sizes approved by Dion. Phase 0 tests passed. T03 Part 1 created the frozen 214/214 job split with duplicate safety and stratum checks. See [split report](supporting/T03_Job_Split_20261001.md). This is prerequisite work only; the extraction, matching, and embedding pipeline is not yet complete.

Fresh verification after the handoff: 81 passed and 1 skipped offline; 82 passed with the local database. The deterministic split rerun changed no frozen file. Cost US$0. Evidence: EXP-20261001-03 and `evals/results/t03_split_verification_20261001.json`.

Plan note: the older D-043 references and multi-method test-pool step above have been superseded by approved D-045 and D-046. The job split is the frozen 214/214 partition, not a labeling pool. Test relevance pools are selected only after configuration approval, under D-046 and T06. Coverage for a fair retrieval comparison remains a separate question before evaluation. No evaluation rule was changed in this verification.

## Historical record: Complete development workbook (2 October 2026)

Current active file: `evals/labeling/JobFit_Development_Labeling_v0.1.xlsx`, under D-048. Earlier batch-specific results are historical.

| Section | Total rows | Previously approved | Pending review |
| --- | ---: | ---: | ---: |
| A_Extraction | 1,069 | 39 | 1,030 |
| B_Evidence | 1,387 | 21 | 1,366 |
| C_Relevance | 67 | 3 | 64 |

The workbook covers 54 development JDs and 67 CV1/CV2 pairs. The frozen pool itself remains 53 JDs and 63 pairs. Four optional pairs provide full CV1/CV2 coverage of the three originally selected extraction JDs, including the retained senior JD outside the relevance pool. All original 84 extraction rows and 60 relevance drafts, including human edits, remain unchanged. Applicable approved pilot rows are copied with their original provenance.

Independent saved-file checks passed: exact source/CV quotes, complete pair-to-unit coverage, unchanged protected sources and rows, development split isolation, 40 designated relevance reviews, saved dropdown rules, and 13 semantic spot checks. Timing formulas were checked with ordinary and midnight-crossing text times and numeric Excel times. All nine sheets were rendered and inspected. Native Microsoft Excel interaction was not exercised. Audit: `evals/results/development_combined_workbook_qa_20261002.json`. The validator describes the initial preparation snapshot; after human edits, do not restore old labels to make that snapshot check pass.

F00364 contains responsibilities without qualifications, so its zero A/B units are intentional. F00369 ends with an incomplete clause, which was not reconstructed. Questions and QA_Log record remaining semantic issues. Relevance remains an ordinal evidence judgment, not a mathematical conversion of match percentage.

The two original workbooks are archived byte-for-byte in `evals/labeling/archive/pre_combined_20261002/`. The pilot remains untouched. New draft labels are pending, and no gold export or tuning occurred. Project API calls for this preparation: 0. Additional cost: US$0; existing ledger total remains US$0.01226822.

Review priority remains D-045: A for D1/D2/D3, B for CV1×D1 and CV2×D2, and C filtered to `gold_review = yes`. Extra rows are optional. If extraction changes, recheck linked evidence and affected relevance before export. CP2.2 remains IN PROGRESS; the independent parser/extraction/matching vertical slice remains unfinished.

## Full first semantic audit (2 October 2026)

The active combined workbook was audited read-only: all 54 development JDs, both CV1/CV2 sources, 1,069 A units, 1,387 B rows and 67 C judgments. This was a full first pass, not sampling or human approval. The audit records 92 finding entries: 51 clear draft errors, 38 ambiguous cases and 3 source/guideline limitations. Detailed row identities, current values, quotations, proposals and dependent B/C records are in the [semantic audit report](supporting/Development_Labeling_Semantic_Audit_20261002.md) and its linked register/JSON/coverage CSV.

Final read-only mechanical verification passed 27 checks. All source/protected-row hashes and current A fingerprints match preparation; there is no saved A-change staleness. The workbook was saved externally during the audit: two draft-note leading spaces were removed and A's freeze pane changed to A18. Labels, source text, review statuses and counts were unchanged; these legitimate saved differences were retained. Latest audited SHA-256: `8be2b05635cc4175f71e2a38cd39dfaa9f17f2f4e4d78d80b20b57516fe733ad`. Unsaved Excel edits cannot be audited.

No labels, guideline, denominator, source, pool, split, workbook, scoring code or database were changed by the audit. Historical validators/QA were preserved, no pytest or database suite ran, and no model-quality metric was produced. API calls: 0; session cost US$0; local ledger still has 88 records totaling US$0.01226822.

STOP before workbook corrections. Resolve priority grouping/duration/importance, source-specific equivalence and language questions, then obtain authorization for a concrete correction list. Preserve approved pilot decisions. D-045 priority stays 82 pending A rows in the three selected JDs, 62 B rows in the two selected pairs, and 40 designated C rows. Other drafts remain optional. **CP2.2 is still IN PROGRESS**; parser, extractor, matcher and paste-JD acceptance remain separate unfinished work.


## Historical record: Authorized pending corrections (2 October 2026)

The user authorized clear pending corrections and deferred new grouping/denominator/equivalence/language decisions. Applied A first: 13 A rows, then 33 B rows and 2 C rationales, all pending. Rechecked 14 linked B rows and 23 C pairs. All 63 approved rows, source sheets, human metadata, counts, groups, score membership and C values remain unchanged. 27 checks passed; no API/export/tuning. [Correction report](supporting/Development_Labeling_Pending_Corrections_20261002.md) and evals/results/development_labeling_pending_corrections_20261002.json record before/after and deferred decisions. Workbook is released for human review; do not write it during independent pipeline implementation. CP2.2 remains IN PROGRESS.

## Historical record: Latest backend continuation (2 October 2026)

The interrupted implementation is verified with **161 database-enabled tests passing** (8.63 seconds, five third-party deprecation warnings). CV1 one/two-column PDFs preserve source text; image-only PDF fails explicitly. Dates, source validation, one repair, memory-only CV/paste processing, versioned public-JD cache and the pasted-JD report are implemented. Dependencies are recorded in requirements.txt.

A live synthetic PDF + J1 run completed, followed by a verified-CV-resume run with 21 extracted units and matching. The latest model percentage is **provisional**, and its denominator differs from approved pilot gold. It is not a validated quality claim or a replacement label. JD prompt v1.1 preserves v1 and corrects instructions conflicting with approved AND/D-041 rules. Empty output despite a populated requirements heading is now a failed extraction after at most one repair.

Six diagnostic runs used 17 calls costing **US$0.15938080**; total project ledger **US$0.17164902**. Full batch extraction was not run. Latest conservative bound for all214 development jobs is US$13.8128838, above authorization/guard; do not execute it or raise the guard without an approved feasible plan. Test214 remains deferred until freeze.

The eight fixtures pass automated checks; planned human acceptance and initial J4 extraction-quality measurement are still open. CP2.2 remains **IN PROGRESS**. The active workbook was not written and still matches the released correction snapshot. Review A D1–D3, B CV1×D1/CV2×D2 and C40 gold_review=yes while pipeline work stays independent.

Read the [implementation and error-analysis report](supporting/CP22_Pipeline_Implementation_20261002.md), [readable synthetic example](supporting/CP22_Synthetic_Example_20261002.md), and [machine verification](../../evals/results/cp22_pipeline_verification_20261002.json). Earlier dated sections are historical, including old placeholder/STOP descriptions.

## Historical record: Latest continuation: offline pipeline audit (2 October 2026)

The actual backend and prior verification hashes were checked before implementation. Clear cache, empty-extraction heading, non-finite duration/budget and legacy exporter risks were corrected with regression tests. A development alignment helper and approved-only export staging helper were added; the latter was exercised only with temporary fixtures, never the active workbook or actual gold. See [audit report](supporting/CP22_Pipeline_Audit_20261002.md).

Final selected offline suite: **164 passed, 0 skipped**, five SWIG warnings, 0.55 s. This is a different selection from the earlier 161-test database run; no new database verification or live model-quality claim is made. All protected file hashes, including the active workbook, matched at the final integrity check.

[Full saved-run J1 alignment](supporting/CP22_Pilot_Alignment_Review_20261002.md) proposes 18 one-to-one groups, one merge and one split across all 21 units/assessments. Alignment is not human verified; no F1/Macro-F1 is reported. J4/F00016 has approved development A only, so any next measurement is extraction-only. Three remaining approved pilot JDs have an actual no-inference preflight bound of US$0.1912998; quality-gated execution is only proposed, not run. The full214 batch remains unexecuted.

Session API cost US$0; ledger105 records totaling US$0.171649020. No new dependency, rule, configuration, label, split or gold change. D-045 priority human review continues in Excel. **CP2.2 remains IN PROGRESS**: eight-case human acceptance, semantic quality checks and feasible staged extraction outcomes remain open.


## Historical record: Latest continuation: probe STOP and guideline v1.3 adoption (2 October 2026)

**CP2.2 remains IN PROGRESS.** The controlled development probe ran under guideline v1.2 / JD prompt v1.1: J4/F00016 returned21 units after one schema repair; J3/F00034 returned16 but has important alternative-group uncertainty. The protocol stopped before F00073. All alignments remain proposals, with no F1 or evidence-accuracy claim. Three calls cost US$0.01996632; ledger108 records totals US$0.191615340. The aggregate US$0.20 guard, project US$8.50 guard and persistent stop remain intact.

Following approved D-049, active runtime now selects guideline v1.3, JD prompt v1.2 and evidence prompt v1.1. Original config is archived; all historical prompts, gold and live results retain their versions. Unresolved composite structure holds the final percentage without changing the scorer formula or silently excluding units. Adoption is implemented and tested offline only: **213 passed,0 skipped**, five SWIG warnings,0.61s. No new v1.3 inference/database verification or dependencies.

Offline CP2.3 metric/comparability/readiness tools are prepared and tested with synthetic examples. Actual quality reporting remains blocked on reviewed labels, completeness, verified alignment, guideline compatibility and metric-contract details. The CLI currently prepares prerequisites, not a formal benchmark. Existing embeddings were inspected and retained.

See [latest audit continuation](supporting/CP22_Pipeline_Audit_20261002.md), [adoption evidence](../../evals/results/cp22_v13_adoption_20261002.json), and [CP2.3 preparation/decision list](CP2_03_System_Tuning.md). Workbook changes made during human review were preserved; no workbook write, gold export, automatic approval, test development, formal tuning or mass extraction occurred. Eight human fixture approvals and semantic acceptance remain open; continue D-045 priority review, not all drafts.


## Historical development review and QA before closure (2 October 2026)

Superseded by the coordination closure below: the required-cloud suggestion was corrected to preferred, follow-up review statuses/notes were completed under delegation. No workbook rollback is permitted.

Dion submitted review of all 54 development JDs and 67 CV1/CV2 pairs, and confirmed that B/C were checked after the final A changes in that submission. The original receipt is archived unchanged. The active workbook is [JobFit_Development_Labeling_v1.3.xlsx](../../evals/labeling/JobFit_Development_Labeling_v1.3.xlsx).

The two explicitly approved QA corrections separate required general cloud experience from preferred AWS experience, and classify debugging as knowledge_area. Active counts are 1,079 A decisions (1,069 retained), 1,406 B rows (1,404 approved, 2 pending; 16 rejected), and 67 C rows (66 approved, 1 pending). Only the two cloud/AWS B rows and their C pair were reopened following the new split. Seven edited A rows still need reasons. F00369 is held from evaluation because its supplemented text came from a similar posting rather than a verified original source.

See the [review report](supporting/Development_Labeling_Review_20261002.md) for row locations, source lineage, historical-version compatibility and group-level OR counting. No expanded gold has been promoted. Existing cell styles, widths, panes, dropdowns and formulas are preserved; JDs/CVs and Timing/Questions/QA_Log are byte-identical worksheet parts. No code, database, corpus, split or billing change was made in this QA stage.

CP2.2 remains **IN PROGRESS**. Remaining gates are the small labeling follow-up list, approved-only candidate validation, human fixture acceptance, v1.3 live quality verification, feasible staged extraction, and evaluation-contract conventions. Formal CP2.3 tuning and held-out evaluation have not begun.


## Current CP2.2 closure checklist — technical continuation, 2 October2026

| Ownership/status | Concrete remaining item or evidence | Stage boundary |
| --- | --- | --- |
| Completed technically | Upload/parser, explicit reference date/partial dates, JD extraction/matcher, source/identity checks, existing scoring/constraint integration, paste flow and versioned cache. Runtime v1.3 tested offline; live successful examples remain historical v1.2 | Does not claim v1.3 semantic validation |
| Completed technically | Cache-only top30 for six methods × CV1/CV2:12successful rankings,214eligible each, full provenance and scoped latency. No-filter condition verified; optional filters deferred | CP2.2 retrieval support; no CP2.3 selection |
| Can proceed independently | Prepare a separately guarded stage-by-stage probe executor with input ceilings and persistent resume reservations, without dispatch; assemble approved-only validation design from recorded review receipts, without exporting | Paid execution/export each wait for their explicit scope |
| Human acceptance pending | Review the existing eight fixtures using the single summary; resolve category/qualifier/source-context issues before revisions. Validate semantic extraction/matching behavior and affected historical compatibility | Core CP2.2 acceptance; no new cases added |
| Cost/scope decision required | Proposed small v1.3 probe US$0.3362892 upper / suggested aggregateUS$0.40, not run; subsequent feasible staged development extraction and per-job outcomes remain open | Full214 extraction is not authorized; held-out remains deferred |
| CP2.3 dependency, not added CP2.2 acceptance | Authorized approved-only gold staging/promotion, F00369 source hold, mixed-version/OR alignment, metric conventions, optional-filter comparative condition, model/K/prompt selection | Review closure does not itself authorize export or formal tuning |

Review closure from the user's coordination note: active `JobFit_Development_Labeling_v1.3.xlsx`; all A/B/C review statuses reported approved, rejected decisions retained (1079A decisions,1406B decisions,67C). This task did not reopen the workbook or independently re-annotate it. F00018 cloud and AWS are both preferred under “Will be a plus”; general-cloud MATCH from CV2 BigQuery does not prove AWS/ML cloud deployment. F00369's similar-posting tail remains unverified and affected evaluation records stay held. No labeling redo is requested.

Separate interrupted v1.3 run `cp22_v13_verified_review_live_20261002` ended with exit130; started is an incomplete artifact, no usable pipeline result. Ledger109records totalsUS$0.21270144, includingUS$0.0210861 uncertain reservation, not confirmed provider billing. This execution task made0paidcalls/US$0. Preserve the interrupted artifact and ledger entry. No workbook, gold, source, split, pool or default retrieval config changed.

Validation this task:13targeted runner/pool tests and29scoring/fixture tests passed, separately recorded; actual local DB retrieval succeeded with12top30rankings. No full DB suite rerun. Current [acceptance summary](supporting/CP22_Acceptance_Review_20261002.md) links final rankings, preflight, tests and readiness. CP2.2 remains IN PROGRESS; no acceptance is inferred from test count alone.
