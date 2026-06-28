from django.contrib import admin
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from i18nfield.fields import I18nTextField
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from modeltranslation.admin import TranslationAdmin

from apps.wiki.models import (
    Bookmark,
    Category,
    EditSuggestion,
    PageRevision,
    SharedLink,
    Tag,
    WikiPage,
    WikiSection,
)
from apps.wiki.services.link_preview import enrich_shared_link
from apps.wiki.services.pages import sync_page_sections


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
class CategoryAdmin(TranslationAdmin, ImportExportModelAdmin):
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
class WikiPageAdmin(TranslationAdmin, ImportExportModelAdmin):
    resource_class = WikiPageResource
    change_form_template = "admin/wiki/wikipage/change_form.html"
    list_display = ("title", "status_badge", "category", "author", "view_count", "updated_at")
    list_filter = ("status", "category", "is_featured", "tags")
    search_fields = ("title", "content", "summary")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    readonly_fields = ("view_count", "created_at", "updated_at", "preview_link")
    inlines = [WikiSectionInline, PageRevisionInline]
    actions = ["publish_pages", "ai_summarize_action", "split_sections_action"]
    fieldsets = (
        (None, {"fields": ("title", "slug", "status", "preview_link")}),
        ("Content", {"fields": ("summary", "content", "cover_image", "editorial_notes")}),
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

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # i18nfield + modeltranslation admin widgets are incompatible (locales kwarg).
        if isinstance(db_field, I18nTextField):
            kwargs.pop("widget", None)
            return db_field.formfield(**kwargs)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        if change and "content" in form.changed_data:
            from apps.wiki.services.pages import save_page_revision

            save_page_revision(obj, editor=request.user, change_summary="Admin edit")
        super().save_model(request, obj, form, change)
        sync_page_sections(obj)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        sync_page_sections(form.instance)

    def response_add(self, request, obj, post_url_continue=False):
        if "_continue" not in request.POST and "_addanother" not in request.POST:
            return HttpResponseRedirect(obj.get_absolute_url())
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if "_view" in request.POST:
            return HttpResponseRedirect(obj.get_absolute_url())
        return super().response_change(request, obj)

    @admin.action(description="Publish selected pages")
    def publish_pages(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status=WikiPage.Status.PUBLISHED, published_at=timezone.now())
        self.message_user(request, f"{updated} page(s) published.")

    @admin.action(description="Generate AI summary for selected pages")
    def ai_summarize_action(self, request, queryset):
        from apps.ai.page_context import page_markdown_text
        from apps.ai.services import get_ai_service

        ai = get_ai_service()
        if not ai.is_configured:
            self.message_user(request, "CEREBRAS_API_KEY is not configured.", level="error")
            return
        count = 0
        for page in queryset:
            page.summary = ai.generate_summary(page_markdown_text(page))[:500]
            page.save(update_fields=["summary", "updated_at"])
            count += 1
        self.message_user(request, f"Generated AI summaries for {count} page(s).")

    @admin.action(description="Re-split sections from markdown")
    def split_sections_action(self, request, queryset):
        from apps.wiki.services.pages import sync_page_sections
        count = 0
        for page in queryset:
            sync_page_sections(page)
            count += 1
        self.message_user(request, f"Re-split sections for {count} page(s).")


@admin.register(EditSuggestion)
class EditSuggestionAdmin(admin.ModelAdmin):
    list_display = ("page", "author", "status", "change_summary", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("page__title", "author__username", "change_summary")
    readonly_fields = ("page", "author", "title", "content", "created_at", "reviewer", "reviewed_at")
    actions = ["approve_suggestions"]

    @admin.action(description="Approve and apply selected suggestions")
    def approve_suggestions(self, request, queryset):
        from django.utils import timezone

        from apps.wiki.services.pages import update_page_content

        count = 0
        for suggestion in queryset.filter(status=EditSuggestion.Status.PENDING):
            page = suggestion.page
            page.title = suggestion.title
            page.save(update_fields=["title", "updated_at"])
            update_page_content(
                page,
                suggestion.content,
                editor=request.user,
                change_summary=f"Applied suggestion #{suggestion.pk}",
            )
            suggestion.status = EditSuggestion.Status.APPROVED
            suggestion.reviewer = request.user
            suggestion.reviewed_at = timezone.now()
            suggestion.save(update_fields=["status", "reviewer", "reviewed_at"])
            count += 1
        self.message_user(request, f"Applied {count} suggestion(s).")


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
