# Environment variables

Copy `backend/.env.example` to `backend/.env` for local development. Production systemd reads `/etc/akuru/akuru.env`, owned by `root:akuru` with mode `0640`, following the project owner's choice of protected dotenv secrets instead of OCI Vault. Never put credentials in frontend variables, committed files, screenshots, logs or support messages.

| Variable | Required | Purpose |
| --- | --- | --- |
| `AKURU_ENVIRONMENT` | Yes | Runtime name such as `development`, `test` or `production`. |
| `AKURU_DATABASE_HOST` | Yes | PostgreSQL host. |
| `AKURU_DATABASE_PORT` | Yes | PostgreSQL port, normally `5432`. |
| `AKURU_DATABASE_NAME` | Yes | Application database name. |
| `AKURU_DATABASE_USER` | Yes | PostgreSQL login used by FastAPI and migrations. |
| `AKURU_DATABASE_PASSWORD` | Yes | PostgreSQL password. Keep this only in backend secrets. |
| `AKURU_CORS_ORIGINS` | Yes | JSON list of browser origins allowed to call FastAPI. |
| `AKURU_ALLOWED_HOSTS` | Yes | JSON list of accepted HTTP host names. |
| `AKURU_COOKIE_SECURE` | Yes | Use `true` behind production HTTPS and `false` for local HTTP. |
| `AKURU_OPERATIONS_TOKEN` | Production | Random secret used to key pseudonymous learner references and operational controls. |
| `AKURU_API_RATE_LIMIT_PER_MINUTE` | No | Distributed per-IP/path API ceiling in production. |
| `AKURU_AUTH_RATE_LIMIT_PER_MINUTE` | No | Lower ceiling for authentication endpoints. |
| `AKURU_FAMILY_AI_REQUESTS_PER_DAY` | No | Rolling per-family assessment request budget. |
| `AKURU_FAMILY_AI_TOKENS_PER_DAY` | No | Rolling per-family provider-token budget. |
| `AKURU_FAMILY_WORKING_STORAGE_BYTES` | No | Total retained private working-file bytes for one family. |
| `AKURU_ASSESSMENT_ANSWER_RETENTION_DAYS` | No | Age at which answer and result evidence is redacted. |
| `AKURU_WORKING_FILE_RETENTION_DAYS` | No | Age at which private handwritten-working objects are deleted. |
| `AKURU_REJECTED_MEDIA_RETENTION_DAYS` | No | Age at which rejected/pending generated media is deleted. |
| `AKURU_AUDIT_RETENTION_DAYS` | No | Security/content audit retention period. |
| `AKURU_SESSION_HOURS` | No | Session lifetime from 1 to 168 hours; default `12`. |
| `AKURU_LOGIN_ATTEMPT_LIMIT` | No | Failed logins allowed in the throttle window; default `8`. |
| `AKURU_LOGIN_WINDOW_MINUTES` | No | Login throttle window; default `15`. |
| `AKURU_LOGIN_LOCK_MINUTES` | No | Lock duration after the limit is reached; default `15`. |
| `AKURU_STORAGE_BACKEND` | Yes | `local` for development or `oci` for private OCI Object Storage. |
| `AKURU_LOCAL_STORAGE_PATH` | Local | Absolute private filesystem root; default `/data/akuru/documents`. |
| `AKURU_MAX_DOCUMENT_BYTES` | No | Maximum original document size; default 52,428,800 bytes (50 MB). |
| `AKURU_MALWARE_SCAN_COMMAND` | Production | Malware scanner executable; production requires `clamscan`. |
| `AKURU_MALWARE_SCAN_TIMEOUT_SECONDS` | No | Fail-closed scanner timeout; default `30`. |
| `AKURU_REDIS_URL` | Yes | Private Redis connection used to transport document job IDs. |
| `AKURU_DOCUMENT_QUEUE_NAME` | No | Redis list name for document jobs; default `akuru:documents`. |
| `AKURU_EMBEDDING_PROVIDER` | No | `local` for deterministic development retrieval or `openai` for production semantic retrieval. |
| `AKURU_EMBEDDING_MODEL` | No | Embedding model/version recorded with every immutable retrieval chunk. |
| `AKURU_EMBEDDING_DIMENSIONS` | No | Must be `256` for the current pgvector schema. |
| `AKURU_DOCUMENT_JOB_TIMEOUT_SECONDS` | No | Maximum processing time per isolated stage; default `120`. |
| `AKURU_DOCUMENT_JOB_MEMORY_MB` | No | Linux worker address-space limit per isolated stage; default `512`. |
| `AKURU_DOCUMENT_MAX_PAGES` | No | Maximum pages accepted by document preflight; default `500`. |
| `AKURU_EXTRACTION_VERSION` | No | Version key used for idempotent stage results; default `deterministic-v1`. |
| `AKURU_DOCUMENT_RENDER_DPI` | No | Review-image resolution; default `180`, accepted range 96–300. |
| `AKURU_DOCUMENT_OCR_MIN_CHARACTERS` | No | Native-text threshold below which a page receives OCR; default `40`. |
| `AKURU_TESSERACT_COMMAND` | No | Tesseract executable name or absolute path; default `tesseract`. |
| `AKURU_OCI_OBJECT_NAMESPACE` | OCI | OCI Object Storage namespace. |
| `AKURU_OCI_OBJECT_BUCKET` | OCI | Private bucket dedicated to AKURU documents. |
| `AKURU_AI_PROVIDER` | No | Single-provider compatibility mode: `disabled`, `fake` or `openai`; default `disabled`. |
| `AKURU_OPENAI_API_KEY` | Single-provider mode | One backend-only OpenAI key. Prefer the account pool for production. |
| `AKURU_OPENAI_MODEL` | Single-provider mode | Model for the single-provider compatibility configuration. |
| `AKURU_OPENAI_ACCOUNT_KEYS` | Account pool | JSON map from Admin-managed aliases to backend-only OpenAI keys. |
| `AKURU_AI_TIMEOUT_SECONDS` | No | Timeout for a complete provider request; default `45`. |
| `AKURU_AI_MAX_RETRIES` | No | Bounded retries within one account; default `2`, maximum `3`. |
| `AKURU_AI_MAX_CONCURRENCY` | No | Concurrent requests allowed per provider client; default `2`. |
| `AKURU_AI_MAX_PAGES_PER_REQUEST` | No | Maximum selected source pages in one AI request; default `8`. |
| `AKURU_AI_MAX_INPUT_CHARACTERS` | No | Maximum source/task text characters; default `80000`. |
| `AKURU_AI_MAX_IMAGE_BYTES` | No | Maximum decoded image bytes in one request; default `20971520`. |
| `AKURU_AI_MAX_OUTPUT_TOKENS` | No | Responses API output ceiling; default `4000`. |
| `AKURU_TUTOR_TEXT_ENABLED` | No | Release flag for text tutoring; defaults to `false`. |
| `AKURU_TUTOR_VOICE_ENABLED` | No | Release flag for realtime voice; defaults to `false`. |
| `AKURU_TUTOR_TOOLS_ENABLED` | No | Release flag for Tutor tool calls; defaults to `false`. |
| `AKURU_TUTOR_RELEASE_GATES_REQUIRED` | Production | Requires passing, staged database release gates for Tutor text, voice and individual tools. Must be `true` in production. |
| `AKURU_TUTOR_REALTIME_MODEL` | No | OpenAI Realtime model used for voice; defaults to `gpt-realtime`. |
| `AKURU_TUTOR_REALTIME_CONNECTION_SECONDS` | No | Maximum voice seconds reserved for one connection, from 60 to 3,600; defaults to 600. Unused seconds are returned when the connection closes. |

Protect the production dotenv file as `root:akuru` mode `0640`. Keep PostgreSQL and Redis private to the server network. Use separate database users and secrets for development, CI and production.

Tutor flags are backend controls and must never use a frontend-exposed environment-variable prefix. Enabling a flag does not permit Tutor access during a live mock or official-paper attempt; FastAPI applies that restriction independently.

Example account pool:

```dotenv
AKURU_OPENAI_ACCOUNT_KEYS='{"HOME":"sk-...","BACKUP":"sk-..."}'
```

The names are aliases, not account IDs. Add the same aliases in the Admin portal and assign unique priorities from 0–100. Changing priority never requires changing the dotenv file.
