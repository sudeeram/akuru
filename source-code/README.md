# AKURU source code

AKURU uses one repository with a React/Vite frontend in `frontend/` and a FastAPI/PostgreSQL backend in `backend/`. The browser calls same-origin `/api/v1/*` routes. During development, Vite proxies those requests to FastAPI on `127.0.0.1:8000`.

The PostgreSQL-backed implementation covers authentication, secure sessions, family-scoped accounts, private document processing, reviewed curriculum content, cumulative coverage, official assessments, source-grounded marking, mastery, recommendations, adaptive study plans, role-specific review experiences, and reviewed educational media.

## Documentation

- [Implementation roadmaps](todo/README.md)
- [Repository overview and setup](../README.md)
- [Overall architecture](docs/architecture.md)
- [Frontend architecture](frontend/docs/architecture.md)
- [Frontend/backend integration status](frontend/docs/backend-integration.md)
- [Backend architecture](backend/docs/architecture.md)
- [Environment variables](docs/environment.md)
- [Database backup and restore](docs/database-backup.md)
- [Step 0: Foundation protection](backend/docs/step-00-foundation-protection.md)
- [Step 1: Backend module boundaries](backend/docs/step-01-module-boundaries.md)
- [Step 2: Private document storage](backend/docs/step-02-document-storage.md)
- [Step 3: Asynchronous document processing](backend/docs/step-03-document-processing.md)
- [Step 4: Deterministic PDF/image extraction](backend/docs/step-04-document-extraction.md)
- [Step 5: OpenAI provider and secret configuration](backend/docs/step-05-ai-provider.md)
- [Step 5A: Ordered OpenAI account routing](backend/docs/step-05a-ai-account-routing.md)
- [Step 6: Reviewed textbook extraction and publication](backend/docs/step-06-textbook-review.md)
- [Step 7: Curriculum plans and cumulative coverage](backend/docs/step-07-curriculum-plans.md)
- [Step 8: Official material review](backend/docs/step-08-official-material-review.md)
- [Step 9: Question-to-unit mapping](backend/docs/step-09-question-unit-mapping.md)
- [Step 10: Approved retrieval and RAG](backend/docs/step-10-approved-retrieval.md)
- [Step 11: Immutable assessment delivery](backend/docs/step-11-immutable-assessments.md)
- [Step 12: AKURU assessment service](backend/docs/step-12-assessment-service.md)
- [Step 13: Subject-specific marking](backend/docs/step-13-subject-marking.md)
- [Step 14: Unit mastery and confidence](backend/docs/step-14-unit-mastery.md)
- [Step 15: Weakness diagnosis and recommendations](backend/docs/step-15-weakness-diagnosis.md)
- [Step 16: Adaptive study planner](backend/docs/step-16-adaptive-study-planner.md)
- [Step 17: Role-specific experiences](backend/docs/step-17-role-experiences.md)
- [Step 18: Diagrams and optional media](backend/docs/step-18-educational-media.md)
- [Step 19: Evaluation and release gates](backend/docs/step-19-evaluation-release-gates.md)
- [Step 20: Production security, privacy and operations](backend/docs/step-20-production-security-operations.md)
- [User guides](../user-docs/README.txt)

## Run locally

Start PostgreSQL and Redis, then use three terminals from this folder:

```bash
npm run backend:dev
```

For a new database, run `npm run backend:migrate` followed by `npm run backend:seed` before creating the first Admin.

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
