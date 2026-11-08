# Private AI request and failure diagnostics

Added 7 November 2026 to investigate a tutor that appears to prepare a reply but returns no answer. No database migration or new public endpoint.

## What is captured

Opt-in diagnostics wrap the existing backend OpenAI SDK operations: structured Responses, image generation, remote embeddings and Realtime session credential creation. Each existing text-provider retry gets its own call ID; no additional paid calls or diagnostic retries are made. Browser-to-OpenAI Realtime audio traffic is not proxied or captured here. Existing transcript/voice usage handling remains separate. Fake/local embeddings make no external model call and are not logged as one.

Events include UTC timestamp, HTTP trace ID, individual model-call ID, model, purpose, prompt name/version, request instructions/task/source-page text, parsed model output, response ID, usage and latency. Content is optional and capped; truncation and content hashes are explicit. Images are represented only by presence/count, embeddings omit vectors, and credential responses omit secret values. SDK schema failures record validation locations/messages without input values. SDK connection/authentication exceptions record safe type/code, never raw exception dumps.

The HTTP trace records completion status and exact controlled AKURU error code/message. This distinguishes quota/rate failures before a model call, provider failures, and a successful provider reply rejected by later citation, teaching-boundary or visual validation. A completed `AIInvocation` means provider completion, not necessarily a delivered student answer; use the full trace to see the final outcome. Deterministic help/topic-list replies have HTTP events but no model events, which is expected.

The same trace ID is returned in `X-AKURU-Trace-ID`. Request bodies, query strings, authentication routes/headers/cookies and CSRF tokens are not logged by the HTTP layer. Per-call content is captured only from explicitly selected model inputs/outputs, with configured credentials and common secret patterns redacted. Redaction is best effort for arbitrary personal secrets typed into free text: these are still private student-data logs, not suitable for public issue attachments.

## Configuration

```dotenv
AKURU_AI_DIAGNOSTICS_ENABLED=true
AKURU_AI_DIAGNOSTICS_CAPTURE_CONTENT=true
AKURU_AI_DIAGNOSTICS_DIRECTORY=/data/akuru/diagnostics/ai
AKURU_AI_DIAGNOSTICS_RETENTION_DAYS=7
AKURU_AI_DIAGNOSTICS_MAX_CONTENT_CHARACTERS=200000
AKURU_AI_DIAGNOSTICS_MAX_FILE_BYTES=10485760
```

Both flags default to false. Enable capture temporarily when investigating an authorised conversation. Content contains student messages, bounded chat history and retrieved textbook passages. Metadata-only mode leaves content out but retains hashes and sizes.

The directory is private (0700), files are 0600, and the app user owns them. JSONL rotation is locked across API/worker processes and retains at most the active 10MiB file plus five backups (approximately 60MiB total, subject to one bounded record). Files older than seven days are removed on subsequent writes. If no writes occur, old files remain until the next event; administrators can remove them manually. This is operational diagnostic retention, separate from transcript retention. No log lives in Git, document storage, public assets, or a public API.

Logging failure produces a generic operational warning and does not fail a student request, alter quotas or trigger model retries. Disable either flag to stop future capture; disabling does not erase existing logs.

## Enable or disable on the production server

After deploying tested code, use the root-only helper. It validates a staged protected environment file, backs up the old one, preserves all unrelated configuration and creates the private directory owned by `akuru`.

```bash
cd /opt/akuru/source-code/backend
sudo .venv/bin/python ../../deploy/ubuntu/configure-ai-diagnostics.py --enable-content
sudo systemctl restart akuru-api akuru-worker
# Later stop content capture or all diagnostics:
# sudo .venv/bin/python ../../deploy/ubuntu/configure-ai-diagnostics.py --metadata-only
# sudo .venv/bin/python ../../deploy/ubuntu/configure-ai-diagnostics.py --disable
# sudo systemctl restart akuru-api akuru-worker
```

## Inspect on the production server

```bash
cd /opt/akuru/source-code/backend
sudo -u akuru .venv/bin/python scripts/inspect_ai_diagnostics.py --last 30
sudo -u akuru .venv/bin/python scripts/inspect_ai_diagnostics.py --trace TRACE_ID --last 100 --content
```

Default output contains metadata only. Use content inspection only when needed. For a failed send, find `api.error` / `http.response`, then inspect the same trace's `model.request`, `model.response` or `model.error`. Absence of a model event means the request was blocked or handled before OpenAI. A process interruption may leave a start event without a completion event; the corresponding systemd journal and deployed release identify the interruption.

Existing failures cannot be reconstructed retrospectively because their raw responses and detailed validation errors were not retained. Reproduce once after enabling this logging. No student allowance increase, safety bypass or relaxed output validation is part of this change.

## Deployment verification — 8 November 2026

Release `2e30ec9` was pushed and deployed with private content capture enabled. All 431 backend regressions passed (one skipped), including nine diagnostic tests; standard production HTTPS, routing, service and binding acceptance passed. A normal unauthenticated request remained 401 and produced correlated error/completion events; directory/file permissions were verified as 0700/0600.

The authorised Student reproduction of “Let's study Life Processes” produced `student_ai_text_quota_exhausted` (429) before any model call. No provider request was made for that trace. The existing tutor reservation algorithm uses instruction/task character length plus the maximum output token budget as a conservative token reservation; therefore it can reject a request while the displayed remaining token balance is positive. Changing that estimator or the quota-exhaustion wording is separate from this diagnostic release. No quotas, usage records, access grants, validation rules or student profiles were changed. Older unlogged 502 responses remain unreconstructable.
