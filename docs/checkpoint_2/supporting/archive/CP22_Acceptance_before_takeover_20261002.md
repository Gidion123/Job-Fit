# CP2.2 acceptance and technical closure — 2 October 2026

Current review aid, not label approval or a replacement workbook. Read this with the latest audit continuation. No active workbook was opened or written by this task. Per the user's coordination note, workbook v1.3 review closure is recorded by the review role under delegation; actual gold export is still absent. F00018 general cloud and AWS are both preferred under “Will be a plus”. F00369's appended tail has unresolved provenance and affected evaluation records remain on hold.

## Eight existing fixtures: human review pending

These are hand-written deterministic fixtures, not eight successful real-model outputs. Source files remain unchanged. Each uses its original reference date **2026-09-29**, preserved rather than silently changed to the runtime development date2026-09-30. Their fragments are not complete CV/JD documents. All eight original expected-result checks pass; the focused scoring module has29passing tests, including quote-preserving deduplication and failure behavior. Semantic compatibility and human acceptance remain separate.

| Existing fixture / purpose | Relevant supplied input | Expected behavior and actual automatic result | v1.3 compatibility / human review question | Human status |
| --- | --- | --- | --- | --- |
| dev_01_clear_match: use versus skill list | Python, SQL, ML development; Docker only in Skills. Internship Feb2025–Apr2026 | D-035: list-only PARTIAL. 3MATCH+1PARTIAL /4 =87.50%, final; experience compatible. Actual matches | No D-049 category/group conflict identified. Confirm scope-grounded internship evidence; duration is a supplied relevant-history assumption, not inferred from title | pending |
| dev_02_experience_too_short: professional minimum | Required3years Python; dated ML employment Aug2025–present | D-042: bounded shortfall explicit_conflict; PARTIAL for experience;83.33%, final mathematical score /3. Actual matches | At fixture date inclusive14months, not3years. Confirm field/activity applicability and display of conflict separately from percentage | pending |
| dev_03_duration_unknown: missing dates | “Personal project: sentiment analysis in Python”, no employment dates;2+years required | PARTIAL+needs_clarification; unknown duration, not explicit conflict.75%, final score /2 with separate unknown constraint. Actual matches | Project is not employment. Empty/unbounded employment input must remain unknown; this fixture cannot establish a project-derived work duration | pending |
| dev_04_or_alternative_group: best OR branch | Python or Java; CS degree or equivalent experience; REST API development. S1 Sistem Informasi evidence | Each OR contributes once: MATCH, PARTIAL, NO_MATCH gives50% /3. Actual matches | **Conflict:** REST API development is a practice/concept, currently skill_tool; propose knowledge_area after review. Related-degree PARTIAL is a supplied assumption, not an approved universal equivalence rule. No source supports an arbitrary years threshold for “equivalent experience” | pending |
| dev_05_repeated_requirement: deduplicate | “Strong SQL skills” and “Experience writing complex SQL queries”; Python; Tableau | Existing normalized SQL duplicates merge; both quotes retained;2MATCH /3 gives66.67%. Actual matches; separate regression checks both quotes | **Qualifier limitation:** decide whether complex-query wording adds a distinct scope before accepting this as a general v1.3 merge example. Do not assume same tool alone justifies merging. Preserve historical expected result until reviewed | pending |
| dev_06_ambiguous_importance: provisional score | “Familiarity with LLM APIs” unknown; “Good communication” unknown; Airflow preferred, but no full heading/local cues | Unknown technical unit excluded provisionally, soft skill excluded under D-032:83.33% /3. Actual matches | **Missing context:** familiarity alone is not an importance softener; D-049 requires genuine ambiguity. Propose making heading/conflict cues explicit in a later reviewed fixture revision. Do not approve extraction importance from these fragments | pending |
| dev_07_no_assessable_requirement: no denominator | “Kaggle experience” preferred; “Passion for AI” unknown | No required technical units: no_score, null%, denominator0. Actual matches | **Missing context:** no preference/ambiguity cues in source fragments. Conditional scoring behavior is valid for supplied labels; fixture does not prove those labels were extracted correctly. Clarify cues before semantic acceptance | pending |
| dev_08_parsing_failure: failed assessment | Python MATCH; PyTorch failed/null; MLOps NO_MATCH | Processing failure stays in3required; on_hold, null%. Actual matches | File name is historical: CV parse status is ok; a required evidence unit failed. Confirm user-facing failure explanation; never convert failure to NO_MATCH | pending |

No new fixtures or approvals were created. Review these same eight cases once (roughly15–25minutes, longer only if the listed ambiguities need discussion). D-049 composite preferred/unknown currently holds the **whole** percentage: this can block an otherwise assessable required subset. Record that consequence for discussion; no rule change is made here. These eight cases do not prove all D-049 model behavior; dedicated v1.3 regression tests from the previous session cover structural hold, not real-model semantics.

## Local retrieval evidence

New runner: `scripts/run_retrieval_comparison.py`; implementation `src/jobfit/eval/retrieval_run.py`. No inference client or embedding fallback. Missing/stale query cache aborts. Sources, skills, profile specs, dimensions, preprocessing and prepared input hashes are checked before ranking. Database transaction is repeatable-read/read-only. Artifact includes vector-content receipts, source/snapshot/split/CV/query/config/code hashes, eligible IDs, filters, K, RRF and tie rules. B0 ties use matched-count then job ID; FTS uses unrounded SQL rank then ID, though displayed scores are rounded; dense uses cosine then ID; RRF uses fused score then ID.

All methods use the same214frozen development target IDs; optional filters are **deferred** because filters.py is a placeholder. The no-optional-filter condition is explicitly recorded, not presented as completed filtered evaluation. Requested top30 requires branch_depth30 in this run, rather than the saved default20. RRF constant60 remains fixed. This mechanical depth extension is recorded; retrieval_v1.yaml and labeling pool remain unchanged. No K/method/model was selected.

| CV | Method | Returned / eligible | Rank-call time ms |
| --- | --- | --- | --- |
| CV1 | B0 | 30 / 214 | 0.36 |
| CV1 | B1 | 30 / 214 | 26.59 |
| CV1 | dense_openai | 30 / 214 | 5.28 |
| CV1 | hybrid_openai | 30 / 214 | 23.25 |
| CV1 | dense_qwen | 30 / 214 | 6.99 |
| CV1 | hybrid_qwen | 30 / 214 | 26.16 |
| CV2 | B0 | 30 / 214 | 0.42 |
| CV2 | B1 | 30 / 214 | 44.56 |
| CV2 | dense_openai | 30 / 214 | 4.14 |
| CV2 | hybrid_openai | 30 / 214 | 48.63 |
| CV2 | dense_qwen | 30 / 214 | 6.63 |
| CV2 | hybrid_qwen | 30 / 214 | 46.79 |

Timing covers each rank invocation (SQL and vector transfer, scoring/sorting), excluding connection, source/cache/tokenizer preparation and serialization. It is a fixed-order local run with cache/order effects, **not a production latency benchmark**. The earlier successful `_02` run and final `_03` run have identical12rankings; the second run verifies completed metadata, not quality. Initial `_01` failed to access the local database inside the sandbox (OperationalError); retry with local-access permission succeeded. No schema/load/update was executed.

Offline runner/pool regression selection:13passed; scoring selection:29passed, reported separately. One intermediate metadata edit had an unmatched parenthesis; its failed collection XML is preserved and the corrected tests pass. Database evidence is the actual12rankings and source/vector checks, not a claim that the whole DB test suite ran. Query caches were reused, with214current vectors checked per embedding profile. No relevance labels, pool edits, quality metrics or winner.

## Proposed v1.3 probe — preflight only

New proposed identity: `cp22_v13_acceptance_probe_after_closure_20261002`. It is separate from the closed v1.2 probe and the interrupted `cp22_v13_verified_review_live_20261002`; neither artifact/run identity is reset or reused. Baseline model and prompts stay fixed. The interrupted run ended with exit130 and has no usable parsed/extracted/matched result; its started field is not success or a running process.

1. Extract development F00034 first. Inspect role alternatives,2year qualifier and portfolio OR against the source, including the prior structural failure. Stop if important semantic uncertainty persists.
2. Only after that check, run CV1 parsing/preview and pasted F00022 extraction. Inspect D-049 and/or composite, local importance/softeners, categories and retained qualifiers. Confirm the parsing preview before matching; automated synthetic confirmation must be labeled as such, never human approval.
3. Match CV1×F00022 only if structure is resolved under existing rules. An honest composite hold is a valid technical finding but stops further paid stages; it is not a failed label or permission to guess grouping.

This is a technical diagnostic plan, **not quality measurement against compatible gold**: no complete v1.3 compatibility/alignment receipt exists yet. The source-backed cases target known failures and D-049; umbrella handling only has coverage if actually present, and no claim that these two JDs exercise every new rule is made. F00369 is excluded. No prompt/model search, new labels or mass extraction.

Maximum8calls (four stages, one repair each), output cap16000 per call. Public F00034 extraction can persist once per exact source/model/prompt/guideline/schema/config identity. Pasted F00022, CV parsing and evidence use session memory; across new user sessions their inference generally recurs. Same-session compatible outputs can be reused; corpus embedding vectors remain reusable. No interrupted response is reusable. Before any future dispatch check for genuinely compatible successful results and lower the estimate where possible; do not automatically pay to replace a stale cache.

Conservative upper bound: **US$0.3362892**, including repair. Proposed aggregate ceiling: **US$0.40** across resume/reservations (not approved/executed here). Ledger is **US$0.212701440**, including **US$0.0210861** uncertain reservation; remaining guard headroom **US$8.287298560**, hard stop US$8.50. The uncertain amount is not a confirmed charge and was not removed. Local registry routing ceilings are used; official availability/prices must be rechecked before a future paid run. No current-price verification or invoice reconciliation is claimed by this preflight.


Parser/matcher use a conditional100000input-token upper bound per attempt (including schema/repair); a future guarded executor must reject a larger actual bound before dispatch. JD bounds use current prompt/source/schema bytes plus repair allowance. Stop before every stage if spent+reservations+next bound exceeds the proposed ceiling or project guard; stop on terminal process failure, quote/identity failure after repair, semantic loss/invention, unresolved structure, or changed baseline/source hashes. The separate staged executor is still needed; do not launch the old closed probe or ungated full-chain command.

The old F00016 stage took226seconds including repair and F00034 took120seconds. Budget several minutes per JD plus manual inspection and parsing/matching; allow roughly10–20minutes operationally, not an SLA. No v1.3 inference was executed by this task; the earlier interrupted attempt must not be reported as a successful v1.3 run.

## Evidence and next handoff

- Final technical rankings: `evals/results/cp22_retrieval_top30_20261002_03.json`.
- Fixture results, exact fixture/source hashes and cost plan: `evals/results/cp22_acceptance_preflight_20261002.json`.
- Targeted JUnit: `cp22_retrieval_final_offline_20261002_02.xml`, `cp22_fixture_acceptance_checks_20261002.xml`.
- Current readiness: `evals/results/cp23_readiness_technical_closure_20261002.json`.

Execution cost this task:US$0; no paid calls, new dependencies, workbook/gold/source/split/pool writes, git, tuning or test evaluation. The review role has stopped shared edits. Next execution ownership: validate approved-only candidate inputs under separately authorized export scope, including F00369 hold, retained rejected decisions, A→B/C dependency receipts and version/group compatibility. Human ownership: eight-fixture acceptance and remaining semantic/metric/scope decisions. Do not ask for a full labeling redo or treat delegated QA as independent human annotation.
