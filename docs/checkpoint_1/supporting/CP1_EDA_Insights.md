# JobFit: CP1.6 EDA Insights

Audit date: 26 September 2026. Sources: `notebooks/01_research.ipynb` and `data/processed/CP1_research_summary.json`. Populations: AUD=632, TGT=428, ID_T=175, FOR_T=186, REM_T=57, UNKNOWN_T=10.

## Findings worth presenting

| Finding | Evidence and denominator | Implication |
| --- | --- | --- |
| The title is not enough for seniority | 128/405 JDs without a level contain a 3+ year signal | Read the JD requirements and evidence; the title is not an automatic rejection |
| The early-career pool is limited | 49/175 Indonesia targets have an entry/≤2 year signal; 69 have a 3+ signal; 57 UNKNOWN | Qualification needs skills, education, location and CV evidence; the 49 are not verified matching jobs yet |
| Level word filters can be too narrow | 37/49 of the early-career pool have no level marker in the title | Does not measure API recall; test retrieval in CP2 |
| AI in the title can be the wrong role | 49 of **463 AI titles**, in 910 clusters; 29 EDA candidates | Hard-negative seeds, not gold labels yet |
| Skills differ by role | Statistics 78% for DS (n=131) versus 2% for GenAI (n=50) | Insights and gaps per role family |
| GenAI skills are often mentioned together | RAG 53% in JDs with LLM (n=180) versus 4% without LLM (n=248); agents 58% versus 12% | Test grouping in explanations; not proof of required skills or causality |
| Part of the regional gap remains after standardization | ID n=151, foreign n=172; SQL +8.8 and ML -23.7 percentage points | Report patterns within the corpus, not claims about the whole market |
| General claims about GenAI are not stable | After adjustment: LLM -2.1, RAG +3.2 points | Role/length composition matters; do not conclude that all GenAI is lower |
| Education needs to be read in context | Bachelor 28/49; master 6/49; no level 19/49 | Mentions are not yet split into required/preferred; evaluate in CP2 |
| Location is concentrated, many work modes are unknown | Jabodetabek (Greater Jakarta) 79.6% in the Indonesia group; unclear mode 76.3% | Explicit eligibility can be a gate; UNKNOWN needs clarification |
| Metadata and sources limit the analysis | Structured date 30%, salary 3%; 109 publishers, top 5 54.4% | Show provenance, UNKNOWN and source bias |

## Regional comparison method

Figure 10 shows **raw** percentages. The notebook also shows a restriction to the 1,500-4,000 character range and a stronger sensitivity analysis: direct standardization by role × five length bins (<1500, 1500-2499, 2500-3999, 4000-5999, ≥6000). A cell needs ≥3 JDs per region. Weights use the combined population in the 12 cells that both regions support.

The adjusted results cover 151/175 ID_T and 172/186 FOR_T. Software AI is not covered because its cells are too small. Publisher, employer, language, seniority, and length variation within a bin are not matched yet. This is descriptive; it does not prove significance or cause and effect. The full numbers, skill numerators/denominators per role, bundles, the pool, and the weights are stored in the summary.

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
