#!/usr/bin/env bash
# Read-only gate for an AKURU production release. Run on the Ubuntu host.
set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <reviewed-git-sha>" >&2
  exit 64
fi
release_sha="$1"
app_root="${AKURU_APP_ROOT:-/opt/akuru}"
source_root="${AKURU_SOURCE_ROOT:-${app_root}/source-code}"
env_file="${AKURU_ENV_FILE:-/etc/akuru/akuru.env}"
report_root="${AKURU_RELEASE_EVIDENCE_ROOT:-/data/akuru/release-evidence}"

fail() { echo "FAIL  $*" >&2; exit 1; }
pass() { echo "PASS  $*"; }
[[ $EUID -eq 0 ]] || fail "run as root so environment-file permissions can be checked"
[[ "$release_sha" =~ ^[0-9a-f]{7,64}$ ]] || fail "release SHA must be hexadecimal"
[[ -d "$app_root/.git" ]] || fail "${app_root} is not a Git checkout"
[[ -d "$source_root/backend" && -d "$source_root/frontend" ]] || fail "source-code folders are missing"

actual="$(git -C "$app_root" rev-parse HEAD)"
expected="$(git -C "$app_root" rev-parse "$release_sha^{commit}")" || fail "release SHA is unavailable in this checkout"
[[ "$actual" == "$expected" ]] || fail "checkout is ${actual}; expected reviewed release ${expected}"
[[ -z "$(git -C "$app_root" status --porcelain)" ]] || fail "release checkout is dirty"
pass "exact reviewed Git revision ${actual}"

[[ -f "$env_file" ]] || fail "missing protected runtime environment file"
[[ "$(stat -c '%U:%G:%a' "$env_file")" == "root:akuru:640" ]] || fail "${env_file} must be root:akuru mode 640"
pass "protected runtime environment file"

# shellcheck disable=SC1090
source "$env_file"
[[ "${AKURU_ENVIRONMENT:-}" == "production" ]] || fail "AKURU_ENVIRONMENT must be production"
[[ "${AKURU_DATABASE_NAME:-}" == "akuru" ]] || fail "AKURU_DATABASE_NAME must be exactly akuru for this release"
[[ "${AKURU_DATABASE_HOST:-}" == "127.0.0.1" || "${AKURU_DATABASE_HOST:-}" == "localhost" ]] || fail "database must be local"
[[ "${AKURU_DATABASE_USER:-}" =~ ^[a-z_][a-z0-9_]*$ ]] || fail "invalid application database role"
[[ "${AKURU_DATABASE_USER:-}" != "postgres" ]] || fail "application must not use the postgres administrator role"
[[ "${AKURU_COOKIE_SECURE:-}" == "true" ]] || fail "secure cookies must be enabled"
[[ "${AKURU_LOCAL_STORAGE_PATH:-}" == /data/akuru/* ]] || fail "document storage must be under /data/akuru"
pass "production runtime configuration"

[[ -L "${source_root}/backend/.env" ]] || fail "backend .env must link to the protected runtime environment"
[[ "$(readlink -f "${source_root}/backend/.env")" == "$env_file" ]] || fail "backend .env points to an unexpected file"
sudo -u akuru test -w "${source_root}/frontend" || fail "akuru must own the frontend build directory"
sudo -u akuru test -w "${source_root}/backend/.venv" || fail "akuru must own the backend virtual environment"
pass "runtime environment link and build-directory ownership"

"${app_root}/deploy/ubuntu/security-check.sh"
(cd "${source_root}/backend" && sudo -u akuru .venv/bin/python -m app.content_migration_audit --require-baseline-reset-eligible)
pass "current and legacy educational-content tables satisfy the baseline-reset policy"

(cd "${source_root}/backend" && sudo -u akuru .venv/bin/alembic heads) | tee /tmp/akuru-alembic-heads.txt
[[ "$(wc -l < /tmp/akuru-alembic-heads.txt | tr -d ' ')" == "1" ]] || fail "repository must have exactly one Alembic migration head"
rm -f /tmp/akuru-alembic-heads.txt
pass "one Alembic migration head in reviewed release"

install -d -o root -g akuru -m 0750 "$report_root"
report="$report_root/preflight-${actual}-$(date -u +%Y%m%dT%H%M%SZ).txt"
{
  echo "AKURU production release preflight"
  echo "release_sha=${actual}"
  echo "checked_at=$(date -u --iso-8601=seconds)"
  echo "baseline_reset_content_audit=eligible"
  echo "migration_heads=one"
  echo "next=take encrypted database and document backup, then execute deploy-reviewed-release.sh"
} > "$report"
chown root:akuru "$report"; chmod 0640 "$report"
echo "Evidence: $report"
