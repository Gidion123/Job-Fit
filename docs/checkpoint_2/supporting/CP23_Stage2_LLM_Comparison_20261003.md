# CP2.3 Stage 2: LLM comparison, quality reference and round two

**Date:** 3 October 2026. **Round one:** measured under D-063. **D-064 follow-up:** all 19 stages completed, evidence measured, new extraction alignment acceptance pending. **Stage-2 model selection:** IN PROGRESS; no configuration is selected. Section 10 is the latest repair and freeze-preparation outcome.

## 1. Purpose and scope

Compare the four D-029 low-cost candidates on the same seven complete development JDs and the same four fixed CV1/CV2–JD evidence pairs. All 28 original extraction cases and 16 matching cases remain in the denominators. Test data, mass extraction, active workbook, gold and runtime defaults were not changed.

Extraction uses experimental JD prompt v1.4 under guideline v1.3. Matching uses evidence prompt v1.1 and reviewed requirement inputs, rather than each candidate’s extraction. This separates matching quality from extraction errors; it does not measure full-chain recommendation quality. CV1 uses its existing checked parse; CV2 is a raw-text matcher fixture, not a CV2 parser benchmark.

## 2. Accepted evaluation rules and provenance

- D-060: the scoped Claude/F00036 two-gold/three-model relation counts 0 TP, 2 FN, 3 FP. Other splits/merges follow D-054.
- D-061: primary extraction equivalence preserves meaning, material qualifiers, AND/OR and importance. Category errors are reported separately. The convention was approved after outputs existed and before primary F1 calculation; it was not pre-registered before inference.
- D-063: Dion accepted the concrete v3 mapping recommendations and fixed adapter. This is human acceptance of assisted source QA, not independent human re-annotation. The receipt binds the proposal and reference hashes.
- Complete extraction reference: 120 logical units per candidate across seven JDs. The failed Gemini/F00815 stage contributes 16 FN; it is not discarded.
- Matching reference: 73 units per candidate, comprising 35 MATCH, 22 PARTIAL and 16 NO_MATCH. Unassessed/failed output contributes FN in its gold class, never an invented NO_MATCH. Macro-F1 uses all three classes.
- Extraction F1 below is micro-aggregated from total TP/FP/FN; it is not a mean of seven case F1 values. Category accuracy is conditional on accepted one-to-one mappings and is not extraction recall.

## 3. Round-one measured results

| Candidate | Extraction TP / FP / FN | Extraction F1 | Category correct / aligned | Matching process-valid | Evidence Macro-F1 | Matching cost, USD |
|---|---|---:|---|---:|---:|---:|
| deepseek-flash | 106 / 20 / 14 | 0.861789 | 105 / 112 | 4/4 | 0.760806 | 0.040561914 |
| gpt-6-luna | 100 / 32 / 20 | 0.793651 | 102 / 114 | 4/4 | 0.744424 | 0.007206285 |
| gemini-3.5-flash-lite | 69 / 36 / 51 | 0.613333 | 75 / 82 | 0/4 | 0.000000 | 0.028526630 |
| claude-haiku-4.5 | 65 / 55 / 55 | 0.541667 | 74 / 86 | 1/4 | 0.186681 | 0.080392000 |

DeepSeek has the highest measured round-one extraction and matching F1 on this accepted small scope. GPT has lower matching cost, but its extraction F1 is more than 0.03 below DeepSeek, so the D-029 price tie rule cannot by itself choose GPT. Neither observation bypasses the safety gate.

Gemini’s zero evidence Macro-F1 reflects four unassessed process failures under this exact protocol. Claude’s value includes three unassessed pairs. These are protocol-level results, not proof that either model family is incapable of matching. Exact quote checks on nine accepted final outputs passed, but quote occurrence alone does not demonstrate entailment.

### Matching confusion matrices

Columns are predicted MATCH, PARTIAL, NO_MATCH and not_assessed. Rows retain the reviewed class.

#### deepseek-flash

| Gold | MATCH | PARTIAL | NO_MATCH | not_assessed |
|---|---:|---:|---:|---:|
| MATCH | 30 | 2 | 3 | 0 |
| PARTIAL | 7 | 11 | 4 | 0 |
| NO_MATCH | 0 | 0 | 16 | 0 |

#### gpt-6-luna

| Gold | MATCH | PARTIAL | NO_MATCH | not_assessed |
|---|---:|---:|---:|---:|
| MATCH | 25 | 6 | 4 | 0 |
| PARTIAL | 1 | 16 | 5 | 0 |
| NO_MATCH | 0 | 2 | 14 | 0 |

#### gemini-3.5-flash-lite

| Gold | MATCH | PARTIAL | NO_MATCH | not_assessed |
|---|---:|---:|---:|---:|
| MATCH | 0 | 0 | 0 | 35 |
| PARTIAL | 0 | 0 | 0 | 22 |
| NO_MATCH | 0 | 0 | 0 | 16 |

#### claude-haiku-4.5

| Gold | MATCH | PARTIAL | NO_MATCH | not_assessed |
|---|---:|---:|---:|---:|
| MATCH | 5 | 2 | 0 | 28 |
| PARTIAL | 3 | 3 | 2 | 14 |
| NO_MATCH | 0 | 0 | 1 | 15 |

## 4. Process diagnosis and source-entailment review

All sixteen typed first drafts were replayed offline through the unchanged validator. Nine passed and seven failed; the first observed validation triggers are recorded below. Offline replay performed no repair inference. Every valid final unit was examined against the fixed requirement, complete CV and quoted evidence: 162 logical-unit results, including alternative branches.

| Failed pair | First observed validator trigger | Final repair outcome |
|---|---|---|
| gemini-3.5-flash-lite/CV1/F00332 | invalid_source_quote | HTTP 400-class BadRequestError; no valid final assessment |
| gemini-3.5-flash-lite/CV1/F00036 | group_label_must_be_resolved_by_scorer | HTTP 400-class BadRequestError; no valid final assessment |
| gemini-3.5-flash-lite/CV2/F00815 | invalid_source_quote | HTTP 400-class BadRequestError; no valid final assessment |
| gemini-3.5-flash-lite/CV2/F00018 | invalid_source_quote | HTTP 400-class BadRequestError; no valid final assessment |
| claude-haiku-4.5/CV1/F00332 | group_label_must_be_resolved_by_scorer | HTTP 400-class BadRequestError; no valid final assessment |
| claude-haiku-4.5/CV1/F00036 | group_label_must_be_resolved_by_scorer | HTTP 400-class BadRequestError; no valid final assessment |
| claude-haiku-4.5/CV2/F00018 | invalid_structured_output_or_source | HTTP 400-class BadRequestError; no valid final assessment |

Provider response bodies were not retained. The exact reason for the HTTP 400 repair rejections is therefore unknown. The historical message sequence ends with a system repair message; a portable framing adapter has been prepared and locally tested as an experimental compatibility mitigation. It is not adopted into the active client, and no old failure is rerun or relabeled as a success.

### Confirmed positive claims exceeding their quoted evidence

| Candidate / pair / unit | Finding |
|---|---|
| deepseek-flash/CV1/F00332 / P30-U15 | Cohort presentation/dashboard and teaching do not state actionable recommendations. Full MATCH exceeds the quoted scope. |
| deepseek-flash/CV2/F00815 / P52-U10 | BigQuery SQL is used, but PostgreSQL occurs only in the skills list. Full SQL/PostgreSQL MATCH is not supported for the entire fixed obligation. |
| deepseek-flash/CV2/F00018 / P04-U12 | API/container work and report scripts do not explicitly show structured modules. Full MATCH exceeds the quoted scope. |
| gpt-6-luna/CV2/F00018 / P04-U06 | An AWS Cloud Practitioner course is not evidence of the named Bedrock service. Vendor overlap cannot create PARTIAL for an unmentioned service. |
| gpt-6-luna/CV2/F00018 / P04-U21 | Docker/FastAPI bootcamp topics do not mention ML pipeline orchestration. Related MLOps vocabulary is not evidence of this distinct requirement. |
| claude-haiku-4.5/CV2/F00815 / P52-U04 | Prompt engineering is only in the skills list in the cited evidence; MATCH conflicts with D-035/B1. |
| claude-haiku-4.5/CV2/F00815 / P52-U10 | BigQuery SQL plus PostgreSQL in a skills list does not support full SQL/PostgreSQL MATCH. |
| claude-haiku-4.5/CV2/F00815 / P52-U13 | Git is only in the quoted skills list; MATCH conflicts with D-035/B1. |

Eight confirmed unsupported positives are distinct from five interpretation questions and one insufficient-cited-context finding. Soft-trait inference and language-level equivalence remain explicit questions rather than automatic gold corrections. Even a label agreeing with gold can have weak citations; the QA packet records that separately. All model predictions and gold labels remain unchanged.

**Safety conclusion:** the tested DeepSeek, GPT and Claude configurations have confirmed unsupported positives; Gemini has no valid final matching coverage and invalid first-draft quotes. No round-one tested configuration qualifies for automatic selection under D-029. This conclusion applies to the tested versions and process, not permanently to a provider family.

## 5. Costs and timing

| Candidate | Matching API attempts | Rejected repairs | Request p50, ms | Request p95, ms |
|---|---:|---:|---:|---:|
| deepseek-flash | 4 | 0 | 28687 | 90747 |
| gpt-6-luna | 4 | 0 | 21559 | 21880 |
| gemini-3.5-flash-lite | 8 | 4 | 592 | 6165 |
| claude-haiku-4.5 | 7 | 3 | 8647 | 12619 |

Nearest-rank request percentiles include billed first attempts and zero-cost rejected repairs. In particular, Gemini’s low request median is dominated by quick rejections; it is not evidence of faster successful analysis. Per-case total wall times are separately retained in the JSON. These samples are not a production latency benchmark.

The D-062 matching experiment used **23 API attempts for 16 stages**, costing **US$0.156686829**, below its US$1.85 ceiling. Original round-one extraction collection cost US$0.3159018938, so the extraction-plus-matching comparison cost is US$0.4725887228. Project ledger at this closure is **US$0.7681457468**, including the historical unresolved US$0.0210861 reservation. The reservation is not silently released. Project hard stop remains US$8.50.

## 6. Verification and limits

- Sixteen targeted offline tests passed, zero skipped, for receipt binding, fixed-reference coverage/failure accounting, accepted alignment inventories, D-060 scope and proposed repair framing. No database suite was repeated.
- Protected source, workbook, gold, CV, split, pool and runtime configuration/prompt hashes are checked separately. No git or new dependency was used.
- Only two development CVs and four evidence pairs support these numbers. They do not establish population-level precision or statistical significance.
- Development labels were draft-first and approved by one annotator; candidate alignments were accepted assisted QA. No inter-annotator agreement or blind candidate audit is claimed.
- Reference GPT-6 Sol, round two and prompt adoption remain outstanding. No test set, final model/embedding/K choice, privacy release or broad extraction is authorized by this result.

## 7. Historical follow-up proposal before D-064 approval

D-029 calls for a quality reference and a second round when no low-cost configuration passes. A fresh, zero-inference proposal is prepared: eight GPT-6 Sol reference stages (four common-JD extractions and four fixed matching pairs) and eleven DeepSeek Pro stages (seven original extractions plus four fixed pairs), with at most one repair each. Reference extraction is compared only on its four-JD, 73-unit common scope; round-one full-seven-JD metrics remain separate.

The proposed aggregate additional bound is US$6.33582444, with ceiling US$6.40. This is a conservative maximum using UTF-8 byte upper bounds and full 16k response allowances, not a forecast of actual charges. It is a separate proposal: D-062 does not cover it. Its portable repair framing and GPT Sol temperature adaptation require an explicit protocol decision; exact provider metadata is saved. No executor, approval or paid follow-up is claimed at this point.

Stage 2 remains IN PROGRESS until the approved follow-up has measured quality/safety and any candidate mappings are accepted, or Dion explicitly revises its reference/selection scope. Later tuning and configuration freeze remain paused. A benchmark with failure findings is complete evidence; it is not a reason to select an unsafe winner.

## 8. Reproducibility and artifacts

- [Accepted metric JSON](../../../evals/results/cp23_stage2_round1_quality_evaluation_20261003_v1.json)
- [Full matching source/semantic QA](../../../evals/results/cp23_stage2_matching_semantic_QA_20261003_v1.json)
- [D-063 acceptance receipt](../../../evals/results/cp23_stage2_alignment_and_fixed_adapter_approval_20261003_v1.json)
- [Matching plan](../../../evals/results/cp23_stage2_fixed_matching_20261003_v1_plan.json)
- [Follow-up proposal, no inference](../../../evals/results/cp23_stage2_reference_round2_proposal_20261003_v1.json)
- [Official public follow-up provider metadata](../../../evals/results/cp23_stage2_followup_provider_preflight_20261003_v1.json)
- [Targeted test XML](../../../evals/results/cp23_stage2_round1_quality_tests_20261003_v1.xml)

Reproduce offline with the existing source and accepted receipt, using a new output path:

```bash
env-job-fit/bin/python scripts/evaluate_cp23_stage2_round1.py --output /tmp/jobfit_stage2_round1_recheck.json
env-job-fit/bin/python scripts/audit_cp23_stage2_matching.py --output /tmp/jobfit_stage2_matching_QA_recheck.json
```

Official request format reference: [OpenRouter chat API](https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion). Endpoint metadata URLs are saved in the preflight. The official message schema does not by itself diagnose the historical rejection.


### D-064 execution update

Dion subsequently approved the exact new protocol and additional US$6.40 ceiling. The approved v2 proposal binds the actual experimental prompt and all 72 protected inputs; scope/cost are unchanged from v1. A frozen executor, exact approval receipt and eleven passing local guard tests are now present. Reference execution has started in a separate durable state. This update supersedes the pending-authorization/executor statement in section 7; measured follow-up quality and accepted new mappings remain pending. No active default or historical prediction was changed.


## 9. D-064 measured follow-up and current closure boundary

The approved follow-up completed all **19 original stages in 25 API calls**, below the 38-call maximum. GPT-6 Sol completed four extraction and four matching stages. DeepSeek Pro completed seven extraction stages and three matching stages; CV1/F00036 matching failed after its one permitted repair. All original failures and first typed attempts remain preserved. No stage was replayed.

The experimental repair adapter preserved the first-call rubric, source inputs, schema and privacy controls. Six repairs were attempted: five recovered a process-valid final result and one remained invalid at application source validation. No new HTTP 400 rejection was observed. This demonstrates compatibility for these requests; it does not identify the cause of historical Gemini/Claude repair rejections. Comparisons therefore concern measured model/protocol combinations, not model capability isolated from request handling.

### Fixed-input evidence results

Both models use the D-063 accepted adapter: **73 units across the same four pairs**, with support 35 MATCH / 22 PARTIAL / 16 NO_MATCH. The failed DeepSeek pair contributes 17 unassessed units (10 MATCH, 3 PARTIAL, 4 NO_MATCH) as gold-class false negatives. It is not dropped or changed to NO_MATCH.

| Configuration | Process-valid pairs | Assessed / all units | Evidence Macro-F1 | Matching API calls | Matching cost, USD |
|---|---:|---:|---:|---:|---:|
| GPT-6 Sol reference / portable repair | 4/4 | 73/73 | 0.818094 | 5 | 0.1675217000 |
| DeepSeek Pro / portable repair | 3/4 | 56/73 | 0.496283 | 6 | 0.0167404530 |

Confusion rows are gold; columns are predicted MATCH, PARTIAL, NO_MATCH, not_assessed:

| Configuration | Gold MATCH | Gold PARTIAL | Gold NO_MATCH |
|---|---|---|---|
| GPT-6 Sol | 31 / 3 / 1 / 0 | 2 / 15 / 5 / 0 | 0 / 1 / 15 / 0 |
| DeepSeek Pro | 21 / 0 / 4 / 10 | 6 / 3 / 10 / 3 | 0 / 0 / 12 / 4 |

These are fixed-requirement evidence results, not full-chain recommendation quality. The reference is about 0.0573 above the strongest round-one evidence result, DeepSeek Flash 0.760806, on the same reference labels. That difference is descriptive on a small development set, not statistical significance or approval of a model.

### Source QA and remaining safety issues

All **129 logical assessments** in the seven valid final matching outputs were checked against the full CV and fixed requirement, including alternative branches. Every final quoted substring was valid. All eleven typed matching attempts were replayed offline against the current application validator.

- DeepSeek Pro incorrectly promoted cohort presentation to actionable recommendations and API/container work to well-structured software modules. These are confirmed unsupported positives even apart from reference ambiguities.
- DeepSeek Pro also marked the full reviewed trend/anomaly obligation MATCH without anomaly-detection evidence.
- GPT Sol and DeepSeek Pro marked SQL/PostgreSQL MATCH using BigQuery SQL work. This exceeds the accepted fixed obligation, but the original JD's example-like wording is a genuine reference-interpretation limitation. Preserve the current label and document this limitation; any correction requires explicit adjudication and a new reference version applied consistently to every candidate. Do not silently change gold to let a model pass.
- Professional-working-proficiency versus strong-upper-intermediate English remains an interpretation question for both models. Teamwork/project ownership also have explicitly separated interpretation questions. A gold disagreement is not automatically an invented claim.
- DeepSeek Pro's failed CV1/F00036 quotes removed Markdown emphasis embedded within the exact CV substrings. The first draft had three invalid quote occurrences and the repaired draft still had two. This is a literal-source validation failure, not proof the underlying degree or internship was fabricated.

The reference is not ground truth. No tested candidate is promoted to runtime. The round-two candidate fails D-029's unsupported-claim gate; the reference has a fixed-scope conflict and unresolved interpretation questions. The earlier round-one safety failures remain. A subsequent matching-prompt experiment is a reasonable next proposal, but it needs its own versioned scope rather than spending an unused D-064 allowance on additional cases.

### Extraction alignment and fair comparison scope

The complete [new alignment review](CP23_Stage2_Followup_Alignment_Review_20261003_v1.md) covers **11 final extraction drafts and 188 relations**: 175 one-to-one, four splits, five merges, three additions and one omission. Every gold/model identity is accounted for once. GPT Sol has 73 gold / 78 model units over four JDs; DeepSeek Pro has 120 gold / 117 model units over seven JDs.

Source findings include AND obligations changed to OR choices, omitted similar-tool routes, unresolved Spark/Dask structure, lost time-series qualification, a missing AWS preference, and splits/merges against the fixed reviewed inventory. All extracted source quotes occur exactly in the original JD. Category mismatches remain a separate measure under D-061. Source-supported opening statements absent from the fixed gold inventory are false positives against that inventory; this does not automatically mean fabrication.

D-054/D-064 still require acceptance of these concrete new mappings before formal extraction F1 is published. D-063 accepted the earlier packet, not these new outputs. The receipt-gated evaluator is ready to produce a seven-JD table for comparable candidates and a separate common-four-JD table including the reference. Neither table may drop the original failed Gemini case. Acceptance is requested as assisted QA, not independent reannotation.

### Cost and timing

| Configuration | Extraction cost, USD | Matching cost, USD | Total D-064 cost, USD |
|---|---:|---:|---:|
| GPT-6 Sol | 0.1501824000 | 0.1675217000 | 0.3177041000 |
| DeepSeek Pro | 0.0709736844 | 0.0167404530 | 0.0877141374 |
| Total | 0.2211560844 | 0.1842621530 | **0.4054182374** |

Project ledger accounting is **US$1.1735639842**, including the preserved historical uncertain **US$0.0210861**. D-064 has no unresolved reservation. The additional US$6.40 cap and project US$8.50 hard stop were respected. Maximum allowance is not actual spend.

Matching request p50/p95: GPT Sol 15,737/16,134 ms (five attempts), DeepSeek Pro 122,388/140,562 ms (six attempts). Total matching-stage wall times include repairs: GPT Sol 11.688–29.045 s; DeepSeek Pro 122.956–246.838 s, including its failed stage. These are sequential development observations, not production latency estimates or a repeated-load benchmark. DeepSeek Pro's lower measured price did not yield better evidence quality or faster completion here.

### Reproducibility and prompt preservation

- [Follow-up evidence metrics and complete matching QA](../../../evals/results/cp23_stage2_followup_matching_evaluation_20261003_v1.json)
- [New extraction mapping packet](../../../evals/results/cp23_stage2_followup_alignment_review_20261003_v1.json)
- [Frozen execution plan](../../../evals/results/cp23_stage2_reference_round2_20261003_v1_plan.json) and [D-064 approval](../../../evals/results/cp23_stage2_reference_round2_20261003_v1_approval.json)
- [Prompt version index](../../../prompts/README.md) and [content/hash inventory](../../../evals/results/cp23_prompt_version_inventory_20261003_v1.json)

Dion reiterated that every prompt version used in a comparison must be saved. Historical prompt files remain intact; the index distinguishes JD v1/v1.1/v1.2/v1.3/v1.4, evidence v1/v1.1, active defaults and experimental request repair. Fourteen prompt/guideline/configuration/repair source snapshots are retained. No new matching rubric was tested in D-064.

Thirteen targeted guard/quality tests passed, zero skipped, before the final evaluator scope change. The final four evaluator-scope tests also passed, zero skipped; these sets overlap and are not added together. Exact outputs, source/reference hashes, paid-plan consistency and offline reproducibility are checked in the closure receipt. No database suite, new dependency, workbook write, gold change, test-set evaluation or git operation occurred.

**Current next step:** accept the new concrete extraction alignment, calculate its gated metrics, and settle the remaining source/safety interpretation or prepare a separately versioned prompt experiment. Stage 2 remains IN PROGRESS for selection; the approved collection itself is complete. Later-stage work stays paused under the user's sequence instruction.


**Final closure verification:** `evals/results/cp23_stage2_followup_closure_verification_20261003_v1.json` confirms 72/72 protected inputs unchanged, 152 local documentation links present, exact evidence/QA and mapping-packet/Markdown reproduction, all 14 prompt/context snapshots matching, and the frozen paid plan unchanged. D-064 is complete with no pending reservation. New extraction acceptance and safe configuration selection remain explicit holds.


## 10. Repair-framing fix and rerun (4 October)

This section records the 4 October presentation preparation run. Calls executed on 3 October 2026 UTC. D-064 already named a completed reference experiment. The new repair authorization is recorded as a separate D-064 addendum; its budget is not borrowed from that experiment.

The repair instruction now has role `user`. Its wording, first-call prompts, schema, routing and 16,000 output-token allowance are unchanged. Every reconstructed request has roles system, user, assistant, user. First drafts were loaded locally with hash checks. Only the eight previously rejected repairs were dispatched. No first attempt was repeated.

The original US$0.30 cap could not cover the conservative bound US$0.6485602. Dion explicitly approved US$0.65 before dispatch. **Actual additional cost: US$0.09795280 for eight calls.** Project ledger: US$1.2715167842, including historical uncertain US$0.0210861. No new uncertain charge. Hard stop: US$8.50. Official public endpoint metadata was checked; request price ceilings and privacy parameters stayed unchanged.

### A versus B

A is the original protocol. B overlays only the eight repaired stages after the repair-framing fix (D-064 addendum). Original failures and costs remain visible. B is recommended as the primary operational comparison because A includes the application framing defect. Dion still decides the primary view. A schema-valid output is not automatically source-valid or semantically correct.

| Model | Extraction F1 A | Extraction F1 B | Evidence Macro-F1 A | Evidence Macro-F1 B | Valid matching A/B | Unsupported positives A/B |
| --- | ---: | --- | ---: | ---: | --- | --- |
| claude-haiku-4.5 | 0.541667 | 0.541667 | 0.186681 | 0.186681 | 1/4 -> 1/4 | 3 / 3 |
| deepseek-flash | 0.861789 | 0.861789 | 0.760806 | 0.760806 | 4/4 -> 4/4 | 3 / 3 |
| gemini-3.5-flash-lite | 0.613333 | Pending new mapping acceptance | 0.000000 | 0.231702 | 0/4 -> 1/4 | 0 / 3 |
| gpt-6-luna | 0.793651 | 0.793651 | 0.744424 | 0.744424 | 4/4 -> 4/4 | 2 / 2 |

The repaired Gemini extraction has 18 units. Its full source review identifies two splits, a SQL/PostgreSQL OR interpretation conflict, and a required-cloud OR changed into two units with AWS preferred. All quotes occur in the source. New concrete mapping acceptance remains required under D-054/D-063. No human approval was manufactured, so B extraction F1 for Gemini is unavailable. The proposed 16-reference mapping is included in the result JSON. Other extraction metrics are unchanged. Process-valid extraction rises from 27/28 to 28/28, without claiming semantic completeness.

### Repair dispositions

| Stage | Initial problem | Repaired result |
| --- | --- | --- |
| gemini-3.5-flash-lite/CV1/F00332 | invalid_source_quote | failed: invalid_source_quote |
| gemini-3.5-flash-lite/CV1/F00036 | group_label_must_be_resolved_by_scorer | done: validator passed; source QA recorded |
| gemini-3.5-flash-lite/CV2/F00815 | invalid_source_quote | failed: invalid_source_quote |
| gemini-3.5-flash-lite/CV2/F00018 | invalid_source_quote | failed: invalid_source_quote |
| claude-haiku-4.5/CV1/F00332 | group_label_must_be_resolved_by_scorer | failed: invalid_structured_output_or_source |
| claude-haiku-4.5/CV1/F00036 | group_label_must_be_resolved_by_scorer | failed: group_label_must_be_resolved_by_scorer |
| claude-haiku-4.5/CV2/F00018 | invalid_structured_output_or_source | failed: invalid_structured_output_or_source |
| gemini-3.5-flash-lite/F00815 | qualification_inventory_unsupported_mapping | done: validator passed; source QA recorded |

All other original stages are excluded: nine successful matching stages and 27 process-valid extraction stages. Their semantic errors remain original observations. The separate DeepSeek Pro/CV1/F00036 failure was an accepted repair with invalid quotes, so it is not a repair-framing replay candidate. Earlier stopped experimental attempts remain historical and outside this comparison. No request in the new batch had a transport rejection; six repaired matching drafts still failed unchanged application validators.

### Per-class evidence accounting

Rows show TP / FP / FN in MATCH, PARTIAL, NO_MATCH order. Every model has the same gold support 35 / 22 / 16. Failed units stay not_assessed and count as FN.

| Model | A per-class TP/FP/FN | B per-class TP/FP/FN |
| --- | --- | --- |
| claude-haiku-4.5 | 5/3/30; 3/2/19; 1/2/15 | 5/3/30; 3/2/19; 1/2/15 |
| deepseek-flash | 30/7/5; 11/2/11; 16/7/0 | 30/7/5; 11/2/11; 16/7/0 |
| gemini-3.5-flash-lite | 0/0/35; 0/0/22; 0/0/16 | 7/2/28; 1/3/21; 3/1/13 |
| gpt-6-luna | 25/1/10; 16/8/6; 14/9/2 | 25/1/10; 16/8/6; 14/9/2 |

### Matching cost and request latency

Includes original billed attempts, original zero-charge rejections and new repairs in B. Percentiles use nearest rank across requests, not successful-stage latency.

| Model | Cost A / B, USD | p50 A / B, ms | p95 A / B, ms |
| --- | --- | --- | --- |
| deepseek-flash | 0.040561914 / 0.040561914 | 28687 / 28687 | 90747 / 90747 |
| gpt-6-luna | 0.007206285 / 0.007206285 | 21559 / 21559 | 21880 / 21880 |
| gemini-3.5-flash-lite | 0.028526630 / 0.058356230 | 592 / 4860 | 6165 / 6165 |
| claude-haiku-4.5 | 0.080392000 / 0.140864000 | 8647 / 7640 | 12619 / 12619 |

The new valid Gemini matching output was reviewed across all 17 logical units and their branches. Exact quotes pass. Three unsupported positives are recorded: generic ML used for unsupervised learning, and Matplotlib/inferential statistics MATCH from Skills only. Descriptive statistics has a weaker cited course list, but the full CV has the cohort evidence used by gold. This is a separate insufficient-citation finding, not a confirmed unsupported label. The v2 QA corrects the v1 classification and preserves both artifacts. Two further interpretation questions concern exploratory workflow and the audience being nontechnical. These are delegated source QA, not new gold labels.

### Proposed offline guardrails (D-065 pending)

G1 lowers skills-list-only MATCH. G2 lowers incomplete use evidence for explicit named-tool conjunctions. G2 excludes skills-list-only mentions when checking use. It does not reinterpret explicit OR or example syntax. Only a bounded vocabulary and literal mentions are checked; aliases, negation, implied scope and general semantic entailment are not solved. No runtime default is changed.

| Model | Macro-F1 A / A+guards | Macro-F1 B / B+guards | Unsupported B / B+guards | Remaining / positive units after guards |
| --- | --- | --- | --- | --- |
| claude-haiku-4.5 | 0.186681 / 0.251754 | 0.186681 / 0.251754 | 3 / 0 | 0 / 13 |
| deepseek-flash | 0.760806 / 0.777417 | 0.760806 / 0.777417 | 3 / 2 | 2 / 50 |
| gemini-3.5-flash-lite | 0.000000 / 0.000000 | 0.231702 / 0.282540 | 3 / 1 | 1 / 13 |
| gpt-6-luna | 0.744424 / 0.744424 | 0.744424 / 0.744424 | 2 / 2 | 2 / 50 |

Four of eight original findings are corrected: Claude P52-U04/P52-U13 and both SQL/PostgreSQL P52-U10 findings. DeepSeek P30-U15/P04-U12 and GPT P04-U06/P04-U21 remain. Two new Gemini skills-only claims are lowered; its generic-ML scope claim persists; the course-citation weakness stays separate. Lowering MATCH to PARTIAL does not prove all remaining positive evidence is supported. Claude's zero observed findings after guards covers only one valid pair, not four successful pairs.

All per-class counts, confusion matrices, change receipts, coverage, new source QA and cost/latency are in the [A/B and guardrail result](../../../evals/results/cp23_stage2_repair_comparison_20261004_v2.json). The [plan](../../../evals/results/cp23_stage2_repair_rerun_20261004_v1_plan.json), [cap approval](../../../evals/results/cp23_stage2_repair_rerun_20261004_v1_approval.json), [actual run summary](../../../evals/results/cp23_stage2_repair_rerun_20261004_v1_summary.json) and [official metadata](../../../evals/results/cp23_stage2_repair_rerun_20261004_v1_provider.json) separate estimate, allowance and billed cost. No winner is frozen.



### Extraction cost and request latency, same original run scope

| Model | Cost A / B, USD | p50 A / B, ms | p95 A / B, ms |
| --- | --- | --- | --- |
| deepseek/deepseek-v4.1-flash | 0.0909947738 / 0.0909947738 | 62352 / 62352 | 453486 / 453486 |
| openai/gpt-6-luna | 0.0172966900 / 0.0172966900 | 31166 / 31166 | 50922 / 50922 |
| google/gemini-3.5-flash-lite | 0.0630724300 / 0.0707236300 | 6463 / 6463 | 13260 / 13260 |
| anthropic/claude-haiku-4.5 | 0.1445380000 / 0.1445380000 | 11158 / 11158 | 16404 / 16404 |

[Extraction operations](../../../evals/results/cp23_stage2_repair_extraction_operations_20261004_v1.json) include v4/v5/v6/v7 original v1.4 attempts and add only the Gemini repair in B. Older v1.3 and separate reference experiments are excluded. Total round-one extraction plus matching cost: A US$0.4725887228; B US$0.5705415228. These are observed collection costs, not a fresh full-run quote.

## 11. Later A1 check under D-066 and D-067, 4 October

The [current versioned-validator and A2 report](CP23_Validator_v11_and_A2_Proposal_20261004.md) supersedes section 10 for model-choice calculations. It retains section 10 as historical A/B evidence. The source-bound validator v1.1 recovered Gemini CV2/F00815 and DeepSeek Pro CV1/F00036 offline, without changing raw model output or making a paid request. Five remaining round-one matching stages are still invalid model outputs. The new SQL reference is applied to every candidate and shown beside the old reference in the [comparison result](../../../evals/results/cp23_sql_reference_comparison_20261004_v2.json). D-065 G1/G2 and D-066 v1 safety/selection amendments are approved, but runtime defaults and the configuration freeze await Dion's A2 decision. The revised Gemini extraction F1 still awaits acceptance of three non-trivial alignments.

## 12. Current decision after the historical boundary

Dion subsequently accepted the strict Gemini/F00815 mappings under D-068. The [versioned result](../../../evals/results/cp23_gemini_f00815_alignment_20261004_v1.json) gives 14 TP, 4 FP and 2 FN for that JD and a seven-JD Gemini extraction F1 of 0.683128. D-068 also selects DeepSeek Flash for both extraction and matching provisionally on development; K and the PARTIAL weight remain open. The [main CP2.3 report](../CP2_03_Model_Comparison.md) contains the current comparison. Section 11 above remains a dated record of what was pending before Dion's decision, not the present status.
