## Learned User Preferences

- Build a self-hosted Wikipedia-style platform with automation, CMS, admin, RSS, adaptive design, PWA, offline mode, bookmarks, content previews, text-to-markdown wiki import split by sections, URL import from Wikipedia/MediaWiki/RSS/docs, and Wikipedia paste with citations and wikilinks.
- Preferred stack: Django, uv, Ruff, Docker, nginx, Let's Encrypt, Fly.io, Cerebras AI (`gpt-oss-120b`) for formatting/import, and Lara Translate for EN→RU page translation.
- Use shadcn-style UI in Django via `django-cotton` and `shadcn_django` — not a React SPA.
- Expect rich UI polish: smooth transitions, tabs, image cards, scrollers, Lucide icons, custom fonts, link previews, and Notion-like page layout.
- Prefer front-end wiki authoring at `/wiki/new/` and `/wiki/<slug>/edit/` with markdown editor and inline media uploads — not admin-only flows.
- Aim for Wikipedia-grade capabilities: OpenGraph, rich media blocks (image/gif/video/audio/code/PDF/docs/HTML/FB2/MD/graph), annotations, CMS import/export, SEO (sitemap, robots), REST API, and MCP endpoint.
- Follow installed skills when implementing features.
- Run local dev on port 9000.
- Deploy to Fly.io as a new app when asked (`fly launch` / `fly deploy`).
- Languages limited to English (primary) and Russian; expect automatic Russian page generation when Lara Translate is configured.

## Learned Workspace Facts

- WikiWonder is a Django 5.x project (Python 3.12+) managed with uv; lint with `uv run ruff check .`.
- Local dev: `uv run python manage.py runserver 9000`; live Tailwind: `uv run python manage.py tailwind start`.
- After CSS or `input.css` changes, run `uv run python manage.py tailwind build` — missing build causes broken styles.
- Core apps live under `apps/`: `wiki`, `ai`, `imports`, `search`, `media`, `previews`, `seo`, `mcp`, `cms_extensions`.
- Auth via django-allauth (`/accounts/`); django CMS 5 catch-all runs after wiki URLs; register `/media/` first (`SERVE_MEDIA=true` in production) or uploads 404.
- CI (`.github/workflows/django.yml`) runs `uv sync`, `uv run ruff check .`, and `uv run pytest` with `config.settings_test` (in-memory SQLite).
- PWA service worker (sw v4) caches `/media/` so offline bookmarked pages keep cover images.
- Database: Supabase Postgres in production (`DATABASE_URL` with URL-encoded password); local SQLite fallback is `sqlite:///db.sqlite3`.
- Cerebras and Lara Translate read `CEREBRAS_API_KEY`, `CEREBRAS_MODEL` (default `gpt-oss-120b`), `LARA_ACCESS_KEY_ID`, and `LARA_ACCESS_KEY_SECRET` from environment — never commit keys.
- Production on Fly.io: app `wikiwonder`, region `iad`, https://wikiwonder.fly.dev, media volume `wikiwonder_media` at `/app/media`; `/health/` with 180s grace for first-boot migrations.
- i18n is en+ru only (`LANGUAGES`, modeltranslation); URL import at `/wiki/import/`; manual translation at `/wiki/<slug>/translate/`.
