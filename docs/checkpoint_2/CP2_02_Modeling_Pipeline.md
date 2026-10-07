# CP2.2: Modeling the Extraction, Search, and Evidence Pipeline

**Project:** JobFit  
**Official checkpoint:** 9, Modeling Deep Learning, 29 September 2026  
**Actual work:** 1 to 3 October 2026  
**Status:** DONE for implementation and evidenced acceptance, 3 October 2026, under explicit user-approved scope decision D-050. Broad extraction is deferred until CP2.3 configuration evaluation; it has not been run.  
**Design:** System Design v1.3; annotation guideline v1.3 (D-049); checkpoint scope D-050.

> **Final reconciled status (7 October 2026):** DONE under D-050. The broad development extraction that D-050 carried into CP2.3 is resolved by [D-091](../decisions.md): the 52-JD development scope used for configuration selection is accepted and exhaustive extraction of the other 162 development JDs is optional future work. The frozen system (D-087) uses JD prompt v1.4 experimental, not the v1.2 default named below. The rest of this report is the 3 October record; its "next steps" in section 11 were carried out in CP2.3 ([final status](CP2_03_System_Tuning.md#final-status-closeout-audit-7-october-2026)). Acceptance evidence: [CP2 closeout audit](CP2_Closeout_Audit_20261007.md).

## 1. Executive summary

The backend can read a synthetic CV, require confirmation of its parsing summary, extract a pasted JD, match requirement units with quoted CV evidence, and produce an evidence-coverage report with separate constraints. Text PDF, DOCX and plain-text paths, dated experience rules, versioned caches, budget controls, two embedding models, and development retrieval are implemented.

The reviewed development workbook has been exported to an immutable, versioned bundle after source, identity, dependency and compatibility checks. It contains **1,058 extraction rows, 1,364 evidence rows and 69 relevance judgments**. Export eligibility is distinct from whole-JD completeness and verified alignment with model output.

The new, explicitly authorized experiment `cp22_extraction_repair_v13_20261003` has completed all four stages. F00034 and pasted F00332 each needed one source-review repair. CV1 parsing succeeded on its first attempt. Matching needed one repair to recognize partial soft-skill evidence. The final CV1 × F00332 report has 16 assessments, nine scored required units and **72.22%** evidence coverage. All positive quotes were checked against the CV. The score is not a hiring probability or an accuracy measurement.

This is **assisted operational acceptance**, not proof of unattended extraction quality. Two model-versus-gold interpretation differences remain documented for alignment; gold is unchanged. Default runtime still uses JD prompt v1.2 under guideline v1.3. The experiment explicitly uses JD prompt v1.3 plus a qualification inventory. No candidate winner or default promotion was selected.

**Stage conclusion:** CP2.2 is **DONE under D-050**, approved explicitly by Dion on 3 October. The fixture, export, backend and small live-chain acceptance tasks are complete with evidence. The previous planned-scale development-extraction criterion is an explicit carryover after CP2.3 configuration evaluation, not a completed batch. No scope was silently removed and no quality, winner or independent-human-approval claim follows from closure. Optional filters, formal metrics and model/K selection remain CP2.3 work. A full labeling redo is not required.

## 2. Objective and scope

Build the one-CV/one-JD vertical slice and reusable retrieval infrastructure. JobFit uses pretrained LLMs and embeddings; it does not train a neural network in this stage. The output percentage measures supported required-requirement evidence, not hiring probability.

Inputs are the CP1 snapshot `CP1_20260926`, 632 EDA candidate jobs, the frozen 214/214 development/test target-job split, approved synthetic CV1/CV2 for development, and the reviewed workbook. CV3-CV5 and held-out judgments were not used for development. Optional product filters and method/model/K selection belong to CP2.3; production session controls belong to CP3.

## 3. Implementation and results

| Component | Implemented behavior | Evidence and limit |
| --- | --- | --- |
| Upload extraction | Text PDF, DOCX and plain text; controlled rejection of image-only PDFs | Synthetic CV1 one/two-column PDF fixtures; no OCR or claim of universal PDF layout support |
| CV parser | Structured evidence, exact quotes, parsing preview, explicit reference date | Offline tests and current real CV1 parsing: 13 evidence facts, two employment entries and two projects; preview checked under delegation |
| Dates and constraints | Preserve partial dates; inclusive months; merge employment overlap; scoped activity evidence required | Unknown duration stays unknown; job tenure is not automatically technology tenure |
| JD extraction | Pydantic validation, identity/quote checks, at most one repair | Default JD prompt v1.2; experimental v1.3 adds source inventory. Two repaired 16-unit outputs were inspected; coverage alone does not prove completeness |
| Coverage guard | Detect unrepresented bullets in supported lists, including cache hits; experimental inventory also handles About You | Known F00034 regression finds eight uncovered bullets; no new requirements or labels invented |
| Evidence matching | MATCH/PARTIAL/NO_MATCH with exact evidence and OR branches | Current real run: 16 assessments, bounded source repair, exact quotes. Failure remains unassessed; unresolved structure/completeness can hold the percentage |
| Score report | Existing formula and separate constraint states | No formula, denominator policy, label threshold or metric contract changed |
| Cache | Source/model/schema/prompt/preprocessing/guideline identities; session-only CV/paste handling | Public model responses preserved; runtime safety checks run again on cache hits |
| Embeddings | OpenAI 1,536 dimensions and Qwen 4,096 dimensions | 632 job vectors and CV1/CV2 query vectors per model from the successful historical build |
| Retrieval | B0, B1, dense and hybrid for each embedding | Twelve saved top 30 rankings over the same 214 development IDs; no winner selected |
| Export | Approved-only record gold with source and dependency receipts | Versioned bundle, rejected exclusions, held records, logical OR mappings, saved-file revalidation |

Retrieval used cached vectors, not new model calls. Its run-local RRF branch depth is 30 and constant is 60; the default configuration was not selected or changed by that run. Single-run local timings are implementation observations, not production benchmarks. Optional filters remain deferred and are explicitly absent from this comparison.

## 4. Reviewed development labels

Bundle at CP2.2 closure: [`development_v13_reviewed_20261002_r2`](../../evals/gold/development_v13_reviewed_20261002_r2/manifest.json). **Current bundle after D-054 (3 October):** [`development_v13_reviewed_20261003_stage1_r3`](../../evals/gold/development_v13_reviewed_20261003_stage1_r3/manifest.json) with 1,058 A / 1,364 B / 78 C. The table below describes the r2 export.

| Section | Workbook decisions | Non-overlapping historical additions | Rejected | Exported | Retained on hold |
| --- | ---: | ---: | ---: | ---: | ---: |
| A: extraction | 1,079 | 34 | 10 | 1,058 | 45 |
| B: evidence | 1,406 | 13 | 16 | 1,364 | 39 |
| C: relevance | 67 | 7 | 0 | 69 | 5 |

The active workbook was read without saving it. Its SHA256 remains `4d96852dce52effdc376709cf8c0131f2f9ad1a6f02795cc556fec1819eccb50`. Historical pilot label files remain unchanged. Non-overlapping pilot records appear once; do not concatenate root pilot exports with this bundle.

Important holds:

- F00369 uses a completion taken from a similar posting, not a verified identical source. All affected records remain excluded from evaluation.
- Historical J1 independent AND units conflict with the later D-049 `and/or` rule. Their approved history is preserved rather than silently relabeled.
- Unresolved composite/group cases and missing historical edit notes remain explicit.
- Generic REST API integration, CI/CD and MLOps practice categorized as named tools require compatibility review. Three additional holds were found in D1/D2/D3; linked B rows are also held. The workbook was not changed.
- Two priority relevance identities remain held: CV1×F00022 and CV2×F00114. Unjudged/held items are not relevance zero.

The saved bundle covers 54 JDs in A, 66 CV-JD pairs across 53 JDs in B, and 69 relevance pairs across 53 JDs in C. There are 56 JD coverage records; 48 have all retained A rows exportable. This does **not** certify complete extraction references. Row-level approval, logical grouping, complete source coverage and model-to-reference alignment are separate checks. Original guideline versions, review notes and provenance are retained. The export does not invent per-row review timestamps or claim independent human annotation where review used drafts or delegated QA.

## 5. Eight development acceptance cases

Current synthetic revisions are in `evals/fixtures/v1_3/`; original files remain intact. Each revision records its source hash, reason and delegated review scope. This fulfills the requested technical/semantic examination under delegation, not eight new independent human approvals or eight model runs.

| Case | Verified output | Interpretation |
| --- | --- | --- |
| Clear evidence | 87.50%, 4 required; compatible experience assumption | Three MATCH and one list-only PARTIAL |
| Experience shortfall | 83.33%, 3 required; explicit conflict | Percentage and eligibility conflict remain separate |
| Unknown duration | 75%, 2 required; unknown constraint | Project evidence does not prove employment duration |
| Alternative groups | 50%, 3 logical requirements | Best supported OR branch; each group counts once |
| Repeated requirement | 62.50%, 4 logical requirements | Exact general SQL duplicate merges; complex-query qualifier stays distinct |
| Ambiguous importance | 83.33%, provisional | Explicit conflicting source, not merely the word familiarity |
| No required denominator | No score | Preferred/soft-skill context does not invent required technical units |
| Assessment failure | On hold; no percentage | Failed assessment is not NO_MATCH; denominator is not reduced |

These cases verify supplied rules and source-grounded synthetic expectations. They do not demonstrate model accuracy or resolve arbitrary degree/tool equivalence in real jobs. See the [acceptance record](supporting/CP22_Acceptance_Review_20261002.md).

## 6. Real-model probes and error analysis

### 6.1 Historical fixed-baseline failure (2 October)

Run: `cp22_v13_acceptance_probe_after_closure_20261002`. Fixed baseline and prompt versions, maximum eight calls including repair, aggregate authorization US$0.40. Official endpoint metadata was recorded by the preceding execution session.

| Stage | Actual result |
| --- | --- |
| F00034 extraction | One call, one education unit, about 62.3 seconds |
| Exact quote/schema | Passed |
| Semantic source coverage | Failed: eight of nine qualification bullets unrepresented |
| CV1 parse, pasted F00022 extraction, evidence matching | Not attempted after stop |
| Probe state | `stopped_semantic_issue`; terminal, not resumed or reset |
| Probe charge | US$0.007648404 |

The omitted content includes the professional minimum, Python, frameworks, LLMs, preferred RAG/cloud/tool experience, soft skills and portfolio alternatives. The degree group also needs shared-qualifier interpretation. No F1 or completeness percentage was reported: bullet count is not atomic-requirement recall.

The safety correction is versioned as `qualification-bullet-coverage-v1`. It rechecks new and cached extractions, marks observed gaps `looks_incomplete`, returns `extraction_review_required`, withholds score, and skips matching. Raw historical output stays intact. Detection is deliberately limited to explicit list sections; wrapped prose, a quote that covers only part of a bullet, and semantic omissions inside one bullet still require review. A pass means only that no supported-format bullet was entirely unrepresented.

### 6.2 Completed scoped repair experiment (3 October)

The old probe above remains terminal. This is the separately authorized new run, with its original US$0.40 aggregate cap retained across the account handoff, repairs and resume. The same baseline model and guideline were used. Gold labels were not given to the model as repair targets.

| Stage | Calls | Time, including both attempts where applicable | Recorded charge | Checked result |
| --- | ---: | ---: | ---: | --- |
| F00034 extraction | 2 | 71.592 s | US$0.018673596 | 16 units represent all 9 qualification bullets; REST API experience, alternative-role duration and named-model categories repaired |
| CV1 parsing | 1 | 154.687 s | US$0.004558000 | 13 facts; education, two jobs and two projects preserved; month/year precision retained |
| F00332 pasted extraction | 2 | 61.955 s | US$0.023246244 | 16 units represent all 8 qualification bullets; Python/SQL/Excel AND and explicit education OR repaired |
| CV1 × F00332 matching | 2 | 64.418 s | US$0.023942700 | 16 assessments; three missing partial soft-skill supports repaired; score unchanged |
| Total | **7** | Serial observed case timings, not a benchmark | **US$0.070420540** | State `complete`, no outstanding request reservation in this run |

The final matching report reuses the exact accepted pasted extraction. No repeated parser, embedding or JD inference was needed during the continuation. The extra matching call cost US$0.010082400 and took 25.151 seconds including local processing. Its per-call conservative allowance was US$0.0492, within the original aggregate authorization.

Manual arithmetic: `(5 MATCH + 0.5 × 3 PARTIAL) / 9 = 72.22%`. One required unit has no evidence. Six soft skills remain outside the denominator: two MATCH, three PARTIAL and one NO_MATCH. The preferred credit-scoring item has no evidence. Experience and location constraints remain `unknown`: no duration minimum is stated, and the location was not confirmed. No unknown condition was turned into a known conflict or compatibility claim.

All 16 extraction units,16 assessment records and both education branches were checked by meaning against the development source. The result is a delegated operational pass. Runtime score status `final` means the identified units meet score-status rules; it is not human certification or model accuracy. The proposed 16 one-to-one gold mappings remain pending human verification. Two differences are retained: learning/mastering new techniques (U15 versus P30-U08) and actionable recommendations (U16 versus P30-U15), model PARTIAL versus gold MATCH. The former is outside the percentage; the latter affects one technical contribution. No F1, gold replacement or forced score agreement is reported.

CV dates use 2026-09-30. The complete listed employment totals 9 calendar months as an upper bound, not 9 months of every technology. Projects are excluded. A nonblocking parser limitation remains: `profile.language` contains a proficiency line rather than a document-language code. No language constraint is evaluated in this case.

Evidence: [final model report](../../evals/results/cp22_extraction_repair_v13_20261003_04_semantic_repair.json), [full semantic check and alignment proposals](../../evals/results/cp22_repair_semantic_review_20261003.json), and [experiment record](supporting/CP22_Extraction_Repair_20261003.md). Earlier attempt files remain intact. These assisted outputs are not silently admitted as unattended public cache successes.

## 7. Verification

Historical 2 October full offline suite: **294 passed, 2 skipped**, with five PyMuPDF/SWIG warnings. The two skipped database cases were separately exercised in the five-test local database selection. These overlapping selections must not be added as a count of unique tests.

Historical test evidence is recorded in `evals/results/cp22_takeover_final_offline_20261002.xml` and `cp22_takeover_database_verified_20261002.xml`. The final verification JSON records exact counts and protected-file checks.

- Full offline suite covers upload layouts, dates, scoring, extraction/matcher failures, cache isolation, budget/probe guards, source coverage, export integrity, and readiness scope.
- Local database selection: **5 passed**, including 632/428 snapshot counts and embedding isolation/rollback. An initial sandbox connection restriction was resolved with authorized local access; that failed attempt is retained separately.
- Source/quote checks and eight fixture expectations pass. Saved gold files, counts and manifest hashes are revalidated after atomic promotion.
- Workbook, frozen split/pool, source dataset, synthetic CVs, original pilot labels and active prompt/model configuration retain their entry hashes. Documentation changes are recorded separately.
- Five PyMuPDF/SWIG deprecation warnings remain. They did not fail extraction tests. Dependencies are already in `requirements.txt`; this continuation added none.

Continuation verification, 3 October: **228 selected offline tests passed,0 skipped**, five known PyMuPDF/SWIG warnings. This covers all changed matching-repair/readiness code, guarded resume, extraction inventory, source coverage, PDF/DOCX/parsing, score/constraints, eight fixtures, export integrity and evaluation preparation. Evidence: [JUnit](../../evals/results/cp22_resume_final_offline_20261003.xml). The earlier 9 repair-guard tests are included in this selection and must not be added as unique cases. After D-050, the changed readiness gate was checked again: 11 tests passed in [separate JUnit evidence](../../evals/results/cp23_D050_readiness_tests_20261003.xml). These tests overlap the earlier selection; they are not 11 additional unique tests.

The final integration is the real-model vertical slice plus offline replay through the ordinary parser/extractor/matcher validators and scorer, followed by saved-bundle and readiness validation. No database behavior changed; PostgreSQL tests/retrieval were not rerun in this continuation. Their prior 5-test/local-retrieval evidence remains historical, not a fresh claim. Workbook, source snapshot, split, pool, gold, model configuration and prompt files remain unchanged from the continuation entry hashes. No dependency was added.

## 8. Cost and reproducibility

Current ledger: **117 records, US$0.290770384**, including the unchanged **US$0.021086100 uncertain reservation** from the separate interrupted run. Confirmed-cost records subtotal **US$0.269684284**; this is not invoice reconciliation. This continuation made **one paid call, US$0.010082400**. The whole repair experiment, including work before the handoff, made **seven calls, US$0.070420540**. The preceding 2 October takeover itself made 0 calls; those historical statements remain in the experiment log.

Hard stop at that time was US$8.50 (raised to US$18.5 by D-070 on 4 October); arithmetic headroom after reservations is US$8.209229616. The closed experiment left US$0.329579460 unused, which does not authorize a new batch or reset its attempt allowance. The initial sandbox DNS failure happened during the read-only key check before dispatch and consumed no inference attempt or charge. Authorized network access then succeeded.

Model availability/pricing and routing documentation were rechecked using the [official endpoint metadata](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4.1-flash/endpoints) and [provider-routing documentation](https://openrouter.ai/docs/guides/routing/provider-selection). The baseline routing ceiling remains US$0.30 input / US$1.20 output per million tokens, with data-collection denial, required supported parameters, strict structured output and zero SDK retries. This is not an independent retention-policy certification.

Reproduce readiness without model calls:

```bash
env-job-fit/bin/python scripts/run_evaluation.py --reviewed-bundle evals/gold/development_v13_reviewed_20261002_r2 --retrieval evals/results/cp22_retrieval_top30_20261002_03.json --acceptance-probe reports/quality_probe/cp22_extraction_repair_v13_20261003.json --output evals/results/cp23_readiness_new_run.json
```

Use a new output filename. Exit 2 currently means the report successfully identified open prerequisites, not that it ran a failed model benchmark. Omitting `--reviewed-bundle` uses the legacy pilot inventory and is unsuitable for current expanded-label readiness.

## 9. Limitations and risks

1. The experimental chain passed delegated source checks only after three semantic repairs across stages. Unattended reliability is not established; the default v1.2 prompt is not silently replaced.
2. Current gold is reviewed-record gold, not an automatically complete, aligned reference for every JD.
3. Two development CV queries give limited ranking diversity. More labeled rows do not create more independent CVs.
4. Unknown/held judgments and partial top 30 coverage must remain explicit in CP2.3.
5. Broad development extraction remains unexecuted. D-050 explicitly carries it forward after CP2.3 configuration evaluation; its original criterion is preserved as history. Held-out extraction still waits for freeze.
6. Optional filters are not implemented in this stage's retrieval comparison.
7. Production PII redaction, TTL, cross-user isolation and provider policy confirmation are future security work. A private discussion note preserves those concerns; no implemented privacy guarantee is claimed.

## 10. Acceptance checklist

- [x] Upload/parser/extractor/matcher/paste backend and controlled failure paths implemented.
- [x] Eight revised synthetic fixtures examined under user delegation and verified automatically.
- [x] Source/version-aware caches, cost guard and stopped-run controls verified.
- [x] Two-model embeddings and comparable development retrieval exist.
- [x] Approved-only expanded gold exported with holds and provenance.
- [x] Frozen split and protected inputs remain unchanged.
- [x] Scoped real-model semantic end-to-end acceptance under experimental JD prompt v1.3, with repairs and interpretation limits recorded.
- [x] Feasible next small-run proposal, aggregate bounds, cache limitations and full-development guard conflict documented.
- [x] User explicitly approved the scope/carryover boundary in D-050.

**Carried forward, not executed:** planned-scale development extraction after CP2.3 configuration evaluation. The original incomplete batch criterion is superseded for this checkpoint only; budget/quality gates and the test freeze remain in force.

## 11. Exact next steps and CP2.3 boundary

1. Use this bundle and readiness report, not old pilot inventory or pending workbook drafts. Do not ask the user to redo all labeling.
2. Reconcile the narrow held cases or choose an explicitly documented compatible comparison subset. Verify complete references and source-to-model alignment for that subset; do not drop requirements to improve scores.
3. Confirm remaining metric conventions before publishing comparisons: NDCG gain, short judged precision, failed-evidence accounting and absent-class macro handling. These are CP2.3 contract decisions, not reasons to rerun CP2.2 infrastructure.
4. The authorized repair experiment is complete. Keep both old failed probes terminal. Review the two specific alignment differences when a quality comparison is prepared; do not ask for another full workbook review. Formal model/prompt/K selection remains CP2.3.
5. **Carried forward under D-050:** the five remaining priority extraction IDs F00016, F00073, F00103, F00074, F00012 have a proposed upper bound US$0.492, proposed aggregate ceiling US$0.50. They were not dispatched. Before a future run, wire the explicit experimental schema and semantic stop/reuse receipts into a staged executor; the legacy batch command still uses the default prompt. Compatible accepted artifacts can be reused for offline review without calls. Do not count a raw first-draft cache entry as the accepted semantic repair.
6. The 214 development jobs have a deliberately conservative maximum US$21.0576 under the 100,000 input / 16,000 output / two-attempt protocol. This is a ceiling, not a predicted bill, and exceeds current project headroom. The two observed JD cases cost US$0.041919840 in total but are too few, selected and assisted to extrapolate a reliable bill or quality rate. No mass execution or budget increase is authorized. Detailed status for all 214 development IDs and token ceilings: [extraction plan](../../evals/results/cp22_development_extraction_plan_20261003.json).
7. D-050 explicitly approves deferring broad materialization until CP2.3 configuration evaluation. Retain this unexecuted work in the implementation backlog with current budget and quality controls. The five-ID proposal is not an automatic next dispatch and need not precede every CP2.3 preparation step.

**CP2.2 complete:** backend implementation, eight delegated fixtures, reviewed-record gold, same-universe retrieval, one assisted live report and an explicit scope receipt. **CP2.3 next:** validate the comparison references/alignments and metric contract, then run preflighted comparative experiments and seek the prescribed configuration/freeze decision. **Later materialization:** approved versioned extraction after those choices. No formal tuning, winner or test evaluation was performed in this session.

## 12. Evidence index

- [Export manifest](../../evals/gold/development_v13_reviewed_20261002_r2/manifest.json), [held records](../../evals/gold/development_v13_reviewed_20261002_r2/held_records.json).
- [Current readiness](../../evals/results/cp23_readiness_after_D050_20261003.json).
- [Top30 retrieval](../../evals/results/cp22_retrieval_top30_20261002_03.json).
- [Probe semantic receipt](../../evals/results/cp22_closure_f00034_semantic_check_20261002.json).
- [Latest verification](../../evals/results/cp22_resume_verification_20261003.json); [historical takeover verification](../../evals/results/cp22_takeover_verification_20261002.json).
- [Historical report before this takeover](supporting/archive/CP2_02_Modeling_Pipeline_before_takeover_20261002.md). Its old status statements and relative links describe their original location/time; they are not current instructions.


## 13. Review and commit inventory

No git command was run. Review the experiment changes already present from the previous execution together with this continuation:

- Runtime experiment: `src/jobfit/extraction/audited.py`, `jd_extractor.py`, `paste_jd.py`; `src/jobfit/pipeline.py`; `src/jobfit/llm/structured.py`, `semantic_repair.py`; `prompts/jd_extraction_v1_3.md`.
- Execution scripts: `scripts/run_cp22_repair_probe.py`, `repair_cp22_semantics.py`, `repair_cp22_matching.py`.
- Readiness: `src/jobfit/eval/bundle_readiness.py`, `scripts/run_evaluation.py`.
- Tests: `tests/test_audited_extraction.py`, `test_semantic_repair.py`, `test_matching_semantic_repair.py`, `test_bundle_readiness.py`.
- Documentation: this report, CP2.3 report, CP2 index, master plan, decisions D-050, experiments, failures, repo structure, documentation index, existing acceptance and extraction-repair supporting reports.
- New versioned evidence: relevant `evals/results/*20261003*` artifacts listed above. The local usage ledger and probe state are reproducibility evidence; follow existing repository privacy/ignore rules before committing them. Private handoff and protected-file receipts stay private.

This is an explicit touched/review list, not a git-derived diff. No dependency was installed; `requirements.txt` did not need a change. Historical gold, workbook, source, split, pool and prompt files were not overwritten by the continuation.
