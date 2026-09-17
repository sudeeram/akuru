# AKURU OCI production deployment plan

Target: `akuru.magicalinternational.com` (`150.136.251.166`)

Prepared from a read-only audit on 15 September 2026. No server changes were made during the audit.

## Current server state

- Ubuntu 24.04.4 LTS, ARM64, Oracle kernel, hostname `vm02-large`.
- 2 vCPUs, 11 GiB RAM, no swap, approximately 191 GiB free on the 193 GiB root filesystem.
- DNS resolves `akuru.magicalinternational.com` to `150.136.251.166`.
- Only SSH is listening. Public HTTP and HTTPS are not reachable yet.
- PostgreSQL, Redis, Nginx, Node.js, UFW, Poppler and Tesseract are not installed or active.
- `/opt/akuru`, `/data/akuru`, and `/etc/akuru` do not exist.
- Nine package updates are pending and the server reports that a reboot is required.

## Deployment principles

- Deploy a reviewed, committed Git revision. Do not deploy the developer working tree or any `.env` file from Git.
- Keep code under `/opt/akuru`, secrets under `/etc/akuru`, and durable documents/backups under `/data/akuru`.
- Expose only SSH, HTTP and HTTPS. PostgreSQL, Redis, FastAPI and the frontend process remain on loopback.
- Use the unprivileged `akuru` system account for application processes.
- Take a database/document backup before every later upgrade and retain an encrypted copy away from the VM.
- Keep Tutor features disabled until their real subject/modality staging evaluations and ordered release gates pass.

## Phase 1 — Freeze the release and secure OCI access

1. Complete local verification, commit the current Steps 8–12 work, push it, and record the exact commit SHA or release tag.
2. Confirm the OCI Network Security Group or security list permits:
   - TCP 22 only from the administrator's trusted public IP range;
   - TCP 80 and 443 from intended clients;
   - no inbound 5432, 6379, 8000, 5180 or 5181.
3. Apply Ubuntu updates, reboot, reconnect, and verify the new boot is healthy.
4. Add a 2–4 GiB swap file to provide build, OCR and ClamAV headroom, while keeping normal work in RAM.
5. Improve `deploy/server/connect-vm2` so it resolves its key relative to the script and forwards optional SSH arguments. Keep the private key mode at `0600` and outside Git.

Exit gate: the reviewed release SHA is known, SSH is restricted, updates are complete, and only intended OCI ingress rules exist.

## Phase 2 — Install and verify prerequisites

1. Place the reviewed repository revision temporarily on the VM so its audited playbook can run.
2. Run:

   ```bash
   cd /opt/akuru
   sudo ./deploy/ubuntu/install-prerequisites.sh
   sudo ./deploy/ubuntu/verify-prerequisites.sh
   ```

3. Confirm Node.js 22, Python 3.12, PostgreSQL with pgvector, Redis, Nginx, Certbot, ClamAV, Poppler, and English/French Tesseract.
4. Confirm UFW allows OpenSSH and Nginx Full, Redis and PostgreSQL bind only to loopback, and `/opt/akuru` plus `/data/akuru/{documents,backups}` have the intended ownership and modes.

Exit gate: prerequisite verification passes and no private service is externally reachable.

## Phase 3 — Install the reviewed application revision

Recommended source strategy: clone the repository using a read-only GitHub deploy key, check out the recorded tag/SHA, and reject a dirty checkout. An operator-driven `rsync` of a release archive is an alternative when no server-side GitHub credential is desired.

1. Put the release at `/opt/akuru` and make it readable by the `akuru` service account.
2. Install locked frontend packages and build the production bundle:

   ```bash
   cd /opt/akuru/source-code/frontend
   sudo -u akuru npm ci
   sudo -u akuru npm run build
   ```

3. Create the backend virtual environment and install locked Python dependencies:

   ```bash
   cd /opt/akuru/source-code/backend
   sudo -u akuru python3 -m venv .venv
   sudo -u akuru .venv/bin/python -m pip install --upgrade pip
   sudo -u akuru .venv/bin/python -m pip install -r requirements.txt
   ```

4. Run contract, type, lint, build and backend test checks against an isolated deployment-test database. Production data must not be used by the test suite.

Exit gate: the exact release builds on ARM64 and all release checks pass.

## Phase 4 — Configure PostgreSQL and protected runtime settings

1. Create a generated database password, the least-privilege `akuru_app` role, the `akuru` database, and the `vector` extension. PostgreSQL must listen only on loopback.
2. Create `/etc/akuru/akuru.env` owned by `root:akuru` with mode `0640`. Configure at least:

   ```dotenv
   AKURU_ENVIRONMENT=production
   AKURU_PUBLIC_HOST=akuru.magicalinternational.com
   AKURU_DATABASE_HOST=127.0.0.1
   AKURU_DATABASE_PORT=5432
   AKURU_DATABASE_NAME=akuru
   AKURU_DATABASE_USER=akuru_app
   AKURU_DATABASE_PASSWORD=<generated database password>
   AKURU_CORS_ORIGINS='["https://akuru.magicalinternational.com"]'
   AKURU_ALLOWED_HOSTS='["akuru.magicalinternational.com"]'
   AKURU_COOKIE_SECURE=true
   AKURU_OPERATIONS_TOKEN=<at least 32 random bytes>
   AKURU_STORAGE_BACKEND=local
   AKURU_LOCAL_STORAGE_PATH=/data/akuru/documents
   AKURU_REDIS_URL=redis://127.0.0.1:6379/0
   AKURU_MALWARE_SCAN_COMMAND=clamscan
   AKURU_TUTOR_RELEASE_GATES_REQUIRED=true
   ```

3. Add OpenAI credential aliases and models only in this protected file. Start with Tutor text, voice and tools feature switches disabled.
4. Apply Alembic migrations as `akuru`, confirm the database is at the expected head, and run `alembic check`.
5. Bootstrap the first production Admin interactively and require its temporary password to be changed on first login.

Exit gate: permissions are correct, no secret is present in Git/process arguments/logs, migrations pass, and the Admin account exists.

## Phase 5 — Configure HTTP, TLS and services

1. Start the packaged default Nginx HTTP site and verify port 80 is reachable through OCI.
2. Obtain a Let's Encrypt certificate for `akuru.magicalinternational.com` using Certbot and the agreed notification email.
3. Install the AKURU Nginx configuration and systemd units:

   ```bash
   cd /opt/akuru
   sudo bash deploy/ubuntu/install-services.sh akuru.magicalinternational.com
   sudo systemctl start akuru-api akuru-worker akuru-web
   sudo systemctl start akuru-retention.timer akuru-backup.timer
   sudo systemctl reload nginx
   ```

4. Confirm FastAPI listens on `127.0.0.1:8000`, the frontend on `127.0.0.1:5181`, and Redis/PostgreSQL remain private.
5. Confirm certificate renewal with `certbot renew --dry-run` and verify HTTPS redirect, security headers, upload limits and microphone permissions.

Exit gate: `https://akuru.magicalinternational.com/health` succeeds externally and no private port is reachable.

## Phase 6 — Configure durable encrypted backups

1. Generate an age identity on a separate protected operator computer. Store only its public recipient in `/etc/akuru/backup-age-recipient`.
2. Run the initial encrypted PostgreSQL and document backup.
3. Copy a backup off the VM and perform the documented isolated restore drill.
4. Confirm backup and retention timers, disk-space monitoring, and failure notifications.

Exit gate: both database and document restoration have been demonstrated from an off-host encrypted backup.

## Phase 7 — Production acceptance and controlled feature release

1. Run smoke tests for Admin login/password change, parent and child creation, enrolment, textbook upload/extraction/review, curriculum coverage, past-paper processing, practice, assessment and family isolation.
2. Verify document malware scanning, Redis worker processing, private storage access, rate limiting, audit records, retention preview, accessibility and mobile/tablet behavior.
3. Run the production-like Tutor evaluation process for each enabled subject and modality. Progress each passing feature through Admin testing, parent pilot, then eligible students.
4. Before Tutor student release, run:

   ```bash
   cd /opt/akuru/source-code/backend
   sudo -u akuru .venv/bin/python -m app.tutor_release_check
   ```

5. Enable environment-level Tutor switches only after database gates pass. Demonstrate rollback by disabling one database feature gate and each outer text/voice/tools switch.
6. Observe logs, resource use, OpenAI cost/quota behavior, backup completion and application errors during the pilot before wider use.

Exit gate: core AKURU is operational, real Tutor evaluation gates pass where enabled, rollback is demonstrated, and the parent pilot is accepted.

## Upgrade and rollback procedure

For each later release: record the target SHA, take and verify encrypted backups, install the release into a new versioned directory, reuse `/etc/akuru` and `/data/akuru`, install dependencies, run checks, migrate, switch `/opt/akuru/current`, restart services, and run smoke tests. Keep the prior application directory for code rollback. Never point old code at a schema it does not support; restore the matching database backup when a migration is not backward compatible.

## Inputs required before execution

- The exact Git commit/tag to deploy and whether to use a GitHub deploy key or an operator-uploaded release archive.
- A Let's Encrypt notification email.
- Confirmation of the OCI ingress source range for SSH and that ports 80/443 are allowed.
- The desired initial production Admin username and display name.
- OpenAI credential aliases/models to configure; secret values should be entered directly into the protected server environment file.
- An age public recipient and off-host backup destination, or an explicit decision to launch the core service before enabling scheduled backups.
