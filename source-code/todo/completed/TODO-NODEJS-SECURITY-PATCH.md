# Patch Node.js security vulnerabilities across AKURU and OpenClaw

Created: 2026-10-30
Started: 2026-10-31
Completed: 2026-10-31
Status: completed for the authorized production/OpenClaw scope. Local installation was explicitly excluded and moved to a separate planned task.
Priority: high — security maintenance; schedule ahead of feature delivery.

## Objective

Patch the Node.js runtimes used by AKURU production, local development and the independent OpenClaw container. Verify application behaviour, preserve persistent data and authentication state, and prevent deployment of the known affected versions.

This is one coordinated security plan. OpenClaw implementation artifacts, container configuration and recovery instructions remain in the top-level `openclaw/` folder. Do not duplicate its installation plans.

## Verified baseline — 2026-10-30

| Component | Observed runtime | Minimum fix for this advisory |
| --- | --- | --- |
| Production AKURU web service | Node 22.23.2, `/usr/bin/node`, Ubuntu package `22.23.2-1nodesource1` | Node 22.23.4 |
| Local development | Node 22.23.2 via NVM | Node 22.23.4 |
| Production OpenClaw container | Node 24.19.0, image `ghcr.io/openclaw/openclaw:2026.9.6` | Node 24.22.1 |

The server package cache offers `22.23.4-1nodesource1`. Recheck availability and current security advice before execution; these are minimum fixes for this advisory, not a permanent claim that a version is secure.

Official sources:

- [October 2026 Node.js security advisory](https://nodejs.org/en/blog/vulnerability/october-2026-security-releases)
- [Node 22.23.4 release](https://nodejs.org/en/blog/release/v22.23.4/)
- [Node 24.22.1 release](https://nodejs.org/en/blog/release/v24.22.1/)

The advisory includes Brotli decoder memory corruption with potential remote code execution (CVE-2026-111497), DNS input validation, TLS hostname validation and HTTP connection reuse fixes. Confirm affected release lines individually: not every listed CVE affects both Node 22 and 24.

AKURU's Node web listener is bound to `127.0.0.1:5181` behind Nginx. This reduces direct exposure but does not remove risk from requests forwarded by Nginx or outbound requests. No direct affected Brotli/DNS calls were found in application code; dependency reachability has not been conclusively excluded. Python FastAPI is not directly affected by Node runtime vulnerabilities. No compromise assessment has been completed.

## Step 0 — Prepare and record recovery evidence

- [x] Move this plan to `ongoing` and record the start date.
- [x] Reconfirm actual running executable versions, host package source, architecture, current Git revision and service health; inspect the running web child process as well as the shell's `node`.
- [x] Record OpenClaw's image tag and immutable digest, internal Node version, Compose configuration, persistent volume locations and health baseline without exposing environment secrets.
- [x] Confirm recent recoverable AKURU backups and securely back up OpenClaw persistent state/configuration/authentication. Keep keys, tokens and backups outside Git with restrictive permissions.
- [x] Choose a short maintenance window and record expected brief web/gateway interruption. Update AKURU and OpenClaw separately so failures can be isolated.
- [x] Record recovery commands and previous package/image references before mutation. No database migration or reset is required.

## Step 1 — Patch AKURU production Node 22

- [x] Refresh package metadata and confirm the trusted NodeSource Node 22 package provides 22.23.4 or a newer reviewed security-patched Node 22 release.
- [x] Review the package operation before installation; upgrade Node without an unrelated full-system or major-version upgrade.
- [x] Restart `akuru-web` and verify the actual serving process uses the patched runtime. Replacing a binary alone does not patch a process already running.
- [x] Rebuild the frontend if compatibility verification requires it; preserve the reviewed application revision and unrelated local work. Do not run broad dependency upgrades as part of the runtime patch.
- [x] Run `deploy/ubuntu/release-acceptance.sh akuru.magicalinternational.com`; verify HTTPS, service health, route fallback, headers and loopback-only web binding.
- [x] Run actual Admin login/logout, catalog/deck reads and Q5(c)(ii) image checks; production routed-entry acceptance and Student-facing frontend regression checks passed. See the evidence limitations below: a real Student sign-in/complete textbook-and-flashcard session was not performed without Student credentials. No reviewed content or Student results were modified.
- [x] Check service logs for startup/runtime errors and record installed package, running process version, timestamps and test evidence without secrets.

## Step 2 — Patch the independent OpenClaw container

- [x] Find a compatible official OpenClaw image containing Node 24.22.1 or a newer patched supported runtime; inspect image provenance, architecture and OpenClaw upgrade/migration notes before selecting it.
- [x] Test the candidate image/runtime and configuration compatibility in isolation. Do not attach a second live gateway to the same Telegram credentials or permit duplicate message processing during testing.
- [x] Pin the approved image digest in the tracked OpenClaw deployment configuration. Updating host Node does not update a container's Node runtime.
- [x] No custom image was needed: official stable OpenClaw 2026.10.9 contains patched Node 24.22.1. No in-container package modification was used.
- [x] Recreate only the OpenClaw gateway with its existing protected volumes/configuration. Preserve authentication, network restrictions, resource limits and restart settings.
- [x] Verify the internal Node version, gateway health, persisted authentication and configured messaging/model connections using an authorized test conversation where applicable.
- [x] Check logs for migration/authentication errors; confirm no additional public ports or weakened container controls were introduced.
- [x] Save the image digest and recovery/reinstallation steps under `openclaw/docs` and its deployment instructions. Record results here rather than starting a duplicate security TODO.

## Step 3 — Local development explicitly deferred

- [x] Record the user's 2026-10-31 exclusion of local deployment; no NVM installation, default-alias change or local server deployment was performed.
- [x] Move local installation/verification actions to [the separate local Node patch plan](../planned/TODO-LOCAL-NODEJS-SECURITY-PATCH.md). The laptop remains on affected Node 22.23.2 and the updated frontend wrapper deliberately rejects it until patched.

## Step 4 — Make the fix reproducible

- [x] Update frontend runtime requirements, wrapper checks, Ubuntu prerequisite verification and installation documentation consistently with the security floor.
- [x] Apply a version-aware check: accept patched supported releases, reject affected older patches and end-of-life lines; do not assume every version numerically above Node 22.23.4 is safe (for example Node 24.19.0).
- [x] Keep CI on a supported patched runtime and record its resolved version. A floating `node-version: 22` normally selects a recent patch but should still be verified.
- [x] Add focused tests for the version-check boundary, including affected Node 22/24 versions and accepted patched versions.
- [x] Update OpenClaw's pinned deployment/recovery artifacts, developer setup guidance and production upgrade instructions.
- [x] Commit and push only this remediation's files; exclude unrelated frontend style/navigation edits and all credentials/runtime backups.

## Step 5 — Final acceptance and closure

- [x] Recheck host, actual web process and container runtime versions after restarts/recreation; record local development as explicitly excluded, still on 22.23.2.
- [x] Record acceptance evidence and remaining limitations. Runtime patching establishes neither absence of compromise nor a clean npm dependency audit.
- [x] Track existing npm dependency-security findings separately; do not imply this patch fixes them or run `npm audit fix --force` implicitly.
- [x] Confirm persistence, authentication, network exposure and core workflows remain functional. Monitor relevant logs after restart.
- [x] Update the delivery-plan index, record completion date and move this plan to `completed` only when all intended environments are patched and verified or any exception has been explicitly agreed and documented.

## Rollback and failure handling

- Preserve persistent data and the exact previous deployment/configuration references before the changes.
- If the host upgrade breaks service, inspect logs and try a compatible patched runtime first. Restoring the known vulnerable package is an emergency availability measure, not successful security remediation; record the exposure and promptly reattempt the patch.
- If OpenClaw fails, stop the candidate before restoring its previous image. Restore matching backed-up state only when required by the image's migration compatibility; avoid overwriting newer user data blindly.
- Do not reset AKURU databases, discard textbooks, delete Student records or revoke all credentials as routine patch steps. If evidence of compromise is discovered, stop treating it as an ordinary patch and prepare incident containment/recovery based on the evidence.

## Completion criteria

Within the user-authorized scope, production AKURU and OpenClaw run verified patched Node versions and pass acceptance checks; reproducible installation/version checks and recovery instructions are committed; and no credentials or private backups enter the repository. Local installation is explicitly deferred in its own planned task.

## Completion evidence — 2026-10-31

- Host package `22.23.4-1nodesource1`; actual web listener process confirmed Node **22.23.4**. Only Node was upgraded; no OS-wide upgrade/reboot or database reset was performed. Initial acceptance immediately after restart saw a transient startup 502; the retry and final release acceptance passed.
- AKURU rebuilt and released under the patched runtime at `d8f404114ffe9eb0a941029c08ff565660012e34`. Evidence: `/data/akuru/release-evidence/deployed-d8f404114ffe9eb0a941029c08ff565660012e34-20261031T051821Z.txt`. Later repository commits record closure/CI documentation rather than change the served UI.
- **103 frontend tests passed**, including three new runtime-policy cases; typecheck/lint/build and schema-drift checks passed. No backend feature logic changed. CI verifies its resolved Node runtime; wrapper and Ubuntu install/verify/release-preflight checks share the same release-line-aware policy.
- Actual authenticated production Admin browser checks passed login/logout, catalog/deck reads and Q5(c)(ii)'s two images on desktop/mobile. Student model-answer desktop/mobile rendering, enlargement and keyboard dismissal passed against the deployed frontend using synthetic browser API fixtures; these are not real Student data or a live Student textbook/flashcard session. Broader Student textbook/flipbook/flashcard behaviour is covered by the automated regression suite; a fresh real Student manual walkthrough remains an optional operational check.
- OpenClaw official ARM64 image **2026.10.9**, digest `sha256:bfa6ab1508b9314e71abb73eaabf472d7fa82c2a1199ff91949a834e9ff00f7f`; internal Node **24.22.1**. The initial one-shot candidate validation encountered an in-progress state migration; the corrected procedure booted the isolated copied state and waited for health before validating/switching. Live configuration validation and gateway health passed.
- Recovery backup: `/data/openclaw/backups/node-security-20261031T051438Z/state.tar.age`, SHA-256 sidecar, previous image and Compose references. Root-only plaintext trial state/container were removed. Existing AKURU backup archive hashes were verified and the normal deployment also took a fresh encrypted backup.
- Gateway remains network-isolated with no published ports, read-only root, dropped capabilities, no-new-privileges and unchanged 1.5 GiB/2 CPU/256 PID limits and state/cache mounts. Unauthenticated `/tools/invoke` returns **401**. Sanitized verification: `/data/akuru/release-evidence/node-security-20261031.json`.
- Health/model status reported **zero configured channels/providers/OAuth profiles**. No provider reauthentication was needed; no external model/Telegram conversation was attempted because none is configured and the gateway has no network. Deep audit: **0 critical, 1 warning, 1 informational**. The existing operator-scope `gateway.probe_failed` warning remains; permissions were not broadened to silence it.
- Existing package audit findings are separately tracked in [npm dependency remediation](../planned/TODO-NPM-DEPENDENCY-SECURITY.md): full install audit 29 findings; production-only audit 23 (1 low, 11 moderate, 10 high, 1 critical). Detailed report retained at `/data/akuru/release-evidence/npm-audit-20261031.json`. This runtime update does not claim those package findings are fixed or establish absence of compromise.
- Local Node installation unchanged as requested; unrelated local `portal.css` and `portal-shell.tsx` edits excluded from all commits/deployment. No temporary local server was started.
