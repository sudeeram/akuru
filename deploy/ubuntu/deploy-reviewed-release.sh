#!/usr/bin/env bash
# Applies a preflighted release already checked out at /opt/akuru.
set -Eeuo pipefail

if [[ $# -eq 2 && "$1" == "--execute" ]]; then
  release_sha="$2"
else
  echo "Usage: sudo $0 --execute <reviewed-git-sha>" >&2
  exit 64
fi
app_root="${AKURU_APP_ROOT:-/opt/akuru}"
source_root="${AKURU_SOURCE_ROOT:-${app_root}/source-code}"
env_file="${AKURU_ENV_FILE:-/etc/akuru/akuru.env}"
evidence_root="${AKURU_RELEASE_EVIDENCE_ROOT:-/data/akuru/release-evidence}"
[[ $EUID -eq 0 ]] || { echo "Run as root." >&2; exit 1; }

"${app_root}/deploy/ubuntu/release-preflight.sh" "$release_sha"
# shellcheck disable=SC1090
source "$env_file"
cd "${source_root}/backend"
[[ "${AKURU_DATABASE_NAME:-}" == "akuru" ]] || { echo "Refusing: database name must be exactly akuru." >&2; exit 1; }
[[ "${AKURU_DATABASE_HOST:-}" == "127.0.0.1" || "${AKURU_DATABASE_HOST:-}" == "localhost" ]] || { echo "Refusing: database must be local." >&2; exit 1; }
[[ "${AKURU_DATABASE_USER:-}" =~ ^[a-z_][a-z0-9_]*$ && "${AKURU_DATABASE_USER}" != "postgres" ]] || { echo "Refusing: invalid least-privilege database owner." >&2; exit 1; }

# The preflight has proved the checkout and runtime configuration. Take both
# encrypted backups immediately before changing dependencies or schema.
backup_marker="$(mktemp)"
trap 'rm -f "$backup_marker"' EXIT
systemctl start akuru-backup.service
[[ "$(systemctl show akuru-backup.service --property=Result --value)" == "success" ]] || { echo "Encrypted backup failed; deployment stopped." >&2; exit 1; }
backup_root="${AKURU_BACKUP_ROOT:-/data/akuru/backups}"
backup_manifest="$(find "$backup_root" -maxdepth 1 -type f -name 'akuru-*.manifest' -newer "$backup_marker" -print -quit)"
[[ -n "$backup_manifest" ]] || { echo "Fresh backup evidence was not created; deployment stopped." >&2; exit 1; }
grep -qx 'database_name=akuru' "$backup_manifest"
grep -qx 'plaintext_database_list=passed' "$backup_manifest"
grep -qx 'plaintext_document_list=passed' "$backup_manifest"

sudo -u akuru npm --prefix "${source_root}/frontend" ci
sudo -u akuru npm --prefix "${source_root}/frontend" run build
sudo -u akuru "${source_root}/backend/.venv/bin/python" -m pip install --requirement "${source_root}/backend/requirements-production.lock"

sudo -u akuru "${source_root}/backend/.venv/bin/alembic" upgrade head
sudo -u akuru "${source_root}/backend/.venv/bin/python" -m app.seed_catalog
sudo -u akuru "${source_root}/backend/.venv/bin/alembic" current
sudo -u akuru "${source_root}/backend/.venv/bin/alembic" check

systemctl restart akuru-api akuru-worker akuru-web
systemctl is-active --quiet akuru-api akuru-worker akuru-web
ready=false
for _ in {1..30}; do
  if curl --fail --silent --show-error --max-time 3 --header "Host: ${AKURU_PUBLIC_HOST}" http://127.0.0.1:8000/health >/dev/null 2>&1; then
    ready=true; break
  fi
  sleep 1
done
[[ "$ready" == "true" ]] || { echo "API did not become ready within 30 seconds." >&2; exit 1; }
curl --fail --silent --show-error --max-time 15 "https://${AKURU_PUBLIC_HOST:?Set AKURU_PUBLIC_HOST in /etc/akuru/akuru.env}/health" >/dev/null

install -d -o root -g akuru -m 0750 "$evidence_root"
actual="$(git -C "$app_root" rev-parse HEAD)"
report="$evidence_root/deployed-${actual}-$(date -u +%Y%m%dT%H%M%SZ).txt"
{
  echo "AKURU production deployment evidence"
  echo "release_sha=${actual}"
  echo "deployed_at=$(date -u --iso-8601=seconds)"
  echo "backup=encrypted database and document backup service completed"
  echo "backup_manifest=${backup_manifest}"
  echo "deployment_mode=forward_migration"
  echo "migration=$(sudo -u akuru "${source_root}/backend/.venv/bin/alembic" current | tail -1)"
  echo "services=akuru-api, akuru-worker, akuru-web active"
  echo "health=loopback and HTTPS passed"
  echo "next=run release-acceptance.sh and complete release-specific functional checks"
} > "$report"
chown root:akuru "$report"; chmod 0640 "$report"
echo "Deployment completed. Evidence: $report"
