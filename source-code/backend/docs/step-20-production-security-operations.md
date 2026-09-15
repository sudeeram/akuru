# Step 20 — Production security, privacy and operations

## Network and processes

Only Nginx listens publicly on ports 80/443. It redirects HTTP to HTTPS, terminates TLS 1.2/1.3, adds HSTS/security headers and rate limits `/api`. FastAPI (`127.0.0.1:8000`), the portal (`127.0.0.1:5181`), PostgreSQL and Redis remain on loopback. Systemd runs the API, worker and portal as the unprivileged `akuru` account with filesystem and privilege restrictions. See `deploy/ubuntu` for the executable installation assets.

FastAPI independently validates hosts/origins/body sizes, uses secure HttpOnly/SameSite cookies and CSRF tokens, disables API documentation in production, and adds CSP, frame, MIME, referrer, permissions and HSTS headers. Redis provides distributed per-IP/path limits in production and fails closed if the limiter cannot reach Redis. Existing username/IP login throttling remains a second authentication-specific control.

## Secrets

The project owner previously chose dotenv-style secrets instead of OCI Vault. Production therefore uses `/etc/akuru/akuru.env`, owned by `root:akuru` with mode `0640`, loaded by systemd. It is outside the checkout and persistent data directory. No secret enters Nginx, a service command line, the frontend, an image, an audit event or Git. The CI security check rejects tracked `.env` files, OpenAI-style keys, populated backend secrets and credential variable names in frontend source. Rotate database, OpenAI and operations credentials after suspected exposure and restart all services.

## Quotas and provider privacy

AKURU has Nginx and API request limits, bounded upload/request sizes, worker time/memory/page limits, AI concurrency/token/request ceilings, and rolling per-family assessment request/token budgets. Family quota reservations use a PostgreSQL advisory lock to avoid concurrent overspend. Provider metadata uses a keyed pseudonymous learner reference; usernames, display names, parent identity and raw UUIDs are excluded. Educational content and the minimum answer/context needed for marking still leave the server, so Admins must enable only reviewed providers and models.

Before public deployment, review the current official OpenAI **Your data** documentation at https://platform.openai.com/docs/guides/your-data and record the selected project's retention/data-control eligibility. Confirm API data is not enabled for provider training, decide whether the organization qualifies for Modified Abuse Monitoring or Zero Data Retention, verify each endpoint/model is eligible for the chosen control, and repeat the review whenever models or API endpoints change. Do not claim zero retention merely because AKURU sets local retention.

## Retention and deletion

Defaults are: submitted answers/result evidence 730 days, handwriting files 90 days, rejected or never-published generated media 30 days, and security audit records 2,190 days. Tutor transcripts have no automatic expiry and are redacted only through the reason-required Admin purge. `python -m app.retention` is a dry run; add `--apply` to redact expired answers and generated feedback and delete expired private objects. `--student-id UUID --apply` ignores age thresholds and immediately redacts that child's answer/feedback artifacts and Tutor transcripts, and deletes all of their working files after an authorized request. It retains minimum assessment scores, Tutor summaries, safety metadata and audit history for learning-integrity and safeguarding records. The daily systemd timer applies the policy. Backups expire separately after 30 days, so deleted content ages out of recovery media within that window.

## Monitoring, backup and incidents

The Admin **Operations** screen shows job states, 24-hour provider calls/tokens/failures/latency, family-token ledger totals, alerts and recent audit actions. Operators should alert from systemd failures, Nginx 5xx/429 rates, PostgreSQL capacity, Redis availability, disk space, backup timer failures and OpenAI project budget alerts.

Daily backups cover both PostgreSQL custom format and the configured local document store, encrypt each locally with an `age` public recipient, retain encrypted files for 30 days and never write a decryption identity to the server. At least monthly, copy a matching database/document pair to a separate protected location, decrypt them on an isolated operator machine, restore the document archive into a temporary private directory, and run `python -m app.database_maintenance restore-drill --backup ...` against the database dump. Record date, revision, table count, object count/checksums and operator.

For an incident: restrict Nginx access; preserve system/audit logs; revoke sessions; rotate affected secrets; stop workers if provider or document processing is implicated; identify affected families/objects and time range; restore only from a verified encrypted backup; notify affected guardians as required; document cause and corrective action; then run authorization, malicious-file, prompt-injection, answer-key and restore tests before reopening access.

## Security verification

Tests cover cross-family object access, unpublished objects, role/CSRF checks, origin/host rejection, secure production configuration, rate limits, pseudonymous provider metadata, prompt-injection boundaries, signatures/MIME/size/page limits, answer-key withholding, family quota ledger behavior, evaluation release gates and Admin-only operational data. These controls require an OCI firewall/security-list review and a real TLS/backup/restore drill on the target server before public access.
