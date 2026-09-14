#!/usr/bin/env bash
set -Eeuo pipefail

failed=0

check_command() {
  local command="$1"
  local label="$2"
  if command -v "${command}" >/dev/null 2>&1; then
    printf 'PASS  %-24s %s\n' "${label}" "$(command -v "${command}")"
  else
    printf 'FAIL  %-24s missing\n' "${label}" >&2
    failed=1
  fi
}

check_service() {
  local service="$1"
  if systemctl is-active --quiet "${service}"; then
    printf 'PASS  %-24s active\n' "${service}"
  else
    printf 'FAIL  %-24s inactive\n' "${service}" >&2
    failed=1
  fi
}

check_command git Git
check_command node "Node.js"
check_command npm npm
check_command python3 Python
check_command psql PostgreSQL-client
check_command pg_dump PostgreSQL-backup
check_command redis-cli Redis-client
check_command nginx Nginx
check_command ufw Firewall
check_command age Backup-encryption
check_command clamscan Malware-scanner
check_command pdftoppm Poppler
check_command tesseract Tesseract-OCR

node_major="$(node --version 2>/dev/null | sed -E 's/^v([0-9]+).*/\1/' || true)"
if [[ -z "${node_major}" || "${node_major}" -lt 22 ]]; then
  echo "FAIL  Node.js version          requires 22.13 or newer" >&2
  failed=1
else
  printf 'PASS  %-24s %s\n' "Node.js version" "$(node --version)"
fi

check_service postgresql
check_service redis-server
check_service nginx

if ufw status | grep -q '^Status: active'; then
  echo "PASS  host firewall            active"
else
  echo "FAIL  host firewall            inactive" >&2; failed=1
fi

if sudo -u postgres psql -Atqc "SELECT 1 FROM pg_available_extensions WHERE name='vector'" | grep -qx 1; then
  echo "PASS  pgvector extension       available"
else
  echo "FAIL  pgvector extension       unavailable" >&2
  failed=1
fi

if ! redis-cli -h 127.0.0.1 ping 2>/dev/null | grep -qx PONG; then
  echo "FAIL  Redis loopback           no PONG response" >&2
  failed=1
else
  echo "PASS  Redis loopback           PONG"
fi

if ss -lnt | awk '{print $4}' | grep -Eq '(^|:)6379$' && \
   ss -lnt | awk '{print $4}' | grep -Eq '(^0\.0\.0\.0:6379$|^\[::\]:6379$)'; then
  echo "FAIL  Redis exposure           port 6379 listens on all interfaces" >&2
  failed=1
else
  echo "PASS  Redis exposure           no public wildcard listener"
fi

for port in 5432 6379 8000 5181; do
  if ss -lnt | awk '{print $4}' | grep -Eq "(^0\\.0\\.0\\.0:${port}$|^\\[::\\]:${port}$)"; then
    echo "FAIL  private port ${port}      public wildcard listener" >&2; failed=1
  else
    printf 'PASS  private port %-9s no public wildcard listener\n' "${port}"
  fi
done

if [[ -f /etc/akuru/akuru.env ]]; then
  env_mode="$(stat -c '%a' /etc/akuru/akuru.env)"
  env_owner="$(stat -c '%U:%G' /etc/akuru/akuru.env)"
  if [[ "${env_mode}" == "640" && "${env_owner}" == "root:akuru" ]]; then
    echo "PASS  production secrets       root:akuru 640"
  else
    echo "FAIL  production secrets       expected root:akuru 640" >&2; failed=1
  fi
fi

exit "${failed}"
