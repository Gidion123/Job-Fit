# Development Labeling: Semantic Audit

**Date:** 2 October 2026  
**Stage:** CP2.2, development annotation audit under D-048  
**Status:** Full first semantic pass complete; findings await human decisions. No workbook edit, label approval, gold export, or tuning. CP2.2 remains **IN PROGRESS**.

## 1. Outcome and reading order

The workbook is structurally consistent, but the drafts contain evidence and extraction problems. Exact quotations and complete row coverage do not establish semantic correctness. This audit records **92 finding entries: 51 clear draft errors, 38 ambiguous cases, and 3 source/guideline limitations**. They refer to 89 distinct primary A/B/C rows; three entries concern a missing or intentionally absent unit. Some entries also identify related A units and dependent B/C rows. These counts are an audit inventory, not an error rate or model accuracy metric.

Read this summary first, then the [finding register](Development_Labeling_Semantic_Audit_Findings_20261002.md). Every entry has a sheet, job/CV/unit identity, saved Excel row, review status, current values, source quotations, problem, impact, proposed correction, and application gate. The [JSON evidence](../../../evals/results/development_labeling_semantic_audit_20261002.json) also includes full current records and dependent B/C identities. [Coverage by JD](../../../evals/results/development_labeling_semantic_audit_coverage_20261002.csv) lists all 54 jobs, including jobs with no findings.

All proposals remain unapplied. A clear error can be corrected in a draft under an existing rule, but the current STOP still requires authorization before editing the workbook. Changes to grouping, denominator, rule interpretation, or approved decisions need explicit human discussion. One entry concerns an approved pilot B row; it is a discussion item, not a reversal of that decision.

## 2. Scope and method

Active workbook: `evals/labeling/JobFit_Development_Labeling_v0.1.xlsx`. The pool remains 53 JDs / 63 pairs; the saved workbook contains 54 JDs / 67 pairs including the retained senior JD and four optional pairs. No split, pool, source, or evaluation contract was changed.

| Sheet/source | Rows actually read semantically | Method |
| --- | ---: | --- |
| JDs | 54 | Complete available JD text; compare requirements with extracted units |
| CVs | 2 | Complete CV1/CV2 bodies; employment, education, projects, courses and skill lists |
| A_Extraction | 1,069 | Every unit, quotation, importance, category, group and duration field in JD context |
| B_Evidence | 1,387 | Every pair/unit label, status and evidence against current A and the complete CV; 43 distinct section/quote combinations reused across rows |
| C_Relevance | 67 | Every ordinal judgment and reason/constraint against role, evidence and uncertainty; no match-percentage conversion |

This was a **full first pass, not sampling**. Repeated exact quotations were read once in their original CV context and checked separately against each requirement that reused them. README, Questions, QA_Log and Timing were also inspected for workflow and open-rule context. A second independent human semantic audit was not performed. Rows without findings are not newly approved and are not guaranteed error-free.

The latest brief, D-032 to D-048, guideline v1.2, workflow, master plan, CP2.2 and supporting reports, tasks T04/T05 and the review guide were read before the audit. D-048 permits complete B drafting before A approval; it does not waive the human review or dependency gate. No held-out JD semantics, CV3/CV4/CV5 contents, or test labels were used.

## 3. Saved-version reconciliation

The initial snapshot was captured at **08:46:09 WIB**, with an Excel lock present:

`8f9f5575a97764152e71df3013fdc5c4503f3a7e5817a936703ccdbf6c9fb01f`

The file was saved during the audit. A second disk snapshot was captured at **09:13:08 WIB**, after the lock was absent; its last modification was **08:54:28 WIB**:

`8be2b05635cc4175f71e2a38cd39dfaa9f17f2f4e4d78d80b20b57516fe733ad`

Only two cell values changed: leading spaces were removed from `draft_note` in B row 330 (CV1/F00332/P30-U01) and B row 1254 (CV2/F00798/P51-U38). A's freeze pane moved from A2 to A18; saved dropdowns remain valid. The two notes were re-read. Source text, A units/fingerprints, evidence/relevance labels, review actions, approval statuses and counts did not change. The full semantic pass therefore remains applicable to the latest saved version. The UI and whitespace changes were preserved, not repaired to match the initial snapshot.

The audit wrote no workbook bytes. Unsaved Excel edits were never visible to the audit. Future edits or sorts require a fresh identity-based comparison; Excel row numbers alone are insufficient.

| Sheet | Total | Approved on latest saved version | Pending |
| --- | ---: | ---: | ---: |
| A_Extraction | 1,069 | 39 | 1,030 |
| B_Evidence | 1,387 | 21 | 1,366 |
| C_Relevance | 67 | 3 | 64 |

## 4. Findings by sheet

| Sheet | Clear errors | Ambiguous | Source/guideline limitations |
| --- | ---: | ---: | ---: |
| A_Extraction | 19 | 10 | 3 |
| B_Evidence | 30 | 28 | 0 |
| C_Relevance | 2 | 0 | 0 |
| Total | 51 | 38 | 3 |

### 4.1 Clear errors: proposed draft corrections

High-impact examples below are fully documented in the register. They are not permission to modify labels or the denominator.

| Finding | Location | Problem and proposed correction |
| --- | --- | --- |
| AUD-023, AUD-028 | A F00075 automation; F00188 Power BI | Repeated qualification without a distinct qualifier. Propose one unit with both source references; obtain permission before merging and recheck B/C. |
| AUD-039, AUD-062 | A F00310 NoSQL; F00663 processing tools | Explicit AND becomes OR. Preserve the conjunction under D-039; any split needs a dependency review and authorization. |
| AUD-080 | A F00208 training alternatives | Statistics/causal inference/program evaluation are OR training alternatives, but split without a group and stripped of the training qualifier. Discuss the D-040 boundary before changing structure. |
| AUD-013, AUD-022, AUD-027, AUD-067 | A debugging, development workflows, Agile | Concrete technical practice labeled soft_skill. Propose categories that follow D-032; do not silently change scoring membership. |
| AUD-026, AUD-048 | A F00117 location; F00412 architecture | Jakarta becomes South Jakarta; model-agnostic becomes agent-agnostic. Restore source meaning. |
| AUD-002 | B CV2/F00103/D1-U28 | Python report automation does not show a data-quality framework. Do not preserve PARTIAL merely because the preparation validator expects it. |
| AUD-025 | B CV2/F00114/J5-U08 | Embedding use does not establish embedding-model selection. Propose PARTIAL for related use. |
| AUD-058, AUD-070 to AUD-072 | B precision/recall, prompt and retrieval evaluation | Answer-accuracy checks are not all these distinct metrics/activities. Credit only the actual evaluation scope. |
| AUD-020, AUD-037, AUD-038, AUD-063 | B CV2 messy data, ingestion, wrangling, preprocessing | Report automation alone does not demonstrate these named operations. Full MATCH lacks the retained qualifier. |
| AUD-029 | B CV1/F00208/P23-U36 | NO_MATCH overlooks the university teaching-assistant role for the higher-education branch. Review the source-supported branch without inferring nonprofit work. |
| AUD-051, AUD-053 | B generic AI-service integration | Drafts add a direct low-level API requirement where the source permits an AI service. Credit the demonstrated OpenAI embedding service without claiming GPT or direct request handling. D2's explicit “not wrappers only” condition remains distinct. |
| AUD-010 | C CV1/F00074 | Constraint note invents leadership duration; the JD asks for production software/LLM duration. Correct the explanation; relevance 1 is not automatically changed. |
| AUD-057 | C CV2/F00438 | Main reason claims dashboard work while B only has a listed Looker Studio skill. Correct the claim, then reassess relevance qualitatively. |

Some errors can inflate evidence; others under-credit it. The audit does not uniformly lower labels. Quotation problems may be resolved by selecting better existing CV sentences rather than automatically treating the candidate as lacking evidence.

### 4.2 Decisions still needed

Existing questions are referenced instead of requesting already-settled approvals. Degree or tool equivalence must be applied to the exact wording of each JD, not turned into blanket equivalence.

| Decision group | Findings / existing questions | Decision needed |
| --- | --- | --- |
| Umbrella and components | AUD-005/006; B1-Q3, QX17 | Is component-built RAG independently assessable beyond its component rows? Do not count a repeated requirement twice. |
| Nested duration | AUD-008/009/032; B1-Q4 | Preserve both minima (2 production + 1 LLM; 5 ML/DS + 2 leadership; 8 overall + 3 applied/production) through a split or an explicit compound interpretation. A single numeric field stores only the outer minimum. |
| Importance and eligibility qualifiers | AUD-001/016/075; B1-Q2/Q5 | Interpret “menjadi prioritas”, “around” and focus clauses from actual text, without using headings as the sole cue. |
| Explicit cardinality and area-list exception | AUD-012/033/080 | How does “one or more” interact with D-040? Does a training list fall under the experience-area exception? Preserve AND/OR and qualifier meaning until decided. |
| Related degree / same-field duration | AUD-003/073/074; B2-Q1/Q2, QX16 | Which relevant CV2 activities qualify as DS employment, and can their duration be bounded? Do not assign the entire marketing tenure to AI/ML/DS. CV1's Statistics degree needs source-specific related-field interpretation. |
| Language evidence | AUD-082 to AUD-092; QX13 | Decide the evidence convention once for self-reported native/professional language and TOEFL, while retaining each JD's modalities. Intermediate English is not automatically professional fluency. |
| Tool, model and activity scope | AUD-004/007/035/052/055/059/061/064/069 | Review FAISS “or similar”, wrapper/service integration, independent ownership, automation builders, F1 versus precision/recall, data modeling and DistilBERT versus the source's LLM scope. These are source-specific judgments, not a reason to invent requirements. |
| Approved pilot precedent | AUD-017/043 | Discuss communication quality and independent-learning inferences in relation to the approved v0.1 pilot cases. Preserve approved decisions; do not retroactively apply a new convention without permission. |

The mixed-category bonus in D1 remains the existing B1-Q1 question. The F00020 mentoring-role question remains B2-Q6; current C=0 is consistent with reading the actual teaching role as outside the automatic target families. No snapshot role family was changed. B2-Q1 names CV2/F00036, but that pair is not in this active workbook; the general same-field question is relevant to active cases, not a reason to add that pair.

### 4.3 Source/guideline limitations

- **AUD-046, F00364:** responsibilities without qualifications; zero A/B is intentional. C is provisional with limited qualification information. Do not invent requirements.
- **AUD-045, F00369:** source ends at “A portfolio of pro”. Available complete clauses were audited; missing source content cannot be certified or reconstructed.
- **AUD-024, F00066:** willingness to take a project-based PKWT contract is explicit but absent from A. The guideline excludes contract length and the approved constraint contract does not clearly cover contract willingness. Discuss scope or a nonscored note; do not create a new scoring constraint. This does not block the D-045 priority subset.

## 5. Chronology and uncertainty

The development combined manifest explicitly records **analysis_date = 2026-09-30**. This audit used that reference rather than the computer date. CV1's analyst internship covers four inclusive calendar months; its separate regression teaching role covers five. The generous nonoverlapping employment upper bound is nine months, still below a one-year employment minimum. Whether the teaching role is the same field is source-specific; this audit does not establish a new exclusion rule for teaching.

CV2's complete dated employment is 26 marketing-executive months plus 39 digital-marketing-analyst months, **65 months in total**. That bounds an eight- or ten-year minimum even under the most generous interpretation. It does not prove 39 or 65 months of Python, AI, DS, production LLMs, or leadership. For shorter specialized minima, use actual duties and eligible dates; an unresolved same-field period can require `needs_clarification`. Project dates, bootcamp attendance and academic work never become employment years. A single project date does not establish its start or total eligible duration.

The existing pipeline issues remain open: explicit configured evaluation dates must reach experience calculations, and date representations must retain original precision. No schema, date rule, source metadata or constraint logic was changed in this audit.

## 6. Technical verification and its limits

The private read-only helper ran with `env-job-fit/bin/python`. Its final result passed **27 mechanical checks**, including exact 54-JD corpus/source mapping, all 56 Markdown source bodies, original CV1/CV2 bodies and hashes, all 1,069 JD quotes, B quote rules, unique identities, complete A-to-B pair coverage, development isolation, frozen pool/split inventory, source hashes, preserved rows, current A fingerprints, review metadata, C range/reasons, 40 designated C reviews, saved dropdowns, and absence of saved Excel error cells. **No current A fingerprint differs from the preparation manifest**, so no B is already stale from an A edit in the saved version. Proposed A corrections would make the listed B/C dependencies require rechecking.

Both historical validators were read, not run. Their entry points write historical QA files and impose preparation-snapshot assumptions. Some “semantic spot checks” merely assert expected draft labels, including AUD-002's questionable PARTIAL. They cannot establish semantic correctness or justify restoring human edits. Their source and historical outputs remain unchanged.

No pytest/database suite, paid API call, parser/matcher experiment, native Excel interaction, fresh sheet rendering, gold export or tuning ran. Mechanical PASS means only the stated mechanical checks passed. No label acceptance rate, semantic accuracy, model comparison or new experiment metric is claimed.

## 7. Efficient next review and STOP

First read the summary and resolve the priority rule questions, about **20–30 minutes**. Then authorize a concrete correction list. Only after authorization, with Excel closed, should draft changes be applied and dependencies rechecked. Approved rows remain protected. Review order stays:

1. A: D1/F00103, D2/F00074, D3/F00012 — 84 units, of which **82 remain pending**.
2. B: CV1×D1 and CV2×D2 — **62 pending rows**, after the relevant A decisions.
3. C: **40 pending rows with gold_review=yes**, judged independently after affected evidence/constraint clarification.

The priority-specific findings are AUD-001/003/004/005/006/007/008/009/075/090. Other drafts remain available and optional. The error in AUD-010 is on an optional C pair; AUD-057 is on a designated C pair. Do not make every optional draft or source question mandatory before the project proceeds.

Using D-045's planning averages of 1.2 minutes per A/B row and 2.4 minutes per C row, the remaining priority rows imply about **4.5 hours before clarification and QA**; allow roughly **5 hours** with QA, spread over **2–3 sessions at 2–3 hours/day**. This is an estimate based on the actual row count, not measured labeling time or an increased labeling target. No Timing entries were filled by this audit.

**STOP:** Await the annotator's decisions and authorization. Do not edit labels, export gold/silver, tune CP2.3, or rebuild split/pool/embeddings. CP2.2 remains IN PROGRESS until its parser, extraction, matching and paste-JD acceptance checklist is met.

## 8. Cost and files

This audit: **0 project API calls; US$0**. Read-only local ledger confirmation: **88 records; exact noncached total US$0.01226822**. No model availability lookup or budget-changing action was needed.

New repository evidence: this report, the finding register, audit JSON and per-JD coverage CSV linked above. The CP2.2 stage/supporting reports, repository structure and private current handoff are updated with this STOP. Workbook, pilot, archived workbooks, manifests, source sheets, labels, split, pool, ledger, guideline, scoring and database were not changed by the audit. No git command or deletion was performed. Audit-only snapshots/helpers and intermediate output remain private under `_private_not_for_github/notes/artifact_work/semantic_audit_20261002/`.
