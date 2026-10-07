# JobFit Annotation Guideline

**Version:** v1.3 · **Date:** 2 October 2026 · **Stage:** CP2 development labeling
**Scope:** Current manual labeling guidance. Pipeline adoption requires coordinated prompt, version, validation, and cache checks; documentation publication alone does not migrate the implementation.
**Status:** Current review guidance, incorporating Dion's four requested rules (D-049). The previous [v1.2 guideline](annotation_guideline_v1.md) remains unchanged as the current runtime input and historical reference. Existing labels retain their actual guideline versions until individually re-reviewed. No workbook, approved gold, scoring code, or prompt was migrated by this documentation update.

**Read first:** A3 (importance), A4/A4a (AND/OR and umbrella overlap), A5a (categories), and the migration checklist below. These rules preserve source meaning; they are not permission to approve a batch automatically.

---

## 0. Label record fields (all label types)

| Field | Meaning |
| --- | --- |
| `guideline_version` | `v1.3` only after the row is actually reviewed under this revision; retain prior versions otherwise |
| `label_source` | `model_draft` (drafted by a language model, then reviewed) or `annotator` (created by the annotator). It stays `model_draft` after the annotator edits the row |
| `review_status` | `pending` (not decided yet) or `approved` (decided by the annotator) |
| `review_action` | Filled by the annotator: `accepted`, `edited`, `rejected`, or `added` (D-038) |
| `draft_note` | Reasoning attached to a model draft |
| `review_note` | The annotator's note: always for `edited` or `rejected`, and for hard cases |
| `reviewed_by`, `reviewed_at` | Added when the workbook is converted to gold files |

Only approved, non-rejected, valid labels are eligible for ground truth (D-016); dependent rows must also pass recheck before export. There is one human annotator, so no inter-annotator agreement is reported. Report acceptance rate and blind agreement only where blind labeling actually occurred. Current development review is draft-first under D-047; do not call it blind.

---

## Part A. Requirement units (from a job description)

### A1. What is a requirement unit?

A requirement unit is one thing the candidate must have or show, written so it can be checked **on its own without losing meaning**. Take units only from the requirement parts of the JD (Requirements, Qualifications, Kualifikasi, What we're looking for, Character, and similar).

### A2. What is not a requirement unit?

- **Responsibilities** ("You will build...", "Tanggung jawab", "What you'll do"): not units, unless the JD says the candidate must already have it.
- Company description, benefits, salary, contract length.

### A3. Importance

| Cue | Importance |
| --- | --- |
| "must", "required", "mandatory", "at least", "minimal", "wajib", "harus", or listed under a requirement heading without a softening word | `required` |
| "a plus", "nice to have", "preferred", "advantage", "nilai tambah", "diutamakan", "lebih disukai", or "prioritas" when it explicitly gives preference to candidates with the qualification | `preferred` |
| Source genuinely leaves obligation ambiguous or gives conflicting signals not resolved by A7/D-042 | `unknown`; record the exact ambiguity |

**Rule 2: use the local clause and its section together.** A qualification without a softener is `required`. A softener applies only to the requirement it modifies, not to every other item in the bullet. For example, "Python required; Docker preferred" gives required Python and preferred Docker. "Prioritas bagi kandidat dengan AWS" is preferred; "able to manage priorities" is not an importance cue. An explicit "must" remains meaningful even without a section heading. A responsibilities heading alone never makes an activity a qualification.

Do not use `unknown` merely because the CV lacks evidence, the skill is difficult, or a named criterion is subjective. "Leading university" is preserved in the education unit; its undefined standard is an assessment limitation, not permission to delete the qualifier or invent a university ranking. Keep unresolved assessment visible rather than claiming full evidence coverage. D-042 still governs explicit Required items and contradictory experience statements.

### A4. How to split a list (D-034, D-039, D-049)

**The conjunction decides the number of units.** Words like strong, good, familiar, or working knowledge describe the level only, which v1 does not measure (D-035).

| Wording in the JD | Units |
| --- | --- |
| "A **and** B" / "A **dan** B" | Split; each is its own unit |
| "A **or** B" / "A **atau** B" | One unit with alternatives (`group_id`); any one is enough |
| "**including / termasuk**" + a list joined by AND | Split, like any AND list |
| "**such as / seperti / e.g.**" + "or / atau", or a list ending with "**etc / atau sejenisnya / lainnya**" | One unit with alternatives; any one item, or an equivalent tool, is enough |
| A level word (familiar with, working knowledge of, good, strong) + a list | Follow the conjunction of the list: AND splits, OR gives one unit |
| **Exception (D-040):** a list of **areas of experience** ("experience building AI applications in areas such as NLP, Computer Vision, or Generative AI"; "pengalaman di bidang A, B, atau C") | Split; each area is its own required unit, even with "such as ... or". Lists of tools, frameworks, languages, and platforms still follow the rows above |
| "3 years of experience using Python" | One **qualified unit** (skill and duration stay together, `min_years = 3`) |
| The same requirement written twice | One unit; keep both source quotes |
| Unclear grouping or cardinality | Preserve one composite with the original conjunction and qualifiers; note what is unresolved. Do not invent independent AND units. Importance follows A3 separately |
| "**and/or**" | Keep one composite with the original conjunction. Do not create independent AND requirements. If the source unambiguously permits any one option, one alternative group is possible; if its minimum selection count or grouping cannot be represented faithfully, retain the composite for review rather than forcing AND or OR |

Examples: "Strong knowledge of AI technologies, including machine learning, natural language processing, and computer vision" gives three units (AND). "Familiarity with REST APIs, Git, Docker, and CI/CD practices" gives four units (AND). "Experience with frameworks such as PyTorch, TensorFlow, or XGBoost" gives one unit with alternatives (such as ... or).

### A4a. Umbrella and children; unsupported cardinality (Rules 1 and 4)

**Rule 1: no duplicate parent contribution.** When an umbrella statement adds no independently assessable obligation beyond all of its extracted children, represent the obligation through the children only. Keep the parent wording in their source quotes/context. Do not add another scored parent unit or change a genuinely required parent to preferred just to remove it from the denominator.

- "Knowledge of AI technologies, including ML, NLP, and computer vision": extract the three knowledge units; do not also score a generic "AI technologies" unit with the same meaning.
- Do not assume that detecting component names covers the parent. "Build and evaluate an end-to-end RAG system" is not exhausted by "embeddings" and "vector search". Integration/evaluation may be a distinct obligation. Preserve the additional scope in the appropriate unit and flag uncertain overlap; do not invent unmentioned components or give automatic RAG MATCH from component evidence.
- Duration, production setting, integration, evaluation, and other qualifiers must not disappear when a parent is reduced. If it is unclear whether children cover the full parent, retain the source-backed composite for review; do not count both an unresolved parent and overlapping children as independent required obligations in a final score.
- In an existing workbook, the reviewer can reject an exactly redundant parent with a note pointing to the retained children. Keep its ID/history; recheck dependent B and C. Do not delete or automatically reject an approved row.

**Rule 4: preserve logical meaning before counting.** `AND` requires all independent children, `OR` offers alternatives, and `and/or` must not silently become an all-children obligation. Preserve shared qualifiers when splitting an explicit AND. A qualified unit such as "3 years using Python" stays together.

The current schema has simple, qualified, and alternative-group units but no general cardinality field (for example, "at least two of A/B/C"). Keep such a clause as one composite in annotation, with its exact selection count and conjunction, rather than inventing multiple required units or assuming best-branch OR. An unresolved composite is a representation requiring review, not proof that one denominator contribution is already valid. Pipeline adoption must preserve a review/hold signal where its semantics cannot yet be evaluated; never silently exclude it to increase the percentage.

D-041's approved mathematical/statistical/ML pilot split remains historical v1.2 evidence, not the default for new v1.3 annotations. Re-review is needed before using that case as v1.3 gold or a prompt precedent. This revision replaces the old fallback "unclear means split" and the open general and/or rule. It does **not** silently repeal D-040's separate, unusual experience-area exception for pure "such as ... or" lists; flag that exception when encountered. D-040 must not be extended to override this explicit and/or rule.

### A5. Fields for each unit

| Field | Rule |
| --- | --- |
| `unit_text` | Short, normalized statement in English |
| `source_quote` | The exact JD words, copied (not retyped, not paraphrased) |
| `importance` | A3 |
| `category` | `skill_tool`, `knowledge_area`, `experience_duration`, `education`, `language`, `certification`, `soft_skill`, `location`, `work_authorization`, `other` (A6) |
| `group_id` | Same id for all options of one alternative group (`G1`, `G2`, ...); empty otherwise |
| `min_years` | Only for qualified experience units; the number written in the JD |
| `draft_note` / `review_note` | Anything unclear (draft reasoning or the annotator's note) |

### A5a. Technology versus knowledge (Rule 3)

Classify what the candidate is asked to demonstrate, not a keyword in isolation.

| Requirement | Category | Reason |
| --- | --- | --- |
| Python, SQL, Docker, AWS, PyTorch, FAISS, LangChain | `skill_tool` | Named language, tool, platform, library, or framework |
| Machine learning, NLP, statistics, RAG methodology, CI/CD practices, REST API concepts | `knowledge_area` | Domain, concept, method, or practice |
| "Knowledge of Docker" | `skill_tool` | The object is still a named tool; the word knowledge does not change it |
| "3 years using Python" | `experience_duration` | Existing qualified-duration rule takes precedence; do not split away Python |
| Degree in computer science | `education` | Educational credential, not a separate knowledge unit |
| AWS certification | `certification` | Credential, not just familiarity with AWS |

Retain `language`, `soft_skill`, `location`, `work_authorization`, and `other` for their existing purposes. Rule 3 distinguishes the two technical categories; it does not replace the entire taxonomy. A named methodology is not automatically a tool. Do not infer equivalence or a MATCH label from its category.

### A6. Categories that do not enter the match % (D-032, D-033)

| Category | What it covers | How it is used |
| --- | --- | --- |
| `soft_skill` | A personal trait or general behavior: teamwork, initiative, general communication, problem solving, working under pressure, willingness to learn | Extracted and labeled, **not** in the match %. Shown under the score ("soft skills asked: y, with evidence: x") |
| `location` | Where the person must work or live: onsite city, commute, relocation, current location | Extracted, **not** in the match %. Feeds the constraint line with the original JD sentence |
| `work_authorization` | Visa, citizenship, right to work | Same as `location` |

**Not soft skills** (they stay in the match % under their own category): a language ("fluent English" is `language`), leading a team for a stated time (`experience_duration`), presenting results to stakeholders as part of a role (`other` or `knowledge_area`), a named method or tool.

### A7. Hard cases

- **Contradictions** ("1-2 years" and "fresh graduates welcome"; "S1 required" and "Diploma/Degree"): one unit per statement, reason in the note. If the softener is in the same sentence as the requirement, set `importance = unknown` (J1-U01). If a separate item is explicitly marked "(Required)", it stays `required` and the conflict is written in the note (J2-U08, J2-U12). (D-042)
- **Conditional requirements** ("For the senior position, at least 3 years"): record the condition in `unit_text` and set `importance = unknown`. Never apply a senior-only condition to every applicant.
- **Complex alternatives** ("Python or Java, with 3 years in one of them"): one unit, `needs review` in the note.

---

## Part B. Evidence labels (requirement unit + CV)

### B1. Labels

| Label | Rule |
| --- | --- |
| `MATCH` | The CV shows the skill or knowledge **used** in work, a project, study, or research, with context. For a qualified unit, the proven duration meets the minimum |
| `PARTIAL` | Evidence exists but is weaker than asked: the skill appears **only in a skills list** (including simple tools such as Git, D-035); only a course or certificate when the JD asks for experience; a duration below the minimum; only one checkable part of a compound unit (for example the skill but not the duration). Level words ("intermediate", "strong", "real-world advantages/drawbacks") are not separate parts; clear evidence of use is MATCH (D-042) |
| `NO_MATCH` | No evidence found in the CV. Shown to the user as "No evidence found in the CV yet", never "You do not have this skill" |

For an alternative group, the group label is the best branch (MATCH if any branch is MATCH). A failed branch is never treated as NO_MATCH (System Design v1.3 section 6).

### B2. What v1 does not judge (D-035)

- **Truth of the CV.** The CV is taken as written. The user is responsible for what it says.
- **Depth.** Words like "strong" or "expert" are not measured. One clear example of use is MATCH.

### B3. Related tools and product names

| Case | Label |
| --- | --- |
| The JD names one tool (AWS) and the CV shows a different one (GCP) | `NO_MATCH` |
| The JD gives alternatives that include the CV's tool ("AWS, Azure, or GCP") | `MATCH` if used with context |
| The JD says "or similar / atau sejenisnya / etc" and the CV shows a comparable tool | `PARTIAL` or `MATCH`, reason in the note |
| Same product under another name (Google Data Studio and Looker Studio) | Treated as the same product |
| A library that runs on top of a framework (Hugging Face) | Does not prove the framework (PyTorch, TensorFlow) unless the CV names it |

### B4. Soft skills and location

- **Soft skills:** MATCH only when a CV sentence clearly shows the behavior. Do not infer a trait from a job title or from having had a job ("did an internship" does not prove teamwork).
- **Location:** a city in the CV does not prove willingness to commute or relocate. Use `PARTIAL` with `check_status = needs_clarification`. The constraint stays `unknown` until the user confirms (D-033).

### B5. Evidence quote

- `cv_quote` is copied **word for word** from the CV. A label without a quote can only be `NO_MATCH`.
- `cv_section`: Experience, Projects, Education, Skills, Certifications, Summary, or Other.
- The CV and the JD may use different languages. Meaning counts, not the language.

### B6. Check status

| Value | Use when |
| --- | --- |
| `done` | The unit could be judged |
| `needs_clarification` | Only the user can tell: a required duration that the CV cannot bound (dates missing or incomplete for the relevant work), or willingness to relocate (D-042) |
| `failed` | The unit or the CV text could not be read (system failure) |

---

## Part C. Constraint states

| Constraint | `compatible` | `unknown` | `explicit_conflict` |
| --- | --- | --- | --- |
| Experience duration | CV proves at least the JD minimum | JD states no minimum, the requirement is `unknown` (contradictory or conditional), or the CV has no dates for the relevant work | CV proves less than a required JD minimum |
| Location | Job is in the user's **confirmed** location, or the JD allows the user's country | No confirmed location, remote with no stated region, or job location missing | Onsite job outside the confirmed location |
| Work authorization | (not used in v1) | JD states a requirement; v1 does not collect the user's status | (not used in v1) |

"No known conflict" is not the same as `compatible`. Constraint warnings show the original JD sentence and appear before the apply link (D-033). A job with a conflict is never removed; it is listed in a separate block below jobs without conflicts (D-013).

**Counting experience (D-042):** a minimum of work experience in a field or role counts only employment in that same field, summed across companies; projects, a thesis, courses, and bootcamps do not count toward it (they can still be PARTIAL evidence). A complete dated work history is an upper bound: if even the most generous reading is below the minimum, the constraint is `explicit_conflict`; if the period cannot be bounded, it is `unknown`. Link the duration to the skill only when the link is clear; do not count overlapping periods twice; "present" means the analysis date; do not invent precision from incomplete dates; internships count unless the JD excludes them (note it).

---

## Part D. Relevance (CV profile + job), 0 to 3 (D-014, D-037)

Relevance measures **how well the CV evidence supports the job, together with the constraints**. It is judged in **automatic mode**: the target is the four target role families (AI/ML engineering, data science, GenAI/LLM, software AI). It does not measure how similar the job title is to a narrower personal target. The `cv_target` column is only a preference note.

| Score | Meaning |
| --- | --- |
| 3 | Most required technical requirements are supported by CV evidence, and there is no explicit constraint conflict |
| 2 | Several key required requirements are supported, some gaps, and no explicit conflict |
| 1 | Weak evidence support, **or** an explicit conflict (for example 3+ years asked, the CV shows under 1 year) |
| 0 | Outside the four target role families, or almost no requirement supported |

Soft skills and location do not lower relevance by themselves, the same as in the score. Write one short reason (`main_reason`) and the constraint that drove the score, if any (`constraint_note`).

---

## Part F. Pilot case notes (1 Oct 2026, D-041)

These are reviewer decisions on specific pilot cases, kept as worked examples. The general rules behind them are in D-042.

| Case | Decision | Open question |
| --- | --- | --- |
| J1-U01 experience 1-2 years + "fresh graduate welcome" (same sentence) | `unknown`, `min_years = 1` | Rule set: D-042 |
| J2-U08 "AI Developer: 1 year (Required)", J2-U12 "S1 (Required)" (separate explicit items) | `required` | Rule set: D-042 |
| J1 "Mathematical, Statistical, and/or Machine Learning" | Historical D-041: three required units, unchanged in existing gold | v1.3 uses the composite rule for new annotations; explicitly re-review before migrating this case |
| CV1 x J1-U20, J1-U21: use shown, trade-offs not explained | MATCH on evidence of use | Rule set: D-042 |
| CV1 x J1-U04: mathematics only through courses | PARTIAL | |
| CV2 x J2-U08: AI projects, no employment as AI Developer | PARTIAL; the complete work history bounds the duration, so `check_status = done` | Rule set: D-042 |

## Part E. Working procedure (D-038)

Full process: [docs/annotation-workflow.md](../docs/annotation-workflow.md).

1. A language model drafts labels under this guideline (`label_source = model_draft`, `review_status = pending`).
2. A QA check looks for exact quotes, complete fields, and rule errors; findings go to the QA_Log sheet.
3. The annotator reviews every row, fills `review_action`, and sets `review_status = approved` only for rows he decided.
4. D-047: current development rows all have drafts followed by human review. Preserve any genuinely blind historical pilot provenance. Held-out test follows D-046 blind-first rules; it is not used to tune this guideline.
5. The annotator records start and end times in the Timing sheet for every review session.
6. Rule questions go to the Questions sheet and are decided by the annotator, never by the model that drafts labels.
7. Pilot and development items never go into the held-out test set.

---

## Version adoption checklist

1. The active Excel workbook and gold files are not rewritten by publishing this document. Keep the original JD/CV source sheets and quotations unchanged.
2. Review pending rows under v1.3. Changed content uses `review_action = edited` plus a reason; newly added units use `added`. Only set approved after an actual decision. Redundant rows use `rejected` with a reference to retained units. Uncertain cases remain pending.
3. Set `guideline_version = v1.3` only for rows actually checked under this version. A merge/split/category/importance change requires dependent B and relevant C to be rechecked. Never mass-update versions or human approval fields.
4. Before metrics or export, identify labels affected by this revision, including approved pilot precedents. Keep historical results and scores with their original guideline. Do not compare models against incompatible unit definitions and call the difference model quality; harmonize the evaluated subset by human review or report separate versioned results.
5. Pipeline owner: coordinate an explicit switch from `annotation_guideline_v1.md` (v1.2) to this file; update GUIDELINE_VERSION and create a new extraction prompt revision. The existing v1.1 extraction prompt explicitly enforces D-041 and leaves umbrella cases unresolved. Do not attach v1.3 while keeping those conflicting instructions.
6. Verify schema/hold behavior for unsupported composites, add focused regression checks, and preserve cache keys including the actual guideline/prompt content and versions. Update matcher/runner metadata consistently. Retain historical cache/results, and never label cached v1.2 output as v1.3. No live inference, score-code change, or paid regeneration is authorized by this documentation edit alone.

## Change log

| Version | Date | Change |
| --- | --- | --- |
| v0.1 | 29 Sep 2026 | First draft for the pilot |
| v1.0 | 30 Sep 2026 | After the pilot: soft skills and location out of the match % (D-032, D-033); list splitting by wording (D-034); skills-list-only is PARTIAL, no truth or depth check (D-035); relevance in automatic mode (D-037); model-draft workflow with review actions and a blind sample (D-038); rules for related tools, conditional and contradictory requirements |
| v1.1 | 30 Sep 2026 | Q17: the conjunction decides how a list is split (D-039), with one exception for lists of experience areas (D-040). Field names `label_source`, `review_status`, `draft_note`, `review_note`. 1 Oct: case notes in Part F and A4/A7 notes from the pilot review (D-041); no rule change |
| v1.2 | 1 Oct 2026 | D-042: explicit Required items versus softeners (A7); level words are not separate parts (B1); needs_clarification for an unbounded required duration (B6); work-experience minimums count employment in the same field only, and a complete dated history is an upper bound (Part C) |

| v1.3 | 2 Oct 2026 | D-049: avoid umbrella/child double counting; local importance cues including preference priority; tool versus knowledge categorization; preserve and/or and unsupported cardinality. Explicit historical-label and runtime migration boundaries; D-047 workflow reflected. |
