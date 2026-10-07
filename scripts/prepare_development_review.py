"""Prepare explicitly reasoned, pending drafts. No inference or gold export.

Spreadsheet authoring is performed separately with the artifact runtime.
"""
import csv
import hashlib
import json
from pathlib import Path
import random
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from jobfit.config import REPO_ROOT
from jobfit.search.embeddings import cv_body

SELECTED = ['F00103', 'F00074', 'F00012']
REASONS = ['Indonesian internship; mixed required/preferred skills and location commitment.',
           'LLM/RAG application engineering; qualified production experience and tool alternatives.',
           'Senior ML leadership; five years in ML/DS plus two years in leadership.']


def main():
    root = REPO_ROOT
    if (root/'evals/labeling/JobFit_Development_Labeling_v0.1.xlsx').exists():
        raise ValueError('Unified review workbook exists; preserve human review and do not recreate old batches')
    jobs = {r['final_cluster_id']:r for r in map(json.loads,
            (root/'data/processed/jobs_features.jsonl').read_text().splitlines())}
    dev = set((root/'evals/splits/dev_job_ids.txt').read_text().splitlines())
    pool = list(csv.DictReader((root/'evals/pools/dev_pool.csv').open()))
    if any(r['gold_review'] == 'pending_decision' for r in pool):
        raise ValueError('pool selection needs a human decision')
    cvs = {'CV1': cv_body(root/'data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md'),
           'CV2': cv_body(root/'data/synthetic_cvs/cv_02_career_switcher_ai_engineer_en.md')}
    units = []

    def add(batch, needle, texts, category='skill_tool', importance='required', group='', years=None, note=''):
        job_id = SELECTED[batch-1]
        matches = [s.strip().removeprefix('•').strip() for s in jobs[job_id]['description_clean'].splitlines() if needle in s]
        if len(matches) != 1:
            raise ValueError((job_id, needle, len(matches)))
        quote = matches[0]
        for text in texts:
            number = 1 + sum(r['pilot_id'] == f'D{batch}' for r in units)
            units.append(dict(pilot_id=f'D{batch}', job_id=job_id, unit_no=f'D{batch}-U{number:02d}',
                unit_text=text, source_quote=quote, importance=importance, category=category,
                group_id=group, min_years=years, label_source='model_draft', review_status='pending',
                review_action='', draft_note=note or ('Explicit qualification; independently assessable requirement.'
                    if importance=='required' else 'The source explicitly softens this qualification.'),
                review_note='', guideline_version='v1.2'))

    # D1. Only the qualification section, not duties or training benefits.
    add(1,'Mahasiswa tingkat akhir',['Final-year student | recent graduate in Engineering, Computer Science/Technology, or a related discipline'],'education',group='D1-G1')
    add(1,'IPK minimal',['GPA at least 3.00/4.00 or equivalent'],'education')
    add(1,'Kemampuan analitis',['Analytical skills','Quantitative skills','Strategic thinking','Complex problem solving'],'soft_skill')
    add(1,'komunikasi tertulis',['Written communication','Verbal communication'],'soft_skill')
    add(1,'kolaboratif dalam tim',['Team collaboration'],'soft_skill')
    add(1,'Microsoft Office Suite',['Microsoft Excel','Microsoft PowerPoint','Microsoft Word'],note='Office Suite explicitly includes these tools; split the enumerated components.')
    add(1,'perbaikan proses bisnis',['Business process improvement methodologies'],'knowledge_area','preferred')
    add(1,'Antusias untuk belajar',['Willingness to learn','Adaptability'],'soft_skill')
    add(1,'keahlian kuat di bidang',['Data science | technology expertise | relevant certification'],'other','preferred',group='D1-G2',note='One alternative bonus; mixed categories retained in other and raised for review.')
    add(1,'Bersedia magang penuh',['Full-time internship in Yogyakarta for at least three months'],'location',note='Location and commitment remain coupled; not three months of prior experience.')
    add(1,'Pengalaman data engineering',['Data engineering experience'],'knowledge_area')
    add(1,'Kemampuan Python dan SQL',['Python','SQL'])
    add(1,'orkestrasi pipeline',['ETL/ELT pipeline design','ETL/ELT pipeline orchestration using Airflow | Azure Data Factory | similar tools'],'knowledge_area',note='Split design and orchestration; tools remain an example/alternative within orchestration.')
    units[-1]['group_id']='D1-G3'
    add(1,'layanan data Azure',['Azure Data Lake','Azure Synapse','Azure Data Factory','Azure Cosmos DB'],note='Azure services are listed without an OR or example marker; draft as separate components.')
    add(1,'Integrasi API',['Consuming enterprise REST APIs'],'skill_tool',note='Oracle, Salesforce and Workday are enterprise examples; do not create three mandatory vendors.')
    add(1,'framework dan monitoring',['Data-quality frameworks','Data-quality monitoring'],'knowledge_area')
    add(1,'tata kelola data',['Data governance','Access control','Privacy requirements'],'knowledge_area')
    add(1,'PDPA/regulasi',['PDPA | data privacy regulations'],'knowledge_area','unknown',group='D1-G4',note='Menjadi prioritas signals priority but does not clearly mean mandatory or bonus. Review needed.')
    add(1,'Microsoft Graph API',['Microsoft Graph API'])
    add(1,'vector database dan',['Vector databases','Embedding pipelines'],'knowledge_area')

    # D2. About-you requirements only.
    add(2,'Professional working proficiency',['Professional working proficiency in written and spoken English'],'language')
    add(2,'2+ years building',['At least two years building production software, including at least one year shipping LLM applications to real users'],'experience_duration',years=2,note='Keep nested duration and production qualifiers together. Both conditions must be supported; min_years describes the outer minimum only.')
    add(2,'Strong Python',['Strong Python','Production web framework such as FastAPI'],note='Python and production framework are independently assessable; FastAPI is an example, not an exclusive requirement.')
    add(2,'Direct experience with LLM',['Direct API-level experience with an LLM provider (Anthropic | OpenAI | Google), not wrappers only'],group='D2-G1')
    add(2,'Demonstrated RAG experience',['Component-built RAG experience','Chunking strategy','Embedding models','Vector store (pgvector | Qdrant | Weaviate | similar)','BM25 | hybrid search','Reranking'],'knowledge_area',note='RAG component skills are independently assessable. Retain explicit vendor/search alternatives within one unit.')
    units[-3]['group_id']='D2-G2'; units[-2]['group_id']='D2-G3'
    add(2,'tool and function calling',['Tool and function calling','Structured output','Schema enforcement'],'knowledge_area')
    add(2,'Practical experience evaluating',['LLM evaluation: building test sets','LLM evaluation: measuring quality','LLM evaluation: preventing regressions'],'knowledge_area')
    add(2,'Working knowledge of PostgreSQL',['PostgreSQL','Git','Docker','CI/CD'])
    add(2,'Comfortable owning cost',['Ownership of cost budgets','Ownership of latency budgets','Reasoning about quality, speed and spend tradeoffs'],'knowledge_area')
    add(2,'Excellent problem-solving',['Problem solving','Independent work in a small team'],'soft_skill')

    # D3. Qualifications only; duplicate duties do not become units.
    add(3,'Gelar Sarjana',['Bachelor degree in Computer Science | Informatics | related discipline'],'education',group='D3-G1')
    add(3,'Gelar Magister',['Master degree'],'education','preferred')
    add(3,'Minimal 5 tahun',['At least five years in applied ML/DS including at least two years in leadership'],'experience_duration',years=5,note='Preserve nested leadership condition; do not take the smallest number or count two independent duration requirements.')
    add(3,'Terbukti pengalaman memimpin',['Leading machine-learning projects','Managing a team of machine-learning engineers'],'knowledge_area')
    add(3,'Pengalaman langsung membangun',['Building ML models','Validating ML models','Deploying ML models','Supervised learning','Unsupervised learning','Deep learning'],'knowledge_area',note='Actions and listed ML areas can be checked separately; the qualification lists all without OR.')
    add(3,'Keterampilan MLOps',['MLOps CI/CD','Model versioning','Model monitoring','MLOps A/B testing'],'knowledge_area')
    add(3,'Rekam jejak mengelola',['Delivering end-to-end ML projects on time and within budget'],'other',note='Keep delivery outcome qualifiers coupled to project experience.')
    add(3,'Komunikasi lintas fungsi',['Cross-functional communication','Stakeholder management'],'soft_skill')
    add(3,'Fokus pada kualitas',['Model quality','Model governance','Scalability','Cost-efficient infrastructure decisions'],'knowledge_area','unknown',note='Focus areas have no clear evidence/depth criterion. Keep for review, do not force required.')

    # Explicit rationale for each pool JD, not a mapping from retrieval scores or percentages.
    # Value: CV1 label/reason/constraint, then CV2 label/reason/constraint.
    low_ai='Python/data analysis is supported, but production LLM, agent and backend engineering evidence is limited.'
    bima_rag='RAG with LangChain/FAISS, FastAPI/Docker and a small question evaluation set are supported; advanced production and operational requirements remain gaps.'
    reasons = {
      'F00003':(1,'Basic ML projects do not meet the software-development and GenAI experience requirements.','Minimum three years software development and one year GenAI projects are not supported.',1,'RAG project supports the topic but does not meet the stated software and GenAI durations.','Three years software development and one year GenAI are not supported by dated relevant experience.'),
      'F00010':(1,'Python and classical ML basics are supported; senior production requirements are not.','Eight years relevant AI/ML/DS experience is not supported.',1,'Transformer and RAG projects provide partial technical evidence, below the senior requirement.','Eight years relevant AI/ML/DS experience is not supported.'),
      'F00018':(1,'Classical ML and sentiment work are supported, but production LLM/RAG/agents and software engineering are weak.','No numeric minimum stated; senior title alone does not prove a duration conflict.',2,bima_rag,'Production LLM systems and agentic experience remain unproven; no explicit duration minimum.'),
      'F00020':(0,'This is a mentoring/training role, outside the four production AI/data target families, despite relevant Python/SQL and teaching evidence.','The v0 taxonomy assigns AI/ML engineering; the actual duties need human role review.',0,'This is a mentoring/training role, outside the four production AI/data target families; matching tools alone do not make it AI engineering.','The v0 taxonomy assigns AI/ML engineering; the actual duties need human role review.'),
      'F00029':(1,low_ai,'Around three to six years relevant engineering experience is not supported.',1,bima_rag,'Three to six years relevant engineering is not supported; marketing years are not automatically engineering years.'),
      'F00036':(1,'Statistics degree, Python/SQL and supervised ML are supported, but the professional duration is not.','Minimum two years professional DS or similar work is not supported.',1,'Python/SQL, forecasting and transformer work give partial coverage.','Two years professional DS or similar work is not established; marketing job relevance needs care.'),
      'F00052':(2,'Python, scikit-learn and ML projects support several key requirements; software fundamentals and Git use lack contextual evidence.','No numeric minimum; production experience is softened by preferably.',2,'Python, transformer/RAG applications, data processing and API projects support several core requirements; software fundamentals remain gaps.','Communication degree relevance or equivalent experience needs review; not assumed satisfied.'),
      'F00055':(1,'Statistics and sentiment work overlap, but professional DS duration and advanced LLM processing are weak.','Three to six years hands-on DS/applied AI is not supported.',1,'Sentiment and LLM projects overlap; the required professional DS/applied AI period remains unsupported.','Three to six years hands-on DS/applied AI is not established by marketing work.'),
      'F00066':(1,low_ai,'Minimum three years AI Developer or similar role is not supported.',1,bima_rag,'Minimum three years AI Developer or similar role is not supported.'),
      'F00074':(1,'Python/SQL are supported, but component-built RAG and production software evidence are weak.','Two years production software including one year shipping LLM apps is not supported.',1,bima_rag,'Two years production software including one year shipping LLM apps is not supported.'),
      'F00075':(1,'Data/ML projects do not demonstrate full-stack development, frontend or production deployment.','One year full-stack development is not supported.',1,'FastAPI/Docker and RAG provide partial backend coverage, but frontend/full-stack work is not evidenced.','One year full-stack development is not supported.'),
      'F00090':(1,'Python/SQL context is supported; backend development duration and production security requirements are not.','Minimum two years Python backend/software engineering is not supported.',1,'FastAPI/Docker and Python automation support part of the stack.','Two years Python-focused backend/software engineering work is not established.'),
      'F00103':(2,'Recent degree, GPA, Python/SQL and data cleaning support several qualifications; Azure, ETL orchestration and governance are gaps.','Full-time Yogyakarta commitment requires confirmation; not scored as a conflict.',2,'Python/SQL, API and embedding project work overlap; Azure and enterprise ETL/governance remain gaps.','Full-time Yogyakarta commitment and relevance of degree require review.'),
      'F00117':(1,'Classical data projects do not evidence full-stack chatbot application engineering.','Three years Full Stack AI Developer or similar role is not supported.',1,'FastAPI/Docker/RAG overlap, but React frontend and production full-stack history are not evidenced.','Three years Full Stack AI Developer or similar role is not supported.'),
      'F00126':(2,'Quantitative fresh-graduate background and Python are supported; actual LLM project experience is missing.','No minimum-duration conflict; LLM project experience is a gap.',1,'Python and RAG project fit the technology, but the quantitative degree/early-career eligibility wording is not clearly met.','Communication degree and more than two years prior professional work need review against the stated eligibility alternative.'),
      'F00176':(1,'Data analysis experience overlaps, but LLM/automation tooling and agent workflows are weak.','No numeric minimum; n8n preference is not a hard conflict.',2,bima_rag+' n8n/Make/Zapier automation and security controls remain gaps.','No numeric minimum; production and automation breadth are not assumed.'),
      'F00188':(3,'Statistics education, analyst internship, dashboard delivery and Python/R practice support most stated core qualifications.','Power BI is preferred; Looker Studio dashboard evidence can support general dashboarding.',2,'Marketing analytics, dashboard reports and Python/SQL support several core qualifications; independent statistical-test selection is less evidenced.','Degree relevance is uncertain; no numeric experience minimum.'),
      'F00189':(1,'Statistics and analysis basics overlap, but financial-domain senior experience is missing.','At least eight years relevant professional experience is not supported.',1,'Marketing analysis overlaps generally, but senior financial-services DS experience is missing.','At least eight years relevant professional experience is not supported.'),
      'F00208':(1,'Statistics/Python/R fit some foundations; principal-level production engineering does not.','Eight to ten years relevant experience is not supported; US residence is separately unconfirmed.',1,bima_rag,'Eight to ten years relevant experience is not supported; US residence is separately unconfirmed.'),
      'F00212':(1,'Python/classical ML provide partial evidence; GPU and distributed engineering are missing.','At least three years software or ML engineering is not supported.',1,'Transformer project gives some deep-learning evidence; CUDA and distributed engineering remain gaps.','At least three years software or ML engineering is not supported.'),
      'F00303':(1,low_ai,'At least two years relevant LLM/RAG/NLP/AI application work is not supported.',1,bima_rag,'At least two years relevant LLM/RAG/NLP/AI application work is not supported.'),
      'F00309':(3,'Python/SQL, statistics, ML and dashboard/presentation work support the preferred analytical competency profile.','One to three years appears under preferred qualifications; not treated as mandatory.'),
      'F00310':(1,'Foundational statistics/ML overlap is far below the extensive enterprise AI requirement.','Ten years DS or related experience is not supported.',1,bima_rag,'Ten years DS or related experience is not supported.'),
      'F00327':(1,'Analyst internship overlaps weakly; campaign automation and engineering requirements are not evidenced.','Three years performance/digital marketing analytics and automation is not supported.',2,'Three years marketing analysis, SQL/Python automation, A/B tests and later AI projects support several requirements; ad APIs, MMP tooling and AI-agent orchestration are gaps.','Do not treat marketing duration as three years AI engineering; compound wording needs review.'),
      'F00330':(1,'Data/ML academic projects do not evidence independent full-stack products used by real customers.','No numeric duration minimum; senior title is not an automatic conflict.',1,'A deployed API project overlaps, but real-user products, frontend ownership and regulated-space production work lack evidence.','No numeric duration minimum; senior title alone is not a conflict.'),
      'F00332':(3,'Statistics degree, Python/SQL internship, large transaction dataset and cohort analysis support most core requirements.','Credit scoring is a plus, not a hard requirement.'),
      'F00333':(1,'Statistics, logistic regression and Python/SQL are supported; long professional feature-engineering history is absent.','At least five years data exploration and feature engineering is not supported.',1,'SQL/Python, reporting and forecasting overlap; long professional feature-engineering history is absent.','At least five years data exploration and feature engineering is not supported.'),
      'F00354':(2,'Quantitative degree, Python/ML thesis and feature/evaluation work support several foundations; genetic algorithms, tuning and software interfaces remain gaps.','No numeric minimum; relocation and internship availability need confirmation.'),
      'F00364':(1,'The text mainly gives advanced industrial AI duties; quantitative basics alone provide weak evidence.','No explicit qualification section or duration; do not invent a hard minimum.',1,'NLP/RAG projects overlap broadly, but closed-loop industrial/edge modelling is not evidenced.','No explicit qualification section or duration; information sufficiency needs review.'),
      'F00366':(2,'Python/pandas/scikit-learn, SQL and ML projects support several basics; deep learning and model-deployment understanding are gaps.','Internship/project experience is an advantage, not a minimum duration.'),
      'F00369':(1,'Python/scikit-learn and modelling overlap, but professional duration and recurrent deep-learning engineering are lacking.','Two to four years hands-on ML/DS roles is not supported.'),
      'F00412':(2,bima_rag+' Automated regressions, safe fallbacks and agents remain gaps.','No numeric minimum; newer agentic specialization is explicitly welcome.'),
      'F00438':(1,'Dashboard and data analysis work overlap, but process mapping, SOPs and AI automation evidence are weak.','No explicit duration minimum.',2,'Marketing report automation, dashboard work and RAG support several areas; process mapping, SOPs and workflow-builder implementation are gaps.','No explicit duration minimum.'),
      'F00463':(1,'Foundational ML/sentiment projects do not support experienced chatbot fine-tuning/deployment.','Three to five years AI/ML work is not supported.',1,'Transformer fine-tuning and RAG support some technical requirements; production observability remains missing.','Three to five years AI/ML work is not supported.'),
      'F00505':(2,'Statistics/ML projects, Python/R and dashboard reporting overlap; managing a DS team and advanced predictive practice are gaps.','No numeric minimum; team-management evidence missing, not inferred from Lead title.'),
      'F00515':(2,'Statistics degree, modelling and Python/R/SQL support several core qualifications.','Typically/representative one to two years is softened; exact mandatory status needs review.'),
      'F00556':(1,'Statistical and Python/ML foundations fit, but current student status conflicts with completed degree.','Currently pursuing a degree is not met as of the CV reference period; Malaysian nationality remains unknown.'),
      'F00601':(1,'Classical ML, Python/SQL and data analysis overlap, but professional production-ML duration is not met.','At least three years DS/ML including API production deployment is not supported.',1,'Marketing A/B tests, Python/SQL and ML projects overlap partially.','At least three years DS/ML with production ML API experience is not established; relocation unknown.'),
      'F00624':(1,low_ai,'Minimum eight years software engineering is not supported.',1,bima_rag,'Minimum eight years software engineering is not supported.'),
      'F00650':(2,bima_rag+' Functional/integration tests and Redis remain gaps.','No numeric minimum; timezone availability requires confirmation, not an automatic conflict.'),
      'F00654':(1,'Python and ML projects overlap, but scaled production ML history is not met.','At least three years ML engineer/scientist deploying models at scale is not supported.'),
      'F00655':(2,'Statistics, Python/R and scikit-learn projects support several foundations; Java, software architecture and professional ML engineering remain gaps.','No numeric minimum; degree discipline relevance should be reviewed rather than guessed.'),
      'F00663':(1,'Statistics/Python and classical ML overlap, but senior AI breadth is not met.','Minimum five years AI/ML development is not supported.',1,'RAG/transformer projects overlap partly; advanced ML/cloud requirements remain gaps.','Minimum five years AI/ML development is not supported.'),
      'F00666':(1,'Data projects do not evidence system-design leadership, mentoring engineers or distributed architecture.','No numeric minimum; weak core engineering evidence, not title-based rejection.'),
      'F00686':(2,'Statistics degree, coded internship and large Python/SQL dataset work fit several requirements; AI-assisted workflows and cloud architecture are gaps.','US work eligibility is unknown, not assumed disqualifying.',2,'Campaign Python/SQL and A/B tests fit parts of the role; quantitative-degree, coded-internship and cloud architecture evidence are gaps.','US work eligibility is unknown; no duration minimum.'),
      'F00698':(2,bima_rag+' Gemini/Vertex, LangGraph and broader cloud deployment are gaps.','USA candidate eligibility is unverified; Indonesian residence alone is not work-authorization evidence.'),
      'F00798':(1,bima_rag,'Six years software engineering is not supported; no credit for unrelated marketing years.'),
      'F00815':(2,bima_rag+' Cloud deployment and CI/CD remain gaps.','Communication degree relevance needs review; no numeric duration minimum.'),
      'F00930':(2,'Statistics, Python/R and scikit-learn context fit the listed junior technical foundations.','TS/SCI with polygraph clearance is unverified; nationality or authorization cannot be inferred from location.'),
      'F00933':(1,bima_rag,'Two years professional Python development and two years AI/ML/GenAI solutions are not supported by contextual dated work.')
    }
    relevance = []
    for r in pool:
        if r['already_gold']=='yes':
            continue
        data = reasons[r['job_id']]
        # Single-CV tuples are intentionally only provided for jobs in that CV's pool.
        offset = 3 if r['cv_id']=='CV2' and len(data)==6 else 0
        label, reason, constraint = data[offset:offset+3]
        relevance.append(dict(cv_id=r['cv_id'],cv_target='Data Science / AI and data target families' if r['cv_id']=='CV1' else 'AI engineering / AI and data target families',
            pilot_id='', job_id=r['job_id'],job_title=r['title'],relevance_0_3=label,
            main_reason=reason,constraint_note=constraint,label_source='model_draft',
            review_status='pending',review_action='',draft_note='Guideline v1.2 Part D; evidence coverage and explicit qualifications, not retrieval score. Human review required.',
            review_note='',guideline_version='v1.2',gold_review=r['gold_review']))
    random.Random(20261001).shuffle(relevance)
    relevance.sort(key=lambda r:r['gold_review']!='yes')
    assert all(r['job_id'] in dev for r in relevance+units)
    assert all(r['source_quote'] in jobs[r['job_id']]['description_clean'] for r in units)
    assert all(jobs[i]['jd_quality']=='full' and jobs[i]['clean_length']>=1500 for i in SELECTED)
    output = dict(selected=SELECTED,reasons=REASONS,units=units,relevance=relevance,cvs=cvs,
        jobs={id:jobs[id] for id in sorted(set(SELECTED)|{r['job_id'] for r in pool})},
        source_hashes={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in [
            'data/processed/jobs_features.jsonl','evals/pools/dev_pool.csv','evals/gold/relevance_gold.csv',
            'evals/annotation_guideline_v1.md','evals/pilot/JobFit_Pilot_Labeling_v0.1.xlsx']})
    dest=root/'evals/labeling/drafts/development_review_v1.json'
    dest.parent.mkdir(parents=True,exist_ok=True)
    if (root/'evals/labeling/dev_batch_01.xlsx').exists() or (root/'evals/labeling/dev_batch_02.xlsx').exists():
        raise ValueError('review workbook exists; do not overwrite reviewed drafts')
    dest.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(units={i:sum(r['job_id']==i for r in units)for i in SELECTED},
        relevance_rows=len(relevance),gold_review_rows=sum(r['gold_review']=='yes'for r in relevance))))


if __name__=='__main__':
    main()
