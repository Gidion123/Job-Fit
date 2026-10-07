# CP2.3: System Tuning

**Current status: IN PROGRESS, provisional development freeze D-068 recorded.** Eight historical repair-only calls cost US$0.09795280. Validator v1.1 then recovered one Gemini and one DeepSeek Pro matching stage offline, with no further API call. Other invalid stages remain failures. D-065 approved G1/G2, D-066 amended v1 selection and safety rules, and D-067 clarified the F00815 SQL reference. Dion accepted DeepSeek Flash for extraction and matching in D-068. Qwen is selected by D-044; Hybrid Qwen, K=20 and PARTIAL weight 0.5 are provisional until Part B. CP2.2 stays DONE under D-050.

| Stage | Status | Evidence and next gate |
| --- | --- | --- |
| 1. Prepare evaluation | READY for accepted original scope | D-054; new extraction mappings need separate acceptance |
| 2. LLM and prompt | DeepSeek Flash provisionally selected by Dion under D-068 | [Validator v1.1 and model basis](CP23_Validator_v11_and_A2_Proposal_20261004.md) |
| 3. Retrieval and embedding | Embedding selected by D-044; method/K pending | [Development retrieval](CP23_Stage3_Retrieval_Comparison_20261003.md#8-d-044-rule-applied-for-freeze-preparation) |
| 4. Tuning and errors | G1/G2 approved offline; runtime integration and ordering incomplete | [Gold-input upper bound](CP23_Gold_Input_Upper_Bound_20261004.md); D-065 approved |
| 5. Synthetic privacy | Partial prior implementation; acceptance open | D-051; no public CV release or new privacy work this run |
| 6. Freeze | Provisional development D-068 recorded; Part B confirmation pending | [Decision log](../../decisions.md); [earlier proposal](CP23_Freeze_Proposal_20261004.md) |
| 7. CP2.2 carryover | NOT RUN | D-050 broad extraction waits for selected configuration and budget |
| 8. Final report | Development figures and presentation summary ready; not closed | Part B, privacy and D-050 scope still required |

Actual replay cost is separate from cap and preflight. The A1 validator and reference comparison added US$0. Total ledger remains US$1.2715167842, including historical uncertain US$0.0210861. No new uncertain charge. Historical snapshots moved unchanged to the [progress log](CP23_Progress_Log_20261003.md).

The [pre-freeze receipt](../../../evals/results/cp23_freeze_precheck_20261004_v1.json) records 433 passed, 2 skipped, protected-input hashes, ledger reconciliation and local-link checks. The [repair-framing inventory](../../../evals/results/cp23_prompt_version_inventory_20261004_v2.json) preserves the prior prompt snapshot and the changed message roles. No prompt wording was revised for the replay.

A read-only recomputation exactly reproduced the saved A/B comparison and all 108 gold-input ordering cells. It issued no API requests and did not rewrite either result file.

## 1. Goal of this stage

Choose the configuration with measurements on the development set, not by changing settings without a metric.

## 2. Inputs and prerequisites

- Checkpoint 9 outputs
- Current reviewed development-record gold in `evals/gold/development_v13_reviewed_20261003_stage1_r3`; earlier r2 is historical; source/version/completeness holds and proposed model-to-gold alignments are not automatically resolved by record approval
- Locked test split (not used here)
- Saved twelve comparable no-filter top 30 rankings for CV1/CV2; judgment coverage and optional-filter implementation still limit comparisons

## 3. Planned method

1. Compare B0, B1, dense and hybrid with both approved embedding candidates on comparable development scope. D-044 option A is approved: silver is exploratory only; every configuration choice must be confirmed with reviewed development gold (D-045). Report labeled-pool Recall@K and judgment coverage; do not treat unjudged items as0.
2. Choose K for stage 2 from 10, 20, 30 by recall, latency, and cost.
3. Compare explicitly versioned extraction prompts only within a human-verified compatible guideline/gold scope. The measured round-one extraction prompt is JD v1.4 under guideline v1.3; the earlier active JD v1.2 remains a historical baseline until a freeze decision.
4. Compare the completed round-one run on seven extraction JDs and four evidence pairs with the separately approved D-064 reference and round-two run. The reference uses four extraction JDs and the same four evidence pairs. Apply D-029 as amended by D-066, only on comparable accepted scopes. Report the safety rate rather than using the old zero gate as a freeze blocker. No LLM is selected yet.
5. Audit the PARTIAL weight (0.5) against the relevance labels.
6. Build the recommendation list end to end: filters, filter status, UNKNOWN option, ordering rules, statuses for not analyzed and failed jobs.
7. Keep labeling the test set (Dion).
8. After configuration evaluation, plan and execute only separately authorized, quality-gated development extraction batches using the chosen explicit configuration and compatible accepted cache entries. Record each eligible JD as accepted, failed, held, or not attempted, with reason and cost. Preserve D-050's unexecuted broad-extraction obligation; do not silently lower the target, raise the budget guard, or process held-out JDs before freeze.

## 4. Planned outputs

- experiment table in docs/experiments.md with config snapshots
- quality vs latency vs cost table
- working recommendation list (script or endpoint)
- this stage report

## 5. Acceptance criteria

- Every change has a before/after on the development set, and the keep/remove decision is written.
- The test set is not used for tuning.
- Spend stays within the budget guard.
- The chosen stage-1 method, K, prompt, and model are recorded in docs/decisions.md, with D-029 and its explicit D-066 v1 amendment both identified.
- D-050 carryover has a verified per-job development extraction inventory and an executed or explicitly approved revised scope/budget disposition; an estimate or partial probe is not the full batch. Any unresolved item remains visible in the stage conclusion.

## 6. Evidence to keep

- docs/experiments.md entries
- config snapshots
- ledger totals

## 7. Estimate and dependencies

- **Historical estimate:** About 1 working day and under US$2. This is not a current batch authorization. Prepare a scoped estimate with actual gold coverage, repair allowance and the remaining US$8.50 guard before execution.
- **Depends on:** Development labels reviewed; checkpoint 9 pipeline working.

## 8. Fallback if blocked

Use only the approved D-045 fallback when its conditions apply; do not silently reduce review sizes or choose K. Earlier15-case/10-and20-only fallback was a historical plan, not a new authorization. Incomplete comparisons remain provisional and do not establish a winner.

## 9. Checklist

- [ ] Compare B0, B1, dense and hybrid with both approved embedding candidates on comparable development scope. D-044 option A is approved: silver is exploratory only; every configuration choice must be confirmed with reviewed development gold (D-045). Report labeled-pool Recall@K and judgment coverage; do not treat unjudged items as0.
- [ ] Choose K for stage 2 from 10, 20, 30 by recall, latency, and cost.
- [ ] Compare explicitly versioned extraction prompts only within a human-verified compatible guideline/gold scope; experimental JD v1.4 is measured, while active JD v1.2 remains unchanged until freeze.
- [ ] LLM comparison round1 (D-029) on the approved D-045 development subsets (7extraction JDs,4evidence pairs; relevance 50 for ranking): `deepseek-flash`, GPT-6 Luna, Gemini 3.5 Flash-Lite, Claude Haiku 4.5, all through OpenRouter, with GPT-6 Sol on at most 10 hard cases as the quality reference. Choose with the fixed selection rule. Round 2 only if the rule asks for it.
- [ ] Audit the PARTIAL weight (0.5) against the relevance labels.
- [ ] Build the recommendation list end to end: filters, filter status, UNKNOWN option, ordering rules, statuses for not analyzed and failed jobs.
- [ ] Keep labeling the test set (Dion).
- [ ] Acceptance: Every change has a before/after on the development set, and the keep/remove decision is written.
- [ ] Acceptance: The test set is not used for tuning.
- [ ] Acceptance: Spend stays within the budget guard.
- [ ] Acceptance: The chosen stage-1 method, K, prompt, and model are recorded in docs/decisions.md, with D-029 and its D-066 v1 amendment both identified.
- [ ] D-050 carryover: quality-gated, versioned development extraction has per-job execution status and a documented executed scope; resolve any remaining target/budget gap explicitly before claiming the carried outcome complete.

- [ ] D-051: implement/test synthetic masking, consent and session primitives, report paired quality impact, and hand off public security gates (section 13A).

## 10. Results

[Stage 2 history](CP23_Stage2_LLM_Comparison_20261003.md#10-repair-framing-fix-and-rerun-4-october) contains original A, bug-fixed B and guardrail comparisons before D-066/D-067. The [current A1/A2 report](CP23_Validator_v11_and_A2_Proposal_20261004.md) applies validator v1.1 and the revised SQL reference to every model. With approved G1/G2, DeepSeek Flash reaches 0.772296 evidence Macro-F1 and GPT Luna 0.730356 over the same 73 units. Both have four valid pairs. New Gemini extraction F1 awaits concrete mapping acceptance. Original metrics are preserved.

[Stage 3](CP23_Stage3_Retrieval_Comparison_20261003.md) selects Qwen by D-044. [Gold-input ordering](CP23_Gold_Input_Upper_Bound_20261004.md) has 0/108 fully scorable cells, with missing IDs retained. It cannot establish an optimal K or PARTIAL weight.

## 11. Interpretation and limitations

Only two development CVs and four matching pairs support these findings. Literal quote validity is not entailment. Validator v1.1 recovers two previously invalid stages across the round-one and reference scopes; remaining model-output failures stay unassessed. Guardrails reduce literal list/scope errors, not all semantic overclaims. B is the approved primary operational comparison under D-066. Missing score inputs prevent complete recommendation-order metrics. Optional filters, synthetic privacy impact and broad extraction remain explicit gaps.

## 12. Decisions from this stage

D-044 selects Qwen using the existing Recall@20 rule; no runtime change or complete configuration freeze follows automatically. D-064 retains its completed reference experiment and adds the separately authorized eight-repair replay with cap raised explicitly from US$0.30 to US$0.65. D-065 guardrails are Pending approval. No safety-gate, gold, label or denominator change is implied.

## 13. Next step

Dion reviews the [freeze proposal](CP23_Freeze_Proposal_20261004.md): primary A/B view, new Gemini extraction mapping, guardrails/safety policy, and incomplete gold-ordering scope. Keep method/K/LLM proposals separate from measured winners. Presentation artifacts follow only after freeze approval. D-050 broad extraction and D-051 privacy acceptance must stay visible; test evaluation is not run in this task.

## 13A. Approved privacy work in CP2.3 (D-051)

The [privacy contract](../../privacy-threat-model.md) is approved as a design, not implemented security. Alongside tuning preparation, implement versioned local full-text masking, exact outgoing-text preview/consent validation, and reusable owner-scoped session lifecycle primitives. Use synthetic CV1/CV2 and fake clocks/provider spies; no real CV or test profile. Verify no transmission before consent, no raw fallback, revoke/expiry behavior and late-result disposal.

Add paired original-synthetic versus masked-synthetic retrieval/matching checks. Keep professional evidence and source dates, verify quotes against masked text, version preprocessing/cache keys and preserve source gold. Use a development-only transformation/alignment receipt; do not overwrite historical labels. Report entity misses/false removals and quality impact separately from model selection. Candidate comparisons must use the same input version; no inference is authorized by this planning update.

API/UI liveness, deployment cleanup, provider-policy enforcement and two-browser isolation are integrated/verified in CP3.1–CP3.4. No claim of immediate deletion on tab closure, complete anonymity or production readiness follows from CP2.3 tests. City/employer/institution handling and measured timing remain open before real uploads.

- [ ] Local masking and consent boundary implemented with synthetic development tests.
- [ ] Owner-scoped session primitives, fake-clock revoke/expiry and late-result tests.
- [ ] Paired masking-impact checks and versioned evidence/quote compatibility receipt.
- [ ] Endpoint-policy feasibility and CP3 security handoff with unresolved choices visible.
- [ ] Results linked to this report and experiments; PR-01–PR-10 status recorded without marking public controls complete.


## 13B. Stage 1: approved evaluation contract (D-052)

[Evaluation contract v1](../../evaluation.md) supersedes the pending numerical suggestions in historical section 14 for the approved items. Relevant=C2/3 for P@5 and labeled-pool Recall@K; NDCG gain is exponential. Primary P@5 uses the original first five positions, never a condensed list; it is unavailable with missing judgments or fewer than five results. Evidence failures stay not_assessed and count as FN for the gold class. Report all three class supports; an absent class in the aggregate comparison set blocks three-class model-selection claims.

Prepare seven complete compatible JD references/four evidence pairs, and audit all valid C plus the six-method original-top10 union. Count additional review needs before changing any workload. No source/gold/pool edits, inference, test access or winner at this step. Implement and test only the evaluator/manifest/readiness changes needed for the contract. Operational receipts and model-assisted corrections are not independent human alignment approval.

- [x] Versioned seven-JD/four-pair candidate manifest and delegated reference/variation audit; future model mappings remain unapproved.
- [x] Deduplicated top 10 label-gap/hold report, with review effort.
- [x] D-052 machine-readable contract plus offline evaluator tests and safe runner integration.
- [x] English preparation report and explicit remaining decisions; formal tuning NOT RUN.

**D-054 closure:** Dion approved the case-scoped F00332 corrections/mappings, six additional C judgments, three direct C-only judgments, and strict split/merge F1. The r3 bundle and v4 readiness replace the pre-decision gate status below. All five Stage-1 prerequisite gates are ready; the original-top-ten union is 70/70 reviewed C. A/B source holds on the three direct C-only pairs persist. This authorizes moving to the Stage-2 development comparison, subject to model/privacy/price/budget preflight and new output alignment. It does not pre-approve any candidate's outputs or create a winner. Targeted offline tests: 78 passed, 0 skipped; no paid comparison yet.

**Follow-up closure audit (3 October):** [Stage-1 report section 5](CP23_Stage1_Evaluation_Preparation_20261003.md#5-stage-1-closure-audit-and-review-boundary) checks the two CV1/F00332 interpretations, proposes but does not adopt a split/merge F1 rule, prepares six source-checked pending C drafts through the annotation workflow, and documents the three original-top10 C holds. Its [technical receipt](../../../evals/results/cp23_stage1_followup_validation_20261003_v1.json) confirms exact source/CV excerpts and 24 unchanged protected inputs. **Stage 1 is still IN PROGRESS for evaluation:** alignment and full judgment coverage await Dion's case decisions/review. Stage 2 paid comparison must not begin from a pending draft or a held record. The seven JD and four fixed-input pair references remain proposed, not an extraction/evidence quality score.

## 14. Historical offline preparation snapshot — 2 October 2026

Formal tuning and model/K selection are **NOT RUN**. Implemented `eval/metrics.py`, `eval/run_eval.py` and the prerequisite CLI `scripts/run_evaluation.py`. Synthetic tests verify manually calculable metrics, coverage, comparability and blocking conditions. No real candidate benchmark, winner, gold export or test evaluation was produced. The original approximately30-case plan (now corrected in the main checklist) was historical; approved D-045 controls current review sizes (7 extraction JDs,4 evidence pairs,50 relevance judgments including pilot).

The CLI writes an exclusive readiness report and exits2 when prerequisites are missing. Pure comparison functions are tested, but actual benchmark orchestration still needs approved inputs/manifests. Whole-JD completeness cannot be inferred from a few approved A rows. Pending/rejected labels are excluded, unjudged jobs are not relevance 0, recall is explicitly limited to the labeled pool, and failed matching remains not_assessed. Proposed unit alignment is not verified alignment. Fake and real artifacts cannot be mixed. Current exported pilot inventory is not the user's latest workbook review state.

### Short decision and review list before publishing metrics

| Item | Source / proposed next action | Impact |
| --- | --- | --- |
| NDCG gain | Evaluation contract names NDCG for 0–3 relevance but does not choose linear relevance or exponential2^relevance−1. Explicitly select one before publication | Changes the relative reward for high relevance |
| Fewer than 5 judged results | Condensed ranking can contain fewer than 5 judgments. Proposed: P@5 undefined with coverage, rather than silently dividing by fewer results; alternative observed-count precision must be named separately | Avoids treating missing judgments as negative or concealing a changed denominator |
| Evidence failures / absent classes | Confirm all-reference false-negative accounting versus an explicitly assessed-only diagnostic; confirm absent-class macro averaging. Always show not_assessed and coverage | Defines denominator and prevents model failures inflating quality |
| Semantic readiness | Verify J1/J3/J4 proposed mappings, affected historical-gold compatibility with D-049, whole-JD completeness, and eight fixtures; do not mass-update versions | Gates extraction/evidence metrics; split/merge cases need reviewed scoring treatment |

No decision is needed now to continue the user's priority review. Once review is ready, reconcile A changes to B/C, inspect approved-only staging under separate export authorization, resolve the small metric/semantic list, then prepare a scoped cost/latency benchmark plan. Do not interpret this preparation as permission to tune, publish F1 on pending mappings, or choose a winning configuration.


## Historical submitted development labels snapshot (2 October 2026)

Human workbook review is submitted. [QA follow-ups](Development_Labeling_Review_20261002.md) precede gold promotion and formal tuning. Do not reopen bulk annotation or treat pending source/metadata/group cases as a benchmark. Configuration choices still require valid development gold under D-044; silver is exploration only. Test remains held out.


## 15. Historical technical readiness snapshot — no formal tuning (2 October 2026)

No-filter retrieval preparation now has12successful top30rankings,214eligible IDs per method/CV, existing embedding/profile/query-cache validation, source/config/input hashes and rank-call latency. New artifact `evals/results/cp22_retrieval_top30_20261002_03.json` preserves older pool/top20 evidence. Run-local RRF branch depth 30 supports top 30; default20 and RRF constant60 are unchanged. No K or model selected. Optional filter behavior is still deferred, explicitly not silently invented. No quality metric was computed.

The [single acceptance/technical summary](CP22_Acceptance_Review_20261002.md) and current top-of-file entry supersede this pre-export snapshot. Formal CP2.3 tuning and test evaluation remain NOT RUN. Evaluation-contract choices and optional-filter comparison are CP2.3 dependencies, not new requirements silently added to CP2.2 completion.

## CP2.3 exit gate for CP2.4 (D-053)

Before held-out processing, approve and freeze configuration **and** test protocol per [evaluation.md section 7](../../evaluation.md#7-held-out-confirmation-protocol-d-053): models, embedding, prompts, preprocessing/masking, K/filters/order/repair, metric and alignment conventions, split hashes and pool construction. The test relevance pool is the union of original top 10 retrieval and top 10 final recommendations per CV, with review counts/effort checked before workbook creation. D-052 development comparison remains unchanged; this is not permission to open test during stage 1. D-050 broad development extraction still needs its own quality/budget plan; D-051 privacy gates still apply. No freeze or test execution is claimed by this update.
