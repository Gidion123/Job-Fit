# Development labeling semantic audit: finding register

**Date:** 2 October 2026  
**Status:** Proposals only; no workbook labels edited or approved.

The summary and coverage limits are in [the audit report](Development_Labeling_Semantic_Audit_20261002.md). Full current records and dependent B/C records are in [the JSON evidence](../../../evals/results/development_labeling_semantic_audit_20261002.json). Row numbers refer to the saved audited snapshot, not future Excel sorting.

## 1. Clear draft errors

### AUD-002: B_Evidence — F00103 / CV2 / D1-U28

- Excel row: 1310. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Data-quality frameworks",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Report automation is related data work; no data-quality framework is identified.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Pengalaman framework dan monitoring kualitas data.

**Current CV quote**

> - Automated report generation with Python scripts, cutting manual reporting time from 6 hours to 1 hour per week.

**Problem:** Automating reports with Python does not show a data-quality framework, a quality check, or monitoring. The stated 'related data work' rationale is too broad to support PARTIAL for this unit.

**Impact:** Inflates evidence coverage for a required qualification.

**Proposed correction:** Propose NO_MATCH with no quote unless a specific quality-related CV sentence is identified; retain pending.

**C rows to recheck:** CV2/F00103 (row 65, pending)

### AUD-010: C_Relevance — F00074 / CV1 / —

- Excel row: 66. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "relevance_0_3": 1,
  "main_reason": "Python/SQL and ML evaluation overlap, but no LLM/RAG, backend framework or production software history is shown.",
  "constraint_note": "Required production/leadership duration is not supported by relevant professional history.",
  "draft_note": "Optional expanded pair, outside frozen dev_pool. Ordinal judgement, not coverage percentage. Review full A/B/C sources.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> 2+ years building production software, with at least 1 year shipping LLM-based applications to real users

**Problem:** constraint_note refers to 'production/leadership duration', but the JD does not ask for leadership duration. This appears copied from the senior D3 case.

**Impact:** The relevance label 1 can remain defensible, but its constraint explanation includes an invented condition.

**Proposed correction:** Remove leadership from the proposed note and cite exactly >=2 years production software and >=1 year shipping LLM apps.

### AUD-013: A_Extraction — F00029 / — / P07-U17

- Excel row: 187. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Debugging",
  "importance": "required",
  "category": "soft_skill",
  "group_id": null,
  "min_years": null,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Strong debugging and problem-solving skills.

**Problem:** Technical debugging is categorized as soft_skill, which excludes it from technical scoring under D-032.

**Impact:** The technical requirement can disappear from the technical denominator.

**Proposed correction:** Propose an appropriate technical category (knowledge_area), preserving the source and pending status.

**B rows to recheck if A changes:** CV2/P07-U17 (row 632, pending)

**C rows to recheck:** CV2/F00029 (row 6, pending)

### AUD-014: A_Extraction — F00029 / — / P07-U24

- Excel row: 194. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "AI evaluation | observability",
  "importance": "preferred",
  "category": "knowledge_area",
  "group_id": "P07-G10",
  "min_years": null,
  "draft_note": "Alternative group: best supported branch; one denominator unit.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Familiarity with AI evaluation or observability tools.

**Problem:** The unit omits 'tools' from familiarity with AI evaluation or observability tools and instead assesses a knowledge area.

**Impact:** The linked MATCH currently credits evaluation activity without checking the source's tool qualification.

**Proposed correction:** Restore the tool qualifier in the proposed draft; recheck CV2 evidence for a named or described evaluation/observability tool.

**B rows to recheck if A changes:** CV2/P07-U24 (row 639, pending)

**C rows to recheck:** CV2/F00029 (row 6, pending)

### AUD-015: A_Extraction — F00029 / — / P07-U27

- Excel row: 197. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Enterprise AI experience",
  "importance": "preferred",
  "category": "knowledge_area",
  "group_id": null,
  "min_years": null,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Experience in enterprise environments is a plus.

**Problem:** The draft adds AI to the requirement although the source only says 'Experience in enterprise environments is a plus.'

**Impact:** Narrows a generic enterprise-environment qualification and affects the linked evidence judgment.

**Proposed correction:** Remove the invented AI qualifier in the proposed draft; reassess B against the original enterprise-environment requirement.

**B rows to recheck if A changes:** CV2/P07-U27 (row 642, pending)

**C rows to recheck:** CV2/F00029 (row 6, pending)

### AUD-018: B_Evidence — F00036 / CV1 / P09-U10

- Excel row: 40. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Descriptive statistics",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Applied regression model and S1 statistics context.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Pemahaman solid tentang statistik deskriptif dan inferensial serta metodologi penelitian.

**Current CV quote**

> - Membangun model regresi logistik dan random forest dengan scikit-learn; F1-score 0,78 pada data uji.

**Problem:** The selected quotation describes supervised model fitting and F1, not descriptive statistics. The draft cites additional degree context outside the quote.

**Impact:** The exact quotation is real but does not support the full MATCH rationale.

**Proposed correction:** Use a genuinely descriptive-statistics activity if present (review cohort/retention analysis) or revise the evidence label; do not retain this quote as full support.

**C rows to recheck:** CV1/F00036 (row 13, pending)

### AUD-019: B_Evidence — F00055 / CV1 / P11-U15

- Excel row: 62. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Written and spoken Indonesian",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Indonesian reviews used in applied NLP.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Clear written and verbal communication in both Bahasa Indonesia and English — you will write insight reports that a bank's business team needs to act on

**Current CV quote**

> - Mengumpulkan 5.000 ulasan berbahasa Indonesia dan mengklasifikasikan sentimen dengan TF-IDF dan Naive Bayes.

**Problem:** Processing Indonesian review text does not demonstrate both written and spoken communication, as required by the unit.

**Impact:** MATCH overstates the modalities proven by the quotation.

**Proposed correction:** Propose PARTIAL plus the explicit native-language statement pending the language-evidence convention; do not infer spoken communication from NLP input.

**C rows to recheck:** CV1/F00055 (row 32, pending)

### AUD-020: B_Evidence — F00055 / CV2 / P11-U14

- Excel row: 705. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Raw messy-data processing",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Python automation of reports provides related data work; exact wrangling steps not specified.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Ability to work with raw, messy data — you will be building pipelines from conversation logs, not receiving clean feature tables

**Current CV quote**

> - Automated report generation with Python scripts, cutting manual reporting time from 6 hours to 1 hour per week.

**Problem:** Report automation says nothing about raw/dirty data or conversation logs. The draft acknowledges that wrangling steps are unspecified but assigns MATCH.

**Impact:** The required messy-data qualifier is not evidenced.

**Proposed correction:** At most PARTIAL for general data work; no full MATCH unless the messy-data qualifier is shown.

**C rows to recheck:** CV2/F00055 (row 14, pending)

### AUD-022: A_Extraction — F00052 / — / P10-U20

- Excel row: 234. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Collaborative development workflows",
  "importance": "required",
  "category": "soft_skill",
  "group_id": null,
  "min_years": null,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Familiarity with Git and collaborative software development workflows.

**Problem:** Collaborative software development workflows (paired with Git in the source) are classified as a general soft skill rather than a named engineering practice.

**Impact:** Excludes a technical workflow requirement from the technical denominator.

**Proposed correction:** Propose knowledge_area; distinguish workflow practice from the separate generic collaboration trait.

**B rows to recheck if A changes:** CV2/P10-U20 (row 678, pending)

**C rows to recheck:** CV2/F00052 (row 40, pending)

### AUD-023: A_Extraction — F00075 / — / P14-U11

- Excel row: 295. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Automation",
  "importance": "required",
  "category": "knowledge_area",
  "group_id": null,
  "min_years": null,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> •⁠ ⁠Memahami integrasi LLM/API dan automation

**Problem:** Automation is entered twice with no distinct qualifier: U03 from 'AI Agent & Automation' and U11 from LLM/API and automation.

**Impact:** Counts the same required capability twice.

**Proposed correction:** Propose one automation unit with both provenance clauses; obtain approval before any denominator-changing merge and recheck linked B.

**Related A units:** P14-U03 (row 287, pending)

**B rows to recheck if A changes:** CV1/P14-U03 (row 71, pending), CV1/P14-U11 (row 79, pending)

**C rows to recheck:** CV1/F00075 (row 43, pending)

### AUD-025: B_Evidence — F00114 / CV2 / J5-U08

- Excel row: 762. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Embedding-model selection",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Contextual use supports this unit; no claim about truth or depth. Confirm against source CV.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Real RAG production experience: chunking trade-offs, embedding selection, hybrid retrieval, reranking, and how to measure retrieval quality.

**Current CV quote**

> - Built a retrieval-augmented chatbot over 40 PDF reports using LangChain, OpenAI embeddings, and a FAISS vector store.

**Problem:** Using OpenAI embeddings does not show embedding-model selection or comparison, which is the actual unit.

**Impact:** Over-credits a specific production-RAG component.

**Proposed correction:** Propose PARTIAL for related embedding use; do not infer selection trade-offs or evaluation.

**C rows to recheck:** CV2/F00114 (row 64, approved)

### AUD-026: A_Extraction — F00117 / — / P18-U23

- Excel row: 373. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Full work-from-office in South Jakarta",
  "importance": "required",
  "category": "location",
  "group_id": null,
  "min_years": null,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Placement client: JAKARTA, Full WFO

**Problem:** The unit adds South Jakarta, while the source only states JAKARTA.

**Impact:** Introduces an unsupported geographical constraint.

**Proposed correction:** Propose 'Full WFO in Jakarta', with location still needs_clarification for CV2.

**B rows to recheck if A changes:** CV2/P18-U23 (row 794, pending)

**C rows to recheck:** CV2/F00117 (row 58, pending)

### AUD-027: A_Extraction — F00117 / — / P18-U18

- Excel row: 368. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Collaborative workflows",
  "importance": "required",
  "category": "soft_skill",
  "group_id": null,
  "min_years": null,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Familiar with Git and collaborative development workflows.

**Problem:** Git-linked collaborative development workflows are labeled soft_skill, like P10-U20, rather than engineering practice.

**Impact:** A technical workflow is excluded from the denominator.

**Proposed correction:** Propose knowledge_area; keep generic cross-functional collaboration separate.

**B rows to recheck if A changes:** CV2/P18-U18 (row 789, pending)

**C rows to recheck:** CV2/F00117 (row 58, pending)

### AUD-028: A_Extraction — F00188 / — / P21-U08

- Excel row: 417. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Power BI",
  "importance": "preferred",
  "category": "skill_tool",
  "group_id": null,
  "min_years": null,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Experience in data visualization and dashboarding tools, preferably Power BI

**Problem:** Power BI appears twice as the same preferred qualification, from a responsibility-adjacent plus statement and the dashboarding requirement.

**Impact:** Duplicates the preferred technical unit without a distinct qualifier.

**Proposed correction:** Propose one Power BI unit with both source references; preserve general dashboarding separately and request approval before a denominator-changing merge.

**Related A units:** P21-U03 (row 412, pending)

**B rows to recheck if A changes:** CV1/P21-U03 (row 156, pending), CV1/P21-U08 (row 161, pending)

**C rows to recheck:** CV1/F00188 (row 45, pending)

### AUD-029: B_Evidence — F00208 / CV1 / P23-U36

- Excel row: 225. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Higher education | nonprofit | mission-driven domain",
  "label": "NO_MATCH",
  "check_status": "done",
  "draft_note": "No evidence found in the CV; this does not assert the person lacks the skill.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Experience in higher education, nonprofit, or mission-driven technology contexts.

**Current CV quote**

> [No quote: current NO_MATCH]

**Overlooked CV context**

> **Asisten Praktikum Analisis Regresi**, Universitas Negeri Contoh · Februari 2025 - Juni 2025
> - Membimbing 40 mahasiswa dalam praktikum regresi menggunakan R.

**Problem:** NO_MATCH overlooks the dated university teaching-assistant work, which is direct higher-education experience, one explicitly allowed OR branch.

**Impact:** Under-credits a preferred domain alternative.

**Proposed correction:** Propose MATCH using the university/practicum teaching-assistant quotation; do not infer nonprofit status.

**C rows to recheck:** CV1/F00208 (row 33, pending)

### AUD-030: B_Evidence — F00208 / CV2 / P23-U37

- Excel row: 867. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Statistics",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Applied A/B experimentation and interpretation.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Advanced training in statistics, causal inference, or program evaluation methods.

**Current CV quote**

> - Ran A/B tests for ad creatives and explained results to account managers.

**Problem:** The source asks for training, but the quotation describes A/B work and reporting, not statistical training.

**Impact:** MATCH substitutes applied work for a distinct training qualification.

**Proposed correction:** Retain the training qualifier and use explicit education/course content if present; otherwise do not claim MATCH from this work quote.

**C rows to recheck:** CV2/F00208 (row 57, pending)

### AUD-031: A_Extraction — F00208 / — / P23-U27

- Excel row: 472. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Communication",
  "importance": "required",
  "category": "soft_skill",
  "group_id": null,
  "min_years": null,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Strong interpersonal and communication skills, with the ability to translate complex AI/ML concepts into accessible language for non-technical stakeholders and executive audiences.

**Problem:** The technical-to-nontechnical/executive translation qualifier is omitted from a generic communication soft-skill row.

**Impact:** Loses a concrete stakeholder task and excludes it from technical scoring under D-032.

**Proposed correction:** Propose a separately scoped concrete stakeholder-communication unit (other), preserving the generic trait where genuinely distinct.

**B rows to recheck if A changes:** CV1/P23-U27 (row 216, pending), CV2/P23-U27 (row 857, pending)

**C rows to recheck:** CV1/F00208 (row 33, pending), CV2/F00208 (row 57, pending)

### AUD-034: A_Extraction — F00208 / — / P23-U02

- Excel row: 447. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Residence within US territories and periodic travel availability",
  "importance": "required",
  "category": "location",
  "group_id": null,
  "min_years": null,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Hybrid Work & Travel: Employees can live anywhere in the US or its territories, with the willingness and ability to travel for periodic in-person events-including semi-annual Common App retreats, department retreats, and strategic leadership sessions.

**Problem:** The second location row narrows allowed residence to US territories, while its source allows the US OR its territories. U01 already repeats US residence.

**Impact:** Can create a false territory-specific obligation and duplicate residence checking.

**Proposed correction:** Propose one US-or-territories residence condition plus separate periodic-travel willingness if required; location remains excluded from match percentage.

**B rows to recheck if A changes:** CV1/P23-U02 (row 191, pending), CV2/P23-U02 (row 832, pending)

**C rows to recheck:** CV1/F00208 (row 33, pending), CV2/F00208 (row 57, pending)

### AUD-036: B_Evidence — F00310 / CV2 / P27-U08

- Excel row: 896. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Current frontier and open-weight models",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "RAG application with embeddings/LangChain; no production deployment inferred.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Expertise in Natural Language Processing (NLP) and Generative AI with a deep understanding of the latest LLM landscape, including transformer-based architectures such as BERT and T5, and current frontier and open-weight models (e.g., GPT-5.x, Claude 4/5, Gemini 2.x/3.x, Llama 4, DeepSeek, Qwen) that are driving the evolution of NLP and agentic AI applications.

**Current CV quote**

> - Built a retrieval-augmented chatbot over 40 PDF reports using LangChain, OpenAI embeddings, and a FAISS vector store.

**Problem:** The quote names OpenAI embeddings, not experience with the source's current frontier/open-weight LLM landscape or named generative models.

**Impact:** MATCH converts embedding-provider use into frontier-LLM evidence.

**Proposed correction:** Do not claim MATCH for this specific model-scope unit; use PARTIAL only for genuinely related context or NO_MATCH if no qualifying model is evidenced.

**C rows to recheck:** CV2/F00310 (row 42, pending)

### AUD-037: B_Evidence — F00310 / CV2 / P27-U49

- Excel row: 937. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Data ingestion",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Python automation of reports provides related data work; exact wrangling steps not specified.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Hands-on experience with data ingestion, data wrangling, and data pipeline orchestration using tools like Apache Kafka, Apache Spark, Airflow, and distributed computing frameworks like Dask and Ray.

**Current CV quote**

> - Automated report generation with Python scripts, cutting manual reporting time from 6 hours to 1 hour per week.

**Problem:** Automating reports does not explicitly describe data ingestion; the draft acknowledges unspecified processing steps but labels MATCH.

**Impact:** Over-credits a specifically named data-engineering activity.

**Proposed correction:** Propose PARTIAL for related data work, pending evidence of ingestion; keep explicit source-tool qualifiers during A review.

**C rows to recheck:** CV2/F00310 (row 42, pending)

### AUD-038: B_Evidence — F00310 / CV2 / P27-U50

- Excel row: 938. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Data wrangling",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Python automation of reports provides related data work; exact wrangling steps not specified.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Hands-on experience with data ingestion, data wrangling, and data pipeline orchestration using tools like Apache Kafka, Apache Spark, Airflow, and distributed computing frameworks like Dask and Ray.

**Current CV quote**

> - Automated report generation with Python scripts, cutting manual reporting time from 6 hours to 1 hour per week.

**Problem:** The same report-automation quote does not state data wrangling/cleaning transformations.

**Impact:** Full MATCH lacks support for the named activity.

**Proposed correction:** Propose PARTIAL for related work unless an actual wrangling sentence is found.

**C rows to recheck:** CV2/F00310 (row 42, pending)

### AUD-039: A_Extraction — F00310 / — / P27-U46

- Excel row: 575. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "MongoDB | Cassandra | DynamoDB NoSQL",
  "importance": "required",
  "category": "skill_tool",
  "group_id": "P27-G1",
  "min_years": null,
  "draft_note": "Alternative group: best supported branch; one denominator unit.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Strong programming skills in Python, R, and SQL, with advanced proficiency in handling large-scale data using distributed data systems like Apache Spark, cloud-native NoSQL databases such as MongoDB, Cassandra, and DynamoDB, as well as search engines like Elasticsearch and vector databases for semantic search (e.g., Pinecone, Weaviate).

**Problem:** MongoDB, Cassandra AND DynamoDB are collapsed into an OR group, contrary to D-039's explicit AND splitting rule.

**Impact:** Any one technology can incorrectly satisfy the entire conjunction.

**Proposed correction:** Propose separate units retaining the exact list qualifier, with human authorization for denominator changes and dependent B review.

**B rows to recheck if A changes:** CV1/P27-U46 (row 301, pending), CV2/P27-U46 (row 934, pending)

**C rows to recheck:** CV2/F00310 (row 42, pending), CV1/F00310 (row 53, pending)

### AUD-040: A_Extraction — F00310 / — / P27-U61

- Excel row: 590. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Communication",
  "importance": "required",
  "category": "soft_skill",
  "group_id": null,
  "min_years": null,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Strong communication skills, with the ability to explain complex technical concepts to both technical and non-technical stakeholders.

**Problem:** Generic communication soft_skill drops the concrete explanation of technical concepts to technical/nontechnical stakeholders.

**Impact:** A concrete D-032 stakeholder task is lost from the technical denominator.

**Proposed correction:** Preserve the concrete explanation task in an appropriate other unit; recheck B quotes for the technical subject.

**B rows to recheck if A changes:** CV1/P27-U61 (row 316, pending), CV2/P27-U61 (row 949, pending)

**C rows to recheck:** CV2/F00310 (row 42, pending), CV1/F00310 (row 53, pending)

### AUD-041: B_Evidence — F00327 / CV2 / P28-U03

- Excel row: 957. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Ad-platform campaign/auction/targeting/measurement mechanics",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Contextual use supports this unit; no claim about truth or depth. Confirm against source CV.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Deep understanding of paid/performance marketing KPIs, how media platforms work (campaign structure, auction mechanics, targeting, measurement) and their APIs (Meta, Google Ads, TikTok), and MMP tooling (AppsFlyer, Adjust).

**Current CV quote**

> - Ran A/B tests for ad creatives and explained results to account managers.

**Problem:** A/B testing ad creatives does not evidence all campaign structure, auction, targeting and measurement mechanics retained in this compound unit.

**Impact:** MATCH overstates full coverage of the compound.

**Proposed correction:** Propose PARTIAL for demonstrated marketing experiments, or reassess after atomic extraction; do not infer auction/API mechanics.

**C rows to recheck:** CV2/F00327 (row 54, pending)

### AUD-042: B_Evidence — F00330 / CV1 / P29-U03

- Excel row: 324. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Learning new AI technologies",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Completed certificate demonstrates learning activity.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> You’re AI-native and you learn fast. You build with AI coding and agent tools (Cursor, Claude Code, and the like), and you keep up with the space by doing, not just reading.

**Current CV quote**

> - Google Data Analytics Professional Certificate (2025)

**Problem:** The Google Data Analytics certificate supports learning, but does not show learning/building with new AI technologies, the qualifier in this source.

**Impact:** Full MATCH drops the AI-specific qualifier.

**Proposed correction:** Use an actual AI/ML project quote for contextual AI learning if it supports the clause; otherwise only PARTIAL for general learning.

**C rows to recheck:** CV1/F00330 (row 35, pending)

### AUD-044: B_Evidence — F00332 / CV1 / P30-U14

- Excel row: 343. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Large tabular-data trend/anomaly analysis",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "1.2 million transaction rows explicitly processed.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Experience working with large tabular datasets to detect trends and anomalies and communicate findings as actionable recommendations.

**Current CV quote**

> - Membersihkan dan menggabungkan data transaksi 1,2 juta baris dengan Python (pandas) dan SQL (PostgreSQL).

**Problem:** Cleaning/joining 1.2 million transaction rows proves tabular-data processing, but not trend AND anomaly detection; the separate anomaly row is NO_MATCH.

**Impact:** Full MATCH contradicts a qualifier retained in the compound and the linked anomaly judgment.

**Proposed correction:** Propose PARTIAL and review extraction granularity; use cohort-analysis context only for the trend part, without fabricating anomaly investigation.

**C rows to recheck:** CV1/F00332 (row 29, pending)

### AUD-048: A_Extraction — F00412 / — / P36-U24

- Excel row: 747. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Multi-agent | agent-agnostic architecture",
  "importance": "preferred",
  "category": "knowledge_area",
  "group_id": "P36-G4",
  "min_years": null,
  "draft_note": "Alternative group: best supported branch; one denominator unit.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Multi-agent systems or model-agnostic architectures.

**Problem:** 'Model-agnostic architectures' is changed to 'agent-agnostic architecture'. These are different requirements.

**Impact:** Changes what the alternative branch assesses.

**Proposed correction:** Restore model-agnostic wording and recheck the related B row.

**B rows to recheck if A changes:** CV2/P36-U24 (row 1025, pending)

**C rows to recheck:** CV2/F00412 (row 12, pending)

### AUD-049: B_Evidence — F00412 / CV2 / P36-U18

- Excel row: 1019. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Willingness to work with human-agent systems",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Ongoing reskilling demonstrates learning activity.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Willingness to work in a human-agent cooperation model.

**Current CV quote**

> **Data Science and AI Bootcamp**, Contoh Academy (online) · June 2026 - present

**Problem:** A DS/AI bootcamp does not express willingness to work under a human-agent cooperation model.

**Impact:** A generic learning event is used for an unrelated willingness claim.

**Proposed correction:** Propose NO_MATCH/no quote for stated willingness, or clarification if the project defines that workflow; do not infer willingness.

**C rows to recheck:** CV2/F00412 (row 12, pending)

### AUD-050: B_Evidence — F00412 / CV2 / P36-U08

- Excel row: 1009. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Interest in agent orchestration/tool-calling/controlled autonomy",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Ongoing reskilling demonstrates learning activity.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Strong interest in agent orchestration, tool calling and controlled autonomy.

**Current CV quote**

> **Data Science and AI Bootcamp**, Contoh Academy (online) · June 2026 - present

**Problem:** The bootcamp entry does not state interest in agent orchestration, tool calling or controlled autonomy.

**Impact:** MATCH ignores the subject-specific interest qualifier.

**Proposed correction:** Do not claim full MATCH; at most PARTIAL for broader AI learning with an explicit caveat.

**C rows to recheck:** CV2/F00412 (row 12, pending)

### AUD-051: B_Evidence — F00412 / CV2 / P36-U03

- Excel row: 1004. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "LLM | ML | AI service integration",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "OpenAI embeddings through LangChain are shown; direct API calls/request handling not demonstrated.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Practical experience integrating LLMs, machine learning or AI services into applications.

**Current CV quote**

> - Built a retrieval-augmented chatbot over 40 PDF reports using LangChain, OpenAI embeddings, and a FAISS vector store.

**Problem:** PARTIAL adds a direct API/request-handling requirement absent from this unit. OpenAI embeddings integrated through LangChain are an AI service integrated into an application, an explicitly permitted branch.

**Impact:** Under-credits actual integration by importing a narrower interface condition.

**Proposed correction:** Propose MATCH for the AI-service branch; do not assert a generative LLM API or direct low-level request handling.

**C rows to recheck:** CV2/F00412 (row 12, pending)

### AUD-053: B_Evidence — F00052 / CV2 / P10-U32

- Excel row: 690. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "OpenAI | Gemini | Anthropic | similar AI API",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "OpenAI embeddings through LangChain are shown; direct API calls/request handling not demonstrated.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Experience working with AI APIs and services such as OpenAI, Google Gemini, Anthropic, or similar platforms.

**Current CV quote**

> - Built a retrieval-augmented chatbot over 40 PDF reports using LangChain, OpenAI embeddings, and a FAISS vector store.

**Problem:** The JD permits AI APIs AND services; OpenAI embeddings are explicitly an AI service. The draft requires direct API call handling that is not asked for.

**Impact:** Under-credits an expressly allowed service example.

**Proposed correction:** Propose MATCH for the service branch, without claiming GPT/LLM-generation experience.

**C rows to recheck:** CV2/F00052 (row 40, pending)

### AUD-054: B_Evidence — F00438 / CV2 / P37-U11

- Excel row: 1043. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Internal AI tools",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Contextual use supports this unit; no claim about truth or depth. Confirm against source CV.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Hands-on technical fluency in configuring and building internal tools using modern AI platforms, automation builders, and dashboard interfaces.

**Current CV quote**

> - Built a retrieval-augmented chatbot over 40 PDF reports using LangChain, OpenAI embeddings, and a FAISS vector store.

**Problem:** A personal document chatbot is credited as MATCH for internal business AI tools without evidence it is an internal/company tool.

**Impact:** Drops the business/internal-use qualifier.

**Proposed correction:** Propose PARTIAL for related chatbot building; do not infer internal adoption.

**C rows to recheck:** CV2/F00438 (row 24, pending)

### AUD-056: B_Evidence — F00438 / CV2 / P37-U14

- Excel row: 1046. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Combining disparate data into executive views",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Python automation of reports provides related data work; exact wrangling steps not specified.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Strong data intuition—you know how to connect disparate data silos into clean, actionable executive views.

**Current CV quote**

> - Automated report generation with Python scripts, cutting manual reporting time from 6 hours to 1 hour per week.

**Problem:** Python report automation does not state connecting disparate data silos or creating actionable executive views.

**Impact:** MATCH overstates both source integration and audience/output scope.

**Proposed correction:** Propose PARTIAL for related reporting and identify which parts remain unsupported.

**C rows to recheck:** CV2/F00438 (row 24, pending)

### AUD-057: C_Relevance — F00438 / CV2 / —

- Excel row: 24. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "relevance_0_3": 2,
  "main_reason": "Marketing report automation, dashboard work and RAG support several areas; process mapping, SOPs and workflow-builder implementation are gaps.",
  "constraint_note": "No explicit duration minimum.",
  "draft_note": "Guideline v1.2 Part D; evidence coverage and explicit qualifications, not retrieval score. Human review required.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Hands-on technical fluency in configuring and building internal tools using modern AI platforms, automation builders, and dashboard interfaces.

**Problem:** main_reason claims dashboard work, while the related B row only has a skills-list Looker Studio PARTIAL and no dashboard build.

**Impact:** C rationale elevates listed skill to completed work; label 2 needs reassessment after B corrections, not an automatic conversion.

**Proposed correction:** Replace the dashboard-work claim with 'Looker Studio listed'; reassess C qualitatively against corrected core evidence.

### AUD-058: B_Evidence — F00601 / CV2 / P42-U12

- Excel row: 1078. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Precision-recall evaluation",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Question-set evaluation and answer accuracy are contextual evaluation.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Solid understanding of classification models (such as XGBoost or LightGBM) and performance evaluation metrics like AUC and precision-recall.

**Current CV quote**

> - Served it with FastAPI in a Docker container; wrote an evaluation set of 30 questions to check answer accuracy.

**Problem:** Answer accuracy on 30 RAG questions is not precision-recall evaluation.

**Impact:** MATCH conflates distinct metrics.

**Proposed correction:** Propose NO_MATCH for explicit precision/recall evidence, or PARTIAL only if a genuinely related classification-metric quote is selected (macro-F1) and its limitation is stated.

**C rows to recheck:** CV2/F00601 (row 37, pending)

### AUD-060: B_Evidence — F00601 / CV1 / P42-U16

- Excel row: 500. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Translating experimental results into decisions",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Contextual use supports this unit; no claim about truth or depth. Confirm against source CV.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Proven experience in experimentation frameworks (A/B testing), including design, analysis, and bias mitigation, along with the ability to translate insights into actionable decisions.

**Current CV quote**

> - Melakukan analisis cohort retensi pelanggan dan mempresentasikan hasilnya ke manajer divisi.

**Problem:** Cohort/retention presentation is not evidence of translating experimental results into decisions; the experiment rows are NO_MATCH.

**Impact:** MATCH drops the experimental provenance qualifier.

**Proposed correction:** Propose PARTIAL for related insight communication, or NO_MATCH for specifically experimental results; no invented experiment.

**C rows to recheck:** CV1/F00601 (row 44, pending)

### AUD-062: A_Extraction — F00663 / — / P47-U13

- Excel row: 941. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "pandas | NumPy | SQL data-processing tools",
  "importance": "required",
  "category": "skill_tool",
  "group_id": "P47-G4",
  "min_years": null,
  "draft_note": "Alternative group: best supported branch; one denominator unit.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Data Processing: Kemampuan strong dalam data preprocessing, feature engineering, dan handling big data menggunakan tools seperti Pandas, NumPy, dan SQL.

**Problem:** Pandas, NumPy AND SQL are converted into an OR group despite the explicit conjunction and no alternative qualifier.

**Impact:** SQL alone is credited for all three tool requirements.

**Proposed correction:** Propose separate tool units under D-039; obtain approval for the denominator change and reassess both CVs' B rows.

**B rows to recheck if A changes:** CV1/P47-U13 (row 547, pending), CV2/P47-U13 (row 1156, pending)

**C rows to recheck:** CV1/F00663 (row 38, pending), CV2/F00663 (row 59, pending)

### AUD-063: B_Evidence — F00663 / CV2 / P47-U10

- Excel row: 1153. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Preprocessing",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Python automation of reports provides related data work; exact wrangling steps not specified.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Data Processing: Kemampuan strong dalam data preprocessing, feature engineering, dan handling big data menggunakan tools seperti Pandas, NumPy, dan SQL.

**Current CV quote**

> - Automated report generation with Python scripts, cutting manual reporting time from 6 hours to 1 hour per week.

**Problem:** Report automation does not document preprocessing; the draft says exact wrangling steps are unspecified yet labels MATCH.

**Impact:** Over-credits a concrete required preprocessing activity.

**Proposed correction:** Propose PARTIAL for related report automation unless actual preprocessing is evidenced.

**C rows to recheck:** CV2/F00663 (row 59, pending)

### AUD-065: B_Evidence — F00654 / CV1 / P45-U10

- Excel row: 515. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Communicating progress, trade-offs and results across functions",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Contextual use supports this unit; no claim about truth or depth. Confirm against source CV.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> You excel at communicating progress, trade-offs, and the results of your work to team

**Current CV quote**

> - Melakukan analisis cohort retensi pelanggan dan mempresentasikan hasilnya ke manajer divisi.

**Problem:** The cohort-results presentation shows results communication but not progress, trade-offs and cross-functional communication retained in the compound.

**Impact:** Full MATCH exceeds the quoted scope.

**Proposed correction:** Propose PARTIAL for results communication; preserve the complete original cross-functional clause in A provenance.

**C rows to recheck:** CV1/F00654 (row 41, pending)

### AUD-066: B_Evidence — F00666 / CV2 / P48-U14

- Excel row: 1175. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "SQL profiling large operational datasets",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Contextual use supports this unit; no claim about truth or depth. Confirm against source CV.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Strong SQL skills for data analysis. Comfortable querying, profiling, and drawing conclusions from large operational datasets.

**Current CV quote**

> - Wrote SQL queries in BigQuery to build weekly campaign performance reports for 12 brands.

**Problem:** BigQuery weekly reports for 12 brands establish SQL use but not profiling or large operational dataset scale.

**Impact:** MATCH drops explicit profiling/scale qualifiers.

**Proposed correction:** Propose PARTIAL for SQL reporting; do not infer dataset volume from the number of brands.

**C rows to recheck:** CV2/F00666 (row 46, pending)

### AUD-067: A_Extraction — F00933 / — / P54-U05

- Excel row: 1065. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Collaborative Agile environment",
  "importance": "required",
  "category": "soft_skill",
  "group_id": null,
  "min_years": null,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Ability to work in a collaborative Agile environment

**Problem:** Agile working practice is classified as a generic soft_skill despite naming a development method.

**Impact:** Excludes a named technical method under D-032.

**Proposed correction:** Propose knowledge_area for Agile practice, keeping generic collaboration distinct if separately extracted.

**B rows to recheck if A changes:** CV2/P54-U05 (row 1277, pending)

**C rows to recheck:** CV2/F00933 (row 48, pending)

### AUD-068: A_Extraction — F00798 / — / P51-U14

- Excel row: 1015. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "LangGraph",
  "importance": "required",
  "category": "knowledge_area",
  "group_id": null,
  "min_years": null,
  "draft_note": "Practical knowledge in requirements; duplicate umbrella/agent synonyms need review before scoring.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> LangGraph

**Problem:** LangGraph and LangChain are explicitly named framework skills but categorized knowledge_area, unlike equivalent tool units elsewhere.

**Impact:** Inconsistent extraction categories affect category-level evaluation and schema semantics.

**Proposed correction:** Propose skill_tool for the named frameworks; retain pending and original quotes.

**Related A units:** P51-U15 (row 1016, pending)

**B rows to recheck if A changes:** CV2/P51-U14 (row 1230, pending), CV2/P51-U15 (row 1231, pending)

**C rows to recheck:** CV2/F00798 (row 19, pending)

### AUD-070: B_Evidence — F00055 / CV2 / P11-U07

- Excel row: 698. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Prompt evaluation",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Question-set evaluation and answer accuracy are contextual evaluation.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Fluency with LLM APIs (Anthropic, OpenAI, or equivalent): structured prompting, JSON output parsing, batch processing, and prompt evaluation — this is your primary technical tool

**Current CV quote**

> - Served it with FastAPI in a Docker container; wrote an evaluation set of 30 questions to check answer accuracy.

**Problem:** Answer-accuracy checks do not show prompt evaluation or prompt iteration/comparison.

**Impact:** Generic end-to-end evaluation is credited as a more specific required evaluation activity.

**Proposed correction:** Propose PARTIAL for related end-to-end answer evaluation; do not infer retrieval metrics or prompt comparison.

**C rows to recheck:** CV2/F00055 (row 14, pending)

### AUD-071: B_Evidence — F00310 / CV2 / P27-U17

- Excel row: 905. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Retrieval evaluation",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Question-set evaluation and answer accuracy are contextual evaluation.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Practical experience with Retrieval-Augmented Generation (RAG), including chunking strategies, embedding models, hybrid search, and retrieval evaluation.

**Current CV quote**

> - Served it with FastAPI in a Docker container; wrote an evaluation set of 30 questions to check answer accuracy.

**Problem:** Answer-accuracy checks on a RAG question set do not show retrieval-quality evaluation.

**Impact:** Generic end-to-end evaluation is credited as a more specific required evaluation activity.

**Proposed correction:** Propose PARTIAL for related end-to-end answer evaluation; do not infer retrieval metrics or prompt comparison.

**C rows to recheck:** CV2/F00310 (row 42, pending)

### AUD-072: B_Evidence — F00310 / CV2 / P27-U21

- Excel row: 909. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Prompt evaluation",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Question-set evaluation and answer accuracy are contextual evaluation.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Experience fine-tuning and adapting large models efficiently, using techniques such as LoRA/QLoRA, parameter-efficient fine-tuning (PEFT), quantization, and distillation, along with LLMOps practices for prompt evaluation, guardrails, hallucination testing, and observability (e.g., LangSmith, RAGAS, Arize).

**Current CV quote**

> - Served it with FastAPI in a Docker container; wrote an evaluation set of 30 questions to check answer accuracy.

**Problem:** Answer-accuracy checks do not show prompt evaluation or prompt iteration/comparison.

**Impact:** Generic end-to-end evaluation is credited as a more specific required evaluation activity.

**Proposed correction:** Propose PARTIAL for related end-to-end answer evaluation; do not infer retrieval metrics or prompt comparison.

**C rows to recheck:** CV2/F00310 (row 42, pending)

### AUD-076: B_Evidence — F00438 / CV1 / P37-U04

- Excel row: 437. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Motivation to build internal tools/workflows",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Completed certificate demonstrates learning activity.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Want It: You genuinely get excited about building internal tools, mapping workflows, and freeing teams from manual reporting drudgery.

**Current CV quote**

> - Google Data Analytics Professional Certificate (2025)

**Problem:** A completed analytics certificate does not state motivation to build internal tools, map workflows, or free teams from manual reporting.

**Impact:** Generic learning is credited as this specific motivation.

**Proposed correction:** Do not claim MATCH from the certificate; use actual internal-dashboard context only for related PARTIAL evidence, without inferring motivation.

**C rows to recheck:** CV1/F00438 (row 8, pending)

### AUD-077: B_Evidence — F00438 / CV2 / P37-U04

- Excel row: 1036. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Motivation to build internal tools/workflows",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Ongoing reskilling demonstrates learning activity.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Want It: You genuinely get excited about building internal tools, mapping workflows, and freeing teams from manual reporting drudgery.

**Current CV quote**

> **Data Science and AI Bootcamp**, Contoh Academy (online) · June 2026 - present

**Problem:** Bootcamp participation does not state motivation to build internal tools and map business workflows.

**Impact:** An unrelated learning entry is used for a specific motivation MATCH.

**Proposed correction:** Propose PARTIAL only if actual report automation supports related interest; otherwise no evidence of the stated motivation.

**C rows to recheck:** CV2/F00438 (row 24, pending)

### AUD-078: A_Extraction — F00698 / — / P50-U23

- Excel row: 996. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "LlamaIndex",
  "importance": "unknown",
  "category": "skill_tool",
  "group_id": null,
  "min_years": null,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Experience with Llama Index

**Problem:** These unknown-importance units have generic draft notes, omitting the reason for unknown: the unheaded keyword block. The reason is only on nearby certification rows/Questions.

**Impact:** Row-level provenance is incomplete under D-039's note requirement.

**Proposed correction:** Propose an explicit unheaded-block importance note for each affected row, without changing unknown or labels.

**Related A units:** P50-U24 (row 997, pending), P50-U25 (row 998, pending), P50-U26 (row 999, pending), P50-U27 (row 1000, pending), P50-U28 (row 1001, pending)

**B rows to recheck if A changes:** CV2/P50-U23 (row 1211, pending), CV2/P50-U24 (row 1212, pending), CV2/P50-U25 (row 1213, pending), CV2/P50-U26 (row 1214, pending), CV2/P50-U27 (row 1215, pending), CV2/P50-U28 (row 1216, pending)

**C rows to recheck:** CV2/F00698 (row 3, pending)

### AUD-079: A_Extraction — F00003 / — / P01-U03

- Excel row: 125. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Python",
  "importance": "preferred",
  "category": "skill_tool",
  "group_id": null,
  "min_years": null,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Minimum 3 years of experience in software development/programming, preferably using Python or related technologies.

**Problem:** The source permits Python OR related technologies, but the normalized unit retains only Python and has no alternative group.

**Impact:** Narrows the preferred alternative qualification even though the current CV2 Python branch happens to fit.

**Proposed correction:** Preserve 'Python or related technologies' and its OR grouping in the proposed draft; do not add unmentioned products.

**B rows to recheck if A changes:** CV2/P01-U03 (row 570, pending)

**C rows to recheck:** CV2/F00003 (row 49, pending)

### AUD-080: A_Extraction — F00208 / — / P23-U37

- Excel row: 482. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Statistics",
  "importance": "preferred",
  "category": "knowledge_area",
  "group_id": null,
  "min_years": null,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Advanced training in statistics, causal inference, or program evaluation methods.

**Problem:** 'Advanced training in statistics, causal inference, OR program evaluation methods' is split into three ungrouped units, and the training qualifier is lost. This is a training alternative, not explicitly an experience-area list.

**Impact:** Requires all three training areas and allows work activity to substitute for training.

**Proposed correction:** Propose one training alternative group retaining the qualifier, unless the annotator explicitly decides D-040 also covers training. Obtain approval for the denominator change and recheck both CVs.

**Related A units:** P23-U38 (row 483, pending), P23-U39 (row 484, pending)

**B rows to recheck if A changes:** CV1/P23-U37 (row 226, pending), CV1/P23-U38 (row 227, pending), CV1/P23-U39 (row 228, pending), CV2/P23-U37 (row 867, pending), CV2/P23-U38 (row 868, pending), CV2/P23-U39 (row 869, pending)

**C rows to recheck:** CV1/F00208 (row 33, pending), CV2/F00208 (row 57, pending)

### AUD-081: B_Evidence — F00438 / CV1 / P37-U14

- Excel row: 447. Review status: **pending**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
{
  "unit_text": "Combining disparate data into executive views",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Contextual use supports this unit; no claim about truth or depth. Confirm against source CV.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Strong data intuition—you know how to connect disparate data silos into clean, actionable executive views.

**Current CV quote**

> - Membersihkan dan menggabungkan data transaksi 1,2 juta baris dengan Python (pandas) dan SQL (PostgreSQL).

**Problem:** The selected quote supports combining/cleaning data, but not the executive view/actionable-output part of this compound.

**Impact:** A true quotation covers only part of the MATCH. Other CV sentences may support output/audience but are not cited.

**Proposed correction:** Add exact dashboard/presentation quotes if they jointly support the full unit; otherwise propose PARTIAL for the supported integration part.

**C rows to recheck:** CV1/F00438 (row 8, pending)

## 2. Ambiguous cases requiring human decisions

### AUD-001: A_Extraction — F00103 / — / D1-U33

- Excel row: 34. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "PDPA | data privacy regulations",
  "importance": "unknown",
  "category": "knowledge_area",
  "group_id": "D1-G4",
  "min_years": null,
  "draft_note": "Menjadi prioritas signals priority but does not clearly mean mandatory or bonus. Review needed.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Pengetahuan tentang PDPA/regulasi privasi data menjadi prioritas.

**Problem:** The phrase 'menjadi prioritas' has no approved required/preferred interpretation. The current unknown importance is a provisional choice.

**Impact:** A decision changes whether this unit enters the required denominator.

**Proposed correction:** Keep pending/unknown until the annotator resolves the existing B1-Q2 question.

**B rows to recheck if A changes:** CV1/D1-U33 (row 150, pending), CV2/D1-U33 (row 1315, pending)

**C rows to recheck:** CV1/F00103 (row 16, pending), CV2/F00103 (row 65, pending)

### AUD-003: B_Evidence — F00103 / CV1 / D1-U01

- Excel row: 118. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Final-year student | recent graduate in Engineering, Computer Science/Technology, or a related discipline",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Degree level proved; whether Statistics is related to the specified technical fields needs reviewer interpretation. Statistics as a related discipline requires human interpretation; acceptance of A is not an evidence approval.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Mahasiswa tingkat akhir atau lulusan baru dari universitas terkemuka, jurusan Teknik, Ilmu Komputer/Teknologi, atau jurusan relevan lainnya.

**Current CV quote**

> **S1 Statistika**, Universitas Negeri Contoh, Jakarta · Agustus 2022 - Agustus 2026

**Problem:** Statistics degree plausibly fits 'related discipline', but the equivalence has not been decided. The approved extraction row does not approve this evidence judgment.

**Impact:** Technical education support and C reasoning depend on the related-field interpretation.

**Proposed correction:** Resolve degree equivalence for this exact JD; recent-graduate status and GPA are independently supported.

**C rows to recheck:** CV1/F00103 (row 16, pending)

### AUD-004: B_Evidence — F00103 / CV1 / D1-U18

- Excel row: 135. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Data engineering experience",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Cleaning/joining shown; end-to-end ETL pipeline design not explicit.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Pengalaman data engineering.

**Current CV quote**

> - Membersihkan dan menggabungkan data transaksi 1,2 juta baris dengan Python (pandas) dan SQL (PostgreSQL).

**Problem:** PARTIAL is justified by a missing end-to-end ETL design, but the unit only asks for data engineering experience. It does not explicitly require end-to-end ETL design (a separate unit does).

**Impact:** Can under-credit contextual cleaning/joining and duplicate the ETL requirement.

**Proposed correction:** Assess whether these demonstrated activities satisfy the general data-engineering requirement; avoid importing D1-U21 into D1-U18.

**C rows to recheck:** CV1/F00103 (row 16, pending)

### AUD-005: A_Extraction — F00074 / — / D2-U06

- Excel row: 43. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Component-built RAG experience",
  "importance": "required",
  "category": "knowledge_area",
  "group_id": null,
  "min_years": null,
  "draft_note": "RAG component skills are independently assessable. Retain explicit vendor/search alternatives within one unit.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Demonstrated RAG experience built from components: chunking strategy, embedding models, a vector store (pgvector, Qdrant, Weaviate, or similar), BM25 or hybrid search, and reranking

**Problem:** The RAG umbrella is counted in addition to five component requirements from the same clause. It is unclear whether this is independently assessable or repeated weighting.

**Impact:** A merge/rewrite changes denominator and linked B judgments.

**Proposed correction:** Resolve existing B1-Q3/QX17 before approval; keep components and make the umbrella independent only if it adds a distinct source-supported requirement.

**B rows to recheck if A changes:** CV2/D2-U06 (row 734, pending), CV1/D2-U06 (row 1324, pending)

**C rows to recheck:** CV2/F00074 (row 15, pending), CV1/F00074 (row 66, pending)

### AUD-006: B_Evidence — F00074 / CV2 / D2-U06

- Excel row: 734. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Component-built RAG experience",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Contextual use supports this unit; no claim about truth or depth. Confirm against source CV.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Demonstrated RAG experience built from components: chunking strategy, embedding models, a vector store (pgvector, Qdrant, Weaviate, or similar), BM25 or hybrid search, and reranking

**Current CV quote**

> - Built a retrieval-augmented chatbot over 40 PDF reports using LangChain, OpenAI embeddings, and a FAISS vector store.

**Problem:** MATCH treats a LangChain RAG prototype as fully satisfying 'component-built RAG' while chunking, BM25/hybrid, and reranking are NO_MATCH in the same clause.

**Impact:** Can over-credit the umbrella or compound meaning until A granularity is decided.

**Proposed correction:** Recheck this B row after the umbrella/component decision; consider PARTIAL if the umbrella retains all listed components.

**C rows to recheck:** CV2/F00074 (row 15, pending)

### AUD-007: B_Evidence — F00074 / CV2 / D2-U09

- Excel row: 737. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Vector store (pgvector | Qdrant | Weaviate | similar)",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "FAISS vector store supports retrieval concepts; persistence, DB operations and named DB products are not demonstrated.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Demonstrated RAG experience built from components: chunking strategy, embedding models, a vector store (pgvector, Qdrant, Weaviate, or similar), BM25 or hybrid search, and reranking

**Current CV quote**

> - Built a retrieval-augmented chatbot over 40 PDF reports using LangChain, OpenAI embeddings, and a FAISS vector store.

**Problem:** The quote explicitly names a FAISS vector store. The PARTIAL rationale adds persistence/database operations that the unit does not ask for and uses them to reject 'or similar'.

**Impact:** Potential under-credit of an explicit vector-store example.

**Proposed correction:** Apply the JD's 'or similar' branch and record the FAISS equivalence judgment; MATCH is a plausible correction without imposing unasked database features.

**C rows to recheck:** CV2/F00074 (row 15, pending)

### AUD-008: A_Extraction — F00074 / — / D2-U02

- Excel row: 39. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "At least two years building production software, including at least one year shipping LLM applications to real users",
  "importance": "required",
  "category": "experience_duration",
  "group_id": null,
  "min_years": 2,
  "draft_note": "Keep nested duration and production qualifiers together. Both conditions must be supported; min_years describes the outer minimum only.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> 2+ years building production software, with at least 1 year shipping LLM-based applications to real users

**Problem:** One row/min_years=2 contains two independent employment-duration conditions: production software >=2 and shipped LLM apps >=1. Both are preserved in text, but one numeric field cannot represent both constraints.

**Impact:** A future evaluator using only min_years would omit the nested one-year condition.

**Proposed correction:** Annotator chooses split versus explicitly structured compound handling; preserve both thresholds in any correction and recheck B/C.

**B rows to recheck if A changes:** CV2/D2-U02 (row 730, pending), CV1/D2-U02 (row 1320, pending)

**C rows to recheck:** CV2/F00074 (row 15, pending), CV1/F00074 (row 66, pending)

### AUD-009: A_Extraction — F00012 / — / D3-U03

- Excel row: 66. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "At least five years in applied ML/DS including at least two years in leadership",
  "importance": "required",
  "category": "experience_duration",
  "group_id": null,
  "min_years": 5,
  "draft_note": "Preserve nested leadership condition; do not take the smallest number or count two independent duration requirements.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Minimal 5 tahun di bidang ML/DS terapan dengan setidaknya 2 tahun pengalaman pada peran kepemimpinan.

**Problem:** One row/min_years=5 also contains >=2 leadership years. Both thresholds are in text but cannot be represented by the single numeric field.

**Impact:** Automated constraint handling may ignore leadership or double-count after an unreviewed split.

**Proposed correction:** Resolve B1-Q4 consistently with D2-U02 before any schema/export interpretation; do not change duration rules during audit.

**B rows to recheck if A changes:** CV1/D3-U03 (row 1347, pending), CV2/D3-U03 (row 1369, pending)

**C rows to recheck:** CV1/F00012 (row 67, pending), CV2/F00012 (row 68, pending)

### AUD-011: B_Evidence — F00003 / CV2 / P01-U04

- Excel row: 571. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "At least 1 year in Generative AI projects",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "August 2026 project is under one year at 30 September 2026; no prior GenAI project period shown.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Minimum 1 year of experience working on Generative AI projects.

**Current CV quote**

> **Document Q&A Assistant (RAG)** · August 2026

**Problem:** The single project date August 2026 is treated as proving that total GenAI project duration is under one year. A project date need not be its start date, and the JD asks about projects rather than explicitly employment.

**Impact:** Current done status and the C duration rationale can overstate an exact shortfall.

**Proposed correction:** Decide the project-versus-employment interpretation of this clause. State that one year is not proven; use needs_clarification if the eligible project period cannot be bounded, without fabricating a start date.

**C rows to recheck:** CV2/F00003 (row 49, pending)

### AUD-012: A_Extraction — F00018 / — / P04-U11

- Excel row: 148. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "NLP use cases",
  "importance": "required",
  "category": "knowledge_area",
  "group_id": null,
  "min_years": null,
  "draft_note": "D-040 experience-area exception: each listed application area is reviewed separately.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Practical experience with one or more use cases from the following: NLP, LLMs, and Recommendation engines.

**Problem:** Three required area rows are made from a clause explicitly saying 'one or more use cases'. D-040 splits experience areas, but does not explicitly resolve that cardinality restriction.

**Impact:** Could turn evidence in one acceptable area into three required denominator units.

**Proposed correction:** Ask whether explicit 'one or more' takes precedence here; preserve the qualifier and do not merge or change denominator without approval.

**Related A units:** P04-U12 (row 149, pending), P04-U13 (row 150, pending)

**B rows to recheck if A changes:** CV2/P04-U11 (row 593, pending), CV2/P04-U12 (row 594, pending), CV2/P04-U13 (row 595, pending)

**C rows to recheck:** CV2/F00018 (row 4, pending)

### AUD-016: A_Extraction — F00029 / — / P07-U02

- Excel row: 172. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Around 3-6 years relevant engineering experience",
  "importance": "required",
  "category": "experience_duration",
  "group_id": null,
  "min_years": 3,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Around 3–6 years of relevant engineering experience.

**Problem:** 'Around 3–6 years' is represented as a hard minimum of 3 years, without recording how 'around' affects the threshold.

**Impact:** B/C can assert an exact conflict where the source expresses an approximate range.

**Proposed correction:** Resolve whether the approximate range creates a hard minimum or a clarification requirement before gold/constraint handling.

**B rows to recheck if A changes:** CV2/P07-U02 (row 617, pending)

**C rows to recheck:** CV2/F00029 (row 6, pending)

### AUD-017: B_Evidence — F00022 / CV1 / J1-U17

- Excel row: 26. Review status: **approved**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Clear and concise communication",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "A terbaru: importance = required; category = soft_skill. Soft skill tetap dinilai buktinya, tetapi tidak masuk persentase match. Presentation demonstrates communication, but clear/concise quality cannot be verified from CV.",
  "review_action": "accepted",
  "review_note": null,
  "guideline_version": "v0.1"
}
```

**JD source**

> Ability to communicate in clear and concise terms.

**Current CV quote**

> Melakukan analisis cohort retensi pelanggan dan mempresentasikan hasilnya ke manajer divisi.

**Problem:** The approved PARTIAL rationale treats 'clearly and concisely' as unverified quality/depth even though D-035/D-042 avoid measuring subjective depth; related contextual communication rows are MATCH.

**Impact:** The approved pilot precedent and new draft communication judgments may apply different evidence standards.

**Proposed correction:** Discuss the approved precedent and scope of subjective-quality wording; preserve the human decision until explicitly authorized.

**C rows to recheck:** CV1/F00022 (row 62, approved)

### AUD-021: B_Evidence — F00055 / CV2 / P11-U19

- Excel row: 710. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Fintech | financial-services | conversion-driven environment",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Contextual use supports this unit; no claim about truth or depth. Confirm against source CV.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Experience in a fintech, financial services, or any high-stakes conversion environment (e-commerce, insurance, lending) where understanding why customers do or do not complete a transaction was the central analytical problem

**Current CV quote**

> - Ran A/B tests for ad creatives and explained results to account managers.

**Problem:** Ordinary marketing A/B tests are treated as proof of a high-stakes conversion environment with conversion behavior as the central analytical problem; neither setting nor centrality is explicit in the quotation.

**Impact:** Can over-credit a domain-qualified preferred requirement.

**Proposed correction:** Consider PARTIAL for conversion-related marketing work; do not assume e-commerce/financial/high-stakes context.

**C rows to recheck:** CV2/F00055 (row 14, pending)

### AUD-032: A_Extraction — F00208 / — / P23-U04

- Excel row: 449. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "8-10 years ML/AI/DS including at least 3 years applied AI/production ML",
  "importance": "required",
  "category": "experience_duration",
  "group_id": null,
  "min_years": 8,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> 8-10 years of progressive experience in machine learning, AI engineering, or data science, with at least 3 years focused on applied AI and production ML systems.

**Problem:** The compound requires 8–10 ML/AI/DS years and at least 3 applied-AI/production-ML years, but only min_years=8 is encoded.

**Impact:** A numeric-only consumer loses the nested minimum.

**Proposed correction:** Resolve alongside D2-U02 and D3-U03; preserve both conditions before any split or export.

**B rows to recheck if A changes:** CV1/P23-U04 (row 193, pending), CV2/P23-U04 (row 834, pending)

**C rows to recheck:** CV1/F00208 (row 33, pending), CV2/F00208 (row 57, pending)

### AUD-033: A_Extraction — F00212 / — / P24-U08

- Excel row: 493. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Cloud/deployment platforms",
  "importance": "required",
  "category": "knowledge_area",
  "group_id": null,
  "min_years": null,
  "draft_note": "Examples mix containers and clouds; equivalent-platform assessment needs review, not a claim that Docker is a cloud.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Experience with distributed systems and cloud computing platforms such as Kubernetes, Docker, GCP, and AWS.

**Problem:** Generic 'Cloud/deployment platforms' drops Kubernetes, Docker, GCP, AWS and does not represent whether the list is AND, examples, or alternatives.

**Impact:** The unit no longer allows checking the source's concrete platform scope or best alternative.

**Proposed correction:** Apply D-039 list interpretation explicitly, preserving the names and noting ambiguity where necessary; no silent group/denominator change.

**B rows to recheck if A changes:** CV1/P24-U08 (row 237, pending)

**C rows to recheck:** CV1/F00212 (row 36, pending)

### AUD-035: B_Evidence — F00303 / CV2 / P25-U12

- Excel row: 882. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Independent end-to-end AI/LLM delivery",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "End-to-end personal application deployment is documented, not production operations.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Ability to independently deliver end-to-end AI/LLM projects.

**Current CV quote**

> - Served it with FastAPI in a Docker container; wrote an evaluation set of 30 questions to check answer accuracy.

**Problem:** MATCH infers independent end-to-end delivery from a prototype serving sentence, while other independence-qualified rows use PARTIAL for the same evidence because supervision/ownership is not stated.

**Impact:** Inconsistent treatment of the independence qualifier.

**Proposed correction:** Resolve evidence of independence consistently; distinguish prototype delivery from confirmed sole ownership, without adding production requirements.

**C rows to recheck:** CV2/F00303 (row 47, pending)

### AUD-043: B_Evidence — F00332 / CV1 / P30-U09

- Excel row: 338. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Independent learning",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Completed certificate demonstrates learning activity.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Willingness to learn new skills independently and strong sense of project ownership.

**Current CV quote**

> - Google Data Analytics Professional Certificate (2025)

**Problem:** Course completion is treated as MATCH for independent learning, unlike approved J1-U18 where no explicit independent-learning evidence was found.

**Impact:** A recurring independence inference differs from the approved pilot case.

**Proposed correction:** Discuss whether self-directed learning is evidenced by this certificate, rather than silently setting a general new rule.

**C rows to recheck:** CV1/F00332 (row 29, pending)

### AUD-047: A_Extraction — F00354 / — / P32-U22

- Excel row: 680. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Validation",
  "importance": "required",
  "category": "knowledge_area",
  "group_id": null,
  "min_years": null,
  "draft_note": "Candidate qualification, normalized independently; evidence of use is assessed without inferring depth.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Experience with time-series modelling, validation and experiment-tracking frameworks.

**Problem:** 'Validation' loses the time-series/framework context of its clause; a generic held-out F1 is used as full MATCH although no time-series validation is shown.

**Impact:** May over-credit a time-series/framework-specific qualification after an overly broad extraction.

**Proposed correction:** Resolve whether the clause means time-series validation and named frameworks or generic validation; then reassess B.

**B rows to recheck if A changes:** CV1/P32-U22 (row 390, pending)

**C rows to recheck:** CV1/F00354 (row 61, pending)

### AUD-052: B_Evidence — F00303 / CV2 / P25-U11

- Excel row: 881. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "API | database | enterprise-system integration",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "LLM library integration shown; no independent third-party REST consumption example.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Experience integrating applications with APIs, databases or enterprise systems.

**Current CV quote**

> - Built a retrieval-augmented chatbot over 40 PDF reports using LangChain, OpenAI embeddings, and a FAISS vector store.

**Problem:** PARTIAL rejects wrapper-based integration because independent third-party REST consumption is not shown, although the JD broadly allows API/database/enterprise integration and does not require direct REST calls.

**Impact:** Possible under-credit from an extra condition absent from the source.

**Proposed correction:** Review generic API integration separately from explicit REST/SDK/request-handling units; accept only the actually demonstrated embedding service if sufficient.

**C rows to recheck:** CV2/F00303 (row 47, pending)

### AUD-055: B_Evidence — F00438 / CV2 / P37-U12

- Excel row: 1044. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Automation builders",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Contextual use supports this unit; no claim about truth or depth. Confirm against source CV.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Hands-on technical fluency in configuring and building internal tools using modern AI platforms, automation builders, and dashboard interfaces.

**Current CV quote**

> - Automated report generation with Python scripts, cutting manual reporting time from 6 hours to 1 hour per week.

**Problem:** Automation builders may mean workflow-builder platforms, while only custom Python report automation is shown.

**Impact:** A tool-class qualification is credited from a general automation result.

**Proposed correction:** Decide whether custom Python scripting qualifies in this JD; avoid imposing n8n when no product is named.

**C rows to recheck:** CV2/F00438 (row 24, pending)

### AUD-059: B_Evidence — F00601 / CV1 / P42-U12

- Excel row: 496. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Precision-recall evaluation",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "F1 on test data is contextual model evaluation.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Solid understanding of classification models (such as XGBoost or LightGBM) and performance evaluation metrics like AUC and precision-recall.

**Current CV quote**

> - Membangun model regresi logistik dan random forest dengan scikit-learn; F1-score 0,78 pada data uji.

**Problem:** F1 mathematically combines precision/recall, but reporting F1 alone does not explicitly document evaluating precision-recall separately or as a curve.

**Impact:** MATCH may rely on an unapproved implication from a related metric.

**Proposed correction:** Decide whether reported F1 satisfies this knowledge unit or only PARTIAL, without inferring AUC/curves.

**C rows to recheck:** CV1/F00601 (row 44, pending)

### AUD-061: B_Evidence — F00650 / CV2 / P44-U15

- Excel row: 1137. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Fine-tuning | evaluation of open-source LLMs",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Contextual use supports this unit; no claim about truth or depth. Confirm against source CV.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Experience fine-tuning or evaluating open-source LLMs.

**Current CV quote**

> - Fine-tuned a small pretrained transformer (DistilBERT) with Hugging Face for 3-class sentiment; macro-F1 0.81.

**Problem:** Fine-tuning DistilBERT is credited as fine-tuning an open-source LLM, but the large/generative-model scope is not established by the small encoder model.

**Impact:** Could conflate transformer/NLP fine-tuning with LLM fine-tuning.

**Proposed correction:** Resolve the LLM scope/equivalence; retain PARTIAL for related transformer fine-tuning if the source requires a larger/generative model.

**C rows to recheck:** CV2/F00650 (row 10, pending)

### AUD-064: B_Evidence — F00655 / CV1 / P46-U03

- Excel row: 518. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Data modelling",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Predictive model is a data-modelling example; schema architecture not inferred.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Understanding of data structures, data modeling and software architecture

**Current CV quote**

> - Membangun model regresi logistik dan random forest dengan scikit-learn; F1-score 0,78 pada data uji.

**Problem:** Predictive ML modelling is treated as full evidence of 'data modeling' in a software-foundations clause (data structures/software architecture); schema/data representation modelling may be intended.

**Impact:** Possible meaning substitution rather than an equivalent skill.

**Proposed correction:** Resolve this JD's intended modelling scope before approval; do not infer relational/schema design from a classifier.

**C rows to recheck:** CV1/F00655 (row 30, pending)

### AUD-069: B_Evidence — F00798 / CV2 / P51-U33

- Excel row: 1249. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Open-weight/open-source LLM integration",
  "label": "MATCH",
  "check_status": "done",
  "draft_note": "Contextual use supports this unit; no claim about truth or depth. Confirm against source CV.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Open-weight models / open-source LLMs

**Current CV quote**

> - Fine-tuned a small pretrained transformer (DistilBERT) with Hugging Face for 3-class sentiment; macro-F1 0.81.

**Problem:** DistilBERT fine-tuning is treated as full open-weight/open-source LLM integration, with neither the source's LLM scope nor application integration demonstrated by the quote.

**Impact:** Could over-credit encoder fine-tuning as generative-model integration.

**Proposed correction:** Resolve the LLM-scope question consistently with P44-U15; consider PARTIAL for related transformer work.

**C rows to recheck:** CV2/F00798 (row 19, pending)

### AUD-073: B_Evidence — F00055 / CV2 / P11-U02

- Excel row: 693. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "3-6 years DS/applied AI with text/conversation/LLM work",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Personal transformer project supports relevant skill only. Marketing employment does not establish AI/ML or specialized text/LLM professional years.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> 3–6 years of hands-on data science or applied AI experience, with demonstrable work in text analytics, conversational data, or LLM-based systems

**Current CV quote**

> - Fine-tuned a small pretrained transformer (DistilBERT) with Hugging Face for 3-class sentiment; macro-F1 0.81.

**Problem:** The DS-equivalent employment duration remains undecided, yet check_status is done. The complete employment history exceeds three years, so an overall upper bound alone cannot prove this particular shortfall.

**Impact:** C=1 may be based on an unresolved specialized-duration interpretation rather than an established conflict.

**Proposed correction:** Resolve whether/when the analyst duties count as DS; if the eligible period is unbounded, propose needs_clarification and reassess C without assigning all marketing years.

**C rows to recheck:** CV2/F00055 (row 14, pending)

### AUD-074: B_Evidence — F00012 / CV2 / D3-U03

- Excel row: 1369. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "At least five years in applied ML/DS including at least two years in leadership",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Personal transformer project supports relevant skill only. Marketing employment does not establish AI/ML or specialized text/LLM professional years.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Minimal 5 tahun di bidang ML/DS terapan dengan setidaknya 2 tahun pengalaman pada peran kepemimpinan.

**Current CV quote**

> - Fine-tuned a small pretrained transformer (DistilBERT) with Hugging Face for 3-class sentiment; macro-F1 0.81.

**Problem:** The complete work history is 65 calendar months, above the outer five-year minimum; same-field ML/DS duration and two-year leadership are separate questions. done should not rest solely on a generic no-AI-tenure note.

**Impact:** Outer-duration and leadership failures/uncertainties can be conflated.

**Proposed correction:** Record the actual eligible work and leadership upper bounds separately; use clarification for unbounded relevant duties, while retaining C=1 if independently supported by missing leadership/core senior evidence.

**C rows to recheck:** CV2/F00012 (row 68, pending)

### AUD-075: A_Extraction — F00012 / — / D3-U19

- Excel row: 82. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Model quality",
  "importance": "unknown",
  "category": "knowledge_area",
  "group_id": null,
  "min_years": null,
  "draft_note": "Focus areas have no clear evidence/depth criterion. Keep for review, do not force required.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Fokus pada kualitas model, tata kelola, skalabilitas, dan keputusan infrastruktur yang hemat biaya.

**Problem:** Focus areas are provisionally unknown, but their requirement versus descriptive emphasis status remains unresolved in B1-Q5.

**Impact:** Changes which independently assessable units enter the required denominator.

**Proposed correction:** Decide the four focus areas together from the actual clause, not the Qualifications heading alone.

**Related A units:** D3-U20 (row 83, pending), D3-U21 (row 84, pending), D3-U22 (row 85, pending)

**B rows to recheck if A changes:** CV1/D3-U19 (row 1363, pending), CV1/D3-U20 (row 1364, pending), CV1/D3-U21 (row 1365, pending), CV1/D3-U22 (row 1366, pending), CV2/D3-U19 (row 1385, pending), CV2/D3-U20 (row 1386, pending), CV2/D3-U21 (row 1387, pending), CV2/D3-U22 (row 1388, pending)

**C rows to recheck:** CV1/F00012 (row 67, pending), CV2/F00012 (row 68, pending)

### AUD-082: B_Evidence — F00055 / CV1 / P11-U16

- Excel row: 63. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Written and spoken English",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Proficiency/test stated; no contextual English work example. Language evidence convention needs reviewer clarification.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Clear written and verbal communication in both Bahasa Indonesia and English — you will write insight reports that a bank's business team needs to act on

**Current CV quote**

> Indonesia (native), Inggris (menengah, TOEFL ITP 540)

**Problem:** The row uses the provisional PARTIAL convention for self-reported language/native proficiency or a TOEFL statement; QX13 has not been decided. The JD's required modality/level must remain in scope.

**Impact:** A consistent language-evidence convention can change individual B judgments; current provisional labels are not a settled rule.

**Proposed correction:** Resolve QX13 once, then apply it separately to each listed unit and its actual native/professional/intermediate/test evidence. Do not equate intermediate TOEFL with professional fluency automatically.

**C rows to recheck:** CV1/F00055 (row 32, pending)

### AUD-083: B_Evidence — F00090 / CV1 / P15-U22

- Excel row: 104. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Active and passive English",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Proficiency/test stated; no contextual English work example. Language evidence convention needs reviewer clarification.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Bahasa Inggris pasif-aktif

**Current CV quote**

> Indonesia (native), Inggris (menengah, TOEFL ITP 540)

**Problem:** The row uses the provisional PARTIAL convention for self-reported language/native proficiency or a TOEFL statement; QX13 has not been decided. The JD's required modality/level must remain in scope.

**Impact:** A consistent language-evidence convention can change individual B judgments; current provisional labels are not a settled rule.

**Proposed correction:** Resolve QX13 once, then apply it separately to each listed unit and its actual native/professional/intermediate/test evidence. Do not equate intermediate TOEFL with professional fluency automatically.

**C rows to recheck:** CV1/F00090 (row 34, pending)

### AUD-084: B_Evidence — F00188 / CV1 / P21-U02

- Excel row: 155. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Fluent spoken and written English",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Proficiency/test stated; no contextual English work example. Language evidence convention needs reviewer clarification.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> The Junior Data Scientist should be fluent in written and spoken English and experienced with the technologies described in the detail below.

**Current CV quote**

> Indonesia (native), Inggris (menengah, TOEFL ITP 540)

**Problem:** The row uses the provisional PARTIAL convention for self-reported language/native proficiency or a TOEFL statement; QX13 has not been decided. The JD's required modality/level must remain in scope.

**Impact:** A consistent language-evidence convention can change individual B judgments; current provisional labels are not a settled rule.

**Proposed correction:** Resolve QX13 once, then apply it separately to each listed unit and its actual native/professional/intermediate/test evidence. Do not equate intermediate TOEFL with professional fluency automatically.

**C rows to recheck:** CV1/F00188 (row 45, pending)

### AUD-085: B_Evidence — F00369 / CV1 / P35-U19

- Excel row: 429. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "English fluency",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Proficiency/test stated; no contextual English work example. Language evidence convention needs reviewer clarification.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Fluency in English.

**Current CV quote**

> Indonesia (native), Inggris (menengah, TOEFL ITP 540)

**Problem:** The row uses the provisional PARTIAL convention for self-reported language/native proficiency or a TOEFL statement; QX13 has not been decided. The JD's required modality/level must remain in scope.

**Impact:** A consistent language-evidence convention can change individual B judgments; current provisional labels are not a settled rule.

**Proposed correction:** Resolve QX13 once, then apply it separately to each listed unit and its actual native/professional/intermediate/test evidence. Do not equate intermediate TOEFL with professional fluency automatically.

**C rows to recheck:** CV1/F00369 (row 52, pending)

### AUD-086: B_Evidence — F00010 / CV2 / P02-U02

- Excel row: 575. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "English communication",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Self-reported professional proficiency; no contextual English work example. Language convention needs review.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Excellent English communication skills.

**Current CV quote**

> Indonesian (native), English (professional working proficiency)

**Problem:** The row uses the provisional PARTIAL convention for self-reported language/native proficiency or a TOEFL statement; QX13 has not been decided. The JD's required modality/level must remain in scope.

**Impact:** A consistent language-evidence convention can change individual B judgments; current provisional labels are not a settled rule.

**Proposed correction:** Resolve QX13 once, then apply it separately to each listed unit and its actual native/professional/intermediate/test evidence. Do not equate intermediate TOEFL with professional fluency automatically.

**C rows to recheck:** CV2/F00010 (row 31, pending)

### AUD-087: B_Evidence — F00018 / CV2 / P04-U17

- Excel row: 599. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "English at strong upper-intermediate level",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Self-reported professional proficiency; no contextual English work example. Language convention needs review.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> English level - strong upper- intermediate.

**Current CV quote**

> Indonesian (native), English (professional working proficiency)

**Problem:** The row uses the provisional PARTIAL convention for self-reported language/native proficiency or a TOEFL statement; QX13 has not been decided. The JD's required modality/level must remain in scope.

**Impact:** A consistent language-evidence convention can change individual B judgments; current provisional labels are not a settled rule.

**Proposed correction:** Resolve QX13 once, then apply it separately to each listed unit and its actual native/professional/intermediate/test evidence. Do not equate intermediate TOEFL with professional fluency automatically.

**C rows to recheck:** CV2/F00018 (row 4, pending)

### AUD-088: B_Evidence — F00055 / CV2 / P11-U15

- Excel row: 706. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Written and spoken Indonesian",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Native language self-report, no explicit applied-language activity; convention needs review.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Clear written and verbal communication in both Bahasa Indonesia and English — you will write insight reports that a bank's business team needs to act on

**Current CV quote**

> Indonesian (native), English (professional working proficiency)

**Problem:** The row uses the provisional PARTIAL convention for self-reported language/native proficiency or a TOEFL statement; QX13 has not been decided. The JD's required modality/level must remain in scope.

**Impact:** A consistent language-evidence convention can change individual B judgments; current provisional labels are not a settled rule.

**Proposed correction:** Resolve QX13 once, then apply it separately to each listed unit and its actual native/professional/intermediate/test evidence. Do not equate intermediate TOEFL with professional fluency automatically.

**C rows to recheck:** CV2/F00055 (row 14, pending)

### AUD-089: B_Evidence — F00055 / CV2 / P11-U16

- Excel row: 707. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Written and spoken English",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Self-reported professional proficiency; no contextual English work example. Language convention needs review.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Clear written and verbal communication in both Bahasa Indonesia and English — you will write insight reports that a bank's business team needs to act on

**Current CV quote**

> Indonesian (native), English (professional working proficiency)

**Problem:** The row uses the provisional PARTIAL convention for self-reported language/native proficiency or a TOEFL statement; QX13 has not been decided. The JD's required modality/level must remain in scope.

**Impact:** A consistent language-evidence convention can change individual B judgments; current provisional labels are not a settled rule.

**Proposed correction:** Resolve QX13 once, then apply it separately to each listed unit and its actual native/professional/intermediate/test evidence. Do not equate intermediate TOEFL with professional fluency automatically.

**C rows to recheck:** CV2/F00055 (row 14, pending)

### AUD-090: B_Evidence — F00074 / CV2 / D2-U01

- Excel row: 729. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Professional working proficiency in written and spoken English",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Self-reported professional proficiency; no contextual English work example. Language convention needs review.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Professional working proficiency in English, written and spoken

**Current CV quote**

> Indonesian (native), English (professional working proficiency)

**Problem:** The row uses the provisional PARTIAL convention for self-reported language/native proficiency or a TOEFL statement; QX13 has not been decided. The JD's required modality/level must remain in scope.

**Impact:** A consistent language-evidence convention can change individual B judgments; current provisional labels are not a settled rule.

**Proposed correction:** Resolve QX13 once, then apply it separately to each listed unit and its actual native/professional/intermediate/test evidence. Do not equate intermediate TOEFL with professional fluency automatically.

**C rows to recheck:** CV2/F00074 (row 15, pending)

### AUD-091: B_Evidence — F00650 / CV2 / P44-U13

- Excel row: 1135. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Written and spoken English",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Self-reported professional proficiency; no contextual English work example. Language convention needs review.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Excellent written and verbal communication skills in English.

**Current CV quote**

> Indonesian (native), English (professional working proficiency)

**Problem:** The row uses the provisional PARTIAL convention for self-reported language/native proficiency or a TOEFL statement; QX13 has not been decided. The JD's required modality/level must remain in scope.

**Impact:** A consistent language-evidence convention can change individual B judgments; current provisional labels are not a settled rule.

**Proposed correction:** Resolve QX13 once, then apply it separately to each listed unit and its actual native/professional/intermediate/test evidence. Do not equate intermediate TOEFL with professional fluency automatically.

**C rows to recheck:** CV2/F00650 (row 10, pending)

### AUD-092: B_Evidence — F00074 / CV1 / D2-U01

- Excel row: 1319. Review status: **pending**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
{
  "unit_text": "Professional working proficiency in written and spoken English",
  "label": "PARTIAL",
  "check_status": "done",
  "draft_note": "Proficiency/test stated; no contextual English work example. Language evidence convention needs reviewer clarification.",
  "review_action": null,
  "review_note": null,
  "guideline_version": "v1.2"
}
```

**JD source**

> Professional working proficiency in English, written and spoken

**Current CV quote**

> Indonesia (native), Inggris (menengah, TOEFL ITP 540)

**Problem:** The row uses the provisional PARTIAL convention for self-reported language/native proficiency or a TOEFL statement; QX13 has not been decided. The JD's required modality/level must remain in scope.

**Impact:** A consistent language-evidence convention can change individual B judgments; current provisional labels are not a settled rule.

**Proposed correction:** Resolve QX13 once, then apply it separately to each listed unit and its actual native/professional/intermediate/test evidence. Do not equate intermediate TOEFL with professional fluency automatically.

**C rows to recheck:** CV1/F00074 (row 66, pending)

## 3. Source or guideline limitations

### AUD-024: A_Extraction — F00066 / — / —

- Excel row: no extracted row. Review status: **not_applicable_no_A_row**.
- Application gate: Human discussion/decision required; no workbook edit authorized yet.

**Current value**

```json
null
```

**JD source**

> Willing to work under a Project-Based Fixed-Term Employment Contract (PKWT) with Lintasarta.

**Problem:** The explicit willingness to take a project-based fixed-term PKWT contract is absent from A. The approved constraint contract only clearly covers location/work authorization.

**Impact:** A employment-condition coverage claim is incomplete unless this omission is explicitly scoped.

**Proposed correction:** Ask whether to track contract willingness as a nonscored clarification/administrative condition; do not silently add a scoring constraint.

**C rows to recheck:** CV2/F00066 (row 50, pending)

### AUD-045: A_Extraction — F00369 / — / —

- Excel row: no extracted row. Review status: **not_applicable_no_A_row**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
null
```

**JD source**

> A portfolio of pro

**Problem:** The source ends at 'A portfolio of pro', so the final qualification cannot be reconstructed or fully extracted.

**Impact:** Coverage is complete only for the available complete clauses, not the missing source tail.

**Proposed correction:** Keep the fragment unexpanded and retain a source-limitation note; any replacement source must follow provenance/version rules.

**C rows to recheck:** CV1/F00369 (row 52, pending)

### AUD-046: A_Extraction — F00364 / — / —

- Excel row: no extracted row. Review status: **not_applicable_no_A_row**.
- Application gate: Draft correction under existing rules; still wait for authorization to edit workbook.

**Current value**

```json
null
```

**JD source**

> Key Responsibilities

**Problem:** This JD contains responsibilities but no qualification clauses; zero A/B is intentional.

**Impact:** C is a role/evidence judgment with limited qualification information; an empty A/B cannot support a qualification score.

**Proposed correction:** Retain zero A/B and review C independently without manufacturing requirements.

**C rows to recheck:** CV2/F00364 (row 27, pending)

