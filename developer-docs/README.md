# AKURU developer handbook

This handbook explains the current AKURU implementation for developers. It describes the running system rather than the historical order in which features were added. User instructions belong in `../user-docs`; implementation-step records remain in `../source-code/backend/docs`, `../source-code/frontend/docs`, and `../source-code/todo`.

## Start here

1. [System architecture](01-system-architecture.md) — processes, request flow, trust boundaries and repository layout.
2. [Frontend](02-frontend.md) — React/Vinext structure, navigation, state, API calls and accessibility.
3. [Backend API](03-backend-api.md) — FastAPI layers, routes, validation, services, repositories and workers.
4. [Data and content lifecycle](04-data-and-content.md) — PostgreSQL, migrations, textbook topics, documents, retrieval and immutable publication.
5. [Authentication and security](05-authentication-and-security.md) — sessions, CSRF, authorization, family isolation and production controls.
6. [AI, assessment and tutoring](06-ai-assessment-and-tutoring.md) — provider routing, grounding, marking, mastery, flashcards and Tutor services.
7. [Local development and testing](07-local-development-and-testing.md) — setup, commands, generated contracts and debugging.
8. [Production and operations](08-production-and-operations.md) — Ubuntu/OCI topology, releases, backups, monitoring and recovery.
9. [Changing AKURU safely](09-change-workflow.md) — practical end-to-end workflows for features, APIs, schema and documents.

## Architectural principles

- FastAPI and PostgreSQL are authoritative. The browser never grants access by hiding or showing a control.
- All browser API traffic uses the same-origin `/api/v1` boundary.
- Internal UUIDs, object keys and provider credentials stay outside ordinary user interfaces.
- Uploaded or AI-generated material is a proposal until the relevant Admin review and publication gate passes.
- Published topic content, assessment sessions, results, deck versions and source evidence are immutable records.
- Subject, course, family and Student ownership checks happen before retrieval, generation or file delivery.
- Missing review, coverage or evidence fails closed; AKURU does not broaden a syllabus to find content.
- Production changes use forward Alembic migrations and the reviewed release scripts.

## Source-of-truth map

| Concern | Source of truth |
| --- | --- |
| Runtime configuration | `source-code/backend/app/config.py` and `source-code/backend/.env.example` |
| Database schema | `source-code/backend/app/models.py` plus `source-code/backend/migrations/versions` |
| HTTP contract | FastAPI route/response schemas and `source-code/backend/docs/openapi.json` |
| Generated frontend API types | `source-code/frontend/lib/generated/api-contract.ts` |
| Browser API integration | `source-code/frontend/api`, exported through `api/index.ts` |
| Authorization | `source-code/backend/app/security.py`, `source-code/backend/app/permissions.py`, and domain services |
| Production services | `deploy/ubuntu` |
| User procedures | `user-docs` |

The OpenAPI JSON and generated TypeScript contract are generated artifacts. Change the FastAPI schemas and routes first, then regenerate them.
