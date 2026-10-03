# Deployment artifacts

The first two plans are implemented here: pinned Docker package versions, a pinned OpenClaw ARM64 image digest, reviewed Compose definition, safe configuration and environment templates, installation scripts and a disposable rollback rehearsal. See the [Docker](../docs/01-docker-host-preparation.md) and [Gateway](../docs/02-openclaw-installation.md) runbooks. Never commit live secrets or runtime state. Keep AKURU's deployment files separate.
