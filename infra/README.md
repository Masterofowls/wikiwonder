# WikiWonder edge stack (self-hosted)

```
Browser
   │  HTTPS / HTTP/3 (QUIC)
   ▼
nginx (infra/nginx) — TLS termination, static/media, Alt-Svc h3
   │
   ▼
Varnish (infra/varnish/default.vcl) — in-memory HTTP cache
   │
   ▼
Django / Gunicorn (web:8000)
```

## Components

| Service | Role |
|---------|------|
| **nginx** | Let's Encrypt certs, HTTP/2 + HTTP/3, `/static/` and `/media/` |
| **Varnish** | Caches anonymous GET pages; bypasses admin, API, authenticated sessions |
| **web** | Django application |
| **db** | PostgreSQL |
| **certbot** | ACME certificate issuance (`--profile production`) |

## Files

- `infra/varnish/default.vcl` — VCL 4.1 caching policy
- `infra/nginx/templates/` — nginx config templates (envsubst `DOMAIN`)
- `infra/nginx/Dockerfile` — nginx with [HTTP/3 module](https://nginx.org/en/docs/http/ngx_http_v3_module.html)
- `scripts/certbot-init.sh` / `certbot-init.ps1` — first-time certificate
- `scripts/certbot-renew.sh` — renewal + nginx reload

## Fly.io

Production at `wikiwonder.fly.dev` does **not** run this stack; Fly terminates TLS at the edge. Use Docker Compose on a VPS or dedicated server for Varnish + custom nginx.
