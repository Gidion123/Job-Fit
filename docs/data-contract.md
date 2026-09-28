# JobFit: Data Contract (draft v0)

**Date:** 26 September 2026 · **Applies to:** JSearch corpus snapshot `CP1_20260926` · **Status:** CP1 v0.1 implementation, audited 26 September 2026; labels are a rule-based baseline, and accuracy will be measured against the CP2 gold set.

Unit of analysis: **1 final job posting** = 1 cluster after dedup. Each cluster has one canonical record (the most complete JD). The other records in the cluster are kept for provenance.

## Principles

1. **Raw is never changed.** Everything derived can be rebuilt from `data/raw/` with `scripts/build_corpus.py`.
2. **UNKNOWN ≠ match.** Missing values are stored as empty/`None`. They are not silently imputed.
3. **`posted_at` is never replaced with `retrieved_at`.** A date derived from relative text must carry a flag that shows its source.
4. **Provider flags are not the single source of truth** (e.g. `job_is_remote`, `job_apply_is_direct`).
5. **All rule-based features are provisional**, including field names without the `_provisional` suffix. Versions are stored, not accuracy scores.
6. **JD text is untrusted data.** An LLM never treats it as instructions.

## Layer 1: Record (1 row per API result slot) · `data/interim/jsearch_records.jsonl`

| Field | Type | Source | Rule / meaning of an empty value |
| --- | --- | --- | --- |
| record_id | str | derived | `<response file name>#<position>`; stable as long as raw does not change |
| source_file | str | derived | relative path of the raw response |
| batch | str | derived | BENCHMARK, COL, B01…B07 |
| query_id, bucket, query, query_country, query_language, page | str/int | request metadata | `bucket` = query stratum (indonesia, remote_candidate, foreign_comparison, role_contrast); **not a job label** |
| retrieved_at_utc | str (ISO) / None | request metadata | None for manual responses that did not record the time |
| source_provider | str | constant | `jsearch` |
| source_platform | str | `job_publisher` | original publisher (LinkedIn, Glints, JobLeads, …) |
| source_job_id | str | `job_id` | provider id; can change across queries for the same job posting |
| job_uid | str | `job_uid` | extra dedup key |
| apply_url, google_url | str | `job_apply_link`, `job_google_link` | apply_url is often an aggregator |
| apply_is_direct | bool | `job_apply_is_direct` | provider flag; all `false` in this snapshot |
| company, title | str | `employer_name`, `job_title` | raw |
| location_raw | str | `job_location` | publisher location text |
| city, country | str / None | `job_city`, `job_country` | often empty; do not use without normalization |
| is_remote_flag | bool | `job_is_remote` | ≠ eligibility to work across countries |
| employment_type | str / None | `job_employment_type` | values in mixed languages; normalized in Layer 3 |
| provider_posted_text | str / None | `job_posted_at` | relative text, stored as is |
| posted_at | str / None | `job_posted_at_datetime_utc` | None when the provider gives no timestamp |
| salary_present | bool | `job_min/max_salary`, `job_salary` | |
| description | str | `job_description` | raw JD text |
| description_length | int | derived | characters after strip |
| content_hash | str / None | derived | SHA-256 of the normalized text (≥200 characters) |
| jd_quality | enum | derived | `full` ≥700 · `summary_only` 200-699 · `insufficient` <200 characters (heuristic) |
| provenance_flags | list | derived | `generic_external_form`, `low_provenance_publisher`, `apply_not_direct_per_provider` |
| geo_stratum | enum | derived | indonesia, foreign, remote_unverified, unknown (query + location text) |
| role_stratum_provisional | enum | derived | target_family, adjacent, wrong_role_content, other (title regex) |
| seniority_stratum_provisional | enum | derived | intern, junior_entry, senior_lead, unspecified (title regex) |
| cluster_id | str | derived | exact-key cluster (`C#####`) |
| final_cluster_id | str | derived | cluster after SAME decisions (`F#####`) |
| is_canonical | bool | derived | the most complete record in the final cluster |
| highlights | dict | `job_highlights` | empty on `/search-v2` in this snapshot |

## Layer 2: Dedup

- Automatic: exact keys `source_job_id`, `job_uid`, normalized apply URL, `content_hash`, `company_key + title + location`.
- Pair review (reviewed against the text evidence; dedup is still v0 and flagged for re-check): pairs from the company_title detector (title Jaccard ≥0.6, same employer) and the content detector (JD 5-gram Jaccard ≥0.5). Decisions are in `data/interim/dedup_decisions.csv`: `SAME` pairs are merged; `DIFFERENT` and `UNSURE` pairs stay separate.

## Layer 3: clean and features implementation (CP1.3-1.4)

`jobs_clean.jsonl` keeps 910 clusters. `jobs_features.jsonl` adds rule-based features. Both CSVs are practical versions without the full JD text. Feature lists in the CSVs are separated by semicolons. JSONL is the main structured contract, with JSON null for UNKNOWN. `is_auditable` selects 632 EDA candidates.

| Actual field | Meaning / limits |
| --- | --- |
| final_cluster_id, record_id, source_file | estimated cluster, canonical record and raw path for audit |
| job_uid, source_job_id, content_hash, google_url, apply_url | provider provenance; not a guarantee of identity or of an official link |
| query, query_country, bucket, geo_stratum | historical collection design; not a verified job location |
| description_clean, cleaning_rules, cleaning_version | masking of emails/Indonesian phone number patterns, HTML/tracking/noise, and the version; raw stays intact; not full anonymization |
| jd_language | en/id/mixed/other_script/unknown; heuristic |
| normalized_title | normalized title; role_family is still read from the original title |
| role_family | ai_ml_engineering, genai_llm, data_science, software_ai, data_analytics, data_engineering, software_general, other_tech, business_product, content_marketing, annotation_labeling, other |
| role_group | target / adjacent / non_target |
| title_seniority | intern / junior / mid / senior / lead_plus / unspecified |
| years_min, years_max, years_evidence | highest per-mention minimum near an experience cue, plus the span; max is only the upper end of an explicit range, null for 5+ or when there is no range; does not yet separate required/preferred/alternative; values >15 are ignored (conservative baseline) |
| entry_level_signal, entry_evidence | keywords such as fresh graduate/intern/etc.; can still be wrong for the context |
| experience_bucket | entry / 1-2y / 3-4y / 5y+ / not_stated; an explicit minimum of 0 goes into entry |
| country_code, country_source | provider field or location text; query country is not used as a fallback |
| city_normalized, metro, location_granularity | Indonesian city/Jabodetabek (Greater Jakarta) based on text; not verified geocoding |
| analysis_geo | indonesia / foreign / remote_unverified / unknown; mutually exclusive, the remote probe is kept separate |
| location_conflict, cluster_location_conflict | country does not match the stratum/city; several countries/cities in one cluster, needs review |
| work_mode | onsite / hybrid / remote / remote_mentioned / unknown; heuristic from title/provider/text |
| remote_eligibility | indonesia_explicit / global_explicit / apac_explicit / restricted_other / unknown / not_applicable; historical name, word signals only, does not confirm permission to work |
| employment_type_normalized | full_time / contract / internship / part_time / unknown |
| skills, n_skills | list of skill aliases and their count; mentioned, not required; openai_api covers OpenAI/GPT mentions, not proof of API use |
| education_levels | diploma / bachelor / master / phd (list); [] means not detected, not "no requirement"; required/preferred not separated yet |
| first_seen_at, last_seen_at | min/max observation timestamp within the cluster |
| posted_at, provider_posted_text | original provider fields |
| posted_at_derived, posted_at_source | ISO date, provider_structured/relative_text/unknown; a relative date must be tied to the timestamp of the same record |
| posted_at_reference_time, posted_at_reference_record | date provenance; reference_time is only for relative dates |
| age_days_at_first_seen | gap between the first observation and the estimated posting date; not a check that the job is active, can conflict if publishers differ |
| experience_entry_conflict, experience_title_conflict | entry and 3+ signals together, or a senior/lead title with a low minimum; review candidates |
| experience_preferred_or_alternative | preference/alternative words in the span; broad triage, not confirmed errors |
| dedup_unsure | cluster linked to an UNSURE pair |
| taxonomy_version, skill_alias_version | feature versions used |

`CP1_human_review_queue.jsonl` holds review candidates only, not gold labels. `CP1_research_summary.json` stores the populations, numerators/denominators, tables per role/bundle, the role × length standardization, runtime and input/code hashes.

### Lineage flow

```text
235 responses + metadata (460 hashed files)
  -> 1,314 slot records + exact keys
  -> 937 clusters + 40 dedup decisions
  -> 910 final clusters (frozen snapshot)
  -> cleaning and provenance (910)
  -> rule-based feature transformation (910)
  -> is_auditable filter (632)
  -> mutually exclusive EDA groups + 14 figures + summary JSON
  -> review queue candidates, not the gold set
```

### Embedding-derived table design for CP2 (not implemented yet)

One chunk stores `chunk_id`, `final_cluster_id`, `record_id`, `source_file`, `section`, `text`, `text_sha256`, `chunking_version`, `embedding_model`, `embedding_dimensions`, `embedding`, and a creation timestamp. Idempotency key: text + chunking version + model. Embeddings do not replace the evidence text or the structured requirements. The whole-job versus section-aware strategy and the model/dimensions will be chosen through experiments. No dummy vectors are created in CP1.

## Layer 4: LLM extraction (CP2, not CP1)

`required_requirements[]`, `preferred_requirements[]`, `required_skills[]`, `preferred_skills[]`, `years_experience`, `seniority`, `education`, `responsibilities[]`, `location_constraints`, `work_authorization`, plus confidence and span provenance. Validated with Pydantic; prompts are versioned.

## Usage policy

- OpenWeb Ninja terms apply. The raw corpus is not published without a terms review. A public repository only needs the code, manifests, aggregate statistics, and small examples.
- The API key is never written to a file, log, or response.
