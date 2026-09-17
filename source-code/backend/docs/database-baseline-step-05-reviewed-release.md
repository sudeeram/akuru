# Database baseline Step 5: reviewed production release

This document prepares the one-time production baseline reset. It does not
authorize or perform the production reset. Production execution belongs to
Steps 6 and 7 and must use the exact reviewed release SHA and tag recorded here
after CI passes.

Reviewed release SHA: `2e2950354b5e275aa102d58684a9023aa94a697e`

Release tag: `database-baseline-v1-20260917`

GitHub Actions: run `35197718649` passed all jobs.

## Maintenance window and write freeze

Before running the reset, the owner must choose a low-use window, notify the
family users, and record a reference such as `MW-2026-09-17T2200Z`. Do not allow
account changes, uploads, assessments, Tutor sessions or other public writes
during the window. The guarded deployment command requires this reference and
stops `akuru-api`, `akuru-worker` and `akuru-web` before the final audit and
backup. Stopped application services are the write freeze; Nginx may remain up
to return a temporary unavailable response.

## Required preflight

On the server, check out the exact reviewed release and run:

```bash
cd /opt/akuru
sudo ./deploy/ubuntu/release-preflight.sh <reviewed-sha>
```

Preflight requires a clean checkout at the requested commit, protected
production configuration, the exact database name `akuru`, a local PostgreSQL
host, a least-privilege application role, secure cookies, private document
storage, no committed secrets, an eligible current-or-legacy content audit, and
one migration head. It records non-secret evidence under
`/data/akuru/release-evidence`.

## Guarded reset command

Run only during the approved window:

```bash
sudo ./deploy/ubuntu/deploy-reviewed-release.sh \
  --recreate-database <reviewed-sha> \
  --confirm 'RESET AKURU DATABASE' \
  --maintenance-window '<approved-window-reference>'
```

The command refuses a remote database, a database other than `akuru`, the
PostgreSQL administrator as the application role, an invalid role name, a
mismatched current owner, an incorrect confirmation, or a missing maintenance
reference. It repeats the content audit after stopping writers.

The backup service runs before recreation. It verifies the plaintext custom
database dump with `pg_restore --list`, verifies the plaintext document tar
archive with `tar --list`, encrypts both with the off-host age recipient, and
writes their SHA-256 checksums to a fresh manifest. Recreation cannot continue
without that manifest and both validation results.

## Fresh Admin

After the baseline migration and catalogue seed, the guarded command runs this
interactive command itself:

```bash
sudo -u akuru /opt/akuru/source-code/backend/.venv/bin/python \
  -m app.bootstrap_admin --username admin --name "AKURU Administrator"
```

Enter a new temporary password twice at the protected terminal. Do not place it
in shell history, documentation, chat, Git or release evidence. On the first
browser login, replace it with a different password and store the final value in
the family's password manager.

## Acceptance checklist

After services restart:

1. Run `sudo ./deploy/ubuntu/release-acceptance.sh akuru.magicalinternational.com`.
2. Confirm Alembic current and heads both show `0001_initial_akuru_schema` and
   `alembic check` reports no drift.
3. Confirm the catalogue contains three courses, eight subjects, five avatars
   and three voices.
4. Sign in as the fresh Admin, replace the temporary password, and confirm the
   Admin dashboard loads.
5. Create one disposable Parent and Student; confirm Parent and Student cannot
   access Admin routes and delete or disable the acceptance accounts afterward.
6. Confirm the educational-content audit is empty, document storage is empty,
   and no old sessions or password hashes survived the recreation.
7. Confirm HTTPS headers, API/worker/web service health, loopback-only internal
   ports, Redis/PostgreSQL health, and absence of new error logs.
8. Copy the encrypted database dump, document archive, manifest, preflight
   evidence and deployment evidence to the protected off-host backup location.

## Rollback

If audit, backup, recreation, migration or Admin bootstrap fails, keep all AKURU
application services stopped. Decrypt the matching pre-reset database and
document backups on the approved recovery path, recreate `akuru` with its
original owner, restore the custom dump, restore the matching document archive,
and check out tag `pre-baseline-squash-20260917`. Confirm the former Alembic
revision and health checks before restarting services. Record the failed release
SHA, backup manifest, failure, rollback operator and time.
