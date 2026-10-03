# OpenClaw for AKURU

This is the independent OpenClaw project area. Its first milestone is a reproducible, isolated installation on the OCI host. AKURU integration and Telegram Quick Mock come later. See the [ordered plans](todo/README.md).

## Repository layout

- [`todo/`](todo/README.md): planned, ongoing and completed delivery records.
- [`deploy/`](deploy/README.md): reviewed Docker/Compose files, host setup scripts, configuration **templates**, pinned versions and rollout/rollback commands when implemented.
- [`plugin/`](plugin/README.md): versioned AKURU Quick Mock plugin code and tests when implemented.
- [`docs/`](docs/README.md): installation, configuration, backup, restore, upgrade and incident procedures, plus sanitized verification evidence.

Commit every script, template, version/digest pin, plugin source, test and runbook needed to recreate the installation. Record the exact deployed Git commit and image digest in the deployment record. A fresh host should be recoverable using the repository plus separately stored secrets and any required state backup.

**Never commit** live `.env` files, API keys, Telegram bot tokens, Gateway tokens, AKURU integration credentials, Student conversations, mock answers, container volumes or backups. Keep live secrets and mutable state outside this checkout on the server. Git alone cannot restore those values; the operations guide must document their secure provision, rotation and state restore.

As of 2026-10-03, a pinned, isolated OpenClaw Gateway is installed on the OCI host. It has no network, published port, Telegram channel, AKURU integration or model credential. See the [installation record](docs/02-openclaw-installation.md). This installation is infrastructure only; no Student-facing OpenClaw feature is released.
