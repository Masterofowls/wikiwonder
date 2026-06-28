"""Import a wiki page from a remote URL."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.imports.sources.fetch import FetchError
from apps.imports.url_import import import_url_as_wiki_page


class Command(BaseCommand):
    help = "Import a wiki page from Wikipedia, RSS, docs, or any public URL"

    def add_arguments(self, parser):
        parser.add_argument("url", help="Source URL to import")
        parser.add_argument("--source", default="auto", help="Source type (auto, wikipedia, mediawiki, rss, docs, web)")
        parser.add_argument("--title", default="", help="Override page title")
        parser.add_argument("--no-ai", action="store_true", help="Skip AI polish")
        parser.add_argument("--publish", action="store_true", help="Publish immediately")
        parser.add_argument("--username", default="admin", help="Author username")

    def handle(self, *args, **options):
        user_model = get_user_model()
        author = user_model.objects.filter(username=options["username"]).first()

        try:
            page = import_url_as_wiki_page(
                options["url"],
                title=options["title"],
                author=author,
                source_type=options["source"],
                use_ai=not options["no_ai"],
                publish=options["publish"],
            )
        except FetchError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported: {page.title} ({page.sections.count()} sections) → {page.get_absolute_url()}"
            )
        )
