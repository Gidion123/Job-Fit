# JobFit CP1 Research Audit

**26 September 2026. Scope: offline audit of the project up to EDA, measured revisions, reproduction, document consistency and PPT readiness.** This audit did not collect job postings, use a paid API, create gold labels, or change the product scope.

## 1. Conclusion and project position

PRE-CHECKPOINT 0 stays **FROZEN: GO WITH LIMITATION**, with a user pilot of n=1. The CP1.3 to CP1.6 implementation uses one notebook. The next step is **CP1.7: PPT and mentoring**. The findings support the evidence-grounded matching direction, but they do not yet prove model performance, or that every candidate in the pool meets entry-level qualifications.

The Canonical stays the design reference. The root Playbook got a note that maps its artifacts, and its goals and acceptance criteria still apply. The Context copy and the old benchmark handoff are kept as history. `CP1_Current_Handoff.md` is now the latest operational progress.

## 2. Scope of the checks

- Read the source of truth, notebook, cleaning/transform/skill/dedup modules, collection scripts, tests, data contract, reports and project logs.
- Checked the structure/parsing of all project JSON, JSONL, CSV, notebook, Python, Markdown, YAML and text files. For DOCX documents, the XML content was checked. There were no parse failures in the initial audit inventory.
- Verified 460 raw/response+metadata files against the snapshot manifest, and the checksums of 225 automatic response/metadata pairs.
- Rebuilt the corpus **in a temporary directory** from raw, using the frozen dedup decisions. The original raw data and snapshot were not changed.
- Ran all 1,314 slots through the pipeline and the reconciliation, and read the evidence for the cases that triggered changes. This is **not a labeled gold set for all 632 JDs**, and it does not verify that every application link is still active.
- Ran the notebook from a clean kernel, checked the outputs and the 14 charts visually, and added tests for the confirmed failure cases.
- Historical external references are not claimed to be re-verified live. Competitor observation claims that are not verified must still show their status in the PPT.

## 3. Findings and revisions

| Area | Finding before the audit | Revision and evidence |
| --- | --- | --- |
| Reproduction | The notebook checked raw hashes but read interim files that could change | Reads records/decisions from the frozen snapshot; an extra manifest for 5 derived files; the code hash, notebook code hash and runtime are added to the summary |
| Location | The query country could become the job country; TikTok Los Angeles `US` was in the Indonesia group | The country field/location text comes first; the query is not a fallback; a country without evidence is UNKNOWN; EDA groups are mutually exclusive |
| Date | The relative text of the canonical record was tied to the cluster's first_seen | Uses the timestamp of the same record and stores the reference record/time; 20 dates without their own timestamp become UNKNOWN |
| Experience | `0-4 years` was not captured; the highest range could take its max from another mention; 5+ got a false max | Supports a minimum of 0; takes the min/max pair from the same mention; max only for an explicit range; the regex does not take 40 from 140 |
| Experience interpretation | The highest mention was treated as a required requirement; the pool was treated as qualified | Renamed to experience signal/early-career pool; preferred, alternative, multi-level and negation stay as baseline limits and review candidates |
| Language | A JD mostly in Japanese could be labeled English because of a few Latin words | Label `other_script`/UNKNOWN for cases dominated by another script or with no signal; still heuristic |
| Education/provenance | Education was counted at the end of the EDA but not stored in the features; the raw path was missing | The education list and provenance are included in the JSONL/CSV; experience quotes are still available |
| Denominator | 49 non-target AI jobs were described as if the denominator of 910 were all AI titles | 49 out of **463 AI titles** in 910 clusters; 29 EDA candidates; explicit denominators in the summary |
| Regional comparison | The 1,500-4,000 range was described as “length matched” | Added direct standardization by role × length bin, common support and weights; the raw chart is kept; no causality/significance claims |
| Product conclusion | A senior title was treated as a rejection, co-mention required a graph, a cross-section was treated as a trend | The title is only a signal; the gate needs requirement/evidence; ontology v1 stays light, the graph is optional; no time-trend claim |
| Review | Location/dedup/experience conflicts were not available as a queue | Flags and a review queue; preference/alternative keywords are broad, not confirmed errors |
| Historical collection script | The free cap counted requests even though num_pages can use several units | The unit budget is checked before each request; bandwidth quota is not used as request quota; the string `false` is not a free plan; free-only pilot; all verified offline |
| Dedup efficiency | The canonical choice was recomputed for every record | Computed once; the rebuild result is identical to the snapshot |

The Assistant Director rule stays non-target and now has an explicit test. The experience max rule of 5 years versus 2 years is kept. Multi-level ambiguity is not yet solved as requirement extraction; CP2 must measure it.

## 4. Number reconciliation

| Measure | Before | After |
| --- | ---: | ---: |
| Slots / final clusters / EDA candidates | 1,314 / 910 / 632 | unchanged |
| Indonesia target | 176 | 175 |
| Foreign comparison target | 195 | 186 |
| Remote query target | 57 | 57 |
| UNKNOWN country target | 0 | 10 |
| Indonesia early-career pool | 49/176 | **49/175** |
| Pool without a level word | 37/49 | 37/49 |
| Indonesia 3+ experience signal | 69 | 69 |
| Indonesia experience not detected | 58 | 57 |
| Title without level, with 3+ | 128/405 | 128/405 |
| Provider / relative / unknown date (910) | 275 / 377 / 258 | 275 / 357 / 278 |
| Regression tests | 11 | see the final verification results below |

The pool size is the same, but its members changed. **F00157** (TikTok intern, Los Angeles) left the pool. **F00019** (Junior Data Scientist, “0-4 years of relevant experience”) joined after zero years was recognized. Bachelor/S1 is now 28/49 and master/S2 is 6/49; the full data is in the summary. These are not 49 jobs that already pass on education/skills/work permission.

## 5. Indonesia versus foreign sensitivity test

The old method only selected lengths of 1,500-4,000 characters. The additional method uses role × five length bins, at least 3 JDs in both regions, and combined composition weights on the 12 cells that both regions support.

Common support: **151/175 Indonesia and 172/186 foreign**. Software AI does not have enough cells and is not represented in the adjusted estimate. Difference, Indonesia minus foreign:

| Skill mentioned | Adjusted difference, percentage points |
| --- | ---: |
| SQL | +8.8 |
| Machine learning | -23.7 |
| Statistics | -11.4 |
| LLM | -2.1 |
| RAG | +3.2 |

The SQL/ML pattern is still visible, but the LLM gap gets smaller and RAG changes direction compared with range restriction alone. The conclusion “all GenAI in Indonesia is lower” is not stably supported. Length bins do not match exact length. Publisher, employer, language, seniority, query and possible residual duplicates are not controlled yet. There is no causal inference or population significance.

## 6. Readiness by Playbook stage

| Stage | Current evidence | Limits / follow-up |
| --- | --- | --- |
| PRE-CP0 | Canonical and PRE report | Frozen GO WITH LIMITATION, limited user validation |
| CP1.1 dataset | Benchmark, batch audits, inventory, raw/snapshot | JSearch provisional, Techmap deferred; dedup is still v0 (the 3 UNSURE pairs are flagged for re-check) |
| CP1.2 methodology/research | Canonical, PRE, related-work report | Use the proposed architecture and planned metrics, not evaluation results |
| CP1.3 cleaning | Notebook section 2, before/after, assertions | Masking is not full anonymization; full is a proxy |
| CP1.4 transform | Section 3, versions, schema/lineage and the embedding-derived table design | Embedding/extractor models are not implemented or measured yet |
| CP1.5 EDA | Section 4, 14 figures, role/length sensitivity | Query-based sample, rule-based v0 labels, small groups |
| CP1.6 insight | Section 5, summary JSON, insights | Hypotheses to be tested in CP2; does not expand the frozen scope |
| CP1.7 PPT | Data and presentation material ready to choose from | PPT, LMS upload and mentor feedback not done yet |

## 7. Kept on purpose

Raw data, screenshots, batch plans, resume manifests, benchmark/CS reports, old audits, dedup decisions, snapshots, Context documents, the PRE report DOCX and the research `_archive` are all kept. Some old numbers are superseded, but these files explain the provenance and the reasons behind decisions. Deleting them would make auditing harder.

Cleanup was limited to Python caches, the pytest cache and `.DS_Store`. The list of actions and the final verification are recorded below. No data or evidence files were deleted.

**Folder cleanup note, 27 September 2026.** Documents outside the project folder were reorganized. Canonical, Playbook, Research and PRE-CP0 (md + DOCX) are now in `../01_Reference_Documents/`. Identical duplicates (checked with checksums) and old versions whose content is fully covered by the latest version were deleted. Unique old versions of Research were moved to `../_archive/`. The benchmark-stage chat handoff and the early "Tahapan Pengerjaan" (work stages) plan were deleted because Canonical, Playbook, and `CP1_Current_Handoff.md` replace them. No data, evidence, snapshots, batch plans, notebooks or code were deleted.

## 8. Final verification results

- **24 tests passed, 0 failed** (`python -m pytest -q tests`). This includes cases for rules, location, dates, standardization, output reconciliation and the quota guard, mocked without network.
- The notebook was run from a clean kernel: **30 code cells in order, 0 errors**. The final version stores outputs that match the code and the summary.
- **14 PNGs** were regenerated and checked visually, including the population labels on the work mode chart. No posting-age or junior-versus-senior figure was added.
- **460 raw files** and **5 frozen derived files** passed the hash check; **225 response metadata files** match the response checksums. The records/canonical/review rebuild is identical; the only progress difference is the creation timestamp.
- The JSON/JSONL/CSV/notebook/Python/document structures that were read have no parse errors. The file counts by type were recorded before the cleanup.
- The summary includes runtime, input/code/notebook-code hashes, denominators and the adjusted tables. All processed files come from the notebook.
- **37 cache/system files** were deleted from `__pycache__` folders, `.pytest_cache` and `.DS_Store` files. No data, evidence, notebooks, source documents or screenshots were deleted.
- Machine-readable details and the list of cleaned files: `evidence/checkpoint_1/corpus_collection/CP1_Research_Audit_Verification.json`.

Limits of these results: successful runs and tests show that the pipeline is consistent on this snapshot. They do not show label accuracy or model superiority. The gold set, active-link validation, retrieval/ranking evaluation and deployment are not done yet.

## 9. Check of my Run All output

My Run All output on Python 3.11.16 was checked: 30 cells in order, 0 errors, and the code/modules still match the summary hashes. The five processed files other than the summary are identical to the audit baseline. The summary only changed in the Python version metadata. Skill numerators/denominators per role, the GenAI bundle, and pool membership were checked again against the JSONL. The main numbers and conclusions still hold.

The introduction sentences were made clearer: four EDA location groups (including UNKNOWN), the JD length threshold as a proxy, the pool as an experience signal, and GenAI co-mention as a hypothesis with no personal gap claim. Only Markdown changed, so my existing output is kept and there is no need to Run All again.

## 10. English version and re-run (27 September 2026)

All documentation was translated to English, and the notebook got short code comments plus English chart labels. After that, the notebook was run again from a clean kernel (Python 3.11.15, 0 errors, 24 of 24 tests passed). Results:

- The five processed data files (`jobs_clean.jsonl`, `jobs_clean_meta.csv`, `jobs_features.jsonl`, `jobs_features.csv`, `CP1_human_review_queue.jsonl`) are byte-identical to the CP1 version (same SHA-256).
- Every number in `CP1_research_summary.json` is the same. Only display labels used as keys were translated (for example the funnel stages, "tidak jelas" to "unclear", and "Luar negeri" to "Foreign"), plus the runtime versions and code hashes.
- The 14 figures were regenerated with English titles and labels. Their numbers did not change.

