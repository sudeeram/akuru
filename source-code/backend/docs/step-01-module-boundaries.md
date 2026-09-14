# Backend module boundaries

Step 1 defines how backend responsibilities are separated so later learning workflows do not accumulate inside one portal module.

## Layers

- `app/api/v1/` contains thin, versioned HTTP routers. Routers parse transport data, apply authentication dependencies and call services.
- `app/schemas/` contains Pydantic request and response contracts grouped by domain.
- `app/services/` owns authorization-aware application rules, transactions and domain validation.
- `app/repositories/` contains reusable SQLAlchemy persistence operations without deciding user access.
- `app/models.py` and Alembic migrations define authoritative relational state and constraints.
- `app/permissions.py`, `app/security.py` and `app/errors.py` provide shared role enforcement, authenticated principals, CSRF protection and stable errors.

Domains have separate routers and schemas for documents, curriculum, questions, assessments, tutoring, mastery and recommendations. A service may call another domain service when a workflow crosses boundaries, while HTTP concerns remain in routers.

## Permission boundary

Every functional endpoint resolves its role and resource scope from the authenticated principal. Admin-only content operations use centralized role and CSRF dependencies. Student writes derive the student identity from the session. Parent reads validate the requested student through the stored parent relationship. Frontend filtering is never treated as authorization.

API errors use a stable envelope containing a machine-readable code, display-safe message and optional field details. Internal exceptions, credentials and private source data are not exposed.

## Frontend contract

FastAPI's OpenAPI document is the source for `backend/docs/openapi.json` and `frontend/lib/generated/api-contract.ts`. Run `npm run contract:generate` after changing an endpoint or schema. `npm run contract:check` and CI reject stale generated contracts.

The complete, evolving backend design remains in [architecture.md](architecture.md). Step 1 is complete when routers contain HTTP concerns, services contain domain rules, repositories contain persistence details, and all access decisions originate from the authenticated principal.
