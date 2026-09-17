# Database baseline Step 2: initial AKURU schema review

## Result

AKURU now has one active Alembic revision:

- Revision: `0001_initial_akuru_schema`
- Parent: none
- Active heads: one
- SQLAlchemy application tables: 72
- Installed PostgreSQL tables after migration: 73, including `alembic_version`
- Deprecated unit-only tables: 0
- pgvector: created idempotently by the baseline; verified locally with extension version 0.8.6

The previous 41 revisions are outside the active version directory under `migrations/archive_pre_baseline`. The immutable tag `pre-baseline-squash-20260917` preserves the original repository state.

## Review performed

The baseline was generated from the final SQLAlchemy metadata against an empty disposable PostgreSQL database, never from the existing local or production AKURU databases.

The generated revision contains:

- 72 table creations
- 188 explicit index creations
- 194 foreign-key constraints
- 81 unique constraints
- 150 check constraints
- PostgreSQL UUID, JSON, numeric, timestamp and pgvector column types from current metadata
- the partial unique indexes that enforce one current progression, one active study plan, one active assessment and one active Tutor session/practice in their defined scopes
- `ck_textbook_group_label`, allowing the intentional `unit` and `module` display labels
- the complete authentication, family, enrolment, document, topic, assessment, mastery, study-plan, Tutor, quota, evaluation and audit table families

Alembic `check` reported no upgrade operations after applying the baseline. `current` and `heads` both reported `0001_initial_akuru_schema (head)`.

## Deliberate adjustments

Alembic autogeneration did not manage the PostgreSQL extension. The reviewed baseline explicitly runs:

```sql
CREATE EXTENSION IF NOT EXISTS vector
```

before creating the vector column and HNSW index.

The baseline refuses downgrade with a runtime error because downgrading it would erase the complete AKURU application database. Recovery uses a reviewed PostgreSQL backup instead.

Mutable catalogue records and child-safe Tutor presets are not embedded in the schema migration. `python -m app.seed_catalog` upserts three courses, eight iGCSE subjects, five curated avatars and three voice presets. Running it twice against the disposable database produced the same counts.

## Scope and safety

The existing local `akuru` database and production database were not migrated, reset or modified. Verification used the disposable local database `akuru_baseline_build`, which was deleted after the checks passed. Step 3 will repeat installation and the complete test suite on a fresh disposable database as the formal release gate.
