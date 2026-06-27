"""Wiki page and section models."""
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from i18nfield.fields import I18nTextField
from markdownx.models import MarkdownxField
from meta.models import ModelMeta


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class WikiPage(ModelMeta, models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, db_index=True)
    summary = models.TextField(blank=True, help_text="Short preview text for cards and RSS")
    content = MarkdownxField(blank=True, help_text="Full page markdown content")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="pages"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="pages")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wiki_pages",
    )
    cover_image = models.ImageField(
        upload_to="covers/", blank=True, null=True, help_text="Card hero image"
    )
    is_featured = models.BooleanField(default=False, db_index=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    editorial_notes = I18nTextField(
        blank=True,
        help_text="Per-language editorial notes (django-i18nfield JSON storage)",
    )

    _metadata = {
        "title": "get_meta_title",
        "description": "get_meta_description",
        "image": "get_meta_image_url",
        "url": "get_absolute_url",
        "object_type": "article",
        "locale": "get_meta_locale",
    }

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status", "-updated_at"]),
            models.Index(fields=["category", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "page"
            slug = base
            counter = 1
            while WikiPage.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("wiki:page_detail", kwargs={"slug": self.slug})

    def get_meta_title(self, context=None):
        from apps.seo.services import page_keywords

        keywords = page_keywords(self)
        primary = keywords[0] if keywords else "wiki"
        return f"{self.title} — {primary} | {settings.SITE_NAME}"

    def get_meta_description(self, context=None):
        from apps.seo.services import _clip

        text = self.summary or f"{self.title} — wiki article on {settings.SITE_NAME}."
        return _clip(text, min_len=50, max_len=160)

    def get_meta_image_url(self, context=None):
        return self.cover_url

    def get_meta_locale(self, context=None):
        from django.utils.translation import get_language
        return (get_language() or "en").replace("-", "_")

    @property
    def cover_url(self) -> str:
        if self.cover_image:
            return self.cover_image.url
        return f"https://picsum.photos/seed/{self.slug}/800/450"

    def __str__(self):
        return self.title


class WikiSection(models.Model):
    """Individual section within a wiki page (auto-split from imports)."""

    page = models.ForeignKey(WikiPage, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    content = MarkdownxField()
    order = models.PositiveIntegerField(default=0, db_index=True)
    anchor = models.CharField(max_length=80, blank=True, help_text="HTML anchor id")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("page", "slug")]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title) or f"section-{self.order}"
        if not self.anchor:
            self.anchor = self.slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.page.title} — {self.title}"


class Bookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookmarks"
    )
    page = models.ForeignKey(WikiPage, on_delete=models.CASCADE, related_name="bookmarks")
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "page")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} → {self.page.title}"


class SharedLink(models.Model):
    """Shareable external link with Open Graph preview metadata."""

    url = models.URLField(max_length=2048, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=2048, blank=True)
    favicon_url = models.URLField(max_length=2048, blank=True)
    site_name = models.CharField(max_length=120, blank=True)
    page = models.ForeignKey(
        WikiPage, null=True, blank=True, on_delete=models.SET_NULL, related_name="shared_links"
    )
    is_featured = models.BooleanField(default=False, db_index=True)
    click_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title or self.url.split("//")[-1][:60]) or "link"
            slug = base
            counter = 1
            while SharedLink.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("wiki:shared_link", kwargs={"slug": self.slug})

    def __str__(self):
        return self.title or self.url


class PageRevision(models.Model):
    """Track page edit history."""

    page = models.ForeignKey(WikiPage, on_delete=models.CASCADE, related_name="revisions")
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    change_summary = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Rev {self.pk} — {self.page.title}"
