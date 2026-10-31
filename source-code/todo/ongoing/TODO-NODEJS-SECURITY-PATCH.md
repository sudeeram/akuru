# Patch Node.js security vulnerabilities across AKURU and OpenClaw

Created: 2026-10-30
Started: 2026-10-31
Status: in progress — production and reproducibility work authorized; local runtime installation explicitly excluded by the user on 2026-10-31.
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

- [ ] Move this plan to `ongoing` and record the start date.
- [ ] Reconfirm actual running executable versions, host package source, architecture, current Git revision and service health; inspect the running web child process as well as the shell's `node`.
- [ ] Record OpenClaw's image tag and immutable digest, internal Node version, Compose configuration, persistent volume locations and health baseline without exposing environment secrets.
- [ ] Confirm recent recoverable AKURU backups and securely back up OpenClaw persistent state/configuration/authentication. Keep keys, tokens and backups outside Git with restrictive permissions.
- [ ] Choose a short maintenance window and record expected brief web/gateway interruption. Update AKURU and OpenClaw separately so failures can be isolated.
- [ ] Record recovery commands and previous package/image references before mutation. No database migration or reset is required.

## Step 1 — Patch AKURU production Node 22

- [ ] Refresh package metadata and confirm the trusted NodeSource Node 22 package provides 22.23.4 or a newer reviewed security-patched Node 22 release.
- [ ] Review the package operation before installation; upgrade Node without an unrelated full-system or major-version upgrade.
- [ ] Restart `akuru-web` and verify the actual serving process uses the patched runtime. Replacing a binary alone does not patch a process already running.
- [ ] Rebuild the frontend if compatibility verification requires it; preserve the reviewed application revision and unrelated local work. Do not run broad dependency upgrades as part of the runtime patch.
- [ ] Run `deploy/ubuntu/release-acceptance.sh akuru.magicalinternational.com`; verify HTTPS, service health, route fallback, headers and loopback-only web binding.
- [ ] Smoke-test login/logout and role navigation; Student textbook/visual-reference reading, flashcards and Admin official-paper review including Q5(c)(ii)'s model-answer images. Use existing authorized accounts and avoid altering reviewed content or Student results.
- [ ] Check service logs for startup/runtime errors and record installed package, running process version, timestamps and test evidence without secrets.

## Step 2 — Patch the independent OpenClaw container

- [ ] Find a compatible official OpenClaw image containing Node 24.22.1 or a newer patched supported runtime; inspect image provenance, architecture and OpenClaw upgrade/migration notes before selecting it.
- [ ] Test the candidate image/runtime and configuration compatibility in isolation. Do not attach a second live gateway to the same Telegram credentials or permit duplicate message processing during testing.
- [ ] Pin the approved image digest in the tracked OpenClaw deployment configuration. Updating host Node does not update a container's Node runtime.
- [ ] If no suitable official image is available, record that blocker and prepare a reproducible reviewed image-build option under `openclaw/`; do not make an untracked in-container package change and call it fixed.
- [ ] Recreate only the OpenClaw gateway with its existing protected volumes/configuration. Preserve authentication, network restrictions, resource limits and restart settings.
- [ ] Verify the internal Node version, gateway health, persisted authentication and configured messaging/model connections using an authorized test conversation where applicable.
- [ ] Check logs for migration/authentication errors; confirm no additional public ports or weakened container controls were introduced.
- [ ] Save the image digest and recovery/reinstallation steps under `openclaw/docs` and its deployment instructions. Record results here rather than starting a duplicate security TODO.

## Step 3 — Patch local development with approval

- [ ] Obtain the user's approval before installing local software, following their existing preference. This planning request does not authorize installation.
- [ ] Install the reviewed patched Node 22 version using existing NVM, select it and update the default alias. Retain the prior version only as a clearly identified recovery option.
- [ ] Confirm `node`, `npm`, the AKURU wrapper scripts and the current shell resolve the patched runtime; account for existing terminals/processes using older binaries.
- [ ] Run frontend tests, typecheck, lint and build. Stop any temporary verification servers afterward.
- [ ] Confirm Python/backend helper commands still launch correctly; run relevant additional tests only if new failures or compatibility concerns justify them.

## Step 4 — Make the fix reproducible

- [ ] Update frontend runtime requirements, wrapper checks, Ubuntu prerequisite verification and installation documentation consistently with the security floor.
- [ ] Apply a version-aware check: accept patched supported releases, reject affected older patches and end-of-life lines; do not assume every version numerically above Node 22.23.4 is safe (for example Node 24.19.0).
- [ ] Keep CI on a supported patched runtime and record its resolved version. A floating `node-version: 22` normally selects a recent patch but should still be verified.
- [ ] Add focused tests for the version-check boundary, including affected Node 22/24 versions and accepted patched versions.
- [ ] Update OpenClaw's pinned deployment/recovery artifacts, developer setup guidance and production upgrade instructions.
- [ ] Commit and push only this remediation's files; exclude unrelated frontend style/navigation edits and all credentials/runtime backups.

## Step 5 — Final acceptance and closure

- [ ] Recheck host, actual web process, local development and container runtime versions against the advisory after all restarts/recreations.
- [ ] Record acceptance evidence and remaining limitations. Runtime patching establishes neither absence of compromise nor a clean npm dependency audit.
- [ ] Track existing npm dependency-security findings separately; do not imply this patch fixes them or run `npm audit fix --force` implicitly.
- [ ] Confirm persistence, authentication, network exposure and core workflows remain functional. Monitor relevant logs after restart.
- [ ] Update the delivery-plan index, record completion date and move this plan to `completed` only when all intended environments are patched and verified or any exception has been explicitly agreed and documented.

## Rollback and failure handling

- Preserve persistent data and the exact previous deployment/configuration references before the changes.
- If the host upgrade breaks service, inspect logs and try a compatible patched runtime first. Restoring the known vulnerable package is an emergency availability measure, not successful security remediation; record the exposure and promptly reattempt the patch.
- If OpenClaw fails, stop the candidate before restoring its previous image. Restore matching backed-up state only when required by the image's migration compatibility; avoid overwriting newer user data blindly.
- Do not reset AKURU databases, discard textbooks, delete Student records or revoke all credentials as routine patch steps. If evidence of compromise is discovered, stop treating it as an ordinary patch and prepare incident containment/recovery based on the evidence.

## Completion criteria

All three environments run verified patched Node versions; AKURU and OpenClaw pass their acceptance checks; reproducible installation/version checks and recovery instructions are committed; and no credentials or private backups enter the repository.
