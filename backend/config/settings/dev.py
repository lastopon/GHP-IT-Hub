"""Development settings."""
from .base import *  # noqa: F401,F403
from .base import INSTALLED_APPS

DEBUG = True

# Permissive CORS in dev so the Vite frontend can talk to the API freely.
CORS_ALLOW_ALL_ORIGINS = True

# Browsable API helps during development.
REST_FRAMEWORK = {  # noqa: F405
    **globals().get("REST_FRAMEWORK", {}),
}

# Make migrations/debugging easier; keep django's default email backend in console.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INTERNAL_IPS = ["127.0.0.1"]
