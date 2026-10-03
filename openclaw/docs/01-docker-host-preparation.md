# Docker host preparation and recovery

Target: AKURU production Ubuntu 24.04 ARM64. This step installs Docker Engine and Compose only. It does not start OpenClaw or publish a container port.

1. Record AKURU Git revision, `systemctl` state, `ss -lnt`, `iptables -S INPUT`, `iptables -S FORWARD`, free space and memory. Verify OCI ingress rules in the OCI console; VM inspection cannot prove cloud security-list settings.
2. Start `akuru-backup.service` and verify `Result=success` and a fresh encrypted manifest. Preserve an off-host copy under the existing AKURU backup policy before any host package change.
3. Run `sudo bash openclaw/deploy/prepare-docker-apt.sh`. Review `apt-cache madison` output and commit exact package versions to `docker-versions.env`.
4. Run `sudo bash openclaw/deploy/install-docker.sh`. Use `sudo docker`; do not add the AKURU service user or operator to the Docker group. Docker socket membership confers root-level privileges.
5. Verify `sudo docker run --rm --pull=always hello-world`, `sudo docker compose version`, `sudo systemctl is-enabled docker`, `sudo systemctl is-active docker`, `sudo iptables -S DOCKER-USER`, `ss -lnt`, AKURU services and `deploy/ubuntu/release-acceptance.sh akuru.magicalinternational.com`. Run a no-port Compose smoke test. Review Docker-created firewall chains; never rely on UFW alone to block a published container port.
6. Reserve `/data/openclaw` for mutable state and `/etc/openclaw` for protected secrets/configuration, outside `/opt/akuru`. Use root-owned `0700` directories until the OpenClaw runtime identity and backup policy are set in plan 02. Define storage limits and backup exclusions before storing Student content.
7. Reboot validation should be done during a maintenance window, followed immediately by AKURU and Docker service/port checks. Do not use a production reboot merely to validate a planning change.

If AKURU health regresses: stop Docker with `sudo systemctl stop docker docker.socket containerd`; inspect firewall and service state before changing any rules. Restore the recorded firewall rules and package state only after comparing with the preflight snapshot. If necessary, remove only the five Docker packages introduced here and disable the Docker apt source; do not delete `/var/lib/docker` or AKURU data during rollback. Re-run AKURU acceptance. Restore AKURU from the verified encrypted backup only if its data is affected.

The package source and installation method follow [Docker's Ubuntu installation guide](https://docs.docker.com/engine/install/ubuntu/). Docker [documents the firewall implications](https://docs.docker.com/engine/network/packet-filtering-firewalls/) and [root-level privilege of Docker group membership](https://docs.docker.com/engine/install/linux-postinstall/).
