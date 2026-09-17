#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "${EUID}" -ne 0 || $# -ne 1 ]]; then
  echo "Usage: sudo $0 akuru.example.com" >&2; exit 1
fi
domain="$1"
if [[ ! "${domain}" =~ ^[A-Za-z0-9.-]+$ ]]; then echo "Invalid domain." >&2; exit 1; fi
install -d -o root -g akuru -m 0750 /etc/akuru
if [[ ! -f /etc/akuru/akuru.env ]]; then
  install -o root -g akuru -m 0640 /opt/akuru/source-code/backend/.env.example /etc/akuru/akuru.env
  echo "Edit /etc/akuru/akuru.env before starting AKURU." >&2
fi
ln -sfn /etc/akuru/akuru.env /opt/akuru/source-code/backend/.env
chown -h root:akuru /opt/akuru/source-code/backend/.env
for unit in /opt/akuru/deploy/ubuntu/systemd/*; do install -o root -g root -m 0644 "${unit}" /etc/systemd/system/; done
sed "s/AKURU_DOMAIN/${domain}/g" /opt/akuru/deploy/ubuntu/nginx-akuru.conf > /etc/nginx/sites-available/akuru
ln -sfn /etc/nginx/sites-available/akuru /etc/nginx/sites-enabled/akuru
rm -f /etc/nginx/sites-enabled/default
systemctl daemon-reload
systemctl enable akuru-api akuru-worker akuru-web akuru-retention.timer akuru-backup.timer
nginx -t
echo "Services installed. Configure /etc/akuru/akuru.env and TLS certificate, then start the services."
