# AKURU backend

This folder contains the first real backend skeleton. FastAPI exposes health, readiness, and curriculum catalog endpoints; SQLAlchemy models and Alembic migrations own the initial PostgreSQL schema. The frontend mock remains in `../frontend/local-server` until feature endpoints are migrated.

## One-time local setup

Run these commands from this `backend` folder after Python dependencies have been approved:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m app.bootstrap_database
.venv/bin/python -m alembic upgrade head
```

The private `.env` file contains the local connection settings and is ignored by Git. Commit `.env.example`, never `.env`. The settings code uses SQLAlchemy's structured URL builder, so special characters in passwords are handled safely.

## Run and test

From `source-code`:

```bash
npm run backend:dev
npm run test:backend
npm test
```

The API runs at `http://127.0.0.1:8000`; interactive OpenAPI documentation is at `/docs`. `npm test` runs the frontend suite and then the backend suite. Authentication integration tests use PostgreSQL transactions that are rolled back, so test users and sessions are not retained.

## Create the first administrator

There is no default production password. Create the first administrator interactively so its password never appears in shell history or source control:

```bash
cd backend
.venv/bin/python -m app.bootstrap_admin --username admin --name "AKURU Administrator"
```

Use at least 12 characters. The password is stored only as an Argon2 hash.

## Authentication security

- `POST /api/v1/auth/login` creates a random opaque session. PostgreSQL stores only its SHA-256 digest.
- The session cookie is `HttpOnly` and `SameSite=Strict`. A separate same-site CSRF cookie supplies the `X-CSRF-Token` value for writes.
- `GET /api/v1/auth/me` restores the signed-in user; `POST /api/v1/auth/logout` requires CSRF and revokes the database session.
- Failed logins are throttled by client and username, with serialized counter updates to resist concurrent bypass.
- `/health` is intentionally public and reveals only a constant liveness value. `/ready`, `/api/v1/catalog`, and future functional routes require a valid session.
- Untrusted browser origins, hosts, and oversized ordinary JSON requests are rejected. Security headers are added to responses.

Before public deployment, set `AKURU_ENVIRONMENT=production`, `AKURU_COOKIE_SECURE=true`, and replace allowed hosts/origins with the real HTTPS host. Terminate TLS at the reverse proxy, prevent direct public access to PostgreSQL, and configure the proxy to overwrite forwarded-client headers. Production API documentation is disabled automatically.

## Database changes

Edit SQLAlchemy models, generate a reviewed migration, and apply it:

```bash
.venv/bin/python -m alembic revision --autogenerate -m "describe change"
.venv/bin/python -m alembic upgrade head
```

Schema changes must be explicit, reviewable migrations. See [docs/architecture.md](docs/architecture.md) for boundaries and constraints.
