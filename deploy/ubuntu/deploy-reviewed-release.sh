#!/usr/bin/env bash
# Applies a preflighted release already checked out at /opt/akuru.
set -Eeuo pipefail

mode=""
release_sha=""
confirmation=""
maintenance_window=""
if [[ $# -eq 2 && "$1" == "--execute" ]]; then
  mode="upgrade"; release_sha="$2"
elif [[ $# -eq 6 && "$1" == "--recreate-database" && "$3" == "--confirm" && "$5" == "--maintenance-window" ]]; then
  mode="recreate"; release_sha="$2"; confirmation="$4"; maintenance_window="$6"
else
  echo "Usage: sudo $0 --execute <reviewed-git-sha>" >&2
  echo "   or: sudo $0 --recreate-database <reviewed-git-sha> --confirm 'RESET AKURU DATABASE' --maintenance-window <approved-window>" >&2
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

if [[ "$mode" == "recreate" ]]; then
  [[ "$confirmation" == "RESET AKURU DATABASE" ]] || { echo "Typed confirmation did not match." >&2; exit 1; }
  [[ "$maintenance_window" =~ ^[A-Za-z0-9][A-Za-z0-9._:+-]{5,79}$ ]] || { echo "Supply the approved maintenance-window reference." >&2; exit 1; }
  # Stopping all writers is the maintenance mode for this one-time reset. A
  # failure after this point deliberately leaves services stopped for rollback.
  systemctl stop akuru-api akuru-worker akuru-web
  sudo -u akuru "${source_root}/backend/.venv/bin/python" -m app.content_migration_audit --require-baseline-reset-eligible
fi

# The preflight has proved the checkout and empty-content migration scope. Take
# both encrypted backups immediately before changing dependencies or schema.
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

if [[ "$mode" == "recreate" ]]; then
  database_owner="$(sudo -u postgres psql --dbname postgres --tuples-only --no-align --command "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname='akuru'")"
  [[ "$database_owner" == "${AKURU_DATABASE_USER}" ]] || { echo "Configured role does not own the akuru database." >&2; exit 1; }
  sudo -u postgres psql --dbname postgres --set ON_ERROR_STOP=1 --command "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='akuru' AND pid<>pg_backend_pid()"
  sudo -u postgres dropdb --if-exists akuru
  sudo -u postgres createdb --owner "${AKURU_DATABASE_USER}" --encoding UTF8 akuru
  sudo -u postgres psql --dbname akuru --set ON_ERROR_STOP=1 --command 'CREATE EXTENSION IF NOT EXISTS vector'
fi

sudo -u akuru "${source_root}/backend/.venv/bin/alembic" upgrade head
sudo -u akuru "${source_root}/backend/.venv/bin/python" -m app.seed_catalog
sudo -u akuru "${source_root}/backend/.venv/bin/alembic" current
sudo -u akuru "${source_root}/backend/.venv/bin/alembic" check

if [[ "$mode" == "recreate" ]]; then
  echo "Create the fresh production Admin now. No credential is stored by this script."
  sudo -u akuru "${source_root}/backend/.venv/bin/python" -m app.bootstrap_admin --username admin --name "AKURU Administrator"
fi

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
  echo "deployment_mode=${mode}"
  [[ "$mode" == "recreate" ]] && echo "maintenance_window=${maintenance_window}"
  echo "migration=$(sudo -u akuru "${source_root}/backend/.venv/bin/alembic" current | tail -1)"
  echo "services=akuru-api, akuru-worker, akuru-web active"
  echo "health=loopback and HTTPS passed"
  echo "next=complete Admin, authorization, HTTPS-header and Chemistry pilot acceptance checks"
} > "$report"
chown root:akuru "$report"; chmod 0640 "$report"
echo "Deployment completed. Evidence: $report"
