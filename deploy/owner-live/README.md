# Owner-only live demo on the VPS

`docker-compose.owner-live.yml` is an override for `/opt/jobfit/docker-compose.prod.yml`. It switches live analysis of uploaded CVs on **for the owner only** (D-105 owner path) and adds a private owner UI. Public live stays off: `JOBFIT_PUBLIC_LIVE=0` and the public beta is hardcoded closed, so the public UI (Caddy + Basic Auth) keeps its disabled consent and any non-owner live request gets 503. Budgets (US$5/day, US$25 lifetime), the ledger, the database, ZDR, idempotency, the D-104 consent lease and the 3-analysis session limit are unchanged.

## One-time preparation (VPS)

1. Back up: tag the running images (`docker tag jobfit-prod-api jobfit-prod-api:rollback-$(date +%Y%m%d)`, same for `jobfit-prod-ui`), copy `docker-compose.prod.yml` and `.env.prod` aside (`cp -p`, never print them), and run the usual database + ledger backup.
2. Add to `.env.prod` (mode 600, never committed or printed): `OPENROUTER_API_KEY=<production key>` and `JOBFIT_OWNER_TOKEN=<random, 32+ characters>` (for example `openssl rand -hex 32`).
3. Create `/opt/jobfit/reports/tokenizers` (`mkdir -p`), then copy the pinned query tokenizer from the Mac: `scp reports/tokenizers/qwen3-embedding-8b-tokenizer.json ubuntu@<vps>:/opt/jobfit/reports/tokenizers/`, then check `sha256sum` = `83cdf8c3a34f68862319cb1810ee7b1e2c0a44e0864ae930194ddb76bb7feb8d` and make it world-readable (`chmod a+r`); the container mounts it read-only.

## Start

```sh
cd /opt/jobfit
git fetch origin && git checkout <reviewed commit>        # the checkout must be clean except docker-compose.prod.yml
C="docker compose -f docker-compose.prod.yml -f deploy/owner-live/docker-compose.owner-live.yml -f deploy/observability/api-network.override.yml --env-file .env.prod"
$C config --quiet                                          # merge check; prints nothing on success
$C up -d --build api ui ui-owner
```

## Check

- Inside the API container, `/health` shows `"live_enabled":true,"real_cv_enabled":true,"live_storage_ready":true,"analysis_limit":10`.
- Public site (Basic Auth): upload a synthetic CV. Consent stays disabled with "Analisis CV asli belum diaktifkan di demo ini"; Saved Demo still works.
- Owner UI: `ssh -L 8511:127.0.0.1:8511 ubuntu@<vps>`, open `http://127.0.0.1:8511`, upload a **synthetic** CV, consent, Lanjutkan (paid parse), Find Jobs (paid query embedding), Cek kecocokan (paid analysis), Perkuat CV.
- Grafana: API target up; cost panels move only after paid calls.

## Revert to the dark deployment

```sh
docker compose -f docker-compose.prod.yml -f deploy/owner-live/docker-compose.owner-live.yml --env-file .env.prod stop ui-owner
docker compose -f docker-compose.prod.yml -f deploy/owner-live/docker-compose.owner-live.yml --env-file .env.prod rm -f ui-owner
docker compose -f docker-compose.prod.yml -f deploy/observability/api-network.override.yml --env-file .env.prod up -d api ui
```

This brings back `JOBFIT_LIVE_ENABLED=0` and `JOBFIT_REAL_CV_ENABLED=0`. The database and ledger are never rolled back. If a paid operation stops with a breach marker or a stuck `reserved` row, follow the CP3.1 manual review procedure (`docs/checkpoint_3/CP3_01_FastAPI_Service.md`); never clear it by hand.
