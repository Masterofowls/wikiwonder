from django.apps import AppConfig


class SeoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.seo"
    verbose_name = "SEO Tools"

    def ready(self):
        from django.db.models.signals import post_migrate

        from apps.seo import signals  # noqa: F401

        post_migrate.connect(signals.ensure_site_seo_keywords, sender=self)
