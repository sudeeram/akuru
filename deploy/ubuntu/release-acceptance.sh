#!/usr/bin/env bash
# Post-deployment checks that do not disclose credentials or private content.
set -Eeuo pipefail
host="${1:?Usage: $0 akuru.example.com}"
[[ "$host" =~ ^[A-Za-z0-9.-]+$ ]] || { echo "Invalid hostname." >&2; exit 64; }

curl --fail --silent --show-error --max-time 15 "https://${host}/health" | grep -q '"status":"ok"'
headers="$(curl --fail --silent --show-error --max-time 15 --dump-header - --output /dev/null "https://${host}/health")"
printf '%s\n' "$headers" | grep -qi '^strict-transport-security:'
printf '%s\n' "$headers" | grep -qi '^x-content-type-options: nosniff'
printf '%s\n' "$headers" | grep -qi '^x-frame-options: DENY'
printf '%s\n' "$headers" | grep -qi '^content-security-policy:'
for service in akuru-api akuru-worker akuru-web redis-server; do systemctl is-active --quiet "$service"; done
for timer in akuru-backup.timer akuru-retention.timer; do
  systemctl is-enabled --quiet "$timer"
  systemctl is-active --quiet "$timer"
done
for port in 5432 6379 8000 5181; do
  ! ss -lnt | awk '{print $4}' | grep -Eq "(^0\\.0\\.0\\.0:${port}$|^\\[::\\]:${port}$)"
done
recent_errors="$(journalctl -u akuru-api -u akuru-worker -u akuru-web -u redis-server --since '-10 min' --priority=err --no-pager || true)"
if [[ -n "$recent_errors" ]]; then
  echo 'Recent service errors found; inspect logs before accepting this release.' >&2
  exit 1
fi
echo "AKURU HTTPS, headers, service health, timers and loopback-binding checks passed for ${host}."
