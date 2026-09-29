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
| D-006 | 28 Sep 2026 | Score = evidence coverage of required requirement units, with hold rules | Approved |
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
- **Decision:** Dion is the only human annotator. AI may prepare candidate labels, formats, and explanations, but every gold label is checked and decided by Dion. Labels not reviewed by Dion stay provisional. AI help does not count as an independent annotator, and no inter-annotator agreement is reported. Each label records whether an AI suggestion was shown.
- **Limitation recorded:** single-annotator bias and the risk of anchoring on AI suggestions.
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
- **Decision:** Claude may run project scripts on Dion's Mac that read the API keys (DeepSeek, OpenAI) from a local `.env` file in `project-job-fit/`. Dion creates and fills this file himself.
- **Rules:** `.env` is listed in `.gitignore`. Keys are never printed, logged, written to other files, committed, or sent to the chat. The usage ledger and the budget guard (D-019) apply to every call.
- **Reason and trade-off:** Much faster than Dion running every LLM script by hand, which matters for the deadline. The trade-off is that scripts run with his keys, so the budget guard must be in place before the first call.
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
  - Claude, the AI assistant helping on this project, is made by Anthropic. The same fixed rule is applied to every candidate, and the results are reported as measured.
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
