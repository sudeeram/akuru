# Step 10 — Safe production release procedure

This step prepares the deployment tooling for the textbook-topic release. It does not deploy a local checkout or run migrations automatically from a developer machine.

## What the release gate protects

`deploy/ubuntu/release-preflight.sh <sha>` runs on the OCI host. It rejects a dirty or different checkout, confirms the protected environment file, checks production settings, runs the tracked-file security check, requires the educational-content audit to be empty, verifies exactly one Alembic head, and records non-secret evidence under `/data/akuru/release-evidence`.

`deploy/ubuntu/deploy-reviewed-release.sh --execute <sha>` runs only after that preflight passes. It takes encrypted database and document backups, installs the committed frontend lockfile and backend production lockfile, builds the frontend, applies Alembic, restarts the three loopback-only services, checks loopback and HTTPS health, and records deployment evidence.

`deploy/ubuntu/release-acceptance.sh akuru.magicalinternational.com` checks HTTPS, security headers, active services, loopback bindings and recent service errors. The Admin login, role authorization, and Chemistry pilot are deliberate manual acceptance tasks because they require the protected production credentials and actual textbook PDFs.

## Rollback decision points

Stop before migration if preflight, the empty-content audit, encrypted backup, dependency installation, or build fails. After a successful migration, never start an older application revision against the changed schema. Restore the matching encrypted database backup and the previous compatible release only after recording the decision and testing the restore in isolation.

## Remaining production execution

The user must run the scripts on the OCI server when ready and supply the protected environment file, age recipient and production Admin details. After deployment, create Chemistry with Unit terminology, define Units 1–4 and Topics 1–29, then upload and review Topics 1 and 2 as the pilot before expanding the collection.
