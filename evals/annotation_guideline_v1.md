# JobFit Annotation Guideline

**Version:** v1.2 · **Date:** 1 October 2026 · **Stage:** CP2.1 (checkpoint 8)
**Used by:** the annotator's approved labels, the model drafts (pre-annotation), the LLM prompts (`prompts/`), and the scoring code (`src/jobfit/scoring/`). All of them follow the same rules (System Design v1.3 section 15).
**Status:** in use. Built from guideline v0.1 ([annotation_guideline_v0.1.md](annotation_guideline_v0.1.md)) and the pilot decisions D-032 to D-042. The working process is in [docs/annotation-workflow.md](../docs/annotation-workflow.md). Every label stores the guideline version it was made with. The pilot rows labeled under v0.1 keep `v0.1`.

---

## 0. Label record fields (all label types)

| Field | Meaning |
| --- | --- |
| `guideline_version` | For example `v1.1` |
| `label_source` | `model_draft` (drafted by a language model, then reviewed) or `annotator` (created by the annotator). It stays `model_draft` after the annotator edits the row |
| `review_status` | `pending` (not decided yet) or `approved` (decided by the annotator) |
| `review_action` | Filled by the annotator: `accepted`, `edited`, `rejected`, or `added` (D-038) |
| `draft_note` | Reasoning attached to a model draft |
| `review_note` | The annotator's note: always for `edited` or `rejected`, and for hard cases |
| `reviewed_by`, `reviewed_at` | Added when the workbook is converted to gold files |

Only `approved` labels are ground truth (D-016). There is one human annotator, so no inter-annotator agreement is reported. Instead, agreement between the model draft and the annotator on the blind sample and the acceptance rate are reported (D-038).

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
| "a plus", "nice to have", "preferred", "advantage", "nilai tambah", "diutamakan", "lebih disukai" | `preferred` |
| Mixed or contradictory signals, or the heading is unclear | `unknown` (do not force it into required) |

### A4. How to split a list (D-034, D-039)

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
| Unclear which pattern applies | Split, set `importance = unknown`, and write the reason in the note |
| "**and/or**" | No general rule yet. Decide case by case and write the reason in the note. Pilot case: J1 "Mathematical, Statistical, and/or Machine Learning skills required" was split into three required units (D-041) |

Examples: "Strong knowledge of AI technologies, including machine learning, natural language processing, and computer vision" gives three units (AND). "Familiarity with REST APIs, Git, Docker, and CI/CD practices" gives four units (AND). "Experience with frameworks such as PyTorch, TensorFlow, or XGBoost" gives one unit with alternatives (such as ... or).

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
| J1 "Mathematical, Statistical, and/or Machine Learning" | Three required units | "and/or" stays case by case |
| CV1 x J1-U20, J1-U21: use shown, trade-offs not explained | MATCH on evidence of use | Rule set: D-042 |
| CV1 x J1-U04: mathematics only through courses | PARTIAL | |
| CV2 x J2-U08: AI projects, no employment as AI Developer | PARTIAL; the complete work history bounds the duration, so `check_status = done` | Rule set: D-042 |

## Part E. Working procedure (D-038)

Full process: [docs/annotation-workflow.md](../docs/annotation-workflow.md).

1. A language model drafts labels under this guideline (`label_source = model_draft`, `review_status = pending`).
2. A QA check looks for exact quotes, complete fields, and rule errors; findings go to the QA_Log sheet.
3. The annotator reviews every row, fills `review_action`, and sets `review_status = approved` only for rows he decided.
4. About 10% of items are labeled by the annotator without any draft (blind sample): `label_source = annotator`, `review_action = added`.
5. The annotator records start and end times in the Timing sheet for every review session.
6. Rule questions go to the Questions sheet and are decided by the annotator, never by the model that drafts labels.
7. Pilot and development items never go into the held-out test set.

---

## Change log

| Version | Date | Change |
| --- | --- | --- |
| v0.1 | 29 Sep 2026 | First draft for the pilot |
| v1.0 | 30 Sep 2026 | After the pilot: soft skills and location out of the match % (D-032, D-033); list splitting by wording (D-034); skills-list-only is PARTIAL, no truth or depth check (D-035); relevance in automatic mode (D-037); model-draft workflow with review actions and a blind sample (D-038); rules for related tools, conditional and contradictory requirements |
| v1.1 | 30 Sep 2026 | Q17: the conjunction decides how a list is split (D-039), with one exception for lists of experience areas (D-040). Field names `label_source`, `review_status`, `draft_note`, `review_note`. 1 Oct: case notes in Part F and A4/A7 notes from the pilot review (D-041); no rule change |
| v1.2 | 1 Oct 2026 | D-042: explicit Required items versus softeners (A7); level words are not separate parts (B1); needs_clarification for an unbounded required duration (B6); work-experience minimums count employment in the same field only, and a complete dated history is an upper bound (Part C) |
