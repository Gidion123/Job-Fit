# CP2.2 pipeline implementation contract

2 October 2026. Implementation scope authorized by the user; no labeling or scoring rule change.

- Reuse the existing requirement, assessment, score and constraint schemas/functions. Do not use pending workbook labels as gold or silently resolve open equivalence/grouping questions.
- CV dates retain their exact source text. Add optional partial-date fields alongside the existing full `start`/`end` fields. Year-month stores no day; year-only stores no month/day. Existing full-date inputs remain valid. Calendar months still count inclusively, with overlapping months counted once. Year-only and unrecognized dates remain unbounded. This is an additive serialization change, versioned separately from the unchanged scoring rule.
- `analysis_date` is required application configuration, recorded in results/cache keys. CV metadata cannot override it. No default to computer date.
- Parsed employment is not automatically relevant experience for every skill. Relevant dated periods require explicit source-grounded scope supplied by the caller; whole employment history may only establish an upper bound when the caller confirms completeness. Neither a title nor project/course time supplies professional experience.
- Missing or invalid model output is a processing failure, never automatically NO_MATCH. One repair maximum per stage covers schema, IDs and source-quote validation. Required failed units remain in the denominator and hold the score using the existing scorer.
- JD cache is versioned by content, model, schema, prompt, preprocessing and guideline. CV parsing/matching and pasted-JD state remain in memory for the session. No uploaded original, CV text or evidence is written to the usage ledger.
- Prompt data is untrusted. Only system instructions define the task. Provider privacy flags and existing budget/ledger apply to any future real call. Fake responses test plumbing, not model semantic quality.
- Acceptance evidence distinguishes offline execution from live model runs, and automated fixture checks from human gold review. Native UI/API deployment and CP2.3 tuning are outside this implementation.

PDF extraction uses position-aware blocks for a simple one- or two-column layout. Every PDF requires a parsing preview; complex layouts are not claimed supported. A scan/no-text page produces a clear limitation and no model call. References: [PyMuPDF text recipes](https://pymupdf.readthedocs.io/en/latest/recipes-text.html), [python-docx documents](https://python-docx.readthedocs.io/en/latest/user/documents.html).

## Verified continuation

See [implementation evidence](CP22_Pipeline_Implementation_20261002.md):161tests pass with database; live synthetic report produced; workbook unchanged. JD v1.1 resolves an instruction conflict using already approved rules, preserving v1. Safe feedback and bounded previous output support one repair. Empty extraction despite an explicit populated requirement section fails; this does not prove completeness of a nonempty result.

Schema/quote validity remains distinct from semantic correctness. Latest provisional coverage differs from approved pilot gold; no annotation/scoring rule was changed to hide that. Full corpus extraction is not run; held-out processing is deferred. Local tests do not establish model accuracy or human fixture approval.


## D-049 coordinated runtime adoption (2 October 2026)

Current runtime selects annotation guideline v1.3, JD prompt v1.2 and evidence prompt v1.1 explicitly from pipeline configuration. Historical configuration is archived and old prompts/results/gold retain original versions. New results carry versions and source hashes; cache identities isolate incompatible versions. No historical gold is implicitly compatible with v1.3 for metrics.

Unresolved and/or/cardinality remains a composite with existing needs_review support; no new cardinality schema or silent AND/OR assumption is introduced. A structural review flag at any importance level holds the final percentage and marks the denominator pending review. Raw identified counts are diagnostic, not a validated scoring denominator. Existing requirement schema, scoring formula and constraint semantics remain unchanged. Processing failure never becomes NO_MATCH. Human review still controls structural resolution and dependent B/C approval.

The final selected offline suite 213 passes; no live model run under v1.3 has occurred. See the [audit continuation](CP22_Pipeline_Audit_20261002.md) and adoption evidence. Historical161database and v1.2live results above remain historical evidence, not v1.3 verification.
