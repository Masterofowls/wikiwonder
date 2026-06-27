#!/usr/bin/env bash
# Obtain initial Let's Encrypt certificate for WikiWonder (Docker Compose production)
set -euo pipefail

DOMAIN="${1:-${DOMAIN:-}}"
EMAIL="${2:-${CERTBOT_EMAIL:-}}"

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
  echo "Usage: DOMAIN=wiki.example.com CERTBOT_EMAIL=you@example.com ./scripts/certbot-init.sh"
  echo "   or: ./scripts/certbot-init.sh wiki.example.com you@example.com"
  exit 1
fi

export DOMAIN EMAIL

echo "Starting nginx for ACME challenge on ${DOMAIN}..."
docker compose up -d web varnish nginx

echo "Requesting certificate..."
docker compose --profile production run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d "$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  --force-renewal

echo "Reloading nginx with TLS + HTTP/3..."
docker compose up -d --force-recreate nginx

echo "Done. Visit https://${DOMAIN}/"
