"""Bootstrap WikiWonder with sample data."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

from apps.wiki.models import Category, SharedLink, WikiPage
from apps.wiki.services.pages import sync_page_sections

SAMPLE_PAGE = """\
# Getting Started

Welcome to WikiWonder — your personal Wikipedia.

## What is WikiWonder?

WikiWonder is a self-hosted knowledge base with:

- **Markdown editing** via django-markdownx
- **AI-powered import** using Cerebras
- **Automatic section splitting** from headings
- **PWA & offline** support with service workers
- **RSS feeds** and bookmarks

## Quick Start

1. Log in to `/admin/` and create pages
2. Use **Import API** at `/api/import/create/` to auto-convert text
3. Subscribe to RSS at `/feeds/latest/`

## Import Example

Paste any raw text into the admin or API — it will be formatted as markdown
and split into sections automatically.

### Section Splitting

Content is split on `##` headings. Each section gets its own anchor
in the table of contents.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/pages/` | GET | List wiki pages |
| `/api/import/preview/` | POST | Preview text import |
| `/api/import/create/` | POST | Create page from text |
| `/api/ai/format/` | POST | AI markdown formatting |
"""


class Command(BaseCommand):
    help = "Bootstrap WikiWonder with admin user and sample content"

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin")
        parser.add_argument("--password", default="admin")
        parser.add_argument("--email", default="admin@wikiwonder.local")

    def handle(self, *args, **options):
        user_model = get_user_model()
        username = options["username"]
        password = options["password"]
        email = options["email"]

        site, _ = Site.objects.get_or_create(pk=settings.SITE_ID)
        site_domain = settings.SITE_URL.replace("https://", "").replace("http://", "").rstrip("/")
        if site.domain != site_domain or site.name != settings.SITE_NAME:
            site.domain = site_domain or "localhost:9000"
            site.name = settings.SITE_NAME
            site.save()
            self.stdout.write(self.style.SUCCESS(f"Updated site: {site.name} ({site.domain})"))

        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created admin user: {username}"))
        else:
            self.stdout.write(f"Admin user '{username}' already exists")

        cat, _ = Category.objects.get_or_create(
            name="Documentation",
            defaults={"description": "WikiWonder documentation and guides"},
        )

        page, created = WikiPage.objects.get_or_create(
            slug="getting-started",
            defaults={
                "title": "Getting Started",
                "content": SAMPLE_PAGE,
                "summary": "Welcome to WikiWonder — your personal Wikipedia.",
                "status": WikiPage.Status.PUBLISHED,
                "category": cat,
                "author": user,
                "is_featured": True,
            },
        )
        if created:
            sync_page_sections(page)
            self.stdout.write(self.style.SUCCESS("Created sample page: Getting Started"))
        else:
            self.stdout.write("Sample page already exists")

        sample_links = [
            ("https://www.djangoproject.com/", "Django Web Framework", True),
            ("https://ui.shadcn.com/", "shadcn/ui Components", True),
            ("https://tailwindcss.com/", "Tailwind CSS", False),
        ]
        for url, title, featured in sample_links:
            link, created = SharedLink.objects.get_or_create(
                url=url,
                defaults={"title": title, "is_featured": featured, "site_name": url.split("/")[2]},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created shared link: {title}"))

        self.stdout.write(self.style.SUCCESS("Bootstrap complete!"))
