# CP1 corpus expansion: 1,000 varied job descriptions

**Status:** Expansion target I approved on 26 September 2026. This extends the *quantity and diversity of the job corpus*. It does not change the frozen v1 user (early-career, Indonesia-first), provider decision gate, or evaluation-set definitions. The Playbook's 50-100 jobs remains the first Checkpoint 1 acceptance milestone, not a maximum.

## Counting rule

The 1,000 target means **1,000 distinct, auditable job descriptions**, including relevant target-role jobs and deliberately retained contrast / hard-negative jobs. An API result slot is not a job count. A record enters this total only when it has a usable title, employer, location or explicit remote status, substantive JD, source URL, source provider, collection timestamp, and deduplication decision. Missing or unverified posting dates, active status, salary, and international work eligibility remain `UNKNOWN`; do not infer them from query text. Each raw response stays intact.

Track separately: raw slots; structurally valid records; distinct vacancies; target-role records; contrast/hard-negative records; verified original-source records; manually labeled evaluation records. Gold evaluation sets remain separate and must not be measured on examples used to tune the same component.

## Provisional sampling targets (all three axes describe the same 1,000 jobs)

| Axis | Proposed target | Interpretation |
| --- | --- | --- |
| Role | 800 target-family AI/ML/Data Science/AI-app or Software-AI; 200 adjacent/wrong-role contrast | Actual labels come from JD review, not from query terms. General Data Analyst is contrast unless the inclusion rubric establishes compatible AI/ML responsibilities. |
| Seniority | 400 entry/junior; 250 mid; 250 senior/lead; 100 ambiguous | Senior jobs are valuable for seniority hard negatives. This does not make senior professionals v1 users. |
| Geography | 600 Indonesia; 200 international remote with Indonesia eligibility *verified*; 200 foreign-market comparison | A remote flag alone does not prove Indonesia eligibility. If 200 verifiable remote jobs cannot be found, report the shortfall rather than relabeling unknown cases. Foreign local-only comparison jobs are excluded from eligible recommendations. |

These are **targets for coverage**, not claims that the provider will return such a distribution. Monitor intersections (e.g. junior × Data Scientist × Indonesia) and avoid interpreting sparse cells as market prevalence. Report source, query, geography, and time-window bias. Online postings are not a probability sample of all jobs.

## Collection stages and gates

1. **Seed / first acceptance:** finish 50-100 unique, auditable jobs while defining schema, provenance, and inclusion rubric. Existing benchmark and COL01-02 responses are candidates, not automatically accepted jobs.
2. **Pilot 20-30 requests across strata:** record raw slots/request, unique usable jobs/request, duplicate rate, JD completeness, source quality, and quota consumed. Use cursor pagination for queries with useful yields. No paid-plan decision from the two existing collection requests alone.
3. **Scale to 300 → 600 → 1,000:** allocate additional requests to undercovered strata. Stop or revise queries with poor yield or repeated low-quality sources. Recompute actual quota and cost from measured yield after each batch.
4. **Manual audit:** review all questionable dedup/provenance cases and a stratified sample of otherwise accepted records; the 1,000 count requires a documented quality decision for each record. Freeze evaluation subsets separately.

## Data quality and safety gates

- Preserve `source_provider`, `source_platform`, `source_job_id`, source/apply URL, query/parameters, `retrieved_at`, raw posting text, and content hash.
- Normalize country, city, role family, seniority, work mode, and explicit work-eligibility evidence; keep unknowns explicit.
- Deduplicate by provider ID, normalized URL, then company/title/location and content-similarity review. Different URLs can represent the same vacancy.
- Flag a short or polluted JD, source/ATS mismatch, generic third-party application forms, suspicious redirects, and missing original-employer evidence. Do not promote a questionable link to a trusted apply destination.
- Distinguish `posted_at` from `first_seen_at`; do not manufacture absolute dates from relative text. A returned posting is not proof of current availability.
- Store API keys only outside the project; never write credentials into raw responses, logs, screenshots, or commits.
- Set a per-run request cap and no automatic paid retry. Check actual plan/overage terms before raising the cap.

## Cost and feasibility

As checked on 26 September 2026, [OpenWeb Ninja's JSearch pricing page](https://www.openwebninja.com/api/jsearch) lists 200 free requests/month, direct-portal Pay As You Go at USD 0.005/request, and Pro at USD 25/month for 10,000 requests; account/RapidAPI terms may differ. The provider recommends cursor pagination for `/search-v2`. These are published rates, not a purchase or an estimate of the project's final bill. Pilot yield, deduplication, and manual review time determine the real cost of 1,000 usable jobs.

Detailed scenarios, deployment usage, and the JSON-first evidence standard are in [JSearch Cost and Evidence Policy](CP1_JSearch_Cost_and_Evidence_Policy.md). I ran the 12-query Basic-plan pilot on 26 September: 47 raw slots, six empty queries, and all 12 responses verified. See the [pilot audit](../../../evidence/checkpoint_1/corpus_collection/CP1_JSearch_Pilot01_Audit.md). Batch 02 is prepared for up to 12 further Free/Basic-only requests; it has not yet run.

## Current position

COL01 and COL02 each returned four slots. COL01 yielded one conditional core Data Scientist job; COL02 yielded no confirmed core Data Scientist job and surfaced adjacent roles and probable cross-source duplication. This is evidence that 1,000 *raw slots* would overstate actual corpus size. Techmap remains access-blocked; JSearch is provisional, not a frozen final provider choice.

On 26 September, the reproducible seed inventory covered 10 archived JSearch responses and 48 raw slots. It found 43 distinct normalized company/title/city keys, 10 descriptions under 500 characters, 36 records without both city and country, and no structured posting timestamp in any of the 48. These are automated flags and preliminary keys, **not** accepted-job counts. See [`CP1_JSearch_Seed_Inventory.json`](../../../data/research/CP1_JSearch_Seed_Inventory.json).

## Reproducible collection commands

The [query manifest](../../../data/research/CP1_JSearch_Query_Plan.csv) contains 113 diverse probes. A 12-query first pilot spans all four buckets and several role/seniority combinations. The runner caps this pilot at 12 API requests, makes no automatic retries, preserves raw JSON, and never writes the API key into project files.

```bash
cd project-job-fit
python3 scripts/jsearch_collection.py collect --pilot --max-requests 12
python3 scripts/run_jsearch_pilot.py
python3 scripts/jsearch_collection.py inventory
```

The first command is a dry run. The second asks for the existing **OpenWeb Ninja direct-portal** JSearch key through a hidden local Terminal prompt and sends the capped pilot requests. Do not paste the key into chat, screenshots, project files, or shell command arguments. RapidAPI keys use different authentication and are not accepted by this runner. If network access or an active plan is unavailable, the runner stops without retries; record that as a blocker. The third command refreshes the inventory after collection. Check the provider's current pricing and quota in the account before any paid tier change or larger batch.

The collector checks the provider's `/usage?api_id=jsearch` endpoint before sending a batch and reduces a Free-plan batch to the verified remaining quota. It refuses to collect if the Free-plan quota cannot be verified. The first pilot remains 12 requests; inspect its yield before using the rest of the Basic quota. No automatic plan upgrade is performed.

## Update after Pilot 01 (26 September 2026)

Pilot JSON and metadata are saved in data/raw/jsearch. The refreshed inventory includes 22 archived responses and 95 raw slots; 88 company/title/city heuristic keys are not accepted-job counts. Full pilot JD review produced 11 target candidates, 15 contrast candidates, 20 holds and 1 insufficient-JD rejection, pending source/deduplication admission. Two pilot slots repeat previous COL01 evidence and one internal pair has identical content. See the pilot audit for precise limitations.

The next adaptive [batch manifest](../../../data/research/CP1_JSearch_Batch02_Plan.json) removes seniority prefixes in matched queries and increases Indonesia coverage. The original 113-probe manifest remains historical. Run `python3 scripts/run_jsearch_batch02.py` for at most 12 requests with a hidden local key prompt; this runner refuses paid plans. No new request has been sent during preparation of this batch.

## Composition and budget decision (26 September 2026, after B05)

Evidence: after B05, there were 497 auditable candidates (Indonesia 293 · foreign 159 · remote_unverified 45). New Indonesia probes gave only ±1.5 new complete JDs per request, and the number was going down. The other groups gave 4-9 per request. Remote jobs with verified Indonesia eligibility were almost zero.

**My decisions:**

1. **Report the shortfall, do not patch it.** Indonesia is collected as much as possible from JSearch. Foreign comparison, remote, and contrast each go only up to ±200. The final total will likely be ±700-800, not 1,000. The Indonesia and verified-remote shortfalls are reported as findings about source coverage. Foreign job postings are not used to reach the 1,000 number.
2. **PAYG after the free quota runs out, with an initial cap of US$2 (±400 requests at the public rate of US$0.005).** I change the plan in the OpenWeb Ninja account myself. Paid manifests use `free_only: false`. The runner shows the maximum estimated cost and asks to confirm the number of requests before it asks for the key. Cumulative spending is recorded in the collection log.

Extra Indonesian source options (Greenhouse/Lever) stay open, but they are not run now.
