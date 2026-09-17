# Database baseline Step 6: production reset evidence

Reset date: 17 September 2026

Reviewed release: `2e2950354b5e275aa102d58684a9023aa94a697e`

Release tag: `database-baseline-v1-20260917`

Maintenance reference: `MW-2026-09-17T0835Z`

## Pre-reset state

Production used database `akuru`, owner `akuru_app`, Alembic revision
`b72fa92d4e11`, and pgvector 0.6.0. The document store contained zero files.
The current-and-legacy content audit returned zero educational records before
backup and again after all application writers stopped.

The server now has an age public recipient at
`/etc/akuru/backup-age-recipient`. Its private recovery identity exists only in
the protected off-host file
`/Users/sudeera/akuru-data/production-backup-age-identity.txt`.

## Backup and recreation

The backup service validated the plaintext PostgreSQL custom dump with
`pg_restore --list` and the document tar with `tar --list`, encrypted both, and
wrote SHA-256 evidence in `akuru-20260917T083713Z.manifest`.

The matching encrypted database archive, encrypted document archive, and
manifest were copied off-host to
`/Users/sudeera/akuru-data/production-pre-reset-20260917/`. The transfer bundle
SHA-256 is
`a394b9116db3bd66fc83827fac3cef1df7048c4917da00293603904fd4efc632`.

Only active connections to `akuru` were terminated. The database was recreated
with its existing least-privilege owner `akuru_app`; server configuration,
roles, `/etc/akuru`, `/data/akuru`, TLS, Redis and PostgreSQL itself were not
removed.

## Result

- current and only Alembic head: `0001_initial_akuru_schema`
- Alembic metadata drift: none
- pgvector: 0.6.0
- public tables: 73, including `alembic_version`
- catalogue: 3 courses and 8 subjects
- fresh Admin accounts: 1
- API, worker, web and Redis services: active
- loopback API health with the production Host header: passed
- public HTTPS health: passed

The fresh Admin was created as `admin` with forced password replacement enabled.
Its temporary credential is stored outside the project in
`/Users/sudeera/akuru-data/production-admin-temporary.txt` with mode 600. The
password replacement and role-level browser acceptance belong to Step 7.

The server evidence record is
`/data/akuru/release-evidence/database-reset-2e2950354b5e275aa102d58684a9023aa94a697e-20260917T083713Z.txt`.
