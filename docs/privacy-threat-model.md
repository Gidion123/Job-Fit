# Privacy and Threat Model

**Version:** privacy-design-v1, 3 October 2026.  
**Decision:** [D-051](decisions.md#d-051-session-only-cv-privacy-and-security).  
**Status:** Design approved by Dion; implementation and security acceptance NOT RUN. **CP3 update (7 Oct 2026):** full public live analysis of real CVs is planned (D-095); on 8 Oct D-102 framed it as a controlled public beta (section 11). It may be enabled only after the CP3.4 release gate in section 11 passes on the deployed stack. Under D-092, privacy remains implemented and component/unit tested only; end-to-end validation and the original-vs-masked comparison are NOT performed yet. CP2.3 adds synthetic development implementation/testing; public API/UI integration and deployment checks remain CP3. This document is the detailed source for privacy behavior. It is not a security certification or permission to send a real CV.

## 1. Scope and trust boundaries

Browser → Streamlit upload/UI → FastAPI/parser → local masking → editable outgoing-text preview → explicit consent → provider gateway and actual LLM/embedding endpoint → session-only results.

Temporary server processing is the accepted v1 architecture: the original file reaches JobFit before masking. Do not describe it as browser-only or guaranteed anonymous. Skills and rare employment histories can still identify a person after direct identifiers are removed. D-021 remains in force: experiments and demo use synthetic CVs; real-CV transmission needs separate explicit consent and a verified release gate. No real-CV processing is authorized by this documentation update.

Protected assets include original bytes, extracted text, masked text, parsing profiles, evidence quotes, CV vectors, pasted JDs, matching results, session credentials and pending-task references. Public JD caches and explicitly labeled synthetic demo artifacts have separate retention rules. Never promote a user's pasted JD or CV into the public corpus or demo cache.

## 2. Input minimization and consent

1. Before upload, explain that JobFit's server temporarily receives the original document. Use HTTPS.
2. Validate the upload, extract text locally without an external model, then detect direct identifiers throughout all text, including summary, sidebar, header and footer. Removing everything before Summary is not sufficient and can destroy evidence.
3. Mask names, emails, phone numbers, detailed addresses, identity numbers and personal profile URLs. A block containing only contact information may be removed; preserve useful professional content in mixed blocks. Do not send original filenames, document metadata, photos or binary documents to model providers.
4. Preserve job titles, skills, activities, achievements, degree/discipline and original date precision. Do not remove arbitrary numbers, technologies or years. Company/institution names and city/country policy remain open (section 9); no silent decision based on a detector default.
5. Show the exact masked text to be used for provider processing, permit corrections and require affirmative consent. Explain gateway/provider processing and retention limits. Any subsequent text edit invalidates prior consent and dependent parsing/vector/matching caches. Consent is bound to this session and text version.
6. Use only approved masked text for LLM parsing, embeddings, matching and suggestions. Quotes are exact substrings of that masked source. If masking fails, stop or offer manual text entry; never silently fall back to raw text. Preview is an extra protection, not a replacement for detection tests.
7. Release original file buffers and raw extracted text as soon as masking produces the preview; cover success, cancellation, exceptions and temporary-file cleanup. Restart upload if original content is needed again. Do not promise physical memory zeroization merely because a Python reference was deleted.

## 3. Data locations and retention

| Asset | Allowed location | End of lifetime |
| --- | --- | --- |
| Original file/raw text | Transient server processing only; restricted temporary files only when unavoidable | After local extraction/masking, or failure/cancel; no original retained for LLM parsing |
| Masked CV/profile/quotes/vector/pasted JD/results | Owner-scoped volatile session memory | Explicit deletion or server expiry; no permanent CV database, disk result cache, backup or browser localStorage |
| Session token/consent/task state | Minimal server session state; opaque client credential | Invalidate on termination; never place credentials in URLs/logs |
| Public job records/vectors/requirements | Existing database/cache | Existing versioned corpus policy |
| Synthetic demo/evaluation results | Explicitly marked synthetic artifacts | Versioned evaluation/demo policy; not a template for storing real CVs |
| Operational events/cost ledger | Sanitized metadata only | Operational retention; no document, quote, filename, credential or contact payload |

Check Streamlit buffers, FastAPI UploadFile spooling, proxy request-body buffering, crash dumps, tracing, caches, backup volumes and hosting policies. A memory-only parser does not establish an end-to-end no-disk guarantee. v1 should use volatile owner-scoped state with persistence disabled; shared/persistent session stores or multiple replicas require an explicit architecture review rather than silently placing CV data in a database. No login is required, but per-request session authorization is mandatory.

## 4. Session lifecycle and deletion

**Primary behavior approved:** a visible “Hentikan & hapus sesi” control; best-effort departure deletion plus server-enforced expiry. The timings below are implementation targets awaiting deployed validation, not present guarantees or OWASP-mandated durations.

| Event | Required behavior / target |
| --- | --- |
| Explicit stop/delete | Atomically invalidate access and cancel cancellable work; clear owned data; return a truthful acknowledgement |
| Navigation away/tab close | Attempt authenticated deletion/disconnect notification; delivery is not guaranteed |
| Lost connection/crash/network failure | Browser-origin liveness lease; target expiry after 2 minutes without a valid signal |
| Normal hidden/background tab | Do not delete solely on visibility change; browser timer suspension can still cause expiry and must be explained |
| Reload | Target a fresh session and clear previous-session UI credentials; revoke old session when identified, otherwise old lease expires; ordinary Streamlit reruns are not browser reloads |
| Inactivity | Proposed fallback: 30 minutes of no meaningful user activity; heartbeat alone must not reset idle age |
| Absolute lifetime | Proposed fallback: 2 hours from session creation, even with ongoing activity |
| Expired/deleted session | Deny access immediately at the server deadline; target removal of remaining owned objects within 1 minute |
| Late provider result | Discard after rechecking session generation and consent version; never recreate expired data |

A browser timer must report actual browser liveness; a server-side loop cannot prove the user is still present. Do not keep a lost session alive simply because its LLM request is running. Polling/cleanup must work even if the user never makes another request. Idle, disconnect and absolute limits are distinct; the earliest applicable deadline wins. Token possession authorizes a session, not a public resource ID. Use high-entropy credentials, validate ownership for read/analyze/delete/feedback, protect state-changing requests from CSRF/origin abuse where applicable, and use secure cookie settings if cookies are chosen.

The two-minute lease plus the one-minute cleanup target can mean roughly three minutes from the last signal to cleanup; access expires earlier. Do not advertise “immediately deleted on tab close.” Deletion cannot recall data already delivered to a provider or erase a user's downloaded copy. Measure logical invalidation and object cleanup separately; do not claim secure physical erasure.

## 5. Provider policy and safe rendering

For real-CV paths, verify the gateway and actual endpoint policies for **both** LLM and embedding, record date/endpoint/retention/location, disable optional prompt logging, and require supported ZDR routing (OpenRouter provider.zdr=true) along with existing data_collection=deny. If no eligible endpoint exists, fail closed or offer the synthetic demo; no silent fallback to weaker privacy. Provider ZDR can permit in-memory prompt caching and is not anonymity. Availability, schema support and privacy controls must be tested together before release.

No private result may enter a cross-user Streamlit cache or a shared conversation history. Preserve only content-free diagnostics; review infrastructure logs and feedback fields too. Treat CV/JD text as untrusted data, validate outputs and render safely without executable HTML or automatic remote-resource loading. Model instructions cannot grant access to another session; access control is enforced in application code. API keys remain server-side.

## 6. Upload and abuse controls

**Real-CV adapter (8 Oct 2026, dark, `e7762a1`..`0fbf37a`):** the consent lease is rebuilt server-side; provider processing of an uploaded CV runs only through `SessionStore.dispatch` with the exact consented masked text; every real-CV-capable provider request (chat and embeddings) carries `provider.data_collection = "deny"` and `provider.zdr = true` per request, with no fallback to a non-ZDR endpoint; the session identifier is never sent (opaque `cv_id`); upload abuse limits apply before any body is read. `real_cv_enabled` stays False until FAIL-37 masking and provider ZDR compatibility pass. Details: [CP3.1 report](checkpoint_3/CP3_01_FastAPI_Service.md#results-8-oct-2026-real-cv-consent-public-beta-adapter).

**Implemented for the controlled beta (8 Oct 2026, `d6e84d5`):** `.pdf`, `.docx`, `.txt` and `.md` only; raw request ≤ 5 MiB + 64 KiB through Starlette's body limiter and file ≤ 5 MiB; memory-only multipart (no temporary file); PDF header, encryption, ≤ 10 pages and text checks; a DOCX central-directory gate (entries, declared sizes, ratio, paths, OOXML parts, macros) before any decompression; UTF-8, NUL and control-character sanity for text; ≤ 100,000 characters with no truncation; extraction in a separate interpreter with an allow-listed environment (no secrets), a 20 s timeout, a 512 MiB address-space limit on Linux and no file writes; one extraction at a time per API process (one API process in the beta); fixed error codes. The worker is resource isolation, not a security sandbox (no seccomp or network namespace). Details: [CP3.1 report](checkpoint_3/CP3_01_FastAPI_Service.md#results-8-oct-2026-lean-public-beta-cv-upload-hardening).

Allow only required file formats; verify structure/signature as well as extension/MIME. Enforce request bytes before full buffering, PDF page/text limits, DOCX expanded-size limits, parsing timeout and memory/concurrency limits. Do not execute macros, scripts, embedded documents or fetch external document links. Keep parser dependencies patched and processing least-privileged; isolate parsing from secrets/network where feasible. Rate-limit sessions, upload and model work as well as enforcing the cost guard. Evaluate local scanning/sandboxing; never upload private CVs to a public scanning service without a separate data-policy decision. Malware scanning does not replace parser limits or isolation.

## 7. Work allocation and evidence

### CP2.3: implement reusable controls and test with development synthetic data

- Add a versioned local masking/preview/consent contract and a shared outgoing-data boundary for CV parsing, query embedding and matching. No raw-text fallback and no cloud model used to redact raw CVs.
- Add session-state/lifecycle primitives and fake-clock tests for authorization, consent-version binding, revoke/expiry and late-response disposal. This prepares API integration; it does not establish public session safety.
- Create synthetic PII variants from **CV1/CV2 only**, using invented identifiers, Indonesian/English wording and varied positions/layouts. Preserve source CVs and gold. CV3-CV5/test remain untouched.
- Test detector misses and harmful over-redaction; report per-entity coverage and evidence/quote preservation. No automatic detector promises complete PII discovery.
- Measure matching/retrieval impact on paired original-synthetic and masked-synthetic cases with the same scope. Masking changes preprocessing and cache identity. Align masked quotes through a development-only transformation receipt rather than rewriting source gold. Any quote alignment ambiguity is held.
- Separate these robustness results from D-029 model comparisons; compare candidates using identical input versions. Record preprocessing, policy, scope, latency, costs and failures. No new paid inference, model winner or test access is authorized by this plan.
- Prepare endpoint-policy feasibility evidence and a release checklist. CP2.3 can report synthetic results while unresolved real-upload details remain blocked for CP3.

**CP2.3 outcome (7 October 2026, D-092):** masking, preview with consent and the session primitives are implemented, and CP2.4 parsed every CV from masked text. They are covered by component/unit tests: the privacy-control and masked-quote tests, and API-level tests with a fake run (PR-01 to PR-07 and PR-09 at that scope, not a deployed host). I have **not** validated privacy end to end, and the original-vs-masked quality comparison (PR-10) has **not** run. Both are CP3 work: CP3.4 runs the end-to-end checks (leakage, logs, outputs, consent and session behavior) and the paired comparison, and CP3.5 reports the results and the effect on matching quality. Until then I make no claim that privacy is validated end to end or that masking leaves matching quality unchanged, and real-CV processing stays off.

### CP3.1-CP3.4: integrate and verify before real-CV enablement

CP3.1 binds every route/task to the real session owner, implements lease/TTL/delete/consent and upload cleanup. CP3.2 verifies no private migrations/persistence/backups, deployment buffering/logs, secrets and TLS. CP3.3 adds pre-upload notice, editable masked preview, explicit send consent, stop/delete, accurate expiry messaging and browser liveness/reload behavior. CP3.4 verifies the deployed application with isolated browsers, provider spies and fault injection. Do not reopen the real-CV path merely because a unit test or user design approval exists. If these gates cannot be completed, keep public demo synthetic-only.

## 8. Mandatory acceptance scenarios (all pending)

| ID | Verification | Required evidence |
| --- | --- | --- |
| PR-01 | Identifiers in header/summary/sidebar/footer, no Summary, two-column CV, Indonesian/English | Entity misses, false removals, preserved skills/dates and masked quote checks |
| PR-02 | Before consent, after text edit, masking error, parser failure | Zero outgoing raw/unauthorized payloads to both chat and embedding clients |
| PR-03 | Two isolated users; swapped session/resource IDs; cache reuse | Cross-session reads/writes/deletes denied; no private result contamination |
| PR-04 | Explicit deletion while parsing/LLM work is active | Immediate invalidation, bounded cleanup, discarded late results, no recreation |
| PR-05 | Navigation, reload, hidden tab, disconnect, crash, idle and absolute age | Fake-clock tests plus browser/deployment observations; measure actual cleanup bounds |
| PR-06 | Upload success/error/timeout, DOCX expansion, oversized/malformed input | Safe rejection, resource limits, no unexpected disk residue/external fetch |
| PR-07 | Database/cache/log/tracing/backup inspection with synthetic canaries | No private text, identifiers, vector or token stored outside owned volatile state |
| PR-08 | Provider unavailable or privacy/schema controls unsupported | Fail closed; no privacy downgrade; endpoint-policy receipts |
| PR-09 | Prompt injection and hostile rendered content | No cross-session access, secret exposure or executable output |
| PR-10 | Same synthetic professional content before/after masking | Paired quality/latency comparison, source/quote compatibility and residual risks |

Log only counts/statuses and synthetic fixtures in test evidence. An acceptance pass applies to its measured scope, not all documents or hosts.

**Synthetic quote check, 4 October 2026:** An [offline receipt](../evals/results/cp23_masking_quote_compatibility_20261004_v1.json) checked 781 nonempty reviewed CV1/CV2 evidence quotes. Masking changed 13 rows representing two repeated contact-header quotes. All 13 have exact transformed spans in the masked synthetic CV. This verifies mechanical quote traceability only. It does not pass PR-10 or settle the open city policy or semantic label compatibility. No real CV, test profile or provider call was used for this check.

## 9. Remaining choices and limits

- City/country and employer/institution handling still require a decision; do not infer consent from a preference filter or permanently store extracted locations. Degree/discipline and activity context must remain useful. No university-prestige classifier is authorized.
- Validate and finalize liveness interval, 2-minute disconnect target, 30-minute idle and 2-hour absolute fallbacks, 1-minute cleanup target and reload/background UX before publishing promises. If infeasible, disclose and seek a scoped revision rather than silently weaken deletion.
- Choose/test a local multilingual detector and deployment session transport. No dependency purchase, new hosting spend or specific redaction library is approved here.
- Existing source-label approvals, scoring, D-029 selection rules, D-046 split, D-050 closure and US$8.50 runtime hard stop remain unchanged. Design approval is distinct from consent to process a particular real CV.

## 10. Primary references (researched 3 October 2026)

- [OWASP File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html): layered validation, resource limits and private processing.
- [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html): server-side expiry, token protection and invalidation.
- [OWASP Logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html): exclude sensitive payloads.
- [OWASP LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html): untrusted inputs, output validation and limited privileges.
- [FastAPI UploadFile](https://fastapi.tiangolo.com/tutorial/request-files/): spooled temporary files can reach disk.
- [Streamlit caching](https://docs.streamlit.io/develop/concepts/architecture/caching): shared cache versus session-scoped state.
- [MDN beforeunload](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event): unreliable departure notification.
- [OpenRouter ZDR](https://openrouter.ai/docs/guides/features/zdr) and [data collection](https://openrouter.ai/docs/guides/privacy/data-collection): endpoint policies, routing and caching caveats.
- [Presidio](https://github.com/data-privacy-stack/presidio): automated PII detection has incomplete coverage; no library choice is implied.

## 11. CP3 public live privacy model (7 Oct 2026, D-095 to D-099): PLANNED / NOT YET VALIDATED

**Controlled public beta (8 Oct 2026, D-102).** Public access means the end-user app only. Public users never get SSH or shell access, container or database administration, direct database connections, environment variables or secrets, deploy or restart controls, budget or live-gate configuration, operator or recovery controls, internal admin endpoints, private operational logs, or Grafana and admin dashboards. Only Caddy publishes ports; every operator and observability interface stays private (D-095). The owner mechanism never weakens the budget, privacy, consent or safety controls. Pasted JDs stay session-only and are never written to the production corpus. Metrics and normal logs carry no CV text, candidate data or raw private content, only pseudonymous correlation ids (D-099).

This section adds the controls for full public live analysis of arbitrary CVs. Every row is a plan. A row is marked validated only when its CP3.4 evidence exists.

| Area | Planned control | Validation (CP3.4) | Status |
| --- | --- | --- | --- |
| Raw CV lifecycle | Upload → hardened text extraction in memory → original bytes deleted → local masking → editable preview → consent → session-only results. Nothing CV-derived is written to the database | Temp-directory scan; database dump grep for canaries | PLANNED |
| Upload hardening | Only the formats the current extractor supports: `.pdf` (text only, ≤ 30 pages, not encrypted), `.docx`, `.txt`, `.md`; ≤ 10 MB; ≤ 100,000 characters. Extension allow-list and signature check; size limit while streaming, before buffering (Caddy, Streamlit, API); **DOCX decompression gate** (central-directory metadata only, bounded entry count, uncompressed size and compression ratio, `word/document.xml` required); extraction timeout; safe errors with no file content. No new formats | Failure-path tests with canaries, including the 6 DOCX gate tests; a deployed rejected-file check | PLANNED |
| Masking boundary | Regex masking (email, phone, ID numbers, profile URLs) plus **user-entered name (required) and address (optional)** as reviewed identifiers. The UI lists exactly what is masked, fixing FAIL-37. Employer, institution and city names stay, because matching needs them, and the consent text says so | Canary tests; UI text test | PLANNED |
| Consent binding | Consent is bound to the exact masked digest. The lease is stored server-side and never sent to the browser. Every provider call for an uploaded CV runs inside `SessionStore.dispatch(handle, lease, op)` and receives only the consented text. The consent compatibility adapter around the frozen parser has no raw-text interface (D-097) | The 7 adapter tests; PR-02 | PLANNED |
| Embedding-provider boundary | Query embedding (Qwen3-Embedding-8B through OpenRouter) receives only the consented masked text, in the recommendation phase | Spy-client payload test; PR-02/PR-08 | PLANNED |
| LLM-provider boundary | CV parse (DeepSeek Flash), JD extraction (DeepSeek Flash, public JD text only) and evidence matching (GPT-6 Sol, Luna fallback) receive only the consented masked CV representation | Spy-client payload test; PR-02/PR-08 | PLANNED |
| OpenRouter routing record | Before public live, Dion and Codex record the actual account privacy settings and the observed upstream routing for each of the four routes. If a promised mode such as zero data retention can't be guaranteed for a route, that is reported before public live and never fixed by changing the model, prompt, K or weights | A written record in this document and the CP3.4 report | PLANNED |
| Logs | JSON logs with an allow-list of fields (request id, run id, session hash, route, status, duration, error code). No CV text, quotes, raw IPs or tokens. Docker log rotation | `docker compose logs` grep | PLANNED |
| Prometheus | Bounded labels only; no job, session, request or run IDs; no content | `/metrics` grep | PLANNED |
| Grafana | Reads Prometheus only; reached through an SSH tunnel | Configuration inspection | PLANNED |
| Langfuse | Required for the final controlled public beta (D-103). Langfuse Cloud hosted free tier (Hobby), Japan region if available; never self-hosted on the VPS; no paid plan without a decision. `capture_input/output=False`, a mask function as a backstop, a metadata allow-list. Never sent: CV text, names, contacts, addresses, identifying employer history, quotes, pasted JDs, session tokens | Exported trace JSON grep | PLANNED |
| Database | Only public job data, the extraction cache for public JDs, HMAC quota rows, budget reservations and sync runs | `pg_dump` grep | PLANNED |
| Error paths | The error taxonomy returns codes. `StageFailure` text and file content are never returned or logged raw | Error-path canary tests | PLANNED |
| Retention | CV session data: lease 2 min, idle 30 min, absolute 2 h (existing), deleted on request. Quota rows: 48 h. Langfuse: plan default (no CV content) | Fake-clock tests; deployed timing (PR-04/05) | PLANNED |
| IP pseudonymisation | `HMAC-SHA256(JOBFIT_IP_HMAC_KEY, ip)`, IPv6 by /64; raw IPs never stored. The client IP is taken from Caddy's `X-Forwarded-For` by Streamlit and passed to the internal API with a service token. Caddy access logs are off or exclude the client IP | Quota tests; configuration inspection | PLANNED |
| Release gate | `JOBFIT_PUBLIC_LIVE=1` only after PR-01 to PR-10 pass on the deployed stack with canaries in every sink above that is enabled for the beta (including the Langfuse row; Langfuse is required for the final beta since D-103), the OpenRouter record exists, the real-CV consent adapter is connected, and `public_beta_phase_eligible` holds: every D-103 beta phase bound is at most the daily cap (the historical D-096 full-analysis condition is not used for the beta) | The CP3.4 gate record | PLANNED |

Until the gate passes, the VPS serves the saved demo, plus owner-token live runs for validation. The CP3.5 report holds the final privacy evaluation and the PR-10 matching-quality impact (D-092).
