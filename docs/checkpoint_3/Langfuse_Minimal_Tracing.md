# CP3 Langfuse tracing candidate

This adapter is **off by default**. With `JOBFIT_LANGFUSE_ENABLED=1`, nonempty
`LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` enable metadata-only tracing to
`https://jp.cloud.langfuse.com`. Missing credentials leave tracing off. The
Langfuse SDK is installed by `requirements.txt`; no credential is stored in Git.
Production Compose must explicitly pass these three variables to the API
container from the owner's secret environment file; this candidate does not
modify the untracked production Compose or any production secret.
Do not enable production tracing until the owner verifies an exported synthetic
canary trace in the Japan project and the CP3.4 privacy gate.

One trace begins in the asynchronous analysis worker after admission. The
separate D-103 parse and search executions also receive one trace each, so
actual CV parsing, query embedding, and retrieval can be inspected. HTTP
acceptance and idempotent duplicates do not start traces. Nested stage spans
appear only for executed boundaries. Cached extraction has no invented span.
Parse and search are not fabricated inside job analysis traces. Durable ledger callbacks add a child
generation for each actual LLM attempt within that analysis. Token counts and
cost appear only when the ledger records known reported or token-estimated
usage; uncertain upper bounds do not masquerade as settled cost. LLM attempt
latency is recorded as bounded metadata because this callback occurs after
the provider call, not at its start. Internal ledger and budget decisions
remain authoritative.

The adapter never passes CVs, JDs, prompts, outputs, user IDs, request headers,
raw exceptions, or HTTP bodies to the SDK. The SDK mask is a backup; the export
filter also refuses any span name, OpenTelemetry attribute, event, link, or
resource attribute outside the explicit allowlist. A changed SDK payload
therefore drops the span. The SDK's `langfuse.release`/`langfuse.environment`
(taken from deploy variables such as `GITHUB_SHA`) pass only as a short
`[A-Za-z0-9._-]{1,64}` token. Langfuse SDK v4 uses the **public project key**
inside the local OpenTelemetry instrumentation scope for project routing. The
filter requires the exact configured key, then the final exporter removes scope
attributes before OTLP serialization. The public and secret keys are used only
for HTTPS transport authentication, never as trace payload fields. Provider or
exporter errors cannot change analysis results. A privacy self-check failure
blocks tracer construction.

Synthetic local check (never use real CVs or provider keys):

```sh
PYTHONPATH=src python -m pytest -q tests/test_langfuse_tracing.py
```

With owner-provided credentials in a local untracked environment, enable the
flag and run an **owner-controlled synthetic analysis** through the existing
API. Inspect the exported Langfuse trace JSON for the canary and verify only
the approved metadata fields appear. Do not enable public live or paid AI merely
to populate Langfuse. If the canary leaks, keep tracing off and fail the release
gate. Rollback is `JOBFIT_LANGFUSE_ENABLED=0` followed by the owner's normal
API restart; no schema, ledger, budget, or data migration is involved.
