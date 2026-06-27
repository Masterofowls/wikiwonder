## Learned User Preferences

- Build a self-hosted Wikipedia-style platform with automation, CMS, admin, RSS, adaptive design, PWA, offline mode, bookmarks, content previews, and text-to-markdown wiki import split by sections.
- Preferred stack: Django, uv, Ruff, Docker, nginx, Let's Encrypt, Fly.io, and Cerebras AI (`gpt-oss-120b`) for formatting/import.
- Use shadcn-style UI in Django via `django-cotton` and `shadcn_django` — not a React SPA.
- Expect rich UI polish: smooth transitions, tabs, image cards, scrollers, Lucide icons, custom fonts, and link previews.
- Aim for Wikipedia-grade capabilities: OpenGraph, rich media blocks (image/gif/video/audio/code/PDF/docs/HTML/FB2/MD/graph), annotations, CMS import/export, SEO (sitemap, robots), REST API, and MCP endpoint.
- Follow installed skills when implementing features.
- Run local dev on port 9000.
- Deploy to Fly.io as a new app when asked (`fly launch` / `fly deploy`).

## Learned Workspace Facts

- WikiWonder is a Django 5.x project (Python 3.12+) managed with uv; lint with `uv run ruff check .`.
- Local dev: `uv run python manage.py runserver 9000`; live Tailwind: `uv run python manage.py tailwind start`.
- After CSS or `input.css` changes, run `uv run python manage.py tailwind build` — missing build causes broken styles.
- Core apps live under `apps/`: `wiki`, `ai`, `imports`, `search`, `media`, `previews`, `seo`, `mcp`, `cms_extensions`.
- Auth via django-allauth (`/accounts/`); content CMS via django CMS 5 (catch-all routes after wiki URLs).
- Database: Supabase Postgres in production (`DATABASE_URL` with URL-encoded password); local SQLite fallback is `sqlite:///db.sqlite3`.
- AI integration reads `CEREBRAS_API_KEY` and `CEREBRAS_MODEL` (default `gpt-oss-120b`) from environment — never commit keys.
- Production is on Fly.io: app `wikiwonder`, region `iad`, URL https://wikiwonder.fly.dev, media volume `wikiwonder_media` at `/app/media`.
- Health check endpoint: `/health/`; `fly.toml` uses a 180s grace period to tolerate long first-boot migrations.
