#!/usr/bin/env bash
# Disposable 2026.9.5 -> 2026.9.6 -> 2026.9.5 rollback rehearsal.
# Run as root on the isolated ARM64 host; never touches the live Gateway state.
set -Eeuo pipefail
[[ "$(id -u)" == 0 && "$(dpkg --print-architecture)" == arm64 ]]
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
test_root=/data/openclaw/rollback-test
[[ ! -e "$test_root" ]] || { echo 'Disposable rollback path already exists; inspect it first.' >&2; exit 1; }
image_old='ghcr.io/openclaw/openclaw:2026.9.5@sha256:65d05df83ed72f25e2e0e3a7496ca5764a8ecf616dfc1f309a111c175f7d495f'
image_new='ghcr.io/openclaw/openclaw:2026.9.6@sha256:62040ed3fe6f566adb39e60c5428cce078989a39cc713d63e873c4dccf166892'
compose_file="${test_root}/compose.yaml"
cleanup() {
  docker compose -f "$compose_file" down --remove-orphans >/dev/null 2>&1 || true
  [[ "$test_root" == /data/openclaw/rollback-test ]] && rm -rf -- "$test_root"
}
trap cleanup EXIT
install -d -o root -g root -m 0700 "$test_root"
install -d -o 1000 -g 1000 -m 0700 "$test_root/state" "$test_root/cache"
install -o 1000 -g 1000 -m 0600 "${script_dir}/openclaw.json" "$test_root/state/openclaw.json"
(umask 077; printf 'OPENCLAW_GATEWAY_TOKEN=%s\n' "$(openssl rand -hex 32)" > "$test_root/gateway.env")
write_compose() {
  cat > "$compose_file" <<EOF
name: akuru-openclaw-rollback
services:
  gateway:
    image: $1
    platform: linux/arm64
    network_mode: none
    env_file: $test_root/gateway.env
    volumes:
      - $test_root/state:/home/node/.openclaw
      - $test_root/cache:/home/node/.cache
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=64m
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 1536m
EOF
}
start_and_wait() {
  docker compose -f "$compose_file" up -d --force-recreate gateway >/dev/null
  local status
  for _ in {1..120}; do
    if docker exec akuru-openclaw-rollback-gateway-1 node dist/docker-healthcheck.js >/dev/null 2>&1; then return 0; fi
    status="$(docker inspect akuru-openclaw-rollback-gateway-1 --format '{{.State.Status}}' 2>/dev/null || true)"
    [[ "$status" == restarting || "$status" == exited ]] && break
    sleep 1
  done
  echo "Rollback rehearsal Gateway failed health check: ${status:-unknown}" >&2
  docker compose -f "$compose_file" logs --tail=20 --no-color gateway | sed -E 's/(token|key|secret)=([^ ]+)/\1=[REDACTED]/Ig' >&2 || true
  return 1
}
write_compose "$image_old"
start_and_wait
docker compose -f "$compose_file" stop gateway >/dev/null
cp -a "$test_root/state" "$test_root/state-baseline"
write_compose "$image_new"
start_and_wait
docker compose -f "$compose_file" stop gateway >/dev/null
rm -rf -- "$test_root/state"
mv "$test_root/state-baseline" "$test_root/state"
write_compose "$image_old"
start_and_wait
echo 'Disposable OpenClaw image switch and rollback passed; live Gateway was untouched.'
