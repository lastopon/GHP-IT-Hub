"""Asset management routes (mounted at /api/v1/assets/)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AssetAssignmentViewSet,
    AssetCategoryViewSet,
    AssetViewSet,
    MaintenanceRecordViewSet,
)

router = DefaultRouter()
router.register("items", AssetViewSet, basename="asset")
router.register("categories", AssetCategoryViewSet, basename="assetcategory")
router.register("assignments", AssetAssignmentViewSet, basename="assetassignment")
router.register("maintenance", MaintenanceRecordViewSet, basename="maintenancerecord")

urlpatterns = [
    path("", include(router.urls)),
]
