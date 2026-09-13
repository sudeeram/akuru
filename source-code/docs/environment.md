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

Protect the production dotenv file with operating-system permissions so only the AKURU backend service account can read it. Keep PostgreSQL and Redis private to the server network. Use separate database users and secrets for development, CI and production.

Example account pool:

```dotenv
AKURU_OPENAI_ACCOUNT_KEYS='{"HOME":"sk-...","BACKUP":"sk-..."}'
```

The names are aliases, not account IDs. Add the same aliases in the Admin portal and assign unique priorities from 0–100. Changing priority never requires changing the dotenv file.
