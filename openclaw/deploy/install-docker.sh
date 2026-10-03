#!/usr/bin/env bash
# Run as root on Ubuntu 24.04 ARM64 after prepare-docker-apt.sh and an AKURU backup.
set -Eeuo pipefail
[[ "$(id -u)" == 0 ]] || { echo 'Run as root.' >&2; exit 1; }
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
. "${script_dir}/docker-versions.env"
for value in "$DOCKER_CE_VERSION" "$CONTAINERD_VERSION" "$BUILDX_VERSION" "$COMPOSE_VERSION"; do
  [[ -n "$value" ]] || { echo 'All Docker version pins are required.' >&2; exit 1; }
done
apt-get install -y --no-install-recommends \
  "docker-ce=${DOCKER_CE_VERSION}" \
  "docker-ce-cli=${DOCKER_CE_VERSION}" \
  "containerd.io=${CONTAINERD_VERSION}" \
  "docker-buildx-plugin=${BUILDX_VERSION}" \
  "docker-compose-plugin=${COMPOSE_VERSION}"
apt-mark hold docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
docker version --format 'Engine {{.Server.Version}}'
docker compose version
