# AKURU database baseline reset and migration-squash roadmap

This roadmap replaces AKURU's development-era Alembic chain with one reviewed baseline before real educational or student-learning data is entered. It covers both the local and OCI production databases.

The reset is justified only while the production database contains no educational content and the production Admin account can be recreated. Once real textbook, assessment, mastery, Tutor transcript or student-learning data exists, AKURU must return to forward-only migrations and must not repeat this reset.

Status: `[ ]` not started, `[~]` in progress, `[x]` complete, `[!]` blocked with the reason recorded beside it.

## Non-negotiable safety rules

- Preserve the current migration chain in Git history and an immutable pre-reset tag.
- Audit local and production independently. An empty local database is not evidence that production is empty.
- Take encrypted PostgreSQL and document-storage backups before changing production.
- Stop API, worker and frontend services before recreating the production application database.
- Drop and recreate only the `akuru` application database. Do not remove PostgreSQL, the database role, `/etc/akuru`, `/data/akuru`, TLS material or server configuration.
- Never generate the baseline from a database. Generate it from the final reviewed SQLAlchemy metadata, then test it against an empty database.
- Do not preserve deprecated unit-only compatibility tables merely because they exist in the current model metadata.
- Recreate the Admin account through the supported bootstrap command. Do not copy password hashes or sessions between databases.
- Record the exact Git revision, baseline revision, backup files, checksums, commands, results and rollback decision.

## Step 0 — Freeze and prove reset eligibility

**Goal:** Establish that a destructive database reset is still safe before changing code or migration history.

- [~] Freeze content uploads, account administration and production deployment work for the reset window. The freeze is recorded; owner confirmation is pending.
- [x] Record the current `main` commit and create an annotated pre-squash Git tag.
- [x] Confirm the repository has one current Alembic head and record the full revision history.
- [!] Run `app.content_migration_audit --require-empty` against the local database. It correctly failed because one empty active study-plan shell exists; it contains zero items.
- [x] Run the equivalent read-only table-count audit against production. The deployed revision predates the reusable audit module; the final audit must be rerun immediately before reset.
- [x] Separately count users, Admins, parents, students, sessions, provider accounts, quotas and audit rows in both environments.
- [!] Confirm production contains only the expected Admin identity and catalogue/operational seed data. Production also contains one Parent, one Student, enrolment and quota records.
- [x] Confirm `/data/akuru/documents` contains no uploaded content or unexplained objects.
- [ ] Privately record the production Admin username and display name immediately before recreation; do not commit it or its password/hash.

**Current evidence:** See [Step 0 eligibility record](../backend/docs/database-baseline-step-00-eligibility.md). The current migration chain is preserved by the pushed tag `pre-baseline-squash-20260917`. No database rows, stored files or services were changed.

**Current blocker:** The owner must confirm that the Parent, Student, enrolment, quota and empty local study-plan records are disposable. Until then, the reset path is not authorized to delete them.

**Stop condition:** If either environment contains educational, assessment, mastery, Tutor, parent or student data that must be retained, stop this roadmap and design a forward data migration instead.

**Done when:** Both environments have timestamped audit evidence proving the reset scope, and the existing migration chain is recoverable from Git.

## Step 1 — Remove obsolete compatibility schema and code

**Goal:** Make the final SQLAlchemy metadata represent the intended topic-based architecture before generating a baseline.

- [x] Inventory every legacy unit-only model, foreign key, JSON field, schema, API and service fallback.
- [x] Decide which `unit` names are legitimate display/domain concepts and which refer to the deprecated `textbook_units` implementation.
- [x] Remove deprecated textbook-content, unit-version, unit-coverage and unit-question-mapping models that have been replaced by textbook groups and topics.
- [x] Remove legacy unit retrieval and citation paths after verifying topic retrieval is authoritative.
- [x] Remove legacy unit mastery persistence where group mastery can be calculated from topic mastery.
- [x] Remove legacy unit references from Tutor sessions, practice, recommendations, history and realtime services, or replace them with group/topic references.
- [x] Remove legacy unit references from assessment questions and immutable snapshots while retaining required group/topic provenance.
- [x] Remove unused legacy API routes, request/response fields and frontend contract types.
- [x] Update content audits, retention, backups, operations and release checks for the final table set.
- [x] Regenerate the OpenAPI frontend contract and remove compatibility-only tests.
- [x] Add tests proving no runtime code writes to or reads from deprecated unit-only tables.

**Evidence:** See [Step 1 topic-only schema record](../backend/docs/database-baseline-step-01-topic-only-schema.md). The non-integration backend suite, frontend tests, typecheck and generated-contract check pass. Database-backed integration tests await the clean baseline in Steps 2–3 because the protected local database still contains the pre-squash columns.

**Done when:** The application, tests and SQLAlchemy metadata contain only the intentional Textbook → Unit/Module Group → Topic model, with no hidden dependency on tables that will be absent from the baseline.

## Step 2 — Create one reviewed baseline migration

**Goal:** Replace the 39-migration development chain with one reproducible initial schema.

- [x] Move the old migration files out of the active Alembic versions directory only after the pre-squash tag exists.
- [x] Generate a new baseline revision from empty database state to the final SQLAlchemy metadata.
- [x] Give the revision a stable descriptive name such as `initial_akuru_schema`.
- [x] Review every generated table, column, type, sequence, index, foreign key, unique constraint and check constraint.
- [x] Ensure PostgreSQL `vector` extension creation is explicit and idempotent.
- [x] Ensure both Unit and Module labels are allowed while sharing the same section-group schema.
- [x] Ensure authentication, family isolation, progression, documents, topics, assessments, mastery, Tutor, quotas, evaluation and audit constraints are present.
- [x] Remove downgrade logic that would silently destroy a populated database, or document that baseline downgrade is development-only.
- [x] Keep operational seed data separate and idempotent where practical; do not hide mutable production records inside the migration.
- [x] Confirm there is exactly one Alembic head and one active baseline revision.

**Evidence:** See [Step 2 initial schema review](../backend/docs/database-baseline-step-02-initial-schema.md). The baseline was generated and applied only to the disposable local database `akuru_baseline_build`; the existing local and production AKURU databases remain unchanged.

**Done when:** A reviewer can understand the complete AKURU schema from one baseline migration and it matches the final model metadata without drift.

## Step 3 — Prove the baseline on disposable databases

**Goal:** Demonstrate that a new installation is complete before touching either real database.

- [x] Create an empty disposable PostgreSQL database owned by a non-superuser application role.
- [x] Run `alembic upgrade head` from zero.
- [x] Run `alembic current`, `alembic heads` and `alembic check`.
- [x] Verify pgvector, public tables, constraints, indexes and catalogue seed records.
- [x] Run the complete backend integration suite against the disposable database.
- [x] Run API contract generation/check, frontend tests, typecheck, lint and production build.
- [x] Run security and deployment-script checks.
- [x] Bootstrap a disposable Admin, complete forced password change and verify role authorization.
- [x] Exercise a minimal topic lifecycle: textbook, Unit/Module, topic, upload metadata, coverage, mapping and retrieval.
- [x] Destroy only the named disposable database after recording results.

**Done when:** CI-equivalent validation passes from a completely empty database without relying on any earlier revision.

## Step 4 — Reset and verify the local database

**Goal:** Make local development use the same clean baseline intended for production.

- [x] Stop local API, worker and frontend processes that access PostgreSQL.
- [x] Create a local custom-format PostgreSQL backup and record its checksum.
- [x] Confirm the local document-storage directory is empty or separately backed up.
- [x] Drop and recreate only the local `akuru` database with the intended owner and encoding.
- [x] Enable pgvector if the baseline does not own extension creation.
- [x] Apply the new baseline migration.
- [x] Bootstrap a fresh local Admin account and complete the first-login password change.
- [x] Run the complete verification suite against the recreated local database.
- [x] Confirm the prior local backup can be listed with `pg_restore --list`.

**Rollback:** Drop the failed local database, recreate it, restore the pre-reset dump, and check out the pre-squash Git tag.

**Done when:** Local AKURU runs entirely from the single baseline and all tests pass.

**Completed:** The local database now runs from `0001_initial_akuru_schema`, the
catalogue is seeded, one fresh Admin exists, and all verification gates pass.
See [Step 4 local reset evidence](../backend/docs/database-baseline-step-04-local-reset.md).

## Step 5 — Prepare the reviewed production release

**Goal:** Make production execution a controlled, reversible maintenance event.

- [x] Commit the baseline and all compatibility removal in one reviewed release revision.
- [x] Push the revision and confirm GitHub CI passes.
- [x] Record the exact commit SHA and create a release tag.
- [x] Update `release-preflight.sh` so its empty-content audit matches the final baseline-reset policy.
- [x] Update `deploy-reviewed-release.sh` with an explicit database-recreation mode that cannot run without a typed confirmation and exact database-name validation.
- [x] Ensure the deployment command refuses database names other than the configured `akuru` application database.
- [x] Ensure encrypted database and document backups complete before database recreation.
- [x] Document the exact production Admin bootstrap command and acceptance checklist without storing credentials.
- [~] Schedule a maintenance window and prevent public writes before starting. The command now requires an approved window reference and stops all application writers; the owner must choose the actual window before Step 6.

**Done when:** The production reset can be executed from a reviewed SHA using guarded commands, with backups and rollback inputs already available.

**Release candidate:** `2e2950354b5e275aa102d58684a9023aa94a697e`,
tagged `database-baseline-v1-20260917`. GitHub Actions run `35197718649`
passed. The only remaining owner action is selecting the actual maintenance
window before Step 6.

## Step 6 — Recreate the production database

**Goal:** Install the baseline without affecting server infrastructure or persistent file storage.

- [ ] Put AKURU into maintenance mode and stop API, worker and frontend services.
- [ ] Run the production content audit again immediately before backup and record its output.
- [ ] Run the encrypted database and document backup and copy the backup evidence off-host.
- [ ] Verify the dump can be listed and the document archive can be read before proceeding.
- [ ] Record existing Alembic revision, database owner and pgvector availability.
- [ ] Terminate only active connections to the configured AKURU database.
- [ ] Drop and recreate only the AKURU application database using the existing least-privilege owner.
- [ ] Apply the single baseline migration from the exact reviewed release SHA.
- [ ] Confirm one Alembic head, current revision and no metadata drift.
- [ ] Bootstrap the production Admin account interactively.
- [ ] Restart API, worker and frontend services.

**Rollback decision:** If recreation, migration or Admin bootstrap fails, keep services stopped. Restore the encrypted pre-reset database, check out the pre-squash release, verify its migration revision, then restart.

**Done when:** Production runs the new baseline with a recreated Admin and no unexpected data or infrastructure changes.

## Step 7 — Production acceptance and evidence

**Goal:** Prove identity, security and the new hierarchy work before content onboarding.

- [ ] Complete the production Admin's forced password change.
- [ ] Verify Admin login, logout, session revocation, CSRF, role enforcement and rate limiting.
- [ ] Verify HTTPS, security headers, public health and loopback-only database, Redis, API and frontend bindings.
- [ ] Verify API, worker and frontend logs contain no startup, migration or queue errors.
- [ ] Verify encrypted backup and retention timers remain enabled.
- [ ] Create the Chemistry textbook using Unit terminology.
- [ ] Define Units 1–4 and Topics 1–29 without uploading files.
- [ ] Upload and review only Chemistry Topics 1 and 2 as the pilot.
- [ ] Verify topic quality reports, publication, exact citations, coverage, question eligibility and retrieval isolation.
- [ ] Record release evidence and the decision to proceed or roll back.

**Done when:** The fresh production baseline supports the complete Chemistry pilot and all operational/security checks pass.

## Step 8 — Close the reset window

**Goal:** Return AKURU to normal forward-only database evolution.

- [ ] Mark the baseline revision and production deployment date in architecture and operations documentation.
- [ ] Update developer setup so a new contributor creates the database from the new baseline.
- [ ] Retain the pre-squash Git tag and encrypted backup according to the approved retention period.
- [ ] Remove any temporary maintenance access or reset-only scripts that should not remain callable.
- [ ] Resume parent/student account creation and content uploads.
- [ ] Record that all future schema changes require additive or explicitly reviewed forward migrations.

**Done when:** The reset is closed, normal operations resume, and the baseline is the only supported starting point for new installations.
