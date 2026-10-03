#!/usr/bin/env bash
# Run as root on Ubuntu 24.04 ARM64. Prepares Docker's official apt repository only.
set -Eeuo pipefail
[[ "$(id -u)" == 0 ]] || { echo 'Run as root.' >&2; exit 1; }
. /etc/os-release
[[ "${ID}" == ubuntu && "${VERSION_ID}" == 24.04 && "$(dpkg --print-architecture)" == arm64 ]] || { echo 'Expected Ubuntu 24.04 arm64.' >&2; exit 1; }
if dpkg-query -W -f='${Status}' docker.io containerd runc 2>/dev/null | grep -q 'install ok installed'; then
  echo 'A conflicting container package is installed; review it before proceeding.' >&2
  exit 1
fi
apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
cat >/etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: noble
Components: stable
Architectures: arm64
Signed-By: /etc/apt/keyrings/docker.asc
EOF
apt-get update
for pkg in docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin; do
  echo "$pkg:"
  apt-cache madison "$pkg" | sed -n '1,3p'
done
