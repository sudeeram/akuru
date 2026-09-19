# Changing AKURU safely

## Feature change

1. Identify the authoritative domain service and existing lifecycle states.
2. Define authorization, ownership, audit and failure behavior before UI work.
3. Add or change backend schemas, service logic and route.
4. Add meaningful backend integration tests, including denial paths.
5. Regenerate the OpenAPI/TypeScript contract.
6. Add typed functions in `frontend/lib/api.ts`.
7. Build the role-specific feature with loading, empty, error and success states.
8. Add frontend contract/accessibility coverage.
9. Update developer and user documentation if behavior or an Admin procedure changed.
10. Run `npm run verify`.

## Schema change

1. Update SQLAlchemy models.
2. Generate one focused forward Alembic migration.
3. Review constraints, indexes, data transformation, locking and downgrade behavior.
4. Upgrade a disposable database from the supported baseline.
5. Run `alembic check` and the full backend tests.
6. Document operational impact and recovery.
7. Deploy only through preflight, encrypted backup and acceptance scripts.

## New document-processing capability

Keep original bytes immutable. Add a versioned extraction method and record it with every derived artifact. Retain page and bounding-box provenance. Make confidence and review requirements explicit. Do not let worker completion imply Admin approval or publication. Ensure retries do not create duplicate authoritative rows.

## New AI-backed capability

1. Define an interface and deterministic fake implementation.
2. Authorize and bound the context before provider invocation.
3. Use a versioned prompt and strict response schema.
4. Validate identifiers, citations, totals and confidence on the server.
5. Record provider/model/prompt/usage/provenance without secrets.
6. Define failure, retry, account failover and usage-limit behavior.
7. Add human review or a release gate proportional to the consequence.
8. Add a reviewed evaluation corpus before automatic production behavior.

## New frontend screen

Prefer an existing role workspace and feature module. Add navigation only when the capability represents a persistent user destination. Use shared components and the API wrapper. Test keyboard operation, focus, labels, status text, responsive layout and readable visual alternatives.

## Review checklist

- Are course, subject, family and Student boundaries enforced in the service?
- Does every mutation require CSRF and the correct role?
- Are private files re-authorized when delivered?
- Can retries or concurrent requests duplicate data or publication?
- Are published/historical versions left immutable?
- Does missing evidence fail closed with an actionable message?
- Are secrets, UUIDs and object keys absent from user output?
- Do tests prove both success and important denial paths?
- Is the API contract regenerated?
- Do user instructions and operational notes match the final behavior?

## Definition of done

A change is complete when code, schema, API contract, frontend experience, tests, documentation and operational consequences agree. Passing a unit test alone is insufficient for a feature that crosses authentication, database, worker, storage, AI or publication boundaries.
