# AKURU backend

This folder contains the real backend foundation. FastAPI provides authentication, role-scoped portal state, Admin account/enrolment management, private document ingestion, health, readiness and curriculum endpoints. SQLAlchemy models and Alembic migrations own the PostgreSQL schema. Redis transports document job identifiers to a separate worker; PostgreSQL remains authoritative. The backend also contains the structured OpenAI provider boundary used by upcoming extraction and learning workflows. The frontend calls the API through `/api/v1`.

## One-time local setup

Run these commands from this `backend` folder after Python dependencies have been approved:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m app.bootstrap_database
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m app.seed_catalog
```

The private `.env` file contains the local connection settings and is ignored by Git. Commit `.env.example`, never `.env`. The settings code uses SQLAlchemy's structured URL builder, so special characters in passwords are handled safely. A new database starts at the single supported Alembic baseline, `0001_initial_akuru_schema`; `alembic upgrade head` then applies every later forward migration.

The safeguards for clean-checkout verification, configuration and recovery are documented in [Step 0 foundation protection](docs/step-00-foundation-protection.md). The router, schema, service, repository and permission responsibilities are documented in [Step 1 module boundaries](docs/step-01-module-boundaries.md).

## Run and test

From `source-code`:

```bash
npm run backend:dev
npm run backend:worker
npm run dev
npm run test:backend
npm test
```

Run the API, worker and frontend in separate terminals. Redis must be available at the configured URL before starting the worker. The API runs at `http://127.0.0.1:8000`; interactive OpenAPI documentation is at `/docs`. `npm test` runs the frontend suite and then the backend suite. Authentication integration tests use PostgreSQL transactions that are rolled back, so test users and sessions are not retained.

Uploads return after the original bytes and an authoritative queued job are stored. The worker performs bounded preflight processing and updates progress for the Admin UI. See [Step 3 document processing](docs/step-03-document-processing.md) for states, retries and recovery.

AI is disabled by default and tests use a fake provider. See the [Step 5 AI provider guide](docs/step-05-ai-provider.md) and [Step 5A account-routing guide](docs/step-05a-ai-account-routing.md) before configuring backend-only OpenAI keys and models.

Admins create a Textbook → Unit/Module Group → Topic structure, attach scanned parts to topics, and publish reviewed topic content before past papers can be accepted. See [the topic-only baseline record](docs/database-baseline-step-01-topic-only-schema.md).

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

Before public deployment, set `AKURU_ENVIRONMENT=production`, `AKURU_COOKIE_SECURE=true`, and `AKURU_TUTOR_RELEASE_GATES_REQUIRED=true`, then replace allowed hosts/origins with the real HTTPS host. Terminate TLS at the reverse proxy, prevent direct public access to PostgreSQL, and configure the proxy to overwrite forwarded-client headers. Production API documentation is disabled automatically. Complete the staged Tutor releases and run `.venv/bin/python -m app.tutor_release_check` before enabling public traffic.

## Database changes

The one-time empty-database reset has closed. Edit SQLAlchemy models, generate a
reviewed forward migration, and apply it:

```bash
.venv/bin/python -m alembic revision --autogenerate -m "describe change"
.venv/bin/python -m alembic upgrade head
```

Prefer additive changes. Any destructive transformation needs an explicitly
reviewed, data-preserving forward migration, tested backup and restore evidence,
and a rollback plan. Never restore the archived pre-baseline migration chain or
recreate a populated database for a routine upgrade. See
[docs/architecture.md](docs/architecture.md) for boundaries and constraints.
