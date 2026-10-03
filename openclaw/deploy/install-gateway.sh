#!/usr/bin/env bash
# Install the isolated, pinned Step 02 Gateway. Run as root from a reviewed checkout.
set -Eeuo pipefail
[[ "$(id -u)" == 0 ]] || { echo 'Run as root.' >&2; exit 1; }
[[ "$(dpkg --print-architecture)" == arm64 ]] || { echo 'Expected ARM64 host.' >&2; exit 1; }
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
command -v docker >/dev/null

install -d -o root -g root -m 0700 /data/openclaw /etc/openclaw
install -d -o 1000 -g 1000 -m 0700 /data/openclaw/state /data/openclaw/cache
install -d -o root -g root -m 0755 /opt/openclaw
install -o root -g root -m 0644 "${script_dir}/compose.yaml" /opt/openclaw/compose.yaml

if [[ ! -e /etc/openclaw/gateway.env ]]; then
  (umask 077; printf 'OPENCLAW_GATEWAY_TOKEN=%s\n' "$(openssl rand -hex 32)" > /etc/openclaw/gateway.env)
fi
chmod 0600 /etc/openclaw/gateway.env
chown root:root /etc/openclaw/gateway.env

config_path=/data/openclaw/state/openclaw.json
if [[ -e "$config_path" ]] && ! cmp -s "${script_dir}/openclaw.json" "$config_path"; then
  cp -p "$config_path" "${config_path}.previous"
fi
install -o 1000 -g 1000 -m 0600 "${script_dir}/openclaw.json" "$config_path"

docker compose -f /opt/openclaw/compose.yaml config -q
docker compose -f /opt/openclaw/compose.yaml up -d gateway
for _ in {1..90}; do
  status="$(docker inspect akuru-openclaw-gateway-1 --format '{{.State.Health.Status}}' 2>/dev/null || true)"
  [[ "$status" == healthy ]] && break
  [[ "$status" == unhealthy ]] && { echo 'Gateway unhealthy; inspect logs.' >&2; exit 1; }
  sleep 1
done
[[ "${status:-}" == healthy ]] || { echo 'Gateway health timeout.' >&2; exit 1; }
[[ "$(docker inspect akuru-openclaw-gateway-1 --format '{{.HostConfig.NetworkMode}}')" == none ]]
[[ "$(docker inspect akuru-openclaw-gateway-1 --format '{{json .NetworkSettings.Ports}}')" == '{}' ]]
echo 'Isolated OpenClaw Gateway is healthy, with no network or published ports.'
