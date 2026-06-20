"""Daily report routes (mounted at /api/v1/dailyreport/)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ChecklistItemResultViewSet,
    ChecklistItemViewSet,
    ChecklistRunViewSet,
    ChecklistTemplateViewSet,
)

router = DefaultRouter()
router.register("templates", ChecklistTemplateViewSet, basename="checklisttemplate")
router.register("items", ChecklistItemViewSet, basename="checklistitem")
router.register("runs", ChecklistRunViewSet, basename="checklistrun")
router.register("results", ChecklistItemResultViewSet, basename="checklistresult")

urlpatterns = [
    path("", include(router.urls)),
]
