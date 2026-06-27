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
- Added Wikipedia-style media blocks, multi-format previews (PDF/doc/HTML/FB2/audio/video/graph), SEO (OG/JSON-LD/robots/sitemap), MCP JSON-RPC API, import/export (md/txt/json/csv/xlsx/pdf/docx), CMS embed plugins; 17 tests passing
- Added share/copy (Web Share API), reading view, cookie consent, offline bookmark SW cache (v3), advanced i18n (modeltranslation, django-i18nfield, rosetta, 5 languages, hreflang + browser translate hints), django-meta, django-check-seo, django-localflavor; 21 tests passing
- Deployed to Fly.io as new app `wikiwonder` (https://wikiwonder.fly.dev), Supabase Postgres, 1GB media volume (iad), production secrets configured
- Fixed signup 500 on production: default console email backend when SMTP unset; email verification defaults to `none` without EMAIL_HOST; unset Fly `ACCOUNT_EMAIL_VERIFICATION` secret
- Created production Django superuser `admin` (danvlad2015@gmail.com) on Fly
- Fixed WikiPage admin 500 (i18nfield editorial_notes vs modeltranslation widget); improved SEO meta keywords, descriptions, home content; sync django-check-seo keywords on publish
- Redeployed to Fly (wikiwonder.fly.dev); updated README Fly deployment docs
