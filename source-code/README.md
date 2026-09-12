# AKURU source code

AKURU uses one repository with a React/Vite frontend in `frontend/` and a FastAPI/PostgreSQL backend in `backend/`. The browser calls same-origin `/api/v1/*` routes. During development, Vite proxies those requests to FastAPI on `127.0.0.1:8000`.

The PostgreSQL-backed implementation currently covers authentication, secure sessions, forced first-login password changes, family-scoped portal state, Admin account management, private document uploads, and asynchronous document preflight processing. Coverage, questions, practice, assessments, and reviews still need their full FastAPI implementations.

## Documentation

- [Ordered implementation roadmap](TODO.md)
- [Repository overview and setup](../README.md)
- [Overall architecture](docs/architecture.md)
- [Frontend architecture](frontend/docs/architecture.md)
- [Backend architecture](backend/docs/architecture.md)
- [Environment variables](docs/environment.md)
- [Database backup and restore](docs/database-backup.md)
- [Private document storage](backend/docs/document-storage.md)
- [Asynchronous document processing](backend/docs/document-processing.md)
- [User guides](../user-docs/README.txt)

## Run locally

Start PostgreSQL and Redis, then use three terminals from this folder:

```bash
npm run backend:dev
```

```bash
npm run backend:worker
```

```bash
npm run dev
```

Open `http://127.0.0.1:5180`. Accounts come only from PostgreSQL and must be created by the bootstrapped Admin.

## Verify

```bash
npm test
npm run typecheck
npm run lint
npm run build
```

Or run the complete local quality gate with `npm run verify`. PostgreSQL integration tests require the configured local database to be running and migrated.

Private `.env` files, Python environments, dependencies, and local data are excluded from Git.
