# Runbook: freeze, held-out test and deployment

**Date:** 6 October 2026. **For:** Dion, on the Mac, from the project folder with `env-job-fit` active. Claude never runs git or paid calls; every paid step below is yours, and each one has a dry run first.

## 0. Check the project

```bash
python -m pytest -q                          # expected: all pass, 2 skipped
python scripts/prepare_cp23_freeze.py --verify evals/freeze/cp23_freeze_draft_v2
```

The second command must print `"ok": true`. If a file changed, tell Claude before going on.

## 1. Approve the freeze (D-053)

1. Read `evals/freeze/cp23_freeze_draft_v2/freeze_receipt.json` (config, call settings, pool rule, 53 file hashes). The choices are explained in D-086. The `report_contract` block fixes how CP2.4 is reported: CV3-CV5 are the headline, CV1-CV2 only a familiar-profile diagnostic, and no pooled CV1-CV5 number exists (`src/jobfit/eval/heldout_report.py`).
2. Tell Claude in chat that you approve it. Claude writes the decision entry (the next free number, for example D-087).
3. Then run:

```bash
python scripts/prepare_cp23_freeze.py --approve evals/freeze/cp23_freeze_draft_v2 --decision D-087
```

From here on no model, prompt, K, weight or rule changes because of test results (D-046, D-053).

## 2. Held-out test run (CP2.4), about US$2

Run each phase without `--execute` first and check the plan it prints.

```bash
F=evals/freeze/cp23_freeze_draft_v2
docker compose up -d db                       # stage 1 needs the local database
python scripts/run_cp24_test.py parse      --freeze $F --execute   # CV3-CV5, about US$0.03
python scripts/run_cp24_test.py queries    --freeze $F --execute   # CV3-CV5 query vectors, under US$0.01
python scripts/run_cp24_test.py stage1     --freeze $F --execute   # no cost
python scripts/run_cp24_test.py extraction --freeze $F --execute   # about US$0.5, cap US$1.00
python scripts/run_cp24_test.py matching   --freeze $F --execute   # about US$1.6, cap US$2.50
python scripts/run_cp24_test.py pool       --freeze $F
python scripts/build_cp23_test_workbook.py evals/results/cp24/test_run_v1/test_run.json          # counts and time first
python scripts/build_cp23_test_workbook.py evals/results/cp24/test_run_v1/test_run.json --write  # after you agree the batch
```

If a phase stops on an error, send Claude the output. Records are write-once, so running the same phase again only does what is missing.

Then label the blind workbook (no model drafts this time, D-053), close Excel and tell Claude. Claude imports the labels and runs `scripts/evaluate_cp24_test.py`, which only prints the CV3-CV5 headline and keeps CV1-CV2 separate.

## 3. App on the Mac

```bash
docker compose up -d --build
docker compose ps                              # api: Up (healthy), ui: Up
python scripts/e2e_check.py --write            # expected: all checks pass
docker compose logs api | grep -c canary       # expected: 0
```

UI: http://127.0.0.1:8501. Optional paid check (about US$0.30, live analysis must be on, so run the API outside Docker):

```bash
uvicorn jobfit.api.wiring:create_default_app --factory --app-dir src --port 8000
python scripts/e2e_check.py --live --write
```

## 4. Deployment (Railway, D-023)

> **Superseded (7 Oct 2026):** D-095 replaces Railway with a SumoPod VPS, so this section is kept only as history. The VPS runbook is written in CP3 Phase 6 ([CP3 execution plan](CP3_Execution_Plan.md)). It will contain:
> - the provisioning checklist;
> - the production compose and Caddy setup;
> - backup-before-migrate and restore-based recovery;
> - the exact two-layer validation commands: **A**, external public smoke through Caddy and Streamlit; **B**, the internal API `e2e_check.py` inside the VPS Docker network or through an SSH tunnel. FastAPI is never exposed publicly.

1. Confirm the monthly cost and set a hard usage limit in Railway.
2. Push the repository to GitHub yourself; the CI workflow (`.github/workflows/tests.yml`) must be green.
3. In Railway create two services from the repository: one with `Dockerfile.api`, one with `Dockerfile.ui`. On the UI service set `JOBFIT_API_URL` to the API's private URL. Railway sets `PORT`; both images use it.
4. Keep `JOBFIT_LIVE_ENABLED=0` (the default) unless you add a persistent named volume at `/var/lib/jobfit/ledger` and a separate OpenRouter key with its own spending limit. The deployed demo then uses the saved results only. Production live additionally needs (CP3 Phase 2, D-101 persistent-ledger addition):
   - `JOBFIT_USAGE_LEDGER=/var/lib/jobfit/ledger/usage_ledger.jsonl`, provisioned once with `python -m jobfit.live.storage init --ledger /var/lib/jobfit/ledger/usage_ledger.jsonl` inside the API container (it refuses an existing marker or unmarked evidence; check with `... storage check ...`);
   - backups of the PostgreSQL database and the whole ledger root (marker, ledger, journal, breach and lock files) taken and restored together, as one recovery set;
   - no purge of closed `budget_reservations` rows (they are the witness of the settled spend) until an approved durable lifetime watermark replaces them;
   - manual review for any reservation the runtime keeps `reserved` (breach marker, damaged evidence, storage mismatch, an expired reservation without evidence); see the CP3.1 manual-review procedure.
5. Run `python scripts/e2e_check.py --base https://<api-url> --write` and record the result in CP3.4.

## What stays closed

Analysis of uploaded real CVs stays off (`/cv/parse` answers 403) until the open D-051 items are decided: city and company policy for masking, and verified zero-retention endpoints for every model and the embedding. Masking, preview and consent already work and can be shown.
