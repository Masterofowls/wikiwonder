#!/bin/sh
set -e

export DOMAIN="${DOMAIN:-localhost}"

mkdir -p /etc/nginx/conf.d

envsubst '${DOMAIN}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

if [ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
  echo "TLS certificates found for ${DOMAIN} — enabling HTTPS + HTTP/3"
  envsubst '${DOMAIN}' < /etc/nginx/templates/ssl.conf.template > /etc/nginx/conf.d/ssl.conf
  # Flag for HTTP→HTTPS redirect in default.conf
  echo "map \$host \$ssl_ready { default 1; }" > /etc/nginx/conf.d/00-ssl-ready.conf
else
  echo "No Let's Encrypt certs for ${DOMAIN} — HTTP only (port 80)"
  echo "map \$host \$ssl_ready { default 0; }" > /etc/nginx/conf.d/00-ssl-ready.conf
fi

exec nginx -g 'daemon off;'
