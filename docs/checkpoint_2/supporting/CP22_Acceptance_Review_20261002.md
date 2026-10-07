# CP2.2 Acceptance Review: Current Outcome

Updated3 October 2026. This record supersedes the earlier preflight-only summary. The [stage report](../CP2_02_Modeling_Pipeline.md) contains the current implementation, export, cost and handoff details. Historical source fixtures and probe results remain unchanged.

## 1. Eight synthetic cases

The user delegated completion and checking of the existing tasks. The eight revisions below were inspected against guideline v1.3 and tested for exact source quotes, schema validity, expected score, constraints and unchanged original hashes. Status: **delegated review complete**. Independent human approval is not claimed. These are controlled rule tests, not predictions from a real model.

| Fixture | Percentage | Score state | Experience constraint | Review and correction |
| --- | ---: | --- | --- | --- |
| dev_01_clear_match | 87.5 | final | compatible | Add explicit required heading and relevant employment scope; retain list-only PARTIAL. |
| dev_02_experience_too_short | 83.33 | final | explicit_conflict | Keep the three-year Python qualifier and inclusive dated employment; do not count title as technology tenure. |
| dev_03_duration_unknown | 75.0 | final | unknown | Explicitly unavailable employment history; project supports use, never employment duration. |
| dev_04_or_alternative_group | 50.0 | final | unknown | REST API development is knowledge_area. Replace unresolved cross-degree equivalence with an explicitly incomplete CS degree in this synthetic fixture; retain OR as one obligation. |
| dev_05_repeated_requirement | 62.5 | final | unknown | Preserve complex SQL activity qualifier as a distinct normalized requirement; add an exact repeated general SQL obligation to keep this a deduplication case. |
| dev_06_ambiguous_importance | 83.33 | provisional | unknown | Supply explicit source conflict for unknown importance and an explicit preferred softener; remove degree-equivalence ambiguity from statistics evidence. Generic LLM API familiarity is knowledge_area, not a named tool. |
| dev_07_no_assessable_requirement | No percentage | no_score | unknown | Supply explicit preferred softener and conflicting soft-skill importance; no technical required denominator. |
| dev_08_parsing_failure | No percentage | on_hold | unknown | Clarify assessment-stage failure despite successful CV parsing; preserve null label and on_hold. |

Important distinctions: an OR group counts once; SQL activity qualifiers are not erased merely because the tool is the same; unknown importance needs explicit conflict; tool usage and unknown duration can coexist; the fixture experience comparison uses its stated relevant-history assumptions, not an inference from the job title. The experience input is a separate constraint test, not an extra hidden unit in the score denominator. Original fixture date 29 September is preserved; runtime date is 30 September.

## 2. Current live result and historical failure

The2 Octoberfixed-baseline probe remains closed after one-of-nine F00034 extraction. Its failure is retained as historical evidence. The new authorized repair experiment `cp22_extraction_repair_v13_20261003` has completed all four stages: F00034, CV1 parsing, pasted F00332 and matching. Both JD stages and matching required one source-based repair; this is assisted acceptance, not unattended-quality proof. Default JD prompt v1.2 is unchanged; experimental JD prompt v1.3 uses explicit qualification inventory.

Final report:16 assessments,5 MATCH + 3 PARTIALof9 required scored units,72.22%,runtime final. Six soft skills and one preferred unit are separate. Experience and location remainunknown. All positive quotes and both education branches were checked. Seven calls cost US$0.070420540within the original US$0.40 cap, including continuation. The run is complete; no reset or new call is required.

Two specific gold-alignment questions remain (not a full-labeling redo):

| Identity | Source/evidence | Current difference | Review scope |
| --- | --- | --- | --- |
| CV1/F00332, modelU15, goldP30-U08 | Drive to learn/master techniques; CV lists completed Google certificate | ModelPARTIAL, gold MATCH | Confirm this case's learning evidence; soft skill, no percentage impact |
| CV1/F00332, modelU16, goldP30-U15 | Communicate findings as actionable recommendations; CV says cohort-results presentation | ModelPARTIAL, gold MATCH | Confirm whether the actionable qualifier is demonstrated; one technical contribution affected |

Gold and workbook remain unchanged. Proposed mappings remain pending human verification; no quality metric is published. See [source review](../../../evals/results/cp22_repair_semantic_review_20261003.json) and the [experiment record](CP22_Extraction_Repair_20261003.md).

## 3. Export and retrieval

Current reviewed bundle: `evals/gold/development_v13_reviewed_20261002_r2`, containing 1,058 A / 1,364 B / 69 C records. Rejected and held decisions are retained in sidecars, not scored. Original workbook and source data are unchanged. The 12 historical comparable top 30 development rankings were revalidated read-only. No method, model or K winner was selected.

## 4. Verification and remaining gate

- Historical full offline suite,2 October:294passed,2database cases skipped,5 SWIG warnings.
- Continuation,3 October:228 selected offline passes,0 skipped,5 known SWIG warnings; includes changed repair/readiness code and fixture/pipeline integration.
- Separate local DB selection: 5 passed, including those 2 cases. This overlaps the offline suite.
- Eight revised fixtures pass; source/cache coverage regression and export/readiness safeguards pass.
- Scoped repaired live acceptance is complete. D-050 explicitly closes CP2.2 implementation and carries broad extraction forward after CP2.3 configuration evaluation; a small-run proposal and full-guard conflict are retained without execution. Complete reference/alignment and metric conventions remain CP2.3 comparison gates.

Readiness is `evals/results/cp23_readiness_after_D050_20261003.json`. Its exit-2 status is intentional; it prevents treating a promoted record bundle as a complete benchmark. No full labeling redo is requested. The archived preflight review is [here](archive/CP22_Acceptance_before_takeover_20261002.md).
