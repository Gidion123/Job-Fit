# D-064 reference and round-two extraction alignment review

3 October 2026. Source-reviewed proposals for the new candidate outputs. Approval of D-064 authorizes execution; it does not approve these alignments. D-063 applies to the earlier candidate packet and fixed matcher adapter only.

## Review and accounting

Recommended equivalents retain meaning, material qualifiers, logical alternatives and importance. Category errors are reported separately under D-061. D-054 strictly counts independently assessable splits/merges as unmatched units. No gold, source or prediction was corrected. No formal extraction F1 or model winner is published here.

| Model / JD | Gold units | Model units | Proposed relations |
|---|---:|---:|---|
| gpt-6-sol/extraction/F00332 | 16 | 18 | {'one_to_one': 14, 'model_split': 2} |
| gpt-6-sol/extraction/F00036 | 17 | 20 | {'one_to_one': 17, 'model_addition': 3} |
| gpt-6-sol/extraction/F00815 | 16 | 17 | {'one_to_one': 15, 'model_split': 1} |
| gpt-6-sol/extraction/F00018 | 24 | 23 | {'one_to_one': 22, 'model_merge': 1} |
| deepseek-v4-pro/extraction/F00332 | 16 | 15 | {'one_to_one': 14, 'model_merge': 1} |
| deepseek-v4-pro/extraction/F00036 | 17 | 17 | {'one_to_one': 17} |
| deepseek-v4-pro/extraction/F00309 | 9 | 9 | {'one_to_one': 9} |
| deepseek-v4-pro/extraction/F00354 | 29 | 31 | {'one_to_one': 24, 'model_merge': 1, 'model_split': 1} |
| deepseek-v4-pro/extraction/F00815 | 16 | 14 | {'one_to_one': 13, 'model_merge': 1} |
| deepseek-v4-pro/extraction/F00010 | 9 | 9 | {'one_to_one': 9} |
| deepseek-v4-pro/extraction/F00018 | 24 | 22 | {'one_to_one': 21, 'model_merge': 1, 'model_omission': 1} |

The GPT reference scope has four whole JDs/73 units. DeepSeek Pro has seven whole JDs/120 units. Reference comparisons must use the common four-JD subset of each other model, retaining original failures. Unresolved model flags remain operational concerns independently of semantic equivalence.

## Complete proposed inventory

Every gold/model unit appears exactly once in the JSON inventory. Full source, original quotes, alternative branches and category/importance checks are attached there. Apparent equivalents below also require acceptance; the table is assisted QA, not independent annotation.

### gpt-6-sol/extraction/F00332

| Gold IDs and text | Model IDs and text | Relation / recommended equivalent | Review note |
|---|---|---|---|
| P30-U01: Fresh graduate  /  bachelor in quantitative/analytical or other considered discipline | U01: Be a fresh graduate or hold a bachelor's degree in an analytical or quantitative discipline; bachelor's degrees in other disciplines will also be considered. | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U02: Python | U02: Experience using Python as a statistical computer language | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U03: SQL | U03: Experience using SQL as a statistical computer language | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U04: Microsoft Excel | U04: Experience using MS Excel as a statistical computer language | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U05: Communication | U05: Good communication skills | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U06: Team collaboration | U06: Ability to work collaboratively in a team | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U07: Problem solving | U07: Excellent problem-solving skills | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U08: Learning new techniques | U08: Drive to learn and master new technologies; U09: Drive to learn and master new techniques | model_split / False | Strict D-054: independently assessable gold/model units are unmatched; no automatic TP for split/merge. |
| P30-U09: Independent learning | U10: Willingness to learn new skills independently | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U10: Project ownership | U11: Strong sense of project ownership | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U11: Data exploration | U12: Comfortable exploring data | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U12: Anomaly investigation | U13: Comfortable investigating anomalies | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U13: SQL-based analysis | U14: Comfortable building SQL-based analyses | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. Category differs; reported separately. |
| P30-U14: Large tabular-data trend/anomaly analysis | U15: Experience working with large tabular datasets to detect trends; U16: Experience working with large tabular datasets to detect anomalies | model_split / False | Strict D-054: independently assessable gold/model units are unmatched; no automatic TP for split/merge. |
| P30-U15: Communicating actionable findings | U17: Experience working with large tabular datasets to communicate findings as actionable recommendations | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. Category differs; reported separately. |
| P30-U16: Credit-scoring modelling | U18: Exposure to credit scoring modelling concepts | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |

### gpt-6-sol/extraction/F00036

| Gold IDs and text | Model IDs and text | Relation / recommended equivalent | Review note |
|---|---|---|---|
| P09-U01: Bachelor Statistics  /  Mathematics  /  CS  /  Informatics  /  DS | U07: At least a bachelor's degree in Statistics, Mathematics, Computer Science, Informatics Engineering, or Data Science | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U02: At least 2-3 years professional DS or similar work | U08: At least 2 years of professional experience as a Data Scientist or in a similar role | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U03: Python  /  R  /  SQL for data manipulation and analysis | U09: Proficiency in a programming language such as Python, R, or SQL for data manipulation and analysis | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U04: Supervised ML | U02: Understanding of supervised learning | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U05: Unsupervised ML | U03: Understanding of unsupervised learning | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U06: Deep learning | U04: Understanding of deep learning | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U07: pandas  /  scikit-learn  /  TensorFlow  /  PyTorch | U10: Experience using a library or tool such as Pandas, Scikit-learn, TensorFlow, or PyTorch | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U08: Exploratory data analysis | U11: Ability to perform exploratory data analysis using a tool such as Tableau, Power BI, or Matplotlib | one_to_one / False | EDA becomes dependent on a named visualization tool rather than the independent reviewed EDA obligation. Category differs; reported separately. |
| P09-U09: Tableau  /  Power BI  /  Matplotlib | U12: Ability to perform data visualization using a tool such as Tableau, Power BI, or Matplotlib | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U10: Descriptive statistics | U13: Understanding of descriptive statistics | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U11: Inferential statistics | U14: Understanding of inferential statistics | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U12: Research methodology | U15: Understanding of research methodology | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U13: Explaining technical analysis to nontechnical stakeholders | U16: Ability to communicate technical concepts to non-technical stakeholders | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U14: Database management | U17: Experience with database management | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U15: Hadoop  /  Spark  /  cloud big-data experience | U18: Experience with big data technologies such as Hadoop, Spark, or cloud platforms | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U16: Problem solving | U19: Strong problem-solving ability when working with data | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U17: Attention to detail | U20: Attention to detail when working with data | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| (none) | U01: Understanding of data analytics | model_addition / False | Outside reviewed inventory. A source-supported opening statement is still FP against the fixed reference; FP is not automatically fabrication. |
| (none) | U05: Understanding of statistical modeling | model_addition / False | Outside reviewed inventory. A source-supported opening statement is still FP against the fixed reference; FP is not automatically fabrication. |
| (none) | U06: Work in Bandung, West Java | model_addition / False | Outside reviewed inventory. A source-supported opening statement is still FP against the fixed reference; FP is not automatically fabrication. |

### gpt-6-sol/extraction/F00815

| Gold IDs and text | Model IDs and text | Relation / recommended equivalent | Review note |
|---|---|---|---|
| P52-U01: Professional AI/ML engineer experience | U01: Proven experience as an AI Engineer or Machine Learning Engineer | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. Category differs; reported separately. |
| P52-U02: Python | U02: Strong programming skills in Python | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U03: OpenAI  /  LangChain  /  LlamaIndex LLM framework | U03: Experience with LLM frameworks, with OpenAI, LangChain and LlamaIndex given as examples | one_to_one / False | Reviewed LLM-framework alternative group stored as a simple example-list unit; no assessable branches. |
| P52-U04: Prompt engineering | U04: Experience with prompt engineering | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U05: RAG | U05: Experience with RAG architectures | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U06: ML fundamentals | U06: Solid understanding of machine learning fundamentals | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U07: Data pipelines | U07: Solid understanding of data pipelines | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U08: ETL | U08: Solid understanding of ETL processes | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U09: FastAPI  /  Flask  /  equivalent API deployment | U09: Experience building APIs with FastAPI, Flask, or a similar framework; U10: Experience deploying APIs with FastAPI, Flask, or a similar framework | model_split / False | Strict D-054: independently assessable gold/model units are unmatched; no automatic TP for split/merge. |
| P52-U10: SQL/PostgreSQL | U11: Familiarity with SQL databases, such as PostgreSQL | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U11: Pinecone  /  FAISS  /  Weaviate vector technology | U12: Familiarity with vector databases, with Pinecone, FAISS and Weaviate given as examples | one_to_one / False | Reviewed vector-technology alternatives stored as a simple example-list unit; no assessable branches. Category differs; reported separately. |
| P52-U12: AWS  /  other cloud platform | U13: Experience with AWS or another cloud platform | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U13: Git | U14: Understanding of Git as a software engineering practice | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U14: Testing | U15: Understanding of software testing practices | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U15: CI/CD | U16: Understanding of CI/CD practices | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U16: Technical bachelor | U17: Bachelor's degree in Computer Science, Engineering, or a related field | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |

### gpt-6-sol/extraction/F00018

| Gold IDs and text | Model IDs and text | Relation / recommended equivalent | Review note |
|---|---|---|---|
| P04-U01: Standard ML algorithms | U01: Comfortable with standard ML algorithms | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U02: Mathematical basis of ML algorithms | U02: Comfortable with the underlying mathematics of standard ML algorithms | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U03: LLMs in production | U03: Strong hands-on experience with LLMs in production | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U04: RAG architecture | U04: Strong hands-on experience with RAG architecture | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U05: Agentic systems | U05: Strong hands-on experience with agentic systems | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U06: AWS Bedrock | U06: Experience with AWS Bedrock | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U07: Classification | U07: Practical experience solving classification tasks | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U08: Regression | U08: Practical experience solving regression tasks | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U09: Feature engineering | U09: Practical experience with feature engineering | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U10: Practical experience with ML models in production | U10: Practical experience with ML models in production | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U11: Experience with at least one of: NLP  /  LLM  /  Recommendation systems | U11: Practical experience with one or more use cases in NLP, LLMs, or recommendation engines | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U12: Software engineering beyond notebooks, with structured modules | U12: Solid software engineering skills, including the ability to produce well-structured modules rather than only notebook scripts | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U13: Python | U13: Python expertise | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U14: Docker | U14: Docker proficiency | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U15: English at strong upper-intermediate level | U15: Strong upper-intermediate English | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U16: Communication | U16: Excellent communication skills | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U17: Problem solving | U17: Excellent problem-solving skills | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U18: Practical experience with cloud platforms; P04-U18-AWS: Experience with the AWS cloud stack | U18: Practical experience with cloud platforms; AWS stack experience is preferred, with Amazon SageMaker, ECR, EMR, S3, and AWS Lambda given as examples | model_merge / False | Strict D-054: independently assessable gold/model units are unmatched; no automatic TP for split/merge. |
| P04-U19: Deep learning models | U19: Practical experience with deep learning models | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U20: Taxonomies  /  ontologies | U20: Experience with taxonomies or ontologies | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U21: ML pipeline orchestration | U21: Practical experience with machine learning pipelines to orchestrate complicated workflows | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U22: Spark  /  Dask distributed processing | U22: Practical experience with Spark/Dask | one_to_one / False | Reviewed Spark/Dask alternative remains unresolved simple composite with needs_review. |
| P04-U23: Great Expectations | U23: Practical experience with Great Expectations | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |

### deepseek-v4-pro/extraction/F00332

| Gold IDs and text | Model IDs and text | Relation / recommended equivalent | Review note |
|---|---|---|---|
| P30-U01: Fresh graduate  /  bachelor in quantitative/analytical or other considered discipline | U01: Fresh Graduate or Bachelor's degree | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U02: Python | U02: Experience using Python | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U03: SQL | U03: Experience using SQL | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U04: Microsoft Excel | U04: Experience using MS Excel | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U05: Communication | U05: Good communication skills | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U06: Team collaboration | U06: Ability to work collaboratively in a team | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U07: Problem solving | U07: Excellent problem-solving skills | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U08: Learning new techniques | U08: Drive to learn and master new technologies and techniques | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U09: Independent learning | U09: Willingness to learn new skills independently | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U10: Project ownership | U10: Strong sense of project ownership | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U11: Data exploration | U11: Comfortable exploring data | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U12: Anomaly investigation | U12: Comfortable investigating anomalies | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U13: SQL-based analysis | U13: Comfortable building SQL-based analyses | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P30-U14: Large tabular-data trend/anomaly analysis; P30-U15: Communicating actionable findings | U14: Experience working with large tabular datasets to detect trends and anomalies and communicate findings as actionable recommendations | model_merge / False | Strict D-054: independently assessable gold/model units are unmatched; no automatic TP for split/merge. |
| P30-U16: Credit-scoring modelling | U15: Exposure to credit scoring modelling concepts | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |

### deepseek-v4-pro/extraction/F00036

| Gold IDs and text | Model IDs and text | Relation / recommended equivalent | Review note |
|---|---|---|---|
| P09-U01: Bachelor Statistics  /  Mathematics  /  CS  /  Informatics  /  DS | U01: Bachelor's degree in Statistics, Mathematics, Computer Science, Informatics Engineering, or Data Science | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U02: At least 2-3 years professional DS or similar work | U02: At least 2 years of professional experience as Data Scientist or similar position | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U03: Python  /  R  /  SQL for data manipulation and analysis | U03: Proficiency in programming languages such as Python, R, or SQL for data manipulation and analysis | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U04: Supervised ML | U04a: Strong understanding of supervised learning | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U05: Unsupervised ML | U04b: Strong understanding of unsupervised learning | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U06: Deep learning | U04c: Strong understanding of deep learning | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U07: pandas  /  scikit-learn  /  TensorFlow  /  PyTorch | U05: Experience using popular tools and libraries such as Pandas, Scikit-learn, TensorFlow, or PyTorch | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U08: Exploratory data analysis | U06a: Ability to perform exploratory data analysis using tools such as Tableau, Power BI, or Matplotlib | one_to_one / False | EDA becomes dependent on a named visualization tool instead of the independent reviewed EDA obligation. Category differs; reported separately. |
| P09-U09: Tableau  /  Power BI  /  Matplotlib | U06b: Ability to perform data visualization using tools such as Tableau, Power BI, or Matplotlib | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U10: Descriptive statistics | U07a: Solid understanding of descriptive statistics | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U11: Inferential statistics | U07b: Solid understanding of inferential statistics | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U12: Research methodology | U07c: Solid understanding of research methodology | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U13: Explaining technical analysis to nontechnical stakeholders | U08: Good communication skills to explain technical concepts to non-technical stakeholders | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. Category differs; reported separately. |
| P09-U14: Database management | U09a: Experience with database management | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. Category differs; reported separately. |
| P09-U15: Hadoop  /  Spark  /  cloud big-data experience | U09b: Experience with big data technologies such as Hadoop, Spark, or cloud platforms | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U16: Problem solving | U10a: Strong problem-solving skills | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P09-U17: Attention to detail | U10b: Attention to detail in working with data | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |

### deepseek-v4-pro/extraction/F00309

| Gold IDs and text | Model IDs and text | Relation / recommended equivalent | Review note |
|---|---|---|---|
| P26-U01: 1-3 years relevant experience | U001: 1-3 years of relevant experience demonstrating practical application of skills at this seniority level | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P26-U02: Python | U002: Proficiency in Python | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P26-U03: SQL | U003: Proficiency in SQL | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P26-U04: Statistics | U004: Proficiency in statistics | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P26-U05: ML | U005: Proficiency in machine learning | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P26-U06: Experimentation | U006: Proficiency in experimentation | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P26-U07: Visualization | U007: Proficiency in data visualization | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P26-U08: Data storytelling | U008: Proficiency in data storytelling | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P26-U09: Diploma/degree  /  equivalent practical experience in a relevant field | U009: Diploma, degree, or equivalent practical experience in a relevant technical, business, or creative discipline | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |

### deepseek-v4-pro/extraction/F00354

| Gold IDs and text | Model IDs and text | Relation / recommended equivalent | Review note |
|---|---|---|---|
| P32-U01: Studying  /  recent graduate in a quantitative field | U01: Currently pursuing or recently completed a degree in Computer Science, Artificial Intelligence, Data Science, Statistics, Mathematics, Operations Research, Engineering, or a related quantitative discipline | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U02: Python | U02: Strong Python programming ability | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U03: ML fundamentals | U03: Sound understanding of machine-learning fundamentals | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U04: Feature engineering | U04: Familiarity with feature engineering | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U05: Model evaluation | U05: Familiarity with model evaluation | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U06: Hyperparameter tuning | U06: Familiarity with hyperparameter optimization | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U07: NumPy; P32-U08: pandas; P32-U09: scikit-learn; P32-U10: XGBoost | U07: Familiarity with libraries such as NumPy, pandas, scikit-learn and XGBoost | model_merge / False | Four AND-listed libraries merged into a single OR choice; reviewed inventory has four independent library obligations. Strict D-054: independently assessable gold/model units are unmatched; no automatic TP for split/merge. |
| P32-U11: Experiment design | U08: Ability to design experiments carefully | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U12: Critical interpretation of results | U09: Ability to interpret results critically | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U13: Git  /  working in an existing codebase | U10: Ability to work with Git or an existing codebase | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U14: Problem solving | U11: Strong problem-solving skills | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U15: Communication | U12: Strong communication skills | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U16: Independent work with guidance | U14: Ability to work independently while seeking guidance when appropriate | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U17: Documentation | U13: Strong documentation skills | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. Category differs; reported separately. |
| P32-U18: Genetic algorithms | U15: Knowledge of genetic algorithms | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U19: Evolutionary methods | U16: Knowledge of evolutionary computation | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U20: Optimization | U17: Knowledge of optimization methods | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U21: Time-series modelling | U18: Experience with time-series modelling | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U22: Validation in time-series modelling | U19: Experience with validation | one_to_one / False | Validation loses the time-series qualifier. |
| P32-U23: Experiment-tracking frameworks | U20: Experience with experiment-tracking frameworks | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. Category differs; reported separately. |
| P32-U24: SQL | U21: Familiarity with Structured Query Language | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U25: Data pipelines | U22: Familiarity with data pipelines | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U26: REST APIs | U23: Exposure to Representational State Transfer Application Programming Interfaces | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U27: Lightweight application development | U24: Exposure to lightweight application development | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U28: Production software exposure | U25: Exposure to production-oriented software engineering | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P32-U29: Interest in LLM/RAG/agents/cloud/containers/CI/CD | U26: Interest in large language models; U27: Interest in retrieval-augmented generation; U28: Interest in agentic workflows; U29: Interest in cloud platforms; U30: Interest in containers; U31: Interest in continuous integration / continuous delivery | model_split / False | The reviewed composite interest requirement is split into six units; no automatic TP under D-054. Strict D-054: independently assessable gold/model units are unmatched; no automatic TP for split/merge. |

### deepseek-v4-pro/extraction/F00815

| Gold IDs and text | Model IDs and text | Relation / recommended equivalent | Review note |
|---|---|---|---|
| P52-U01: Professional AI/ML engineer experience | U01: Proven experience as an AI Engineer or Machine Learning Engineer | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. Category differs; reported separately. |
| P52-U02: Python | U02: Strong programming skills in Python | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U03: OpenAI  /  LangChain  /  LlamaIndex LLM framework | U03: Experience with LLM frameworks (e.g. OpenAI, LangChain, LlamaIndex) | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U04: Prompt engineering | U04: Experience with Prompt engineering | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U05: RAG | U05: Experience with RAG architectures | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U06: ML fundamentals | U06: Solid understanding of machine learning fundamentals | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U07: Data pipelines | U07: Solid understanding of data pipelines | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U08: ETL | U08: Solid understanding of ETL processes | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U09: FastAPI  /  Flask  /  equivalent API deployment | U09: Experience building and deploying APIs (FastAPI, Flask, etc.) | one_to_one / False | FastAPI/Flask branches omit the source and reviewed equivalent-framework route. |
| P52-U10: SQL/PostgreSQL | U10: Familiarity with SQL databases (PostgreSQL) | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U11: Pinecone  /  FAISS  /  Weaviate vector technology | U11: Familiarity with Vector databases (e.g. Pinecone, FAISS, Weaviate) | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U12: AWS  /  other cloud platform | U12: Experience with AWS or other cloud platforms | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P52-U13: Git; P52-U14: Testing; P52-U15: CI/CD | U13: Understanding of software engineering best practices (Git, testing, CI/CD) | model_merge / False | Git/testing/CI-CD AND obligations merged into one OR group. Strict D-054: independently assessable gold/model units are unmatched; no automatic TP for split/merge. |
| P52-U16: Technical bachelor | U14: Bachelor's degree in Computer Science, Engineering, or related field | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |

### deepseek-v4-pro/extraction/F00010

| Gold IDs and text | Model IDs and text | Relation / recommended equivalent | Review note |
|---|---|---|---|
| P02-U01: At least 8 years in AI  /  ML  /  Data Science roles | U01: 8 years of relevant experience in AI, Machine Learning, or Data Science roles | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P02-U02: English communication | U02: Excellent English communication skills | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P02-U03: Python | U03: Strong proficiency in Python | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P02-U04: TensorFlow  /  PyTorch  /  scikit-learn  /  similar ML framework | U04: Strong proficiency in common ML frameworks (TensorFlow, PyTorch, scikit-learn, or similar) | one_to_one / False | Explicit similar-framework route omitted from assessable branches although retained in parent text. |
| P02-U05: Deploying ML models on AWS  /  GCP  /  Azure  /  similar cloud | U05: Familiarity with deploying ML models in cloud environments (AWS, GCP, Azure, or similar) | one_to_one / False | Explicit similar-cloud route omitted from assessable branches although retained in parent text. |
| P02-U06: Communication | U06: Strong communication skills | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P02-U07: Working with remote cross-functional teams | U07: Ability to work effectively in a remote, cross-functional team | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P02-U08: Copilot  /  Cursor  /  Warp  /  similar AI coding assistant | U08: Experience using AI coding assistants (Copilot, Cursor, Warp) | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P02-U09: Indonesian citizenship | U09: Indonesian Citizen | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |

### deepseek-v4-pro/extraction/F00018

| Gold IDs and text | Model IDs and text | Relation / recommended equivalent | Review note |
|---|---|---|---|
| P04-U01: Standard ML algorithms | U01: Comfortable with standard ML algorithms | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U02: Mathematical basis of ML algorithms | U02: Comfortable with underlying math | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U03: LLMs in production | U03: Strong hands-on experience with LLMs in production | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U04: RAG architecture | U04: Strong hands-on experience with RAG architecture | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U05: Agentic systems | U05: Strong hands-on experience with agentic systems | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U06: AWS Bedrock | U06: AWS Bedrock experience | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U07: Classification; P04-U08: Regression | U07: Practical experience with solving classification and regression tasks | model_merge / False | Strict D-054: independently assessable gold/model units are unmatched; no automatic TP for split/merge. |
| P04-U09: Feature engineering | U08: Practical experience with feature engineering | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U10: Practical experience with ML models in production | U09: Practical experience with ML models in production | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U11: Experience with at least one of: NLP  /  LLM  /  Recommendation systems | U10: Practical experience with one or more use cases from NLP, LLMs, and Recommendation engines | one_to_one / False | One-or-more use-case alternatives stored simple with no assessable branches. |
| P04-U12: Software engineering beyond notebooks, with structured modules | U11: Solid software engineering skills (ability to produce well-structured modules, not only notebook scripts) | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U13: Python | U12: Python expertise | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U14: Docker | U13: Docker | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U15: English at strong upper-intermediate level | U14: English level strong upper-intermediate | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U16: Communication | U15: Excellent communication skills | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U17: Problem solving | U16: Excellent problem-solving skills | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U18: Practical experience with cloud platforms | U17: Practical experience with cloud platforms | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U19: Deep learning models | U18: Practical experience with deep learning models | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U20: Taxonomies  /  ontologies | U19: Experience with taxonomies or ontologies | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U21: ML pipeline orchestration | U20: Practical experience with machine learning pipelines to orchestrate complicated workflows | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U22: Spark  /  Dask distributed processing | U21: Practical experience with Spark or Dask | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U23: Great Expectations | U22: Practical experience with Great Expectations | one_to_one / True | Source-reviewed meaning, material qualifiers and importance preserved; category evaluated separately. |
| P04-U18-AWS: Experience with the AWS cloud stack | (none) | model_omission / False | Reviewed obligation omitted. |
