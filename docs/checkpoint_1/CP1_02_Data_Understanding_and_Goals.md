# CP1.2: Data Understanding and Setting Goals

**Status:** CP1 report complete; the metric map follows the source of truth; model measurement waits for CP2.  
**Foundation:** PRE-CP0 stays **FROZEN: GO WITH LIMITATION**, user pilot n=1.

## 1. Problem and target users

JobFit's main users are early-career job seekers in Indonesia in AI, ML, Data, and AI-related software. The main problem is not only finding job postings with relevant titles, but deciding which ones are worth prioritizing and why they fit.

PRE-CP0 records a user pilot in which the respondent checked level, years of experience, education, responsibilities, and skills manually. The priorities were realistic ranking, reasons that can be checked, and clear gaps. Because the pilot is only one person, these findings set the early design direction; they are not evidence of what all job seekers need.

Evidence from the literature and observations of other systems are already recorded in PRE-CP0 and the reference reports. Macro evidence gives context; the pilot gives usage context; system testing gives examples of failures. These three must not be mixed into one statistical claim. The JobSentinel observation applies only to cases with stored evidence; it is not a generalization that all other tools fail to give evidence.

## 2. Goals and product boundaries

| Level | Goal | Evidence of success needed |
| --- | --- | --- |
| User | Decide which jobs to prioritize, understand the reasons, and see the gaps to act on | Relevance and usefulness ratings by users or human raters |
| Product | Find realistic jobs, see evidence and gaps, decide priorities, then tailor the CV honestly | A flow that can be checked; no invented skills or experience |
| Engineering | A modular, reproducible, measurable system that protects privacy | Component tests, metrics, provenance, latency/cost, and failure handling |

Fixed principles: **retrieval ≠ qualification**, **qualification ≠ preference**, and **UNKNOWN ≠ match**. Salary and work mode, as preferences, do not replace evidence of qualification. Missing CV evidence must be kept apart from evidence that the candidate truly lacks the skill; a clarification loop helps when the data is not enough.

Non-goals for v1 include predicting the chance of being hired, auto-apply, automated hiring decisions, a universal ATS score, permanent storage of raw CVs, and invented CV claims. The EDA does not expand this scope.

## 3. Understanding the available dataset

**Unit of analysis:** one estimated job cluster, not one API result slot and not one CV-JD pair. Three counting units are used for different purposes, and their numbers must not be mixed:

| Unit | Count | Used for |
| --- | ---: | --- |
| API result slots | 1,314 | Collection and dedup audit |
| Jobs (final clusters) | 910 | Clean data, data quality, language, and dates |
| EDA candidates | 632 | Feature transformation, and analysis of role, experience, skills, and location |

Each job has three kinds of information: (1) identity and source (employer, title, publisher, apply URL, retrieval time), (2) structured metadata from the provider (country, city, posting date, job type, salary), which is often empty, and (3) the JD text as the main source of requirements. The features JobFit needs most, namely role family, experience requirement, and skills, are **not available as columns**. All of them are derived from the title and JD text with versioned rules (CP1.4).

| EDA candidate group | Target | Adjacent | Non-target | Total |
| --- | ---: | ---: | ---: | ---: |
| Indonesia | 175 | 126 | 71 | 372 |
| Foreign | 186 | 3 | 1 | 190 |
| Remote query | 57 | 2 | 1 | 60 |
| Country UNKNOWN | 10 | 0 | 0 | 10 |
| Total | 428 | 131 | 73 | 632 |

`geo_stratum` stores the collection strata. `analysis_geo` uses location evidence and is built to be mutually exclusive. The query country does not fill in an empty job country. Also, a remote query does not mean the job accepts applicants from Indonesia.

Sampling is query-based and adaptive, not random. The mix of publishers, roles, and countries is shaped by the collection design. So the EDA percentages describe this corpus; they are not prevalence estimates for the whole Indonesian market.

## 4. CP1 questions and how they connect to the project

| Question | Data/analysis | Design purpose | Notebook |
| --- | --- | --- | --- |
| How complete and traceable is the data? | Field completeness, sources, dedup, dates, JD length | Decide on UNKNOWN and which inputs are fit for analysis | 1.2, 1.3, 2 |
| Is the title enough to understand role and level? | Role family, title level × experience signal | Prepare an evidence-based role/seniority gate | 3.2, 3.3, 4.1, 4.3 |
| How large is the early-career pool? | Indonesian targets, entry/≤2 years, education | Understand the candidate limits before personal matching | 4.2, 4.9 |
| Do skills differ between roles? | Skill mentions per family | Insights and gaps that fit the target role | 4.4, 4.5 |
| Which GenAI skills often appear together? | Comparison of JDs with and without LLM | Hypothesis for grouping explanations, not mandatory requirements | 4.6 |
| Are regional differences driven by data composition? | Raw comparison and standardization by role × JD length | Avoid generalizing from foreign jobs to Indonesia | 4.7 |
| How complete are location, work mode, and date for filtering? | Location from evidence, work mode, remote signal | Decide which can be filters and which stay UNKNOWN | 2.6, 3.4, 4.8 |

In short, the CP1 data **can answer** which requirements are mentioned in JDs and how often, which data problems the pipeline must handle, which hard cases can be used for evaluation, and how skill patterns differ between roles and regions. This data **cannot answer yet** how well a CV fits a job (there are no CVs or fit labels yet), whether an experience number is required or preferred (no gold labels yet), national market size or time trends (a query-based sample from two days), or salary, whether a job is still open, and remote eligibility from Indonesia.

CP1 answers those descriptive questions. Questions like “is hybrid better?” or “is LLM extraction more accurate?” are not answered by the EDA; they need the gold set and CP2 experiments.

## 5. Why is AI needed only selectively?

Counting, dedup, filtering, hashing, and metric calculation still use Python/SQL. These tasks need consistent results that can be tested.

An LLM is a candidate for understanding requirement sentences, separating required from preferred, and mapping evidence context. Embeddings are a candidate for synonym/semantic search. Both are compared with a baseline, because having unstructured text does not automatically prove that an LLM is more accurate.

Ranking is still explained through factors and evidence. Market RAG uses cited data, and CV tailoring needs evidence and clarification. High similarity does not automatically mean qualified, and it does not allow adding new CV claims.

## 6. Metric contract follows PRE-CP0 and the Canonical

| Component | Metric | Evaluation unit / label needs | CP1 status |
| --- | --- | --- | --- |
| Ranking, primary | Precision@5, NDCG@10 | Profile-query pairs with relevance-labeled candidates; graded relevance 0-3 | Not measured yet |
| Safety gate | Wrong-role and seniority hard-negative false-positive rate | Share of hard negatives wrongly passed; needs a gold definition | Not measured yet |
| Extraction | Precision, recall, F1, schema validity | Extracted requirements/fields versus JD annotations | Not measured yet |
| Evidence | Macro-F1, confusion matrix MATCH/PARTIAL/NO_MATCH | Labeled pairs of requirement and CV evidence | Not measured yet |
| Retrieval | Recall@10/20/50 | Relevant-job set per query/profile in the evaluation pool | Not measured yet |
| RAG | Correctness, citation correctness/coverage, refusal; retrieval recall | Questions, reference answers, evidence, and unanswerable cases | Not measured yet |
| CV safety | Unsupported Claim Rate; Evidence Citation Coverage | Output claims on the frozen safety set | Engineering targets **0** and **100%**, not achieved results |
| User utility | Useful/Not Useful and reasons; exploratory time-to-decision | Pilot/dogfooding | No product evaluation yet |
| System | p50/p95/p99, error/timeout, cost per flow | Representative runs with configuration versions | Not measured end-to-end yet |

No new numeric targets are added for F1, Recall, or NDCG. The field-matching definition, the handling of abstention/UNKNOWN, aggregation across profiles, the binary relevance threshold for P@5, and the test split must be made operational before the experiments. Targets must not be set after seeing test results.

## 7. Data not available yet

The gold sets (extraction ±50 JDs, evidence ±100 pairs, ranking 40-60 jobs, RAG 15-20 questions, and CV safety 20-30 scenarios) are still plans, as set in the Canonical. The corpus of 632 candidates and the review queue do not replace manual gold labels.

Cases already used to fix the rules become development/regression cases. The held-out test must be split off before tuning. This way, code fixes can be tested without claiming accuracy on examples that are already known.

## 8. Results and sources

**Acceptance:** the problem, users, goals, unit of analysis, research questions, and metric map are explained. The product scope stays frozen; model scores and wider user validation are not claimed. This report brings together the Data Understanding content that was previously spread across several places.

- [Research notebook, section 1.4](../../notebooks/01_research.ipynb)
- PRE-CP0, especially §10 to 15
- Canonical, scope, principles, and evaluation assets
- [Data contract](../data-contract.md), [inventory](supporting/CP1_Dataset_Inventory.md), [summary](../../data/processed/CP1_research_summary.json).

**Next:** [CP1.3: Cleaning and Missing Values](CP1_03_Cleaning_and_Missing_Values.md).
