"""Import raw text as wiki page from CLI."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.imports.services import import_text_as_wiki_page


class Command(BaseCommand):
    help = "Import a text file as a wiki page with auto section splitting"

    def add_arguments(self, parser):
        parser.add_argument("file", help="Path to text/markdown file")
        parser.add_argument("--title", default="", help="Page title (auto-detected if omitted)")
        parser.add_argument("--no-ai", action="store_true", help="Skip Cerebras AI formatting")
        parser.add_argument("--publish", action="store_true", help="Publish immediately")
        parser.add_argument("--username", default="admin", help="Author username")

    def handle(self, *args, **options):
        path = options["file"]
        with open(path, encoding="utf-8") as f:
            raw_text = f.read()

        user_model = get_user_model()
        author = user_model.objects.filter(username=options["username"]).first()

        page = import_text_as_wiki_page(
            raw_text,
            title=options["title"],
            author=author,
            use_ai=not options["no_ai"],
            publish=options["publish"],
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Created page: {page.title} ({page.sections.count()} sections) → {page.get_absolute_url()}"
            )
        )
