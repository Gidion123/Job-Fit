# JobFit Annotation Guideline

**Version:** v0.1 (draft for the labeling pilot) · **Date:** 29 September 2026 · **Stage:** CP2.1 (checkpoint 8)
**Used by:** Dion's gold labels, the LLM prompts (`prompts/`), and the scoring code (`src/jobfit/scoring/`). All three must follow the same rules (System Design v1.3 section 15).
**Status:** superseded by v1.0 ([annotation_guideline_v1.md](annotation_guideline_v1.md)) on 30 Sep 2026. Kept because the pilot rows were labeled with v0.1.

---

## 0. Label record fields (all label types)

| Field | Meaning |
| --- | --- |
| `guideline_version` | For example `v0.1` |
| `status` | `provisional` (not reviewed by Dion yet) or `gold` (reviewed and decided by Dion) |
| `ai_suggested` | `true` if an AI suggestion was shown before Dion decided |
| `reviewed_by`, `reviewed_at` | Who decided and when (gold labels only) |
| `notes` | Short reason when the case was hard |

Only `gold` labels are used as ground truth (D-016). There is one human annotator, so no inter-annotator agreement is reported.

---

## Part A. Requirement units (from a job description)

### A1. What is a requirement unit?

A requirement unit is one thing the candidate must have or show, written so it can be checked **on its own without losing meaning**. It does not mean splitting at every comma.

| JD text | Units |
| --- | --- |
| "Proficient in Python, SQL, and Docker" | 3 units: Python; SQL; Docker |
| "Python or Java" | 1 unit with an **alternative group** (either is enough) |
| "3 years of experience using Python" | 1 **qualified unit** (Python + 3 years stay together) |
| "Bachelor's degree or equivalent experience" | 1 unit with an alternative group |
| The same requirement written twice | 1 unit; keep both source quotes |
| "TensorFlow, PyTorch, or Keras" | 1 unit with an alternative group |

### A2. What is not a requirement unit?

- **Responsibilities** ("You will build...", "Tanggung jawab"): not units, unless the JD states it as something the candidate must already have.
- Company description, benefits, salary, contract length.
- Pure logistics ("able to commute to Bandung") is **not** a skill unit; record it as a `location` unit so it becomes a constraint.

### A3. Importance: required, preferred, or unknown

| Cue | Importance |
| --- | --- |
| "must", "required", "mandatory", "at least", "minimal", "wajib", "harus", or listed under Requirements / Qualifications / Kualifikasi without a softening word | `required` |
| "a plus", "nice to have", "preferred", "advantage", "nilai tambah", "diutamakan", "lebih disukai" | `preferred` |
| Mixed or contradictory signals, or the section heading is unclear | `unknown` (do not force it into required) |

### A4. Fields for each unit

| Field | Rule |
| --- | --- |
| `unit_text` | Short, normalized statement, in English (for example "Python", "SQL", "Bachelor's degree in CS or related") |
| `source_quote` | The exact JD words the unit comes from (copy, do not paraphrase) |
| `importance` | `required`, `preferred`, or `unknown` (A3) |
| `category` | `skill_tool`, `knowledge_area`, `experience_duration`, `education`, `language`, `certification`, `soft_skill`, `location`, `work_authorization`, `other` |
| `group_id` | Same id for all options of one alternative group (for example `G1`); empty otherwise |
| `min_years` | Only for qualified experience units; the number written in the JD |
| `notes` | Anything unclear |

### A5. Hard cases

- **Contradictions** ("For the senior position at least 3 years" + "Fresh graduates welcome" + "1 year required"): make one `experience_duration` unit per distinct statement, and set `importance = unknown` for the ones that conflict. Explain in `notes`.
- **Complex alternatives** ("Python or Java, with 3 years in one of them"): keep as one unit, write `needs review` in `notes`. v1 supports only clear alternatives.
- **Soft skills** ("good communication", "problem solving"): record them with `category = soft_skill` and the importance the JD gives. Whether they stay in the score denominator is **open question Q1**, decided after the pilot.

---

## Part B. Evidence labels (requirement unit + CV)

### B1. Labels

| Label | Rule |
| --- | --- |
| `MATCH` | The CV shows direct evidence that meets the unit: the skill or knowledge is **used** in work, a project, research, or study, with context. For a qualified unit, the proven duration meets the minimum. |
| `PARTIAL` | Evidence exists but is weaker than asked, for example: the skill appears **only in a skills list** without use context; only a course or certificate when the JD asks for experience; a duration below the minimum; only part of a compound unit shown. |
| `NO_MATCH` | No evidence found in the CV. Shown to the user as "No evidence found in the CV yet", never "You do not have this skill". |

For an alternative group, the group label is the best branch (MATCH if any branch is MATCH).

### B2. Evidence quote

- `cv_quote` must be copied **word for word** from the CV. A label without a quote can only be `NO_MATCH`.
- `cv_section`: the CV section the quote comes from (Experience, Projects, Education, Skills, Certifications, Summary, Other).
- The CV may be in Indonesian and the JD in English (or the other way). Meaning counts, not the language.

### B3. Check status

| Value | Use when |
| --- | --- |
| `done` | The unit could be judged |
| `needs_clarification` | The CV is ambiguous and only the user could tell (for example a project with no dates for a duration unit) |
| `failed` | The unit or the CV text could not be read (system failure) |

### B4. Rules still to be confirmed in the pilot

- **Q2:** Is "skill only in a skills list" always `PARTIAL`, or `MATCH` for simple tools (for example Git)?
- **Q3:** Does a related tool count (GCP when the JD says AWS)? Draft rule: `PARTIAL` only if the JD says "or similar" / "atau sejenisnya"; otherwise `NO_MATCH`.

---

## Part C. Constraint states

| Constraint | `compatible` | `unknown` | `explicit_conflict` |
| --- | --- | --- | --- |
| Experience duration | CV proves at least the JD minimum | JD states no minimum, or the CV has no dates for the relevant work | CV proves less than the JD minimum |
| Location | Job is in the user's **confirmed** location, or the JD says the user's country is allowed | No confirmed user location, remote with no stated region, or job location missing | Onsite job outside the confirmed location |
| Work authorization | (not used in v1) | JD states a work-authorization requirement; v1 does not collect the user's status | (not used in v1) |

"No known conflict" is not the same as `compatible`.

**Counting experience** (from System Design v1.2 section 5):

- Link the duration to the skill only when the link is clear.
- Do not count overlapping periods twice.
- "Present" means the analysis date, which is recorded.
- Do not invent precision from incomplete dates.
- Internships count as experience only when the JD does not exclude them. Mark this in `notes`.

---

## Part D. Relevance (CV profile + job), 0 to 3

Relevance measures **how well the candidate's CV evidence supports the job, given the candidate's target and the constraints**. It does **not** measure how similar the job title is to the target role (D-014).

| Score | Meaning |
| --- | --- |
| 3 | Most required requirements are supported by CV evidence, and there is no explicit constraint conflict |
| 2 | Several key required requirements are supported, some gaps, and no explicit conflict |
| 1 | In the target role family, but weak evidence support, **or** an explicit conflict (for example 3+ years asked, the CV shows under 1 year) |
| 0 | Not suitable for the target (wrong role family, or almost no requirement supported) |

Write one short reason (`main_reason`) and, if any, the constraint that drove the score (`constraint_note`).

---

## Part E. Pilot procedure (evening of 29 September 2026)

1. Read Parts A to D once (about 10 minutes).
2. Open the pilot workbook (`evals/pilot/JobFit_Pilot_Labeling_v0.1.xlsx`).
3. For every task, write the start and end time in the `Timing` sheet.
4. Part A: extract units for J1 and J3 **without** AI suggestions, then review the AI suggestions for J2 (edit freely).
5. Part B: label evidence for CV1 × J1 and CV2 × J2.
6. Part D: give relevance 0-3 for CV1 and CV2 against J1 to J5.
7. Write every rule that felt unclear in the `Questions` sheet.

Pilot items belong to the **development** set, never to the held-out test set.

---

## Change log

| Version | Date | Change |
| --- | --- | --- |
| v0.1 | 29 Sep 2026 | First draft for the pilot |
