# Runbook: owner-only Local Mac validation of the real-user flow (D-105)

**Status: PENDING, NOT RUN.** This milestone stops at *ready for owner Local Mac validation*. Nothing below has been executed. No paid call was made while it was prepared.

**What it validates:** the complete real-user flow on Dion's Mac with one real CV:
- upload → local sanitizer → exact preview → consent → parse;
- Find Jobs and Check a Job → Analyze Fit → Improve My CV;
- delete the session.

It runs on the production runtime, owner-only, with the public beta closed.

**Out of scope:** VPS, Caddy, DNS/TLS, monitoring (Prometheus, Grafana, Langfuse), the deployed privacy release gate, public activation, PR-10 and D-045 paid runs.

## Safety rules for this run

- **Never touch the CP2 evaluation database** (`docker-compose.yml`, container `jobfit-db`, port 5434, volume `jobfit_pgdata`). It is only read once with `pg_dump`, which is read-only. All writes go to a separate restored copy in its own stack (`docker-compose.owner-local.yml`, project `jobfit-owner`, port 5435).
- **Secrets live only in an untracked env file.** Use `.env.owner-local` (ignored like every `.env.*`; also excluded from images by `.dockerignore`). Never commit it or paste it anywhere.
- **The public beta stays closed.** `JOBFIT_PUBLIC_LIVE=0`, and `public_beta_open` is hardcoded False, so a request without the owner token gets 503. `JOBFIT_REAL_CV_ENABLED=1` exists only in the owner-local profile.
- **Budget: nothing is set or raised automatically.** You choose the values. Admission uses the D-103 **deterministic upper bounds**, not observed spend:

  | Phase | Admission bound (US$) |
  | --- | --- |
  | `parse` | 0.0614679 |
  | `search` | 0.0001648 |
  | `job_analysis` | **4.0012836** |

  Observed spend is typically much lower: development-ledger estimates are about US$0.06–0.10 per settled analysis, an estimate only and not a guarantee. A `job_analysis` is admitted only while:
  - the day's settled spend + open liability + 4.0012836 ≤ `JOBFIT_DAILY_BUDGET_USD`;
  - recorded spend + open liability + the bound stays within the lifetime limits (`API_HARD_STOP_USD` ≤ `API_BUDGET_USD`).

  Operations run one at a time. **Worked example:** with `JOBFIT_DAILY_BUDGET_USD=5`, the first analysis is admitted (0 + 4.0012836 ≤ 5). Later analyses are admitted while that day's settled spend stays below about US$0.99. A daily cap below 4.0012836 admits no analysis at all. Choose `JOBFIT_DAILY_BUDGET_USD` ≤ `API_HARD_STOP_USD` ≤ `API_BUDGET_USD` deliberately for the paid steps you plan.
- **Search allowance:** you may repeat Find Jobs during this validation because the owner bypasses the public session allowance. The controlled-public-beta allowance stays parse 1 / search 1 / job_analysis 3 (D-103, unchanged). That one-search behaviour is reviewed after this validation, before any public activation. "Refine these results" is local, makes no call and can be changed freely.

## Steps

1. **Fetch the accepted branch.**
   ```sh
   cd ~/path/to/Job-Fit
   git status                         # clean, or stash your local changes first
   git fetch origin cp3-development-20261007
   git checkout cp3-development-20261007
   git merge --ff-only origin/cp3-development-20261007   # fast-forward only; stop if it refuses
   git log -1 --oneline               # the independently accepted HEAD
   ```
2. **Create the env file without committing secrets.** Create `.env.owner-local`:
   ```sh
   OPENROUTER_API_KEY=...                         # your key
   JOBFIT_INTERNAL_TOKEN=$(openssl rand -hex 32)  # paste the generated values; 32+ characters
   JOBFIT_OWNER_TOKEN=$(openssl rand -hex 32)
   JOBFIT_DAILY_BUDGET_USD=...                    # your deliberate choice (see the budget rules above)
   API_HARD_STOP_USD=...
   API_BUDGET_USD=...
   ```
   Then confirm it is ignored: `git check-ignore .env.owner-local` prints the name.
3. **Start the owner database only.**
   ```sh
   C="docker compose -f docker-compose.owner-local.yml -p jobfit-owner --env-file .env.owner-local"
   $C up -d db
   ```
4. **Load the existing corpus into the copy.** This reads the CP2 DB, never writes to it.
   ```sh
   docker compose up -d db                                       # the CP2 stack's db, if not running
   docker exec jobfit-db pg_dump -U jobfit -d jobfit -Fc > /tmp/jobfit_cp2.dump
   shasum -a 256 /tmp/jobfit_cp2.dump                             # record it
   docker exec -i jobfit-owner-db pg_restore -U jobfit -d jobfit --no-owner < /tmp/jobfit_cp2.dump
   ```
5. **Verify, migrate, seed and verify again** inside the API image; the API is not serving yet.
   ```sh
   $C run --rm --no-deps api python scripts/db_baseline.py verify    # must report ok; stop otherwise
   $C run --rm --no-deps api python scripts/db_baseline.py stamp     # guarded stamp 0001; never bare alembic stamp
   $C run --rm --no-deps api alembic upgrade head                    # 0001 -> 0002
   $C run --rm --no-deps api python -m jobfit.db.seed_production --dry-run
   $C run --rm --no-deps api python -m jobfit.db.seed_production
   $C run --rm --no-deps api python -m jobfit.db.seed_production --verify
   ```
   `--verify` must report `"ok": true` with:
   - 632 job ids, 428 active target and 204 inactive non-target;
   - 632 `job_sources`;
   - a complete embedding index for the eligible jobs.

   The seed reports `legacy_seen_timestamp_fallback` (expected 6, 5 of them target). Those rows entered the production lifecycle at seed time; no historical date was invented. `job_sources` hold the canonical source identity only; member-level alias provenance is deferred.
6. **Query tokenizer.** On the Mac, run `python scripts/setup_embedding_tokenizers.py` once. It downloads only the pinned tokenizer file, with no inference and no CV data. Then check that `reports/tokenizers/qwen3-embedding-8b-tokenizer.json` exists and is readable by others (`chmod a+r`); the container mounts it read-only.
7. **Provision the persistent ledger storage once.**
   ```sh
   $C run --rm --no-deps api python -m jobfit.live.storage init --ledger /var/lib/jobfit/ledger/usage_ledger.jsonl
   $C run --rm --no-deps api python -m jobfit.live.storage check --ledger /var/lib/jobfit/ledger/usage_ledger.jsonl
   ```
8. **Start the owner-only API and the UI.**
   ```sh
   $C up -d --build api ui
   curl -s http://127.0.0.1:8010/health
   ```
   The health check needs `"real_cv_enabled": true`. A request without the internal token gets 401.
9. **Open the browser** at <http://127.0.0.1:8511>.
10. **Upload one real CV** (PDF, DOCX or text).
11. **Check the sanitized preview.**
    - Name, contact details, Summary/profile and privacy-only sections (references, interests, organizations and similar) are gone or masked.
    - The text starts at a professional section.
    - Correct anything missed and press "Use my corrected text"; it is sanitized again.
12. **Consent.** Tick the agreement box. This makes no call.
13. **Parse.** Press **Continue: analyze my CV** (one paid parse), wait for the status, and expect **CV ready**.
14. **Find Jobs.**
    - With all filters on Any: Relevant Jobs, in search-relevance order, with no score.
    - Then one filtered search (for example a role family or experience requirement). The results narrow, and nothing is widened.
    - Then **Refine these results**: changing it changes "Showing X of Y" with no new request (the API log shows no new call).
15. **Analyze Fit for one chosen job** (one paid `job_analysis`).
    - Optionally confirm "My CV lists my complete work history" first.
    - Check the evidence coverage (not a hiring probability), the per-requirement MATCH/PARTIAL/NO_MATCH with exact quotes, the strengths and gaps, and any experience conflict.
16. **Improve My CV for This Job.**
    - A shows only your existing evidence plus fixed guidance.
    - B asks about missing items; a bullet is built only from your answers.
    - C lists confirmed conflicts only.
    - "Not verified" lists years, location or work-permit items your CV does not establish.
17. **Check a Job.** Paste a real job description (at least 200 characters) and press Analyze Fit (one paid `job_analysis`). You get the same result view and the same coach.
18. **Delete the session** with "Hentikan & hapus sesi" in the sidebar. The page starts empty, and the server session is gone.
19. **Inspect local budget and ledger evidence.**
    ```sh
    $C exec api sh -c 'tail -n 5 /var/lib/jobfit/ledger/usage_ledger.jsonl; tail -n 5 /var/lib/jobfit/ledger/usage_ledger.jsonl.intents.jsonl'
    docker exec jobfit-owner-db psql -U jobfit -d jobfit -c \
      "SELECT phase, status, reserved_usd, settled_usd, production_day FROM budget_reservations ORDER BY production_day"
    ```
    Expect one reservation per paid operation (`parse`; `search` and `job_analysis` are stored as the coarse label `recommendation`, D-103), each settled. Every provider request goes through the ZDR client (`data_collection: deny`, `zdr: true`). No CV text appears in the ledger.
20. **Stop cleanly.**
    ```sh
    $C down               # keeps the volumes (database copy and ledger) for later inspection
    rm /tmp/jobfit_cp2.dump
    ```
    `$C down -v` deletes the owner copy and its ledger. Do that only after you have recorded the evidence.

## Pass/fail checklist (fill in during the run)

| # | Check | Result |
| --- | --- | --- |
| 1 | Seed `--verify` ok (632 / 428 / 204, index complete) | pending |
| 2 | Preview shows no identity, contact, Summary or privacy section; edit re-sanitizes | pending |
| 3 | No provider call before Continue; parse → CV ready | pending |
| 4 | Find Jobs blank and filtered; results never widened; no score on Relevant Jobs | pending |
| 5 | Refine makes no request; order kept | pending |
| 6 | Analyze Fit result honest; score only for an analyzed job | pending |
| 7 | Coach: no invented claim; bullets only from answers | pending |
| 8 | Check a Job works with the same views | pending |
| 9 | Delete session clears everything | pending |
| 10 | Ledger and reservations match the paid operations; spend within the chosen budget | pending |
