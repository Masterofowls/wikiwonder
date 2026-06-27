# WikiWonder

Self-hosted Wikipedia with AI-powered import, CMS admin, PWA offline support, RSS, bookmarks, and automatic markdown section splitting.

## Features

- **Wiki pages** with markdown editing (django-markdownx)
- **Auto section splitting** — content divided by `##` headings into navigable sections
- **AI import** — paste raw text, Cerebras formats it into markdown wiki pages
- **Admin CMS** — full Django admin with import/export, bulk actions
- **RSS/Atom feed** at `/feeds/latest/`
- **Bookmarks** for authenticated users
- **Content previews** on hover
- **PWA + offline** via service worker caching
- **Responsive design** with Tailwind CSS
- **REST API** for pages, bookmarks, import, and AI formatting
- **Health checks** at `/health/`
- **Docker + Varnish + nginx** — HTTP cache, TLS (Let's Encrypt), HTTP/3 (QUIC)
- **Fly.io** deployment config included (edge TLS; no Varnish on Fly)

## Quick Start (Local)

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

### Setup

```bash
# Clone and enter project
cd wikiwonder

# Copy environment template
cp .env.example .env
# Edit .env and set CEREBRAS_API_KEY for AI features

# Install dependencies
uv sync

# Run migrations and bootstrap sample data
uv run python manage.py migrate
uv run python manage.py bootstrap_wiki

# Build Tailwind CSS
uv run python manage.py tailwind install
uv run python manage.py tailwind build

# Collect static files
uv run python manage.py collectstatic --noinput

# Start dev server (port 9000)
uv run python manage.py runserver 9000
```

Visit http://localhost:9000 — admin login: `admin` / `admin`

## Docker

Stack: **Client → nginx (TLS, HTTP/3) → [Varnish Cache](https://www.varnish.org/) → Django**

```bash
# Development (Postgres + Django + Varnish + nginx)
docker compose up --build

# Direct Django (bypass cache): http://localhost:9000
# Through Varnish + nginx:      http://localhost:9080
# HTTPS + HTTP/3 (after certs): https://localhost:9443
```

Set `DATABASE_URL=postgres://wikiwonder:wikiwonder@db:5432/wikiwonder` in `.env` for Docker.

### Production: Let's Encrypt + HTTP/3

Point DNS for your domain to the server, then:

```bash
# .env
DOMAIN=wiki.example.com
CERTBOT_EMAIL=you@example.com
ALLOWED_HOSTS=wiki.example.com
SITE_URL=https://wiki.example.com
META_SITE_PROTOCOL=https
META_SITE_DOMAIN=wiki.example.com

# Linux/macOS
chmod +x scripts/certbot-init.sh
./scripts/certbot-init.sh wiki.example.com you@example.com

# Windows PowerShell
.\scripts\certbot-init.ps1 -Domain wiki.example.com -Email you@example.com

# Auto-renew (cron)
0 3 * * * /path/to/wikiwonder/scripts/certbot-renew.sh
```

Optional: run certbot renew loop in Docker:

```bash
docker compose --profile production up -d certbot-renew
```

**Verify HTTP/3:** `curl -I --http3-only https://wiki.example.com/` (requires curl with HTTP/3).

**Varnish:** anonymous GET wiki pages are cached in memory; check `X-Cache: HIT|MISS` response headers. Config: `infra/varnish/default.vcl`.

**Note:** [Fly.io production](https://wikiwonder.fly.dev) uses Fly's edge proxy (TLS/HTTP/2) directly to Gunicorn — use this Docker stack for VPS/self-hosted deployments.

## Fly.io Deployment

Production: **https://wikiwonder.fly.dev**

```bash
# Install flyctl: https://fly.io/docs/hands-on/install-flyctl/
fly auth login

# First-time setup (app already exists as wikiwonder)
fly launch --no-deploy   # skip if app exists

# Required secrets (use Supabase Postgres DATABASE_URL in production)
fly secrets set SECRET_KEY="$(python -c "import secrets; print(secrets.token_urlsafe(50))")"
fly secrets set DEBUG=false
fly secrets set ALLOWED_HOSTS=wikiwonder.fly.dev
fly secrets set SITE_URL=https://wikiwonder.fly.dev
fly secrets set META_SITE_PROTOCOL=https
fly secrets set META_SITE_DOMAIN=wikiwonder.fly.dev
fly secrets set DATABASE_URL="postgresql://..."   # Supabase connection string

# Optional
fly secrets set CEREBRAS_API_KEY=your-key-here
fly secrets set SEO_SITE_KEYWORDS="wiki, knowledge base, encyclopedia, WikiWonder, articles"

# Media volume (iad region)
fly volumes create wikiwonder_media --size 1 --region iad

# Deploy
fly deploy -a wikiwonder

# Create admin user on production
fly ssh console -a wikiwonder -C "sh -c 'DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_EMAIL=you@example.com DJANGO_SUPERUSER_PASSWORD=your-password /app/.venv/bin/python manage.py createsuperuser --noinput'"

# Logs and health
fly logs -a wikiwonder
curl https://wikiwonder.fly.dev/health/
```

## API Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/pages/` | GET | Optional | List published pages |
| `/api/pages/{slug}/` | GET | Optional | Page detail with sections |
| `/api/pages/{slug}/preview/` | GET | Optional | Content preview |
| `/api/bookmarks/` | GET/POST | Required | User bookmarks |
| `/api/import/preview/` | POST | Required | Preview text import |
| `/api/import/create/` | POST | Required | Create page from text |
| `/api/ai/status/` | GET | None | Cerebras configured + model |
| `/api/ai/format/` | POST | Required | Format text → markdown + title + summary |
| `/api/ai/chat/` | POST | Required | Cerebras chat completion |
| `/api/ai/chat/stream/` | POST | Required | Streaming chat (SSE) |
| `/api/ai/suggest-title/` | POST | Required | Suggest wiki page title |
| `/feeds/latest/` | GET | None | Atom RSS feed |
| `/health/` | GET | None | Health check |

### Import Example

```bash
curl -X POST http://localhost:9000/api/import/create/ \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -d '{"text": "My raw notes about Python...\n\nSECTION ONE\nDetails here.", "use_ai": true, "publish": true}'
```

## Project Structure

```
wikiwonder/
├── apps/
│   ├── wiki/       # Pages, sections, bookmarks, RSS
│   ├── ai/         # Cerebras AI integration
│   └── imports/    # Text import & conversion
├── config/         # Django settings & URLs
├── theme/          # Tailwind CSS theme
├── templates/      # HTML templates
├── static/         # CSS, JS, PWA service worker
├── infra/          # Docker, nginx configs
├── tests/          # pytest suite
├── Dockerfile
├── docker-compose.yml
└── fly.toml
```

## Development

```bash
# Lint
uv run ruff check .
uv run ruff format .

# Test
uv run pytest

# Create superuser
uv run python manage.py createsuperuser
```

## Security

- Store `CEREBRAS_API_KEY` and `SECRET_KEY` in environment variables only
- Never commit `.env` files
- Rotate API keys if exposed

## License

MIT
