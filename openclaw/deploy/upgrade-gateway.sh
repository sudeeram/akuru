#!/usr/bin/env bash
# Upgrade the existing isolated gateway without overwriting live configuration.
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo 'Run as root.' >&2; exit 1; }
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
compose=/opt/openclaw/compose.yaml
container=akuru-openclaw-gateway-1
image="$(sed -n 's/^    image: //p' "${script_dir}/compose.yaml")"
[[ "$image" =~ ^ghcr.io/openclaw/openclaw:[a-zA-Z0-9.-]+@sha256:[a-f0-9]{64}$ ]] || { echo 'Expected a pinned official image.' >&2; exit 1; }
[[ -f "$compose" && -f /etc/openclaw/gateway.env ]] || { echo 'Existing deployment required; use install-gateway.sh for a new installation.' >&2; exit 1; }
[[ $(docker inspect "$container" --format '{{.HostConfig.NetworkMode}}') == none ]] || { echo 'Only the isolated network=none deployment is supported.' >&2; exit 1; }
[[ $(docker inspect "$container" --format '{{json .NetworkSettings.Ports}}') == '{}' ]] || { echo 'Unexpected exposed ports.' >&2; exit 1; }
[[ -s /etc/akuru/backup-age-recipient ]] || { echo 'Encrypted backup recipient missing.' >&2; exit 1; }

docker pull "$image"
# Check the candidate runtime without any credentials/state mounted.
runtime="$(docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --entrypoint node "$image" --version)"
node "${script_dir}/../../source-code/scripts/node-version-policy.mjs"
# Use dynamic import so this script works from absolute repository paths.
node --input-type=module -e 'const {isSupportedNode}=await import(process.argv[1]); if(!isSupportedNode(process.argv[2])) process.exit(1)' \
  "file://${script_dir}/../../source-code/scripts/node-version-policy.mjs" "$runtime"

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_dir="/data/openclaw/backups/node-security-${stamp}"
install -d -m 0700 "$backup_dir"
work="$(mktemp -d /data/openclaw/.upgrade.XXXXXX)"
trial="akuru-openclaw-upgrade-check-${stamp}"
stopped=false
cleanup() {
  docker rm -f "$trial" >/dev/null 2>&1 || true
  rm -rf -- "$work"
  if [[ "$stopped" == true ]]; then docker compose -f "$compose" start gateway >/dev/null || true; fi
}
trap cleanup EXIT
docker inspect "$container" --format '{{.Config.Image}}' > "$backup_dir/previous-image.txt"
cp -p "$compose" "$backup_dir/previous-compose.yaml"
docker compose -f "$compose" stop gateway
stopped=true
tar -cf "$work/state.tar" -C / data/openclaw/state etc/openclaw opt/openclaw/compose.yaml
tar -tf "$work/state.tar" >/dev/null
age -r "$(tr -d '[:space:]' < /etc/akuru/backup-age-recipient)" -o "$backup_dir/state.tar.age" "$work/state.tar"
sha256sum "$backup_dir/state.tar.age" > "$backup_dir/state.sha256"
cp -a /data/openclaw/state "$work/state"
install -d -o 1000 -g 1000 -m 0700 "$work/cache"
# Start the existing gateway again while validating an independent state copy.
docker compose -f "$compose" start gateway
stopped=false

docker run -d --name "$trial" --network none --read-only --cap-drop ALL --security-opt no-new-privileges \
  --pids-limit 256 --memory 1536m --cpus 2 --env-file /etc/openclaw/gateway.env \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m -v "$work/state:/home/node/.openclaw" \
  -v "$work/cache:/home/node/.cache" "$image" >/dev/null
healthy=false
for _ in {1..90}; do
  if docker exec "$trial" node dist/index.js health --json > "$work/health.json" 2>/dev/null; then healthy=true; break; fi
  sleep 1
done
[[ "$healthy" == true ]] || { echo "Candidate health failed. Live gateway retained; backup: $backup_dir" >&2; exit 1; }
docker exec "$trial" node dist/index.js config validate --json
docker rm -f "$trial" >/dev/null
# Copy only the reviewed Compose specification. Never reinstall the bootstrap config.
install -m 0644 -o root -g root "${script_dir}/compose.yaml" "$compose"
docker compose -f "$compose" config -q
docker compose -f "$compose" up -d --no-deps --force-recreate gateway
healthy=false
for _ in {1..90}; do
  if docker exec "$container" node dist/index.js health --json > "$work/health.json" 2>/dev/null; then healthy=true; break; fi
  sleep 1
done
[[ "$healthy" == true ]] || { echo "Gateway health failed. Inspect logs and matching-state recovery in docs; backup: $backup_dir" >&2; exit 1; }
[[ $(docker inspect "$container" --format '{{.HostConfig.NetworkMode}}') == none ]]
[[ $(docker inspect "$container" --format '{{json .NetworkSettings.Ports}}') == '{}' ]]
[[ $(docker inspect "$container" --format '{{.HostConfig.ReadonlyRootfs}}') == true ]]
docker exec "$container" node --version
printf 'Gateway healthy; encrypted recovery backup: %s\n' "$backup_dir"
