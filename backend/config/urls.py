"""Root URL configuration for GHP IT Hub."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def health(_request):
    """Lightweight liveness probe (used by Docker / load balancers)."""
    return JsonResponse({"status": "ok", "service": "ghp-it-hub"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    # ---- API v1 ----
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/helpdesk/", include("apps.helpdesk.urls")),
    # ---- API schema & docs ----
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
