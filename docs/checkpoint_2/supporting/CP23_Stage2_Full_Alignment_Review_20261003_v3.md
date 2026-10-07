# CP2.3 Stage-2 candidate-specific extraction alignment review

**Current acceptance:** Dion accepted the recommended relations and fixed adapter under D-063. The immutable proposal JSON retains its pre-acceptance flags; the separate hash-bound receipt and derived metric artifact carry the acceptance provenance. The original snapshot below is historical, not independent human annotation.

3 October 2026. Complete proposals for 27 final drafts plus one retained process failure. D-060/D-061 conventions approved; concrete recommended mappings still await acceptance. No candidate-specific human approval or formal F1 is claimed.

## Review boundaries

Gold and original outputs are unchanged. Primary proposed equivalence follows D-061, with category accuracy separate. Structural splits/merges follow D-054; the exact Claude/F00036 complex relation follows D-060. All original cases remain in the comparison denominator. Recommended booleans remain QA proposals, not accepted relations.

**Reassessment of historical source QA:** the active evidence prompt explicitly inherits shared parent qualifiers into every OR branch. Missing repeated words in a branch are not automatically a semantic failure when the parent retains the scope. Ordinary proficiency-depth words also follow D-035/D-042, rather than becoming new obligations. Original QA notes below are historical observations; current mapping notes distinguish these cases from genuine missing context. Neither correction changes gold or authorizes a candidate winner.

| Candidate / JD | Gold units | Model units | Proposed relations |
|---|---:|---:|---|
| deepseek-flash/F00332 | 16 | 17 | {'one_to_one': 15, 'model_split': 1} |
| deepseek-flash/F00036 | 17 | 19 | {'one_to_one': 17, 'model_addition': 2} |
| deepseek-flash/F00309 | 9 | 9 | {'one_to_one': 9} |
| deepseek-flash/F00354 | 29 | 34 | {'one_to_one': 28, 'model_split': 1} |
| deepseek-flash/F00815 | 16 | 15 | {'one_to_one': 12, 'model_split': 1, 'model_merge': 1} |
| deepseek-flash/F00010 | 9 | 9 | {'one_to_one': 9} |
| deepseek-flash/F00018 | 24 | 23 | {'one_to_one': 22, 'model_merge': 1} |
| gpt-6-luna/F00332 | 16 | 20 | {'one_to_one': 14, 'model_split': 2} |
| gpt-6-luna/F00036 | 17 | 20 | {'one_to_one': 17, 'model_addition': 3} |
| gpt-6-luna/F00309 | 9 | 9 | {'one_to_one': 9} |
| gpt-6-luna/F00354 | 29 | 34 | {'one_to_one': 28, 'model_split': 1} |
| gpt-6-luna/F00815 | 16 | 17 | {'one_to_one': 15, 'model_split': 1} |
| gpt-6-luna/F00010 | 9 | 9 | {'one_to_one': 9} |
| gpt-6-luna/F00018 | 24 | 23 | {'one_to_one': 22, 'model_merge': 1} |
| gemini-3.5-flash-lite/F00332 | 16 | 19 | {'model_split': 1, 'one_to_one': 15} |
| gemini-3.5-flash-lite/F00036 | 17 | 14 | {'one_to_one': 11, 'model_merge': 3} |
| gemini-3.5-flash-lite/F00309 | 9 | 9 | {'one_to_one': 9} |
| gemini-3.5-flash-lite/F00354 | 29 | 38 | {'model_split': 2, 'one_to_one': 23, 'model_merge': 1} |
| gemini-3.5-flash-lite/F00815 | 16 | 0 | retained_process_failure |
| gemini-3.5-flash-lite/F00010 | 9 | 9 | {'one_to_one': 9} |
| gemini-3.5-flash-lite/F00018 | 24 | 16 | {'one_to_one': 15, 'model_merge': 1, 'model_omission': 7} |
| claude-haiku-4.5/F00332 | 16 | 13 | {'one_to_one': 11, 'model_merge': 2} |
| claude-haiku-4.5/F00036 | 17 | 18 | {'one_to_one': 3, 'model_split': 2, 'model_merge': 4, 'complex_pending': 1, 'model_addition': 1} |
| claude-haiku-4.5/F00309 | 9 | 9 | {'one_to_one': 9} |
| claude-haiku-4.5/F00354 | 29 | 34 | {'one_to_one': 28, 'model_split': 1} |
| claude-haiku-4.5/F00815 | 16 | 16 | {'one_to_one': 16} |
| claude-haiku-4.5/F00010 | 9 | 12 | {'one_to_one': 5, 'model_split': 2, 'model_merge': 1} |
| claude-haiku-4.5/F00018 | 24 | 18 | {'model_merge': 1, 'one_to_one': 14, 'model_split': 1, 'model_omission': 7} |

## Complete row inventory

Each row below is a proposal awaiting acceptance, including apparent equivalents. Full original JD, branch qualifiers, quotes and typed records are retained in the paired JSON.

### deepseek-flash/F00332

Delegated source-semantic QA of the full F00332 JD and the reviewed 16-logical-unit reference. Both attempts are ledgered; the final draft has 17 units. All eight qualification inventory entries are mapped and every source quote is exact. Python, SQL and Excel are now independent. However, Q01's source says 'other disciplines will be considered' while its alternative_group branches only encode fresh graduate and a bachelor's degree in an analytical/quantitative discipline; needs_review=true prevents silent scoring but does not represent the considered-other-discipline path as an assessable branch. U14/U15 also split one reviewed large-tabular trend/anomaly obligation, a strict D-054 split/merge relation rather than an automatic TP. Category for SQL-based analyses differs from the reviewed knowledge_area category and needs alignment. Therefore coverage, grouping and qualifier compatibility are not established. Stop before the next JD/model under the frozen quality gate; preserve both paid attempts. This is not a gold amendment or winner claim.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P30-U01: Fresh graduate  /  bachelor in quantitative/analytical or other considered discipline | U01: Fresh graduate or bachelor's degree in an analytical or quantitative discipline (e.g., math, statistics, engineering, computer science); other disciplines will be considered. | one_to_one / False | Missing considered-other-discipline branch |
| P30-U02: Python | U02: Experience using statistical computer languages such as Python. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U03: SQL | U03: Experience using statistical computer languages such as SQL. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U04: Microsoft Excel | U04: Experience using statistical computer languages such as MS Excel. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U05: Communication | U05: Good communication skills. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U06: Team collaboration | U06: Ability to work collaboratively in a team. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U07: Problem solving | U07: Excellent problem-solving skills. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U08: Learning new techniques | U08: Drive to learn and master new technologies and techniques. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U09: Independent learning | U09: Willingness to learn new skills independently. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U10: Project ownership | U10: Strong sense of project ownership. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U11: Data exploration | U11: Comfortable exploring data. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U12: Anomaly investigation | U12: Comfortable investigating anomalies. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U13: SQL-based analysis | U13: Comfortable building SQL-based analyses. | one_to_one / True | SQL activity category differs |
| P30-U14: Large tabular-data trend/anomaly analysis | U14: Experience working with large tabular datasets to detect trends.; U15: Experience working with large tabular datasets to detect anomalies. | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P30-U15: Communicating actionable findings | U16: Experience working with large tabular datasets to communicate findings as actionable recommendations. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U16: Credit-scoring modelling | U17: Exposure to credit scoring modelling concepts. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |

### deepseek-flash/F00036

Delegated source QA compared the full F00036 JD and 17 reviewed logical units. Every model quote occurs in the source. The model has 19 units, including two opening-paragraph umbrella concepts ('analitik data' and 'pemodelan statistik') absent as independent gold units; the paragraph also names ML, while later qualification bullets cover its components. Guideline A1/A4a leaves the opening-paragraph versus redundant-umbrella interpretation unresolved for this specific source, so no gold change or model TP is inferred. The model makes EDA itself an alternative group over Tableau/Power BI/Matplotlib rather than preserving the reviewed simple EDA obligation plus a separate visualization-tool alternative. Its two-year DS-or-similar minimum is present, although it unnecessarily marks this clear source wording needs_review. Preferred database and Hadoop/Spark/cloud context is retained. This case is a semantic comparison failure/uncertainty, not a complete compatible alignment; record it and continue under the separately approved v5 policy. No relevance or evidence label changes.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P09-U01: Bachelor Statistics  /  Mathematics  /  CS  /  Informatics  /  DS | U03: Minimum bachelor's degree (S1) in Statistics, Mathematics, Computer Science, Informatics Engineering, or Data Science | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U02: At least 2-3 years professional DS or similar work | U04: Minimum 2-3 years professional experience as a Data Scientist or similar position | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U03: Python  /  R  /  SQL for data manipulation and analysis | U05: Proficiency in a programming language such as Python, R, or SQL for data manipulation and analysis | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U04: Supervised ML | U06: Strong understanding of supervised learning | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U05: Unsupervised ML | U07: Strong understanding of unsupervised learning | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U06: Deep learning | U08: Strong understanding of deep learning | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U07: pandas  /  scikit-learn  /  TensorFlow  /  PyTorch | U09: Experience using popular tools and libraries such as Pandas, Scikit-learn, TensorFlow, or PyTorch | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U08: Exploratory data analysis | U10: Ability to perform exploratory data analysis using tools such as Tableau, Power BI, or Matplotlib | one_to_one / False | EDA made tool-choice-dependent instead of independent obligation |
| P09-U09: Tableau  /  Power BI  /  Matplotlib | U11: Ability to perform data visualization using tools such as Tableau, Power BI, or Matplotlib | one_to_one / True | Named visualization tool classified concept |
| P09-U10: Descriptive statistics | U12: Solid understanding of descriptive statistics | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U11: Inferential statistics | U13: Solid understanding of inferential statistics | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U12: Research methodology | U14: Solid understanding of research methodology | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U13: Explaining technical analysis to nontechnical stakeholders | U15: Good communication skills to explain technical concepts to non-technical stakeholders | one_to_one / True | Reviewed stakeholder activity versus soft-skill category; source interpretation needs adjudication |
| P09-U14: Database management | U16: Experience with database management | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U15: Hadoop  /  Spark  /  cloud big-data experience | U17: Experience with big data technologies such as Hadoop, Spark, or cloud platforms | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U16: Problem solving | U18: Strong problem-solving skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U17: Attention to detail | U19: Attention to detail in working with data | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| (none) | U01: Deep understanding of data analytics | model_addition / False | Model addition outside reviewed inventory; opening-paragraph umbrella/location applicability needs adjudication where noted in source QA |
| (none) | U02: Deep understanding of statistical modeling | model_addition / False | Model addition outside reviewed inventory; opening-paragraph umbrella/location applicability needs adjudication where noted in source QA |

### deepseek-flash/F00309

Delegated full-source QA: the nine model units cover the nine reviewed logical obligations under the 'Preferred competencies and qualifications' heading. Python/SQL and five independently listed competencies remain separate; the 1-3-year relevant-experience minimum remains qualified at one year; diploma, degree and equivalent practical experience are one OR group with the relevant-field qualifier on every branch. No responsibilities were added as requirements. Exact quotes, preferred status and categories are compatible. This operational check is not an independently human-approved model-to-gold alignment or an extraction F1 receipt.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P26-U01: 1-3 years relevant experience | U01: 1-3 years of relevant experience demonstrating practical application of skills at this seniority level | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U02: Python | U02: Proficiency in Python | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U03: SQL | U03: Proficiency in SQL | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U04: Statistics | U04: Proficiency in statistics | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U05: ML | U05: Proficiency in machine learning | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U06: Experimentation | U06: Proficiency in experimentation | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U07: Visualization | U07: Proficiency in data visualization | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U08: Data storytelling | U08: Proficiency in data storytelling | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U09: Diploma/degree  /  equivalent practical experience in a relevant field | U09: Diploma, degree, or equivalent practical experience in a relevant technical, business, or creative discipline | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |

### deepseek-flash/F00354

Delegated full-source QA: all 10 qualification bullets are represented and every model quote occurs exactly in the F00354 JD; responsibilities are not added. The model has 34 units versus 29 reviewed logical gold units. U22 says generic validation, losing the source/gold 'validation in time-series modelling' scope. U29-U34 split the one reviewed soft-skill interest clause covering LLM/RAG/agents/cloud/containers/CI/CD into six separately scored knowledge/tool units; this is a D-054 strict split/merge relation, not automatic TPs, and needs reference compatibility review rather than gold editing. Documentation and experiment-tracking categories also differ from reviewed units. The first attempt failed schema validation and one repair produced this final draft; both attempts/costs remain recorded. Source completeness alone does not certify compatible unit structure. Record failure and continue under approved v5 policy; no human alignment approval, F1 or winner.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P32-U01: Studying  /  recent graduate in a quantitative field | U01: Currently pursuing or recently completed a degree in Computer Science, Artificial Intelligence, Data Science, Statistics, Mathematics, Operations Research, Engineering or a related quantitative discipline | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U02: Python | U02: Strong Python programming ability | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U03: ML fundamentals | U03: Sound understanding of machine-learning fundamentals | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U04: Feature engineering | U04: Familiarity with feature engineering | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U05: Model evaluation | U05: Familiarity with model evaluation | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U06: Hyperparameter tuning | U06: Familiarity with hyperparameter optimization | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U07: NumPy | U07: Familiarity with libraries such as NumPy | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U08: pandas | U08: Familiarity with libraries such as pandas | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U09: scikit-learn | U09: Familiarity with libraries such as scikit-learn | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U10: XGBoost | U10: Familiarity with libraries such as XGBoost | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U11: Experiment design | U11: Ability to design experiments carefully | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U12: Critical interpretation of results | U12: Ability to interpret results critically | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U13: Git  /  working in an existing codebase | U13: Ability to work with Git or an existing codebase | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U14: Problem solving | U14: Strong problem-solving skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U15: Communication | U15: Strong communication skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U16: Independent work with guidance | U17: Ability to work independently while seeking guidance when appropriate | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U17: Documentation | U16: Strong documentation skills | one_to_one / True | Documentation concept classified soft_skill |
| P32-U18: Genetic algorithms | U18: Knowledge of genetic algorithms | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U19: Evolutionary methods | U19: Knowledge of evolutionary computation | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U20: Optimization | U20: Knowledge of optimization methods | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U21: Time-series modelling | U21: Experience with time-series modelling | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U22: Validation in time-series modelling | U22: Experience with validation | one_to_one / False | Time-series qualifier missing |
| P32-U23: Experiment-tracking frameworks | U23: Experience with experiment-tracking frameworks | one_to_one / True | Unnamed framework classified skill_tool |
| P32-U24: SQL | U24: Familiarity with Structured Query Language | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U25: Data pipelines | U25: Familiarity with data pipelines | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U26: REST APIs | U26: Exposure to Representational State Transfer Application Programming Interfaces | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U27: Lightweight application development | U27: Exposure to lightweight application development | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U28: Production software exposure | U28: Exposure to production-oriented software engineering | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U29: Interest in LLM/RAG/agents/cloud/containers/CI/CD | U29: Interest in large language models; U30: Interest in retrieval-augmented generation; U31: Interest in agentic workflows; U32: Interest in cloud platforms; U33: Interest in containers; U34: Interest in continuous integration / continuous delivery | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |

### deepseek-flash/F00815

Delegated full-source QA of F00815: all nine requirement bullets have mappings and every quote is an exact source substring, but 15 model units do not preserve the 16 reviewed logical obligations. U03 flattens the OpenAI/LangChain/LlamaIndex framework alternatives into one simple item; U12 similarly flattens Pinecone/FAISS/Weaviate vector-database alternatives. U14 merges independently assessable Git, testing and CI/CD requirements. U09/U10 split API building/deployment while dropping the reviewed FastAPI/Flask/equivalent alternative branches and their shared build-and-deploy scope. U13 correctly retains AWS or other cloud as a required alternative despite the intro's AWS preference. U01 category also differs from the reviewed professional AI/ML experience unit. Source inventory success is insufficient; record semantic failure and continue only under the approved v5 policy. No gold/denominator change, human mapping approval, F1 or winner.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P52-U01: Professional AI/ML engineer experience | U01: Proven experience as an AI Engineer or Machine Learning Engineer | one_to_one / True | Role experience classified other |
| P52-U02: Python | U02: Strong programming skills in Python | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U03: OpenAI  /  LangChain  /  LlamaIndex LLM framework | U03: Experience with LLM frameworks (e.g. OpenAI, LangChain, LlamaIndex) | one_to_one / False | LLM alternative group stored simple |
| P52-U04: Prompt engineering | U04: Prompt engineering | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U05: RAG | U05: RAG architectures | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U06: ML fundamentals | U06: Solid understanding of machine learning fundamentals | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U07: Data pipelines | U07: Solid understanding of data pipelines | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U08: ETL | U08: Solid understanding of ETL processes | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U09: FastAPI  /  Flask  /  equivalent API deployment | U09: Experience building APIs (FastAPI, Flask, etc.); U10: Experience deploying APIs (FastAPI, Flask, etc.) | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P52-U10: SQL/PostgreSQL | U11: Familiarity with databases such as SQL (PostgreSQL) | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U11: Pinecone  /  FAISS  /  Weaviate vector technology | U12: Familiarity with Vector databases (e.g. Pinecone, FAISS, Weaviate) | one_to_one / False | Vector alternatives stored simple and classified knowledge_area |
| P52-U12: AWS  /  other cloud platform | U13: Experience with AWS or other cloud platforms | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U13: Git; P52-U14: Testing; P52-U15: CI/CD | U14: Understanding of software engineering best practices (Git, testing, CI/CD) | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P52-U16: Technical bachelor | U15: Bachelor's degree in Computer Science, Engineering, or related field | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |

### deepseek-flash/F00010

Delegated full-source QA: all seven qualification bullets and nine reviewed logical obligations have model units; every source quote is exact, the three role branches each retain the eight-year professional minimum, and required/preferred statuses are appropriate. Yet U04's TensorFlow/PyTorch/scikit-learn branches do not each retain the source's 'strong proficiency in common ML frameworks' qualifier, and U05's AWS/GCP/Azure branches omit 'familiarity with deploying ML models in cloud environments'. U08 is a simple list of Copilot/Cursor/Warp rather than the reviewed one-of alternative group. These structural losses can alter evidence assessment despite the same unit count. Record a semantic failure, no automatic one-to-one TP, gold change, F1 or winner; continue under approved v5 policy.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P02-U01: At least 8 years in AI  /  ML  /  Data Science roles | U01: Minimum 8 years of relevant experience in AI, Machine Learning, or Data Science roles | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U02: English communication | U02: Excellent English communication skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U03: Python | U03: Strong proficiency in Python | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U04: TensorFlow  /  PyTorch  /  scikit-learn  /  similar ML framework | U04: Strong proficiency in common ML frameworks (TensorFlow, PyTorch, scikit-learn, or similar) | one_to_one / True | Shared proficiency present in parent; inherited by branches per active matcher prompt, not automatically a qualifier error |
| P02-U05: Deploying ML models on AWS  /  GCP  /  Azure  /  similar cloud | U05: Familiarity with deploying ML models in cloud environments (AWS, GCP, Azure, or similar) | one_to_one / True | Shared deployment present in parent; inherited by branches, not automatically a qualifier error |
| P02-U06: Communication | U06: Strong communication skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U07: Working with remote cross-functional teams | U07: Ability to work effectively in a remote, cross-functional team | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U08: Copilot  /  Cursor  /  Warp  /  similar AI coding assistant | U08: Experience using AI coding assistants (Copilot, Cursor, Warp) | one_to_one / False | Coding-assistant alternatives stored simple |
| P02-U09: Indonesian citizenship | U09: Indonesian Citizen | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |

### deepseek-flash/F00018

Delegated full-source review of 23 final units versus 24 reviewed logical references. Exact quotes and required/preferred context are retained. U18 combines general cloud-platform experience and the distinct AWS-stack preference; the gold records P04-U18 and P04-U18-AWS are independent reviewed obligations. U18 also classifies the generic cloud-platform requirement as skill_tool rather than gold knowledge_area. U11 retains 'practical experience' in its parent but its NLP/LLM/recommendation branches omit that shared experience qualifier, as do the taxonomies/ontologies and Spark/Dask branches. These differences remain source-semantic/grouping failures under the same branch-qualifier protocol used earlier. No gold correction, semantic TP or human alignment approval is inferred; continue only under the authorized v5 policy.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P04-U01: Standard ML algorithms | U01: Comfortable with standard ML algorithms | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U02: Mathematical basis of ML algorithms | U02: Comfortable with underlying math | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U03: LLMs in production | U03: Strong hands-on experience with LLMs in production | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U04: RAG architecture | U04: Strong hands-on experience with RAG architecture | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U05: Agentic systems | U05: Strong hands-on experience with agentic systems | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U06: AWS Bedrock | U06: AWS Bedrock experience | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U07: Classification | U07: Practical experience with solving classification tasks in general | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U08: Regression | U08: Practical experience with solving regression tasks in general | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U09: Feature engineering | U09: Practical experience with feature engineering | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U10: Practical experience with ML models in production | U10: Practical experience with ML models in production | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U11: Experience with at least one of: NLP  /  LLM  /  Recommendation systems | U11: Practical experience with one or more use cases from the following: NLP, LLMs, and Recommendation engines | one_to_one / True | Parent practical-use-case qualifier is inherited by branches under active matcher prompt |
| P04-U12: Software engineering beyond notebooks, with structured modules | U12: Solid software engineering skills (i.e., ability to produce well-structured modules, not only notebook scripts) | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U13: Python | U13: Python expertise | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U14: Docker | U14: Docker | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U15: English at strong upper-intermediate level | U15: English level: strong upper-intermediate | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U16: Communication | U16: Excellent communication skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U17: Problem solving | U17: Excellent problem-solving skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U18: Practical experience with cloud platforms; P04-U18-AWS: Experience with the AWS cloud stack | U18: Practical experience with cloud platforms (AWS stack preferred, e.g. Amazon SageMaker, ECR, EMR, S3, AWS Lambda) | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P04-U19: Deep learning models | U19: Practical experience with deep learning models | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U20: Taxonomies  /  ontologies | U20: Experience with taxonomies or ontologies | one_to_one / True | Parent experience qualifier is inherited by branches |
| P04-U21: ML pipeline orchestration | U21: Practical experience with machine learning pipelines to orchestrate complicated workflows | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U22: Spark  /  Dask distributed processing | U22: Practical experience with Spark or Dask | one_to_one / True | Parent practical-experience qualifier is inherited by branches |
| P04-U23: Great Expectations | U23: Practical experience with Great Expectations | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |

### gpt-6-luna/F00332

Delegated full-source comparison of all eight qualification clauses and 20 final units against the 16 reviewed logical units. Other considered education disciplines and experience qualifiers are retained. The learning/mastering-technologies/techniques clause is over-split into U08-U11 rather than the reviewed independent learning obligation; trend/anomaly analysis is split into U17/U18 instead of the reviewed joint analytical obligation. Data exploration and actionable findings use other rather than the reviewed knowledge_area; SQL-based analysis uses skill_tool instead of knowledge_area. This is a failed grouping/category observation, not approved alignment or F1. Exact source quotes are valid and plus remains preferred.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P30-U01: Fresh graduate  /  bachelor in quantitative/analytical or other considered discipline | U01: Fresh graduate or bachelor's degree in an analytical or quantitative discipline (e.g., math, statistics, engineering, or computer science); other disciplines will be considered. | one_to_one / True | Education classified other |
| P30-U02: Python | U02: Experience using Python as a statistical computer language. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U03: SQL | U03: Experience using SQL as a statistical computer language. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U04: Microsoft Excel | U04: Experience using MS Excel as a statistical computer language. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U05: Communication | U05: Good communication skills. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U06: Team collaboration | U06: Ability to work collaboratively in a team. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U07: Problem solving | U07: Excellent problem-solving skills. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U08: Learning new techniques | U08: Drive to learn new technologies.; U09: Drive to learn new techniques.; U10: Drive to master new technologies.; U11: Drive to master new techniques. | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P30-U09: Independent learning | U12: Willingness to learn new skills independently. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U10: Project ownership | U13: Strong sense of project ownership. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U11: Data exploration | U14: Comfortable exploring data. | one_to_one / True | Concept classified other |
| P30-U12: Anomaly investigation | U15: Comfortable investigating anomalies. | one_to_one / True | Concept classified other |
| P30-U13: SQL-based analysis | U16: Comfortable building SQL-based analyses. | one_to_one / True | SQL activity category differs |
| P30-U14: Large tabular-data trend/anomaly analysis | U17: Experience working with large tabular datasets to detect trends.; U18: Experience working with large tabular datasets to detect anomalies. | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P30-U15: Communicating actionable findings | U19: Experience working with large tabular datasets to communicate findings as actionable recommendations. | one_to_one / True | Actionable activity classified other |
| P30-U16: Credit-scoring modelling | U20: Exposure to credit scoring modelling concepts. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |

### gpt-6-luna/F00036

Full Indonesian source and 17 logical references reviewed against 20 final units. All quotes are exact. Opening paragraph analytics/statistical-modelling and work-location units require the same unresolved umbrella/intro interpretation retained for DeepSeek; no gold mutation or TP is inferred. U11 makes EDA contingent on Tableau/Power BI/Matplotlib even though the source and reviewed reference preserve EDA separately from the visualization-tool alternative; this attaches an inappropriate tool qualifier to EDA. U16 represents technical-to-nontechnical explanation as soft_skill rather than the reviewed other obligation. Preferred database/big-data scope and explicit two-year minimum are retained. Grouping/qualifier comparison fails; candidate alignment stays pending.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P09-U01: Bachelor Statistics  /  Mathematics  /  CS  /  Informatics  /  DS | U07: Bachelor's degree (S1) in one of the listed fields. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U02: At least 2-3 years professional DS or similar work | U08: At least 2–3 years of professional experience as a Data Scientist or in a similar position. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U03: Python  /  R  /  SQL for data manipulation and analysis | U09: Ability to manipulate and analyze data using one of the listed programming languages. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U04: Supervised ML | U03: Strong understanding of supervised learning. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U05: Unsupervised ML | U04: Strong understanding of unsupervised learning. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U06: Deep learning | U05: Strong understanding of deep learning. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U07: pandas  /  scikit-learn  /  TensorFlow  /  PyTorch | U10: Experience using one of the listed tools or libraries. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U08: Exploratory data analysis | U11: Ability to perform exploratory data analysis using one of the listed tools. | one_to_one / False | EDA made tool-choice-dependent |
| P09-U09: Tableau  /  Power BI  /  Matplotlib | U12: Ability to perform data visualization using one of the listed tools. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U10: Descriptive statistics | U13: Understanding of descriptive statistics. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U11: Inferential statistics | U14: Understanding of inferential statistics. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U12: Research methodology | U15: Understanding of research methodology. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U13: Explaining technical analysis to nontechnical stakeholders | U16: Good communication skills to explain technical concepts to non-technical stakeholders. | one_to_one / True | Reviewed stakeholder activity versus soft-skill category; adjudication needed |
| P09-U14: Database management | U17: Experience with database management. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U15: Hadoop  /  Spark  /  cloud big-data experience | U18: Experience with one of the listed big data technologies. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U16: Problem solving | U19: Strong problem-solving ability when working with data. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U17: Attention to detail | U20: Attention to detail when working with data. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| (none) | U01: Work full-time in Bandung, West Java. | model_addition / False | Model addition outside reviewed inventory; opening-paragraph umbrella/location applicability needs adjudication where noted in source QA |
| (none) | U02: Understanding of data analytics. | model_addition / False | Model addition outside reviewed inventory; opening-paragraph umbrella/location applicability needs adjudication where noted in source QA |
| (none) | U06: Understanding of statistical modeling. | model_addition / False | Model addition outside reviewed inventory; opening-paragraph umbrella/location applicability needs adjudication where noted in source QA |

### gpt-6-luna/F00309

All three preferred-qualification clauses and nine independent logical obligations checked against the complete source. Exact quotes, one-to-three-year minimum and education/equivalent-practical-experience alternatives are retained. Every output unit is required although the entire source section is explicitly Preferred competencies and qualifications and all nine reviewed references are preferred. This changes eligibility/scoring meaning and fails importance. The education composite also uses other rather than reviewed education; its branch expansion preserves the alternatives and is not counted as extra denominator units. No gold update or approved candidate alignment.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P26-U01: 1-3 years relevant experience | U01: 1–3 years of relevant experience demonstrating practical application of skills at this seniority level | one_to_one / False | Explicit preferred section changed to required |
| P26-U02: Python | U02: Proficiency in Python | one_to_one / False | Explicit preferred section changed to required |
| P26-U03: SQL | U03: Proficiency in SQL | one_to_one / False | Explicit preferred section changed to required |
| P26-U04: Statistics | U04: Proficiency in statistics | one_to_one / False | Explicit preferred section changed to required |
| P26-U05: ML | U05: Proficiency in machine learning | one_to_one / False | Explicit preferred section changed to required |
| P26-U06: Experimentation | U06: Proficiency in experimentation | one_to_one / False | Explicit preferred section changed to required |
| P26-U07: Visualization | U07: Proficiency in data visualization | one_to_one / False | Explicit preferred section changed to required |
| P26-U08: Data storytelling | U08: Proficiency in data storytelling | one_to_one / False | Explicit preferred section changed to required |
| P26-U09: Diploma/degree  /  equivalent practical experience in a relevant field | U09: A diploma, degree, or equivalent practical experience in a relevant technical, business, or creative discipline | one_to_one / False | Preferred changed required and education classified other |

### gpt-6-luna/F00354

Complete ten-clause qualification source and 29 reviewed logical units inspected against 34 outputs. Exact quotes, education alternatives, named libraries and required context are retained. The interest clause is split into six technical scored obligations U29-U34 rather than the reviewed single interest soft-skill; it does not establish hands-on proficiency. Generic experiment-tracking frameworks/cloud platforms/containers are labeled skill_tool without a named product. U16 documentation uses other rather than knowledge_area; U22 validation loses the reviewed time-series context. All-source coverage is not semantic alignment. Retain grouping/category/qualifier failure; no gold edit or F1 approval.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P32-U01: Studying  /  recent graduate in a quantitative field | U01: Currently pursuing or recently completed a degree in one of the listed or related quantitative disciplines. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U02: Python | U02: Strong Python programming ability. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U03: ML fundamentals | U03: A sound understanding of machine-learning fundamentals. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U04: Feature engineering | U04: Familiarity with feature engineering. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U05: Model evaluation | U05: Familiarity with model evaluation. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U06: Hyperparameter tuning | U06: Familiarity with hyperparameter optimization. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U07: NumPy | U07: Familiarity with NumPy. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U08: pandas | U08: Familiarity with pandas. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U09: scikit-learn | U09: Familiarity with scikit-learn. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U10: XGBoost | U10: Familiarity with XGBoost. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U11: Experiment design | U11: Ability to design experiments carefully. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U12: Critical interpretation of results | U12: Ability to interpret results critically. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U13: Git  /  working in an existing codebase | U13: Ability to work with Git or an existing codebase. | one_to_one / True | Git/codebase group classified other |
| P32-U14: Problem solving | U14: Strong problem-solving skills. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U15: Communication | U15: Strong communication skills. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U16: Independent work with guidance | U17: Ability to work independently while seeking guidance when appropriate. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U17: Documentation | U16: Strong documentation skills. | one_to_one / True | Documentation classified other |
| P32-U18: Genetic algorithms | U18: Knowledge of genetic algorithms. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U19: Evolutionary methods | U19: Knowledge of evolutionary computation. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U20: Optimization | U20: Knowledge of optimization methods. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U21: Time-series modelling | U21: Experience with time-series modelling. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U22: Validation in time-series modelling | U22: Experience with validation. | one_to_one / False | Time-series qualifier missing |
| P32-U23: Experiment-tracking frameworks | U23: Experience with experiment-tracking frameworks. | one_to_one / True | Unnamed framework classified skill_tool |
| P32-U24: SQL | U24: Familiarity with Structured Query Language (SQL). | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U25: Data pipelines | U25: Familiarity with data pipelines. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U26: REST APIs | U26: Exposure to Representational State Transfer (REST) APIs. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U27: Lightweight application development | U27: Exposure to lightweight application development. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U28: Production software exposure | U28: Exposure to production-oriented software engineering. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U29: Interest in LLM/RAG/agents/cloud/containers/CI/CD | U29: Interest in large language models.; U30: Interest in retrieval-augmented generation.; U31: Interest in agentic workflows.; U32: Interest in cloud platforms.; U33: Interest in containers.; U34: Interest in continuous integration / continuous delivery practices. | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |

### gpt-6-luna/F00815

All nine requirement bullets reviewed against 16 logical references and 17 outputs. Quotes and shared experience/understanding qualifiers are retained. The reviewed API building/deployment obligation is split into U09 and U10, with repeated FastAPI/Flask alternatives; under D-054 this is a split relation, not two TPs. The source example-list etc permits other API frameworks, while explicit branches list only FastAPI/Flask: unresolved alternative coverage, not a new gold decision. U01 professional role experience is other instead of reviewed knowledge_area. LLM frameworks, prompt engineering, RAG, SQL/vector technology, cloud, Git/testing/CI/CD and education clauses are present; no source duty-only addition. Retain failed/uncertain semantics and pending alignment.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P52-U01: Professional AI/ML engineer experience | U01: Proven experience as an AI Engineer or Machine Learning Engineer | one_to_one / True | Role experience classified other; gold stored simple whereas model uses OR |
| P52-U02: Python | U02: Strong programming skills in Python | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U03: OpenAI  /  LangChain  /  LlamaIndex LLM framework | U03: Experience with an LLM framework | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U04: Prompt engineering | U04: Experience with prompt engineering | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U05: RAG | U05: Experience with RAG architectures | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U06: ML fundamentals | U06: Solid understanding of machine learning fundamentals | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U07: Data pipelines | U07: Solid understanding of data pipelines | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U08: ETL | U08: Solid understanding of ETL processes | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U09: FastAPI  /  Flask  /  equivalent API deployment | U09: Experience building APIs using an API framework; U10: Experience deploying APIs using an API framework | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P52-U10: SQL/PostgreSQL | U11: Familiarity with SQL databases (PostgreSQL) | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U11: Pinecone  /  FAISS  /  Weaviate vector technology | U12: Familiarity with a vector database | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U12: AWS  /  other cloud platform | U13: Experience with AWS or another cloud platform | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U13: Git | U14: Understanding of software engineering best practices involving Git | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U14: Testing | U15: Understanding of software engineering best practices involving testing | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U15: CI/CD | U16: Understanding of software engineering best practices involving CI/CD | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U16: Technical bachelor | U17: Bachelor's degree in Computer Science, Engineering, or a related field | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |

### gpt-6-luna/F00010

All seven qualifications and nine logical obligations reviewed; exact quotes and source importance are retained. The eight-year minimum is correctly present in every AI/ML/DS branch (parent min_years is null, not a lost branch duration). ML-framework and cloud-deployment alternatives retain proficiency/deployment and similar-platform routes. U08 leaves the named AI-assistant example list as an unresolved simple composite with needs_review instead of the reviewed alternative group. This is a guarded representation, but not a compatible approved alternative alignment; grouping remains uncertain and score-hold consequences remain visible. No responsibilities, duration, citizenship or English qualification invented; no gold edits or candidate F1.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P02-U01: At least 8 years in AI  /  ML  /  Data Science roles | U01: At least 8 years of relevant experience in an AI role. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U02: English communication | U02: Excellent English communication skills. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U03: Python | U03: Strong proficiency in Python. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U04: TensorFlow  /  PyTorch  /  scikit-learn  /  similar ML framework | U04: Strong proficiency in a common ML framework. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U05: Deploying ML models on AWS  /  GCP  /  Azure  /  similar cloud | U05: Familiarity with deploying ML models in cloud environments using AWS, GCP, Azure, or a similar cloud platform. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U06: Communication | U06: Strong communication skills. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U07: Working with remote cross-functional teams | U07: Ability to work effectively in a remote, cross-functional team. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U08: Copilot  /  Cursor  /  Warp  /  similar AI coding assistant | U08: Experience using AI coding assistants, including Copilot, Cursor, and Warp; the required selection among the named assistants is unclear. | one_to_one / False | Unresolved coding-assistant composite |
| P02-U09: Indonesian citizenship | U09: Indonesian citizenship. | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |

### gpt-6-luna/F00018

All ten required and five plus-section clauses reviewed against 24 logical references and 23 outputs. Exact quotes and preferred scopes remain. U01 strengthens Comfortable with standard ML algorithms into Hands-on experience, which the quoted source does not require. U18 merges generic practical cloud experience and a distinct AWS-stack preference, whereas the reviewed gold preserves two independent obligations; it also labels generic cloud platforms skill_tool. U11 preserves the one-or-more use-case wording but does not expose assessable branches, leaving a composite to review. Classification/regression, production, English, named tools and taxonomies/Spark alternatives are present. This is a qualifier/grouping/coverage failure, not candidate alignment approval.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P04-U01: Standard ML algorithms | U01: Hands-on experience with standard machine learning algorithms | one_to_one / False | Comfortable understanding strengthened to hands-on experience |
| P04-U02: Mathematical basis of ML algorithms | U02: Comfortable with the underlying mathematics of standard machine learning algorithms | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U03: LLMs in production | U03: Strong hands-on experience with LLMs in production | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U04: RAG architecture | U04: Strong hands-on experience with RAG architecture | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U05: Agentic systems | U05: Strong hands-on experience with agentic systems | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U06: AWS Bedrock | U06: Experience with AWS Bedrock | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U07: Classification | U07: Practical experience solving classification tasks | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U08: Regression | U08: Practical experience solving regression tasks | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U09: Feature engineering | U09: Practical experience with feature engineering | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U10: Practical experience with ML models in production | U10: Practical experience with machine learning models in production | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U11: Experience with at least one of: NLP  /  LLM  /  Recommendation systems | U11: Practical experience with one or more use cases among NLP, LLMs, and recommendation engines | one_to_one / False | One-or-more alternative stored simple |
| P04-U12: Software engineering beyond notebooks, with structured modules | U12: Solid software engineering skills, including producing well-structured modules rather than only notebook scripts | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U13: Python | U13: Expertise in Python | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U14: Docker | U14: Docker proficiency | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U15: English at strong upper-intermediate level | U15: Strong upper-intermediate English proficiency | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U16: Communication | U16: Excellent communication skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U17: Problem solving | U17: Excellent problem-solving skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U18: Practical experience with cloud platforms; P04-U18-AWS: Experience with the AWS cloud stack | U18: Practical experience with cloud platforms, particularly the AWS stack; examples include Amazon SageMaker, ECR, EMR, S3, and AWS Lambda | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P04-U19: Deep learning models | U19: Practical experience with deep learning models | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U20: Taxonomies  /  ontologies | U20: Experience with taxonomies or ontologies | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U21: ML pipeline orchestration | U21: Practical experience with machine learning pipelines for orchestrating complicated workflows | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U22: Spark  /  Dask distributed processing | U22: Practical experience with Spark or Dask | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U23: Great Expectations | U23: Practical experience with Great Expectations | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |

### gemini-3.5-flash-lite/F00332

Complete eight-clause source reviewed against 16 logical gold requirements and 19 outputs. Exact quotes, Python/SQL/Excel AND units, preferred credit-scoring exposure and joint trend/anomaly obligation are retained. U01-U04 incorrectly turn the education example disciplines into four independent required degrees. The fresh-graduate route and other-disciplines-considered route are not represented. This loses explicit OR/admission structure and inflates the denominator. U16 SQL-based analysis is skill_tool rather than reviewed knowledge_area; U18 actionable communication is other and loses the shared large-tabular-data experience context. No gold changes or candidate F1 approval; retain semantic failure.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P30-U01: Fresh graduate  /  bachelor in quantitative/analytical or other considered discipline | U01: Bachelor's degree in math; U02: Bachelor's degree in statistics; U03: Bachelor's degree in engineering; U04: Bachelor's degree in computer science | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P30-U02: Python | U05: Experience using Python | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U03: SQL | U06: Experience using SQL | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U04: Microsoft Excel | U07: Experience using MS Excel | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U05: Communication | U08: Good communication skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U06: Team collaboration | U09: Ability to work collaboratively in a team | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U07: Problem solving | U10: Excellent problem-solving skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U08: Learning new techniques | U11: Drive to learn and master new technologies and techniques | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U09: Independent learning | U12: Willingness to learn new skills independently | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U10: Project ownership | U13: Strong sense of project ownership | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U11: Data exploration | U14: Comfortable exploring data | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U12: Anomaly investigation | U15: Investigating anomalies | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U13: SQL-based analysis | U16: Building SQL-based analyses | one_to_one / True | SQL activity category differs |
| P30-U14: Large tabular-data trend/anomaly analysis | U17: Experience working with large tabular datasets to detect trends and anomalies | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U15: Communicating actionable findings | U18: Communicate findings as actionable recommendations | one_to_one / True | Actionable activity classified other |
| P30-U16: Credit-scoring modelling | U19: Exposure to credit scoring modelling concepts | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |

### gemini-3.5-flash-lite/F00036

All ten Persyaratan clauses checked against 17 logical references and 14 outputs; quotes and required/preferred scope are valid. U13 converts independent database-management AND big-data experience into one OR group containing database management/Hadoop/Spark/cloud, and miscategorizes generic database management as a tool. U08 merges EDA and visualization/tool requirements, whereas references retain EDA independently. U14 merges independently reviewed problem-solving and attention-to-detail obligations. Python/R/SQL and library/tool branches are bare names rather than assessable shared proficiency/analysis/experience statements; the source data-manipulation/analysis qualifier is lost. Education OR and two-year minimum are retained. These are substantive grouping/coverage/qualifier failures; no candidate alignment approval.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P09-U01: Bachelor Statistics  /  Mathematics  /  CS  /  Informatics  /  DS | U01: Bachelor's degree in Statistics, Mathematics, Computer Science, Informatics Engineering, or Data Science | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U02: At least 2-3 years professional DS or similar work | U02: 2 to 3 years of professional experience as a Data Scientist or in a similar position | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U03: Python  /  R  /  SQL for data manipulation and analysis | U03: Proficiency in Python programming language | one_to_one / False | Parent singles out Python and omits data-manipulation/analysis qualifier; inspect complete source-grounded unit |
| P09-U04: Supervised ML | U04: Understanding of supervised learning | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U05: Unsupervised ML | U05: Understanding of unsupervised learning | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U06: Deep learning | U06: Understanding of deep learning | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U07: pandas  /  scikit-learn  /  TensorFlow  /  PyTorch | U07: Experience with Pandas | one_to_one / True | Parent singles out Pandas although explicit OR branches include other libraries; shared experience is inherited from parent |
| P09-U08: Exploratory data analysis; P09-U09: Tableau  /  Power BI  /  Matplotlib | U08: Ability to perform exploratory data analysis and data visualization using Tableau | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P09-U10: Descriptive statistics | U09: Solid understanding of descriptive statistics | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U11: Inferential statistics | U10: Solid understanding of inferential statistics | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U12: Research methodology | U11: Solid understanding of research methodology | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U13: Explaining technical analysis to nontechnical stakeholders | U12: Good communication skills to explain technical concepts to non-technical stakeholders | one_to_one / True | Reviewed stakeholder activity versus soft-skill category; adjudication needed |
| P09-U14: Database management; P09-U15: Hadoop  /  Spark  /  cloud big-data experience | U13: Experience with database management | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P09-U16: Problem solving; P09-U17: Attention to detail | U14: Strong problem-solving skills and attention to detail in working with data | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |

### gemini-3.5-flash-lite/F00309

All three source clauses and nine logical obligations checked. Every unit correctly remains preferred, one-to-three years is retained, and the diploma/degree/equivalent-practical-experience OR group preserves shared relevant discipline context. No AND/OR grouping loss observed. However U07 data visualization and U08 data storytelling are classified skill_tool, despite being unnamed concepts/methods and reviewed knowledge_area under Rule3. The uncertain grouping/representation flag denotes this logical-type compatibility issue, not an invented conjunction error. Exact quotes and proficiency qualifiers pass; source-based taxonomy compatibility must be resolved before approved candidate alignment/F1. No gold amendment.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P26-U01: 1-3 years relevant experience | U01: 1-3 years of relevant experience demonstrating practical application of skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U02: Python | U02: Proficiency in Python | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U03: SQL | U03: Proficiency in SQL | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U04: Statistics | U04: Proficiency in statistics | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U05: ML | U05: Proficiency in machine learning | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U06: Experimentation | U06: Proficiency in experimentation | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U07: Visualization | U07: Proficiency in data visualization | one_to_one / True | Unnamed visualization concept classified skill_tool |
| P26-U08: Data storytelling | U08: Proficiency in data storytelling | one_to_one / True | Unnamed storytelling concept classified skill_tool |
| P26-U09: Diploma/degree  /  equivalent practical experience in a relevant field | U09: Diploma, degree, or equivalent practical experience in a relevant technical, business, or creative discipline | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |

### gemini-3.5-flash-lite/F00354

All ten qualification bullets reviewed against 29 logical references and 38 outputs. Source education OR is turned into eight independent required-degree units U01-U08. Four reviewed named-library requirements are collapsed into one OR group U14 with invented or wording. The uns softened later bullets (genetic algorithms through LLM/agent/cloud interest) are preferred in U22-U38 although the source contains no preferred heading/softener there and reviewed importance is required. The one interest soft-skill becomes six technical/tool units; generic experiment-tracking/cloud/container and documentation types conflict with Rule3/reference, and validation loses time-series scope. Exact quotes pass but source grouping/importance and denominator meaning do not. No silent gold correction or candidate F1.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P32-U01: Studying  /  recent graduate in a quantitative field | U01: Currently pursuing or recently completed a degree in Computer Science; U02: Currently pursuing or recently completed a degree in Artificial Intelligence; U03: Currently pursuing or recently completed a degree in Data Science; U04: Currently pursuing or recently completed a degree in Statistics; U05: Currently pursuing or recently completed a degree in Mathematics; U06: Currently pursuing or recently completed a degree in Operations Research; U07: Currently pursuing or recently completed a degree in Engineering; U08: Currently pursuing or recently completed a degree in a related quantitative discipline | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P32-U02: Python | U09: Strong Python programming ability | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U03: ML fundamentals | U10: Sound understanding of machine-learning fundamentals | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U04: Feature engineering | U11: Familiarity with feature engineering | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U05: Model evaluation | U12: Familiarity with model evaluation | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U06: Hyperparameter tuning | U13: Familiarity with hyperparameter optimization | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U07: NumPy; P32-U08: pandas; P32-U09: scikit-learn; P32-U10: XGBoost | U14: Familiarity with libraries such as NumPy, pandas, scikit-learn or XGBoost | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P32-U11: Experiment design | U15: Ability to design experiments carefully | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U12: Critical interpretation of results | U16: Ability to interpret results critically | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U13: Git  /  working in an existing codebase | U17: Ability to work with Git or an existing codebase | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U14: Problem solving | U18: Strong problem-solving skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U15: Communication | U19: Strong communication skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U16: Independent work with guidance | U21: Ability to work independently while seeking guidance when appropriate | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U17: Documentation | U20: Strong documentation skills | one_to_one / True | Documentation concept classified soft_skill |
| P32-U18: Genetic algorithms | U22: Knowledge of genetic algorithms | one_to_one / False | Required source changed preferred |
| P32-U19: Evolutionary methods | U23: Knowledge of evolutionary computation | one_to_one / False | Required source changed preferred |
| P32-U20: Optimization | U24: Knowledge of optimization methods | one_to_one / False | Required source changed preferred |
| P32-U21: Time-series modelling | U25: Experience with time-series modelling | one_to_one / False | Required source changed preferred |
| P32-U22: Validation in time-series modelling | U26: Experience with validation | one_to_one / False | Required changed preferred and time-series qualifier absent |
| P32-U23: Experiment-tracking frameworks | U27: Experience with experiment-tracking frameworks | one_to_one / False | Required changed preferred; unnamed framework classified skill_tool |
| P32-U24: SQL | U28: Familiarity with Structured Query Language | one_to_one / False | Required source changed preferred |
| P32-U25: Data pipelines | U29: Familiarity with data pipelines | one_to_one / False | Required source changed preferred |
| P32-U26: REST APIs | U30: Exposure to Representational State Transfer Application Programming Interfaces | one_to_one / False | Required source changed preferred |
| P32-U27: Lightweight application development | U31: Exposure to lightweight application development | one_to_one / False | Required source changed preferred |
| P32-U28: Production software exposure | U32: Exposure to production-oriented software engineering | one_to_one / False | Required source changed preferred |
| P32-U29: Interest in LLM/RAG/agents/cloud/containers/CI/CD | U33: Interest in large language models; U34: Interest in retrieval-augmented generation; U35: Interest in agentic workflows; U36: Interest in cloud platforms; U37: Interest in containers; U38: Interest in continuous integration / continuous delivery | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |

### gemini-3.5-flash-lite/F00815

Process failure retained; no final draft, no invented alignment.

### gemini-3.5-flash-lite/F00010

All seven qualification clauses checked; nine units. Minimum eight years remains, but its AI/ML/Data Science OR route is stored as one qualified unit without assessable alternative branches. U04 framework branches lose strong proficiency; U05 AWS/GCP/Azure branches lose familiarity with ML deployment. Parent text alone does not preserve these qualifiers in independently matched branches. Similar framework/cloud options and preferred coding assistants remain represented. Citizenship and importance pass. No gold or approved alignment change.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P02-U01: At least 8 years in AI  /  ML  /  Data Science roles | U01: Minimum 8 years of relevant experience in AI, Machine Learning, or Data Science roles | one_to_one / False | Role alternatives stored without branches |
| P02-U02: English communication | U02: Excellent English communication skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U03: Python | U03: Strong proficiency in Python | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U04: TensorFlow  /  PyTorch  /  scikit-learn  /  similar ML framework | U04: Proficiency in common ML frameworks such as TensorFlow, PyTorch, scikit-learn, or similar | one_to_one / True | Parent proficiency applies to branches; ordinary depth word is not a separate obligation under D-035/D-042 |
| P02-U05: Deploying ML models on AWS  /  GCP  /  Azure  /  similar cloud | U05: Familiarity with deploying ML models in cloud environments such as AWS, GCP, Azure, or similar | one_to_one / True | Parent deployment scope applies to branches; no independent bare-cloud matching is authorized |
| P02-U06: Communication | U06: Strong communication skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U07: Working with remote cross-functional teams | U07: Ability to work effectively in a remote, cross-functional team | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U08: Copilot  /  Cursor  /  Warp  /  similar AI coding assistant | U08: Experience using AI coding assistants such as Copilot, Cursor, or Warp | one_to_one / True | Reviewed similar-assistant route versus source example-list interpretation needs adjudication |
| P02-U09: Indonesian citizenship | U09: Indonesian Citizen | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |

### gemini-3.5-flash-lite/F00018

Full required and plus sections checked; 16 units. The five plus-section clauses are absent: general cloud/AWS-stack preference, deep learning, taxonomies/ontologies, pipeline orchestration, and big-data/data-quality tools. Required classification and regression are merged despite independently assessable tasks. U10 bare NLP/LLM/recommendation branches lose practical-use-case experience; LLM/RAG/agentic units lose strong qualifier, and problem-solving loses excellent. Required/preferred values on extracted units are correct, but missing preferred obligations remain a coverage failure. No gold change.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P04-U01: Standard ML algorithms | U01: Comfortable with standard ML algorithms | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U02: Mathematical basis of ML algorithms | U02: Comfortable with underlying math of ML | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U03: LLMs in production | U03: Hands-on experience with LLMs in production | one_to_one / True | Hands-on production retained; ordinary strong depth word is not a separate obligation |
| P04-U04: RAG architecture | U04: Hands-on experience with RAG architecture | one_to_one / True | Hands-on RAG retained; ordinary strong depth word is not a separate obligation |
| P04-U05: Agentic systems | U05: Hands-on experience with agentic systems | one_to_one / True | Hands-on agentic retained; ordinary strong depth word is not a separate obligation |
| P04-U06: AWS Bedrock | U06: AWS Bedrock experience | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U07: Classification; P04-U08: Regression | U07: Practical experience with solving classification and regression tasks in general | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P04-U09: Feature engineering | U08: Practical experience with feature engineering | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U10: Practical experience with ML models in production | U09: Practical experience with ML models in production | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U11: Experience with at least one of: NLP  /  LLM  /  Recommendation systems | U10: Practical experience with use cases from NLP, LLMs, or Recommendation engines | one_to_one / True | Parent practical-use-case qualifier is inherited by branches |
| P04-U12: Software engineering beyond notebooks, with structured modules | U11: Solid software engineering skills to produce well-structured modules | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U13: Python | U12: Python expertise | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U14: Docker | U13: Docker experience | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U15: English at strong upper-intermediate level | U14: English level - strong upper-intermediate | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U16: Communication | U15: Excellent communication skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U17: Problem solving | U16: Problem-solving skills | one_to_one / True | Ordinary excellent depth word is not a separate obligation |
| P04-U18: Practical experience with cloud platforms | (none) | model_omission / False | Reviewed source obligation omitted from final model draft |
| P04-U19: Deep learning models | (none) | model_omission / False | Reviewed source obligation omitted from final model draft |
| P04-U20: Taxonomies  /  ontologies | (none) | model_omission / False | Reviewed source obligation omitted from final model draft |
| P04-U21: ML pipeline orchestration | (none) | model_omission / False | Reviewed source obligation omitted from final model draft |
| P04-U22: Spark  /  Dask distributed processing | (none) | model_omission / False | Reviewed source obligation omitted from final model draft |
| P04-U23: Great Expectations | (none) | model_omission / False | Reviewed source obligation omitted from final model draft |
| P04-U18-AWS: Experience with the AWS cloud stack | (none) | model_omission / False | Reviewed source obligation omitted from final model draft |

### claude-haiku-4.5/F00332

All eight source qualification bullets checked; 13 units. U01 source quote includes Fresh Graduate OR degree, but normalized requirement loses the fresh-graduate route and has no alternative branches. U11 merges exploration, anomaly investigation and SQL-based analyses; U12 merges large-tabular trend/anomaly work with actionable recommendations and incorrectly uses experience_duration despite no numerical duration. Python/SQL/Excel are separate and preferred credit-scoring exposure is correct. Exact quotes do not rescue lost normalized alternatives. Candidate alignment remains pending; no gold change.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P30-U01: Fresh graduate  /  bachelor in quantitative/analytical or other considered discipline | U01: Bachelor's degree in an analytical or quantitative discipline such as mathematics, statistics, engineering, or computer science; other disciplines will be considered | one_to_one / False | Fresh-graduate alternative missing |
| P30-U02: Python | U02: Experience using Python | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U03: SQL | U03: Experience using SQL | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U04: Microsoft Excel | U04: Experience using MS Excel | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U05: Communication | U05: Good communication skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U06: Team collaboration | U06: Ability to work collaboratively in a team | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U07: Problem solving | U07: Excellent problem-solving skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U08: Learning new techniques | U08: Drive to learn and master new technologies and techniques | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U09: Independent learning | U09: Willingness to learn new skills independently | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U10: Project ownership | U10: Strong sense of project ownership | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P30-U11: Data exploration; P30-U12: Anomaly investigation; P30-U13: SQL-based analysis | U11: Comfortable exploring data, investigating anomalies, and building SQL-based analyses | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P30-U14: Large tabular-data trend/anomaly analysis; P30-U15: Communicating actionable findings | U12: Experience working with large tabular datasets to detect trends and anomalies and communicate findings as actionable recommendations | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P30-U16: Credit-scoring modelling | U13: Exposure to credit scoring modelling concepts | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |

### claude-haiku-4.5/F00036

All ten Persyaratan clauses and introductory work-location context checked; 18 units. Python/R/SQL, library alternatives and visualization-tool alternatives are converted into independent required AND units. Education and DS-or-similar experience routes have no alternative branches. ML concepts, descriptive/inferential statistics/research methodology, and problem-solving/detail remain merged. Libraries gain data-analysis qualification not explicitly stated in their source clause. Bandung full-time introductory context is added as a required location unit outside the reviewed qualification scope; its inclusion/importance needs alignment rather than silently altering the reference. The preferred big-data clause retains preferred importance but merges database AND technology alternatives. Exact quotes pass; no gold change.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P09-U01: Bachelor Statistics  /  Mathematics  /  CS  /  Informatics  /  DS | U01: Bachelor's degree in Statistics, Mathematics, Computer Science, Information Technology, or Data Science | one_to_one / False | Degree OR stored simple; Informatics translated IT rather than Informatics |
| P09-U02: At least 2-3 years professional DS or similar work | U02: 2-3 years of professional experience as a Data Scientist or similar position | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P09-U03: Python  /  R  /  SQL for data manipulation and analysis | U03: Proficiency in Python for data manipulation and analysis; U04: Proficiency in R for data manipulation and analysis; U05: Proficiency in SQL for data manipulation and analysis | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P09-U04: Supervised ML; P09-U05: Unsupervised ML; P09-U06: Deep learning | U06: Strong understanding of machine learning concepts including supervised learning, unsupervised learning, and deep learning | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P09-U07: pandas  /  scikit-learn  /  TensorFlow  /  PyTorch | U07: Experience using Pandas for data analysis; U08: Experience using Scikit-learn for data analysis; U09: Experience using TensorFlow for data analysis; U10: Experience using PyTorch for data analysis | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P09-U08: Exploratory data analysis; P09-U09: Tableau  /  Power BI  /  Matplotlib | U11: Ability to perform exploratory data analysis and data visualization using Tableau; U12: Ability to perform exploratory data analysis and data visualization using Power BI; U13: Ability to perform exploratory data analysis and data visualization using Matplotlib | complex_pending / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P09-U10: Descriptive statistics; P09-U11: Inferential statistics; P09-U12: Research methodology | U14: Solid understanding of descriptive and inferential statistics and research methodology | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P09-U13: Explaining technical analysis to nontechnical stakeholders | U15: Good communication skills to explain technical concepts to non-technical stakeholders | one_to_one / True | Reviewed stakeholder activity versus soft-skill category; adjudication needed |
| P09-U14: Database management; P09-U15: Hadoop  /  Spark  /  cloud big-data experience | U16: Experience with database management and big data technologies such as Hadoop, Spark, or cloud platforms | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P09-U16: Problem solving; P09-U17: Attention to detail | U17: Strong problem-solving ability and attention to detail when working with data | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| (none) | U18: Work full-time in Bandung, West Java | model_addition / False | Model addition outside reviewed inventory; opening-paragraph umbrella/location applicability needs adjudication where noted in source QA |

### claude-haiku-4.5/F00309

All three preferred qualification clauses checked; nine units. Python/SQL and five knowledge domains are atomized with correct proficiency and concept/tool categories; the experience minimum is one year and every unit is preferred. U09 preserves diploma/degree/equivalent-practical-experience wording and shared discipline in text, but stores explicit alternatives as a simple education unit without assessable OR branches. This logical representation differs from the approved alternative group and needs alignment; exact quotes and retained qualifiers pass. No gold change or automatic F1.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P26-U01: 1-3 years relevant experience | U01: 1-3 years of relevant experience demonstrating practical application of skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U02: Python | U02: Proficiency in Python | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U03: SQL | U03: Proficiency in SQL | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U04: Statistics | U04: Proficiency in statistics | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U05: ML | U05: Proficiency in machine learning | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U06: Experimentation | U06: Proficiency in experimentation | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U07: Visualization | U07: Proficiency in data visualization | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U08: Data storytelling | U08: Proficiency in data storytelling | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P26-U09: Diploma/degree  /  equivalent practical experience in a relevant field | U09: Diploma, degree, or equivalent practical experience in a relevant technical, business, or creative discipline | one_to_one / False | Equivalent-experience OR stored simple without assessable branches |

### claude-haiku-4.5/F00354

All ten success-qualification clauses checked; 34 units. U18-U34 are preferred without any source softener or preferred section; these requirements should retain required importance under Rule2. Education and Git-or-existing-codebase explicit OR routes are simple units without alternative branches. Interest is split into six technical requirements despite reviewed single interest soft-skill unit; experiment design/critical interpretation are miscategorized soft_skill and unnamed experiment-tracking frameworks/containers as skill_tool. Libraries are strengthened from familiarity to experience, and validation loses time-series context. Quotes and clause-level representation pass; they do not certify semantic completeness. No gold change.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P32-U01: Studying  /  recent graduate in a quantitative field | U01: Currently pursuing or recently completed degree in Computer Science, Artificial Intelligence, Data Science, Statistics, Mathematics, Operations Research, Engineering or related quantitative discipline | one_to_one / False | Education OR stored simple |
| P32-U02: Python | U02: Strong Python programming ability | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U03: ML fundamentals | U03: Sound understanding of machine-learning fundamentals | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U04: Feature engineering | U04: Familiarity with feature engineering | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U05: Model evaluation | U05: Familiarity with model evaluation | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U06: Hyperparameter tuning | U06: Familiarity with hyperparameter optimization | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U07: NumPy | U07: Experience with NumPy | one_to_one / True | Familiarity strengthened to experience |
| P32-U08: pandas | U08: Experience with pandas | one_to_one / True | Familiarity strengthened to experience |
| P32-U09: scikit-learn | U09: Experience with scikit-learn | one_to_one / True | Familiarity strengthened to experience |
| P32-U10: XGBoost | U10: Experience with XGBoost | one_to_one / True | Familiarity strengthened to experience |
| P32-U11: Experiment design | U11: Ability to design experiments carefully | one_to_one / True | Method classified soft_skill |
| P32-U12: Critical interpretation of results | U12: Ability to interpret results critically | one_to_one / True | Method classified soft_skill |
| P32-U13: Git  /  working in an existing codebase | U13: Ability to work with Git or existing codebase | one_to_one / False | Git/codebase OR stored simple |
| P32-U14: Problem solving | U14: Strong problem-solving skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U15: Communication | U15: Strong communication skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U16: Independent work with guidance | U17: Ability to work independently while seeking guidance when appropriate | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P32-U17: Documentation | U16: Strong documentation skills | one_to_one / True | Documentation classified soft_skill |
| P32-U18: Genetic algorithms | U18: Knowledge of genetic algorithms | one_to_one / False | Required source changed preferred |
| P32-U19: Evolutionary methods | U19: Knowledge of evolutionary computation | one_to_one / False | Required source changed preferred |
| P32-U20: Optimization | U20: Knowledge of optimization methods | one_to_one / False | Required source changed preferred |
| P32-U21: Time-series modelling | U21: Experience with time-series modelling | one_to_one / False | Required source changed preferred |
| P32-U22: Validation in time-series modelling | U22: Experience with validation | one_to_one / False | Required changed preferred and time-series qualifier absent |
| P32-U23: Experiment-tracking frameworks | U23: Experience with experiment-tracking frameworks | one_to_one / False | Required changed preferred; unnamed framework classified skill_tool |
| P32-U24: SQL | U24: Familiarity with Structured Query Language | one_to_one / False | Required source changed preferred |
| P32-U25: Data pipelines | U25: Familiarity with data pipelines | one_to_one / False | Required source changed preferred |
| P32-U26: REST APIs | U26: Exposure to Representational State Transfer Application Programming Interfaces | one_to_one / False | Required source changed preferred |
| P32-U27: Lightweight application development | U27: Exposure to lightweight application development | one_to_one / False | Required source changed preferred |
| P32-U28: Production software exposure | U28: Exposure to production-oriented software engineering | one_to_one / False | Required source changed preferred |
| P32-U29: Interest in LLM/RAG/agents/cloud/containers/CI/CD | U29: Interest in large language models; U30: Interest in retrieval-augmented generation; U31: Interest in agentic workflows; U32: Interest in cloud platforms; U33: Interest in containers; U34: Interest in continuous integration / continuous delivery | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |

### claude-haiku-4.5/F00815

All nine qualification clauses checked; 16 units. U09 makes FastAPI/Flask a closed alternative but omits the source etc./other-framework route retained in the reviewed reference. Data pipelines and ETL are strengthened from solid understanding to experience. Proven professional-role experience is classified experience_duration despite no numerical duration. LLM and vector-framework examples represented as closed alternatives also need source-compatible alignment; explicit AWS-or-other-cloud and degree branches retain their experience/degree qualifiers. Importance is correct and source quotes are exact. No reference amendment or F1 inferred.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P52-U01: Professional AI/ML engineer experience | U01: Proven experience as an AI Engineer or Machine Learning Engineer | one_to_one / True | No numeric duration but classified experience_duration |
| P52-U02: Python | U02: Strong programming skills in Python | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U03: OpenAI  /  LangChain  /  LlamaIndex LLM framework | U03: Experience with LLM frameworks such as OpenAI, LangChain, or LlamaIndex | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U04: Prompt engineering | U04: Prompt engineering experience | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U05: RAG | U05: Experience with RAG architectures | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U06: ML fundamentals | U06: Solid understanding of machine learning fundamentals | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U07: Data pipelines | U07: Experience with data pipelines | one_to_one / False | Understanding strengthened to experience |
| P52-U08: ETL | U08: Experience with ETL processes | one_to_one / False | Understanding strengthened to experience |
| P52-U09: FastAPI  /  Flask  /  equivalent API deployment | U09: Experience building and deploying APIs using FastAPI or Flask | one_to_one / False | Equivalent-framework route omitted |
| P52-U10: SQL/PostgreSQL | U10: Familiarity with SQL databases such as PostgreSQL | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U11: Pinecone  /  FAISS  /  Weaviate vector technology | U11: Familiarity with Vector databases such as Pinecone, FAISS, or Weaviate | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U12: AWS  /  other cloud platform | U12: Experience with AWS or other cloud platforms | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U13: Git | U13: Understanding of Git | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U14: Testing | U14: Understanding of testing practices | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U15: CI/CD | U15: Understanding of CI/CD practices | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P52-U16: Technical bachelor | U16: Bachelor's degree in Computer Science, Engineering, or related field | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |

### claude-haiku-4.5/F00010

All seven qualification clauses checked; 12 units. Framework and cloud OR alternatives are converted into three independent required AND units each, and both similar-framework and similar-cloud routes are omitted. Eight-year AI/ML/DS alternatives are retained only in one qualified text, not explicit assessable branches. Communication and remote cross-functional teamwork remain merged; preferred coding assistants remain a simple composite without approved alternative representation. Proficiency/deployment qualifiers and eight-year minimum are retained in the emitted units; importance and exact quotes pass. No gold change.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P02-U01: At least 8 years in AI  /  ML  /  Data Science roles | U01: 8 years of relevant experience in AI, Machine Learning, or Data Science roles | one_to_one / False | Role alternatives stored without branches |
| P02-U02: English communication | U02: Excellent English communication skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U03: Python | U03: Strong proficiency in Python | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P02-U04: TensorFlow  /  PyTorch  /  scikit-learn  /  similar ML framework | U04: Strong proficiency in TensorFlow; U05: Strong proficiency in PyTorch; U06: Strong proficiency in scikit-learn | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P02-U05: Deploying ML models on AWS  /  GCP  /  Azure  /  similar cloud | U07: Familiarity with deploying ML models in AWS; U08: Familiarity with deploying ML models in GCP; U09: Familiarity with deploying ML models in Azure | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P02-U06: Communication; P02-U07: Working with remote cross-functional teams | U10: Strong communication skills and ability to work effectively in a remote, cross-functional team | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P02-U08: Copilot  /  Cursor  /  Warp  /  similar AI coding assistant | U11: Experience using AI coding assistants (Copilot, Cursor, Warp) | one_to_one / False | Coding-assistant alternatives stored simple |
| P02-U09: Indonesian citizenship | U12: Indonesian Citizen | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |

### claude-haiku-4.5/F00018

All required and plus sections checked; 18 units. The entire five-clause plus section is absent, including cloud/AWS-stack preference, deep learning, taxonomies/ontologies, pipeline orchestration and Spark/Dask/Great Expectations. One-or-more NLP/LLM/recommendation use cases become three independent required AND obligations. Algorithms and underlying math remain merged. RAG and agentic units lose the shared strong hands-on qualifier. Five non-numerical experience units are misclassified experience_duration and generic software engineering as skill_tool. Extracted required/preferred importance and quotes pass, but completeness and grouping fail. No gold change.

| Gold IDs and text | Model IDs and text | Relation / recommended primary equivalent | Review note |
|---|---|---|---|
| P04-U01: Standard ML algorithms; P04-U02: Mathematical basis of ML algorithms | U01: Comfortable with standard ML algorithms and underlying math | model_merge / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P04-U03: LLMs in production | U02: Strong hands-on experience with LLMs in production | one_to_one / True | Nonnumeric experience misclassified duration |
| P04-U04: RAG architecture | U03: Experience with RAG architecture | one_to_one / True | Strong hands-on qualifier absent |
| P04-U05: Agentic systems | U04: Experience with agentic systems | one_to_one / True | Strong hands-on qualifier absent |
| P04-U06: AWS Bedrock | U05: AWS Bedrock experience | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U07: Classification | U06: Practical experience with solving classification tasks | one_to_one / True | Nonnumeric experience misclassified duration |
| P04-U08: Regression | U07: Practical experience with solving regression tasks | one_to_one / True | Nonnumeric experience misclassified duration |
| P04-U09: Feature engineering | U08: Practical experience with feature engineering | one_to_one / True | Nonnumeric experience misclassified duration |
| P04-U10: Practical experience with ML models in production | U09: Practical experience with ML models in production | one_to_one / True | Nonnumeric experience misclassified duration |
| P04-U11: Experience with at least one of: NLP  /  LLM  /  Recommendation systems | U10: Practical experience with NLP; U11: Practical experience with LLMs; U12: Practical experience with Recommendation engines | model_split / False | Strict D-054 structural split/merge: no automatic TP; many-to-many remains held |
| P04-U12: Software engineering beyond notebooks, with structured modules | U13: Solid software engineering skills including ability to produce well-structured modules | one_to_one / True | Generic engineering concept classified tool |
| P04-U13: Python | U14: Python expertise | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U14: Docker | U15: Docker | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U15: English at strong upper-intermediate level | U16: English level strong upper-intermediate | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U16: Communication | U17: Excellent communication skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U17: Problem solving | U18: Excellent problem-solving skills | one_to_one / True | Source obligation appears equivalent; confirm shared qualifiers, importance and type against full row. |
| P04-U18: Practical experience with cloud platforms | (none) | model_omission / False | Reviewed source obligation omitted from final model draft |
| P04-U19: Deep learning models | (none) | model_omission / False | Reviewed source obligation omitted from final model draft |
| P04-U20: Taxonomies  /  ontologies | (none) | model_omission / False | Reviewed source obligation omitted from final model draft |
| P04-U21: ML pipeline orchestration | (none) | model_omission / False | Reviewed source obligation omitted from final model draft |
| P04-U22: Spark  /  Dask distributed processing | (none) | model_omission / False | Reviewed source obligation omitted from final model draft |
| P04-U23: Great Expectations | (none) | model_omission / False | Reviewed source obligation omitted from final model draft |
| P04-U18-AWS: Experience with the AWS cloud stack | (none) | model_omission / False | Reviewed source obligation omitted from final model draft |
