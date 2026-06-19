"""Test settings — SQLite in-memory, no external services required.

Lets `manage.py test` run without PostgreSQL/Redis (CI & quick local checks).
Production/dev still use PostgreSQL via base settings.
"""
from .base import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Run Celery tasks eagerly / use a dummy cache so tests need no Redis.
CELERY_TASK_ALWAYS_EAGER = True
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # faster tests
