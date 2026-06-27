#!/usr/bin/env bash
# Renew Let's Encrypt certificates (run via cron: 0 3 * * * /path/to/certbot-renew.sh)
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose --profile production run --rm certbot renew --quiet
docker compose exec nginx nginx -s reload || docker compose up -d --force-recreate nginx

echo "Certificate renewal complete."
