# Foundation protection

Step 0 establishes the checks and operational safeguards that protect AKURU while later roadmap steps change the application.

## Verification baseline

Run `npm run verify` from `source-code/`. It checks the generated OpenAPI contract, frontend tests, PostgreSQL-backed backend tests, TypeScript, lint and the production frontend build. The integration suite covers authenticated roles, family isolation, iGCSE catalog restrictions, student progression and cumulative Grade + Term coverage.

GitHub Actions repeats these checks from a clean checkout. CI provisions an isolated PostgreSQL service, installs the pgvector extension, applies every Alembic migration and runs the backend integration suite. This catches missing migrations and assumptions based on a developer's existing database.

## Configuration and secrets

Committed `.env.example` files document supported settings with safe placeholders. Actual `.env` files are ignored and must contain deployment-specific database passwords, session configuration, storage paths and provider credentials. See the [environment reference](../../docs/environment.md).

Secrets must not appear in frontend environment variables, generated assets, logs, tests or committed files. Production files should be readable only by the AKURU service account.

## Backup and recovery

The database backup process uses PostgreSQL custom-format backups, validates each archive and supports a restore drill into a temporary database. Original and derived private files under the configured storage root must be backed up separately from PostgreSQL. See the [database backup and restore guide](../../docs/database-backup.md).

Step 0 is complete when a clean environment can run the documented checks and restore its authoritative data without weakening authentication, family scoping or progression behavior.
