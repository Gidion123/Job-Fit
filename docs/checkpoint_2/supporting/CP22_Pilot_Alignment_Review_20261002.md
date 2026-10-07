# CP2.2 Pilot Alignment Review — 2 October 2026

Status: **proposed alignment; awaiting human verification**. This is offline error analysis of saved run 06, not a new model run or label approval. CP2.2 remains IN PROGRESS.

## Scope and identity

CV1 × J1/F00022, frozen development; all 21 approved A records and 21 approved B records compared against all 21 model units and assessments. The saved pasted-JD identity is linked to F00022 by the exact source SHA-256, not its display ID. Reference date: 2026-09-30. Gold guideline provenance remains v0.1; it is not relabeled as v1.2 approval.

There are 20 proposed groups: 18 one-to-one, one model merge and one model split. No units are unmapped in this proposal. Complete bookkeeping does not prove semantic equivalence or extraction recall. No omission/addition is proposed for this pilot; qualifier losses and structural differences are recorded below. Every mapping remains pending alignment review.

Full source quotations, original records, CV evidence quotations, hashes and check statuses are preserved in [the JSON register](../../../evals/results/cp22_pilot_alignment_review_20261002.json). Reproduce with `env-job-fit/bin/python scripts/prepare_cp22_alignment_review.py --output <new-path.json>`; the CLI refuses to overwrite an existing artifact.

## Findings

- The model marks structured/unstructured data unknown and unresolved, whereas approved gold has a required alternative unit G2. This removes a required technical unit from the model denominator (6 versus pilot 7). Failed/null matching is a process limitation, not NO_MATCH.
- Architecture and engineering are merged despite two distinct approved units. A single model assessment cannot be compared to both as two independent correct/incorrect decisions.
- Willingness to learn and learning independently split one approved scoped unit into two. Do not duplicate its reference label in an accuracy denominator.
- Math, statistics and ML model text omit the Intermediate depth wording present in the source. Its practical interpretation must follow existing D-035/D-042; do not add a depth-label rule.
- Problem solving, scientific approach, keeping supervisors informed and communication differ from the approved evidence labels. Exact quotation validity alone does not settle their semantics. Existing approved communication precedent remains unchanged.

## Complete proposed map

Gold numbers below are J1-Uxx; model numbers are Uxx. Slashes separate multiple records, not OR-rule decisions.

| Gold IDs | Model IDs | Proposed relation | Gold importance → model | Gold label → model label/status | Diagnosis |
| --- | --- | --- | --- | --- | --- |
| J1-U01 | U01 | one_to_one | unknown → unknown | PARTIAL (done) → PARTIAL (done) | Same scoped DS employment duration; fresh-graduate exception remains unknown importance. |
| J1-U02 | U02 | one_to_one | required → required | MATCH (done) → MATCH (done) | Python requirement; compare qualification wording, not only the shared clause. |
| J1-U03 | U03 | one_to_one | required → required | MATCH (done) → MATCH (done) | SQL requirement; shared Python/SQL clause is not an automatic merge. |
| J1-U04 | U04 | one_to_one | required → required | PARTIAL (done) → PARTIAL (done) | Math: model drops Intermediate depth wording; inspect qualifier preservation without inventing a new depth label rule. |
| J1-U20 | U05 | one_to_one | required → required | MATCH (done) → MATCH (done) | Statistics: model drops Intermediate depth wording; same qualifier review as math. |
| J1-U21 | U06 | one_to_one | required → required | MATCH (done) → MATCH (done) | Machine learning: model drops Intermediate depth wording; same qualifier review as math. |
| J1-U05 | U07 | one_to_one | required → unknown | MATCH (done) → null (failed) | Gold required structured/unstructured alternative G2; model unknown simple unresolved. Gold MATCH versus model failed/null is not NO_MATCH. Main denominator changes. |
| J1-U06, J1-U07 | U08 | model_merge | preferred/preferred → preferred | NO_MATCH (done) / PARTIAL (done) → null (failed) | Model combines architecture AND engineering, unresolved. Gold has two preferred units with NO_MATCH and PARTIAL. Not one comparable label. |
| J1-U08 | U09 | one_to_one | preferred → preferred | NO_MATCH (done) → NO_MATCH (done) | GCP preferred requirement. |
| J1-U09 | U10 | one_to_one | required → required | MATCH (done) → MATCH (done) | Visualization tools required; preserve tool-versus-example distinction. |
| J1-U10 | U11 | one_to_one | preferred → preferred | MATCH (done) → MATCH (done) | Google Data Studio preferred example. |
| J1-U11 | U12 | one_to_one | required → required | MATCH (done) → NO_MATCH (done) | Problem solving: model NO_MATCH versus approved MATCH; review meaning of source evidence. |
| J1-U12 | U13 | one_to_one | required → required | NO_MATCH (done) → NO_MATCH (done) | Structured thinking: both NO_MATCH; agreement is not a new annotation approval. |
| J1-U13 | U14 | one_to_one | required → required | PARTIAL (done) → NO_MATCH (done) | Scientific approach: model NO_MATCH versus approved PARTIAL. |
| J1-U14 | U15 | one_to_one | required → required | NO_MATCH (done) → NO_MATCH (done) | Minimal supervision: both NO_MATCH. |
| J1-U15 | U16 | one_to_one | required → required | MATCH (done) → NO_MATCH (done) | Keeping supervisor informed: model NO_MATCH versus approved MATCH. |
| J1-U16 | U17 | one_to_one | required → required | NO_MATCH (done) → NO_MATCH (done) | Teamwork: both NO_MATCH. |
| J1-U17 | U18 | one_to_one | required → required | PARTIAL (done) → MATCH (done) | Communication: model MATCH versus approved PARTIAL. Preserve pilot v0.1 precedent; any clarification remains a human decision. |
| J1-U18 | U19, U20 | model_split | required → required/required | NO_MATCH (done) → NO_MATCH (done) / NO_MATCH (done) | Model splits willingness to learn and independent learning; gold keeps one scoped unit. Do not count one gold label twice. |
| J1-U19 | U21 | one_to_one | required → required | NO_MATCH (done) → NO_MATCH (done) | Initiative: both NO_MATCH. |

## Measurement limits and next checks

No extraction F1, Macro-F1, evidence accuracy or calibration metric is published. Human verification of alignment and explicit handling of split/merge/qualifiers are prerequisites. Score 91.67% is the saved model result, provisional; pilot 92.86% is a historical approved-reference calculation. Neither is recomputed to make the other agree. Soft skills remain outside the primary percentage.

J4/F00016 is in the frozen development split with 21 approved extraction rows. It has no approved B evidence rows in the current gold file. It is eligible for a scoped extraction check, not a J4 evidence-accuracy claim. The historical word blind does not override verified split/provenance. No J4 inference or source-derived rule change was performed.

Before widening inference, review the three structural mappings (structured/unstructured, architecture/engineering, learning independently). Check the four evidence disagreements against the preserved quotations. Any rule clarification stays separate from mapping confirmation; gold and scoring remain unchanged. Existing D-045 workbook priorities take precedence, and the complete pending workbook is not a prerequisite for these offline checks.

API calls/cost for this report: 0 / US$0. No workbook was opened by this script. No source, gold, prompt, model, split or configuration was changed.
