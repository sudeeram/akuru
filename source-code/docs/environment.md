# Environment variables

Copy `backend/.env.example` to `backend/.env` for local development. The real file is ignored by Git. Never put credentials in frontend variables, committed files, screenshots, logs or support messages.

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
| `AKURU_SESSION_HOURS` | No | Session lifetime from 1 to 168 hours; default `12`. |
| `AKURU_LOGIN_ATTEMPT_LIMIT` | No | Failed logins allowed in the throttle window; default `8`. |
| `AKURU_LOGIN_WINDOW_MINUTES` | No | Login throttle window; default `15`. |
| `AKURU_LOGIN_LOCK_MINUTES` | No | Lock duration after the limit is reached; default `15`. |
| `AKURU_STORAGE_BACKEND` | Yes | `local` for development or `oci` for private OCI Object Storage. |
| `AKURU_LOCAL_STORAGE_PATH` | Local | Absolute private filesystem root; default `/data/akuru/documents`. |
| `AKURU_MAX_DOCUMENT_BYTES` | No | Maximum original document size; default 52,428,800 bytes (50 MB). |
| `AKURU_REDIS_URL` | Yes | Private Redis connection used to transport document job IDs. |
| `AKURU_DOCUMENT_QUEUE_NAME` | No | Redis list name for document jobs; default `akuru:documents`. |
| `AKURU_DOCUMENT_JOB_TIMEOUT_SECONDS` | No | Maximum processing time per isolated stage; default `120`. |
| `AKURU_DOCUMENT_JOB_MEMORY_MB` | No | Linux worker address-space limit per isolated stage; default `512`. |
| `AKURU_DOCUMENT_MAX_PAGES` | No | Maximum pages accepted by document preflight; default `500`. |
| `AKURU_EXTRACTION_VERSION` | No | Version key used for idempotent stage results; default `preflight-v1`. |
| `AKURU_OCI_OBJECT_NAMESPACE` | OCI | OCI Object Storage namespace. |
| `AKURU_OCI_OBJECT_BUCKET` | OCI | Private bucket dedicated to AKURU documents. |

Production credentials belong in OCI Vault and should be injected into the backend and worker processes at deployment time. Keep PostgreSQL and Redis private to the server network. Use separate database users and secrets for development, CI and production. OpenAI settings will be added when that roadmap step is implemented.
