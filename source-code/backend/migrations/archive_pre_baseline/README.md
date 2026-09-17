# Archived pre-baseline migrations

These 41 migrations are retained for historical review only. Alembic does not load this directory.

The immutable Git tag `pre-baseline-squash-20260917` is the authoritative recovery point for the complete pre-squash chain. New installations start from `migrations/versions/0001_initial_akuru_schema.py`.

Do not configure Alembic with this directory as a version location and do not apply these revisions to a database using the new baseline.
