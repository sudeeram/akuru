# Database baseline Step 4: local reset evidence

Reset date: 17 September 2026

Recovery tag: `pre-baseline-squash-20260917`

Baseline revision: `0001_initial_akuru_schema`

This operation reset only the PostgreSQL database named `akuru` on localhost.
It did not connect to or modify the production server or production database.

## Before the reset

The local API processes listening on port 8000 and the frontend process on port
5180 were stopped. Nothing was listening on port 5181. The configured local
document directory `/Users/sudeera/akuru-data/documents` existed and contained
zero files and zero bytes, so no separate document archive was required.

A PostgreSQL custom-format backup was created outside the source checkout:

`/Users/sudeera/akuru-data/backups/akuru-pre-baseline-step4-20260917.dump`

SHA-256:

`bec94a77bd48d845bf9653ecd2d88b606106d5b3b74671ec85686916b7f437c0`

`pg_restore --list` read the backup successfully and returned 811 archive-list
lines. This backup and the recovery tag provide the documented rollback path.

## Recreated database

The local `akuru` database was dropped and recreated with the configured
`postgres` owner and UTF-8 encoding. The baseline created or confirmed pgvector
0.8.6, and Alembic reported exactly one current head with no schema drift.

The final inventory contains:

- 72 AKURU public tables, plus `alembic_version`
- 1,219 PostgreSQL constraints
- 342 PostgreSQL indexes
- 3 courses and 8 subjects
- 5 curated Tutor avatars and 3 curated Tutor voices
- 1 fresh local Admin
- no educational content records

The Admin was created through `app.bootstrap_admin`. The bootstrap password was
reported as requiring replacement on first login, replaced through the
authenticated API, and then verified to allow an Admin-only route. The final
local credential is stored outside the source checkout at
`/Users/sudeera/akuru-data/local-admin-credentials.txt` with mode 600.

## Verification

`npm run verify` passed against the recreated database:

- generated API contract check passed
- 39 frontend tests passed
- 109 backend tests passed
- TypeScript typecheck passed
- lint passed
- production frontend build passed

The post-reset content audit returned `status: empty` with zero records in every
educational-content category. The local application processes remain stopped;
they can be started normally when local testing resumes.
