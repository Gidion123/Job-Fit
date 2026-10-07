# CP2.2 Pipeline Continuation Audit — 2 October 2026

Status: **IN PROGRESS**. This continuation audits actual implementation and prepares independent development checks while the annotator reviews Excel. It does not approve labels or finish CP2.2.

## Verified starting point

The private handoff/brief, latest implementation/example/verification records, contract, decisions, annotation rules, stage/master plan and relevant design/reference sections were read before changes. All final code hashes in the previous pipeline verification matched at entry. The parser is implemented, not a placeholder. PDF/DOCX/text extraction, explicit evaluation date and partial dates, extraction/matching, scoring/constraints, pasted-JD flow and scoped cache already exist. Embeddings, split, pools and CV approval were not repeated.

Historical evidence remains distinct: the earlier 161-test database-enabled run and live runs 01–06 belong to the previous continuation. Run 06 is structurally valid but not semantically equivalent to pilot gold. No new real-model run occurred here.

## Implementation findings and corrections

| Finding | Change | Regression evidence |
| --- | --- | --- |
| In-memory extraction cache could return the same supplied key across scopes; malformed disk envelopes could raise instead of missing | Memory is keyed by scope and key; allowed scopes and persisted public scope are validated; malformed envelopes are cache misses; value hashes remain mandatory | Cross-scope private-evidence isolation, malformed envelopes, tampering, existing version-key/resume tests |
| Empty-extraction guard recognized headings ending in a colon only | Populated requirement headings without a colon also reject empty extraction and allow at most one repair | Five English/Indonesian headings; existing responsibilities-only case still passes |
| Non-finite duration input could bypass the minimum-duration comparison | Reject nonnumeric, boolean, negative and non-finite duration bounds before inference | Invalid bounds make zero fake-client calls; existing bounded-duration behavior passes |
| Non-finite budget estimates, batch approval ceilings or ledger totals could bypass comparisons | Reject invalid finite/nonnegative values before spend; configured hard stop remains US$8.50 | NaN/infinity/negative estimates/CLI approval ceilings and corrupt ledger total rejected; existing budget and embedding tests pass |
| Historical pilot exporter could rewrite frozen development IDs with pilot-only IDs | Legacy entry point stops before workbook read or any write when the frozen split manifest exists | Temporary split marker and nonexistent workbook/output prove no read/write path is reached |

These are implementation corrections, not new labeling, grouping, denominator, equivalence or language rules. Prompts, model/configuration files, scoring code and constraints are unchanged. The production extraction-cache directory has **zero entries**, so adding explicit envelope scope invalidated no successful paid extraction. Older unscoped envelopes are deliberately not reused; future migration of any external cache requires validation, not silent paid recomputation.

## Safe review/export preparation

`src/jobfit/eval/review_export.py` accepts in-memory review records and a verified baseline. It has no workbook reader or actual gold-promotion operation. Tests used temporary synthetic dictionaries only.

- Candidates must be individually approved, non-rejected and valid, with source membership, identities, guideline version and provenance. Pending/rejected rows never become candidate gold. Invalid approved rows are reported, not modified.
- Stable keys are job/unit or CV/job/unit, not spreadsheet row positions. Source changes and duplicate identities block staging.
- B requires an exportable approved A unit and matching unit text. Failed process status cannot become a NO_MATCH gold label.
- A content/group changes invalidate affected B; whole-job A or pair B changes invalidate C. Rechecks require the exact dependency token and actual reviewer/time attribution. Reordering or a note-only change does not cause false semantic staleness.
- C remains an independent whole-CV/JD judgment. Unrelated pending A/B does not force the annotator to finish the whole workbook before the designated C subset can be considered. Upstream changes still require rechecking.
- Existing reviewer/time metadata survives. A supplied timestamp must be the actual review time, not an invented approval or export timestamp.
- Only a new, exclusive staging directory can be written. Actual `evals/gold/` is refused. Coverage reports do not claim that reviewed extraction is semantically complete.

After review is declared complete and export is authorized: make a read-only snapshot of the closed workbook; reconcile it against the released review baseline and correction log; show A→B/C changes; have the annotator acknowledge affected judgments; then build and inspect a candidate export. A workbook adapter and final promotion still need scoped implementation/verification at that point. This audit did not run any of these steps on the active workbook or create actual gold.

## Pilot diagnosis and bounded next-run plan

See [complete pilot alignment review](CP22_Pilot_Alignment_Review_20261002.md). All 21 gold/model A units and 21 gold/model B assessments are accounted for in 20 proposed mapping groups: 18 one-to-one, one merge and one split. Every mapping remains pending verification. No F1/Macro-F1 or accuracy metric is published.

The structured/unstructured requirement has wrong model importance and unresolved structure; architecture/engineering remain merged; independent learning is split. Intermediate depth wording is lost from three unit texts. Four soft-skill evidence judgments disagree with approved labels. The saved provisional score 91.67%/denominator 6 must not replace pilot 92.86%/denominator 7. No source/gold/scoring change was made to force agreement.

J4/F00016 is verified development with 21 approved A rows and no approved B rows. It can support an extraction check; it cannot currently support a J4 evidence-accuracy claim.

An actual **preflight only** was run for the three other approved extraction JDs: F00016, F00034, F00073. Configured model: `deepseek/deepseek-v4.1-flash`, current JD v1.1 plus guideline, 16,000 output allowance, one repair maximum. Bound: **US$0.1912998** for three JDs; all three are uncached. This uses current local registry prices and the existing conservative byte/output calculation, not a new provider-price verification or a mean bill forecast. It is not a partial execution of the 214-JD plan.

Suggested future quality probe, after reviewing current structural errors: these three JDs only, aggregate maximum US$0.20, excluding the already exercised J1. Start with J4, inspect its saved extraction before continuing; stop on the first unresolved structural/qualifier error or failed stage, or before the aggregate ceiling. Preserve successful public-JD cache results and use a new run ID to resume. The batch driver would need the strict first-failure/intermediate-quality gate for this proposed protocol; it is not claimed implemented by this plan. Re-estimate immediately before any paid request, reuse valid cache, check the guard/ledger and verify official provider information if configuration changes. No inference was executed under this proposal.

Full 214-development extraction remains unexecuted. Its historical conservative bound US$13.8128838 exceeds both the approval threshold and remaining guard capacity. No budget increase or split-batch workaround occurred.

## Actual verification and limits

Final selected offline suite: **164 passed, 0 failed, 0 skipped**, five PyMuPDF/SWIG deprecation warnings, pytest reported 0.55 seconds. This is a **different test set** from the earlier database suite (161 passed). It includes new audit/export/alignment cases plus existing upload, extraction/matching, schema, constraints, scoring, budget and embedding-client tests. No database-enabled suite was rerun and no fresh database verification is claimed.

The first selected subset had 119 passed; an intermediate selection had 161 passed before three CLI approval-ceiling regressions. Its XML is preserved separately as `cp22_pipeline_audit_tests_20261002.xml`. A new alignment CLI initially failed to import `scripts`; its repository-root path was fixed, and the actual CLI then generated the report successfully. A preliminary Python command used the workspace root instead of the repository and did not execute; it was rerun from the repository. Neither command made an API call or touched the workbook.

Evidence: [audit JSON](../../../evals/results/cp22_pipeline_audit_20261002.json), [JUnit result](../../../evals/results/cp22_pipeline_audit_final_tests_20261002.xml), [alignment register](../../../evals/results/cp22_pilot_alignment_review_20261002.json), [three-JD preflight](../../../evals/results/cp22_pilot_remaining_preflight_20261002.json).

At the integrity check, workbook, approved gold, CV1/CV2 sources, CP1 corpus, frozen split, guideline, decisions, prompts, model/pipeline configuration, requirements and ledger matched entry hashes. The active workbook was not loaded into a workbook library or written. Any later user save is legitimate and must not be restored to this hash. No held-out CV/JD content was used for development. No git, deletion, new dependency, export, tuning or budget change occurred. PyMuPDF and python-docx remain recorded in requirements.txt.

API calls this audit: **0**. Session cost: **US$0**. Ledger: **105 records, US$0.171649020**. Arithmetic headroom under US$8.50: **US$8.328350980**; headroom is not batch authorization.

## Remaining work and human review

CP2.2 remains IN PROGRESS: human acceptance of the eight development fixtures, semantic extraction/matching checks and a feasible execution plan with complete per-job outcomes remain open. Offline tests do not prove model quality. New label gold export and CP2.3 tuning wait for the necessary approved development subset and pipeline acceptance.

Keep D-045 review priorities: A D1/F00103, D2/F00074, D3/F00012; B CV1×D1 and CV2×D2; C 40 rows with `gold_review=yes`. Work in the agreed 2–3-hour daily capacity; the other drafts remain optional. Afterwards, review the three structural alignment proposals and four evidence differences (about 15–20 minutes). This requests no new rule now; pending grouping/denominator/language/equivalence questions remain in the existing correction decision list. Notify the execution role when the priority review is ready and authorize the export stage separately.

## Files for the user's commit review

- Modified: `src/jobfit/extraction/cache.py`, `jd_extractor.py`, `src/jobfit/matching/evidence_matcher.py`, `src/jobfit/llm/budget.py`, `scripts/export_pilot_gold.py`, `scripts/run_batch_extraction.py`.
- New: `src/jobfit/eval/alignment.py`, `review_export.py`, `scripts/prepare_cp22_alignment_review.py`; three audit/alignment/export test modules.
- New evidence: five `evals/results/cp22_*20261002` audit/alignment/preflight/test artifacts linked above; this report and the pilot alignment report.
- Updated documentation: CP2.2 stage report, original pipeline implementation report (append-only continuation), experiments, failures, repository structure, and private handoff. Private handoff is not intended for the repository commit. No workbook or gold file belongs to this change set.


## Latest continuation: controlled probe, evaluation preparation and D-049 adoption

2 October 2026. This section supersedes the earlier proposed-only probe and runtime-version descriptions, without changing historical results. CP2.2 remains **IN PROGRESS**. The active workbook was never loaded into a workbook library or written in this continuation. Its hash changed during the user's review; the saved change was preserved, not restored. Approved gold, source CVs/JDs, frozen split, model and retrieval configurations are unchanged.

### Controlled baseline probe — guideline v1.2, JD prompt v1.1

Implemented `src/jobfit/llm/probe.py` and `scripts/run_pilot_probe.py` before paid execution. A fixed run identity, source/configuration fingerprints, invocation lock, persistent pre-request reservations and ledger reconciliation enforce the aggregate US$0.20 ceiling across repairs/resume, in addition to the US$8.50 project guard. An unresolved reservation blocks retry. One JD is executed per invocation; continuation requires a source-backed operational check tied to its saved result hash. This check does not approve annotation or alignment. Terminal process failure or important semantic uncertainty stops subsequent JDs. Fake-client tests covered the protocol before execution.

Official OpenRouter endpoint metadata was retrieved and recorded in `evals/results/cp22_probe_provider_20261002.json`. The unchanged baseline is `deepseek/deepseek-v4.1-flash`; routing ceilings remain US$0.30 input / US$1.20 output per million tokens. Request privacy restrictions remain enforced; public endpoint metadata alone does not independently certify provider retention. The three-JD conservative bound, including one repair each, was **US$0.1912998**. See `cp22_pilot_quality_probe_20261002_preflight_00.json` and `_01.json`.

| Development JD | Actual outcome | Calls / cost | Interpretation |
| --- | --- | --- | --- |
| J4 / F00016 | First response failed schema validation; one permitted repair returned 21 units. Stage latency 225,914 ms | 2 / US$0.01550648 | Read the whole source and all 21 gold/model units. No important omission or structural error found under this v1.2 operational check; minor category/wording differences remain. Not human-verified alignment or evidence accuracy |
| J3 / F00034 | 16 units on first attempt; stage latency 120,151 ms | 1 / US$0.00445984 | Model U02 represents a two-year role-alternative requirement as qualified with no branches, unlike approved G2. U16 remains unresolved despite a gold alternative group. Important structural uncertainty: stop |
| F00073 | Not attempted | 0 / US$0 | Protocol stopped before this JD |

The state in `reports/quality_probe/cp22_pilot_quality_probe_20261002.json` is **stopped_semantic_issue**. Do not reset it or change its run identity to bypass the stop. The later v1.3 configuration also differs from its fingerprint. Two successful public-JD cache entries remain intact, including the semantically flagged result; cache/schema success is not annotation validity. First-attempt J4 failure details were recorded only as ValidationError, so the exact failing field is not reconstructed.

All 21 J4 and 16 J3 units have proposed meaning-based one-to-one mappings in `cp22_j4_alignment_proposal_20261002.json` and `cp22_j3_alignment_proposal_20261002.json`; operational reviews are separate JSON files. All semantic alignments remain pending human verification. There is no F1, evidence-accuracy result, or automatic approval. J4 has approved A but insufficient approved B for an evidence-quality claim. Historical J1, J3 and J4 diagnostics retain their original guideline versions.

Three billed calls cost **US$0.01996632**. Ledger: **108 records, US$0.191615340**; arithmetic headroom **US$8.308384660**. No other inference, embedding build, database run or full extraction batch occurred.

### Offline CP2.3 preparation

Implemented metric/comparison functions in `src/jobfit/eval/metrics.py` and `run_eval.py`, with a read-only prerequisite CLI in `scripts/run_evaluation.py`. The CLI prepares readiness only; it is not a completed formal benchmark adapter. Tests use manually computable synthetic cases and clearly separate fake from live artifacts.

- Ranking reports distinguish judged/unjudged coverage, raw-top-K labeled-pool recall and a condensed judged list. Unjudged jobs never become relevance 0; recall is not claimed for the whole corpus. Zero/insufficient denominators are explicit.
- Comparable methods must share development CVs, split, filters, eligible scope, input/gold fingerprints and execution type. Top-20 saved rankings cannot support K=30. No winner or configuration selection is produced.
- Extraction metrics require verified semantic alignment and whole-JD completeness, not matching IDs/counts/quotes. Split/merge scoring and pending mapping block publication. Evidence failures remain not_assessed with coverage; no failure becomes NO_MATCH.
- LLM comparison requires registered candidate identities, input/prompt/gold/guideline provenance and a verified metric contract. The reference model is capped at 10 cases. Historical/current guideline compatibility must be explicitly verified.
- Readiness inventories existing six-method CV1/CV2 ranks and four query embedding caches without regenerating them. Historical ranks lack original corpus hash and latency, and lack the full filtered/K=30 comparison: future retrieval using existing vectors must record these. Current hashes do not retroactively supply missing provenance.

Current readiness: `evals/results/cp23_readiness_v13_20261002.json`. Exported pilot gold contains 71 A rows, 34 B rows and 10 C judgments; this is not a count of the user's current Excel approvals. The historical C CSV is trusted only through its exact audited export hash. Partially approved units do not imply complete JD annotation. Priority gold, eight human fixture approvals, completeness, semantic alignment, version compatibility and explicit metric conventions remain gates. See the short decision list in [CP2.3](../CP2_03_System_Tuning.md).

### D-049 runtime adoption — implemented and tested offline

After the user updated the manual, read D-049, `evals/annotation_guideline_v1_3.md` and the latest handoff. New `prompts/jd_extraction_v1_2.md` and `prompts/evidence_matching_v1_1.md` align umbrella/component handling, qualification/local-softener importance, tool/concept categories and unresolved and/or cardinality with v1.3. Old D-041 is preserved historically, not used as a v1.3 precedent. D-040's pure-or exception remains separate.

`config/pipeline_v1.yaml` now selects guideline v1.3 and these stage-specific prompt versions. Its exact prior bytes are in `config/archive/pipeline_v1_pre_D049_20261002.yaml`. Config loading, extractor, matcher, example/batch/probe drivers, reports, evaluation prerequisites and cache identities use the explicit versions. Original guideline, old prompts, results and cache files remain unchanged. No historical label/artifact was relabeled v1.3.

The existing requirement schema and score formula remain unchanged. Ambiguous composites use existing `needs_review` support; any such structure, including preferred/unknown units, holds the final percentage with `structure_review_required` / `pending_structure_review`. Identified counts are retained as tentative; the pipeline neither silently drops a composite from a validated denominator nor invents OR cardinality. Comparison reports add version/hash metadata. Failed processing remains distinct from NO_MATCH.

**No real model inference under v1.3 was run.** Prompt wiring, cache isolation and hold behavior are tested, not model semantic adherence. Gold compatibility with v1.3 still requires review before quality metrics. D-049 does not automatically reapprove any historical decision or the eight fixtures.

### Final verification and files

Final selected offline suite: **213 passed, 0 failed, 0 skipped**, five PyMuPDF/SWIG deprecation warnings, 0.61 s. No database verification was repeated. The earlier 186-test artifact belongs to the pre-adoption selection; the final suite adds v1.3 cases. Evidence: [adoption JSON](../../../evals/results/cp22_v13_adoption_20261002.json), [final JUnit](../../../evals/results/cp22_v13_final_tests_20261002.xml), [baseline probe summary](../../../evals/results/cp22_pilot_probe_review_20261002.json). These record code/source hashes and the exact test selection. No new dependency; requirements.txt already contains PDF/DOCX dependencies.

Files for user commit review: new probe module/driver/tests; implemented eval metrics/runner/CLI plus test_evaluation_tools.py; config.py and pipeline_v1.yaml plus archived prior configuration; extractor, matcher, pipeline.py and example/batch drivers; two new prompts and test_guideline_v13_runtime.py; the new versioned results/JUnit files; updates to this report, CP2.2, CP2.3, pipeline contract, experiments, failures, master plan and repo structure. Local reports/cache/probe receipts and the private handoff remain operational/private artifacts according to repository policy. No workbook or gold change belongs to this work.

Human next step remains priority labeling at 2–3 hours/day: A D1/F00103, D2/F00074, D3/F00012; B CV1×D1 and CV2×D2; C40 gold_review=yes. Additional drafts are optional. Afterwards, review version-affected alignment/fixture cases and authorize approved-only staging separately. CP2.2 acceptance still needs semantic quality, eight human fixture approvals and a feasible extraction plan. No formal tuning, held-out evaluation or mass extraction was performed.


## Technical closure continuation after delegated review (2 October 2026)

Read the [single acceptance summary](CP22_Acceptance_Review_20261002.md), not the earlier pending-workbook snapshot as current state. User-confirmed coordination note reports reviewed workbook v1.3, all A/B/C statuses approved under delegated QA, rejected decisions retained. Cloud/AWS F00018 both preferred; F00369 unverified similar-posting tail remains held. No workbook read/write or gold export here. The separate interrupted v1.3 run has no usable result; started does not mean success/active execution.

Implemented cache-only read-only retrieval runner:12successful top30rankings across six methods andCV1/CV2 over the same214development IDs. Exact profile/input/cache/source checks, source/config/code hashes, vector receipts, effective filters/depth/RRF, ties and scoped latency are saved. Default retrieval config and labeling pool unchanged. Run-local branch_depth30 is recorded to support requested top 30; optional filters remain deferred. Two successful runs have identical rankings, not proof of quality or production latency. Final evidence `evals/results/cp22_retrieval_top30_20261002_03.json`; initial sandbox connection failure and intermediate syntax-error test record retained.

Targeted offline checks:13runner/pool tests passed and29scoring/fixture tests passed separately. Actual read-only DB integration produced the rankings; no full DB-suite or paid-model run. All eight existing fixture expected results pass; category/qualifier/missing-context limitations are listed, none approved or edited. Proposed separate v1.3 probe preflight upper US$0.3362892/max8calls, suggested aggregate US$0.40; execution remains unperformed and needs guarded staged dispatch. Prior closed/interrupted probe artifacts preserved.

Session API cost US$0. Ledger109records US$0.21270144 includes US$0.0210861 uncertain reservation from the other role's interrupted run; not confirmed billing and not removed. No new dependency, schema/scoring/constraint/metric rule change, gold/source/split/pool mutation, git, paid inference, tuning or test evaluation. Current readiness `cp23_readiness_technical_closure_20261002.json` still blocks formal evaluation on approved-only export/provenance/completeness/compatibility and metric conventions. CP2.2 remains IN PROGRESS; CP2.3-only choices are not silently added to CP2.2 acceptance.
