"""Repair stored wiki markdown link targets in the database."""
from django.core.management.base import BaseCommand

from apps.wiki.models import WikiPage
from apps.wiki.services.pages import sync_page_sections
from apps.wiki.services.wikilinks import process_all_wiki_links


class Command(BaseCommand):
    help = "Rewrite stored markdown to fix nested/broken wiki links (dry-run by default)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Persist repaired markdown to the database.",
        )
        parser.add_argument("--slug", type=str, help="Repair a single page slug.")
        parser.add_argument(
            "--status",
            type=str,
            default="",
            help="Limit to status (draft, published, archived).",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        slug = options.get("slug")
        status = options.get("status") or ""

        qs = WikiPage.objects.all().order_by("slug")
        if slug:
            qs = qs.filter(slug=slug)
        if status:
            qs = qs.filter(status=status)

        changed = 0
        for page in qs.iterator():
            original = page.content or ""
            repaired = process_all_wiki_links(original, exclude_slug=page.slug)
            if repaired == original:
                continue
            changed += 1
            self.stdout.write(f"{'[dry-run] ' if not apply else ''}repair {page.slug}")
            if apply:
                page.content = repaired
                page.save(update_fields=["content", "updated_at"])
                sync_page_sections(page, repaired)

        verb = "Repaired" if apply else "Would repair"
        self.stdout.write(self.style.SUCCESS(f"{verb} {changed} page(s)."))
