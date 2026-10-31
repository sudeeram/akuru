# AKURU Ubuntu installation playbook

This playbook prepares a fresh **Ubuntu 24.04 LTS** OCI instance for the current AKURU architecture. It installs Node.js 22, Python, PostgreSQL, Redis, Nginx, TLS tooling, and the native PDF/OCR utilities required by the upcoming extraction pipeline. It also creates an unprivileged `akuru` service account and persistent directories outside the Git checkout.

The scripts do not contain database, OpenAI, OCI, or TLS credentials. Run them on the Ubuntu server, not on a developer computer.

GitHub Actions `.github/workflows/ci.yml` is a quality gate, not a server installer. It tests each Git revision on disposable GitHub-hosted Ubuntu runners. The CI workflow validates this playbook's shell syntax, but it never connects to or changes the OCI server.

## 1. OCI preparation

Create an Ubuntu 24.04 LTS instance with a persistent boot or block volume and a reserved public IP. In the OCI Network Security Group or security list, allow inbound TCP:

- `22` from your administration IP range
- `80` and `443` from the clients that will use AKURU

Do not expose ports `5432`, `6379`, `8000`, or `5181`. Point the intended DNS name at the reserved public IP before requesting a TLS certificate.

## 2. Install all prerequisites

After cloning the repository, run:

```bash
cd akuru
sudo ./deploy/ubuntu/install-prerequisites.sh
sudo ./deploy/ubuntu/verify-prerequisites.sh
```

The installer is repeatable and stops if the operating system is not Ubuntu 24.04. Override directory or account defaults only before the first run:

```bash
sudo AKURU_APP_USER=akuru \
  AKURU_APP_ROOT=/opt/akuru \
  AKURU_DATA_ROOT=/data/akuru \
  ./deploy/ubuntu/install-prerequisites.sh
```

Installed components:

| Component | Purpose |
| --- | --- |
| Node.js 22 and npm | Build and run the React/Vite frontend |
| Python 3, venv and build tools | Run FastAPI and document workers |
| PostgreSQL and pgvector | Authoritative data and approved semantic retrieval |
| Redis | Private job transport between FastAPI and the document worker |
| Nginx and Certbot | HTTPS entry point and reverse proxy |
| Poppler | PDF inspection and page rendering |
| Tesseract English/French | OCR for scanned learning material |
| Git, libpq and compiler tooling | Deployment and Python dependency installation |

## 3. Prepare PostgreSQL

Generate a strong password with a password manager, then open PostgreSQL locally:

```bash
sudo -u postgres psql
```

Run the following SQL after replacing the example password:

```sql
CREATE ROLE akuru_app LOGIN PASSWORD 'replace-with-a-generated-secret';
CREATE DATABASE akuru OWNER akuru_app;
REVOKE ALL ON DATABASE akuru FROM PUBLIC;
\q
```

PostgreSQL should listen only on loopback for this single-server deployment. Do not use the `postgres` administrator account in AKURU's `.env`.

## 4. Place and install the application

Copy or clone the repository into `/opt/akuru`. Keep the checkout owned by the deployment administrator and allow the `akuru` service account to read it. Install dependencies and build the portal:

```bash
cd /opt/akuru/source-code/frontend
sudo -u akuru npm ci
sudo -u akuru npm run build

cd /opt/akuru/source-code/backend
sudo -u akuru python3 -m venv .venv
sudo -u akuru .venv/bin/python -m pip install --upgrade pip
sudo -u akuru .venv/bin/python -m pip install -r requirements.txt
```

Create the production environment file outside the checkout. The project owner selected this root-protected dotenv approach instead of OCI Vault:

```bash
sudo install -d -o root -g akuru -m 0750 /etc/akuru
sudo install -o root -g akuru -m 0640 /opt/akuru/source-code/backend/.env.example /etc/akuru/akuru.env
sudoedit /etc/akuru/akuru.env
```

At minimum, set the real database password and public hostname, and verify these production values:

```dotenv
AKURU_ENVIRONMENT=production
AKURU_PUBLIC_HOST=akuru.example.com
AKURU_TUTOR_RELEASE_GATES_REQUIRED=true
AKURU_DATABASE_HOST=127.0.0.1
AKURU_DATABASE_PORT=5432
AKURU_DATABASE_NAME=akuru
AKURU_DATABASE_USER=akuru_app
AKURU_DATABASE_PASSWORD=replace-with-a-generated-secret
AKURU_CORS_ORIGINS='["https://akuru.example.com"]'
AKURU_ALLOWED_HOSTS='["akuru.example.com"]'
AKURU_COOKIE_SECURE=true
AKURU_OPERATIONS_TOKEN=replace-with-at-least-32-random-bytes
AKURU_STORAGE_BACKEND=local
AKURU_LOCAL_STORAGE_PATH=/data/akuru/documents
AKURU_MALWARE_SCAN_COMMAND=clamscan
AKURU_REDIS_URL=redis://127.0.0.1:6379/0
AKURU_EMBEDDING_PROVIDER=openai
AKURU_EMBEDDING_MODEL=text-embedding-3-small
AKURU_EMBEDDING_DIMENSIONS=256
```

Apply the schema and create the first administrator interactively:

```bash
cd /opt/akuru/source-code/backend
sudo -u akuru .venv/bin/python -m alembic upgrade head
sudo -u akuru .venv/bin/python -m app.seed_catalog
sudo -u akuru .venv/bin/python -m app.bootstrap_admin \
  --username admin --name "AKURU Administrator"
```

Generate an operations token without printing it into shell history, and place OpenAI/database credentials only in this protected file. Confirm `sudo stat -c '%U %G %a' /etc/akuru/akuru.env` reports `root akuru 640`.

## 5. Services and HTTPS

AKURU requires three application processes in production:

1. the FastAPI service bound to `127.0.0.1:8000`;
2. the document worker connected to PostgreSQL, private storage and Redis;
3. the compiled frontend bound to `127.0.0.1:5181`.

Request a certificate after DNS is correct, while the default Nginx site is active:

```bash
sudo certbot --nginx -d akuru.example.com
```

Install the hardened Nginx proxy and systemd services, then start them:

```bash
cd /opt/akuru
sudo bash deploy/ubuntu/install-services.sh akuru.example.com
sudo systemctl start akuru-api akuru-worker akuru-web
sudo systemctl start akuru-retention.timer akuru-backup.timer
sudo systemctl reload nginx

AKURU's Nginx configuration proxies application paths to the Vinext server, whose catch-all page supports direct navigation and refresh for TanStack Router URLs. `/api/`, `/health` and `/_next/` remain explicit locations so API and missing asset responses cannot be replaced by application HTML. After a release, verify a nested Flashcard URL directly, an unknown API URL, and a missing `/_next/` asset.
```

The services bind the application only to loopback. In OCI, permit inbound 22 only from administrator addresses and 80/443 from intended clients; never permit 5432, 6379, 8000 or 5181.

## 6. Encrypted backups

Create an age identity on a separate protected operator machine. Put only its public `age1...` recipient on the server:

```bash
sudo install -o root -g akuru -m 0640 /dev/null /etc/akuru/backup-age-recipient
sudoedit /etc/akuru/backup-age-recipient
sudo systemctl start akuru-backup.service
```

For the monthly restoration drill, copy the matching `.dump.age` and `akuru-documents-*.tar.age` files to an isolated operator machine. Decrypt both, extract the document archive into a temporary private directory, verify representative checksums, then run:

```bash
cd /opt/akuru/source-code/backend
sudo -u akuru .venv/bin/python -m app.database_maintenance restore-drill --backup /secure/path/akuru.dump
```

Never copy the age private identity to the AKURU server. Keep at least one encrypted backup in a separate protected location.

## 7. Verification and operations

Before enabling public access:

```bash
cd /opt/akuru
sudo ./deploy/ubuntu/verify-prerequisites.sh

cd /opt/akuru/source-code
sudo -u akuru npm run contract:check
sudo -u akuru npm run typecheck
sudo -u akuru npm run lint
sudo -u akuru npm run build
```

Verify database migrations and back up the database before every release:

```bash
cd /opt/akuru/source-code/backend
sudo -u akuru .venv/bin/python -m alembic current
sudo -u akuru .venv/bin/python -m alembic check
sudo -u akuru .venv/bin/python -m app.retention
sudo systemctl --failed
sudo systemctl status akuru-api akuru-worker akuru-web akuru-backup.timer akuru-retention.timer
curl --fail https://akuru.example.com/health
```

Keep `/data/akuru`, encrypted PostgreSQL backups, and `/etc/akuru/akuru.env` outside release replacement. See the [database backup guide](../../source-code/docs/database-backup.md), [environment reference](../../source-code/docs/environment.md), [production security guide](../../source-code/backend/docs/step-20-production-security-operations.md), and [Step 2 document-storage guide](../../source-code/backend/docs/step-02-document-storage.md).

## Reviewed release procedure

For the textbook-topic release, run the deployment tools only on the OCI host after the target Git SHA has been reviewed and pushed:

```bash
cd /opt/akuru
sudo ./deploy/ubuntu/release-preflight.sh <reviewed-sha>
sudo ./deploy/ubuntu/deploy-reviewed-release.sh --execute <reviewed-sha>
sudo ./deploy/ubuntu/release-acceptance.sh akuru.magicalinternational.com
```

The deployment command takes encrypted database and document backups before it
installs locked dependencies or applies Alembic. It writes non-secret evidence
below `/data/akuru/release-evidence`. The production reset window is closed:
the deployment tool supports forward migrations only and contains no database
drop, recreation or Admin-bootstrap mode.

## Upgrade outline

For each release, take a database and document backup, fetch the reviewed Git revision, install locked frontend/backend dependencies, run the quality gate, build the frontend, apply Alembic migrations, and restart the application services. If a migration fails, stop deployment and restore the tested backup; do not point an older application release at a newer incompatible schema.

## Node.js security maintenance

The supported runtime floors are Node **22.23.4**, **24.22.1** and **26.12.1** within their respective release lines (October 2026 security advisory). Production AKURU uses Node 22. The shared `source-code/scripts/node-version-policy.mjs` gate is used by the frontend wrapper, prerequisite installation/verification, CI and production release preflight. Odd, end-of-life and unreviewed major versions are rejected. Update this policy when reviewing future advisories; these floors are not a substitute for ongoing patching.

For a Node 22 security update: confirm backups and current running versions; run `sudo apt-get update`, inspect `apt-cache policy nodejs` and simulate the selected package operation, then install only the reviewed Node 22 package. Restart `akuru-web`, allow startup to complete, verify the actual serving process's executable version, and run `sudo deploy/ubuntu/release-acceptance.sh akuru.magicalinternational.com` from the deployed checkout. Test authenticated learning/review workflows. A shell's updated `node --version` alone does not prove an existing process was restarted. No database migration is needed for a runtime patch.

OpenClaw's Node runtime belongs to its Docker image and must be patched separately; follow `openclaw/deploy/upgrade-gateway.sh` and the OpenClaw recovery guide. Local NVM updates require the user's approval. Until local Node is patched, the frontend wrapper intentionally refuses affected runtimes; it never installs software automatically.
