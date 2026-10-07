# CP2.3 Pipeline v1.1: Part B diagnosis

Development CV1/CV2 only. All 40 pairs without a final score are listed below. The old run and gold remain unchanged.

| CV | JD | Stage | Cause | Error / hold detail |
| --- | --- | --- | --- | --- |
| CV1 | F00366 | extraction | extraction_schema_or_mapping_failure | qualification_inventory_unsupported_mapping |
| CV1 | F00601 | matching | transport_timeout | APITimeoutError |
| CV1 | F00132 | extraction | extraction_output_limit_suspected | IncompleteStructuredResponse; output tokens [16000, 16000] of 16000 |
| CV1 | F00022 | scoring | needs_review_structure_hold | ok; 4 needs_review unit(s) |
| CV1 | F00556 | scoring | needs_review_structure_hold | ok; 1 needs_review unit(s) |
| CV1 | F00655 | extraction | looks_incomplete | looks_incomplete |
| CV1 | F00208 | extraction | extraction_output_limit_suspected | IncompleteStructuredResponse; output tokens [16000, 16000] of 16000 |
| CV1 | F00090 | extraction | extraction_output_limit_suspected | IncompleteStructuredResponse; output tokens [16000, 16000] of 16000 |
| CV1 | F00103 | extraction | extraction_output_limit_suspected | IncompleteStructuredResponse; output tokens [16000, 16000] of 16000 |
| CV1 | F00189 | extraction | extraction_output_limit_suspected | IncompleteStructuredResponse; output tokens [16000, 16000] of 16000 |
| CV1 | F00369 | source | source_hold |  |
| CV1 | F00654 | matching | matching_invalid_output_unclassified | invalid_structured_output_or_source |
| CV1 | F00309 | scoring | zero_assessable_required_denominator | ok |
| CV1 | F00310 | extraction | extraction_output_limit_suspected | IncompleteStructuredResponse; output tokens [16000, 16000] of 16000 |
| CV1 | F00055 | scoring | needs_review_structure_hold | ok; 1 needs_review unit(s) |
| CV1 | F00060 | scoring | needs_review_structure_hold | ok; 1 needs_review unit(s) |
| CV1 | F00351 | scoring | zero_assessable_required_denominator | ok |
| CV1 | F00527 | extraction | extraction_output_limit_suspected | IncompleteStructuredResponse; output tokens [16000, 16000] of 16000 |
| CV1 | F00650 | matching | transport_timeout | APITimeoutError |
| CV2 | F00018 | scoring | needs_review_structure_hold | ok; 2 needs_review unit(s) |
| CV2 | F00463 | extraction | extraction_output_limit_suspected | IncompleteStructuredResponse; output tokens [16000, 16000] of 16000 |
| CV2 | F00074 | extraction | extraction_schema_or_mapping_failure | qualification_inventory_incomplete |
| CV2 | F00029 | extraction | extraction_output_limit_suspected | IncompleteStructuredResponse; output tokens [16000, 16000] of 16000 |
| CV2 | F00176 | extraction | extraction_output_limit_suspected | IncompleteStructuredResponse; output tokens [16000, 16000] of 16000 |
| CV2 | F00559 | scoring | zero_assessable_required_denominator | ok |
| CV2 | F00629 | scoring | needs_review_structure_hold | ok; 1 needs_review unit(s) |
| CV2 | F00645 | matching | matching_invalid_output_unclassified | invalid_structured_output_or_source |
| CV2 | F00698 | extraction | extraction_output_limit_suspected | IncompleteStructuredResponse; output tokens [16000, 16000] of 16000 |
| CV2 | F00034 | matching | matching_invalid_output_unclassified | invalid_structured_output_or_source |
| CV2 | F00310 | extraction | extraction_output_limit_suspected | IncompleteStructuredResponse; output tokens [16000, 16000] of 16000 |
| CV2 | F00055 | scoring | needs_review_structure_hold | ok; 1 needs_review unit(s) |
| CV2 | F00126 | scoring | needs_review_structure_hold | ok; 1 needs_review unit(s) |
| CV2 | F00208 | extraction | extraction_output_limit_suspected | IncompleteStructuredResponse; output tokens [16000, 16000] of 16000 |
| CV2 | F00303 | scoring | needs_review_structure_hold | ok; 1 needs_review unit(s) |
| CV2 | F00556 | scoring | needs_review_structure_hold | ok; 1 needs_review unit(s) |
| CV2 | F00418 | scoring | needs_review_structure_hold | ok; 1 needs_review unit(s) |
| CV2 | F00682 | matching | matching_invalid_output_unclassified | invalid_structured_output_or_source |
| CV2 | F00436 | extraction | extraction_schema_or_mapping_failure | qualification_inventory_incomplete |
| CV2 | F00114 | scoring | needs_review_structure_hold | ok; 1 needs_review unit(s) |
| CV2 | F00343 | extraction | looks_incomplete | looks_incomplete; 1 needs_review unit(s) |

## Interpretation

- Output-limit cases reached the old 16,000-token allowance and returned `IncompleteStructuredResponse`. The old client did not save `finish_reason`, so truncation is strongly indicated, not proven per request.
- Generic invalid matching output does not retain the exact validator rule or first draft. Do not call it a code bug without a saved trace.
- `needs_review` and zero-denominator holds follow the current approved rules. Changing them needs Dion's decision.
- F00369 stays source-held. A similar posting is not its verified original source.

Machine-readable identities and token counts: [diagnosis_v1.json](../../../evals/results/cp23/pipeline_v11/diagnosis_v1.json).

## Hold-rule choice before a paid v1.1 run

H1 keeps D-006: **20/60** pairs have a final or provisional score. H2 removes `needs_review` units when at most 20% of logical required score units are unresolved, then marks the remaining score provisional: **30/60** pairs would have a score on the saved outputs. H2 changes the denominator and needs Dion's approval. It does not solve the extraction failures, source hold or other matching failures. Two flagged cases exceed 20% and remain held (CV1/F00022, CV2/F00126). `looks_incomplete` remains held.

| Pair changing under H2 | Unresolved required / required | Proposed provisional score |
| --- | ---: | ---: |
| CV1/F00556 | 0/5 (preferred or other unit unresolved) | 60.00% |
| CV1/F00055 | 1/15 | 46.43% |
| CV1/F00060 | 0/5 (preferred or other unit unresolved) | 90.00% |
| CV2/F00018 | 1/14 | 65.38% |
| CV2/F00629 | 1/25 | 47.92% |
| CV2/F00055 | 1/15 | 50.00% |
| CV2/F00303 | 1/16 | 66.67% |
| CV2/F00556 | 0/5 (preferred or other unit unresolved) | 70.00% |
| CV2/F00418 | 1/20 | 47.37% |
| CV2/F00114 | 1/17 | 37.50% |

These are counterfactual calculations, not new labels or approved scores. The [full H1/H2 receipt](../../../evals/results/cp23/pipeline_v11/hold_options_v1.json) records all 60 pair identities and the denominator change. H2 would still leave half the pairs without a score, so the v1.1 extraction and matching improvements remain necessary under either choice.
