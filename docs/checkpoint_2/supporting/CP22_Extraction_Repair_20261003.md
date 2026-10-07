# CP2.2 Scoped Extraction Repair Experiment

**Date:** 3 October 2026 (Asia/Jakarta). **Run ID:** `cp22_extraction_repair_v13_20261003`.  
**Authorization:** fix extraction in a new versioned development experiment, F00034 first, then CV1 plus one compatible development JD; additional aggregate cap US$0.40 including repair. No mass extraction, test access or model-winner selection.

## Pre-registered scope

Fixed model: existing `deepseek-flash` baseline, low reasoning, unchanged registry. Experimental JD prompt `jd_extraction_v1_3.md` adds an explicit qualification inventory and source-to-unit coverage receipts. Existing guideline v1.3 and scoring formula remain unchanged. Runtime default still selects prompt v1.2; this experiment passes an explicit `ExtractionSpec` and separate cache identity. Every output records the actual experimental prompt version/hash.

The wire schema adds `qualification_coverage`, not a new scored requirement type. Each enumerated qualification bullet maps to actual source-backed unit IDs. The runtime validates full inventory representation, mapping identities and exact quotes, with at most one repair. No bullet is automatically an atomic requirement and no coverage pass is claimed as semantic recall. Public outputs retain the existing `JDExtraction` schema; coverage diagnostics are separate.

| Ordered stage | Purpose | Maximum attempts |
| --- | --- | ---: |
| F00034 | Known one-of-nine qualification omission regression; inspect shared alternative qualifiers and importance | 2 |
| CV1 parse | Confirm complete synthetic sections, work/project distinction and source dates | 2 |
| F00332 pasted JD | Extract the eight qualification bullets and compare coverage/meaning with reviewed development references | 2 |
| CV1 × F00332 matching | Produce source-grounded evidence, constraints and deterministic report; reuse exact same-session extraction | 2 |

F00505 was initially considered before inference but rejected after semantic reference review: P39-U10 explicitly asks for communication skills yet is classified `other`, which may affect the denominator. F00332 instead has 16 approved extraction and 16 CV1 evidence rows, no current export holds, explicit required/preferred context and no `and/or` cardinality conflict. The selection record is `evals/results/cp22_repair_reference_compatibility_20261003.json`. The changed selection is not based on model results; all inference occurs after selection. No gold/workbook edits.

## Cost and stop protocol

Total maximum eight calls; at most one repair per stage. Per-attempt upper bound uses at most 100,000 input tokens and 16,000 output tokens, with routing ceilings US$0.30/US$1.20 per million. Maximum per stage US$0.0984; total conservative bound US$0.3936. Larger requests fail before dispatch. Aggregate ceiling US$0.40 is additional to previous experiments and applies across resume/repairs; project hard stop remains US$8.50. Existing uncertain charges remain reserved.

The staged runner persists attempt slots, request reservations, input/code/prompt fingerprints and ledger receipts. It executes exactly one stage, then requires an operational source-based semantic receipt. Important semantic loss, fabricated claims, unresolved required structure, uncertain transport or unreconciled reservations stop progression. No automatic reset, alternate model, silent prompt edit or new run ID can bypass the aggregate cap. The old failed probe remains terminal and unchanged.

Official endpoint metadata was checked3 October:32endpoints,22listing structured output within the fixed price ceiling. Requests still enforce supported parameters, data-collection denial, routing price caps and zero SDK retries. This does not independently certify provider retention/privacy.

## Reference and interpretation limits

The model receives original source text, the guideline and source-bullet inventory; it never receives gold labels or gold unit text. Operational inspection is delegated QA, not new human approval. No F1, benchmark winner, calibrated hiring probability or test result will be inferred from this small case study. Model output must be checked for full meaning beyond syntactic coverage.

## Results

Initial preflight and fake-client safeguards were prepared before execution. The following entries preserve each stage in order. Final outcome: all four stages completed with delegated operational checks;7 calls,US$0.070420540 total, within the original US$0.40 authorization. Default prompt selection is unchanged; broad development extraction remains open.

### First-stage inspection and remaining repair allowance

Initial F00034 call:16 units, all9explicit qualification bullets represented,51.413seconds,US$0.007494996. The coverage omission is corrected in this response, but source inspection found REST API experience weakened to understanding and named model alternatives assigned generic concept categories. These details are not accepted merely because coverage/schema passed.

The second and final stage attempt is used for a source-review semantic repair. This is within the originally authorized repair allowance, not a new model/prompt search or a reset. `semantic_repair.py` provides a nonterminal-only transition: it preserves the first result in history, retains attempt counts/reservations/ledger, and cannot reopen a terminal failure. Its extension hash and exact correction receipt are recorded. A structural repair would have consumed this same slot; a third attempt is prohibited. The repaired result must pass source inspection before downstream stages.

### F00034 accepted operationally after repair

The final allowed repair took 20.179seconds and retained16 units for 9 qualification bullets. All source quotes match; required/preferred scope, the two-year qualifier on each role branch, degree scope, and portfolio OR are preserved. REST API experience is restored, named LLM alternatives use tool categories, and generic LLM group context remains a knowledge area. First and repaired artifacts are retained separately with linkage hashes; no gold labels changed.

Stage aggregate cost US$0.018673596 across2 calls. The operational acceptance receipt permits CV1 parsing next. This establishes a narrow source-based repair success, not model accuracy on unseen jobs or the superiority of this model/prompt.

### CV1 parsing and F00332 first extraction

CV1 parsing completed in 154.687 seconds,one attempt. Thirteen quoted facts preserve education, two employment entries, two projects, skills, certification and languages. Employment dates retain month precision and projects do not create work tenure. Nonblocking metadata issue: `profile.language` contains a proficiency line rather than normalized document language; this field is not used for matching/constraints here. Location remains only a suggestion.

F00332 first extraction:12units representing8 source bullets,45.364seconds. Source review rejected the AND-to-OR conversion for Python/SQL/Excel, a falsely unresolved plain education OR, a practice/tool category and incomplete atomic splitting. This stage still has one repair allowance. The same semantic-repair extension is generalized to the two pre-authorized JD stages only; both attempt/cost limits and first-output retention remain enforced. The exact code-extension hash is recorded per repair. No gold record is edited or sent to the model.


### F00332 repaired extraction and final matching (3 October continuation)

F00332's one permitted repair produced16 units for 8 source bullets. It restored the three independent Python/SQL/Excel requirements, resolved the explicit education OR, retained knowledge/practice categories and separated source-backed activities. The accepted source receipt is `cp22_repair_f00332_acceptance_20261003.json`. The repaired source and original output are retained; neither becomes new gold.

The first matching call had already finished when execution transferred:16 assessments,72.22%,39.267 seconds,US$0.013860300. The run was awaiting semantic inspection, not still running or failed. Source review found omitted partial support for learning/independence/project ownership. A final matching repair used the same run ID, ledger, US$0.40 cap and remaining stage allowance. `scripts/repair_cp22_matching.py` delegates to the ordinary pipeline validators and scorer, reuses exact accepted extraction in session memory, permits one matching dispatch only and cannot issue extraction or an extra validation-repair call. The first result remains in history.

The final call cost US$0.010082400 and took 25.151 seconds. All 16 evidence records and both education branches were inspected against CV1. Three soft-skill results changed from NO_MATCH to PARTIAL with certificate/thesis quotes; no automatic claim of independent learning or full autonomy. The score remains 72.22%:5 MATCH + 3 PARTIALout of 9 required scored units. Six soft skills and one preferred item are shown separately. Experience and location areunknown for explicit reasons, not inferred compatible.

Two differences remain against approved gold:U15/P30-U08learning andU16/P30-U15actionable recommendations arePARTIALversusMATCH. They are recorded in `cp22_repair_semantic_review_20261003.json`; proposed one-to-one mappings were checked by meaning, not row number. Human alignment remains pending and no F1/Macro-F1 is published. The source-based operational pass does not certify unattended quality. In particular, the actionable qualifier is not explicitly demonstrated by a presentation sentence, so it was not forced to MATCH.

The experiment is now terminal `complete`,7 calls,US$0.070420540,attempt counts2/1/2/2 and no outstanding request reservation. No more inference is needed or authorized under this closed stage sequence. The older failed probes remain unchanged. Official model/routing sources were checked before this final call; routing/privacy/price controls stayed in the existing client. Initial sandbox DNS failure occurred during key verification before dispatch, consumed no attempt or inference charge, and was followed by authorized network access.

### Verification, scaling and checkpoint boundary

Continuation tests:228 selected offline passes,0 skipped,5 known SWIG warnings. They include the 9 guard tests run before dispatch; do not add counts. The real-model chain and deterministic saved-response replay provide end-to-end integration evidence. No DB change or DB rerun; prior5 database passes remain historical. Gold manifest/files revalidated, workbook/source/split/pool/config/prompt hashes unchanged. No dependency, git, workbook write, export, gold alteration, tuning or test evaluation.

Current ledger 117 records,US$0.290770384 including US$0.021086100 uncertain prior reservation; confirmed-record subtotal US$0.269684284. The current continuation itself cost US$0.010082400. Full cost details and acceptance boundaries are in the main English CP2.2 report.

`cp22_development_extraction_plan_20261003.json` inventories 214 development IDs without inference. Five remaining priority IDs have a proposed US$0.492 upper bound,US$0.50 ceiling; this is a future scoped proposal, not a continuation of the closed US$0.40 run. Full 214 has US$21.0576 maximum under the same conservative request bounds, exceeding the US$8.50guard. Before execution, add explicit experimental-spec and semantic-checkpoint support; never use the legacy default batch or treat a raw first draft as an accepted repair. Two observed assisted JD costs are insufficient for reliable extrapolation.

D-050, approved explicitly by Dion on 3 October, closes CP2.2 implementation and evidenced acceptance. Broad development extraction remains unexecuted and moves after CP2.3 configuration evaluation. The previous planned-scale criterion is superseded for this checkpoint, not silently marked achieved. Default selection, gold, metrics, budget and test-isolation rules remain unchanged. Formal tuning is NOT RUN.


Final administrative gate: D-050 readiness regression passed11 tests after the explicit scope decision. This selection overlaps the 228-test suite. All36 protected-file hashes and the saved gold bundle were verified in `cp22_resume_verification_20261003.json`. CP2.2 is DONE for its approved scope; CP2.3 formal tuning remains NOT RUN.
