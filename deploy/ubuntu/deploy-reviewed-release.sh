#!/usr/bin/env bash
# Applies a preflighted release already checked out at /opt/akuru.
set -Eeuo pipefail
umask 027
if [[ $# -lt 2 || $# -gt 3 || ( "$1" != "--execute" && "$1" != "--plan" ) || ( $# -eq 3 && "$3" != "--full" ) ]]; then
  echo "Usage: sudo $0 <--plan|--execute> <reviewed-git-sha> [--full]" >&2; exit 64
fi
mode="$1"; release_sha="$2"
app_root="${AKURU_APP_ROOT:-/opt/akuru}"
source_root="${AKURU_SOURCE_ROOT:-${app_root}/source-code}"
env_file="${AKURU_ENV_FILE:-/etc/akuru/akuru.env}"
evidence_root="${AKURU_RELEASE_EVIDENCE_ROOT:-/data/akuru/release-evidence}"
planner=(python3 "${app_root}/deploy/ubuntu/release-plan.py" --root "$app_root" --target "$release_sha" --state "$evidence_root/last-successful-release.json")
if [[ -r "$env_file" ]]; then planner+=(--environment-file "$env_file"); fi
if [[ "${3:-}" == "--full" ]]; then planner+=(--full); fi
if [[ "$mode" == "--plan" ]]; then "${planner[@]}"; exit; fi
[[ $EUID -eq 0 ]] || { echo "Run as root." >&2; exit 1; }
# Serialize deployment and its successful-state/dependency receipts.
exec 9>/run/lock/akuru-deploy.lock
flock -n 9 || { echo 'Another AKURU deployment is running.' >&2; exit 1; }
install -d -o root -g akuru -m 0750 "$evidence_root"
actual="$(git -C "$app_root" rev-parse HEAD)"
run_id="${actual}-$(date -u +%Y%m%dT%H%M%SZ)"
timings="$evidence_root/timings-${run_id}.tsv"
install -o root -g akuru -m 0640 /dev/null "$timings"
printf 'stage\tseconds\tstatus\n' > "$timings"
active_stage=initialization; stage_started=$SECONDS; deployment_started=$SECONDS
trap 'status=$?; printf "%s\t%s\tfailed:%s\n" "$active_stage" "$((SECONDS-stage_started))" "$status" >> "$timings"; echo "Deployment failed during $active_stage; baseline not advanced. Timings: $timings" >&2; exit "$status"' ERR
run_stage() {
  active_stage="$1"; shift; stage_started=$SECONDS
  echo "START $active_stage"
  "$@"
  printf '%s\t%s\tpassed\n' "$active_stage" "$((SECONDS-stage_started))" >> "$timings"
  echo "DONE $active_stage ($((SECONDS-stage_started))s)"
}
run_stage preflight "${app_root}/deploy/ubuntu/release-preflight.sh" "$release_sha"
# shellcheck disable=SC1090
source "$env_file"
cd "${source_root}/backend"
[[ "${AKURU_DATABASE_NAME:-}" == "akuru" ]] || { echo "Refusing: database name must be exactly akuru." >&2; exit 1; }
[[ "${AKURU_DATABASE_HOST:-}" == "127.0.0.1" || "${AKURU_DATABASE_HOST:-}" == "localhost" ]] || { echo "Refusing: database must be local." >&2; exit 1; }
[[ "${AKURU_DATABASE_USER:-}" =~ ^[a-z_][a-z0-9_]*$ && "${AKURU_DATABASE_USER}" != "postgres" ]] || { echo "Refusing: invalid least-privilege database owner." >&2; exit 1; }
plan_file="$evidence_root/plan-${run_id}.json"
make_plan() { "${planner[@]}" > "$plan_file"; }
run_stage planning make_plan
chown root:akuru "$plan_file"; chmod 0640 "$plan_file"
flag() { python3 -c 'import json,sys;print(str(json.load(open(sys.argv[1]))[sys.argv[2]]).lower())' "$plan_file" "$1"; }
cat "$plan_file"
backup_manifest=not-required-no-runtime-change
backup_marker="$(mktemp)"
trap 'rm -f "$backup_marker"' EXIT
backup() {
  systemctl start akuru-backup.service
  [[ "$(systemctl show akuru-backup.service --property=Result --value)" == "success" ]] || { echo "Encrypted backup failed; deployment stopped." >&2; return 1; }
  backup_root="${AKURU_BACKUP_ROOT:-/data/akuru/backups}"
  backup_manifest="$(find "$backup_root" -maxdepth 1 -type f -name 'akuru-*.manifest' -newer "$backup_marker" -print -quit)"
  [[ -n "$backup_manifest" ]] || { echo "Fresh backup evidence was not created; deployment stopped." >&2; return 1; }
  grep -qx 'database_name=akuru' "$backup_manifest"
  grep -qx 'plaintext_database_list=passed' "$backup_manifest"
  grep -qx 'plaintext_document_list=passed' "$backup_manifest"
}
if [[ "$(flag backup)" == true ]]; then run_stage backup backup; fi
cache=(python3 "${app_root}/deploy/ubuntu/dependency-cache.py")
cache_args=(--source "$source_root" --state-dir "$evidence_root/dependency-cache")
frontend_dependencies() {
  if [[ "$(flag full)" != true ]] && "${cache[@]}" check frontend "${cache_args[@]}"; then return; fi
  sudo -u akuru npm --prefix "${source_root}/frontend" ci
  "${cache[@]}" record frontend "${cache_args[@]}"
}
backend_dependencies() {
  if [[ "$(flag full)" != true ]] && "${cache[@]}" check backend "${cache_args[@]}"; then return; fi
  sudo -u akuru "${source_root}/backend/.venv/bin/python" -m pip install --requirement "${source_root}/backend/requirements-production.lock"
  "${cache[@]}" record backend "${cache_args[@]}"
}
if [[ "$(flag frontend)" == true ]]; then
  run_stage frontend_dependencies frontend_dependencies
  run_stage frontend_build sudo -u akuru npm --prefix "${source_root}/frontend" run build
fi
if [[ "$(flag backend)" == true ]]; then
  run_stage backend_dependencies backend_dependencies
  if [[ "$(flag migrations)" == true ]]; then
    run_stage migrations sudo -u akuru "${source_root}/backend/.venv/bin/alembic" upgrade head
  fi
  if [[ "$(flag catalog)" == true ]]; then
    run_stage catalog sudo -u akuru "${source_root}/backend/.venv/bin/python" -m app.seed_catalog
  fi
  run_stage migration_current sudo -u akuru "${source_root}/backend/.venv/bin/alembic" current
  run_stage schema_check sudo -u akuru "${source_root}/backend/.venv/bin/alembic" check
fi
services=()
if [[ "$(flag backend)" == true ]]; then services+=(akuru-api akuru-worker); fi
if [[ "$(flag frontend)" == true ]]; then services+=(akuru-web); fi
if [[ ${#services[@]} -gt 0 ]]; then run_stage restart systemctl restart "${services[@]}"; fi
systemctl is-active --quiet akuru-api akuru-worker akuru-web
health() {
  ready=false
  for _ in {1..30}; do
    if curl --fail --silent --show-error --max-time 3 --header "Host: ${AKURU_PUBLIC_HOST}" http://127.0.0.1:8000/health >/dev/null 2>&1; then
      ready=true; break
    fi
    sleep 1
  done
  [[ "$ready" == true ]] || { echo "API did not become ready." >&2; return 1; }
  curl --fail --silent --show-error --max-time 15 "https://${AKURU_PUBLIC_HOST:?Set AKURU_PUBLIC_HOST in /etc/akuru/akuru.env}/health" >/dev/null
}
run_stage health health
run_stage acceptance "${app_root}/deploy/ubuntu/release-acceptance.sh" "$AKURU_PUBLIC_HOST"
# Advance only after build, restart and acceptance succeed. The JSON is data, never sourced.
run_stage accepted_baseline python3 - "$plan_file" "$evidence_root/last-successful-release.json" <<'PY'
import json,os,sys,tempfile
plan=json.load(open(sys.argv[1]));plan['accepted']=True
fd,path=tempfile.mkstemp(dir=os.path.dirname(sys.argv[2]))
try:
    with os.fdopen(fd,'w') as f:json.dump(plan,f,indent=2);f.flush();os.fsync(f.fileno())
    os.replace(path,sys.argv[2])
finally:
    if os.path.exists(path):os.unlink(path)
PY
chown root:akuru "$evidence_root/last-successful-release.json"; chmod 0640 "$evidence_root/last-successful-release.json"
report="$evidence_root/deployed-${run_id}.txt"
{
  echo "AKURU production deployment evidence"
  echo "release_sha=${actual}"
  echo "deployed_at=$(date -u --iso-8601=seconds)"
  echo "backup_manifest=${backup_manifest}"
  echo "deployment_mode=component_aware_forward_migration"
  echo "plan=${plan_file}"
  echo "timings=${timings}"
  echo "elapsed_seconds=$((SECONDS-deployment_started))"
  echo "services=akuru-api, akuru-worker, akuru-web active"
  echo "health=loopback, HTTPS and release acceptance passed"
  echo "next=complete release-specific authenticated functional checks"
} > "$report"
chown root:akuru "$report"; chmod 0640 "$report"
echo "Deployment completed in $((SECONDS-deployment_started))s. Evidence: $report"
