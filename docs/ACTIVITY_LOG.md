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
- Wiki creation: /wiki/new/ markdown paste + EasyMDE + media upload; admin auto-sync sections + redirect; API returns url/path; production media serving; share modal; page load optimizations
- Integrated Cerebras AI (cerebras-cloud-sdk): chat/stream/format API, wiki create “Format with AI”, test_cerebras command
- Notion-style quick create: title + markdown editor + auto created date; cover image preview; inline editor uploads (image/video/audio) via `/wiki/api/upload/`; Notion page layout on detail view; link highlight + hover OG previews in article content
- Page AI for viewers: Summarize / Ask AI on wiki pages (10 free requests/user/day); staff admin AI assist on WikiPage edit + bulk summary action; fixed `/wiki/new/` 500 (FormView without form_class → TemplateView)
- Fixed media rendering: markdown links to /media/* now render as inline video/audio/image/gif embeds instead of file-icon download links
- Fixed instant search (Alpine component registered before Alpine loads; native search input); fixed reading view exit (CSS no longer hides article header; floating exit button + Escape key)
- Added Docker production stack: Varnish Cache → Django, nginx with Let's Encrypt + HTTP/3 (QUIC), certbot scripts; PublicPageCacheMiddleware for cache headers
- Fixed PWA console errors: point django-pwa at custom `static/js/sw.js` via `PWA_SERVICE_WORKER_PATH`; removed duplicate SW registration from `app.js` (SecurityError scope mismatch); deduped manifest link in base template
- Fixed media/images 404 on production: register `/media/` URL patterns before django CMS catch-all (CMS was treating media paths as page slugs → 301 redirect loop / 404)
- Fixed production media serving when DEBUG=False (Django static() helper is debug-only); custom serve view with trailing-slash normalization for cached CMS redirects
- Wiki create editor: dedicated Upload image toolbar button (parity with video/audio); inserts `![title](/media/editor/...)` markdown inline; drag-drop and paste still supported
- Fixed mobile navigation: teleport sheet menu to body (header backdrop-filter broke overlay); full-width nav links, complete menu items, language + search sections
