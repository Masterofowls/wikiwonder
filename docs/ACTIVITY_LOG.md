# Activity Log

## 2026-06-27

- Initialized WikiWonder Django project with uv, Ruff, and pyproject.toml
- Created apps: wiki (pages, sections, bookmarks, RSS), ai (Cerebras), imports (text conversion)
- Added Tailwind CSS theme, responsive templates, PWA service worker, offline caching
- Configured Docker, docker-compose (Postgres + nginx), fly.toml for Fly.io
- Added REST API, admin import/export, bootstrap and import_text management commands
- All 6 pytest tests passing; Ruff lint clean
- Fixed empty Tailwind CSS: migrated styles.css to v4 `@import` + `@source` directives, rebuilt (16KB utilities)
- Integrated shadcn/ui via django-cotton + shadcn_django (24 components), dark mode, redesigned all templates
- Added SharedLink model with OG previews, image cards, horizontal scrollers, Lucide icons, DM Sans/Fraunces fonts, tabbed home
- Integrated Supabase Postgres, django-allauth (accounts/), django CMS 5 (page publishing), instant search API + header typeahead; 9 pytest tests passing
