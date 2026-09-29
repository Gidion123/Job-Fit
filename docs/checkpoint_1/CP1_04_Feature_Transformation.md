# CP1.4: Data Manipulation and Feature Transformation

**Status:** baseline features saved; labels are rule-based v0 (their accuracy will be measured against the CP2 gold set).  
**Version:** `role_taxonomy_v0.1_audited`, skill aliases `v0`.  
**Implementation:** notebook section 3 and the `src/jobfit/jobs/` modules (moved from `src/jobs/` on 29 Sep 2026).

## 1. Goal of this stage

A clean JD is still just text. To use it for filtering, retrieval, analysis, and requirement checks, the text has to be turned into fields with consistent definitions. The CP1 transformation uses deterministic rules so it is easy to audit and can serve as the baseline for the CP2 extractor.

Rule-based fields are not treated as final truth. Every important feature needs provenance or evidence, and information not found yet stays UNKNOWN. The transformation also does not change the raw text or the frozen product decisions.

## 2. Features created

| Feature | How it is built | Used for | Limits |
| --- | --- | --- | --- |
| normalized_title | Remove noise and separators | Retrieval/inspection | Role family still uses the original title |
| role_family and role_group | Ordered title rules | EDA and the baseline role gate | The job function can be ambiguous from the title |
| title_seniority | Words intern/junior/mid/senior/lead | Extra signal | Not evidence of a mandatory requirement |
| years_min/max and evidence | Numbers near experience cues | Minimum signal and JD checks | Preferred, alternatives, and multi-level are not separated yet |
| entry signal | Keywords fresh graduate/intern/etc. | Finding signs of early-career experience | Can refer to another context in the text |
| location and analysis_geo | Country field/publisher text | EDA population and possible filter | Query country is not a location; conflicts need review |
| work_mode and remote signal | Title, provider flag, JD words | Preference / candidate for eligibility checks | Remote does not mean worldwide |
| skills and n_skills | 64 canonical skills with aliases | Skill frequency and possible matching | Mentions are not split into required/preferred yet |
| education_levels | Patterns for diploma/bachelor (S1)/master (S2)/PhD | Pool profile and extraction candidates | No field of study or mandatory requirement yet |

There are 4 target roles: AI/ML engineering, Data Science, GenAI/LLM, and software AI. Adjacent and non-target roles are still kept to check wrong-role cases; they are not dropped just because they are not the user's main goal.

## 3. Why does rule order matter?

The title “AI Content Creator” contains AI, but the job function is not AI engineering. Content, business, annotation, and some other-tech patterns are checked before the generic AI pattern. The administrative case “Assistant Director (AI Specialist)” also goes to business_product, not target.

Baseline result: 428 targets out of 632 EDA candidates (AI/ML engineering 222, data science 131, GenAI/LLM 50, software AI 25). The remaining 204 are comparison roles: 131 adjacent and 73 non-target. Across all 910 clusters there are 49 non-target AI titles out of 463 AI titles, and 29 of them are EDA candidates. The breakdown is business/product 26, content/marketing 13, QA/IT 5, and data annotation 5.

**Insight:** about 1 in 10 titles that mention AI are not actually AI engineering jobs. A system that only matches words would rank jobs like these high, because their words look similar to an AI engineer's CV. So the AI keyword is not enough to decide the job function. However, this classification still needs to be assessed against the JD content in the gold set.

## 4. Experience: numbers must be read in context

**Main finding:** 405 of 632 EDA candidates (64%) do not state any level in the title. Of those 405, 128 (31.6%) mention 3+ years: 83 mention 3-4 years and 45 mention 5+ years. Even a "junior" title is not always safe, because 7 of 33 mention 3+ years. This means that if a beginner reads only the title, about 1 in 3 jobs without a level turn out to be too senior. This matches the complaint in the pilot interview, so the seniority gate must read the requirement in the JD body and show the quote.

For the sentence “minimal 5 tahun di ML dengan 2 tahun memimpin tim” (at least 5 years in ML with 2 years leading a team), the old rule that took the smallest number gave 2. Now the highest per-mention minimum is chosen, which is 5. `years_max` only stores the upper end of an explicit range; “5+ tahun” (5+ years) is not given a fake max of 5.

A minimum of 0 is also read. Case F00019 has a range of 0 to 4 years, so it gets an entry signal. That range does not mean every beginner meets the other requirements. This example shows why minimum years help screening but are not enough to call someone qualified.

Remaining weaknesses: a JD can mention fresh graduate for one position and 3 years for a senior position, or 5 years as a preference. The highest mention can be too strict. Numbers above 15 are ignored by the conservative baseline; negation, candidate age, and company context are also not handled perfectly yet. CP2 needs to separate requirement scope, required/preferred, and alternatives.

## 5. Location, skills, and education

Case F00157, a TikTok intern job in Los Angeles with country `US`, was previously counted as Indonesia because of the query. The fix gives priority to the provider's country evidence. Targets are now split into Indonesia 175, foreign 186, remote query 57, and country UNKNOWN 10. The old collection strata are still available so the history is not lost. Countries of EDA candidates: Indonesia 372, Singapore 115, Malaysia 51, Philippines 15, US 10, and 69 with no country evidence.

A remote job cannot always be applied for from Indonesia. Of the 85 jobs checked for remote eligibility, only 3 mention Indonesia, 3 mention APAC, 10 mention worldwide, 11 are limited to other countries (for example, a US work permit is required), and 58 are unclear. These signals are only words in the JD and still need verification.

Skill aliases merge variants like Postgres/PostgreSQL. With 64 canonical skills, 93% of EDA candidates mention at least one skill, with a median of 6 skills per JD. This 93% is dictionary coverage, not extraction accuracy. The short names R and Go use special patterns so they are not counted from R&D or “go beyond”. The historical field `openai_api` can also come from a mention of OpenAI/GPT, so the analysis label does not claim that all of it is API experience.

Education is stored as a list. One JD can mention both bachelor and master, so the level percentages do not have to add up to 100%. This can reflect alternatives or preferences; it must not be turned into a conclusion that applicants must have every level.

## 6. Lineage and derived schema

```text
Raw response + request metadata
  → record_id + source_file + source_job_id + hash
  → final_cluster_id and canonical record
  → description_clean + cleaning rules + source timestamp
  → role/experience/location/skill/education features + version
  → EDA candidates + flags for the review queue
```

A full example record with evidence is in notebook 3.6. There, the JD "Backend Engineer (AI Engineer)" from Glints in Surabaya becomes a record with role ai_ml_engineering, an experience signal of 1-3 years (bucket 1-2y) with the quote "1-3 years experience as a Backend Engineer", 9 skills (including Python, Docker, LLM, PostgreSQL), and posting date UNKNOWN. The fields `record_id`, `source_file`, and `final_cluster_id` make it possible to trace the record back. The experience quote is kept; the number alone is not enough to check extractor errors.

The CP2 requirement schema is planned to separate required/preferred, skills, years, education, responsibility, location/authorization, confidence, and evidence span. The embedding table is designed to have chunk ID, job/record ID, section/text/hash, chunking version, model, dimension, embedding, and timestamp. Both are still designs, not evaluated model outputs.

## 7. Review and outputs

There are 260 EDA candidates with at least one review flag. Almost all of them (251) are flagged because their experience quote contains words like "preferred", "or", or "atau" (or). The rest are for senior/lead titles with a low experience signal (9), different locations within one cluster (5), an entry signal but a mention of 3+ years (2), UNSURE dedup pairs (2), and a location conflict (1). One job can have more than one flag. The "preferred/atau" word filter is broad on purpose so important cases are not missed, so **260 is not a count of confirmed errors**. The queue helps choose cases to check; it does not replace annotation.

- [jobs_features.jsonl](../../data/processed/jobs_features.jsonl): text, structured features, and provenance.
- [jobs_features.csv](../../data/processed/jobs_features.csv): table inspection without the full text.
- [Review queue](../../data/processed/CP1_human_review_queue.jsonl): review candidates, not gold labels yet.
- [Data contract](../data-contract.md): fields, lineage, and the embedding table design.

**Acceptance:** a sample JD can be turned into a consistent, traceable record. LLM-based JobRequirements are still CP2 work; baseline fields are not claimed to be equal to annotated results.

**Next:** [CP1.5: EDA](CP1_05_EDA_Distribution_and_Visualization.md).
