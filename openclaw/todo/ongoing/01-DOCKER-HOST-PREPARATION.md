# 01 — Docker host preparation on OCI Ubuntu

**Status:** Ongoing since 2026-10-03
**Scope:** Container runtime only. This plan does not install or start OpenClaw.

The current AKURU VM is ARM64 Ubuntu 24 LTS with about 11 GiB RAM and 173 GiB free disk. Docker is not installed. The existing Node v22.23.2, AKURU services, PostgreSQL, Redis, Nginx and ports 80/443 must continue unchanged.

## Preflight and installation

- [ ] Record VM architecture, kernel, free memory/disk, current AKURU Git revision, systemd health, firewall and OCI security-list rules. Host-side evidence recorded; confirm OCI rules in console.
- [x] Run the normal AKURU encrypted backup and capture the pre-install host/service/firewall state. Fresh successful manifest: `akuru-20261003T095612Z.manifest`. Off-host copy/snapshot remains to verify separately.
- [x] Select Docker's official apt repository for Ubuntu 24 ARM64, pin all five package versions in `deploy/docker-versions.env`, and hold them pending reviewed upgrades.
- [x] Install Docker Engine and Compose without replacing AKURU's Node runtime or changing its existing service definitions.
- [x] Keep Docker administration limited to root via `sudo`; Docker group has no members, and the AKURU service user has no socket access.
- [ ] Review Docker's iptables/`DOCKER-USER` effects alongside OCI ingress and the VM's existing rules. Host-side rules and listening ports checked; confirm OCI ingress in console.
- [ ] Reserve separate OpenClaw state/secret locations outside AKURU Git. Root-owned `0700` `/data/openclaw` and `/etc/openclaw` exist; finalize backup exclusions and disk limits in plan 02 before storing Student content.

## Verification and rollback

- [ ] Run an ARM64 test container and Compose health check; verify Docker starts after reboot. Both smoke tests passed; reboot deferred to a maintenance window.
- [x] Re-run AKURU HTTPS, route, service and loopback-binding acceptance tests; inspect listening ports and effective firewall rules. Production acceptance passed; no container ports published.
- [x] Document how to stop Docker containers and revert the host package/network change if AKURU health regresses in `docs/01-docker-host-preparation.md`.
- [x] Record installed package versions and operational commands in the deployment guide.
- [ ] Commit reviewed host setup/verification scripts, package version pins and rollback instructions under `openclaw/deploy/` and `openclaw/docs/`; keep host-specific secrets and backup data outside Git.

**Done when:** Docker and Compose work on the VM, no new public port is exposed, and AKURU production acceptance still passes. Do not proceed to OpenClaw installation if host networking or AKURU service health changes unexpectedly.

**2026-10-03 evidence:** Ubuntu 24.04.5 ARM64; kernel `6.17.0-1020-oracle`; 11 GiB RAM; 173 GiB disk free before install; AKURU Git revision `746460e9`. Docker Engine `29.8.2` and Compose `5.6.0` installed. `hello-world` and a no-port Compose test passed. Docker/containerd enabled and active. Docker added `DOCKER-USER` and set `FORWARD` policy to DROP; the existing input rules for 22/80/443 and AKURU loopback bindings remained intact. AKURU release acceptance passed. No reboot performed; the host also reports a pending kernel upgrade, which must be reviewed separately from this Docker step.
