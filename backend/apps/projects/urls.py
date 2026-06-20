"""Project / Kanban routes (mounted at /api/v1/projects/)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BoardColumnViewSet, CardViewSet, ProjectViewSet

router = DefaultRouter()
router.register("items", ProjectViewSet, basename="project")
router.register("columns", BoardColumnViewSet, basename="boardcolumn")
router.register("cards", CardViewSet, basename="card")

urlpatterns = [
    path("", include(router.urls)),
]
