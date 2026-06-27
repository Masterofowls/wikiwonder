from django.apps import AppConfig


class CmsExtensionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cms_extensions"
    verbose_name = "WikiWonder CMS Extensions"

    def ready(self):
        from apps.cms_extensions import cms_plugins  # noqa: F401
