"""Re-translate wiki pages with Lara Translate."""
from django.core.management.base import BaseCommand

from apps.wiki.models import WikiPage
from apps.wiki.services.lara_translate import auto_translate_wiki_page, get_lara_service


class Command(BaseCommand):
    help = "Generate or refresh Russian translations for wiki pages via Lara Translate"

    def add_arguments(self, parser):
        parser.add_argument("--slug", default="", help="Single page slug (default: all published)")
        parser.add_argument("--force", action="store_true", help="Overwrite existing Russian fields")

    def handle(self, *args, **options):
        service = get_lara_service()
        if not service.is_configured:
            self.stderr.write(self.style.ERROR("Lara Translate credentials are not configured."))
            return

        qs = WikiPage.objects.all().order_by("-updated_at")
        if options["slug"]:
            qs = qs.filter(slug=options["slug"])

        count = 0
        for page in qs:
            results = auto_translate_wiki_page(page, force=options["force"])
            if results.get("ru"):
                count += 1
                self.stdout.write(self.style.SUCCESS(f"Translated: {page.title} ({page.slug})"))
            elif results:
                self.stderr.write(self.style.WARNING(f"Failed: {page.slug}"))

        self.stdout.write(self.style.SUCCESS(f"Done — {count} page(s) translated."))
