"""Test settings — always use in-memory SQLite."""
from config.settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

STORAGES = {
    **STORAGES,  # noqa: F405
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Disable Lara Translate in tests unless explicitly overridden
LARA_ACCESS_KEY_ID = ""
LARA_ACCESS_KEY_SECRET = ""
LARA_AUTO_TRANSLATE = False
