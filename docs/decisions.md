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

- **Mentor:** feedback from the CP1 mentoring session on 27 September 2026, as passed on by Dion.
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
| D-019 | 29 Sep 2026 | API budget cap of US$15 for CP2 and CP3 | Approved (budget mechanics changed by D-031) |
| D-020 | 29 Sep 2026 | Embedding model: OpenAI `text-embedding-3-small` | Approved (called through OpenRouter, D-030) |
| D-021 | 29 Sep 2026 | Synthetic CVs by default; real CV only after explicit confirmation | Approved |
| D-022 | 29 Sep 2026 | Demo path with saved results, honestly labeled | Approved |
| D-023 | 29 Sep 2026 | Hosting: Railway | Approved (paid plan confirmed before subscribing) |
| D-024 | 29 Sep 2026 | Local development database with Docker Compose | Approved |
| D-025 | 29 Sep 2026 | Feature status and the rule for removing minimal features | Approved |
| D-026 | 29 Sep 2026 | Definition of Done v1 and the cut order | Approved |
| D-027 | 29 Sep 2026 | Official dates, revised schedule, and actual dates are tracked separately | Approved |
| D-028 | 29 Sep 2026 | Scripts may read API keys from a git-ignored local `.env` | Approved (keys changed by D-030 and D-031) |
| D-029 | 29 Sep 2026 | LLM shortlist across providers and a pre-registered selection rule | Approved (access changed by D-030) |
| D-030 | 29 Sep 2026 | OpenRouter as the single gateway for all LLM and embedding calls | Approved (DeepSeek fallback removed by D-031) |
| D-031 | 29 Sep 2026 | OpenRouter only (no direct DeepSeek key); budget guard follows the OpenRouter credit actually bought | Approved |
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
| D-043 | 1 Oct 2026 | Gold-set sizes from the pilot timing (2 hours of annotator time left) | Pending approval |
| D-044 | 1 Oct 2026 | Model benchmark protocol: where the LLM and embedding models are compared, and a second embedding candidate | Pending approval |

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
  - Two to three synthetic CVs are the default for evaluation and the public demo. Dion checks that they are realistic before labeling starts.
  - Dion's real CV is not needed to start. If it is needed later for private testing, it is sent to an external provider only after a separate, explicit confirmation.
  - Indonesian and English support is tested, including an Indonesian CV with English JDs (402 of the 428 target JDs are in English).
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
- **Status:** Pending approval by Dion.

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
- **Status:** Pending approval by Dion (option A or B).
