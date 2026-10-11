# CP3 figures: application and monitoring screenshots

The owner captured these screenshots on **10 October 2026**, between 17:51 and 19:47 (Asia/Jakarta). Each one is cropped to the application or dashboard area. Browser chrome, other tabs and the macOS screenshot preview were removed. The pixels are otherwise unchanged. The only exception is figure 19, where the macOS preview thumbnail covered an empty part of the *Budget Refusals* panel and was filled with the panel background colour.

Where they were taken:

- **Figures 1-13:** an owner-run session served on `127.0.0.1`, using an uploaded test CV and live model calls.
- **Figures 14-15:** the deployed controlled demo at `https://jobfit-demo.duckdns.org`, which sits behind Caddy Basic Auth (credentials are never shown or stored).
- **Figures 16-19:** the production Grafana dashboard *JobFit - Production Monitoring*, opened through the private tunnel on `127.0.0.1`.

The CV shown is a test CV. The sanitizer removed the name, contact header and Summary before the preview (figure 3).

| File | What it shows | Captured |
| --- | --- | --- |
| `fig01_ui_landing.png` | Landing page: "Cari lowongan. Lihat buktinya di CV kamu.", with an example quote-backed result | 18:43 |
| `fig02_ui_upload_cv.png` | Step 1, upload (PDF, DOCX, TXT, MD; 5 MB) and the privacy notice | 17:51 |
| `fig03_ui_review_sanitized_text.png` | Step 2, the exact sanitized text that will be analyzed ("header lines (3), summary sections (1)" removed) | 17:51 |
| `fig04_ui_consent.png` | Consent bound to the exact text, with the ZDR notice, before any provider call | 17:51 |
| `fig05_ui_cv_ready.png` | CV ready: choose Find Jobs or Check a Job | 17:54 |
| `fig06_ui_find_jobs_filters.png` | Find Jobs with optional pre-search filters | 18:45 |
| `fig07_ui_relevant_jobs.png` | Relevant Jobs: search order, no score yet, local refinement panel | 18:46 |
| `fig08_ui_analysis_progress.png` | Honest stage-based progress during Analyze Fit | 18:46 |
| `fig09_ui_analyze_fit_score.png` | Analyze Fit: 86% evidence coverage (5 MATCH, 2 PARTIAL, 0 NO_MATCH of 7 required) | 18:47 |
| `fig10_ui_evidence_per_requirement.png` | Evidence per requirement with exact CV quotes, "not verifiable" items, strengths and gaps | 18:47 |
| `fig11_ui_improve_my_cv.png` | Improve My CV for This Job: clarify existing evidence | 18:47 |
| `fig12_ui_improve_cv_answer_draft.png` | A possibly missing item: a draft built only from the user's answers, marked "Perlu dicek" | 19:21 |
| `fig13_ui_honest_gap_guidance.png` | A confirmed gap: no claim is added, with learning ideas instead | 19:22 |
| `fig14_ui_check_a_job_deployed.png` | Check a Job on the deployed demo: pasted JD, session only, never added to the corpus | 19:35 |
| `fig15_ui_check_a_job_result_deployed.png` | Check a Job result on the deployed demo: 67% (2 MATCH, 0 PARTIAL, 1 NO_MATCH of 3 required) | 19:42 |
| `fig16_grafana_system_health.png` | Grafana, system health: API scrape and restarts, PostgreSQL and ledger health, CPU, RAM | 19:47 |
| `fig17_grafana_api_and_ai_pipeline.png` | Grafana, API latency, analysis admission/execution outcomes, AI stage latency and outcomes | 19:47 |
| `fig18_grafana_llm.png` | Grafana, LLM attempts, p95 latency, token usage per model, retries and fallbacks | 19:47 |
| `fig19_grafana_cost_and_safety.png` | Grafana, budget remaining and liability, persisted spending, estimated vs accounted cost, ledger size, budget refusals | 19:47 |

These figures are product evidence, not evaluation metrics. The evaluation results stay in `reports/figures/cp2/`.
