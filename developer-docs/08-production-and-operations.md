# Production and operations

## Current deployment model

AKURU runs on Ubuntu 24.04 LTS in OCI. Nginx terminates TLS for `akuru.magicalinternational.com`. Systemd manages:

- `akuru-api`: FastAPI on `127.0.0.1:8000`;
- `akuru-worker`: document processing worker;
- `akuru-web`: built portal on `127.0.0.1:5181`;
- backup and retention timers.

PostgreSQL, Redis and local private storage remain on the server. Persistent data is outside the Git checkout under `/data/akuru`; production configuration is outside it at `/etc/akuru/akuru.env`.

## Release process

The authoritative scripts are in repository-root `deploy/ubuntu`:

1. Push and review an exact Git SHA.
2. Put the production checkout on that SHA.
3. Run `release-preflight.sh <sha>`.
4. Run `deploy-reviewed-release.sh --execute <sha>`.
5. Run `release-acceptance.sh akuru.magicalinternational.com`.

Preflight verifies the exact clean revision, protected environment, production configuration, secret/frontend boundaries and one migration head. Deployment creates fresh encrypted database and document backups before dependency installation or migration, builds the portal, applies Alembic, checks drift, restarts services and checks loopback plus HTTPS health. Non-secret evidence is written under `/data/akuru/release-evidence`.

Do not manually copy a working tree over production or run migrations before the backup gate.

## Backups and recovery

The backup service encrypts PostgreSQL and document-storage backups with an age public recipient. The private age identity remains off-server. A manifest proves the expected database and absence of plaintext backup artifacts.

Restoration is practiced on an isolated environment using `app.database_maintenance restore-drill`. An application rollback is not a database rollback: after a schema migration, do not run an older incompatible application against the newer schema. Use the reviewed recovery plan and backup if a migration must be reversed.

## Health and monitoring

- `/health` is public and constant.
- `/ready` is authenticated and verifies database access.
- The Admin Operations screen reports failed jobs, provider failures, token usage, latency and audit events.
- `systemctl --failed` must be empty after release.
- API, worker, web, backup timer and retention timer must be active.

Review disk capacity for both PostgreSQL and `/data/akuru/documents`. Uploaded originals and derived page/visual assets can grow faster than relational data.

## Production configuration changes

Edit `/etc/akuru/akuru.env` through privileged operator procedures. Validate ownership `root:akuru` and mode `0640`, then restart only affected services. Model, prompt, feature-flag or OpenAI account changes may also require evaluation/release evidence; a service restart alone does not satisfy the domain gate.

## CI versus deployment

`.github/workflows/ci.yml` runs quality gates on GitHub-hosted runners. It does not install or update the OCI server. The deployment playbook job validates scripts and rejects committed secrets; frontend and backend jobs test the application against disposable dependencies.

See `../deploy/ubuntu/README.md` and `../source-code/backend/docs/step-20-production-security-operations.md` for command-level operator procedures.
