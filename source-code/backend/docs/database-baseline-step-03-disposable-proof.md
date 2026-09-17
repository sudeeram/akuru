# Database baseline Step 3: disposable installation proof

This record proves that the consolidated AKURU baseline can create a complete
application database from zero. The exercise used only the disposable database
`akuru_baseline_test`; it did not migrate, reset or otherwise modify the local
`akuru` database or the production database.

## Test environment

- PostgreSQL 18 on the local development computer
- disposable database owner: `akuru_baseline_test_role`
- owner privileges: `NOSUPERUSER`
- migration head: `0001_initial_akuru_schema`
- pgvector: `0.8.6`, provisioned by the PostgreSQL administrator before the
  application-role migration, matching the production prerequisite workflow

## Empty-install evidence

The database began empty. Running `alembic upgrade head` as the non-superuser
owner completed successfully. `alembic current`, `alembic heads` and
`alembic check` all reported the single `0001_initial_akuru_schema` head with no
unproduced schema operations.

The installed database contained:

- 72 AKURU public tables, plus `alembic_version`
- 1,219 PostgreSQL constraints
- 342 PostgreSQL indexes
- 3 course catalogue rows
- 8 iGCSE subject catalogue rows
- 5 curated tutor avatars
- 3 curated tutor voices

The catalogue seed was run explicitly after migration and completed
idempotently. CI and the reviewed-release deployment script now run the same
seed step after applying migrations.

## Application acceptance evidence

- complete backend suite: 109 passed
- frontend suite: 39 passed
- generated OpenAPI and TypeScript contracts: generated and current
- frontend typecheck: passed
- frontend lint: passed
- frontend production build: passed
- Ubuntu deployment shell syntax checks: passed for every deployment script
- tracked-secret and frontend/backend secret-boundary check: passed

The backend integration suite exercised the minimal topic lifecycle on this
fresh database: textbook creation, Unit/Module grouping, topic creation,
scanned-document metadata and extraction, independent topic publication,
versioned cumulative coverage, weighted same-subject question mapping, and
retrieval chunk generation and retrieval behavior.

A disposable Admin was also created through the real bootstrap command. Its
initial password required replacement on first login. After replacement, the
Admin route was authorized, while a disposable Parent received HTTP 403 for
the same Admin-only route. The bootstrap implementation has a regression test
that preserves this forced-change rule.

## Cleanup

After all results above were recorded, only `akuru_baseline_test` and
`akuru_baseline_test_role` were removed. The temporary local credential and
acceptance scripts were also deleted. Step 4 remains the first step permitted
to reset the normal local `akuru` database.
