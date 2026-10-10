# UI v3 production integration handoff

Status: local integration prepared for review; not committed, merged, pushed, or deployed.

- Integration branch: `claude/cp3-ui-v3-integration`.
- Base/deployed CP3 source: `d7420a918399708d1b8b66501a2b0a61b0ba5327`.
- Approved UI v3 source: `30f2aa85046112df00d1e41ec5a2d8af7be332de`.
- The two branches diverged. Only the 20 paths below were taken from the UI v3 commit. No wholesale merge or cherry-pick was used.
- The dirty `main` worktree, untracked production Compose, CP3 integration branch, and uncommitted observability worktree were not modified.

## Selected files and dependency boundary

| Purpose | Paths |
| --- | --- |
| UI screens, components, copy, theme and self-hosted font | `ui/streamlit_app.py`, `ui/components.py`, `ui/texts.py`, `ui/theme.py`, `ui/static/IBMPlexSans.ttf`, `ui/static/IBMPlexSans-LICENSE.txt`, `.streamlit/config.toml` |
| Docker and Python compatibility | `Dockerfile.ui`, `requirements.txt` (`streamlit>=1.64,<2`) |
| API contract used by the UI | `src/jobfit/api/main.py` (`/health.analysis_limit`, preview edit flag, session analysis limit) |
| D-104 edit-safe privacy dependency | `src/jobfit/privacy/masking.py`, `src/jobfit/privacy/structure.py`, `evals/results/fail37_structural_calibration_20261009_v2_dev.json` (sanitizer hash receipt) |
| Tests | `tests/test_api.py`, `tests/test_privacy_edit_lead.py`, `tests/test_ui_client.py`, `tests/test_ui_product_flow.py` |
| Documentation / local-only owner setting | `docs/checkpoint_3/CP3_03_Streamlit_UI.md`, `docs/checkpoint_3/Runbook_Owner_Local_Validation.md`, `docker-compose.owner-local.yml` |

The source commit also changed CP2 charts/notebooks, LLM comparison artifacts, the development usage ledger and other documents. None were imported. The owner-local Compose addition sets `JOBFIT_SESSION_ANALYSIS_LIMIT=10` only in that local profile; **do not copy it into `/opt/jobfit/docker-compose.prod.yml` or `/opt/jobfit/.env.prod`**. Without the variable, the API defaults to 3. The public D-103 `BetaAllowances` remains parse 1 / search 1 / job_analysis 3, and the budget/ledger enforcement code is unchanged.

## Local evidence

- UI/API/privacy/runtime selected suite: **320 passed, 0 failed, 0 skipped**.
- Full offline suite: **1413 passed, 245 skipped, 2 deselected, 0 failed**. The two deselections are pre-existing macOS-specific tests: `/var` versus `/private/var` in `test_owner_local_compose`, and macOS `__CF_USER_TEXT_ENCODING` in `test_upload_guard`. They are not claimed as passes.
- Ruff CI gates `E9,F63,F7,F82` over `src scripts ui tests` and `F` over `src ui`: **pass**.
- D-087 freeze verification: `ok=true`, `changed_files=[]`.
- `git diff --check`: pass.
- Streamlit 1.64.0 is installed in the local project environment. `Dockerfile.ui` installs `streamlit>=1.64,<2`, copies both `ui/` and `.streamlit/`, and `.dockerignore` does not exclude either. The font is vendored; no remote font request is needed.
- The UI test suite includes a real FastAPI app with fake dependencies, the saved-demo flow, edit/consent/analysis contracts, and an outdated-API warning. No paid LLM call or real CV was used here.
- Local Docker builds passed for both `Dockerfile.ui` and `Dockerfile.api` using the integrated source (`--pull=false`). A network-disabled inspection of the UI image confirmed Streamlit 1.65.0 and the bundled `.streamlit/config.toml` and font. A network-disabled inspection of the API image confirmed FastAPI 0.143.0 and a successful `jobfit.api.main` import. These builds created local validation tags only; the actual VPS Compose/Caddy checks and production image builds remain deployment preflight gates.

MacBook verification from the integration worktree:

```sh
../project-job-fit/env-job-fit/bin/python -m pytest -q tests/test_ui_client.py tests/test_ui_product_flow.py tests/test_api.py tests/test_privacy_edit_lead.py tests/test_masking_fail37.py tests/test_fail37_api_privacy.py tests/test_cp3_product_api.py tests/test_real_cv_api.py tests/test_public_beta_api.py tests/test_public_beta_runtime.py -p no:cacheprovider
../project-job-fit/env-job-fit/bin/python -m pytest -q --deselect=tests/test_owner_local_compose.py::test_the_profile_is_owner_only_and_passes_the_production_invariants --deselect=tests/test_upload_guard.py::test_the_worker_gets_an_allow_listed_environment_and_isolated_mode -p no:cacheprovider
../project-job-fit/env-job-fit/bin/python scripts/prepare_cp23_freeze.py --verify evals/freeze/cp23_freeze_draft_v2
RUFF_CACHE_DIR=/private/tmp/jobfit-ui-v3-ruff-cache ruff check --select E9,F63,F7,F82 src scripts ui tests
RUFF_CACHE_DIR=/private/tmp/jobfit-ui-v3-ruff-cache ruff check --select F src ui
docker build --pull=false -f Dockerfile.ui -t jobfit-ui-v3-validation:local .
docker build --pull=false -f Dockerfile.api -t jobfit-api-ui-v3-validation:local .
git diff --check
```

## Production preflight after independent review and integration approval

1. Confirm the VPS checkout and deployed image identities before changing anything. The expected current source is `d7420a9`; stop if the real state differs. Preserve the existing `/opt/jobfit/docker-compose.prod.yml`, `/opt/jobfit/.env.prod`, Caddy/Basic Authentication configuration, existing image IDs/tags, and a rollback copy of the provisioned UI. Keep backups private; never print or package secret values. Follow the existing paired database-and-ledger backup procedure, but do not migrate, reset or restore either for this UI update.
2. Review the **actual** production Compose merged configuration. It must still bind UI only to `127.0.0.1:8501`, API only to `127.0.0.1:8000`, publish no PostgreSQL port, keep `JOBFIT_LIVE_ENABLED=0`, `JOBFIT_PUBLIC_LIVE=0`, `JOBFIT_REAL_CV_ENABLED=0`, and avoid an owner token or `JOBFIT_SESSION_ANALYSIS_LIMIT=10` in production. Do not reuse `docker-compose.owner-local.yml`. Use `docker compose --env-file /opt/jobfit/.env.prod -f /opt/jobfit/docker-compose.prod.yml config --quiet` for syntax validation without printing resolved secrets. Check sensitive settings by name/presence or in a protected owner session, never in a shared log.
3. Build **both** API and UI images from the reviewed integrated source. The API image must contain the edit-safe sanitizer and `/health.analysis_limit` that UI v3 expects; a UI-only image update is insufficient. The UI image must include `.streamlit/config.toml`, `ui/static/IBMPlexSans.ttf`, and Streamlit 1.64 or newer but below 2. Keep Dockerfile and build context pointed at the integrated checkout. Do not build from `main`, the owner-local profile, or the observability worktree.
4. Only after separate deployment approval, update API and UI services without recreating PostgreSQL, Caddy, Grafana or Prometheus. Keep the old image IDs/tags for rollback. Verify the production dark flags and `analysis_limit=3` on `GET http://127.0.0.1:8000/health` immediately after the update.

## Post-deployment smoke and rollback

- Check API `/health` and Streamlit `/_stcore/health` over the VPS loopback ports. Confirm HTTPS through Caddy still requires Basic Authentication, and only the intended Caddy ports are public. The UI and API stay private behind the existing ingress.
- In a browser behind Basic Authentication, run the **synthetic saved demo only**: Home, language switch, demo results, Analyze Fit display, and session delete. Verify no unexpected `Not Found`, that the UI reads `analysis_limit=3`, and that a real-CV or live action remains unavailable while the dark flags are off. Inspect only content-free operational logs; do not paste personal CVs or call paid providers.
- If any smoke check fails, restore the prior API and UI images and their prior Compose/Caddy files as needed, then verify `/health`, HTTPS/Basic Authentication and the saved demo again. This UI change has no schema migration; do not roll back, reset or restore the database or production ledger merely to reverse UI/API images. Leave observability services untouched.

Remaining gate: the actual VPS Compose/Caddy/image build and deployed browser checks have not been performed here. This local integration is ready for independent CP3 review, not yet approved for deployment or public-live activation.
