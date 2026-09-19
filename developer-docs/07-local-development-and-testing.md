# Local development and testing

## Prerequisites

- Node.js 22.13 or later
- Python 3.12
- PostgreSQL with pgvector
- Redis for document-worker flows
- Tesseract and PDF rendering utilities for real extraction

Project dependencies are installed inside the repository; no global JavaScript package is required.

## First setup

From `source-code/backend`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
cp .env.example .env
.venv/bin/python -m app.bootstrap_database
.venv/bin/alembic upgrade head
.venv/bin/python -m app.seed_catalog
```

Review `backend/.env` before running commands. It is ignored by Git. From `source-code/frontend` run `npm ci`.

## Running the system

Use separate terminals from `source-code`:

```bash
npm run backend:dev
npm run backend:worker
npm run dev
```

- Portal: `http://127.0.0.1:5180`
- FastAPI: `http://127.0.0.1:8000`
- Development API docs: `http://127.0.0.1:8000/docs`

The root npm scripts are convenience wrappers. `backend:dev` invokes Python/Uvicorn through `scripts/run-backend.mjs`; the backend itself is Python, not Node.js.

## Verification commands

From `source-code`:

```bash
npm run test:frontend
npm run test:backend
npm run contract:check
npm run typecheck
npm run lint
npm run build
npm run verify
```

`npm run verify` is the required local release gate and runs contract checking, both test suites, TypeScript, lint and the production frontend build.

## Test organization

Frontend tests under `frontend/tests` are fast Node contract/behavior tests. They verify user-visible wiring, API usage, security boundaries and accessibility affordances without substituting for browser acceptance tests.

Backend tests under `backend/tests` include:

- domain and schema tests;
- authenticated HTTP integration tests;
- PostgreSQL constraints and migration-baseline checks;
- document/extraction fixtures;
- AI provider and release-gate behavior; and
- ownership and role isolation.

Integration tests use transactions/fixtures so test accounts and records are not retained.

## API contract workflow

After changing a route or Pydantic response:

```bash
npm run contract:generate
npm run contract:check
```

Commit both `backend/docs/openapi.json` and `frontend/lib/generated/api-contract.ts`. Then update `frontend/lib/api.ts` and the feature consuming the endpoint.

## Database workflow

After changing SQLAlchemy models:

```bash
cd backend
.venv/bin/alembic revision --autogenerate -m "describe the change"
.venv/bin/alembic upgrade head
.venv/bin/alembic check
```

Read the generated migration. Add meaningful constraints/indexes and a safe downgrade where possible. Prove upgrades on a disposable database and test important lifecycle behavior through services, not only table existence.

## Debugging sequence

1. Read the structured browser/API error before checking logs.
2. Confirm FastAPI `/health`; use authenticated `/ready` for database connectivity.
3. Check API, worker and frontend terminals separately.
4. For uploads, inspect document version, job stage, page/block review state and worker logs.
5. For access issues, trace Principal → role → family/student ownership → curriculum eligibility.
6. For AI issues, confirm feature gate, account alias health, model/prompt release, authorized evidence and usage limits.
