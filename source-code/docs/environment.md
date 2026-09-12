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
| `AKURU_OCI_OBJECT_NAMESPACE` | OCI | OCI Object Storage namespace. |
| `AKURU_OCI_OBJECT_BUCKET` | OCI | Private bucket dedicated to AKURU documents. |

Production credentials belong in OCI Vault and should be injected into the backend process at deployment time. Use separate database users and secrets for development, CI and production. OpenAI and object-storage settings will be added when their roadmap steps are implemented.
