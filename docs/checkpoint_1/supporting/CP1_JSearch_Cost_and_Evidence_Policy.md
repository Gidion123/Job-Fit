# JSearch budget model and evidence policy

**Checked:** 26 September 2026. **Scope:** OpenWeb Ninja direct-portal JSearch only. This document estimates API spend; it does not include LLM, embeddings, hosting, database, payment fees, tax, or exchange-rate effects. No paid subscription or billing setting has been changed.

## Published API prices

The [official JSearch pricing page](https://www.openwebninja.com/api/jsearch) lists Free: 200 requests/month with a hard limit; Pay As You Go: USD 0.005/request with no monthly fee; Pro: USD 25/month for 10,000 requests plus USD 0.003 for each additional request. Prices and account-specific conditions must be checked in the account before subscribing. The provider describes API-key billing as card/monthly billing in its [x402 comparison](https://www.openwebninja.com/blog/x402-agentic-payments); the public page does **not** establish a prepaid minimum or a top-up amount. So I do not plan around depositing a specific sum; the checkout UI may instead ask to select a plan or payment method. The [terms](https://www.openwebninja.com/terms) say subscriptions renew until canceled and may include tax.

## One-time collection target: 1,000 distinct auditable JDs

Cost is based on **requests**, not returned jobs. Illustrative PAYG scenarios assume no free-plan allowance is combined with PAYG and exclude unsuccessful/extra verification requests:

| Distinct auditable jobs per request | Requests needed for 1,000 | JSearch PAYG charge |
| ---: | ---: | ---: |
| 8 | 125 | USD 0.63 |
| 4 | 250 | USD 1.25 |
| 2 | 500 | USD 2.50 |
| 1 | 1,000 | USD 5.00 |
| 0.5 | 2,000 | USD 10.00 |
| 0.2 | 5,000 | USD 25.00 |

The current two collection queries returned four *raw* jobs each, with far fewer confirmed target-role jobs. They are insufficient to predict yield. A **USD 10 JSearch request budget / 2,000-request stop** is a reasonable initial ceiling for the acquisition experiment, not a guaranteed final bill or a required payment. If measured yield stays below 0.5 distinct auditable JD per request, revise query/source strategy before spending further. Run the 12-request pilot first, then recalculate from actual deduplicated and accepted jobs per request. For PAYG, the published price would make that pilot USD 0.06; on Free it should consume quota rather than incur a published per-request charge. Confirm the active plan in the account.

## Public app: monthly JSearch usage

Preferred pattern: serve searches from the cleaned local corpus; call JSearch from a scheduled refresh worker, not once per user page view. For example, 20 refresh requests/day = 600/month = USD 3.00 PAYG; 100/day = 3,000/month = USD 15.00 PAYG. Mark `last_seen_at`, verification status, and staleness to avoid presenting old results as active. Maintain a server-side request cap, caching, deduplication, alert at 80% of the monthly budget, and no unbounded retry loop. The provider's [usage endpoint guide](https://www.openwebninja.com/blog/check-api-quota-usage-programmatically) describes quota checks for the current plan.

If instead every user search calls JSearch, 100 daily users × 2 searches/day × 30 days = 6,000 requests/month: USD 30 PAYG at the published rate. Pro is USD 25/month for up to 10,000, before applicable tax; above 10,000 it advertises paid overage, so a separate application cap is still necessary. The PAYG/Pro crossover is 5,000 requests/month at listed prices. Public demand is unknown, so do not purchase Pro only for an expected 1,000-job initial corpus.

**Recommended first step:** keep the existing Free plan for the capped pilot if quota remains. If that is insufficient, choose PAYG only after reviewing the account checkout and set an internal experiment cap equivalent to **USD 10**. A billing card may be charged as usage occurs; the public documentation does not establish a wallet amount to “fill.” Do not set a full-app monthly budget from JSearch alone; measure hosting, database, embedding, and LLM costs separately after model/deployment choices are fixed.

**Free-first collection decision (26 September):** Use the official Basic quota first. Run the varied 12-request pilot, review accepted unique jobs/request, then allocate later batches to undercovered strata and productive cursor pages. The collector now queries the provider's current usage endpoint before each executed batch and will not exceed the verified Free-plan remainder in that batch. Upgrade only after the free quota has been used productively and the measured yield justifies it.

## Evidence standard for professional collection

For programmatic API collection, store **raw JSON response + request metadata** (query, country, language, cursor-page index, UTC retrieval time, HTTP status, provider request ID, SHA-256 hash), then a quality/dedup audit and normalized records. This is more reproducible than screenshots and is what the local collector already writes. Screenshots are **optional exception evidence** for UI-only issues, payment/plan errors, or a response not reproducible from API data. They are not required per job or per successful request. Avoid screenshots that expose API keys or personal/billing details.

Earlier COL01/COL02 screenshots remain historical evidence of manual 200-OK tests. Future automated collection need not produce screenshots.
