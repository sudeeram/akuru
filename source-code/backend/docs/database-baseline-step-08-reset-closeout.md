# Database baseline Step 8 — Reset closeout

The one-time AKURU database reset window closed on 17 September 2026.
Production was created from Alembic revision `0001_initial_akuru_schema` and
normal forward-only database evolution has resumed.

## Supported starting point

New local, test and production databases start with the active migration
`migrations/versions/0001_initial_akuru_schema.py`, then apply every later
migration with `alembic upgrade head`. The old chain under
`migrations/archive_pre_baseline` is historical evidence. It is not an Alembic
version location and must never be applied before or after the new baseline.

The production baseline was installed on 17 September 2026 from reviewed commit
`2e2950354b5e275aa102d58684a9023aa94a697e`. Operational acceptance is recorded
in the [Step 7 evidence](database-baseline-step-07-production-acceptance.md).

## Recovery assets and retention

- The immutable tag `pre-baseline-squash-20260917` retains the former migration
  chain. The reviewed baseline tag is `database-baseline-v1-20260917`.
- The off-host encrypted recovery bundle is
  `/Users/sudeera/akuru-data/production-pre-reset-20260917/akuru-production-pre-reset-evidence.tar`.
- Its verified SHA-256 is
  `a394b9116db3bd66fc83827fac3cef1df7048c4917da00293603904fd4efc632`.
- The age recovery identity remains off-host with owner-only permissions.

Retain both Git tags indefinitely as release history. Retain the special
pre-reset recovery bundle for at least the production 30-day encrypted-backup
retention period and until one post-baseline restore drill passes, whichever is
later. Its recovery identity must remain separate from the server.

## Removed reset paths

The production deployment command now accepts only
`deploy-reviewed-release.sh --execute <reviewed-sha>`. Database drop/recreation,
maintenance-window confirmation, empty-content gating and automatic Admin
bootstrap were removed from the callable deployment path. Normal deployment
still requires an exact clean Git revision, protected configuration, security
preflight, one migration head, a fresh encrypted database/document backup,
`alembic upgrade head`, metadata drift checking, service restart and health
evidence.

## Forward migration policy

All future schema work must use an additive migration where possible. A change
that cannot be additive requires an explicitly reviewed, data-preserving
forward migration with production-like upgrade tests, encrypted backup and
restore evidence, a maintenance/compatibility plan and a documented rollback.
The baseline downgrade deliberately remains unsupported. Never reset or
recreate a populated database as an ordinary upgrade mechanism.

Parent/Student account creation and document ingestion may resume. Chemistry
content remains intentionally deferred by the project owner and can begin later
through the supported Admin workflow.

The temporary acceptance Parent and Student were disabled and all of their
sessions revoked. The obsolete bootstrap Admin password file and local Step 7
scratch artifacts were removed; the current Admin credential and recovery
identity remain protected outside the repository. Production release, baseline,
service and timer checks passed, and the non-secret closeout record is stored at
`/data/akuru/release-evidence/database-reset-closeout-20260917.txt`.
