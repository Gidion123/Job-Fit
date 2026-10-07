# JobFit Experiment Log

One entry per experiment run in CP2 and CP3. Stage reports link here instead of copying numbers, so every number has one source.

## Entry format

| Field | Content |
| --- | --- |
| Run id | `EXP-YYYYMMDD-NN` |
| Date and stage | For example 2 Oct 2026, CP2.3 |
| Hypothesis | Which hypothesis from System Design v1.3 section 21 (H1 to H9) |
| Configuration | Stage-1 method, K, LLM model id, prompt version, embedding model and dimensions, guideline version |
| Data | Split (development or test), number of cases, snapshot `CP1_20260926` |
| Metrics | The metrics named in the hypothesis, with denominators |
| Cost and latency | From the usage ledger; live and cached separately |
| Git SHA | Commit of the code that ran |
| Result and decision | Keep / remove / needs more data, with a link to the docs/decisions.md entry if a decision was made |

## Experiment matrix

Written in CP2.1 (checkpoint 8), 29 Sep 2026; stages aligned with the master plan and M04b added on 1 Oct 2026 (D-044, pending). This is the plan of what gets compared, fixed before any result is seen. Nothing here is a result. No deep learning model is trained in any row (D-001): every row compares search methods, LLMs through OpenRouter, prompts, or fixed rules.

All rows use snapshot `CP1_20260926`, development cases only, until the test set is locked in CP2.3. Model ids and prices are in `config/models_v1.yaml`. A model not in that file cannot be called by the code, so a new candidate needs a row here first.

| Plan id | Stage | Hypothesis | What is compared | Fixed settings | Metric (decides) | Also reported | Est. cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | CP2.1 | Scoring rules match System Design v1.3 section 8 | Rule outputs vs the 8 hand-written fixtures | Score v0, PARTIAL weight 0.5 | All fixtures pass (pytest) | Nothing else | US$0 |
| M02 | CP2.1 | Baselines give a reference point | B0 keyword/skill overlap (CP1 v0 skill list) vs B1 PostgreSQL FTS | Pilot pool, 2 synthetic CVs | Stage-1 Recall@10 on pilot labels (small, only a sanity check) | Latency | US$0 |
| M03 | CP2.2 | H9: extraction is accurate enough | Extraction prompt v1 on `deepseek-flash` | Guideline v1, development JDs | Extraction precision / recall / F1 vs gold | Schema validity, cost, p50/p95 latency | under US$0.20 |
| M04 | CP2.3 | H3: hybrid finds relevant jobs better | B0, B1, B2 dense (`openai/text-embedding-3-small`, 1536 dim), C hybrid FTS + dense RRF | Development CVs, filters off and one filter setting | Stage-1 Recall@K | Filter recall, latency | under US$0.10 (embeddings) |
| M04b | CP2.3 (only if D-044 option A is approved) | H7 and H3: a multilingual embedding model finds relevant jobs better | Dense and hybrid search with `openai/text-embedding-3-small` vs `qwen/qwen3-embedding-8b` | Same pool and K as M04; silver development labels (D-044) | Stage-1 Recall@20; a model wins only if at least 0.05 better | Indonesian-CV gap, cost of embedding the corpus, latency per CV | under US$0.05 |
| M05 | CP2.3 | H2: K between 10 and 30 is enough | K = 10, 20, 30 with the stage-1 winner of M04 | Same pool as M04 | Recall@K and cost per run | p95 latency | under US$0.50 |
| M06 | CP2.3 | H5: a low-cost LLM is within 3 points of the reference | Round 1: `deepseek-flash`, `gpt-6-luna`, `gemini-3.5-flash-lite`, `claude-haiku-4.5`; reference `gpt-6-sol` on at most 10 hard cases | Prompt v1, about 30 development cases, temperature 0 | D-029 rule: safety gate, then evidence Macro-F1, then extraction F1, then cost within 0.03, then p95 latency | Cost per run, schema validity | under US$2 |
| M07 | CP2.3 (only if needed) | H5 round 2 | `deepseek-v4-pro` | Same as M06 | Same as M06 | Same as M06 | under US$1 |
| M08 | CP2.3 | H6: prompt v2 is better than v1 | Prompt v1 vs v2 on the M06 winner | Same cases as M06 | Extraction F1 and evidence Macro-F1 | Cost, latency | under US$0.50 |
| M09 | CP2.3 (development), CP2.4 (test) | H7: embeddings work for an Indonesian CV with English JDs | Recall@K for the Indonesian CV vs the English CVs | M04 winner | Recall@K gap | Examples of misses | US$0 extra |
| M10 | CP2.3 | H1: PARTIAL weight 0.5 makes sense | 0.5 vs 0.25 vs 0.75 | Final pipeline, development | Error audit against relevance labels; NDCG@10 | Examples where the order changes | US$0 (cached) |
| M11 | CP2.3 (development), CP2.4 (test) | H4: evidence match % improves the order | Stage-1 order vs final match-% order | Final pipeline, development | NDCG@10 and P@5 | Safety: hard negatives in top 10 | US$0 (cached) |
| M12 | CP2.3 (only if ties are common) | H8: another tie-break | Stage-1 order (default) vs "more requirements met" | Final pipeline | NDCG@10 | Tie count | US$0 |

Rules for every row:

- Numbers go in the Runs section below, with the run id, git SHA, and ledger cost. Stage reports link to them.
- The test set is used once, in CP2.4, after the choices above are frozen. Only the chosen configuration runs on it, plus the stage-1 methods as a measurement (M11).
- Only synthetic CVs and public job descriptions are sent to OpenRouter (D-021, D-030).

## Runs

### EXP-20261001-01: Baselines B0 and B1 (plan M02)

| Field | Content |
| --- | --- |
| Date and stage | 1 Oct 2026, CP2.1 |
| Hypothesis | Baselines give a reference point (M02); prepares H3 |
| Configuration | B0: share of the job's v0 skills found in the CV (`skill_aliases_v0`). B1: PostgreSQL full-text search, `simple` configuration, title weight A and JD text weight B, `ts_rank_cd`, query = phrase OR of the aliases of the CV's v0 skills. No LLM, no embeddings |
| Data | Snapshot `CP1_20260926`; 632 jobs loaded into PostgreSQL 17 with pgvector (Docker); pool = 428 target jobs (automatic mode, D-009); CV1, CV2, CV3 synthetic |
| Metrics | No gold labels yet for this pool, so no Recall@K. Reported: ranks of the 5 pilot jobs, size of the B1 match set, overlap of the B0 and B1 top 10 |
| Cost and latency | US$0 (no API call); runs in seconds |
| Git SHA | Commit by Dion after this run |
| Output | `evals/results/cp21_baselines.json` |

Results (Dion's run on the Docker database; identical to an earlier dry run on a separate PostgreSQL 16 test database):

| CV | B1 matched jobs | B0/B1 top-10 overlap | Pilot job ranks, B0 / B1 |
| --- | --- | --- | --- |
| CV1 (Rina) | 373 of 428 | 0 | J1 14 / 75; J2 293 / 275; J3 265 / 105; J4 238 / 103; J5 315 / 278 |
| CV2 (Bima) | 392 of 428 | 0 | J1 77 / 208; J2 345 / 302; J3 149 / 61; J4 306 / 107; J5 61 / 21 |
| CV3 (Dewi) | 381 of 428 | 0 | J1 91 / 165; J2 136 / 203; J3 129 / 55; J4 130 / 67; J5 133 / 70 |

Result and decision:

- The two baselines disagree completely on the top 10 for every CV, so stage-1 method choice matters (H3 is worth testing).
- B0 favors jobs with very short v0 skill lists (one matching skill can give 1.0). B1 matches almost every job (373 to 392 of 428) and favors long JDs that repeat terms.
- The only pilot job labeled 3 (CV1 x J1) is ranked 14 by B0 and 75 by B1. One labeled pair cannot compare the methods; Recall@K is computed in CP2.3 on the test pool (D-043).
- Kept as reference baselines. No decision entry.

### EXP-20261001-02: Score v1 on the approved pilot labels (plan M01, check of D-032)

| Field | Content |
| --- | --- |
| Date and stage | 1 Oct 2026, CP2.1 |
| Hypothesis | Score v1 follows the relevance labels better when soft skills are shown separately (D-032) |
| Configuration | Score v1, PARTIAL weight 0.5; soft skills, location, and work authorization outside the percentage; comparison mode with soft skills inside. Input = approved extraction and evidence labels, not model output |
| Data | Development split: CV1 x J1 (21 units) and CV2 x J2 (13 units), guideline v1.2 |
| Metrics | Score %, score status, counts; relevance label of the same pair |
| Cost and latency | US$0 (no API call) |
| Git SHA | Commit by Dion after this run |
| Output | `evals/results/cp21_pilot_scores.json` (`scripts/score_pilot_pairs.py`) |

| Pair | Relevance label | Score v1 | Status | Required met | Soft skills with evidence | Score with soft skills inside |
| --- | --- | --- | --- | --- | --- | --- |
| CV1 x J1 | 3 | 92.86% | provisional (1 unit of unknown importance) | 6 MATCH + 1 PARTIAL of 7 | 2 MATCH + 2 PARTIAL of 9 | 59.38% |
| CV2 x J2 | 1 | 55.56% | provisional | 4 MATCH + 2 PARTIAL of 9 | 0 of 1 | 50.00% |

Result and decision:

- With soft skills outside, the gap between the pair labeled 3 and the pair labeled 1 is 37 points; with soft skills inside it is 9 points. This supports D-032, but two pairs prove nothing on their own. The real check is M10 and M11 on more pairs.
- Both scores are provisional because each JD has one requirement whose importance is unknown (D-042). The app shows this status next to the score.
- CV2 x J2 also has an explicit experience conflict (D-042), which the score does not include; it is shown as a constraint above the score (D-013).
- No decision entry; D-032 stays approved and is checked again in CP2.3.

### EXP-20261001-03: Phase 0 and frozen T03 Part 1 verification

| Field | Content |
| --- | --- |
| Date and stage | 1 Oct 2026, CP2.2 prerequisites |
| Hypothesis | The existing split follows D-046 and can be reproduced without changing frozen files. This is an integrity check, not a retrieval experiment |
| Configuration | Existing component split v1, seed 20261001, role_family x experience_bucket. No model, prompt, embedding, K, or label selection |
| Data | Snapshot CP1_20260926; 428 auditable target jobs; both duplicate review files; frozen record-to-cluster mapping |
| Metrics | 214 development, 214 test; 19 strata; maximum stratum imbalance 1; 5 of 5 pilot jobs in development; 0 of 19 protected cluster pairs cross the split |
| Cost and latency | No provider calls. Session cost US$0; project ledger 0 records, US$0. Offline suite: 7.28 seconds. Database-enabled suite: 7.47 seconds. These are test durations, not pipeline latency |
| Git SHA | Commit by Dion after this run. No git command run. Code hashes are in the output |
| Output | `evals/results/t03_split_verification_20261001.json`; `docs/checkpoint_2/supporting/T03_Job_Split_20261001.md` |

Actual checks:

- The default Anaconda Python 3.13 failed collection because psycopg was missing. The existing project environment passed: `env-job-fit/bin/python -m pytest -q`, 81 passed, 1 skipped. No dependency installation was needed.
- `JOBFIT_DB_TESTS=1 env-job-fit/bin/python -m pytest -q` passed all 82 tests after approved access outside the sandbox. The database test performs an idempotent snapshot load and verifies 632 jobs, including 428 target jobs.
- The local .env exists and contains all 4 required variable names. Loaded budget settings match D-031. No environment values or secrets were printed.
- Independent metadata checks confirmed sorted distinct IDs, complete coverage, disjoint splits, pilot placement, manifest counts, 4 input hashes, 2 output hashes, and the mapping hash in RESEARCH_INPUT_HASHES.json.
- The two review files contain 80 source rows in total: 48 protected target rows, 16 explicitly DIFFERENT rows, and 16 rows outside the target pool. Source rows overlap between files. The protected rows reduce to 19 distinct target-cluster pairs: 18 already merged pairs and F00014/F00812, both in test. No protected pair crosses the split.
- The deterministic script rerun changed none of the input files, split ID files, manifest, or pilot workbook. The workbook layout was inspected read-only and its bytes stayed unchanged.

Result and next step: the existing T03 Part 1 implementation is verified. No split assignment, code, label, or decision was changed. D-045 approval was already present in decisions.md. STOP for Dion to review the stratum counts. T03 Part 2 and later tasks were not started. CP2.2 remains IN PROGRESS.


### EXP-20261001-04: Versioned embedding implementation and blocked live build

| Field | Content |
| --- | --- |
| Date and stage | 1 Oct 2026, CP2.2 |
| Purpose | Verify implementation, cost controls, and access before a live corpus build; no quality comparison or configuration selection |
| Configuration | OpenAI 1536 and Qwen 4096 native dimensions; title-clean-jd-cv-body-v1; exact cosine; RRF k60, branch depth 20; batch16, max64000 tokens; required privacy routing and maximum prices |
| Data | 632 fixed public JDs and CV1/CV2 only. Future smoke retrieval restricted to frozen 214 development IDs; no test CV queries or labels |
| Preflight | 805,727 tokens; estimated US$0.01208639; conservative US$0.06603606; no truncation |
| Actual result | Original and resumed first batches rejected HTTP 401; one single-input diagnostic rejected likewise. `/key` reports management key. Zero vectors, Qwen not attempted, no live search smoke |
| Cost | Three rejected inference records, US$0 total including prior run. Read-only key checks do not run inference |
| Verification | Final database-enabled suite 120 passed in 7.72s; approved CV and frozen split hashes match |
| Evidence | `evals/results/embedding_continuation_audit_20261001.json`, `embedding_resume_20261001.json`, `embedding_key_preflight_20261001.json`; supporting embedding implementation report |
| Source revision | Source files are local changes; Dion handles commit. No git command executed |

Interpretation: local behavior is verified, model quality and provider routing are not. Added a key-type check to reject management keys before inference and atomic cache/report writes to support interrupted-run recovery. FAIL-03 records the access diagnosis. Next: regular inference key, resumed live build, stored-vector and scoped-search checks. STOP before labeling workbooks.


### EXP-20261001-05: Successful two-model embedding build and cache verification

| Field | Content |
| --- | --- |
| Date and stage |1 Oct 2026, CP2.2 |
| Configuration | Same profiles/preprocessing as EXP-04; strict per-model native response aliases added after FAIL-04; regular inference key replaced by Dion |
| Data |632 public jobs per model; CV1/CV2 only. Query/cache provenance and search scope remain separate from held-out CV3/CV4/CV5 |
| Actual build |632 job + 2 query vectors per model,1268 total;82 successful inference requests; no truncation or failed batch |
| Storage | OpenAI1536 and Qwen4096 dimensions in separate profiles; legacy table and job inventory unchanged |
| Retrieval | Four model/CV checks: dense20, hybrid20, stable repeated hybrid; all returned IDs in development214 |
| Cache | Post-build preflight: zero pending jobs or queries on both profiles; zero additional cost; ledger unchanged |
| Tests | Final database-enabled suite:123 passed in 8.39 seconds. Aliases are accepted only for their respective model; unrelated model still rejected |
| Cost | Successful build US$0.01209273; all-session ledger US$0.01226822 including US$0.00017549 billed validation failures. Three auth rejections cost 0. All 85 billed records use reported cost |
| Evidence | `evals/results/embedding_validated_aliases_20261001.json`, `embedding_cache_verification_20261001.json`, `embedding_continuation_audit_20261001.json`; supporting CP2.2 embedding report |
| Source revision | Source hashes in continuation audit; Dion handles commit; no git command executed |

Interpretation: pipeline readiness is verified, not ranking quality or a winning model/K. No label or workbook changed. STOP before T03 Part 2/T04/T05 workbooks. CP2.2 remains IN PROGRESS pending the remaining vertical slice and labeling work.

EXP-04 is the historical blocked attempt. FAIL-03 access is resolved; FAIL-04 aliases are fixed. Costs from rejected local validations remain recorded rather than being treated as free failures.


### EXP-20261001-06: Development pooling and pending annotation drafts

| Field | Result |
| --- | --- |
| Scope | T03 Part 2, T04 steps 1-2, T05 drafting; no model or K selection |
| Methods | B0, B1, dense/hybrid OpenAI, dense/hybrid Qwen; RRF k60, depth 20 implementation defaults |
| Data | Frozen214 development only; CV1/CV2 only; cached vectors |
| Pool | CV1:29 rows,17 mandatory new top-five candidates; CV2:34 rows,18 mandatory.20 new review rows per CV, no cap conflict |
| Drafts | Three extraction JDs,84 units;60 relevance drafts,40 designated for review. No evidence drafts or new gold export |
| Checks | Exact source quotes/text, untouched protected inputs, pending labels, full pool coverage.125 tests passed with DB in 7.67s |
| Cost |0 API calls; additional US$0; previously recorded project ledger US$0.01226822 |
| Evidence | evals/results/t03_dev_pool_20261001.json; development_workbook_qa_20261001.json; supporting/T03_T04_T05_Development_Review_20261001.md |

Interpretation: the review subset covers every candidate-method top-five result within the approved40 new-label capacity. No quality metric is reported from draft judgments. F00020's mentoring duties conflict with its v0 engineering label; draft relevance 0 is flagged for human review, not written back to the snapshot. Duration applicability and degree equivalence remain review cases. The D-038 blind-sample instruction versus T05 draft-all instruction was raised to Dion. His answer is recorded as approved D-047: complete drafts followed by human review for current development batches; held-out test unchanged. No label or model selection was approved. STOP before evidence drafting and gold export.

### EXP-20261002-01: Complete combined development drafts

Scope: D-048 preparation only. Frozen development pool plus retained optional extraction pairs; CV1/CV2 only. One pilot-format workbook contains 54 JDs, 67 pairs, 1,069 A units, 1,387 B rows, and 67 C judgments. Preserved approvals: A39, B21, C3. New draft rows remain pending. No gold export, model selection or quality metric is inferred from draft labels.

Checks: saved-file exact quotes and sources, unchanged protected rows, complete pair/unit coverage, split isolation, native list-validation XML, Timing boundaries, nine rendered sheet previews and 13 semantic spot checks. Audit: `evals/results/development_combined_workbook_qa_20261002.json`. Excel UI behavior is not independently tested. F00364 has zero qualification units; F00369's truncated clause remains flagged. Original books are archived byte-for-byte. Additional API calls/cost: 0/US$0. Ledger unchanged at US$0.01226822. D-045 review priority unchanged; A edits require dependent B/C review.

### EXP-20261002-02: Upload and pasted-JD backend verification

| Field | Result |
| --- | --- |
| Scope | CP2.2 implementation, not model selection or held-out evaluation |
| Data | Synthetic CV1 two-column PDF, development pilot J1/F00022, eight static fixtures |
| Configuration | Reference date 2026-09-30; existing deepseek-flash baseline via OpenRouter. Later runs: low reasoning, 16,000 output tokens. JD v1 preserved; v1.1 corrects approved AND/D-041 precedence and states existing schema invariants |
| Live history | Six reports `_01` through `_06`, failures retained. Run 04 completes the live chain with score held; run 06 reuses its valid synthetic CV parse and produces21 units plus matching on first attempts |
| Latest result | Provisional91.67%, denominator 6; approved pilot 92.86%, denominator 7. Importance/grouping and soft-skill differences remain. No accuracy or calibration claim |
| Tests | 161 passed with database,0 skipped,8.63 s; five PyMuPDF SWIG warnings. Eight fixtures pass automated checks, not human sign-off |
| Cost | 17 new calls,US$0.15938080; entire ledger US$0.17164902 |
| Batch | Script/preflight ready;214 development pending,214 test deferred. Conservative bound US$13.8128838 exceeds authorization/guard; expected bill is uncertain |
| Evidence | evals/results/cp22_pipeline_verification_20261002.json; cp22_live_cv1_j1_20261002_*.json; supporting/CP22_Pipeline_Implementation_20261002.md |
| Protected work | Workbook hash unchanged; no gold export, test development, git, deletion or budget change |

Interpretation: the backend executes and rejects invalid outputs, but schema/quote validity does not prove completeness or correct labels. CP2.3 must measure quality on approved development gold. CP2.2 remains IN PROGRESS. Final audit hashes describe final code, not every intermediate run. SDK inactivity timeout is not a total wall-clock bound: some JD calls exceeded two minutes. See FAIL-05 to 07 and the detailed implementation report.

### EXP-20261002-03: Offline pipeline audit and proposed pilot alignment

Actual work: reproduced implementation edge cases with fake clients and temporary review data; final selected suite 164 passed,0 skipped,5 SWIG warnings in 0.55 s. Includes shared budget and embedding client regression checks; no database suite or new model inference. The earlier database-enabled161 count is a different test set.

Saved run 06 versus approved development CV1/J1:21 A and 21 B reference/model records,20 pending alignment groups (18 one-to-one,1 merge,1 split). No F1/Macro-F1 or human semantic approval. J4/F00016 verified development with 21 approved A and no approved B. A real preflight-only command for F00016/F00034/F00073 gives conservative bound US$0.1912998, pending3,cache0. No extraction executed; the 214-JD batch remains deferred.

Review-export preparation ran only on temporary fixtures. Pending/rejected exclusion, A-to-B/C dependency acknowledgment, approved validity, immutable provenance and protected gold staging were checked. Legacy pilot exporter now refuses a frozen split. Active workbook, gold, sources, split, prompts/configuration and ledger unchanged at the integrity check.

Cost:0 project API calls,US$0 this audit; ledger 105 records,US$0.171649020. Evidence: `evals/results/cp22_pipeline_audit_20261002.json`, `cp22_pipeline_audit_final_tests_20261002.xml`, `cp22_pilot_alignment_review_20261002.json`, `cp22_pilot_remaining_preflight_20261002.json`; [audit report](checkpoint_2/supporting/CP22_Pipeline_Audit_20261002.md). CP2.2 stays IN PROGRESS.


### EXP-20261002-04: Controlled pilot extraction probe (guideline v1.2)

Approved scope: F00016 then F00034 then F00073, aggregate US$0.20 including repair/resume; project hard stop US$8.50 unchanged. Fixed baseline deepseek/deepseek-v4.1-flash, JD prompt v1.1, guideline v1.2. Official endpoint metadata saved; conservative preflight US$0.1912998. Protocol/fake-client checks ran before calls.

F00016: initial ValidationError, one permitted repair succeeds with 21 units; two calls US$0.01550648,225914ms stage. Full source and21gold/model units read; operational continuation passed with minor differences, no human alignment approval. F00034:16units first attempt,US$0.00445984,120151ms stage; role/duration alternative representation and unresolved portfolio group require review. Protocol stopped_semantic_issue; F00073 was not called. No evidence matching inference or F1. Proposed J4/J3 alignments remain pending.

Total3calls US$0.01996632; ledger108records US$0.191615340. Two public-JD cache successes preserved; semantic validity is not implied. Evidence: `evals/results/cp22_pilot_probe_review_20261002.json`, provider/preflight/operational/alignment artifacts, and [audit report](checkpoint_2/supporting/CP22_Pipeline_Audit_20261002.md). FAIL-09/10 distinguish repaired process failure from semantic failure. No mass extraction or workbook/gold write.

### EXP-20261002-05: Offline evaluation preparation and D-049 adoption

After the v1.2 probe stopped, user requested coordinated runtime adoption of manual v1.3. New JD/evidence prompts, explicit config versions, cache separation, result provenance and structural hold follow approved D-049. Scorer formula and old gold/results remain unchanged. Metrics/readiness functions were exercised with synthetic manually computable examples; actual CP2.3 tuning is not run. Prerequisites block unverified alignment, partial-JD completeness assumptions, mixed versions/scope, insufficient ranking depth and missing metric conventions.

Final selected offline suite:213passed,0failed,0skipped,5SWIGwarnings,0.61s. No database rerun, v1.3model call, new dependency or API cost for this adoption. Current evidence: `evals/results/cp22_v13_adoption_20261002.json`, `cp22_v13_final_tests_20261002.xml`, `cp23_readiness_v13_20261002.json`. Earlier186test and v1.2probe artifacts preserved. Workbook saves during human review were retained; no automatic label approval/version change. CP2.2 remains IN PROGRESS.


### EXP-20261002-06: Cache-only comparable retrieval and acceptance preflight

Six methods × CV1/CV2 on the same214development target IDs, no optional filters:12successful top30rankings. Existing OpenAI/Qwen corpus vectors and four query caches validated and reused. Database repeatable-read/read-only; no source or pool writes. Branch_depth30 is a run-local depth extension from default20, RRF60 unchanged; no model/K selection. Final `evals/results/cp22_retrieval_top30_20261002_03.json` records hashes, vectors' metadata receipts, scope, applied filters, timing boundaries and tie rules. `_02` and `_03` rankings identical; one fixed-order local measurement is not a production benchmark. `_01` local DB access failed in sandbox; authorized retry succeeded.

Targeted tests:13runner/pool passes,29scoring/fixture passes separately. An intermediate unmatched parenthesis caused test collection failure; fixed, failed XML retained. No full suite/database test-suite claim; database evidence is actual retrieval plus source/profile validation. Eight fixture outputs pass deterministic expectations but human acceptance remains pending; semantic compatibility limitations documented.

Preflight only: separate proposed v1.3 F00034 extraction then CV1×pastedF00022 chain, max8calls including repair, upper US$0.3362892, proposed aggregate US$0.40. No inference executed under this plan. Current ledger109records US$0.21270144 includes uncertain US$0.0210861 from a separate interrupted run; this task cost US$0. Read [acceptance summary](checkpoint_2/supporting/CP22_Acceptance_Review_20261002.md). No metrics, label approval, gold export, winner or test evaluation.


### EXP-20261002-07: Fixed v1.3 closure probe and reviewed-record export

Continuation of authorized closure work, not model/prompt tuning. The preceding execution completed one F00034 call in `cp22_v13_acceptance_probe_after_closure_20261002`: one education unit, schema/quote valid, eight qualification bullets omitted. Stage took about 62.3seconds, US$0.007648404. Semantic receipt stops the run; three downstream stages remain unattempted. No reset, F1 or full-chain success.

The takeover revised eight synthetic fixtures under existing D-049 rules, added a conservative source-bullet coverage hold before matching (including cache hits), and promoted approved-only versioned gold:1,058A/1,364B/69C.45A/39B/5C retained holds and10A/16B rejected decisions remain explicit. Three additional technical-category holds in D1/D2/D3 were propagated to B. Workbook, pilot label data, corpus, split/pool and CVs unchanged. Gold includes non-overlapping pilot rows exactly once.

Final full offline suite294passed/2skipped,5SWIG warnings; local database selection5passed separately. Readiness revalidates12saved top 30 runs and inventories new gold without metrics or winner. Entry hashes and saved bundle verified. Latest ledger110records US$0.220349844 includes US$0.0210861 uncertain reservation. Takeover API calls0; no new dependency or git. CP2.2 remains IN PROGRESS; CP2.3 formal tuning NOT RUN.

Evidence: `cp22_takeover_verification_20261002.json`, `cp23_reviewed_bundle_readiness_20261002.json`, current gold manifest, `cp22_closure_f00034_semantic_check_20261002.json`, and the [English CP2.2 report](checkpoint_2/CP2_02_Modeling_Pipeline.md).

### EXP-20261003-01: Pre-registered extraction coverage repair

Authorized additional cap US$0.40 including repair. Fixed baseline, experimental JD promptv1.3 plus qualification-inventory wire checks; default pipeline/prompt/model selection unchanged. Frozen stage order:F00034,CV1parse,F00332paste,CV1×F00332match. Conservative maximum US$0.3936/8attempts. Semantic checks between stages; terminal stop on material error. Source-based selection of F00332 occurs before inference; initial F00505 rejected for a reference category issue. No gold/workbook/test mutations. See [experiment record](checkpoint_2/supporting/CP22_Extraction_Repair_20261003.md) for results and exact boundaries.


**EXP-20261003-01 completion,3 October:** seven real calls,US$0.070420540 total across the original execution and continuation. F00034 two calls US$0.018673596;CV1 parse one US$0.004558;F00332 two US$0.023246244;matching two US$0.023942700. All four stages completed with delegated source checks, not new human gold approval.16 assessments,72.22%,denominator 9; two gold interpretation differences pending alignment. No F1/model winner. The continuation added one matching repair US$0.010082400, reused accepted session extraction, and preserved historical results. Default configuration unchanged.

228 selected offline tests pass,0 skipped,5 SWIG warnings. Readiness now accepts an explicit, hash-checked completed operational-probe receipt without enabling metrics or selecting a baseline. Gold 1058 A / 1364 B / 69 C and protected hashes revalidated; no workbook write, gold export, DB rerun, test evaluation or dependency. Ledger117 records US$0.290770384includes unchanged US$0.0210861uncertain reservation. CP2.2 IN PROGRESS for planned-scale outcomes, not the now-completed small live chain. Next extraction preflight has5priority IDs US$0.492 maximum;full 214US$21.0576conservative ceiling does not fit the guard. Both are proposals, no dispatch.

Evidence: `cp22_resume_final_offline_20261003.xml`, `cp22_resume_verification_20261003.json`, `cp22_repair_semantic_review_20261003.json`, `cp22_development_extraction_plan_20261003.json`, `cp23_readiness_after_repair_20261003.json`. Initial sandbox DNS failure in read-only key check happened before inference; no charge/attempt, authorized retry succeeded.


**Checkpoint scope receipt, D-050 (3 October):** after reviewing the completed evidence, Dion explicitly approved CP2.2 implementation closure and carrying broad extraction forward after CP2.3 configuration evaluation. CP2.2 is DONE under that scope; the pre-decision IN PROGRESS status above is historical. No additional inference or measured quality result accompanies this administrative decision. New readiness artifact: `cp23_readiness_after_D050_20261003.json`; broad materialization is a carryover, not a circular prerequisite for the comparisons that select its configuration.


**Final verification:** 36 protected-file hashes match the continuation entry, including the active workbook. Saved gold has A:54 JDs/1,058 units; B:53 JDs/66 pairs/1,364 rows; C:53 JDs/69 pairs. No exported F00369 and no orphan B identity. D-050 readiness regression:11 tests passed after the scope decision, overlapping the earlier228-test selection; no new paid call or DB rerun. Verification: `evals/results/cp22_resume_verification_20261003.json`.

### EXP-20261003-02: D-052 offline Stage-1 evaluation preparation

Read-only reviewed-gold/source/saved-ranking inspection proposed seven development JD references and four fixed-input evidence pairs. Original-top10 union across six methods × CV1/CV2 has70distinct pairs:61eligible judged,6new unjudged and3held. No relevance label was created or changed; F00369 provenance and two existing C holds remain explicit. The versioned case/gap/readiness manifests and the [English supporting report](checkpoint_2/supporting/CP23_Stage1_Evaluation_Preparation_20261003.md) are the receipts.

The D-052 evaluator now computes original-position P@5/NDCG and labeled-pool Recall@K, counts failed evidence as gold-class FN, and blocks unsupported three-class selection and unverified/incomplete extraction alignment. Final targeted offline command adds `--junitxml=evals/results/cp23_stage1_offline_tests_20261003_v2.xml` to the six-module command in the supporting report →72passed,0skipped. No database, model call, cost, quality metric, winner or configuration promotion. The final protected-input verification receipt confirms24/24hashes unchanged and the ledger at117records/US$0.290770384; session cost US$0. CP2.2 remains DONE under D-050 and CP2.3 formal tuning remains NOT RUN.

### EXP-20261003-03: D-054 Stage-1 closure and Stage-2 extraction preflight

Dion's explicit D-054 case reviews were applied in a new immutable r3 gold bundle: 1,058 A / 1,364 B / 78 C, with two F00332 B changes and nine reviewed C additions; the previous bundle and workbook remain intact. Updated seven-JD/four-pair and original-top10 receipts show 70/70 eligible judged development pairs. Five Stage-1 prerequisite gates are ready; future model output alignment and quality are not inferred. Targeted Stage-1 tests:78passed/0skipped. See the [Stage-1 closure](checkpoint_2/supporting/CP23_Stage1_Evaluation_Preparation_20261003.md#6-d-054-closure-and-current-stage-1-status-3-october).

The [Stage-2 preflight](checkpoint_2/supporting/CP23_Stage2_Comparison_Preflight_20261003.md) fixed four D-029 candidates on the same seven JDs and experimental prompt v1.3. It computed a conservative US$3.191929 bound for 28 cases/at most56calls including one repair each. The batch awaits explicit approval of a proposed US$3.20 cap. A guarded, resumable one-stage runner and fake-client mutation tests were added; final selected offline command in that report passed41/0. Earlier v1 XML contains two corrected test-assertion mismatches; v2/v3 pass. No paid call, database run, model-quality metric, prompt promotion, winner or test access. Ledger remains117records/US$0.290770384, including US$0.0210861 uncertain historical reservation; this session spent US$0. Protected-input snapshot:24/24unchanged.

**Actual Stage-2 continuation, same date:** Dion approved the exact US$3.20 cap. One DeepSeek/F00332 first attempt returned13units from8qualification bullets; exact quotes/schema passed, but source review found merged Python/SQL/Excel AND obligations, missing education OR structure and merged large-tabular/actionable-communication obligations. Batch stopped after 1/28cases; no repair or later candidate call. Provider-reported charge US$0.00478664, latency394.786s, ledger118records/US$0.295557024 including the historical uncertain US$0.0210861. No quality metric/winner. A separate four-pair fixed-input adapter was built offline with73logical units and13OR groups; selected adapter/runner/evaluator tests43passed/0skipped. See the same Stage-2 report section 5 and FAIL-15. The earlier preflight statement above is historical; no further paid scope is inferred from unused cap.

**Offline v1.4 revision:** A new experimental prompt restates the approved AND/OR atomization check with generic examples, without changing the guideline, gold, active prompt or source set. A fresh four-model/seven-JD plan estimates US$3.2232974 including repair; proposed cap US$3.23 requires its own approval. Targeted offline tests44passed/0skipped. No v1.4 paid call or quality result at this preflight snapshot. The prior v3 run remains terminal; see the Stage-2 report section 6.

**Matcher-only payload preflight, same day:** four reviewed CV/JD pairs across four models were captured without inference using the ordinary evidence matcher boundary. The source-checked fixed adapter preserved73logical units and13OR groups. CV1's saved parse/source hash matched; CV1/F00036 duration0.75year is only the complete-employment upper bound. The32-call conservative bound including repair is US$1.8464752, **not** a payment approval or actual charge. Selected offline tests after this addition45passed/0skipped; no matching inference or model comparison metric. The earlier44-count is its historical prior subset.

**Actual v1.4 first stage, same date:** Dion approved the distinct US$3.23 v4 extraction plan under D-056. DeepSeek/F00332 produced a17-unit final draft after2attempts, with all8source qualification bullets mapped and exact quotes. Source QA found that the education group does not represent the “other disciplines will be considered” branch, though `needs_review=true` prevents silent scoring; the reviewed trend/anomaly obligation is also split. The durable batch stopped at 1/28stages. Stage latency93.293s; charges US$0.007094697+US$0.0150615=US$0.022156197. Ledger120records/US$0.317713221 including the historical uncertain US$0.0210861 reservation. No other model/JD, matcher call, F1 or winner. The first typed draft was not separately retained. See [Stage-2 report section 7](checkpoint_2/supporting/CP23_Stage2_Comparison_Preflight_20261003.md#7-actual-v14-first-stage-and-source-semantic-stop) and FAIL-16. Historical preflight and v3 failure statements above remain as their dated snapshots.

**Offline continuation preparation, same day:** A distinct v5 plan reuses the exact v1.4 protocol and carries the failed v4 case as an external observation; the remaining27stages have a conservative bound US$3.1559888. The proposed US$3.16 cap and continue-after-documented-semantic-failure policy await Dion's approval. The guarded executor retains typed attempts and stops on missing QA, process/transport uncertainty or budget. Targeted fake-client/mutation suite16passed/0skipped; **zero v5 calls and US$0 v5 cost**. This is protocol readiness, not candidate quality, F1 or a winner. Details and plan SHA are in [Stage-2 report section 8](checkpoint_2/supporting/CP23_Stage2_Comparison_Preflight_20261003.md#8-proposed-same-protocol-continuation-no-paid-dispatch).


### EXP-20261003-04: Versioned Stage-2 takeover and GPT route repair

Dion authorized finishing Stage 2 then Stage 3. The existing DeepSeek/F00018 result received delegated full-source QA; cloud/AWS merging and shared branch qualifiers remained failures. V5 attempted GPT/F00332 once and stopped on a zero-charge process rejection. D-057/D-058 record v5 approval and the explicitly approved v6 compatibility protocol, with the same cumulative US$3.16 ceiling and no changed model/prompt/gold. The experimental adapter omits unsupported GPT temperature and recognizes its published dated ID. First adapted GPT request succeeded; each next case receives source-based QA. Collection is still in progress; the final per-case inventory, costs and limits will be recorded in the Stage 2 supporting report. No matching inference, approved candidate alignment, F1, winner or test evaluation follows from this entry.

### EXP-20261003-05: Six-method development retrieval comparison

Saved twelve top 30 rankings were evaluated against the current78 reviewed C records on the same 214-job development universe, CV1/CV2 only. Complete original top 10 coverage enables P@5/NDCG@10 for all12runs. Macro values: B0 0.500/0.604; B1 0.400/0.450; dense OpenAI 0.200/0.378; dense Qwen 0.300/0.547; hybrid OpenAI 0.200/0.380; hybrid Qwen 0.300/0.522. Hybrid Qwen labeled-pool Recall@30=0.671,46/60positions judged. No unjudged item is declared irrelevant; no corpus recall or filter recall claim. Each method's macro mean covers only two CV queries.

Result `evals/results/cp23_stage3_retrieval_evaluation_20261003_v2.json`, per-CV CSV and [English report](checkpoint_2/supporting/CP23_Stage3_Retrieval_Comparison_20261003.md) retain provenance and limitations. V1 is an initial same-number calculation receipt; v2 binds evaluator/script and existing query-cache hashes. Single local invocation timing excludes query embedding, LLM and preparation; no productionp95claim. Existing vectors reused, no API or database run in this evaluation, session cost US$0. No configuration selected. Targeted offline verification64passed/0skipped, JUnit `cp23_takeover_targeted_tests_20261003_v1.xml`.


### EXP-20261003-06: Preserved partial extraction inventory and terminal Gemini failure

Frozen experimentalv1.4, seven development JDs, four original candidates. V5/v6 continuation has 19/28original cases attempted (including externalv4firstcase);18process-valid final drafts and one process failure. No inferred winner, F1 or gold amendment. Detailed counts, semantics and cost are in [Stage-2 section 9](checkpoint_2/supporting/CP23_Stage2_Comparison_Preflight_20261003.md#9-current-takeover-results-v5v6-terminal-stage-3-measured). Gemini/F00815 retained first typed source-mapping failure plus rejected repair; terminalv6was not reset. Proposedv7covers only nine unattempted cases with bound US$2.0236408 and awaiting protocol approval. Latest offline verification73passed/0skipped; earlier fixture-setup failure retained. Total ledger US$0.4521917578, cumulativev5/v6US$0.1344785368. Stage 3 retrieval is complete for its measured no-optional-filter scope; selection and later stages remain open.


### EXP-20261003-07: Round-one extraction collection completed with failures retained

D-059 authorized only nine unattempted original extraction cases; v7 completed all nine with delegated source checks. Across preserved v4/v5/v6/v7, 28/28 cases were attempted; 27 final process-valid objects, one retained Gemini process failure, one of the 27 finals passing all five source checks. Candidate alignment/F1, evidence matching and winner remain unavailable. Current [inventory](../evals/results/cp23_stage2_v14_observation_inventory_20261003_v3.json) and [Stage-2 section 10](checkpoint_2/supporting/CP23_Stage2_Comparison_Preflight_20261003.md#10-round-one-extraction-collection-completed-under-d-059) provide case-level evidence, cross-candidate semantics, sequential timings and exact costs. V5/v6/v7 cost US$0.2937456968 under the same US$3.16 cap; total project accounting US$0.6114589178 includes the separate historical uncertain US$0.0210861. This takeover added US$0.224907120. Final targeted tests: 73 passed, zero skips; 72 protected hashes unchanged. No broad extraction, test access, active-config promotion, matching call or git operation.


### EXP-20261003-08: Stage-2 complete alignment proposals and fixed matcher preparation

Per Dion's sequencing instruction, later-stage work is paused until Stage 2 closes. All 27 saved drafts have complete proposed gold/model mapping inventories (447 rows, including one complex many-to-many); the retained Gemini failure stays in the original common-case denominator. Mapping acceptance and two explicit metric conventions remain pending. Revised notes correct historical branch-qualifier warnings using the active matcher's parent inheritance and ordinary-depth policy, without rewriting old outputs or receipts. See [current preparation](checkpoint_2/supporting/CP23_Stage2_Comparison_Preflight_20261003.md#11-stage-2-closure-preparation-and-sequential-work-boundary).

Fixed matching references cover73units/4pairs with35MATCH,22PARTIAL,16NO_MATCH. A new guarded16-stage runner defaults to preflight;32maximumcalls including repairs have conservative bound US$1.8464752 and a proposed separate US$1.85cap awaiting authorization. No matching inference or quality selection. Targeted preparation30passed/0skipped;72protectedinputhashesunchanged. Session API cost US$0; ledger US$0.6114589178 including historical uncertainty US$0.0210861. Preliminary synthetic privacy prototype18localtests passed previously; later-stage implementation is paused and no real-CV release is implied.


### EXP-20261003-09: round-one fixed-input matching and accepted quality metrics (M06)

- **Data/configuration:** four D-029 candidates × four frozen development CV1/CV2 pairs; 73 logical evidence units per candidate, active evidence prompt v1.1/guideline v1.3. Existing experimental JD v1.4 extraction outputs from all seven JDs are evaluated separately.
- **Approval:** D-062 exact matching ceiling US$1.85; D-060/D-061 conventions and D-063 accepted mapping/fixed-input receipt.
- **Results:** 16 matching stages, 23 API calls, nine process-valid finals, seven retained process failures. Extraction F1 / evidence Macro-F1: DeepSeek 0.861789 / 0.760806; GPT Luna 0.793651 / 0.744424; Gemini 0.613333 / 0; Claude 0.541667 / 0.186681. Failures remain in common-case denominators.
- **Safety:** source QA across 162 valid final logical-unit assessments, all alternative positive branches and sixteen typed first drafts. Eight confirmed unsupported positives, five interpretation questions and one citation-context issue; no prediction/gold correction. No round-one tested configuration meets every safety/operational gate.
- **Cost:** matching US$0.156686829; project ledger US$0.7681457468 including historical unresolved US$0.0210861. Original extraction+matching comparison US$0.4725887228. Rejected repair costs/latency retained; quick rejections are not fast successful analysis.
- **Verification:** 16 targeted offline tests passed, zero skipped; database suite not repeated. Git intentionally not used.
- **Artifacts:** `evals/results/cp23_stage2_round1_quality_evaluation_20261003_v1.json`, `cp23_stage2_matching_semantic_QA_20261003_v1.json`; English [comparison report](checkpoint_2/supporting/CP23_Stage2_LLM_Comparison_20261003.md).
- **Decision boundary:** no winner or test evaluation. D-029 reference/round-two and a proposed portable repair framing remain separately gated; no follow-up paid calls.


### EXP-20261003-10: D-064 quality reference and round two

Approved 19-stage development follow-up completed in 25 calls: GPT Sol8/8 process-valid; DeepSeek Pro10/11, retaining its CV1/F00036 matching quote-validation failure. Same JD v1.4/evidence v1.1 rubric, new portable repair framing and explicit GPT sampling adaptation. Five of six repairs recovered a valid final stage; no new HTTP 400 rejection was observed, without claiming the historical cause is proven. No runtime default or gold changed.

Fixed-input evidence: GPT Sol Macro-F1=0.818094, DeepSeek Pro=0.496283;73 reference units/model, failed units kept as gold-class FN. Source QA covers129 valid final assessments and eleven typed matching attempts. Unsupported positives and source-interpretation limitations prevent an automatic winner. Eleven extraction drafts/188 proposed mapping relations await new acceptance; separate 73-unit common-four and 120-unit full-seven comparisons are prepared. D-064 cost US$0.4054182374; ledger US$1.1735639842 includes historical uncertain US$0.0210861.

[Full English report](checkpoint_2/supporting/CP23_Stage2_LLM_Comparison_20261003.md#9-d-064-measured-follow-up-and-current-closure-boundary), [evidence/QA artifact](../evals/results/cp23_stage2_followup_matching_evaluation_20261003_v1.json), and [new mapping review](checkpoint_2/supporting/CP23_Stage2_Followup_Alignment_Review_20261003_v1.md). Historical request failures remain. Tests and hash checks are recorded in the report; no DB rerun, test data or broad extraction.

**Prompt retention:** every used prompt remains versioned. [Prompt index](../prompts/README.md) and dated content/hash inventory preserve the rubric, guideline, schema/request context and portable repair implementation. New versions must record their reason, predecessor, run, cost and outcome; a proposed prompt is not an executed experiment.


### EXP-20261004-01: repair-only framing replay

Executed on 3 October 2026 UTC for 4 October presentation preparation. Eight confirmed rejected repairs reused their original saved drafts; no repeated first attempts. Two process-valid stages, six retained matching validation failures. Actual US$0.09795280; approved cap US$0.65; conservative upper US$0.6485602. Ledger US$1.2715167842 includes historical uncertain US$0.0210861. [Actual summary](../evals/results/cp23_stage2_repair_rerun_20261004_v1_summary.json), [A/B source QA and metrics](../evals/results/cp23_stage2_repair_comparison_20261004_v2.json). New Gemini extraction F1 awaits mapping acceptance.

### EXP-20261004-02: offline evidence guardrails

G1/G2 lower four of eight original unsupported positives, plus two new Gemini skills-list findings. Remaining original scope claims are not fixed. B Macro-F1 with proposed guards: DeepSeek 0.777417, GPT 0.744424, Gemini 0.282540, Claude 0.251754. No runtime adoption or gold edit. [Per-class counts and change receipts](../evals/results/cp23_stage2_repair_comparison_20261004_v2.json). API cost US$0; D-065 pending.

### EXP-20261004-03: apply D-044 embedding rule

Saved development Recall@20 gains exceed 0.05 for Qwen in dense and hybrid comparisons. Qwen selected by the pre-registered rule on two CVs; runtime unchanged pending freeze. Hybrid Qwen leads recall, B0 leads P@5. [Rule receipt](../evals/results/cp23_embedding_D044_selection_20261004_v1.json). API cost US$0; no new retrieval or vectors.

### EXP-20261004-04: gold-input upper-bound ordering (M10/M11)

Six methods, two CVs, three K values, three PARTIAL weights. All 108 cells retain missing/held A/B rather than creating scores. Complete score-order metrics unavailable in 108/108 cells; original rank metrics retained. 104 distinct CV/job pairs lack usable A/B somewhere in the top 30 union. No K/weight optimum claimed. [Result](../evals/results/cp23_gold_input_upper_bound_20261004_v1.json), [short report](checkpoint_2/supporting/CP23_Gold_Input_Upper_Bound_20261004.md). API cost US$0.

### EXP-20261004-05: validator v1.1 and D-067 reference comparison

Offline revalidation of saved B, reference and round-two matching outputs used the same D-066 quote and OR rules for every model. Gemini CV2/F00815 and DeepSeek Pro CV1/F00036 became process-valid through punctuation/Markdown normalization. Five remaining invalid round-one outputs are model-output failures, not proven application failures. No paid replay qualified under the additional US$0.30 allowance. [Validator record](../evals/results/cp23_stage2_validator_v11_20261004_v2.json).

D-067 changes the F00815/P52-U10 evidence reference from PARTIAL to MATCH for CV2's BigQuery SQL work evidence, with PostgreSQL treated as an example. The original gold and old metric view are preserved. The evaluation also exempts the example-like requirement from G2 in its new view. All-case guarded Macro-F1 changes from 0.777417 to 0.772296 for DeepSeek Flash and from 0.744424 to 0.730356 for GPT-6 Luna, each on four complete pairs and 73 units. [Old/new result](../evals/results/cp23_sql_reference_comparison_20261004_v2.json); [English A1/A2 report](checkpoint_2/supporting/CP23_Validator_v11_and_A2_Proposal_20261004.md). Actual additional API cost US$0. This is a post-result reference clarification, not a held-out test or a model freeze.

### EXP-20261004-06: strict Gemini mapping and provisional development freeze

The three non-trivial Gemini/F00815 mappings use the same D-054 split/merge rule, D-061 importance rule and D-067 SQL reference as every other model. F00815 has 14 TP, 4 FP and 2 FN; its F1 is 0.823529. Gemini's seven-JD extraction F1 is 0.683128. [Mapping result](../evals/results/cp23_gemini_f00815_alignment_20261004_v1.json). No API call or gold edit occurred.

D-068 selects Hybrid Qwen and DeepSeek Flash for JD extraction and matching for provisional development use. JD prompt v1.4, evidence prompt v1.1, validator v1.1 and G1/G2 are identified. K=20 and PARTIAL weight 0.5 remain hypotheses for Part B. [Versioned configuration](../config/versions/pipeline_cp23_provisional_20261004.yaml), [K20 cost projection](../evals/results/cp23_k20_cost_projection_20261004_v1.json), [main comparison](checkpoint_2/CP2_03_Model_Comparison.md). The legacy config remains unchanged to preserve frozen input hashes. This offline decision cost US$0. The older D-065 pending wording above records its status at that historical point; D-065 is now approved.

### EXP-20261004-07: Part B offline safety and masking quote check

The capped D-068 development run was already active. This check made no API call. The Part B evaluator now withholds a percentage for saved JD units marked `needs_review`, as the one-JD pipeline already does under D-049. Optional filters require an exact configured date, separate UNKNOWN from conflicts and never widen empty results. These are implementation checks, not filter quality measurements.

Local masking of synthetic CV1/CV2 changed 13 of 781 reviewed evidence rows with a nonempty CV quote. The rows repeat two contact-header quotes. Every changed quote has an exact transformed span in the masked CV. [The versioned receipt](../evals/results/cp23_masking_quote_compatibility_20261004_v1.json) stores hashes and identities, not quote text. It does not approve semantic equivalence. Most affected rows concern location or availability, so the open city policy in D-051 still matters. Targeted tests for the changed filter, runner gate, evaluator gate and privacy controls: 28 passed, 0 skipped. The earlier full-suite check before the receipt test was 453 passed, 2 skipped. No database test was repeated.

The offline recommendation assembler now uses existing D-013 ordering to separate matching filters, UNKNOWN filters, explicit constraint conflicts, and held analyses. It refuses to invent a score for a selected candidate with no result. Three focused tests pass. This validates deterministic grouping only; the live Part B run does not yet supply confirmed constraint context or a production UI.

### EXP-20261004-08: capped Part B development run, stopped partial

The D-068 Hybrid Qwen and DeepSeek Flash configuration used saved original top-30 lists for synthetic CV1/CV2, with 52 distinct development JDs and 60 planned pairs. Extraction attempted 51 JDs; F00369 stayed source-held. Thirty-seven extraction objects were process-valid and 14 failed. Only 25 of the 52 JDs passed deterministic score eligibility after incomplete and `needs_review` holds. Matching saved 29 pair records: 16 process-valid, three failed, eight blocked by failed extraction, one by incomplete extraction and one by F00369. Thirty-one pairs were unattempted when the second transport timeout stopped dispatch. No failed stage was replayed. See the [English Part B report](checkpoint_2/supporting/CP23_PartB_Development_Run_20261004.md), [extraction receipt](../evals/results/cp23/end_to_end_dev/cp23_partb_extraction_closure_20261004_v1.json) and [partial run receipt](../evals/results/cp23/end_to_end_dev/cp23_partb_partial_summary_20261004_v1.json).

The D-052 offline evaluation has 18 CV/K/weight cells. Nine CV1 P@5 values are available, but no final-order NDCG@10 and no CV2 final-order value are available. It does not select K, weight or a model. Matching stage wall time for 16 completed outputs has p50 51.830 seconds and p95 125.951 seconds, not one-CV K20 wall time. The 102 ledger entries for this run account for US$0.9906384192 against the US$2 cap, including US$0.0646905 uncertain timeout reservations. Settled or provider-reported cost is US$0.9259479192. Project ledger accounting is US$2.2621552034 including the historical US$0.0210861 uncertain reservation. No paid masked-pair comparison followed the repeated timeouts. Source, gold and workbook outputs were not changed.

Final offline verification after the local filter, grouping, masking receipt, preflight and score-hold changes: `env-job-fit/bin/python -m pytest -q` returned 459 passed, 2 skipped, 0 failed. The [protection receipt](../evals/results/cp23/end_to_end_dev/cp23_partb_protected_check_20261004_v1.json) reports 9/9 frozen plan inputs, 10/10 gold-manifest files and 521/521 historical protected data paths unchanged. No database suite, git command or test-set evaluation ran.

### EXP-20261004-09: Part B resume and complete collection (M10/M11 coverage check)

Dion approved a US$2.50 **total** cap and only the 31 previously unattempted CV/JD pairs. The original two timeout stages were skipped. All 60 planned development pair records are now saved. Process statuses: 35 matching done, six matching failed, 16 blocked by failed extraction, two held extraction and one held source. Only 20 have final numeric scores. No new timeout or new model was introduced. The [amendment](../evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1/cap_and_deadline_amendment_v2.json) preserves the original plan and cutoff; the [completion receipt](../evals/results/cp23/end_to_end_dev/cp23_partb_completion_20261004_v3.json) records exact outputs and costs.

The [D-052 evaluation v2](../evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1_evaluation_v2.json) checks two CVs, K=10/20/30 and PARTIAL weights 0.25/0.5/0.75. None of its 18 final-order cells has all original top-K candidates scored. H4, K and weight therefore remain unconfirmed; the scored-subset diagnostic cannot select a setting. A new evaluator gate prevents an unassessed candidate from being skipped when calculating primary final-order P@5 or NDCG@10. The [coverage figure](../reports/figures/cp2/fig07_partb_coverage_20261004_v1.png) shows this limit without implying that held cases are negative.

Part B accounted US$1.1875181592 in 129 ledger entries, including old uncertain reservations of US$0.0646905. Resume cost was US$0.1968797400. Project ledger total is US$2.4590349434. For 35 completed matching stages, nearest-rank p50 is 35.215 seconds and p95 is 120.212 seconds; full one-CV K20 wall time was not measured. Offline `env-job-fit/bin/python -m pytest -q` returned 462 passed, 2 skipped. [Protected-input hashes](../evals/results/cp23/end_to_end_dev/cp23_partb_protected_check_20261004_v2.json) matched 9/9 frozen plan paths, 10/10 gold files, 487/487 historical data paths and the active workbook. No database suite, test evaluation, paid masking comparison or git command ran. [English interpretation](checkpoint_2/supporting/CP23_PartB_Development_Run_20261004.md).

### EXP-20261004-10: pipeline v1.1 development coverage and bounded follow-up

- **Scope and decision:** D-070/D-071; the same 52 unique Hybrid Qwen development JDs and 60 CV1/CV2 ranked pairs as Part B. F00369 remained source-held, so 51 JDs were attempted. Original v1 records remain intact. The new versioned [plan](../evals/results/cp23/pipeline_v11/plan_v1.json) reran 16 affected JDs and up to 25 affected pairs; a bounded [follow-up](../evals/results/cp23/pipeline_v11/hold_continuation_plan_v2.json) examined three remaining JDs and four associated pairs. F00309 was excluded from paid follow-up because its nine saved units were already extracted and all are preferred.
- **Changes:** dynamic output allowances with one length continuation, 240-second request timeout, four-worker matching, source-section empty-output checks and H2 provisional exclusion of at most 20 percent unresolved required logical units. JD prompt v1.4, evidence prompt v1.1, DeepSeek Flash, guideline v1.3, D-052 metric contract, source and gold stayed fixed.
- **Measured result:** process-valid JD output rose from 37/51 to 48/51 after follow-up. H1 score coverage rose from 20/60 to 26/60. H2 gave 42/60 final or provisional scores, versus 30/60 in the saved-v1 offline counterfactual. The 54/60 target was not met. The follow-up did not raise coverage: F00022 and F00126 remained over the H2 structural threshold, and F00310 failed exact source quote validation. Every one of 36 H1/H2 CV/K/weight final-order cells remains incomplete. K and PARTIAL weight were not selected.
- **Cost and timing:** 57 v1.1 ledger calls accounted US$0.6281001646 against the separate US$3.00 aggregate cap, including US$0.0501633 of uncertain reservation. Project accounting after the run was US$3.087135. The primary mixed-workload run took 2,648 seconds; a clean one-CV K20 end-to-end time was not measured.
- **Quality and checks:** [Final coverage receipt](../evals/results/cp23/pipeline_v11/coverage_summary_v2.json), [D-052 evaluation](../evals/results/cp23/pipeline_v11/evaluation_v2.json), [technical quote audit](../evals/results/cp23/pipeline_v11/technical_qa_v2.json), [semantic spot check](../evals/results/cp23/pipeline_v11/semantic_spot_v1.json), and [English experiment report](checkpoint_2/supporting/CP23_Pipeline_v11_20261004.md). Technical quote audit found no exact-source fault, but the spot check found unsupported/merged meanings. No test inference, real CV, gold edit or configuration promotion occurred.

### EXP-20261004-AUDIT. Offline development re-evaluation after the CP2 audit

- **Scope and decision:** D-072 to D-076, development CV1/CV2 only, saved outputs only, no model call, no gold or source change.
- **Runs:**
  - `scripts/evaluate_cp23_product_order.py`: rescored all 60 saved v1.1 pairs with H1/H2/H2v2 and weights 0.25/0.5/0.75. Saved H1/H2 scores reproduced exactly (0 mismatches; 26 and 42 usable). H2v2 gives 33 usable. Product-order metrics (D-073): stage 1 macro P@5 0.30 and NDCG@10 0.522; H2v2 weight 0.5 K=10 P@5 0.40 and NDCG@10 0.551.
  - `scripts/evaluate_cp23_seniority_rule.py`: D-074 rule on all six methods; Hybrid Qwen P@5 CV1 0.2 to 0.6 and CV2 0.4 to 0.8.
  - `scripts/evaluate_cp23_uncertainty.py`: paired bootstrap for matching models, error direction, pool-bias counts and H7 gap (D-075).
- **Outputs:** `evals/results/cp23/dev_eval_v2_20261004/` (`product_order_v1.json`, `seniority_rule_v1.json`, `uncertainty_v1.json`).
- **Open:** D-076 Luna matching check (paid, cap US$0.40) waits for Dion's local run. Seven relevance labels are missing for some K=20/K=30 and seniority cells (CV1: F00060, F00129; CV2: F00418, F00556, F00629, F00645, F00682).

### EXP-20261004-LUNA. D-076 Luna matching check

- **Version 1:** stopped (route adaptation missing, cap too small for parallel reservations); US$0.1219; records kept in `evals/results/cp23/luna_matching_v1/`.
- **Version 2:** completed on the same 60 development pairs and DeepSeek extractions. 50 of 54 called pairs process-valid, US$0.1043, one-CV K=20 wall time 62.5 s with 20 workers. Usable pairs under H2v2: Luna 36, DeepSeek 33. Comparison: `evals/results/cp23/dev_eval_v2_20261004/luna_comparison_v1.json`.

### EXP-20261004-SWEEP. D-079 matching model sweep and Sol coverage check

- **Stage 1:** ten models on the four gold pairs under one setting (US$1.2822 plus US$0.6305 recovery after the D-081 workspace budget fix). Best: GPT-6 Sol 0.846; Luna 0.736. Run-to-run label agreement for rerun models 0.81 to 0.90. Result: `evals/results/cp23/dev_eval_v2_20261004/model_sweep_stage1_v3.json`.
- **Stage 2:** GPT-6 Sol on the 60 development pairs, US$1.4808, 54 of 54 called pairs valid, 40 of 60 usable under H2v2, one-CV K=20 in 35.4 s with 9 workers. Result: `evals/results/cp23/dev_eval_v2_20261004/sol_comparison_v1.json`.


### EXP-20261004-PREP. Recommendation flow, freeze preparation and realistic PDF fixture (no model call)

- **Recommendation flow:** `src/jobfit/recommend/service.py` runs one CV through the evaluated steps in order: stage-1 top 30, seniority rule, top K, cached extraction, Sol matching (Luna once on a processing failure, model recorded per job), H2v2 score, product order. Retrieval uses `branch_depth = max(K, 20)`, the same rule as the saved development runs. Settings load from the v3 version file. Tests: `tests/test_recommend_service.py` with a fake matcher.
- **Freeze preparation (D-053):** `scripts/prepare_cp23_freeze.py` drafts the freeze receipt (43 file hashes, call settings, pool rule) and lists blockers. Current blockers: K and PARTIAL weight (D-078 after the 46 labels), gold r4 not imported. Note: `config/pipeline_v1.yaml` still names JD prompt v1.2, so the test extraction passes the v1.4 prompt explicitly. `--approve` writes an approved copy only with a decision id and no drift. `src/jobfit/eval/test_pool.py` and `scripts/build_cp23_test_workbook.py` build the top-10 union pool and the blind workbook, and refuse without an approved receipt. Nothing was written to `evals/freeze/` yet.
- **Corpus extraction:** `scripts/run_corpus_extraction.py` (dry run by default). Development reuses 47 evaluated JD records and calls about 167 more; estimate about US$2.2 at 1.5 times the median call (US$0.0086). (Corrected from 48/166: F00310's older success must not replace its newer follow-up record; see EXP-20261004-DEMO.) Test extraction is refused until the freeze is approved.
- **Realistic PDF:** `evals/fixtures/cv1_realistic_pdf_v1/` renders CV1 with capital headings and bullets, no Markdown. Found: the PDF text keeps the "fi" ligature (U+FB01). Quote check v1.1 resolves it through NFKC; G1 finds the plain headings. Tests: `tests/test_cv1_realistic_pdf.py`.
- **Checks:** 545 passed, 2 skipped. `docs/evaluation.md` hash unchanged.

### EXP-20261004-APP. Runtime client, experience block, first API and UI, P7 report (no model call)

- **Runtime client:** `src/jobfit/llm/runtime.py` uses the same request rules as the evaluated Sol run (temperature left out, output limit, dated ids) from the frozen file `config/versions/route_rules_cp23_v1.json`. The timeout comes from the version file (240 s), not the 90 s default.
- **Experience conflict block:** `src/jobfit/matching/experience_rule.py`, rule `experience-upper-bound-v1`. A job gets an explicit conflict only if the whole confirmed CV work history is shorter than a required minimum. It never marks a job as compatible. Not in the config yet; it waits for Dion's decision. Offline check (`scripts/evaluate_cp23_experience_block.py`, result `experience_block_r3_v1.json`): 15 pairs flagged (12 CV1, 3 CV2). All 11 flagged pairs that have a label were rated 1. CV1 NDCG@10 at K=10 with the seniority rule goes from 0.543 to 0.579, P@5 stays the same. Many cells wait for gold r4. CV2 has about 5.4 years of total history, so the rule cannot flag most of its jobs.
- **API and UI (first slice):** `src/jobfit/api/main.py`, `presenter.py` and `wiring.py`, plus `ui/streamlit_app.py`, `ui/api_client.py` and `ui/components.py`. They provide sessions with a token, demo runs for synthetic CV1/CV2 with progress, and groups (matches, conflicts, not fully analyzed). Uploads are masked locally and show a preview. Provider processing of uploaded CVs stays off (D-051), and deleting a session drops late results. Before the freeze the app only searches the 214 development jobs. Tests use a fake run: `tests/test_api.py` and `tests/test_ui_client.py`.
- **P7 report:** `scripts/evaluate_cp23_p7.py`, result `p7_report_r3_v1.json`. H7 (Indonesian vs English) cannot be answered with this data: there is 1 relevant Indonesian JD for CV1 and 0 for CV2, and the two CVs also differ in profile. Wilson 95% intervals for one-CV P@5 are wide (for example 0.2 gives 0.04 to 0.62). Hard negatives in the final top 10: CV1 has 4 (2 ask for 1 to 2 years and are caught by the experience block), and both CVs have F00020, a mentor/trainer post at 50%.
- **Stability script:** `scripts/run_extraction_stability.py` re-extracts 5 gold JDs twice with no cache (estimate US$0.13, cap US$0.50). Dry run only, not executed.
- **Checks:** 564 passed, 2 skipped. `docs/evaluation.md` hash unchanged.

### EXP-20261004-DEMO. Optional filters, saved demo, deploy files and CI (no model call)

- **Optional filters (D-010):** `recommend(..., filtered=...)` takes the filter result. Retrieval runs only on eligible jobs. Jobs that match the filters come first, and jobs with missing filter values come next as a separate block. Each block keeps the product order. Without active filters the order is identical, and a test also checks it against `assemble_recommendations`. If no job fits, the result carries the "did not widen" message. The API and UI offer country, work mode and posting window, plus "also show missing".
- **Saved demo (D-022):** `scripts/build_demo_bundle.py` replays the saved Sol answers through the same `recommend()` code (`src/jobfit/recommend/saved_demo.py`). Output: `evals/demo/saved_demo_v1/bundle.json`, CV1/CV2 with the seniority rule on and off. Checks: 73 replayed scores equal a direct H2v2 rescoring, and all four orders equal the freeze-grid product order (K=20, w 0.5). The key covers the CV file, the v3 config and the route rules, so after any config change (for example D-078) the demo refuses and must be rebuilt. The saved demo is the default in the API and UI and is labeled "Demo with saved results". Filters need a live run.
- **Extraction record rule:** found while building the demo. The newest evaluated record now always wins (`src/jobfit/extraction/saved_records.py`), the same rule as `jd_path`. Before this, the app and the corpus reuse could pick F00310's older success instead of its newer follow-up record. All 52 development jobs now resolve to the same file as the evaluated runs. A first bundle built with the old rule was moved to `evals/demo/archive/saved_demo_v1_used_older_extraction/`.
- **Deploy files:** `Dockerfile.api` (saved demo works without a database or model call; live analysis is off by default, because a fresh container has an empty usage ledger), `Dockerfile.ui`, and api/ui services in `docker-compose.yml`, all bound to 127.0.0.1. The images were not built here (no Docker in the VM). The file set of the API image was checked by running the app from a copy of exactly those paths.
- **CI:** `.github/workflows/tests.yml` runs the offline suite on Python 3.11. Simulated on a copy without git-ignored files: 571 passed, 9 skipped. `tests/test_cp23_retrieval_evaluation.py` now skips when the local query cache is missing.
- **Product note:** in the saved demo the top CV1 match is a "Data Science Trainer" post at 87.5%, and F00020 (mentor) also scores high. Trainer and mentor posts fit the required-skill coverage but not the job seeker's goal. This is a known limit, not fixed here.
- **Checks:** 578 passed, 2 skipped. `docs/evaluation.md` hash unchanged.

### EXP-20261004-POST. Post-labeling command, trainer/mentor check, API privacy tests (no model call)

- **One command after the labels:** `scripts/run_post_labeling.py` checks gold r4 hashes, runs the Sol freeze grid on r4 and applies D-078 through `src/jobfit/eval/d078.py`, a pure function tested on hand-made grids. It then compares the six retrievers plus a Hybrid Qwen + B0 fusion, each with and without the seniority rule, and reruns the experience block and P7. On r3 every D-078 cell is unavailable, as expected. A coverage check with placeholder labels (not saved, values not used) shows that after r4 all D-078 cells and all retriever P@5/NDCG@10 cells are computable, except dense OpenAI with the rule on.
- **Proposed retriever rule (needs Dion's approval before r4 numbers exist):** keep Hybrid Qwen unless a challenger has macro NDCG@10 at least 0.05 higher and macro P@5 not lower, both with the seniority rule on. A switch would need new Sol matching before the freeze.
- **Trainer/mentor posts:** `scripts/evaluate_cp23_trainer_roles.py`, result `trainer_roles_v1.json`. Three development jobs match the title pattern (F00020, F00129, F00514), and the test split has one (title not shown). CP1 classed all three as target role families. F00020 has approved labels of 0 for both CVs (mentoring role, outside the target families), yet in the saved demo it sits at position 9 (CV1) and 8 (CV2). F00129 is in the pending blind workbook, so its label was not read. Too few cases to tune a rule; recorded as a known limit.
- **API privacy tests:** `tests/test_api_privacy.py` maps PR-01 to PR-07 and PR-09 to API-level checks: masking of email, phone and profile (names need reviewed hints, warning shown), no provider run for uploads, session isolation, deletion during work with late results dropped, fake-clock expiry with the sweeper, oversized and malformed uploads rejected, no CV canary in logs or error bodies, and no raw HTML in the UI. Limit: the temp-file check is weak on Linux, where spooled upload files are unlinked at creation. PR-08 and PR-10 need provider calls and are not covered. Synthetic scope only, not a deployed host.
- **Checks:** full suite passes; `docs/evaluation.md` hash unchanged.

### EXP-20261006-R4. Gap labels imported (gold r4) and the freeze candidate (no model call)

- **Import (D-085):** `scripts/import_dev_gap_r4.py` wrote `evals/gold/development_v13_reviewed_20261004_gap_r4/`: 45 new relevance rows, G04 held as unscorable (not 0), 759 gap extraction units for 39 JDs and 826 evidence rows for 42 pairs in their own `gap_v2` files. All quotes were found in their JD or CV text. r3 is unchanged. Labels are model-draft-assisted and accepted by Dion.
- **Post-labeling run:** `scripts/run_post_labeling.py --write`, result `evals/results/cp23/post_labeling_development_v13_reviewed_20261004_gap_r4_v1/summary.json`.
  - D-078 (mechanical): K 10, weight 0.5, seniority rule on. Final order macro P@5 0.70, NDCG@10 0.552.
  - D-084: Hybrid Qwen stays; no challenger reached +0.05 NDCG@10 with P@5 not lower.
  - Experience block at K 10: CV1 NDCG@10 0.483 to 0.515, CV2 unchanged; approved into the freeze (D-086).
  - Stage 1 with the seniority rule already gives P@5 0.70 and NDCG@10 0.550. The LLM order at K 10 is equal, and at K 20 or 30 it is worse (P@5 0.40 and 0.30). Stage 2 adds evidence and gap explanations, not ranking gain, on these two CVs.
- **Config and demo:** `config/versions/pipeline_cp23_freeze_candidate_v4_20261006.yaml`; saved demo rebuilt as `evals/demo/saved_demo_v4/` (38 replayed scores equal direct H2v2 rescoring; CV1 and CV2 top 5 equal the evaluated cell).
- **Freeze draft:** `evals/freeze/cp23_freeze_draft_v1/freeze_receipt.json`, 53 file hashes, no blockers. Not approved yet.
- **CP2.4 runner:** `scripts/run_cp24_test.py` (phases parse, queries, stage1, extraction, matching, pool) refuses to run without an approved freeze receipt.

### EXP-20261006-CP3. API, UI, CV coach, Docker and CI (no model call)

- **API (CP3.1):** all planned endpoints: `/health`, session create, heartbeat and delete, `/demo/cvs` and summary, `/cv/upload`, `/cv/preview` (edit), `/cv/consent`, `/cv/parse` (gated, 403), `/recommendations`, `/tailor` and `/tailor/answer` (CV coach v1, D-036), `/jobs/{job_id}`, `/jobs/paste`, `/analyze`, `/market/skills` and `/market/query`, `/feedback` (categories only). The heartbeat keeps the lease but no longer resets the idle age (privacy-threat-model section 4).
- **CV coach v1:** deterministic, no model. At most three gaps per job, four fixed questions, a bullet built only from the answers. 11 scenario tests: unsupported words 0, every part cites an answer, "not done" gives no bullet.
- **UI (CP3.3):** parsing summary with the location suggestion, filters with the missing-value block, "K candidates analyzed", evidence per requirement, job posting text, paste-a-job, market, suggestions and coach, feedback, saved-demo label, pre-upload notice, editable masked preview with consent, 30-second liveness heartbeat, honest session-expiry message. Untrusted text is escaped before Markdown.
- **Docker and CI (CP3.2):** FAIL-29 and FAIL-30 fixed. CI runs ruff (syntax and undefined names), the offline tests, both image builds and a `/health` smoke check. Simulated CI on a copy without git-ignored files: 615 passed, 9 skipped.
- **End-to-end (CP3.4, local):** `scripts/e2e_check.py` against the API started from exactly the image file set: 27 of 27 checks passed (saved demo for both CVs, coach, suggestions, market, invalid inputs, masking canaries, consent binding, delete). The server log contained no canary. The live part (`--live`, paid) and the deployed host are still to run.
- **Checks:** 622 passed, 2 skipped. `docs/evaluation.md` hash unchanged.

### EXP-20261006-CP24-PARSE. CP2.4 parse phase (held-out run, in progress)

- After the D-087 freeze approval, Dion ran the `parse` phase: CV1 and CV2 reused their development parse, CV3 and CV4 parsed ok, CV5 failed on a provider timeout (FAIL-32). Recovery: archive the failed record with a receipt, then rerun the frozen phase for CV5 only. No test result has been read.

## CP24-LABELS. Test label import test_v13_cp24_r1 (D-088)

- Date: 7 October 2026. Input: `C_Relevance` of `JobFit_Test_Relevance_Final_.xlsx` (68 pairs).
- Provenance: AI-assisted (ChatGPT), human-reviewed by Dion, blind to ranking. Not independent human gold.
- Result: 67 judged, 1 unjudged (T68, CV5). Per CV judged: CV1 14, CV2 13, CV3 14, CV4 12, CV5 14.
- Changes: 1 relevance-label change (T68 2 -> UNJUDGED); 5 text-only corrections (T17, T21, T23, T43, T50); 0 other relevance/score changes.
- Metadata v2 (same day): wording fix only; v1 archived in `evals/gold/archive/test_v13_cp24_r1_metadata_v1/`.
- Metrics: not computed yet; waiting for Dion's review.

## CP24-RESULT and CP25. Held-out evaluation and figures

- Date: 7 October 2026. Evaluator run by Dion; report `evals/results/cp24/heldout_report_v1.json`.
- Headline CV3-CV5: P@5 0.533 -> 0.733 (3/3 CV); NDCG@10 0.805 -> 0.960 (2/3 CV, CV3-CV4; CV5 unavailable, F00070 unjudged).
- Supplementary CV1-CV2: P@5 0.30 -> 0.70; NDCG@10 0.688 -> 0.892.
- Figures 9-11 and tables: notebook `notebooks/02_cp2_heldout_evaluation.ipynb` -> `reports/figures/cp2/fig09-fig11_*_v1.png`, `evals/results/cp24/cp25_tables_v1/`. The saved report reproduces exactly from the labels. An earlier preview run is kept in `reports/figures/cp2/archive/preview_20261007/` and `evals/results/cp24/archive/cp25_tables_v1_preview/`.
- Post-hoc decomposition (diagnostic only): P@5 gain mostly from the seniority rule; NDCG@10 gain mostly from the LLM order.
- No change to freeze, labels, model, prompt, K, metrics or rules.

## QA-E00-BASELINE. Phase A baseline (D-089)

- Date: 7 October 2026. Development only; no call. Command: `python scripts/qa_phase_a.py baseline`.
- Setup: D-087 configuration on saved development artifacts (60 saved Sol pairs, r3 anchor, gold r4 relevance for CV1-CV2).
- Result: P@5 0.70, NDCG@10 0.567, 4/20 held or unscored; 676/676 positive items with exact quotes; anchor macro-F1 0.846, run-to-run 64/73.
- Failure taxonomy (`QA-E00-BASELINE/failures.json`): anchor errors 5 underclaim, 3 adjacent-evidence overclaim, 2 strict soft skill, 1 inferred soft skill; most ranking errors come from holds and job-level fit, not from matching labels.
- Decision: baseline recorded.

## QA Wave 1 (proposed, not run)

- Hypotheses QA-H01 (calibration), QA-H02 (direct evidence), QA-H03 (procedure and stability); prompts `evidence_matching_v1_2_qa_e01..e03.md`.
- Data: QA-DEV-FI-v1 optimization subset (20 pairs, 411 units) and QA-DEV-RANK-v1 (19 matchable pairs). Baseline run twice for noise.
- Dry runs: 177 calls, estimate US$5.16, upper US$7.22, wave cap US$7.50.
- Decision: approved by Dion as a staged wave of 5 runs (R1, R2, E01, E02, E03; 157 calls, estimate US$4.58, upper US$6.40). QA-E03-R is conditional. Confirmation subset sealed.

## QA-E00-FI-R1 and QA-E00-FI-R2. Baseline on the optimization subset, run twice (D-089)

- Date: 7 October 2026. Run by Dion; evaluated offline. Prompt v1.1, GPT-6 Sol, 20 pairs / 411 units each.
- Result: macro-F1 0.7139 / 0.7146; accuracy 0.7518 / 0.7543; unsupported positives 59 / 59; 0 failed pairs, 0 repairs; quote validity 1.0. Cost US$0.504 + US$0.373.
- Repeatability: 382/411 units identical (92.9%); 29 changes, 25 of them one step on the label scale, spread over knowledge areas mostly, CV2 21 / CV1 8; no direction toward gold.
- Interpretation: run-to-run noise is real at unit level but cancels out in the aggregate metrics, so the D-089 floor of 0.02 macro-F1 is the binding bar, not the R1/R2 gap.
- Decision: baseline noise reference. Finalist bars: macro-F1 > 0.7343, unsupported positives <= 59, failed pairs <= 1.
- Run log: before QA-E01 the provider key had about US$0.50 left (Dion's reading: about US$0.87 before R2, R2 used US$0.37); QA-E01 needs up to US$1.61. The runner now reads the key limit (GET /key, no inference) and refuses to start a run the key cannot finish. QA-E01 waits until the limit is raised.

## D-089 amendment 1 (before QA-E01)

- Date: 7 October 2026. Written after the baseline repeat and before any challenger run; no paid call.
- Change: macro-F1 +0.02 is a reference, not a gate; preregistered scorecard with hard gates, path A (quality) and path B (product errors); finalist repeat `<ID>-R2` replaces the fixed QA-E03-R (withdrawn); transient failures get one documented retry or make the run invalid.
- Locked numbers: `evals/results/quality_optimization/selection_rule_v2.json` (sha256 3ab3111a...). Prompts, data, split, taxonomy and metrics unchanged.
- Budget plan: needed US$16.82 in total; recommended key limit US$17.00; margin 1.50 to the 18.50 hard stop.

## QA-E01. QA-H01 MATCH/PARTIAL calibration (prompt v1.2-qa-e01)

- Date: 7 October 2026. Run by Dion, evaluated offline; 38 calls, US$0.99, 0 repairs, 0 failures.
- Result: macro-F1 0.6992 (baseline 0.7143), accuracy 0.7591 (0.7530), unsupported positives 47 (59), overclaims 61 (67-68), underclaims 23 (19-20), quote validity 1.0, ranking P@5 0.70 / NDCG@10 0.553, holds 4/20.
- Scorecard (`analysis/scorecard_QA-E01_v1.json`): all hard gates pass; path A fails (F1 below 0.7343); path B fails (overclaims 61 > 60, F1 below baseline mean). Not eligible.
- Interpretation: the prompt replaced many PARTIAL labels; weak positives on gold NO_MATCH fell (40 to 21) but full MATCH on gold NO_MATCH rose (19 to 26). Fewer but stronger unsupported claims. QA-H01 not supported.
- Decision: not eligible. Adaptive stopping: run QA-E02 next; QA-E03 only on Dion's request. `select` now accepts E01 and E02 with E03 not run (listed as not run).

## D-089 amendment 2 (before QA-E02): staged execution

- Date: 7 October 2026; no paid call. Lock file `evals/results/quality_optimization/amendment2_staged_execution.json`.
- Staged challengers: Stage A fixed-input only (20 pairs), `stage-a-check`, Stage B ranking (19 pairs) only on `continue_to_ranking`. QA-E03 not approved by default.
- Saves the ranking calls (about US$0.53) for any challenger that cannot become a finalist; the decision is the same because path A/B are unit-level.

## QA-E02. QA-H02 direct-evidence check (prompt v1.2-qa-e02), Stage A only

- Date: 7 October 2026. Run by Dion; 20 calls, US$0.50, 0 repairs, 0 failures.
- Result: macro-F1 0.7397, accuracy 0.7859, unsupported positives 37, overclaims 40, underclaims 33, unassessed 15, quote validity 1.0.
- Stage A check: gates pass, path A and B met, no-regression limit fails (underclaims 33 > 25) -> stop; no ranking calls.
- Interpretation: precision/recall trade-off. Most unsupported claims disappear, but some true evidence is lowered (gold MATCH -> PARTIAL 12, gold PARTIAL -> NO_MATCH 17), mainly in knowledge areas.
- Decision: not eligible; future direction QA-H04.

## Phase A close (D-090)

- `select`: no provisional finalist -> KEEP BASELINE. QA-E03, repeats and confirmation not run; confirmation subset still sealed.
- Cost: US$2.38 total for Phase A (101 calls); adaptive stopping avoided about US$3.41 (upper US$4.62).
- Summary file: `evals/results/quality_optimization/analysis/phase_a_conclusion_v1.json`.
