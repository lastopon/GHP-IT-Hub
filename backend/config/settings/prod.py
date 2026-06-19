"""Production settings (On-Premise hardened)."""
from .base import *  # noqa: F401,F403

DEBUG = False

# ---- Security headers (behind Nginx/Kong reverse proxy doing SSL, per cloude.md §3) ----
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ---- Object storage (MinIO / S3-compatible, per cloude.md §3 / §4.3) ----
# Configure via env when MinIO is deployed; falls back to local FS otherwise.
# STORAGES = {"default": {"BACKEND": "storages.backends.s3.S3Storage"}, ...}
