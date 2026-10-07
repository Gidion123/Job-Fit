# CP2.2: Embedding implementation and access verification

Date: 1 October 2026. **DONE for this subtask: code, live build, scoped retrieval, and cache verified.** CP2.2 remains IN PROGRESS. No development labeling workbook was created.

## 1. Goal and boundaries

Prepare two versioned embedding candidates and exact dense / FTS + dense search. This is pipeline readiness, not a model-quality comparison. Preserve the 632-job snapshot, the frozen 214/214 split, approved labels, and the test-only CV4/CV5 contents. Only CV1/CV2 are query inputs at this stage. All 632 public JDs may be embedded into the fixed corpus cache, but development retrieval must be restricted to the 214 development IDs before ranking and LIMIT.

T07 is DONE: Dion approved CV4/CV5 content and realism on 1 October. Approved file and body hashes match the approval manifest. This approval does not assign evidence or relevance labels.

## 2. Implementation

| Component | Implemented behavior |
| --- | --- |
| Embedding client | Native dimensions, response index ordering, finite nonzero vectors, returned-model check with explicit observed aliases; no automatic SDK retries |
| Provider policy | `data_collection: deny`, `require_parameters: true`; maximum prompt and request prices sent in the request |
| Budget and ledger | Serialized check and one durable record per inference attempt; rejected requests cost zero; uncertain failures reserve a conservative bound |
| Tokenizers | cl100k for OpenAI; official Qwen tokenizer pinned to revision and SHA-256. UTF-8 prefix trimming if needed, with token/truncation metadata |
| PostgreSQL | Separate versioned table for 1536/4096 dimensions; original table and job records retained. Transaction commits per successful batch |
| Cache identity | Model, dimension, preprocessing, token limit, tokenizer version, source hash, input hash |
| Recovery | SQLite API receipts precede storage writes; completed batches are reused. Query JSON and run reports use atomic replacement |
| Search | Exact cosine; FTS and dense constrained before LIMIT; RRF uses ranks with k=60 and stable job-ID ties |
| Key readiness | Read-only `/key` check distinguishes regular and management keys. Management or unknown key type stops the build before inference |

Receipt recovery does not promise exactly-once billing if a process dies between a provider response and the local receipt commit. Concurrent multi-host execution is outside this local implementation. The 20-result branch depth is an implementation default, not the selected CP2.3 K.

## 3. Preflight on the actual corpus

| Model | Dimensions | Input tokens, jobs + CV1/CV2 | Estimated US$ | Conservative bound US$ |
| --- | ---: | ---: | ---: | ---: |
| openai/text-embedding-3-small | 1536 | 402,912 | 0.00805824 | 0.04402404 |
| qwen/qwen3-embedding-8b | 4096 | 402,815 | 0.00402815 | 0.02201202 |
| Total | | 805,727 | 0.01208639 | 0.06603606 |

632 jobs and 2 development queries per model; no input needed truncation. Ledger hard stop remains US$8.50. Prices and official model endpoint metadata are in `evals/results/embedding_provider_check_20261001.json`; both models subsequently accepted requests with the configured provider restrictions. This is request acceptance, not an independent provider privacy audit.

## 4. Actual runs, failures, and recovery

**Historical access failure:** the original and first resumed runs stopped at the first OpenAI batch (16 inputs), and a one-input probe also returned HTTP 401. At that point zero vectors existed and Qwen was not attempted. GET `/key` succeeded but reported `is_management_key=true`. A management key authenticates administration, not inference. Three rejected requests are recorded with zero cost. Dion replaced the local value with a regular API key; its type check passed. No key was created or environment value changed by this task.

**Historical validation failure:** a successful 16-input OpenAI response and one-input probes for OpenAI/Qwen were rejected locally because their native model names differed from router IDs. Observed names were `text-embedding-3-small` and `Qwen/Qwen3-Embedding-8B`. Added an explicit per-model alias allowlist, without fuzzy or cross-model acceptance. Dimension, ordering, nonzero and finite checks remain unchanged. These three billed validation failures cost **US$0.00017549**; that cost remains in the ledger.

**Successful build:** `embedding_validated_aliases_20261001` completed:

| Model | Job vectors in PostgreSQL | Query vectors in local cache | Live retrieval checks |
| --- | ---: | ---: | --- |
| OpenAI | 632 at 1536 dimensions | 2: CV1/CV2 | Dense and hybrid each return 20 development jobs; repeated hybrid output stable |
| Qwen | 632 at 4096 dimensions | 2: CV1/CV2 | Dense and hybrid each return 20 development jobs; repeated hybrid output stable |

All four model/CV checks passed and their rankings contain only development IDs. Job inventory and the original embedding table are unchanged. No input was truncated. Build: **82 successful inference requests**, reported cost **US$0.01209273** (run summary rounds to US$0.012093).

**Total ledger:** 88 inference records, comprising 82 successful build calls, 3 billed validation failures, and 3 rejected authentication calls. Total reported cost: **US$0.01226822**, leaving **US$8.487732** to the local hard stop by its rounded ledger calculation. All 85 billed records contain provider-reported cost. Read-only key checks do not run inference.

**Resume check:** post-build preflight finds 632 cached jobs and 2 cached queries for each model: zero pending inputs, estimated repeat inference cost US$0, unchanged ledger. This verifies reuse readiness without another paid run.

No key, account label, complete key response, vector values, or CV/JD input text appears in the diagnostic reports. Operational receipt/query caches do contain vectors and hashes and remain ignored local files.

## 5. Verification

- Final database-enabled suite: `JOBFIT_DB_TESTS=1 env-job-fit/bin/python -m pytest -q`: **123 passed in 8.39 seconds**.
- Tests cover rejected and uncertain billing, budget stop before request, response ordering/dimensions/model/finite values, profile isolation, resume after a database write failure, recovery after an interrupted query cache write, management-key preflight, scoped search, stable RRF, and transactional rollback.
- PostgreSQL integration ran against the local service. Source inventory remains 632 jobs; before the live build, zero legacy embeddings existed and this legacy table remains unchanged. The suite verifies the 632 total / 428 target inventory.
- Both frozen split file hashes and both approved CV file/body hashes match their manifests. No label approval, split change, or test-CV query was introduced.

Evidence: `evals/results/embedding_continuation_audit_20261001.json`, `embedding_preflight_resume_20261001.json`, `embedding_resume_20261001.json`, and `embedding_key_preflight_20261001.json`. Successful run: `embedding_validated_aliases_20261001.json`. Resume check: `embedding_cache_verification_20261001.json`. Earlier failed run files remain historical evidence.

## 6. Interpretation and next step

This subtask is complete. Live vectors, scoped retrieval, deterministic results, budget accounting, and cache reuse are verified. These results do not measure ranking relevance, compare model quality, or select a model/K. No gold/silver label was changed. CV4/CV5 remain approved, held out, and unused in development. Parser date precision and explicit evaluation-clock wiring remain open pipeline work.

**STOP before T03 Part 2 / T04 / T05 labeling workbooks.** Under the next authorized scope, build the development pools, measure the top 5 union, resolve its conflict with the 20-review-per-CV cap, and prepare pending drafts for Dion's review. Only approved rows become gold. Continue the CV parser, extraction/matching vertical slice, and development evaluation afterward; CP2.2 overall remains IN PROGRESS. No repeat approval for D-045, split acceptance, or T07 is needed.

Official reference for the resolved access problem: [OpenRouter Management API Keys](https://openrouter.ai/docs/guides/overview/auth/management-api-keys).
