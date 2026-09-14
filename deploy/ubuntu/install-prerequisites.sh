#!/usr/bin/env bash
set -Eeuo pipefail

readonly REQUIRED_UBUNTU_RELEASE="24.04"
readonly NODE_MAJOR="22"
readonly APP_USER="${AKURU_APP_USER:-akuru}"
readonly APP_ROOT="${AKURU_APP_ROOT:-/opt/akuru}"
readonly DATA_ROOT="${AKURU_DATA_ROOT:-/data/akuru}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this installer as root, for example: sudo ./install-prerequisites.sh" >&2
  exit 1
fi

if [[ ! -r /etc/os-release ]]; then
  echo "Cannot identify this operating system." >&2
  exit 1
fi

# shellcheck disable=SC1091
source /etc/os-release
if [[ "${ID:-}" != "ubuntu" || "${VERSION_ID:-}" != "${REQUIRED_UBUNTU_RELEASE}" ]]; then
  echo "This playbook supports Ubuntu ${REQUIRED_UBUNTU_RELEASE} LTS; found ${PRETTY_NAME:-unknown}." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  gnupg \
  git \
  build-essential \
  python3 \
  python3-dev \
  python3-pip \
  python3-venv \
  libpq-dev \
  postgresql \
  postgresql-contrib \
  postgresql-16-pgvector \
  redis-server \
  nginx \
  ufw \
  certbot \
  python3-certbot-nginx \
  poppler-utils \
  tesseract-ocr \
  tesseract-ocr-eng \
  tesseract-ocr-fra \
  libmagic1 \
  age \
  clamav \
  clamav-freshclam

install -d -m 0755 /etc/apt/keyrings
node_key="/etc/apt/keyrings/nodesource.gpg"
node_list="/etc/apt/sources.list.d/nodesource.list"
if [[ ! -s "${node_key}" ]]; then
  curl --fail --silent --show-error --location \
    https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
    | gpg --dearmor --yes --output "${node_key}"
fi
chmod 0644 "${node_key}"
printf 'deb [signed-by=%s] https://deb.nodesource.com/node_%s.x nodistro main\n' \
  "${node_key}" "${NODE_MAJOR}" > "${node_list}"
apt-get update
apt-get install -y --no-install-recommends nodejs

if ! id "${APP_USER}" >/dev/null 2>&1; then
  useradd --system --create-home --home-dir "/var/lib/${APP_USER}" \
    --shell /usr/sbin/nologin "${APP_USER}"
fi

install -d -o "${APP_USER}" -g "${APP_USER}" -m 0750 "${APP_ROOT}"
install -d -o "${APP_USER}" -g "${APP_USER}" -m 0750 "${DATA_ROOT}"
install -d -o "${APP_USER}" -g "${APP_USER}" -m 0750 "${DATA_ROOT}/documents"
install -d -o "${APP_USER}" -g "${APP_USER}" -m 0750 "${DATA_ROOT}/backups"

systemctl enable --now postgresql
systemctl enable --now redis-server
systemctl enable --now nginx

ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# Redis must remain a local infrastructure service on a single-host deployment.
redis_bind="$(redis-cli CONFIG GET bind | tail -n 1)"
if [[ " ${redis_bind} " != *" 127.0.0.1 "* && "${redis_bind}" != "127.0.0.1" ]]; then
  echo "Redis is not bound to 127.0.0.1. Correct /etc/redis/redis.conf before deployment." >&2
  exit 1
fi

node_major="$(node --version | sed -E 's/^v([0-9]+).*/\1/')"
if (( node_major < NODE_MAJOR )); then
  echo "Node.js ${NODE_MAJOR}+ is required; found $(node --version)." >&2
  exit 1
fi

echo "AKURU prerequisites installed successfully."
echo "Application user: ${APP_USER}"
echo "Application root: ${APP_ROOT}"
echo "Persistent data root: ${DATA_ROOT}"
echo "Next: follow deploy/ubuntu/README.md to configure PostgreSQL and deploy AKURU."
