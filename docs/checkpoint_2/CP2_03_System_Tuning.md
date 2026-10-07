# CP2.3: System Tuning

## Final status (7 October 2026)

**Status:** DONE. The configuration was chosen on development data and frozen before the held-out test (D-087), and the two items left open at the end of CP2.3 are settled (D-091, D-092).

**Goal.** Pick every setting by measurement on the development split (retriever, embedding, K, PARTIAL weight, models, prompts, hold and order rules), then freeze the configuration and the test protocol (D-053), so that nothing in CP2.4 is tuned on test data.

**Data.** Development split only: 214 target-role JDs, synthetic CV1 (Indonesian) and CV2 (English), reviewed development gold (r3, then r4 with 46 gap labels, D-085), seven extraction reference JDs and four evidence pairs (73 units). I did not touch the 214 test JDs, CV3-CV5 or any test label.

**Method.** For each component I fixed the selection rule before computing the deciding numbers: D-044 (embedding), D-029 as amended by D-066 (models), D-078 (K, weight, seniority rule) and D-084 (retriever change). Metrics follow D-052 and D-073: original positions, unjudged jobs never counted as 0, and held jobs kept in the product order. D-075 adds bootstrap intervals.

| Setting | Final choice | Evidence |
| --- | --- | --- |
| Stage-1 retriever | Hybrid FTS + Qwen3 dense, RRF k 60 (Qwen won the D-044 rule; D-084 kept hybrid against every challenger on gold r4) | `evals/results/cp23/post_labeling_development_v13_reviewed_20261004_gap_r4_v1/summary.json` |
| Seniority rule | `seniority-demote-3y-v1` over the stage-1 top 30 (D-074, D-078) | same summary |
| K and PARTIAL weight | K = 10, weight 0.5, from the D-078 rule (D-086) | same summary |
| JD extraction | DeepSeek Flash, JD prompt v1.4 experimental (D-068, kept by D-077 and D-083) | [Model comparison](CP2_03_Model_Comparison.md) |
| Evidence matching | GPT-6 Sol with Luna fallback (D-083), evidence prompt v1.1, quote check v1.1, G1/G2 | D-079, D-082, D-083 |
| Holds and order | H2v2 (D-072), experience block (D-086), product order (D-073) | D-086 |
| Freeze | Receipt `evals/freeze/cp23_freeze_draft_v2/`, approved as D-087 on 6 Oct (57 file hashes; v1 superseded) | `freeze_receipt_APPROVED.json`; `prepare_cp23_freeze.py --verify` ok on 7 Oct |
| Development result | Final order macro P@5 0.70, NDCG@10 0.552 (0.568 with the experience block). Stage 1 with the seniority rule alone already reaches P@5 0.70, NDCG@10 0.550 | D-086 |

**Extraction scope (D-091).** D-050 had moved full development extraction into CP2.3. In the end I only extracted the 52 JDs that appear in the Hybrid Qwen top 30 for CV1 or CV2: 51 were attempted, 48 came back process-valid, and F00369 is held at source (`evals/results/cp23/pipeline_v11/coverage_summary_v2.json`). The other 162 development JDs were never extracted; the 3 October per-JD inventory of all 214 is in `evals/results/cp22_development_extraction_plan_20261003.json`. I did not run them because they could not change any CP2 choice: every K, weight and order cell in D-078 sits inside the reordered top 30. I recorded this scope as D-091. Extracting the rest stays optional.

**Privacy (D-092).** Local masking, consent tied to the exact masked text and the session controls are implemented, and all CP2.4 parses ran on masked text. They are covered by component/unit tests: the privacy-control and masked-quote tests, and API-level tests with a fake run (PR-01 to PR-07 and PR-09, not a deployed host). The masked-quote receipt (`evals/results/cp23_masking_quote_compatibility_20261004_v1.json`) only shows that quotes can still be traced. I have not validated privacy end to end, and the original-vs-masked quality comparison did not run (only the offline preflight `tests/test_cp23_masking_pairs_preflight.py` exists). Both move to CP3: CP3.4 runs them and CP3.5 reports them. Until then there is no claim that masking has no effect on matching, and real-CV processing stays off.

**Test leakage.** None. The test split was opened only after D-087.

**Figures (development, two CVs).** [Retrieval methods](../../reports/figures/cp2/fig01_retrieval_methods.png), [embedding rule](../../reports/figures/cp2/fig02_embedding_recall20.png), [LLM quality](../../reports/figures/cp2/fig03_llm_quality.png), [cost and latency](../../reports/figures/cp2/fig06_cost_latency.png) and [pipeline v1.1 coverage](../../reports/figures/cp2/fig08_pipeline_v11_coverage_20261004_v3.png). Denominators and limits are in [CP2.5](CP2_05_Evaluation_Visualization.md).

**Limitations.** Only two development CVs; labels are assisted and come from one reviewer; most of the development ranking gain came from the seniority rule (D-086); privacy is not validated end to end (D-092).

**Reproducibility.** `scripts/run_post_labeling.py` produces the D-078/D-084 result. `python scripts/prepare_cp23_freeze.py --verify evals/freeze/cp23_freeze_draft_v2` checks the 57 frozen hashes.

**Next.** CP2.4 ran the D-087 configuration once on the held-out split, unchanged.

Everything below is the 3-6 October record, kept as written. Its provisional statements (DeepSeek matching, K = 20, "not DONE", open D-050/D-051) were replaced later by D-083, D-086, D-087, D-091 and D-092.

## Historical record (3-6 October 2026)

**Update, 6 October 2026:** **Status:** DONE for development; the freeze receipt waits for Dion's approval (approved later the same day as D-087). Gold r4 (D-085) completed the judgments. The D-078 rule chose K 10, PARTIAL weight 0.5 and the seniority rule; Hybrid Qwen stays under D-084; GPT-6 Sol matches (D-083); the experience block joins the freeze (D-086). Final product order on development: macro P@5 0.70, NDCG@10 0.552 (0.568 with the experience block). With the seniority rule, stage 1 alone reaches P@5 0.70 and NDCG@10 0.550, so stage 2 adds explanations rather than ranking gain on these two CVs. Details: [EXP-20261006-R4](../experiments.md).

**Earlier status (3 to 4 October 2026):** IN PROGRESS. D-068 records a provisional development configuration. The later pipeline v1.1 experiment has 42 of 60 development pairs with a final or explicitly provisional score under D-071, below its 54 of 60 target. It cannot confirm H4, K, the PARTIAL weight or full one-CV latency. D-050 extraction and D-051 privacy impact remain open. The frozen test set has not been used.

**Audit update, 4 October 2026:** see the [audit fixes report](supporting/CP23_Audit_Fixes_20261004.md). H2v2 (D-072) gives 33 of 60 usable pairs, product-order metrics (D-073) make final-order cells measurable, a seniority rule (D-074) is a development candidate, bootstrap intervals (D-075) show DeepSeek and Luna are not distinguishable on this sample, and a Luna matching check (D-076) is approved but not yet run.

## Summary

JobFit compared six retrieval methods, two embedding models, and six LLM configurations across round one, reference and round two. Qwen met the pre-registered embedding selection rule. Hybrid Qwen and DeepSeek Flash were chosen provisionally for candidate retrieval, JD extraction and evidence matching. The larger Part B collection exposed extraction and matching coverage limits. Pipeline v1.1 raised process-valid JD extraction and score coverage but did not meet its coverage target; no K or PARTIAL weight can be selected from complete final-order metrics. The [main comparison report](CP2_03_Model_Comparison.md) contains the small fixed-case comparison. The [Part B report](supporting/CP23_PartB_Development_Run_20261004.md) and [pipeline v1.1 report](supporting/CP23_Pipeline_v11_20261004.md) retain both larger runs and their limits.

## Goal

Choose a measured configuration for recommending jobs from a CV. Keep candidate retrieval, requirement extraction, evidence matching and final ordering distinct so that one metric cannot hide a failure in another stage.

## Inputs

- Locked 214-job development half of the 428 target-role jobs, with CV1 and CV2 only.
- Reviewed development relevance labels, seven JD extraction references, and four fixed CV/JD evidence pairs containing 73 requirement units.
- Frozen source and split hashes, versioned prompts, saved model outputs, source-span validation, the usage ledger and D-029/D-044/D-052/D-054 evaluation rules.
- The untouched test split, CV3 through CV5, and real CVs are outside this stage's model-selection inputs.

## What was done

1. Compared keyword B0, PostgreSQL FTS B1, dense and hybrid retrieval with both embedding models on identical development scopes.
2. Compared four low-cost LLMs for extraction and matching, then measured GPT-6 Sol as a quality reference and DeepSeek Pro as a second-round candidate.
3. Fixed a request-repair framing defect. Preserved original A results and used the bug-fixed B view as the primary operational comparison under D-066.
4. Applied validator v1.1, bounded guardrails G1/G2 and the D-067 SQL reference consistently. Strict D-054 accounting was also applied to Gemini/F00815.
5. Recorded the provisional D-068 configuration, six comparison figures, a Part B coverage figure, a one-page presentation summary and an explicit K=20 cost projection.
6. Ran a capped development end-to-end check on the frozen Hybrid Qwen top-30 lists. It stopped after two matching transport timeouts, then resumed only 31 untouched pairs under Dion's amended US$2.50 total cap. All 60 pair records are saved. The [Part B report](supporting/CP23_PartB_Development_Run_20261004.md) separates collection from score quality.
7. Checked optional-filter grouping and a mechanical masked-quote mapping on synthetic CV1/CV2. The Part B evaluator now holds percentages for JD units marked `needs_review`, following D-049. These checks are offline and do not approve semantic labels or public CV handling.
8. Ran a versioned pipeline v1.1 coverage experiment on the same 60 development pairs. Dynamic output limits, longer timeouts, four-worker matching and D-071's provisional H2 hold rule were tested. A bounded follow-up retained unresolved source and model failures rather than loosening validation.

## Results

| Question | Development result | Record |
| --- | --- | --- |
| Embedding | Qwen beats OpenAI by 0.206 dense and 0.077 hybrid labeled-pool Recall@20, exceeding D-044's 0.05 rule | [Retrieval report](supporting/CP23_Stage3_Retrieval_Comparison_20261003.md) |
| Candidate method | Hybrid Qwen has the highest labeled-pool Recall@20, 0.549; B0 has the highest P@5, 0.500 | [Comparison](CP2_03_Model_Comparison.md#3-stage-1-retrieval-comparison) |
| Extraction | DeepSeek Flash F1 0.862 versus Luna 0.794 on seven JDs; strict Gemini F1 0.683 | [Extraction record](../../evals/results/cp23_gemini_f00815_alignment_20261004_v1.json) |
| Matching | DeepSeek Flash guarded Macro-F1 0.772 versus Luna 0.730 on 73 units, with four valid pairs each | [Validator and selection report](supporting/CP23_Validator_v11_and_A2_Proposal_20261004.md) |
| Safety | DeepSeek retains two confirmed unsupported positives among 50 positive units; source spans must be displayed | [Decision D-068](../decisions.md) |
| Cost and latency | Cached-JD K20 matching projection is US$0.203 for DeepSeek; its observed matching request p95 is 90.747 seconds | [Projection](../../evals/results/cp23_k20_cost_projection_20261004_v1.json) |
| Larger development check | 51/52 JDs attempted, 37 process-valid and 14 failed; 25 pass deterministic score eligibility. All 60 pair records saved, but only 20 final scores; 0/18 complete final-order metric cells | [Part B completion](../../evals/results/cp23/end_to_end_dev/cp23_partb_completion_20261004_v3.json) |
| Pipeline v1.1 coverage | 48/51 process-valid JD outputs; H1 26/60 final scores, H2 26 final plus 16 provisional, or 42/60 usable; 0/36 complete H1/H2 final-order cells | [Final v1.1 receipt](../../evals/results/cp23/pipeline_v11/coverage_summary_v2.json) |

The [figures](CP2_05_Evaluation_Visualization.md) and [recommendation summary](CP2_06_Recommendation_and_Summary.md) use development results only.

## Interpretation

Hybrid retrieval finds more known relevant candidates at depth, while B0 ranks the first five better in this small pool. DeepSeek's guarded matching quality exceeds Luna's by about 0.042, which is above the revised D-029 0.03 cost switch threshold. DeepSeek is much slower in the observed requests. CP3 needs concurrent matching, cached JD extraction and a precomputed synthetic demo. If one-CV latency proves unacceptable, Luna is the speed fallback with its measured quality trade-off. Match percentages remain evidence coverage of identified required units, not probabilities of hiring.

## Limitations

- Only two development CV queries and four fixed evidence pairs informed the choice. Labels were assisted and reviewed by one annotator.
- The 214-job development half is a tuning scope, not a representative deployment estimate. Deeper ranking positions have incomplete relevance judgments.
- Gold-input final ordering had no fully scorable K/weight cells. K20 and weight 0.5 remain provisional after pipeline v1.1 because only 42/60 pairs have a final or provisional score under H2. A provisional score excludes listed unresolved units and is less complete than a final score.
- All 18 Part B and all 36 pipeline v1.1 H1/H2 final-order metric cells are unavailable under D-052's original-position and complete-candidate rule. The scorer's subset diagnostic cannot choose K or the PARTIAL weight. The one-CV K20 end-to-end wall time was not measured. The v1.1 ledger retains a US$0.0501633 uncertain reservation from its interrupted first dispatch.
- Complete cached extraction coverage for all 214 development jobs is not claimed. D-050 requires a per-job status and an approved scope or budget disposition.
- D-051 local masking and session controls are prototypes for synthetic data. Paired quality impact and public API/UI security acceptance remain separate gates. Real CV processing is disabled.
- The Part B score-order diagnostic is not the full D-013 product order. Saved stages do not carry confirmed constraint context. The offline [quote mapping receipt](../../evals/results/cp23_masking_quote_compatibility_20261004_v1.json) found 13 changed evidence rows, all mechanically traceable after masking; semantic compatibility and city policy remain open.
- Held-out CP2.4 evaluation has not been performed and must not be used to choose prompt, model, K or weight.

## Decisions (as of 4 October; final decisions are in the table at the top)

- D-044 selects Qwen on development using the pre-registered Recall@20 rule.
- D-065 approves bounded G1/G2 guardrails. D-066 revises D-029 for v1 safety reporting and per-task selection. D-067 records the consistent SQL example reference.
- D-068 provisionally selects Hybrid Qwen and DeepSeek Flash for extraction and matching. The selected settings live in [a versioned configuration](../../config/versions/pipeline_cp23_provisional_20261004.yaml). The historical active config remains unchanged because frozen experiment records hash that path.

## Changes from the plan

The development comparison needed a repair-framing correction, source-bound quote validation and a reviewed SQL reference before model choice. GPT-6 Sol remained a quality reference. Broad JD extraction was carried from CP2.2 under D-050 and is now planned as quality-gated, resumable development work. It cannot be reported complete from a small probe or from the top-30 Part B subset. The historical schedule and the full sequence of changes remain in the [progress log](supporting/CP23_Progress_Log.md).

## Historical next step (4 October 2026)

Use the [pipeline v1.1 report](supporting/CP23_Pipeline_v11_20261004.md) as a measured coverage finding, not a full quality benchmark. It reached 42/60 H2 scores against the 54/60 target, with zero complete final-order cells and unresolved semantic disagreements. K and weight remain provisional. D-050 broad extraction and any further retry plan need a separate quality and budget decision. The four-pair D-051 masked comparison remains deferred. Freeze the full test protocol under D-053 before CP2.4. Do not mark CP2.3 DONE until these acceptance items are satisfied or Dion explicitly accepts a documented carry-over.
