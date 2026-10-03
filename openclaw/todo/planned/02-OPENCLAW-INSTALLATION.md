# 02 — Install and harden OpenClaw

**Status:** Planned
**Depends on:** Docker host preparation (plan 01) passing its gate. AKURU integration APIs are not required for this isolated installation. Do not connect Telegram, the AKURU plugin or Student data during initial installation.

Use an official prebuilt ARM64 OpenClaw container image pinned to a reviewed release digest. This avoids changing the VM's Node v22.23.2; current OpenClaw requires a newer Node runtime inside its image. Keep installation artifacts, state and secrets outside AKURU's checkout.

## Image, service and state

- [ ] Confirm the current official stable image, ARM64 manifest, release notes and image digest; avoid `latest` for the production deployment.
- [ ] Create a dedicated Compose project with restart policy, health check, bounded logs and persistent OpenClaw state. Use only the volumes required by the Gateway.
- [ ] Bind the Gateway to loopback or an internal-only network. Do not publish its control UI or port 18789 to OCI public ingress or AKURU's Nginx routes.
- [ ] Keep AKURU `.env`, PostgreSQL socket/credentials, document storage, SSH keys, Docker socket and application checkout unmounted and unreadable.
- [ ] Provision a separate Gateway token in protected server configuration; document rotation and revocation. Do not put it in Compose YAML, Git or command-line history. Defer any OpenAI/provider credential until a controlled smoke test requires it; do not use an AKURU provider key.
- [ ] Use one dedicated exam agent and an explicit minimal tool allowlist. Disable shell, filesystem, browser, general web, gateway administration, cron, cross-agent/session and unrelated messaging tools.
- [ ] Set direct-message session isolation to `per-channel-peer`; treat this as session separation, while AKURU's API remains the authorization boundary.

## Initial validation

- [ ] Start the Gateway without Telegram, AKURU integration or Student data and verify health, restart behaviour and resource use. Keep model-backed interaction disabled until its separate provider credential and access policy are reviewed.
- [ ] Run `openclaw security audit --deep` and document/remediate findings before adding a channel.
- [ ] Confirm an unauthenticated network client cannot reach the Gateway or invoke tools.
- [ ] Test container stop/start and image rollback without affecting AKURU web/API services.
- [ ] Write an update playbook: stage and test a new digest, back up configuration, change one image reference, verify, and restore the previous digest if needed.
- [ ] Commit the exact image digest, Compose definition, safe configuration templates, health checks and recovery runbook under `openclaw/`. Verify a clean checkout can recreate the isolated Gateway once secrets are provisioned separately.

**Done when:** A pinned, isolated OpenClaw Gateway runs reliably with no public control surface and no access to AKURU secrets or data paths. Telegram and AKURU plugin activation belong to the next plan.
