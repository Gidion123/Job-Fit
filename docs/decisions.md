# JobFit Decision Log

This file records design and scope decisions for JobFit: what was decided, by whom, what it replaced, why, and what it affects. An entry is added when a decision is made. A change is only described as "recorded" once its entry exists here.

The full design that these decisions produce is System Design v1.3 (`02_System_Design/JobFit_System_Design_v1.3.md`, in the project folder outside this repository).

## Status values

| Status | Meaning |
| --- | --- |
| Approved | Decided and in effect |
| Hypothesis | Used as a starting point; kept or changed based on development-set results |
| Pending approval | Recommended, but needs Dion's approval before it takes effect (usually because it costs money) |
| Deferred | Not in v1 for now; may come back later |
| Out of scope v1 | Deliberately not built in v1 |
| Superseded | Replaced by a later entry |
| Cancelled | Dropped |

## Sources

- **Mentor:** feedback from the CP1 mentoring session on 27 September 2026, as passed on by Dion; feedback from the CP2 mentoring session on 4 October 2026, passed on by Dion on 7 October (D-093).
- **Dion:** decisions Dion made in design sessions.
- **Implementation:** technical decisions made to carry out an approved decision.

## Summary

| ID | Date | Decision | Status |
| --- | --- | --- | --- |
| D-001 | 27 Sep 2026 | Model selection through retrieval, ranking, LLM extraction, and prompt experiments | Approved |
| D-002 | 27 Sep 2026 | Target-first flow where the user picks 1-5 jobs before analysis | Superseded by D-008 |
| D-003 | 27 Sep 2026 | Snapshot database; paste JD and job link for the latest jobs | Approved for paste JD; link changed by D-011 |
| D-004 | 27 Sep 2026 | Focus on matching and evaluation; market insight and CV suggestions as simple versions | Approved, continued in D-025 |
| D-005 | 27 Sep 2026 | Jobs from paste or link are session-only | Approved (paste JD only) |
| D-006 | 28 Sep 2026 | Score = evidence coverage of required requirement units, with hold rules | Approved (soft skills and location units leave the denominator: D-032, D-033) |
| D-007 | 28 Sep 2026 | Two main evaluation goals, safety metrics as a pass condition | Superseded by D-017 |
| D-008 | 29 Sep 2026 | Main goal: ranked list of jobs best supported by CV evidence; CV-first flow with optional filters | Approved |
| D-009 | 29 Sep 2026 | Automatic mode searches only the target role families | Approved |
| D-010 | 29 Sep 2026 | Filter rules: location suggestion, UNKNOWN on by default, no silent relaxation | Approved |
| D-011 | 29 Sep 2026 | Import link removed from v1 | Out of scope v1 |
| D-012 | 29 Sep 2026 | Two-stage search; the list shows only evidence-matched results | Approved (K is a hypothesis) |
| D-013 | 29 Sep 2026 | Ordering, constraint states, tie-break, and score display rules | Approved (tie-break alternative is a hypothesis) |
| D-014 | 29 Sep 2026 | Relevance labels measure fit to CV evidence and the user's target | Approved |
| D-015 | 29 Sep 2026 | Labeling process: pilot first, then set gold sizes | Approved |
| D-016 | 29 Sep 2026 | Single human annotator with AI assistance | Approved |
| D-017 | 29 Sep 2026 | Evaluation priorities for v1.3 | Approved |
| D-018 | 29 Sep 2026 | LLM: DeepSeek baseline, compared on the development set | Superseded by D-029 |
| D-019 | 29 Sep 2026 | Historical US$15 project ceiling | Revised by D-070 on 4 October 2026 |
| D-020 | 29 Sep 2026 | Embedding model: OpenAI `text-embedding-3-small` | Approved (called through OpenRouter, D-030) |
| D-021 | 29 Sep 2026 | Synthetic CVs by default; real CV only after explicit confirmation | Approved |
| D-022 | 29 Sep 2026 | Demo path with saved results, honestly labeled | Approved |
| D-023 | 29 Sep 2026 | Hosting: Railway | Superseded by D-095 (SumoPod VPS) |
| D-024 | 29 Sep 2026 | Local development database with Docker Compose | Approved |
| D-025 | 29 Sep 2026 | Feature status and the rule for removing minimal features | Approved |
| D-026 | 29 Sep 2026 | Definition of Done v1 and the cut order | Approved |
| D-027 | 29 Sep 2026 | Official dates, revised schedule, and actual dates are tracked separately | Approved |
| D-028 | 29 Sep 2026 | Scripts may read API keys from a git-ignored local `.env` | Approved (keys changed by D-030 and D-031) |
| D-029 | 29 Sep 2026 | LLM shortlist across providers and a pre-registered selection rule | Approved (access changed by D-030) |
| D-030 | 29 Sep 2026 | OpenRouter as the single gateway for all LLM and embedding calls | Approved (DeepSeek fallback removed by D-031) |
| D-031 | 29 Sep 2026 | OpenRouter only; guard follows credit bought | Approved; current numeric limits revised by D-070 |
| D-032 | 30 Sep 2026 | Soft skills are shown separately and are not part of the match % | Approved (to be checked against relevance labels) |
| D-033 | 30 Sep 2026 | Location and work-authorization requirements are constraints, not score units | Approved |
| D-034 | 30 Sep 2026 | How a JD list is split into requirement units depends on its wording | Approved (rule simplified by D-039) |
| D-035 | 30 Sep 2026 | Evidence strength in v1: skills-list-only is PARTIAL; CV truth and depth are not verified | Approved |
| D-036 | 30 Sep 2026 | CV coach: minimal guided version in v1 after matching is done; full coach as a later upgrade | Approved |
| D-037 | 30 Sep 2026 | Relevance labels are judged in automatic mode (all four target role families), from CV evidence and constraints | Approved |
| D-038 | 30 Sep 2026 | Labeling workflow: a language model drafts, Dion verifies every row, with a blind sample and a recorded review action | Approved |
| D-039 | 30 Sep 2026 | The conjunction decides how a JD list is split (AND splits; OR, such as, etc give one unit) | Approved |
| D-040 | 30 Sep 2026 | Exception to D-039: a list of experience areas is split into one required unit per area, even with "such as ... or" | Approved |
| D-041 | 1 Oct 2026 | Pilot review decisions on A_Extraction and B_Evidence (case decisions, not general rules) | Approved; general rules set by D-042 |
| D-042 | 1 Oct 2026 | General rules from the pilot review: explicit Required items, level qualifiers, unbounded duration, and how experience minimums are counted | Approved |
| D-043 | 1 Oct 2026 | Gold-set sizes from the pilot timing (2 hours of annotator time left) | Superseded by D-045 |
| D-044 | 1 Oct 2026 | Model benchmark protocol: where the LLM and embedding models are compared, and a second embedding candidate | Approved (option A, with the silver/gold rules in D-045) |
| D-045 | 1 Oct 2026 | Gold-set sizes v2, silver labels, and a phased labeling plan | Approved on 1 Oct 2026 |
| D-046 | 1 Oct 2026 | Development/test split rules and the blind-first test labeling process | Approved (rules); split method is an implementation choice |
| D-047 | 1 Oct 2026 | Development drafts followed by full human review | Approved |
| D-048 | 2 Oct 2026 | Combined development A/B/C workbook preparation | Approved workflow; historical counts below |
| D-049 | 2 Oct 2026 | Four annotation rules: umbrella overlap, importance, categories, and/or preservation | Adopted for manual review; runtime and historical-label migration pending |
| D-050 | 3 Oct 2026 | Close CP2.2 implementation; materialize broad development extraction after CP2.3 configuration evaluation | Approved explicitly by Dion |
| D-051 | 3 Oct 2026 | Server-temporary masking, isolated volatile CV sessions, explicit stop/delete and disconnect expiry | Design approved; implementation and deployed acceptance pending |
| D-052 | 3 Oct 2026 | Development evaluation scope, original-rank precision, relevant threshold and failure/class accounting | Conventions approved; cases/alignment and evaluator verification pending |
| D-053 | 3 Oct 2026 | Held-out top 10-union pool, coverage and configuration/protocol freeze | Approved protocol; execution pending |
| D-054 | 3 Oct 2026 | Six development C decisions, F00332 mapping/B corrections, C-only hold review path, strict split/merge extraction F1 | All listed case decisions confirmed; Stage-1 gates ready |
| D-055 | 3 Oct 2026 | Exact US$3.20 cap for four-model/seven-JD Stage-2 extraction batch | Approved; run stopped after first semantic failure, unused cap not transferable to changed protocol |
| D-056 | 3 Oct 2026 | Exact US$3.23 cap for versioned v1.4 Stage-2 extraction batch | Approved; run stopped after the first case on semantic review, no winner |
| D-057 | 3 Oct 2026 | V5 same-protocol remaining 27 extraction cases; keep semantic failures and review each next case; US$3.16 cap | Approved; terminal GPT process rejection preserved |
| D-058 | 3 Oct 2026 | GPT-only unsupported-temperature omission and published dated response ID; v6 remaining 21 cases within cumulative v5/v6 US$3.16 | Explicitly approved by Dion; not a model winner |
| D-059 | 3 Oct 2026 | Retain settled process failures and complete nine unattempted extraction cases; cumulative v5/v6/v7 US$3.16 | Explicitly approved by Dion; v7 completed |
| D-060 | 3 Oct 2026 | Scoped Claude/F00036 complex accounting: 0 TP, 2 FN, 3 FP | Approved |
| D-061 | 3 Oct 2026 | Primary extraction equivalence includes importance; category accuracy separate | Approved |
| D-062 | 3 Oct 2026 | Four-model/four-pair fixed-input matching, separate US$1.85 cap | Approved; 16 stages complete, cost US$0.156686829 |
| D-063 | 3 Oct 2026 | Accept v3 mapping recommendations and fixed adapter for metric calculation | Approved; assisted-QA acceptance, not independent re-annotation |
| D-064 | 3 Oct 2026 | Completed reference experiment; separate repair-only addendum below | Completed; replay cost US$0.09795280 against approved US$0.65 cap |
| D-065 | 4 Oct 2026 | G1/G2 evidence guardrails | Approved for v1 with recorded limits; runtime integration pending |
| D-066 | 4 Oct 2026 | V1 safety, per-task cost selection and quote validator v1.1 | Approved by Dion; D-029 retained as history |
| D-067 | 4 Oct 2026 | F00815 SQL reference v2, PostgreSQL as example | Approved by Dion; original gold unchanged |
| D-068 | 4 Oct 2026 | Provisional CP2.3 configuration and DeepSeek Flash model choice | Approved by Dion for development; K/weight await Part B |
| D-069 | 4 Oct 2026 | Resume only untouched Part B pairs under a US$2.50 aggregate cap and presentation cutoff | Approved and executed; no new configuration winner |
| D-070 | 4 Oct 2026 | Revised project credit and guard for the bounded pipeline v1.1 run | Approved by Dion; provider balance not independently verified |
| D-071 | 4 Oct 2026 | Pipeline v1.1 H2 provisional hold policy | Approved by Dion for development; comparative evaluation required |
| D-072 | 4 Oct 2026 | H2v2: experience, level and education are never excluded | Approved by Dion |
| D-073 | 4 Oct 2026 | Development final-order metrics use the real product order | Approved by Dion |
| D-074 | 4 Oct 2026 | Stage-1 seniority rule (3+ years moved down) | Approved by Dion; frozen in D-086 |
| D-075 | 4 Oct 2026 | Uncertainty reporting for CP2.3 comparisons | Recorded |
| D-076 | 4 Oct 2026 | Development check of GPT-6 Luna for matching | Done |
| D-077 | 4 Oct 2026 | DeepSeek Flash extracts, Luna matches | Matching part replaced by D-083 |
| D-078 | 4 Oct 2026 | Rule for K and PARTIAL weight, set before the labels | Approved; applied in D-086 |
| D-079 | 4 Oct 2026 | Matching model sweep under the same settings | Done |
| D-080 | 4 Oct 2026 | Fair retriever comparison labels (46 gap items) | Labels imported in D-085 |
| D-081 | 4 Oct 2026 | OpenRouter workspace budget versus the JobFit guard | Recorded |
| D-082 | 4 Oct 2026 | Sweep results after budget recovery; Sol 60-pair check | Proposal approved as D-083 |
| D-083 | 4 Oct 2026 | GPT-6 Sol matches, Luna is the fallback | Approved by Dion |
| D-084 | 6 Oct 2026 | Rule for changing the stage-1 retriever | Approved by Dion before the r4 numbers |
| D-085 | 6 Oct 2026 | Gap workbook imported as gold r4 (G04 held, A/B kept separate) | Approved by Dion; written |
| D-086 | 6 Oct 2026 | Freeze candidate: K 10, weight 0.5, seniority rule, experience block | Approved; frozen in D-087 |
| D-087 | 6 Oct 2026 | D-053 freeze approved (receipt v2, CP2.4 report contract) | Approved by Dion |
| D-088 | 7 Oct 2026 | CP2.4 test labels: AI-assisted, human-reviewed provenance; import test_v13_cp24_r1 | Approved by Dion; written |
| D-089 | 7 Oct 2026 | Phase A (post-test quality optimization) started; CP2.4 locked from optimization | Approved by Dion; closed by D-090 |
| D-090 | 7 Oct 2026 | Phase A closed: keep the baseline prompt v1.1 | Decided by the locked rule; confirmed by Dion |
| D-091 | 7 Oct 2026 | Accept the 52-JD extraction scope used in CP2.3; full development extraction stays optional (closes the D-050 carry-over) | Approved by Dion |
| D-092 | 7 Oct 2026 | Privacy is implemented and component/unit tested only; end-to-end validation and the original-vs-masked comparison move to CP3.4/CP3.5 | Approved by Dion |
| D-093 | 7 Oct 2026 | CP2 mentor feedback taken into CP3: waiting-state UX for the long LLM wait; vacancy-specific CV guidance | Approved by Dion |
| D-094 | 7 Oct 2026 | CP2 closed: acceptance work complete, reports current, freeze verified; handoff to CP3 | Approved by Dion |
| D-095 | 7 Oct 2026 | CP3 deployment target (SumoPod VPS), full public live product scope and branch lifecycle | Approved by Dion and Codex; planned, not deployed |
| D-096 | 7 Oct 2026 | Public live cost and abuse controls: US$5 validation budget, US$2/day cap, deterministic phase bounds, 1 analysis per IP per 24 h, one live analysis at a time | Approved by Dion and Codex; planned |
| D-097 | 7 Oct 2026 | CP3 runtime changes go through non-frozen adapters; the D-087 files stay byte-identical | Approved by Dion and Codex; planned |
| D-098 | 7 Oct 2026 | Mutable production job corpus: twice-monthly JSearch sync, dedupe, lifecycle, lazy extraction cache, minimal Alembic baseline | Approved by Dion and Codex; Alembic 0001/0002 implemented 8 Oct (schema only); sync and seed planned |
| D-099 | 7 Oct 2026 | CP3 observability: Prometheus and Grafana with email alerts, Langfuse Cloud (Japan) metadata only | Approved by Dion and Codex; planned |
| D-100 | 7 Oct 2026 | CP3 evaluation obligations and feature freeze: D-045 to be completed with option B, PR-10, freeze at the end of 9 Oct | Approved by Dion and Codex; planned, not completed |

---

## D-001. Model selection through experiments, not CNN/LSTM training

- **Date and source:** 27 Sep 2026, mentor.
- **Previous:** The bootcamp timeline names checkpoint 8 "Model Selection (CNN/LSTM/DNN)" and checkpoint 9 "Modeling Deep Learning".
- **Decision:** For JobFit, these checkpoints are met by experiments on retrieval, ranking, LLM extraction evaluation, and prompt engineering.
- **Reason and trade-off:** JobFit is an LLM and information retrieval system. Training a CNN or LSTM would not answer its main question. The trade-off is that the experiments must be clearly measured, so the checkpoint is not seen as skipped.
- **Affects:** Playbook checkpoints 8-11; CP2 stage reports.
- **Status:** Approved.

## D-002. Target-first flow with a 1-5 job selection

- **Date and source:** 27 Sep 2026, mentor (target-first, match %, CV weaknesses) and Dion (filter, the system sorts, the user picks 1-5 jobs).
- **Decision at the time:** The user filters, picks 1-5 jobs, then the CV is compared with those jobs.
- **Status:** Superseded by D-008 on 29 Sep 2026. The mentor's parts (match %, CV weaknesses, the user's target through filters) are kept. Only the mandatory 1-5 selection step, which was Dion's decision, is removed.

## D-003. Snapshot database, paste JD, and job link

- **Date and source:** 27 Sep 2026, mentor.
- **Decision:** The database can be a snapshot that is not always up to date. For the latest jobs there are two options: paste the JD, or give a job link.
- **Status:** Approved for paste JD (MUST). The job link was later removed from v1 by D-011.

## D-004. Focus on matching and evaluation

- **Date and source:** 27 Sep 2026, mentor.
- **Decision:** Put the effort into matching and its evaluation. Market insight and CV suggestions are built as simple versions.
- **Status:** Approved. Continued in D-025.

## D-005. Jobs from paste or link are session-only

- **Date and source:** 27 Sep 2026, Dion.
- **Decision:** A pasted JD is used only in that session. It is not added to the main corpus, the market statistics, or the gold set.
- **Status:** Approved (paste JD only, since the link is out of scope).

## D-006. Score definition and hold rules

- **Date and source:** 28 Sep 2026, Dion, after two review rounds on System Design v1.1.
- **Previous:** v1.1 used a match % with an inconsistent definition and an example that was miscalculated (64% instead of 60%).
- **Decision:** Required-requirement match = (MATCH + 0.5 × PARTIAL) / all identified required requirement units × 100. Failed units stay in the denominator. The score is shown, provisional, or on hold depending on the check status. Strong/Realistic/Stretch labels are postponed.
- **Reason and trade-off:** One clear definition that can be checked by hand. The 0.5 weight is not proven yet.
- **Affects:** Scoring code, annotation guideline, report display.
- **Status:** Approved. The 0.5 weight is a hypothesis (tested in CP2). The labels are now out of scope for v1 (D-025).

## D-007. Two main evaluation goals

- **Date and source:** 28 Sep 2026, Dion (System Design v1.2).
- **Decision at the time:** Evidence Macro-F1 and NDCG@10 as the two main goals, with safety metrics as a pass condition.
- **Status:** Superseded by D-017, which keeps the same metrics but orders them around the new main goal.

---

## D-008. Main goal and CV-first flow with optional filters

- **Date and source:** 29 Sep 2026, Dion.
- **Previous:** D-002. The main output was a report for 1-5 jobs the user picked first.
- **Decision:**
  - The main output is a **ranked list of jobs best supported by the user's CV evidence**, with match %, reasons, missing evidence, and important constraints.
  - Flow: upload CV, check the parsing summary, fill optional filters, see recommendations, open the match details.
  - Empty filters: search by CV within the target role families. Partial filters: use the chosen filters and the CV evidence. Full filters: filter first, then order by match.
  - Filters can be changed on the results page. The user does not have to pick 1-5 jobs to get recommendations.
  - The user's experience-level choice never replaces the experience proven in the CV.
  - CV suggestions and market insight stay as minimal supporting features.
- **Reason and trade-off:** This matches what an early-career job seeker needs first: which jobs to look at. The trade-off is that match % must be computed for many jobs, so a two-stage search is needed (D-012). The automatic mode with empty filters differs partly from the mentor's target-first direction, so it will be presented to the mentor at CP2 as a proposal.
- **Affects:** System Design v1.3 sections 3-4; Canonical sections 2, 13, J; Playbook checkpoints 9, 15, 17; API endpoints; UI.
- **Status:** Approved.

## D-009. Search scope of the automatic mode

- **Date and source:** 29 Sep 2026, Dion.
- **Decision:**
  - The automatic mode searches only the target role families (`ai_ml_engineering`, `data_science`, `genai_llm`, `software_ai`): 428 of the 632 EDA candidates in snapshot `CP1_20260926`.
  - Adjacent roles (131, for example Data Analyst and Data Engineering) and non-target roles (73) do not appear in recommendations. They stay in the data as evaluation material, for example as hard negatives.
  - Official support for adjacent roles is future work, because it needs its own annotation and evaluation.
  - Not all 910 records are ready for analysis. The 632 EDA candidates only passed the EDA quality rules; a job can still fail requirement extraction.
- **Reason and trade-off:** Keeps the scope and the gold set small enough for the deadline. Users targeting Data Analyst roles are not served in v1.
- **Affects:** Filter options, stage-1 search, evaluation pool.
- **Status:** Approved.

## D-010. Filter rules

- **Date and source:** 29 Sep 2026, Dion.
- **Decision:**
  - **Location:** A location detected in the CV is offered as a visible filter suggestion that the user must confirm. The CV address is never treated as the desired work location or as work-authorization evidence. If no location is chosen, all countries in the JobFit scope are searched, and each job shows its location and eligibility status.
  - **UNKNOWN:** On by default. Results that match the filter are shown separately from results whose information is unknown. The user can turn UNKNOWN off. The list is never called "matching your filters" when part of it is UNKNOWN.
  - **Empty results:** Filters are never relaxed silently. The page says that there are no results and lets the user change the filters.
- **Reason and trade-off:** Many fields are empty in the data (among the 428 target jobs, 153 do not state experience), so hiding UNKNOWN would remove many possible jobs. Showing it separately keeps the result honest.
- **Affects:** Filter logic, result page layout, filter recall evaluation.
- **Status:** Approved.

## D-011. Import link removed from v1

- **Date and source:** 29 Sep 2026, Dion.
- **Previous:** D-003 (link as SHOULD).
- **Decision:** Import link is removed from the v1 scope. No provider is added and no link integration experiment is run now. For jobs outside the database: paste the JD text, preview the extraction, compare with the CV, get a match report. Pasted JDs are session-only.
- **Reason and trade-off:** Protects the deadline. This is a scope limit, not a conclusion that import link is technically impossible. Checked facts: JSearch has no endpoint that accepts a job URL (only keyword search and details by its own `job_id`), and fetching LinkedIn pages directly would break LinkedIn's User Agreement. A "search and match" approach through JSearch is noted as a possible future idea. Users must copy the JD text themselves.
- **Affects:** System Design v1.2 section 8 (removed), `/jobs/import` link option, SSRF tests (no longer needed), CP2 presentation (explain to the mentor, since the link was part of the feedback).
- **Status:** Out of scope v1.

## D-012. Two-stage search

- **Date and source:** 29 Sep 2026, Dion.
- **Decision:**
  - **Stage 1 (candidate search):** hybrid search without an LLM call per job. Its score is used only to choose which jobs are analyzed and is never shown as a match.
  - **Stage 2 (evidence matching):** the same evidence-matching method runs on the top K candidates.
  - The main list shows only jobs analyzed with the stage-2 method. Retrieval or overlap scores are never mixed into the match %.
  - The page says "K candidates from the search were analyzed", not that these are the best matches in the whole database.
  - Candidates outside K and candidates that failed processing get their own status. They are not treated as "not a match".
  - **K is not fixed.** It is chosen by an experiment on recall, latency, and cost (starting candidates: 10, 20, 30).
- **Reason and trade-off:** Running the LLM on every job for every user is too slow and costly. The trade-off is that a good job missed by stage 1 is never analyzed, so stage-1 Recall@K is measured.
- **Affects:** Architecture, `/recommendations` endpoint, cost per analysis, evaluation.
- **Status:** Approved. The K value is a hypothesis.

## D-013. Ordering, constraint states, and score display

- **Date and source:** 29 Sep 2026, Dion.
- **Decision:**
  - Three constraint states: **compatible** (evidence shows the constraint is met), **unknown**, and **explicit conflict**. "No known conflict" does not mean compatible.
  - Order within a result group: jobs without an explicit conflict first, then by match %. Jobs with an explicit conflict come after, also by match %.
  - Tie-break for equal match %: keep the stage-1 search order. This adds no quality claim.
  - "More requirements met first" is **not** adopted as a tie-break, because it favors longer JDs or JDs split into more units. It is kept as a hypothesis.
  - Jobs are not pushed down just because few skills were detected by the rule-based v0 skill list.
  - The match % is always shown with its denominator ("x of y required requirements"), the score status, the JD quality status, and the constraint line. Showing "x of y" helps transparency but does not solve every cross-job comparison problem; this is written as a limitation.
- **Reason and trade-off:** Puts realistic jobs first without hiding strong matches that simply lack information.
- **Affects:** Ranking code, result page, evaluation of ordering (NDCG@10).
- **Status:** Approved. The alternative tie-break is a hypothesis.

## D-014. Meaning of relevance labels

- **Date and source:** 29 Sep 2026, Dion.
- **Decision:** Relevance labels (0-3) for NDCG@10 and P@5 measure how well the candidate's CV evidence supports the job's requirements, given the user's target and the constraints. They do not measure role similarity alone.
- **Reason:** Otherwise a good NDCG would not prove the main goal.
- **Affects:** Annotation guideline, ranking gold set.
- **Status:** Approved.

## D-015. Labeling process

- **Date and source:** 29 Sep 2026, Dion.
- **Decision:** (1) Write the annotation guideline. (2) Label a small development pilot to test whether the rubric is clear, and time it. (3) Fix the guideline. (4) Prepare the development and held-out test split. (5) Keep labeling while implementation runs. Gold-set sizes are set after the pilot timing, not before.
- **If gold sizes are reduced from the Canonical targets** (extraction about 50 JDs, evidence about 100 pairs, ranking 40-60 jobs), a new entry records: the original and revised targets, the reason, the case coverage that stays mandatory, and the impact on how strong the conclusions are. A smaller gold set supports a limited demonstration only and is not claimed to prove broad performance.
- **Status:** Approved. The revised sizes will be a separate entry after the pilot.

## D-016. Single human annotator with AI assistance

- **Date and source:** 29 Sep 2026, Dion.
- **Decision:** Dion is the only human annotator. A language model may draft candidate labels and explanations, but every gold label is checked and decided by Dion. Labels not reviewed by Dion stay pending. Model drafts do not count as an independent annotator, and no inter-annotator agreement is reported. Each label records whether it started from a model draft (`label_source`).
- **Limitation recorded:** single-annotator bias and the risk of anchoring on model drafts.
- **Status:** Approved.

## D-017. Evaluation priorities

- **Date and source:** 29 Sep 2026, Dion.
- **Previous:** D-007.
- **Decision:**
  - **Main goal (recommendations):** NDCG@10 and P@5 on the analyzed recommendation list.
  - **Evidence accuracy:** Macro-F1, per-class results, and the share of cases that were successfully assessed.
  - **Diagnostics:** extraction quality, filter recall, and stage-1 Recall@K.
  - **Safety (pass condition):** hard-negative false positives, evidence quote validity, unsupported claims.
  - **Operations:** latency and cost, with live and cached runs reported separately.
  - Configurations are chosen on the development set. The held-out test set is not used for tuning.
- **Affects:** Canonical sections B, D, 18; Playbook checkpoints 11-12; evaluation scripts.
- **Status:** Approved.

## D-018. LLM choice

- **Date and source:** 29 Sep 2026, Dion.
- **Decision:**
  - DeepSeek is the first baseline candidate (`deepseek-flash`, the current name on DeepSeek's pricing page on 29 Sep 2026). `deepseek-v4-pro` is the only comparison candidate, from the same provider, so no new top-up is needed.
  - Both are tested on JobFit development cases (alternative requirements, experience, incomplete evidence, Indonesian CV with English JD), comparing extraction quality, evidence matching, unsupported claims, cost, and latency.
  - Another provider is considered only if both fail on the development set, and only after Dion approves a new top-up.
  - The exact model id, date, and settings are recorded with every run.
- **Status:** Superseded by D-029 on 29 Sep 2026, after Dion asked to compare all major LLMs, including Claude, and to pick the best result at a sensible cost.

## D-019. API budget cap

- **Date and source:** 29 Sep 2026, Dion.
- **Decision:**
  - Total API spend for CP2 and CP3 is capped at **US$15**, including the existing DeepSeek balance of US$3.47. It covers the LLM, embeddings, experiments, and demo tests. Hosting is counted separately.
  - Every call is logged (date, purpose, model, tokens, estimated cost; never CV text).
  - Retries and the number of analyzed candidates are limited.
  - Calls stop before the cap is passed. US$15 is a limit, not a target.
  - Do not top up many providers at once.
- **Implementation:** Batch runs are estimated before they start and scheduled in DeepSeek off-peak hours when possible (peak is 08:00-11:00 and 13:00-17:00 WIB on weekdays).
- **Status:** Approved.

## D-020. Embedding model

- **Date and source:** 29 Sep 2026, implementation recommendation for Dion.
- **Recommendation:** OpenAI `text-embedding-3-small` as the only dense-retrieval model in CP2.
  - US$0.02 per 1M tokens. Embedding the whole target corpus is estimated at well under US$0.10.
  - Default 1536 dimensions, one multilingual model, and nothing heavy to load on the server.
- **Cost that needs approval:** a new OpenAI API account with the minimum prepaid purchase of **US$5** (credits expire after 1 year). This counts toward the US$15 cap.
- **Fallback if not approved:** `intfloat/multilingual-e5-small` run locally (384 dimensions). No API cost, but it adds memory, startup time, and image size on the hosting side.
- **Long JD handling:** see System Design v1.3 section 11.
- **Approval:** Dion approved on 29 Sep 2026 and will top up US$5 on a new OpenAI API account.
- **Status:** Approved.

## D-021. Synthetic CVs and real-CV rule

- **Date and source:** 29 Sep 2026, Dion.
- **Decision:**
  - Two to three synthetic CVs are the default for evaluation and the public demo (five from 1 Oct 2026: CV4 and CV5 are added for the test set only, D-045). Dion checks that they are realistic before labeling starts.
  - Dion's real CV is not needed to start. If it is needed later for private testing, it is sent to an external provider only after a separate, explicit confirmation.
  - Indonesian and English support is tested, including an Indonesian CV with English JDs (402 of the 428 target JDs are in English).
- **Update (1 Oct 2026, Dion):** evaluation and the demo use synthetic CVs only. A real CV needs its own explicit consent before it is sent to any provider. The five open privacy design questions are needed before real uploads are built (CP3.1), not for the evaluation.
- **Status:** Approved.

## D-022. Demo path with saved results

- **Date and source:** 29 Sep 2026, Dion.
- **Decision:**
  - The analysis of the synthetic CVs can be computed ahead of time and saved.
  - The page says "Demo with saved results".
  - Saved results are used only for the exact CV, job set, and configuration in the cache key. They are never returned as the analysis of another user's CV.
  - Live and cached runs are measured separately for latency and cost.
  - If a live analysis fails, the page shows the failure or offers the demo mode explicitly.
- **Status:** Approved.

## D-023. Hosting

- **Date and source:** 29 Sep 2026, implementation recommendation for Dion.
- **Recommendation:** Railway as the single platform for FastAPI, Streamlit, and PostgreSQL with pgvector.
  - An early smoke deploy uses the one-time Trial credit (US$5).
  - Then the Hobby plan: US$5 per month, including US$5 of usage.
  - Estimated total: **US$5 to 12 per month**, depending on memory use and whether sleeping is enabled.
  - Set a hard usage limit so the bill cannot run away.
- **Free fallback:** Hugging Face Spaces (Docker). It has enough memory, but it sleeps after 48 hours without use, its disk is not persistent, and outbound connections are limited to ports 80, 443, and 8080, so an external Postgres cannot be reached and Postgres would have to run inside the container.
- **Details:** System Design v1.3 section 16.
- **Approval:** Dion approved Railway on 29 Sep 2026. The Trial credit is used first; the concrete monthly cost is confirmed with Dion before subscribing to the Hobby plan.
- **Status:** Approved.

## D-024. Local development database

- **Date and source:** 29 Sep 2026, implementation.
- **Decision:** Local development uses Docker Compose with a PostgreSQL image that includes pgvector.
  - Dion reported Docker 29.4.3 and Docker Compose v5.1.3 on his Mac. This shows the CLI is installed; whether the engine starts and runs containers is checked on the first run.
  - PostgreSQL is needed early, because the FTS baseline in checkpoint 8 uses PostgreSQL full-text search.
- **Status:** Approved.

## D-025. Feature status

- **Date and source:** 29 Sep 2026, Dion.
- **Decision:**
  - **Out of scope v1:** import link, auto-apply, cover letter, Strong/Realistic/Stretch labels.
  - **Deferred:** second job-data provider, reranker, automatic refresh from JSearch, official support for adjacent roles.
  - **Minimal version:** market insight, and evidence-based CV suggestions.
- **Update (30 Sep 2026):** the minimal CV suggestions are specified in D-036 (CV coach, v1 and later upgrade).
- **Rule:** Removing a minimal-version feature requires its own new entry here, including its impact on Canonical and the Definition of Done. "Supporting feature" does not mean it can be dropped without a recorded decision. Core evaluation, testing, privacy, and deployment are protected.
- **Status:** Approved.

## D-026. Definition of Done v1 and the cut order

- **Date and source:** 29 Sep 2026, Dion.
- **Definition of Done:**
  - A user can enter a CV, get recommendations, open the evidence, and compare a pasted JD.
  - The flow is tested and runs on the deployed app.
  - A demo path exists with synthetic CVs and the fixed snapshot. A failure of an external API does not stop the demo.
- **Cut order when time is short:** first UI polish, then reduce extra experiments (fewer configurations and model comparisons). The reranker, second provider, and automatic refresh are already deferred. Only after that, and with a recorded decision (D-025), the minimal market insight or CV suggestions.
- **Never cut:** core evaluation, tests, privacy, deployment, and the explanation of limitations.
- **Feature freeze:** 8 October 2026. Afterwards only bug fixes, documentation, and presentation work.
- **Status:** Approved.

## D-027. Official dates, revised schedule, and actual dates

- **Date and source:** 29 Sep 2026, Dion.
- **Decision:**
  - Official dates follow the bootcamp Timeline file (checkpoint 8 = 28 Sep, checkpoint 9 = 29 Sep, and so on to checkpoint 21 = 11 Oct).
  - The revised work schedule and the actual completion date are tracked separately in the master plan. Checkpoints 8 and 9 are both worked on 29 September 2026.
  - A stage report stays PLANNED / NOT RUN until the work is actually done.
- **Status:** Approved.

## D-028. API keys for scripts

- **Date and source:** 29 Sep 2026, Dion.
- **Decision:** Project scripts on Dion's Mac may read the API keys from a local `.env` file in `project-job-fit/`. Dion creates and fills this file himself.
- **Rules:** `.env` is listed in `.gitignore`. Keys are never printed, logged, written to other files, committed, or sent to the chat. The usage ledger and the budget guard (D-019) apply to every call.
- **Reason and trade-off:** Scripts can run without the key being typed or pasted anywhere, which matters for the deadline. The trade-off is that scripts run with his keys, so the budget guard must be in place before the first call.
- **Status:** Approved.

## D-029. LLM shortlist and selection rule

- **Date and source:** 29 Sep 2026, Dion. He agreed to add OpenAI models (the OpenAI credit is already approved in D-020) and asked to compare all major LLMs, including Claude, and to choose the best result at a sensible cost.
- **Previous:** D-018 (DeepSeek flash vs pro only).
- **Price screen** (per 1M tokens, standard rates, from the official pricing pages, checked 29 Sep 2026). "Per run" is one recommendation run with K = 20, about 60k input and 14k output tokens.

  | Provider | Model | Input | Output | Per run (estimate) |
  | --- | --- | --- | --- | --- |
  | OpenAI | GPT-6 Luna | US$0.10 | US$0.50 | about US$0.01 |
  | DeepSeek | `deepseek-flash` (off-peak / peak) | US$0.15 / 0.30 | US$0.60 / 1.20 | about US$0.02 / 0.04 |
  | Google | Gemini 3.5 Flash-Lite | US$0.30 | US$2.50 | about US$0.05 |
  | DeepSeek | `deepseek-v4-pro` (off-peak / peak) | US$0.66 / 1.32 | US$1.98 / 3.96 | about US$0.07 / 0.14 |
  | Google | Gemini 3.8 Flash | US$0.75 | US$3.75 | about US$0.10 |
  | Anthropic | Claude Haiku 4.5 | US$1.00 | US$5.00 | about US$0.13 |
  | OpenAI | GPT-6 Sol | US$2.00 | US$10.00 | about US$0.26 |
  | Anthropic | Claude Sonnet 5.5 | US$2.00 | US$10.00 | about US$0.26 |
  | Google | Gemini 3.1 Pro (preview) | US$2.00 | US$12.00 | about US$0.29 |
  | Anthropic | Claude Opus 5.5 | US$4.00 | US$20.00 | about US$0.52 |
  | OpenAI | GPT-6 Astra | US$10.00 | US$50.00 | about US$1.30 |

- **What the price screen can and cannot say:** price is known; quality on JobFit's task is not. Public benchmarks do not measure requirement extraction and evidence matching on Indonesian and English CVs. So quality is decided only by our development set.
- **Round 1 (CP2.3, about 30 development cases, extraction and evidence matching):**
  - Low-cost candidates: `deepseek-flash` (baseline), GPT-6 Luna, Gemini 3.5 Flash-Lite, and Claude Haiku 4.5.
  - Quality reference: GPT-6 Sol on at most 10 hard cases, to see how much quality the low-cost models lose. It is not a production candidate unless the rule below says so.
  - Gemini runs on the free tier for development only. Google may use free-tier content to improve its products, so only synthetic CVs and public job descriptions are sent. If Gemini wins, production needs the paid tier, decided at that point.
  - Claude Haiku 4.5 needs an Anthropic account with prepaid credit. If Dion does not add it, Haiku moves to round 2.
- **Round 2 (only if needed):** `deepseek-v4-pro` and Claude Haiku 4.5 (if not in round 1), when no low-cost model passes the rule, or when the best one is more than 3 points of evidence Macro-F1 below the quality reference.
- **Selection rule, fixed before any result is seen:**
  1. **Safety gate:** zero unsupported claims and 100% valid evidence quotes on the development cases. A model that fails is out.
  2. **Quality:** evidence Macro-F1 first, extraction F1 second.
  3. **Cost:** a cheaper model wins if it is within 0.03 of the best on both Macro-F1 and extraction F1.
  4. **Tie:** lower p95 latency.
  5. The same model is used for extraction and evidence matching, unless a split is at least 0.03 better on one task.
- **Honesty notes:**
  - The development set is small, so differences of a few points can be noise.
  - The assistant tools used during development include models from OpenAI and Anthropic, and both companies have candidates on this list. The same fixed rule is applied to every candidate, and the results are reported as measured.
- **Budget (D-019):**
  - Committed: US$3.47 (DeepSeek) + US$5 (OpenAI) = US$8.47.
  - Anthropic credit, if Dion adds it, would bring this to about US$13.47, still under US$15.
  - Round 1 is estimated at under US$2 of actual use in total.
- **Affects:** System Design v1.3 section 11; Canonical section 17; Playbook checkpoints 8 and 10, section 4A, and section 6; stage report CP2.3.
- **Status:** Approved (shortlist and rule). Claude Haiku 4.5 in round 1 depends on Dion adding Anthropic credit.

## D-030. OpenRouter as the single model gateway

- **Date and source:** 29 Sep 2026, Dion. He wants to try models from different providers freely, as long as they are worth it, cheap, and give the best result.
- **Decision:**
  - All LLM calls and embedding calls go through OpenRouter: one API key and one OpenAI-compatible endpoint (`https://openrouter.ai/api/v1`, chat completions and `/embeddings`).
  - Model ids are stored as OpenRouter ids with the date of each run.
  - The D-029 shortlist and selection rule stay the same. Any other model on OpenRouter may be added to a round if it looks worth testing, but only through an entry in the docs/experiments.md matrix, so the number of candidates stays under control.
- **Technical rules:**
  - Structured output uses `response_format` with a JSON schema and `strict: true`.
  - Provider routing uses `require_parameters: true`, so a request is only sent to endpoints that support the schema.
  - Pydantic validation still runs on every output.
- **Privacy:** In OpenRouter settings, prompt logging stays off, and providers that train on user data are excluded. Only synthetic CVs and public job descriptions are sent (D-021).
- **Changes to earlier entries:**
  - D-020: the embedding model stays `text-embedding-3-small`, called as `openai/text-embedding-3-small` through OpenRouter. A direct OpenAI account is not needed.
  - D-028: `.env` holds `OPENROUTER_API_KEY`. `DEEPSEEK_API_KEY` stays as an optional direct fallback, since the existing US$3.47 DeepSeek balance can still be used.
  - D-029: all candidates, including Claude Haiku 4.5, Gemini 3.5 Flash-Lite, and GPT-6 Luna, are reached through OpenRouter. The Gemini free tier and separate Anthropic or OpenAI accounts are no longer needed.
- **Cost:** OpenRouter passes provider prices through and charges a fee when credit is bought (5.5% for pay-as-you-go, per a third-party summary dated 14 Sep 2026; checked again at purchase). The OpenRouter top-up counts toward the US$15 cap (D-019). Recommended: start with US$5 and top up only when the usage ledger shows it is needed.
- **Trade-off:** One more company sits between JobFit and the model providers. In return, there is one key, one bill, and switching models is a configuration change instead of new code.
- **Status:** Approved.

## D-031. OpenRouter only, and a budget guard that follows the real credit

- **Date and source:** 29 Sep 2026, Dion. He removed `DEEPSEEK_API_KEY` from his `.env` because the project uses only OpenRouter, and he asked why the budget settings said US$15 and US$14 when the first top-up is US$5.
- **Decision:**
  - OpenRouter is the only gateway. There is no direct DeepSeek fallback. DeepSeek models can still be tested, but through OpenRouter like every other model.
  - The existing DeepSeek balance (US$3.47) is no longer part of this project and is not counted in the cap.
  - D-019 stays as the **project ceiling**: all OpenRouter top-ups for CP2 and CP3 together may not pass US$15. A new top-up needs Dion's approval and a reason from the usage ledger.
  - The app's budget guard follows the **credit actually bought**, not the ceiling:
    - `API_BUDGET_USD` = the OpenRouter credit available for JobFit, rounded down (now US$9; the balance is US$9.22).
    - `API_HARD_STOP_USD` = that amount minus a US$0.50 safety margin (now US$8.50).
    - Both values are raised in `.env` only after an approved top-up.
- **Where budget limits live (three layers):**
  1. **OpenRouter prepaid credit.** Calls fail when the balance is used up, so real spending cannot pass what was bought.
  2. **OpenRouter key limit.** The API key gets a credit limit in the OpenRouter settings (now US$8.50). This key is used only for JobFit, so the ledger and the OpenRouter balance stay comparable. A later production key for the Railway demo gets its own, smaller limit.

  3. **App budget guard (D-019).** Reads the two values from `.env`, stops a call before it happens, and writes the usage ledger, so each experiment's cost is known.
  Limits are configuration, not code. The code only holds safe default values equal to `.env.example`.
- **Changes to earlier entries:**
  - D-019: the cap is now counted on OpenRouter top-ups only, and the DeepSeek off-peak scheduling no longer applies.
  - D-028 and D-030: `.env` holds only `OPENROUTER_API_KEY` for model calls.
- **Affects:** `.env.example`, `src/jobfit/config.py`, System Design v1.3 section 11, master plan section 6.
- **Status:** Approved.

**4 October 2026 addendum (D-070):** The figures above are historical. Dion reported about US$19.22 total credit bought after adding US$10. The configured local numbers verified before pipeline v1.1 were `API_BUDGET_USD=19` and `API_HARD_STOP_USD=18.5`. The new project ceiling is the credit actually bought, as recorded in D-070. The provider balance and OpenRouter key limit were not independently verified in this local check.

## D-032. Soft skills are shown separately, not in the match %

- **Date and source:** 30 Sep 2026, Dion (pilot question Q1).
- **Context:** In the pilot, J1 had 14 required units and 9 were soft skills (problem solving, teamwork, initiative, and others). CVs rarely contain evidence for these, and the guideline forbids inferring personal traits, so they are almost always NO_MATCH. With the first model-draft labels, CV1 x J1 scored 53.6% with soft skills and 90% without them.
- **Decision:**
  - Units with `category = soft_skill` are still extracted and still labeled, but they are **not** in the match % denominator.
  - They are shown on the same job card, directly under the score, for example: "Soft skills asked: 9. With evidence in the CV: 3 points. Not part of the percentage."
  - Guideline v1 defines a soft skill as a personal trait or general behavior (teamwork, initiative, general communication). Things that can be shown with evidence stay in the score under their own category: a language (`language`), leading a team (`experience_duration` or `other`), presenting to stakeholders as part of a job.
  - The denominator is always shown ("x of y required requirements"), so a small denominator is visible.
- **Reason (Dion):** the score should focus on abilities that the CV can prove. CVs rarely write evidence for soft skills, so counting them lowers almost every score without saying anything useful about fit.
- **Trade-off:** companies that stress character are less visible in the main number. This is reduced by showing soft skills on the same card.
- **Check:** the code keeps both versions. In CP2 both are compared with Dion's relevance labels (NDCG@10); if the version with soft skills orders jobs better, the result is reported as measured.
- **Changes:** D-006 (denominator).
- **Affects:** guideline v1, `src/jobfit/scoring/score.py`, System Design v1.3 section 8, result page.
- **Status:** Approved.

## D-033. Location and work authorization are constraints, not score units

- **Date and source:** 30 Sep 2026, Dion (pilot question Q16).
- **Decision:**
  - Units with `category = location` or `work_authorization` are extracted but never enter the match %. They feed the constraint line (compatible / unknown / explicit conflict, D-013).
  - The warning shows the **original JD sentence**, for example "Bandung: Reliably commute or planning to relocate before starting work (Required)".
  - The warning appears on the job card and on the job detail page, before the link to apply.
  - The state is compared only with a location the user confirmed, never with the city read from the CV (D-010).
- **Reason (Dion):** the user must know before applying that the job needs a move or daily commute. Finding out only at the interview wastes the user's time and hurts them. Reading one more line is fine because it protects the user.
- **Affects:** guideline v1, scoring code, result page, System Design v1.3 sections 8 and 9.
- **Status:** Approved.

## D-034. Splitting JD lists depends on the wording

- **Date and source:** 30 Sep 2026, Dion (pilot question Q6). The first proposal treated "including" as examples; Dion disagreed because "Strong knowledge of ..." shows the company wants each area, and this entry follows his reasoning.
- **Decision (rules for guideline v1):**

  | Wording in the JD | Units |
  | --- | --- |
  | Strength word (strong, deep, solid, proficient, expert, kuat, mendalam) + "including / termasuk" + list | Split; every item is its own unit with the same importance |
  | "such as / seperti / e.g." + "or / atau", or a list ending with "etc / atau sejenisnya / lainnya" | One unit with alternatives; any one item, or an equivalent tool, is enough |
  | Light word (familiar with, basic understanding, exposure to, pemahaman dasar) + list | One unit; evidence for one item is enough |
  | "and / dan" in a requirement list | Split; all required |
  | "or / atau" | One unit with alternatives |
  | Unclear | Split, set `importance = unknown`, and write the reason in `notes` |

- **Example:** "Strong knowledge of AI technologies, including machine learning, natural language processing, and computer vision" becomes three required units.
- **Limitation:** words like "strong" also describe a level. v1 checks only whether evidence of use exists, not how strong it is (D-035).
- **Affects:** guideline v1, extraction prompt v1, pilot labels (the model drafts already follow these rules).
- **Status:** Approved. The table is simplified by D-039: the conjunction decides the count, and strength or light words only describe level.

## D-035. Evidence strength in v1

- **Date and source:** 30 Sep 2026, Dion (pilot question Q2 and the discussion that followed).
- **Decision:**
  - A skill that appears **only in a skills list**, without a sentence showing its use, is PARTIAL. This includes simple tools such as Git. MATCH needs use in work, a project, study, or research, with context.
  - This is **not** distrust of the user. It follows how a recruiter reads a CV, it keeps the skill-gap output useful, and it stops scores from being raised by long skill lists.
  - The message to the user is supportive, for example: "NLP: only listed in your skills. Add an example of a project or job where you used it to make it stronger."
  - **Assumption written in the documents:** the system does not verify whether CV content is true. The user is responsible for what the CV says.
  - **Limitation:** v1 does not measure proficiency depth ("strong", "expert"). One clear example of use counts as MATCH. Measuring depth is a later upgrade.
- **Affects:** guideline v1, evidence-matching prompt v1, result page text, evaluation report limitations.
- **Status:** Approved.

## D-036. CV coach feature: minimal in v1, full coach later

- **Date and source:** 30 Sep 2026, Dion. Dion proposed a coach that asks the user about their projects and turns the answers into CV bullet points, similar to the suggestions in LinkedIn Premium.
- **Relation to earlier decisions:** this is the fuller version of the minimal evidence-based CV suggestions in D-025, Canonical section 16 (support status `NEEDS_USER_EVIDENCE`), and the `/tailor` endpoint in System Design v1.3. The plan is in [cv-coach-plan.md](cv-coach-plan.md).
- **Decision:**
  - **Priority:** matching is the main feature and is finished first. The CV coach is built only after matching is complete and stable. It stays first in the cut order (System Design v1.3 section 18).
  - **v1 (minimal, CP3.1 or later if time allows):** for one job the user picks, at most three of the most important gaps; three to four fixed questions per gap (what and when, own role, tools or methods, result or number); one or two suggested CV bullets per gap; the user can accept, edit, reject, or copy.
  - **Rules:**
    - A bullet may contain only facts from the user's answers. Every part points to its source answer. Numbers appear only if the user gave them. Target: unsupported claims = 0.
    - If the user says they have not done it, no bullet is written. The system gives learning or project ideas instead.
    - Answers never change the score. The score changes only after the user updates the CV and uploads it again. Answers are stored as user statements, only for the session, and pass the same privacy rules as the CV.
  - **Later upgrade (after v1 and after 11 Oct if needed):** free multi-turn coaching, many jobs at once, rewriting whole CV sections, export to .docx, and tests with real users.
- **Evaluation for v1:** about 10 scenarios; unsupported claims = 0; every bullet cites a user answer; "not done" answers produce no bullet.
- **Affects:** D-025 (spec of the minimal feature), CP3.1 report, `prompts/cv_suggestions_v1.md`, README roadmap.
- **Status:** Approved.

## D-037. Relevance labels are judged in automatic mode

- **Date and source:** 30 Sep 2026, Dion (pilot question Q9).
- **Context:** The pilot workbook had a `cv_target` column with a narrow target per CV (added when the workbook was built). The model draft followed it literally and gave 0 to 8 of 10 pairs only because the job title was outside that narrow target, even when the CV had relevant evidence.
- **Decision:**
  - Relevance 0 to 3 is judged as in automatic mode: the target is the four target role families (AI/ML engineering, data science, GenAI/LLM, software AI).
  - 0 is only for jobs outside those four families, or with almost no requirement supported. Inside them, the label follows CV evidence and constraints (D-014).
  - A role-family filter chosen by the user removes jobs from the list; it is not expressed through relevance 0.
  - `cv_target` stays in the workbook as a preference note, not as a labeling rule.
- **Reason (Dion):** relevance means fit to the CV evidence, the same rule the system uses.
- **Affects:** guideline v1 Part D, pilot sheet C_Relevance (to be relabeled), evaluation (NDCG@10, P@5).
- **Status:** Approved.

## D-038. Labeling workflow: model drafts, Dion verifies

- **Update (30 Sep 2026):** the workbook fields were renamed from `ai_suggested` / `status` to `label_source` (`model_draft` / `annotator`) and `review_status` (`pending` / `approved`). The tools behind each role are listed only in [annotation-workflow.md](annotation-workflow.md), not in data cells.

- **Date and source:** 30 Sep 2026, Dion. He proposed letting a language model draft most labels and checking the results himself. The safeguards below were added in the design review and approved by Dion.
- **Previous:** D-015 and D-016 (single annotator with model drafts; only reviewed labels are gold).
- **Decision:**
  - A language model writes draft labels (`label_source = model_draft`, `review_status = pending`) following the current guideline version.
  - Dion reviews every row and records `review_action` (`accepted`, `edited`, `rejected`, `added`). Only rows he reviewed become `approved`. Edits and rejections have a short reason in `review_note`.
  - **Blind sample:** about 10% of items are labeled by Dion without seeing any model draft (first item: pilot J4 extraction). Agreement between the model draft and Dion on these items is reported.
  - **Acceptance rate** (share of `accepted` rows) is reported. A rate near 100% is treated as a warning sign of shallow review.
  - **Roles:** the drafting model only writes draft labels in the labeling workbook. A separate QA check reviews the drafts and the annotator's rows. Dion makes the decisions and reviews labels. Only one assistant edits a given file at a time. The tools are listed in [annotation-workflow.md](annotation-workflow.md).
  - Rule questions (such as Q1 to Q9 in the pilot) are decided by Dion, never by the model that drafts the labels.
- **Known limitation:** the drafting model is an OpenAI model and some LLM candidates in D-029 are also OpenAI models. Labels drafted by one model family may favor similar models. The blind sample and Dion's edits reduce this; the limitation is written in the evaluation report.
- **Time:** Dion's review time per item is measured in the Timing sheet and used for the gold-set size decision.
- **Affects:** pilot workbook, guideline v1, gold-set plan, evaluation report.
- **Status:** Approved.

## D-039. The conjunction decides how a JD list is split

- **Date and source:** 30 Sep 2026, Dion (pilot question Q17, found in the J4 blind extraction).
- **Problem:** two rows of the D-034 table disagreed for a light word followed by an AND list, for example "Familiarity with REST APIs, Git, Docker, and CI/CD practices" and "Working knowledge of SQL and NoSQL databases".
- **Decision:**
  - **AND / dan** between items: split; every item is its own unit with the same importance.
  - **OR / atau**, **such as / seperti / e.g.** with "or", or a list ending with **etc / atau sejenisnya / lainnya**: one unit with alternatives; any one item is enough.
  - Words like strong, good, familiar, working knowledge describe the **level** only. v1 does not measure level (D-035), so they do not change the number of units.
  - Unclear cases: split, `importance = unknown`, reason in the note.
- **Consistency with D-034:** "Strong knowledge of AI technologies, including machine learning, natural language processing, and computer vision" still gives three units, because the list uses AND.
- **Applied to:** J4-U12 becomes four units (REST APIs, Git, Docker, CI/CD); J4-U13 becomes two units (SQL, NoSQL).
- **Affects:** guideline v1.1 section A4, extraction prompt v1, pilot J4 rows.
- **Status:** Approved.

## D-040. Exception: a list of experience areas is split per area

- **Date and source:** 30 Sep 2026, Dion (QA check D1 on the J4 blind extraction).
- **Case:** J4 says "Experience building AI applications in areas such as Natural Language Processing (NLP), Computer Vision, Recommendation Systems, or Generative AI." Under D-039 this would be one unit with alternatives. Dion labeled it as four required units.
- **Decision:**
  - When a requirement asks for **experience in a list of areas or domains** (experience building X in areas such as A, B, or C; pengalaman di bidang A, B, atau C), each area is its own **required** unit, even when the list uses "such as ... or".
  - The exception covers **areas of experience only**. Lists of tools, frameworks, languages, and platforms still follow D-039 ("such as PyTorch, TensorFlow, or XGBoost" stays one unit with alternatives).
- **Reason (Dion):** a requirement section that lists areas of experience shows the kinds of projects the company expects a candidate to have done; for a role asking for several years of experience, it is reasonable to expect work across all listed areas.
- **Other view recorded:** the QA check recommended one unit, because the sentence uses "such as ... or" and the J4 minimum is 2 years (2 to 5 years). Treating every area as required can lower scores for candidates who match only some areas.
- **Check:** the effect is visible in the evaluation. If ordering by match % disagrees with Dion's relevance labels on jobs with such lists, this rule is revisited with data.
- **Applied to:** J4-U08 to J4-U11 stay four required units.
- **Affects:** guideline v1.1 section A4, extraction prompt v1.
- **Status:** Approved.

## D-041. Pilot review decisions (A_Extraction and B_Evidence)

- **Date and source:** 1 Oct 2026, Dion, reviewing the model drafts for J1, J2, J3 and the evidence for CV1 x J1 and CV2 x J2 (with help from the pre-annotation assistant for alignment and technical fixes).
- **Scope:** these are **decisions on specific pilot cases**. They are not general rules. Where a general rule is still needed, it is listed as an open question (Q18 to Q21) and is not applied to other jobs until Dion decides it.

### Extraction (A)

| Unit | Decision | Reason (Dion) |
| --- | --- | --- |
| J1-U01 "1-2 years ... Fresh graduate are welcome to apply." | `unknown`, `min_years = 1` | The two statements are in the same sentence and their relation is unclear. The minimum is recorded as written; it is not changed to 0 and not treated as preferred |
| J1-U04, J1-U20, J1-U21 "Intermediate Mathematical, Statistical, and/or Machine Learning skills required, and their real-world advantages/drawbacks." | Three required units (mathematics, statistics, machine learning), no group | Each area is checked on its own, and the JD says "skills required". **Case decision:** "and/or" is ambiguous, and this is the reviewer's interpretation. Other "and/or" lists are decided case by case |
| J2-U02, J2-U10, J2-U11 "Strong knowledge of AI technologies, including machine learning, natural language processing, and computer vision." | Three required units, no group | Follows D-034 and D-039 (AND list). Depth ("strong") is not measured in v1 (D-035) |
| J2-U12 "S1 (Required)" | `required` | Explicitly marked Required. The level (S1) is judged apart from the field (J2-U01). The difference with "Diploma/Degree" is noted |
| J2-U08 "AI Developer: 1 year (Required)" | `required`, `min_years = 1` | A specific, explicitly Required item is not cancelled by the general "fresh graduates welcome". It asks for relevant experience as an AI Developer, not general work or a skills list |
| J2-U07 "For Senior position, at least 3 years ..." | `unknown`, condition kept | Applies only to the senior track, never to every applicant |

J1-U01 and J2-U08 differ on purpose: in J1 the softener is in the same sentence as the minimum; in J2 the requirement is a separate line marked "(Required)". Whether this becomes a general rule is Q18.

### Evidence (B)

| Case | Decision |
| --- | --- |
| Experience below a minimum | PARTIAL when relevant evidence exists but does not meet the whole requirement; NO_MATCH only when no relevant evidence is found |
| CV1 x J1-U04 (mathematics) | PARTIAL, Education: courses support mathematics only indirectly; no use is shown. The intermediate level is not measured in v1 |
| CV1 x J1-U20 (statistics) | MATCH, Experience: "Membimbing 40 mahasiswa dalam praktikum regresi menggunakan R." |
| CV1 x J1-U21 (machine learning) | MATCH, Projects: churn project (logistic regression, random forest, F1, SMOTE, SHAP) |
| CV2 x J2-U07, J2-U08 (experience) | PARTIAL: AI projects exist, but the CV does not prove the minimum. Project dates (2025, Jul 2026, Aug 2026) do not give a full duration; marketing experience is not AI Developer experience; no exact duration or explicit conflict is inferred from one project date |
| CV2 x J2-U12 / J2-U01 (education) | S1 level MATCH; CS/IT/Computer Engineering field NO_MATCH (S1 Communication) |
| CV2 x J2-U09 (location) | PARTIAL, needs_clarification: living in Bandung does not prove readiness to commute or relocate |

### Honest limits of these decisions

- **Statistics and ML (J1-U20, J1-U21) are MATCH on evidence of use.** The units keep "real-world advantages/drawbacks", and the CV does not explain trade-offs. The MATCH label therefore does not claim that every part of the JD sentence is proven. Guideline B1 says a compound unit with only part shown is PARTIAL; whether these words are a separate part or a level qualifier (not measured, D-035) is Q19.
- **`check_status = done` on CV2 x J2-U07 and J2-U08 records that the label was judged; it does not mean the candidate's actual duration is verified.** Guideline B6 would suggest `needs_clarification` for a duration only the user can state (Q20).
- One annotator reviewed model drafts. This is not multi-annotator labeling, and none of these items may enter the held-out test set.

- **Open questions:** Q18 (softener versus explicit Required), Q19 (level qualifiers in compound units), Q20 (check_status for unbounded duration), Q21 (when a duration shortfall is an explicit conflict, and whether projects count toward a role duration).
- **Affects:** pilot workbook, guideline v1.1 case notes, CP2.1 report.
- **Status:** Approved as case decisions. The general rules are in D-042.

## D-042. General rules from the pilot review (Q18 to Q21)

- **Date and source:** 1 Oct 2026, Dion. He agreed with the QA proposals for Q18 to Q21 and added how work experience is counted.
- **Decision:**
  1. **Q18, softener versus explicit Required.** If a softener ("fresh graduates welcome", "Diploma/Degree") is in the **same sentence** as a requirement, importance is `unknown`. If a **separate item is explicitly marked "(Required)"**, it stays `required`, and the conflict is written in the note.
  2. **Q19, level qualifiers.** Words that describe level or depth inside a unit ("intermediate", "strong", "real-world advantages/drawbacks") are not separate parts of the unit. v1 does not measure them (D-035), so clear evidence of use is MATCH. The "compound unit" rule in guideline B1 applies only to parts that can be checked on their own (for example a skill and a duration).
  3. **Q20, unbounded duration.** When a required duration cannot be bounded from the CV (dates missing or incomplete for the relevant work), `check_status = needs_clarification`. The score treats it the same; the app asks the user.
  4. **Q21, experience minimums and explicit conflict.**
     - A minimum of **work experience** in a field or role counts only **employment in that same field**, summed across companies, without counting overlaps twice. Projects, a thesis, courses, and bootcamps do **not** count toward it; they can still be relevant evidence (PARTIAL).
     - A **complete dated work history is an upper bound.** If even the most generous reading of the employment periods is below the minimum, the constraint is `explicit_conflict`. If dates are missing or the relevant period cannot be bounded, it is `unknown`.
- **Effect on the pilot:** CV1 x J2 and CV1 x J3 relevance drafts become 1; CV2 x J3 becomes 1. CV2 x J2 and CV2 x J4 depend on whether marketing analytics counts as the same field (see the C_Relevance drafts). The B labels do not change; PARTIAL still means relevant evidence that does not meet the requirement.
- **Affects:** guideline v1.2 (A7, B1, B6, Part C), evidence-matching prompt v1, `src/jobfit/matching/constraints.py` (CP2.2: count employment in the field only), pilot C drafts.
- **Status:** Approved.

## D-043. Gold-set sizes from the pilot timing

- **Date and source:** 1 Oct 2026. Proposed from the pilot timing; Dion has about **2 hours** for labeling before 3 Oct morning.
- **Measured time (single annotator, model drafts reviewed; approximate, reported by Dion):**

  | Task | Time | Per item |
  | --- | --- | --- |
  | Blind extraction, J4 (no draft) | 60 min for 13 units | 4.6 min per unit |
  | Review of extraction drafts, J1 to J3 | about 60 min for 50 units | 1.2 min per unit (about 20 min per JD) |
  | Review of evidence drafts | about 40 min for 34 rows | 1.2 min per row (about 20 min per CV-job pair) |
  | Review of relevance drafts | about 24 min for 10 labels | 2.4 min per label |

  Reviewing drafts was about 3.8 times faster than blind extraction. Model drafting and QA check time is not counted.
- **Original targets (Canonical):** extraction about 50 JDs, evidence about 100 requirement-evidence pairs, ranking 40 to 60 jobs. At the measured speed this needs about 19 hours of annotator time, which does not fit the schedule.
- **Proposed sizes:**

  | Set | Extraction | Evidence | Relevance |
  | --- | --- | --- | --- |
  | Development (pilot, done) | 4 JDs, 71 units | 2 CV-job pairs, 34 rows | 10 labels (CV1, CV2 x J1 to J5) |
  | Held-out test (new, about 112 min) | 1 JD (about 20 min) | 1 CV-job pair on that JD (about 20 min) | 3 CVs x 10 jobs = 30 labels (about 72 min) |
  | **Total** | **5 JDs** | **3 pairs, about 50 rows** | **40 labels** |

- **Why this split:** the main metric is the ranking quality (NDCG@10, P@5, D-017), so most of the time goes to relevance labels for the test pool. Extraction and evidence keep a small test sample so the development numbers can be checked once on unseen data.
- **Test pool design:**
  - 10 jobs per CV from the 428 target jobs, none from the pilot jobs or their dedup clusters.
  - Each pool mixes: top results of the stage-1 methods, jobs that suit the CV level (entry or junior), and hard negatives (an adjacent or non-target role, 5+ years for a beginner, a JD with many unknown fields). The pilot showed 7 of 10 labels at 1; without suitable jobs, NDCG and P@5 cannot separate good from bad orderings.
  - **CV3 (Dewi) is used only in the test set** (no development labels), so one CV is completely unseen during tuning.
  - Model drafts are reviewed by Dion with time recorded (D-038). The job IDs are fixed in `evals/splits/test_job_ids.txt` before any tuning in CP2.3.
- **Mandatory coverage (System Design v1.3 section 15):** the 8 development cases are covered by the code fixtures; an Indonesian CV with English JDs (CV1) is in both sets; hard negatives and a JD with many unknown fields are in the test pool; prompt injection is covered by tests in CP3.4, not by gold labels.
- **Impact on conclusions:** the sets are small. Results are reported with the denominators, per CV, and with bootstrap confidence intervals, and they are described as indicative for this corpus, not as general accuracy. Extraction and evidence results on one test JD are a sanity check only.
- **Status:** Superseded by D-045 on 1 Oct 2026. Dion asked for larger sets because 1 JD and 1 CV-job pair are too small for a meaningful test.

## D-044. Model benchmark protocol and a second embedding candidate

- **Date and source:** 1 Oct 2026. Dion asked where the LLM and embedding models are compared on quality and cost, and asked for an industry-standard approach. Proposed for his approval.
- **Context:**
  - The LLM comparison is already planned: shortlist and price screen in CP2.1 (D-029), measured comparison in CP2.3 (plan M06, M07).
  - The embedding model was chosen without a comparison (D-020). The plan only compares search methods (B0, B1, dense, hybrid; M04) and checks the Indonesian CV (H7, M09) with that one model.
  - Common practice for both kinds of model: use public leaderboards and prices only to make a shortlist, then decide on the project's own labeled data, and report quality, cost, and latency together.
- **Proposal: three steps, each in a fixed stage.**

  | Step | Stage | What happens | Uses |
  | --- | --- | --- | --- |
  | 1. Screen | CP2.1 (done for the LLM, D-029; embeddings below) | Shortlist from price, context length, language support, and data policy. Selection rule written before any result | Public information only |
  | 2. Compare | CP2.3 | Every candidate runs on the same development cases with the same prompt or input. Quality metric, cost per run from the usage ledger, p50/p95 latency, schema validity, and failures go in one table. The rule picks the winner | Development set only |
  | 3. Confirm | CP2.4 | Only the chosen configuration runs once on the held-out test set. Cost and latency are reported live and cached | Test set, once |

- **Embedding shortlist (OpenRouter prices checked 1 Oct 2026; checked again before the run):**

  | Model | Price per 1M tokens | Dimensions | Why |
  | --- | --- | --- | --- |
  | `openai/text-embedding-3-small` | US$0.02 | 1536 | Current choice (D-020), the baseline |
  | `qwen/qwen3-embedding-8b` | US$0.01 | 4096 | Open weights and listed as multilingual; tests whether the Indonesian CV is matched better (H7) |

  The whole EDA corpus (632 jobs) is about 0.5M tokens, so embedding it with both models costs under US$0.05. A larger model (`openai/text-embedding-3-large`, US$0.13) is added only if both candidates miss many relevant jobs.
- **Selection rule for the embedding model, fixed before any result:**
  1. Main metric: stage-1 Recall@20 on the development relevance labels, inside the dense and the hybrid search.
  2. A model wins only if it is at least 0.05 better; otherwise the cheaper or current model stays.
  3. The Indonesian-CV gap (H7) is reported for both models.
- **Labels for the comparison (the trade-off to decide):** the development set has only 10 relevance labels on 5 jobs. That is too few to compare embedding models, and also too few for the planned stage-1 method and K choices (M04, M05). Two options:
  - **A. Silver labels for development:** the drafting model rates the top results of every stage-1 method for CV1 and CV2 (about 40 to 60 pairs), and Dion spot-checks 10 of them (about 25 minutes). These labels are used only for tuning and are reported as silver, never as gold.
  - **B. No new labels:** keep D-020 and use hybrid search (RRF) with K = 20 as the default without tuning. Every stage-1 method is still measured on the test pool in CP2.4, as a measurement only, not to choose. The embedding choice is reported as not compared.
- **Effect on the test pool (D-043):** the test pool takes the top results of every stage-1 method, including the dense search with each embedding candidate, so no method is favored because only its results were labeled. The pool is therefore picked after the embeddings exist (CP2.2), and locked before CP2.3.
- **Technical notes:** if A is approved, `job_embeddings` gets a model id column and room for the 4096-dimension vectors (it is fixed at 1536 now). With 632 jobs an exact search is fast, so no vector index is needed. Provider routing keeps `data_collection: deny` (D-030); only public JDs and synthetic CVs are sent.
- **Affects:** plan M04 and M09 in experiments.md, master plan CP2.2 and CP2.3, D-043 test pool, System Design v1.3 section 11.
- **Status:** Approved on 1 Oct 2026, option A. Dion's conditions: the drafting model writes silver labels; only rows Dion reviews and approves become gold; unreviewed rows stay silver, and a spot check never turns a whole batch into gold; silver is used for exploration only, and every configuration choice is confirmed on the development gold. Sizes and process: D-045, D-046.

## D-045. Gold-set sizes v2, silver labels, and a phased labeling plan

- **Date and source:** 1 Oct 2026, Dion. He asked for larger sets (development: 10 to 15 JDs, 60 to 100 evidence units, 60 to 90 relevance pairs; test: 5 to 8 JDs, 40 to 60 evidence units, 30 to 45 relevance pairs) as a starting target, checked against the pilot timing and the deadline. The drafting model may help; Dion reviews.
- **Previous:** D-043 (1 test JD, 1 test CV-job pair, 30 test relevance labels).
- **Terms:**
  - An **evidence pair** is one CV x one JD. It holds one evidence row per requirement unit of that JD (about 17 rows on average in the pilot). An **evidence unit** is one row.
  - **Gold** = reviewed and approved by Dion. **Silver** = model draft that Dion has not reviewed. Silver is stored apart from gold and is used only to explore (D-044).
- **Time per item used for the plan:**

  | Task | Per item | Source |
  | --- | --- | --- |
  | Review of an extraction draft | about 20 min per JD (1.2 min per unit) | Pilot, measured |
  | Review of evidence drafts | about 20 min per CV-JD pair (1.2 min per row) | Pilot, measured |
  | Review of a relevance draft | 2.4 min per label | Pilot, measured |
  | Blind extraction | about 50 to 60 min per JD | Pilot J4, one JD (60 min, first time) |
  | Blind evidence | about 3.5 min per row, about 60 min per pair | Estimate (same ratio as extraction); measured on the first pair |
  | Blind relevance | about 3.5 min per label | Estimate; measured on the first 10 labels |

  A QA fix round adds about 10 to 15%.
- **Feasibility of the requested targets** (test labeled blind): the lower targets need about 13 hours of Dion's time (development 4.5, test 8.5) and the upper targets about 22 hours (development 8, test 13.5). The plan assumes about 5 hours before tuning (to 2 Oct), about 3 hours on 3 Oct, and more time on 4 to 7 Oct before the feature freeze (8 Oct); Dion confirms these hours. So the plan below keeps the development targets near their lower end, keeps the test relevance at the upper end (the main metric), and moves part of the test extraction and evidence work after the CP2 presentation.
- **Update (1 Oct 2026, evening):** Dion has 2 to 3 hours per day for labeling and approved two more synthetic CVs for the test set (CV4, CV5). The sizes and phases below replace the first version of this entry.
- **Recommended final sizes (historical relevance test target; D-053 replaces fixed 60 with top 10 union):**

  | Set | Extraction | Evidence | Relevance |
  | --- | --- | --- | --- |
  | Development gold | 7 JDs (4 pilot + 3 new), about 120 units | 4 pairs (2 pilot + 2 new), about 68 rows | 50 labels (10 pilot + CV1 and CV2 x 20) |
  | Development silver | none | none | the rest of the development pool (about 40 to 80 pairs) |
  | Test gold | 4 JDs: 2 blind, 2 from model drafts | 3 pairs (CV3 x T1 blind; CV1 x T3 and CV2 x T4 from drafts), about 50 rows | 60 labels (CV1 to CV5 x 12), all blind |

  Compared with Dion's starting targets: development extraction and relevance are a little below the lower end, evidence is inside the range, and test relevance is above it. More CVs (queries) matter more for the ranking metric than more jobs per CV, so the extra time goes to CV4 and CV5.
- **Dion's time (estimate, 2 to 3 hours per day):**

  | Phase | When | Work | Time |
  | --- | --- | --- | --- |
  | 1. Development | 2 Oct (and early 3 Oct) | 40 relevance labels (96 min), 3 extraction JDs (60 min), 2 evidence pairs (40 min), QA fixes | about 3.5 h |
  | 2. Test relevance, CV1 to CV3 | 3 Oct, after the configuration is frozen | 36 blind labels | about 2 h |
  | 3. Test expansion | 5 to 7 Oct | review CV4 and CV5 (30 min), 24 blind relevance labels for CV4 and CV5 (85 min), 2 blind extraction JDs (100 min), 2 reviewed JDs (40 min), 1 blind evidence pair (60 min), 2 reviewed pairs (40 min) | about 6 h |
  | **Total** | | | **about 11.5 h** |

- **What is reported when:**
  - CP2.4 (3 Oct): ranking metrics (NDCG@10, P@5, safety) on the test relevance labels of CV1 to CV3. Extraction and evidence metrics on the development gold, marked as development numbers (optimistic, because prompts and models were chosen on them).
  - Final report (CP3.5): the same frozen configuration on the full test set (CV1 to CV5, test extraction and evidence). The configuration frozen in CP2.6 is not changed because of these results; a bug fix is recorded and the whole test set is run again.
  - Test extraction and evidence results are reported separately for the blind items and the model-draft items.
  - If phase 2 cannot finish on 3 Oct, the CP2 presentation shows development results, clearly marked, and the test run moves to 5 Oct.
- **Minimum if time runs out:** development relevance 30 gold, test relevance 36 (CV1 to CV3 only), test extraction 2 blind JDs, test evidence 2 pairs. The conclusions then say so.
- **Limits that stay:** three CVs are three queries, so ranking results are shown per CV with bootstrap intervals and called indicative. One annotator. The drafting model is from the same family as some LLM candidates (D-038); the blind test items limit this effect.
- **Status:** Approved on 1 October 2026 by Dion: sizes above, 2 to 3 hours per day, and the fallback if test labeling is not finished before CP2.

## D-046. Development/test split rules and the blind-first test labeling

- **Date and source:** 1 Oct 2026, Dion (rules 1 to 5); implementation choices marked below.
- **Rules (approved):**
  1. A JD and its duplicates are never in both splits.
  2. The pilot jobs stay in development.
  3. CV3 (Dewi) is used only with the test split. The same holds for CV4 and CV5 (added 1 Oct): they are written before the test pool exists, without looking at test jobs, and are never used in tuning.
  4. Test labels and test results are never used to choose the model, prompt, weights, or K.
  5. Test gold is labeled blind first: Dion gives his labels without seeing any model draft. Afterwards the drafting model only checks quotes, completeness, and rule consistency; Dion decides every change. Any test item that starts from a model draft is marked `label_source = model_draft` and reported separately.
- **Implementation (proposed, Dion may change):**
  - The 428 target jobs are split by job cluster into two halves with a fixed random seed, stratified by `role_family` and `experience_bucket`. The 5 pilot jobs are forced into development. Probable-duplicate pairs from the CP1 dedup review are kept on the same side.
  - The split is written to `evals/splits/dev_job_ids.txt` and `evals/splits/test_job_ids.txt` before any tuning and is not changed afterwards.
  - Development pools: for CV1 and CV2, the top 10 of every stage-1 candidate (B0, B1, dense and hybrid with both embedding models) inside the development half. Gold review covers every job in the top 5 of any method first, then random others up to 20 new labels per CV.
  - **Historical, superseded by D-053:** Test pool: for each test CV (CV1 to CV5), the top 12 of the frozen configuration inside the test half, picked after CP2.3 ends. Jobs ranked lower that move into the final top 10 are reported as unjudged; NDCG@10 is computed on the judged jobs (condensed list), and the number of unjudged jobs is shown.
  - Relevance 2 or 3 counts as relevant for P@5 and Recall@K (System Design v1.3 section 14).
- **Trade-off:** each half has about 214 jobs, so stage-1 search in tuning and in testing runs on half of the corpus. K chosen on 214 jobs may act a little differently on 428; this is stated in the report.
- **Status:** Approved (rules 1 to 5). Implementation choices take effect unless Dion changes them before the split is written.

## D-047. Development batches use complete drafts followed by human review

- **Date and source:** 1 October 2026, Dion's direct answer to the development blind-sample question: prepare every draft carefully; he will review the work afterwards.
- **Reason:** Guideline v1.2 Part E/D-038 suggests about 10% annotator-first blind items, while T05 asks for a draft of every development pool row. This conflict was raised before review and resolved by Dion.
- **Decision:** The current expanded development batches use draft-first human review for every row. Do not reserve four empty relevance rows or silently describe any development review as blind. All 60 new relevance rows have pending drafts available. The 40 designated review rows remain the D-045 planning subset; additional rows may be reviewed individually, but none become gold through a spot check or this decision.
- **Unchanged:** Unit definitions, labels, scoring denominator, constraints, frozen split, configuration-selection rules, and D-046 held-out blind-first test procedure. CV3/CV4/CV5 remain test-only. Test items that start from drafts are still identified and reported separately.
- **Limit:** Development draft review can anchor the annotator to the draft, so development quality numbers are not an independent blind evaluation. Report that provenance and rely on the separate test procedure for confirmation.
- **Status:** Approved. This workflow exception applies to the current expanded development batches; it does not rewrite historical pilot provenance or approve any annotation label.

## D-048. Complete development drafts in one pilot-format workbook

- **Date and source:** 2 October 2026, Dion's direct instruction to complete A/B/C for every JD and CV-JD pair in the development pool and combine the two batches using the pilot template.
- **Decision:** One active workbook, `evals/labeling/JobFit_Development_Labeling_v0.1.xlsx`. It contains 54 development JDs and 67 CV1/CV2 pairs: 53 frozen-pool JDs and 63 pool pairs, plus the retained selected senior JD and four explicitly optional pairs. A has 1,069 units, B has 1,387 evidence rows, and C has 67 relevance judgments.
- **Provenance:** Existing decisions are preserved exactly: 39 approved A rows, 21 approved B rows, and 3 approved C rows. The remaining 1,030 A, 1,366 B, and 64 C rows are pending drafts. No new label is approved or exported by this preparation.
- **Preparation dependency:** B can now be drafted before A is fully approved, as requested. This replaces T04's previous preparation stop only. If A changes, dependent B rows and affected C judgments must be checked again before gold export. Requirement fingerprints are recorded in the preparation manifest.
- **Review capacity:** D-045 stays unchanged: prioritize A for D1/F00103, D2/F00074, D3/F00012; B for CV1×D1 and CV2×D2; C for the 40 `gold_review = yes` rows. Extra drafts are available for optional review and do not increase the mandatory labeling target.
- **Exceptions:** F00364 has no qualification section, so no A/B requirements are invented. Its C draft remains. F00369 has a truncated clause; only available text is used and the limitation is recorded.
- **Preservation:** The pilot, approved gold CSVs, source CV bodies, frozen split and pool are unchanged. Original development workbooks are retained byte-for-byte in `evals/labeling/archive/pre_combined_20261002/`. Only one editor should modify the active workbook. Never regenerate it to undo human review.
- **Unchanged:** Guideline v1.2, score denominator, constraints, D-046 blind-first held-out test, test-only CV3-CV5, configuration-selection rules, and CP2.2 IN PROGRESS status.
- **Status:** Approved workflow instruction. Draft semantic correctness still requires Dion's review.


## D-049. Four clarification rules for development labeling (guideline v1.3)

- **Date and source:** 2 October 2026, Dion proposed four explicit rules to speed up a large review and requested guideline updates if the review supported them. The rules below implement that request; the examples and migration safeguards are implementation clarifications, not approvals of individual labels.
- **Decision:** (1) Do not score a redundant umbrella when its children fully represent the same obligation. Retain any distinct scope or qualifier. (2) Qualifications without local softeners are required; explicit preference cues are preferred; unknown is for genuine unresolved source ambiguity/conflict, subject to D-042. (3) Named technologies/tools/platforms/frameworks are skill_tool, concepts/domains/methods are knowledge_area; specific duration/education/certification and other existing categories retain precedence. (4) Do not split and/or into independent AND obligations; retain composites when selection count/grouping cannot be represented faithfully.
- **Guideline:** [annotation_guideline_v1_3.md](../evals/annotation_guideline_v1_3.md), especially A3, A4/A4a, A5a, and the adoption checklist.
- **Precedence:** Replaces the old general ambiguous-splitting fallback and and/or handling for new v1.3 review. D-041's historical pilot split remains unchanged, but is not a new-annotation precedent in v1.3. D-040's pure-or experience-area exception is not otherwise repealed and must not be extended to and/or. D-042 remains effective. This does not approve any unresolved equivalence, language-evidence, or degree-ranking policy.
- **Score impact:** Unit count and therefore denominator can change after reviewed merges/rejections/splits. The mathematical score formula is unchanged. A mere category fix is not a MATCH decision. Unsupported composites need an honest review/hold path, not silent removal from the denominator.
- **Migration:** Existing workbook, gold, source, split, prompt, config, runtime guideline v1.2, and scoring code remain unchanged in this documentation update. No bulk relabeling or version bump of old rows. Re-review affected A and dependent B/C before export/evaluation. Preserve historical results. Coordinate runtime adoption with the pipeline owner because the current extraction prompt hard-codes the older D-041 case.
- **Status:** Adopted for manual review under Dion's conditional instruction to update the guideline after analysis. Runtime adoption and individual-label migration remain pending; no human label/fixture/alignment approval is implied.


## D-050. CP2.2 implementation closure and deferred broad extraction

- **Date and source:** 3 October 2026, Dion explicitly selected: “Tutup implementasi CP2.2; ekstraksi massal dilanjutkan setelah evaluasi CP2.3. Catat perubahan cakupan dan keterbatasannya.”
- **Decision:** Close CP2.2 for implemented and evidenced backend acceptance: parser/upload/preview, requirement extraction, evidence matching, existing constraints/score, eight delegated fixtures, embedding/retrieval infrastructure, valid reviewed-record export, protected data, and a source-checked small real-model chain. Broad development extraction is carried forward until configuration evaluation in CP2.3. It is not claimed executed or replaced by pending statuses.
- **Why:** The authorized small experiment completed with seven calls and bounded repairs. Full 214-JD materialization is premature before configuration evaluation and its conservative ceiling exceeds the current guard. Completing it is not required to begin the comparisons that should determine its configuration.
- **Scope change:** Supersedes the CP2.2 acceptance requirement for planned-scale/all-target per-job extraction outcomes. The earlier criterion and its incomplete execution remain historical evidence. The master plan and CP2.2 report must mark this as an explicit user-approved carryover, not an achieved batch result.
- **Evidence limits:** The operational pass is assisted and delegated, not independent human annotation or model accuracy. Two proposed F00332 alignments still have label-interpretation differences. Default JD prompt v1.2 is unchanged; experimental v1.3 is not a selected winner. Formal metrics, compatible complete references and alignment remain CP2.3 gates.
- **Unchanged:** Gold, workbook, source data, split, pool, annotation/grouping/denominator/constraint rules, metric contract, D-044 selection requirements and D-046 test isolation. No model/prompt/K winner, bulk inference or new gold approval is authorized by closure. Hard stop US$8.50 remains; future batches need a quality/cost plan and existing approval thresholds. Held-out extraction/evaluation still wait for freeze.
- **Status:** Approved explicitly by the user. CP2.2 may be marked DONE with this scope and its concrete evidence. CP2.3 formal tuning is NOT RUN.


## D-051. Session-only CV privacy and security

- **Date and source:** 3 October 2026. Dion approved full-text identity masking and the layered privacy design, emphasized no cross-user disclosure or private CV database storage, requested explicit stop/delete plus automatic cleanup on departure, then authorized documentation and CP2.3 implementation planning.
- **Decision:** Accept temporary server processing for v1, mask locally before any LLM or embedding transmission, show an editable exact-text preview, and obtain explicit processing consent. Identify PII throughout the document; deleting everything before Summary is insufficient. Retain professional evidence and date precision. Masking is not guaranteed anonymization.
- **Session boundary:** Private CV data and all derivatives remain owner-scoped volatile session state, never permanent database/public corpus/shared cache/log payloads. No account/login feature is added; secure session ownership checks are mandatory. Public jobs and labeled synthetic demo artifacts retain separate policies.
- **Termination:** Visible “Hentikan & hapus sesi” invalidates access immediately and clears data, with cancellation where possible and late-result discard. Browser departure notification is best effort; server expiry is required. A two-minute lost-liveness lease is the proposed implementation target, with idle/absolute fallback and bounded cleanup. Background-tab visibility alone is not deletion. Exact timings/reload UX are acceptance targets to test before claiming guarantees; two hours is a fallback maximum, not the normal wait after exit.
- **Additional controls:** Layered upload/resource validation, cleanup of framework temporary copies, HTTPS/token protection, payload-free logging, safe rendering/prompt-injection boundaries, endpoint policy verification for LLM and embedding, ZDR routing for real-CV paths and fail-closed behavior. Provider receipt of data cannot be undone by deleting a JobFit session.
- **Plan:** CP2.3 implements/tests masking, consent/session primitives and paired quality impact using development synthetic CV1/CV2. CP3 integrates API ownership/TTL/delete, deployment persistence checks, browser UI and security acceptance. Detailed contract, timing targets, open fields and PR-01-PR-10 tests live in [privacy-threat-model.md](privacy-threat-model.md).
- **Open:** City/country, company/institution treatment; final measured timing/transport behavior; detector choice and endpoint-policy verification. These are not silently resolved by approval of the architecture.
- **Unchanged:** Synthetic-only current evaluation/demo and separate real-CV consent (D-021); gold/sources/split, score, model-selection contract, budget, D-050 and test isolation. No paid call, real upload, public enablement or dependency installation is authorized by this documentation change.
- **Status:** Design approved. Implementation/security acceptance NOT RUN. Real-CV provider processing remains disabled until its gates and consent are met.


## D-052. Development evaluation scope and metric conventions

- **Date/source:** 3 October 2026, Dion accepted the stage-1 scope and fair-comparison discussion, then explicitly approved the three clarifications: relevance 2-3 for P@5/Recall@K; failed evidence as not_assessed with all-reference false negatives; all three gold classes represented or no three-class winner claim. He requested documentation and a bounded execution brief for Codex2.
- **Scope:** Initial seven extraction JDs and four CV1/CV2 evidence pairs remain D-045 targets. Use all eligible reviewed development C records and audit missing judgments in the deduplicated top 10 union across six methods. Report added review effort before requesting it; do not silently change the frozen pool or create labels. Difficult but valid cases remain eligible. F00034 is a known regression, not unseen confirmation.
- **Ranking:** C2/3 is relevant; NDCG exponential gain. P@5 uses original positions 1-5 and denominator 5, available only if all five are judged and present; no condensed replacement or implicit negative. Recall uses original topK and a declared labeled-pool denominator. Missing judgments/coverage are explicit; zero denominators are unavailable.
- **Evidence:** MATCH/PARTIAL/NO_MATCH; invalid/missing assessments remain not_assessed, contributing FN to their gold class in all-reference primary scoring. Per-class counts and coverage are mandatory. Require all three classes across the chosen aggregate set for primary three-class Macro-F1 selection. Absent-class cases cannot silently change averaging or receive a perfect score. Assessed-only quality is diagnostic.
- **Comparison:** Same inputs/rules, first attempt versus automatic repair reported separately, maximum one automatic repair per stage, failed-call costs/latency included. Reviewer-assisted corrections remain separately disclosed. Matching first uses fixed verified requirement inputs; full-chain effects are measured separately.
- **Contract:** [evaluation.md](evaluation.md) specifies implementation and readiness gates. NDCG missing/short-ranking details and unresolved extraction split/merge mappings must be explicit; never infer semantic approval from numeric unit IDs or output validity.
- **Unchanged:** D-029 selection/safety rules, original source/gold, D-046 split/test isolation, D-050 broad-extraction carryover, D-051 privacy scope, score formula, runtime budget and current model defaults. No inference, winner, gold edit or test access is authorized by this documentation decision.
- **Status:** Conventions approved. Case manifest, source completeness, alignment and evaluator implementation remain to be verified; an approved contract is not blanket dataset/benchmark readiness.

## D-053. Held-out ranking pool, coverage and CP2.3 freeze boundary

- **Date/source:** 3 October 2026. Dion explicitly approved all discussed CP2.4 corrections and requested documentation alignment with CP2.3.
- **Decision:** After approved configuration/protocol freeze, label the deduplicated union of original top 10 stage-1 and top 10 final recommendations per CV, normally 10-20 pairs/CV. Report exact counts and effort before workbook preparation, respecting 2-3 hours/day. C labeling stays blind. This replaces D-045's fixed 60-label target and D-046's top 12/condensed-list test rule only; extraction/evidence sizes, provenance and the frozen JD split remain unchanged.
- **Metrics:** Original-rank P@5/NDCG@10 are primary ranking outcomes, gated on required judgments. Both orders use a common eligible pool/IDCG and paired eligible CV subset. Missing labels are never negatives or replaced by lower ranks. Recall is labeled-pool diagnostic only; filter recall needs pre-filter relevant judgments or is not measured. Partial reports disclose all coverage/hold reasons.
- **Isolation:** CV1/CV2 with new test JDs are familiar-profile results; CV3-CV5 are held-out-profile results. Report separately and per CV. Freeze models/prompts/embedding/K/preprocessing/privacy/ordering/metric/reference/pool rules before held-out processing. No tuning on test outcomes; subsequent reuse is regression, not independent confirmation.
- **Authority:** [evaluation.md section 7](evaluation.md#7-held-out-confirmation-protocol-d-053) supplies the operational protocol. D-050 carryover and D-051 privacy gates remain effective. No workbook, source, gold, split, code or API change is authorized by this documentation update.
- **Status:** Approved protocol; implementation verification, configuration freeze, test preparation and evaluation remain pending. Codex2's current D-052 development stage 1 scope is unchanged.

## D-054. CP2.3 Stage-1 case reviews and strict split/merge extraction F1

- **Date/source:** 3 October 2026, Dion's explicit replies in the current project chat to the case-specific Stage-1 review questions. The prior [Stage-1 report](checkpoint_2/supporting/CP23_Stage1_Evaluation_Preparation_20261003.md) and versioned review packets identify the exact records. No exact per-row review time was supplied.
- **Six additional C decisions:** Dion confirmed that he reviewed the full JD/CV and approved CV1/F00010=1, F00132=1, F00284=1, F00312=2; CV2/F00090=1, F00559=2. These are case decisions, not an approval of other missing relevance labels or a change to the frozen pool. Preserve model-assisted draft provenance and record his acceptance in a versioned amendment; do not edit the active workbook.
- **F00332 alignment and evidence:** Dion approved the 16 proposed one-to-one CV1/F00332 model-to-gold mappings and changed gold B P30-U08 and P30-U15 from MATCH to PARTIAL. The two original MATCH judgments remain in the historical bundle; record before/after and why in a new version. Recheck the dependent C reason/status, without assuming its value is unchanged until Dion confirms it.
- **C-only hold path:** Dion approved preparing direct JD/CV C review for CV1/F00022, CV2/F00114 and CV1/F00369 while their A/B records stay held. This **does not approve the new C values or clear the historical holds**. F00369 must use only its archived truncated source and carry a source-limitation flag; a similar posting is not original proof. Pending reviews cannot enter gold or replace a ranked position.
- **Extraction split/merge:** For human-verified one-to-many/many-to-one mappings over complete independently assessable logical-unit inventories, count no automatic TP: each unmatched gold unit is FN and each unmatched model unit is FP. Report clause-level similarity separately. Unverified alignments and complex many-to-many mappings remain unavailable. This amends the unresolved D-052 split/merge convention only; no annotation schema, match-score denominator, PARTIAL weight or relevance rubric changes.
- **Subsequent explicit review replies, same date:** Dion approved retaining CV1/F00332 C=3 and its existing reason after the two B corrections. After reading the original JD/CV, he also approved fresh direct C-only judgments CV1/F00022=3, CV2/F00114=1 and CV1/F00369=1; the last judgment is explicitly limited to the truncated archived JD. The A/B holds remain. The new values and original source limitations are recorded in `evals/results/cp23_stage1_user_review_receipt_20261003_v2.json` and the versioned r3 amendment, without inventing a per-row timestamp or independent annotator.
- **Current status:** These case decisions and the strict rule are approved. The five Stage-1 prerequisite gates are ready in `evals/results/cp23_stage1_readiness_20261003_v4.json`; each future candidate output still requires its own alignment and semantic review. No model, embedding, prompt or K winner is approved.

## D-055. Bounded CP2.3 Stage-2 extraction comparison budget

- **Date/source:** 3 October 2026, Dion's explicit reply approving the exact question for four D-029 round-one models × seven fixed development JDs, including at most one automatic repair per case, with an aggregate additional ceiling of **US$3.20**. Receipt: `evals/results/cp23_stage2_extraction_budget_approval_20261003_v1.json`, bound to the v3 preflight hash.
- **Scope:** Extraction only, experimental JD prompt v1.3, same sources/configuration for each model. The project US$8.50 hard stop remains. Matching, GPT-6 Sol reference, test data, broad extraction and a changed protocol are excluded. No batch splitting to evade the standing US$1 approval threshold.
- **Execution:** The first DeepSeek/F00332 call cost US$0.00478664. Source-semantic QA found merged AND obligations and lost OR structure, so the durable run stopped after 1/28cases. The unused portion of the cap does not approve a new prompt, a reset, or a different batch. Preserve the failure as development evidence; replan and seek applicable approval before changed paid work.
- **Status:** Approved for the frozen batch only; that batch is terminal on semantic failure. No winner or extraction-quality benchmark claim follows.

## D-056. Bounded experimental v1.4 Stage-2 extraction budget

- **Date/source:** 3 October 2026. After the explicit v1.4 preflight and US$3.23 approval request, Dion replied “Iya saya setuju, ayo selesaikan tahap 2.” The exact [approval receipt](../evals/results/cp23_stage2_extraction_budget_approval_20261003_v2.json) binds plan SHA `b901bad9176e33d45845dcd9748d2c3eb05bbf627b592655e174d697b2e9a0c2` and run ID `cp23_stage2_round1_extraction_20261003_v4`. No exact review time is asserted.
- **Scope:** At most 28 extraction cases (four D-029 round-one models × the same seven development JDs), one automatic repair per case, aggregate additional cap US$3.23 including failures and uncertain charges. The conservative preflight bound is US$3.2232974. The US$8.50 project hard stop and existing guard/ledger remain. Experimental JD prompt v1.4 is fixed for this plan and is not the active default, a guideline change or a selected prompt.
- **Exclusions:** Evidence matching, GPT-6 Sol reference, broad development extraction, test data and configuration selection require their own plans. Approval does not migrate from v3 or to a later changed protocol.
- **Execution:** The first DeepSeek/F00332 stage returned a 17-unit draft after one automatic repair, two calls, US$0.022156197 provider-reported. Source-semantic QA found that the alternative branches do not represent the source's “other disciplines will be considered” path even though the group text repeats it and `needs_review=true` prevents scoring. One reviewed trend/anomaly obligation was split into two model units; D-054's strict mapping applies. The durable run stopped after 1/28 stages under its frozen quality gate. No model winner or extraction F1 is claimed.
- **Status:** Exact paid scope approved and terminal on the recorded semantic failure. Any changed stop policy or further paid plan requires a distinct versioned scope and applicable approval; unused cap is not transferable.


## D-057. Same-protocol v5 continuation with visible semantic failures

- **Date/source:** 3 October 2026, Dion's explicit answer “Ya, setujui plan v5 dan plafon US$3,16”; original receipt `evals/results/cp23_stage2_continuation_budget_approval_20261003_v1.json`.
- **Decision:** Run the remaining 27 original model/JD extraction cases on experimental v1.4; retain DeepSeek/F00332 as an external failure. A recorded source-semantic failure does not end the whole comparison, but each next case requires source QA. Process/schema failures, uncertain charges, changed hashes and budget breaches still stop.
- **Limit:** US$3.16 including repairs/failed or uncertain charges; no matcher, reference, mass extraction, test or configuration selection.
- **Outcome:** Six remaining DeepSeek cases collected and checked. V5 then stopped on the first rejected GPT/F00332 request. The terminal state is retained; no reset or hidden replay.

## D-058. Versioned GPT request compatibility adaptation

- **Date/source:** 3 October 2026, Dion's explicit answer “Setuju v6 dalam plafon kumulatif US$3,16” to the concrete21-case route-repair proposal.
- **Decision:** Use a separate v6 run for the remaining GPT/Gemini/Claude extraction cases. Omit `temperature` only for GPT-6 Luna, whose published endpoints do not advertise it, and accept the verified published dated GPT response ID. Other models retain explicit temperature 0. GPT's provider default is not described as temperature 0 or deterministic sampling.
- **Protection:** Same seven development sources, experimental prompt v1.4, guideline/schema, privacy controls, price ceilings and one automatic repair. All earlier results remain visible; original v5 state is not resumed. Cumulative v5 plus v6 spending is bounded by US$3.16, not a fresh allocation. The project hard stop remains US$8.50.
- **Evidence:** Proposal `evals/results/cp23_stage2_v6_route_repair_proposal_20261003_v1.json`; plan-bound approval `evals/results/cp23_stage2_v6_route_approval_20261003_v1.json`; official endpoint metadata `evals/results/cp23_stage2_route_diagnosis_20261003_v1.json`.
- **Limit:** Operational compatibility fix, not a selected model/prompt or relaxation of output/source validation. Candidate alignment, paid evidence matching and final selection remain separate.


## D-059. Retain settled process failures and complete unattempted extraction cases

**Approved by Dion, 3 October 2026**, explicit reply “Setuju v7 dalam plafon kumulatif US$3,16”. The terminal v6 Gemini/F00815 failure remains failed and is not replayed. V7 covers only the two remaining Gemini and seven Claude cases, with no request/prompt/privacy change and at most one automatic repair per case. After an exact failure receipt establishes settled charges, a process failure is retained as a comparison outcome and the next original case may proceed. Uncertain charges/reservations, changed source/identity and insufficient budget still stop. V5/v6/v7 share the same cumulative US$3.16 ceiling; the remaining conservative bound is US$2.0236408. No matching, test access, reference model, broad extraction or winner selection is authorized by this decision.

[Plan](../evals/results/cp23_stage2_round1_extraction_20261003_v7_remaining_cases_preflight.json) and [approval](../evals/results/cp23_stage2_v7_remaining_cases_approval_20261003_v1.json) preserve the predecessor hashes and approval scope.


## D-060. Scoped strict many-to-many accounting for Claude/F00036

- **Date/source:** 3 October 2026, Dion explicitly replied “Setuju dengan hitungan ketat tersebut” to the exact Claude/F00036 question.
- **Approved case:** reviewed gold P09-U08/P09-U09 (EDA and visualization-tool alternatives) versus model U11/U12/U13. Count **0 TP, 2 FN, 3 FP**, consistent with strict split/merge accounting. This closes that case's previously missing many-to-many convention.
- **Implementation:** an accounting-only adapter preserves the original complex relation and emits two FN records/three FP records. It adds no source units and does not approve other model-to-gold mappings.
- **Limits:** no blanket complex-case policy, no field-level-equivalence decision, no paid matching approval, no whole-alignment human verification and no model/configuration winner. Candidate-specific semantic review and the other pending questions remain.
- **Receipt:** `evals/results/cp23_stage2_complex_alignment_approval_20261003_v1.json`, bound to current proposal packet v2.


## D-061. Primary extraction equivalence and separate category accuracy

- **Date/source:** 3 October 2026, Dion explicitly replied “Setuju dengan definisi tersebut” to the stated evaluation definition.
- **Primary extraction F1:** a verified one-to-one semantic equivalent preserves meaning, material qualifiers, AND/OR structure and required/preferred importance. Ordinary proficiency-depth words remain subject to D-035/D-042.
- **Category errors:** report category accuracy separately; a category mismatch alone does not invalidate a semantically equivalent unit for primary F1. Category effects on denominator/scoring remain visible and are not erased or treated as acceptable production behavior.
- **Limits:** this is a development evaluation clarification recorded before final metric computation, after outputs had been inspected; report that chronology. No gold, score formula, prompt or test-set change. Candidate-specific mapping acceptance is still required.

## D-062. Separate capped fixed-input matching experiment

- **Date/source:** 3 October 2026, Dion explicitly approved “Setuju, maksimal US$1,85”.
- **Scope:** four round-one models × four fixed reviewed development CV/JD pairs,16stages,atmost32calls includingoneautomaticrepair percase. Additional aggregate ceiling **US$1.85**; conservative preflight bound US$1.8464752. Exact plan/receipt in `evals/results/cp23_stage2_fixed_matching_20261003_v1_plan.json` and `_approval.json`.
- **Protocol:** retain settled invalid-output failures and proceed to unattempted original stages; never repeat a failed stage or convert it into NO_MATCH. Persist typed attempts, ledger reservations and results; stop on uncertain cost, interrupted request, changed protected inputs or exhausted budget. GPT-only omission of unsupported temperature and published dated response-ID allowance are explicit. Existing privacy/provider routing and project hard stop US$8.50 remain.
- **Exclusions:** test set, gold edits, broad extraction, quality-reference calls and automatic candidate/configuration selection. Acceptance of payment does not certify extraction alignment, fixed-adapter semantics or evidence accuracy.


## D-063. Accepted Stage-2 candidate mappings and fixed matching adapter

- **Date/source:** 3 October 2026, Dion: “Setuju pemetaan rekomendasi dan adapter tetap”.
- **Scope:** recommended relations in the complete v3 packet (27 final extraction drafts and one retained failure, 447 relations), and the source-checked fixed matcher adapter containing 73 logical units across four development pairs. D-060 and D-061 accounting apply.
- **Provenance:** human acceptance of assisted source QA, not independent human annotation of every candidate output. Original gold, outputs and historical source observations remain unchanged.
- **Receipt:** `evals/results/cp23_stage2_alignment_and_fixed_adapter_approval_20261003_v1.json`, binding the packet, adapter, plan and reference hashes.
- **Limits:** permits metric calculation on this accepted scope; does not approve evidence predictions, a winner, additional paid calls, test use or a change to the scoring formula.
- **Status:** Approved.


## D-064. Separate capped quality-reference and round-two experiment

- **Date/source:** 3 October 2026, Dion: “Setuju protokol dan batas tambahan US$6,40”, followed by an instruction to continue maximally and precisely.
- **Scope:** eight GPT-6 Sol reference stages (four extraction JDs shared with matching plus four fixed matching pairs), eleven DeepSeek Pro stages (seven original extraction JDs plus four fixed pairs); 19 stages, at most 38 calls including one repair per stage.
- **Budget:** separate aggregate additional ceiling US$6.40; conservative bound US$6.33582444. Existing US$8.50 project hard stop remains. Unknown charges/reservations, changed inputs or unsafe headroom stop dispatch. Unused D-062 cap is not transferred.
- **Protocol:** new versioned experiment; portable application-owned repair framing, unchanged first-call rubric/prompts/inputs, omit unsupported temperature only for GPT Sol, and allow only exact dated response IDs published in saved official endpoint metadata. Original failures and paid states remain unchanged. The framing is a compatibility mitigation, not a proven historical HTTP 400 diagnosis. Settled failures remain observations; failed cases are not repeated.
- **Comparison limits:** reference extraction uses only its four-JD/73-unit common scope. Round-two extraction uses the common full-seven-JD/120-unit scope. Fixed-input matching has the same 73 reference units per model. New extraction alignments still require concrete acceptance; payment is not semantic approval or a winner. No test use, broad extraction, gold correction or runtime default promotion.
- **Receipt:** `evals/results/cp23_stage2_reference_round2_20261003_v1_approval.json`, binding the accepted proposal v2 and frozen executor plan.
- **Execution outcome:** all 19 stages completed in 25 calls, D-064 cost US$0.4054182374. All11 extraction drafts are process-valid; seven of eight matching outputs are valid. The retained DeepSeek Pro/CV1/F00036 source-quote failure is included in evaluation. Project ledger US$1.1735639842 includes historical uncertain US$0.0210861. New extraction mappings await their own acceptance; no winner is approved.
- **Status:** Approved execution completed; quality/selection gates remain.


### D-064 addendum: repair-only replay for 4 October preparation

D-064 already identifies the completed reference/round-two experiment above. Preserve that authority, cost and results. Dion's new instruction explicitly authorizes fixing the repair bug and replaying only affected rejected repairs: "Jika ada bug, perbaiki. Jika tahap yang terkena bug itu penting, jalankan ulang khusus tahap itu saja."

Initial cap US$0.30 was blocked by conservative preflight US$0.6485602. Dion then answered **"Setujui plafon US$0,65"**. This is a separate aggregate replay ceiling, not an increase to the US$8.50 project guard or authorization for more reference/model calls. Same first drafts, prompt/schema/model/parameters, one replay per stage. Repair instruction role changes from system to user; wording is preserved.

Eight calls completed. Actual additional cost **US$0.09795280**, below **US$0.65**. One matching and one extraction became valid; six matching repairs remained invalid. No original output, gold, source or default model was overwritten. Human acceptance of the new Gemini extraction mapping is pending. Guardrails are a separate offline proposal. [Plan and budget receipt](../evals/results/cp23_stage2_repair_rerun_20261004_v1_approval.json), [actual outcome](../evals/results/cp23_stage2_repair_rerun_20261004_v1_summary.json).

## D-065. Deterministic evidence guardrails

- **Status:** Approved for v1 by Dion on 4 October 2026. Runtime integration and release verification remain pending.
- **G1:** MATCH supported only by quotes wholly inside Skills becomes PARTIAL, with `skills_list_only`.
- **G2:** MATCH for an explicit named-tool conjunction with only some items supported outside Skills becomes PARTIAL, with `partial_item_coverage`. Explicit OR/example syntax is excluded. This bounded literal checker is not general entailment or technology equivalence.
- **Trace:** preserve the input, record each unit/branch before and after, never raise labels. Gold, runtime labels, score formula and denominator stay unchanged.
- **Measured result under the original reference:** four original unsupported positives lowered; four original scope overclaims remain. D-067 later clarified that the two SQL/PostgreSQL claims were supported by SQL work evidence. The revised evaluation therefore exempts that example-like requirement from G2 and reports the old and new references separately. Two additional Gemini skills-list claims are lowered; one additional Gemini scope claim remains. Insufficient citation is recorded separately. No claim that showing a quote alone makes an unsupported label safe.
- **Evidence:** [A/B guardrail result v2](../evals/results/cp23_stage2_repair_comparison_20261004_v2.json). D-066 separately changes the v1 safety rule. Offline results alone do not certify the public runtime.

## D-066. V1 safety and per-task selection amendment to D-029; quote validator v1.1

- **Date/source:** 4 October 2026. Dion explicitly approved both D-029 revisions and the stated safe bounds for quote validator v1.1. D-029 remains unchanged as the historical pre-registered rule; this entry is a post-result amendment for v1 and must be identified as such in comparisons.
- **Primary comparison:** the bug-fixed B view is primary; the original A view remains historical. Do not erase either result.
- **Safety for v1:** zero unsupported positives remains a target, not a freeze-blocking gate. Report the observed unsupported-positive rate for model plus approved G1/G2 on development, then on held-out test. Display the actual matched CV source span beside each label. CP3 plans a separate display rule for MATCH claims that cannot be confirmed: PARTIAL, marked "perlu dicek". That display rule is not yet implemented or measured.
- **Per-task model selection:** retain D-029 rule 5 allowing different extraction and matching models when one is at least 0.03 better on its own task. For cost comparison, use extraction F1 for extraction and evidence Macro-F1 for matching. Within each task, a cheaper model wins when it is within 0.03 of the best low-cost candidate on that task; use p95 latency to break a tie. A complete process run in that task remains mandatory. Report coverage, failure counts, quality and latency before a proposed model choice; Dion approves or rejects that choice.
- **Quote validator v1.1:** keep the model's returned quote and a separate original source span. The displayed and evaluated evidence is the original CV span. Normalize only Unicode representation, separator/control punctuation, Markdown emphasis and whitespace; case-insensitive comparison is a fallback. Tokens must remain identical and adjacent in the same order. Any changed or invented word fails. Ambiguous source-span matches fail instead of silently choosing one. Every normalization is flagged.
- **OR groups:** move a parent label and its quotes to a branch only if exactly one branch is clearly supported by the matched source span. If branch labels already exist, keep them and ignore the parent with a flag. Ambiguous branches remain not_assessed. Do not infer skill equivalence from a string match alone.
- **Scope:** apply the same versioned validator to every saved development output from round one, repair replay, reference and round two. Preserve raw results, gold, workbook, sources, split and pool. Any model failure that survives validation remains a failure. Paid reruns are limited to confirmed application-caused failures under the separately approved US$0.30 cap; model mistakes do not qualify. No test access or freeze follows automatically.

## D-067. F00815 SQL reference interpretation for development evaluation

- **Date/source:** 4 October 2026. Dion explicitly decided: "SQL with PostgreSQL as an example: SQL evidence such as BigQuery SQL is MATCH."
- **New reference:** F00815/P52-U10 means SQL familiarity with PostgreSQL as an example, not SQL plus mandatory PostgreSQL experience. CV2's work quote about SQL queries in BigQuery supports MATCH. The previous reviewed evidence label was PARTIAL under the narrower interpretation.
- **Versioning:** retain the approved workbook and original gold intact. Store the old and new text, labels, source quote and file hashes in [reference v2](../evals/results/cp23_f00815_sql_reference_20261004_v2.json). Apply the same revised reference to every development candidate and show both metric views. Do not revise other units or the held-out test set.
- **Guardrail consistency:** P52-U10 is SQL with PostgreSQL as an example. G2 must not treat the slash in the historical adapter as an AND requirement. The [offline comparison](../evals/results/cp23_sql_reference_comparison_20261004_v2.json) applies this exception to every model in the new-reference view while retaining the original view.
- **Later resolution:** D-067 alone did not approve the three non-trivial Gemini/F00815 extraction alignments. Dion subsequently approved strict D-054/D-061/D-067 accounting under D-068. The [versioned Gemini result](../evals/results/cp23_gemini_f00815_alignment_20261004_v1.json) reports the new F1 without changing original gold.

## D-068. Provisional CP2.3 freeze for development

- **Date/source:** 4 October 2026. Dion accepted DeepSeek Flash for JD extraction and evidence matching under D-066, approved strict D-054/D-061/D-067 mapping of Gemini/F00815, and authorized Part A3, Part B and Part C under the existing capped protocol. This is an assisted development decision, not held-out test confirmation.
- **Selected development configuration:** B as primary; hybrid FTS plus dense RRF with Qwen3-Embedding-8B by D-044; stage-1 K=20 provisionally; DeepSeek Flash for both tasks; JD extraction prompt v1.4 with qualification inventory; evidence prompt v1.1; quote validator v1.1; approved G1/G2; PARTIAL weight 0.5 provisionally. Original A, old SQL reference and earlier config remain as historical artifacts.
- **Evidence:** On seven development JDs, DeepSeek Flash extraction F1 is 0.861789 versus GPT-6 Luna 0.793651. On four fixed development CV/JD pairs after validator v1.1, G1/G2 and D-067, evidence Macro-F1 is 0.772296 versus 0.730356. The 0.041940 gap exceeds the 0.03 cost switch threshold. Qwen wins the pre-registered embedding Recall@20 comparison. K and PARTIAL weight lack complete gold-input ordering and must be tested in Part B.
- **Latency condition:** DeepSeek Flash request p95 was 90.747 seconds per matching pair in this small development run. CP3 must run independent matching calls concurrently, cache JD extraction, and prepare a precomputed synthetic demo under D-022. Part B measures actual end-to-end wall time for one CV and K=20. If unacceptable, GPT-6 Luna is the speed fallback; its observed p95 was 21.880 seconds and its guarded Macro-F1 is lower by about 0.042. Do not imply this sample is a production service guarantee.
- **Quality reference and safety:** GPT-6 Sol is a measured quality reference, not the production choice. Report its K=20 cost projection beside both candidates. Two unsupported positives among 50 positive units remain for DeepSeek Flash after G1/G2 on the reviewed development pairs. Show source CV spans beside labels, report the safety rate on held-out test, and retain the CP3 "perlu dicek" display plan from D-066. The zero target remains a target, not an automatic release claim.
- **Configuration provenance:** The provisional settings are saved in `config/versions/pipeline_cp23_provisional_20261004.yaml`. The historical `config/pipeline_v1.yaml` retains its original bytes because frozen retrieval and model-evaluation receipts hash that path. Overwriting it produced 28 failed checks and three setup errors; restoring it returned the full suite to 444 passed, 2 skipped. Part B must pass the provisional spec explicitly. CP3 runtime promotion needs a separately versioned migration and new acceptance checks; the freeze decision must not rewrite historical input hashes.
- **Boundary:** Freeze is provisional development only. No test data selects settings. No real CV is sent to a provider. K/weight, public privacy gates, broad development extraction and CP2.4 frozen test evaluation remain open.

## D-069. Bounded Part B resume before the CP2 presentation

- **Date/source:** 4 October 2026. Dion chose option 2: finish A3 materials first, then continue only the 31 unattempted development CV/JD pairs. The aggregate Part B cap rises from US$2.00 to **US$2.50 total**, including previous costs and uncertain reservations. Previously timed-out pairs are skipped without replay. New timeouts must be recorded and skipped. Stop no later than two hours before the presentation; if incomplete, present clearly labeled partial results.
- **Execution:** The [A3 snapshot](../evals/results/cp23/end_to_end_dev/cp23_a3_presentation_snapshot_20261004_v1.json) predates the resumed calls. The [plan amendment](../evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1/cap_and_deadline_amendment_v2.json) binds the original plan hash, cap, skip rule and conservative 11:00 WIB cutoff. All 31 untouched pairs received records before that cutoff; the two old timeout pairs were not replayed and no new timeout occurred.
- **Outcome:** All 60 planned pair records exist, but only 20 have final numeric scores. The [completion receipt](../evals/results/cp23/end_to_end_dev/cp23_partb_completion_20261004_v3.json) reports US$1.1875181592 total Part B accounting, including US$0.0646905 of old uncertain charges. Resumed calls added US$0.1968797400. This is collection completion, not semantic quality acceptance. H4, K and PARTIAL weight still lack complete final-order coverage; D-068 remains provisional.
- **Limits:** No new model, prompt, gold, workbook, source, split, pool, test data or paid privacy comparison. The unused cap does not authorize retrying failed stages or broad extraction. D-050, D-051 and D-053 remain separate gates.

## D-070. Revised project credit and bounded pipeline v1.1 budget

- **Date/source:** 4 October 2026. Dion authorized adding US$10 of OpenRouter credit and a new development pipeline v1.1 run on the same 60 Part B pairs, with a separate aggregate cap of US$3.00. He reported that total credit bought would be about US$19.22. That provider balance is a user statement, not an independently verified balance.
- **Revised D-019 ceiling:** replace the old US$15 planning ceiling with the actual credit bought, reported as about US$19.22. The numeric local guard is more restrictive: `API_BUDGET_USD=19` and `API_HARD_STOP_USD=18.5`. Dion updates `.env` and the OpenRouter key limit. Code and documentation must not edit or reveal the key. The preflight on 4 October read numeric guard values 19.0 and 18.5; the ledger was US$2.4590349434 before v1.1 paid work.
- **Scope:** only previously failed or held stages among the same 52 development JDs and 60 CV1/CV2 pairs may be rerun under the changed pipeline. Valid v1 outputs are reused. All calls use the guard and ledger. Original results remain intact. No test use, new model, broad extraction, prompt change, gold edit, or configuration winner is approved by this budget decision.

## D-071. Pipeline v1.1 H2 provisional hold policy

- **Date/source:** 4 October 2026. Dion chose H2 with a 20 percent threshold after reviewing the H1/H2 saved-output simulation. This revises the D-006 whole-job `needs_review` hold for pipeline v1.1. Historical v1 scores and the score formula remain unchanged.
- **Rule:** count scored required logical units after duplicate merging. If at most 20 percent of them have unresolved `needs_review` structure, exclude the unresolved logical units from the denominator and report a **provisional** score. Record each excluded unit's ID, text, source quote and reason. The user interface must show these as "syarat yang perlu dicek". If more than 20 percent are unresolved, or another processing failure prevents a score, keep `on_hold`.
- **Evaluation:** report H1 and H2 side by side for coverage and original-position order metrics when available. Never replace an unjudged unit or job with a negative label or the next ranked job. The changed denominator is visible in every v1.1 pair receipt. No gold or annotation meaning is changed.
- **Known trade-off:** H2 can raise coverage by omitting unresolved required units. Its percentage is less complete than a final score. The pre-run offline simulation moved 10 of 60 pairs from on hold to provisional, giving H1 20/60 and H2 30/60 usable scores on the saved v1 outputs; it did not fix extraction failures.
- **Measured 4 October outcome:** Pipeline v1.1 and its bounded follow-up yielded H1 26/60 and H2 42/60, comprising 26 final and 16 provisional scores. The 54/60 development target was not met; zero of 36 final-order metric cells were complete. D-068's K20 and PARTIAL weight 0.5 remain provisional. The [versioned report](checkpoint_2/supporting/CP23_Pipeline_v11_20261004.md) and [coverage receipt](../evals/results/cp23/pipeline_v11/coverage_summary_v2.json) preserve both the gains and unresolved cases. This measurement does not expand D-071 into permission to hide exclusions or use the test split for tuning.

## D-072. H2v2 hold policy: experience, level and education are never excluded

- **Date/source:** 4 October 2026. Dion approved audit decision 2 after seeing that 9 of the 16 provisional H2 scores in pipeline v1.1 had removed a work-experience, seniority or education requirement from the denominator (for example "8-10 years of progressive experience" for a principal role, scored 39.47% for the fresh-graduate CV1).
- **Problem:** for early-career users these requirements are usually NO_MATCH. Removing them raises the score of senior jobs, which is the opposite of what JobFit should do. The model marks exactly these complex requirements as `needs_review` most often.
- **Rule (H2v2):**
  - If a scored required unit marked `needs_review` states work experience, a seniority level or education, the pair stays **on hold**. Detection: category `experience_duration` or `education`, a `min_years` value, the same on any OR branch, or a documented seniority/years pattern in the text (`hold_policy_v11.is_protected_unit`).
  - Other unresolved scored required units follow D-071: at most 20 percent may be excluded, the score is provisional and the excluded units are listed.
  - A `needs_review` flag on a unit outside the percentage (preferred, unknown importance, soft skill, location, work authorization) no longer makes the score provisional. This fixes a bug in the H2 code (CV1 and CV2 x F00556 were provisional because of one preferred unit).
- **Effect on saved v1.1 outputs (offline, no model call):** usable pairs H1 26, H2 42, **H2v2 33 of 60**. Nine pairs move from provisional to on hold; two move from provisional to final. Result: `evals/results/cp23/dev_eval_v2_20261004/product_order_v1.json`.
- **Unchanged:** score formula, PARTIAL weight, gold, D-071 history and its receipts. H1 and H2 stay available for comparison.
- **Trade-off:** lower coverage. A held job is shown under "could not be fully analyzed" instead of a misleading percentage.
- **Status:** Approved. H2v2 is the development hold policy for the next freeze proposal.

## D-073. Development final-order metrics use the real product order

- **Date/source:** 4 October 2026. Dion approved audit decision 3. Amends the D-052 development contract for final-order metrics only.
- **Problem:** under the strict D-052 rule, a top-K list with any held job gives no final-order metric, so 0 of 36 cells were measurable and H4, K and the PARTIAL weight could not be studied.
- **Rule:** the primary development final-order metric uses the order the user actually sees (D-013, `scoring/ranking.py`): scored jobs by percentage, explicit-conflict jobs next, held or failed jobs last in stage-1 order. A held job is never skipped, never given relevance 0 and never replaced by a lower-ranked job. Every cell reports the number of unscored jobs in the top K. The strict D-052 completeness flag is reported next to it. P@5 and NDCG@10 keep the original-position rules (an unjudged job in the final top 10 makes the metric unavailable).
- **Implementation:** `src/jobfit/eval/product_order.py`, tests in `tests/test_product_order.py`, script `scripts/evaluate_cp23_product_order.py`. The script first reproduces every saved H1/H2 score exactly (0 mismatches) before computing metrics.
- **First development result (two CVs, indicative):** stage 1 macro P@5 0.30 and NDCG@10 0.522. Final order, H2v2, weight 0.5: K=10 P@5 0.40, NDCG@10 0.551. K=20 P@5 0.50, NDCG@10 unavailable because one job (CV2/F00629) has no relevance label. The explicit-conflict block is empty because saved stages carry no confirmed constraint context.
- **Contract file:** `docs/evaluation.md` is left byte-identical because the approved D-052 receipt hashes it. This entry and `product_order.py` carry the amendment; a new versioned contract receipt is needed before the text of `evaluation.md` changes.
- **Status:** Approved for development. D-053 already uses the same product order for the held-out test.

## D-074. Stage-1 seniority rule for early-career users (development candidate)

- **Date/source:** 4 October 2026. Dion approved audit decision 4: test a rule that moves jobs asking for three or more years below the others.
- **Evidence (development only):** in the judged pool, all 14 jobs with bucket 3-4y or 5y+ are not relevant for CV1, and 16 of 17 for CV2. In the Hybrid Qwen top 20, none of the 16 such jobs is relevant.
- **Rule:** `src/jobfit/search/seniority.py`, version `seniority-demote-3y-v1`. Stable partition of the stage-1 ranking: buckets `3-4y` and `5y+` move below all other jobs, order kept inside each group. `not_stated` is never demoted. Nothing is removed and the user can switch it off.
- **Development result (offline):** Hybrid Qwen P@5 CV1 0.2 to 0.6 and CV2 0.4 to 0.8; NDCG@10 CV1 0.355 to 0.525 (CV2 unavailable: two newly promoted jobs have no label). Most other methods also gain P@5. Final order with the rule, H2v2, K=10: CV1 P@5 0.4, NDCG@10 0.581. Result: `evals/results/cp23/dev_eval_v2_20261004/seniority_rule_v1.json`.
- **Limits:** two development CVs; the bucket is the CP1 v0 regex feature (many jobs are `not_stated`); the rule was found after looking at development labels, so only the held-out test can confirm it.
- **Circularity note (added 4 October):** guideline Part D already gives relevance 1 when a job asks for 3+ years and the CV shows under 1 year. Part of the rule's gain therefore restates the labeling rule. That is still the right product behaviour (the user should not see such jobs first), but the gain is not independent evidence of better matching.
- **Status:** Approved as a development candidate. It must be written into the frozen configuration before any test processing and never tuned on test outcomes.

## D-075. Uncertainty reporting for CP2.3 comparisons

- **Date/source:** 4 October 2026. Fulfils the D-045 promise of bootstrap intervals; reporting only, no rule change.
- **Matching (73 units, 4 pairs, paired bootstrap, 5,000 draws):** DeepSeek minus Luna Macro-F1 is 0.042 under the reported view, 95 percent unit interval -0.067 to 0.148, pair interval -0.042 to 0.091. Without G1/G2 and the D-067 reference change the difference is 0.016. The difference is **not distinguishable from zero**, and the 0.03 cost rule cannot separate the two models on this sample.
- **Error direction:** DeepSeek gives a stronger label than gold 6 times and a weaker one 9 times; Luna 3 and 16 times. MATCH precision is 0.84 for DeepSeek and 0.96 for Luna. For an evidence product a stronger-than-gold label is the more harmful error.
- **Retrieval:** results are per CV with counts; Hybrid Qwen top 30 has 6 and 8 unjudged jobs, B0 15 and 16, so labeled-pool recall favours hybrid. B0 is better than Hybrid Qwen for CV1 at Recall@20 (8 versus 6 of 13). "Hybrid Qwen is best" is not established; Qwen over OpenAI is consistent on both CVs. Indonesian CV1 versus English CV2 Recall@20 for Hybrid Qwen: 0.46 versus 0.64 (H7, two CVs).
- **Result:** `evals/results/cp23/dev_eval_v2_20261004/uncertainty_v1.json`.
- **Status:** Recorded. Future comparisons report intervals next to point values.

## D-076. Development check of GPT-6 Luna for evidence matching

- **Date/source:** 4 October 2026. Dion approved audit decision 1 (test Luna before deciding), aggregate cap **US$0.40**.
- **Scope:** same 60 development pairs and saved DeepSeek extractions; only the matching model changes. Phase A Luna CV1 top 20 with 20 workers and phase B DeepSeek CV1 top 20 with 20 workers measure one-CV K=20 wall time; phase C runs Luna on the other 40 pairs. Script `scripts/run_cp23_luna_matching.py` (zero-call preflight by default), comparison `scripts/evaluate_cp23_luna_matching.py`.
- **Preflight (offline):** 54 Luna and 18 DeepSeek matching calls (held extractions are not called), median-based estimate US$0.30, guard 19 / 18.5, ledger US$3.09.
- **Version 1 outcome (4 October):** stopped. All 18 Luna calls were rejected with `NotFoundError` at US$0 because the script sent `temperature`, which Luna endpoints do not support (the D-058 adaptation was not reused). The DeepSeek phase then hit `RunCapReached`: 20 parallel calls reserve about US$0.97 of conservative upper cost, above the US$0.40 cap. Eight DeepSeek calls finished; run cost US$0.1219. Records stay in `evals/results/cp23/luna_matching_v1/`.
- **Version 2 (Dion's choice: Luna only):** D-058 `RouteClient` (temperature omitted, dated alias accepted), one canary call first, route/key errors stop the run, cap **US$0.50**, peak in-flight reservation US$0.379, median estimate US$0.15. DeepSeek latency is taken from saved runs (pipeline v1.1 and the eight v1 calls) instead of a new 20-worker phase.
- **Version 2 outcome (4 October, run by Dion):** completed. 54 Luna pairs called (59 requests including 6 validation repairs), 50 process-valid, 4 failed (3 invalid output, 1 unbounded duration), US$0.1043. Ledger total US$3.313.
  - Usable pairs of 60 under H2v2: Luna 36, DeepSeek 33.
  - One-CV K=20 wall time with 20 workers: Luna **62.5 s** (pair p50 24 s). DeepSeek one-CV wall time was not measured; its pair times are p50 32 to 39 s and up to 113 s, so a fully parallel CV is bounded near 113 s.
  - Same units, Luna versus DeepSeek labels: 740 of 848 equal (87 percent); Luna weaker on 94, stronger on 14. This matches the gold-pair finding that Luna is more conservative.
  - Product order (H2v2, weight 0.5): CV1 K=10 P@5 0.2 both, NDCG@10 0.354 Luna versus 0.358 DeepSeek; CV1 K=20 P@5 0.6 versus 0.4, NDCG@10 0.450 versus 0.419; CV2 K=10 identical (0.6, 0.745). CV2 K=20 is unavailable (F00629, F00645 unlabeled).
  - Cost per matched pair about US$0.002 (Luna) versus about US$0.010 (DeepSeek).
  - Result: `evals/results/cp23/dev_eval_v2_20261004/luna_comparison_v1.json`; run records `evals/results/cp23/luna_matching_v2/`.
- **Status:** Measured. Model choice waits for Dion; D-068 stays provisional until then. Candidate outcome: DeepSeek for offline JD extraction and Luna for online matching (D-029 rule 5).

## D-077. Development model choice: DeepSeek Flash extracts, GPT-6 Luna matches

- **Date/source:** 4 October 2026. Dion approved after reviewing D-075 and the D-076 Luna check.
- **Decision:** JD extraction stays on DeepSeek Flash (seven-JD extraction F1 0.862 versus Luna 0.794; extraction runs once offline and is cached, so latency does not reach the user). Evidence matching moves to GPT-6 Luna with the D-058 request adaptation. This uses D-029 rule 5 (different models per task).
- **Evidence for matching:** quality not distinguishable from DeepSeek (Macro-F1 difference 0.042, interval -0.067 to 0.148); fewer stronger-than-gold labels (3 versus 6); usable pairs 36 versus 33 under H2v2; equal or better product order on the comparable cells; one-CV K=20 in 62.5 s measured; about US$0.002 per pair versus about US$0.010.
- **Known cost:** Luna gives weaker labels more often (16 weaker-than-gold on the fixed pairs, 94 weaker than DeepSeek on 848 shared units), so percentages tend to be lower. Four of 54 Luna pairs failed processing.
- **Configuration:** `config/versions/pipeline_cp23_provisional_v2_20261004.yaml`. Earlier version files and `config/pipeline_v1.yaml` are unchanged. D-068 is superseded for the matching model only.
- **Status:** Approved for development. Still provisional until the D-053 freeze; held-out test confirms it.

## D-078. Proposed rule for choosing K and PARTIAL weight before the freeze

- **Date/source:** 4 October 2026. **Approved by Dion** (same day). Written before the missing development relevance labels are filled, so the rule is fixed before the deciding numbers exist.
- **Fixed inputs:** D-077 models, H2v2, product order (D-073), seniority rule on (D-074), development CV1/CV2, gold r3 plus the new gap labels (as a new versioned bundle).
- **Seniority rule depth:** stage 1 returns 30 candidates; the rule reorders those 30; the top K of that list is analyzed. This makes every K <= 30 cell exact and matches what the app will do.
- **Rule:**
  1. Primary metric: macro NDCG@10 of the final product order at weight 0.5; secondary: macro P@5.
  2. K in {10, 20, 30}: choose the smallest K whose NDCG@10 is within 0.02 of the best K and whose P@5 is not lower than the best K's P@5 minus 0.1. Smaller K wins ties (faster and cheaper).
  3. Weight in {0.25, 0.5, 0.75} at the chosen K: keep 0.5 unless another weight is better by more than 0.02 NDCG@10.
  4. Seniority rule check: if the rule is worse than no rule on both NDCG@10 and P@5 at the chosen K, freeze without it.
  5. Any cell still missing a label is reported unavailable; it never counts as zero.
- **Limit:** two CVs, so this is a development choice, not a significance claim. The held-out test (D-053) confirms it.

## D-079. Matching model sweep: all candidates under the same current settings

- **Date/source:** 4 October 2026. Dion asked to test all matching candidates at once instead of only Luna and DeepSeek, including models never tested (Claude Sonnet 5.5, Gemini 3.8 Flash, Gemini 3.1 Pro preview, Claude Opus 5.5).
- **Correction recorded with this decision:** GPT-6 Sol was excluded earlier by its D-029 role (quality reference), not by data. Sol minus Luna Macro-F1 is 0.099, unit interval 0.006 to 0.199 (pair interval -0.023 to 0.19), and Sol has only 2 stronger-than-gold labels. So Sol is likely better than Luna on quality, at about 20 times the cost.
- **Stage 1 (cap US$3.00, median-based estimate US$2.64):** ten models (Luna, DeepSeek Flash, Gemini 3.5 Flash-Lite, DeepSeek Pro, Gemini 3.8 Flash, Claude Haiku 4.5, GPT-6 Sol, Claude Sonnet 5.5, Gemini 3.1 Pro, Claude Opus 5.5) on the same four gold pairs, same fixed requirements, evidence prompt v1.1, validator v1.1, dynamic output, 240 s timeout, one call at a time. Request handling per model comes only from public endpoint metadata (temperature omitted when unsupported, output limit clamp, published aliases); prices must be at or below the D-029 ceilings. Evaluation reproduces the D-067 accounting exactly (checked: saved round-one outputs give 0.772, 0.730, 0.829, 0.457, 0.249, 0.642). Rerunning the six earlier models also measures run-to-run label agreement.
- **Stage 2 (cap US$5.00):** models with 4/4 valid pairs and Macro-F1 at least Luna's go to the 60-pair coverage, latency and product-order check. The final matching choice then weighs quality, error direction, coverage, latency and cost; D-077 is revised if another model wins.
- **Extraction:** not part of the sweep. A new extraction comparison needs manual semantic mapping per JD; DeepSeek keeps the highest measured F1.
- **Scripts:** `scripts/run_cp23_model_sweep.py`, `scripts/evaluate_cp23_model_sweep.py`, tests `tests/test_model_sweep.py`.
- **Stage 1 outcome (4 October, run by Dion):** US$1.282, stopped after Gemini 3.1 Pro returned `PermissionDeniedError` (403, US$0) on its last pair, so Claude Opus 5.5 did not run. **Corrected cause (D-081):** the 403 was the OpenRouter workspace lifetime budget of US$5.00 being exceeded at that moment, not a model-level restriction. Stopping the whole run was the right behaviour; the later change that made 403 skip only one model was wrong and is reverted. Result: `evals/results/cp23/dev_eval_v2_20261004/model_sweep_stage1_v1.json`.

  | Model | Valid pairs | Macro-F1 (all 73 units) | Stronger / weaker than gold | MATCH precision | Cost per valid pair | Pair p50 | Same label as earlier run |
  | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
  | GPT-6 Sol | 4/4 | 0.846 | 4 / 7 | 0.91 | US$0.038 | 17 s | 0.88 |
  | Claude Sonnet 5.5 | 4/4 | 0.786 | 1 / 15 | 1.00 | US$0.084 | 34 s | new |
  | Gemini 3.8 Flash | 4/4 | 0.747 | 2 / 16 | 0.93 | US$0.048 | 36 s | new |
  | GPT-6 Luna | 4/4 | 0.736 | 4 / 14 | 0.96 | US$0.002 | 21 s | 0.90 |
  | DeepSeek Pro | 4/4 | 0.663 | 6 / 14 | 0.84 | US$0.014 | 86 s | 0.86 |
  | DeepSeek Flash | 3/4 (one 252 s timeout) | 0.578 (0.726 answered) | 3 / 9 | 0.88 | US$0.028 | 34 s | 0.82 |
  | Gemini 3.5 Flash-Lite | 2/4 | 0.477 | 8 / 5 | 0.74 | US$0.021 | 7 s | 0.81 |
  | Gemini 3.1 Pro | 2/4 (one invalid output; one 403 from the workspace budget, an infrastructure failure) | 0.420 | 0 / 10 | 1.00 | US$0.148 | 30 s | new |
  | Claude Haiku 4.5 | 2/4 | 0.405 | 2 / 7 | 1.00 | US$0.061 | 14 s | 1.00 |
  | Claude Opus 5.5 | not run | - | - | - | - | - | - |

  Paired bootstrap against Luna: Sol +0.110 (unit -0.001 to 0.225, pair 0.022 to 0.182); Sonnet +0.050 (unit -0.044 to 0.149); Gemini 3.8 Flash +0.011 (unit -0.077 to 0.103); DeepSeek Pro -0.073. Stage-2 gate passed: Sol, Sonnet, Gemini 3.8 Flash. Run-to-run label agreement of the same model across two runs is 0.81 to 0.90, so a single run moves Macro-F1 by several points (DeepSeek Flash 0.772 earlier, 0.578 now with one timeout).
- **Follow-up prepared:** `--continue-models claude-opus-5.5` runs Opus only under the same plan and the same cumulative US$3.00 cap (US$1.72 left, Opus estimate US$0.98). Superseded by the D-081 budget recovery run, which also redoes the Gemini 3.1 Pro pair blocked by the same budget. Stage 2 runner: `scripts/run_cp23_matcher_coverage.py --model <key>`, cumulative US$5.00 cap. Gemini 3.8 Flash and Sonnet are dominated by Luna and Sol respectively on cost and quality, so only Sol is proposed for stage 2 (estimate US$2.45).
- **Opus continuation (4 October):** the first Opus request was rejected with `PermissionDeniedError` (403) after 115 ms at US$0, before any generation. An earlier version of this entry said the block was specific to Opus access; **that was wrong**. Dion's minimal direct probe returned the provider message `Workspace lifetime budget of $5.00 exceeded. Contact your org admin.` (D-081). Sonnet and the others had succeeded only because they ran before the workspace total crossed US$5. Opus and Gemini 3.1 Pro CV2/F00018 are infrastructure failures, not model results; their v1 failure files are kept as provenance.
- **Status:** Stage 1 complete for eight models plus Gemini 3.1 Pro on 3 of 4 pairs; Opus and one Gemini pair wait for the D-081 budget recovery. Stage 2 proposed for Sol only.

## D-080. Fair retriever comparison labels

- **Date/source:** 4 October 2026. Dion approved labeling every unjudged job in the top 20 of all six retrieval methods, plus the Hybrid Qwen top 30.
- **Workbook:** `evals/labeling/dev_relevance_gap_20261004_v2/` (46 items: 24 CV1, 22 CV2), blind and shuffled. It replaces the unfilled 14-item v1 workbook.
- **Use:** after Dion's labels are imported into a new versioned gold bundle (r3 unchanged), all six methods have complete top-20 judgments, so Recall@20 and the B0 versus Hybrid comparison are no longer biased by the pool; the seniority rule and an offline Hybrid+B0 fusion are compared on the same footing. Embedding choice (D-044) is not reopened: Qwen won on both CVs under a pre-registered rule.
- **Status:** Approved; labeling pending.

## D-081. OpenRouter workspace lifetime budget versus the JobFit guard

- **Date/source:** 4 October 2026. Root cause confirmed by Dion with a minimal direct probe to `anthropic/claude-opus-5.5` ("Reply only with OK."): HTTP 403 `Workspace lifetime budget of $5.00 exceeded. Contact your org admin.`
- **Three separate limits:**
  1. **OpenRouter workspace (organization) lifetime budget:** set in the OpenRouter dashboard by the org admin. It counts all spending in that workspace, from every key and from playground use, over its whole life. It was US$5.00 and blocked every model with 403 once crossed.
  2. **OpenRouter key credit limit:** a per-key cap in the key settings (D-031). Separate from the workspace budget.
  3. **JobFit guard (`API_BUDGET_USD=19`, `API_HARD_STOP_USD=18.5`, D-070):** local, computed from `reports/usage/usage_ledger.jsonl`. It only sees calls made through the JobFit client, so it cannot see other keys, playground use or direct probes. It does not change, and is not changed by this entry.
- **Ledger reconciliation:** the local ledger shows US$4.4173 reported plus US$0.1782 of uncertain timeout reservations (US$4.5956) when the block happened. OpenRouter counted more than US$5.00 for the workspace, so at least about US$0.40 came from outside this ledger (other keys, playground, direct probes, or charges on requests the ledger holds as uncertain). Dion checks the workspace usage page to reconcile.
- **Required dashboard change (Dion, not code):** raise the workspace lifetime budget so it is not lower than the planned spend. Recommendation: set it to the credit actually bought (about US$19, D-070), keep the key limit at or below that, and use this workspace and key only for JobFit so the outside spend stays visible. The JobFit `.env` stays at 19 / 18.5.
- **Code changes:** `scripts/probe_openrouter_access.py` (one tiny structured request per model, at most 64 output tokens, no CV or JD text; prints only the redacted provider message, its classified cause and the key's numeric usage/limit). Paid sweep and stage-2 runs now call this probe first and stop before any benchmark call if a model is blocked. HTTP 403 again stops the whole run. `--budget-recovery` redoes only the five pairs blocked by the budget (four Opus, one Gemini 3.1 Pro) into `evals/results/cp23/model_sweep_v1/continuation_2/`; v1 failure files stay; the evaluator prefers the recovery file and records it. Same cumulative US$3.00 stage-1 cap (US$1.72 left, estimate US$1.11).
- **Status:** Root cause recorded. Recovery waits for Dion's dashboard change and probe.

## D-082. D-079 results after the budget recovery and the Sol 60-pair check; matcher proposal

- **Date/source:** 4 October 2026, runs by Dion after raising the OpenRouter workspace budget (D-081).
- **Budget recovery (US$0.6305):** access probe passed for Opus and Gemini 3.1 Pro; all five blocked pairs completed. Final stage-1 table (`evals/results/cp23/dev_eval_v2_20261004/model_sweep_stage1_v3.json`):

  | Model | Valid pairs | Macro-F1 | Stronger / weaker than gold | MATCH precision | Cost per pair | Pair p50 |
  | --- | ---: | ---: | ---: | ---: | ---: | ---: |
  | GPT-6 Sol | 4/4 | **0.846** | 4 / 7 | 0.91 | US$0.038 | 17 s |
  | Claude Sonnet 5.5 | 4/4 | 0.786 | 1 / 15 | 1.00 | US$0.084 | 34 s |
  | Claude Opus 5.5 | 4/4 | 0.770 | 0 / 17 | 1.00 | US$0.136 | 32 s |
  | Gemini 3.8 Flash | 4/4 | 0.747 | 2 / 16 | 0.93 | US$0.048 | 36 s |
  | GPT-6 Luna | 4/4 | 0.736 | 4 / 14 | 0.96 | US$0.002 | 21 s |
  | DeepSeek Pro | 4/4 | 0.663 | 6 / 14 | 0.84 | US$0.014 | 86 s |
  | Gemini 3.1 Pro | 3/4 | 0.639 | 1 / 14 | 0.95 | US$0.127 | 34 s |
  | DeepSeek Flash | 3/4 | 0.578 | 3 / 9 | 0.88 | US$0.028 | 34 s |
  | Gemini 3.5 Flash-Lite | 2/4 | 0.477 | 8 / 5 | 0.74 | US$0.021 | 7 s |
  | Claude Haiku 4.5 | 2/4 | 0.405 | 2 / 7 | 1.00 | US$0.061 | 14 s |

  Against Luna: Sol +0.110 (pair interval 0.022 to 0.182), Sonnet +0.050, Opus +0.033, Gemini 3.8 Flash +0.011 (the last three intervals include zero). Opus and Sonnet never overclaim MATCH but miss more true MATCH labels; both cost more than Sol and score lower, so they were not sent to stage 2. Gemini 3.8 Flash costs about 28 times Luna for the same quality.
- **Sol 60-pair check (US$1.4808, `evals/results/cp23/matcher_coverage_gpt-6-sol_v1/`, comparison `sol_comparison_v1.json`):** all 54 called pairs process-valid, no repair needed; usable pairs under H2v2 **40 of 60** (Luna 36, DeepSeek 33). One-CV K=20 wall time **35.4 s with 9 workers** (pair p50 15 s, max 23 s); Luna needed 62.5 s with 20 workers. Product order: CV1 K=10 P@5 0.2, NDCG@10 0.356; CV1 K=20 P@5 0.6, NDCG@10 0.419; CV2 K=10 P@5 0.6, NDCG@10 0.739; CV2 K=20 unavailable (F00645 unlabeled). On shared units Sol agrees with DeepSeek on 784 of 889 (stronger 41, weaker 64).
- **Cost view:** about US$0.027 per matched pair in the 60-pair run, so about US$0.55 per CV at K=20, versus about US$0.04 for Luna. Ledger after the runs US$6.71. The key credit limit is still US$9.32 and must be raised before broad extraction and the test run.
- **Proposal (approved by Dion, see D-083):** matching model GPT-6 Sol (best quality with a supported margin over Luna, 100 percent process-valid, fastest, most usable pairs); Luna stays the documented low-cost fallback. Extraction stays DeepSeek Flash. If approved, this supersedes the matching part of D-077 and creates a new configuration version file; the D-078 rule for K and weight then runs with Sol scores once the 46 labels are imported.

## D-083. Development model choice revised: GPT-6 Sol matches, Luna is the fallback

- **Date/source:** 4 October 2026. Dion approved the D-082 proposal.
- **Decision:** evidence matching uses GPT-6 Sol with the metadata-based request handling of D-079. GPT-6 Luna stays the documented low-cost fallback (about US$0.04 versus about US$0.55 per CV at K=20). JD extraction stays DeepSeek Flash. This replaces the matching part of D-077; D-077's extraction choice and all other settings stand.
- **Evidence:** D-082 (Macro-F1 0.846 versus 0.736, pair-bootstrap interval for the difference 0.022 to 0.182; 54 of 54 pairs valid; 40 of 60 usable pairs; one-CV K=20 in 35 s with 9 workers).
- **Budget:** Dion raised the OpenRouter key credit limit and the workspace lifetime budget to about US$19 (4 October). The JobFit guard stays at 19 / 18.5. Ledger US$6.71 after the D-082 runs.
- **Configuration:** `config/versions/pipeline_cp23_provisional_v3_20261004.yaml` (adds `stage1_candidate_depth: 30` from D-078). Earlier version files unchanged.
- **Next:** import the 46 gap labels as a new gold bundle after Dion approves, compare retrievers on complete top-20 judgments, apply D-078 with Sol scores, then prepare the D-053 freeze.
- **Status:** Approved for development; the held-out test confirms it.


## D-084. Rule for changing the stage-1 retriever (set before the r4 numbers)

- **Date/source:** 6 October 2026. Approved by Dion in chat before the 46 gap labels were imported or any r4 metric was computed.
- **Rule:** Hybrid Qwen stays the stage-1 retriever unless a challenger (B0, B1, dense Qwen, dense OpenAI, hybrid OpenAI, or the offline Hybrid Qwen + B0 RRF fusion) has macro NDCG@10 at least 0.05 higher and macro P@5 not lower than Hybrid Qwen, both with the D-074 seniority rule on, on complete development judgments for CV1 and CV2. A challenger with a missing label in the needed positions is reported unavailable and cannot win.
- **If a challenger wins:** this is a new development iteration. Its top 30 needs new Sol matching on development before the D-053 freeze; no test job is touched.
- **Implementation:** `scripts/run_post_labeling.py` (`PROPOSED_RETRIEVER_RULE`, now approved).
- **Limit:** two CVs; the margin is a practical threshold, not a significance test.
- **Status:** Approved.

## D-085. Import of the completed gap workbook into gold r4

- **Date/source:** 6 October 2026. Dion finished `JobFit_Dev_Relevance_Gap_v2_v1.3_Final.xlsx`, asked for it to be checked and used, and chose in chat: G04 is unjudged, not 0; the A/B sheets are imported as extra development gold.
- **Relevance:** 45 new rows (CV1 23, CV2 22). G04 (CV1/F00559) was marked UNSCORABLE by Dion because the JD has no candidate requirements. It is stored as a source-quality hold in `held_gap_v2.json`, never as 0 (D-052).
- **Extraction and evidence:** 759 units for 39 JDs and 826 evidence rows for 42 CV/JD pairs, stored in `extraction_gold_gap_v2.jsonl` and `evidence_gold_gap_v2.jsonl` with their own unit namespace `gap_v2`. Seven of the JDs (F00029, F00052, F00126, F00212, F00332, F00556, F00650) already have r3 extraction gold; the r3 units stay authoritative and the two sets are never merged. One evidence row (CV2/G33-U27, `needs_clarification`) is held.
- **Provenance:** the sheets were drafted by a model and accepted by Dion (`draft_note`: Stage 5 model draft). They are recorded as `model_draft_assisted_human_accepted`, the D-047 development practice, not as blind labels. D-080 described the workbook as blind; that description no longer holds for these labels and is corrected here.
- **Checks:** every A source quote is found in its JD text, every MATCH/PARTIAL quote in its CV text, every B unit exists in A, identities match the manifest, Items and C_Relevance agree except G04. r3 files are copied byte for byte and re-hashed after the import.
- **Bundle:** `evals/gold/development_v13_reviewed_20261004_gap_r4/` (script `scripts/import_dev_gap_r4.py`). r3 is unchanged.
- **Status:** Approved by Dion; written.

## D-086. Development configuration for the freeze (D-078 result, D-084 result, experience block)

- **Date/source:** 6 October 2026. Computed by `scripts/run_post_labeling.py` on gold r4 (`evals/results/cp23/post_labeling_development_v13_reviewed_20261004_gap_r4_v1/summary.json`); the experience block was approved by Dion in chat after seeing the numbers.
- **D-078 result (mechanical):** K = 10, PARTIAL weight 0.5, seniority rule on. Final product order macro P@5 0.70, NDCG@10 0.552 (CV1 0.483, CV2 0.620). No weight beat 0.5 by more than 0.02; the rule is not worse than no rule.
- **D-084 result:** Hybrid Qwen stays. Best challenger on NDCG@10 was dense Qwen (+0.029, P@5 -0.2) and the Hybrid + B0 fusion (+0.004, P@5 -0.1); none met the rule. Dense OpenAI with the rule is unavailable (missing labels).
- **Experience block (approved):** rule `experience-upper-bound-v1` is part of the frozen order. A job moves to the "possible conflict" block only when the whole confirmed CV work history is shorter than a required minimum; the score itself does not change. At K = 10 it raises CV1 NDCG@10 from 0.483 to 0.515; CV2 is unchanged; P@5 is unchanged. Macro with the block: P@5 0.70, NDCG@10 0.568.
- **Honest reading:** with the seniority rule, stage 1 alone already gives P@5 0.70 and NDCG@10 0.550. The LLM match order at K = 10 is equal, not better, and at K = 20 or 30 it is worse (P@5 0.40 and 0.30), mostly because held jobs and match-percentage sorting pull in less relevant jobs. The value of stage 2 is the evidence and gap explanation per job, not a ranking gain. Two CVs only; the D-053 test confirms or refutes this.
- **Configuration:** `config/versions/pipeline_cp23_freeze_candidate_v4_20261006.yaml`. Earlier version files unchanged.
- **Status:** Approved for the freeze draft; the freeze itself needs Dion's approval of the receipt (D-053).

## D-087. D-053 configuration and protocol freeze approved

- **Date/source:** 6 October 2026. Dion wrote "approve freeze v2" in chat after asking for, and checking, the CP2.4 report contract.
- **What is frozen:** the receipt `evals/freeze/cp23_freeze_draft_v2/freeze_receipt.json` (sha256 `18c1d17c41588a4780a6dfec147947057191f361434146b634890364a0e3a6f8`): config `pipeline_cp23_freeze_candidate_v4_20261006.yaml` (D-086), the stage-1, extraction and matching call settings, the experience block, the D-053 pool rule, D-052 metrics, gold r4, the splits and 57 file hashes.
- **Report contract (frozen):** `cp24-report-contract-v1`. The headline held-out result is CV3-CV5 only (held-out profiles and jobs). CV1-CV2 are a separate familiar-profile diagnostic. No pooled CV1-CV5 metric is produced (`src/jobfit/eval/heldout_report.py`, `check_contract`).
- **From now on:** no model, prompt, K, weight, rule, metric or report change because of test results (D-046, D-053). A bug fix is recorded and the whole test is rerun; any other change is a new development iteration.
- **Next:** Dion runs `python scripts/prepare_cp23_freeze.py --approve evals/freeze/cp23_freeze_draft_v2 --decision D-087`, then the CP2.4 phases in the runbook.
- **Status:** Approved.

## D-088. CP2.4 test labels: provenance correction and import as test_v13_cp24_r1

- **Date/source:** 7 October 2026. Before the gold import, Dion told me in chat that he labeled the CP2.4 test workbook with help from ChatGPT. ChatGPT assessed the CV-JD pairs and gave recommendations; Dion reviewed every pair and made the final decision. During labeling he did not see the JobFit rank, score, retriever method, JobFit model suggestions or `pool_provenance.json`.
- **Provenance:** `ai_assisted_human_reviewed_blind_to_ranking`. The labels are blind to the system output, but they are NOT pure human gold and NOT independent human annotation. One reviewer, no inter-annotator agreement. This deviates from the D-053 wording "no model suggestions". D-053 itself is not edited; this record is the correction.
- **Why it is still usable:** the configuration was frozen (D-087) before labeling, the labels never saw the system ranking, and the test set was not used for tuning. So it is valid for an internal held-out evaluation, with the disclosures below.
- **Required disclosures in every CP2.4 report:**
  - AI-assisted (ChatGPT) and human-reviewed by one reviewer; not independent human annotation.
  - "Because the labeling assistant and matcher are both OpenAI-family models, correlated model preferences may inflate apparent agreement. The direction and magnitude of this bias were not independently measured."
  - The headline covers three synthetic CVs (CV3-CV5); results are indicative only.
- **Headline:** CV3-CV5 stay the primary held-out headline under `cp24-report-contract-v1`, with the disclosure next to the numbers. CV1-CV2 stay a supplementary diagnostic. No pooled CV1-CV5 metric.
- **Source and corrections (approved by Dion):** the label source is sheet `C_Relevance` of `JobFit_Test_Relevance_Final_.xlsx` (the Items sheet is empty and not used). T68 (CV5/F00070) becomes an unscorable source-quality hold, unjudged and never 0 (D-052): the JD has responsibilities only and zero A_Extraction units. Five `main_reason` texts (T17, T21, T23, T43, T50) had requirement text cut with "…"; the cut part is filled with the full `unit_text` of the same job from A_Extraction. Change summary: 1 relevance-label change (T68 2 -> UNJUDGED); 5 text-only corrections (T17, T21, T23, T43, T50); 0 other relevance/score changes. The one empty `pilot_id` (T68) is noted in the manifest.
- **Bundle:** `evals/gold/test_v13_cp24_r1/` (script `scripts/import_test_labels_cp24_r1.py`): `relevance_gold.jsonl` (67 judged), `held_test_r1.json` (T68), `relevance_before_correction.jsonl` (all 68 as in the sheet), `correction_diff.json`, `provenance_manifest.json`, `import_receipt.json`. Both workbooks are unchanged (sha256 before and after in the receipt). The first write of this bundle said "no score changed" next to the T68 change; Dion asked for the wording to be explicit, so the bundle was rebuilt with a `change_summary` and the first version is kept in `evals/gold/archive/test_v13_cp24_r1_metadata_v1/` (labels and texts identical). The freeze verify stays ok; no frozen file, model, prompt, K, metric or rule changed.
- **Next:** Dion reviews the bundle. Only after that is `scripts/evaluate_cp24_test.py` run on it.
- **Status:** Approved by Dion; written. Evaluator not run.

## D-089. Phase A started: post-test quality optimization on development data; CP2.4 locked

- **Date/source:** 7 October 2026. Dion asked for a quality-first optimization phase (Phase A) after CP2.4, with cost and latency recorded but not optimized yet (that is Phase B, not started).
- **CP2.4 is locked from optimization.** Its labels (`test_v13_cp24_r1`), workbook, results (`evals/results/cp24/`), the held-out CVs CV3-CV5 and the test jobs are never used to choose anything. `src/jobfit/eval/qa_phase_a.py` refuses those paths, CVs and jobs (`LeakageError`), and tests check it. D-087, D-088, `heldout_report_v1.json` and the CP2.4 contract stay unchanged. CP2.4 is not rerun to compare challengers.
- **Claim boundary:** any Phase A result is post-test development optimization, not an improved held-out result. Testing generalization needs a new fresh test set that Phase A never touched.
- **What may change:** the evidence-matching prompt only, as new versioned files (`prompts/evidence_matching_v1_2_qa_e0N.md` plus a metadata file with the sha256). Model (GPT-6 Sol, frozen request rules, no fallback in Phase A), retriever, K 10, weight 0.5, seniority and experience rules, H2v2, schema, validator v1.1 and G1/G2 stay as in D-087. The frozen matcher file is not edited; the runner points it at a challenger prompt only inside its own process.
- **Development data:** (1) QA-DEV-FI-v1: gold gap_v2 requirement units as matcher input and their gold labels as the answer (42 CV1/CV2 pairs, 826 units; model-draft-assisted, accepted by Dion, D-085), split by job with seed 20261007 into an optimization subset (20 pairs, 411 units) and a confirmation subset (22 pairs, 415 units); (2) QA-DEV-RANK-v1: the 20 analyzed top-10 pairs of CV1/CV2 with gold r4 relevance; (3) the r3 anchor (73 units) from saved outputs. Denominators are reported separately, never pooled.
- **Baseline QA-E00-BASELINE (no call):** reproduced from saved artifacts: P@5 0.70, NDCG@10 0.567 (equal to D-086 with the experience block), hold rate 4/20, quote validity 676/676, anchor macro-F1 0.846, anchor run-to-run agreement 64/73.
- **Selection rule (proposed before any Wave 1 result; Dion approves it with Wave 1):** a challenger is a finalist only if, against the two baseline runs on the optimization subset: unsupported positives are not higher than the higher baseline run and quote validity stays 1.0; failed pairs are not more than the baseline maximum plus one; macro-F1 beats the baseline mean by more than the larger of 0.02 and the baseline R1/R2 gap; the gain holds with any single pair left out; and on QA-DEV-RANK-v1 P@5 is not lower and NDCG@10 is not lower by more than 0.02 than the saved baseline. A finalist is then run once on the confirmation subset with a new experiment ID next to a new baseline run; it must keep the direction and pass the same grounding checks. If nothing passes: keep the baseline. Note: Dion's brief asks for a ranking improvement; here ranking is a non-inferiority check, because on two development CVs a matching prompt can only reorder the same 10 analyzed jobs. This difference needs Dion's decision.
- **Stopping rule:** stop after (a) a finalist is confirmed, or (b) two waves without a finalist, or (c) gains that only trade one metric against grounding or reliability.
- **Wave 1 (proposed, not run):** QA-E00-FI-R1 and R2 (baseline twice), QA-E01 (QA-H01, MATCH/PARTIAL calibration), QA-E02 (QA-H02, direct-evidence check), QA-E03 and QA-E03-R (QA-H03, ordered procedure and self-check). 177 calls, estimate US$5.16, upper US$7.22, cap US$7.50 for the whole wave inside the project guard.
- **Dion's final decisions (7 Oct 2026, after reviewing the proposal):**
  - Selection hierarchy: (1) grounding/correctness is a hard gate; (2) schema/reliability is a hard gate; (3) unit matching quality is the primary objective; (4) ranking is non-inferiority only (P@5 not lower than baseline, NDCG@10 not lower by more than 0.02); (5) hold/unscored behavior is a secondary diagnostic; (6) cost/latency is observability only. A prompt with better ranking but worse grounding or more hallucinations is rejected.
  - Development references keep their source provenance: gap_v2 labels are `model_draft_assisted_human_accepted` (drafted with model help, accepted by Dion); r3 anchor labels are model drafts reviewed by the user with delegated follow-up QA. They are not independent human ground truth, and they may carry correlated model preferences if the draft model shares a family with the matcher. Phase A never edits them. Counts from the source metadata: `evals/results/quality_optimization/benchmark_v1/provenance.json`.
  - GPT-6 Sol without the Luna fallback during prompt experiments. Results measure primary-Sol prompt behavior, not full production fallback reliability; a separate full-pipeline integration run checks the deployment configuration after a prompt is chosen.
  - Failure taxonomy and QA-H01/H02/H03 approved; the taxonomy is never changed from confirmation results.
  - The confirmation subset (22 pairs, 415 units) stays sealed during Wave 1 selection: no per-item confirmation result is shown and nothing is fixed from it. It opens only after exactly one finalist is recorded (code: `confirmation_unsealed`).
  - Staged Wave 1: QA-E00-FI-R1, QA-E00-FI-R2, QA-E01, QA-E02, QA-E03, in that order (each needs the previous one run and evaluated), then stop and report. QA-E03-R runs only if E03 is still competitive and repeatability matters for the decision.
  - Dion runs every paid call on his Mac, one command at a time.
- **Amendment 1 (7 Oct 2026, Dion; written after QA-E00-FI-R1/R2 and before any challenger run):**
  - The +0.02 macro-F1 bar is no longer a hard gate. 0.7343 (baseline mean 0.7143 + 0.02) is the practical improvement reference.
  - Hard gates (reject if any fails): quote validity 1.0 with 0 invalid quotes; unsupported positives not above the baseline maximum (59); prompt-induced failed pairs not above the baseline maximum (0; transient failures are excluded, see below); ranking non-inferiority (P@5 >= 0.70, NDCG@10 >= 0.547).
  - Eligible as finalist if it passes the gates, has no other regression (underclaims <= baseline max + 5, unassessed units <= baseline max + 2), and meets path A or B. Path A (quality): macro-F1 >= 0.7343, accuracy >= baseline mean, and with any single pair left out accuracy stays at or above the baseline on the same pairs. Path B (product errors): unsupported positives <= 53 and overclaims <= 60 (both 10% below baseline), macro-F1 and accuracy not below the baseline mean, and fewer unsupported positives in at least 3 pairs. Error categories (over/under/unassessed by field) are reported with every decision.
  - Exactly one provisional finalist: lowest unsupported positives (candidates within 2 of the lowest stay), then highest macro-F1, then accuracy, then lowest ID. None eligible: keep the baseline.
  - Repeat: the finalist runs again on the same optimization subset as `<ID>-R2` (QA-E01-R2, QA-E02-R2 or QA-E03-R2). The repeat must pass the same gates (ranking not rerun) and stay eligible. The fixed QA-E03-R is withdrawn (never run). The confirmation subset stays sealed until the repeat passes.
  - Failure handling: a prompt- or schema-induced failure (schema_validation, truncated, coverage or quote codes) is a quality regression and is never retried. A transient provider/network/budget failure (timeout, connection, rate limit, 403 budget, run cap) is not a prompt error: it gets one documented retry with the same prompt and settings (`recover`; the failed record is moved with its sha256, never edited); if it fails again the run is marked invalid and repeated later under a new ID. Unknown codes are decided by Dion. Retries are never used to fish for better outputs.
  - Numbers are locked in `evals/results/quality_optimization/selection_rule_v2.json` (written before any challenger result; the selection, repeat and unseal code reads only this file).
  - Budget: no run starts unless the provider key's `limit_remaining` covers its upper estimate (checked read-only before every paid run). `budget-plan` computes the needed key limit from the ledger, the remaining upper bounds, the finalist repeat, the confirmation runs and a 10% buffer; `API_HARD_STOP_USD` stays 18.5.
  - Prompts, data, split, taxonomy and metrics of E01-E03 are unchanged by this amendment.
- **Amendment 2 (7 Oct 2026, Dion; after QA-E01, before any QA-E02 call): staged execution and adaptive stopping.**
  - A challenger runs in two stages. Stage A: only the 20 optimization fixed-input pairs, evaluated offline. Stage B: the 19 ranking pairs, only if the Stage A check says `continue_to_ranking`.
  - Stop after Stage A when: quote validity is below 1.0; unsupported positives exceed the locked limit; a prompt/schema-induced failure occurs; another regression appears; or neither path A nor path B can be met. Path A and B are unit-level, so they are final after Stage A and ranking can never rescue a Stage A failure.
  - If QA-E02 stops at Stage A and no challenger is eligible, Phase A stops and the baseline (prompt v1.1) stays. QA-E03 is not run by default; it runs only if E01/E02 leave the decision ambiguous and the H03 information is needed (Dion's call).
  - Locked in `evals/results/quality_optimization/amendment2_staged_execution.json` (prompt, split, rule and code hashes) before any QA-E02 call. Prompts, data, split, labels, taxonomy and the selection thresholds are unchanged.
- **Status:** Approved by Dion, amendments 1 and 2 included. Closed by D-090.

## D-090. Phase A closed: keep the baseline prompt v1.1

- **Date/source:** 7 October 2026. Dion asked to finish Phase A offline after QA-E02 Stage A, following amendment 2 and the locked rule, with no further paid call.
- **Selection (`python scripts/qa_phase_a.py select`, rule `selection_rule_v2.json` sha256 3ab3111a...):** no eligible challenger, so no provisional finalist. Final decision: KEEP BASELINE (prompt v1.1, D-087). No finalist repeat, no confirmation run; the confirmation subset stays sealed and unused.
- **QA-E01 (H01):** hard gates pass; not eligible (macro-F1 0.699 below both paths; overclaims 61 > 60). It replaced weak PARTIAL claims with more full MATCH claims on gold NO_MATCH units (19 to 26). H01 not supported.
- **QA-E02 (H02):** a precision/recall trade-off, not a plain failure. Macro-F1 0.740 and accuracy 0.786 are above the baseline (0.714, 0.753); unsupported positives 37 (59) and overclaims 40 (67-68) fall sharply; path A and path B are both met. But underclaims rise to 33, above the locked no-regression limit 25 (baseline max 20 + 5), so `stage-a-check` stopped it before ranking. The stricter evidence check also removes some true evidence (gold MATCH -> PARTIAL 12, gold PARTIAL -> NO_MATCH 17), mostly in knowledge areas.
- **QA-E03 (H03):** not run (adaptive stopping). E01/E02 did not leave an ambiguity that a stability prompt would resolve.
- **Future direction (not created, not run):** QA-H04 for a possible Phase A2: keep E02's direct-evidence behaviour for named tools, frameworks and components while keeping applied use of a knowledge area as MATCH and related-but-partial evidence as PARTIAL. It needs its own decision, a single preregistered challenger, the same locked rule, and the sealed confirmation subset as the real check, because the optimization subset has already been used by four prompt runs.
- **Cost:** Phase A paid calls US$2.38 (R1 0.50, R2 0.37, E01 0.99, E02 Stage A 0.50, probes under 0.001). Adaptive stopping avoided about US$3.41 (upper US$4.62): E02 Stage B, E03, the finalist repeat and the two confirmation runs. Ledger total US$10.53; `API_HARD_STOP_USD` 18.5 unchanged.
- **Claim boundary:** post-test development optimization only. CP2.4, D-087, D-088 and their files are unchanged.
- **Status:** Closed.

## D-091. Accept the extraction scope used in CP2.3; full development extraction stays optional

- **Date/source:** 7 October 2026. Approved by Dion after the [CP2 closeout audit](checkpoint_2/CP2_Closeout_Audit_20261007.md) listed the D-050 carry-over as still open.
- **Background:** D-050 closed CP2.2 and moved extraction of all development JDs to "after CP2.3 configuration evaluation". The CP2.3 criterion in the master plan asks for a per-JD status of what was run, or an approved revised scope.
- **What was actually extracted:** the development split has 214 JDs. A per-JD inventory of all 214 exists from 3 October (`evals/results/cp22_development_extraction_plan_20261003.json`). For configuration selection, extraction ran on the 52 JDs in the Hybrid Qwen top 30 of CV1 and CV2: 51 attempted, 48 process-valid, 47 with acceptable JD quality, F00369 held at source (`evals/results/cp23/pipeline_v11/coverage_summary_v2.json`). The other 162 development JDs were never extracted.
- **Why 52 was enough:** every choice that depends on extraction was made inside the top 30. D-078 compares K = 10, 20 and 30 inside the reordered top 30, and the seniority rule only reorders those 30, so a job outside them cannot change any result. Failed or held extractions inside the top 30 stayed holds, never zeros (D-052, D-073). The model choice used the fixed seven-JD and four-pair references (D-068, D-077, D-083).
- **Why CP2 does not need the rest:** the frozen product extracts and caches each JD when it is analyzed; CP2.4 handled its 26 test JDs that way. The full 214-JD run (bounded at US$21.0576 in the CP2.2 plan) was never needed for any evaluation result.
- **Unchanged:** no test data was used; the test split was opened only after D-087. D-087, its 57 frozen hashes, the CP2.4 result, gold, split, prompts, models, K, weight and rules stay as they are. No inference is approved here.
- **Later:** extracting the remaining JDs is optional and needs its own budget if production caching or a wider evaluation calls for it.
- **Status:** Approved. Closes the D-050 carry-over.

## D-092. Privacy status in CP2; end-to-end validation and the masked comparison move to CP3

- **Date/source:** 7 October 2026. Dion approved deferring the paired comparison after the closeout audit, and clarified the same day that privacy has **not** been validated end to end and must not be described as fully validated, proven safe or proven to have no effect on matching quality.
- **Implemented:** local masking (`src/jobfit/privacy/masking.py`), an editable preview with consent tied to the exact masked text, owner-scoped sessions with lease, idle and absolute expiry and delete, upload cleanup, and the 403 gate that keeps real-CV provider processing off. The frozen pipeline parses masked text; all five CP2.4 parse records carry masking counts.
- **Component/unit tested:** `tests/test_privacy_controls.py` (12 tests), `tests/test_cp23_masking_quotes.py` (1), `tests/test_cp23_masking_pairs_preflight.py` (2, offline preflight only) and `tests/test_api_privacy.py` (8, FastAPI layer with a fake run, PR-01 to PR-07 and PR-09; the file itself says a pass "covers this measured scope only, not a deployed host"). The masked-quote receipt (`evals/results/cp23_masking_quote_compatibility_20261004_v1.json`, 13 changed rows, all traceable) only checks that quotes can still be traced. The local scripted API check with synthetic canaries in EXP-20261006-CP3 is CP3 work and is not end-to-end validation either.
- **Not done:** end-to-end privacy validation of the integrated or deployed system (two-user isolation, browser liveness and expiry, provider payload checks, log/database/backup inspection, measured deletion timing, the PR-08 provider policy check), and the original-vs-masked matching comparison (PR-10).
- **Decision:** both move to CP3. CP3.4 runs the end-to-end privacy checks (leakage, logs, outputs, consent and session behavior) and the original-vs-masked comparison. CP3.5 reports the privacy results and the matching-quality impact.
- **Why this does not reopen CP2:** neither item is a configuration choice, and none of D-078, D-084 or D-087 depends on them. CP2.4 already ran with the masking the product uses. The master plan already puts deployed privacy acceptance in CP3.4.
- **Claim limits:** CP2 documents privacy as implemented and component/unit tested only. It does not claim end-to-end validation, end-to-end safety or no effect on matching. Real-CV processing stays off (`/cv/parse` answers 403) until the D-051 release gates, the CP3.4 checks and separate consent are in place.
- **Unchanged:** the D-051 design, D-087, the CP2.4 result and all frozen files. No experiment or paid call is approved here.
- **Status:** Approved (deferred to CP3.4 and CP3.5).

## D-093. CP2 mentor feedback taken into CP3

- **Date/source:** the CP2 presentation and mentoring session was on 4 October 2026. The D-069 amendment notes at 08:13 WIB that the presentation was about six hours away, and the 4 October audit report starts with "After the CP2 presentation"; the exact time was not written down. On 7 October Dion confirmed the session and gave the mentor's feedback:
  > "Latency LLM nya cukup tinggi yaitu 95 s, maka dibuat semacam UI atau animasi menunggu seperti Claude thinking agar user tidak bosan.
  > Jika core fitur sudah jadi, tambahkan fitur utk memperbaiki CV atau saran perbaikan CV utk lowongan tersebut, sehingga menaikkan matching nya."
- **In English:** (1) LLM latency is high, about 95 seconds; add a waiting UI or animation, like a "thinking" indicator, so the user does not get bored. (2) Once the core features work, add CV improvement suggestions for the target vacancy so the user can raise the match.
- **Context:** the 4 October deck showed development results, including a DeepSeek Flash matching request p95 of about 91 s (D-068); 95 s is the mentor's figure. Matching later moved to GPT-6 Sol; in the held-out run, one CV took 37.2 to 87.2 s (median 80.6 s) to match (CP2.4 section 10b).
- **A, waiting-state UX (CP3):** show a clear waiting state for long analyses (progress, current step, a "thinking" indicator). This makes the wait easier to sit through; it does not make the model faster, and no speed-up is claimed unless one is measured. The UI already has a per-job progress bar and a spinner (`ui/streamlit_app.py`); check those first instead of building a second feature.
- **B, CV improvement guidance (CP3, after the core flow is stable):** suggestions come from the user's real CV evidence, the target JD's requirements and the gaps found. They never invent experience or encourage overstating skills. A CV edit only raises the evidence-coverage score when it adds true evidence, and it does not guarantee a better real fit. This extends the CV coach plan (D-036, [cv-coach-plan.md](cv-coach-plan.md)) and CV coach v1 (EXP-20261006-CP3) rather than adding a new feature.
- **Unchanged:** the CP2.4 evaluation, D-087, the held-out result, thresholds and CP2 tuning. No paid call is approved here.
- **Status:** Approved. Meets the CP2.7 criterion that mentor feedback is recorded here as new entries.

## D-094. CP2 closed

- **Date/source:** 7 October 2026, after the final pass of the [CP2 closeout audit](checkpoint_2/CP2_Closeout_Audit_20261007.md). Approved by Dion.
- **Why:** the CP2.1-CP2.7 acceptance work is complete. The held-out evaluation ran under the D-087 freeze and `cp24-report-contract-v1`. Its report, tables, figures and notebooks reproduce from the saved files (21/21 receipt hashes), and `prepare_cp23_freeze.py --verify` shows no changed file. D-091 settled the extraction scope, D-092 moved the unvalidated privacy work to CP3, and D-093 recorded the mentor feedback. Phase A ended with KEEP BASELINE (D-090). Every CP2.1-CP2.8 stage report is current, with older text marked as historical.
- **Moves to CP3 (not CP2 gaps):** privacy validation and the original-vs-masked comparison (CP3.4) and their report (CP3.5), both from D-092; D-093 items A and B; the D-045 test extraction and evidence results (CP3.5); FAIL-35, the three environment-dependent tests that keep the full suite and CI red without affecting CP2 results.
- **Unchanged:** D-087, the CP2.4 result and its frozen files, and D-090. The CP2 claims stay as reported: CV3-CV5 headline P@5 0.5333 -> 0.7333 (3/3 CVs), NDCG@10 0.8047 -> 0.9604 for CV3-CV4 only, F00070 unjudged, CV1-CV2 supplementary, privacy not validated end to end.
- **Status:** Approved. CP2 is closed; CP3 starts from section 11 of the closeout audit.

## D-095. CP3 deployment target, public product scope and branch lifecycle

- **Date/source:** 7 October 2026. Dion and Codex approved the CP3 final execution plan after three review rounds.
- **Hosting (replaces D-023):** a SumoPod VPS in Singapore, Ubuntu Server 24.04 LTS, 2 vCPU / 8 GB RAM / 80 GB storage.
  - Dion and Codex buy and configure the machine (SSH keys, ufw, Docker, DNS, secrets).
  - The repository provides the production compose file, the Caddyfile, the runbook and scripts.
  - Railway is no longer the target.
- **Reverse proxy:** Caddy with automatic HTTPS.
  - Only Caddy publishes ports (80/443). FastAPI, PostgreSQL, Prometheus and Grafana stay on internal Docker networks.
  - FastAPI is never exposed publicly, including for testing. Grafana is reached through an SSH tunnel.
  - The domain is a placeholder (`JOBFIT_PUBLIC_HOST`) until VPS setup.
- **Product scope: full public live JobFit.** Anyone can upload a real CV:
  - safe parsing, local masking with reviewed identifiers, explicit consent bound to the exact masked text;
  - runtime query embedding, hybrid retrieval, lazy JD extraction with a cache, evidence matching, the experience and seniority rules, scoring and ranking;
  - recommendations and the CV coach.

  The saved demo stays as the zero-cost demo and as the fallback for the presentation and for any time live mode is unavailable.
- **Release gate:**
  - Public real-CV live mode (`JOBFIT_PUBLIC_LIVE=1`) is switched on only after the CP3.4 privacy release gate passes on the deployed stack. That gate includes the recorded OpenRouter per-route privacy configuration and a configured `full_analysis_upper_bound` within the daily cap (D-096).
  - Until then the VPS is "deployed dark": saved demo for the public, and owner-token live runs for validation.
- **Deployment:** manual tagged deploys (SSH, check out a tag, `docker compose up -d --build`). Automatic CD stays optional.
- **Validation layers:**
  - A, external public checks through Caddy and Streamlit;
  - B, an internal API `e2e_check.py` run inside the VPS Docker network or through an SSH tunnel.
- **Branch lifecycle:** `cp3-development-20261007` → implementation → validation → feature freeze → review by Dion and Codex → squash or merge into `main` (Dion) → release. Scheduled production workflows run from `main` after that merge. No CP3 implementation reaches `main` before the final review and freeze.
- **Status:** Approved. Planned; nothing is deployed yet.

## D-096. Public live cost and abuse controls

- **Date/source:** 7 October 2026, Dion and Codex.
- **Two budgets:**
  - **CP3 validation:** US$5 in total (live E2E checks, latency measurements, PR-10, the D-045 blind run). I report the reason, cost, benefit and a no-spend alternative before anything would cross it.
  - **Production:** a US$2/day global hard cap (Asia/Jakarta calendar day, configurable).
  - The D-070 project hard stop of US$18.5 covers the development and validation ledger. Production spend is separate and limited by the production key and the daily cap.
- **Deterministic phase bounds:** computed by a non-frozen module from versioned configuration only: allowed model ids, prices in `config/models_v1.yaml`, maximum input and output tokens per task, and maximum call counts including repairs and allowed fallbacks.
  - `parse_max`
  - `recommendation_upper_bound = embed_max + extraction_max + matching_max + fallback_max`
  - `full_analysis_upper_bound = parse_max + recommendation_upper_bound`

  A missing price, limit or count fails closed. `full_analysis_upper_bound` must be at most the daily cap before `JOBFIT_PUBLIC_LIVE=1`. If it is higher, that is a production configuration blocker, reported to Dion and Codex; the bound is never quietly reduced. The planning estimate (about US$0.25-0.6 per run) is never used for enforcement.
- **Separate phase reservations:**
  - `/cv/parse` reserves `parse_max`.
  - `/recommendations` reserves `recommendation_upper_bound`. Query embedding, extraction, matching and fallback are charged only to this reservation, never to the parse reservation.
  - Each reservation is settled from the ledger and the unused part is released at completion, failure or cancel.
  - Admission rule: `settled_spend_today + outstanding_reservations + new_phase_bound <= daily_cap`.
  - No billable provider call runs without an active reservation of its phase.
  - Reservations are persisted. A stale reservation from a crashed process counts in full until the end of the day. If the ledger or reservation state can't be trusted, live admission is refused.
- **Authority:** the persistent production ledger is authoritative, with the provider-side credit limit of a dedicated OpenRouter production key as the outer fail-safe. Prometheus and Langfuse cost figures are telemetry only.
- **Per IP:**
  - One full live CV analysis per IP per 24 hours (rolling). One ticket covers the parse, one recommendation run and up to three pasted-JD analyses in that session.
  - The ticket is consumed at the first billable provider operation (the parse). Refusals before that point (disabled, busy, budget, invalid file, consent failure, preflight failure) do not consume it.
  - A busy or budget refusal of the recommendation keeps the ticket valid for a retry in the same session.
  - IPs are stored only as `HMAC-SHA256(key, ip)` (IPv6 by /64), with rows deleted after 48 hours.
  - The client IP comes from Caddy through Streamlit and is forwarded to the internal API with an internal service token.
- **Global concurrency:** one live analysis at a time (calls inside a run may run in parallel).
- **Other controls:**
  - session creation is rate-limited per IP pseudonym;
  - an owner override token bypasses only the per-IP limit (for a shared presentation network), never the cap, the gate or consent;
  - live and public live are off by default.
- **Status:** Approved. Planned, not implemented.

## D-097. CP3 runtime changes outside the D-087 freeze

- **Date/source:** 7 October 2026, Dion and Codex.
- **Rule:** CP3 production changes go through non-frozen modules and the dependency-injection seams that already exist (`recommend(..., retrieve, extraction_for, client, matcher)`, `api/wiring.py`). The 57 D-087 files stay byte-identical, and `prepare_cp23_freeze.py --verify` must stay `"ok": true`. No change to the model, prompt, K, weights or retrieval configuration.
- **Planned adapters:**
  1. **A concurrency-safe app client** (F2): the frozen client holds a file lock for the whole network call, so live matching runs one call at a time. The adapter keeps request semantics, matching inputs and the model, prompt and config unchanged. It makes the network call outside the long lock, does reservation and in-flight accounting, writes one ledger entry per call and has telemetry hooks. Fake-SDK tests compare serial and concurrent `Recommendation` outputs, and live timing is measured before any latency claim. The mentor's 95 s is not attributed to serialization unless measurement shows it.
  2. **The CP3 consent compatibility adapter around the frozen CP2 parser.**
     - The frozen `parse_cv` uses `is_synthetic` as its real-CV guard.
     - The adapter has no raw-text interface. It is entered only through `SessionStore.dispatch(handle, lease, op)`, passes only the exact consented masked text to the frozen parse logic, and relabels the profile `is_synthetic=False`.
     - Seven required tests: no lease means no call; a changed preview means no call; raw text can't be passed; the payload equals the consented text; `is_synthetic` is False; a late result after expiry or delete is not stored; frozen files are unchanged.
     - If inspection finds another semantic dependency on `is_synthetic`, I stop and report instead of forcing the design.
  3. Runtime query embedding of the consented masked text with the frozen profile.
  4. A production retriever over active, canonical, target-role DB jobs.
  5. A lazy JD extraction provider with a persistent cache and parallel prefetch.
  6. The public recommendation API contract: `cv_source = demo | upload`. The uploaded CV is resolved from the owner's session and never posted back by the browser.
- **Frozen-file edits:** any edit to a frozen file needs a new decision labelled "POST-FREEZE CP3 PRODUCTION CHANGE", with a new freeze-receipt version.
- **Status:** Approved. Planned, not implemented.

## D-098. Mutable production job corpus

- **Date/source:** 7 October 2026, Dion and Codex.
- **Separation:**
  - The frozen CP2 evaluation corpus (the snapshot `CP1_20260926`, splits, gold, freeze receipts and the local CP2 database built by the unchanged loader and `SCHEMA_SQL`) is never touched by production code.
  - The mutable CP3 production corpus lives only in the VPS database. See [production-corpus.md](production-corpus.md).
- **Seed:** a restore-tested dump of the verified local database, 632 rows with Qwen vectors.
  - The 428 target-role rows (dev and test) are active and retrievable.
  - The 204 non-target rows are kept but excluded from retrieval.
  - Serving historical test jobs is allowed, but **CP2 held-out and test labels are never used** for prompt, threshold, ranking, model-selection or retrieval tuning (D-046 rule 4, D-089).
- **Refresh:** JSearch, twice a month (about every two weeks; GitHub cron on the 1st and 15th, not an exact 14-day schedule).
  - GitHub Actions is only the scheduler and SSH trigger: a forced-command key for a dedicated VPS user.
  - JSearch and database credentials stay on the VPS.
  - A versioned production query manifest is required, capped at 80 requests per sync.
- **Identity and dedupe:**
  - Provider identity is `job_sources(source, source_job_id)`, unique on that pair.
  - New IDs are `J` plus 16 hex characters of SHA-256.
  - Exact duplicates map to the one canonical job with no new row (a `duplicate_exact` report counter).
  - Fuzzy probable duplicates (the CP1 rules) are not merged automatically. They become `dedupe_status='review_required'` and inactive, so they are excluded from retrieval until a small review command resolves them.
  - Production retrieval uses only `is_active AND dedupe_status='canonical' AND role_group='target'` with a current embedding.
  - The same vacancy must never appear twice in retrieval.
- **Classification:**
  - NEW;
  - CONTENT_CHANGED (embedding or extraction inputs changed: re-embed, and the extraction cache is invalidated);
  - METADATA_CHANGED (row updated, no re-embedding);
  - UNCHANGED;
  - STALE / INACTIVE.
- **Lifecycle (coverage-aware):**
  - A job counts as missed only when a query that previously found it completed.
  - It becomes inactive after two covered misses, 30 days without being seen, or a trusted provider expiration (none observed so far).
  - It is hard-deleted after 60 days inactive.
  - Embeddings are incremental. There is no extraction during the sync.
- **JD extraction:** lazy with a persistent Postgres cache keyed by the existing extraction cache key (content hash, model, prompt, schema, guideline, scope, context), with a 7-day negative cache for failures. It is seeded from the development saved records only. CP2 extraction evidence stays separate and historical.
- **Database:** a minimal Alembic baseline (raw-SQL revisions): `0001` = the current `SCHEMA_SQL`, so restored databases can be stamped; `0002` = lifecycle, dedupe, sources, sync runs, extraction cache, quota and reservations.
  - Production deploys upgrade only after a verified backup.
  - Downgrade is not a recovery strategy; recovery is the previous app tag plus a database restore.
  - The CP2 `SCHEMA_SQL` and loader stay unchanged.
- **Status:** Approved. The Alembic baseline (`0001`, exact `SCHEMA_SQL`) and production schema (`0002`) are implemented and tested (8 Oct, [CP3.2 report](checkpoint_3/CP3_02_Database_and_CICD.md#results-8-oct-2026-alembic-00010002)); the seed, the sync and the extraction-cache provider are planned, not implemented.

## D-099. CP3 observability

- **Date/source:** 7 October 2026, Dion and Codex.
- **Prometheus and Grafana:** RED metrics for the API, USE metrics for the VPS (node_exporter), and app counters with bounded labels only (no job, session, request or run IDs as labels).
  - Sync results are exposed as gauges from the latest sync run.
  - Two dashboards: service with a small corpus/sync row, and VPS.
  - No cAdvisor in the MVP. The only restart alert is the API restart loop (`process_start_time_seconds`).
- **Alerts:** Grafana-managed alerts sent by email through an SMTP contact point. The settings are `GRAFANA_SMTP_HOST`, `GRAFANA_SMTP_PORT`, `GRAFANA_SMTP_USER`, `GRAFANA_SMTP_PASSWORD`, `GRAFANA_ALERT_FROM` and `GRAFANA_ALERT_TO`; Dion and Codex choose the account during VPS setup.
- **Langfuse Cloud:** Japan region, Hobby plan, metadata only.
  - Input and output capture is off, with a mask function as a backup and a metadata allow-list (run id, stage, model, provider, duration, tokens, cost, retry/fallback, error code, hold status, public job id).
  - Never sent: CV text, names, contacts, addresses, identifying employer history, evidence quotes, pasted JDs or session tokens.
- **Logs:** JSON lines with `request_id`, `run_id`, a session hash, route, status, duration and error code, with Docker log rotation. No CV content, quotes, raw IPs or tokens.
- **Cost figures:** Prometheus and Langfuse cost numbers are not authoritative (D-096).
- **No CORS:** the browser only talks to Streamlit, so no cross-origin call to FastAPI exists.
- **Status:** Approved. Planned, not implemented.

## D-100. CP3 evaluation obligations and feature freeze

- **Date/source:** 7 October 2026, Dion and Codex.
- **Feature freeze:** the formal CP3 feature freeze is at the end of 9 October 2026.
  - Plan for 8 October: core engineering and the dark deployment substantially complete.
  - Plan for 9 October: deployed validation, the privacy release gate, public-live enablement, PR-10 and the freeze.
  - Plan for 10 October: reports, README, deck, video and rehearsal.
  - The presentation stays on 11 October.
  - Freeze criteria: 0 unexpected offline failures, freeze verify ok, the privacy gate status recorded, no P3 work before the presentation.
- **PR-10 (original-vs-masked):** development CV1/CV2 only, on the frozen configuration. It is executed in CP3.4 and reported in CP3.5. Acceptance proposal:
  - quote validity 1.0;
  - no canary in any payload;
  - masked-vs-original agreement within the original-vs-original noise band;
  - macro-F1 drop of at most 0.02.

  A failure is reported, not tuned away.
- **D-045 will be completed as originally written, using option B:**
  - 2 blind test extraction JDs and 1 blind CV3 evidence pair. Dion labels them first, and the frozen pipeline output is produced and shown only after the blind labels are locked (file hash recorded).
  - The existing CP2.4 workbook (A_Extraction, B_Evidence) stays **MODEL-ASSISTED, HUMAN-REVIEWED** and is never relabelled as blind. It covers the model-draft portion.
  - The two groups are reported separately in CP3.5.
  - Later paid inference is about US$0.10, inside the US$5 validation budget.
  - **Phase 0 stop condition:** if 2 eligible unseen test JDs and 1 eligible unseen CV3 pair could not be verified, the work stops and is reported; no seen item is used, no non-blind item is substituted, and D-045 is not redefined. Phase 0 found eligible candidates (see the [CP3.5 report](checkpoint_3/CP3_05_Final_Presentation_and_Portfolio.md)).
- **Status:** Approved. PLANNED / NOT YET COMPLETED.
