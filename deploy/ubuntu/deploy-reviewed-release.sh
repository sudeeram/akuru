#!/usr/bin/env bash
# Applies a preflighted release already checked out at /opt/akuru.
set -Eeuo pipefail

if [[ $# -ne 2 || "$1" != "--execute" ]]; then
  echo "Usage: sudo $0 --execute <reviewed-git-sha>" >&2
  echo "This command changes production services only after release-preflight.sh passes." >&2
  exit 64
fi
release_sha="$2"
app_root="${AKURU_APP_ROOT:-/opt/akuru}"
source_root="${AKURU_SOURCE_ROOT:-${app_root}/source-code}"
env_file="${AKURU_ENV_FILE:-/etc/akuru/akuru.env}"
evidence_root="${AKURU_RELEASE_EVIDENCE_ROOT:-/data/akuru/release-evidence}"
[[ $EUID -eq 0 ]] || { echo "Run as root." >&2; exit 1; }

"${app_root}/deploy/ubuntu/release-preflight.sh" "$release_sha"
# shellcheck disable=SC1090
source "$env_file"

# The preflight has proved the checkout and empty-content migration scope. Take
# both encrypted backups immediately before changing dependencies or schema.
systemctl start akuru-backup.service
systemctl is-active --quiet akuru-backup.service || { echo "Encrypted backup failed; deployment stopped." >&2; exit 1; }

sudo -u akuru npm --prefix "${source_root}/frontend" ci
sudo -u akuru npm --prefix "${source_root}/frontend" run build
sudo -u akuru "${source_root}/backend/.venv/bin/python" -m pip install --requirement "${source_root}/backend/requirements-production.lock"
sudo -u akuru "${source_root}/backend/.venv/bin/alembic" upgrade head
sudo -u akuru "${source_root}/backend/.venv/bin/alembic" current
sudo -u akuru "${source_root}/backend/.venv/bin/alembic" check

systemctl restart akuru-api akuru-worker akuru-web
systemctl is-active --quiet akuru-api akuru-worker akuru-web
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:8000/health >/dev/null
curl --fail --silent --show-error --max-time 15 "https://${AKURU_PUBLIC_HOST:?Set AKURU_PUBLIC_HOST in /etc/akuru/akuru.env}/health" >/dev/null

install -d -o root -g akuru -m 0750 "$evidence_root"
actual="$(git -C "$app_root" rev-parse HEAD)"
report="$evidence_root/deployed-${actual}-$(date -u +%Y%m%dT%H%M%SZ).txt"
{
  echo "AKURU production deployment evidence"
  echo "release_sha=${actual}"
  echo "deployed_at=$(date -u --iso-8601=seconds)"
  echo "backup=encrypted database and document backup service completed"
  echo "migration=$(sudo -u akuru "${source_root}/backend/.venv/bin/alembic" current | tail -1)"
  echo "services=akuru-api, akuru-worker, akuru-web active"
  echo "health=loopback and HTTPS passed"
  echo "next=complete Admin, authorization, HTTPS-header and Chemistry pilot acceptance checks"
} > "$report"
chown root:akuru "$report"; chmod 0640 "$report"
echo "Deployment completed. Evidence: $report"
