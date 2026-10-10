# Controlled public live demo behind Basic Auth

Goal: a mentor opens `https://jobfit-demo.duckdns.org`, passes Caddy Basic Auth, uploads a CV, reviews the sanitized text, consents, and runs parse → Find Jobs → Analyze Fit with live LLM calls. No SSH tunnel, no owner token in the public UI.

`docker-compose.public-live.yml` overrides `/opt/jobfit/docker-compose.prod.yml` (api and ui environment only). Non-owners are admitted only when `JOBFIT_PUBLIC_LIVE=1` **and** every gate in `jobfit.api.wiring.public_beta_open` holds: production runtime, live and uploaded-CV switches, every D-103 phase bound within the daily cap, and active metadata-only Langfuse (D-103). Per-IP tickets: 10 per IP per 24 h. Unchanged: session allowance (parse 1, search 1, job_analysis 3), US$5/day and US$25 lifetime budgets, ledger, ZDR (`data_collection: deny`), idempotency, the D-104 consent lease, internal-token API on `127.0.0.1` only.

## What is already validated locally (synthetic, no paid call)

| Gate item | Local evidence (pytest) |
| --- | --- |
| No raw canary in responses, logs, `/metrics`, provider payloads, session state (owner path) | `tests/test_fail37_api_privacy.py::test_raw_canary_sinks_zero_across_the_full_flow` |
| Public visitor path: one per-IP ticket, never the owner; ZDR on every provider call; no canary in any sink **including the Langfuse export** | `tests/test_privacy_release_public.py` |
| D-104 structural boundary (header, Summary, privacy sections, start, fail-closed), edit path | `tests/test_masking_fail37.py`, `tests/test_privacy_edit_lead.py`, dev calibration receipt |
| Langfuse metadata-only allowlist, mask, Japan endpoint, privacy self-check, fail-open | `tests/test_langfuse_tracing.py` |
| Public beta opens only with every gate (incl. Langfuse) | `tests/test_public_beta_gate.py` |
| Client IP from Caddy only through a trusted proxy peer | `tests/test_client_ip.py` |
| Upload failure paths (DOCX gates, oversized, malformed) | `tests/test_upload_guard.py` |

## Deployed gate on the VPS (owner, before `JOBFIT_PUBLIC_LIVE=1`)

1. **Backup:** tag `jobfit-prod-api` and `jobfit-prod-ui` as `rollback-<date>`; `cp -p` `docker-compose.prod.yml` and `.env.prod` aside (never print them); run the usual database + ledger backup.
2. **Secrets in `.env.prod`** (mode 600): `OPENROUTER_API_KEY`, `JOBFIT_OWNER_TOKEN` and `JOBFIT_IP_HMAC_KEY` (each `openssl rand -hex 32` for the two tokens), `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` from a Langfuse Cloud **Japan** project (Hobby plan). Leave `JOBFIT_PUBLIC_LIVE` unset (0).
3. **Trusted proxy:** `docker network inspect $(docker network ls -q -f name=application_net) -f '{{(index .IPAM.Config 0).Gateway}}'` → put that IP in `JOBFIT_TRUSTED_PROXIES`. Keep Caddy as is: `reverse_proxy 127.0.0.1:8501`, no `trusted_proxies` (Caddy then overwrites any client `X-Forwarded-For`), and no `log` directive (no IPs in access logs).
4. **Tokenizer:** `mkdir -p /opt/jobfit/reports/tokenizers`, `scp` `reports/tokenizers/qwen3-embedding-8b-tokenizer.json` from the Mac, check `sha256sum` = `83cdf8c3a34f68862319cb1810ee7b1e2c0a44e0864ae930194ddb76bb7feb8d`, `chmod a+r`.
5. **Start (still closed to the public):**
   ```sh
   cd /opt/jobfit && git fetch origin && git checkout <reviewed commit>
   C="docker compose -f docker-compose.prod.yml -f deploy/public-live/docker-compose.public-live.yml --env-file .env.prod"
   $C config --quiet && $C up -d --build api ui
   ```
   `/health` inside the API: `"live_enabled":true,"real_cv_enabled":true,"live_storage_ready":true`. `docker logs jobfit-prod-ui-1 | grep client_ip_source` shows `forwarded` after opening the site (anything else: fix step 3 before continuing).
6. **No-cost deployed canary sweep:** run `scripts/e2e_check.py` against the internal API (inside the VPS network); it uploads a synthetic canary CV and checks masking, consent binding, deletion and responses. Then grep for the canary strings in `docker logs` of api/ui, in authorized `/metrics`, and in a `pg_dump` of the production database: zero hits required.
7. **Paid canary run (owner approval, about US$0.10–0.30):** with `JOBFIT_PUBLIC_LIVE=1` set temporarily only for this check, or through the owner token from inside the VPS, run one synthetic canary CV through parse → search → one Analyze Fit. Then: zero canary hits in logs, `/metrics`, `pg_dump`, and the **exported Langfuse traces** (Langfuse UI → trace → JSON: only stage, outcome, error code, latency, token and cost metadata); OpenRouter activity shows only ZDR-routed providers for CV parse, query embedding, JD extraction and evidence matching (the per-route privacy record).
8. **Record** the results (date, commit, pass/fail per item, cost) in `docs/checkpoint_3/CP3_04_End_to_End_Testing.md`. PR-10 (original vs masked quality, about US$2) is a quality comparison, not a leak check; record it as done or deferred.
9. **Open:** set `JOBFIT_PUBLIC_LIVE=1` in `.env.prod`, `$C up -d api`, and confirm a mentor flow over `https://jobfit-demo.duckdns.org` with a synthetic CV.

## Revert

```sh
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d api ui
```

This restores the dark deployment (live off, consent disabled for everyone). The database and ledger are never rolled back. A stuck `reserved` row or a breach marker follows the CP3.1 manual review procedure (`docs/checkpoint_3/CP3_01_FastAPI_Service.md`).

## Known limits for a mentor demo

- Ten tickets per public IP per 24 hours: mentors on the same campus Wi-Fi share one IP, so at most ten sessions per day from that network.
- One paid operation at a time across all users, and each Analyze Fit reserves about US$4 of the US$5 daily cap until it settles: concurrent visitors see "busy"; the day closes after about US$1 of actual spend.
- A provider call past its time limit writes a breach marker that stops paid operations until the manual review (FAIL-39).
