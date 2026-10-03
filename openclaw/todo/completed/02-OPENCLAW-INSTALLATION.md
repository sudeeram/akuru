# 02 — Install and harden OpenClaw

**Status:** Completed 2026-10-03
**Depends on:** Docker host preparation (plan 01) passing its gate. AKURU integration APIs are not required for this isolated installation. Do not connect Telegram, the AKURU plugin or Student data during initial installation.

Use an official prebuilt ARM64 OpenClaw container image pinned to a reviewed release digest. This avoids changing the VM's Node v22.23.2; current OpenClaw requires a newer Node runtime inside its image. Keep installation artifacts, state and secrets outside AKURU's checkout.

## Image, service and state

- [x] Confirm official stable `2026.9.6`, ARM64 manifest, release notes and exact ARM64 digest; no floating tag.
- [x] Create a dedicated Compose project with restart policy, built-in health check, bounded logs and persistent state/cache mounts.
- [x] Run the Gateway with `network_mode: none`, no published port and no Control UI or AKURU Nginx route.
- [x] Keep AKURU secrets, database, document storage, SSH keys, Docker socket and application checkout unmounted.
- [x] Provision a separate random Gateway token in root-owned mode-0600 server config; document rotation. No provider or AKURU credential configured.
- [x] Use one dedicated inactive exam agent with only `session_status` allowed; disable shell, filesystem, browser, web, gateway, automation, cross-session and messaging tools.
- [x] Set direct-message session isolation to `per-channel-peer`; AKURU will remain the future authorization boundary.

## Initial validation

- [x] Start the Gateway without Telegram, AKURU integration or Student data; verify health, restart and resource use. No model/provider credential supplied.
- [x] Run `openclaw security audit --deep`: zero critical, one documented limited-operator-scope warning. Pair an operator device and rerun before any channel is enabled.
- [x] Confirm there is no host listener or published port, and an unauthenticated in-container tool request returns HTTP 401.
- [x] Test stop/start and a disposable previous-image rollback rehearsal; AKURU acceptance passed afterward.
- [x] Write update, token rotation, recovery and rollback instructions in `docs/02-openclaw-installation.md`.
- [x] Commit the pinned image, Compose/config, safe templates, installer, rollback test and recovery runbook under `openclaw/`. The installer was tested from transferred repository files; live secrets and state remain outside Git.

**Done when:** A pinned, isolated OpenClaw Gateway runs reliably with no public control surface and no access to AKURU secrets or data paths. Telegram and AKURU plugin activation belong to the next plan.

**Evidence:** Official ARM64 image `sha256:62040ed3fe6f566adb39e60c5428cce078989a39cc713d63e873c4dccf166892`; OpenClaw CLI `2026.9.6`; healthy container with zero restarts, no network and no published ports. See [installation and verification record](../../docs/02-openclaw-installation.md). The deep-audit operator-read warning is an explicit gate before enabling Telegram, not an exposed service.
