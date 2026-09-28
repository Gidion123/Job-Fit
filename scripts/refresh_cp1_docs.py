#!/usr/bin/env python3
"""Refresh CP1 inventory and insight notes from notebook-produced summary, offline."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def render():
    s = json.loads((ROOT/'data/processed/CP1_research_summary.json').read_text())
    pop=s['populations']; pool=s['experience_screen_pool_ID']; e=s['experience_bucket_ID_T']; st=s['geo_skills_standardized']
    bachelor=pool['education_mentions']['bachelor']['n']; master=pool['education_mentions']['master']['n']
    def delta(k): return f"{st['skills'][k]['difference_pp']:+.1f}"
    table='\n'.join(f"| {g} | {r['target']} | {r['adjacent']} | {r['non_target']} | {sum(r.values())} |" for g,r in s['geo_by_role_group'].items())
    experience='\n'.join(f"| {g} ({pop[g]}) | "+' | '.join(str(r.get(k,0)) for k in ['entry','1-2y','3-4y','5y+','not_stated'])+' |' for g,r in s['experience_by_population'].items())
    inventory=f'''# JobFit: CP1 Dataset Inventory

Audit date: 26 September 2026. Collection is **CLOSED**. Source of the EDA numbers: `data/processed/CP1_research_summary.json`, produced by `notebooks/01_research.ipynb`. v0.1 labels are a rule-based baseline; accuracy will be measured against the CP2 gold set.

## 1. Corpus and sources

| Metric | Value |
| --- | ---: |
| Stored responses | 235 |
| API result slots | 1,314 |
| Exact-key clusters | 937 |
| Final clusters after dedup decisions | 910 |
| EDA candidates (`is_auditable`) | 632 |
| JD full / summary / insufficient | 667 / 236 / 7 |
| Full JDs held back for a generic external form | 35 |
| EDA candidate publishers | {s['publishers']['n']} |
| EDA candidate employers | 505 |
| Collection period | 25 to 26 September 2026 |

Exclusive funnel: **910 = 236 summary + 7 insufficient + 35 full held back + 632 EDA candidates**. `full` means a length of ≥700 characters, not a JD that has been checked as complete. `auditable` means a candidate for analysis/review, not a verified job posting or one that is sure to be active. Final clusters are an estimate of the number of job postings. False merges and remaining duplicates are still possible.

JSearch/OpenWeb Ninja `/search-v2` is used as **provisional**. Techmap is **deferred** because of checkout problems and has no benchmark data results yet. Greenhouse/Lever are not used yet. The final provider choice is still OPEN, as stated in the Canonical.

Collection stopped because the yield on the Indonesia queries tested in B07 was only 6 new full JDs in 26 successful responses (0.23/request; 17 empty). This is a limit observed for those queries, sources and times, not proof that the whole Indonesian supply is used up. The 1,000 target is not filled up with foreign jobs just to reach the number.

## 2. Provenance and dedup review

- 460 raw/response and metadata files were verified with SHA-256 against the original manifest.
- Five frozen derived files were verified with the extra manifest `RESEARCH_INPUT_HASHES.json`. The original manifest was not changed.
- An offline rebuild from raw produced records, canonical CSV and probable-review CSV identical to the snapshot. The progress creation timestamp changed, as expected.
- 40 **dedup decisions**, reviewed against the text evidence: 29 SAME, 8 DIFFERENT, 3 UNSURE. The 29 SAME edges remove 27 clusters because some edges are redundant. Dedup is still v0; the 3 UNSURE pairs are flagged for re-check.
- All raw data, decisions, batch audits and snapshots are kept. The canonical source is chosen by heuristic length/quality, not by publisher authenticity.

## 3. Collection history

| Batch | Responses | Slots | Final clusters first seen |
| --- | ---: | ---: | ---: |
| Benchmark | 8 | 40 | 35 |
| COL01/02 | 2 | 8 | 8 |
| B01 | 12 | 47 | 43 |
| B02 | 12 | 80 | 62 |
| B03 | 23 | 131 | 90 |
| B04 | 34 | 208 | 130 |
| B05A | 1 | 27 | 24 |
| B05 + resume | 80 | 469 | 332 |
| B06 | 31 | 228 | 136 |
| B07 + resume | 32 | 76 | 50 |

The log records 4 failed requests (3 timeouts, 1 HTTP 500). Historical cost: free quota 198/200 units and PAYG 34 requests, about US$0.17, based on the collection notes; this is not a current price offer. **This audit did not send any API requests.**

## 4. EDA populations after the location fix

`geo_stratum` keeps the old collection design. `analysis_geo` uses the country field or the publisher location text; the query country does not fill in an empty country. The remote probe becomes a separate group. TikTok Los Angeles (`US`) is removed from the Indonesia group. Ten targets without location evidence become UNKNOWN.

| analysis_geo | Target | Adjacent | Non-target | Total |
| --- | ---: | ---: | ---: | ---: |
{table}

Total targets: {pop['TGT']}; all candidates: {pop['AUD']}. Compared with the initial plan, coverage of Indonesia and verified remote jobs is still short. In total, 60 candidates from remote queries are not yet verified as open to applicants from Indonesia.

## 5. Experience signals

| Group | Entry | 1-2 years | 3-4 years | 5+ years | Not detected |
| --- | ---: | ---: | ---: | ---: | ---: |
{experience}

Indonesia early-career pool: **{pool['n']}/{pool['of']}**, based on entry/≤2 years. This is **not** a set of job postings that surely fit fresh graduates. There are {e['3-4y']+e['5y+']} signals of 3+ years and {e['not_stated']} UNKNOWN. The highest per-mention number can still come from a preference, an alternative or a multi-level posting. Titles without a level that have 3+ years: {s['title_unspecified_3plus']['n']}/{s['title_unspecified_3plus']['of']}.

{pool['title_seniority'].get('unspecified',0)} of the {pool['n']} jobs in the early-career pool have no level word. A bachelor's degree is mentioned in {bachelor}/{pool['n']}, a master's in {master}/{pool['n']}, and {pool['education_unknown_n']} have no detected education level. An education mention does not mean it is required. Pool members changed during the audit even though the total stayed 49: the Los Angeles intern left, and a Junior Data Scientist posting with 0 to 4 years joined.

## 6. Metadata and quality limits

- EDA candidates: structured city 20%, country 45%, date 30%, salary 3%, highlights 0%. The exact percentages are in the summary.
- All 910 clusters: provider date {s['posted_at_source']['provider_structured']}, relative {s['posted_at_source']['relative_text']}, UNKNOWN {s['posted_at_source']['unknown']}. Relative dates use the timestamp of the same record; 20 old estimates were dropped because the manual responses have no timestamp.
- EDA candidate languages: {s['language_auditable']}. This is a heuristic, not a measured classifier.
- Remote, direct-link, location, skill, education and seniority flags are rule-based v0, not gold labels. Masking covers only emails and Indonesian phone number patterns; it is not full anonymization.
- **{s['review_queue_n']} candidates** have a review flag. The preference/alternative flag is broad on purpose for triage; it is not a count of confirmed errors. Review queue: `data/processed/CP1_human_review_queue.jsonl`.

## 7. Next evaluation datasets (CP2)

| Set (per the Canonical) | Target | Status |
| --- | --- | --- |
| A. Raw Job Corpus | early CP1: 50-100 | 632 EDA candidates, collection closed |
| B. Extraction Gold | ±50 JDs | Not labeled yet |
| C. Evidence Matching | ±100 pairs | Not yet; needs synthetic CVs and labels |
| D. Ranking | 40-60 jobs, relevance 0-3 | Not yet; sampled from the corpus |
| E. RAG evaluation | 15-20 questions | Not yet |
| F. CV Safety | 20-30 scenarios | Not yet |
| G. Hard negatives | growing | Seeds: wrong-role, multi-level, seniority, location |

Separate development/regression from the held-out test before tuning. Cases already used to change the rules are not independent evidence of accuracy. Do not call the review queue a gold set.

## 8. Artifacts and reproduction

See `notebooks/README.md` to run the notebook from a clean kernel. All processed files and the 14 figures are produced by a single notebook. `docs/data-contract.md` explains the fields and provenance. `scripts/refresh_cp1_docs.py` keeps this document and the insights in sync with the summary.

Raw data and snapshots are not published without a terms review. Historical files in evidence explain the decisions made at the time; **the latest EDA numbers follow the summary and the audit**, not the old provisional numbers.

Next step: **PPT CP1.7**, mentor feedback, then the gold set and CP2 experiments.
'''
    insights=f'''# JobFit: CP1.6 EDA Insights

Audit date: 26 September 2026. Sources: `notebooks/01_research.ipynb` and `data/processed/CP1_research_summary.json`. Populations: AUD={pop['AUD']}, TGT={pop['TGT']}, ID_T={pop['ID_T']}, FOR_T={pop['FOR_T']}, REM_T={pop['REM_T']}, UNKNOWN_T={pop['UNKNOWN_T']}.

## Findings worth presenting

| Finding | Evidence and denominator | Implication |
| --- | --- | --- |
| The title is not enough for seniority | {s['title_unspecified_3plus']['n']}/{s['title_unspecified_3plus']['of']} JDs without a level contain a 3+ year signal | Read the JD requirements and evidence; the title is not an automatic rejection |
| The early-career pool is limited | {pool['n']}/{pool['of']} Indonesia targets have an entry/≤2 year signal; {e['3-4y']+e['5y+']} have a 3+ signal; {e['not_stated']} UNKNOWN | Qualification needs skills, education, location and CV evidence; the 49 are not verified matching jobs yet |
| Level word filters can be too narrow | {pool['title_seniority'].get('unspecified',0)}/{pool['n']} of the early-career pool have no level marker in the title | Does not measure API recall; test retrieval in CP2 |
| AI in the title can be the wrong role | 49 of **463 AI titles**, in 910 clusters; 29 EDA candidates | Hard-negative seeds, not gold labels yet |
| Skills differ by role | Statistics 78% for DS (n=131) versus 2% for GenAI (n=50) | Insights and gaps per role family |
| GenAI skills are often mentioned together | RAG 53% in JDs with LLM (n=180) versus 4% without LLM (n=248); agents 58% versus 12% | Test grouping in explanations; not proof of required skills or causality |
| Part of the regional gap remains after standardization | ID n={st['retained_n']['ID']}, foreign n={st['retained_n']['foreign']}; SQL {delta('sql')} and ML {delta('machine_learning')} percentage points | Report patterns within the corpus, not claims about the whole market |
| General claims about GenAI are not stable | After adjustment: LLM {delta('llm')}, RAG {delta('rag')} points | Role/length composition matters; do not conclude that all GenAI is lower |
| Education needs to be read in context | Bachelor {bachelor}/{pool['n']}; master {master}/{pool['n']}; no level {pool['education_unknown_n']}/{pool['n']} | Mentions are not yet split into required/preferred; evaluate in CP2 |
| Location is concentrated, many work modes are unknown | Jabodetabek (Greater Jakarta) {s['jabodetabek_pct_ID']:.1f}% in the Indonesia group; unclear mode {s['work_mode_unclear_pct_ID']:.1f}% | Explicit eligibility can be a gate; UNKNOWN needs clarification |
| Metadata and sources limit the analysis | Structured date 30%, salary 3%; 109 publishers, top 5 {s['publishers']['top5_pct']:.1f}% | Show provenance, UNKNOWN and source bias |

## Regional comparison method

Figure 10 shows **raw** percentages. The notebook also shows a restriction to the 1,500-4,000 character range and a stronger sensitivity analysis: direct standardization by role × five length bins (<1500, 1500-2499, 2500-3999, 4000-5999, ≥6000). A cell needs ≥3 JDs per region. Weights use the combined population in the 12 cells that both regions support.

The adjusted results cover {st['retained_n']['ID']}/{pop['ID_T']} ID_T and {st['retained_n']['foreign']}/{pop['FOR_T']} FOR_T. Software AI is not covered because its cells are too small. Publisher, employer, language, seniority, and length variation within a bin are not matched yet. This is descriptive; it does not prove significance or cause and effect. The full numbers, skill numerators/denominators per role, bundles, the pool, and the weights are stored in the summary.

## Decisions and limitations

- The Canonical still applies: ontology v1 is a light alias list; a knowledge graph, reranker and complex relations do not become new requirements because of the EDA.
- Rule-based labels are v0; their accuracy will be measured against the CP2 gold set. Preference/alternative, negation, multi-level, false entry mentions and mentions of candidate age can distort the experience signal. Numbers >15 are ignored (conservative heuristic).
- Text of ≥700 characters does not yet guarantee a complete or authentic JD. Dedup is still v0 (40 pairs reviewed against the text evidence, 3 UNSURE); these pairs are flagged for a spot-check.
- `analysis_geo` separates location evidence from the query. The ten targets with an UNKNOWN location are not forced into foreign.
- Query-based snapshot, one provider, two days: not a time trend and not a random sample of the market. Saturation applies only to the collection queries that were tested.
- No new data or API requests during the audit. The next priority is the CP2 gold labels, not forcing the 1,000 target.

## Figures and presentation steps

The 14 figures stay in `reports/figures/cp1/`. Pick 6 to 10 for the deck, for example:

1. `fig01_funnel.png`: dataset and unit of analysis.
2. `fig02_field_completeness.png`: reason for preprocessing/extraction.
3. `fig05_experience_requirement.png`: experience signals, not a claim of being qualified.
4. `fig06_title_vs_experience.png`: title versus JD content.
5. `fig08_skills_by_role.png`: insight needs per role.
6. `fig09_genai_bundle.png`: GenAI co-mention.
7. `fig10_skills_id_vs_foreign.png`: raw + adjusted table from the summary.
8. `fig13_realistic_pool_skills.png`: early-career pool and education; the historical file name is kept.

Next is **PPT CP1.7**: problem/evidence, dataset, cleaning/transformation, EDA, proposed architecture, baseline/metric, experiment plan and limitations. After mentor feedback, continue with the CP2 gold set and evaluation. No model score has been measured at the EDA stage.
'''
    (ROOT/'docs/checkpoint_1/supporting/CP1_Dataset_Inventory.md').write_text(inventory)
    (ROOT/'docs/checkpoint_1/supporting/CP1_EDA_Insights.md').write_text(insights)
    print('Refreshed inventory and insights from CP1_research_summary.json')

if __name__=='__main__':render()
