# nginx with HTTP/3 (QUIC) — see https://nginx.org/en/docs/http/ngx_http_v3_module.html
FROM macbre/nginx-http3:1.27.0-alpine

RUN apk add --no-cache gettext

COPY templates/ /etc/nginx/templates/
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh \
  && cp /etc/nginx/templates/00-upstream.conf /etc/nginx/conf.d/00-upstream.conf

EXPOSE 80 443/tcp 443/udp

ENTRYPOINT ["/docker-entrypoint.sh"]
