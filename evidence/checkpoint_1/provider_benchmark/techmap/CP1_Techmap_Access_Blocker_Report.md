# CP1.1D: Techmap access blocker (interim evidence report)

**Project:** JobFit Intelligence  
**Date:** 25 September 2026  
**Status:** DEFERRED (RapidAPI subscription/access unresolved)  
**Scope:** Provider access and benchmark feasibility; this is **not** the final Checkpoint 1 report.

## Objective

Evaluate Techmap's *Daily International Job Postings* API against the completed JSearch benchmark before choosing a primary job-data provider. The planned first test (`TM01`) was `title=AI Engineer`, `countryCode=id`, `dateCreated=2026-09`, `format=json`, `page=1`, with the other filters empty.

## Evidence and observations

| ID | Type | Observation |
| --- | --- | --- |
| TM-A01 | UI observation | RapidAPI lists the API as *Daily International Job Postings* by Techmap GmbH. The `GET search` endpoint exposes filters including `title`, `countryCode`, `dateCreated`, `language`, `city`, and `page`. |
| TM-A02 | UI observation | The BASIC plan displayed $0/month, 100 requests/month, 10 jobs/request, one request/second, $0.06 per request above the allowance, and a bandwidth allowance/overage. These are the terms observed on 25 September 2026, not a permanent price guarantee. |
| TM-A03 | My checkout attempt | Subscription checkout first showed: “Your selected payment method failed. Please try another payment method.” |
| TM-A04 | Payment state (my observation) | The bank displayed a USD 0.50 verification that I approved. I did not see a posted debit in the transaction history. A Visa card then appeared in RapidAPI Billing. This does not establish that the API subscription was activated. |
| TM-A05 | Account state (my observation) | At one check, **Personal Account → My Subscriptions** contained no active APIs. Later BASIC appeared active, but no successful search response or subscription record was provided. |
| TM-A06 | Latest screenshot | On the BASIC checkout screen, clicking **Subscribe** produced: “User must have active payment method to subscribe to this billing plan.” The screen still showed a subscription checkout, not a `GET search` result. |

RapidAPI's [terms](https://rapidapi.com/page/terms) describe a USD 0.50 authorization hold for Freemium plans. The hold is consistent with the amount I saw; the cause of the failed subscription is still **unknown**. RapidAPI's [billing FAQ](https://docs.rapidapi.com/docs/faqs) recommends contacting support when card validation fails.

## Benchmark result and limitation

| Item | Status |
| --- | --- |
| API documentation and parameter inspection | Completed |
| Pricing/access inspection | Completed |
| Active Techmap subscription | **Unverified / checkout blocked in latest evidence** |
| Successful `GET search` call | **None verified** |
| Techmap response JSON or job sample | **None** |
| Indonesia AI/ML coverage, JD quality, provenance, freshness, duplicates | **Not measured** |
| JSearch vs Techmap weighted score | **Not calculated** |
| Primary provider decision | **OPEN** |

This is an **access failure**, not evidence that Techmap's job data is poor or that an `AI Engineer` query returns zero jobs. Do not enter a zero-result row for `TM01` and do not invent a Techmap quality score.

## Decision and trade-offs

**Decision on 25 September:** Pause repeated checkout attempts, keep the blocker as CP1.1D evidence, and contact RapidAPI support. Do not test a random marketplace API just because it is listed. A replacement provider would need the same source-selection rubric and a comparable benchmark.

The handoff originally required an actual Techmap benchmark before primary-provider selection. Access is currently preventing that test. This is a **temporary deviation from the planned sequence**, not a reversal of the provider-selection rule. JSearch remains a strong candidate based on its completed benchmark, but it is **not selected as the final primary provider** here. If the deadline forces data collection before the support case is resolved, document any JSearch use as **provisional**, with this limitation visible in the Checkpoint 1 report.

An optional parallel route is to [request a targeted sample from Techmap](https://jobdatafeeds.com/data) for Indonesia AI/ML roles. A supplied sample could help inspect fields and JD quality, but it would not measure API access or reliability and should be labeled that way.

## Follow-up and evidence handling

1. Submit the separate [support-ticket draft](./CP1_Techmap_RapidAPI_Support_Draft.md) through RapidAPI's support form; keep the ticket ID and reply.
2. Record any confirmed subscription status from **Personal Account → My Subscriptions** before retrying the endpoint.
3. If access is restored, run `TM01` once and save the actual response JSON, result screenshot, request parameters, date/time, and HTTP status. Continue the planned role queries only after auditing `TM01`.
4. If access stays blocked, carry this limitation into the CP1 provider comparison. Do not claim a completed actual Techmap benchmark.

The checkout screenshot shared in chat contains personal contact and payment information. **Do not copy it unchanged into the repository or presentation.** A manually redacted screenshot may later be saved as `CP1_Techmap_TM00_Subscription_Error_Redacted.png`. The exact error strings and observations above are the current text evidence.

## Source register

- [Techmap API listing on RapidAPI](https://rapidapi.com/techmap-io-techmap-io-default/api/daily-international-job-postings)
- [RapidAPI Terms of Service: Freemium authorization](https://rapidapi.com/page/terms)
- [RapidAPI billing FAQ](https://docs.rapidapi.com/docs/faqs)
- [Techmap data sample request](https://jobdatafeeds.com/data)

