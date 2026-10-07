# Development Evaluation Contract

**Version:** evaluation-contract-v1.1. **Date:** 3 October 2026.  
**Authority:** [D-052](decisions.md#d-052-development-evaluation-scope-and-metric-conventions) and [D-054](decisions.md#d-054-cp23-stage-1-case-reviews-and-strict-splitmerge-extraction-f1).  
**Status:** Conventions approved; implementation alignment and benchmark readiness are checked separately. This contract is not a completed comparison or blanket approval of future model mappings. v1 is retained in historical receipts.

## 1. Scope and reference selection

Start with seven complete compatible development JDs for extraction and four CV–JD evidence pairs using CV1/CV2, following D-045. Choose varied language, role, seniority, length, education/experience and AND/OR/preference cases before inspecting candidate performance. Do not cherry-pick easy cases. Include F00034 as a disclosed known development regression where compatible; if it cannot join the seven valid references, keep it separately and explain. Its repair history is not unseen performance evidence.

Use all valid reviewed C labels in the common development scope, beyond the historical 50 target when eligible. Audit the union of original top10 results across all six methods for CV1/CV2; deduplicate by CV/job identity. Produce a gap/review request manifest, not automatic labels or a new frozen collection pool. The 69-row export is an inventory, not a claim that every row is eligible for every comparison. Held/unjudged items stay explicit. Added review volume must be shown before requesting work; no full labeling redo.

Authority is `evals/gold/development_v13_reviewed_20261002_r2`, not concatenated pilot exports or mutable workbook copies. Record row/source hashes, historical guideline versions, completeness, logical units, holds and CV compatibility. Row approval alone does not establish whole-JD completeness. No workbook/gold/source/split change is authorized. Test CV3–CV5 and test labels/output remain closed.

## 2. Ranking conventions

- Relevant means C=2 or3 for both P@5 and Recall@K. NDCG uses all relevance grades0–3 with exponential gain `2**relevance - 1` and logarithmic position discount.
- Primary P@5 uses the **original first five returned positions**, denominator5, only when five results exist and all five have eligible judgments. Otherwise return unavailable with reason and coverage. Never fill a missing judgment with a lower-ranked labeled result or assign it relevance0.
- Keep original rank positions and report missing top10 judgments for NDCG@10. Implementation should withhold the primary value if required top10 judgments are missing; an exhausted shorter ranking must be explicitly marked and evaluated under a documented short-ranking convention, not invented labels. IDCG uses the same declared eligible judged pool. No corpus-complete claim follows from partial pool judgments. Any condensed-list diagnostic must be separately named and cannot replace original-rank primary metrics.
- Recall@10/20/30 = judged relevant jobs in the original topK divided by all judged relevant jobs in the declared eligible pool. Report this as **labeled-pool recall**, plus unjudged topK and overall judgment coverage. Zero relevant denominator is unavailable, not a perfect score. Filter recall is separate: retained judged-relevant jobs / judged-relevant jobs before filtering.
- Per-CV results and query count are mandatory; CV1/CV2 are two queries, not dozens of independent queries. No uncertain statistical superiority from small differences.

## 3. Evidence metrics and failure accounting

Use MATCH, PARTIAL and NO_MATCH on fixed verified requirement identities. All reference units remain in the primary denominator. Missing/failed/needs-clarification assessments lacking a valid final label are `not_assessed`; do not convert them to NO_MATCH. They add a false negative to the corresponding gold class without inventing a fourth prediction class. If an artifact carries contradictory status/label, flag it instead of silently accepting it. Report the confusion table including not_assessed, per-class support, TP/FP/FN, coverage and failures.

Primary per-class F1 is `2TP/(2TP+FP+FN)`. With positive gold support and no correct predictions, F1=0 even when precision is undefined because no positives were predicted. If gold support is zero for any class in the **aggregate chosen comparison set**, flag class coverage incomplete and do not use that result to select a three-class winner. Report per-class counts and any supported-class diagnostic explicitly; do not silently change averaging across candidates or label an absent class perfect. Aim to select the four pairs with all three classes represented without editing gold. A single pair missing a class does not invalidate an aggregate set that covers all three.

Primary Macro-F1 averages all three F1 values only on an eligible common three-class set. Assessed-only quality is optional diagnostic and never the main selection result. Compare matchers on identical verified requirements first; end-to-end quality with model-extracted requirements is a separate experiment.

## 4. Extraction alignment and fair comparison

Check source coverage, qualifications, AND/OR/grouping, shared qualifiers, category and importance as well as exact quotes. Equal row numbers or identical text similarity do not certify semantic equivalence. Missing model units and hallucinated extras remain omissions/extras. **Historical D-052 state:** split/merge scoring was blocked and two F00332 interpretations awaited review. **D-054 amendment:** after human verification of complete inventories and semantic mappings, one-to-many/many-to-one relations use strict independently assessable logical-unit F1: no automatic TP; count unmatched gold obligations as FN and unmatched model units as FP. Clause-level similarity is a separate diagnostic. Many-to-many relations remain unavailable pending a separate convention. Dion approved the 16 F00332 mappings and the two PARTIAL corrections; the original artifacts remain historical and the approved amendment is versioned separately.

All candidates receive the same case set, guideline, substantive instructions and correction allowance. Log necessary API-format/support differences and all versions. At most one automated repair per stage under a fixed declared protocol. Record first-attempt results separately from repaired automatic results; charges/latency include failure and repair. Bespoke reviewer corrections are diagnosis/assisted acceptance, not unattended benchmark success. Never send gold labels or expected answers to candidate inference/repair.

D-029 selection and safety rules remain unchanged. This document does not choose a model, change PARTIAL0.5 or score denominators, certify a safety pass, authorize inference or approve a frozen configuration.

## 5. Stage-1 execution deliverables

1. Versioned candidate manifest: seven JDs/four pairs, variation matrix, source/reference identities, provenance and unresolved cases.
2. Deduplicated original-top10 judgment gap list with held reasons and estimated human review effort; no workbook or pool regeneration.
3. Machine-readable contract receipt citing D-052, distinct from case/alignment approval status.
4. Evaluator compatibility audit and scoped fixes/tests with hand-computable synthetic examples. Preserve old artifacts and label old condensed metrics as historical if present.
5. One English supporting report and readiness JSON showing each gate separately: contract, references, alignment, coverage and implementation. Partial readiness never becomes blanket approval.
6. Updated CP2.3 report/master plan/handoff. Formal tuning remains NOT RUN; preparation can be IN PROGRESS or COMPLETE. No paid call, test evaluation or winner.

## 6. Privacy boundary

Follow [D-051 privacy design](privacy-threat-model.md). This stage uses original development synthetic references only. Do not implement masking/session/UI controls in this audit; that is the next planned workstream. Later paired masked variants require versioned preprocessing and exact masked-source quotes without altering original gold. Real CVs remain disabled.

## 7. Held-out confirmation protocol (D-053)

Approved 3 October 2026; documentation only, execution NOT RUN. D-053 supersedes the historical top12/condensed test-pool rule in D-046 and fixed 60-relevance-label target in D-045. D-052 remains the development contract; its metric/failure conventions carry into test without choosing them from test outcomes.

### Freeze before held-out processing

CP2.3 must record an approved immutable configuration/protocol identity before any held-out model processing or evaluation: LLM and embedding IDs, prompt/schema/guideline/preprocessing/masking versions, retrieval method and K, RRF/filters, deterministic tie-breaking, score/constraint ordering and hold rules, repair allowance, metric definitions, reference alignment rules, eligible universe/split hashes and pool construction. Settle unresolved short-ranking and extraction split/merge conventions before the affected metric is run; otherwise mark it unavailable. Test inference needs its own preflight under the existing budget guard. This decision does not authorize calls or label exports.

Use the same frozen test universe and filters for both orders. Preserve the initial stage-1 order and the final application order after matching, including the existing constraint-first/score/hold behavior; do not implement a new pure-percentage sort. The final list only contains candidates actually analyzed under the frozen K policy. Keep failures/held counts visible; never backfill or change K in response to test labels.

### Blind ranking pool

After freeze, form the union of original top10 stage-1 and original top10 final recommendations for each CV, deduplicated by (cv_id, job_id). This is normally 10–20 pairs per CV, 50–100 for five CVs if both lists have at least ten; shorter/failed lists are reported rather than padded. This pool compares the two orders of the selected system, not all development candidates. Preserve both rankings and a separate provenance manifest with ranks, reasons, hashes and run identity.

Before producing review workbooks, report the exact pair counts, overlap and estimated effort using measured review times or explicit assumptions. Schedule within Dion's 2–3 hours/day and confirm practical batching with him; approval of the pool rule does not assume unlimited review time. Never choose a smaller subset based on relevance outcomes. Label all selected C items blind: shuffled rows, no ranks, scores, method names, or model suggestions. QA follows the saved initial human labels; changes require human approval. Preserve draft-assisted provenance for the separately planned extraction/evidence test items.

### Coverage and interpretation

- Primary ranking outcomes are P@5 and NDCG@10 on original positions. P@5 requires five returned and judged positions, denominator5. NDCG@10 requires complete judgments for needed original top10 positions, with relevance0–3 and exponential gain. No condensing or unjudged=0. Short/exhausted lists follow only a predeclared convention, otherwise unavailable.
- For a paired comparison, use the same declared eligible judged pool/IDCG for both orders and only the CVs eligible for both. Report method-specific coverage and omitted reasons separately. IDCG is pool-relative, not the unknown ideal over all214 test jobs. IDCG0 is unavailable.
- Recall@10/20/30, if reported, is labeled-pool recall with original topK, numerator/denominator and unjudged coverage. The top10 union does not establish corpus recall and can strongly favor the pool-building system; recall is a limited diagnostic, not a headline retrieval-completeness claim. Do not claim Recall@20/30 when the saved run is shallower than K without a predeclared exhausted-list rule.
- Filter recall requires judged relevant cases before filtering, including discarded cases, in a declared pre-filter scope. If unavailable, report not measured; a post-filter pool cannot establish filter recall.
- Report CV1/CV2 (familiar profiles, held-out jobs) separately from CV3–CV5 (held-out profiles and jobs), alongside per-CV results and query counts. Five CVs do not justify broad statistical generalization.
- Partial completion may report only eligible CV/metric combinations, with planned/completed counts and missingness. No selective best-CV aggregate. Paired comparisons use a common eligible subset. Pending/draft labels never become gold or implicit negatives. Evidence class support/failures and extraction compatibility retain D-052 gates; assisted/blind provenance remains explicit.

### Isolation and follow-up

Keep the frozen cluster-separated JD split, pilot in development and CV3–CV5 out of tuning. Existing fixed corpus embeddings do not authorize using held-out labels, rankings or CVs for configuration selection. Log test exposure/run identity and deterministic reruns; failed-call retries/one repair follow the already frozen allowance. After test exposure, any model/prompt/K/masking change is a new development iteration. Reusing the exposed test is regression evidence, not fresh independent confirmation; new independent claims require an untouched holdout. Preserve unfavorable results and technical failures.

D-050 development extraction carryover and D-051 privacy acceptance remain separate obligations. An unmasked synthetic test does not validate the private-upload path. This protocol changes evaluation planning only, not application behavior, source/gold data, runtime configuration, or current CP2.3 execution authorization.
