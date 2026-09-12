# AKURU source code

AKURU uses one repository with a React/Vite frontend in `frontend/` and a FastAPI/PostgreSQL backend in `backend/`. The browser calls same-origin `/api/v1/*` routes. During development, Vite proxies those requests to FastAPI on `127.0.0.1:8000`.

The PostgreSQL-backed implementation currently covers authentication, secure sessions, forced first-login password changes, family-scoped portal state, and Admin creation/update of Parent and Student accounts. Document ingestion, coverage, questions, practice, assessments, and reviews still need their FastAPI endpoints.

## Documentation

- [Ordered implementation roadmap](TODO.md)
- [Repository overview and setup](../README.md)
- [Overall architecture](docs/architecture.md)
- [Frontend architecture](frontend/docs/architecture.md)
- [Backend architecture](backend/docs/architecture.md)
- [User guides](../user-docs/README.txt)

## Run locally

Start PostgreSQL, then use two terminals from this folder:

```bash
npm run backend:dev
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

Private `.env` files, Python environments, dependencies, and local data are excluded from Git.
