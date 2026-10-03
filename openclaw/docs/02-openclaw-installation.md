# Isolated OpenClaw Gateway installation

Step 02 uses official OpenClaw `2026.9.6` on Linux ARM64, pinned to manifest digest `sha256:62040ed3fe6f566adb39e60c5428cce078989a39cc713d63e873c4dccf166892` (multi-arch index digest `sha256:0a5ff5e682e62afa19149df126aa50063bf65ef885b5c94713ce32dc0eb12e15`). The image runs as uid 1000. Do not use `latest`, an unofficial mirror or an unreviewed replacement digest. The installed container has no network, published port, provider credential, Telegram token or AKURU mount.

## Install or recreate

1. Confirm the [Docker host preparation](../todo/ongoing/01-DOCKER-HOST-PREPARATION.md) checks and AKURU backup policy. Review the pinned image's release notes and ARM64 manifest.
2. From a reviewed repository checkout on the server, run `sudo bash openclaw/deploy/install-gateway.sh`. The script installs `/opt/openclaw/compose.yaml`, root-only `/etc/openclaw/gateway.env`, the repository config at `/data/openclaw/state/openclaw.json`, and a separate writable cache. It generates a random token only if no server token exists. It never prints the token.
3. Run `sudo docker compose -f /opt/openclaw/compose.yaml ps`, `sudo docker compose -f /opt/openclaw/compose.yaml exec -T gateway node dist/index.js config validate --json`, `sudo docker compose -f /opt/openclaw/compose.yaml exec -T gateway node dist/index.js health --json`, and `sudo docker compose -f /opt/openclaw/compose.yaml exec -T gateway node dist/index.js security audit --deep --json`.
4. Confirm `docker inspect akuru-openclaw-gateway-1` shows `NetworkMode=none`, `Ports={}`, a read-only root filesystem, and only `/data/openclaw/state` and `/data/openclaw/cache` mounted. Confirm `ss -lnt` has no `18789` listener and AKURU production acceptance still passes.

## Credentials and storage

`/etc/openclaw/gateway.env` is mode `0600` and root-owned. Rotate its token by writing a newly generated value to a root-only temporary file in `/etc/openclaw`, replacing `gateway.env` atomically, then recreating the container with `sudo docker compose -f /opt/openclaw/compose.yaml up -d --force-recreate gateway`. Re-run health and audit. Do not print tokens, include them in commands, or commit them. No model/provider token belongs here during Step 02.

`/data/openclaw/state` is durable runtime state; back it up encrypted, offline and separately from AKURU before future user sessions are enabled. Do not back up `/data/openclaw/cache` or `/tmp` logs. Docker JSON logs rotate at 10 MiB × 3 files; the container has a 1.5 GiB memory limit and 64 MiB tmpfs. Monitor `/data/openclaw` and Docker image usage; set a retention and disk quota before storing Student transcripts. Parent directory mode `0700` prevents the host uid 1000 account from traversing state despite the container's uid mapping. Root is the only Docker operator.

## Update and rollback

Take an encrypted copy of `/data/openclaw/state` and a protected copy of `/etc/openclaw/gateway.env`. Stage the replacement image by exact ARM64 digest, verify its manifest and release notes, test the new config with `config validate`, then change only the image reference in `compose.yaml`. Re-run `install-gateway.sh` and acceptance checks. For rollback, restore the previous digest and matching configuration/state snapshot, then `docker compose -f /opt/openclaw/compose.yaml up -d --force-recreate gateway`. Do not prune the prior image until rollback is verified. A failed state migration can make old code incompatible with new state, so restore the matching state snapshot rather than pointing an old image at migrated state.

For immediate isolation or suspected exposure: `sudo docker compose -f /opt/openclaw/compose.yaml stop gateway`; then investigate or rotate the Gateway token. Stopping this Compose project does not affect AKURU services.

`sudo bash openclaw/deploy/verify-image-rollback.sh` rehearses a `2026.9.5` → `2026.9.6` → `2026.9.5` switch using a temporary separate Compose project and a matching state snapshot. It uses no host port or AKURU mount, cleans up its temporary state, and does not modify the live Gateway. The rehearsal passed on 2026-10-03. Re-run it only after reviewing its pinned images and resource impact; it does not replace a production state restore drill.

The initial deep audit reported zero critical findings and one `gateway.probe_failed` warning: the internal CLI connected with the bootstrap token but had no paired `operator.read` scope. With no network and no channel, this limits CLI diagnostics; it does not expose the Gateway. Pair a dedicated operator device and rerun the audit before any future channel or AKURU integration. Do not broaden the Gateway's token or enable unauthenticated access merely to silence this warning.

Production validation on 2026-10-03: configuration valid; Gateway healthy after restart; unauthenticated `/tools/invoke` returned HTTP 401 inside the container; Docker reported `NetworkMode=none`, `Ports={}`, read-only root filesystem, and only state/cache mounts. No host listener on 18789. AKURU release acceptance passed after installation and again after stop/start and rollback rehearsal. At the observed idle sample, OpenClaw used approximately 687 MiB of its 1.5 GiB limit. No provider or Student data has been configured.

References: [official Docker installation](https://docs.openclaw.ai/install/docker), [security audit](https://docs.openclaw.ai/gateway/security/running-the-audit), [operator scopes](https://docs.openclaw.ai/gateway/operator-scopes), [release](https://github.com/openclaw/openclaw/releases/tag/v2026.9.6).
