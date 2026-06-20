"""Inventory routes (mounted at /api/v1/inventory/)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    InventoryCategoryViewSet,
    InventoryItemViewSet,
    StockMovementViewSet,
)

router = DefaultRouter()
router.register("items", InventoryItemViewSet, basename="inventoryitem")
router.register("categories", InventoryCategoryViewSet, basename="inventorycategory")
router.register("movements", StockMovementViewSet, basename="stockmovement")

urlpatterns = [
    path("", include(router.urls)),
]
