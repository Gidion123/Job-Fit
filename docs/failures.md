# JobFit Failure Log

Failures found during development, evaluation, and testing. Each failure becomes a regression case when possible (Playbook standard S5).

## Entry format

| Field | Content |
| --- | --- |
| Id | `FAIL-NN` |
| Date and stage | For example 3 Oct 2026, CP2.4 |
| Category | Filter miss, stage-1 miss, extraction error, matching error, ordering error, safety, system |
| What happened | Short description with the job id and the synthetic CV id (never real CV text) |
| Why | Root cause, if known |
| Fix or decision | What changed, or why it was kept as a known limitation |
| Regression case | Path of the fixture or test that now covers it |

## Failures

### FAIL-01. v0 experience rule misses "5+ Years as an Engineer"

| Field | Content |
| --- | --- |
| Id | FAIL-01 |
| Date and stage | 29 Sep 2026, CP2.1 (found in the labeling pilot) |
| Category | Extraction error (CP1 rule-based v0) |
| What happened | Job F00114 (pilot J5, "AI Engineer (AI Agent & RAG)") asks for "5+ Years as an Engineer" and "2+ years shipping production LLM features". The CP1 v0 field `experience_bucket` says `not_stated`. |
| Why | `extract_years` in `src/jobfit/jobs/transform.py` only accepts a year mention when a context word (experience, pengalaman, work in, background) is within 80 characters. Neither sentence has one. The rule was built for precision, so it misses short phrasing like this. |
| Fix or decision | Kept as a known limitation. The CP1 snapshot and its numbers stay frozen. CP2 uses the LLM extractor for requirements, and this job is a development check for it: the extractor must return both duration units. |
| Regression case | Planned for CP2.2: pilot J5 (F00114) in the development extraction set. |

### FAIL-02. Phase 0 used the default Python environment

| Field | Content |
| --- | --- |
| Id | FAIL-02 |
| Date and stage | 1 Oct 2026, Phase 0 before T03 verification |
| Category | System setup |
| What happened | `python -m pytest -q` failed collection in tests/test_baselines.py with ModuleNotFoundError for psycopg |
| Why | The shell resolved Python to Anaconda 3.13 instead of the existing project environment |
| Fix or decision | Use `env-job-fit/bin/python`. The offline suite passed 81 tests with 1 skipped; the database-enabled suite passed all 82. No package, code, or environment file was changed |
| Regression case | No new test. Use the project environment for future checks. Evidence: EXP-20261001-03 and `evals/results/t03_split_verification_20261001.json` |


### FAIL-03. Management key authenticated information requests but rejected inference

| Field | Content |
| --- | --- |
| Date and stage | 1 Oct 2026, CP2.2 embedding build and continuation |
| Category | API access configuration |
| What happened | OpenAI embedding first batch returned HTTP 401 `User not found.` in original and resumed builds; one connectivity probe also rejected. GET `/key` succeeded |
| Why | `/key` explicitly reports `is_management_key=true`. Management keys are for administration, not inference; key presence and information-endpoint HTTP 200 were insufficient checks |
| Fix or decision | Add read-only key-type preflight before build inference. Management or unrecognized key type stops without submitting input. Dion must replace the local value with a regular API key; no .env edit or key creation by this task |
| Regression | `tests/test_embeddings.py::test_key_preflight_distinguishes_management_and_inference` (regular, management, missing, invalid type); auth rejection stays zero-charge in the ledger |
| Status | Resolved: Dion replaced the management key with a regular key; the gate passed and EXP-05 completed. Historical auth attempts:three rejections at US$0. No routing/privacy relaxation |
| Evidence | `evals/results/embedding_key_preflight_20261001.json`; `embedding_continuation_audit_20261001.json`; EXP-20261001-04 |

Official reference: [OpenRouter Management API Keys](https://openrouter.ai/docs/guides/overview/auth/management-api-keys).


### FAIL-04. Native response model names rejected by exact router-ID comparison

| Field | Content |
| --- | --- |
| Date and stage | 1 Oct 2026, CP2.2 after regular API key replacement |
| Category | Response validation |
| What happened | A successful 16-input OpenAI response was rejected locally; one-input OpenAI and Qwen diagnostics reproduced the name mismatch. These successful provider calls are billed and remain in the ledger |
| Why | Requests use router IDs (`openai/text-embedding-3-small`, `qwen/qwen3-embedding-8b`), while native responses returned `text-embedding-3-small` and `Qwen/Qwen3-Embedding-8B` respectively. The original check accepted only exact router IDs |
| Fix | Explicit per-model response alias lists in `config/models_v1.yaml`; no general suffix, case, or fuzzy matching. Canonical request IDs remain the storage and ledger identity. Dimension/index/nonzero/finite checks stay in force |
| Regression | Explicit OpenAI alias accepted; similarly named different model rejected; Qwen alias accepted only for Qwen. Covered by `tests/test_embeddings.py` |
| Evidence | Safe one-input metadata probes recorded in `evals/results/embedding_continuation_audit_20261001.json`; original failed run `embedding_regular_key_20261001.json`; full build uses `embedding_validated_aliases_20261001.json` |

The rejected local validation responses were not committed to the cache. Their cost must not be erased or called a free rejection. All later successful batch responses are committed through durable receipts before storage.

### FAIL-05. Structured responses exhausted their output allowance

2 October, CP2.2 CV1/J1. Several responses stopped at 6,000 tokens before a valid result; low reasoning alone did not resolve this. The output allowance is now16,000, low reasoning is explicit, and incomplete finish reasons are rejected with billed costs retained. One repair maximum remains. Tests: test_cp22_contract.py and budget tests; live runs 01/02 preserve failures. This is an operational correction, not a quality win, and increases conservative batch cost.

**4 October v1.1 mitigation:** Later Part B still had 25 failed JD calls at the old 16,000-token allowance; the old ledger did not persist finish reason, so truncation is strongly suspected rather than proven for each call. Pipeline v1.1 uses a measured dynamic allowance and records finish reason. It permits one separate continuation after an explicit length stop. Process-valid JD outputs reached 48/51 after the bounded follow-up, but score coverage reached only 42/60 under H2 and semantic correctness remains unproven. See [EXP-20261004-10](experiments.md) and [the v1.1 report](checkpoint_2/supporting/CP23_Pipeline_v11_20261004.md).

### FAIL-06. Valid JSON omitted source sections

On one CV attempt, education/employment evidence existed but its corresponding sections were missing. Stage validation rejected it. Repair now receives safe validation codes/schema-owned field paths and a bounded prior typed response. Raw exception inputs are not promoted to system instructions. Run 04 successfully retains seven sections and both employment spans. Tests cover source membership and safe feedback. Ledger ok means client-level validation, not semantic correctness.

### FAIL-07. Empty or unresolved extraction despite known requirements

Run 05 returned zero units despite a populated Qualifications and Requirements section. The historical no_score is a quality failure, not evidence of no requirements. The extractor now rejects this conflict, repairs once, then fails if unresolved; responsibilities-only empty results remain supported. Both cases have regression tests.

The original prompt also broadly withheld and/or clauses despite approved D-041. Prompt v1.1 preserves v1 and clarifies existing precedent/AND splitting/schema invariants without changing the guideline. Run 06 has 21 units but still disagrees with approved structured/unstructured importance and architecture/engineering grouping. Its provisional denominator 6 differs from pilot7. This remains a CP2.3 quality limitation; no approved label/scorer was changed to match the output. Equal counts and exact quotes do not establish complete/correct extraction. See the implementation report and runs 04-06.

### FAIL-08. Offline audit found cache, validation and legacy-export risks

2 October, CP2.2 continuation audit. These are reproduced implementation edge cases, not additional production/provider failures:

- An identical caller-supplied cache key could return another memory scope; malformed JSON envelopes could crash. Scope now forms the memory identity; public disk envelopes require explicit scope/value hash and record shape. There were 0 public extraction-cache entries, so no successful paid extraction was invalidated.
- A populated requirement heading without a colon could accept empty extraction. Optional-colon detection now rejects it and preserves the one-repair limit. Responsibilities-only empty extraction remains supported.
- NaN/infinity/negative duration values or budget estimates/CLI approval ceilings could bypass ordinary comparisons; invalid ledger totals could disable the hard-stop comparison. They now fail before inference. No configured budget or valid experience rule changed.
- The historical pilot exporter's write path could replace frozen development IDs with only pilot IDs. It now stops before any workbook read/write if the split manifest exists. The new staging helper cannot write actual gold. No actual split or gold corruption occurred.

Regression evidence: `tests/test_cp22_audit_regressions.py`, `tests/test_review_export.py`, existing pipeline/budget/embedding tests. Final selected offline suite 164 passed. No API cost, workbook write or source/label mutation. A new alignment CLI's first invocation failed on a missing repository import path; corrected locally before artifact creation and successfully rerun. Details: [audit report](checkpoint_2/supporting/CP22_Pipeline_Audit_20261002.md).


### FAIL-09. J4 baseline first extraction response failed validation

2 October 2026, controlled v1.2 probe, F00016. First response raised ValidationError and cost US$0.00664460. Exact invalid field was not saved, so no field-level cause is asserted. The already-authorized single repair succeeded (US$0.00886188), producing21 units. Both calls remain in ledger; this was not first-attempt success. One-repair and protocol caps were preserved. See EXP-20261002-04 and the pilot probe summary. No gold/source mutation.

### FAIL-10. J3 technical success contains important structural uncertainty

Same fixed v1.2 baseline, F00034. Successful16-unit extraction has U02 qualified/no branches where approved J3-U02 uses role alternatives G2 with a two-year minimum; U16 retains needs_review despite the approved portfolio/AI-experience alternative. These differences can change matching/constraint handling and prevent a clean semantic pass. Operational review stopped the protocol before F00073. Cost US$0.00445984 retained; output/cache preserved as technically successful, not semantically approved. Mapping remains a proposal and no F1 is published.

Later D-049 adoption is a separately authorized guideline migration, not a prompt search to erase this failure. The historical v1.2 result remains unchanged; no v1.3 paid rerun has been made. Offline hold/cache/version regressions pass, but do not establish v1.3 model quality.


### FAIL-11. Separate v1.3 vertical-slice run interrupted; cost uncertain

Coordination note from the review role, user-confirmed2October2026: `cp22_v13_verified_review_live_20261002` stopped with exit130/KeyboardInterrupt. Its started artifact contains no usable parse/extraction/evidence result and must not be called success or an active process. One ledger reservation US$0.0210861 is uncertain_upper_bound without requestID, not a confirmed provider charge. Preserve both; reconciliation requires separate evidence. No restart or paid call was made by the technical continuation. Total ledger including reservation US$0.21270144.

### FAIL-12. Technical retrieval setup/verification failures, corrected locally

Initial local DB connection inside sandbox failed with OperationalError; no queries/results were produced. Retained `cp22_retrieval_top30_20261002_01.json`; authorized local-access retry produced12successful rankings. An intermediate B0/B1 metadata edit had an unmatched parenthesis and failed pytest collection (`cp22_retrieval_final_offline_20261002.xml`); fixed before the final13passing selection (`_02.xml`) and final local retrieval. No paid API cost or source/database/workbook mutation. These are technical execution failures, not evidence of model or ranking quality failure.


### FAIL-13. Current v1.3 extraction passes schema but omits qualification bullets

Observed in fixed F00034 closure probe: one education unit from nine qualification bullets. Exact quotes and schema are valid, but source coverage is inadequate; degree alternatives also need shared-qualifier review. Run terminated at semantic gate, cost US$0.007648404. No downstream matching, no current-version live full-chain success. Raw output/protocol receipts preserved.

Mitigation implemented offline: `qualification-bullet-coverage-v1` flags entirely unrepresented explicit qualification bullets for review, reapplies to cached responses, sets incomplete quality, holds score and skips matcher. This is a safety mitigation, not an extraction-quality repair or recall metric. Partial bullet coverage, unrecognized layout and semantic loss still require review. Prompt/model diagnosis remains a versioned CP2.3 task; do not reopen the terminal run.

An initial local-DB verification attempt was denied by sandbox networking. Authorized local-access retry passed5tests; this environmental failure is separate from model semantics.


### FAIL-14. Experimental source coverage did not guarantee semantic structure or evidence completeness

3 October 2026, `cp22_extraction_repair_v13_20261003`. The new inventory recovered all9F00034qualification bullets, but its first 16-unit output weakenedREST API experience and miscategorized named-model branches. One permitted source-review repair corrected these details. F00332 initial 12 units covered8bullets but incorrectly madePython/SQL/Excel OR and left an explicit education OR unresolved. Its one repair produced16 units; all were checked against source. This is a bounded operational fix, not a new global rule or unattended-quality guarantee.

The first complete matching call ignored certificate/thesis partial support for three soft skills. Its remaining repair slot restored PARTIAL with exact quotes; score stayed 72.22 because soft skills are excluded. Two interpretation differences with reviewed goldremain explicit(U15/P30-U08andU16/P30-U15), no silent gold change. No more stage repair is allowed; the checked run is complete. The older one-of-nine failure remainsclosedandunchanged. New versioned artifacts preserve every first and repaired output.

A local sandbox DNS failure occurred in the key-type GET before inference or attempt reservation. Authorized network retry succeeded; no paid failure/reservation resulted. Prior uncertain US$0.0210861from a separate interrupted run remains in the ledger. Links: [experiment](checkpoint_2/supporting/CP22_Extraction_Repair_20261003.md), [source review](../evals/results/cp22_repair_semantic_review_20261003.json).

### FAIL-15. First CP2.3 round-one extraction merged independently assessable JD obligations

3 October 2026, frozen Stage-2 run `cp23_stage2_round1_extraction_20261003_v3`, first and only dispatched case DeepSeek/F00332. The model returned13units in one structurally valid call; all8qualification bullets were mapped and quotes were exact. Source inspection found that U02 merged Python, SQL and Excel (an AND clause) into one requirement, U01 represented the education alternative as a simple unit, and U12 merged large-tabular trend/anomaly work with actionable communication. The reviewed reference has16logical units. Thus the source-coverage inventory is insufficient to certify semantic atomization. No extraction F1 or model ranking was computed; the stage source check failed and the durable batch state is `stopped_semantic_issue` after 1/28cases. No automatic repair was invoked because the structural validator saw no invalid field; the accepted experimental prompt was not modified or promoted.

The single paid call took 394.786seconds and cost US$0.00478664 reported by OpenRouter; the ledger total became US$0.295557024 including the separate historical US$0.0210861 uncertain reservation. An initial sandbox DNS failure during a key-type GET happened before the paid dispatch and created no ledger charge. Source [result](../evals/results/cp23_stage2_round1_extraction_20261003_v3_01.json), [delegated semantic check](../evals/results/cp23_stage2_round1_extraction_20261003_v3_01_semantic_check.json), and [Stage-2 report](checkpoint_2/supporting/CP23_Stage2_Comparison_Preflight_20261003.md). Preserve this run and its unused approved cap as historical; a changed prompt/protocol needs a new versioned plan and appropriate budget approval, not a silent continuation.

### FAIL-16. v1.4 repair improved atomization but left an education alternative incomplete

3 October 2026, separately approved v4 Stage-2 experiment, DeepSeek/F00332. The final 17-unit draft followed one automatic repair and mapped all eight qualification bullets with exact quotes. The previously merged Python/SQL/Excel requirements are independent. However, the source's “other disciplines will be considered” route appears in the group text but not in any assessable branch. `needs_review=true` safely holds downstream scoring; it does not establish semantic completeness. The final draft also splits a reviewed trend/anomaly obligation, requiring D-054 strict split/merge accounting, and has a SQL-analysis category alignment question. Delegated source QA failed coverage/grouping/qualifiers and the frozen batch stopped after 1/28 stages. This is an extraction-quality failure, not a new labeling rule or evidence that another unrun model is better.

Both paid attempts are retained in the ledger: US$0.007094697 and US$0.0150615, total **US$0.022156197**. The final artifact does not separately persist the first typed draft, so only its cost and attempt count can be independently checked. Ledger total after this run: 120 records / US$0.317713221, including a separate historical US$0.0210861 uncertain reservation. See the [v4 result](../evals/results/cp23_stage2_round1_extraction_20261003_v4_01.json), [semantic stop receipt](../evals/results/cp23_stage2_round1_extraction_20261003_v4_01_semantic_check.json), and [Stage-2 report section 7](checkpoint_2/supporting/CP23_Stage2_Comparison_Preflight_20261003.md#7-actual-v14-first-stage-and-source-semantic-stop). The remaining batch cap is not transferable to a changed stop protocol.


### FAIL-17. GPT request parameter compatibility caused a zero-charge Stage-2 stop

3 October 2026, terminal v5 stage `gpt-6-luna/F00332`. The existing client supplied `temperature=0` while requiring all request parameters. OpenRouter rejected the call with `NotFoundError` (HTTP 404 class); ledger records zero tokens/cost as a rejected request. Published metadata still lists the model, but none of its seven endpoints advertises temperature. This is a likely routing rejection explanation, not evidence the model does not exist. The original response body was not retained, so the exact provider error message is unavailable.

Dion approved a separate v6 protocol, retaining old results and counting v5/v6 cost cumulatively under US$3.16. An experimental SDK adapter omits only GPT temperature and recognizes its published dated response ID; privacy/strict schema/price ceilings remain intact. The first adapted request succeeded, showing operational compatibility. GPT now uses provider sampling defaults; this is reported as a comparison limitation rather than silently described as temperature 0. Metadata and approval receipts are linked from D-058. Old v5 state is terminal and untouched by the successor.

Source review has already exposed further semantic issues (over-splitting related obligations and changing a preferred section to required). Process success never becomes source approval or candidate F1 automatically. Every permitted next dispatch waits for a case-specific receipt.


### FAIL-18. Gemini extraction failed its source mapping; repair request rejected

**Fix, 3 October 2026:** repair instruction now uses role `user`; wording and one-repair limit retained. Regression tests: `test_first_and_repair_have_one_leading_system_and_user_repair`, `test_repair_failure_never_dispatches_third_call`, and eight-draft reconstruction test. Historical provider error bodies remain unavailable; no exact original provider diagnosis is invented.

3 October 2026, v6 Gemini/F00815: the typed first draft mapped an AWS quote from introduction/responsibilities to a different qualification inventory item and failed `qualification_inventory_unsupported_mapping`. The one permitted repair was rejected with `BadRequestError` (HTTP 400 class). Initial cost US$0.00927525, rejected repair US$0, two attempts, no final extraction. V6 stopped under its frozen process-failure policy. All outputs/costs remain preserved; a first typed draft is not an accepted extraction. The provider response body was not saved, so no exact rejection cause is asserted. A separate nine-case continuation proposal awaits approval; it neither repeats this failed case nor changes request semantics.

The first test run for the proposed failure-disposition gate failed seven tests due to fake-fixture setup ordering (ledger before state creation), correctly exercising the orphan-receipt guard. Correcting the fixture order yielded73targeted passing tests; the failed XML is retained. No paid request resulted from this local test issue.


### FAIL-19. Round-one matching validation failures followed by rejected repairs

**Fix, 3 October 2026:** repair instruction now uses role `user`; wording and one-repair limit retained. Regression tests: `test_first_and_repair_have_one_leading_system_and_user_repair`, `test_repair_failure_never_dispatches_third_call`, and eight-draft reconstruction test. Historical provider error bodies remain unavailable; no exact original provider diagnosis is invented.

3 October 2026, D-062 fixed-input matching. Gemini failed four pairs and Claude three, each after one permitted repair; all seven repair requests returned HTTP 400-class BadRequestError at zero recorded repair charge. Offline replay of preserved typed drafts shows first triggers: three invalid_source_quote (Gemini), three group_label_must_be_resolved_by_scorer (one Gemini/two Claude), and one generic structured/source validation error (Claude). These are first triggers, not exhaustive diagnoses. Provider error bodies were not saved; the exact rejection cause is unknown. The historical system-message suffix is a compatibility hypothesis only. A separate experimental portable framing adapter is tested but not adopted or used for inference. No failed stage is repeated.

### FAIL-20. Valid quote occurrence does not prove full requirement support

All nine valid matching final outputs pass exact source-quote checks. Delegated full source QA nevertheless finds eight unsupported positives: actionable recommendations, complete SQL/PostgreSQL scope, structured modules, Bedrock from a general AWS course, pipeline orchestration from unrelated MLOps topics, and skills-list-only prompt engineering/Git promoted to MATCH. Five ambiguous interpretations and one label-agrees-with-gold-but-citation-weaker case remain separate. No gold or prediction is corrected to improve F1. D-029 selection remains blocked for the tested round-one configurations; reference/round-two is proposed with separate budget approval. See the current Stage-2 comparison report and semantic QA JSON.


### FAIL-21. DeepSeek Pro retained literal quote failure and semantic overclaims

D-064 completed every original stage; CV1/F00036 matching remained failed after one repair. The first typed response had three exact-quote mismatches and the repair retained two, removing embedded Markdown emphasis from education/internship source strings. This is a source-validation failure, not fabricated education evidence. All17 fixed units stay unassessed in metrics; no manual quote correction or paid replay occurred.

Valid matching results also overstated actionable recommendations and structured modules; two further full-scope flags concern trend/anomaly coverage and SQL/PostgreSQL. Interpretation questions are kept separate. GPT Sol also overstated the accepted SQL/PostgreSQL scope, whose original example-like wording needs explicit adjudication before any reference correction. No model is selected from a higher score alone. Full source QA and request/case diagnostics are in the D-064 evidence artifact and current Stage-2 report.

Portable repair recovered five of six repaired stages in this follow-up, with no new HTTP 400 rejection. That is observed compatibility, not proof of the cause of FAIL-19. The old failed experiments and their costs remain unchanged.


### Repair-framing outcome for FAIL-18 and FAIL-19

Eight repair-only calls under the separate D-064 addendum cost US$0.09795280 against approved cap US$0.65. No new transport rejection. FAIL-18 now has a process-valid extraction with pending new mapping acceptance and real semantic errors. FAIL-19 recovers only Gemini/CV1/F00036; six matching repairs remain application-invalid and not_assessed. Do not retry them again under this approval. [Actual summary](../evals/results/cp23_stage2_repair_rerun_20261004_v1_summary.json).

The first full local suite after the framing fix had 413 passed, one failed, two skipped: a historical probe test incorrectly expected old source hashes to certify changed code. The validator correctly rejected them. The acceptance test now uses a clearly synthetic temporary receipt and separately tests historical rejection. The production validator and historical receipt were not relaxed or changed. Initial and final test artifacts are retained.

### Validator v1.1 follow-up, 4 October 2026

D-066's source-bound normalization recovered Gemini CV2/F00815 and DeepSeek Pro CV1/F00036 without another API call. The other invalid outputs remain invalid. Gemini CV1/F00332 and CV2/F00018 contain added words in quotes. Two Claude outputs identify their source as an annotator even though the model produced them. Claude CV1/F00036 has unresolved OR branches. The new validator does not relax any of those checks. No confirmed application-caused failed stage remains for the additional US$0.30 replay allowance. [Stage record](../evals/results/cp23_stage2_validator_v11_20261004_v2.json).

D-067 clarifies that SQL work in BigQuery supports F00815/P52-U10, where PostgreSQL is an example. The two historical SQL/PostgreSQL unsupported-positive findings in FAIL-20 and FAIL-21 are therefore reference-interpretation errors under the new view. Their historical records are retained. The [old and new comparison](../evals/results/cp23_sql_reference_comparison_20261004_v2.json) applies this change equally to every candidate, while other semantic overclaims remain.

### FAIL-22. Part B development run stopped after repeated matching timeouts

On 4 October 2026, the 52-JD/60-pair development check attempted 51 JD extractions and saved 29 pair records. Fourteen JD extractions failed process validation. Eleven process-valid JD objects still contain units marked `needs_review`; two look incomplete. Exactly 25 of the 52 JDs pass deterministic score eligibility. Process validity is not semantic completeness.

CV1/F00601 and CV1/F00650 matching returned `APITimeoutError`. The runner saved each failure, reserved uncertain upper-bound charges of US$0.0321066 and US$0.0325839, and stopped after each occurrence. The second stop ended paid dispatch. CV1/F00654 separately failed source or structured-output validation after one repair. None of these is converted to NO_MATCH or silently retried. Total Part B accounting is US$0.9906384192, including US$0.0646905 uncertain reservations, versus its US$2 cap. The [partial summary](../evals/results/cp23/end_to_end_dev/cp23_partb_partial_summary_20261004_v1.json) and [report](checkpoint_2/supporting/CP23_PartB_Development_Run_20261004.md) retain the exact case status. The cause of the provider timeouts and final provider charges is unknown. No full K20 latency or final-order NDCG@10 is claimed.

**4 October 2026 continuation:** Dion raised the shared cap to US$2.50 for the 31 unattempted pairs only. All 31 received records. CV1/F00601 and CV1/F00650 were skipped and remain the two timeout failures; no new timeout occurred. Four pairs total now have invalid final matching output: CV1/F00654, CV2/F00645, CV2/F00034 and CV2/F00682. Sixteen pairs were blocked by failed extraction, two by incomplete extraction and one by the F00369 source hold. The final [completion receipt](../evals/results/cp23/end_to_end_dev/cp23_partb_completion_20261004_v3.json) accounts for US$1.1875181592 total Part B cost, including the unchanged US$0.0646905 uncertain reservations. Thirty-five process-valid matching outputs do not establish semantic accuracy. Final-order metrics remain unavailable because every tested top-K contains held or failed analyses. These are latency and coverage findings, not NO_MATCH labels.

**Pipeline v1.1 mitigation:** The timeout was increased to 240 seconds and matching used at most four workers. The previously timed-out CV1/F00601 and CV1/F00650 yielded process-valid results in the new experiment. Their old failures and uncertain reservations remain intact. This is development evidence that the new configuration can complete those cases, not proof of reliable production latency or a complete K20 run. See [the v1.1 report](checkpoint_2/supporting/CP23_Pipeline_v11_20261004.md).

### FAIL-23. Pipeline v1.1 improved process validity but missed score coverage

The same 60 development pairs were rerun only at affected stages under D-070/D-071. Dynamic output sizing, a single length continuation, longer timeout and four-worker matching raised process-valid JD extractions from 37/51 to 48/51 after the bounded follow-up. H2 produced 26 final plus 16 provisional scores, or 42/60, below the 54/60 target. H1 produced 26/60. No complete final-order metric cell exists across 36 D-052 CV/K/weight/H1-or-H2 settings. The technical improvements did not establish a viable full-list recommendation or one-CV K20 end-to-end latency. [Experiment report](checkpoint_2/supporting/CP23_Pipeline_v11_20261004.md) and [final receipt](../evals/results/cp23/pipeline_v11/coverage_summary_v2.json).

The saved F00310 answer contained zero units despite a qualification heading. A new source-section guard rejected that pattern; the follow-up then failed exact source quote validation. F00022 and F00126 remained above the approved 20 percent structural uncertainty threshold. F00309 was not rerun: nine extracted units are all preferred and give no required-score denominator. F00369 remains source-held. None of these conditions was rewritten as a negative CV match. The technical [quote audit](../evals/results/cp23/pipeline_v11/technical_qa_v2.json) found zero exact-source faults among records that passed, while the [semantic spot check](../evals/results/cp23/pipeline_v11/semantic_spot_v1.json) still found an unsupported communication MATCH and a merged Office-suite requirement. These require semantic review or a new versioned plan, not selective score promotion.

### FAIL-24. H2 removed the requirements that decide fit for early-career users

Found in the 4 October audit of pipeline v1.1. Nine of the 16 provisional H2 scores had dropped a work-experience, seniority or education requirement from the denominator, because the model often marks these complex requirements `needs_review`. Example: CV1 (fresh graduate) x F00208 (principal role, "8-10 years of progressive experience") was scored 39.47% provisional. The same code also made two scores provisional when only a preferred unit was flagged.

**Fix:** D-072 H2v2 keeps such pairs on hold and only changes status when a scored required unit is unresolved. Tests: `tests/test_pipeline_v11_policy.py`. Saved v1.1 outputs rescored offline: 33 of 60 usable under H2v2. H2 receipts stay unchanged.

### FAIL-25. G1 skills-list check only worked on Markdown CVs

G1 looked for a Markdown heading such as `## Skills`. Real PDF and DOCX uploads have no `#` marks, and the upload fixtures were rendered from Markdown so their text still contained `#`. G1 would almost never fire on a real CV.

**Fix:** the Skills section and the next section are now also found from plain heading lines with a known section name (English and Indonesian, optional colon). On all five synthetic CVs (526 quote checks) and all 341 saved development assessments the result is identical to the old code. New plain-text tests are in `tests/test_evidence_guardrails.py`. A real non-Markdown PDF fixture is still missing.

### FAIL-26. A closed experiment test failed after a README edit

`test_cp23_stage2_followup.py` rebuilt the live D-064 plan, whose guard hashes `evals/labeling/README.md`. A documentation edit on 4 October turned the full suite red (473 passed, 1 failed). The test now checks the frozen plan that the run used, plus a separate check that every protocol input except README documentation still matches the approved hashes.

### FAIL-27. First Luna matching check rejected every Luna request

D-076 version 1 used the plain client. Luna endpoints do not accept `temperature`, so all 18 Luna requests returned `NotFoundError` (US$0). The failure did not stop the run because `NotFoundError` was not a stop error, and the next DeepSeek phase stopped on `RunCapReached` because 20 parallel calls reserve more conservative upper cost than the US$0.40 cap. Version 2 reuses the approved D-058 route adaptation, adds a one-call canary, treats route errors as stop errors and checks peak reservation against the cap in preflight.

### FAIL-28. 403 read as model access when it was the OpenRouter workspace budget

During the D-079 sweep, Gemini 3.1 Pro (last pair) and then Claude Opus 5.5 returned HTTP 403 within about 0.1 s. Because other models had just worked with the same key, the 403 was first read as a model-specific restriction, the script was changed to skip one model on 403, and D-079 said Opus was unavailable. Dion's direct probe showed the real message: the OpenRouter workspace lifetime budget of US$5.00 was exceeded. The JobFit ledger (US$4.60) could not see it because the workspace budget also counts spending outside JobFit.

**Fix:** D-081. 403 stops the whole run again; an access probe that prints the redacted provider message runs before paid benchmarks; the five blocked pairs are redone in a separate continuation while the v1 failure files stay.


### FAIL-29. The API image could not find its config files

The first `Dockerfile.api` installed JobFit as a package (`pip install .`). The code finds `config/`, `data/` and `evals/` relative to its own folder, so inside `site-packages` every path was wrong and the API stopped at start (`FileNotFoundError: /usr/local/lib/python3.11/config/pipeline_v1.yaml`). My local check had run the code from `src/`, not from the installed copy, so it missed this.

**Fix:** the image runs from `/app/src` through `PYTHONPATH`, the same way as on the Mac. The CI workflow now builds both images and calls `/health`.

### FAIL-30. The API container could not read its own files

After FAIL-29, the API stopped with `PermissionError: /app/src/jobfit/config.py`. Files in the project folder are mode 600 (owner only); `COPY` kept that mode, and the app runs as the non-root user `jobfit`, which could not read them. The UI container showed `Name or service not known` because the API container never started.

**Fix:** both Dockerfiles run `chmod -R a+rX /app` before switching to the non-root user. `docker-compose.yml` now starts the UI only after the API is healthy, both services restart on failure, and the UI shows a clear message with a Retry button instead of a traceback.

### FAIL-31. A closed run's input workbook changed after the run

On 6 Oct 2026 `tests/test_cp23_stage2_followup.py` found that `evals/labeling/JobFit_Development_Labeling_v1.3.xlsx` no longer matched the hash the closed D-064 run recorded. The file time still says 4 Oct, but the folder changed on 6 Oct, so the file was most likely replaced by a copy. Row counts equal the r3 export, and no result after 3 Oct reads this workbook.

**Fix:** receipt `evals/results/cp23/protocol_drift_receipt_20261006_v1.json`; the test pins the new hash for this one file, so any further change still fails. The workbook was not edited. **Resolved 6 Oct:** Dion restored a repaired copy because the earlier file no longer opened in Excel; the current file is the one to use.

### FAIL-32. CP2.4 parse of CV5 timed out, and the frozen runner would not retry it

On 6 Oct 2026 the `parse` phase of `scripts/run_cp24_test.py` (frozen in D-087) parsed CV3 and CV4, then CV5 failed with `cv_parsing: APITimeoutError (1 attempt(s))` after about 312 s. The ledger holds an uncertain upper-bound reservation of US$0.0212 for that call. The runner wrote the failure as `CV5_parse.json` and decides what is left to do only by whether that file exists, so a rerun would have skipped CV5. Dion found this and changed nothing.

**Recovery (no change to frozen files):** `scripts/cp24_archive_failed_parse.py` moves the failed record, byte for byte, to `failed_attempts/CV5_parse_attempt1.json` and writes a receipt with its sha256 and reason. It refuses anything that is not a pure timeout, success records, more than two archived attempts per CV, and a freeze with drift. The unchanged frozen `parse` phase then retries CV5 only, with the same model, prompt, masking and settings; CV3 and CV4 are not called again. No test outcome is read. If the retry fails again, stop and review. Tests: `tests/test_cp24_parse_recovery.py`.

### FAIL-33. Two CP2.4 test extractions failed (one timeout, one schema validation)

The frozen `extraction` phase wrote 26 of 26 records; two are failures.

- **F00206:** `APITimeoutError` after about 244 s, 1 attempt (ledger: uncertain upper-bound reservation US$0.0495). Operational only. Recovery is the same as FAIL-32: `scripts/cp24_archive_failed_parse.py --job F00206` moves the record with a sha256 receipt into `failed_attempts/`, then the unchanged frozen phase retries that job only.
- **F00480:** `schema_validation` with 2 attempts: the first answer failed validation, the one frozen validation repair (`max_validation_repairs: 1`, `validated_call`) also failed (ledger: `jd_extraction` and `jd_extraction_validation_repair`, both `ValidationError`). The retry policy is used up. It is **not** retried. The record stays as it is; `extraction_from_record` returns no extraction with reason `schema_validation`, so in matching the job is an explicit hold ("JD extraction not available: schema_validation") in the "not fully analyzed" block of the product order (D-073). It is never scored as 0 and never replaced by a lower job. It still enters the blind pool if it is in a top 10, and its relevance label is judged from the JD like any other job.

The recovery helper refuses any failure that is not a timeout, so it cannot retry F00480 by mistake. Tests: `tests/test_cp24_parse_recovery.py`.

### FAIL-34. The CP2.4 run cap refused 14 Sol matching calls, so Luna or a hold took over

- **Found:** 7 October 2026, offline, while writing the CP2.4 supplementary metrics (`scripts/cp24_supplementary_offline.py`, `evals/results/cp24/supplementary_v2/summary.json`).
- **What happened:** the frozen runner wraps the client in `CappedClient` with a US$2.50 matching cap. It reserves a conservative upper cost for every in-flight request before sending it. With parallel matching, the reservations reached the cap although the real spend was only US$0.94, so 14 of 44 Sol matching calls were refused locally with `RunCapReached` (no request was sent). The service then tried the Luna fallback: 11 finished with Luna, 2 failed Luna's own validation (`unbounded_required_duration_needs_clarification`) and 1 was refused by the cap again.
- **Effect on CP2.4:** of 50 analyzed jobs, 30 were matched by Sol, 11 by Luna, 3 became holds because of this, and 6 were held before matching (extraction). Three of CV5's five unscored jobs (F00071, F00599, F00651) come from this cap, not from the model or the JD. The headline numbers stay as measured (they describe the system as run, fallback included, contract `cp24-report-contract-v1`), but they are not a pure Sol measurement and the CV5 hold count overstates the product's hold rate.
- **Not a test change:** nothing is rerun or replaced (D-087, D-089). Phase A runs used a separate cap and had no `RunCapReached`.
- **Fix for later runs (not applied to CP2.4):** size the in-flight reservation from observed cost (or lower the concurrency) so a cap guard cannot change which model answers; record any guard refusal as an operational failure, as amendment 1 of D-089 does.

### FAIL-35. Three tests fail in a fresh clone, so CI is red on the CP2 snapshot

- **Found:** 7 October 2026, offline, during the [CP2 closeout audit](checkpoint_2/CP2_Closeout_Audit_20261007.md). GitHub Actions run 37604915026 on commit `8ca6b41` shows the same result: 3 failed, 671 passed, 9 skipped.
- **What happens:** `tests/test_splits.py` (two tests) opens the git-ignored raw snapshot `data/interim/snapshots/CP1_20260926/jsearch_records.jsonl` and has no skip guard when it is missing. `tests/test_qa_phase_a.py::test_budget_plan_stays_below_hard_stop_and_covers_need` reads the budget from the environment; without the git-ignored `.env` the code default hard stop is US$4.5, so the Phase A budget plan is not covered. With the `.env.example` values (19 / 18.5) that test passes.
- **Effect:** none on the CP2 results; the D-087 freeze check still verifies the split hashes, and the Phase A results are saved. But CI is not green on this snapshot, so the earlier note that CI is ready (CP3.2) is wrong for now.
- **Fix (CP3.2, not done yet):** skip the split tests when the raw snapshot is missing, and pass the budget values to the Phase A test or to CI explicitly. No frozen file is involved.
- **CP3 status (7 Oct 2026):** still OPEN on `cp3-development-20261007`. A working fix exists on an old side branch. It will be re-applied cleanly as the first implementation batch (Phase 1, [CP3 execution plan](checkpoint_3/CP3_Execution_Plan.md)), not merged from that branch.
- **Resolved (7 Oct 2026, CP3 Phase 1, commit `33c5584`):**
  - The two split tests skip with the reason "requires git-ignored raw snapshot data/interim/snapshots/CP1_20260926/jsearch_records.jsonl" when that file is absent. They still run unchanged when it exists.
  - The Phase A budget test sets the approved budget (`API_BUDGET_USD=19`, `API_HARD_STOP_USD=18.5`) itself. `.env` loading does not override existing variables, so a local `.env` no longer matters.
  - Only tests changed; no production default or frozen file.
  - Full offline suite: 672 passed, 11 skipped, 0 failed (683 tests).
  - GitHub Actions run [37641393567](https://github.com/Gidion123/Job-Fit/actions/runs/37641393567) succeeded (lint-and-test and docker-build).
- **Status:** RESOLVED.

### FAIL-36. Live matching in the app runs one model call at a time

- **Found:** 7 October 2026, offline code reading during CP3 planning (no run).
- **What happens:** `OpenRouterClient.chat_structured` holds an exclusive file lock (`ledger.exclusive()`, `fcntl.flock`) for the whole network call (`src/jobfit/llm/client.py:110-112`), and `RuntimeClient` does not override it. So the 10 matching workers in `recommend()` (`src/jobfit/recommend/service.py:200`) queue on the lock. The CP2.4 test scripts used `CappedClient` with real parallelism, so the app's live latency is probably closer to the sum of the per-job times than to their maximum.
- **Effect:** impact on wall time not measured yet. It is not claimed to explain the mentor's 95 s figure. No CP2 result changes; CP2.4 ran in parallel through the scripts.
- **Fix (CP3.1, planned):** a non-frozen concurrency-safe app client with budget reservations (D-096, D-097), proven first offline with a fake SDK (serial versus concurrent, identical outputs), then measured live.
- **Status:** OPEN.

### FAIL-37. The upload screen says names are masked, but uploads get no name or address masking

- **Found:** 7 October 2026, offline code reading during CP3 planning.
- **What happens:** `_set_preview` calls `mask_local(raw)` without `reviewed_identifiers` (`src/jobfit/api/main.py:195`), so only emails, phone numbers, ID numbers and profile links are masked. The UI says "Names, emails, phone numbers, profile links and ID numbers are then masked locally" (`ui/streamlit_app.py:251`).
- **Effect:** no data reached a provider, because `/cv/parse` is gated (403). The preview wording, though, is a privacy claim the code does not keep.
- **Fix (CP3.1/CP3.3, planned, P0):** a required name field and an optional address field passed as reviewed identifiers, and UI text that lists exactly what is masked. Canary tests cover it.
- **Status:** OPEN.

### FAIL-38. The budget guard does not protect live runs inside a container

- **Found:** 7 October 2026, offline code reading during CP3 planning.
- **What happens:**
  - `reports/` is in `.dockerignore`, so a fresh container starts with an empty usage ledger.
  - Without `.env`, the code defaults are a US$5 budget and a US$4.5 hard stop (`src/jobfit/config.py:52-53`).
  - `JOBFIT_LIVE_ENABLED` defaults to on in code (`src/jobfit/api/wiring.py:76`); the Docker image sets it to 0.
  - There is no daily cap, no per-run cap and no global limit on live runs across sessions.
- **Effect:** none so far, because live mode is off in the image. A public deployment with live mode on would not be protected.
- **Fix (CP3.1, planned, P0):** fail-closed settings with live off by default, a persistent production ledger on a volume, the US$2/day cap with deterministic phase bounds and persisted reservations, a per-IP ticket and a global live gate (D-096).
- **Progress (7 Oct 2026, CP3 Phase 2A):** partly addressed.
  - Commit `1574e31`: fail-closed production settings. Live mode is now off by default in code. `prod` requires an explicit database URL and tokens. Live in `prod` requires a non-repository ledger and explicit budgets.
  - Commits `9286fd9`, `3f20f55`: deterministic phase bounds over every reachable allowance (corrected 8 Oct). `full_analysis_upper_bound` = US$84.7704449, above the US$2/day cap, so public live is not eligible under D-096 ([CP3.1 report](checkpoint_3/CP3_01_FastAPI_Service.md#results-7-oct-2026-phase-2a)).
  - Commit `aa33f10`: the settings invariants are enforced on every construction, and public-live eligibility fails closed.
  - Still missing (Phase 2B):
    - the ledger volume;
    - wiring the live client to `client_settings()` (it still uses `get_settings()`);
    - daily-cap enforcement with persisted reservations;
    - the per-IP ticket and the global live gate.
- **Status:** OPEN.
