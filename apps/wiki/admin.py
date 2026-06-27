from django.contrib import admin
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.wiki.models import (
    Bookmark,
    Category,
    PageRevision,
    SharedLink,
    Tag,
    WikiPage,
    WikiSection,
)
from apps.wiki.services.link_preview import enrich_shared_link


class WikiSectionInline(admin.TabularInline):
    model = WikiSection
    extra = 0
    fields = ("order", "title", "anchor", "content")
    ordering = ("order",)


class PageRevisionInline(admin.TabularInline):
    model = PageRevision
    extra = 0
    readonly_fields = ("editor", "title", "change_summary", "created_at")
    can_delete = False
    max_num = 5


@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    list_display = ("name", "slug", "parent", "page_count")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    @admin.display(description="Pages")
    def page_count(self, obj):
        return obj.pages.count()


@admin.register(Tag)
class TagAdmin(ImportExportModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class WikiPageResource(resources.ModelResource):
    class Meta:
        model = WikiPage
        fields = (
            "id", "title", "slug", "summary", "content", "status",
            "category", "is_featured", "created_at", "updated_at",
        )
        export_order = fields


@admin.register(WikiPage)
class WikiPageAdmin(ImportExportModelAdmin):
    resource_class = WikiPageResource
    list_display = ("title", "status_badge", "category", "author", "view_count", "updated_at")
    list_filter = ("status", "category", "is_featured", "tags")
    search_fields = ("title", "content", "summary")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    readonly_fields = ("view_count", "created_at", "updated_at", "preview_link")
    inlines = [WikiSectionInline, PageRevisionInline]
    actions = ["publish_pages", "split_sections_action"]
    fieldsets = (
        (None, {"fields": ("title", "slug", "status", "preview_link")}),
        ("Content", {"fields": ("summary", "content", "cover_image")}),
        ("Organization", {"fields": ("category", "tags", "is_featured")}),
        ("Meta", {"fields": ("author", "view_count", "published_at", "created_at", "updated_at")}),
    )

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {"draft": "#6b7280", "published": "#16a34a", "archived": "#dc2626"}
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Preview")
    def preview_link(self, obj):
        if obj.pk:
            return format_html('<a href="{}" target="_blank">View page →</a>', obj.get_absolute_url())
        return "—"

    @admin.action(description="Publish selected pages")
    def publish_pages(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status=WikiPage.Status.PUBLISHED, published_at=timezone.now())
        self.message_user(request, f"{updated} page(s) published.")

    @admin.action(description="Re-split sections from markdown")
    def split_sections_action(self, request, queryset):
        from apps.wiki.services.pages import sync_page_sections
        count = 0
        for page in queryset:
            sync_page_sections(page)
            count += 1
        self.message_user(request, f"Re-split sections for {count} page(s).")


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "page", "note", "created_at")
    list_filter = ("user",)
    search_fields = ("page__title", "note")


@admin.register(PageRevision)
class PageRevisionAdmin(admin.ModelAdmin):
    list_display = ("page", "editor", "change_summary", "created_at")
    list_filter = ("created_at",)
    readonly_fields = ("page", "editor", "title", "content", "change_summary", "created_at")


@admin.register(SharedLink)
class SharedLinkAdmin(admin.ModelAdmin):
    list_display = ("title", "site_name", "url", "is_featured", "click_count", "created_at")
    list_filter = ("is_featured", "site_name")
    search_fields = ("title", "url", "description")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("click_count", "created_at", "updated_at")
    actions = ["fetch_previews", "mark_featured"]

    @admin.action(description="Fetch Open Graph previews")
    def fetch_previews(self, request, queryset):
        for link in queryset:
            enrich_shared_link(link)
            link.save()
        self.message_user(request, f"Updated previews for {queryset.count()} link(s).")

    @admin.action(description="Mark as featured")
    def mark_featured(self, request, queryset):
        queryset.update(is_featured=True)
