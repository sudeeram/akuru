#!/usr/bin/env bash
# Post-deployment checks that do not disclose credentials or private content.
set -Eeuo pipefail
host="${1:?Usage: $0 akuru.example.com}"
[[ "$host" =~ ^[A-Za-z0-9.-]+$ ]] || { echo "Invalid hostname." >&2; exit 64; }
tmp_body="$(mktemp)"
tmp_headers="$(mktemp)"
trap 'rm -f "$tmp_body" "$tmp_headers"' EXIT

curl --fail --silent --show-error --max-time 15 "https://${host}/health" | grep -q '"status":"ok"'
headers="$(curl --fail --silent --show-error --max-time 15 --dump-header - --output /dev/null "https://${host}/health")"
printf '%s\n' "$headers" | grep -qi '^strict-transport-security:'
printf '%s\n' "$headers" | grep -qi '^x-content-type-options: nosniff'
printf '%s\n' "$headers" | grep -qi '^x-frame-options: DENY'
printf '%s\n' "$headers" | grep -qi '^content-security-policy:'
for route in /login /flashcards /student/subjects /admin/accounts /parent/students; do
  curl --fail --silent --show-error --max-time 15 --output "$tmp_body" "https://${host}${route}"
  grep -q 'AKURU' "$tmp_body"
done
missing_asset_status="$(curl --silent --show-error --max-time 15 --output "$tmp_body" --write-out '%{http_code}' "https://${host}/_next/routing-acceptance-missing.js")"
[[ "$missing_asset_status" == "404" ]] || { echo 'Missing build asset did not return 404.' >&2; exit 1; }
missing_api_status="$(curl --silent --show-error --max-time 15 --dump-header "$tmp_headers" --output "$tmp_body" --write-out '%{http_code}' "https://${host}/api/v1/routing-acceptance-missing")"
[[ "$missing_api_status" == "404" ]] || { echo 'Unknown API route did not return 404.' >&2; exit 1; }
grep -qi '^content-type: application/json' "$tmp_headers" || { echo 'Unknown API route returned frontend content.' >&2; exit 1; }
for service in akuru-api akuru-worker akuru-web redis-server; do systemctl is-active --quiet "$service"; done
for timer in akuru-backup.timer akuru-retention.timer; do
  systemctl is-enabled --quiet "$timer"
  systemctl is-active --quiet "$timer"
done
for port in 5432 6379 8000 5181; do
  ! ss -lnt | awk '{print $4}' | grep -Eq "(^0\\.0\\.0\\.0:${port}$|^\\[::\\]:${port}$)"
done
recent_errors="$(journalctl -u akuru-api -u akuru-worker -u akuru-web -u redis-server --since '-10 min' --priority=err --quiet --no-pager || true)"
if [[ -n "$recent_errors" ]]; then
  echo 'Recent service errors found; inspect logs before accepting this release.' >&2
  exit 1
fi
echo "AKURU HTTPS, headers, routed entry points, fallback boundaries, service health, timers and loopback-binding checks passed for ${host}."
