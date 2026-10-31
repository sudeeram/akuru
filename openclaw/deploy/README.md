# Deployment artifacts

The first two plans are implemented here: pinned Docker package versions, a pinned OpenClaw ARM64 image digest, reviewed Compose definition, safe configuration and environment templates, installation scripts and a disposable rollback rehearsal. See the [Docker](../docs/01-docker-host-preparation.md) and [Gateway](../docs/02-openclaw-installation.md) runbooks. Never commit live secrets or runtime state. Keep AKURU's deployment files separate.

For the current pinned image and Node security maintenance, see [the gateway guide](../docs/02-openclaw-installation.md#october-2026-node-security-patch). Upgrade an existing isolated deployment with `sudo bash openclaw/deploy/upgrade-gateway.sh` from the reviewed repository. This preserves live configuration and takes an encrypted state/authentication backup. `install-gateway.sh` is for initial setup and preserves an existing configuration file.
