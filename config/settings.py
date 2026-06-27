"""WikiWonder Django settings."""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-only-insecure-key-change-in-production")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "djangocms_admin_style",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    "django.contrib.postgres",
    # django-allauth
    "allauth",
    "allauth.account",
    # django CMS
    "cms",
    "menus",
    "treebeard",
    "sekizai",
    "filer",
    "easy_thumbnails",
    "djangocms_text_ckeditor",
    # Third-party
    "rest_framework",
    "corsheaders",
    "markdownx",
    "pwa",
    "import_export",
    "tailwind",
    "django_cotton",
    "widget_tweaks",
    "django_user_agents",
    "imagekit",
    "theme",
    # Local apps
    "apps.wiki",
    "apps.ai",
    "apps.imports",
    "apps.search",
]

MIDDLEWARE = [
    "cms.middleware.utils.ApphookReloadMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "cms.middleware.user.CurrentUserMiddleware",
    "cms.middleware.page.CurrentPageMiddleware",
    "cms.middleware.toolbar.ToolbarMiddleware",
    "cms.middleware.language.LanguageCookieMiddleware",
    "django_user_agents.middleware.UserAgentMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "sekizai.context_processors.sekizai",
                "cms.context_processors.cms_settings",
                "apps.wiki.context_processors.site_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


def _supabase_database_config() -> dict:
    """Ensure Supabase Postgres connections use SSL."""
    db = env.db("DATABASE_URL", default="sqlite:///db.sqlite3")
    if db.get("ENGINE", "").endswith("postgresql"):
        options = db.setdefault("OPTIONS", {})
        options.setdefault("sslmode", "require")
        db.setdefault("CONN_MAX_AGE", 60)
        db.setdefault("CONN_HEALTH_CHECKS", True)
    return db


DATABASES = {"default": _supabase_database_config()}

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

SITE_ID = 1
LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LANGUAGES = [("en", "English")]

CMS_CONFIRM_VERSION4 = True
CMS_TEMPLATES = [
    ("cms/page.html", "Standard page"),
    ("cms/fullwidth.html", "Full width page"),
]
CMS_LANGUAGES = {
    1: [
        {
            "code": "en",
            "name": "English",
            "public": True,
            "redirect_on_fallback": True,
        },
    ],
    "default": {
        "public": True,
        "redirect_on_fallback": True,
    },
}
CMS_PERMISSION = True
CMS_PLACEHOLDER_CONF = {
    "content": {
        "plugins": ["TextPlugin", "PicturePlugin", "LinkPlugin"],
        "name": "Main content",
    },
}
X_FRAME_OPTIONS = "SAMEORIGIN"

THUMBNAIL_PROCESSORS = (
    "easy_thumbnails.processors.colorspace",
    "easy_thumbnails.processors.autocrop",
    "easy_thumbnails.processors.scale_and_crop",
)

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Site
SITE_NAME = env("SITE_NAME", default="WikiWonder")
SITE_URL = env("SITE_URL", default="http://localhost:9000")

# Supabase (optional — for future integrations; auth uses django-allauth)
SUPABASE_URL = env("SUPABASE_URL", default="")
SUPABASE_PUBLISHABLE_KEY = env("SUPABASE_PUBLISHABLE_KEY", default="")
SUPABASE_SECRET_KEY = env("SUPABASE_SECRET_KEY", default="")
SUPABASE_JWKS_URL = env("SUPABASE_JWKS_URL", default="")

# django-allauth
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = env("ACCOUNT_EMAIL_VERIFICATION", default="optional")
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_SESSION_REMEMBER = True
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

# Cerebras AI
CEREBRAS_API_KEY = env("CEREBRAS_API_KEY", default="")
CEREBRAS_MODEL = env("CEREBRAS_MODEL", default="gpt-oss-120b")

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticatedOrReadOnly"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# MarkdownX
MARKDOWNX_MARKDOWNIFY_FUNCTION = "markdownx.utils.markdownify"
MARKDOWNX_MEDIA_PATH = "markdownx/"
MARKDOWNX_UPLOAD_MAX_SIZE = 5 * 1024 * 1024  # 5 MB

# Tailwind
TAILWIND_APP_NAME = "theme"

# PWA
PWA_APP_NAME = env("PWA_APP_NAME", default="WikiWonder")
PWA_APP_DESCRIPTION = env("PWA_APP_DESCRIPTION", default="Your personal Wikipedia")
PWA_APP_THEME_COLOR = "#1e40af"
PWA_APP_BACKGROUND_COLOR = "#ffffff"
PWA_APP_DISPLAY = "standalone"
PWA_APP_SCOPE = "/"
PWA_APP_ORIENTATION = "any"
PWA_APP_START_URL = "/"
PWA_APP_STATUS_BAR_COLOR = "default"
PWA_APP_ICONS = [
    {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
]
PWA_APP_ICONS_APPLE = [
    {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
]
PWA_APP_SPLASH_SCREEN = []
PWA_APP_DIR = "ltr"
PWA_APP_LANG = "en-US"

# Security (production)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
