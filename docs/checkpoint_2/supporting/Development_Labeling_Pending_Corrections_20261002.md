# Development labeling: authorized pending corrections

**Date:** 2 October 2026. **Status:** Saved; every corrected row remains pending. CP2.2 stays **IN PROGRESS**.

The user authorized clear corrections under existing rules, with A first and dependent B/C rechecked. Excel was confirmed closed immediately before saving. The current workbook received 13 A-row corrections, 33 B-row corrections and 2 C-rationale corrections (118 cells). Relevance numbers were not changed. All 63 approved rows, all review metadata, JD/CV source sheets, source quotes, pool, split, grouping, minima and scoring membership were preserved.

35 audit findings received draft corrections. AUD-034 was partly corrected (restore the US option), with the structural question still open. The other 56 original findings are deferred; this includes three source/guideline limitations. Corrected drafts are not approved labels. Enterprise context under AUD-015 remains an interpretation question even though the invented AI qualifier and inappropriate personal-project quote were corrected.

## Checks and limits

- 27 checks passed: exact saved candidate, all approved records and human metadata, source and non-annotation ZIP parts, worksheet layout/styles/validation/formulas, all source quotes, all B-to-A links, complete pair coverage, unchanged grouping/scoring membership, frozen files and installed hash.
- Rechecked 14 B rows linked to changed A and 23 affected C pairs. An approved C was inspected without modification. Both complete CV1/CV2 sources were read when selecting replacement evidence. This is targeted correction/dependency review, not a second complete semantic audit.
- No native Excel opening, new rendering, pytest/database test, API call, gold export or tuning. Unmodified worksheet XML outside the edited cells preserves layout and validation. Original snapshot validators were not rerun or modified.
- Session API cost US$0. Ledger: 88 records, US$0.01226822.

## Versions and evidence

- Before SHA-256: `8be2b05635cc4175f71e2a38cd39dfaa9f17f2f4e4d78d80b20b57516fe733ad`
- After SHA-256: `7a1321180ae7785d3ab018b9317acf76f97769404e06375ad8370753cc195bc1`
- Original-byte backup and candidate: private `notes/artifact_work/pending_corrections_20261002/`. The active workbook is now released for human review; pipeline work must not write it.
- [Full machine-readable before/after log and dependency checks](../../../evals/results/development_labeling_pending_corrections_20261002.json). The preparation manifest and original audit remain historical; this log records A fingerprint lineage separately.

## Short decision list (no decision applied)

| Topic | Pending choice and examples |
| --- | --- |
| Grouping and denominator | Merge duplicate automation/Power BI (AUD-023/028); restore AND tool lists (039/062); training OR versus D-040 (030/080); Python-related alternatives (079); US residence/travel split (034); RAG umbrella, one-or-more, nested minima (005/008/009/012/032/033). Category/technical-task changes affecting score membership also held (013/022/027/031/040/067). |
| Equivalence and relevant experience | Source-specific degree, FAISS, wrapper-restricted API, data modeling, DistilBERT/LLM and F1/precision-recall cases remain pending (003/004/007/052/055/058/059/061/064/069/073/074). Enterprise-environment scope remains open for F00029/P07-U27; company work receives only PARTIAL. |
| Language | Decide the native/professional self-report and TOEFL convention with written/spoken modalities (019 and 082 to 092). No language row changed. |
| Importance and behavioral precedent | Priority/around/focus clauses (001/016/075), independent ownership/high-stakes context (011/021/035/043/047), and the approved pilot communication precedent (017) require contextual review. The approved row remains unchanged. |

F00364 intentionally has zero A/B units. F00369 remains truncated. F00066 contract-willingness scope is optional and unresolved. Do not expand the required review workload to all drafts. Priority remains A D1/D2/D3, B CV1×D1 and CV2×D2, and the 40 C rows marked gold_review=yes.

## Before/after register

Identities, not spreadsheet row numbers, identify changes. The JSON also retains complete records, source quotes, unchanged review statuses, and the 37 dependency checks.

### 1. A_Extraction: F00029 / P07-U24

Findings: AUD-014. Review status: **pending -> pending**.

Restore the tools qualifier from the unchanged JD sentence; the existing alternative group stays intact. Guideline A1/A5.

| Field | Before | After |
| --- | --- | --- |
| unit_text | AI evaluation \| observability | AI evaluation tools \| observability tools |
| draft_note | Alternative group: best supported branch; one denominator unit. | Correction 2026-10-02 (AUD-014). Restore the tools qualifier from the unchanged JD sentence; the existing alternative group stays intact. Guideline A1/A5. Still pending human review. |

JD source (unchanged):

> Familiarity with AI evaluation or observability tools.

### 2. A_Extraction: F00029 / P07-U27

Findings: AUD-015. Review status: **pending -> pending**.

The source asks for enterprise environments and does not add an AI qualifier. Guideline A1/A5.

| Field | Before | After |
| --- | --- | --- |
| unit_text | Enterprise AI experience | Experience in enterprise environments |
| draft_note | Candidate qualification, normalized independently; evidence of use is assessed without inferring depth. | Correction 2026-10-02 (AUD-015). The source asks for enterprise environments and does not add an AI qualifier. Guideline A1/A5. Still pending human review. |

JD source (unchanged):

> Experience in enterprise environments is a plus.

### 3. A_Extraction: F00117 / P18-U23

Findings: AUD-026. Review status: **pending -> pending**.

The source says Jakarta, without South Jakarta. Willingness remains unconfirmed. Guideline A5/B4 and D-033.

| Field | Before | After |
| --- | --- | --- |
| unit_text | Full work-from-office in South Jakarta | Full work-from-office in Jakarta |
| draft_note | Candidate qualification, normalized independently; evidence of use is assessed without inferring depth. | Correction 2026-10-02 (AUD-026). The source says Jakarta, without South Jakarta. Willingness remains unconfirmed. Guideline A5/B4 and D-033. Still pending human review. |

JD source (unchanged):

> Placement client: JAKARTA, Full WFO

### 4. A_Extraction: F00208 / P23-U02

Findings: AUD-034. Review status: **pending -> pending**.

Restore the omitted US residence option. Keep the existing compound unit; residence/travel separation and overlap with P23-U01 remain deferred. Guideline A1/A5; no grouping decision applied.

| Field | Before | After |
| --- | --- | --- |
| unit_text | Residence within US territories and periodic travel availability | Residence in the US or its territories and periodic travel availability |
| draft_note | Candidate qualification, normalized independently; evidence of use is assessed without inferring depth. | Correction 2026-10-02 (AUD-034). Restore the omitted US residence option. Keep the existing compound unit; residence/travel separation and overlap with P23-U01 remain deferred. Guideline A1/A5; no grouping decision applied. Still pending human review. |

JD source (unchanged):

> Hybrid Work & Travel: Employees can live anywhere in the US or its territories, with the willingness and ability to travel for periodic in-person events-including semi-annual Common App retreats, department retreats, and strategic leadership sessions.

### 5. A_Extraction: F00412 / P36-U24

Findings: AUD-048. Review status: **pending -> pending**.

The source says model-agnostic, not agent-agnostic. Existing OR group unchanged. Guideline A5.

| Field | Before | After |
| --- | --- | --- |
| unit_text | Multi-agent \| agent-agnostic architecture | Multi-agent systems \| model-agnostic architectures |
| draft_note | Alternative group: best supported branch; one denominator unit. | Correction 2026-10-02 (AUD-048). The source says model-agnostic, not agent-agnostic. Existing OR group unchanged. Guideline A5. Still pending human review. |

JD source (unchanged):

> Multi-agent systems or model-agnostic architectures.

### 6. A_Extraction: F00798 / P51-U14

Findings: AUD-068. Review status: **pending -> pending**.

LangGraph/LangChain are explicitly named frameworks. Both old and corrected categories are technical; score membership is unchanged. Guideline A5/A6.

| Field | Before | After |
| --- | --- | --- |
| category | knowledge_area | skill_tool |
| draft_note | Practical knowledge in requirements; duplicate umbrella/agent synonyms need review before scoring. | Correction 2026-10-02 (AUD-068). LangGraph/LangChain are explicitly named frameworks. Both old and corrected categories are technical; score membership is unchanged. Guideline A5/A6. Still pending human review. |

JD source (unchanged):

> LangGraph

### 7. A_Extraction: F00798 / P51-U15

Findings: AUD-068. Review status: **pending -> pending**.

LangGraph/LangChain are explicitly named frameworks. Both old and corrected categories are technical; score membership is unchanged. Guideline A5/A6.

| Field | Before | After |
| --- | --- | --- |
| category | knowledge_area | skill_tool |
| draft_note | Practical knowledge in requirements; duplicate umbrella/agent synonyms need review before scoring. | Correction 2026-10-02 (AUD-068). LangGraph/LangChain are explicitly named frameworks. Both old and corrected categories are technical; score membership is unchanged. Guideline A5/A6. Still pending human review. |

JD source (unchanged):

> LangChain

### 8. A_Extraction: F00698 / P50-U23

Findings: AUD-078. Review status: **pending -> pending**.

This trailing qualification/keyword block has no clear requirement or preference heading. Retain importance=unknown and the existing unit, source and group; do not promote it based on position. Guideline A3/A4.

| Field | Before | After |
| --- | --- | --- |
| draft_note | Candidate qualification, normalized independently; evidence of use is assessed without inferring depth. | Correction 2026-10-02 (AUD-078). This trailing qualification/keyword block has no clear requirement or preference heading. Retain importance=unknown and the existing unit, source and group; do not promote it based on position. Guideline A3/A4. Still pending human review. |

JD source (unchanged):

> Experience with Llama Index

### 9. A_Extraction: F00698 / P50-U24

Findings: AUD-078. Review status: **pending -> pending**.

This trailing qualification/keyword block has no clear requirement or preference heading. Retain importance=unknown and the existing unit, source and group; do not promote it based on position. Guideline A3/A4.

| Field | Before | After |
| --- | --- | --- |
| draft_note | Candidate qualification, normalized independently; evidence of use is assessed without inferring depth. | Correction 2026-10-02 (AUD-078). This trailing qualification/keyword block has no clear requirement or preference heading. Retain importance=unknown and the existing unit, source and group; do not promote it based on position. Guideline A3/A4. Still pending human review. |

JD source (unchanged):

> Experience with Hugging Face

### 10. A_Extraction: F00698 / P50-U25

Findings: AUD-078. Review status: **pending -> pending**.

This trailing qualification/keyword block has no clear requirement or preference heading. Retain importance=unknown and the existing unit, source and group; do not promote it based on position. Guideline A3/A4.

| Field | Before | After |
| --- | --- | --- |
| draft_note | Candidate qualification, normalized independently; evidence of use is assessed without inferring depth. | Correction 2026-10-02 (AUD-078). This trailing qualification/keyword block has no clear requirement or preference heading. Retain importance=unknown and the existing unit, source and group; do not promote it based on position. Guideline A3/A4. Still pending human review. |

JD source (unchanged):

> Experience with React and TypeScript

### 11. A_Extraction: F00698 / P50-U26

Findings: AUD-078. Review status: **pending -> pending**.

This trailing qualification/keyword block has no clear requirement or preference heading. Retain importance=unknown and the existing unit, source and group; do not promote it based on position. Guideline A3/A4.

| Field | Before | After |
| --- | --- | --- |
| draft_note | Candidate qualification, normalized independently; evidence of use is assessed without inferring depth. | Correction 2026-10-02 (AUD-078). This trailing qualification/keyword block has no clear requirement or preference heading. Retain importance=unknown and the existing unit, source and group; do not promote it based on position. Guideline A3/A4. Still pending human review. |

JD source (unchanged):

> Experience with React and TypeScript

### 12. A_Extraction: F00698 / P50-U27

Findings: AUD-078. Review status: **pending -> pending**.

This trailing qualification/keyword block has no clear requirement or preference heading. Retain importance=unknown and the existing unit, source and group; do not promote it based on position. Guideline A3/A4.

| Field | Before | After |
| --- | --- | --- |
| draft_note | Candidate qualification, normalized independently; evidence of use is assessed without inferring depth. | Correction 2026-10-02 (AUD-078). This trailing qualification/keyword block has no clear requirement or preference heading. Retain importance=unknown and the existing unit, source and group; do not promote it based on position. Guideline A3/A4. Still pending human review. |

JD source (unchanged):

> Knowledge of Agentic AI architectures

### 13. A_Extraction: F00698 / P50-U28

Findings: AUD-078. Review status: **pending -> pending**.

This trailing qualification/keyword block has no clear requirement or preference heading. Retain importance=unknown and the existing unit, source and group; do not promote it based on position. Guideline A3/A4.

| Field | Before | After |
| --- | --- | --- |
| draft_note | Alternative group: best supported branch; one denominator unit. | Correction 2026-10-02 (AUD-078). This trailing qualification/keyword block has no clear requirement or preference heading. Retain importance=unknown and the existing unit, source and group; do not promote it based on position. Guideline A3/A4. Still pending human review. |

JD source (unchanged):

> Experience with MLOps or LLMOps platforms

### 14. B_Evidence: CV2 / F00029 / P07-U24

Findings: AUD-014. Review status: **pending -> pending**.

The project shows an answer-evaluation question set, but no named or described evaluation/observability tool. Credit evaluation activity only; full tool support is not established. Guideline B1/B4/B5; A dependency review under D-048.

| Field | Before | After |
| --- | --- | --- |
| unit_text | AI evaluation \| observability | AI evaluation tools \| observability tools |
| label | MATCH | PARTIAL |
| draft_note | Question-set evaluation and answer accuracy are contextual evaluation. | Correction 2026-10-02 (AUD-014). The project shows an answer-evaluation question set, but no named or described evaluation/observability tool. Credit evaluation activity only; full tool support is not established. Guideline B1/B4/B5; A dependency review under D-048. Still pending human review. |

JD source (unchanged):

> Familiarity with AI evaluation or observability tools.

### 15. B_Evidence: CV2 / F00029 / P07-U27

Findings: AUD-015. Review status: **pending -> pending**.

Replace the personal chatbot quote with actual company work. PARTIAL credits a professional environment only; enterprise scale/context is unproven and its interpretation remains open. No AI requirement or full enterprise equivalence is inferred. Guideline B1/B4/B5; A dependency review under D-048.

| Field | Before | After |
| --- | --- | --- |
| unit_text | Enterprise AI experience | Experience in enterprise environments |
| cv_quote | - Built a retrieval-augmented chatbot over 40 PDF reports using LangChain, OpenAI embeddings, and a FAISS vector store. | **Digital Marketing Analyst**, PT Contoh Media Digital, Bandung · March 2023 - May 2026<br>- Wrote SQL queries in BigQuery to build weekly campaign performance reports for 12 brands. |
| cv_section | Projects | Experience |
| draft_note | Personal PDF assistant, not enterprise system integration. | Correction 2026-10-02 (AUD-015). Replace the personal chatbot quote with actual company work. PARTIAL credits a professional environment only; enterprise scale/context is unproven and its interpretation remains open. No AI requirement or full enterprise equivalence is inferred. Guideline B1/B4/B5; A dependency review under D-048. Still pending human review. |

JD source (unchanged):

> Experience in enterprise environments is a plus.

### 16. B_Evidence: CV2 / F00117 / P18-U23

Findings: AUD-026. Review status: **pending -> pending**.

Corrected location wording does not confirm relocation or travel willingness. Keep PARTIAL and needs_clarification; do not infer eligibility or conflict from residence. Guideline B1/B4/B5; A dependency review under D-048.

| Field | Before | After |
| --- | --- | --- |
| unit_text | Full work-from-office in South Jakarta | Full work-from-office in Jakarta |
| draft_note | Residence does not prove commute, relocation or timezone availability. | Correction 2026-10-02 (AUD-026). Corrected location wording does not confirm relocation or travel willingness. Keep PARTIAL and needs_clarification; do not infer eligibility or conflict from residence. Guideline B1/B4/B5; A dependency review under D-048. Still pending human review. |

JD source (unchanged):

> Placement client: JAKARTA, Full WFO

### 17. B_Evidence: CV1 / F00208 / P23-U02

Findings: AUD-034. Review status: **pending -> pending**.

Corrected location wording does not confirm relocation or travel willingness. Keep PARTIAL and needs_clarification; do not infer eligibility or conflict from residence. Guideline B1/B4/B5; A dependency review under D-048.

| Field | Before | After |
| --- | --- | --- |
| unit_text | Residence within US territories and periodic travel availability | Residence in the US or its territories and periodic travel availability |
| draft_note | Residence does not prove commute, relocation or timezone availability. | Correction 2026-10-02 (AUD-034). Corrected location wording does not confirm relocation or travel willingness. Keep PARTIAL and needs_clarification; do not infer eligibility or conflict from residence. Guideline B1/B4/B5; A dependency review under D-048. Still pending human review. |

JD source (unchanged):

> Hybrid Work & Travel: Employees can live anywhere in the US or its territories, with the willingness and ability to travel for periodic in-person events-including semi-annual Common App retreats, department retreats, and strategic leadership sessions.

### 18. B_Evidence: CV2 / F00208 / P23-U02

Findings: AUD-034. Review status: **pending -> pending**.

Corrected location wording does not confirm relocation or travel willingness. Keep PARTIAL and needs_clarification; do not infer eligibility or conflict from residence. Guideline B1/B4/B5; A dependency review under D-048.

| Field | Before | After |
| --- | --- | --- |
| unit_text | Residence within US territories and periodic travel availability | Residence in the US or its territories and periodic travel availability |
| draft_note | Residence does not prove commute, relocation or timezone availability. | Correction 2026-10-02 (AUD-034). Corrected location wording does not confirm relocation or travel willingness. Keep PARTIAL and needs_clarification; do not infer eligibility or conflict from residence. Guideline B1/B4/B5; A dependency review under D-048. Still pending human review. |

JD source (unchanged):

> Hybrid Work & Travel: Employees can live anywhere in the US or its territories, with the willingness and ability to travel for periodic in-person events-including semi-annual Common App retreats, department retreats, and strategic leadership sessions.

### 19. B_Evidence: CV2 / F00412 / P36-U24

Findings: AUD-048. Review status: **pending -> pending**.

Neither multi-agent systems nor model-agnostic architecture is evidenced in the complete CV. Keep NO_MATCH, done and no quote under corrected A. Guideline B1/B4/B5; A dependency review under D-048.

| Field | Before | After |
| --- | --- | --- |
| unit_text | Multi-agent \| agent-agnostic architecture | Multi-agent systems \| model-agnostic architectures |
| draft_note | No evidence found in the CV; this does not assert the person lacks the skill. | Correction 2026-10-02 (AUD-048). Neither multi-agent systems nor model-agnostic architecture is evidenced in the complete CV. Keep NO_MATCH, done and no quote under corrected A. Guideline B1/B4/B5; A dependency review under D-048. Still pending human review. |

JD source (unchanged):

> Multi-agent systems or model-agnostic architectures.

### 20. B_Evidence: CV2 / F00103 / D1-U28

Findings: AUD-002. Review status: **pending -> pending**.

The complete CV has reporting, data preparation and application projects, but no data-quality framework or matching skills-list item. Report automation is not evidence of this requirement. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | PARTIAL | NO_MATCH |
| cv_quote | - Automated report generation with Python scripts, cutting manual reporting time from 6 hours to 1 hour per week. | (empty) |
| cv_section | Experience | (empty) |
| draft_note | Report automation is related data work; no data-quality framework is identified. | Correction 2026-10-02 (AUD-002). The complete CV has reporting, data preparation and application projects, but no data-quality framework or matching skills-list item. Report automation is not evidence of this requirement. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Pengalaman framework dan monitoring kualitas data.

### 21. B_Evidence: CV1 / F00036 / P09-U10

Findings: AUD-018. Review status: **pending -> pending**.

Use the actual cohort-retention analysis activity as descriptive analysis in work. Regression/F1 prediction metrics were the wrong evidence; no credit is based on degree title alone. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| cv_quote | - Membangun model regresi logistik dan random forest dengan scikit-learn; F1-score 0,78 pada data uji. | - Melakukan analisis cohort retensi pelanggan dan mempresentasikan hasilnya ke manajer divisi. |
| cv_section | Projects | Experience |
| draft_note | Applied regression model and S1 statistics context. | Correction 2026-10-02 (AUD-018). Use the actual cohort-retention analysis activity as descriptive analysis in work. Regression/F1 prediction metrics were the wrong evidence; no credit is based on degree title alone. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Pemahaman solid tentang statistik deskriptif dan inferensial serta metodologi penelitian.

### 22. B_Evidence: CV2 / F00055 / P11-U14

Findings: AUD-020. Review status: **pending -> pending**.

The summary explicitly reports data preparation in LLM/retrieval projects. It does not establish raw messy conversation-log processing. Credit the supported data-preparation component only. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| cv_quote | - Automated report generation with Python scripts, cutting manual reporting time from 6 hours to 1 hour per week. | Built LLM and retrieval projects end to end, from data preparation to a deployed API. |
| cv_section | Experience | Summary |
| draft_note | Python automation of reports provides related data work; exact wrangling steps not specified. | Correction 2026-10-02 (AUD-020). The summary explicitly reports data preparation in LLM/retrieval projects. It does not establish raw messy conversation-log processing. Credit the supported data-preparation component only. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Ability to work with raw, messy data — you will be building pipelines from conversation logs, not receiving clean feature tables

### 23. B_Evidence: CV2 / F00114 / J5-U08

Findings: AUD-025. Review status: **pending -> pending**.

The project uses OpenAI embeddings, but does not document embedding-model selection. Credit embedding use without inventing a selection exercise or production RAG. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| draft_note | Contextual use supports this unit; no claim about truth or depth. Confirm against source CV. | Correction 2026-10-02 (AUD-025). The project uses OpenAI embeddings, but does not document embedding-model selection. Credit embedding use without inventing a selection exercise or production RAG. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Real RAG production experience: chunking trade-offs, embedding selection, hybrid retrieval, reranking, and how to measure retrieval quality.

### 24. B_Evidence: CV1 / F00208 / P23-U36

Findings: AUD-029. Review status: **pending -> pending**.

The university regression-practicum assistant role explicitly supports the existing higher-education alternative. No nonprofit status or new alternative group is inferred. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | NO_MATCH | MATCH |
| cv_quote | (empty) | **Asisten Praktikum Analisis Regresi**, Universitas Negeri Contoh · Februari 2025 - Juni 2025<br>- Membimbing 40 mahasiswa dalam praktikum regresi menggunakan R. |
| cv_section | (empty) | Experience |
| draft_note | No evidence found in the CV; this does not assert the person lacks the skill. | Correction 2026-10-02 (AUD-029). The university regression-practicum assistant role explicitly supports the existing higher-education alternative. No nonprofit status or new alternative group is inferred. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Experience in higher education, nonprofit, or mission-driven technology contexts.

### 25. B_Evidence: CV2 / F00310 / P27-U08

Findings: AUD-036. Review status: **pending -> pending**.

The complete CV names DistilBERT and an unspecified OpenAI embedding service, but no current frontier/open-weight model in this unit. General NLP/RAG experience is credited in separate units, not substituted here. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | NO_MATCH |
| cv_quote | - Built a retrieval-augmented chatbot over 40 PDF reports using LangChain, OpenAI embeddings, and a FAISS vector store. | (empty) |
| cv_section | Projects | (empty) |
| draft_note | RAG application with embeddings/LangChain; no production deployment inferred. | Correction 2026-10-02 (AUD-036). The complete CV names DistilBERT and an unspecified OpenAI embedding service, but no current frontier/open-weight model in this unit. General NLP/RAG experience is credited in separate units, not substituted here. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Expertise in Natural Language Processing (NLP) and Generative AI with a deep understanding of the latest LLM landscape, including transformer-based architectures such as BERT and T5, and current frontier and open-weight models (e.g., GPT-5.x, Claude 4/5, Gemini 2.x/3.x, Llama 4, DeepSeek, Qwen) that are driving the evolution of NLP and agentic AI applications.

### 26. B_Evidence: CV2 / F00310 / P27-U49

Findings: AUD-037. Review status: **pending -> pending**.

The summary reports data preparation for a retrieval application. This is limited related input-data work, not explicit ingestion implementation or use of the JD ingestion/distributed tools. Withdraw full MATCH. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| cv_quote | - Automated report generation with Python scripts, cutting manual reporting time from 6 hours to 1 hour per week. | Built LLM and retrieval projects end to end, from data preparation to a deployed API. |
| cv_section | Experience | Summary |
| draft_note | Python automation of reports provides related data work; exact wrangling steps not specified. | Correction 2026-10-02 (AUD-037). The summary reports data preparation for a retrieval application. This is limited related input-data work, not explicit ingestion implementation or use of the JD ingestion/distributed tools. Withdraw full MATCH. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Hands-on experience with data ingestion, data wrangling, and data pipeline orchestration using tools like Apache Kafka, Apache Spark, Airflow, and distributed computing frameworks like Dask and Ray.

### 27. B_Evidence: CV2 / F00310 / P27-U50

Findings: AUD-038. Review status: **pending -> pending**.

The summary explicitly states data preparation, but no concrete wrangling operation or requested distributed tool is described. Withdraw full MATCH; reporting automation alone was insufficient. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| cv_quote | - Automated report generation with Python scripts, cutting manual reporting time from 6 hours to 1 hour per week. | Built LLM and retrieval projects end to end, from data preparation to a deployed API. |
| cv_section | Experience | Summary |
| draft_note | Python automation of reports provides related data work; exact wrangling steps not specified. | Correction 2026-10-02 (AUD-038). The summary explicitly states data preparation, but no concrete wrangling operation or requested distributed tool is described. Withdraw full MATCH; reporting automation alone was insufficient. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Hands-on experience with data ingestion, data wrangling, and data pipeline orchestration using tools like Apache Kafka, Apache Spark, Airflow, and distributed computing frameworks like Dask and Ray.

### 28. B_Evidence: CV2 / F00327 / P28-U03

Findings: AUD-041. Review status: **pending -> pending**.

A/B tests support the marketing measurement/experimentation component. Auction mechanics, campaign structure and targeting mechanics are not established by that sentence. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| draft_note | Contextual use supports this unit; no claim about truth or depth. Confirm against source CV. | Correction 2026-10-02 (AUD-041). A/B tests support the marketing measurement/experimentation component. Auction mechanics, campaign structure and targeting mechanics are not established by that sentence. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Deep understanding of paid/performance marketing KPIs, how media platforms work (campaign structure, auction mechanics, targeting, measurement) and their APIs (Meta, Google Ads, TikTok), and MMP tooling (AppsFlyer, Adjust).

### 29. B_Evidence: CV1 / F00330 / P29-U03

Findings: AUD-042. Review status: **pending -> pending**.

Actual applied ML project work supports related AI learning. It does not establish the source-specific AI coding/agent-tool practice or ongoing learning behavior. The analytics certificate was insufficient. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| cv_quote | - Google Data Analytics Professional Certificate (2025) | - Membangun model regresi logistik dan random forest dengan scikit-learn; F1-score 0,78 pada data uji. |
| cv_section | Certifications | Projects |
| draft_note | Completed certificate demonstrates learning activity. | Correction 2026-10-02 (AUD-042). Actual applied ML project work supports related AI learning. It does not establish the source-specific AI coding/agent-tool practice or ongoing learning behavior. The analytics certificate was insufficient. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> You’re AI-native and you learn fast. You build with AI coding and agent tools (Cursor, Claude Code, and the like), and you keep up with the space by doing, not just reading.

### 30. B_Evidence: CV1 / F00332 / P30-U14

Findings: AUD-044. Review status: **pending -> pending**.

The quote demonstrates processing a large tabular dataset. It does not demonstrate anomaly investigation or the full trend/anomaly-to-recommendation requirement. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| draft_note | 1.2 million transaction rows explicitly processed. | Correction 2026-10-02 (AUD-044). The quote demonstrates processing a large tabular dataset. It does not demonstrate anomaly investigation or the full trend/anomaly-to-recommendation requirement. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Experience working with large tabular datasets to detect trends and anomalies and communicate findings as actionable recommendations.

### 31. B_Evidence: CV2 / F00412 / P36-U18

Findings: AUD-049. Review status: **pending -> pending**.

No CV statement expresses willingness to work in human-agent cooperation. Bootcamp attendance does not demonstrate that specific willingness; this is absence of evidence, not refusal. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | NO_MATCH |
| cv_quote | **Data Science and AI Bootcamp**, Contoh Academy (online) · June 2026 - present | (empty) |
| cv_section | Education | (empty) |
| draft_note | Ongoing reskilling demonstrates learning activity. | Correction 2026-10-02 (AUD-049). No CV statement expresses willingness to work in human-agent cooperation. Bootcamp attendance does not demonstrate that specific willingness; this is absence of evidence, not refusal. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Willingness to work in a human-agent cooperation model.

### 32. B_Evidence: CV2 / F00412 / P36-U08

Findings: AUD-050. Review status: **pending -> pending**.

No CV sentence demonstrates the stated interest in agent orchestration, tool calling or controlled autonomy. General AI bootcamp attendance does not establish this specific behavior. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | NO_MATCH |
| cv_quote | **Data Science and AI Bootcamp**, Contoh Academy (online) · June 2026 - present | (empty) |
| cv_section | Education | (empty) |
| draft_note | Ongoing reskilling demonstrates learning activity. | Correction 2026-10-02 (AUD-050). No CV sentence demonstrates the stated interest in agent orchestration, tool calling or controlled autonomy. General AI bootcamp attendance does not establish this specific behavior. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Strong interest in agent orchestration, tool calling and controlled autonomy.

### 33. B_Evidence: CV2 / F00412 / P36-U03

Findings: AUD-051. Review status: **pending -> pending**.

Using OpenAI embeddings in a LangChain application supports the explicitly allowed AI-service integration branch. The JD does not require direct low-level requests; no generative LLM API or wrapper equivalence decision is inferred. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | PARTIAL | MATCH |
| draft_note | OpenAI embeddings through LangChain are shown; direct API calls/request handling not demonstrated. | Correction 2026-10-02 (AUD-051). Using OpenAI embeddings in a LangChain application supports the explicitly allowed AI-service integration branch. The JD does not require direct low-level requests; no generative LLM API or wrapper equivalence decision is inferred. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Practical experience integrating LLMs, machine learning or AI services into applications.

### 34. B_Evidence: CV2 / F00052 / P10-U32

Findings: AUD-053. Review status: **pending -> pending**.

The source explicitly includes OpenAI services; the RAG application uses OpenAI embeddings. Direct low-level API request handling is not stated as a condition here. Do not generalize to wrapper-restricted JDs. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | PARTIAL | MATCH |
| draft_note | OpenAI embeddings through LangChain are shown; direct API calls/request handling not demonstrated. | Correction 2026-10-02 (AUD-053). The source explicitly includes OpenAI services; the RAG application uses OpenAI embeddings. Direct low-level API request handling is not stated as a condition here. Do not generalize to wrapper-restricted JDs. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Experience working with AI APIs and services such as OpenAI, Google Gemini, Anthropic, or similar platforms.

### 35. B_Evidence: CV2 / F00438 / P37-U11

Findings: AUD-054. Review status: **pending -> pending**.

The personal RAG chatbot demonstrates AI-tool building. Internal business use/adoption is not stated and must not be invented. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| draft_note | Contextual use supports this unit; no claim about truth or depth. Confirm against source CV. | Correction 2026-10-02 (AUD-054). The personal RAG chatbot demonstrates AI-tool building. Internal business use/adoption is not stated and must not be invented. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Hands-on technical fluency in configuring and building internal tools using modern AI platforms, automation builders, and dashboard interfaces.

### 36. B_Evidence: CV2 / F00438 / P37-U14

Findings: AUD-056. Review status: **pending -> pending**.

Python report automation supports related reporting output. Combining disparate silos and executive-facing actionable views are not evidenced; no integration or audience is inferred. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| draft_note | Python automation of reports provides related data work; exact wrangling steps not specified. | Correction 2026-10-02 (AUD-056). Python report automation supports related reporting output. Combining disparate silos and executive-facing actionable views are not evidenced; no integration or audience is inferred. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Strong data intuition—you know how to connect disparate data silos into clean, actionable executive views.

### 37. B_Evidence: CV1 / F00601 / P42-U16

Findings: AUD-060. Review status: **pending -> pending**.

Cohort analysis and presentation support insight communication. No experiment or conversion of experimental results into decisions is stated. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| draft_note | Contextual use supports this unit; no claim about truth or depth. Confirm against source CV. | Correction 2026-10-02 (AUD-060). Cohort analysis and presentation support insight communication. No experiment or conversion of experimental results into decisions is stated. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Proven experience in experimentation frameworks (A/B testing), including design, analysis, and bias mitigation, along with the ability to translate insights into actionable decisions.

### 38. B_Evidence: CV2 / F00663 / P47-U10

Findings: AUD-063. Review status: **pending -> pending**.

The summary states data preparation for LLM/retrieval projects, without concrete preprocessing operations. Credit weaker related preparation evidence only, not full preprocessing expertise. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| cv_quote | - Automated report generation with Python scripts, cutting manual reporting time from 6 hours to 1 hour per week. | Built LLM and retrieval projects end to end, from data preparation to a deployed API. |
| cv_section | Experience | Summary |
| draft_note | Python automation of reports provides related data work; exact wrangling steps not specified. | Correction 2026-10-02 (AUD-063). The summary states data preparation for LLM/retrieval projects, without concrete preprocessing operations. Credit weaker related preparation evidence only, not full preprocessing expertise. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Data Processing: Kemampuan strong dalam data preprocessing, feature engineering, dan handling big data menggunakan tools seperti Pandas, NumPy, dan SQL.

### 39. B_Evidence: CV1 / F00654 / P45-U10

Findings: AUD-065. Review status: **pending -> pending**.

The sentence supports communicating analysis results to a manager. Progress, trade-offs and the full cross-functional scope are not shown; these are distinct checkable activities, not proficiency depth. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| draft_note | Contextual use supports this unit; no claim about truth or depth. Confirm against source CV. | Correction 2026-10-02 (AUD-065). The sentence supports communicating analysis results to a manager. Progress, trade-offs and the full cross-functional scope are not shown; these are distinct checkable activities, not proficiency depth. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> You excel at communicating progress, trade-offs, and the results of your work to team

### 40. B_Evidence: CV2 / F00666 / P48-U14

Findings: AUD-066. Review status: **pending -> pending**.

BigQuery SQL reporting is explicit. Profiling and large operational dataset volume are not established by the number of brands. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| draft_note | Contextual use supports this unit; no claim about truth or depth. Confirm against source CV. | Correction 2026-10-02 (AUD-066). BigQuery SQL reporting is explicit. Profiling and large operational dataset volume are not established by the number of brands. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Strong SQL skills for data analysis. Comfortable querying, profiling, and drawing conclusions from large operational datasets.

### 41. B_Evidence: CV2 / F00055 / P11-U07

Findings: AUD-070. Review status: **pending -> pending**.

The project evaluates end-to-end answer accuracy using a question set. It does not separately demonstrate prompt evaluation/comparison or retrieval-quality evaluation. Credit only the related evaluation component. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| draft_note | Question-set evaluation and answer accuracy are contextual evaluation. | Correction 2026-10-02 (AUD-070). The project evaluates end-to-end answer accuracy using a question set. It does not separately demonstrate prompt evaluation/comparison or retrieval-quality evaluation. Credit only the related evaluation component. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Fluency with LLM APIs (Anthropic, OpenAI, or equivalent): structured prompting, JSON output parsing, batch processing, and prompt evaluation — this is your primary technical tool

### 42. B_Evidence: CV2 / F00310 / P27-U17

Findings: AUD-071. Review status: **pending -> pending**.

The project evaluates end-to-end answer accuracy using a question set. It does not separately demonstrate prompt evaluation/comparison or retrieval-quality evaluation. Credit only the related evaluation component. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| draft_note | Question-set evaluation and answer accuracy are contextual evaluation. | Correction 2026-10-02 (AUD-071). The project evaluates end-to-end answer accuracy using a question set. It does not separately demonstrate prompt evaluation/comparison or retrieval-quality evaluation. Credit only the related evaluation component. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Practical experience with Retrieval-Augmented Generation (RAG), including chunking strategies, embedding models, hybrid search, and retrieval evaluation.

### 43. B_Evidence: CV2 / F00310 / P27-U21

Findings: AUD-072. Review status: **pending -> pending**.

The project evaluates end-to-end answer accuracy using a question set. It does not separately demonstrate prompt evaluation/comparison or retrieval-quality evaluation. Credit only the related evaluation component. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| draft_note | Question-set evaluation and answer accuracy are contextual evaluation. | Correction 2026-10-02 (AUD-072). The project evaluates end-to-end answer accuracy using a question set. It does not separately demonstrate prompt evaluation/comparison or retrieval-quality evaluation. Credit only the related evaluation component. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Experience fine-tuning and adapting large models efficiently, using techniques such as LoRA/QLoRA, parameter-efficient fine-tuning (PEFT), quantization, and distillation, along with LLMOps practices for prompt evaluation, guardrails, hallucination testing, and observability (e.g., LangSmith, RAGAS, Arize).

### 44. B_Evidence: CV1 / F00438 / P37-U04

Findings: AUD-076. Review status: **pending -> pending**.

An actual internal marketing dashboard supports related tool-building activity. Personal excitement/motivation is not established; the analytics certificate did not support this specific behavior. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| cv_quote | - Google Data Analytics Professional Certificate (2025) | - Membuat dashboard penjualan mingguan di Looker Studio untuk tim marketing. |
| cv_section | Certifications | Experience |
| draft_note | Completed certificate demonstrates learning activity. | Correction 2026-10-02 (AUD-076). An actual internal marketing dashboard supports related tool-building activity. Personal excitement/motivation is not established; the analytics certificate did not support this specific behavior. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Want It: You genuinely get excited about building internal tools, mapping workflows, and freeing teams from manual reporting drudgery.

### 45. B_Evidence: CV2 / F00438 / P37-U04

Findings: AUD-077. Review status: **pending -> pending**.

Actual report automation supports related workflow improvement. Personal excitement/motivation is not established; bootcamp attendance did not support this specific behavior. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| cv_quote | **Data Science and AI Bootcamp**, Contoh Academy (online) · June 2026 - present | - Automated report generation with Python scripts, cutting manual reporting time from 6 hours to 1 hour per week. |
| cv_section | Education | Experience |
| draft_note | Ongoing reskilling demonstrates learning activity. | Correction 2026-10-02 (AUD-077). Actual report automation supports related workflow improvement. Personal excitement/motivation is not established; bootcamp attendance did not support this specific behavior. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Want It: You genuinely get excited about building internal tools, mapping workflows, and freeing teams from manual reporting drudgery.

### 46. B_Evidence: CV1 / F00438 / P37-U14

Findings: AUD-081. Review status: **pending -> pending**.

Cleaning and combining transaction data supports the data-integration component. Even the dashboard and manager-presentation bullets do not establish the full executive-view scope. Guideline B1/B4/B5; no new equivalence or depth rule.

| Field | Before | After |
| --- | --- | --- |
| label | MATCH | PARTIAL |
| draft_note | Contextual use supports this unit; no claim about truth or depth. Confirm against source CV. | Correction 2026-10-02 (AUD-081). Cleaning and combining transaction data supports the data-integration component. Even the dashboard and manager-presentation bullets do not establish the full executive-view scope. Guideline B1/B4/B5; no new equivalence or depth rule. Still pending human review. |

JD source (unchanged):

> Strong data intuition—you know how to connect disparate data silos into clean, actionable executive views.

### 47. C_Relevance: CV1 / F00074

Findings: AUD-010. Review status: **pending -> pending**.

Remove invented leadership. Keep relevance 1: weak relevant production/LLM evidence and the dated employment upper bound do not support the stated minimum. Guideline Part C/Part D and D-042.

| Field | Before | After |
| --- | --- | --- |
| constraint_note | Required production/leadership duration is not supported by relevant professional history. | The JD requires at least 2 years building production software and at least 1 year shipping LLM apps. CV1 does not evidence these periods; leadership is not a requirement in this JD. |
| draft_note | Optional expanded pair, outside frozen dev_pool. Ordinal judgement, not coverage percentage. Review full A/B/C sources. | Correction 2026-10-02 (AUD-010). Remove invented leadership. Keep relevance 1: weak relevant production/LLM evidence and the dated employment upper bound do not support the stated minimum. Guideline Part C/Part D and D-042. Still pending human review. |

### 48. C_Relevance: CV2 / F00438

Findings: AUD-057. Review status: **pending -> pending**.

Replace the unsupported dashboard-work claim. Keep relevance 2 as a pending ordinal judgment from actual automation and AI-tool overlap, with the newly clarified gaps; no explicit duration minimum. Guideline Part D; not a match-percentage conversion.

| Field | Before | After |
| --- | --- | --- |
| main_reason | Marketing report automation, dashboard work and RAG support several areas; process mapping, SOPs and workflow-builder implementation are gaps. | Marketing report automation and a RAG project support several areas; Looker Studio is listed only. Internal adoption, executive data integration, process mapping, SOPs and workflow-builder implementation remain gaps. |
| draft_note | Guideline v1.2 Part D; evidence coverage and explicit qualifications, not retrieval score. Human review required. | Correction 2026-10-02 (AUD-057). Replace the unsupported dashboard-work claim. Keep relevance 2 as a pending ordinal judgment from actual automation and AI-tool overlap, with the newly clarified gaps; no explicit duration minimum. Guideline Part D; not a match-percentage conversion. Still pending human review. |

## Next work

Human review and unresolved decisions remain open. The user separately authorized independent CP2.2 parser/extraction/matching/paste-JD implementation while reviewing in Excel. That work must not write this workbook. CP2.3 remains out of scope.
